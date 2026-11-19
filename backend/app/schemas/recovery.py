"""
BankFlow AI - Recovery Schemas (Phase 8)
Pydantic v2 schemas for agent health, failure logs, and recovery management endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentHealthSummary(BaseModel):
    """Aggregate agent health status counts."""
    total: int
    healthy: int
    busy: int
    unresponsive: int
    failed: int
    recovering: int


class RequestsRecoverySummary(BaseModel):
    """Aggregate request recovery metrics."""
    awaiting_recovery: int
    successfully_recovered: int
    human_intervention_needed: int
    total_failures_recorded: int


class CircuitBreakerStatusResponse(BaseModel):
    """Circuit breaker operational status."""
    name: str
    state: str
    failure_count: int
    failure_threshold: int
    recovery_timeout_seconds: float
    half_open_attempts: int
    half_open_max_requests: int
    last_state_change: Optional[str] = None
    last_failure_time: Optional[str] = None
    last_error_message: Optional[str] = None


class FailureRecordItem(BaseModel):
    """Individual recorded failure event."""
    failure_id: str
    agent_code: Optional[str] = None
    request_code: Optional[str] = None
    failure_type: str
    error_details: Optional[str] = None
    recovery_status: str
    retry_count: int
    created_at: Optional[str] = None
    recovered_at: Optional[str] = None


class RecoveryDashboardResponse(BaseModel):
    """Complete recovery and reliability dashboard metrics."""
    agents_summary: AgentHealthSummary
    requests_summary: RequestsRecoverySummary
    circuit_breaker: CircuitBreakerStatusResponse
    recent_failures: List[FailureRecordItem]


class ManualReassignPayload(BaseModel):
    """Payload for manual staff task reassignment."""
    target_agent_code: str = Field(..., min_length=2, max_length=50)


class SimulateCrashPayload(BaseModel):
    """Payload for simulating an agent crash."""
    agent_code: str = Field(..., min_length=2, max_length=50)
    reason: Optional[str] = "Simulated crash event"


class SimulateHeartbeatPayload(BaseModel):
    """Payload for simulating a missed heartbeat."""
    agent_code: str = Field(..., min_length=2, max_length=50)
    seconds_ago: float = 60.0
