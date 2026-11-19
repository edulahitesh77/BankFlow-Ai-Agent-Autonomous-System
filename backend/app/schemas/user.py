"""
BankFlow AI - User and Profile Schemas
Defines serialization models for User, Customer, and Employee profile details.
Never exposes password hashes or secret tokens.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Safe user identity representation without credentials."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountSummary(BaseModel):
    """Synthetic account overview for customer profile view."""
    id: int
    synthetic_account_number: str
    account_type: str
    account_status: str
    branch_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerProfileResponse(BaseModel):
    """Customer profile schema."""
    id: int
    user_id: int
    customer_code: str
    full_name: str
    phone: Optional[str] = None
    email: str
    branch_id: Optional[str] = None
    created_at: datetime
    role: str = "CUSTOMER"
    accounts: List[AccountSummary] = []

    model_config = ConfigDict(from_attributes=True)


class EmployeeProfileResponse(BaseModel):
    """Bank employee profile schema."""
    id: int
    user_id: int
    employee_code: str
    full_name: str
    department: Optional[str] = None
    designation: Optional[str] = None
    branch_id: Optional[str] = None
    created_at: datetime
    role: str = "BANK_EMPLOYEE"

    model_config = ConfigDict(from_attributes=True)
