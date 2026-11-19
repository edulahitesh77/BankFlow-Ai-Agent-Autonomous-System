"""
BankFlow AI - Agent Failure and Recovery Model
Tracks agent failure events, timeouts, duplicate attempts, crashes, and recovery states.
"""

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class FailureType(str, enum.Enum):
    """Categories of agent and workflow failures (Phase 8)."""
    UNRESPONSIVE_HEARTBEAT = "UNRESPONSIVE_HEARTBEAT"
    CRASH_DURING_EXECUTION = "CRASH_DURING_EXECUTION"
    PROCESSING_TIMEOUT = "PROCESSING_TIMEOUT"
    RABBITMQ_UNAVAILABLE = "RABBITMQ_UNAVAILABLE"
    DUPLICATE_DELIVERY = "DUPLICATE_DELIVERY"
    REPEATED_PROCESSING_FAILURE = "REPEATED_PROCESSING_FAILURE"
    INVALID_RESULT_PAYLOAD = "INVALID_RESULT_PAYLOAD"
    DEPENDENCY_CIRCUIT_OPEN = "DEPENDENCY_CIRCUIT_OPEN"
    MANUAL_INTERVENTION_REQUIRED = "MANUAL_INTERVENTION_REQUIRED"


class RecoveryStatus(str, enum.Enum):
    """Progression states of task failure recovery (Phase 8)."""
    DETECTED = "DETECTED"
    RECOVERING = "RECOVERING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    ESCALATED_TO_HUMAN = "ESCALATED_TO_HUMAN"


class AgentFailure(Base):
    """
    Records agent failures, crashes, message anomalies, and recovery outcomes.
    Maintains complete operational traceability for supervisors and audits.
    """
    __tablename__ = "agent_failures"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    failure_id = Column(String(50), unique=True, index=True, nullable=False)
    agent_id = Column(
        Integer,
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_code = Column(String(50), nullable=True, index=True)
    request_id = Column(
        Integer,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_code = Column(String(50), nullable=True, index=True)
    failure_type = Column(String(100), nullable=False, index=True)
    error_details = Column(Text, nullable=True)
    recovery_status = Column(
        String(50),
        default="DETECTED",
        nullable=False,
        index=True,
    )
    retry_count = Column(Integer, default=0, nullable=False)
    recovered_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    agent = relationship("Agent", foreign_keys=[agent_id])
    request = relationship("Request", foreign_keys=[request_id])

    def __repr__(self) -> str:
        return f"<AgentFailure(id={self.id}, failure_id='{self.failure_id}', type='{self.failure_type}', status='{self.recovery_status}')>"
