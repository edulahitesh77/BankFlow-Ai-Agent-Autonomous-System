"""
BankFlow AI - Account Model
Represents synthetic customer bank accounts.
All accounts and numbers are entirely synthetic simulations for educational purposes.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Account(Base):
    """
    Accounts table storing synthetic banking accounts.
    Financial transactions and real-world banking account data are not supported.
    """
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    synthetic_account_number = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    account_type = Column(String(50), nullable=False)  # SAVINGS, CHECKING, CURRENT, etc.
    account_status = Column(String(30), nullable=False, default="ACTIVE")  # ACTIVE, INACTIVE, DORMANT, CLOSED
    branch_id = Column(String(50), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    customer = relationship(
        "Customer",
        back_populates="accounts",
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, synthetic_num='{self.synthetic_account_number}', type='{self.account_type}')>"
