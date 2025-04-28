"""
Token schema definitions.

This module defines Pydantic models for token-related data validation and serialization.
It includes schemas for access tokens, refresh tokens, and token requests.

The schemas implement proper validation rules for token data handling.
"""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """
    Schema for token response data.

    This schema defines the structure of the authentication token response.
    It includes both access and refresh tokens with their type information.

    Attributes:
        access_token (str): JWT access token
        token_type (str): Token type (default: "bearer")
        refresh_token (str): JWT refresh token
    """
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """
    Schema for refresh token request.

    This schema defines the structure for requesting a new access token
    using a refresh token.

    Attributes:
        refresh_token (str): Valid refresh token
    """
    refresh_token: str


# class PasswordResetToken(BaseModel):
#     """
#     Schema for password reset token.
#
#     This schema defines the structure for password reset token validation.
#
#     Attributes:
#         token (str): Password reset token
#     """
#     token: str
#
#
# class NewPassword(BaseModel):
#     """
#     Schema for new password submission.
#
#     This schema defines the structure for submitting a new password
#     with confirmation.
#
#     Attributes:
#         password (str): New password
#         confirm_password (str): Password confirmation
#     """
#     password: str
#     confirm_password: str
