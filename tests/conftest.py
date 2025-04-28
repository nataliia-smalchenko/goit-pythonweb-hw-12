import asyncio
import pytest
import pytest_asyncio
import logging
import jwt
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, FastAPI
from sqlalchemy import text
from redis.asyncio import Redis
from fastapi import status

from src.entity.models import Base, User, UserRole, Contact, RefreshToken
from src.services.auth import AuthService
from src.conf.config import config
from main import app
from src.database.db import get_db
from src.schemas.user import UserRole
from src.core.depend_service import get_redis, get_auth_service, get_user_service
from src.services.user import UserService
from src.services.email import send_email, send_reset_password_email
from src.api.auth import router as auth_router
from src.api.users import router as users_router

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False, 
    bind=engine,
    class_=AsyncSession,
)

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest_asyncio.fixture
async def session(init_models):
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
            # Clean up all tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)

@pytest.fixture
def mock_redis():
    redis_mock = AsyncMock(spec=Redis)
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.exists.return_value = False
    return redis_mock

@pytest.fixture
def app(session, mock_redis):
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    app.include_router(users_router, prefix="/users")

    async def override_db():
        try:
            yield session
        finally:
            await session.close()

    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def user():
    return {"email": "test@example.com", "username": "testuser", "password": "testpass123"}

@pytest.fixture
def mock_email_service():
    """Mock email service functions."""
    async def mock_send_email(*args, **kwargs):
        return None
    
    async def mock_send_reset_password_email(*args, **kwargs):
        return None
    
    email_service = AsyncMock()
    email_service.send_verification_email = mock_send_email
    email_service.send_reset_password_email = mock_send_reset_password_email
    return email_service

@pytest.fixture
def mock_user_service(session):
    user_service = AsyncMock(spec=UserService)
    user_service.get_user_by_email.return_value = None
    user_service.create_user.return_value = User(
        id=1,
        email="test@example.com",
        username="testuser",
        hashed_password="hashedpass123",
        is_verified=False
    )
    user_service.update_avatar_url.return_value = None
    user_service.confirmed_email.return_value = None
    return user_service

@pytest.fixture
def mock_auth_service():
    auth_service = AsyncMock()
    
    # Configure basic auth operations
    auth_service._hash_password = lambda password: "hashedpass123"
    auth_service.get_password_hash = auth_service._hash_password
    auth_service._verify_password.return_value = True
    
    # Configure token operations
    auth_service.create_access_token.return_value = "test_access_token"
    auth_service.create_refresh_token.return_value = "test_refresh_token"
    auth_service.create_email_token.return_value = "test_email_token"
    auth_service.get_email_from_token.return_value = "test@example.com"
    auth_service.decode_and_validate_access_token.return_value = {"sub": "test@example.com"}
    auth_service.validate_token.return_value = True
    
    return auth_service

@pytest.fixture(autouse=True)
def override_dependencies(app, mock_auth_service, mock_user_service, mock_email_service):
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    return app
