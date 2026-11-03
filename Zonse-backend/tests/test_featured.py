from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.discovery import router as discovery_router
from app.api.v1.endpoints.discovery import featured_router as featured_discovery_router
from app.api.v1.endpoints.featured import router as featured_router
from app.config import settings
from app.database import Base, get_db
from app.models.admin_audit import AdminActionLog
from app.models.featured import (
    FeaturedPlacementPackage,
    FeaturedPromotion,
    FeaturedPromotionOrder,
    FeaturedPromotionSettings,
)
from app.models.identity import UserRole
from app.models.property import Property, PropertyStatus
from app.models.user import User
from app.security.sessions import create_user_session

_COOKIE_NAME = "zonse_session"
_WEBHOOK_SECRET = "featured-webhook-test-secret-at-least-32-bytes"


@pytest.fixture
def featured_environment(monkeypatch):
    monkeypatch.setattr(settings, "SESSION_COOKIE_NAME", _COOKIE_NAME)
    monkeypatch.setattr(settings, "SESSION_LIFETIME_SECONDS", 86400)
    monkeypatch.setattr(settings, "SESSION_COOKIE_SAMESITE", "lax")
    monkeypatch.setattr(settings, "SESSION_COOKIE_SECURE", False)
    monkeypatch.setattr(settings, "SESSION_CSRF_TRUSTED_ORIGINS", ())
    monkeypatch.setattr(
        settings,
        "FEATURED_PAYMENT_WEBHOOK_SECRET",
        _WEBHOOK_SECRET,
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

    with session_factory() as db:
        owner = User(
            email="featured-owner@example.test",
            canonical_email="featured-owner@example.test",
            hashed_password="sha256:placeholder",
            full_name="Featured Owner",
            account_status="active",
            email_verified_at=datetime.now(timezone.utc),
            is_active=True,
        )
        admin = User(
            email="featured-admin@example.test",
            canonical_email="featured-admin@example.test",
            hashed_password="sha256:placeholder",
            full_name="Featured Admin",
            account_status="active",
            email_verified_at=datetime.now(timezone.utc),
            is_active=True,
        )
        db.add_all([owner, admin])
        db.flush()
        db.add_all(
            [
                UserRole(user_id=owner.id, role="owner"),
                UserRole(user_id=admin.id, role="admin"),
                FeaturedPromotionSettings(id=1, homepage_inventory_limit=1),
                FeaturedPlacementPackage(
                    id=1,
                    placement_type="area",
                    duration="weekly",
                    price="2000.00",
                    currency="MWK",
                    is_available=True,
                ),
                FeaturedPlacementPackage(
                    id=2,
                    placement_type="homepage",
                    duration="weekly",
                    price="5000.00",
                    currency="MWK",
                    is_available=True,
                ),
            ]
        )
        db.flush()
        for listing_id, listing_status in (
            (1, PropertyStatus.PUBLISHED.value),
            (2, PropertyStatus.PUBLISHED.value),
            (3, PropertyStatus.PENDING_REVIEW.value),
        ):
            db.add(
                Property(
                    id=listing_id,
                    title=f"Featured home {listing_id}",
                    price="250000.00",
                    currency="MWK",
                    city="Lilongwe",
                    district="Area 3",
                    neighborhood="Old Town",
                    property_type="house",
                    intent="sale",
                    owner_id=owner.id,
                    status=listing_status,
                    amenities=[],
                    utilities=[],
                )
            )
        db.commit()
        owner_id = owner.id
        admin_id = admin.id

    app = FastAPI()
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(discovery_router, prefix="/api/v1")
    app.include_router(featured_discovery_router, prefix="/api/v1")
    app.include_router(featured_router, prefix="/api/v1")

    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, session_factory, owner_id, admin_id

    app.dependency_overrides.clear()
    engine.dispose()


def _authenticate(client, session_factory, user_id):
    with session_factory() as db:
        token, _ = create_user_session(db, user_id=user_id)
    client.cookies.set(_COOKIE_NAME, token)
    client.headers.update({"Origin": "http://testserver"})


def _create_order(client, *, listing_id, package_id, target=True):
    payload = {"listing_id": listing_id, "package_id": package_id}
    if target:
        payload.update(
            target_city="Lilongwe",
            target_district="Area 3",
            target_neighborhood="Old Town",
        )
    return client.post("/api/v1/featured/orders", json=payload)


def _send_signed_payment(
    client,
    *,
    order_id,
    amount="2000.00",
    currency="MWK",
    reference="gateway-reference-1",
    payment_status="paid",
    secret=_WEBHOOK_SECRET,
):
    body = json.dumps(
        {
            "order_id": order_id,
            "payment_reference": reference,
            "status": payment_status,
            "amount": amount,
            "currency": currency,
        },
        separators=(",", ":"),
    ).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return client.post(
        "/api/v1/featured/payment-webhook",
        content=body,
        headers={"X-Payment-Signature": signature, "Content-Type": "application/json"},
    )


def test_area_feature_activates_only_after_signed_payment_and_matches_search_context(
    featured_environment,
):
    client, session_factory, owner_id, admin_id = featured_environment
    packages = client.get("/api/v1/featured/packages")
    assert packages.status_code == 200
    assert [(item["placement_type"], item["price"]) for item in packages.json()] == [
        ("area", "2000.00"),
        ("homepage", "5000.00"),
    ]

    _authenticate(client, session_factory, owner_id)
    draft_order = _create_order(client, listing_id=3, package_id=1)
    assert draft_order.status_code == 409

    mismatch = client.post(
        "/api/v1/featured/orders",
        json={
            "listing_id": 1,
            "package_id": 1,
            "target_city": "Blantyre",
        },
    )
    assert mismatch.status_code == 422

    order_response = _create_order(client, listing_id=1, package_id=1)
    assert order_response.status_code == 201
    order = order_response.json()
    assert order["amount"] == "2000.00"
    assert order["placement_type"] == "area"
    assert order["payment_status"] == "pending"

    assert client.get(
        "/api/v1/discovery/properties",
        params={"city": "Lilongwe"},
    ).json()[0]["is_featured"] is False
    assert client.post(
        "/api/v1/featured/payment-webhook",
        json={
            "order_id": order["id"],
            "payment_reference": "bad-signature",
            "status": "paid",
            "amount": "2000.00",
            "currency": "MWK",
        },
    ).status_code == 401
    assert _send_signed_payment(
        client,
        order_id=order["id"],
        amount="2000.01",
    ).status_code == 422

    payment = _send_signed_payment(client, order_id=order["id"])
    assert payment.status_code == 200
    assert _send_signed_payment(client, order_id=order["id"]).status_code == 200

    area_results = client.get(
        "/api/v1/discovery/properties",
        params={
            "city": "Lilongwe",
            "district": "Area 3",
            "neighborhood": "Old Town",
        },
    )
    promoted_listing = next(
        listing for listing in area_results.json() if listing["id"] == 1
    )
    assert promoted_listing["is_featured"] is True
    assert promoted_listing["featured_placement"] == "area"
    assert promoted_listing["featured_expires_at"] is not None
    general_results = client.get("/api/v1/discovery/properties").json()
    assert next(item for item in general_results if item["id"] == 1)["is_featured"] is False

    with session_factory() as db:
        promotion_id = db.execute(
            select(FeaturedPromotion.id).where(FeaturedPromotion.listing_id == 1)
        ).scalar_one()
    view_event = client.post(
        f"/api/v1/featured/promotions/{promotion_id}/events",
        json={"event_type": "view"},
    )
    assert view_event.status_code == 200
    assert view_event.json() == {"recorded": True}
    assert client.post(
        f"/api/v1/featured/promotions/{promotion_id}/events",
        json={"event_type": "view"},
    ).json() == {"recorded": False}
    assert client.post(
        f"/api/v1/featured/promotions/{promotion_id}/events",
        json={"event_type": "interaction"},
    ).json() == {"recorded": True}

    _authenticate(client, session_factory, owner_id)
    owner_orders = client.get("/api/v1/featured/orders")
    assert owner_orders.status_code == 200
    assert owner_orders.json()[0]["fulfillment_status"] == "fulfilled"
    with session_factory() as db:
        promotion = db.get(FeaturedPromotion, promotion_id)
        now = datetime.now(timezone.utc)
        promotion.starts_at = now - timedelta(days=3)
        promotion.expires_at = now - timedelta(days=1)
        db.commit()
    expired_search = client.get(
        "/api/v1/discovery/properties",
        params={
            "city": "Lilongwe",
            "district": "Area 3",
            "neighborhood": "Old Town",
        },
    )
    assert next(item for item in expired_search.json() if item["id"] == 1)[
        "is_featured"
    ] is False
    assert client.post(
        f"/api/v1/featured/promotions/{promotion_id}/events",
        json={"event_type": "view"},
    ).status_code == 404
    _authenticate(client, session_factory, admin_id)
    admin_promotions = client.get("/api/v1/admin/featured/promotions")
    assert admin_promotions.json()[0]["status"] == "expired"


def test_homepage_inventory_admin_controls_and_explicit_cancellation(
    featured_environment,
):
    client, session_factory, owner_id, admin_id = featured_environment
    assert client.get("/api/v1/discovery/featured/homepage").status_code == 401
    assert client.post(
        "/api/v1/admin/listings/1/hide",
        json={"reason": "Only moderators can hide listings."},
    ).status_code == 401
    assert client.post(
        "/api/v1/admin/listings/1/restore",
        json={"reason": "Only moderators can restore listings."},
    ).status_code == 401
    _authenticate(client, session_factory, owner_id)
    assert client.get("/api/v1/discovery/featured/homepage").status_code == 200

    first_order = _create_order(client, listing_id=1, package_id=2, target=False)
    second_order = _create_order(client, listing_id=2, package_id=2, target=False)
    assert first_order.status_code == 201
    assert second_order.status_code == 201
    assert _send_signed_payment(
        client,
        order_id=first_order.json()["id"],
        amount="5000.00",
        reference="homepage-reference-1",
    ).status_code == 200
    assert _send_signed_payment(
        client,
        order_id=second_order.json()["id"],
        amount="5000.00",
        reference="homepage-reference-2",
    ).status_code == 200

    homepage = client.get("/api/v1/discovery/featured/homepage")
    assert homepage.status_code == 200
    assert [listing["id"] for listing in homepage.json()] == [1]
    assert homepage.json()[0]["featured_placement"] == "homepage"
    with session_factory() as db:
        blocked_order = db.get(FeaturedPromotionOrder, second_order.json()["id"])
        assert blocked_order.payment_status == "paid"
        assert blocked_order.fulfillment_status == "blocked"

    _authenticate(client, session_factory, admin_id)
    admin_promotions = client.get("/api/v1/admin/featured/promotions")
    assert admin_promotions.status_code == 200
    promotion_id = admin_promotions.json()[0]["id"]
    cancelled = client.post(
        f"/api/v1/admin/featured/promotions/{promotion_id}/cancel",
        json={"reason": "End this paid placement at advertiser request."},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancelled_by_user_id"] == admin_id
    cancellation_log = client.get("/api/v1/admin/action-logs").json()[0]
    assert cancellation_log["action"] == "cancel"
    assert cancellation_log["entity_type"] == "featured_promotion"
    assert cancellation_log["entity_id"] == str(promotion_id)
    assert cancellation_log["after_data"]["status"] == "cancelled"
    assert client.get("/api/v1/discovery/featured/homepage").json() == []
    assert _send_signed_payment(
        client,
        order_id=second_order.json()["id"],
        amount="5000.00",
        reference="homepage-reference-2",
    ).status_code == 200
    with session_factory() as db:
        listing = db.get(Property, 2)
        listing.moderator_hidden = True
        db.commit()
    assert client.get("/api/v1/discovery/featured/homepage").json() == []
    with session_factory() as db:
        listing = db.get(Property, 2)
        listing.moderator_hidden = False
        db.commit()
    assert [
        listing["id"]
        for listing in client.get("/api/v1/discovery/featured/homepage").json()
    ] == [2]

    settings_response = client.patch(
        "/api/v1/admin/featured/settings",
        json={"homepage_inventory_limit": None},
    )
    assert settings_response.status_code == 200
    assert settings_response.json()["homepage_inventory_limit"] is None
    settings_log = client.get("/api/v1/admin/action-logs").json()[0]
    assert settings_log["entity_type"] == "featured_settings"
    assert settings_log["before_data"]["homepage_inventory_limit"] == 1
    assert settings_log["after_data"]["homepage_inventory_limit"] is None


def test_admin_package_pricing_requires_homepage_tier_to_be_higher(
    featured_environment,
):
    client, session_factory, owner_id, admin_id = featured_environment
    _authenticate(client, session_factory, owner_id)
    assert client.post(
        "/api/v1/admin/featured/packages",
        json={
            "placement_type": "area",
            "duration": "monthly",
            "price": "25000.00",
        },
    ).status_code == 403

    _authenticate(client, session_factory, admin_id)
    area_package = client.post(
        "/api/v1/admin/featured/packages",
        json={
            "placement_type": "area",
            "duration": "monthly",
            "price": "25000.00",
        },
    )
    assert area_package.status_code == 201
    invalid_homepage_price = client.post(
        "/api/v1/admin/featured/packages",
        json={
            "placement_type": "homepage",
            "duration": "monthly",
            "price": "25000.00",
        },
    )
    assert invalid_homepage_price.status_code == 422
    valid_homepage_price = client.post(
        "/api/v1/admin/featured/packages",
        json={
            "placement_type": "homepage",
            "duration": "monthly",
            "price": "30000.00",
            "is_available": True,
        },
    )
    assert valid_homepage_price.status_code == 201
    with session_factory() as db:
        audit_entries = list(
            db.execute(
                select(AdminActionLog).where(
                    AdminActionLog.entity_type == "featured_package"
                )
            ).scalars()
        )
    assert len(audit_entries) == 2
    assert {
        (entry.actor_id, entry.action, entry.entity_id)
        for entry in audit_entries
    } == {
        (admin_id, "create", str(area_package.json()["id"])),
        (admin_id, "create", str(valid_homepage_price.json()["id"])),
    }
    update = client.patch(
        f"/api/v1/admin/featured/packages/{area_package.json()['id']}",
        json={"is_available": True},
    )
    assert update.status_code == 200
    update_log = client.get("/api/v1/admin/action-logs").json()[0]
    assert update_log["action"] == "update"
    assert update_log["entity_type"] == "featured_package"
    assert update_log["before_data"]["is_available"] is False
    assert update_log["after_data"]["is_available"] is True
    assert valid_homepage_price.json()["is_available"] is True


def test_paid_order_does_not_activate_when_listing_is_no_longer_published(
    featured_environment,
):
    client, session_factory, owner_id, _ = featured_environment
    _authenticate(client, session_factory, owner_id)
    order = _create_order(client, listing_id=1, package_id=1)
    assert order.status_code == 201
    with session_factory() as db:
        listing = db.get(Property, 1)
        listing.status = PropertyStatus.PAUSED.value
        db.commit()

    payment = _send_signed_payment(client, order_id=order.json()["id"])
    assert payment.status_code == 200
    with session_factory() as db:
        paid_order = db.get(FeaturedPromotionOrder, order.json()["id"])
        promotion = db.execute(
            select(FeaturedPromotion.id).where(
                FeaturedPromotion.listing_id == 1
            )
        ).scalar_one_or_none()
    assert paid_order.payment_status == "paid"
    assert paid_order.fulfillment_status == "blocked"
    assert promotion is None
