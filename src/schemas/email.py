"""
Email schema definitions.

This module defines Pydantic models for email-related data validation.
It includes schemas for email requests and validation.

The schemas implement proper email validation using Pydantic's EmailStr type.
"""

from pydantic import BaseModel, EmailStr


class RequestEmail(BaseModel):
    """
    Schema for email request data.

    This schema defines the structure for submitting an email address
    with proper validation.

    Attributes:
        email (EmailStr): Valid email address
    """
    email: EmailStr