"""
BankFlow AI - Agent and Simulation Service
Business logic powering agent inspection, simulation control, and benchmark scenario execution.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status

from app.models.agent import Agent as DBAgent, AgentHealthStatus
from app.models.request import Request, RequestStatus
from app.models.agent_event import AgentEvent
from app.models.failure_record import AgentFailure
from app.schemas.agent_simulation import (
    AgentDetailResponse,
    AgentListResponse,
    AgentStatisticsResponse,
    SimulationStartRequest,
    SimulationStatusResponse,
    SimulationStatisticsResponse,
    RunTestScenarioRequest,
    RunTestScenarioResponse,
)
from app.simulation.configuration import SimulationConfig
from app.simulation.simulation_runner import simulation_runner
from app.simulation.agent_registry import AgentRegistry
from app.simulation.model import BankingSimulationModel


class AgentService:
    """Service handling multi-agent introspection and simulation controls."""

    @staticmethod
    def get_all_agents(db: Session) -> AgentListResponse:
        """
        Returns all registered agent instances.
        If the in-memory simulation model is initialized, returns live operational state;
        otherwise initializes model and syncs persisted records to PostgreSQL.
        """
        if not simulation_runner.model:
            simulation_runner.model = BankingSimulationModel()
            AgentRegistry.sync_agents_to_database(db, simulation_runner.model.get_all_agents())

        agents_data = [
            AgentDetailResponse(
                id=getattr(a, "db_id", None),
                agent_code=a.agent_code,
                agent_type=a.agent_type.value if hasattr(a.agent_type, "value") else str(a.agent_type),
                availability_status=a.availability_status,
                processing_status=a.processing_status,
                current_request_id=a.current_request_id,
                assigned_version=a.assigned_version,
                completed_work_count=a.completed_work_count,
                last_active_at=a.last_active_at.isoformat() if a.last_active_at else None,
                branch_id=a.branch_id,
            )
            for a in simulation_runner.model.get_all_agents()
        ]
        return AgentListResponse(agents=agents_data, total=len(agents_data))

    @staticmethod
    def get_agent_by_id(db: Session, agent_id: str) -> AgentDetailResponse:
        """Retrieves details of an individual agent by code or numeric database ID."""
        # 1. Check in-memory simulation
        if simulation_runner.model:
            agent = next(
                (a for a in simulation_runner.model.get_all_agents()
                 if a.agent_code == agent_id or str(getattr(a, "db_id", "")) == agent_id),
                None,
            )
            if agent:
                return AgentDetailResponse(
                    id=getattr(agent, "db_id", None),
                    agent_code=agent.agent_code,
                    agent_type=agent.agent_type.value if hasattr(agent.agent_type, "value") else str(agent.agent_type),
                    availability_status=agent.availability_status,
                    processing_status=agent.processing_status,
                    current_request_id=agent.current_request_id,
                    assigned_version=agent.assigned_version,
                    completed_work_count=agent.completed_work_count,
                    last_active_at=agent.last_active_at.isoformat() if agent.last_active_at else None,
                    branch_id=agent.branch_id,
                )

        # 2. Check DB
        query = db.query(DBAgent).filter(
            (DBAgent.agent_code == agent_id) |
            (DBAgent.id == int(agent_id) if agent_id.isdigit() else False)
        )
        db_agent = query.first()
        if not db_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found.",
            )

        return AgentDetailResponse(
            id=db_agent.id,
            agent_code=db_agent.agent_code,
            agent_type=db_agent.agent_type.value if hasattr(db_agent.agent_type, "value") else str(db_agent.agent_type),
            availability_status=db_agent.availability_status,
            processing_status=getattr(db_agent, "processing_status", "IDLE"),
            current_request_id=str(db_agent.current_request_id) if db_agent.current_request_id else None,
            assigned_version=0,
            completed_work_count=getattr(db_agent, "completed_work_count", 0),
            last_active_at=db_agent.last_active_at.isoformat() if getattr(db_agent, "last_active_at", None) else None,
            branch_id=db_agent.branch_id,
        )

    @staticmethod
    def get_agent_statistics(db: Session) -> AgentStatisticsResponse:
        """Calculates agent workload telemetry."""
        agents_resp = AgentService.get_all_agents(db)
        total = len(agents_resp.agents)
        available = sum(1 for a in agents_resp.agents if a.availability_status == "AVAILABLE")
        busy = sum(1 for a in agents_resp.agents if a.availability_status == "BUSY")
        unavailable = sum(1 for a in agents_resp.agents if a.availability_status == "UNAVAILABLE")
        processed = sum(a.completed_work_count for a in agents_resp.agents)

        return AgentStatisticsResponse(
            total_agents=total,
            available_agents=available,
            busy_agents=busy,
            unavailable_agents=unavailable,
            total_requests_processed=processed,
        )

    @staticmethod
    def start_simulation(config_req: SimulationStartRequest) -> Dict[str, Any]:
        """Starts background simulation loop."""
        config = SimulationConfig(
            num_request_agents=config_req.num_request_agents,
            tick_delay_seconds=config_req.tick_delay_seconds,
            scenario_name=config_req.scenario_name,
        )
        return simulation_runner.start(config)

    @staticmethod
    def stop_simulation() -> Dict[str, Any]:
        """Stops background simulation."""
        return simulation_runner.stop()

    @staticmethod
    def get_simulation_status() -> SimulationStatusResponse:
        """Returns status of simulation runner."""
        st = simulation_runner.get_status()
        return SimulationStatusResponse(**st)

    @staticmethod
    def get_simulation_statistics(db: Session) -> SimulationStatisticsResponse:
        """Computes current request pipeline counts."""
        total = db.query(func.count(Request.id)).scalar() or 0
        completed = (
            db.query(func.count(Request.id))
            .filter(Request.request_status == RequestStatus.COMPLETED)
            .scalar()
            or 0
        )
        human_review = (
            db.query(func.count(Request.id))
            .filter(Request.request_status == RequestStatus.HUMAN_REVIEW)
            .scalar()
            or 0
        )
        correction = (
            db.query(func.count(Request.id))
            .filter(Request.request_status == RequestStatus.NEEDS_CORRECTION)
            .scalar()
            or 0
        )
        failed = (
            db.query(func.count(Request.id))
            .filter(Request.request_status.in_([RequestStatus.REJECTED_INPUT, RequestStatus.FAILED]))
            .scalar()
            or 0
        )
        pending = (
            db.query(func.count(Request.id))
            .filter(
                Request.request_status.in_(
                    [
                        RequestStatus.NEW,
                        RequestStatus.CLASSIFIED,
                        RequestStatus.QUEUED,
                        RequestStatus.VERIFIED,
                        RequestStatus.IN_SERVICE,
                    ]
                )
            )
            .scalar()
            or 0
        )

        active_workers = (
            sum(1 for a in simulation_runner.model.get_all_agents() if a.availability_status == "BUSY")
            if simulation_runner.model
            else 0
        )

        return SimulationStatisticsResponse(
            total_requests=total,
            processed_requests=completed,
            pending_requests=pending,
            completed_requests=completed,
            human_review_requests=human_review,
            correction_requests=correction,
            failed_requests=failed,
            active_agents=active_workers,
        )

    @staticmethod
    def run_test_scenario(req: RunTestScenarioRequest, db: Session) -> RunTestScenarioResponse:
        """Executes a benchmark scenario."""
        res = simulation_runner.run_scenario(req.scenario_id, db)
        return RunTestScenarioResponse(**res)

    @staticmethod
    def get_realtime_monitoring_data(db: Session) -> Dict[str, Any]:
        """
        Gathers comprehensive real-time multi-agent telemetry using live Mesa in-memory instances
        and authoritative PostgreSQL event tables.
        Returns actual backend data across all agent pools, assigned requests, pipeline stages,
        communication/assignment/failure events, and high-level metrics.
        """
        if not simulation_runner.model:
            simulation_runner.model = BankingSimulationModel()
            AgentRegistry.sync_agents_to_database(db, simulation_runner.model.get_all_agents())

        model = simulation_runner.model
        is_running = simulation_runner.is_running
        status_indicator = "LIVE" if is_running else "SIMULATION STOPPED"
        now_iso = datetime.now(timezone.utc).isoformat()

        all_agents = model.get_all_agents()
        agent_infos = []

        agent_meta = {
            "AGT-CUST-SIM-01": {"name": "Customer Simulation Agent", "category": "CORE_PIPELINE"},
            "AGT-INTAKE-01": {"name": "Intake & Classification Agent", "category": "CORE_PIPELINE"},
            "AGT-VERIF-01": {"name": "Verification Agent", "category": "CORE_PIPELINE"},
            "AGT-SUPERVISOR-01": {"name": "Supervisor Agent", "category": "SUPERVISOR"},
            "ServiceAgent_CHEQUE_BOOK": {"name": "Service Agent (Cheque Book)", "category": "SERVICE_POOL"},
            "ServiceAgent_DEBIT_CARD": {"name": "Service Agent (Debit Card)", "category": "SERVICE_POOL"},
            "ServiceAgent_ADDRESS": {"name": "Service Agent (Address Update)", "category": "SERVICE_POOL"},
            "ServiceAgent_APPLICATION": {"name": "Service Agent (Account Applications)", "category": "SERVICE_POOL"},
        }

        active_req_ids = [a.current_request_id for a in all_agents if a.current_request_id]
        req_status_map = {}
        if active_req_ids:
            reqs = db.query(Request.request_id, Request.request_status).filter(
                Request.request_id.in_(active_req_ids)
            ).all()
            for r_id, r_st in reqs:
                req_status_map[r_id] = r_st.value if hasattr(r_st, "value") else str(r_st)

        for agt in all_agents:
            code = agt.agent_code
            agt_type = agt.agent_type.value if hasattr(agt.agent_type, "value") else str(agt.agent_type)

            meta = agent_meta.get(code, {})
            if not meta:
                if agt_type == "REQUEST":
                    meta = {"name": f"Request Worker ({code})", "category": "REQUEST_POOL"}
                elif agt_type == "SERVICE":
                    meta = {"name": f"Service Worker ({code})", "category": "SERVICE_POOL"}
                else:
                    meta = {"name": code, "category": "CORE_PIPELINE"}

            health_str = agt.health_status.value if hasattr(agt.health_status, "value") else str(agt.health_status)

            if health_str in ("FAILED", "UNRESPONSIVE"):
                computed_status = "FAILED"
            elif health_str == "RECOVERING":
                computed_status = "RECOVERING"
            elif agt.current_request_id:
                computed_status = "PROCESSING"
            elif agt.availability_status == "BUSY" or agt.processing_status == "BUSY":
                computed_status = "BUSY"
            else:
                computed_status = "IDLE"

            current_req = agt.current_request_id
            if current_req:
                stage = req_status_map.get(current_req, "PROCESSING")
            else:
                stage = "IDLE" if computed_status == "IDLE" else computed_status

            skills = getattr(agt, "supported_skills", []) or []

            agent_infos.append({
                "id": getattr(agt, "db_id", None),
                "agent_code": code,
                "agent_name": meta.get("name", code),
                "agent_type": agt_type,
                "category": meta.get("category", "CORE_PIPELINE"),
                "availability_status": agt.availability_status,
                "health_status": health_str,
                "status": computed_status,
                "current_request_id": current_req,
                "current_stage": stage,
                "completed_tasks": agt.completed_work_count,
                "failed_tasks": getattr(agt, "failed_work_count", 0),
                "last_heartbeat": agt.last_heartbeat_at.isoformat() if getattr(agt, "last_heartbeat_at", None) else None,
                "last_active_at": agt.last_active_at.isoformat() if getattr(agt, "last_active_at", None) else None,
                "supported_skills": list(skills),
            })

        # Pipeline metrics from PostgreSQL
        total_r = db.query(func.count(Request.id)).scalar() or 0
        completed_r = db.query(func.count(Request.id)).filter(Request.request_status == RequestStatus.COMPLETED).scalar() or 0
        failed_r = db.query(func.count(Request.id)).filter(
            Request.request_status.in_([RequestStatus.REJECTED_INPUT, RequestStatus.FAILED])
        ).scalar() or 0
        pending_r = db.query(func.count(Request.id)).filter(
            Request.request_status.in_([
                RequestStatus.NEW,
                RequestStatus.CLASSIFIED,
                RequestStatus.QUEUED,
                RequestStatus.VERIFIED,
                RequestStatus.IN_SERVICE,
            ])
        ).scalar() or 0
        human_r = db.query(func.count(Request.id)).filter(Request.request_status == RequestStatus.HUMAN_REVIEW).scalar() or 0
        correction_r = db.query(func.count(Request.id)).filter(Request.request_status == RequestStatus.NEEDS_CORRECTION).scalar() or 0

        active_workers = sum(1 for a in agent_infos if a["status"] in ("BUSY", "PROCESSING"))
        idle_agents = sum(1 for a in agent_infos if a["status"] == "IDLE")

        metrics = {
            "total_requests": total_r,
            "processed_requests": completed_r,
            "failed_requests": failed_r,
            "pending_requests": pending_r,
            "human_review_requests": human_r,
            "correction_requests": correction_r,
            "active_workers": active_workers,
            "total_agents": len(agent_infos),
            "idle_agents": idle_agents,
        }

        # Event log items
        event_items = []
        db_events = db.query(AgentEvent).order_by(desc(AgentEvent.timestamp)).limit(30).all()
        for ev in db_events:
            ev_type = ev.event_type or "EVENT"
            ts_str = ev.timestamp.isoformat() if ev.timestamp else now_iso

            if ev_type in ("REQUEST_CREATED", "INTAKE_ACCEPTED", "CUSTOMER_CORRECTION_SUBMITTED"):
                cat = "COMMUNICATION"
                sev = "info"
                msg = f"{ev.agent_id} initiated/intake request {ev.request_id}"
            elif ev_type in ("REQUEST_DISPATCHED", "ASSIGNMENT_DISPATCHED"):
                cat = "ASSIGNMENT"
                sev = "info"
                msg = f"Request {ev.request_id} dispatched to {ev.agent_id}"
            elif ev_type in ("VERIFICATION_COMPLETED", "SERVICE_COMPLETED", "REQUEST_COMPLETED"):
                cat = "COMPLETION"
                sev = "success"
                msg = f"Request {ev.request_id} completed stage by {ev.agent_id} ({ev.reason_code or 'Success'})"
            elif ev_type in ("VERIFICATION_FAILED", "REQUEST_REJECTED", "REQUEST_NEEDS_CORRECTION"):
                cat = "COMPLETION"
                sev = "warning"
                msg = f"Request {ev.request_id} exception state: {ev.new_state} ({ev.reason_code})"
            elif ev_type == "HUMAN_REVIEW_REQUIRED":
                cat = "COMMUNICATION"
                sev = "warning"
                msg = f"Request {ev.request_id} escalated to human review by {ev.agent_id}"
            else:
                cat = "COMMUNICATION"
                sev = "info"
                msg = f"{ev.agent_id}: {ev_type} on {ev.request_id}"

            payload_data = ev.payload if isinstance(ev.payload, dict) else {}
            receiver = payload_data.get("receiver_agent_id") or payload_data.get("receiver")

            event_items.append({
                "event_id": ev.event_id,
                "timestamp": ts_str,
                "category": cat,
                "sender": ev.agent_id,
                "receiver": receiver,
                "request_id": ev.request_id,
                "message": msg,
                "severity": sev,
                "details": payload_data,
            })

        db_failures = db.query(AgentFailure).order_by(desc(AgentFailure.created_at)).limit(15).all()
        for f in db_failures:
            ts_str = f.created_at.isoformat() if f.created_at else now_iso
            is_recovered = f.recovery_status == "RECOVERED"
            cat = "RECOVERY" if is_recovered else "FAILURE"
            sev = "success" if is_recovered else ("error" if f.recovery_status == "FAILED" else "warning")
            msg = f"Failure [{f.failure_type}] on {f.agent_code or 'Worker'} - Status: {f.recovery_status}"
            if f.error_details:
                msg += f" ({f.error_details[:60]}...)" if len(f.error_details) > 60 else f" ({f.error_details})"

            event_items.append({
                "event_id": f.failure_id,
                "timestamp": ts_str,
                "category": cat,
                "sender": f.agent_code or "SystemMonitor",
                "receiver": "SupervisorAgent",
                "request_id": f.request_code,
                "message": msg,
                "severity": sev,
                "details": {"retry_count": f.retry_count, "status": f.recovery_status},
            })

        event_items.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "is_running": is_running,
            "status_indicator": status_indicator,
            "current_tick": model.current_tick if model else 0,
            "scenario_name": simulation_runner.scenario_name,
            "timestamp": now_iso,
            "metrics": metrics,
            "agents": agent_infos,
            "events": event_items[:40],
        }
