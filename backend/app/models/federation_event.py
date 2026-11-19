"""
BankFlow AI - Federation Event Model (Phase 10)
Stores immutable audit records of all cross-branch federation requests,
authorizations, data exchanges, and security rejections across branches.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class FederationEvent(Base):
    """
    FederationEvents table recording every inter-branch information exchange
    for full cross-branch compliance, replay, and security auditing.
    """
    __tablename__ = "federation_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    federation_event_id = Column(String(100), unique=True, index=True, nullable=False)
    source_branch_id = Column(String(50), index=True, nullable=False)
    destination_branch_id = Column(String(50), index=True, nullable=False)
    request_id = Column(String(50), index=True, nullable=True)
    event_type = Column(String(100), index=True, nullable=False)
    requested_scope = Column(String(100), nullable=False)
    authorization_result = Column(String(50), nullable=False, index=True)
    correlation_id = Column(String(100), index=True, nullable=False)
    event_status = Column(String(50), index=True, nullable=False)
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)
    error_message = Column(String(255), nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<FederationEvent(id={self.id}, event_id='{self.federation_event_id}', "
            f"src='{self.source_branch_id}', dest='{self.destination_branch_id}', "
            f"status='{self.event_status}')>"
        )
