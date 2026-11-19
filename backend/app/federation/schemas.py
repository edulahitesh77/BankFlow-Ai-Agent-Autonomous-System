"""
BankFlow AI - Federation Schemas (Phase 10)
Defines Pydantic v2 schemas for cross-branch requests, authorization checks,
data transfer payloads, and federation telemetry.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CrossBranchRequest(BaseModel):
    """Payload submitted by a source branch to the Federation Gateway."""
    source_branch_id: str = Field(..., description="ID of the initiating branch (e.g. BLR001)")
    destination_branch_id: str = Field(..., description="ID of the target branch (e.g. CHE001)")
    requested_scope: str = Field(..., description="Requested scope: ACCOUNT_STATUS_CONFIRMATION, CUSTOMER_KYC_VERIFICATION, etc.")
    request_id: Optional[str] = Field(None, description="Local service request ID triggering the federation query")
    correlation_id: str = Field(..., description="Unique UUID correlation ID for idempotency and traceability")
    query_params: Dict[str, Any] = Field(..., description="Query criteria (e.g. synthetic_account_number, customer_code)")


class CrossBranchResponse(BaseModel):
    """Restricted response returned by the Federation Gateway to the source branch."""
    federation_event_id: str
    correlation_id: str
    source_branch_id: str
    destination_branch_id: str
    requested_scope: str
    authorization_result: str
    status: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BranchSummaryResponse(BaseModel):
    """Branch metadata summary for federation monitoring."""
    branch_id: str
    branch_name: str
    location: str
    branch_status: str
    active_agents: int = 0
    pending_requests: int = 0
    completed_requests: int = 0
    is_gateway_enabled: bool = True


class FederationStatisticsResponse(BaseModel):
    """Aggregate cross-branch federation telemetry."""
    total_branches: int
    active_branches: int
    inactive_branches: int
    total_exchanges: int
    successful_exchanges: int
    rejected_exchanges: int
    failed_exchanges: int
    recent_events: List[Dict[str, Any]] = []


class FederationEventItem(BaseModel):
    """Individual federation audit event record."""
    federation_event_id: str
    source_branch_id: str
    destination_branch_id: str
    request_id: Optional[str] = None
    event_type: str
    requested_scope: str
    authorization_result: str
    correlation_id: str
    event_status: str
    timestamp: str
    error_message: Optional[str] = None
