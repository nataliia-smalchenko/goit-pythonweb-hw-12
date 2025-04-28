from datetime import datetime, date
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import Base, Contact, User, UserRole, RefreshToken
from src.services.auth import AuthService
from sqlalchemy import select

@pytest.mark.asyncio
async def test_contact_creation(session: AsyncSession):
    # Create a test user first
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        username="testuser",
        is_verified=False,
        role=UserRole.USER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create a contact
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone_number="+1234567890",
        birthday=date(1990, 1, 1),
        additional_data="Test data",
        user_id=user.id
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)

    # Retrieve the contact
    retrieved_contact = await session.get(Contact, contact.id)
    
    assert retrieved_contact.first_name == "John"
    assert retrieved_contact.last_name == "Doe"
    assert retrieved_contact.email == "john@example.com"
    assert retrieved_contact.phone_number == "+1234567890"
    assert retrieved_contact.birthday == date(1990, 1, 1)
    assert retrieved_contact.additional_data == "Test data"
    assert retrieved_contact.user_id == user.id
    assert retrieved_contact.full_name == "John Doe"
    assert isinstance(retrieved_contact.created_at, datetime)
    assert isinstance(retrieved_contact.updated_at, datetime)

@pytest.mark.asyncio
async def test_user_creation(session: AsyncSession):
    user = User(
        email="test2@example.com",
        hashed_password="hashed_password",
        username="testuser2",
        role=UserRole.ADMIN,
        avatar_url="http://example.com/avatar.jpg",
        is_verified=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    retrieved_user = await session.get(User, user.id)
    
    assert retrieved_user.email == "test2@example.com"
    assert retrieved_user.hashed_password == "hashed_password"
    assert retrieved_user.username == "testuser2"
    assert retrieved_user.role == UserRole.ADMIN
    assert retrieved_user.avatar_url == "http://example.com/avatar.jpg"
    assert retrieved_user.is_verified is True
    assert isinstance(retrieved_user.created_at, datetime)
    assert isinstance(retrieved_user.updated_at, datetime)

@pytest.mark.asyncio
async def test_refresh_token_creation(session: AsyncSession):
    # Create a test user first
    user = User(
        email="test3@example.com",
        hashed_password="hashed_password",
        username="testuser3",
        is_verified=False,
        role=UserRole.USER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create a refresh token
    current_time = datetime.now()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash="test_token_hash",
        expired_at=current_time,
        ip_address="127.0.0.1",
        user_agent="Test User Agent"
    )
    session.add(refresh_token)
    await session.commit()
    await session.refresh(refresh_token)

    retrieved_token = await session.get(RefreshToken, refresh_token.id)
    
    assert retrieved_token.user_id == user.id
    assert retrieved_token.token_hash == "test_token_hash"
    assert isinstance(retrieved_token.created_at, datetime)
    assert isinstance(retrieved_token.expired_at, datetime)
    assert retrieved_token.revoked_at is None
    assert retrieved_token.ip_address == "127.0.0.1"
    assert retrieved_token.user_agent == "Test User Agent"

@pytest.mark.asyncio
async def test_contact_user_relationship(session: AsyncSession):
    # Create a user
    user = User(
        email="test4@example.com",
        hashed_password="hashed_password",
        username="testuser4",
        is_verified=False,
        role=UserRole.USER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create contacts for the user
    contact1 = Contact(
        first_name="John",
        last_name="Doe",
        user_id=user.id
    )
    contact2 = Contact(
        first_name="Jane",
        last_name="Doe",
        user_id=user.id
    )
    session.add_all([contact1, contact2])
    await session.commit()

    # Test the relationship by querying contacts directly
    contacts = await session.execute(
        select(Contact).where(Contact.user_id == user.id)
    )
    contacts = contacts.scalars().all()
    
    assert len(contacts) == 2
    contacts = sorted(contacts, key=lambda x: x.first_name)
    assert contacts[0].first_name == "Jane"
    assert contacts[1].first_name == "John"
    assert contacts[0].owner == user
    assert contacts[1].owner == user

@pytest.mark.asyncio
async def test_user_refresh_token_relationship(session: AsyncSession):
    # Create a user
    user = User(
        email="test5@example.com",
        hashed_password="hashed_password",
        username="testuser5",
        is_verified=False,
        role=UserRole.USER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create refresh tokens for the user
    current_time = datetime.now()
    token1 = RefreshToken(
        user_id=user.id,
        token_hash="token1",
        expired_at=current_time
    )
    token2 = RefreshToken(
        user_id=user.id,
        token_hash="token2",
        expired_at=current_time
    )
    session.add_all([token1, token2])
    await session.commit()

    # Test the relationship by querying tokens directly
    tokens = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    tokens = tokens.scalars().all()
    
    assert len(tokens) == 2
    tokens = sorted(tokens, key=lambda x: x.token_hash)
    assert tokens[0].token_hash == "token1"
    assert tokens[1].token_hash == "token2"
    assert tokens[0].user == user
    assert tokens[1].user == user 