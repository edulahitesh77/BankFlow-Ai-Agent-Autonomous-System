"""
BankFlow AI - Processed Message Model
Provides persistent deduplication and idempotency protection for message broker consumers.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class ProcessedMessage(Base):
    """
    ProcessedMessages table tracking unique messages processed by the messaging layer.
    Guarantees that duplicate messages are detected and operations are not repeated.
    """
    __tablename__ = "processed_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(String(100), unique=True, index=True, nullable=False)
    request_id = Column(String(50), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    consumer_name = Column(String(100), nullable=False)
    processing_status = Column(String(50), nullable=False, default="PROCESSED")  # PROCESSED, FAILED, DUPLICATE, DEAD_LETTER
    retry_count = Column(Integer, default=0, nullable=False)
    received_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    payload_snapshot = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<ProcessedMessage(id={self.id}, msg_id='{self.message_id}', status='{self.processing_status}')>"
