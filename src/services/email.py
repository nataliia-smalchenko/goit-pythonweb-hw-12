"""
Email service for sending verification and password reset emails.

This module provides functionality for sending emails using FastAPI-Mail.
It includes templates for email verification and password reset operations.

The service handles email configuration and template rendering for
various email types.
"""

from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import config as settings
from src.core.email_token import create_email_token

# Email service configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str) -> None:
    """
    Send an email verification message.

    This function sends an email with a verification token to confirm
    the user's email address.

    Args:
        email (EmailStr): Recipient's email address
        username (str): Recipient's username
        host (str): Host URL for verification link

    Note:
        Uses the verify_email.html template for the email body.
    """
    try:
        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)


async def send_reset_password_email(email: EmailStr, username: str, host: str) -> None:
    """
    Send a password reset email.

    This function sends an email with a password reset token to allow
    the user to reset their password.

    Args:
        email (EmailStr): Recipient's email address
        username (str): Recipient's username
        host (str): Host URL for password reset link

    Note:
        Uses the reset_password_email.html template for the email body.
    """
    try:
        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Account Recovery",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password_email.html")
    except ConnectionErrors as err:
        print(err)
