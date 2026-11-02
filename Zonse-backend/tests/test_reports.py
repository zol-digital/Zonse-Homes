from datetime import datetime, timedelta, timezone
import hashlib
import hmac

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.discovery import router as discovery_router
from app.api.v1.endpoints.properties import router as properties_router
from app.api.v1.endpoints.reports import router as reports_router
from app.config import settings
from app.database import Base, get_db
from app.models.identity import UserRole
from app.models.moderation import ModerationActionLog
from app.models.property import Property, PropertyStatus
from app.models.report import PropertyReport, ReportStatus
from app.models.user import User
from app.security.sessions import create_user_session

_COOKIE_NAME = "zonse_session"
_REPORT_IP_HASH_SECRET = "test-report-ip-hash-secret-32-bytes-minimum"
_REPORT_PAYLOAD = {
    "reason_code": "wrong_price",
    "description": "The advertised price does not match the listing details.",
}


@pytest.fixture
def report_environment(monkeypatch):
    monkeypatch.setattr(settings, "SESSION_COOKIE_NAME", _COOKIE_NAME)
    monkeypatch.setattr(settings, "SESSION_LIFETIME_SECONDS", 86400)
    monkeypatch.setattr(settings, "SESSION_COOKIE_SAMESITE", "lax")
    monkeypatch.setattr(settings, "SESSION_COOKIE_SECURE", False)
    monkeypatch.setattr(settings, "SESSION_CSRF_TRUSTED_ORIGINS", ())
    monkeypatch.setattr(
        settings,
        "REPORT_IP_HASH_SECRET",
        _REPORT_IP_HASH_SECRET,
    )

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
    app.include_router(reports_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(discovery_router, prefix="/api/v1")

    @app.middleware("http")
    async def set_test_client_ip(request, call_next):
        request.scope["client"] = ("198.51.100.10", 12345)
        return await call_next(request)

    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, session_factory, app

    app.dependency_overrides.clear()
    engine.dispose()


def _create_user(
    session_factory,
    *,
    email: str,
    role: str = "seeker",
) -> int:
    with session_factory() as db:
        user = User(
            email=email,
            canonical_email=email,
            hashed_password="not-used-in-report-tests",
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


def _create_listing(session_factory, owner_id: int) -> int:
    with session_factory() as db:
        listing = Property(
            title="Reportable listing",
            description="A publicly available property",
            price=250000,
            currency="MWK",
            city="Lilongwe",
            property_type="house",
            intent="sale",
            owner_id=owner_id,
            status=PropertyStatus.PUBLISHED.value,
        )
        db.add(listing)
        db.commit()
        return listing.id


def _create_session_cookie(client, session_factory, user_id: int) -> None:
    with session_factory() as db:
        token, _ = create_user_session(db, user_id=user_id)
    client.cookies.set(_COOKIE_NAME, token)
    client.headers.update({"Origin": "http://testserver"})


def _submit_report(client, listing_id: int, payload=None):
    return client.post(
        f"/api/v1/properties/{listing_id}/reports",
        json=payload or _REPORT_PAYLOAD,
    )


def _create_listings(session_factory, owner_id: int, count: int) -> list[int]:
    return [_create_listing(session_factory, owner_id) for _ in range(count)]


def test_valid_authenticated_report_is_private_and_does_not_change_listing(
    report_environment,
):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="listing-owner@example.test",
        role="owner",
    )
    reporter_id = _create_user(
        session_factory,
        email="reporter@example.test",
    )
    listing_id = _create_listing(session_factory, owner_id)
    _create_session_cookie(client, session_factory, reporter_id)

    response = _submit_report(client, listing_id)

    assert response.status_code == 202
    assert response.json() == {"message": "Report received. Thank you."}
    assert str(listing_id) not in response.text
    assert "reporter" not in response.text.lower()

    with session_factory() as db:
        report = db.execute(select(PropertyReport)).scalar_one()
        listing = db.get(Property, listing_id)
        owner = db.get(User, owner_id)

        assert report.listing_id == listing_id
        assert report.reported_user_id == owner_id
        assert report.reporter_user_id == reporter_id
        assert report.reason_code == "wrong_price"
        assert report.status == ReportStatus.NEW.value
        assert report.created_at is not None
        assert report.reporter_ip_digest == hmac.new(
            _REPORT_IP_HASH_SECRET.encode(),
            b"198.51.100.10",
            hashlib.sha256,
        ).hexdigest()
        assert "198.51.100.10" not in report.reporter_ip_digest
        assert listing.status == PropertyStatus.PUBLISHED.value
        assert owner.account_status == "active"
        assert db.execute(select(ModerationActionLog)).scalars().all() == []


@pytest.mark.parametrize(
    "payload",
    [
        {"reason_code": "suspicious_payment"},
        {"reason_code": "not_a_reason"},
        {"reason_code": "wrong_price", "unexpected": "field"},
        {"reason_code": "wrong_price", "description": "   "},
    ],
)
def test_invalid_report_payloads_are_rejected(report_environment, payload):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="invalid-owner@example.test",
        role="owner",
    )
    listing_id = _create_listing(session_factory, owner_id)

    response = _submit_report(client, listing_id, payload)

    assert response.status_code == 422
    with session_factory() as db:
        assert db.execute(select(PropertyReport)).scalars().all() == []


def test_authenticated_reporter_limit_is_three_with_rolling_window(
    report_environment,
):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="user-limit-owner@example.test",
        role="owner",
    )
    reporter_id = _create_user(
        session_factory,
        email="user-limited@example.test",
    )
    listing_ids = _create_listings(session_factory, owner_id, 4)
    _create_session_cookie(client, session_factory, reporter_id)

    for listing_id in listing_ids[:3]:
        assert _submit_report(client, listing_id).status_code == 202

    limited = _submit_report(
        client,
        listing_ids[3],
        {
            "reason_code": "unavailable",
            "description": "A materially different listing issue.",
        },
    )
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) > 0
    assert "report" not in limited.text.lower() or "details" not in limited.text.lower()

    with session_factory() as db:
        db.execute(
            update(PropertyReport)
            .where(PropertyReport.reporter_user_id == reporter_id)
            .values(
                created_at=datetime.now(timezone.utc)
                - timedelta(hours=24, minutes=1)
            )
        )
        db.commit()

    expired_window = _submit_report(client, listing_ids[3])
    assert expired_window.status_code == 202


def test_guest_ip_limit_is_ten_and_cannot_be_bypassed_by_reason_variations(
    report_environment,
):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="guest-limit-owner@example.test",
        role="owner",
    )
    listing_ids = _create_listings(session_factory, owner_id, 11)

    for index, listing_id in enumerate(listing_ids[:10]):
        payload = {
            "reason_code": (
                "wrong_price" if index % 2 == 0 else "misleading_details"
            ),
            "description": f"Different detail {index}.",
        }
        assert _submit_report(client, listing_id, payload).status_code == 202

    limited = _submit_report(
        client,
        listing_ids[10],
        {
            "reason_code": "other",
            "description": "Another report with changed text.",
        },
    )
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) > 0


def test_authenticated_users_are_also_limited_by_shared_ip(report_environment):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="authenticated-ip-owner@example.test",
        role="owner",
    )
    reporter_ids = [
        _create_user(
            session_factory,
            email=f"authenticated-ip-{index}@example.test",
        )
        for index in range(11)
    ]
    listing_ids = _create_listings(session_factory, owner_id, 11)

    for index, (reporter_id, listing_id) in enumerate(
        zip(reporter_ids[:10], listing_ids[:10])
    ):
        _create_session_cookie(client, session_factory, reporter_id)
        response = _submit_report(
            client,
            listing_id,
            {
                "reason_code": "other",
                "description": f"Report from account {index}.",
            },
        )
        assert response.status_code == 202

    _create_session_cookie(client, session_factory, reporter_ids[10])
    limited = _submit_report(
        client,
        listing_ids[10],
        {
            "reason_code": "other",
            "description": "A separate account using the same IP.",
        },
    )
    assert limited.status_code == 429


def test_open_duplicate_is_rejected_without_using_an_additional_quota(report_environment):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="duplicate-owner@example.test",
        role="owner",
    )
    reporter_id = _create_user(
        session_factory,
        email="duplicate-reporter@example.test",
    )
    listing_ids = _create_listings(session_factory, owner_id, 4)
    _create_session_cookie(client, session_factory, reporter_id)

    assert _submit_report(client, listing_ids[0]).status_code == 202
    duplicate = _submit_report(client, listing_ids[0])
    assert duplicate.status_code == 409
    assert _submit_report(client, listing_ids[1]).status_code == 202
    assert _submit_report(client, listing_ids[2]).status_code == 202
    limited = _submit_report(client, listing_ids[3])
    assert limited.status_code == 429

    with session_factory() as db:
        assert len(
            db.execute(
                select(PropertyReport).where(
                    PropertyReport.reporter_user_id == reporter_id
                )
            ).scalars().all()
        ) == 3


def test_resolved_report_allows_new_issue_or_evidence_but_rejects_exact_repeat(
    report_environment,
):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="resolved-owner@example.test",
        role="owner",
    )
    reporter_id = _create_user(
        session_factory,
        email="resolved-reporter@example.test",
    )
    moderator_id = _create_user(
        session_factory,
        email="reports-moderator@example.test",
        role="moderator",
    )
    listing_id = _create_listing(session_factory, owner_id)
    _create_session_cookie(client, session_factory, reporter_id)
    assert _submit_report(client, listing_id).status_code == 202
    with session_factory() as db:
        report_id = db.execute(select(PropertyReport.id)).scalar_one()

    _create_session_cookie(client, session_factory, moderator_id)
    queue = client.get("/api/v1/admin/reports")
    assert queue.status_code == 200
    assert len(queue.json()) == 1
    queued_report = queue.json()[0]
    assert queued_report["id"] == str(report_id)
    assert queued_report["reporter_user_id"] == reporter_id
    assert "reporter_ip_digest" not in queued_report

    review = client.post(
        f"/api/v1/admin/reports/{report_id}/resolve",
        json={
            "status": "dismissed",
            "reason": "The review found no actionable listing issue.",
            "resolution_code": "no_violation",
            "moderator_notes": "Private review note.",
        },
    )
    assert review.status_code == 200
    assert review.json()["status"] == ReportStatus.DISMISSED.value
    assert "moderator_notes" not in review.json()
    assert client.get("/api/v1/admin/reports").json() == []

    _create_session_cookie(client, session_factory, reporter_id)
    repeated = _submit_report(client, listing_id)
    assert repeated.status_code == 409
    new_evidence = _submit_report(
        client,
        listing_id,
        {
            "reason_code": "wrong_price",
            "description": "New evidence: the owner posted a different amount today.",
        },
    )
    assert new_evidence.status_code == 202
    with session_factory() as db:
        evidence_report_id = db.execute(
            select(PropertyReport.id).where(
                PropertyReport.status == ReportStatus.NEW.value
            )
        ).scalar_one()

    _create_session_cookie(client, session_factory, moderator_id)
    evidence_review = client.post(
        f"/api/v1/admin/reports/{evidence_report_id}/resolve",
        json={
            "status": "dismissed",
            "reason": "The additional evidence was reviewed.",
        },
    )
    assert evidence_review.status_code == 200

    _create_session_cookie(client, session_factory, reporter_id)
    different_issue = _submit_report(
        client,
        listing_id,
        {
            "reason_code": "unavailable",
            "description": "The property is no longer available.",
        },
    )
    assert different_issue.status_code == 202

    with session_factory() as db:
        actions = db.execute(
            select(ModerationActionLog).where(
                ModerationActionLog.action == "review_report"
            ).order_by(ModerationActionLog.id)
        ).scalars().all()
        assert len(actions) == 2
        action = actions[0]
        assert action.report_id == report_id
        assert action.actor_id == moderator_id
        assert action.listing_id == listing_id
        assert action.previous_status == ReportStatus.NEW.value
        assert action.new_status == ReportStatus.DISMISSED.value
        assert action.reason == "The review found no actionable listing issue."


def test_reports_do_not_leak_to_public_or_advertiser_responses(report_environment):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="privacy-owner@example.test",
        role="owner",
    )
    reporter_id = _create_user(
        session_factory,
        email="privacy-reporter@example.test",
    )
    listing_id = _create_listing(session_factory, owner_id)
    _create_session_cookie(client, session_factory, reporter_id)
    assert _submit_report(client, listing_id).status_code == 202

    public = client.get("/api/v1/discovery/properties")
    assert public.status_code == 200
    public_listing = next(
        entry for entry in public.json() if entry["id"] == listing_id
    )
    assert "reports" not in public_listing
    assert "reporter_user_id" not in public_listing
    assert "reporter_ip_digest" not in public_listing

    _create_session_cookie(client, session_factory, owner_id)
    advertiser_listing = client.get(f"/api/v1/properties/{listing_id}")
    assert advertiser_listing.status_code == 200
    assert "reports" not in advertiser_listing.json()
    assert "reporter_user_id" not in advertiser_listing.json()
    assert "reporter_ip_digest" not in advertiser_listing.json()
    assert client.get("/api/v1/admin/reports").status_code == 403


def test_only_moderators_and_admins_can_review_reports(report_environment):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="permission-owner@example.test",
        role="owner",
    )
    user_id = _create_user(
        session_factory,
        email="permission-user@example.test",
    )
    admin_id = _create_user(
        session_factory,
        email="reports-admin@example.test",
        role="admin",
    )
    listing_id = _create_listing(session_factory, owner_id)
    assert _submit_report(client, listing_id).status_code == 202
    with session_factory() as db:
        report_id = db.execute(select(PropertyReport.id)).scalar_one()

    _create_session_cookie(client, session_factory, user_id)
    assert client.get("/api/v1/admin/reports").status_code == 403
    denied_review = client.post(
        f"/api/v1/admin/reports/{report_id}/resolve",
        json={"status": "dismissed", "reason": "Not authorized"},
    )
    assert denied_review.status_code == 403

    _create_session_cookie(client, session_factory, admin_id)
    authorized = client.get("/api/v1/admin/reports")
    assert authorized.status_code == 200
    assert len(authorized.json()) == 1


def test_report_submission_requires_published_listing_and_valid_session_cookie(
    report_environment,
):
    client, session_factory, _ = report_environment
    owner_id = _create_user(
        session_factory,
        email="not-published-owner@example.test",
        role="owner",
    )
    listing_id = _create_listing(session_factory, owner_id)
    with session_factory() as db:
        db.get(Property, listing_id).status = PropertyStatus.PENDING_REVIEW.value
        db.commit()

    assert _submit_report(client, listing_id).status_code == 404

    client.cookies.set(_COOKIE_NAME, "invalid-session-token")
    client.headers.update({"Origin": "http://testserver"})
    invalid_cookie = _submit_report(client, listing_id)
    assert invalid_cookie.status_code == 401
