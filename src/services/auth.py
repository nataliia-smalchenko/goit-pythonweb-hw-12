"""
Authentication service for user management and token handling.

This module provides authentication and authorization functionality including:
- User registration and verification
- Password hashing and verification
- JWT token generation and validation
- Refresh token management
- Token revocation
- User session management

The service implements secure authentication mechanisms using bcrypt for password
hashing and JWT for token management.
"""

from datetime import datetime, timedelta, UTC, timezone
import secrets

import jwt

# from jose import jwt
import bcrypt
import hashlib
import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.conf.config import config as settings
from src.entity.models import User
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.users import UserRepository
from src.schemas.user import UserCreate


redis_client = redis.from_url(settings.REDIS_URL)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    """
    Service class for handling authentication and authorization.

    This class provides methods for user authentication, token management,
    and security operations. It uses repositories for data access and
    implements secure password hashing and token generation.

    Attributes:
        db (AsyncSession): Database session for operations
        user_repository (UserRepository): Repository for user operations
        refresh_token_repository (RefreshTokenRepository): Repository for token operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the AuthService.

        Args:
            db (AsyncSession): Database session for operations
        """
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.refresh_token_repository = RefreshTokenRepository(self.db)

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password (str): Plain text password to hash

        Returns:
            str: Hashed password
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        return hashed_password.decode()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password (str): Password to verify
            hashed_password (str): Hashed password to check against

        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    def _hash_token(self, token: str) -> str:
        """
        Hash a token using SHA-256.

        Args:
            token (str): Token to hash

        Returns:
            str: Hashed token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def authenticate(self, username: str, password: str) -> User:
        """
        Authenticate a user with username and password.

        Args:
            username (str): Username to authenticate
            password (str): Password to verify

        Returns:
            User: Authenticated user

        Raises:
            HTTPException: If authentication fails or user is not verified
        """
        user = await self.user_repository.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Електронна адреса не підтверджена",
            )

        if not self._verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        return user

    async def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.

        Args:
            user_data (UserCreate): User registration data

        Returns:
            User: Newly created user

        Raises:
            HTTPException: If username or email already exists
        """
        if await self.user_repository.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already exists"
            )
        if await self.user_repository.get_by_email(str(user_data.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )
        avatar = None
        try:
            g = Gravatar(user_data.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        hashed_password = self._hash_password(user_data.password)
        user = await self.user_repository.create_user(
            user_data, hashed_password, avatar
        )
        return user

    def create_access_token(self, username: str) -> str:
        """
        Create a new JWT access token.

        Args:
            username (str): Username to include in token

        Returns:
            str: JWT access token
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {"sub": username, "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    async def create_refresh_token(
        self, user_id: int, ip_address: str | None, user_agent: str | None
    ) -> str:
        """
        Create a new refresh token.

        Args:
            user_id (int): ID of the user
            ip_address (str | None): IP address of the request
            user_agent (str | None): User agent string

        Returns:
            str: New refresh token
        """
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        expired_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.refresh_token_repository.save_token(
            user_id, token_hash, expired_at, ip_address, user_agent
        )
        return token

    def decode_and_validate_access_token(self, token: str) -> dict:
        """
        Decode and validate a JWT access token.

        Args:
            token (str): JWT token to validate

        Returns:
            dict: Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token wrong"
            )

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """
        Get the current authenticated user from token.

        Args:
            token (str): JWT access token

        Returns:
            User: Current authenticated user

        Raises:
            HTTPException: If token is invalid or user not found
        """
        payload = self.decode_and_validate_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user = await self.user_repository.get_by_username(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return user

    async def validate_refresh_token(self, token: str) -> User:
        """
        Validate a refresh token and return the associated user.

        Args:
            token (str): Refresh token to validate

        Returns:
            User: User associated with the token

        Raises:
            HTTPException: If token is invalid or expired
        """
        token_hash = self._hash_token(token)
        current_time = datetime.now(timezone.utc)
        refresh_token = await self.refresh_token_repository.get_active_token(
            token_hash, current_time
        )
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user = await self.user_repository.get_by_id(refresh_token.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

    async def revoke_refresh_token(self, token: str) -> None:
        """
        Revoke a refresh token.

        Args:
            token (str): Refresh token to revoke

        Raises:
            HTTPException: If token is invalid
        """
        token_hash = self._hash_token(token)
        refresh_token = await self.refresh_token_repository.get_by_token_hash(token_hash)
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        await self.refresh_token_repository.revoke_token(refresh_token)

    async def revoke_access_token(self, token: str) -> None:
        """
        Revoke an access token by adding it to the blacklist.

        Args:
            token (str): Access token to revoke
        """
        await redis_client.setex(
            f"blacklist:{token}",
            settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "revoked",
        )
