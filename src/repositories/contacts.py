"""
Contact repository for database operations.

This module provides a repository class for contact-related database operations.
It implements methods for CRUD operations, search functionality, and birthday
management for contacts. The repository ensures data integrity and proper
validation of contact information.

The repository handles user-specific contact management and implements
unique constraints for email and phone numbers per user.
"""

import logging
from typing import Sequence, Optional
from datetime import date, timedelta

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact
from src.schemas.contact import ContactCreateSchema, ContactUpdateSchema

logger = logging.getLogger("uvicorn.error")


class ContactRepository:
    """
    Repository class for contact database operations.

    This class provides methods for managing contacts in the database,
    including CRUD operations, search functionality, and birthday management.
    It ensures proper data validation and user-specific contact management.

    Attributes:
        db (AsyncSession): Database session for operations
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the contact repository.

        Args:
            session (AsyncSession): Database session for operations
        """
        self.db = session

    async def get_contacts(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> Sequence[Contact]:
        """
        Get a paginated list of contacts for a specific user.

        Args:
            user_id (int): ID of the user
            limit (int): Maximum number of contacts to return
            offset (int): Number of contacts to skip

        Returns:
            Sequence[Contact]: List of contacts
        """
        stmt = (
            select(Contact)
            .where(Contact.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(
        self, contact_id: int, user_id: int
    ) -> Optional[Contact]:
        """
        Get a contact by its ID for a specific user.

        Args:
            contact_id (int): ID of the contact to retrieve
            user_id (int): ID of the user

        Returns:
            Optional[Contact]: Contact if found, None otherwise
        """
        stmt = select(Contact).where(
            Contact.id == contact_id, Contact.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactCreateSchema, user_id: int) -> Contact:
        """
        Create a new contact with email/phone uniqueness check for a user.

        Args:
            body (ContactCreateSchema): Contact data to create
            user_id (int): ID of the user creating the contact

        Returns:
            Contact: Newly created contact

        Raises:
            ValueError: If email or phone number already exists for the user
        """
        if body.email:
            stmt = select(Contact).where(
                Contact.email == body.email, Contact.user_id == user_id
            )
            existing_contact = await self.db.execute(stmt)
            if existing_contact.scalar_one_or_none():
                raise ValueError(
                    "Контакт з таким email вже існує для цього користувача"
                )

        if body.phone_number:
            stmt = select(Contact).where(
                Contact.phone_number == body.phone_number, Contact.user_id == user_id
            )
            existing_contact = await self.db.execute(stmt)
            if existing_contact.scalar_one_or_none():
                raise ValueError(
                    "Контакт з таким телефоном вже існує для цього користувача"
                )

        contact_data = body.model_dump()
        contact = Contact(user_id=user_id, **contact_data)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactUpdateSchema, user_id: int
    ) -> Optional[Contact]:
        """
        Update a contact with email/phone uniqueness check for a user.

        Args:
            contact_id (int): ID of the contact to update
            body (ContactUpdateSchema): Updated contact data
            user_id (int): ID of the user updating the contact

        Returns:
            Optional[Contact]: Updated contact if found, None otherwise

        Raises:
            ValueError: If email or phone number already exists for another contact
        """
        contact = await self.get_contact_by_id(contact_id, user_id)
        if not contact:
            return None

        update_data = body.model_dump(exclude_unset=True)

        new_email = update_data.get("email")
        new_phone = update_data.get("phone_number")

        if new_email:
            stmt = select(Contact).where(
                Contact.email == new_email,
                Contact.id != contact_id,
                Contact.user_id == user_id,
            )
            existing_contact = await self.db.execute(stmt)
            if existing_contact.scalar_one_or_none():
                raise ValueError(
                    "Інший контакт вже використовує цей email для цього користувача"
                )

        if new_phone:
            stmt = select(Contact).where(
                Contact.phone_number == new_phone,
                Contact.id != contact_id,
                Contact.user_id == user_id,
            )
            existing_contact = await self.db.execute(stmt)
            if existing_contact.scalar_one_or_none():
                raise ValueError(
                    "Інший контакт вже використовує цей телефон для цього користувача"
                )

        for key, value in update_data.items():
            setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user_id: int) -> Optional[Contact]:
        """
        Remove a contact by its ID for a specific user.

        Args:
            contact_id (int): ID of the contact to remove
            user_id (int): ID of the user removing the contact

        Returns:
            Optional[Contact]: Removed contact if found, None otherwise
        """
        contact = await self.get_contact_by_id(contact_id, user_id)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Contact]:
        """
        Search contacts by name or email for a specific user.

        Args:
            user_id (int): ID of the user searching contacts
            first_name (Optional[str]): First name to search for
            last_name (Optional[str]): Last name to search for
            email (Optional[str]): Email to search for
            limit (int): Maximum number of results to return
            offset (int): Number of results to skip

        Returns:
            Sequence[Contact]: List of matching contacts
        """
        stmt = select(Contact).where(Contact.user_id == user_id)
        if first_name:
            stmt = stmt.where(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            stmt = stmt.where(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            stmt = stmt.where(Contact.email.ilike(f"%{email}%"))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contacts_with_upcoming_birthdays(
        self, user_id: int
    ) -> Sequence[Contact]:
        """
        Get contacts with upcoming birthdays (next 7 days) for a specific user.

        Args:
            user_id (int): ID of the user requesting contacts

        Returns:
            Sequence[Contact]: List of contacts with upcoming birthdays
        """
        today = date.today()
        end_date = today + timedelta(days=7)
        
        stmt = select(Contact).where(
            Contact.user_id == user_id,
            func.date(Contact.birthday).between(
                func.date(today),
                func.date(end_date)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
