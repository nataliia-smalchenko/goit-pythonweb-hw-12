from datetime import datetime, date
from typing import Optional
import re

from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict

# Регулярний вираз для валідації номера телефону:
# Допускається необовʼязковий знак "+" на початку та від 10 до 15 цифр.
PHONE_REGEX = re.compile(r"^\+?\d{10,15}$")


class ContactCreateSchema(BaseModel):
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
        if value is None:
            return value
        if not PHONE_REGEX.match(value):
            raise ValueError(
                "Невірний формат номеру телефону. Очікується формат: +1234567890 (10-15 цифр)"
            )
        return value


class ContactUpdateSchema(BaseModel):
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
        if value is None:
            return value
        if not PHONE_REGEX.match(value):
            raise ValueError(
                "Невірний формат номеру телефону. Очікується формат: +1234567890 (10-15 цифр)"
            )
        return value


class ContactResponseSchema(BaseModel):
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
