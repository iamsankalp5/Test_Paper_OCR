"""
User data models.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles."""
    TEACHER = "teacher"
    STUDENT = "student"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    full_name: str
    role: UserRole
    institution: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator('password')
    def validate_password(cls, v):
        """Validate password requirements."""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long (max 72 bytes for bcrypt)')
        return v


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response model (no password)."""
    user_id: str
    created_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """User model stored in database."""
    user_id: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    email: str
    role: UserRole