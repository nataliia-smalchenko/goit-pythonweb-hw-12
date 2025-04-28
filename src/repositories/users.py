"""
User repository for database operations.

This module provides a repository class for user-related database operations.
It extends the base repository and implements user-specific methods for
authentication, profile management, and user verification.

The repository handles user data access and implements proper security
measures for sensitive operations.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User, UserRole
from src.repositories.base import BaseRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")


class UserRepository(BaseRepository):
    """
    Repository class for user database operations.

    This class extends the base repository and provides methods for
    user-specific database operations. It handles user authentication,
    profile management, and verification processes.

    Attributes:
        db (AsyncSession): Database session for operations
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the user repository.

        Args:
            session (AsyncSession): Database session for operations
        """
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.

        Args:
            email (str): Email address to search for

        Returns:
            Optional[User]: User if found, None otherwise
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            username (str): Username to search for

        Returns:
            Optional[User]: User if found, None otherwise
        """
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_user(
        self, user_data: UserCreate, hashed_password: str, avatar: str
    ) -> User:
        """
        Create a new user with hashed password and avatar.

        Args:
            user_data (UserCreate): User registration data
            hashed_password (str): Hashed password for the user
            avatar (str): URL of the user's avatar

        Returns:
            User: Newly created user
        """
        user = User(
            **user_data.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=hashed_password,
            avatar_url=avatar,
        )
        return await self.create(user)

    async def confirmed_email(self, email: str) -> None:
        """
        Mark a user's email as verified.

        Args:
            email (str): Email address to verify
        """
        user = await self.get_by_email(email)
        user.is_verified = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update a user's avatar URL.

        Args:
            email (str): Email of the user to update
            url (str): New avatar URL

        Returns:
            User: Updated user

        Raises:
            PermissionError: If user is not an admin
        """
        user = await self.get_by_email(email)
        if user.role != UserRole.ADMIN:
            raise PermissionError("Only admin can update avatar")

        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, email: str, hashed_password: str) -> User:
        """
        Update a user's password.

        Args:
            email (str): Email of the user to update
            hashed_password (str): New hashed password

        Returns:
            User: Updated user
        """
        user = await self.get_by_email(email)
        user.hashed_password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user
