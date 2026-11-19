"""
BankFlow AI - Agent and Simulation Schemas
Pydantic v2 schemas for multi-agent status, control endpoints, and test scenario benchmarks.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AgentDetailResponse(BaseModel):
    """Detailed telemetry and operational status for an individual agent instance."""
    id: Optional[int] = None
    agent_code: str
    agent_type: str
    availability_status: str
    processing_status: str
    current_request_id: Optional[str] = None
    assigned_version: int = 0
    completed_work_count: int = 0
    last_active_at: Optional[str] = None
    branch_id: Optional[str] = None


class AgentListResponse(BaseModel):
    """List of all registered agents in the multi-agent system."""
    agents: List[AgentDetailResponse]
    total: int


class AgentStatisticsResponse(BaseModel):
    """Aggregate statistics on agent availability and processing volume."""
    total_agents: int
    available_agents: int
    busy_agents: int
    unavailable_agents: int
    total_requests_processed: int


class SimulationStartRequest(BaseModel):
    """Configuration options for starting background simulation."""
    num_request_agents: int = Field(3, ge=1, le=20, description="Number of concurrent RequestAgent instances")
    tick_delay_seconds: float = Field(0.5, ge=0.01, le=5.0, description="Delay between ticks in seconds")
    scenario_name: str = Field("MANUAL_OPERATION", description="Descriptive label for simulation run")


class SimulationStatusResponse(BaseModel):
    """Real-time operational status of the background simulation runner."""
    is_running: bool
    scenario: str
    current_tick: int
    active_workers: int
    total_agents: int
    agents: List[Dict[str, Any]]
    logs_preview: List[str]


class SimulationStatisticsResponse(BaseModel):
    """High-level simulation throughput and pipeline metrics."""
    total_requests: int
    processed_requests: int
    pending_requests: int
    completed_requests: int
    human_review_requests: int
    correction_requests: int
    failed_requests: int
    active_agents: int


class RunTestScenarioRequest(BaseModel):
    """Parameters for running a controlled benchmark scenario."""
    scenario_id: int = Field(
        1,
        ge=1,
        le=5,
        description="Scenario 1 (Normal), 2 (High Load), 3 (Incomplete), 4 (Mixed), 5 (Human Review)",
    )


class RunTestScenarioResponse(BaseModel):
    """Results and telemetry from a completed simulation scenario benchmark."""
    scenario_id: int
    scenario_name: str
    total_requests: int
    request_agents_count: int
    duration_seconds: float
    peak_concurrency: int
    status_breakdown: Dict[str, int]
    execution_logs: List[str]


# ----------------------------------------------------------------------------
# Real-Time Agent Monitoring Dashboard Schemas
# ----------------------------------------------------------------------------

class RealtimeAgentInfo(BaseModel):
    """Live telemetry and status for an individual agent in the swarm."""
    id: Optional[int] = None
    agent_code: str
    agent_name: str
    agent_type: str
    category: str  # CORE_PIPELINE, REQUEST_POOL, SERVICE_POOL, SUPERVISOR
    availability_status: str  # AVAILABLE, BUSY, UNAVAILABLE
    health_status: str  # HEALTHY, IDLE, BUSY, UNRESPONSIVE, FAILED, RECOVERING
    status: str  # IDLE, BUSY, PROCESSING, FAILED, RECOVERING
    current_request_id: Optional[str] = None
    current_stage: str  # IDLE, NEW, CLASSIFIED, QUEUED, VERIFIED, IN_SERVICE, COMPLETED, etc.
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_heartbeat: Optional[str] = None
    last_active_at: Optional[str] = None
    supported_skills: List[str] = []


class RealtimeEventLogItem(BaseModel):
    """Immutable timestamped event in the live monitoring stream."""
    event_id: str
    timestamp: str
    category: str  # COMMUNICATION, ASSIGNMENT, COMPLETION, FAILURE, RECOVERY
    sender: str
    receiver: Optional[str] = None
    request_id: Optional[str] = None
    message: str
    severity: str  # info, success, warning, error
    details: Optional[Dict[str, Any]] = None


class RealtimeMonitoringMetrics(BaseModel):
    """High-level request throughput and worker availability metrics."""
    total_requests: int
    processed_requests: int
    failed_requests: int
    pending_requests: int
    human_review_requests: int
    correction_requests: int
    active_workers: int
    total_agents: int
    idle_agents: int


class RealtimeMonitoringResponse(BaseModel):
    """Complete real-time monitoring telemetry payload."""
    is_running: bool
    status_indicator: str  # "LIVE" or "SIMULATION STOPPED"
    current_tick: int
    scenario_name: str
    timestamp: str
    metrics: RealtimeMonitoringMetrics
    agents: List[RealtimeAgentInfo]
    events: List[RealtimeEventLogItem]

