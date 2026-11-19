"""
BankFlow AI - Authentication Endpoints
Provides customer registration, dual login pipelines, identity resolution, and logout.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Response, Request as FastAPIRequest
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    CustomerRegisterRequest,
    CustomerLoginRequest,
    BankLoginRequest,
    TokenResponse,
    AuthMessageResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.auth.dependencies import (
    get_current_user,
    extract_token_from_request,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/customer/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
    description="Registers a new customer, hashes the password using Argon2id, and issues a JWT token.",
)
def register_customer(
    data: CustomerRegisterRequest,
    request: FastAPIRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Customer self-service registration endpoint."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user, customer, token = AuthService.register_customer(db, data, client_ip)

    # Set secure HTTP-only cookie for browser-based session continuity
    response.set_cookie(
        key="bankflow_access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production
        max_age=3600,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
        role=user.role.value,
        user_id=user.id,
        username=user.username,
        redirect_url="/customer/dashboard",
    )


@router.post(
    "/customer/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Customer authentication",
    description="Authenticates customer credentials, applies rate limiting, and issues a JWT access token.",
)
def customer_login(
    data: CustomerLoginRequest,
    request: FastAPIRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Customer login endpoint with redirect to /customer/dashboard."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user, token, expires_in = AuthService.authenticate_customer(db, data, client_ip)

    response.set_cookie(
        key="bankflow_access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=expires_in,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        role=user.role.value,
        user_id=user.id,
        username=user.username,
        redirect_url="/customer/dashboard",
    )


@router.post(
    "/bank/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Bank Employee authentication",
    description="Authenticates bank staff credentials with strict role validation and issues a JWT token.",
)
def bank_login(
    data: BankLoginRequest,
    request: FastAPIRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Internal bank staff login endpoint with redirect to /bank/dashboard."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user, employee, token, expires_in = AuthService.authenticate_bank_employee(db, data, client_ip)

    response.set_cookie(
        key="bankflow_access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=expires_in,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        role=user.role.value,
        user_id=user.id,
        username=user.username,
        redirect_url="/bank/dashboard",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated identity",
    description="Returns the authenticated user's core identity profile.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Fetch authenticated caller details."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout session",
    description="Revokes the active JWT token, clears cookies, and writes an audit log.",
)
def logout(
    request: FastAPIRequest,
    response: Response,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(extract_token_from_request),
) -> AuthMessageResponse:
    """Logout endpoint invalidating token and clearing session cookie."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    current_user = None

    if token:
        try:
            current_user = get_current_user(token, db)
        except Exception:
            current_user = None

    AuthService.logout(token, current_user, client_ip, db)

    # Clear auth cookie
    response.delete_cookie(
        key="bankflow_access_token",
        httponly=True,
        samesite="lax",
    )

    return AuthMessageResponse(
        status="success",
        message="Session successfully terminated. Access token has been revoked.",
    )
