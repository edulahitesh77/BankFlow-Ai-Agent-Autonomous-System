"""
BankFlow AI - Agent and Simulation Service
Business logic powering agent inspection, simulation control, and benchmark scenario execution.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.agent import Agent as DBAgent
from app.models.request import Request, RequestStatus
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
