"""
User service for managing user operations.

This module provides business logic for user management operations including:
- User creation and registration
- User profile management
- Email confirmation
- Password updates
- Avatar management

The service acts as an intermediary between the API layer and the repository layer,
implementing business rules and data validation.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.users import UserRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService


class UserService:
    """
    Service class for user management operations.

    This class provides methods for managing users, including registration,
    profile management, and authentication-related operations. It uses both
    the user repository and auth service for data access and security operations.

    Attributes:
        db (AsyncSession): Database session for operations
        user_repository (UserRepository): Repository for user operations
        auth_service (AuthService): Service for authentication operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the UserService.

        Args:
            db (AsyncSession): Database session for operations
        """
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data (UserCreate): User registration data

        Returns:
            User: Newly created user
        """
        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Get a user by username.

        Args:
            username (str): Username to search for

        Returns:
            User | None: User if found, None otherwise
        """
        user = await self.user_repository.get_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Get a user by email.

        Args:
            email (str): Email to search for

        Returns:
            User | None: User if found, None otherwise
        """
        user = await self.user_repository.get_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Confirm a user's email address.

        Args:
            email (str): Email address to confirm
        """
        user = await self.user_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        """
        Update a user's avatar URL.

        Args:
            email (str): Email of the user to update
            url (str): New avatar URL

        Returns:
            User: Updated user
        """
        return await self.user_repository.update_avatar_url(email, url)

    async def update_password(self, email: str, new_password: str) -> User:
        """
        Update a user's password.

        Args:
            email (str): Email of the user to update
            new_password (str): New password to set

        Returns:
            User: Updated user
        """
        hashed_password = self.auth_service._hash_password(new_password)
        user = await self.user_repository.update_password(email, hashed_password)
        return user
