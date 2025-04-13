import logging
from typing import Sequence, Optional

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact
from src.schemas.contact import ContactCreateSchema, ContactUpdateSchema

logger = logging.getLogger("uvicorn.error")


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> Sequence[Contact]:
        """Отримати список контактів з пагінацією для заданого користувача"""
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
        """Отримати контакт за його ідентифікатором для заданого користувача"""
        stmt = select(Contact).where(
            Contact.id == contact_id, Contact.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactCreateSchema, user_id: int) -> Contact:
        """Створити новий контакт з перевіркою унікальності email/телефону для користувача"""
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

        # Додаємо параметр user_id до даних контакту
        contact_data = body.model_dump()
        contact = Contact(user_id=user_id, **contact_data)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactUpdateSchema, user_id: int
    ) -> Optional[Contact]:
        """Оновити контакт з перевіркою унікальності email/телефону для заданого користувача"""
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
        """Видалити контакт за ідентифікатором для заданого користувача"""
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
        Пошук контактів за іменем, прізвищем чи електронною адресою для заданого користувача.
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
        Отримати контакти із днями народження, що настануть протягом наступних 7 днів,
        для заданого користувача.
        """
        stmt = select(Contact).where(
            Contact.user_id == user_id,
            func.to_char(Contact.birthday, "MM-DD").between(
                func.to_char(func.current_date(), "MM-DD"),
                func.to_char(func.current_date() + text("interval '7 days'"), "MM-DD"),
            ),
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
