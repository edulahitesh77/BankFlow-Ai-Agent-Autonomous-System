"""
BankFlow AI - Customer Domain Routes
Provides secure endpoints for customer dashboard metrics, accounts, service requests, and profile.
Protected strictly by require_customer dependency.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, Request as FastAPIRequest
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerDashboardResponse,
    CustomerProfileUpdateRequest,
    CreateSyntheticAccountRequest,
)
from app.schemas.user import CustomerProfileResponse, AccountSummary
from app.schemas.request import (
    CreateServiceRequest,
    CorrectServiceRequest,
    ServiceRequestResponse,
    RequestListResponse,
)
from app.schemas.notification import NotificationListResponse, NotificationItem
from app.services.customer_service import CustomerService
from app.services.request_service import RequestService
from app.auth.dependencies import require_customer

router = APIRouter(prefix="/api/customer", tags=["Customer Portal"])


def get_active_customer(current_user: User = Depends(require_customer)) -> Customer:
    """Dependency resolving and validating the active customer entity."""
    customer = current_user.customer
    if not customer:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer record not found for the authenticated user identity.",
        )
    return customer


# ============================================================================
# 1. CUSTOMER DASHBOARD
# ============================================================================

@router.get(
    "/dashboard",
    response_model=CustomerDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get customer dashboard metrics",
    description="Returns aggregate card metrics (accounts, requests, pending, completed) and recent requests.",
)
def get_customer_dashboard(
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> CustomerDashboardResponse:
    """Fetch customer dashboard summary metrics."""
    return CustomerService.get_dashboard_data(db, customer)


# ============================================================================
# 2. MY ACCOUNTS
# ============================================================================

@router.get(
    "/accounts",
    response_model=List[AccountSummary],
    status_code=status.HTTP_200_OK,
    summary="List customer synthetic bank accounts",
    description="Returns all synthetic accounts owned by the authenticated customer.",
)
def get_customer_accounts(
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> List[AccountSummary]:
    """Retrieve all synthetic accounts belonging strictly to the caller."""
    return CustomerService.get_accounts(db, customer)


@router.post(
    "/accounts",
    response_model=AccountSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a synthetic demo account",
    description="Generates an educational synthetic banking account for testing request workflows.",
)
def create_customer_account(
    data: CreateSyntheticAccountRequest,
    request: FastAPIRequest,
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> AccountSummary:
    """Provision a new synthetic account for the customer."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    return CustomerService.create_synthetic_account(db, customer, data, client_ip)


# ============================================================================
# 3. SERVICE REQUESTS
# ============================================================================

@router.post(
    "/requests",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new banking service request",
    description="Validates form parameters, creates a new request in NEW status, and assigns a unique ID.",
)
def submit_service_request(
    data: CreateServiceRequest,
    request: FastAPIRequest,
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> ServiceRequestResponse:
    """Submit Cheque Book, Debit Card Replacement, Address Update, or Account Application request."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    return RequestService.submit_service_request(db, customer, data, client_ip)


@router.get(
    "/requests",
    response_model=RequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all submitted service requests",
    description="Returns paginated requests submitted by the customer with optional status filtering and search.",
)
def list_service_requests(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter: ALL, PENDING, COMPLETED, NEEDS_CORRECTION, etc."),
    search: Optional[str] = Query(None, description="Search by Request ID or service type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> RequestListResponse:
    """Fetch paginated requests for the authenticated customer."""
    return RequestService.get_customer_requests(
        db=db,
        customer_id=customer.id,
        status_filter=status_filter,
        search=search,
        page=page,
        limit=limit,
    )


@router.get(
    "/requests/{request_id}",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get request details and tracking state",
    description="Returns full request details, progress stage, and payload. Returns 404 if unauthorized.",
)
def get_service_request_detail(
    request_id: str,
    request: FastAPIRequest,
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> ServiceRequestResponse:
    """Fetch specific request details. Enforces customer data ownership."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    return RequestService.get_customer_request_by_id(
        db=db,
        customer_id=customer.id,
        request_id=request_id,
        user_id=customer.user_id,
        client_ip=client_ip,
    )


# ============================================================================
# 4. REQUEST CORRECTIONS
# ============================================================================

@router.put(
    "/requests/{request_id}/correction",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit corrections for a request",
    description="Updates request payload and increments version strictly when status is NEEDS_CORRECTION.",
)
def correct_service_request(
    request_id: str,
    data: CorrectServiceRequest,
    request: FastAPIRequest,
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> ServiceRequestResponse:
    """Submit corrected request information. Resets status to NEW for re-processing."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    return RequestService.submit_correction(
        db=db,
        customer_id=customer.id,
        request_id=request_id,
        data=data,
        user_id=customer.user_id,
        client_ip=client_ip,
    )


# ============================================================================
# 5. CUSTOMER PROFILE
# ============================================================================

@router.get(
    "/profile",
    response_model=CustomerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated customer profile",
    description="Returns personal profile details and synthetic accounts for the logged-in customer.",
)
def get_customer_profile(
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> CustomerProfileResponse:
    """Retrieve customer profile. Requires CUSTOMER role."""
    from app.services.user_service import UserService
    return UserService.get_customer_profile(db, customer.user)


@router.put(
    "/profile",
    response_model=CustomerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update customer profile",
    description="Allows updating permitted fields (full_name, phone). Disallows modifying code, email, or role.",
)
def update_customer_profile(
    data: CustomerProfileUpdateRequest,
    request: FastAPIRequest,
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> CustomerProfileResponse:
    """Update authorized personal details."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    return CustomerService.update_profile(db, customer, data, client_ip)


# ============================================================================
# 6. CUSTOMER NOTIFICATIONS
# ============================================================================

@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get customer notifications",
    description="Returns notifications generated by bank employee reviews or corrections.",
)
def get_customer_notifications(
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    """Retrieve notifications for the authenticated customer."""
    from app.models.notification import Notification
    from sqlalchemy import desc

    notifs = (
        db.query(Notification)
        .filter(Notification.customer_id == customer.id)
        .order_by(desc(Notification.created_at))
        .all()
    )
    items = [
        NotificationItem(
            id=n.id,
            customer_id=n.customer_id,
            request_id=n.request_id,
            notification_title=n.notification_title,
            notification_message=n.notification_message,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifs
    ]
    unread = sum(1 for n in items if not n.is_read)
    return NotificationListResponse(items=items, unread_count=unread, total=len(items))


@router.put(
    "/notifications/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Mark notification as read",
)
def mark_notification_read(
    notification_id: int,
    customer: Customer = Depends(get_active_customer),
    db: Session = Depends(get_db),
):
    """Marks a notification as read."""
    from app.models.notification import Notification
    from fastapi import HTTPException
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.customer_id == customer.id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    notif.is_read = True
    db.commit()
    return {"status": "success", "message": "Notification marked as read."}

