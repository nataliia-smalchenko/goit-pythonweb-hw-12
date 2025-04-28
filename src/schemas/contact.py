"""
Contact schema definitions.

This module defines Pydantic models for contact-related data validation and serialization.
It includes schemas for contact creation, updates, and responses, with proper
validation rules for phone numbers and email addresses.

The schemas implement comprehensive validation for contact information
and proper type conversion for database operations.
"""

from datetime import datetime, date
from typing import Optional
import re

from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict

# Регулярний вираз для валідації номера телефону:
# Допускається необовʼязковий знак "+" на початку та від 10 до 15 цифр.
PHONE_REGEX = re.compile(r"^\+?\d{10,15}$")


class ContactCreateSchema(BaseModel):
    """
    Schema for contact creation.

    This schema defines the structure and validation rules for creating a new contact.
    It includes fields for personal information with proper validation.

    Attributes:
        first_name (str): Contact's first name (1-50 characters)
        last_name (str): Contact's last name (1-50 characters)
        email (Optional[EmailStr]): Contact's email address
        phone_number (Optional[str]): Contact's phone number
        birthday (Optional[date]): Contact's birthday
        additional_data (Optional[str]): Additional contact information
    """

    first_name: str = Field(
        ..., min_length=1, max_length=50, description="Ім'я контакту"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=50, description="Прізвище контакту"
    )
    email: Optional[EmailStr] = Field(
        default=None, max_length=100, description="Електронна адреса контакту"
    )
    phone_number: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Номер телефону контакту. Формат: +1234567890 (10-15 цифр)",
    )
    birthday: Optional[date] = Field(
        default=None, description="Дата народження контакту"
    )
    additional_data: Optional[str] = Field(
        default=None, max_length=255, description="Додаткова інформація про контакт"
    )

    @validator("phone_number")
    def validate_phone(cls, value):
        """
        Validate phone number format.

        Args:
            value (str): Phone number to validate

        Returns:
            str: Validated phone number

        Raises:
            ValueError: If phone number format is invalid
        """
        if value is None:
            return value
        if not PHONE_REGEX.match(value):
            raise ValueError(
                "Невірний формат номеру телефону. Очікується формат: +1234567890 (10-15 цифр)"
            )
        return value


class ContactUpdateSchema(BaseModel):
    """
    Schema for contact updates.

    This schema defines the structure and validation rules for updating an existing contact.
    All fields are optional to allow partial updates.

    Attributes:
        first_name (Optional[str]): Contact's first name (1-50 characters)
        last_name (Optional[str]): Contact's last name (1-50 characters)
        email (Optional[EmailStr]): Contact's email address
        phone_number (Optional[str]): Contact's phone number
        birthday (Optional[date]): Contact's birthday
        additional_data (Optional[str]): Additional contact information
    """

    first_name: Optional[str] = Field(
        default=None, min_length=1, max_length=50, description="Ім'я контакту"
    )
    last_name: Optional[str] = Field(
        default=None, min_length=1, max_length=50, description="Прізвище контакту"
    )
    email: Optional[EmailStr] = Field(
        default=None, max_length=100, description="Електронна адреса контакту"
    )
    phone_number: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Номер телефону контакту. Формат: +1234567890 (10-15 цифр)",
    )
    birthday: Optional[date] = Field(
        default=None, description="Дата народження контакту"
    )
    additional_data: Optional[str] = Field(
        default=None, max_length=255, description="Додаткова інформація про контакт"
    )

    @validator("phone_number")
    def validate_phone(cls, value):
        """
        Validate phone number format.

        Args:
            value (str): Phone number to validate

        Returns:
            str: Validated phone number

        Raises:
            ValueError: If phone number format is invalid
        """
        if value is None:
            return value
        if not PHONE_REGEX.match(value):
            raise ValueError(
                "Невірний формат номеру телефону. Очікується формат: +1234567890 (10-15 цифр)"
            )
        return value


class ContactResponseSchema(BaseModel):
    """
    Schema for contact response data.

    This schema defines the structure for contact data responses.
    It includes all contact information and timestamps.

    Attributes:
        id (int): Contact's unique identifier
        first_name (str): Contact's first name
        last_name (str): Contact's last name
        full_name (str): Contact's full name
        email (Optional[EmailStr]): Contact's email address
        phone_number (Optional[str]): Contact's phone number
        birthday (Optional[date]): Contact's birthday
        additional_data (Optional[str]): Additional contact information
        created_at (Optional[datetime]): Record creation timestamp
        updated_at (Optional[datetime]): Record last update timestamp
    """

    id: int
    first_name: str
    last_name: str
    full_name: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_data: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
