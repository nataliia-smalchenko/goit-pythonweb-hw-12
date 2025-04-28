import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.users import UserRepository
from src.entity.models import User, UserRole
from src.schemas.user import UserCreate

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture(scope="function")
async def user_repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session)

@pytest_asyncio.fixture(scope="function")
async def test_user(user_repository: UserRepository) -> User:
    user_data = UserCreate(
        email="test1@example.com",
        username="testuser1",
        password="testpass123"
    )
    user = await user_repository.create_user(
        user_data=user_data,
        hashed_password="hashed_password",
        avatar="http://example.com/avatar.jpg"
    )
    yield user
    await user_repository.delete(user)

@pytest.mark.asyncio
async def test_get_by_email(user_repository: UserRepository, test_user: User):
    # Test existing user
    found_user = await user_repository.get_by_email(test_user.email)
    assert found_user is not None
    assert found_user.email == test_user.email
    assert found_user.username == test_user.username

    # Test non-existent user
    non_existent = await user_repository.get_by_email("nonexistent@example.com")
    assert non_existent is None

@pytest.mark.asyncio
async def test_get_by_username(user_repository: UserRepository, test_user: User):
    # Test existing user
    found_user = await user_repository.get_by_username(test_user.username)
    assert found_user is not None
    assert found_user.email == test_user.email
    assert found_user.username == test_user.username

    # Test non-existent user
    non_existent = await user_repository.get_by_username("nonexistent")
    assert non_existent is None

@pytest.mark.asyncio
async def test_create_user(user_repository: UserRepository):
    # Test successful creation
    user_data = UserCreate(
        email="test2@example.com",
        username="testuser2",
        password="testpass123"
    )
    user = await user_repository.create_user(
        user_data=user_data,
        hashed_password="hashed_password",
        avatar="http://example.com/avatar.jpg"
    )
    assert user is not None
    assert user.email == user_data.email
    assert user.username == user_data.username
    assert user.hashed_password == "hashed_password"
    assert user.avatar_url == "http://example.com/avatar.jpg"
    assert user.is_verified is False
    assert user.role == UserRole.USER

    # Cleanup
    await user_repository.delete(user)

@pytest.mark.asyncio
async def test_confirmed_email(user_repository: UserRepository, test_user: User):
    # Test successful confirmation
    assert test_user.is_verified is False
    await user_repository.confirmed_email(test_user.email)
    updated_user = await user_repository.get_by_email(test_user.email)
    assert updated_user.is_verified is True

@pytest.mark.asyncio
async def test_update_avatar_url(user_repository: UserRepository, test_user: User):
    # Test admin update
    admin_user = await user_repository.create_user(
        user_data=UserCreate(
            email="admin@example.com",
            username="admin",
            password="adminpass"
        ),
        hashed_password="hashed_password",
        avatar="http://example.com/avatar.jpg"
    )
    admin_user.role = UserRole.ADMIN
    await user_repository.db.commit()

    new_avatar = "http://example.com/new_avatar.jpg"
    updated_user = await user_repository.update_avatar_url(
        email=admin_user.email,
        url=new_avatar
    )
    assert updated_user.avatar == new_avatar

    # Test non-admin update
    non_admin_user = await user_repository.create_user(
        user_data=UserCreate(
            email="user@example.com",
            username="regularuser",
            password="userpass"
        ),
        hashed_password="hashed_password",
        avatar="http://example.com/avatar.jpg"
    )

    with pytest.raises(PermissionError):
        await user_repository.update_avatar_url(
            email=non_admin_user.email,
            url=new_avatar
        )

    # Cleanup
    await user_repository.delete(admin_user)
    await user_repository.delete(non_admin_user)

@pytest.mark.asyncio
async def test_update_password(user_repository: UserRepository, test_user: User):
    # Test successful update
    new_password = "new_hashed_password"
    updated_user = await user_repository.update_password(
        email=test_user.email,
        hashed_password=new_password
    )
    assert updated_user.hashed_password == new_password 