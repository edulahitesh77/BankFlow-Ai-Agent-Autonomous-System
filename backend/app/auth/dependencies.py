"""
BankFlow AI - Authentication Dependencies
Provides FastAPI dependencies for user extraction, JWT validation, and RBAC enforcement.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request as FastAPIRequest
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.auth.jwt_handler import decode_access_token

# OAuth2 password bearer with auto_error=False so we can provide clean custom responses
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/customer/login",
    auto_error=False,
)


def extract_token_from_request(
    request: FastAPIRequest,
    header_token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[str]:
    """
    Extract JWT token from either Authorization header or secure auth cookie.
    Allows flexibility across client configurations.
    """
    if header_token:
        return header_token

    # Check cookies as fallback
    cookie_token = request.cookies.get("bankflow_access_token")
    if cookie_token:
        return cookie_token

    return None


def get_current_user(
    token: Optional[str] = Depends(extract_token_from_request),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the incoming JWT token and resolve the active User entity from the database.
    Rejects missing, expired, invalid, or revoked tokens with HTTP 401.
    Rejects inactive user accounts with HTTP 401.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user identifier in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_customer(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Role-based dependency requiring the authenticated identity to be a CUSTOMER.
    Returns HTTP 403 Forbidden if user role is not CUSTOMER.
    """
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Customer privileges required",
        )
    return current_user


def require_bank_employee(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Role-based dependency requiring the authenticated identity to be Bank Staff
    (BANK_EMPLOYEE, SUPERVISOR, or ADMINISTRATOR).
    Returns HTTP 403 Forbidden if user role is not authorized.
    """
    if current_user.role not in (
        UserRole.BANK_EMPLOYEE,
        UserRole.SUPERVISOR,
        UserRole.ADMINISTRATOR,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Bank employee privileges required",
        )
    return current_user


def require_supervisor(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Role-based dependency requiring the authenticated identity to have SUPERVISOR or ADMINISTRATOR role.
    Returns HTTP 403 Forbidden if user role is not SUPERVISOR or ADMINISTRATOR.
    """
    if current_user.role not in (UserRole.SUPERVISOR, UserRole.ADMINISTRATOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Supervisor privileges required",
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Role-based dependency requiring the authenticated identity to be an ADMINISTRATOR.
    Returns HTTP 403 Forbidden if user role is not ADMINISTRATOR.
    """
    if current_user.role != UserRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Administrator privileges required",
        )
    return current_user


def require_roles(*allowed_roles: UserRole):
    """Factory creating a FastAPI dependency enforcing any of the specified roles."""
    def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Required role in {[r.value for r in allowed_roles]}",
            )
        return current_user
    return _role_checker
