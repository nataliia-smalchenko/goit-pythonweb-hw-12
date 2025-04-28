"""
Contact service for managing contact operations.

This module provides business logic for contact management operations including:
- Contact creation and retrieval
- Contact updates and deletion
- Contact search functionality
- Birthday management
- Pagination support

The service acts as an intermediary between the API layer and the repository layer,
implementing business rules and data validation.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.contacts import ContactRepository
from src.schemas.contact import ContactCreateSchema, ContactUpdateSchema


class ContactService:
    """
    Service class for contact management operations.

    This class provides methods for managing contacts, including CRUD operations,
    search functionality, and birthday management. It uses the contact repository
    for data access and implements business logic for contact operations.

    Attributes:
        contact_repository (ContactRepository): Repository for contact operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the ContactService.

        Args:
            db (AsyncSession): Database session for operations
        """
        self.contact_repository = ContactRepository(db)

    async def create_contact(self, body: ContactCreateSchema, user_id: int):
        """
        Create a new contact.

        Args:
            body (ContactCreateSchema): Contact data to create
            user_id (int): ID of the user creating the contact

        Returns:
            Contact: Newly created contact
        """
        return await self.contact_repository.create_contact(body, user_id)

    async def get_contacts(self, limit: int, offset: int, user_id: int):
        """
        Get a paginated list of contacts.

        Args:
            limit (int): Maximum number of contacts to return
            offset (int): Number of contacts to skip
            user_id (int): ID of the user requesting contacts

        Returns:
            List[Contact]: List of contacts
        """
        return await self.contact_repository.get_contacts(user_id, limit, offset)

    async def get_contact_by_id(self, contact_id: int, user_id: int):
        """
        Get a contact by its ID.

        Args:
            contact_id (int): ID of the contact to retrieve
            user_id (int): ID of the user requesting the contact

        Returns:
            Contact: Contact with the specified ID
        """
        return await self.contact_repository.get_contact_by_id(contact_id, user_id)

    async def update_contact(
        self, contact_id: int, body: ContactUpdateSchema, user_id: int
    ):
        """
        Update an existing contact.

        Args:
            contact_id (int): ID of the contact to update
            body (ContactUpdateSchema): Updated contact data
            user_id (int): ID of the user updating the contact

        Returns:
            Contact: Updated contact
        """
        return await self.contact_repository.update_contact(contact_id, body, user_id)

    async def remove_contact(self, contact_id: int, user_id: int):
        """
        Remove a contact.

        Args:
            contact_id (int): ID of the contact to remove
            user_id (int): ID of the user removing the contact

        Returns:
            Contact: Removed contact
        """
        return await self.contact_repository.remove_contact(contact_id, user_id)

    async def search_contacts(
        self,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ):
        """
        Search contacts by various criteria.

        Args:
            user_id (int): ID of the user searching contacts
            first_name (str | None): First name to search for
            last_name (str | None): Last name to search for
            email (str | None): Email to search for
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip

        Returns:
            List[Contact]: List of matching contacts
        """
        return await self.contact_repository.search_contacts(
            user_id, first_name, last_name, email, limit, offset
        )

    async def get_contacts_with_upcoming_birthdays(self, user_id: int):
        """
        Get contacts with upcoming birthdays.

        Args:
            user_id (int): ID of the user requesting contacts

        Returns:
            List[Contact]: List of contacts with upcoming birthdays
        """
        return await self.contact_repository.get_contacts_with_upcoming_birthdays(
            user_id
        )
