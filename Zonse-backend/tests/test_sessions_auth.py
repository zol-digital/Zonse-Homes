from datetime import datetime, timedelta, timezone

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.v1.endpoints.auth import router as auth_router
from app.config import settings
from app.database import Base, get_db
from app.exception_handlers import register_exception_handlers
from app.models.identity import UserRole
from app.models.property import Property
from app.models.session import UserSession
from app.models.user import User
from app.security.authorization import require_property_owner, require_roles
from app.security.passwords import hash_password
from app.security.sessions import (
    create_user_session,
    digest_session_token,
    revoke_all_user_sessions,
)

_PASSWORD = "correct horse battery staple"
_COOKIE_NAME = "zonse_session"


@pytest.fixture
def auth_environment(monkeypatch):
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
    assert app.models.PropertyImage.__table__ in Base.metadata.tables.values()
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    test_app = FastAPI()
    register_exception_handlers(test_app)
    test_app.include_router(auth_router, prefix="/api/v1")

    protected_router = APIRouter()

    @protected_router.get("/test/roles/owner")
    def owner_route(user: User = Depends(require_roles("owner"))):
        return {"user_id": user.id}

    @protected_router.get("/test/roles/admin")
    def admin_route(user: User = Depends(require_roles("admin"))):
        return {"user_id": user.id}

    @protected_router.get("/test/roles/owner-or-agent")
    def owner_or_agent_route(user: User = Depends(require_roles("owner", "agent"))):
        return {"user_id": user.id}

    @protected_router.get("/test/properties/{property_id}")
    def property_route(
        property_record: Property = Depends(require_property_owner),
    ):
        return {"owner_id": property_record.owner_id}

    test_app.include_router(protected_router, prefix="/api/v1")

    def override_get_db():
        with session_factory() as db:
            yield db

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as client:
        yield client, session_factory

    test_app.dependency_overrides.clear()
    engine.dispose()


def _create_user(
    session_factory,
    *,
    email="member@example.test",
    roles=("seeker",),
    legacy_role="client",
    account_status="active",
    is_active=True,
    verified=True,
):
    password_hash = (
        hash_password(_PASSWORD) if account_status == "active" else "not-used"
    )
    with session_factory() as db:
        user = User(
            email=email,
            canonical_email=email,
            hashed_password=password_hash,
            account_status=account_status,
            is_active=is_active,
            email_verified_at=datetime.now(timezone.utc) if verified else None,
            role=legacy_role,
        )
        db.add(user)
        db.flush()
        db.add_all(UserRole(user_id=user.id, role=role) for role in roles)
        db.commit()
        return user.id


def _issue_cookie(client, session_factory, user_id):
    with session_factory() as db:
        token, _ = create_user_session(db, user_id=user_id)
    client.cookies.set(_COOKIE_NAME, token)
    return token


def test_login_persists_only_digest_sets_protected_cookie_and_authenticates_me(
    auth_environment,
):
    client, session_factory = auth_environment
    user_id = _create_user(
        session_factory,
        email="active@example.test",
        roles=("seeker", "owner"),
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ACTIVE@example.test", "password": _PASSWORD},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "active@example.test"
    assert payload["roles"] == ["owner", "seeker"]
    assert "hashed_password" not in payload
    assert "token_digest" not in payload
    token = client.cookies.get(_COOKIE_NAME)
    assert token
    assert token not in response.text

    cookie_header = response.headers["set-cookie"].lower()
    assert "httponly" in cookie_header
    assert "secure" not in cookie_header
    assert "samesite=lax" in cookie_header
    assert "path=/" in cookie_header

    with session_factory() as db:
        user_session = db.execute(
            select(UserSession).where(UserSession.user_id == user_id)
        ).scalar_one()
        assert user_session.token_digest == digest_session_token(token)
        assert user_session.token_digest != token
        assert len(user_session.token_digest) == 64

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["id"] == user_id
    assert me_response.json()["roles"] == ["owner", "seeker"]


def test_login_errors_are_generic_and_never_create_sessions(auth_environment):
    client, session_factory = auth_environment
    _create_user(session_factory, email="known@example.test")
    _create_user(
        session_factory,
        email="pending@example.test",
        account_status="pending_verification",
        verified=False,
    )
    _create_user(
        session_factory,
        email="suspended@example.test",
        account_status="suspended",
    )
    _create_user(
        session_factory,
        email="disabled@example.test",
        account_status="disabled",
    )
    _create_user(
        session_factory,
        email="inactive@example.test",
        is_active=False,
    )

    responses = [
        client.post(
            "/api/v1/auth/login",
            json={"email": "known@example.test", "password": "incorrect password"},
        ),
        client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.test", "password": _PASSWORD},
        ),
        *[
            client.post(
                "/api/v1/auth/login",
                json={"email": f"{status_name}@example.test", "password": _PASSWORD},
            )
            for status_name in (
                "pending",
                "suspended",
                "disabled",
                "inactive",
            )
        ],
    ]

    assert {response.status_code for response in responses} == {401}
    assert all(response.json() == responses[0].json() for response in responses)
    with session_factory() as db:
        assert db.query(UserSession).count() == 0


def test_secure_cookie_is_emitted_when_configured(auth_environment, monkeypatch):
    client, session_factory = auth_environment
    monkeypatch.setattr(settings, "SESSION_COOKIE_SECURE", True)
    _create_user(session_factory)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "member@example.test", "password": _PASSWORD},
        headers={"Origin": "http://testserver"},
    )

    assert response.status_code == 200
    assert "secure" in response.headers["set-cookie"].lower()


def test_session_tokens_have_high_entropy_and_only_digests_are_stored(
    auth_environment,
):
    _, session_factory = auth_environment
    user_id = _create_user(session_factory)

    with session_factory() as db:
        first_token, _ = create_user_session(db, user_id=user_id)
        second_token, _ = create_user_session(db, user_id=user_id)
        stored_digests = list(
            db.execute(select(UserSession.token_digest)).scalars()
        )

    assert first_token != second_token
    assert len(first_token) >= 43
    assert len(second_token) >= 43
    assert digest_session_token(first_token) in stored_digests
    assert digest_session_token(second_token) in stored_digests
    assert first_token not in stored_digests
    assert second_token not in stored_digests


def test_missing_malformed_expired_revoked_and_disabled_sessions_fail_closed(
    auth_environment,
):
    client, session_factory = auth_environment
    user_id = _create_user(session_factory)

    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set(_COOKIE_NAME, "malformed-or-unknown-token")
    assert client.get("/api/v1/auth/me").status_code == 401

    expired_token = _issue_cookie(client, session_factory, user_id)
    expired_at = datetime.now(timezone.utc)
    with session_factory() as db:
        db.execute(
            update(UserSession)
            .where(UserSession.token_digest == digest_session_token(expired_token))
            .values(
                created_at=expired_at - timedelta(days=2),
                expires_at=expired_at - timedelta(days=1),
            )
        )
        db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401

    revoked_token = _issue_cookie(client, session_factory, user_id)
    with session_factory() as db:
        db.execute(
            update(UserSession)
            .where(UserSession.token_digest == digest_session_token(revoked_token))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401

    active_token = _issue_cookie(client, session_factory, user_id)
    with session_factory() as db:
        db.execute(
            update(User).where(User.id == user_id).values(account_status="suspended")
        )
        db.commit()
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set(_COOKIE_NAME, active_token)
    assert client.get("/api/v1/auth/me").status_code == 401


def test_deleted_user_sessions_are_cascaded_and_cannot_authenticate(
    auth_environment,
):
    client, session_factory = auth_environment
    user_id = _create_user(session_factory)
    _issue_cookie(client, session_factory, user_id)

    with session_factory() as db:
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
        assert db.query(UserSession).count() == 0

    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_revokes_session_clears_cookie_and_is_idempotent(auth_environment):
    client, session_factory = auth_environment
    user_id = _create_user(session_factory)
    token = _issue_cookie(client, session_factory, user_id)

    assert client.get("/api/v1/auth/me").status_code == 200
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://testserver"},
    )

    assert response.status_code == 204
    clear_cookie = response.headers["set-cookie"].lower()
    assert 'zonse_session=""' in clear_cookie
    assert "max-age=0" in clear_cookie
    assert "httponly" in clear_cookie
    assert "samesite=lax" in clear_cookie
    assert "path=/" in clear_cookie
    with session_factory() as db:
        user_session = db.execute(
            select(UserSession).where(
                UserSession.token_digest == digest_session_token(token)
            )
        ).scalar_one()
        assert user_session.revoked_at is not None

    client.cookies.set(_COOKIE_NAME, token)
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://testserver"},
        ).status_code
        == 204
    )


def test_successful_login_rotates_and_revokes_existing_session(auth_environment):
    client, session_factory = auth_environment
    _create_user(session_factory, email="first@example.test")
    second_user_id = _create_user(
        session_factory,
        email="member@example.test",
    )
    old_token = client.post(
        "/api/v1/auth/login",
        json={"email": "first@example.test", "password": _PASSWORD},
    ).cookies.get(_COOKIE_NAME)
    assert old_token

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "member@example.test", "password": _PASSWORD},
        headers={"Origin": "http://testserver"},
    )
    new_token = response.cookies.get(_COOKIE_NAME)

    assert response.status_code == 200
    assert new_token and new_token != old_token
    with session_factory() as db:
        old_session = db.execute(
            select(UserSession).where(
                UserSession.token_digest == digest_session_token(old_token)
            )
        ).scalar_one()
        new_session = db.execute(
            select(UserSession).where(
                UserSession.token_digest == digest_session_token(new_token)
            )
        ).scalar_one()
        assert old_session.revoked_at is not None
        assert new_session.revoked_at is None
        assert new_session.user_id == second_user_id


def test_user_can_revoke_all_of_their_sessions(auth_environment):
    _, session_factory = auth_environment
    user_id = _create_user(session_factory)
    other_user_id = _create_user(
        session_factory,
        email="other@example.test",
    )

    with session_factory() as db:
        create_user_session(db, user_id=user_id)
        create_user_session(db, user_id=user_id)
        create_user_session(db, user_id=other_user_id)
        assert revoke_all_user_sessions(db, user_id) == 2
        sessions = list(db.execute(select(UserSession)).scalars())

    revoked = [session for session in sessions if session.user_id == user_id]
    other_sessions = [session for session in sessions if session.user_id != user_id]
    assert len(revoked) == 2
    assert all(session.revoked_at is not None for session in revoked)
    assert len(other_sessions) == 1
    assert other_sessions[0].revoked_at is None


def test_roles_are_authoritative_and_allow_any_requested_assigned_role(
    auth_environment,
):
    client, session_factory = auth_environment
    assigned_owner_id = _create_user(
        session_factory,
        email="assigned-owner@example.test",
        roles=("owner",),
    )
    legacy_admin_id = _create_user(
        session_factory,
        email="legacy-admin@example.test",
        roles=(),
        legacy_role="admin",
    )

    _issue_cookie(client, session_factory, assigned_owner_id)
    assert client.get("/api/v1/test/roles/owner").json() == {
        "user_id": assigned_owner_id
    }
    assert (
        client.get("/api/v1/test/roles/owner-or-agent").status_code == 200
    )
    assert client.get("/api/v1/test/roles/admin").status_code == 403

    client.cookies.set(_COOKIE_NAME, "")
    with session_factory() as db:
        token, _ = create_user_session(db, user_id=legacy_admin_id)
    client.cookies.set(_COOKIE_NAME, token)

    assert client.get("/api/v1/test/roles/admin").status_code == 403
    assert client.get("/api/v1/auth/me").json()["roles"] == []


def test_owner_role_does_not_grant_access_to_another_users_property(
    auth_environment,
):
    client, session_factory = auth_environment
    actual_owner_id = _create_user(
        session_factory,
        email="property-owner@example.test",
        roles=("owner",),
    )
    other_owner_id = _create_user(
        session_factory,
        email="other-owner@example.test",
        roles=("owner",),
    )
    with session_factory() as db:
        property_record = Property(
            title="Owner-specific listing",
            price=100000,
            currency="MWK",
            city="Lilongwe",
            property_type="house",
            owner_id=actual_owner_id,
        )
        db.add(property_record)
        db.commit()
        property_id = property_record.id

    other_owner_token = _issue_cookie(client, session_factory, other_owner_id)
    denied = client.get(f"/api/v1/test/properties/{property_id}")
    assert denied.status_code == 404

    actual_owner_token = _issue_cookie(client, session_factory, actual_owner_id)
    allowed = client.get(f"/api/v1/test/properties/{property_id}")
    assert allowed.status_code == 200
    assert allowed.json()["owner_id"] == actual_owner_id
    assert other_owner_token != actual_owner_token


def test_cross_origin_unsafe_requests_are_rejected(auth_environment):
    client, session_factory = auth_environment
    user_id = _create_user(session_factory)
    _issue_cookie(client, session_factory, user_id)

    origin_response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.test", "password": _PASSWORD},
        headers={"Origin": "https://evil.example"},
    )
    referer_response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.test", "password": _PASSWORD},
        headers={"Referer": "https://evil.example/attack"},
    )
    same_origin_response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.test", "password": _PASSWORD},
        headers={"Origin": "http://testserver"},
    )
    missing_origin_logout = client.post("/api/v1/auth/logout")

    assert origin_response.status_code == 403
    assert referer_response.status_code == 403
    assert same_origin_response.status_code == 401
    assert missing_origin_logout.status_code == 403


def test_configured_frontend_origin_is_accepted_for_unsafe_requests(
    auth_environment,
    monkeypatch,
):
    client, _ = auth_environment
    monkeypatch.setattr(
        settings,
        "SESSION_CSRF_TRUSTED_ORIGINS",
        ("https://frontend.example.test",),
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.test", "password": _PASSWORD},
        headers={"Origin": "https://frontend.example.test"},
    )

    assert response.status_code == 401
