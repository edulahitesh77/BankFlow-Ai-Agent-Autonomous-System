"""
BankFlow AI - Service Agent
Simulates backend fulfillment execution for verified customer banking requests.
Publishes processing start and completion events to RabbitMQ and notifies customers.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
import mesa
from sqlalchemy.orm import Session

from app.models.agent import AgentType
from app.models.request import Request, ServiceType, RequestStatus
from app.agents.base_agent import BaseBankingAgent
from app.simulation.state_machine import transition_request
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher
from app.messaging.notifications import dispatch_customer_notification

logger = logging.getLogger("bankflow_ai.agents.service")


class ServiceAgent(BaseBankingAgent):
    """
    Service Agent simulating banking service fulfillment.
    Accepts only VERIFIED requests matching its supported skills.
    """

    def __init__(
        self,
        model: mesa.Model,
        agent_code: str = "ServiceAgent_CHEQUE_BOOK",
        supported_skills: Optional[List[str]] = None,
    ):
        super().__init__(model, agent_code, AgentType.SERVICE)
        self.supported_skills = supported_skills or ["CHEQUE_BOOK"]

    def can_handle_service(self, service_type: ServiceType) -> bool:
        """Checks if the service agent has the skill required for the request."""
        val = service_type.value if hasattr(service_type, "value") else str(service_type)
        return val in self.supported_skills or "ALL" in self.supported_skills

    def execute_service(self, db: Session, request: Request) -> Request:
        """
        Executes simulated fulfillment:
        1. Transitions to IN_SERVICE and publishes SERVICE_STARTED.
        2. Simulates dispatch/generation.
        3. Transitions to COMPLETED and publishes SERVICE_COMPLETED.
        """
        if request.request_status != RequestStatus.VERIFIED:
            raise ValueError(
                f"Service agent '{self.agent_code}' can only accept VERIFIED requests, got '{request.request_status}'."
            )

        if not self.can_handle_service(request.service_type):
            raise ValueError(
                f"Service agent '{self.agent_code}' with skills {self.supported_skills} cannot process '{request.service_type}'."
            )

        orig_status = request.request_status.value if hasattr(request.request_status, "value") else str(request.request_status)
        self.assign_request(request.request_id, version=request.assignment_version)

        # 1. Transition to IN_SERVICE
        transition_request(
            db=db,
            request=request,
            new_status=RequestStatus.IN_SERVICE,
            agent_code=self.agent_code,
            reason_code="SERVICE_PROCESSING_STARTED",
            note=f"Simulated execution initiated by '{self.agent_code}'.",
        )

        # Publish SERVICE_STARTED event
        msg_started = StandardBankingMessage(
            request_id=request.request_id,
            request_version=request.assignment_version,
            sender_agent_id=self.agent_code,
            receiver_agent_id="AGT-SUPERVISOR-01",
            event_type=BankingEventType.SERVICE_STARTED,
            payload={
                "service_agent": self.agent_code,
                "service_type": request.service_type.value if hasattr(request.service_type, "value") else str(request.service_type),
            },
        )
        MessagePublisher.publish_event(db=db, message=msg_started, previous_state=orig_status, new_state="IN_SERVICE")

        # 2. Simulated fulfillment logic
        payload = request.payload or {}
        fulfillment_record = {
            "fulfilled_by": self.agent_code,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "simulation_notice": "Educational simulation only. No physical instruments or real accounts modified.",
        }

        if request.service_type == ServiceType.CHEQUE_BOOK:
            fulfillment_record["dispatch_tracking_number"] = f"SYN-POST-{request.request_id}"
            fulfillment_record["leaves_dispatched"] = payload.get("number_of_leaves", 25)

        elif request.service_type == ServiceType.DEBIT_CARD_REPLACEMENT:
            fulfillment_record["synthetic_card_reference"] = f"SYN-CARD-{request.request_id[-5:]}"

        elif request.service_type == ServiceType.ADDRESS_UPDATE:
            fulfillment_record["ledger_record_updated"] = True

        elif request.service_type == ServiceType.ACCOUNT_APPLICATION:
            # Pre-screening completion
            fulfillment_record["pre_screening_completed"] = True

        # Append fulfillment metadata to payload
        updated_payload = dict(payload)
        updated_payload["fulfillment_data"] = fulfillment_record
        request.payload = updated_payload

        # 3. Transition to COMPLETED
        transition_request(
            db=db,
            request=request,
            new_status=RequestStatus.COMPLETED,
            agent_code=self.agent_code,
            reason_code="SERVICE_FULFILLED",
            note="Simulated fulfillment completed successfully.",
        )

        # Publish SERVICE_COMPLETED event
        msg_completed = StandardBankingMessage(
            request_id=request.request_id,
            request_version=request.assignment_version,
            sender_agent_id=self.agent_code,
            receiver_agent_id="AGT-SUPERVISOR-01",
            event_type=BankingEventType.SERVICE_COMPLETED,
            payload={
                "service_agent": self.agent_code,
                "fulfillment_data": fulfillment_record,
            },
        )
        MessagePublisher.publish_event(db=db, message=msg_completed, previous_state="IN_SERVICE", new_state="COMPLETED")

        # Notify Customer
        dispatch_customer_notification(
            db=db,
            request=request,
            title="Service Request Completed",
            message=f"Your request {request.request_id} has been successfully processed and fulfilled.",
        )

        # Release agent
        self.release_request(increment_completed=True)
        return request
