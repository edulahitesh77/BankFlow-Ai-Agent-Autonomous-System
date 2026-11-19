"""
BankFlow AI - Base Banking Agent
Abstract Mesa agent representing a cooperative actor in the banking automation workflow.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
import mesa
from app.models.agent import AgentType, AgentHealthStatus


class BaseBankingAgent(mesa.Agent):
    """
    Base Mesa agent providing identity, workload tracking, availability state,
    heartbeat monitoring, and failure tracking for the BankFlow AI multi-agent system.
    """

    def __init__(
        self,
        model: mesa.Model,
        agent_code: str,
        agent_type: AgentType,
        branch_id: Optional[str] = "BR-MAIN-001",
    ):
        super().__init__(model)
        self.agent_code = agent_code
        self.agent_type = agent_type
        self.branch_id = branch_id

        # Availability & Workload State
        self.availability_status = "AVAILABLE"  # AVAILABLE, BUSY, UNAVAILABLE
        self.processing_status = "IDLE"        # IDLE, BUSY
        self.current_request_id: Optional[str] = None
        self.assigned_version: int = 0
        self.completed_work_count: int = 0
        self.last_active_at: Optional[datetime] = None

        # Phase 8: Health, heartbeats, failure & latency metrics
        self.health_status = AgentHealthStatus.HEALTHY
        self.last_heartbeat_at: Optional[datetime] = datetime.now(timezone.utc)
        self.failed_work_count: int = 0
        self.retry_count: int = 0
        self.total_processing_time_ms: float = 0.0
        self.last_error_message: Optional[str] = None
        self.task_start_time: Optional[datetime] = None
        self.is_paused: bool = False

    @property
    def is_available(self) -> bool:
        """Agent is eligible to accept new work if healthy, unpaused, marked AVAILABLE and IDLE."""
        return (
            not self.is_paused
            and self.health_status in (AgentHealthStatus.HEALTHY, AgentHealthStatus.IDLE)
            and self.availability_status == "AVAILABLE"
            and self.processing_status == "IDLE"
            and self.current_request_id is None
        )

    def send_heartbeat(self, timestamp: Optional[datetime] = None) -> datetime:
        """Records a periodic heartbeat and confirms healthy operational status."""
        hb_time = timestamp or datetime.now(timezone.utc)
        self.last_heartbeat_at = hb_time
        self.last_active_at = hb_time
        if self.health_status in (AgentHealthStatus.UNRESPONSIVE, AgentHealthStatus.RECOVERING):
            self.health_status = AgentHealthStatus.BUSY if self.current_request_id else AgentHealthStatus.HEALTHY
        return hb_time

    def assign_request(self, request_id: str, version: int = 0) -> None:
        """Binds the agent to exclusive ownership of a specific request version."""
        if not self.is_available:
            raise RuntimeError(
                f"Agent '{self.agent_code}' is currently BUSY on request '{self.current_request_id}'. Cannot assign '{request_id}'."
            )
        self.current_request_id = request_id
        self.assigned_version = version
        self.availability_status = "BUSY"
        self.processing_status = "BUSY"
        self.health_status = AgentHealthStatus.BUSY
        now = datetime.now(timezone.utc)
        self.task_start_time = now
        self.last_active_at = now
        self.last_heartbeat_at = now

    def release_request(self, increment_completed: bool = True) -> None:
        """Releases request ownership, resetting agent back to AVAILABLE and IDLE."""
        if self.task_start_time and increment_completed:
            duration = (datetime.now(timezone.utc) - self.task_start_time).total_seconds() * 1000.0
            self.total_processing_time_ms += duration
        self.task_start_time = None
        self.current_request_id = None
        self.availability_status = "AVAILABLE"
        self.processing_status = "IDLE"
        if not self.is_paused and self.health_status != AgentHealthStatus.FAILED:
            self.health_status = AgentHealthStatus.HEALTHY
        if increment_completed:
            self.completed_work_count += 1
        now = datetime.now(timezone.utc)
        self.last_active_at = now
        self.last_heartbeat_at = now

    def record_failure(self, error_message: str, is_terminal: bool = False) -> None:
        """Records a processing failure, captures sanitized error summary, and updates state."""
        self.failed_work_count += 1
        self.last_error_message = error_message[:500] if error_message else "Unknown execution error"
        self.health_status = AgentHealthStatus.FAILED if is_terminal else AgentHealthStatus.RECOVERING
        self.last_active_at = datetime.now(timezone.utc)

    def recover(self) -> None:
        """Restores a failed or recovering agent back to healthy and available."""
        self.health_status = AgentHealthStatus.HEALTHY
        self.availability_status = "AVAILABLE"
        self.processing_status = "IDLE"
        self.current_request_id = None
        self.task_start_time = None
        self.last_error_message = None
        self.last_heartbeat_at = datetime.now(timezone.utc)

    def step(self) -> None:
        """Default step action for Mesa scheduler cycle. Emits heartbeat."""
        self.send_heartbeat()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes agent operational state for API reporting."""
        return {
            "unique_id": self.unique_id,
            "agent_code": self.agent_code,
            "agent_type": self.agent_type.value if hasattr(self.agent_type, "value") else str(self.agent_type),
            "availability_status": self.availability_status,
            "processing_status": self.processing_status,
            "health_status": self.health_status.value if hasattr(self.health_status, "value") else str(self.health_status),
            "current_request_id": self.current_request_id,
            "assigned_version": self.assigned_version,
            "completed_work_count": self.completed_work_count,
            "failed_work_count": self.failed_work_count,
            "retry_count": self.retry_count,
            "total_processing_time_ms": round(self.total_processing_time_ms, 2),
            "last_error_message": self.last_error_message,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "is_paused": self.is_paused,
            "branch_id": self.branch_id,
        }
