"""
BankFlow AI - Pydantic Schemas Package
Defines request and response schemas for API serialization and validation.
"""

from app.schemas.auth import (
    CustomerRegisterRequest,
    CustomerLoginRequest,
    BankLoginRequest,
    TokenResponse,
    AuthMessageResponse,
)
from app.schemas.user import (
    UserResponse,
    AccountSummary,
    CustomerProfileResponse,
    EmployeeProfileResponse,
)
from app.schemas.request import (
    ChequeBookPayload,
    DebitCardReplacementPayload,
    AddressUpdatePayload,
    AccountApplicationPayload,
    CreateServiceRequest,
    CorrectServiceRequest,
    ServiceRequestResponse,
    RequestListResponse,
)
from app.schemas.customer import (
    DashboardSummary,
    CustomerDashboardResponse,
    CustomerProfileUpdateRequest,
    CreateSyntheticAccountRequest,
)
from app.schemas.bank import (
    BankDashboardSummary,
    ServiceDemandItem,
    RecentActivityItem,
    BankDashboardResponse,
    SubmitReviewRequest,
    ReviewRecordResponse,
    SubmitCorrectionRequest,
    CorrectionRecordResponse,
    BankRequestItem,
    BankRequestListResponse,
    BankRequestDetailResponse,
    CustomerRecordItem,
    CustomerRecordListResponse,
    CustomerDetailResponse,
    AuditLogItem,
    AuditLogListResponse,
    AgentMonitoringResponse,
)
from app.schemas.notification import NotificationItem, NotificationListResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class ProjectInfoResponse(BaseModel):
    """Schema for root endpoint project information."""
    name: str
    version: str
    description: str
    phase: str
    status: str
    docs_url: str
    endpoints: Dict[str, str]

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Schema for backend health check response."""
    status: str
    service: str
    version: str
    environment: str

    model_config = ConfigDict(from_attributes=True)


class DatabaseHealthResponse(BaseModel):
    """Schema for database connectivity health response."""
    status: str
    reachable: bool
    database: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "CustomerRegisterRequest",
    "CustomerLoginRequest",
    "BankLoginRequest",
    "TokenResponse",
    "AuthMessageResponse",
    "UserResponse",
    "AccountSummary",
    "CustomerProfileResponse",
    "EmployeeProfileResponse",
    "ProjectInfoResponse",
    "HealthResponse",
    "DatabaseHealthResponse",
    "ChequeBookPayload",
    "DebitCardReplacementPayload",
    "AddressUpdatePayload",
    "AccountApplicationPayload",
    "CreateServiceRequest",
    "CorrectServiceRequest",
    "ServiceRequestResponse",
    "RequestListResponse",
    "DashboardSummary",
    "CustomerDashboardResponse",
    "CustomerProfileUpdateRequest",
    "CreateSyntheticAccountRequest",
]
