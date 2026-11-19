"""
BankFlow AI - Authentication Service
Handles customer registration, credential verification, JWT issuance, rate limiting, and audit trails.
"""

import uuid
from datetime import timedelta
from typing import Tuple, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.config import settings
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService
from app.schemas.auth import (
    CustomerRegisterRequest,
    CustomerLoginRequest,
    BankLoginRequest,
)
from app.auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    login_rate_limiter,
)
from app.auth.jwt_handler import create_access_token, revoke_token


class AuthService:
    """Authentication and session management business logic."""

    @staticmethod
    def register_customer(
        db: Session,
        data: CustomerRegisterRequest,
        client_ip: str = "127.0.0.1",
    ) -> Tuple[User, Customer, str]:
        """
        Register a new customer profile.
        - Validates input complexity
        - Enforces unique username and email
        - Hashes password using Argon2id
        - Generates synthetic customer code
        - Creates User and Customer records in an atomic transaction
        - Emits audit log entry
        """
        # Validate password strength
        is_strong, msg = validate_password_strength(data.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg,
            )

        # Check existing username
        if db.query(User).filter(User.username == data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already registered. Please choose another username.",
            )

        # Check existing email
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered. Please use another email.",
            )

        # Hash password using Argon2id
        hashed_pw = hash_password(data.password)

        # Generate synthetic customer code
        synthetic_code = f"CUST-SYN-{uuid.uuid4().hex[:6].upper()}"

        try:
            # Create user entity
            user = User(
                username=data.username,
                email=data.email,
                password_hash=hashed_pw,
                role=UserRole.CUSTOMER,
                is_active=True,
            )
            db.add(user)
            db.flush()

            # Create customer profile
            customer = Customer(
                user_id=user.id,
                customer_code=synthetic_code,
                full_name=data.full_name,
                phone=data.phone,
                email=data.email,
                branch_id="BR-MAIN-001",
            )
            db.add(customer)
            db.flush()

            # Record audit log
            AuditService.record_event(
                db=db,
                action="CUSTOMER_REGISTRATION",
                user_id=user.id,
                outcome="SUCCESS",
                entity_type="CUSTOMER",
                entity_id=synthetic_code,
                description=f"New customer '{data.username}' registered from IP {client_ip}",
                source_ip=client_ip,
                auto_commit=False,
            )
            db.commit()
            db.refresh(user)
            db.refresh(customer)

        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while creating the customer account: {str(exc)}",
            )

        # Generate access token
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
            username=user.username,
        )

        return user, customer, token

    @staticmethod
    def authenticate_customer(
        db: Session,
        data: CustomerLoginRequest,
        client_ip: str = "127.0.0.1",
    ) -> Tuple[User, str, int]:
        """
        Authenticate a customer via username or email.
        Applies rate limiting and produces audit logs.
        """
        rate_key = f"cust:{data.username_or_email.lower()}"
        is_limited, retry_after = login_rate_limiter.is_rate_limited(rate_key)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please wait {retry_after} seconds before trying again.",
                headers={"Retry-After": str(retry_after)},
            )

        # Lookup customer by username or email
        user = (
            db.query(User)
            .filter(
                or_(
                    User.username == data.username_or_email,
                    User.email == data.username_or_email,
                )
            )
            .first()
        )

        # Validate existence, role, and password
        auth_valid = False
        if user and user.role == UserRole.CUSTOMER and user.password_hash:
            auth_valid = verify_password(data.password, user.password_hash)

        if not auth_valid:
            login_rate_limiter.record_failure(rate_key)
            # Record failed login attempt in audit log
            AuditService.record_event(
                db=db,
                action="CUSTOMER_LOGIN_FAILED",
                user_id=user.id if user else None,
                outcome="FAILED",
                entity_type="AUTH",
                entity_id=data.username_or_email,
                description=f"Failed customer login attempt for '{data.username_or_email}' from IP {client_ip}",
                source_ip=client_ip,
                auto_commit=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username, email, or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify active status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your customer account has been deactivated. Please contact customer support.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Success - reset rate limit and record audit
        login_rate_limiter.record_success(rate_key)
        AuditService.record_event(
            db=db,
            action="CUSTOMER_LOGIN_SUCCESS",
            user_id=user.id,
            outcome="SUCCESS",
            entity_type="AUTH",
            entity_id=str(user.id),
            description=f"Customer '{user.username}' successfully logged in from IP {client_ip}",
            source_ip=client_ip,
            auto_commit=True,
        )

        # Token duration
        expire_minutes = (
            settings.REMEMBER_ME_ACCESS_TOKEN_EXPIRE_MINUTES
            if data.remember_me
            else settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
            username=user.username,
            expires_delta=timedelta(minutes=expire_minutes),
        )

        return user, token, expire_minutes * 60

    @staticmethod
    def authenticate_bank_employee(
        db: Session,
        data: BankLoginRequest,
        client_ip: str = "127.0.0.1",
    ) -> Tuple[User, Employee, str, int]:
        """
        Authenticate a bank employee via Employee ID or username.
        Strictly enforces BANK_EMPLOYEE role.
        """
        rate_key = f"emp:{data.employee_id_or_username.lower()}"
        is_limited, retry_after = login_rate_limiter.is_rate_limited(rate_key)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please wait {retry_after} seconds before trying again.",
                headers={"Retry-After": str(retry_after)},
            )

        # Lookup employee by employee_code or user username
        employee = (
            db.query(Employee)
            .join(User, Employee.user_id == User.id)
            .filter(
                or_(
                    Employee.employee_code == data.employee_id_or_username,
                    User.username == data.employee_id_or_username,
                )
            )
            .first()
        )

        user: Optional[User] = employee.user if employee else None

        auth_valid = False
        if (
            user
            and user.role in (UserRole.BANK_EMPLOYEE, UserRole.SUPERVISOR, UserRole.ADMINISTRATOR)
            and user.password_hash
        ):
            auth_valid = verify_password(data.password, user.password_hash)

        if not auth_valid:
            login_rate_limiter.record_failure(rate_key)
            AuditService.record_event(
                db=db,
                action="BANK_LOGIN_FAILED",
                user_id=user.id if user else None,
                outcome="FAILED",
                entity_type="AUTH",
                entity_id=data.employee_id_or_username,
                description=f"Failed bank employee login attempt for '{data.employee_id_or_username}' from IP {client_ip}",
                source_ip=client_ip,
                auto_commit=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid employee credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bank employee account is inactive. Please contact bank administration.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        login_rate_limiter.record_success(rate_key)
        AuditService.record_event(
            db=db,
            action="BANK_LOGIN_SUCCESS",
            user_id=user.id,
            outcome="SUCCESS",
            entity_type="AUTH",
            entity_id=employee.employee_code,
            description=f"Bank employee '{user.username}' ({employee.employee_code}) logged in from IP {client_ip}",
            source_ip=client_ip,
            auto_commit=True,
        )

        token = create_access_token(
            user_id=user.id,
            role=user.role.value,
            username=user.username,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return user, employee, token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @staticmethod
    def logout(token: Optional[str], user: Optional[User], client_ip: str, db: Session) -> None:
        """
        Revoke active token and record logout event in audit logs.
        """
        if token:
            revoke_token(token)

        if user:
            AuditService.record_event(
                db=db,
                action="USER_LOGOUT",
                user_id=user.id,
                outcome="SUCCESS",
                entity_type="AUTH",
                entity_id=str(user.id),
                description=f"User '{user.username}' logged out from IP {client_ip}",
                source_ip=client_ip,
                auto_commit=True,
            )
