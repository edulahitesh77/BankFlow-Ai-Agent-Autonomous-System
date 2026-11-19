"""
BankFlow AI - Audit Log Model
Records operational actions, state transitions, and audit events across the system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    """
    Audit logs table providing an immutable trail of actions, agent operations,
    and user interactions for compliance and observability.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(50), unique=True, index=True, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_id = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    outcome = Column(String(50), nullable=True, default="SUCCESS", index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    source_ip = Column(String(50), nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="audit_logs",
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', entity='{self.entity_type}:{self.entity_id}')>"
