"""
BankFlow AI - Review Record Model
Records bank employee review decisions, notes, and escalations on customer service requests.
"""

import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ReviewDecision(str, enum.Enum):
    """Possible outcomes of an internal bank employee review."""
    REVIEW_COMPLETED = "REVIEW_COMPLETED"
    ADDITIONAL_INFORMATION_REQUIRED = "ADDITIONAL_INFORMATION_REQUIRED"
    REVIEW_REJECTED = "REVIEW_REJECTED"
    ESCALATED = "ESCALATED"


class ReviewRecord(Base):
    """
    Review records table storing human supervisor/employee decisions and notes.
    """
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(
        Integer,
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    review_decision = Column(
        Enum(ReviewDecision, native_enum=False, length=50),
        nullable=False,
    )
    internal_note = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    request = relationship("Request", back_populates="review_records")
    employee = relationship("Employee", back_populates="review_records")

    def __repr__(self) -> str:
        return f"<ReviewRecord(id={self.id}, request_id={self.request_id}, decision='{self.review_decision}')>"
