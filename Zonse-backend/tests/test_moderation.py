from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.discovery import router as discovery_router
from app.api.v1.endpoints.properties import router as properties_router
from app.config import settings
from app.database import Base, get_db
from app.models.identity import UserRole
from app.models.moderation import ModerationActionLog
from app.models.property import Property, PropertyStatus
from app.models.user import User
from app.security.sessions import create_user_session


@pytest.fixture
def moderation_environment(monkeypatch):
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

    app = FastAPI()
    app.include_router(properties_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(discovery_router, prefix="/api/v1")

    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, session_factory

    app.dependency_overrides.clear()
    engine.dispose()


def _create_user(session_factory, *, email: str, role: str) -> int:
    with session_factory() as db:
        user = User(
            email=email,
            canonical_email=email,
            hashed_password="sha256:placeholder",
            full_name="Example User",
            account_status="active",
            email_verified_at=datetime.now(timezone.utc),
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role=role))
        db.commit()
        return user.id


def _set_session_cookie(client, session_factory, user_id: int) -> None:
    with session_factory() as db:
        token, _ = create_user_session(db, user_id=user_id)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    client.headers.update({"Origin": "http://testserver"})


def _create_and_submit_listing(client: TestClient) -> int:
    response = client.post(
        "/api/v1/properties",
        json={
            "title": "Test listing",
            "description": "A home available for rent",
            "price": "250000.00",
            "currency": "MWK",
            "city": "Lilongwe",
            "property_type": "house",
            "intent": "sale",
            "advertiser_name": "Example Advertiser",
        },
    )
    assert response.status_code == 201
    listing = response.json()
    assert listing["status"] == PropertyStatus.DRAFT.value

    submission = client.post(f"/api/v1/properties/{listing['id']}/submit")
    assert submission.status_code == 200
    assert submission.json()["status"] == PropertyStatus.PENDING_REVIEW.value
    return listing["id"]


def test_submission_review_and_approval_publish_only_after_moderator_action(
    moderation_environment,
):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="owner@example.test",
        role="owner",
    )
    moderator_id = _create_user(
        session_factory,
        email="moderator@example.test",
        role="moderator",
    )

    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)

    discovery = client.get("/api/v1/discovery/properties")
    assert discovery.status_code == 200
    assert discovery.json() == []

    owner_review_attempt = client.post(
        f"/api/v1/admin/listings/{listing_id}/approve",
        json={"reason": "Owner cannot approve their listing"},
    )
    assert owner_review_attempt.status_code == 403

    _set_session_cookie(client, session_factory, moderator_id)
    queue = client.get("/api/v1/admin/moderation/listings")
    assert queue.status_code == 200
    assert [listing["id"] for listing in queue.json()] == [listing_id]

    requested_changes = client.post(
        f"/api/v1/admin/listings/{listing_id}/request-changes",
        json={
            "reason": "Clarify the property description.",
            "moderator_notes": "Internal: confirm the advertised location.",
        },
    )
    assert requested_changes.status_code == 200
    assert requested_changes.json()["status"] == PropertyStatus.CHANGES_REQUESTED.value
    assert "moderator_notes" not in requested_changes.json()

    queue = client.get("/api/v1/admin/moderation/listings")
    assert queue.status_code == 200
    assert queue.json() == []

    _set_session_cookie(client, session_factory, owner_id)
    advertiser_listings = client.get("/api/v1/properties")
    assert advertiser_listings.status_code == 200
    advertiser_listing = advertiser_listings.json()[0]
    assert advertiser_listing["status"] == PropertyStatus.CHANGES_REQUESTED.value
    assert "moderator_notes" not in advertiser_listing

    update = client.patch(
        f"/api/v1/properties/{listing_id}",
        json={"description": "Updated description with the requested clarification."},
    )
    assert update.status_code == 200
    resubmission = client.post(f"/api/v1/properties/{listing_id}/submit")
    assert resubmission.status_code == 200
    assert resubmission.json()["status"] == PropertyStatus.PENDING_REVIEW.value

    _set_session_cookie(client, session_factory, moderator_id)
    approval = client.post(
        f"/api/v1/admin/listings/{listing_id}/approve",
        json={
            "reason": "The requested clarification is present.",
            "moderator_notes": "Internal review completed.",
        },
    )
    assert approval.status_code == 200
    assert approval.json()["status"] == PropertyStatus.PUBLISHED.value
    assert "moderator_notes" not in approval.json()

    discovery = client.get("/api/v1/discovery/properties")
    assert discovery.status_code == 200
    assert [listing["id"] for listing in discovery.json()] == [listing_id]
    assert "moderator_notes" not in discovery.json()[0]

    invalid_transition = client.post(
        f"/api/v1/admin/listings/{listing_id}/reject",
        json={"reason": "A published listing cannot be rejected from this state."},
    )
    assert invalid_transition.status_code == 409

    with session_factory() as db:
        audit_entries = list(
            db.execute(
                select(ModerationActionLog)
                .where(ModerationActionLog.listing_id == listing_id)
                .order_by(ModerationActionLog.id)
            ).scalars()
        )

    assert [entry.action for entry in audit_entries] == [
        "request_changes",
        "approve",
    ]
    assert [entry.actor_id for entry in audit_entries] == [
        moderator_id,
        moderator_id,
    ]
    assert [entry.previous_status for entry in audit_entries] == [
        PropertyStatus.PENDING_REVIEW.value,
        PropertyStatus.PENDING_REVIEW.value,
    ]
    assert [entry.new_status for entry in audit_entries] == [
        PropertyStatus.CHANGES_REQUESTED.value,
        PropertyStatus.PUBLISHED.value,
    ]
    assert audit_entries[0].reason == "Clarify the property description."
    assert audit_entries[0].moderator_notes == (
        "Internal: confirm the advertised location."
    )
    assert all(entry.created_at is not None for entry in audit_entries)


def test_moderation_requires_reason_and_rejects_non_moderator_roles(
    moderation_environment,
):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="owner2@example.test",
        role="owner",
    )
    seeker_id = _create_user(
        session_factory,
        email="seeker@example.test",
        role="seeker",
    )
    moderator_id = _create_user(
        session_factory,
        email="moderator2@example.test",
        role="moderator",
    )

    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)

    _set_session_cookie(client, session_factory, seeker_id)
    forbidden = client.post(
        f"/api/v1/admin/listings/{listing_id}/reject",
        json={"reason": "Not authorized"},
    )
    assert forbidden.status_code == 403

    _set_session_cookie(client, session_factory, moderator_id)
    missing_reason = client.post(
        f"/api/v1/admin/listings/{listing_id}/reject",
        json={},
    )
    assert missing_reason.status_code == 422
    blank_reason = client.post(
        f"/api/v1/admin/listings/{listing_id}/reject",
        json={"reason": "   "},
    )
    assert blank_reason.status_code == 422

    with session_factory() as db:
        assert db.get(Property, listing_id).status == PropertyStatus.PENDING_REVIEW.value
        assert db.execute(select(ModerationActionLog)).scalars().all() == []


def test_rejection_remains_private_and_does_not_create_public_listing(
    moderation_environment,
):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="owner3@example.test",
        role="owner",
    )
    moderator_id = _create_user(
        session_factory,
        email="moderator3@example.test",
        role="moderator",
    )

    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)
    _set_session_cookie(client, session_factory, moderator_id)

    response = client.post(
        f"/api/v1/admin/listings/{listing_id}/reject",
        json={"reason": "The listing does not meet publication standards."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == PropertyStatus.REJECTED.value

    discovery = client.get("/api/v1/discovery/properties")
    assert discovery.status_code == 200
    assert discovery.json() == []


def test_only_administrators_can_read_audit_logs_and_scope_is_limited(
    moderation_environment,
):
    client, session_factory = moderation_environment
    moderator_id = _create_user(
        session_factory,
        email="moderator4@example.test",
        role="moderator",
    )
    admin_id = _create_user(
        session_factory,
        email="admin@example.test",
        role="admin",
    )

    _set_session_cookie(client, session_factory, moderator_id)
    assert client.get("/api/v1/admin/audit-logs").status_code == 403

    _set_session_cookie(client, session_factory, admin_id)
    response = client.get("/api/v1/admin/audit-logs")
    assert response.status_code == 200
    assert response.json() == []


def test_openapi_exposes_only_approved_first_increment_operations(
    moderation_environment,
):
    client, _ = moderation_environment
    specification = client.get("/openapi.json").json()
    paths = specification["paths"]

    assert "/api/v1/admin/moderation/listings" in paths
    assert "/api/v1/admin/listings/{property_id}/approve" in paths
    assert "/api/v1/admin/listings/{property_id}/reject" in paths
    assert "/api/v1/admin/listings/{property_id}/request-changes" in paths
    assert "/api/v1/admin/listings/{property_id}/hide" not in paths
    assert "/api/v1/admin/listings/{property_id}/remove" not in paths
