"""Authentication models for the MCP service."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """User model with basic attributes."""
    
    username: str
    email: Optional[str] = None  # Changed from EmailStr to str to avoid email-validator dependency
    full_name: Optional[str] = None
    disabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    roles: List[str] = Field(default_factory=list)


class UserInDB(User):
    """User model with password hash for storage."""
    
    hashed_password: str


class Token(BaseModel):
    """Token response model."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    
    username: str
    roles: List[str] = Field(default_factory=list)
    exp: Optional[int] = None


class UserCreate(BaseModel):
    """Model for user creation requests."""
    
    username: str
    email: str  # Changed from EmailStr to str to avoid email-validator dependency
    full_name: Optional[str] = None
    password: str
    roles: List[str] = Field(default_factory=lambda: ["user"])
