"""
BankFlow AI - Request Management Service
Handles validation, creation, retrieval, tracking, and customer correction of banking service requests.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any, Union
from sqlalchemy import or_, desc, func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.request import Request, ServiceType, RequestStatus
from app.models.customer import Customer
from app.models.account import Account
from app.models.audit_log import AuditLog
from app.auth.encryption import encrypt_payload_fields, decrypt_payload_fields
from app.services.audit_service import AuditService
from app.schemas.request import (
    CreateServiceRequest,
    CorrectServiceRequest,
    ServiceRequestResponse,
    RequestListResponse,
    ChequeBookPayload,
    DebitCardReplacementPayload,
    AddressUpdatePayload,
    AccountApplicationPayload,
)


def derive_current_stage(req_status: Union[RequestStatus, str]) -> str:
    """Map internal database request status to a human-readable visual workflow stage."""
    status_val = req_status.value if isinstance(req_status, RequestStatus) else req_status

    stage_map = {
        RequestStatus.NEW.value: "1. Request Submitted (Awaiting Intake)",
        RequestStatus.CLASSIFIED.value: "2. Intake Classification Completed",
        RequestStatus.QUEUED.value: "2. Queued for Agent Verification",
        RequestStatus.VERIFIED.value: "3. Identity & Documents Verified",
        RequestStatus.IN_SERVICE.value: "4. Service Processing Underway",
        RequestStatus.COMPLETED.value: "5. Completed Successfully",
        RequestStatus.NEEDS_CORRECTION.value: "Action Required: Customer Correction Needed",
        RequestStatus.HUMAN_REVIEW.value: "Supervisor Review: Under Human Staff Oversight",
        RequestStatus.REJECTED_INPUT.value: "Final Disposition: Request Rejected",
        RequestStatus.FAILED.value: "Final Disposition: Workflow Execution Failed",
    }
    return stage_map.get(status_val, f"Status: {status_val}")


class RequestService:
    """Service handling all service request operations for authenticated customers."""

    @staticmethod
    def generate_unique_request_id(db: Session) -> str:
        """
        Generate a unique human-friendly banking request identifier.
        Format: BFA-REQ-YYYY-NNNNN
        """
        year = datetime.now(timezone.utc).year
        # Count existing requests to get sequence base
        total_count = db.query(func.count(Request.id)).scalar() or 0
        seq = total_count + 1

        for attempt in range(50):
            candidate = f"BFA-REQ-{year}-{seq + attempt:05d}"
            exists = db.query(Request.id).filter(Request.request_id == candidate).first()
            if not exists:
                return candidate

        # Fallback to random suffix if sequence clashes
        return f"BFA-REQ-{year}-{uuid.uuid4().hex[:6].upper()}"

    @classmethod
    def validate_service_payload(
        cls,
        db: Session,
        customer_id: int,
        service_type: ServiceType,
        payload: Dict[str, Any],
        account_id: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], Optional[int]]:
        """
        Strictly validate payload fields according to the requested service type.
        Ensures target accounts belong strictly to the authenticated customer.
        """
        validated_account_id = account_id

        if service_type == ServiceType.CHEQUE_BOOK:
            # Inject account_id into payload if not already present
            if account_id and "account_id" not in payload:
                payload["account_id"] = account_id
            try:
                validated = ChequeBookPayload(**payload)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
            validated_account_id = validated.account_id

        elif service_type == ServiceType.DEBIT_CARD_REPLACEMENT:
            if account_id and "account_id" not in payload:
                payload["account_id"] = account_id
            try:
                validated = DebitCardReplacementPayload(**payload)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
            validated_account_id = validated.account_id

        elif service_type == ServiceType.ADDRESS_UPDATE:
            if account_id and "account_id" not in payload:
                payload["account_id"] = account_id
            try:
                validated = AddressUpdatePayload(**payload)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
            validated_account_id = validated.account_id

        elif service_type == ServiceType.ACCOUNT_APPLICATION:
            try:
                validated = AccountApplicationPayload(**payload)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
            validated_account_id = None

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported service type: {service_type}",
            )

        # If an account is linked, verify ownership
        if validated_account_id:
            acc = (
                db.query(Account)
                .filter(Account.id == validated_account_id, Account.customer_id == customer_id)
                .first()
            )
            if not acc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The selected bank account does not belong to your customer profile.",
                )

        return payload, validated_account_id

    @classmethod
    def submit_service_request(
        cls,
        db: Session,
        customer: Customer,
        data: CreateServiceRequest,
        client_ip: str = "127.0.0.1",
    ) -> ServiceRequestResponse:
        """
        Process and persist a new customer service request.
        Initial status is set strictly to NEW.
        """
        validated_payload, account_id = cls.validate_service_payload(
            db=db,
            customer_id=customer.id,
            service_type=data.service_type,
            payload=data.payload,
            account_id=data.account_id,
        )

        request_id = cls.generate_unique_request_id(db)

        # Set review_required true for high/critical priority or sensitive categories
        review_req = data.priority in ("HIGH", "CRITICAL")

        encrypted_payload = encrypt_payload_fields(validated_payload)

        req = Request(
            request_id=request_id,
            customer_id=customer.id,
            account_id=account_id,
            service_type=data.service_type,
            request_status=RequestStatus.NEW,
            priority=data.priority.upper(),
            assigned_agent_id=None,
            assignment_version=0,
            required_skill=f"{data.service_type.value}_PROCESSING",
            completeness_status="PENDING",
            review_required=review_req,
            reason_code=None,
            payload=encrypted_payload,
        )
        db.add(req)
        db.flush()

        AuditService.record_event(
            db=db,
            action="SERVICE_REQUEST_SUBMITTED",
            user_id=customer.user_id,
            request_id=request_id,
            outcome="SUCCESS",
            description=f"Customer '{customer.customer_code}' submitted {data.service_type.value} request ({request_id}) from IP {client_ip}",
            source_ip=client_ip,
            entity_type="REQUEST",
            entity_id=request_id,
            auto_commit=False,
        )

        # Emit REQUEST_CREATED to RabbitMQ broker
        try:
            from app.messaging.message_schema import StandardBankingMessage, BankingEventType
            from app.messaging.publisher import MessagePublisher
            msg = StandardBankingMessage(
                request_id=request_id,
                request_version=0,
                sender_agent_id="CustomerPortal",
                receiver_agent_id="AGT-INTAKE-01",
                event_type=BankingEventType.REQUEST_CREATED,
                payload={
                    "service_type": data.service_type.value,
                    "customer_id": customer.id,
                    "account_id": account_id,
                    "priority": data.priority.upper(),
                },
            )
            MessagePublisher.publish_event(db, msg, new_state="NEW")
        except Exception as ex:
            logger.warning("Non-critical: Failed to publish REQUEST_CREATED event to broker: %s", str(ex))

        db.commit()
        db.refresh(req)

        return cls.format_request_response(req)

    @classmethod
    def get_customer_requests(
        cls,
        db: Session,
        customer_id: int,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> RequestListResponse:
        """
        Fetch paginated requests belonging strictly to the authenticated customer.
        Supports status filtering and search by request_id.
        """
        query = db.query(Request).filter(Request.customer_id == customer_id)

        if status_filter and status_filter.upper() != "ALL":
            filter_val = status_filter.upper()
            # Support group filters: "PENDING"
            if filter_val == "PENDING":
                pending_statuses = [
                    RequestStatus.NEW,
                    RequestStatus.CLASSIFIED,
                    RequestStatus.QUEUED,
                    RequestStatus.VERIFIED,
                    RequestStatus.IN_SERVICE,
                    RequestStatus.NEEDS_CORRECTION,
                    RequestStatus.HUMAN_REVIEW,
                ]
                query = query.filter(Request.request_status.in_(pending_statuses))
            elif filter_val == "COMPLETED":
                query = query.filter(Request.request_status == RequestStatus.COMPLETED)
            elif filter_val == "NEEDS_CORRECTION":
                query = query.filter(Request.request_status == RequestStatus.NEEDS_CORRECTION)
            elif filter_val == "HUMAN_REVIEW":
                query = query.filter(Request.request_status == RequestStatus.HUMAN_REVIEW)
            elif filter_val == "REJECTED":
                query = query.filter(
                    Request.request_status.in_([RequestStatus.REJECTED_INPUT, RequestStatus.FAILED])
                )
            else:
                query = query.filter(Request.request_status == filter_val)

        if search:
            search_clean = f"%{search.strip().upper()}%"
            query = query.filter(
                or_(
                    Request.request_id.ilike(search_clean),
                    Request.service_type.ilike(search_clean),
                )
            )

        total = query.count()
        pages = max(1, (total + limit - 1) // limit)
        offset = (page - 1) * limit

        records = (
            query.order_by(desc(Request.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = [cls.format_request_response(r) for r in records]
        return RequestListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

    @classmethod
    def get_customer_request_by_id(
        cls,
        db: Session,
        customer_id: int,
        request_id: str,
        user_id: Optional[int] = None,
        client_ip: str = "127.0.0.1",
    ) -> ServiceRequestResponse:
        """
        Retrieve request details ensuring customer ownership.
        Returns HTTP 404 if not found or unauthorized.
        """
        req = (
            db.query(Request)
            .filter(Request.request_id == request_id, Request.customer_id == customer_id)
            .first()
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request '{request_id}' not found or you are not authorized to view it.",
            )

        # Audit view
        if user_id:
            audit = AuditLog(
                user_id=user_id,
                action="SERVICE_REQUEST_VIEWED",
                entity_type="REQUEST",
                entity_id=request_id,
                description=f"Request details viewed from IP {client_ip}",
            )
            db.add(audit)
            db.commit()

        return cls.format_request_response(req)

    @classmethod
    def submit_correction(
        cls,
        db: Session,
        customer_id: int,
        request_id: str,
        data: CorrectServiceRequest,
        user_id: Optional[int] = None,
        client_ip: str = "127.0.0.1",
    ) -> ServiceRequestResponse:
        """
        Allow customer to update request fields strictly when status is NEEDS_CORRECTION.
        Increments assignment_version and resets status to NEW.
        """
        req = (
            db.query(Request)
            .filter(Request.request_id == request_id, Request.customer_id == customer_id)
            .first()
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request '{request_id}' not found.",
            )

        if req.request_status != RequestStatus.NEEDS_CORRECTION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request '{request_id}' is currently in '{req.request_status.value}' status. Corrections are only permitted when status is 'NEEDS_CORRECTION'.",
            )

        # Re-validate corrected payload against original service_type
        validated_payload, account_id = cls.validate_service_payload(
            db=db,
            customer_id=customer_id,
            service_type=req.service_type,
            payload=data.payload,
            account_id=req.account_id,
        )

        # Merge previous payload into history if applicable
        current_payload = dict(decrypt_payload_fields(req.payload) or {})
        current_payload.update(validated_payload)
        if data.correction_notes:
            current_payload["customer_correction_notes"] = data.correction_notes

        # Encrypt sensitive fields before persistence
        req.payload = encrypt_payload_fields(current_payload)
        req.account_id = account_id
        req.assignment_version += 1
        req.request_status = RequestStatus.NEW
        req.completeness_status = "CORRECTED_PENDING_REVIEW"
        req.reason_code = None

        AuditService.record_event(
            db=db,
            action="SERVICE_REQUEST_CORRECTED",
            user_id=user_id,
            request_id=request_id,
            outcome="SUCCESS",
            description=f"Customer corrected request ({request_id}), version incremented to {req.assignment_version} from IP {client_ip}",
            source_ip=client_ip,
            entity_type="REQUEST",
            entity_id=request_id,
            auto_commit=False,
        )

        # Emit correction resubmission event to RabbitMQ broker
        try:
            from app.messaging.message_schema import StandardBankingMessage, BankingEventType
            from app.messaging.publisher import MessagePublisher
            msg = StandardBankingMessage(
                request_id=request_id,
                request_version=req.assignment_version,
                sender_agent_id="CustomerPortal",
                receiver_agent_id="AGT-INTAKE-01",
                event_type=BankingEventType.REQUEST_CREATED,
                reason_code="CUSTOMER_CORRECTION_RESUBMISSION",
                payload={
                    "service_type": req.service_type.value if hasattr(req.service_type, "value") else str(req.service_type),
                    "customer_id": customer_id,
                    "account_id": account_id,
                    "assignment_version": req.assignment_version,
                },
            )
            MessagePublisher.publish_event(db, msg, previous_state="NEEDS_CORRECTION", new_state="NEW")
        except Exception as ex:
            logger.warning("Non-critical: Failed to publish correction event to broker: %s", str(ex))

        db.commit()
        db.refresh(req)

        return cls.format_request_response(req)

    @staticmethod
    def format_request_response(req: Request) -> ServiceRequestResponse:
        """Helper serializing Request model to ServiceRequestResponse."""
        status_msg = None
        if getattr(req, "retry_count", 0) > 0 and req.request_status not in (RequestStatus.COMPLETED, RequestStatus.REJECTED_INPUT):
            status_msg = "Your request is taking longer than expected. Our team is monitoring it."

        return ServiceRequestResponse(
            id=req.id,
            request_id=req.request_id,
            customer_id=req.customer_id,
            account_id=req.account_id,
            service_type=req.service_type.value if hasattr(req.service_type, 'value') else str(req.service_type),
            request_status=req.request_status.value if hasattr(req.request_status, 'value') else str(req.request_status),
            priority=req.priority,
            assigned_agent_id=req.assigned_agent_id,
            assignment_version=req.assignment_version,
            required_skill=req.required_skill,
            completeness_status=req.completeness_status,
            review_required=req.review_required,
            reason_code=req.reason_code,
            payload=decrypt_payload_fields(req.payload),
            created_at=req.created_at,
            updated_at=req.updated_at,
            completed_at=req.completed_at,
            current_stage=derive_current_stage(req.request_status),
            retry_count=getattr(req, "retry_count", 0),
            customer_status_message=status_msg,
        )
