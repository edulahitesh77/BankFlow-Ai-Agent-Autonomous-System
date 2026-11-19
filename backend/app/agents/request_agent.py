"""
BankFlow AI - Request Agent
Core concurrent worker agent owning and orchestrating individual customer request versions.
Exchanges structured messages over RabbitMQ for assignment, acceptance, and heartbeats.
"""

import logging
from typing import Optional
from datetime import datetime, timezone
import mesa
from sqlalchemy.orm import Session

from app.models.agent import AgentType
from app.models.request import Request, RequestStatus
from app.agents.base_agent import BaseBankingAgent
from app.simulation.state_machine import transition_request
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher

logger = logging.getLogger("bankflow_ai.agents.request")


class RequestAgent(BaseBankingAgent):
    """
    Request Agent worker instance.
    Maintains exclusive ownership of an individual request version during processing.
    """

    def __init__(
        self,
        model: mesa.Model,
        agent_code: str = "RequestAgent_1",
    ):
        super().__init__(model, agent_code, AgentType.REQUEST)
        self.assigned_at: Optional[datetime] = None

    def accept_and_queue_request(self, db: Session, request: Request) -> Request:
        """
        Accepts assignment of a CLASSIFIED request, transitions state to QUEUED,
        marks this agent instance as BUSY, and publishes REQUEST_ASSIGNED and REQUEST_ACCEPTED.
        """
        orig_status = request.request_status.value if hasattr(request.request_status, "value") else str(request.request_status)
        self.assign_request(request.request_id, version=request.assignment_version)
        self.assigned_at = datetime.now(timezone.utc)

        # Update Request entity in DB
        request.assigned_agent_id = getattr(self, "db_id", None)
        request.priority = request.priority or "MEDIUM"

        transition_request(
            db=db,
            request=request,
            new_status=RequestStatus.QUEUED,
            agent_code=self.agent_code,
            reason_code="AGENT_ASSIGNED",
            note=f"Assigned to worker '{self.agent_code}'.",
        )

        # 1. Publish REQUEST_ASSIGNED event
        msg_assigned = StandardBankingMessage(
            request_id=request.request_id,
            request_version=request.assignment_version,
            sender_agent_id="WorkloadScheduler",
            receiver_agent_id=self.agent_code,
            event_type=BankingEventType.REQUEST_ASSIGNED,
            payload={
                "worker": self.agent_code,
                "service_type": request.service_type.value if hasattr(request.service_type, "value") else str(request.service_type),
            },
        )
        MessagePublisher.publish_event(db=db, message=msg_assigned, previous_state=orig_status, new_state="QUEUED")

        # 2. Publish REQUEST_ACCEPTED event to Verification Agent
        msg_accepted = StandardBankingMessage(
            request_id=request.request_id,
            request_version=request.assignment_version,
            sender_agent_id=self.agent_code,
            receiver_agent_id="AGT-VERIF-01",
            event_type=BankingEventType.REQUEST_ACCEPTED,
            payload={
                "worker": self.agent_code,
                "account_id": request.account_id,
            },
        )
        MessagePublisher.publish_event(db=db, message=msg_accepted, previous_state="QUEUED", new_state="QUEUED")

        # Broadcast UNAVAILABLE since worker is now busy
        self.emit_availability(db, is_available=False)

        return request

    def complete_and_release(self, db: Session, request: Request, final_status: RequestStatus = RequestStatus.COMPLETED) -> None:
        """
        Releases ownership of the request and returns the agent back to IDLE / AVAILABLE.
        Protects against stale agents completing tasks that were already reassigned.
        """
        if self.assigned_version < request.assignment_version:
            logger.warning(
                "Stale worker '%s' (assigned ver: %s) attempted to complete request '%s' (current DB ver: %s). Operation rejected.",
                self.agent_code,
                self.assigned_version,
                request.request_id,
                request.assignment_version,
            )
            self.release_request(increment_completed=False)
            self.assigned_at = None
            self.emit_availability(db, is_available=True)
            return

        self.release_request(increment_completed=True)
        self.assigned_at = None

        # Broadcast worker availability
        self.emit_availability(db, is_available=True)

    def emit_heartbeat(self, db: Session) -> StandardBankingMessage:
        """Emits an AGENT_HEARTBEAT message to the supervisor queue."""
        self.last_active_at = datetime.now(timezone.utc)
        msg = StandardBankingMessage(
            request_id=self.current_request_id or "HEARTBEAT",
            request_version=self.assigned_version,
            sender_agent_id=self.agent_code,
            receiver_agent_id="AGT-SUPERVISOR-01",
            event_type=BankingEventType.AGENT_HEARTBEAT,
            payload={
                "agent_type": self.agent_type.value if hasattr(self.agent_type, "value") else str(self.agent_type),
                "availability": self.availability_status,
                "processing_status": self.processing_status,
                "completed_tasks": self.completed_work_count,
            },
        )
        return MessagePublisher.publish_event(db=db, message=msg)

    def emit_availability(self, db: Session, is_available: bool) -> StandardBankingMessage:
        """Broadcasts AGENT_AVAILABLE or AGENT_UNAVAILABLE state change."""
        self.last_active_at = datetime.now(timezone.utc)
        evt_type = BankingEventType.AGENT_AVAILABLE if is_available else BankingEventType.AGENT_UNAVAILABLE
        msg = StandardBankingMessage(
            request_id="AVAILABILITY_STATE",
            request_version=0,
            sender_agent_id=self.agent_code,
            receiver_agent_id="WorkloadScheduler",
            event_type=evt_type,
            payload={
                "availability": "AVAILABLE" if is_available else "BUSY",
                "current_request_id": self.current_request_id,
            },
        )
        return MessagePublisher.publish_event(db=db, message=msg)
