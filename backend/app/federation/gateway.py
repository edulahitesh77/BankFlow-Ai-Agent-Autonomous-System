"""
BankFlow AI - Federation Gateway (Phase 10)
Central controlled communication layer managing inter-branch information exchange,
service authentication, scope authorization, data sanitization, and dual-branch audit logging.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import BranchDatabaseManager, SessionLocal
from app.models.branch import Branch, BranchStatus
from app.models.account import Account
from app.models.customer import Customer
from app.models.federation_event import FederationEvent
from app.federation.schemas import CrossBranchRequest, CrossBranchResponse
from app.federation.security import FederationSecurityManager

logger = logging.getLogger("bankflow_ai.federation.gateway")


class FederationGateway:
    """
    Central Federation Gateway enforcing controlled cross-branch information exchange.
    Prevents unrestricted database access between branches while providing authorized confirmations.
    """

    @classmethod
    def process_cross_branch_request(
        cls,
        req: CrossBranchRequest,
        api_key: str,
        gateway_db: Optional[Session] = None,
        is_test: bool = False,
    ) -> CrossBranchResponse:
        """
        Processes a cross-branch information request:
        1. Authenticates source branch credentials.
        2. Authorizes source -> destination permissions and scope.
        3. Protects against duplicate requests via correlation_id.
        4. Queries destination branch database safely.
        5. Sanitizes and returns ONLY permitted confirmation fields.
        6. Persists audit events on both branches.
        """
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        event_id = f"FED-EVT-{uuid.uuid4().hex[:12].upper()}"

        own_gateway_session = False
        if gateway_db is None:
            gateway_db = SessionLocal()
            own_gateway_session = True

        try:
            # 1. Check for Duplicate Request (Anti-Replay / Idempotency)
            existing_event = gateway_db.query(FederationEvent).filter(
                FederationEvent.correlation_id == req.correlation_id
            ).first()

            if existing_event:
                logger.info("Duplicate federation request detected for correlation_id '%s'", req.correlation_id)
                return CrossBranchResponse(
                    federation_event_id=existing_event.federation_event_id,
                    correlation_id=req.correlation_id,
                    source_branch_id=req.source_branch_id,
                    destination_branch_id=req.destination_branch_id,
                    requested_scope=req.requested_scope,
                    authorization_result="DUPLICATE_REQUEST",
                    status="DUPLICATE",
                    timestamp=existing_event.timestamp.isoformat() if existing_event.timestamp else now_str,
                    data=existing_event.response_payload,
                    error_message="Duplicate request: Cached response returned.",
                )

            # 2. Authenticate Source Branch Identity
            is_authenticated, auth_code = FederationSecurityManager.authenticate_branch(
                req.source_branch_id, api_key
            )
            if not is_authenticated:
                cls._record_event(
                    gateway_db=gateway_db,
                    event_id=event_id,
                    req=req,
                    auth_result=auth_code or "REJECTED_AUTHENTICATION",
                    status="REJECTED",
                    error="Invalid branch service credentials.",
                    is_test=is_test,
                )
                return CrossBranchResponse(
                    federation_event_id=event_id,
                    correlation_id=req.correlation_id,
                    source_branch_id=req.source_branch_id,
                    destination_branch_id=req.destination_branch_id,
                    requested_scope=req.requested_scope,
                    authorization_result=auth_code or "REJECTED_AUTHENTICATION",
                    status="REJECTED",
                    timestamp=now_str,
                    data=None,
                    error_message="Branch authentication failed: Invalid or unregistered credentials.",
                )

            # 3. Authorize Destination and Permitted Scope
            is_authorized, auth_res = FederationSecurityManager.authorize_scope(
                req.source_branch_id, req.destination_branch_id, req.requested_scope
            )
            if not is_authorized:
                cls._record_event(
                    gateway_db=gateway_db,
                    event_id=event_id,
                    req=req,
                    auth_result=auth_res or "REJECTED_UNAUTHORIZED",
                    status="REJECTED",
                    error=f"Scope '{req.requested_scope}' is outside permitted cross-branch information exchange.",
                    is_test=is_test,
                )
                return CrossBranchResponse(
                    federation_event_id=event_id,
                    correlation_id=req.correlation_id,
                    source_branch_id=req.source_branch_id,
                    destination_branch_id=req.destination_branch_id,
                    requested_scope=req.requested_scope,
                    authorization_result=auth_res or "REJECTED_UNAUTHORIZED",
                    status="REJECTED",
                    timestamp=now_str,
                    data=None,
                    error_message=f"Access denied: Requested scope '{req.requested_scope}' is not authorized.",
                )

            # 4. Query Destination Branch Safely
            try:
                dest_session = BranchDatabaseManager.get_session(req.destination_branch_id, is_test=is_test)
            except Exception as e:
                logger.error("Failed to connect to destination branch database '%s': %s", req.destination_branch_id, str(e))
                cls._record_event(
                    gateway_db=gateway_db,
                    event_id=event_id,
                    req=req,
                    auth_result="AUTHORIZED",
                    status="FAILED",
                    error=f"Destination branch '{req.destination_branch_id}' database unavailable.",
                    is_test=is_test,
                )
                return CrossBranchResponse(
                    federation_event_id=event_id,
                    correlation_id=req.correlation_id,
                    source_branch_id=req.source_branch_id,
                    destination_branch_id=req.destination_branch_id,
                    requested_scope=req.requested_scope,
                    authorization_result="AUTHORIZED",
                    status="FAILED",
                    timestamp=now_str,
                    data=None,
                    error_message=f"Destination branch '{req.destination_branch_id}' is currently unavailable.",
                )

            raw_result: Dict[str, Any] = {}
            try:
                if req.requested_scope == "ACCOUNT_STATUS_CONFIRMATION":
                    acc_num = req.query_params.get("synthetic_account_number")
                    account = dest_session.query(Account).filter(
                        Account.synthetic_account_number == acc_num
                    ).first()

                    if account:
                        raw_result = {
                            "synthetic_account_number": account.synthetic_account_number,
                            "account_status": account.account_status,
                            "is_confirmed": account.account_status == "ACTIVE",
                            "branch_id": req.destination_branch_id,
                        }
                    else:
                        raw_result = {
                            "synthetic_account_number": acc_num,
                            "account_status": "NOT_FOUND",
                            "is_confirmed": False,
                            "branch_id": req.destination_branch_id,
                        }

                elif req.requested_scope == "CUSTOMER_KYC_VERIFICATION":
                    c_code = req.query_params.get("customer_code")
                    cust = dest_session.query(Customer).filter(
                        Customer.customer_code == c_code
                    ).first()

                    if cust:
                        raw_result = {
                            "customer_code": cust.customer_code,
                            "kyc_status": "VERIFIED",
                            "is_verified": True,
                            "branch_id": req.destination_branch_id,
                        }
                    else:
                        raw_result = {
                            "customer_code": c_code,
                            "kyc_status": "NOT_FOUND",
                            "is_verified": False,
                            "branch_id": req.destination_branch_id,
                        }

                elif req.requested_scope == "SERVICE_ELIGIBILITY_CONFIRMATION":
                    acc_num = req.query_params.get("synthetic_account_number")
                    svc_type = req.query_params.get("service_type")
                    account = dest_session.query(Account).filter(
                        Account.synthetic_account_number == acc_num
                    ).first()

                    is_elig = bool(account and account.account_status == "ACTIVE")
                    raw_result = {
                        "synthetic_account_number": acc_num,
                        "service_type": svc_type,
                        "is_eligible": is_elig,
                        "branch_id": req.destination_branch_id,
                    }

            finally:
                dest_session.close()

            # 5. Sanitize Result Data (Strictly limited to permitted scope fields)
            sanitized_data = FederationSecurityManager.sanitize_response(req.requested_scope, raw_result)

            # 6. Record Audit Event on Gateway and Branches
            cls._record_event(
                gateway_db=gateway_db,
                event_id=event_id,
                req=req,
                auth_result="AUTHORIZED",
                status="SUCCESS",
                response_data=sanitized_data,
                is_test=is_test,
            )

            return CrossBranchResponse(
                federation_event_id=event_id,
                correlation_id=req.correlation_id,
                source_branch_id=req.source_branch_id,
                destination_branch_id=req.destination_branch_id,
                requested_scope=req.requested_scope,
                authorization_result="AUTHORIZED",
                status="SUCCESS",
                timestamp=now_str,
                data=sanitized_data,
                error_message=None,
            )

        finally:
            if own_gateway_session:
                gateway_db.close()

    @classmethod
    def _record_event(
        cls,
        gateway_db: Session,
        event_id: str,
        req: CrossBranchRequest,
        auth_result: str,
        status: str,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        is_test: bool = False,
    ):
        """Persists federation event across gateway and relevant branch audit stores."""
        evt = FederationEvent(
            federation_event_id=event_id,
            source_branch_id=req.source_branch_id,
            destination_branch_id=req.destination_branch_id,
            request_id=req.request_id,
            event_type=req.requested_scope,
            requested_scope=req.requested_scope,
            authorization_result=auth_result,
            correlation_id=req.correlation_id,
            event_status=status,
            request_payload=req.query_params,
            response_payload=response_data,
            error_message=error,
        )

        try:
            gateway_db.add(evt)
            gateway_db.commit()
        except Exception as e:
            gateway_db.rollback()
            logger.error("Failed to persist federation event on gateway DB: %s", str(e))

        # Also persist to source branch database for branch-local audit trail
        try:
            src_session = BranchDatabaseManager.get_session(req.source_branch_id, is_test=is_test)
            src_evt = FederationEvent(
                federation_event_id=event_id,
                source_branch_id=req.source_branch_id,
                destination_branch_id=req.destination_branch_id,
                request_id=req.request_id,
                event_type=req.requested_scope,
                requested_scope=req.requested_scope,
                authorization_result=auth_result,
                correlation_id=req.correlation_id,
                event_status=status,
                request_payload=req.query_params,
                response_payload=response_data,
                error_message=error,
            )
            src_session.add(src_evt)
            src_session.commit()
            src_session.close()
        except Exception as e:
            logger.debug("Source branch audit logging deferred: %s", str(e))
