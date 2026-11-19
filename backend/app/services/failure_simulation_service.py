"""
BankFlow AI - Failure Simulation and Testing Service (Phase 8)
Supports controlled simulation of agent crashes, missed heartbeats, broker blips,
duplicate messages, and retry exhaustion for development, chaos engineering, and tests.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models.agent import Agent, AgentHealthStatus
from app.models.request import Request, RequestStatus
from app.models.failure_record import FailureType, RecoveryStatus
from app.services.recovery_service import AgentRecoveryService
from app.services.retry_service import RecoveryRetryService
from app.messaging.circuit_breaker import rabbitmq_circuit_breaker
from app.messaging.message_schema import StandardBankingMessage, BankingEventType

logger = logging.getLogger("bankflow_ai.services.failure_simulation")


class FailureSimulationService:
    """
    Simulates operational anomalies and failure scenarios under controlled test settings.
    """

    @staticmethod
    def simulate_agent_crash(
        db: Session,
        agent_code: str,
        reason: str = "Simulated unexpected worker process termination",
    ) -> Dict[str, Any]:
        """Scenario 1 & 6: Crashes an agent, sets status to FAILED, records failure."""
        agent = db.query(Agent).filter(Agent.agent_code == agent_code).first()
        if not agent:
            return {"success": False, "message": f"Agent '{agent_code}' not found"}

        agent.health_status = AgentHealthStatus.FAILED.value
        agent.availability_status = "UNAVAILABLE"
        agent.processing_status = "IDLE"
        agent.last_error_message = reason

        req = None
        if agent.current_request_id:
            req = db.query(Request).filter(Request.id == agent.current_request_id).first()

        failure_rec = AgentRecoveryService.record_failure(
            db=db,
            failure_type=FailureType.CRASH_DURING_EXECUTION,
            error_details=reason,
            agent=agent,
            request=req,
            retry_count=req.retry_count if req else 0,
        )
        db.commit()
        return {
            "success": True,
            "agent_code": agent_code,
            "failure_id": failure_rec.failure_id,
            "status": "FAILED",
            "assigned_request": req.request_id if req else None,
        }

    @staticmethod
    def simulate_missed_heartbeat(
        db: Session,
        agent_code: str,
        seconds_ago: float = 60.0,
    ) -> Dict[str, Any]:
        """Scenario 2: Simulates missed heartbeat by setting last_heartbeat_at back in time."""
        agent = db.query(Agent).filter(Agent.agent_code == agent_code).first()
        if not agent:
            return {"success": False, "message": f"Agent '{agent_code}' not found"}

        stale_time = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
        agent.last_heartbeat_at = stale_time
        agent.last_active_at = stale_time
        db.commit()
        return {
            "success": True,
            "agent_code": agent_code,
            "simulated_last_heartbeat": stale_time.isoformat(),
            "elapsed_seconds": seconds_ago,
        }

    @staticmethod
    def simulate_rabbitmq_outage() -> Dict[str, Any]:
        """Scenario 3: Trips the circuit breaker to simulate RabbitMQ broker outage."""
        rabbitmq_circuit_breaker.trip(reason="Chaos test: Simulated RabbitMQ connection loss")
        return {
            "success": True,
            "circuit_breaker": rabbitmq_circuit_breaker.name,
            "state": rabbitmq_circuit_breaker.state.value,
        }

    @staticmethod
    def simulate_rabbitmq_restore() -> Dict[str, Any]:
        """Scenario 10: Resets the circuit breaker to simulate RabbitMQ broker recovery."""
        rabbitmq_circuit_breaker.reset(reason="Chaos test: RabbitMQ connection re-established")
        return {
            "success": True,
            "circuit_breaker": rabbitmq_circuit_breaker.name,
            "state": rabbitmq_circuit_breaker.state.value,
        }

    @staticmethod
    def simulate_processing_timeout(
        db: Session,
        request_id: str,
    ) -> Dict[str, Any]:
        """Scenario 7: Simulates a request timeout exceeding maximum processing window."""
        req = db.query(Request).filter(Request.request_id == request_id).first()
        if not req:
            return {"success": False, "message": f"Request '{request_id}' not found"}

        # Trigger recovery due to timeout
        recovery_res = AgentRecoveryService.recover_abandoned_task(
            db=db,
            request_id_or_code=req.request_id,
            failure_type=FailureType.PROCESSING_TIMEOUT,
            error_details="Request exceeded maximum processing time limit",
        )
        return {"success": True, "recovery_result": recovery_res}

    @staticmethod
    def simulate_competing_agents(
        db: Session,
        request_id: str,
        agent_codes: List[str],
    ) -> Dict[str, Any]:
        """Scenario 8: Multiple agents attempt to concurrently claim the same request."""
        req = db.query(Request).filter(Request.request_id == request_id).first()
        if not req:
            return {"success": False, "message": f"Request '{request_id}' not found"}

        success_agent = None
        rejected_agents = []

        for code in agent_codes:
            agt = db.query(Agent).filter(Agent.agent_code == code).first()
            if not agt:
                continue

            # Attempt atomic claim
            if req.assigned_agent_id is None:
                req.assigned_agent_id = agt.id
                req.assignment_version += 1
                agt.current_request_id = req.id
                agt.availability_status = "BUSY"
                agt.processing_status = "BUSY"
                success_agent = code
                db.commit()
            else:
                rejected_agents.append(code)

        return {
            "success": True,
            "claimed_by": success_agent,
            "rejected_agents": rejected_agents,
            "assignment_version": req.assignment_version,
        }

    @staticmethod
    def simulate_retry_exhaustion(
        db: Session,
        request_id: str,
    ) -> Dict[str, Any]:
        """Scenario 9: Rapidly exhausts max retries to test escalation to HUMAN_REVIEW."""
        req = db.query(Request).filter(Request.request_id == request_id).first()
        if not req:
            return {"success": False, "message": f"Request '{request_id}' not found"}

        # Artificially set retry count to max
        req.retry_count = settings.RECOVERY_MAX_RETRIES

        recovery_res = AgentRecoveryService.recover_abandoned_task(
            db=db,
            request_id_or_code=req.request_id,
            failure_type=FailureType.REPEATED_PROCESSING_FAILURE,
            error_details="Simulated cascading failure exceeding maximum retry limit",
        )
        return {
            "success": True,
            "request_id": req.request_id,
            "final_status": req.request_status.value if hasattr(req.request_status, "value") else str(req.request_status),
            "review_required": req.review_required,
            "recovery_result": recovery_res,
        }
