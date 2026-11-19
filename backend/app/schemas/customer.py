"""
BankFlow AI - Customer Domain Schemas
Defines responses and update schemas for customer dashboard, accounts, and profile.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.request import ServiceRequestResponse
from app.schemas.user import AccountSummary


class DashboardSummary(BaseModel):
    """Aggregate statistics for customer summary cards."""
    total_accounts: int
    total_requests: int
    pending_requests: int
    completed_requests: int


class CustomerDashboardResponse(BaseModel):
    """Data payload for the primary customer dashboard view."""
    customer_name: str
    customer_code: str
    email: str
    branch: str
    summary: DashboardSummary
    recent_requests: List[ServiceRequestResponse]


class CustomerProfileUpdateRequest(BaseModel):
    """Schema allowing customers to update only authorized personal fields."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)


class CreateSyntheticAccountRequest(BaseModel):
    """Simulated creation of an initial or additional synthetic demo account."""
    account_type: str = Field("SAVINGS", description="SAVINGS, CHECKING, etc.")
    branch_id: Optional[str] = Field("BR-MAIN-001", max_length=50)
