"""
BankFlow AI - Service Request Schemas
Validates request submissions, corrections, and detailed payload serialization.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from app.models.request import ServiceType, RequestStatus


# ============================================================================
# 1. SERVICE-SPECIFIC PAYLOAD SCHEMAS
# ============================================================================

class ChequeBookPayload(BaseModel):
    """Payload validation for Cheque Book Requests."""
    account_id: int = Field(..., description="Target synthetic account ID")
    cheque_leaves: int = Field(..., description="Number of leaves: 25, 50, or 100")
    delivery_preference: str = Field(..., description="Standard Postal, Branch Pickup, or Express Delivery")
    remarks: Optional[str] = Field(None, max_length=255)

    @field_validator("cheque_leaves")
    @classmethod
    def validate_leaves(cls, v: int) -> int:
        if v not in (25, 50, 100):
            raise ValueError("Cheque leaves must be 25, 50, or 100.")
        return v

    @field_validator("delivery_preference")
    @classmethod
    def validate_delivery(cls, v: str) -> str:
        valid_options = ["Standard Postal", "Branch Pickup", "Express Delivery"]
        if v not in valid_options:
            raise ValueError(f"Delivery preference must be one of: {', '.join(valid_options)}.")
        return v


class DebitCardReplacementPayload(BaseModel):
    """Payload validation for Debit Card Replacement Requests."""
    account_id: int = Field(..., description="Target synthetic account ID")
    replacement_reason: str = Field(..., description="Damaged Card, Lost Card (simulation only), or Other")
    remarks: Optional[str] = Field(None, max_length=255)

    @field_validator("replacement_reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        valid_reasons = ["Damaged Card", "Lost Card (simulation only)", "Other"]
        if v not in valid_reasons:
            raise ValueError(f"Replacement reason must be one of: {', '.join(valid_reasons)}.")
        return v


class AddressUpdatePayload(BaseModel):
    """Payload validation for Simulated Address Update Requests."""
    account_id: int = Field(..., description="Target synthetic account ID")
    new_synthetic_address: str = Field(..., min_length=5, max_length=150, description="New fictional street address")
    city: str = Field(..., min_length=2, max_length=60, description="City")
    state: str = Field(..., min_length=2, max_length=60, description="State / Province")
    postal_code: str = Field(..., min_length=3, max_length=20, description="Postal / ZIP Code")
    reason_for_update: str = Field(..., min_length=3, max_length=150, description="Reason for updating address")


class AccountApplicationPayload(BaseModel):
    """Payload validation for Account Application Pre-Screening."""
    applicant_name: str = Field(..., min_length=2, max_length=100, description="Legal applicant full name")
    email: EmailStr = Field(..., description="Applicant contact email")
    phone: str = Field(..., min_length=7, max_length=30, description="Applicant phone number")
    requested_account_type: str = Field(..., description="SAVINGS, CHECKING, FIXED_DEPOSIT, or MONEY_MARKET")
    branch_preference: str = Field(..., min_length=2, max_length=80, description="Preferred branch location")
    remarks: Optional[str] = Field(None, max_length=255)

    @field_validator("requested_account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        valid_types = ["SAVINGS", "CHECKING", "FIXED_DEPOSIT", "MONEY_MARKET"]
        if v.upper() not in valid_types:
            raise ValueError(f"Requested account type must be one of: {', '.join(valid_types)}.")
        return v.upper()


# ============================================================================
# 2. SUBMISSION AND CORRECTION SCHEMAS
# ============================================================================

class CreateServiceRequest(BaseModel):
    """Unified request submission schema."""
    service_type: ServiceType
    account_id: Optional[int] = None
    priority: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    payload: Dict[str, Any] = Field(..., description="Service-specific form parameters")


class CorrectServiceRequest(BaseModel):
    """Request correction submission schema for requests in NEEDS_CORRECTION state."""
    payload: Dict[str, Any] = Field(..., description="Corrected service parameters")
    correction_notes: Optional[str] = Field(None, max_length=255, description="Explanation of changes made")


# ============================================================================
# 3. SERIALIZATION SCHEMAS
# ============================================================================

class ServiceRequestResponse(BaseModel):
    """Comprehensive serialization schema for a banking service request."""
    id: int
    request_id: str
    customer_id: int
    account_id: Optional[int] = None
    service_type: str
    request_status: str
    priority: str
    assigned_agent_id: Optional[int] = None
    assignment_version: int
    required_skill: Optional[str] = None
    completeness_status: Optional[str] = None
    review_required: bool
    reason_code: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    current_stage: str
    retry_count: int = 0
    customer_status_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RequestListResponse(BaseModel):
    """Paginated list of service requests."""
    items: List[ServiceRequestResponse]
    total: int
    page: int
    limit: int
    pages: int
