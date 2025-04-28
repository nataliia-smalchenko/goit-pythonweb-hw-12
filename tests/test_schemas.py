from datetime import datetime, date
import pytest
from pydantic import ValidationError

from src.entity.models import UserRole
from src.schemas.user import UserBase, UserCreate, UserResponse, NewPasswordModel
from src.schemas.token import TokenResponse, RefreshTokenRequest
from src.schemas.contact import ContactCreateSchema, ContactUpdateSchema, ContactResponseSchema
from src.schemas.email import RequestEmail


def test_user_base_schema():
    # Test valid data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "role": UserRole.USER
    }
    user = UserBase(**user_data)
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.role == UserRole.USER

    # Test invalid username (too short)
    with pytest.raises(ValidationError):
        UserBase(username="a", email="test@example.com", role=UserRole.USER)

    # Test invalid email
    with pytest.raises(ValidationError):
        UserBase(username="testuser", email="invalid_email", role=UserRole.USER)


def test_user_create_schema():
    # Test valid data
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "role": UserRole.USER
    }
    user = UserCreate(**user_data)
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.password == "password123"
    assert user.role == UserRole.USER

    # Test invalid password (too short)
    with pytest.raises(ValidationError):
        UserCreate(
            username="testuser",
            email="test@example.com",
            password="12345",
            role=UserRole.USER
        )


def test_user_response_schema():
    # Test valid data
    user_data = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": UserRole.USER,
        "avatar": "http://example.com/avatar.jpg"
    }
    user = UserResponse(**user_data)
    assert user.id == 1
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.role == UserRole.USER
    assert user.avatar == "http://example.com/avatar.jpg"

    # Test without optional avatar
    user_data.pop("avatar")
    user = UserResponse(**user_data)
    assert user.avatar is None


def test_new_password_model():
    # Test valid data
    password_data = {
        "new_password": "newpassword123"
    }
    password = NewPasswordModel(**password_data)
    assert password.new_password == "newpassword123"

    # Test invalid password (too short)
    with pytest.raises(ValidationError):
        NewPasswordModel(new_password="12345")


def test_token_response_schema():
    # Test valid data
    token_data = {
        "access_token": "access_token_value",
        "refresh_token": "refresh_token_value"
    }
    token = TokenResponse(**token_data)
    assert token.access_token == "access_token_value"
    assert token.refresh_token == "refresh_token_value"
    assert token.token_type == "bearer"  # default value


def test_refresh_token_request_schema():
    # Test valid data
    token_data = {
        "refresh_token": "refresh_token_value"
    }
    token = RefreshTokenRequest(**token_data)
    assert token.refresh_token == "refresh_token_value"


def test_contact_create_schema():
    # Test valid data
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone_number": "+1234567890",
        "birthday": date(1990, 1, 1),
        "additional_data": "Some notes"
    }
    contact = ContactCreateSchema(**contact_data)
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.email == "john@example.com"
    assert contact.phone_number == "+1234567890"
    assert contact.birthday == date(1990, 1, 1)
    assert contact.additional_data == "Some notes"

    # Test minimal valid data
    minimal_data = {
        "first_name": "John",
        "last_name": "Doe"
    }
    contact = ContactCreateSchema(**minimal_data)
    assert contact.email is None
    assert contact.phone_number is None
    assert contact.birthday is None
    assert contact.additional_data is None

    # Test invalid phone number
    with pytest.raises(ValidationError):
        ContactCreateSchema(
            first_name="John",
            last_name="Doe",
            phone_number="invalid"
        )

    # Test invalid email
    with pytest.raises(ValidationError):
        ContactCreateSchema(
            first_name="John",
            last_name="Doe",
            email="invalid_email"
        )


def test_contact_update_schema():
    # Test full update
    update_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone_number": "+1234567890",
        "birthday": date(1990, 1, 1),
        "additional_data": "Some notes"
    }
    contact = ContactUpdateSchema(**update_data)
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.email == "john@example.com"
    assert contact.phone_number == "+1234567890"
    assert contact.birthday == date(1990, 1, 1)
    assert contact.additional_data == "Some notes"

    # Test partial update
    partial_data = {
        "first_name": "John"
    }
    contact = ContactUpdateSchema(**partial_data)
    assert contact.first_name == "John"
    assert contact.last_name is None
    assert contact.email is None
    assert contact.phone_number is None
    assert contact.birthday is None
    assert contact.additional_data is None

    # Test invalid phone number
    with pytest.raises(ValidationError):
        ContactUpdateSchema(phone_number="invalid")

    # Test invalid email
    with pytest.raises(ValidationError):
        ContactUpdateSchema(email="invalid_email")


def test_contact_response_schema():
    # Test full response
    response_data = {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone_number": "+1234567890",
        "birthday": date(1990, 1, 1),
        "additional_data": "Some notes",
        "created_at": datetime(2024, 1, 1, 12, 0),
        "updated_at": datetime(2024, 1, 1, 12, 0)
    }
    contact = ContactResponseSchema(**response_data)
    assert contact.id == 1
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.full_name == "John Doe"
    assert contact.email == "john@example.com"
    assert contact.phone_number == "+1234567890"
    assert contact.birthday == date(1990, 1, 1)
    assert contact.additional_data == "Some notes"
    assert isinstance(contact.created_at, datetime)
    assert isinstance(contact.updated_at, datetime)

    # Test minimal response
    minimal_data = {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "full_name": "John Doe"
    }
    contact = ContactResponseSchema(**minimal_data)
    assert contact.email is None
    assert contact.phone_number is None
    assert contact.birthday is None
    assert contact.additional_data is None
    assert contact.created_at is None
    assert contact.updated_at is None


def test_request_email_schema():
    # Test valid email
    email_data = {
        "email": "test@example.com"
    }
    email_request = RequestEmail(**email_data)
    assert email_request.email == "test@example.com"

    # Test invalid email
    with pytest.raises(ValidationError):
        RequestEmail(email="invalid_email") 