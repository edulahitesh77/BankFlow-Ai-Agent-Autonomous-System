"""
BankFlow AI - Notification Model
Captures in-app notifications generated for customers during banking workflows.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Notification(Base):
    """
    Notifications table storing alerts for customers regarding their requests.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    request_id = Column(
        Integer,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    notification_title = Column(String(150), nullable=False)
    notification_message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    customer = relationship("Customer", back_populates="notifications")
    request = relationship("Request", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, customer_id={self.customer_id}, title='{self.notification_title}')>"
