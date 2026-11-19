"""
BankFlow AI - Customer Agent
Simulates retail banking customers, synthetic request submission, and correction responses.
"""

import random
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import mesa
from sqlalchemy.orm import Session

from app.models.agent import AgentType
from app.models.request import Request, ServiceType
from app.agents.base_agent import BaseBankingAgent
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher
from app.messaging.notifications import dispatch_customer_notification

logger = logging.getLogger("bankflow_ai.agents.customer")


class CustomerAgent(BaseBankingAgent):
    """
    Customer Agent representing simulated synthetic account holders.
    Generates test requests, tracks submission codes, and provides correction payloads.
    """

    def __init__(
        self,
        model: mesa.Model,
        agent_code: str = "AGT-CUST-SIM-01",
        customer_code: Optional[str] = "CUST-SYN-00001",
    ):
        super().__init__(model, agent_code, AgentType.CUSTOMER)
        self.customer_code = customer_code
        self.submitted_requests: List[str] = []
        self.pending_corrections: Dict[str, Dict[str, Any]] = {}

    def generate_synthetic_request(
        self,
        service_type: ServiceType,
        is_valid: bool = True,
        account_id: Optional[int] = 1,
        account_number: Optional[str] = "ACC-SYN-1001",
    ) -> Dict[str, Any]:
        """
        Creates a synthetic service request payload according to Phase 3 validation rules.
        Supports generating valid or intentionally incomplete requests for scenario testing.
        """
        if service_type == ServiceType.CHEQUE_BOOK:
            leaves = random.choice([25, 50, 100]) if is_valid else 30  # 30 is invalid
            payload = {
                "account_id": account_id if is_valid else None,
                "account_number": account_number if is_valid else None,
                "number_of_leaves": leaves,
                "delivery_preference": "Standard Postal",
                "remarks": "Automated simulation test request",
            }

        elif service_type == ServiceType.DEBIT_CARD_REPLACEMENT:
            reason = "Damaged Card" if is_valid else "UnsupportedReason"
            payload = {
                "account_id": account_id if is_valid else None,
                "account_number": account_number if is_valid else None,
                "replacement_reason": reason,
                "delivery_address": "123 Simulation Way, Suite 400",
                "remarks": "Chip reading degradation",
            }

        elif service_type == ServiceType.ADDRESS_UPDATE:
            payload = {
                "account_id": account_id if is_valid else None,
                "account_number": account_number if is_valid else None,
                "new_synthetic_address": "789 Synthetic Parkway" if is_valid else "",
                "city": "Metropolis" if is_valid else "",
                "state": "NY" if is_valid else "",
                "postal_code": "10001" if is_valid else "",
                "reason_for_update": "Relocation across branch district",
            }

        elif service_type == ServiceType.ACCOUNT_APPLICATION:
            payload = {
                "applicant_name": "Synthetic Applicant Alpha" if is_valid else "",
                "email": "applicant.alpha@bankflow.synthetic" if is_valid else "invalid-email",
                "phone": "+1-555-0199",
                "requested_account_type": "SAVINGS",
                "monthly_income": 6500.0,
                "employment_status": "Employed Full-Time",
                "branch_preference": "Central Digital Branch",
            }
        else:
            payload = {"generic": "Unsupported request type"}

        return {
            "customer_code": self.customer_code,
            "service_type": service_type,
            "payload": payload,
            "is_valid": is_valid,
        }

    def publish_request_created(self, db: Session, request: Request) -> StandardBankingMessage:
        """
        Publishes REQUEST_CREATED event to RabbitMQ when a customer initiates a service request.
        Dispatches in-app confirmation notification to the customer.
        """
        msg = StandardBankingMessage(
            request_id=request.request_id,
            request_version=request.assignment_version,
            sender_agent_id=self.agent_code,
            receiver_agent_id="AGT-INTAKE-01",
            event_type=BankingEventType.REQUEST_CREATED,
            payload={
                "service_type": request.service_type.value if hasattr(request.service_type, "value") else str(request.service_type),
                "customer_id": request.customer_id,
                "account_id": request.account_id,
                "priority": request.priority,
            },
        )
        MessagePublisher.publish_event(db=db, message=msg, new_state="NEW")
        dispatch_customer_notification(
            db=db,
            request=request,
            title="Service Request Submitted",
            message=f"Your request {request.request_id} for {request.service_type.value if hasattr(request.service_type, 'value') else request.service_type} has been submitted for automated intake processing.",
        )
        self.submitted_requests.append(request.request_id)
        return msg

    def receive_correction_notification(self, request_id: str, reason: str, instruction: str) -> None:
        """Stores a correction request received from the intake or verification gate."""
        self.pending_corrections[request_id] = {
            "reason": reason,
            "instruction": instruction,
        }

    def generate_correction_payload(self, request_id: str, service_type: ServiceType, account_id: int = 1) -> Dict[str, Any]:
        """Provides a corrected valid payload to resolve a pending correction."""
        corrected = self.generate_synthetic_request(service_type, is_valid=True, account_id=account_id)
        if request_id in self.pending_corrections:
            del self.pending_corrections[request_id]
        return corrected["payload"]
