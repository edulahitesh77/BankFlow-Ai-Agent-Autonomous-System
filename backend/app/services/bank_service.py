"""
BankFlow AI - Bank Service
Comprehensive business logic for bank employee dashboard, request review,
correction workflows, customer investigation, and compliance audit reporting.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.account import Account
from app.models.request import Request, ServiceType, RequestStatus
from app.models.agent import Agent
from app.models.audit_log import AuditLog
from app.models.review_record import ReviewRecord, ReviewDecision
from app.models.correction_record import CorrectionRecord
from app.models.notification import Notification
from app.auth.encryption import decrypt_payload_fields
from app.services.audit_service import AuditService

from app.schemas.bank import (
    BankDashboardResponse,
    BankDashboardSummary,
    ServiceDemandItem,
    RecentActivityItem,
    BankRequestItem,
    BankRequestListResponse,
    BankRequestDetailResponse,
    ReviewRecordResponse,
    CorrectionRecordResponse,
    SubmitReviewRequest,
    SubmitCorrectionRequest,
    CustomerRecordItem,
    CustomerRecordListResponse,
    CustomerAccountItem,
    CustomerDetailResponse,
    AuditLogItem,
    AuditLogListResponse,
    AgentMonitoringResponse,
    AgentMonitoringItem,
)


class BankService:
    """Service providing bank employee operational workflows."""

    @staticmethod
    def get_dashboard_metrics(db: Session) -> BankDashboardResponse:
        """
        Calculates real-time aggregate statistics, distributions, and recent audit activity.
        All metrics are strictly calculated from PostgreSQL records.
        """
        # 1. Total & Status Counts
        total_requests = db.query(func.count(Request.id)).scalar() or 0
        new_requests = (
            db.query(func.count(Request.id))
            .filter(Request.request_status == RequestStatus.NEW)
            .scalar()
            or 0
        )
        completed_requests = (
            db.query(func.count(Request.id))
            .filter(Request.request_status == RequestStatus.COMPLETED)
            .scalar()
            or 0
        )
        needs_correction_requests = (
            db.query(func.count(Request.id))
            .filter(Request.request_status == RequestStatus.NEEDS_CORRECTION)
            .scalar()
            or 0
        )
        rejected_requests = (
            db.query(func.count(Request.id))
            .filter(
                Request.request_status.in_(
                    [RequestStatus.REJECTED_INPUT, RequestStatus.FAILED]
                )
            )
            .scalar()
            or 0
        )
        human_review_requests = (
            db.query(func.count(Request.id))
            .filter(
                or_(
                    Request.review_required == True,
                    Request.request_status == RequestStatus.HUMAN_REVIEW,
                )
            )
            .scalar()
            or 0
        )
        pending_requests = (
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

        total_customers = db.query(func.count(Customer.id)).scalar() or 0
        total_accounts = db.query(func.count(Account.id)).scalar() or 0

        summary = BankDashboardSummary(
            total_requests=total_requests,
            new_requests=new_requests,
            pending_requests=pending_requests,
            human_review_requests=human_review_requests,
            needs_correction_requests=needs_correction_requests,
            completed_requests=completed_requests,
            rejected_requests=rejected_requests,
            total_customers=total_customers,
            total_accounts=total_accounts,
        )

        # 2. Request Distribution by Service Type
        service_counts_raw = (
            db.query(Request.service_type, func.count(Request.id))
            .group_by(Request.service_type)
            .all()
        )
        request_distribution = {st.value: 0 for st in ServiceType}
        for st, count in service_counts_raw:
            key = st.value if hasattr(st, "value") else str(st)
            request_distribution[key] = count

        # 3. Request Status Distribution
        status_counts_raw = (
            db.query(Request.request_status, func.count(Request.id))
            .group_by(Request.request_status)
            .all()
        )
        status_distribution = {rs.value: 0 for rs in RequestStatus}
        for rs, count in status_counts_raw:
            key = rs.value if hasattr(rs, "value") else str(rs)
            status_distribution[key] = count

        # 4. Service Demand (sorted descending)
        service_demand = []
        for st in ServiceType:
            count = request_distribution.get(st.value, 0)
            percentage = round((count / total_requests * 100), 1) if total_requests > 0 else 0.0
            service_demand.append(
                ServiceDemandItem(
                    service_type=st,
                    count=count,
                    percentage=percentage,
                )
            )
        service_demand.sort(key=lambda x: x.count, reverse=True)

        # 5. Recent Activity (Audit logs)
        recent_logs = (
            db.query(AuditLog)
            .order_by(desc(AuditLog.timestamp))
            .limit(10)
            .all()
        )
        recent_activity = []
        for log in recent_logs:
            actor = "System"
            role = "SYSTEM"
            if log.user:
                role = log.user.role.value if hasattr(log.user.role, "value") else str(log.user.role)
                if log.user.employee:
                    actor = f"{log.user.employee.full_name} ({log.user.employee.employee_code})"
                elif log.user.customer:
                    actor = f"{log.user.customer.full_name} ({log.user.customer.customer_code})"
                else:
                    actor = log.user.username

            recent_activity.append(
                RecentActivityItem(
                    id=log.id,
                    timestamp=log.timestamp,
                    actor=actor,
                    role=role,
                    action=log.action,
                    entity_type=log.entity_type,
                    entity_id=log.entity_id,
                    description=log.description,
                )
            )

        return BankDashboardResponse(
            summary=summary,
            request_distribution=request_distribution,
            status_distribution=status_distribution,
            service_demand=service_demand,
            recent_activity=recent_activity,
        )

    @staticmethod
    def get_requests(
        db: Session,
        status_filter: Optional[str] = None,
        service_type_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        branch_filter: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> BankRequestListResponse:
        """
        Lists and filters requests with server-side pagination and relational joins.
        """
        query = db.query(Request).join(Customer, Request.customer_id == Customer.id)

        if status_filter and status_filter.upper() != "ALL":
            try:
                target_status = RequestStatus(status_filter.upper())
                query = query.filter(Request.request_status == target_status)
            except ValueError:
                pass

        if service_type_filter and service_type_filter.upper() != "ALL":
            try:
                target_st = ServiceType(service_type_filter.upper())
                query = query.filter(Request.service_type == target_st)
            except ValueError:
                pass

        if priority_filter and priority_filter.upper() != "ALL":
            query = query.filter(Request.priority == priority_filter.upper())

        if branch_filter and branch_filter.upper() != "ALL":
            query = query.filter(Customer.branch_id.ilike(f"%{branch_filter}%"))

        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Request.request_id.ilike(search_clean),
                    Customer.customer_code.ilike(search_clean),
                    Customer.full_name.ilike(search_clean),
                )
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))

        offset = (page - 1) * page_size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(page_size).all()

        items = []
        for req in requests:
            cust = req.customer
            items.append(
                BankRequestItem(
                    id=req.id,
                    request_id=req.request_id,
                    customer_id=req.customer_id,
                    customer_code=cust.customer_code if cust else "UNKNOWN",
                    customer_name=cust.full_name if cust else "UNKNOWN",
                    customer_email=cust.email if cust else "UNKNOWN",
                    customer_phone=cust.phone if cust else None,
                    customer_branch=cust.branch_id if cust else None,
                    service_type=req.service_type,
                    request_status=req.request_status,
                    priority=req.priority,
                    assigned_agent_id=req.assigned_agent_id,
                    assigned_agent_code=req.assigned_agent.agent_code if req.assigned_agent else None,
                    assignment_version=req.assignment_version,
                    review_required=req.review_required,
                    completeness_status=req.completeness_status,
                    reason_code=req.reason_code,
                    created_at=req.created_at,
                    updated_at=req.updated_at,
                    completed_at=req.completed_at,
                )
            )

        return BankRequestListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_pending_requests(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
    ) -> BankRequestListResponse:
        """Retrieves requests awaiting processing or validation."""
        query = db.query(Request).join(Customer, Request.customer_id == Customer.id)
        query = query.filter(
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
        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Request.request_id.ilike(search_clean),
                    Customer.customer_code.ilike(search_clean),
                    Customer.full_name.ilike(search_clean),
                )
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(page_size).all()

        items = [
            BankRequestItem(
                id=req.id,
                request_id=req.request_id,
                customer_id=req.customer_id,
                customer_code=req.customer.customer_code,
                customer_name=req.customer.full_name,
                customer_email=req.customer.email,
                customer_phone=req.customer.phone,
                customer_branch=req.customer.branch_id,
                service_type=req.service_type,
                request_status=req.request_status,
                priority=req.priority,
                assigned_agent_id=req.assigned_agent_id,
                assigned_agent_code=req.assigned_agent.agent_code if req.assigned_agent else None,
                assignment_version=req.assignment_version,
                review_required=req.review_required,
                completeness_status=req.completeness_status,
                reason_code=req.reason_code,
                created_at=req.created_at,
                updated_at=req.updated_at,
                completed_at=req.completed_at,
            )
            for req in requests
        ]
        return BankRequestListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_human_review_requests(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
    ) -> BankRequestListResponse:
        """Retrieves requests marked for human review or with status HUMAN_REVIEW."""
        query = db.query(Request).join(Customer, Request.customer_id == Customer.id)
        query = query.filter(
            or_(
                Request.review_required == True,
                Request.request_status == RequestStatus.HUMAN_REVIEW,
            )
        )
        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Request.request_id.ilike(search_clean),
                    Customer.customer_code.ilike(search_clean),
                    Customer.full_name.ilike(search_clean),
                )
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(page_size).all()

        items = [
            BankRequestItem(
                id=req.id,
                request_id=req.request_id,
                customer_id=req.customer_id,
                customer_code=req.customer.customer_code,
                customer_name=req.customer.full_name,
                customer_email=req.customer.email,
                customer_phone=req.customer.phone,
                customer_branch=req.customer.branch_id,
                service_type=req.service_type,
                request_status=req.request_status,
                priority=req.priority,
                assigned_agent_id=req.assigned_agent_id,
                assigned_agent_code=req.assigned_agent.agent_code if req.assigned_agent else None,
                assignment_version=req.assignment_version,
                review_required=req.review_required,
                completeness_status=req.completeness_status,
                reason_code=req.reason_code,
                created_at=req.created_at,
                updated_at=req.updated_at,
                completed_at=req.completed_at,
            )
            for req in requests
        ]
        return BankRequestListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_needs_correction_requests(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
    ) -> BankRequestListResponse:
        """Retrieves requests currently in NEEDS_CORRECTION status."""
        query = db.query(Request).join(Customer, Request.customer_id == Customer.id)
        query = query.filter(Request.request_status == RequestStatus.NEEDS_CORRECTION)

        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Request.request_id.ilike(search_clean),
                    Customer.customer_code.ilike(search_clean),
                    Customer.full_name.ilike(search_clean),
                )
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(page_size).all()

        items = [
            BankRequestItem(
                id=req.id,
                request_id=req.request_id,
                customer_id=req.customer_id,
                customer_code=req.customer.customer_code,
                customer_name=req.customer.full_name,
                customer_email=req.customer.email,
                customer_phone=req.customer.phone,
                customer_branch=req.customer.branch_id,
                service_type=req.service_type,
                request_status=req.request_status,
                priority=req.priority,
                assigned_agent_id=req.assigned_agent_id,
                assigned_agent_code=req.assigned_agent.agent_code if req.assigned_agent else None,
                assignment_version=req.assignment_version,
                review_required=req.review_required,
                completeness_status=req.completeness_status,
                reason_code=req.reason_code,
                created_at=req.created_at,
                updated_at=req.updated_at,
                completed_at=req.completed_at,
            )
            for req in requests
        ]
        return BankRequestListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_rejected_requests(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
    ) -> BankRequestListResponse:
        """Retrieves requests with status REJECTED_INPUT or FAILED."""
        query = db.query(Request).join(Customer, Request.customer_id == Customer.id)
        query = query.filter(
            Request.request_status.in_(
                [RequestStatus.REJECTED_INPUT, RequestStatus.FAILED]
            )
        )

        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Request.request_id.ilike(search_clean),
                    Customer.customer_code.ilike(search_clean),
                    Customer.full_name.ilike(search_clean),
                )
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        requests = query.order_by(desc(Request.created_at)).offset(offset).limit(page_size).all()

        items = [
            BankRequestItem(
                id=req.id,
                request_id=req.request_id,
                customer_id=req.customer_id,
                customer_code=req.customer.customer_code,
                customer_name=req.customer.full_name,
                customer_email=req.customer.email,
                customer_phone=req.customer.phone,
                customer_branch=req.customer.branch_id,
                service_type=req.service_type,
                request_status=req.request_status,
                priority=req.priority,
                assigned_agent_id=req.assigned_agent_id,
                assigned_agent_code=req.assigned_agent.agent_code if req.assigned_agent else None,
                assignment_version=req.assignment_version,
                review_required=req.review_required,
                completeness_status=req.completeness_status,
                reason_code=req.reason_code,
                created_at=req.created_at,
                updated_at=req.updated_at,
                completed_at=req.completed_at,
            )
            for req in requests
        ]
        return BankRequestListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_request_details(
        db: Session,
        request_id: str,
        current_employee: Optional[Employee] = None,
        record_audit: bool = True,
    ) -> BankRequestDetailResponse:
        """
        Retrieves complete request details, payload parameters, review logs,
        and records an employee inspection audit event.
        """
        query = db.query(Request).filter(
            or_(
                Request.request_id == request_id,
                Request.id == int(request_id) if request_id.isdigit() else False,
            )
        )
        req = query.first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request '{request_id}' not found.",
            )

        cust = req.customer
        acc = req.account

        # Reviews
        reviews = []
        for r in req.review_records:
            reviews.append(
                ReviewRecordResponse(
                    id=r.id,
                    request_id=r.request_id,
                    employee_id=r.employee_id,
                    employee_code=r.employee.employee_code if r.employee else None,
                    employee_name=r.employee.full_name if r.employee else None,
                    review_decision=r.review_decision.value if hasattr(r.review_decision, "value") else str(r.review_decision),
                    internal_note=r.internal_note,
                    created_at=r.created_at,
                )
            )

        # Corrections
        corrections = []
        for c in req.correction_records:
            corrections.append(
                CorrectionRecordResponse(
                    id=c.id,
                    request_id=c.request_id,
                    employee_id=c.employee_id,
                    employee_code=c.employee.employee_code if c.employee else None,
                    employee_name=c.employee.full_name if c.employee else None,
                    correction_reason=c.correction_reason,
                    customer_instruction=c.customer_instruction,
                    created_at=c.created_at,
                )
            )

        # Audit trail for this request
        audit_records = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == "REQUEST",
                AuditLog.entity_id == req.request_id,
            )
            .order_by(desc(AuditLog.timestamp))
            .all()
        )
        audit_trail = []
        for a in audit_records:
            actor = "System"
            role = "SYSTEM"
            if a.user:
                role = a.user.role.value if hasattr(a.user.role, "value") else str(a.user.role)
                if a.user.employee:
                    actor = f"{a.user.employee.full_name} ({a.user.employee.employee_code})"
                elif a.user.customer:
                    actor = f"{a.user.customer.full_name} ({a.user.customer.customer_code})"
                else:
                    actor = a.user.username
            audit_trail.append(
                RecentActivityItem(
                    id=a.id,
                    timestamp=a.timestamp,
                    actor=actor,
                    role=role,
                    action=a.action,
                    entity_type=a.entity_type,
                    entity_id=a.entity_id,
                    description=a.description,
                )
            )

        # Record employee viewing action in audit log
        if current_employee and record_audit:
            AuditService.record_event(
                db=db,
                action="EMPLOYEE_VIEWED_REQUEST",
                user_id=current_employee.user_id,
                request_id=req.request_id,
                outcome="SUCCESS",
                description=f"Bank staff {current_employee.full_name} ({current_employee.employee_code}) viewed request {req.request_id}.",
                source_ip="127.0.0.1",
                entity_type="REQUEST",
                entity_id=req.request_id,
                auto_commit=True,
            )

        return BankRequestDetailResponse(
            id=req.id,
            request_id=req.request_id,
            customer_id=req.customer_id,
            customer_code=cust.customer_code if cust else "UNKNOWN",
            customer_name=cust.full_name if cust else "UNKNOWN",
            customer_email=cust.email if cust else "UNKNOWN",
            customer_phone=cust.phone if cust else None,
            customer_branch=cust.branch_id if cust else None,
            account_id=req.account_id,
            account_number=acc.synthetic_account_number if acc else None,
            account_type=acc.account_type if acc else None,
            service_type=req.service_type,
            request_status=req.request_status,
            priority=req.priority,
            assigned_agent_id=req.assigned_agent_id,
            assigned_agent_code=req.assigned_agent.agent_code if req.assigned_agent else None,
            assignment_version=req.assignment_version,
            required_skill=req.required_skill,
            completeness_status=req.completeness_status,
            review_required=req.review_required,
            reason_code=req.reason_code,
            payload=decrypt_payload_fields(req.payload),
            created_at=req.created_at,
            updated_at=req.updated_at,
            completed_at=req.completed_at,
            reviews=reviews,
            corrections=corrections,
            audit_trail=audit_trail,
        )

    @staticmethod
    def submit_review_decision(
        db: Session,
        request_id: str,
        current_employee: Employee,
        review_data: SubmitReviewRequest,
    ) -> BankRequestDetailResponse:
        """
        Records human employee review decision, updates request workflow state,
        creates customer notification if needed, and writes an audit log.
        """
        query = db.query(Request).filter(
            or_(
                Request.request_id == request_id,
                Request.id == int(request_id) if request_id.isdigit() else False,
            )
        )
        req = query.first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request '{request_id}' not found.",
            )

        # 1. Create ReviewRecord
        review_record = ReviewRecord(
            request_id=req.id,
            employee_id=current_employee.id,
            review_decision=review_data.decision,
            internal_note=review_data.internal_note.strip(),
        )
        db.add(review_record)

        # 2. State transition based on outcome
        if review_data.decision == ReviewDecision.REVIEW_COMPLETED:
            req.review_required = False
            # If in HUMAN_REVIEW, move forward to VERIFIED (awaiting agent or next step)
            if req.request_status == RequestStatus.HUMAN_REVIEW:
                req.request_status = RequestStatus.VERIFIED
            action_desc = f"Human review completed by {current_employee.employee_code}: {review_data.internal_note}"

        elif review_data.decision == ReviewDecision.ADDITIONAL_INFORMATION_REQUIRED:
            req.request_status = RequestStatus.NEEDS_CORRECTION
            req.review_required = False
            req.reason_code = review_data.reason_code or "ADDITIONAL_INFO_REQUIRED"
            action_desc = f"Review resulted in correction request by {current_employee.employee_code}: {review_data.internal_note}"

            # Create notification for customer
            notif = Notification(
                customer_id=req.customer_id,
                request_id=req.id,
                notification_title=f"Review Update: Additional Information Needed for {req.request_id}",
                notification_message=review_data.internal_note,
            )
            db.add(notif)

        elif review_data.decision == ReviewDecision.REVIEW_REJECTED:
            req.request_status = RequestStatus.REJECTED_INPUT
            req.review_required = False
            req.reason_code = review_data.reason_code or "HUMAN_REVIEW_REJECTED"
            action_desc = f"Request rejected during human review by {current_employee.employee_code}: {review_data.internal_note}"

            notif = Notification(
                customer_id=req.customer_id,
                request_id=req.id,
                notification_title=f"Request Not Approved: {req.request_id}",
                notification_message=f"Following internal review, your request could not be processed: {review_data.internal_note}",
            )
            db.add(notif)

        elif review_data.decision == ReviewDecision.ESCALATED:
            req.review_required = True
            req.priority = "HIGH"
            action_desc = f"Request escalated to supervisor by {current_employee.employee_code}: {review_data.internal_note}"

        # 3. Write Audit Log
        audit = AuditLog(
            user_id=current_employee.user_id,
            action="HUMAN_REVIEW_DECISION",
            entity_type="REQUEST",
            entity_id=req.request_id,
            description=action_desc,
        )
        db.add(audit)
        db.commit()
        db.refresh(req)

        return BankService.get_request_details(db, req.request_id, current_employee, record_audit=False)

    @staticmethod
    def request_correction(
        db: Session,
        request_id: str,
        current_employee: Employee,
        correction_data: SubmitCorrectionRequest,
    ) -> BankRequestDetailResponse:
        """
        Flags a request as NEEDS_CORRECTION, captures reason & customer instruction,
        creates an in-app notification for the customer, and preserves request ID and history.
        """
        query = db.query(Request).filter(
            or_(
                Request.request_id == request_id,
                Request.id == int(request_id) if request_id.isdigit() else False,
            )
        )
        req = query.first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request '{request_id}' not found.",
            )

        # 1. Create CorrectionRecord
        correction = CorrectionRecord(
            request_id=req.id,
            employee_id=current_employee.id,
            correction_reason=correction_data.correction_reason.strip(),
            customer_instruction=correction_data.customer_instruction.strip(),
        )
        db.add(correction)

        # 2. Update Request Status
        req.request_status = RequestStatus.NEEDS_CORRECTION
        req.reason_code = correction_data.correction_reason.strip()

        # 3. Create Notification for Customer
        notif = Notification(
            customer_id=req.customer_id,
            request_id=req.id,
            notification_title=f"Action Required: Correction for {req.request_id}",
            notification_message=correction_data.customer_instruction.strip(),
        )
        db.add(notif)

        # 4. Audit Trail
        audit = AuditLog(
            user_id=current_employee.user_id,
            action="CORRECTION_REQUESTED",
            entity_type="REQUEST",
            entity_id=req.request_id,
            description=(
                f"Correction requested by {current_employee.full_name} ({current_employee.employee_code}): "
                f"{correction_data.correction_reason}. Instruction: {correction_data.customer_instruction}"
            ),
        )
        db.add(audit)
        db.commit()
        db.refresh(req)

        return BankService.get_request_details(db, req.request_id, current_employee, record_audit=False)

    @staticmethod
    def get_customers(
        db: Session,
        search: Optional[str] = None,
        branch: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> CustomerRecordListResponse:
        """
        Returns searchable list of customer profiles with aggregate account & request counts.
        Never returns password hashes or JWT secrets.
        """
        query = db.query(Customer).join(User, Customer.user_id == User.id)

        if branch and branch.upper() != "ALL":
            query = query.filter(Customer.branch_id.ilike(f"%{branch}%"))

        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Customer.customer_code.ilike(search_clean),
                    Customer.full_name.ilike(search_clean),
                    Customer.email.ilike(search_clean),
                )
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))
        offset = (page - 1) * page_size

        customers = query.order_by(desc(Customer.created_at)).offset(offset).limit(page_size).all()

        items = []
        for cust in customers:
            items.append(
                CustomerRecordItem(
                    id=cust.id,
                    customer_code=cust.customer_code,
                    full_name=cust.full_name,
                    email=cust.email,
                    phone=cust.phone,
                    branch_id=cust.branch_id,
                    created_at=cust.created_at,
                    total_accounts=len(cust.accounts),
                    total_requests=len(cust.requests),
                    is_active=cust.user.is_active if cust.user else True,
                )
            )

        return CustomerRecordListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_customer_details(db: Session, customer_id: int) -> CustomerDetailResponse:
        """
        Retrieves detailed profile, synthetic accounts, and recent requests for a customer.
        """
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found.",
            )

        accounts = [
            CustomerAccountItem(
                id=acc.id,
                account_number=acc.synthetic_account_number,
                account_type=acc.account_type,
                status=acc.account_status,
                branch_id=acc.branch_id,
                created_at=acc.created_at,
            )
            for acc in cust.accounts
        ]

        requests = [
            BankRequestItem(
                id=req.id,
                request_id=req.request_id,
                customer_id=req.customer_id,
                customer_code=cust.customer_code,
                customer_name=cust.full_name,
                customer_email=cust.email,
                customer_phone=cust.phone,
                customer_branch=cust.branch_id,
                service_type=req.service_type,
                request_status=req.request_status,
                priority=req.priority,
                assigned_agent_id=req.assigned_agent_id,
                assigned_agent_code=req.assigned_agent.agent_code if req.assigned_agent else None,
                assignment_version=req.assignment_version,
                review_required=req.review_required,
                completeness_status=req.completeness_status,
                reason_code=req.reason_code,
                created_at=req.created_at,
                updated_at=req.updated_at,
                completed_at=req.completed_at,
            )
            for req in sorted(cust.requests, key=lambda r: r.created_at, reverse=True)
        ]

        return CustomerDetailResponse(
            id=cust.id,
            customer_code=cust.customer_code,
            full_name=cust.full_name,
            email=cust.email,
            phone=cust.phone,
            branch_id=cust.branch_id,
            created_at=cust.created_at,
            is_active=cust.user.is_active if cust.user else True,
            accounts=accounts,
            requests=requests,
        )

    @staticmethod
    def get_customer_requests(db: Session, customer_id: int) -> List[BankRequestItem]:
        """Returns all service requests submitted by the specified customer."""
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found.",
            )

        requests = (
            db.query(Request)
            .filter(Request.customer_id == customer_id)
            .order_by(desc(Request.created_at))
            .all()
        )

        return [
            BankRequestItem(
                id=req.id,
                request_id=req.request_id,
                customer_id=req.customer_id,
                customer_code=cust.customer_code,
                customer_name=cust.full_name,
                customer_email=cust.email,
                customer_phone=cust.phone,
                customer_branch=cust.branch_id,
                service_type=req.service_type,
                request_status=req.request_status,
                priority=req.priority,
                assigned_agent_id=req.assigned_agent_id,
                assigned_agent_code=req.assigned_agent.agent_code if req.assigned_agent else None,
                assignment_version=req.assignment_version,
                review_required=req.review_required,
                completeness_status=req.completeness_status,
                reason_code=req.reason_code,
                created_at=req.created_at,
                updated_at=req.updated_at,
                completed_at=req.completed_at,
            )
            for req in requests
        ]

    @staticmethod
    def get_audit_logs(
        db: Session,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogListResponse:
        """
        Retrieves compliance audit logs with filtering and actor resolution.
        """
        query = db.query(AuditLog)

        if action and action.upper() != "ALL":
            query = query.filter(AuditLog.action.ilike(f"%{action}%"))

        if entity_type and entity_type.upper() != "ALL":
            query = query.filter(AuditLog.entity_type == entity_type.upper())

        if entity_id:
            query = query.filter(AuditLog.entity_id.ilike(f"%{entity_id}%"))

        if search:
            search_clean = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    AuditLog.description.ilike(search_clean),
                    AuditLog.action.ilike(search_clean),
                    AuditLog.entity_id.ilike(search_clean),
                )
            )

        total = query.count()
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))
        offset = (page - 1) * page_size

        logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(page_size).all()

        items = []
        for log in logs:
            actor = "System"
            role = "SYSTEM"
            if log.user:
                role = log.user.role.value if hasattr(log.user.role, "value") else str(log.user.role)
                if log.user.employee:
                    actor = f"{log.user.employee.full_name} ({log.user.employee.employee_code})"
                elif log.user.customer:
                    actor = f"{log.user.customer.full_name} ({log.user.customer.customer_code})"
                else:
                    actor = log.user.username

            items.append(
                AuditLogItem(
                    id=log.id,
                    event_id=log.event_id,
                    timestamp=log.timestamp,
                    actor=actor,
                    role=role,
                    action=log.action,
                    outcome=log.outcome or "SUCCESS",
                    request_id=log.request_id,
                    entity_type=log.entity_type,
                    entity_id=log.entity_id,
                    description=log.description,
                    source_ip=log.source_ip,
                )
            )

        return AuditLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_agent_monitoring_status(db: Session) -> AgentMonitoringResponse:
        """
        Agent Monitoring placeholder response for future phases.
        Returns the database registered agents or an empty list with informative state.
        """
        agents_db = db.query(Agent).all()
        items = [
            AgentMonitoringItem(
                id=a.id,
                agent_code=a.agent_code,
                agent_type=a.agent_type.value if hasattr(a.agent_type, "value") else str(a.agent_type),
                availability_status=a.availability_status,
                current_request_id=a.current_request_id,
            )
            for a in agents_db
        ]
        return AgentMonitoringResponse(
            message="Multi-Agent Processing will be available in upcoming development phases.",
            is_active=False,
            agents=items,
        )
