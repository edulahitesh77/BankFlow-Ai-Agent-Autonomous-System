"""
BankFlow AI - Correction Record Model
Stores employee instructions and reasons for requests requiring customer corrections.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CorrectionRecord(Base):
    """
    Correction records table capturing missing or invalid fields and employee instructions.
    """
    __tablename__ = "correction_records"

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
    correction_reason = Column(String(200), nullable=False)
    customer_instruction = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    request = relationship("Request", back_populates="correction_records")
    employee = relationship("Employee", back_populates="correction_records")

    def __repr__(self) -> str:
        return f"<CorrectionRecord(id={self.id}, request_id={self.request_id}, reason='{self.correction_reason}')>"
