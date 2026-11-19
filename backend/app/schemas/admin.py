"""
BankFlow AI - Administrator Schemas
Schemas for user role administration, security configuration inspection, and system controls.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.user import UserRole


class AdminUserItem(BaseModel):
    """User summary item for administrator review."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    """Paginated list of system identities."""
    total: int
    items: List[AdminUserItem]


class UpdateUserRoleRequest(BaseModel):
    """Request payload to change an identity's access role."""
    role: UserRole = Field(..., description="Target system role (CUSTOMER, BANK_EMPLOYEE, SUPERVISOR, ADMINISTRATOR)")


class SecurityStatusResponse(BaseModel):
    """High-level security architecture audit summary."""
    argon2id_hashing: bool = True
    aes_256_gcm_encryption: bool = True
    encryption_key_bits: int = 256
    jwt_algorithm: str
    rate_limiter_active: bool = True
    total_audit_events: int
    environment: str
