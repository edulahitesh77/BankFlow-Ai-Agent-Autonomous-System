"""
BankFlow AI - Simulation Runner & Scenario Execution
Provides thread-safe background execution and controlled synthetic test scenarios.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.request import Request, ServiceType, RequestStatus
from app.models.customer import Customer
from app.models.account import Account
from app.models.user import User, UserRole
from app.models.agent import AgentType
from app.auth.security import hash_password
from app.simulation.configuration import SimulationConfig
from app.simulation.model import BankingSimulationModel

logger = logging.getLogger("bankflow_ai.simulation")


class SimulationRunner:
    """
    Singleton controller managing the lifecycle of background Mesa simulations
    and executing controlled benchmark scenarios.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SimulationRunner, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.model: Optional[BankingSimulationModel] = None
        self.is_running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.scenario_name: str = "IDLE"
        self.start_time: Optional[float] = None
        self.execution_logs: List[str] = []

    def get_status(self) -> Dict[str, Any]:
        """Returns current operational status of the simulation."""
        current_tick = self.model.current_tick if self.model else 0
        agents_data = [a.to_dict() for a in self.model.get_all_agents()] if self.model else []

        active_workers = sum(1 for a in agents_data if a["processing_status"] == "BUSY")

        return {
            "is_running": self.is_running,
            "scenario": self.scenario_name,
            "current_tick": current_tick,
            "active_workers": active_workers,
            "total_agents": len(agents_data),
            "agents": agents_data,
            "logs_preview": self.execution_logs[-10:],
        }

    def start(self, config: Optional[SimulationConfig] = None) -> Dict[str, Any]:
        """Starts the background simulation loop safely."""
        with self._lock:
            if self.is_running:
                return {"message": "Simulation is already running.", "is_running": True}

            self.model = BankingSimulationModel(config or SimulationConfig())
            self.is_running = True
            self.scenario_name = self.model.config.scenario_name
            self.start_time = time.time()
            self.execution_logs = [f"Simulation started with {self.model.config.num_request_agents} Request Agents."]

            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

            return {
                "message": "Simulation started successfully.",
                "is_running": True,
                "config": {
                    "num_request_agents": self.model.config.num_request_agents,
                    "tick_delay": self.model.config.tick_delay_seconds,
                },
            }

    def stop(self) -> Dict[str, Any]:
        """Safely signals the simulation loop to terminate."""
        with self._lock:
            if not self.is_running:
                return {"message": "Simulation is not currently running.", "is_running": False}

            self.is_running = False
            self.scenario_name = "STOPPED"
            self.execution_logs.append("Simulation stop signal received.")
            return {"message": "Simulation stop signal acknowledged.", "is_running": False}

    def _run_loop(self) -> None:
        """Internal background loop running simulation ticks against database sessions."""
        logger.info("Simulation background thread active.")
        while self.is_running:
            db: Session = SessionLocal()
            try:
                summary = self.model.step(db)
                if (
                    summary["intake_processed"] > 0
                    or summary["dispatched_to_request_agents"] > 0
                    or summary["verified"] > 0
                    or summary["services_completed"] > 0
                ):
                    log_msg = (
                        f"Tick {summary['tick']}: Intake={summary['intake_processed']}, "
                        f"Dispatched={summary['dispatched_to_request_agents']}, "
                        f"Verified={summary['verified']}, Done={summary['services_completed']} "
                        f"(Active Workers: {summary['active_request_agents']})"
                    )
                    self.execution_logs.append(log_msg)
            except Exception as e:
                logger.error("Error in simulation step: %s", str(e))
                self.execution_logs.append(f"Tick error: {str(e)}")
            finally:
                db.close()

            time.sleep(self.model.config.tick_delay_seconds)

    # ------------------------------------------------------------------------
    # SCENARIOS IMPLEMENTATION (Controlled benchmarks)
    # ------------------------------------------------------------------------

    def run_scenario(self, scenario_id: int, db: Session) -> Dict[str, Any]:
        """
        Executes one of the 5 predefined synthetic scenarios deterministically:
        1: Normal Processing (20 valid requests, 3 Request Agents)
        2: Increased Load (60 valid requests, 5 Request Agents)
        3: Incomplete Requests (requests with missing fields -> NEEDS_CORRECTION)
        4: Mixed Service Types (all 4 service types)
        5: Human Review (inconsistent synthetic records -> HUMAN_REVIEW)
        """
        # Ensure test customer & account exist
        cust, acc = self._ensure_test_customer_and_account(db)

        # Configure scenario parameters
        if scenario_id == 1:
            name = "SCENARIO 1 – Normal Processing"
            num_reqs = 20
            num_agents = 3
            types = [ServiceType.CHEQUE_BOOK, ServiceType.DEBIT_CARD_REPLACEMENT]
            is_valid_list = [True] * num_reqs

        elif scenario_id == 2:
            name = "SCENARIO 2 – Increased Load"
            num_reqs = 60
            num_agents = 5
            types = [ServiceType.CHEQUE_BOOK, ServiceType.DEBIT_CARD_REPLACEMENT, ServiceType.ADDRESS_UPDATE]
            is_valid_list = [True] * num_reqs

        elif scenario_id == 3:
            name = "SCENARIO 3 – Incomplete Requests"
            num_reqs = 20
            num_agents = 3
            types = [ServiceType.CHEQUE_BOOK, ServiceType.ADDRESS_UPDATE]
            # 50% valid, 50% missing required fields
            is_valid_list = [i % 2 == 0 for i in range(num_reqs)]

        elif scenario_id == 4:
            name = "SCENARIO 4 – Mixed Service Types"
            num_reqs = 24
            num_agents = 4
            types = [
                ServiceType.CHEQUE_BOOK,
                ServiceType.DEBIT_CARD_REPLACEMENT,
                ServiceType.ADDRESS_UPDATE,
                ServiceType.ACCOUNT_APPLICATION,
            ]
            is_valid_list = [True] * num_reqs

        elif scenario_id == 5:
            name = "SCENARIO 5 – Human Review Gate"
            num_reqs = 20
            num_agents = 3
            # Mix lost card and account applications which trigger HUMAN_REVIEW
            types = [ServiceType.ACCOUNT_APPLICATION, ServiceType.DEBIT_CARD_REPLACEMENT]
            is_valid_list = [True] * num_reqs

        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        # 1. Initialize clean model with scenario config
        config = SimulationConfig(
            num_request_agents=num_agents,
            tick_delay_seconds=0.01,  # fast for testing
            scenario_name=name,
            random_seed=42,
        )
        test_model = BankingSimulationModel(config)

        # 2. Seed requests into PostgreSQL
        seeded_request_ids = []
        for i in range(num_reqs):
            st = types[i % len(types)]
            valid = is_valid_list[i]

            req_dict = test_model.customer_agent.generate_synthetic_request(
                service_type=st,
                is_valid=valid,
                account_id=acc.id,
                account_number=acc.synthetic_account_number,
            )

            req_code = f"BFA-SIM-{scenario_id}-{int(time.time())}-{str(i+1).zfill(3)}"
            req = Request(
                request_id=req_code,
                customer_id=cust.id,
                account_id=acc.id,
                service_type=st,
                request_status=RequestStatus.NEW,
                priority="HIGH" if scenario_id == 5 else "MEDIUM",
                assignment_version=0,
                payload=req_dict["payload"],
            )
            db.add(req)
            seeded_request_ids.append(req_code)

        db.commit()

        # 3. Step the simulation until all requests exit NEW state
        start_t = time.time()
        max_ticks = 60
        logs = []
        concurrency_snapshots = []

        for tick in range(1, max_ticks + 1):
            tick_res = test_model.step(db)
            active_count = tick_res["active_request_agents"]
            concurrency_snapshots.append(active_count)

            log_entry = (
                f"Tick {tick}: ActiveWorkers={active_count}/{num_agents}, "
                f"Intake={tick_res['intake_processed']}, Verified={tick_res['verified']}, "
                f"Completed={tick_res['services_completed']}"
            )
            logs.append(log_entry)

            # Check if all seeded requests are processed
            pending_in_workflow = (
                db.query(Request)
                .filter(
                    Request.request_id.in_(seeded_request_ids),
                    Request.request_status.in_([
                        RequestStatus.NEW,
                        RequestStatus.CLASSIFIED,
                        RequestStatus.QUEUED,
                        RequestStatus.VERIFIED,
                        RequestStatus.IN_SERVICE,
                    ]),
                )
                .count()
            )
            if pending_in_workflow == 0 and active_count == 0:
                break

        duration = round(time.time() - start_t, 3)

        # 4. Gather final status counts for seeded requests
        final_requests = db.query(Request).filter(Request.request_id.in_(seeded_request_ids)).all()
        status_counts = {}
        for r in final_requests:
            st_name = r.request_status.value if hasattr(r.request_status, "value") else str(r.request_status)
            status_counts[st_name] = status_counts.get(st_name, 0) + 1

        peak_concurrency = max(concurrency_snapshots) if concurrency_snapshots else 0

        return {
            "scenario_id": scenario_id,
            "scenario_name": name,
            "total_requests": num_reqs,
            "request_agents_count": num_agents,
            "duration_seconds": duration,
            "peak_concurrency": peak_concurrency,
            "status_breakdown": status_counts,
            "execution_logs": logs,
        }

    def _ensure_test_customer_and_account(self, db: Session) -> tuple[Customer, Account]:
        """Ensures a synthetic customer and account exist in DB for simulation ingestion."""
        cust = db.query(Customer).filter(Customer.customer_code == "CUST-SYN-00001").first()
        if not cust:
            user = db.query(User).filter(User.username == "sim_customer_01").first()
            if not user:
                user = User(
                    username="sim_customer_01",
                    email="sim_customer@bankflow.synthetic",
                    password_hash=hash_password("SimPass@2026!"),
                    role=UserRole.CUSTOMER,
                    is_active=True,
                )
                db.add(user)
                db.flush()

            cust = Customer(
                user_id=user.id,
                customer_code="CUST-SYN-00001",
                full_name="Synthetic Simulation Customer",
                email="sim_customer@bankflow.synthetic",
                phone="+1-555-0100",
                branch_id="BR-MAIN-001",
            )
            db.add(cust)
            db.flush()

        acc = db.query(Account).filter(Account.customer_id == cust.id).first()
        if not acc:
            acc = Account(
                customer_id=cust.id,
                synthetic_account_number="ACC-SYN-1001",
                account_type="SAVINGS",
                account_status="ACTIVE",
                branch_id="BR-MAIN-001",
            )
            db.add(acc)
            db.flush()

        db.commit()
        return cust, acc


# Global singleton instance
simulation_runner = SimulationRunner()
