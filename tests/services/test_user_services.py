import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import jwt

from src.services.user import UserService
from src.entity.models import User, UserRole
from src.schemas.user import UserCreate
from src.schemas.email import RequestEmail
from src.conf.config import config


@pytest_asyncio.fixture
async def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest_asyncio.fixture
async def mock_user_repository():
    return AsyncMock()


@pytest_asyncio.fixture
async def mock_auth_service():
    mock = AsyncMock()
    mock._hash_password = MagicMock()  # Використовуємо MagicMock для синхронного методу
    return mock


@pytest_asyncio.fixture
async def mock_email_service():
    mock = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def user_service(mock_db, mock_user_repository, mock_auth_service, mock_email_service):
    service = UserService(mock_db)
    service.user_repository = mock_user_repository
    service.auth_service = mock_auth_service
    service.email_service = mock_email_service
    return service


@pytest_asyncio.fixture
async def test_user_data():
    return UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpass123"
    )


@pytest_asyncio.fixture
async def test_user():
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_verified=False,
        role=UserRole.USER,
        avatar_url="http://example.com/avatar.jpg"
    )


@pytest.mark.asyncio
async def test_create_user(user_service, test_user_data, test_user):
    # Arrange
    user_service.auth_service.register_user.return_value = test_user

    # Act
    result = await user_service.create_user(test_user_data)

    # Assert
    assert result == test_user
    user_service.auth_service.register_user.assert_called_once_with(test_user_data)


@pytest.mark.asyncio
async def test_get_user_by_username(user_service, test_user):
    # Arrange
    user_service.user_repository.get_by_username.return_value = test_user

    # Act
    result = await user_service.get_user_by_username(test_user.username)

    # Assert
    assert result == test_user
    user_service.user_repository.get_by_username.assert_called_once_with(test_user.username)


@pytest.mark.asyncio
async def test_get_user_by_email(user_service, test_user):
    # Arrange
    user_service.user_repository.get_by_email.return_value = test_user

    # Act
    result = await user_service.get_user_by_email(test_user.email)

    # Assert
    assert result == test_user
    user_service.user_repository.get_by_email.assert_called_once_with(test_user.email)


@pytest.mark.asyncio
async def test_confirmed_email(user_service, test_user):
    # Arrange
    user_service.user_repository.confirmed_email.return_value = None

    # Act
    await user_service.confirmed_email(test_user.email)

    # Assert
    user_service.user_repository.confirmed_email.assert_called_once_with(test_user.email)


@pytest.mark.asyncio
async def test_update_avatar_url(user_service, test_user):
    # Arrange
    new_avatar_url = "http://example.com/new_avatar.jpg"
    user_service.user_repository.update_avatar_url.return_value = test_user

    # Act
    result = await user_service.update_avatar_url(test_user.email, new_avatar_url)

    # Assert
    assert result == test_user
    user_service.user_repository.update_avatar_url.assert_called_once_with(test_user.email, new_avatar_url)


@pytest.mark.asyncio
async def test_update_password(user_service, test_user):
    # Arrange
    new_password = "newpass123"
    hashed_password = "hashed_new_password"
    user_service.auth_service._hash_password.return_value = hashed_password
    user_service.user_repository.update_password.return_value = test_user

    # Act
    result = await user_service.update_password(test_user.email, new_password)

    # Assert
    assert result == test_user
    user_service.auth_service._hash_password.assert_called_once_with(new_password)
    user_service.user_repository.update_password.assert_awaited_once_with(test_user.email, hashed_password)


@pytest.mark.asyncio
async def test_confirmed_email_endpoint(user_service, test_user):
    """Test email confirmation with a valid token."""
    test_email = test_user.email
    
    # Mock user repository to return an unconfirmed user first
    unconfirmed_user = User(
        id=test_user.id,
        email=test_user.email,
        username=test_user.username,
        hashed_password=test_user.hashed_password,
        is_verified=False,
        role=test_user.role,
        avatar_url=test_user.avatar_url
    )
    user_service.user_repository.get_by_email.return_value = unconfirmed_user
    
    await user_service.confirmed_email(test_email)
    
    user_service.user_repository.confirmed_email.assert_called_once_with(test_email) 