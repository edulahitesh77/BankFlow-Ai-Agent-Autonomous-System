"""
BankFlow AI - Agent Event Model
Stores the complete, immutable communication and state transition history across agents.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class AgentEvent(Base):
    """
    AgentEvents table recording all published agent events and state transitions.
    Enables request communication inspection and workflow telemetry.
    """
    __tablename__ = "agent_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    request_id = Column(String(50), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    previous_state = Column(String(50), nullable=True)
    new_state = Column(String(50), nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    reason_code = Column(String(100), nullable=True)
    payload = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentEvent(id={self.id}, request_id='{self.request_id}', type='{self.event_type}', agent='{self.agent_id}')>"
