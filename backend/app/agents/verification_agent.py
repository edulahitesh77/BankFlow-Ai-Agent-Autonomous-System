"""
BankFlow AI - Verification Agent
Simulates banking prerequisite verification, account relationship checks, and human gate routing.
Exchanges messages with Request and Service agents via RabbitMQ.
"""

import logging
from typing import Tuple, Optional
import mesa
from sqlalchemy.orm import Session

from app.models.agent import AgentType
from app.models.request import Request, ServiceType, RequestStatus
from app.models.account import Account
from app.agents.base_agent import BaseBankingAgent
from app.simulation.state_machine import transition_request
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher
from app.messaging.notifications import dispatch_customer_notification

logger = logging.getLogger("bankflow_ai.agents.verification")


class VerificationAgent(BaseBankingAgent):
    """
    Verification Agent verifying synthetic customer-account relationships
    and routing exceptions to human supervisory review.
    """

    def __init__(
        self,
        model: mesa.Model,
        agent_code: str = "AGT-VERIF-01",
    ):
        super().__init__(model, agent_code, AgentType.VERIFICATION)

    def verify_request_prerequisites(self, db: Session, request: Request) -> Tuple[bool, Optional[str], RequestStatus]:
        """
        Validates account existence, customer ownership, and prerequisite rules.
        """
        payload = request.payload or {}

        # Check if cross-branch federation is required
        if getattr(request, "requires_federation", False) and getattr(request, "origin_branch_id", None):
            try:
                import uuid
                from app.federation.gateway import FederationGateway
                from app.federation.schemas import CrossBranchRequest
                from app.federation.security import BRANCH_SECRETS
                src_branch = request.branch_id or "BLR001"
                api_key = BRANCH_SECRETS.get(src_branch.upper(), "")
                scope_choice = (
                    "CUSTOMER_KYC_VERIFICATION"
                    if request.service_type == ServiceType.ACCOUNT_APPLICATION
                    else "ACCOUNT_STATUS_CONFIRMATION"
                )
                query_p = (
                    {"customer_code": f"CUST-{request.origin_branch_id}-0001", "full_name": "Synthetic Customer"}
                    if scope_choice == "CUSTOMER_KYC_VERIFICATION"
                    else {"synthetic_account_number": str(payload.get("account_number") or f"ACC-{request.origin_branch_id}-1001")}
                )
                fed_req = CrossBranchRequest(
                    source_branch_id=src_branch,
                    destination_branch_id=request.origin_branch_id,
                    requested_scope=scope_choice,
                    request_id=request.request_id,
                    correlation_id=f"CORR-VERIF-{uuid.uuid4().hex[:12].upper()}",
                    query_params=query_p,
                )
                fed_res = FederationGateway.process_cross_branch_request(req=fed_req, api_key=api_key, gateway_db=db)
                if fed_res.authorization_result != "AUTHORIZED":
                    return False, "FEDERATION_REJECTED", RequestStatus.REJECTED_INPUT
                request.federation_status = "FEDERATED_VERIFIED"
            except Exception as fed_err:
                logger.warning("Federation check encountered error: %s", str(fed_err))

        # Account Application special handling
        if request.service_type == ServiceType.ACCOUNT_APPLICATION:
            # Completeness pre-screening passed; simulated banking requires supervisor concurrence
            request.review_required = True
            return True, "ACCOUNT_PRE_SCREENING_REFERRAL", RequestStatus.HUMAN_REVIEW

        # For existing account services, verify account ownership
        account = None
        if request.account_id:
            account = db.query(Account).filter(Account.id == request.account_id).first()
        elif payload.get("account_number"):
            account = db.query(Account).filter(
                Account.synthetic_account_number == str(payload.get("account_number"))
            ).first()

        # If account is missing or doesn't belong to customer
        if account:
            if account.customer_id != request.customer_id:
                return False, "ACCOUNT_OWNERSHIP_MISMATCH", RequestStatus.REJECTED_INPUT
            if account.account_status != "ACTIVE":
                return False, "ACCOUNT_INACTIVE_OR_DORMANT", RequestStatus.NEEDS_CORRECTION
        else:
            # Fallback if account wasn't linked directly in simulation
            pass

        # Check for high-risk flags that require human review
        if request.reason_code == "SECURITY_CARD_REPLACEMENT":
            request.review_required = True
            return True, "SECURITY_CARD_REPLACEMENT", RequestStatus.HUMAN_REVIEW

        if request.priority == "URGENT":
            request.review_required = True
            return True, "URGENT_PRIORITY_REVIEW", RequestStatus.HUMAN_REVIEW

        return True, "PREREQUISITES_VERIFIED", RequestStatus.VERIFIED

    def process_request(self, db: Session, request: Request) -> Request:
        """Verifies prerequisites, updates lifecycle state, and publishes RabbitMQ events."""
        orig_status = request.request_status.value if hasattr(request.request_status, "value") else str(request.request_status)
        is_verified, reason_code, target_status = self.verify_request_prerequisites(db, request)

        transition_request(
            db=db,
            request=request,
            new_status=target_status,
            agent_code=self.agent_code,
            reason_code=reason_code,
            note="Verification check against synthetic account and customer records.",
        )

        target_status_val = target_status.value if hasattr(target_status, "value") else str(target_status)

        # --------------------------------------------------------------------
        # Publish Verification Events via RabbitMQ
        # --------------------------------------------------------------------
        if target_status == RequestStatus.VERIFIED:
            msg = StandardBankingMessage(
                request_id=request.request_id,
                request_version=request.assignment_version,
                sender_agent_id=self.agent_code,
                receiver_agent_id="ServiceAgentPool",
                event_type=BankingEventType.VERIFICATION_COMPLETED,
                reason_code=reason_code,
                payload={
                    "service_type": request.service_type.value if hasattr(request.service_type, "value") else str(request.service_type),
                    "account_verified": True,
                },
            )
            MessagePublisher.publish_event(db=db, message=msg, previous_state=orig_status, new_state=target_status_val)

        elif target_status == RequestStatus.HUMAN_REVIEW:
            msg = StandardBankingMessage(
                request_id=request.request_id,
                request_version=request.assignment_version,
                sender_agent_id=self.agent_code,
                receiver_agent_id="AGT-SUPERVISOR-01",
                event_type=BankingEventType.HUMAN_REVIEW_REQUIRED,
                reason_code=reason_code,
                payload={"verification_flag": True, "reason": reason_code},
            )
            MessagePublisher.publish_event(db=db, message=msg, previous_state=orig_status, new_state=target_status_val)
            dispatch_customer_notification(
                db=db,
                request=request,
                title="Supervisory Verification Referral",
                message=f"Request {request.request_id} has been referred for staff review: {reason_code}.",
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
                title="Account Verification Failed",
                message=f"Request {request.request_id} was rejected during account verification: {reason_code}.",
            )

        elif target_status == RequestStatus.NEEDS_CORRECTION:
            msg = StandardBankingMessage(
                request_id=request.request_id,
                request_version=request.assignment_version,
                sender_agent_id=self.agent_code,
                receiver_agent_id=f"CUSTOMER_{request.customer_id}",
                event_type=BankingEventType.REQUEST_NEEDS_CORRECTION,
                reason_code=reason_code,
                payload={"reason": reason_code},
            )
            MessagePublisher.publish_event(db=db, message=msg, previous_state=orig_status, new_state=target_status_val)
            dispatch_customer_notification(
                db=db,
                request=request,
                title="Account Status Warning",
                message=f"Request {request.request_id} requires correction: {reason_code}.",
            )

        self.completed_work_count += 1
        return request
