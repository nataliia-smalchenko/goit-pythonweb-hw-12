"""
Email token management module.

This module provides functions for creating and validating email verification tokens.
It uses JWT (JSON Web Tokens) for secure token generation and validation.
The tokens are used for email verification and password reset operations.

The module handles token creation with expiration and validation with proper
error handling for invalid tokens.
"""

from datetime import datetime, timedelta, timezone

import jwt

# from jose import jwt
from fastapi import HTTPException, status

from src.conf.config import config as settings


def create_email_token(data: dict) -> str:
    """
    Create a JWT token for email verification.

    Args:
        data (dict): Data to encode in the token, typically containing user information

    Returns:
        str: Encoded JWT token with expiration set to 7 days from creation

    Note:
        The token includes:
        - Original data
        - Issued at time (iat)
        - Expiration time (exp)
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_email_from_token(token: str, detail: str = "Неправильний токен для перевірки електронної пошти") -> str:
    """
    Extract email from a JWT token.

    Args:
        token (str): JWT token to decode
        detail (str): Error message to display if token is invalid

    Returns:
        str: Email address extracted from the token

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload["sub"]
        return email
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )