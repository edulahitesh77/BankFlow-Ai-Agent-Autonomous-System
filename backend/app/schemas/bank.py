"""
BankFlow AI - Bank Employee Schemas
Pydantic v2 schemas for bank employee operations, request reviews, corrections, and audit logging.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.request import ServiceType, RequestStatus
from app.models.review_record import ReviewDecision


# --- Dashboard Overview Schemas ---

class BankDashboardSummary(BaseModel):
    """Aggregate statistics for bank employee management dashboard."""
    total_requests: int
    new_requests: int
    pending_requests: int
    human_review_requests: int
    needs_correction_requests: int
    completed_requests: int
    rejected_requests: int
    total_customers: int
    total_accounts: int


class ServiceDemandItem(BaseModel):
    """Service request demand metrics."""
    service_type: ServiceType
    count: int
    percentage: float


class RecentActivityItem(BaseModel):
    """Recent event item for bank activity stream."""
    id: int
    timestamp: datetime
    actor: str
    role: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    description: Optional[str] = None


class BankDashboardResponse(BaseModel):
    """Complete bank dashboard response payload."""
    summary: BankDashboardSummary
    request_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    service_demand: List[ServiceDemandItem]
    recent_activity: List[RecentActivityItem]


# --- Review & Correction Schemas ---

class SubmitReviewRequest(BaseModel):
    """Input payload for recording an employee review decision."""
    decision: ReviewDecision
    internal_note: str = Field(..., min_length=3, max_length=2000, description="Internal review note / rationale")
    reason_code: Optional[str] = Field(None, max_length=100)


class ReviewRecordResponse(BaseModel):
    """Output schema for a review record."""
    id: int
    request_id: int
    employee_id: Optional[int] = None
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    review_decision: str
    internal_note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SubmitCorrectionRequest(BaseModel):
    """Input payload for requesting customer corrections on a service request."""
    correction_reason: str = Field(..., min_length=3, max_length=200, description="Reason why correction is required")
    customer_instruction: str = Field(..., min_length=5, max_length=2000, description="Actionable instruction for the customer")


class CorrectionRecordResponse(BaseModel):
    """Output schema for a correction record."""
    id: int
    request_id: int
    employee_id: Optional[int] = None
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    correction_reason: str
    customer_instruction: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Request Details & List Schemas ---

class BankRequestItem(BaseModel):
    """Item summary in bank employee request tables."""
    id: int
    request_id: str
    customer_id: int
    customer_code: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_branch: Optional[str] = None
    service_type: ServiceType
    request_status: RequestStatus
    priority: str
    assigned_agent_id: Optional[int] = None
    assigned_agent_code: Optional[str] = None
    assignment_version: int
    review_required: bool
    completeness_status: Optional[str] = None
    reason_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BankRequestListResponse(BaseModel):
    """Paginated list of customer requests for bank employees."""
    items: List[BankRequestItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class BankRequestDetailResponse(BaseModel):
    """Full request details for employee review and inspection."""
    id: int
    request_id: str
    customer_id: int
    customer_code: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_branch: Optional[str] = None
    account_id: Optional[int] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    service_type: ServiceType
    request_status: RequestStatus
    priority: str
    assigned_agent_id: Optional[int] = None
    assigned_agent_code: Optional[str] = None
    assignment_version: int
    required_skill: Optional[str] = None
    completeness_status: Optional[str] = None
    review_required: bool
    reason_code: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    reviews: List[ReviewRecordResponse] = []
    corrections: List[CorrectionRecordResponse] = []
    audit_trail: List[RecentActivityItem] = []

    model_config = {"from_attributes": True}


# --- Customer Records Schemas ---

class CustomerRecordItem(BaseModel):
    """Summary of customer profile for bank employee customer search table."""
    id: int
    customer_code: str
    full_name: str
    email: str
    phone: Optional[str] = None
    branch_id: Optional[str] = None
    created_at: datetime
    total_accounts: int
    total_requests: int
    is_active: bool

    model_config = {"from_attributes": True}


class CustomerRecordListResponse(BaseModel):
    """Paginated response for customer records."""
    items: List[CustomerRecordItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class CustomerAccountItem(BaseModel):
    """Synthetic account summary for customer detail inspection."""
    id: int
    account_number: str
    account_type: str
    status: str
    branch_id: Optional[str] = None
    created_at: datetime


class CustomerDetailResponse(BaseModel):
    """Detailed synthetic customer profile for bank employee view."""
    id: int
    customer_code: str
    full_name: str
    email: str
    phone: Optional[str] = None
    branch_id: Optional[str] = None
    created_at: datetime
    is_active: bool
    accounts: List[CustomerAccountItem] = []
    requests: List[BankRequestItem] = []


# --- Audit Log Schemas ---

class AuditLogItem(BaseModel):
    """Audit log row for bank compliance investigation."""
    id: int
    event_id: Optional[str] = None
    timestamp: datetime
    actor: Optional[str] = None
    role: Optional[str] = None
    action: str
    outcome: Optional[str] = "SUCCESS"
    request_id: Optional[str] = None
    entity_type: str
    entity_id: Optional[str] = None
    description: Optional[str] = None
    source_ip: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated list of audit events."""
    items: List[AuditLogItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Agent Placeholder Schema ---

class AgentMonitoringItem(BaseModel):
    """Schema for individual agent representation."""
    id: Optional[int] = None
    agent_code: str
    agent_type: str
    availability_status: str
    current_request_id: Optional[int] = None


class AgentMonitoringResponse(BaseModel):
    """Response schema for agent monitoring placeholder."""
    message: str
    is_active: bool
    agents: List[AgentMonitoringItem] = []
