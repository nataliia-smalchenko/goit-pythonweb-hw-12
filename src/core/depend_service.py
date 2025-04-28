"""
Dependency injection services for FastAPI application.

This module provides dependency injection functions for various services
used throughout the application, including authentication, user management,
and Redis client management. It also includes role-based access control
dependencies for moderators and administrators.

The module ensures proper service initialization and error handling
for external dependencies like Redis.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from fastapi import status

from src.database.db import get_db
from src.entity.models import User, UserRole
from src.services.auth import AuthService, oauth2_scheme
from src.services.user import UserService
from src.conf.config import config


def get_auth_service(db: AsyncSession = Depends(get_db)):
    """
    Get authentication service instance.

    Args:
        db (AsyncSession): Database session dependency.

    Returns:
        AuthService: Authentication service instance.
    """
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)):
    """
    Get user service instance.

    Args:
        db (AsyncSession): Database session dependency.

    Returns:
        UserService: User service instance.
    """
    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Get current authenticated user.

    Args:
        token (str): JWT token from request.
        auth_service (AuthService): Authentication service instance.

    Returns:
        User: Current authenticated user.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    return await auth_service.get_current_user(token)


# Залежності для перевірки ролей
def get_current_moderator_user(current_user: User = Depends(get_current_user)):
    """
    Get current user with moderator or admin role.

    Args:
        current_user (User): Current authenticated user.

    Returns:
        User: Current user with moderator or admin role.

    Raises:
        HTTPException: If user doesn't have required role.
    """
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Недостатньо прав доступу")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Get current user with admin role.

    Args:
        current_user (User): Current authenticated user.

    Returns:
        User: Current user with admin role.

    Raises:
        HTTPException: If user doesn't have admin role.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостатньо прав доступу")
    return current_user


async def get_redis_client() -> Redis:
    """
    Get Redis client as a FastAPI dependency with improved error handling.

    Returns:
        Redis: Redis client instance.
    
    Raises:
        HTTPException: If Redis connection fails
    """
    try:
        redis = Redis.from_url(config.REDIS_URL, encoding="utf-8", decode_responses=True)
        # Test the connection
        await redis.ping()
        yield redis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection error: {str(e)}"
        )
    finally:
        if 'redis' in locals():
            await redis.close()


async def get_redis(
    redis_client: Redis = Depends(get_redis_client),
) -> Redis:
    """
    Get Redis client as a FastAPI dependency with connection validation.

    Args:
        redis_client: Redis client instance from dependency injection.

    Returns:
        Redis: Redis client instance.
    
    Raises:
        HTTPException: If Redis connection is not available
    """
    try:
        # Verify the connection is still alive
        await redis_client.ping()
        return redis_client
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection error: {str(e)}"
        )
