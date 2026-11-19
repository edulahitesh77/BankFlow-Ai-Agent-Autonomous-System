"""
BankFlow AI - Customer Model
Represents customer banking profiles linked to an underlying user identity.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Customer(Base):
    """
    Customers table representing bank account holders.
    Contains synthetic customer identifiers and profile information.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    customer_code = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    phone = Column(String(30), nullable=True)
    email = Column(String(120), nullable=False)
    branch_id = Column(String(50), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="customer",
    )
    accounts = relationship(
        "Account",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    requests = relationship(
        "Request",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    notifications = relationship(
        "Notification",
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="desc(Notification.created_at)",
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, code='{self.customer_code}', name='{self.full_name}')>"
