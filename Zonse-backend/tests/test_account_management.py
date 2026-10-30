from datetime import datetime, timedelta, timezone
import hashlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.config import settings
from app.database import Base, get_db
from app.exception_handlers import register_exception_handlers
from app.models.action_token import UserActionToken
from app.models.session import UserSession
from app.models.user import User
from app.security.account_tokens import (
    EMAIL_VERIFICATION,
    PASSWORD_RECOVERY,
    digest_action_token,
)
from app.security.credentials import AuthenticationError, authenticate_user
from app.security.email_delivery import (
    MemoryEmailDelivery,
    UnconfiguredEmailDelivery,
    get_email_delivery,
)
from app.security.passwords import hash_password
from app.security.sessions import create_user_session

_COOKIE_NAME = "zonse_session"
_OLD_PASSWORD = "correct horse battery staple"
_NEW_PASSWORD = "a different correct horse battery"


@pytest.fixture
def account_environment(monkeypatch):
    monkeypatch.setattr(settings, "SESSION_COOKIE_NAME", _COOKIE_NAME)
    monkeypatch.setattr(settings, "SESSION_LIFETIME_SECONDS", 86400)
    monkeypatch.setattr(settings, "SESSION_COOKIE_SAMESITE", "lax")
    monkeypatch.setattr(settings, "SESSION_COOKIE_SECURE", False)
    monkeypatch.setattr(settings, "SESSION_CSRF_TRUSTED_ORIGINS", ())

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    delivery = MemoryEmailDelivery()
    test_app = FastAPI()
    register_exception_handlers(test_app)
    test_app.include_router(auth_router, prefix="/api/v1")
    test_app.include_router(users_router, prefix="/api/v1")

    def override_get_db():
        with session_factory() as db:
            yield db

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_email_delivery] = lambda: delivery
    with TestClient(test_app) as client:
        yield client, session_factory, delivery, test_app

    test_app.dependency_overrides.clear()
    engine.dispose()


def _create_user(
    session_factory,
    *,
    email="member@example.test",
    account_status="active",
    verified=True,
    is_active=True,
    phone_number="+265991000001",
):
    with session_factory() as db:
        user = User(
            email=email,
            canonical_email=email,
            hashed_password=hash_password(_OLD_PASSWORD),
            full_name="Original Name",
            phone_number=phone_number,
            phone_verified_at=(
                datetime.now(timezone.utc) if phone_number else None
            ),
            account_status=account_status,
            email_verified_at=(
                datetime.now(timezone.utc) if verified else None
            ),
            is_active=is_active,
            role="client",
        )
        db.add(user)
        db.commit()
        return user.id


def _message_token(delivery: MemoryEmailDelivery, index: int = -1) -> str:
    body = delivery.messages[index].body
    return body.split(" is ", 1)[1].split(".", 1)[0]


def _request_action(client, path: str, email: str) -> dict:
    response = client.post(path, json={"email": email})
    assert response.status_code == 202
    return response.json()


def _stored_token(session_factory, purpose: str) -> UserActionToken:
    with session_factory() as db:
        return db.execute(
            select(UserActionToken).where(UserActionToken.purpose == purpose)
        ).scalar_one()


def test_profile_requires_authentication_and_returns_only_safe_private_fields(
    account_environment,
):
    client, session_factory, _, _ = account_environment
    user_id = _create_user(session_factory)

    assert client.get("/api/v1/users/me").status_code == 401
    assert (
        client.patch("/api/v1/users/me", json={"full_name": "Updated"}).status_code
        == 401
    )

    token, _ = _create_session(session_factory, user_id)
    client.cookies.set(_COOKIE_NAME, token)
    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == user_id
    assert payload["email"] == "member@example.test"
    assert payload["phone_number"] == "+265991000001"
    assert payload["full_name"] == "Original Name"
    assert "hashed_password" not in payload
    assert "role" not in payload
    assert "assigned_roles" not in payload
    assert "verification_documents" not in payload
    assert client.get(f"/api/v1/users/{user_id}").status_code == 404


def _create_session(session_factory, user_id: int) -> tuple[str, str]:
    with session_factory() as db:
        token, user_session = create_user_session(db, user_id=user_id)
        return token, user_session.token_digest


def test_profile_update_normalizes_fields_and_clears_phone_verification(
    account_environment,
):
    client, session_factory, _, _ = account_environment
    user_id = _create_user(session_factory)
    token, _ = _create_session(session_factory, user_id)
    client.cookies.set(_COOKIE_NAME, token)
    client.headers.update({"Origin": "http://testserver"})

    response = client.patch(
        "/api/v1/users/me",
        json={"full_name": "  Jane Doe  ", "phone_number": " +265 888 111 222 "},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Jane Doe"
    assert response.json()["phone_number"] == "+265 888 111 222"
    assert response.json()["phone_verified_at"] is None

    with session_factory() as db:
        user = db.get(User, user_id)
        assert user.full_name == "Jane Doe"
        assert user.phone_number == "+265 888 111 222"
        assert user.phone_verified_at is None


@pytest.mark.parametrize(
    "forbidden_field,value",
    [
        ("role", "admin"),
        ("roles", ["admin"]),
        ("assigned_roles", [{"role": "admin"}]),
        ("account_status", "active"),
        ("is_active", False),
        ("email_verified_at", "2026-01-01T00:00:00Z"),
        ("phone_verified_at", "2026-01-01T00:00:00Z"),
        ("hashed_password", "attacker-controlled"),
        ("email", "attacker@example.test"),
    ],
)
def test_profile_update_rejects_privileged_and_identity_fields(
    account_environment,
    forbidden_field,
    value,
):
    client, session_factory, _, _ = account_environment
    user_id = _create_user(session_factory)
    token, _ = _create_session(session_factory, user_id)
    client.cookies.set(_COOKIE_NAME, token)
    client.headers.update({"Origin": "http://testserver"})
    with session_factory() as db:
        original_hash = db.get(User, user_id).hashed_password

    response = client.patch(
        "/api/v1/users/me",
        json={forbidden_field: value},
    )

    assert response.status_code == 422
    with session_factory() as db:
        user = db.get(User, user_id)
        assert user.role == "client"
        assert user.account_status == "active"
        assert user.email_verified_at is not None
        assert user.hashed_password == original_hash
        assert user.email == "member@example.test"


def test_profile_update_rejects_invalid_lengths_and_can_clear_phone(
    account_environment,
):
    client, session_factory, _, _ = account_environment
    user_id = _create_user(session_factory)
    token, _ = _create_session(session_factory, user_id)
    client.cookies.set(_COOKIE_NAME, token)
    client.headers.update({"Origin": "http://testserver"})

    invalid = client.patch(
        "/api/v1/users/me",
        json={"phone_number": "x" * 33},
    )
    assert invalid.status_code == 422

    cleared = client.patch("/api/v1/users/me", json={"phone_number": None})
    assert cleared.status_code == 200
    assert cleared.json()["phone_number"] is None
    assert cleared.json()["phone_verified_at"] is None


def test_email_verification_request_is_generic_digest_only_and_rate_limited(
    account_environment,
):
    client, session_factory, delivery, _ = account_environment
    user_id = _create_user(
        session_factory,
        email="pending@example.test",
        account_status="pending_verification",
        verified=False,
    )

    known = _request_action(
        client,
        "/api/v1/auth/email-verification/request",
        " PENDING@example.test ",
    )
    unknown = _request_action(
        client,
        "/api/v1/auth/email-verification/request",
        "missing@example.test",
    )
    assert known == unknown
    assert len(delivery.messages) == 1
    raw_token = _message_token(delivery)
    assert raw_token not in known.values()
    assert raw_token not in client.post(
        "/api/v1/auth/email-verification/request",
        json={"email": "pending@example.test"},
    ).text

    stored = _stored_token(session_factory, EMAIL_VERIFICATION)
    assert stored.user_id == user_id
    assert stored.token_digest == digest_action_token(raw_token)
    assert stored.token_digest != raw_token
    assert len(stored.token_digest) == 64
    assert len(delivery.messages) == 1


def test_email_request_matches_legacy_mixed_case_email_values(account_environment):
    client, session_factory, delivery, _ = account_environment
    user_id = _create_user(
        session_factory,
        email="legacy.user@example.test",
        account_status="pending_verification",
        verified=False,
    )
    with session_factory() as db:
        user = db.get(User, user_id)
        user.email = "Legacy.User@Example.test"
        user.canonical_email = None
        db.commit()

    _request_action(
        client,
        "/api/v1/auth/email-verification/request",
        " legacy.user@example.test ",
    )

    assert len(delivery.messages) == 1
    assert delivery.messages[0].recipient == "Legacy.User@Example.test"
    stored = _stored_token(session_factory, EMAIL_VERIFICATION)
    assert stored.user_id == user_id


def test_email_verification_activates_pending_account_and_is_single_use(
    account_environment,
):
    client, session_factory, delivery, _ = account_environment
    user_id = _create_user(
        session_factory,
        email="pending@example.test",
        account_status="pending_verification",
        verified=False,
    )
    _request_action(
        client,
        "/api/v1/auth/email-verification/request",
        "pending@example.test",
    )
    token = _message_token(delivery)

    response = client.post(
        "/api/v1/auth/email-verification/confirm",
        json={"token": token},
    )
    assert response.status_code == 200
    assert token not in response.text

    with session_factory() as db:
        user = db.get(User, user_id)
        action_token = db.execute(
            select(UserActionToken).where(
                UserActionToken.purpose == EMAIL_VERIFICATION
            )
        ).scalar_one()
        assert user.email_verified_at is not None
        assert user.account_status == "active"
        assert action_token.consumed_at is not None

    replay = client.post(
        "/api/v1/auth/email-verification/confirm",
        json={"token": token},
    )
    assert replay.status_code == 400


@pytest.mark.parametrize(
    ("account_status", "is_active"),
    [("suspended", True), ("disabled", False)],
)
def test_email_verification_never_reactivates_suspended_or_disabled_accounts(
    account_environment,
    account_status,
    is_active,
):
    client, session_factory, delivery, _ = account_environment
    user_id = _create_user(
        session_factory,
        email=f"{account_status}@example.test",
        account_status=account_status,
        verified=False,
        is_active=is_active,
    )
    _request_action(
        client,
        "/api/v1/auth/email-verification/request",
        f"{account_status}@example.test",
    )

    response = client.post(
        "/api/v1/auth/email-verification/confirm",
        json={"token": _message_token(delivery)},
    )

    assert response.status_code == 200
    with session_factory() as db:
        user = db.get(User, user_id)
        assert user.email_verified_at is not None
        assert user.account_status == account_status
        assert user.is_active is is_active


def test_email_verification_rejects_invalid_expired_and_wrong_purpose_tokens(
    account_environment,
):
    client, session_factory, delivery, _ = account_environment
    user_id = _create_user(
        session_factory,
        email="pending@example.test",
        account_status="pending_verification",
        verified=False,
    )
    _request_action(
        client,
        "/api/v1/auth/email-verification/request",
        "pending@example.test",
    )
    email_token = _message_token(delivery)

    assert (
        client.post(
            "/api/v1/auth/email-verification/confirm",
            json={"token": "invalid-token"},
        ).status_code
        == 400
    )
    with session_factory() as db:
        action_token = db.execute(
            select(UserActionToken).where(
                UserActionToken.token_digest == digest_action_token(email_token)
            )
        ).scalar_one()
        action_token.created_at = datetime.now(timezone.utc) - timedelta(days=2)
        action_token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
    assert (
        client.post(
            "/api/v1/auth/email-verification/confirm",
            json={"token": email_token},
        ).status_code
        == 400
    )

    _request_action(
        client,
        "/api/v1/auth/password-recovery/request",
        "pending@example.test",
    )
    recovery_token = _message_token(delivery)
    assert (
        client.post(
            "/api/v1/auth/email-verification/confirm",
            json={"token": recovery_token},
        ).status_code
        == 400
    )
    with session_factory() as db:
        user = db.get(User, user_id)
        recovery_record = db.execute(
            select(UserActionToken).where(
                UserActionToken.token_digest == digest_action_token(recovery_token)
            )
        ).scalar_one()
        assert user.email_verified_at is None
        assert recovery_record.consumed_at is None


def test_unconfigured_email_delivery_is_uniformly_unavailable_and_creates_no_tokens(
    account_environment,
):
    client, session_factory, _, test_app = account_environment
    user_id = _create_user(
        session_factory,
        email="pending@example.test",
        account_status="pending_verification",
        verified=False,
    )
    test_app.dependency_overrides[get_email_delivery] = UnconfiguredEmailDelivery

    verification_responses = [
        client.post(
            "/api/v1/auth/email-verification/request",
            json={"email": email},
        )
        for email in ("pending@example.test", "missing@example.test")
    ]
    recovery_responses = [
        client.post(
            "/api/v1/auth/password-recovery/request",
            json={"email": email},
        )
        for email in ("pending@example.test", "missing@example.test")
    ]

    assert [response.status_code for response in verification_responses] == [503, 503]
    assert [response.json() for response in verification_responses][0] == (
        verification_responses[1].json()
    )
    assert [response.status_code for response in recovery_responses] == [503, 503]
    assert recovery_responses[0].json() == recovery_responses[1].json()
    with session_factory() as db:
        assert db.query(UserActionToken).filter_by(user_id=user_id).count() == 0


def test_memory_email_delivery_cannot_be_enabled_in_production(
    account_environment,
    monkeypatch,
):
    _, _, _, test_app = account_environment
    test_app.dependency_overrides.pop(get_email_delivery, None)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    with pytest.raises(RuntimeError, match="unavailable in production"):
        MemoryEmailDelivery()


def test_password_recovery_is_generic_digest_only_and_rate_limited(
    account_environment,
):
    client, session_factory, delivery, _ = account_environment
    user_id = _create_user(session_factory)

    known = _request_action(
        client,
        "/api/v1/auth/password-recovery/request",
        " MEMBER@example.test ",
    )
    unknown = _request_action(
        client,
        "/api/v1/auth/password-recovery/request",
        "missing@example.test",
    )
    assert known == unknown
    assert len(delivery.messages) == 1
    raw_token = _message_token(delivery)

    stored = _stored_token(session_factory, PASSWORD_RECOVERY)
    assert stored.user_id == user_id
    assert stored.token_digest == digest_action_token(raw_token)
    assert raw_token not in known.values()
    assert raw_token not in client.post(
        "/api/v1/auth/password-recovery/request",
        json={"email": "member@example.test"},
    ).text
    assert len(delivery.messages) == 1

    with session_factory() as db:
        stored = db.execute(
            select(UserActionToken).where(
                UserActionToken.purpose == PASSWORD_RECOVERY
            )
        ).scalar_one()
        stored.created_at = datetime.now(timezone.utc) - timedelta(minutes=2)
        db.commit()

    _request_action(
        client,
        "/api/v1/auth/password-recovery/request",
        "member@example.test",
    )
    replacement_token = _message_token(delivery)
    assert replacement_token != raw_token
    assert len(delivery.messages) == 2
    with session_factory() as db:
        tokens = db.execute(
            select(UserActionToken)
            .where(UserActionToken.purpose == PASSWORD_RECOVERY)
            .order_by(UserActionToken.created_at)
        ).scalars().all()
        assert len(tokens) == 2
        assert tokens[0].consumed_at is not None
        assert tokens[1].consumed_at is None


def test_password_recovery_changes_hash_and_revokes_every_session(
    account_environment,
):
    client, session_factory, delivery, _ = account_environment
    user_id = _create_user(session_factory)
    with session_factory() as db:
        original_hash = db.get(User, user_id).hashed_password
    original_token, _ = _create_session(session_factory, user_id)
    another_token, _ = _create_session(session_factory, user_id)
    client.cookies.set(_COOKIE_NAME, original_token)
    client.headers.update({"Origin": "http://testserver"})

    _request_action(
        client,
        "/api/v1/auth/password-recovery/request",
        "member@example.test",
    )
    recovery_token = _message_token(delivery)
    response = client.post(
        "/api/v1/auth/password-recovery/confirm",
        json={"token": recovery_token, "new_password": _NEW_PASSWORD},
    )

    assert response.status_code == 200
    assert recovery_token not in response.text
    assert "set-cookie" not in response.headers
    assert client.get("/api/v1/auth/me").status_code == 401

    with session_factory() as db:
        user = db.get(User, user_id)
        sessions = db.execute(
            select(UserSession).where(UserSession.user_id == user_id)
        ).scalars().all()
        action_token = db.execute(
            select(UserActionToken).where(
                UserActionToken.purpose == PASSWORD_RECOVERY
            )
        ).scalar_one()
        assert user.hashed_password != original_hash
        assert user.hashed_password.startswith("$argon2id$")
        assert {session.token_digest for session in sessions} == {
            hashlib.sha256(original_token.encode()).hexdigest(),
            hashlib.sha256(another_token.encode()).hexdigest(),
        }
        assert all(session.revoked_at is not None for session in sessions)
        assert action_token.consumed_at is not None

    with session_factory() as db:
        with pytest.raises(AuthenticationError):
            authenticate_user(
                db,
                email="member@example.test",
                password=_OLD_PASSWORD,
            )
        assert (
            authenticate_user(
                db,
                email="member@example.test",
                password=_NEW_PASSWORD,
            ).id
            == user_id
        )

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "member@example.test", "password": _NEW_PASSWORD},
    )
    assert login_response.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200


def test_password_recovery_rejects_invalid_expired_reused_and_weak_passwords(
    account_environment,
):
    client, session_factory, delivery, _ = account_environment
    _create_user(session_factory)
    _request_action(
        client,
        "/api/v1/auth/password-recovery/request",
        "member@example.test",
    )
    recovery_token = _message_token(delivery)

    invalid = client.post(
        "/api/v1/auth/password-recovery/confirm",
        json={"token": "not-a-token", "new_password": _NEW_PASSWORD},
    )
    weak = client.post(
        "/api/v1/auth/password-recovery/confirm",
        json={"token": recovery_token, "new_password": "short"},
    )
    assert invalid.status_code == 400
    assert weak.status_code == 422
    assert (
        client.post(
            "/api/v1/auth/password-recovery/confirm",
            json={"token": recovery_token, "new_password": _NEW_PASSWORD},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/password-recovery/confirm",
            json={"token": recovery_token, "new_password": _NEW_PASSWORD},
        ).status_code
        == 400
    )

    _request_action(
        client,
        "/api/v1/auth/password-recovery/request",
        "member@example.test",
    )
    expired_token = _message_token(delivery)
    with session_factory() as db:
        action_token = db.execute(
            select(UserActionToken).where(
                UserActionToken.token_digest == digest_action_token(expired_token)
            )
        ).scalar_one()
        action_token.created_at = datetime.now(timezone.utc) - timedelta(days=2)
        action_token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
    assert (
        client.post(
            "/api/v1/auth/password-recovery/confirm",
            json={"token": expired_token, "new_password": _NEW_PASSWORD},
        ).status_code
        == 400
    )
