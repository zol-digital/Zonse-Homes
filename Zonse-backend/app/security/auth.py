"""Compatibility wrapper for credential registration and authentication helpers."""

from app.security.credentials import (
    AuthenticationError,
    DuplicateUserError,
    authenticate_user,
    normalize_email,
    normalize_full_name,
    normalize_phone_number,
    register_user,
)

__all__ = [
    "AuthenticationError",
    "DuplicateUserError",
    "authenticate_user",
    "normalize_email",
    "normalize_full_name",
    "normalize_phone_number",
    "register_user",
]
