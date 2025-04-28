import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import User, UserRole
from src.schemas.user import UserResponse, ResetPasswordResponse
from src.schemas.email import RequestEmail
from src.schemas.user import NewPasswordModel
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from fastapi import status
from src.api.users import router
from src.core.depend_service import get_user_service, get_auth_service
from redis.asyncio import Redis
import jwt
from src.conf.config import config

pytestmark = pytest.mark.asyncio

# Create a properly signed test token
def create_test_token(email: str = "test@example.com") -> str:
    payload = {
        "sub": email,
        "iat": datetime.now(timezone.utc).timestamp(),
        "type": "access"
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)

TEST_ACCESS_TOKEN = create_test_token()
TEST_REFRESH_TOKEN = create_test_token()

@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    if loop.is_running():
        loop.stop()
    if not loop.is_closed():
        loop.close()

@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    return mock

@pytest.fixture(scope="module")
def test_user_data():
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "hashed_password": "hashedpass123",
        "is_verified": True,
        "role": UserRole.USER,
        "avatar_url": None,
        "created_at": None,
        "updated_at": None
    }

@pytest.fixture
def test_admin_data():
    timestamp = datetime.now().timestamp()
    return {
        "email": f"admin_{timestamp}@example.com",
        "username": f"admin_{timestamp}",
        "is_verified": True,
        "hashed_password": "hashed_adminpass123",
        "role": UserRole.ADMIN,
        "avatar_url": None
    }

@pytest.fixture
def test_moderator_data():
    timestamp = datetime.now().timestamp()
    return {
        "email": f"moderator_{timestamp}@example.com",
        "username": f"moderator_{timestamp}",
        "is_verified": True,
        "hashed_password": "hashed_modpass123",
        "role": UserRole.MODERATOR,
        "avatar_url": None
    }

@pytest.fixture
def mock_user_service():
    mock = AsyncMock()
    
    async def get_user_by_id_mock(user_id: int):
        if user_id == 1:
            return User(**test_user_data)
        return None
    
    async def update_avatar_mock(user_id: int, url: str):
        user_data = test_user_data.copy()
        user_data["avatar_url"] = url
        return User(**user_data)
    
    async def update_password_mock(user_id: int, password: str):
        return User(**test_user_data)
    
    mock.get_user_by_id = get_user_by_id_mock
    mock.update_avatar = update_avatar_mock
    mock.update_password = update_password_mock
    return mock

@pytest.fixture
def mock_auth_service(test_user_data):
    auth_service = AsyncMock()
    user = User(**test_user_data)
    
    auth_service.get_current_user.return_value = user
    auth_service.get_email_from_token.return_value = test_user_data["email"]
    auth_service.create_email_token.return_value = "test_email_token"
    auth_service.create_access_token.return_value = TEST_ACCESS_TOKEN
    auth_service.create_refresh_token.return_value = TEST_REFRESH_TOKEN
    
    def mock_decode_token(token):
        try:
            return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        except jwt.InvalidTokenError:
            return None
    
    auth_service.decode_token.side_effect = mock_decode_token
    auth_service.decode_and_validate_access_token.return_value = {"sub": test_user_data["email"], "type": "access"}
    auth_service.decode_and_validate_refresh_token.return_value = {"sub": test_user_data["email"], "type": "refresh"}
    auth_service.validate_token.return_value = True
    auth_service.verify_email_token.return_value = True
    
    return auth_service

@pytest.fixture
def mock_upload_file_service():
    service = AsyncMock()
    service.upload_file.return_value = "http://example.com/avatar.jpg"
    return service

@pytest.fixture
def mock_email_service():
    email_service = AsyncMock()
    return email_service

@pytest.fixture
def client(mock_user_service, mock_auth_service, mock_redis):
    router.dependency_overrides = {}
    router.dependency_overrides[get_user_service] = lambda: mock_user_service
    router.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    router.dependency_overrides[Redis] = lambda: mock_redis
    client = TestClient(router)
    yield client
    router.dependency_overrides = {}

@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {TEST_ACCESS_TOKEN}"}

@pytest.mark.asyncio
async def test_get_user_me(client, mock_user_service):
    response = await client.get("/api/users/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]

@pytest.mark.asyncio
async def test_update_avatar(client, mock_user_service):
    new_avatar_url = "https://example.com/avatar.jpg"
    response = await client.patch("/api/users/avatar", json={"url": new_avatar_url})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["avatar_url"] == new_avatar_url

@pytest.mark.asyncio
async def test_update_password(client, mock_user_service, mock_redis):
    mock_redis.get.return_value = b"valid_token"
    response = await client.patch(
        "/api/users/password",
        json={
            "token": "valid_token",
            "new_password": "newpass123"
        }
    )
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_confirmed_email(client, mock_auth_service, mock_user_service):
    response = client.get("/users/confirmed_email/test_token")
    assert response.status_code == status.HTTP_200_OK
    mock_auth_service.get_email_from_token.assert_called_once_with("test_token")
    mock_user_service.confirmed_email.assert_called_once()

@pytest.mark.asyncio
async def test_request_email(client, mock_user_service, mock_email_service):
    response = client.post("/users/request_email", json={"email": "test@example.com"})
    assert response.status_code == status.HTTP_201_CREATED
    mock_user_service.get_user_by_email.assert_called_once()

@pytest.mark.asyncio
async def test_read_moderator(client, mock_auth_service, auth_headers):
    response = client.get("/users/moderator", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_read_admin(client, mock_auth_service, auth_headers):
    response = client.get("/users/admin", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_reset_password(client, mock_user_service, test_user_data):
    response = client.post("/users/reset-password", json={"email": test_user_data["email"]})
    assert response.status_code == status.HTTP_202_ACCEPTED

@pytest.mark.asyncio
async def test_password_reset(client, mock_auth_service, mock_user_service):
    token = "test_reset_token"
    new_password = "new_password123"
    response = client.post(f"/users/reset_password/{token}", json={"new_password": new_password})
    assert response.status_code == status.HTTP_200_OK
    mock_auth_service.get_email_from_token.assert_called_once_with(token)
    mock_user_service.update_password.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit(client, auth_headers, mock_redis):
    # Test rate limiting
    mock_redis.exists.return_value = True  # Simulate rate limit hit
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS 