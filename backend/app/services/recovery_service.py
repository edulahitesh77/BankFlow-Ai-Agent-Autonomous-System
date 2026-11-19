"""
BankFlow AI - Agent Recovery Service (Phase 8)
Central coordinator for agent health inspection, heartbeat freshness,
failure detection, atomic task reassignment, and supervisor recovery metrics.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.config import settings
from app.models.agent import Agent, AgentType, AgentHealthStatus
from app.models.request import Request, RequestStatus
from app.models.failure_record import AgentFailure, FailureType, RecoveryStatus
from app.services.audit_service import AuditService
from app.services.retry_service import RecoveryRetryService
from app.messaging.circuit_breaker import rabbitmq_circuit_breaker
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher

logger = logging.getLogger("bankflow_ai.services.recovery")


class AgentRecoveryService:
    """
    Orchestrates fault tolerance, failure recording, heartbeat validation,
    and automated/manual recovery workflows for BankFlow AI agents.
    """

    @staticmethod
    def record_failure(
        db: Session,
        failure_type: Union[FailureType, str],
        error_details: str,
        agent: Optional[Agent] = None,
        agent_code: Optional[str] = None,
        request: Optional[Request] = None,
        request_code: Optional[str] = None,
        retry_count: int = 0,
        recovery_status: str = RecoveryStatus.DETECTED.value,
    ) -> AgentFailure:
        """
        Creates an immutable failure record in PostgreSQL with sanitized details.
        """
        failure_type_val = failure_type.value if hasattr(failure_type, "value") else str(failure_type)
        resolved_agent_id = agent.id if agent else None
        resolved_agent_code = agent.agent_code if agent else agent_code
        resolved_request_id = request.id if request else None
        resolved_request_code = request.request_id if request else request_code

        # Sanitize error details to prevent leaking internal stack traces or secrets
        sanitized_error = AuditService.sanitize_description(error_details or "Unspecified execution failure")[:1000]

        failure_rec = AgentFailure(
            failure_id=f"FAIL-{uuid.uuid4().hex[:10].upper()}",
            agent_id=resolved_agent_id,
            agent_code=resolved_agent_code,
            request_id=resolved_request_id,
            request_code=resolved_request_code,
            failure_type=failure_type_val,
            error_details=sanitized_error,
            recovery_status=recovery_status,
            retry_count=retry_count,
        )
        db.add(failure_rec)
        db.flush()

        logger.warning(
            "Failure registered [%s] Type: %s, Agent: %s, Request: %s",
            failure_rec.failure_id,
            failure_type_val,
            resolved_agent_code,
            resolved_request_code,
        )
        return failure_rec

    @staticmethod
    def inspect_agents_health(
        db: Session,
        sim_model: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Inspects all agents for missed heartbeats and processing timeouts.
        Transitions unresponsive agents and triggers automatic request recovery.
        """
        now = datetime.now(timezone.utc)
        agents = db.query(Agent).all()
        unresponsive_count = 0
        timed_out_tasks = 0
        recovered_tasks = 0

        for agt in agents:
            # Skip if agent is paused by administrator
            if agt.is_paused:
                continue

            # 1. Heartbeat Freshness Check
            last_hb = agt.last_heartbeat_at or agt.last_active_at
            if last_hb:
                if last_hb.tzinfo is None:
                    last_hb = last_hb.replace(tzinfo=timezone.utc)
                elapsed_hb = (now - last_hb).total_seconds()

                if elapsed_hb > settings.AGENT_HEARTBEAT_TIMEOUT_SECONDS:
                    if agt.health_status != AgentHealthStatus.UNRESPONSIVE.value:
                        agt.health_status = AgentHealthStatus.UNRESPONSIVE.value
                        unresponsive_count += 1
                        AgentRecoveryService.record_failure(
                            db=db,
                            agent=agt,
                            failure_type=FailureType.UNRESPONSIVE_HEARTBEAT,
                            error_details=f"Agent '{agt.agent_code}' missed heartbeats for {round(elapsed_hb, 1)}s (timeout threshold: {settings.AGENT_HEARTBEAT_TIMEOUT_SECONDS}s).",
                        )

            # 2. Abandoned or Timed-out Task Check
            if agt.current_request_id:
                req = db.query(Request).filter(Request.id == agt.current_request_id).first()
                if req and req.request_status in (RequestStatus.QUEUED, RequestStatus.IN_SERVICE, RequestStatus.CLASSIFIED):
                    # Check if agent is UNRESPONSIVE or FAILED
                    if agt.health_status in (AgentHealthStatus.UNRESPONSIVE.value, AgentHealthStatus.FAILED.value):
                        recovery_res = AgentRecoveryService.recover_abandoned_task(
                            db=db,
                            request_id_or_code=req.request_id,
                            failed_agent_code=agt.agent_code,
                            failure_type=FailureType.UNRESPONSIVE_HEARTBEAT,
                            error_details=f"Agent '{agt.agent_code}' became unresponsive while processing request.",
                            sim_model=sim_model,
                        )
                        if recovery_res.get("status") in ("REASSIGNED", "QUEUED_FOR_RECOVERY", "ESCALATED"):
                            recovered_tasks += 1

        db.commit()
        return {
            "unresponsive_detected": unresponsive_count,
            "timed_out_tasks": timed_out_tasks,
            "recovered_tasks": recovered_tasks,
            "inspected_at": now.isoformat(),
        }

    @staticmethod
    def recover_abandoned_task(
        db: Session,
        request_id_or_code: str,
        failed_agent_code: Optional[str] = None,
        failure_type: Union[FailureType, str] = FailureType.CRASH_DURING_EXECUTION,
        error_details: str = "Agent failed during execution",
        sim_model: Optional[Any] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes automatic recovery workflow:
        1. Atomic verification of request state.
        2. Release abandoned assignment and increment assignment_version to prevent stale completion.
        3. Check retry policy (exponential backoff / max retries).
        4. Reassign to another healthy eligible agent or place in queue.
        5. Publish RabbitMQ event and record audit log.
        """
        failure_type_val = failure_type.value if hasattr(failure_type, "value") else str(failure_type)

        # 1. Resolve request
        req = (
            db.query(Request)
            .filter((Request.request_id == request_id_or_code) | (Request.id == request_id_or_code if request_id_or_code.isdigit() else False))
            .with_for_update()
            .first()
        )
        if not req:
            return {"status": "NOT_FOUND", "message": f"Request '{request_id_or_code}' not found"}

        # If already completed or rejected, do not alter
        if req.request_status in (RequestStatus.COMPLETED, RequestStatus.REJECTED_INPUT):
            return {
                "status": "ALREADY_TERMINAL",
                "message": f"Request '{req.request_id}' is already in terminal state '{req.request_status}'.",
            }

        # 2. Resolve failed agent
        old_agent = None
        if failed_agent_code:
            old_agent = db.query(Agent).filter(Agent.agent_code == failed_agent_code).first()
        elif req.assigned_agent_id:
            old_agent = db.query(Agent).filter(Agent.id == req.assigned_agent_id).first()

        # 3. Check retry policy eligibility
        if not RecoveryRetryService.can_retry_request(req, error_details):
            failure_rec = AgentRecoveryService.record_failure(
                db=db,
                failure_type=FailureType.REPEATED_PROCESSING_FAILURE,
                error_details=error_details,
                agent=old_agent,
                request=req,
                retry_count=req.retry_count,
                recovery_status=RecoveryStatus.ESCALATED_TO_HUMAN.value,
            )
            RecoveryRetryService.escalate_to_human_intervention(
                db=db,
                request=req,
                failure_record=failure_rec,
                reason=f"Exceeded max retries or permanent error: {error_details}",
                user_id=user_id,
            )
            # Release failed agent
            if old_agent and old_agent.current_request_id == req.id:
                old_agent.current_request_id = None
                old_agent.availability_status = "AVAILABLE"
                old_agent.health_status = AgentHealthStatus.RECOVERING.value
            db.commit()
            return {
                "status": "ESCALATED",
                "request_id": req.request_id,
                "message": "Retry limit reached. Escalated to HUMAN_REVIEW.",
                "retry_count": req.retry_count,
            }

        # 4. Increment retry count and assignment version (invalidates stale agent)
        req.retry_count += 1
        req.assignment_version += 1
        req.last_recovery_at = datetime.now(timezone.utc)
        req.recovery_reason = f"Recovered after {failure_type_val}: {error_details[:100]}"

        # Unbind failed agent
        if old_agent:
            if old_agent.current_request_id == req.id:
                old_agent.current_request_id = None
            old_agent.health_status = AgentHealthStatus.RECOVERING.value
            old_agent.availability_status = "AVAILABLE"
            old_agent.processing_status = "IDLE"

        # Record failure event in registry
        failure_rec = AgentRecoveryService.record_failure(
            db=db,
            failure_type=failure_type_val,
            error_details=error_details,
            agent=old_agent,
            request=req,
            retry_count=req.retry_count,
            recovery_status=RecoveryStatus.RECOVERING.value,
        )

        # 5. Search for a healthy, available replacement Request Agent
        eligible_agent = (
            db.query(Agent)
            .filter(
                Agent.agent_type == AgentType.REQUEST,
                Agent.availability_status == "AVAILABLE",
                Agent.processing_status == "IDLE",
                Agent.health_status.in_([AgentHealthStatus.HEALTHY.value, AgentHealthStatus.IDLE.value]),
                Agent.is_paused == False,
                Agent.current_request_id == None,
            )
            .order_by(Agent.completed_work_count.asc())
            .first()
        )

        if eligible_agent:
            # Reassign request to healthy replacement
            req.assigned_agent_id = eligible_agent.id
            req.request_status = RequestStatus.QUEUED
            eligible_agent.current_request_id = req.id
            eligible_agent.availability_status = "BUSY"
            eligible_agent.processing_status = "BUSY"
            eligible_agent.health_status = AgentHealthStatus.BUSY.value
            eligible_agent.last_active_at = datetime.now(timezone.utc)

            failure_rec.recovery_status = RecoveryStatus.RECOVERED.value
            failure_rec.recovered_at = datetime.now(timezone.utc)

            # Sync in-memory Mesa model if available
            if sim_model:
                for a in getattr(sim_model, "agents", []):
                    if getattr(a, "agent_code", None) == eligible_agent.agent_code:
                        try:
                            a.assign_request(req.request_id, req.assignment_version)
                        except Exception:
                            pass
                    elif old_agent and getattr(a, "agent_code", None) == old_agent.agent_code:
                        try:
                            a.release_request(increment_completed=False)
                            a.health_status = AgentHealthStatus.RECOVERING
                        except Exception:
                            pass

            # Publish reassignment event over RabbitMQ
            try:
                msg = StandardBankingMessage(
                    request_id=req.request_id,
                    request_version=req.assignment_version,
                    sender_agent_id="AGT-SUPERVISOR-01",
                    receiver_agent_id=eligible_agent.agent_code,
                    event_type=BankingEventType.SUPERVISOR_ALERT,
                    reason_code="REQUEST_REASSIGNED_AFTER_FAILURE",
                    payload={
                        "previous_agent": old_agent.agent_code if old_agent else None,
                        "new_agent": eligible_agent.agent_code,
                        "retry_count": req.retry_count,
                        "assignment_version": req.assignment_version,
                        "failure_type": failure_type_val,
                    },
                )
                MessagePublisher.publish_event(
                    db=db,
                    message=msg,
                    previous_state="FAILED",
                    new_state="QUEUED",
                    routing_key="supervisor.recovery",
                )
            except Exception as broker_err:
                logger.warning("RabbitMQ notification deferred during recovery: %s", str(broker_err))

            AuditService.record_event(
                db=db,
                action="REQUEST_AUTOMATICALLY_RECOVERED",
                outcome="SUCCESS",
                user_id=user_id,
                request_id=req.request_id,
                description=f"Request {req.request_id} reallocated from {old_agent.agent_code if old_agent else 'None'} to {eligible_agent.agent_code} (Version: {req.assignment_version}, Attempt: {req.retry_count}).",
            )
            db.commit()
            return {
                "status": "REASSIGNED",
                "request_id": req.request_id,
                "reassigned_to": eligible_agent.agent_code,
                "assignment_version": req.assignment_version,
                "retry_count": req.retry_count,
            }
        else:
            # No eligible agent available right now; keep in QUEUED state for scheduler to pick up
            req.assigned_agent_id = None
            req.request_status = RequestStatus.QUEUED
            failure_rec.recovery_status = RecoveryStatus.RECOVERING.value

            AuditService.record_event(
                db=db,
                action="REQUEST_QUEUED_FOR_RECOVERY",
                outcome="SUCCESS",
                user_id=user_id,
                request_id=req.request_id,
                description=f"Request {req.request_id} queued for recovery. No idle agents currently available (Version: {req.assignment_version}, Attempt: {req.retry_count}).",
            )
            db.commit()
            return {
                "status": "QUEUED_FOR_RECOVERY",
                "request_id": req.request_id,
                "assignment_version": req.assignment_version,
                "retry_count": req.retry_count,
                "message": "All agents busy. Request placed in QUEUED state awaiting worker.",
            }

    @staticmethod
    def manual_retry_task(
        db: Session,
        request_id: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Manually re-triggers recovery on an eligible failed or human-review task.
        """
        req = db.query(Request).filter(Request.request_id == request_id).first()
        if not req:
            return {"success": False, "message": f"Request '{request_id}' not found"}

        if req.request_status == RequestStatus.COMPLETED:
            return {"success": False, "message": "Cannot retry an already completed request"}

        # Reset retry counter for manual intervention if requested
        req.retry_count = 0
        req.review_required = False

        res = AgentRecoveryService.recover_abandoned_task(
            db=db,
            request_id_or_code=req.request_id,
            failure_type=FailureType.MANUAL_INTERVENTION_REQUIRED,
            error_details="Manual retry triggered by authorized staff",
            user_id=user_id,
        )

        AuditService.record_event(
            db=db,
            action="MANUAL_RECOVERY_RETRY",
            outcome="SUCCESS",
            user_id=user_id,
            request_id=req.request_id,
            description=f"Staff user {user_id} triggered manual retry for request {req.request_id}.",
        )
        return {"success": True, "recovery_result": res}

    @staticmethod
    def manual_reassign_task(
        db: Session,
        request_id: str,
        target_agent_code: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Manually reassigns a service request to a specific healthy agent.
        """
        req = db.query(Request).filter(Request.request_id == request_id).with_for_update().first()
        if not req:
            return {"success": False, "message": f"Request '{request_id}' not found"}

        target_agent = db.query(Agent).filter(Agent.agent_code == target_agent_code).first()
        if not target_agent:
            return {"success": False, "message": f"Target agent '{target_agent_code}' not found"}

        if target_agent.is_paused or target_agent.health_status == AgentHealthStatus.FAILED.value:
            return {"success": False, "message": f"Target agent '{target_agent_code}' is paused or failed"}

        # Release previous agent if bound
        if req.assigned_agent_id:
            prev_agent = db.query(Agent).filter(Agent.id == req.assigned_agent_id).first()
            if prev_agent and prev_agent.current_request_id == req.id:
                prev_agent.current_request_id = None
                prev_agent.availability_status = "AVAILABLE"
                prev_agent.processing_status = "IDLE"

        req.assigned_agent_id = target_agent.id
        req.assignment_version += 1
        req.request_status = RequestStatus.QUEUED
        req.last_recovery_at = datetime.now(timezone.utc)
        req.recovery_reason = f"Manually reassigned to {target_agent_code}"

        target_agent.current_request_id = req.id
        target_agent.availability_status = "BUSY"
        target_agent.processing_status = "BUSY"
        target_agent.health_status = AgentHealthStatus.BUSY.value

        AuditService.record_event(
            db=db,
            action="MANUAL_REQUEST_REASSIGNED",
            outcome="SUCCESS",
            user_id=user_id,
            request_id=req.request_id,
            description=f"Staff user {user_id} manually reassigned request {req.request_id} to agent {target_agent_code} (Version: {req.assignment_version}).",
        )
        db.commit()
        return {
            "success": True,
            "request_id": req.request_id,
            "assigned_to": target_agent_code,
            "assignment_version": req.assignment_version,
        }

    @staticmethod
    def reset_agent_health(
        db: Session,
        agent_code: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Resets an agent's status back to HEALTHY and AVAILABLE.
        """
        agent = db.query(Agent).filter(Agent.agent_code == agent_code).first()
        if not agent:
            return {"success": False, "message": f"Agent '{agent_code}' not found"}

        agent.health_status = AgentHealthStatus.HEALTHY.value
        agent.availability_status = "AVAILABLE"
        agent.processing_status = "IDLE"
        agent.last_error_message = None
        agent.last_heartbeat_at = datetime.now(timezone.utc)
        agent.last_active_at = datetime.now(timezone.utc)
        agent.current_request_id = None
        agent.is_paused = False

        AuditService.record_event(
            db=db,
            action="AGENT_HEALTH_RESET",
            outcome="SUCCESS",
            user_id=user_id,
            description=f"Staff user {user_id} manually reset health for agent '{agent_code}' to HEALTHY.",
        )
        db.commit()
        return {"success": True, "agent_code": agent_code, "status": "HEALTHY"}

    @staticmethod
    def set_agent_pause_state(
        db: Session,
        agent_code: str,
        is_paused: bool,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Pauses or resumes an agent worker.
        """
        agent = db.query(Agent).filter(Agent.agent_code == agent_code).first()
        if not agent:
            return {"success": False, "message": f"Agent '{agent_code}' not found"}

        agent.is_paused = is_paused
        action_name = "AGENT_PAUSED" if is_paused else "AGENT_RESUMED"

        AuditService.record_event(
            db=db,
            action=action_name,
            outcome="SUCCESS",
            user_id=user_id,
            description=f"Staff user {user_id} set pause={is_paused} for agent '{agent_code}'.",
        )
        db.commit()
        return {"success": True, "agent_code": agent_code, "is_paused": is_paused}

    @staticmethod
    def get_recovery_dashboard_metrics(db: Session) -> Dict[str, Any]:
        """
        Aggregates operational reliability, failure counts, and recovery telemetry.
        """
        agents = db.query(Agent).all()
        total_agents = len(agents)
        healthy = sum(1 for a in agents if a.health_status == AgentHealthStatus.HEALTHY.value)
        busy = sum(1 for a in agents if a.health_status == AgentHealthStatus.BUSY.value)
        unresponsive = sum(1 for a in agents if a.health_status == AgentHealthStatus.UNRESPONSIVE.value)
        failed = sum(1 for a in agents if a.health_status == AgentHealthStatus.FAILED.value)
        recovering = sum(1 for a in agents if a.health_status == AgentHealthStatus.RECOVERING.value)

        # Request recovery metrics
        awaiting_recovery = (
            db.query(func.count(Request.id))
            .filter(
                Request.request_status.in_([RequestStatus.QUEUED, RequestStatus.CLASSIFIED]),
                Request.retry_count > 0,
            )
            .scalar() or 0
        )
        recovered_count = (
            db.query(func.count(AgentFailure.id))
            .filter(AgentFailure.recovery_status == RecoveryStatus.RECOVERED.value)
            .scalar() or 0
        )
        human_intervention_needed = (
            db.query(func.count(Request.id))
            .filter(Request.request_status == RequestStatus.HUMAN_REVIEW)
            .scalar() or 0
        )
        total_failures = db.query(func.count(AgentFailure.id)).scalar() or 0

        # Recent failure events
        recent_failures = (
            db.query(AgentFailure)
            .order_by(desc(AgentFailure.created_at))
            .limit(10)
            .all()
        )

        return {
            "agents_summary": {
                "total": total_agents,
                "healthy": healthy,
                "busy": busy,
                "unresponsive": unresponsive,
                "failed": failed,
                "recovering": recovering,
            },
            "requests_summary": {
                "awaiting_recovery": awaiting_recovery,
                "successfully_recovered": recovered_count,
                "human_intervention_needed": human_intervention_needed,
                "total_failures_recorded": total_failures,
            },
            "circuit_breaker": rabbitmq_circuit_breaker.get_status(),
            "recent_failures": [
                {
                    "failure_id": f.failure_id,
                    "agent_code": f.agent_code,
                    "request_code": f.request_code,
                    "failure_type": f.failure_type,
                    "error_details": f.error_details,
                    "recovery_status": f.recovery_status,
                    "retry_count": f.retry_count,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "recovered_at": f.recovered_at.isoformat() if f.recovered_at else None,
                }
                for f in recent_failures
            ],
        }
