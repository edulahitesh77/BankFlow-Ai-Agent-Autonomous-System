"""
BankFlow AI - Primary Mesa Simulation Model
Orchestrates multi-agent banking execution, concurrent Request Agent pools,
and end-to-end request lifecycle processing using Mesa 3.x abstractions.
"""

from typing import List, Dict, Any, Optional
import random
import mesa
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.request import Request, ServiceType, RequestStatus
from app.models.agent import AgentType
from app.agents.customer_agent import CustomerAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.verification_agent import VerificationAgent
from app.agents.request_agent import RequestAgent
from app.agents.service_agent import ServiceAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.simulation.configuration import SimulationConfig
from app.simulation.scheduler import WorkloadScheduler, LeastLoadedPolicy
from app.simulation.agent_registry import AgentRegistry


class BankingSimulationModel(mesa.Model):
    """
    Primary Mesa simulation model coordinating the BankFlow AI multi-agent swarm.
    Executes staged simulation ticks and ensures transparent concurrency across Request Agents.
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        super().__init__()
        self.config = config or SimulationConfig()
        if self.config.random_seed is not None:
            self.random.seed(self.config.random_seed)

        # Mesa 3 _wrapped_step discards return value; restore returning user step result
        def _step_with_return(*args, **kwargs):
            self.steps += 1
            return self._user_step(*args, **kwargs)
        self.step = _step_with_return

        self.current_tick: int = 0
        self.scheduler = WorkloadScheduler(LeastLoadedPolicy)

        # 1. Customer Agent
        self.customer_agent = CustomerAgent(
            self, agent_code="AGT-CUST-SIM-01", customer_code="CUST-SYN-00001"
        )

        # 2. Intake Agent
        self.intake_agent = IntakeAgent(self, agent_code="AGT-INTAKE-01")

        # 3. Verification Agent
        self.verification_agent = VerificationAgent(self, agent_code="AGT-VERIF-01")

        # 4. Request Agent Pool (Configurable number of concurrent workers)
        self.request_agent_pool: List[RequestAgent] = []
        for i in range(1, self.config.num_request_agents + 1):
            agent = RequestAgent(self, agent_code=f"RequestAgent_{i}")
            self.request_agent_pool.append(agent)

        # 5. Service Agent Pool
        self.service_agent_pool: List[ServiceAgent] = [
            ServiceAgent(self, agent_code="ServiceAgent_CHEQUE_BOOK", supported_skills=["CHEQUE_BOOK"]),
            ServiceAgent(self, agent_code="ServiceAgent_DEBIT_CARD", supported_skills=["DEBIT_CARD_REPLACEMENT"]),
            ServiceAgent(self, agent_code="ServiceAgent_ADDRESS", supported_skills=["ADDRESS_UPDATE"]),
            ServiceAgent(
                self,
                agent_code="ServiceAgent_APPLICATION",
                supported_skills=["ACCOUNT_APPLICATION", "ACCOUNT_APPLICATION_PRE_SCREENING"],
            ),
        ]

        # 6. Supervisor Agent
        self.supervisor_agent = SupervisorAgent(self, agent_code="AGT-SUPERVISOR-01")

        # Ensure RabbitMQ topology is initialized if broker is accessible
        try:
            from app.messaging.queues import declare_queues_and_bindings
            declare_queues_and_bindings()
        except Exception as e:
            logger.debug("RabbitMQ topology setup deferred: %s", str(e))

        # Execution telemetry
        self.tick_history: List[Dict[str, Any]] = []

    def get_all_agents(self) -> List[Any]:
        """Returns flat list of all active agent instances."""
        return list(self.agents)

    def get_request_agents(self) -> List[RequestAgent]:
        """Returns the pool of RequestAgent instances."""
        return self.request_agent_pool

    def get_service_agents(self) -> List[ServiceAgent]:
        """Returns the pool of ServiceAgent instances."""
        return self.service_agent_pool

    def step(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Executes a single simulation tick:
        - Phase 1: Intake & Classification of NEW requests.
        - Phase 2: Dispatch of CLASSIFIED requests to available Request Agents.
        - Phase 3: Prerequisite verification of QUEUED requests.
        - Phase 4: Simulated service execution of VERIFIED requests.
        - Phase 5: Telemetry capture and database sync.
        """
        self.current_tick += 1
        tick_summary: Dict[str, Any] = {
            "tick": self.current_tick,
            "intake_processed": 0,
            "dispatched_to_request_agents": 0,
            "verified": 0,
            "services_completed": 0,
            "active_request_agents": 0,
        }

        if db is None:
            return tick_summary

        # Snapshot IDs at tick start to enforce staged discrete advancement across ticks
        new_ids = [
            r[0]
            for r in db.query(Request.id)
            .filter(Request.request_status == RequestStatus.NEW)
            .order_by(Request.created_at)
            .limit(self.config.synthetic_batch_size)
            .all()
        ]
        classified_ids = [
            r[0]
            for r in db.query(Request.id)
            .filter(Request.request_status == RequestStatus.CLASSIFIED)
            .order_by(Request.created_at)
            .all()
        ]
        queued_ids = [
            r[0]
            for r in db.query(Request.id)
            .filter(Request.request_status == RequestStatus.QUEUED)
            .all()
        ]
        verified_ids = [
            r[0]
            for r in db.query(Request.id)
            .filter(Request.request_status == RequestStatus.VERIFIED)
            .all()
        ]

        # --------------------------------------------------------------------
        # Phase 1: Intake & Classification of NEW Requests
        # --------------------------------------------------------------------
        if new_ids:
            new_requests = (
                db.query(Request)
                .filter(Request.id.in_(new_ids))
                .order_by(Request.created_at)
                .all()
            )
            for req in new_requests:
                self.intake_agent.process_request(db, req)
                tick_summary["intake_processed"] += 1
            db.commit()

        # --------------------------------------------------------------------
        # Phase 2: Dispatch CLASSIFIED Requests to Available Request Agents
        # --------------------------------------------------------------------
        if classified_ids:
            classified_requests = (
                db.query(Request)
                .filter(Request.id.in_(classified_ids))
                .order_by(Request.created_at)
                .all()
            )
            for req in classified_requests:
                available_worker = self.scheduler.dispatch_request_agent(
                    self.request_agent_pool, req
                )
                if available_worker:
                    available_worker.accept_and_queue_request(db, req)
                    tick_summary["dispatched_to_request_agents"] += 1
                else:
                    # All Request Agents busy; request remains in CLASSIFIED waiting for next tick
                    break
            db.commit()

        # --------------------------------------------------------------------
        # Phase 3: Verification of QUEUED Requests by Verification Agent
        # --------------------------------------------------------------------
        if queued_ids:
            queued_requests = (
                db.query(Request)
                .filter(Request.id.in_(queued_ids))
                .all()
            )
            for req in queued_requests:
                assigned_worker = next(
                    (a for a in self.request_agent_pool if a.current_request_id == req.request_id),
                    None,
                )
                if assigned_worker:
                    self.verification_agent.process_request(db, req)
                    tick_summary["verified"] += 1

                    # If verification resulted in an exception state (e.g. NEEDS_CORRECTION or HUMAN_REVIEW),
                    # the Request Agent's active work on this version is completed
                    if req.request_status in [
                        RequestStatus.NEEDS_CORRECTION,
                        RequestStatus.HUMAN_REVIEW,
                        RequestStatus.REJECTED_INPUT,
                    ]:
                        assigned_worker.complete_and_release(db, req, final_status=req.request_status)
            db.commit()

        # --------------------------------------------------------------------
        # Phase 4: Service Execution of VERIFIED Requests
        # --------------------------------------------------------------------
        if verified_ids:
            verified_requests = (
                db.query(Request)
                .filter(Request.id.in_(verified_ids))
                .all()
            )
            for req in verified_requests:
                assigned_worker = next(
                    (a for a in self.request_agent_pool if a.current_request_id == req.request_id),
                    None,
                )
                if assigned_worker:
                    service_worker = self.scheduler.dispatch_service_agent(
                        self.service_agent_pool, req.service_type
                    )
                    if service_worker:
                        service_worker.execute_service(db, req)
                        assigned_worker.complete_and_release(db, req, final_status=req.request_status)
                        tick_summary["services_completed"] += 1
            db.commit()

        # --------------------------------------------------------------------
        # Phase 5: Telemetry & Status Capture
        # --------------------------------------------------------------------
        tick_summary["active_request_agents"] = sum(
            1 for a in self.request_agent_pool if not a.is_available
        )
        self.tick_history.append(tick_summary)

        # Emit worker heartbeats over RabbitMQ
        for worker in self.request_agent_pool:
            try:
                worker.emit_heartbeat(db)
            except Exception as e:
                logger.debug("Non-critical: Heartbeat emission skipped: %s", str(e))

        # Sync state with PostgreSQL database
        AgentRegistry.sync_agents_to_database(db, self.get_all_agents())

        return tick_summary
