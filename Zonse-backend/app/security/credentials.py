"""Reusable registration and credential-authentication helpers."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.identity import UserRole
from app.models.user import User
from app.security.passwords import (
    hash_password,
    password_hash_needs_rehash,
    validate_password,
    verify_password,
    verify_password_and_update,
)

_EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


class DuplicateUserError(ValueError):
    """Raised when the provided email is already registered."""


class AuthenticationError(ValueError):
    """Raised when the supplied credentials are invalid or the account is ineligible."""


def normalize_email(email: Any) -> str:
    """Normalize user email addresses for login and registration."""
    if not isinstance(email, str):
        raise ValueError("Email is required")

    normalized = email.strip().lower()
    if not normalized:
        raise ValueError("Email is required")

    if not _EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("Email is invalid")

    return normalized


def normalize_full_name(full_name: Any) -> str | None:
    if full_name is None:
        return None

    normalized = str(full_name).strip()
    return normalized or None


def normalize_phone_number(phone_number: Any) -> str | None:
    if phone_number is None:
        return None

    normalized = str(phone_number).strip()
    return normalized or None


def email_match_filter(email: str):
    return or_(
        User.email == email,
        func.lower(User.email) == email,
        User.canonical_email == email,
    )


def register_user(
    db: Session,
    *,
    email: Any,
    password: Any,
    full_name: Any = None,
    phone_number: Any = None,
) -> User:
    """Register a user with enforced normalization and safe account status defaults."""
    normalized_email = normalize_email(email)
    validate_password(password)

    existing_user = db.query(User).filter(email_match_filter(normalized_email)).first()
    if existing_user is not None:
        raise DuplicateUserError("This email is already registered")

    user = User(
        email=normalized_email,
        canonical_email=normalized_email,
        hashed_password=hash_password(password),
        full_name=normalize_full_name(full_name),
        phone_number=normalize_phone_number(phone_number),
        account_status="pending_verification",
        role="client",
        is_active=True,
    )

    try:
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role="seeker"))
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise DuplicateUserError("This email is already registered") from None

    return user


def authenticate_user(db: Session, *, email: Any, password: Any) -> User:
    """Authenticate a user by normalized email and password without leaking credentials."""
    normalized_email = normalize_email(email)

    user = db.query(User).filter(email_match_filter(normalized_email)).one_or_none()
    if user is None:
        raise AuthenticationError("Invalid credentials")

    if not user.is_active or user.account_status != "active":
        raise AuthenticationError("Account is not eligible")

    if user.email_verified_at is None:
        raise AuthenticationError("Account is not eligible")

    stored_hash = user.hashed_password
    if not verify_password(password, stored_hash):
        raise AuthenticationError("Invalid credentials")

    if password_hash_needs_rehash(stored_hash):
        verified, replacement_hash = verify_password_and_update(password, stored_hash)
        if not verified or replacement_hash is None:
            raise AuthenticationError("Invalid credentials")
        user.hashed_password = replacement_hash
        db.add(user)
        db.commit()

    return user
