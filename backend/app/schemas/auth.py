"""
BankFlow AI - Authentication Schemas
Defines request and response validation models for customer registration and both logins.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class CustomerRegisterRequest(BaseModel):
    """Schema for customer self-service registration."""
    full_name: str = Field(..., min_length=2, max_length=100, description="Customer's legal full name")
    email: EmailStr = Field(..., description="Customer's unique email address")
    phone: Optional[str] = Field(None, max_length=30, description="Customer's contact phone number")
    username: str = Field(..., min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$", description="Unique username")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Must match password")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Confirm password does not match the chosen password.")
        return v


class CustomerLoginRequest(BaseModel):
    """Schema for customer authentication."""
    username_or_email: str = Field(..., min_length=1, max_length=120, description="Customer username or registered email")
    password: str = Field(..., min_length=1, description="Password")
    remember_me: Optional[bool] = Field(False, description="Extend token expiration duration")


class BankLoginRequest(BaseModel):
    """Schema for bank employee authentication."""
    employee_id_or_username: str = Field(..., min_length=1, max_length=100, description="Employee Code or registered username")
    password: str = Field(..., min_length=1, description="Password")


class TokenResponse(BaseModel):
    """Schema for successful authentication response with JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    user_id: int
    username: str
    redirect_url: str


class AuthMessageResponse(BaseModel):
    """Generic message response schema for authentication events."""
    status: str
    message: str
