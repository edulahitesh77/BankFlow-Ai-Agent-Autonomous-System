"""
BankFlow AI - Employee Model
Represents internal banking staff profiles linked to an underlying user identity.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Employee(Base):
    """
    Employees table representing bank personnel (branch managers, officers, supervisors).
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    department = Column(String(80), nullable=True)
    designation = Column(String(80), nullable=True)
    branch_id = Column(String(50), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="employee",
    )
    review_records = relationship(
        "ReviewRecord",
        back_populates="employee",
    )
    correction_records = relationship(
        "CorrectionRecord",
        back_populates="employee",
    )

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, code='{self.employee_code}', name='{self.full_name}')>"
