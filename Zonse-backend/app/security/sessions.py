from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.identity import UserRole
from app.models.session import UserSession
from app.models.user import User


def digest_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user_session(
    db: Session,
    *,
    user_id: int,
    previous_token: str | None = None,
) -> tuple[str, UserSession]:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    user_session = UserSession(
        user_id=user_id,
        token_digest=digest_session_token(token),
        created_at=now,
        expires_at=now + timedelta(seconds=settings.SESSION_LIFETIME_SECONDS),
    )

    try:
        if previous_token:
            db.execute(
                update(UserSession)
                .where(
                    UserSession.token_digest == digest_session_token(previous_token),
                    UserSession.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
        db.add(user_session)
        db.commit()
        db.refresh(user_session)
    except SQLAlchemyError:
        db.rollback()
        raise

    return token, user_session


def revoke_user_session(db: Session, token: str) -> bool:
    try:
        result = db.execute(
            update(UserSession)
            .where(
                UserSession.token_digest == digest_session_token(token),
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return result.rowcount > 0


def revoke_all_user_sessions(
    db: Session,
    user_id: int,
    *,
    commit: bool = True,
) -> int:
    try:
        result = db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        if commit:
            db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return result.rowcount


def _find_current_session(db: Session, token: str) -> UserSession | None:
    now = datetime.now(timezone.utc)
    statement = (
        select(UserSession)
        .join(UserSession.user)
        .where(
            UserSession.token_digest == digest_session_token(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
            User.is_active.is_(True),
            User.account_status == "active",
            User.email_verified_at.is_not(None),
        )
    )
    return db.execute(statement).scalar_one_or_none()


def get_current_session(
    request: Request,
    db: Session = Depends(get_db),
) -> UserSession:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required",
        )

    user_session = _find_current_session(db, token)
    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required",
        )
    return user_session


def get_current_user(
    user_session: UserSession = Depends(get_current_session),
) -> User:
    return user_session.user


def get_assigned_roles(db: Session, user_id: int) -> list[str]:
    statement = (
        select(UserRole.role)
        .where(UserRole.user_id == user_id)
        .order_by(UserRole.role)
    )
    return list(db.execute(statement).scalars())
