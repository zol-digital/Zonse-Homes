from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.v1.endpoints.admin import router as admin_router
from app.config import settings
from app.database import Base, get_db
from app.models.identity import UserRole
from app.models.session import UserSession
from app.models.user import User
from app.security.sessions import create_user_session, digest_session_token


@pytest.fixture
def admin_account_environment(monkeypatch):
    monkeypatch.setattr(settings, "SESSION_COOKIE_NAME", "zonse_session")
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
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db:
        accounts = {
            "admin": User(
                email="admin-account@example.test",
                canonical_email="admin-account@example.test",
                hashed_password="sha256:placeholder",
                full_name="Admin Account",
                account_status="active",
                email_verified_at=datetime.now(timezone.utc),
                is_active=True,
            ),
            "moderator": User(
                email="moderator-account@example.test",
                canonical_email="moderator-account@example.test",
                hashed_password="sha256:placeholder",
                full_name="Moderator Account",
                account_status="active",
                email_verified_at=datetime.now(timezone.utc),
                is_active=True,
            ),
            "owner": User(
                email="owner-account@example.test",
                canonical_email="owner-account@example.test",
                hashed_password="sha256:placeholder",
                full_name="Owner Account",
                account_status="active",
                email_verified_at=datetime.now(timezone.utc),
                is_active=True,
            ),
            "disabled": User(
                email="disabled-account@example.test",
                canonical_email="disabled-account@example.test",
                hashed_password="sha256:placeholder",
                full_name="Disabled Account",
                account_status="disabled",
                email_verified_at=datetime.now(timezone.utc),
                is_active=False,
            ),
            "unverified": User(
                email="unverified-account@example.test",
                canonical_email="unverified-account@example.test",
                hashed_password="sha256:placeholder",
                full_name="Unverified Account",
                account_status="suspended",
                email_verified_at=None,
                is_active=True,
            ),
        }
        db.add_all(accounts.values())
        db.flush()
        db.add_all(
            [
                UserRole(user_id=accounts["admin"].id, role="admin"),
                UserRole(user_id=accounts["moderator"].id, role="moderator"),
                UserRole(user_id=accounts["owner"].id, role="owner"),
            ]
        )
        db.commit()
        account_ids = {name: account.id for name, account in accounts.items()}

    app = FastAPI()
    app.include_router(admin_router, prefix="/api/v1")

    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, session_factory, account_ids, app

    app.dependency_overrides.clear()
    engine.dispose()


def _session_token(session_factory, user_id: int) -> str:
    with session_factory() as db:
        token, _ = create_user_session(db, user_id=user_id)
        return token


def _set_session(client: TestClient, token: str) -> None:
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    client.headers.update({"Origin": "http://testserver"})


def test_admin_suspend_revokes_sessions_and_restore_does_not_revive_them(
    admin_account_environment,
):
    client, session_factory, account_ids, _ = admin_account_environment
    admin_token = _session_token(session_factory, account_ids["admin"])
    owner_token = _session_token(session_factory, account_ids["owner"])

    assert client.post(
        f"/api/v1/admin/accounts/{account_ids['owner']}/suspend"
    ).status_code == 401
    _set_session(client, _session_token(session_factory, account_ids["moderator"]))
    assert client.post(
        f"/api/v1/admin/accounts/{account_ids['owner']}/suspend"
    ).status_code == 403

    _set_session(client, admin_token)
    suspended = client.post(
        f"/api/v1/admin/accounts/{account_ids['owner']}/suspend"
    )
    assert suspended.status_code == 200
    assert suspended.json()["account_status"] == "suspended"
    assert suspended.json()["is_active"] is True
    assert "hashed_password" not in suspended.json()
    assert client.post(
        f"/api/v1/admin/accounts/{account_ids['owner']}/suspend"
    ).status_code == 409

    with session_factory() as db:
        owner_session = db.execute(
            select(UserSession).where(
                UserSession.token_digest == digest_session_token(owner_token)
            )
        ).scalar_one()
        assert owner_session.revoked_at is not None
        account = db.get(User, account_ids["owner"])
        assert account is not None
        assert account.account_status == "suspended"
        assert account.is_active is True

    _set_session(client, owner_token)
    assert client.get("/api/v1/admin/dashboard").status_code == 401

    _set_session(client, admin_token)
    restored = client.post(
        f"/api/v1/admin/accounts/{account_ids['owner']}/restore"
    )
    assert restored.status_code == 200
    assert restored.json()["account_status"] == "active"
    action_logs = client.get("/api/v1/admin/action-logs")
    assert action_logs.status_code == 200
    assert [
        (entry["action"], entry["entity_type"], entry["entity_id"])
        for entry in action_logs.json()
    ] == [
        ("restore", "user", str(account_ids["owner"])),
        ("suspend", "user", str(account_ids["owner"])),
    ]
    assert action_logs.json()[0]["before_data"] == {
        "account_status": "suspended",
        "is_active": True,
    }
    assert action_logs.json()[1]["after_data"] == {
        "account_status": "suspended",
        "is_active": True,
    }
    _set_session(client, _session_token(session_factory, account_ids["moderator"]))
    assert client.get("/api/v1/admin/action-logs").status_code == 403
    _set_session(client, owner_token)
    assert client.get("/api/v1/admin/dashboard").status_code == 401


def test_admin_account_actions_reject_self_suspension_and_unrestorable_accounts(
    admin_account_environment,
):
    client, session_factory, account_ids, _ = admin_account_environment
    _set_session(client, _session_token(session_factory, account_ids["admin"]))

    assert client.post(
        f"/api/v1/admin/accounts/{account_ids['admin']}/suspend"
    ).status_code == 409
    assert client.post(
        f"/api/v1/admin/accounts/{account_ids['disabled']}/restore"
    ).status_code == 409
    assert client.post(
        f"/api/v1/admin/accounts/{account_ids['unverified']}/restore"
    ).status_code == 409
    assert client.post("/api/v1/admin/accounts/999999/suspend").status_code == 404


def test_admin_account_actions_are_documented(admin_account_environment):
    client, _, _, _ = admin_account_environment
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/admin/accounts/{user_id}/suspend" in paths
    assert "/api/v1/admin/accounts/{user_id}/restore" in paths
