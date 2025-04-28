import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from src.services.auth import AuthService, redis_client
from src.entity.models import User, UserRole, RefreshToken
from src.schemas.user import UserCreate


@pytest_asyncio.fixture
async def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest_asyncio.fixture
async def mock_user_repository():
    return AsyncMock()


@pytest_asyncio.fixture
async def mock_refresh_token_repository():
    return AsyncMock()


@pytest_asyncio.fixture
async def auth_service(mock_db, mock_user_repository, mock_refresh_token_repository):
    service = AuthService(mock_db)
    service.user_repository = mock_user_repository
    service.refresh_token_repository = mock_refresh_token_repository
    return service


@pytest_asyncio.fixture
async def test_user():
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        hashed_password=b"$2b$12$dWqYBGGBXzK4Y5zPyPfCn.C7YXgp9uHhw0DJwwJwt3ZKKwJ5m2Kxm".decode(),  # password: testpass123
        is_verified=True,
        role=UserRole.USER,
        avatar_url="http://example.com/avatar.jpg"
    )


@pytest_asyncio.fixture
async def test_user_data():
    return UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpass123"
    )


@pytest.mark.asyncio
async def test_authenticate_success(auth_service, test_user):
    # Arrange
    auth_service.user_repository.get_by_username.return_value = test_user
    auth_service._verify_password = MagicMock(return_value=True)  # Mock password verification

    # Act
    result = await auth_service.authenticate("testuser", "testpass123")

    # Assert
    assert result == test_user
    auth_service.user_repository.get_by_username.assert_called_once_with("testuser")
    auth_service._verify_password.assert_called_once_with("testpass123", test_user.hashed_password)


@pytest.mark.asyncio
async def test_authenticate_wrong_password(auth_service, test_user):
    # Arrange
    auth_service.user_repository.get_by_username.return_value = test_user

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate("testuser", "wrongpass")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Incorrect username or password"


@pytest.mark.asyncio
async def test_authenticate_user_not_verified(auth_service, test_user):
    # Arrange
    test_user.is_verified = False
    auth_service.user_repository.get_by_username.return_value = test_user

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate("testuser", "testpass123")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Електронна адреса не підтверджена"


@pytest.mark.asyncio
async def test_register_user_success(auth_service, test_user_data, test_user):
    # Arrange
    auth_service.user_repository.get_by_username.return_value = None
    auth_service.user_repository.get_by_email.return_value = None
    auth_service.user_repository.create_user.return_value = test_user

    # Act
    result = await auth_service.register_user(test_user_data)

    # Assert
    assert result == test_user
    auth_service.user_repository.get_by_username.assert_called_once_with(test_user_data.username)
    auth_service.user_repository.get_by_email.assert_called_once_with(str(test_user_data.email))


@pytest.mark.asyncio
async def test_register_user_username_exists(auth_service, test_user_data, test_user):
    # Arrange
    auth_service.user_repository.get_by_username.return_value = test_user

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(test_user_data)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "User already exists"


@pytest.mark.asyncio
async def test_create_refresh_token(auth_service):
    # Arrange
    user_id = 1
    ip_address = "127.0.0.1"
    user_agent = "test-agent"
    auth_service.refresh_token_repository.save_token.return_value = None

    # Act
    token = await auth_service.create_refresh_token(user_id, ip_address, user_agent)

    # Assert
    assert isinstance(token, str)
    assert len(token) > 32
    auth_service.refresh_token_repository.save_token.assert_called_once()


@pytest.mark.asyncio
async def test_validate_refresh_token_success(auth_service, test_user):
    # Arrange
    token = "test_token"
    token_hash = auth_service._hash_token(token)
    refresh_token = RefreshToken(
        id=1,
        token_hash=token_hash,
        user_id=test_user.id,
        expired_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    auth_service.refresh_token_repository.get_active_token.return_value = refresh_token
    auth_service.user_repository.get_by_id.return_value = test_user

    # Act
    result = await auth_service.validate_refresh_token(token)

    # Assert
    assert result == test_user
    auth_service.refresh_token_repository.get_active_token.assert_called_once()
    auth_service.user_repository.get_by_id.assert_called_once_with(test_user.id)


@pytest.mark.asyncio
async def test_validate_refresh_token_invalid(auth_service):
    # Arrange
    token = "invalid_token"
    auth_service.refresh_token_repository.get_active_token.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.validate_refresh_token(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid refresh token"


@pytest.mark.asyncio
async def test_revoke_refresh_token(auth_service):
    # Arrange
    token = "test_token"
    token_hash = auth_service._hash_token(token)
    refresh_token = RefreshToken(
        id=1,
        token_hash=token_hash,
        user_id=1,
        expired_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    auth_service.refresh_token_repository.get_by_token_hash.return_value = refresh_token
    auth_service.refresh_token_repository.revoke_token.return_value = None

    # Act
    await auth_service.revoke_refresh_token(token)

    # Assert
    auth_service.refresh_token_repository.get_by_token_hash.assert_called_once_with(token_hash)
    auth_service.refresh_token_repository.revoke_token.assert_called_once_with(refresh_token)


@pytest.mark.asyncio
async def test_revoke_access_token(auth_service):
    # Arrange
    token = "test_access_token"
    
    with patch.object(redis_client, 'setex', new_callable=AsyncMock) as mock_setex:
        mock_setex.return_value = True

        # Act
        await auth_service.revoke_access_token(token)

        # Assert
        mock_setex.assert_called_once() 