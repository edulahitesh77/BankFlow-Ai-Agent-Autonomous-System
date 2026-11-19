"""
BankFlow AI - Intake Agent
Validates incoming customer service requests, enforces schema completeness,
classifies service categories, and routes requests to Request Agents via RabbitMQ.
"""

import logging
from typing import Dict, Any, Tuple, Optional
import mesa
from sqlalchemy.orm import Session

from app.models.agent import AgentType
from app.models.request import Request, ServiceType, RequestStatus
from app.agents.base_agent import BaseBankingAgent
from app.simulation.state_machine import transition_request
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher
from app.messaging.notifications import dispatch_customer_notification

logger = logging.getLogger("bankflow_ai.agents.intake")


class IntakeAgent(BaseBankingAgent):
    """
    Intake Agent responsible for intake validation, schema compliance,
    and publishing classified events to the Request Agent Pool.
    """

    def __init__(
        self,
        model: mesa.Model,
        agent_code: str = "AGT-INTAKE-01",
    ):
        super().__init__(model, agent_code, AgentType.INTAKE)

    def validate_request_completeness(self, request: Request) -> Tuple[bool, Optional[str], Optional[RequestStatus]]:
        """
        Validates request fields against strict banking rule sets.
        Returns (is_valid, reason_code, target_status).
        """
        if not request.request_id or not request.service_type:
            return False, "MALFORMED_REQUEST", RequestStatus.REJECTED_INPUT

        payload = request.payload or {}

        # 1. Cheque Book Rules
        if request.service_type == ServiceType.CHEQUE_BOOK:
            acc_ref = request.account_id or payload.get("account_id") or payload.get("account_number")
            leaves = payload.get("number_of_leaves")
            if not acc_ref:
                return False, "MISSING_ACCOUNT_REFERENCE", RequestStatus.NEEDS_CORRECTION
            if leaves not in [25, 50, 100]:
                return False, "INVALID_LEAF_SELECTION", RequestStatus.NEEDS_CORRECTION
            return True, None, RequestStatus.CLASSIFIED

        # 2. Debit Card Replacement Rules
        elif request.service_type == ServiceType.DEBIT_CARD_REPLACEMENT:
            acc_ref = request.account_id or payload.get("account_id") or payload.get("account_number")
            reason = payload.get("replacement_reason")
            valid_reasons = [
                "Damaged Card", "Lost Card (simulation only)", "Other",
                "damaged", "lost", "stolen", "expired"
            ]
            if not acc_ref:
                return False, "MISSING_ACCOUNT_REFERENCE", RequestStatus.NEEDS_CORRECTION
            if not reason or str(reason) not in valid_reasons:
                return False, "INVALID_REPLACEMENT_REASON", RequestStatus.NEEDS_CORRECTION
            if str(reason).lower() in ["lost", "stolen", "lost card (simulation only)"]:
                # High-risk security event: flag for human supervisor review
                return True, "SECURITY_CARD_REPLACEMENT", RequestStatus.HUMAN_REVIEW
            return True, None, RequestStatus.CLASSIFIED

        # 3. Address Update Rules
        elif request.service_type == ServiceType.ADDRESS_UPDATE:
            acc_ref = request.account_id or payload.get("account_id") or payload.get("account_number")
            street = payload.get("new_synthetic_address") or payload.get("street")
            city = payload.get("city")
            state = payload.get("state") or payload.get("state_province")
            postal_code = payload.get("postal_code")

            if not acc_ref:
                return False, "MISSING_ACCOUNT_REFERENCE", RequestStatus.NEEDS_CORRECTION
            if not (street and city and state and postal_code):
                return False, "INCOMPLETE_ADDRESS_FIELDS", RequestStatus.NEEDS_CORRECTION
            return True, None, RequestStatus.CLASSIFIED

        # 4. Account Application Pre-Screening Rules
        elif request.service_type == ServiceType.ACCOUNT_APPLICATION:
            name = payload.get("applicant_name")
            email = payload.get("email")
            acc_type = payload.get("requested_account_type")

            if not (name and email and acc_type):
                return False, "INCOMPLETE_APPLICANT_DETAILS", RequestStatus.NEEDS_CORRECTION
            if "@" not in str(email):
                return False, "MALFORMED_CONTACT_EMAIL", RequestStatus.NEEDS_CORRECTION
            # All account applications are pre-screened and routed for supervisory human concurrence
            return True, "PRE_SCREENING_EVALUATION", RequestStatus.CLASSIFIED

        else:
            return False, "UNSUPPORTED_SERVICE_TYPE", RequestStatus.REJECTED_INPUT

    def process_request(self, db: Session, request: Request) -> Request:
        """Evaluates an incoming request, transitions state, and publishes RabbitMQ events."""
        orig_status = request.request_status.value if hasattr(request.request_status, "value") else str(request.request_status)
        is_valid, reason_code, target_status = self.validate_request_completeness(request)

        if not target_status:
            target_status = RequestStatus.CLASSIFIED if is_valid else RequestStatus.NEEDS_CORRECTION

        # Execute transition through central state machine
        transition_request(
            db=db,
            request=request,
            new_status=target_status,
            agent_code=self.agent_code,
            reason_code=reason_code,
            note="Intake validation and schema compliance check.",
        )

        target_status_val = target_status.value if hasattr(target_status, "value") else str(target_status)

        # --------------------------------------------------------------------
        # Publish RabbitMQ Events & Dispatch Notifications based on Outcome
        # --------------------------------------------------------------------
        if target_status == RequestStatus.CLASSIFIED:
            msg = StandardBankingMessage(
                request_id=request.request_id,
                request_version=request.assignment_version,
                sender_agent_id=self.agent_code,
                receiver_agent_id="RequestAgentPool",
                event_type=BankingEventType.REQUEST_CLASSIFIED,
                reason_code=reason_code,
                payload={"service_type": request.service_type.value if hasattr(request.service_type, "value") else str(request.service_type)},
            )
            MessagePublisher.publish_event(db=db, message=msg, previous_state=orig_status, new_state=target_status_val)

        elif target_status == RequestStatus.NEEDS_CORRECTION:
            msg = StandardBankingMessage(
                request_id=request.request_id,
                request_version=request.assignment_version,
                sender_agent_id=self.agent_code,
                receiver_agent_id=f"CUSTOMER_{request.customer_id}",
                event_type=BankingEventType.REQUEST_NEEDS_CORRECTION,
                reason_code=reason_code,
                payload={"reason": reason_code, "instruction": "Please update and resubmit required fields."},
            )
            MessagePublisher.publish_event(db=db, message=msg, previous_state=orig_status, new_state=target_status_val)
            dispatch_customer_notification(
                db=db,
                request=request,
                title="Action Required: Request Needs Correction",
                message=f"Your request {request.request_id} requires correction: {reason_code}. Please edit and resubmit.",
            )

        elif target_status == RequestStatus.HUMAN_REVIEW:
            msg = StandardBankingMessage(
                request_id=request.request_id,
                request_version=request.assignment_version,
                sender_agent_id=self.agent_code,
                receiver_agent_id="AGT-SUPERVISOR-01",
                event_type=BankingEventType.HUMAN_REVIEW_REQUIRED,
                reason_code=reason_code,
                payload={"security_flag": True, "reason": reason_code},
            )
            MessagePublisher.publish_event(db=db, message=msg, previous_state=orig_status, new_state=target_status_val)
            dispatch_customer_notification(
                db=db,
                request=request,
                title="Supervisory Review Initiated",
                message=f"Request {request.request_id} has been referred for internal supervisory review.",
            )

        elif target_status == RequestStatus.REJECTED_INPUT:
            msg = StandardBankingMessage(
                request_id=request.request_id,
                request_version=request.assignment_version,
                sender_agent_id=self.agent_code,
                receiver_agent_id=f"CUSTOMER_{request.customer_id}",
                event_type=BankingEventType.VERIFICATION_FAILED,
                reason_code=reason_code,
                payload={"reason": reason_code},
            )
            MessagePublisher.publish_event(db=db, message=msg, previous_state=orig_status, new_state=target_status_val)
            dispatch_customer_notification(
                db=db,
                request=request,
                title="Service Request Rejected",
                message=f"Request {request.request_id} was rejected: {reason_code}.",
            )

        self.completed_work_count += 1
        return request
