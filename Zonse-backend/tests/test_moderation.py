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
from app.models.reference_data import DEFAULT_PROPERTY_CATEGORIES, PropertyCategory
from app.models.report import PropertyReport, ReportStatus
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
    with session_factory() as db:
        db.add_all(
            PropertyCategory(slug=slug, name=name)
            for slug, name in DEFAULT_PROPERTY_CATEGORIES.items()
        )
        db.commit()

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


@pytest.mark.parametrize("reviewer_role", ["moderator", "admin"])
def test_authorized_reviewer_can_remove_listing_with_audit_and_private_reason(
    moderation_environment,
    reviewer_role,
):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="remove-owner@example.test",
        role="owner",
    )
    moderator_id = _create_user(
        session_factory,
        email=f"remove-{reviewer_role}@example.test",
        role=reviewer_role,
    )

    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)
    _set_session_cookie(client, session_factory, moderator_id)
    approved = client.post(
        f"/api/v1/admin/listings/{listing_id}/approve",
        json={"reason": "Initial review completed."},
    )
    assert approved.status_code == 200

    removed = client.post(
        f"/api/v1/admin/listings/{listing_id}/remove",
        json={
            "reason": "Credible evidence of a fraudulent listing.",
            "moderator_notes": "Internal: preserve the evidence for follow-up.",
        },
    )

    assert removed.status_code == 200
    assert removed.json()["status"] == PropertyStatus.REMOVED.value
    assert "reason" not in removed.json()
    assert "moderator_notes" not in removed.json()
    assert client.get("/api/v1/discovery/properties").json() == []

    _set_session_cookie(client, session_factory, owner_id)
    advertiser_listing = client.get(f"/api/v1/properties/{listing_id}")
    assert advertiser_listing.status_code == 200
    assert advertiser_listing.json()["status"] == PropertyStatus.REMOVED.value
    assert "reason" not in advertiser_listing.json()
    assert "moderator_notes" not in advertiser_listing.json()

    with session_factory() as db:
        removal = db.execute(
            select(ModerationActionLog).where(
                ModerationActionLog.listing_id == listing_id,
                ModerationActionLog.action == "remove",
            )
        ).scalar_one()

    assert removal.actor_id == moderator_id
    assert removal.previous_status == PropertyStatus.PUBLISHED.value
    assert removal.new_status == PropertyStatus.REMOVED.value
    assert removal.reason == "Credible evidence of a fraudulent listing."
    assert removal.moderator_notes == (
        "Internal: preserve the evidence for follow-up."
    )
    assert removal.created_at is not None

    _set_session_cookie(client, session_factory, moderator_id)
    repeated = client.post(
        f"/api/v1/admin/listings/{listing_id}/remove",
        json={"reason": "Repeated removal must not be logged."},
    )
    assert repeated.status_code == 409
    with session_factory() as db:
        removals = db.execute(
            select(ModerationActionLog).where(
                ModerationActionLog.listing_id == listing_id,
                ModerationActionLog.action == "remove",
            )
        ).scalars().all()
    assert len(removals) == 1


def test_listing_removal_requires_moderator_and_reason(moderation_environment):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="remove-auth-owner@example.test",
        role="owner",
    )
    seeker_id = _create_user(
        session_factory,
        email="remove-auth-seeker@example.test",
        role="seeker",
    )
    moderator_id = _create_user(
        session_factory,
        email="remove-auth-moderator@example.test",
        role="moderator",
    )

    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)

    client.cookies.clear()
    client.headers.update({"Origin": "http://testserver"})
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/remove",
        json={"reason": "Unauthenticated action"},
    ).status_code == 401

    _set_session_cookie(client, session_factory, seeker_id)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/remove",
        json={"reason": "Unauthorized action"},
    ).status_code == 403

    _set_session_cookie(client, session_factory, moderator_id)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/remove",
        json={"reason": "   "},
    ).status_code == 422
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/remove",
        json={},
    ).status_code == 422

    with session_factory() as db:
        assert db.get(Property, listing_id).status == PropertyStatus.PENDING_REVIEW.value
        assert db.execute(select(ModerationActionLog)).scalars().all() == []


def test_moderator_hide_preserves_status_and_restore_is_audited(moderation_environment):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="hide-owner@example.test",
        role="owner",
    )
    moderator_id = _create_user(
        session_factory,
        email="hide-moderator@example.test",
        role="moderator",
    )

    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)
    _set_session_cookie(client, session_factory, moderator_id)
    approved = client.post(
        f"/api/v1/admin/listings/{listing_id}/approve",
        json={"reason": "Initial review completed."},
    )
    assert approved.status_code == 200

    hidden = client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={
            "reason": "Credible report requires investigation.",
            "moderator_notes": "Private: contact the reporter for evidence.",
        },
    )

    assert hidden.status_code == 200
    assert hidden.json()["status"] == PropertyStatus.PUBLISHED.value
    assert "moderator_hidden" not in hidden.json()
    assert "reason" not in hidden.json()
    assert "moderator_notes" not in hidden.json()
    assert client.get("/api/v1/discovery/properties").json() == []

    _set_session_cookie(client, session_factory, owner_id)
    advertiser_listing = client.get(f"/api/v1/properties/{listing_id}")
    assert advertiser_listing.status_code == 200
    assert advertiser_listing.json()["status"] == PropertyStatus.PUBLISHED.value
    assert "moderator_hidden" not in advertiser_listing.json()
    assert "reason" not in advertiser_listing.json()
    assert "moderator_notes" not in advertiser_listing.json()

    _set_session_cookie(client, session_factory, moderator_id)
    restored = client.post(
        f"/api/v1/admin/listings/{listing_id}/restore",
        json={"reason": "Investigation is complete; listing is eligible."},
    )

    assert restored.status_code == 200
    assert restored.json()["status"] == PropertyStatus.PUBLISHED.value
    assert client.get("/api/v1/discovery/properties").json()[0]["id"] == listing_id

    with session_factory() as db:
        listing = db.get(Property, listing_id)
        actions = db.execute(
            select(ModerationActionLog)
            .where(ModerationActionLog.listing_id == listing_id)
            .order_by(ModerationActionLog.id)
        ).scalars().all()

    assert listing.moderator_hidden is False
    assert [action.action for action in actions] == ["approve", "hide", "restore"]
    assert [action.actor_id for action in actions[1:]] == [
        moderator_id,
        moderator_id,
    ]
    assert [action.previous_status for action in actions[1:]] == [
        PropertyStatus.PUBLISHED.value,
        PropertyStatus.PUBLISHED.value,
    ]
    assert [action.new_status for action in actions[1:]] == [
        PropertyStatus.PUBLISHED.value,
        PropertyStatus.PUBLISHED.value,
    ]
    assert [action.reason for action in actions[1:]] == [
        "Credible report requires investigation.",
        "Investigation is complete; listing is eligible.",
    ]
    assert actions[1].created_at is not None
    assert actions[2].created_at is not None
    assert actions[1].moderator_notes == (
        "Private: contact the reporter for evidence."
    )


def test_hide_restore_authorization_reasons_and_repeated_actions(
    moderation_environment,
):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="hide-auth-owner@example.test",
        role="owner",
    )
    seeker_id = _create_user(
        session_factory,
        email="hide-auth-seeker@example.test",
        role="seeker",
    )
    admin_id = _create_user(
        session_factory,
        email="hide-auth-admin@example.test",
        role="admin",
    )
    moderator_id = _create_user(
        session_factory,
        email="hide-auth-moderator@example.test",
        role="moderator",
    )

    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)
    _set_session_cookie(client, session_factory, moderator_id)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/approve",
        json={"reason": "Initial review completed."},
    ).status_code == 200

    client.cookies.clear()
    client.headers.pop("Origin", None)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={"reason": "Authentication is required."},
    ).status_code == 401
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/restore",
        json={"reason": "Authentication is required."},
    ).status_code == 401

    _set_session_cookie(client, session_factory, owner_id)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={"reason": "Owner is not a moderator."},
    ).status_code == 403
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/restore",
        json={"reason": "Owner is not a moderator."},
    ).status_code == 403

    _set_session_cookie(client, session_factory, seeker_id)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={"reason": "Seeker is not a moderator."},
    ).status_code == 403

    _set_session_cookie(client, session_factory, admin_id)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={"reason": "   "},
    ).status_code == 422
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={},
    ).status_code == 422
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/restore",
        json={"reason": "   "},
    ).status_code == 422
    hidden = client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={"reason": "Administrator initiated investigation."},
    )
    assert hidden.status_code == 200
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={"reason": "Repeated hide is invalid."},
    ).status_code == 409
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/restore",
        json={"reason": "Restore requires a reason."},
    ).status_code == 200
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/restore",
        json={"reason": "Repeated restore is invalid."},
    ).status_code == 409


def test_restore_ineligible_listing_does_not_republish_it(moderation_environment):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="expired-hide-owner@example.test",
        role="owner",
    )
    moderator_id = _create_user(
        session_factory,
        email="expired-hide-moderator@example.test",
        role="moderator",
    )
    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)
    _set_session_cookie(client, session_factory, moderator_id)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/approve",
        json={"reason": "Initial review completed."},
    ).status_code == 200
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={"reason": "Temporarily hidden pending review."},
    ).status_code == 200

    with session_factory() as db:
        listing = db.get(Property, listing_id)
        listing.status = PropertyStatus.EXPIRED.value
        db.commit()

    restored = client.post(
        f"/api/v1/admin/listings/{listing_id}/restore",
        json={"reason": "Lift moderation hold without republishing."},
    )

    assert restored.status_code == 200
    assert restored.json()["status"] == PropertyStatus.EXPIRED.value
    assert client.get("/api/v1/discovery/properties").json() == []
    with session_factory() as db:
        listing = db.get(Property, listing_id)
        assert listing.status == PropertyStatus.EXPIRED.value
        assert listing.moderator_hidden is False


def test_moderation_restore_cannot_restore_removed_listing(moderation_environment):
    client, session_factory = moderation_environment
    owner_id = _create_user(
        session_factory,
        email="removed-hide-owner@example.test",
        role="owner",
    )
    moderator_id = _create_user(
        session_factory,
        email="removed-hide-moderator@example.test",
        role="moderator",
    )
    _set_session_cookie(client, session_factory, owner_id)
    listing_id = _create_and_submit_listing(client)
    _set_session_cookie(client, session_factory, moderator_id)
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/approve",
        json={"reason": "Initial review completed."},
    ).status_code == 200
    assert client.post(
        f"/api/v1/admin/listings/{listing_id}/hide",
        json={"reason": "Temporarily hidden pending review."},
    ).status_code == 200

    with session_factory() as db:
        listing = db.get(Property, listing_id)
        listing.status = PropertyStatus.REMOVED.value
        db.commit()

    restored = client.post(
        f"/api/v1/admin/listings/{listing_id}/restore",
        json={"reason": "A removed listing must remain removed."},
    )

    assert restored.status_code == 409
    with session_factory() as db:
        listing = db.get(Property, listing_id)
        assert listing.status == PropertyStatus.REMOVED.value
        assert listing.moderator_hidden is True


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


def test_admin_dashboard_summarizes_listing_report_and_backlog_counts(
    moderation_environment,
):
    client, session_factory = moderation_environment
    moderator_id = _create_user(
        session_factory,
        email="dashboard-moderator@example.test",
        role="moderator",
    )
    admin_id = _create_user(
        session_factory,
        email="dashboard-admin@example.test",
        role="admin",
    )
    with session_factory() as db:
        db.add_all(
            [
                Property(
                    title=f"Dashboard listing {index}",
                    price="1000.00",
                    currency="MWK",
                    city="Lilongwe",
                    property_type="house",
                    intent="sale",
                    owner_id=admin_id,
                    status=listing_status.value,
                    amenities=[],
                    utilities=[],
                )
                for index, listing_status in enumerate(
                    (
                        PropertyStatus.PENDING_REVIEW,
                        PropertyStatus.PENDING_REVIEW,
                        PropertyStatus.PUBLISHED,
                        PropertyStatus.REMOVED,
                    )
                )
            ]
        )
        db.add_all(
            [
                PropertyReport(
                    reporter_ip_digest="a" * 64,
                    reason_code="other",
                    status=report_status.value,
                )
                for report_status in ReportStatus
            ]
        )
        db.commit()

    assert client.get("/api/v1/admin/dashboard").status_code == 401
    _set_session_cookie(client, session_factory, moderator_id)
    assert client.get("/api/v1/admin/dashboard").status_code == 403

    _set_session_cookie(client, session_factory, admin_id)
    response = client.get("/api/v1/admin/dashboard")

    assert response.status_code == 200
    payload = response.json()
    expected_listing_counts = {
        listing_status.value: 0 for listing_status in PropertyStatus
    }
    expected_listing_counts.update(
        {
            PropertyStatus.PENDING_REVIEW.value: 2,
            PropertyStatus.PUBLISHED.value: 1,
            PropertyStatus.REMOVED.value: 1,
        }
    )
    assert payload["listing_counts_by_status"] == expected_listing_counts
    assert payload["report_counts_by_status"] == {
        report_status.value: 1 for report_status in ReportStatus
    }
    assert payload["moderation_backlog"] == {
        "pending_listings": 2,
        "open_reports": 3,
        "total": 5,
    }
    assert set(payload) == {
        "listing_counts_by_status",
        "report_counts_by_status",
        "moderation_backlog",
    }


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
    assert "/api/v1/admin/listings/{property_id}/remove" in paths
    assert "/api/v1/admin/listings/{property_id}/hide" in paths
    assert "/api/v1/admin/listings/{property_id}/restore" in paths
    assert "/api/v1/admin/dashboard" in paths
    schemas = specification["components"]["schemas"]
    moderation_request = schemas["ModerationActionRequest"]
    assert "reason" in moderation_request["required"]
    property_response_fields = schemas["PropertyResponse"]["properties"]
    assert "moderator_hidden" not in property_response_fields
    assert "moderator_notes" not in property_response_fields
