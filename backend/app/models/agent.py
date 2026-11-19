"""
BankFlow AI - Agent Model
Represents multi-agent worker entities in the banking automation system.
Supports multiple REQUEST agent instances and distinct agent roles.
"""

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AgentType(str, enum.Enum):
    """Supported agent types in the BankFlow AI multi-agent architecture."""
    CUSTOMER = "CUSTOMER"
    INTAKE = "INTAKE"
    VERIFICATION = "VERIFICATION"
    REQUEST = "REQUEST"
    SERVICE = "SERVICE"
    SUPERVISOR = "SUPERVISOR"


class AgentHealthStatus(str, enum.Enum):
    """Health and operational states for multi-agent health tracking (Phase 8)."""
    IDLE = "IDLE"
    BUSY = "BUSY"
    HEALTHY = "HEALTHY"
    UNRESPONSIVE = "UNRESPONSIVE"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"


class Agent(Base):
    """
    Agents table recording AI agent instances participating in request workflows.
    Multiple REQUEST agent instances are supported to enable concurrent processing.
    """
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_code = Column(String(50), unique=True, index=True, nullable=False)
    agent_type = Column(
        Enum(AgentType, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    availability_status = Column(
        String(50),
        default="AVAILABLE",
        nullable=False,
    )
    current_request_id = Column(
        Integer,
        ForeignKey(
            "requests.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_agents_current_request_id",
        ),
        nullable=True,
        index=True,
    )
    branch_id = Column(String(50), nullable=True, index=True)
    processing_status = Column(String(50), default="IDLE", nullable=False)
    completed_work_count = Column(Integer, default=0, nullable=False)
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    # Phase 8: Health monitoring, heartbeats, and failure tracking
    health_status = Column(
        String(50),
        default="HEALTHY",
        nullable=False,
        index=True,
    )
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    failed_work_count = Column(Integer, default=0, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    total_processing_time_ms = Column(Float, default=0.0, nullable=False)
    last_error_message = Column(Text, nullable=True)
    is_paused = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    assigned_requests = relationship(
        "Request",
        foreign_keys="Request.assigned_agent_id",
        back_populates="assigned_agent",
    )
    current_request = relationship(
        "Request",
        foreign_keys=[current_request_id],
        post_update=True,
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, code='{self.agent_code}', type='{self.agent_type}')>"
