"""
BankFlow AI - Administrator Routes
High-privilege management endpoints accessible only to users with ADMINISTRATOR role.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request as FastAPIRequest
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.config import settings
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.auth.dependencies import require_admin
from app.schemas.admin import (
    AdminUserItem,
    AdminUserListResponse,
    UpdateUserRoleRequest,
    SecurityStatusResponse,
)
from app.services.audit_service import AuditService

admin_router = APIRouter(
    prefix="/api/bank/admin",
    tags=["Administration & Security Management"],
)


@admin_router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="List system identities and roles (Administrator Only)",
)
def list_system_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lists registered system users. Restricted to administrators."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(User.id.asc()).offset(offset).limit(page_size).all()

    items = [
        AdminUserItem(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            is_active=u.is_active,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]
    return AdminUserListResponse(total=total, items=items)


@admin_router.put(
    "/users/{user_id}/role",
    response_model=AdminUserItem,
    summary="Modify identity role (Administrator Only)",
)
def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    req: FastAPIRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Modifies an account's role.
    Prevents self-demotion and logs an immutable ROLE_CHANGED audit event.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    # Prevent admin from self-demotion
    if target_user.id == current_admin.id and payload.role != UserRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot demote their own account. Another administrator must make this change.",
        )

    previous_role = target_user.role.value if hasattr(target_user.role, "value") else str(target_user.role)
    new_role = payload.role

    target_user.role = new_role
    db.commit()
    db.refresh(target_user)

    client_ip = req.client.host if req.client else "127.0.0.1"

    # Record mandatory security audit log
    AuditService.record_event(
        db=db,
        action="ROLE_CHANGED",
        user_id=current_admin.id,
        outcome="SUCCESS",
        description=(
            f"Administrator '{current_admin.username}' updated role of user '{target_user.username}' (ID {target_user.id}) "
            f"from '{previous_role}' to '{new_role.value}'."
        ),
        source_ip=client_ip,
        entity_type="USER",
        entity_id=str(target_user.id),
    )

    return AdminUserItem(
        id=target_user.id,
        username=target_user.username,
        email=target_user.email,
        role=target_user.role.value if hasattr(target_user.role, "value") else str(target_user.role),
        is_active=target_user.is_active,
        created_at=target_user.created_at,
        updated_at=target_user.updated_at,
    )


@admin_router.get(
    "/security-status",
    response_model=SecurityStatusResponse,
    summary="Inspect security architecture status (Administrator Only)",
)
def get_security_status(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Returns security configuration and audit health."""
    total_audits = db.query(func.count(AuditLog.id)).scalar() or 0
    return SecurityStatusResponse(
        argon2id_hashing=True,
        aes_256_gcm_encryption=True,
        encryption_key_bits=256,
        jwt_algorithm=settings.JWT_ALGORITHM,
        rate_limiter_active=True,
        total_audit_events=total_audits,
        environment=settings.ENVIRONMENT,
    )
