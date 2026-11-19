"""
BankFlow AI - Request Model
Core orchestration table tracking customer banking service requests across AI agents.
"""

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ServiceType(str, enum.Enum):
    """Supported banking service categories."""
    CHEQUE_BOOK = "CHEQUE_BOOK"
    DEBIT_CARD_REPLACEMENT = "DEBIT_CARD_REPLACEMENT"
    ADDRESS_UPDATE = "ADDRESS_UPDATE"
    ACCOUNT_APPLICATION = "ACCOUNT_APPLICATION"


class RequestStatus(str, enum.Enum):
    """Lifecycle statuses for multi-agent service request processing."""
    NEW = "NEW"
    CLASSIFIED = "CLASSIFIED"
    QUEUED = "QUEUED"
    VERIFIED = "VERIFIED"
    IN_SERVICE = "IN_SERVICE"
    COMPLETED = "COMPLETED"
    NEEDS_CORRECTION = "NEEDS_CORRECTION"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECTED_INPUT = "REJECTED_INPUT"
    FAILED = "FAILED"


class Request(Base):
    """
    Requests table tracking automated and supervised banking service workflows.
    """
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    service_type = Column(
        Enum(ServiceType, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    request_status = Column(
        Enum(RequestStatus, native_enum=False, length=50),
        nullable=False,
        default=RequestStatus.NEW,
        index=True,
    )
    priority = Column(String(20), nullable=False, default="MEDIUM")
    assigned_agent_id = Column(
        Integer,
        ForeignKey("agents.id", ondelete="SET NULL", name="fk_requests_assigned_agent_id"),
        nullable=True,
        index=True,
    )
    assignment_version = Column(Integer, default=0, nullable=False)
    # Phase 8: Recovery tracking, retry counting, and fault tolerance
    retry_count = Column(Integer, default=0, nullable=False)
    last_recovery_at = Column(DateTime(timezone=True), nullable=True)
    recovery_reason = Column(String(255), nullable=True)

    # Phase 10: Multi-Branch Federation
    branch_id = Column(String(50), default="BLR001", nullable=False, index=True)
    origin_branch_id = Column(String(50), nullable=True)
    requires_federation = Column(Boolean, default=False, nullable=False)
    federation_status = Column(String(50), nullable=True)

    required_skill = Column(String(100), nullable=True)
    completeness_status = Column(String(50), nullable=True, default="PENDING")
    review_required = Column(Boolean, default=False, nullable=False)
    reason_code = Column(String(100), nullable=True)
    payload = Column(JSON, nullable=True)

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
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship(
        "Customer",
        back_populates="requests",
    )
    account = relationship(
        "Account",
        backref="requests",
    )
    assigned_agent = relationship(
        "Agent",
        foreign_keys=[assigned_agent_id],
        back_populates="assigned_requests",
    )
    review_records = relationship(
        "ReviewRecord",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="desc(ReviewRecord.created_at)",
    )
    correction_records = relationship(
        "CorrectionRecord",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="desc(CorrectionRecord.created_at)",
    )
    notifications = relationship(
        "Notification",
        back_populates="request",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Request(id={self.id}, request_id='{self.request_id}', status='{self.request_status}')>"
