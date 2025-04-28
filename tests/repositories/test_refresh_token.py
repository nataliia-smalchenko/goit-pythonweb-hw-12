import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.refresh_token import RefreshTokenRepository
from src.entity.models import RefreshToken

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture()
async def refresh_token_repository(session: AsyncSession) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)

@pytest_asyncio.fixture(scope="function")
async def test_refresh_token(refresh_token_repository: RefreshTokenRepository) -> RefreshToken:
    token_hash = f"test_token_hash_{datetime.utcnow().timestamp()}"  # Generate unique hash
    current_time = datetime.utcnow()
    token = await refresh_token_repository.save_token(
        user_id=1,
        token_hash=token_hash,
        expired_at=current_time + timedelta(days=1),
        ip_address="127.0.0.1",
        user_agent="test-agent"
    )
    return token

async def test_get_by_token_hash(refresh_token_repository: RefreshTokenRepository, test_refresh_token: RefreshToken):
    # Test getting existing token
    token = await refresh_token_repository.get_by_token_hash(test_refresh_token.token_hash)
    assert token is not None
    assert token.token_hash == test_refresh_token.token_hash
    
    # Test getting non-existent token
    token = await refresh_token_repository.get_by_token_hash("non_existent_hash")
    assert token is None

async def test_get_active_token(refresh_token_repository: RefreshTokenRepository, test_refresh_token: RefreshToken):
    current_time = datetime.utcnow()
    
    # Test getting active token
    token = await refresh_token_repository.get_active_token(test_refresh_token.token_hash, current_time)
    assert token is not None
    assert token.token_hash == test_refresh_token.token_hash
    assert token.revoked_at is None
    
    # Test getting expired token
    test_refresh_token.expired_at = current_time - timedelta(days=1)
    await refresh_token_repository.db.commit()
    token = await refresh_token_repository.get_active_token(test_refresh_token.token_hash, current_time)
    assert token is None
    
    # Test getting revoked token
    test_refresh_token.expired_at = current_time + timedelta(days=1)
    await refresh_token_repository.revoke_token(test_refresh_token)
    token = await refresh_token_repository.get_active_token(test_refresh_token.token_hash, current_time)
    assert token is None

async def test_save_token(refresh_token_repository: RefreshTokenRepository):
    current_time = datetime.utcnow()
    expired_at = current_time + timedelta(days=1)
    token_hash = f"test_token_hash_{datetime.utcnow().timestamp()}"  # Generate unique hash
    
    token = await refresh_token_repository.save_token(
        user_id=1,
        token_hash=token_hash,
        expired_at=expired_at,
        ip_address="127.0.0.1",
        user_agent="test-agent"
    )
    assert token is not None
    assert token.token_hash == token_hash
    assert token.user_id == 1
    assert token.expired_at == expired_at
    assert token.revoked_at is None

async def test_revoke_token(refresh_token_repository: RefreshTokenRepository):
    current_time = datetime.utcnow()
    token_hash = f"test_token_hash_{datetime.utcnow().timestamp()}"  # Generate unique hash
    
    # Create a new token specifically for this test
    token = await refresh_token_repository.save_token(
        user_id=1,
        token_hash=token_hash,
        expired_at=current_time + timedelta(days=1),
        ip_address="127.0.0.1",
        user_agent="test-agent"
    )
    
    assert token.revoked_at is None
    await refresh_token_repository.revoke_token(token)
    assert token.revoked_at is not None
    
    # Verify the token is revoked in the database
    db_token = await refresh_token_repository.get_by_token_hash(token_hash)
    assert db_token is not None
    assert db_token.revoked_at is not None 