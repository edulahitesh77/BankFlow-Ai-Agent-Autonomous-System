"""
BankFlow AI - Message Delivery Attempt Model
Tracks delivery attempts, retries, and dead-letter assignments for broker messages.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class MessageDeliveryAttempt(Base):
    """
    MessageDeliveryAttempts table recording each individual delivery attempt for a message.
    Preserves error logs and retry metrics for observability and supervisory inspection.
    """
    __tablename__ = "message_delivery_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(String(100), nullable=False, index=True)
    consumer_name = Column(String(100), nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    delivery_status = Column(String(50), nullable=False)  # SUCCESS, RETRY, DEAD_LETTER, DUPLICATE_IGNORED
    error_message = Column(Text, nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<MessageDeliveryAttempt(id={self.id}, msg_id='{self.message_id}', attempt={self.attempt_number}, status='{self.delivery_status}')>"
