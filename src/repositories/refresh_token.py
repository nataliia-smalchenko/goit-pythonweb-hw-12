"""
Refresh token repository for database operations.

This module provides a repository class for managing refresh tokens in the database.
It extends the base repository and implements methods for token validation,
creation, and revocation. The repository ensures proper token lifecycle management
and security measures.

The repository handles token storage, validation, and cleanup operations.
"""

import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken
from src.repositories.base import BaseRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")


class RefreshTokenRepository(BaseRepository):
    """
    Repository class for refresh token database operations.

    This class extends the base repository and provides methods for
    managing refresh tokens. It handles token creation, validation,
    and revocation processes.

    Attributes:
        db (AsyncSession): Database session for operations
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the refresh token repository.

        Args:
            session (AsyncSession): Database session for operations
        """
        super().__init__(session, RefreshToken)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """
        Get a refresh token by its hash.

        Args:
            token_hash (str): Hash of the token to find

        Returns:
            RefreshToken | None: Token if found, None otherwise
        """
        stmt = select(self.model).where(RefreshToken.token_hash == token_hash)
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def get_active_token(
        self, token_hash: str, current_time: datetime
    ) -> RefreshToken | None:
        """
        Get an active (non-expired, non-revoked) refresh token.

        Args:
            token_hash (str): Hash of the token to find
            current_time (datetime): Current time for validation

        Returns:
            RefreshToken | None: Active token if found, None otherwise
        """
        stmt = select(self.model).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expired_at > current_time,
            RefreshToken.revoked_at.is_(None),
        )
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def save_token(
        self,
        user_id: int,
        token_hash: str,
        expired_at: datetime,
        ip_address: str,
        user_agent: str,
    ) -> RefreshToken:
        """
        Save a new refresh token.

        Args:
            user_id (int): ID of the user
            token_hash (str): Hash of the token
            expired_at (datetime): Token expiration time
            ip_address (str): IP address of the request
            user_agent (str): User agent string

        Returns:
            RefreshToken: Created refresh token
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expired_at=expired_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.create(refresh_token)

    async def revoke_token(self, refresh_token: RefreshToken) -> None:
        """
        Revoke a refresh token.

        Args:
            refresh_token (RefreshToken): Token to revoke
        """
        refresh_token.revoked_at = datetime.now()
        await self.db.commit()
