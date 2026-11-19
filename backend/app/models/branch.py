"""
BankFlow AI - Branch Model (Phase 10)
Represents independent bank branches participating in the simulated banking federation.
Supports Bengaluru (BLR001), Chennai (CHE001), and Hyderabad (HYD001).
"""

import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class BranchStatus(str, enum.Enum):
    """Operational status of a bank branch."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class Branch(Base):
    """
    Branches table maintaining registration, connection endpoints,
    and service credentials for the multi-branch federation.
    """
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    branch_id = Column(String(50), unique=True, index=True, nullable=False)
    branch_name = Column(String(100), nullable=False)
    location = Column(String(150), nullable=False)
    branch_status = Column(String(20), default=BranchStatus.ACTIVE.value, nullable=False, index=True)
    api_endpoint = Column(String(255), nullable=True)
    database_name = Column(String(100), nullable=True)
    api_key_hash = Column(String(255), nullable=False)
    is_gateway_enabled = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Branch(id={self.id}, branch_id='{self.branch_id}', name='{self.branch_name}', status='{self.branch_status}')>"
