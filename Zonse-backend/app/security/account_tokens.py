"""Digest-only email verification and password recovery token workflows."""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.action_token import UserActionToken
from app.models.user import User
from app.security.credentials import email_match_filter, normalize_email
from app.security.email_delivery import EmailMessage
from app.security.email_templates import (
    email_verification_message,
    password_recovery_message,
)
from app.security.passwords import (
    PasswordHashingError,
    hash_password,
    validate_password,
)
from app.security.sessions import revoke_all_user_sessions

EMAIL_VERIFICATION = "email_verification"
PASSWORD_RECOVERY = "password_recovery"
TOKEN_REQUEST_COOLDOWN = timedelta(seconds=60)
EMAIL_VERIFICATION_TTL = timedelta(hours=24)
PASSWORD_RECOVERY_TTL = timedelta(hours=1)


def digest_action_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def request_account_token(
    db: Session,
    *,
    email: str,
    purpose: str,
) -> EmailMessage | None:
    if purpose not in {EMAIL_VERIFICATION, PASSWORD_RECOVERY}:
        raise ValueError("Unsupported account token purpose")

    normalized_email = normalize_email(email)
    now = datetime.now(timezone.utc)
    expiry = (
        now + EMAIL_VERIFICATION_TTL
        if purpose == EMAIL_VERIFICATION
        else now + PASSWORD_RECOVERY_TTL
    )
    message_factory = (
        email_verification_message
        if purpose == EMAIL_VERIFICATION
        else password_recovery_message
    )

    try:
        user = db.execute(
            select(User)
            .where(email_match_filter(normalized_email))
            .with_for_update()
        ).scalar_one_or_none()
        if user is None or (
            purpose == EMAIL_VERIFICATION and user.email_verified_at is not None
        ):
            db.rollback()
            return None

        recent_token_id = db.execute(
            select(UserActionToken.id)
            .where(
                UserActionToken.user_id == user.id,
                UserActionToken.purpose == purpose,
                UserActionToken.consumed_at.is_(None),
                UserActionToken.expires_at > now,
                UserActionToken.created_at > now - TOKEN_REQUEST_COOLDOWN,
            )
            .limit(1)
        ).scalar_one_or_none()
        if recent_token_id is not None:
            db.rollback()
            return None

        db.execute(
            update(UserActionToken)
            .where(
                UserActionToken.user_id == user.id,
                UserActionToken.purpose == purpose,
                UserActionToken.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )

        raw_token = secrets.token_urlsafe(32)
        db.add(
            UserActionToken(
                user_id=user.id,
                purpose=purpose,
                token_digest=digest_action_token(raw_token),
                created_at=now,
                expires_at=expiry,
            )
        )
        db.flush()
        message = message_factory(user.email, raw_token)
        db.commit()
        return message
    except SQLAlchemyError:
        db.rollback()
        raise


def confirm_email_verification(db: Session, token: str) -> bool:
    now = datetime.now(timezone.utc)
    try:
        action_token = db.execute(
            select(UserActionToken)
            .where(
                UserActionToken.token_digest == digest_action_token(token),
                UserActionToken.purpose == EMAIL_VERIFICATION,
                UserActionToken.consumed_at.is_(None),
                UserActionToken.expires_at > now,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if action_token is None:
            db.rollback()
            return False

        user = db.execute(
            select(User)
            .where(User.id == action_token.user_id)
            .with_for_update()
        ).scalar_one_or_none()
        if user is None:
            db.rollback()
            return False

        consumed = db.execute(
            update(UserActionToken)
            .where(
                UserActionToken.id == action_token.id,
                UserActionToken.consumed_at.is_(None),
                UserActionToken.expires_at > now,
            )
            .values(consumed_at=now)
            .execution_options(synchronize_session=False)
        )
        if consumed.rowcount != 1:
            db.rollback()
            return False

        if user.email_verified_at is None:
            user.email_verified_at = now
            if user.account_status == "pending_verification" and user.is_active:
                user.account_status = "active"

        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise


def recover_account_password(
    db: Session,
    *,
    token: str,
    new_password: str,
) -> bool:
    validate_password(new_password)
    now = datetime.now(timezone.utc)
    try:
        action_token = db.execute(
            select(UserActionToken)
            .where(
                UserActionToken.token_digest == digest_action_token(token),
                UserActionToken.purpose == PASSWORD_RECOVERY,
                UserActionToken.consumed_at.is_(None),
                UserActionToken.expires_at > now,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if action_token is None:
            db.rollback()
            return False

        user = db.execute(
            select(User)
            .where(User.id == action_token.user_id)
            .with_for_update()
        ).scalar_one_or_none()
        if user is None:
            db.rollback()
            return False

        replacement_hash = hash_password(new_password)
        consumed = db.execute(
            update(UserActionToken)
            .where(
                UserActionToken.id == action_token.id,
                UserActionToken.consumed_at.is_(None),
                UserActionToken.expires_at > now,
            )
            .values(consumed_at=now)
            .execution_options(synchronize_session=False)
        )
        if consumed.rowcount != 1:
            db.rollback()
            return False

        user.hashed_password = replacement_hash
        db.execute(
            update(UserActionToken)
            .where(
                UserActionToken.user_id == user.id,
                UserActionToken.purpose == PASSWORD_RECOVERY,
                UserActionToken.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        revoke_all_user_sessions(db, user.id, commit=False)
        db.commit()
        return True
    except (PasswordHashingError, SQLAlchemyError):
        db.rollback()
        raise
