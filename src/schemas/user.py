"""
User schema definitions.

This module defines Pydantic models for user-related data validation and serialization.
It includes schemas for user creation, response, and password management.

The schemas implement proper validation rules and type hints for user data.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from src.entity.models import UserRole


class UserBase(BaseModel):
    """
    Base user schema with common fields.

    This schema defines the common fields shared across user-related schemas.
    It includes basic user information and role assignment.

    Attributes:
        username (str): User's username (2-50 characters)
        email (EmailStr): User's email address
        role (UserRole): User's role in the system
    """
    username: str = Field(..., min_length=2, max_length=50, description="Username")
    email: EmailStr
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """
    Schema for user creation.

    This schema extends UserBase and adds password field for user registration.
    It includes validation rules for password strength.

    Attributes:
        password (str): User's password (6-30 characters)
    """
    password: str = Field(..., min_length=6, max_length=30, description="Password")


class UserResponse(UserBase):
    """
    Schema for user response data.

    This schema extends UserBase and adds fields for user identification
    and profile information. It includes configuration for ORM model conversion.

    Attributes:
        id (int): User's unique identifier
        avatar (Optional[str]): URL to user's avatar image
    """
    id: int
    avatar: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResetPasswordResponse(BaseModel):
    """
    Schema for password reset response.

    This schema defines the response message for password reset operations.

    Attributes:
        message (str): Response message
    """
    message: str


class NewPasswordModel(BaseModel):
    """
    Schema for new password submission.

    This schema defines the structure for submitting a new password
    with proper validation rules.

    Attributes:
        new_password (str): New password (6-30 characters)
    """
    new_password: str = Field(
        ..., min_length=6, max_length=30, description="New Password"
    )
