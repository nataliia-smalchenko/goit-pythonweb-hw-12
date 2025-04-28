"""
Database session management module.

This module provides database session management functionality using SQLAlchemy's
async session features. It includes a session manager class that handles
database connections, session creation, and error handling.

The module ensures proper database connection lifecycle management and
implements error handling for database operations.
"""

import contextlib
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import config as settings

logger = logging.getLogger("uvicorn.error")
logger.info("Database URL: %s", settings.DB_URL)


class DatabaseSessionManager:
    """
    Database session manager class.

    This class manages database sessions using SQLAlchemy's async features.
    It handles engine creation, session management, and provides context
    managers for database operations.

    Attributes:
        _engine (AsyncEngine | None): SQLAlchemy async engine
        _session_maker (async_sessionmaker): Session factory
    """

    def __init__(self, url: str):
        """
        Initialize the database session manager.

        Args:
            url (str): Database connection URL
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Create and manage a database session.

        Yields:
            AsyncSession: Database session for operations

        Raises:
            Exception: If session manager is not initialized
            SQLAlchemyError: For database-related errors
            Exception: For unexpected errors
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Get a database session.

    This function is used as a FastAPI dependency to provide database sessions
    to route handlers.

    Yields:
        AsyncSession: Database session for operations
    """
    async with sessionmanager.session() as session:
        yield session
