"""
BankFlow AI - Bank Employee Domain Routes
Protected endpoints accessible strictly by internal BANK_EMPLOYEE staff.
Covers dashboard metrics, full request operations, review decisions, corrections,
customer records, compliance audit logging, and multi-agent monitoring status.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.schemas.user import EmployeeProfileResponse
from app.schemas.bank import (
    BankDashboardResponse,
    BankRequestListResponse,
    BankRequestDetailResponse,
    BankRequestItem,
    SubmitReviewRequest,
    SubmitCorrectionRequest,
    CustomerRecordListResponse,
    CustomerDetailResponse,
    AuditLogListResponse,
    AgentMonitoringResponse,
)
from app.services.user_service import UserService
from app.services.bank_service import BankService
from app.auth.dependencies import require_bank_employee

router = APIRouter(prefix="/api/bank", tags=["Bank Staff Portal"])


@router.get(
    "/profile",
    response_model=EmployeeProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated bank employee profile",
    description="Returns designation, employee code, department, and internal staff details.",
)
def get_bank_employee_profile(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> EmployeeProfileResponse:
    """Retrieve bank employee profile. Requires BANK_EMPLOYEE role."""
    return UserService.get_employee_profile(db, current_user)


@router.get(
    "/dashboard",
    response_model=BankDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get bank dashboard statistics",
    description="Returns summary counts, service distribution, status breakdown, service demand, and recent audit activity.",
)
def get_dashboard_metrics(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankDashboardResponse:
    """Retrieve aggregate banking statistics from real database records."""
    return BankService.get_dashboard_metrics(db)


# Specific request queues (Declared BEFORE /{request_id} parameterized route)

@router.get(
    "/requests/pending",
    response_model=BankRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get pending requests awaiting processing",
)
def get_pending_requests(
    search: Optional[str] = Query(None, description="Search request ID or customer"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankRequestListResponse:
    """List requests awaiting processing or validation."""
    return BankService.get_pending_requests(db, page=page, page_size=page_size, search=search)


@router.get(
    "/requests/human-review",
    response_model=BankRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get requests requiring human review",
)
def get_human_review_requests(
    search: Optional[str] = Query(None, description="Search request ID or customer"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankRequestListResponse:
    """List requests where review_required=True or status is HUMAN_REVIEW."""
    return BankService.get_human_review_requests(db, page=page, page_size=page_size, search=search)


@router.get(
    "/requests/needs-correction",
    response_model=BankRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get requests in NEEDS_CORRECTION status",
)
def get_needs_correction_requests(
    search: Optional[str] = Query(None, description="Search request ID or customer"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankRequestListResponse:
    """List requests flagged for customer corrections."""
    return BankService.get_needs_correction_requests(db, page=page, page_size=page_size, search=search)


@router.get(
    "/requests/rejected",
    response_model=BankRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get rejected requests",
)
def get_rejected_requests(
    search: Optional[str] = Query(None, description="Search request ID or customer"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankRequestListResponse:
    """List rejected customer service requests."""
    return BankService.get_rejected_requests(db, page=page, page_size=page_size, search=search)


@router.get(
    "/requests",
    response_model=BankRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all customer service requests",
    description="List and filter all banking requests with server-side pagination, search, and status/service filters.",
)
def get_all_requests(
    status: Optional[str] = Query(None, description="Filter by status (e.g. NEW, CLASSIFIED, COMPLETED)"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, URGENT)"),
    branch: Optional[str] = Query(None, description="Filter by customer branch"),
    search: Optional[str] = Query(None, description="Search by Request ID, Customer Code, or Name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankRequestListResponse:
    """List all customer service requests with filtering and search."""
    return BankService.get_requests(
        db=db,
        status_filter=status,
        service_type_filter=service_type,
        priority_filter=priority,
        branch_filter=branch,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/requests/{request_id}",
    response_model=BankRequestDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed request information",
    description="Returns full customer info, service parameters, review history, and records employee inspection in audit log.",
)
def get_request_details(
    request_id: str,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankRequestDetailResponse:
    """Inspect request details and record audit log entry."""
    employee = current_user.employee
    return BankService.get_request_details(db, request_id, current_employee=employee, record_audit=True)


@router.post(
    "/requests/{request_id}/review",
    response_model=BankRequestDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Record human review decision",
    description="Submits an employee review outcome: REVIEW_COMPLETED, ADDITIONAL_INFORMATION_REQUIRED, REVIEW_REJECTED, or ESCALATED.",
)
def submit_review_decision(
    request_id: str,
    review_data: SubmitReviewRequest,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankRequestDetailResponse:
    """Record a review decision and advance or update the workflow state."""
    employee = current_user.employee
    return BankService.submit_review_decision(
        db=db,
        request_id=request_id,
        current_employee=employee,
        review_data=review_data,
    )


@router.post(
    "/requests/{request_id}/request-correction",
    response_model=BankRequestDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Flag request for customer correction",
    description="Updates status to NEEDS_CORRECTION, saves instruction, and notifies customer.",
)
def request_correction(
    request_id: str,
    correction_data: SubmitCorrectionRequest,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> BankRequestDetailResponse:
    """Request customer correction and notify the customer."""
    employee = current_user.employee
    return BankService.request_correction(
        db=db,
        request_id=request_id,
        current_employee=employee,
        correction_data=correction_data,
    )


# Customer Records Endpoints

@router.get(
    "/customers",
    response_model=CustomerRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get customer records",
    description="Search and browse customer profiles with branch filters and account/request totals.",
)
def get_customers(
    search: Optional[str] = Query(None, description="Search by name, customer code, or email"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> CustomerRecordListResponse:
    """Search and browse synthetic customer records."""
    return BankService.get_customers(
        db=db,
        search=search,
        branch=branch,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get customer profile details and accounts",
)
def get_customer_details(
    customer_id: int,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> CustomerDetailResponse:
    """Inspect customer profile, synthetic accounts, and recent request history."""
    return BankService.get_customer_details(db, customer_id=customer_id)


@router.get(
    "/customers/{customer_id}/requests",
    response_model=List[BankRequestItem],
    status_code=status.HTTP_200_OK,
    summary="Get all requests for a customer",
)
def get_customer_requests(
    customer_id: int,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> List[BankRequestItem]:
    """Retrieve full request history for the specified customer."""
    return BankService.get_customer_requests(db, customer_id=customer_id)


# Audit Logs Endpoint

@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get compliance audit logs",
    description="Retrieve backend audit log entries with action, entity, actor resolution, and filters.",
)
def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action name"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (REQUEST, USER, etc.)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity identifier"),
    search: Optional[str] = Query(None, description="Search description or action"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    """Retrieve paginated audit logs for regulatory compliance."""
    return BankService.get_audit_logs(
        db=db,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        search=search,
        page=page,
        page_size=page_size,
    )
