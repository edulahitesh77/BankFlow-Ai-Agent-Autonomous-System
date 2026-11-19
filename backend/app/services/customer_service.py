"""
BankFlow AI - Customer Service
Manages customer dashboard metrics, synthetic accounts, and permitted profile edits.
"""

import uuid
from typing import List
from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.models.account import Account
from app.models.request import Request, RequestStatus
from app.models.audit_log import AuditLog
from app.schemas.customer import (
    CustomerDashboardResponse,
    DashboardSummary,
    CustomerProfileUpdateRequest,
    CreateSyntheticAccountRequest,
)
from app.schemas.user import AccountSummary, CustomerProfileResponse
from app.services.request_service import RequestService


class CustomerService:
    """Service providing customer dashboard aggregations, synthetic accounts, and profile management."""

    @staticmethod
    def get_dashboard_data(db: Session, customer: Customer) -> CustomerDashboardResponse:
        """
        Compute top summary card metrics and recent request history for the authenticated customer.
        All calculations query strictly by customer.id.
        """
        # Accounts count
        total_accounts = (
            db.query(Account).filter(Account.customer_id == customer.id).count()
        )

        # Requests count
        total_requests = (
            db.query(Request).filter(Request.customer_id == customer.id).count()
        )

        # Pending Requests: NEW, CLASSIFIED, QUEUED, VERIFIED, IN_SERVICE, NEEDS_CORRECTION, HUMAN_REVIEW
        pending_statuses = [
            RequestStatus.NEW,
            RequestStatus.CLASSIFIED,
            RequestStatus.QUEUED,
            RequestStatus.VERIFIED,
            RequestStatus.IN_SERVICE,
            RequestStatus.NEEDS_CORRECTION,
            RequestStatus.HUMAN_REVIEW,
        ]
        pending_requests = (
            db.query(Request)
            .filter(
                Request.customer_id == customer.id,
                Request.request_status.in_(pending_statuses),
            )
            .count()
        )

        # Completed / Finalized Requests: COMPLETED, REJECTED_INPUT, FAILED
        completed_statuses = [
            RequestStatus.COMPLETED,
            RequestStatus.REJECTED_INPUT,
            RequestStatus.FAILED,
        ]
        completed_requests = (
            db.query(Request)
            .filter(
                Request.customer_id == customer.id,
                Request.request_status.in_(completed_statuses),
            )
            .count()
        )

        # 5 Most recent requests
        recent_records = (
            db.query(Request)
            .filter(Request.customer_id == customer.id)
            .order_by(desc(Request.created_at))
            .limit(5)
            .all()
        )
        recent_requests = [RequestService.format_request_response(r) for r in recent_records]

        return CustomerDashboardResponse(
            customer_name=customer.full_name,
            customer_code=customer.customer_code,
            email=customer.email,
            branch=customer.branch_id or "Main Branch",
            summary=DashboardSummary(
                total_accounts=total_accounts,
                total_requests=total_requests,
                pending_requests=pending_requests,
                completed_requests=completed_requests,
            ),
            recent_requests=recent_requests,
        )

    @staticmethod
    def get_accounts(db: Session, customer: Customer) -> List[AccountSummary]:
        """Fetch synthetic banking accounts for the authenticated customer."""
        accounts = (
            db.query(Account)
            .filter(Account.customer_id == customer.id)
            .order_by(desc(Account.created_at))
            .all()
        )
        return [
            AccountSummary(
                id=acc.id,
                synthetic_account_number=acc.synthetic_account_number,
                account_type=acc.account_type,
                account_status=acc.account_status,
                branch_id=acc.branch_id,
                created_at=acc.created_at,
            )
            for acc in accounts
        ]

    @staticmethod
    def create_synthetic_account(
        db: Session,
        customer: Customer,
        data: CreateSyntheticAccountRequest,
        client_ip: str = "127.0.0.1",
    ) -> AccountSummary:
        """
        Generate a simulated synthetic banking account for the customer.
        Fictional data for testing and simulation purposes only.
        """
        # Generate 10-digit synthetic account number
        rand_suffix = f"{uuid.uuid4().int % 10000000000:010d}"
        synthetic_num = f"SYN-ACC-{rand_suffix}"

        account = Account(
            customer_id=customer.id,
            synthetic_account_number=synthetic_num,
            account_type=data.account_type.upper(),
            account_status="ACTIVE",
            branch_id=data.branch_id or "BR-MAIN-001",
        )
        db.add(account)
        db.flush()

        audit = AuditLog(
            user_id=customer.user_id,
            action="SYNTHETIC_ACCOUNT_CREATED",
            entity_type="ACCOUNT",
            entity_id=synthetic_num,
            description=f"Generated synthetic {data.account_type} account ({synthetic_num}) for customer {customer.customer_code} from IP {client_ip}",
        )
        db.add(audit)
        db.commit()
        db.refresh(account)

        return AccountSummary(
            id=account.id,
            synthetic_account_number=account.synthetic_account_number,
            account_type=account.account_type,
            account_status=account.account_status,
            branch_id=account.branch_id,
            created_at=account.created_at,
        )

    @staticmethod
    def update_profile(
        db: Session,
        customer: Customer,
        data: CustomerProfileUpdateRequest,
        client_ip: str = "127.0.0.1",
    ) -> CustomerProfileResponse:
        """
        Update authorized profile fields (full_name, phone).
        Disallows customer modifications to user_id, customer_code, email, or role.
        """
        changes = []
        if data.full_name and data.full_name.strip():
            old_name = customer.full_name
            customer.full_name = data.full_name.strip()
            changes.append(f"name: '{old_name}' -> '{customer.full_name}'")

        if data.phone is not None:
            old_phone = customer.phone
            customer.phone = data.phone.strip() if data.phone.strip() else None
            changes.append(f"phone: '{old_phone}' -> '{customer.phone}'")

        if changes:
            audit = AuditLog(
                user_id=customer.user_id,
                action="CUSTOMER_PROFILE_UPDATED",
                entity_type="CUSTOMER",
                entity_id=customer.customer_code,
                description=f"Customer updated profile: {', '.join(changes)} from IP {client_ip}",
            )
            db.add(audit)
            db.commit()
            db.refresh(customer)

        accounts_summary = [
            AccountSummary(
                id=acc.id,
                synthetic_account_number=acc.synthetic_account_number,
                account_type=acc.account_type,
                account_status=acc.account_status,
                branch_id=acc.branch_id,
                created_at=acc.created_at,
            )
            for acc in customer.accounts
        ]

        return CustomerProfileResponse(
            id=customer.id,
            user_id=customer.user_id,
            customer_code=customer.customer_code,
            full_name=customer.full_name,
            phone=customer.phone,
            email=customer.email,
            branch_id=customer.branch_id,
            created_at=customer.created_at,
            role="CUSTOMER",
            accounts=accounts_summary,
        )
