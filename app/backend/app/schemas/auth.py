"""
Pydantic schemas for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Response schema for user information."""
    id: str
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Response schema for authentication operations."""
    success: bool
    user: Optional[UserResponse] = None
    error: Optional[str] = None


class LoginResponse(BaseModel):
    """Response schema for login operation."""
    success: bool
    token: Optional[str] = None
    expires_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    error: Optional[str] = None


class LogoutResponse(BaseModel):
    """Response schema for logout operation."""
    success: bool
    message: str
