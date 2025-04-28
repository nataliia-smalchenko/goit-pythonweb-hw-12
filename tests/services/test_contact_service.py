import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from pydantic import ValidationError

from sqlalchemy.ext.asyncio import AsyncSession
from src.services.contacts import ContactService
from src.schemas.contact import ContactCreateSchema, ContactUpdateSchema
from src.entity.models import Contact, User


@pytest_asyncio.fixture
async def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest_asyncio.fixture
async def contact_service(mock_db):
    service = ContactService(mock_db)
    service.contact_repository = AsyncMock()
    return service


@pytest_asyncio.fixture
async def test_contact():
    return Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="+1234567890",
        birthday=datetime.now().date(),
        user_id=1
    )


@pytest_asyncio.fixture
async def test_contact_data():
    return ContactCreateSchema(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone_number="+1234567890",
        birthday=datetime.now().date()
    )


@pytest_asyncio.fixture
async def test_contact_update_data():
    return ContactUpdateSchema(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        phone_number="+0987654321",
        birthday=datetime.now().date() + timedelta(days=1)
    )


@pytest.mark.asyncio
async def test_create_contact(contact_service, test_contact, test_contact_data):
    # Arrange
    user_id = 1
    contact_service.contact_repository.create_contact.return_value = test_contact

    # Act
    result = await contact_service.create_contact(test_contact_data, user_id)

    # Assert
    assert result == test_contact
    contact_service.contact_repository.create_contact.assert_called_once_with(test_contact_data, user_id)


@pytest.mark.asyncio
async def test_create_contact_invalid_phone():
    # Arrange
    with pytest.raises(ValidationError) as exc_info:
        ContactCreateSchema(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone_number="123",  # Invalid phone number
            birthday=datetime.now().date()
        )
    
    # Assert
    assert "Невірний формат номеру телефону" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_contacts(contact_service, test_contact):
    # Arrange
    limit = 10
    offset = 0
    user_id = 1
    contact_service.contact_repository.get_contacts.return_value = [test_contact]

    # Act
    result = await contact_service.get_contacts(limit, offset, user_id)

    # Assert
    assert result == [test_contact]
    contact_service.contact_repository.get_contacts.assert_called_once_with(user_id, limit, offset)


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_service, test_contact):
    # Arrange
    contact_id = 1
    user_id = 1
    contact_service.contact_repository.get_contact_by_id.return_value = test_contact

    # Act
    result = await contact_service.get_contact_by_id(contact_id, user_id)

    # Assert
    assert result == test_contact
    contact_service.contact_repository.get_contact_by_id.assert_called_once_with(contact_id, user_id)


@pytest.mark.asyncio
async def test_update_contact(contact_service, test_contact, test_contact_update_data):
    # Arrange
    contact_id = 1
    user_id = 1
    contact_service.contact_repository.update_contact.return_value = test_contact

    # Act
    result = await contact_service.update_contact(contact_id, test_contact_update_data, user_id)

    # Assert
    assert result == test_contact
    contact_service.contact_repository.update_contact.assert_called_once_with(
        contact_id, test_contact_update_data, user_id
    )


@pytest.mark.asyncio
async def test_update_contact_invalid_phone():
    # Arrange
    with pytest.raises(ValidationError) as exc_info:
        ContactUpdateSchema(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone_number="123",  # Invalid phone number
            birthday=datetime.now().date() + timedelta(days=1)
        )
    
    # Assert
    assert "Невірний формат номеру телефону" in str(exc_info.value)


@pytest.mark.asyncio
async def test_remove_contact(contact_service, test_contact):
    # Arrange
    contact_id = 1
    user_id = 1
    contact_service.contact_repository.remove_contact.return_value = test_contact

    # Act
    result = await contact_service.remove_contact(contact_id, user_id)

    # Assert
    assert result == test_contact
    contact_service.contact_repository.remove_contact.assert_called_once_with(contact_id, user_id)


@pytest.mark.asyncio
async def test_search_contacts(contact_service, test_contact):
    # Arrange
    user_id = 1
    first_name = "John"
    last_name = "Doe"
    email = "john.doe@example.com"
    limit = 10
    offset = 0
    contact_service.contact_repository.search_contacts.return_value = [test_contact]

    # Act
    result = await contact_service.search_contacts(
        user_id, first_name, last_name, email, limit, offset
    )

    # Assert
    assert result == [test_contact]
    contact_service.contact_repository.search_contacts.assert_called_once_with(
        user_id, first_name, last_name, email, limit, offset
    )


@pytest.mark.asyncio
async def test_get_contacts_with_upcoming_birthdays(contact_service, test_contact):
    # Arrange
    user_id = 1
    contact_service.contact_repository.get_contacts_with_upcoming_birthdays.return_value = [test_contact]

    # Act
    result = await contact_service.get_contacts_with_upcoming_birthdays(user_id)

    # Assert
    assert result == [test_contact]
    contact_service.contact_repository.get_contacts_with_upcoming_birthdays.assert_called_once_with(user_id) 