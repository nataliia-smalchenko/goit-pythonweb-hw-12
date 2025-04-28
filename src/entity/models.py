"""
Database models module.

This module defines the SQLAlchemy models for the application's database.
It includes models for users, contacts, and refresh tokens, with proper
relationships and constraints defined.

The models implement proper data validation, relationships, and indexing
for efficient database operations.
"""

from datetime import datetime, date
from enum import Enum
from sqlalchemy import (
    String,
    DateTime,
    Date,
    func,
    Index,
    ForeignKey,
    Text,
    Enum as SqlEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property


class Base(DeclarativeBase):
    """
    Base class for all database models.

    This class serves as the base for all SQLAlchemy models in the application.
    It provides common functionality and configuration for all models.
    """
    pass


class Contact(Base):
    """
    Contact model representing a user's contact information.

    This model stores contact details including name, email, phone number,
    and additional information. It maintains relationships with users and
    implements proper indexing for efficient queries.

    Attributes:
        id (int): Primary key
        first_name (str): Contact's first name
        last_name (str): Contact's last name
        email (str): Contact's email address
        phone_number (str): Contact's phone number
        birthday (date): Contact's birthday
        additional_data (str): Additional contact information
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Record last update timestamp
        user_id (int): Foreign key to associated user
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    phone_number: Mapped[str] = mapped_column(
        String(20), nullable=True, unique=True, index=True
    )
    birthday: Mapped[date] = mapped_column(Date, nullable=True)
    additional_data: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=True
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    __table_args__ = (Index("ix_full_name", "first_name", "last_name"),)

    owner: Mapped["User"] = relationship("User", back_populates="contacts")

    @hybrid_property
    def full_name(self) -> str:
        """
        Get the contact's full name.

        Returns:
            str: Concatenated first and last name
        """
        return f"{self.first_name} {self.last_name}"

    @full_name.expression
    def full_name(cls):
        """
        SQL expression for full name.

        Returns:
            SQL expression: Concatenated first and last name for SQL queries
        """
        return func.concat(cls.first_name, " ", cls.last_name)

    def __repr__(self) -> str:
        """
        String representation of the contact.

        Returns:
            str: Formatted string with contact details
        """
        return (
            f"Student(id={self.id}, first_name={self.first_name}, "
            f"last_name={self.last_name}, email={self.email}, phone={self.phone_number})"
        )


class UserRole(str, Enum):
    """
    User role enumeration.

    This enum defines the possible roles for users in the system:
    - USER: Regular user
    - MODERATOR: User with moderation privileges
    - ADMIN: Administrator with full access
    """
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class User(Base):
    """
    User model representing system users.

    This model stores user information including authentication details,
    profile information, and role assignments. It maintains relationships
    with contacts and refresh tokens.

    Attributes:
        id (int): Primary key
        email (str): User's email address
        hashed_password (str): Hashed user password
        username (str): User's username
        is_verified (bool): Email verification status
        role (UserRole): User's role in the system
        avatar_url (str): URL to user's avatar
        created_at (datetime): Account creation timestamp
        updated_at (datetime): Last update timestamp
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), default=UserRole.USER, nullable=False
    )
    avatar_url: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="owner", cascade="all, delete-orphan")

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        String representation of the user.

        Returns:
            str: Formatted string with user details
        """
        return f"User(id={self.id}, email={self.email}, username={self.username})"


class RefreshToken(Base):
    """
    Refresh token model for user authentication.

    This model stores refresh tokens used for maintaining user sessions.
    It includes token validation information and user association.

    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to associated user
        token_hash (str): Hashed token value
        created_at (datetime): Token creation timestamp
        expired_at (datetime): Token expiration timestamp
        revoked_at (datetime): Token revocation timestamp
        ip_address (str): IP address of token creation
        user_agent (str): User agent string of token creation
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    expired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        """
        String representation of the refresh token.

        Returns:
            str: Formatted string with token details
        """
        return f"RefreshToken(id={self.id}, user_id={self.user_id}, expired_at={self.expired_at})"
