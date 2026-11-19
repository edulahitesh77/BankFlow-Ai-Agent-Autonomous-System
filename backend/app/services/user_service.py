"""
BankFlow AI - User and Profile Service
Handles bank employee provisioning and role-scoped profile resolution.
"""

from typing import Tuple, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.audit_log import AuditLog
from app.schemas.user import (
    CustomerProfileResponse,
    EmployeeProfileResponse,
    AccountSummary,
)
from app.auth.security import hash_password


class UserService:
    """User profile management and controlled staff provisioning."""

    @staticmethod
    def provision_bank_employee(
        db: Session,
        username: str,
        email: str,
        password: str,
        employee_code: str,
        full_name: str,
        department: Optional[str] = "Operations",
        designation: Optional[str] = "Bank Officer",
        branch_id: Optional[str] = "BR-MAIN-001",
    ) -> Tuple[User, Employee]:
        """
        Controlled internal provisioning for bank employee accounts.
        Never exposed to public registration.
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            # If user exists with employee profile, update password if needed
            if existing_user.employee:
                existing_user.password_hash = hash_password(password)
                existing_user.is_active = True
                db.commit()
                db.refresh(existing_user)
                return existing_user, existing_user.employee

        hashed_pw = hash_password(password)

        user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,
            role=UserRole.BANK_EMPLOYEE,
            is_active=True,
        )
        db.add(user)
        db.flush()

        employee = Employee(
            user_id=user.id,
            employee_code=employee_code,
            full_name=full_name,
            department=department,
            designation=designation,
            branch_id=branch_id,
        )
        db.add(employee)
        db.flush()

        audit = AuditLog(
            user_id=user.id,
            action="EMPLOYEE_PROVISIONED",
            entity_type="EMPLOYEE",
            entity_id=employee_code,
            description=f"Bank employee '{username}' ({employee_code}) provisioned successfully",
        )
        db.add(audit)
        db.commit()
        db.refresh(user)
        db.refresh(employee)

        return user, employee

    @staticmethod
    def get_customer_profile(db: Session, user: User) -> CustomerProfileResponse:
        """Retrieve the customer profile for an authenticated customer user."""
        customer = user.customer
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer profile not found for the authenticated user",
            )

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
            user_id=user.id,
            customer_code=customer.customer_code,
            full_name=customer.full_name,
            phone=customer.phone,
            email=customer.email,
            branch_id=customer.branch_id,
            created_at=customer.created_at,
            role="CUSTOMER",
            accounts=accounts_summary,
        )

    @staticmethod
    def get_employee_profile(db: Session, user: User) -> EmployeeProfileResponse:
        """Retrieve the employee profile for an authenticated bank employee user."""
        employee = user.employee
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found for the authenticated user",
            )

        return EmployeeProfileResponse(
            id=employee.id,
            user_id=user.id,
            employee_code=employee.employee_code,
            full_name=employee.full_name,
            department=employee.department,
            designation=employee.designation,
            branch_id=employee.branch_id,
            created_at=employee.created_at,
            role="BANK_EMPLOYEE",
        )
