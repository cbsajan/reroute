"""
User Pydantic Models

Demonstrates REROUTE model usage with parameter injection
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """
    Base User schema with common fields.
    """
    name: str = Field(..., description="User full name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="User description or bio")
    is_active: bool = Field(True, description="Whether the user account is active")


class UserCreate(UserBase):
    """
    Schema for creating a new User.
    Used in POST requests.
    """
    pass


class UserUpdate(BaseModel):
    """
    Schema for updating an existing User.
    Used in PUT/PATCH requests. All fields are optional.
    """
    name: Optional[str] = Field(None, description="User full name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="User description or bio")
    is_active: Optional[bool] = Field(None, description="Whether the user account is active")


class UserInDB(UserBase):
    """
    Schema for User as stored in database.
    Includes additional fields like id, created_at, updated_at.
    """
    id: int = Field(..., description="Unique user identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """
    Schema for User in API responses.
    Used in GET requests.
    """
    pass
