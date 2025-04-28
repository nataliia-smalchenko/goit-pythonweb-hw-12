import pytest
import pytest_asyncio
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.contacts import ContactRepository
from src.entity.models import Contact, User, UserRole
from src.schemas.contact import ContactCreateSchema, ContactUpdateSchema
from src.schemas.user import UserCreate


@pytest_asyncio.fixture(scope="function")
async def test_user(session: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashedpass123",
        is_verified=False,
        role=UserRole.USER,
        avatar_url="http://example.com/avatar.jpg"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    yield user
    await session.delete(user)
    await session.commit()


@pytest.mark.asyncio
async def test_get_contacts(session: AsyncSession, test_user):
    """Test getting contacts with pagination"""
    repo = ContactRepository(session)
    
    # Create test contacts
    contacts = [
        Contact(
            first_name=f"Test{i}",
            last_name="User",
            email=f"test{i}@example.com",
            phone_number=f"1111111111{i}",
            birthday=date(1990, 1, 1),
            user_id=test_user.id
        ) for i in range(5)
    ]
    for contact in contacts:
        session.add(contact)
    await session.commit()

    # Test getting all contacts
    result = await repo.get_contacts(test_user.id)
    assert len(result) == 5

    # Test pagination
    result = await repo.get_contacts(test_user.id, limit=2, offset=2)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_contact_by_id(session: AsyncSession, test_user):
    """Test getting a contact by ID"""
    repo = ContactRepository(session)
    
    # Create test contact
    contact = Contact(
        first_name="Test",
        last_name="User",
        email="test_get_by_id@example.com",
        phone_number="2222222222",
        birthday=date(1990, 1, 1),
        user_id=test_user.id
    )
    session.add(contact)
    await session.commit()

    # Test getting existing contact
    result = await repo.get_contact_by_id(contact.id, test_user.id)
    assert result is not None
    assert result.first_name == "Test"

    # Test getting non-existent contact
    result = await repo.get_contact_by_id(999, test_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_create_contact(session: AsyncSession, test_user):
    """Test creating a new contact"""
    repo = ContactRepository(session)
    
    # Create contact data
    contact_data = ContactCreateSchema(
        first_name="Test",
        last_name="User",
        email="test_create@example.com",
        phone_number="3333333333",
        birthday=date(1990, 1, 1)
    )

    # Test successful creation
    contact = await repo.create_contact(contact_data, test_user.id)
    assert contact is not None
    assert contact.first_name == "Test"
    assert contact.user_id == test_user.id

    # Test duplicate email
    with pytest.raises(ValueError):
        await repo.create_contact(contact_data, test_user.id)

    # Test duplicate phone
    contact_data.email = "test_create2@example.com"
    with pytest.raises(ValueError):
        await repo.create_contact(contact_data, test_user.id)


@pytest.mark.asyncio
async def test_update_contact(session: AsyncSession, test_user):
    """Test updating a contact"""
    repo = ContactRepository(session)
    
    # Create test contact
    contact = Contact(
        first_name="Test",
        last_name="User",
        email="test_update@example.com",
        phone_number="4444444444",
        birthday=date(1990, 1, 1),
        user_id=test_user.id
    )
    session.add(contact)
    await session.commit()

    # Create another contact for duplicate testing
    contact2 = Contact(
        first_name="Test2",
        last_name="User2",
        email="test_update2@example.com",
        phone_number="4444444445",
        birthday=date(1990, 1, 1),
        user_id=test_user.id
    )
    session.add(contact2)
    await session.commit()

    # Test successful update
    update_data = ContactUpdateSchema(first_name="Updated")
    updated_contact = await repo.update_contact(contact.id, update_data, test_user.id)
    assert updated_contact is not None
    assert updated_contact.first_name == "Updated"

    # Test update with duplicate email
    update_data = ContactUpdateSchema(email="test_update2@example.com")
    with pytest.raises(ValueError):
        await repo.update_contact(contact.id, update_data, test_user.id)

    # Test update with duplicate phone
    update_data = ContactUpdateSchema(phone_number="4444444445")
    with pytest.raises(ValueError):
        await repo.update_contact(contact.id, update_data, test_user.id)

    # Test update non-existent contact
    result = await repo.update_contact(999, update_data, test_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_remove_contact(session: AsyncSession, test_user):
    """Test removing a contact"""
    repo = ContactRepository(session)
    
    # Create test contact
    contact = Contact(
        first_name="Test",
        last_name="User",
        email="test_remove@example.com",
        phone_number="5555555555",
        birthday=date(1990, 1, 1),
        user_id=test_user.id
    )
    session.add(contact)
    await session.commit()

    # Test successful removal
    removed_contact = await repo.remove_contact(contact.id, test_user.id)
    assert removed_contact is not None
    assert removed_contact.id == contact.id

    # Verify contact is removed
    result = await repo.get_contact_by_id(contact.id, test_user.id)
    assert result is None

    # Test removing non-existent contact
    result = await repo.remove_contact(999, test_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_search_contacts(session: AsyncSession, test_user):
    """Test searching contacts"""
    repo = ContactRepository(session)
    
    # Create test contacts
    contacts = [
        Contact(
            first_name="John",
            last_name="Doe",
            email="john_search@example.com",
            phone_number="6666666666",
            birthday=date(1990, 1, 1),
            user_id=test_user.id
        ),
        Contact(
            first_name="Jane",
            last_name="Doe",
            email="jane_search@example.com",
            phone_number="6666666667",
            birthday=date(1990, 1, 1),
            user_id=test_user.id
        )
    ]
    for contact in contacts:
        session.add(contact)
    await session.commit()

    # Test search by first name
    result = await repo.search_contacts(test_user.id, first_name="John")
    assert len(result) == 1
    assert result[0].first_name == "John"

    # Test search by last name
    result = await repo.search_contacts(test_user.id, last_name="Doe")
    assert len(result) == 2

    # Test search by email
    result = await repo.search_contacts(test_user.id, email="john_search@example.com")
    assert len(result) == 1
    assert result[0].email == "john_search@example.com"

    # Test pagination
    result = await repo.search_contacts(test_user.id, last_name="Doe", limit=1)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_contacts_with_upcoming_birthdays(session: AsyncSession, test_user):
    """Test getting contacts with upcoming birthdays"""
    repo = ContactRepository(session)
    
    # Get current date
    today = date.today()
    
    # Create test contacts with different birthdays
    contacts = [
        Contact(
            first_name="Today",
            last_name="Birthday",
            email="today_birthday@example.com",
            phone_number="7777777777",
            birthday=today,
            user_id=test_user.id
        ),
        Contact(
            first_name="Tomorrow",
            last_name="Birthday",
            email="tomorrow_birthday@example.com",
            phone_number="7777777778",
            birthday=today + timedelta(days=1),
            user_id=test_user.id
        ),
        Contact(
            first_name="Next Week",
            last_name="Birthday",
            email="nextweek_birthday@example.com",
            phone_number="7777777779",
            birthday=today + timedelta(days=7),
            user_id=test_user.id
        ),
        Contact(
            first_name="Next Month",
            last_name="Birthday",
            email="nextmonth_birthday@example.com",
            phone_number="7777777780",
            birthday=today + timedelta(days=30),
            user_id=test_user.id
        ),
        Contact(
            first_name="Last Month",
            last_name="Birthday",
            email="lastmonth_birthday@example.com",
            phone_number="7777777781",
            birthday=today - timedelta(days=30),
            user_id=test_user.id
        )
    ]
    for contact in contacts:
        session.add(contact)
    await session.commit()

    # Test getting contacts with upcoming birthdays
    result = await repo.get_contacts_with_upcoming_birthdays(test_user.id)
    
    # Get the birthdays from the result
    result_birthdays = {contact.birthday for contact in result}
    expected_birthdays = {
        today,
        today + timedelta(days=1),
        today + timedelta(days=7)
    }
    
    assert result_birthdays == expected_birthdays 