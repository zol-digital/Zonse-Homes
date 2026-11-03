from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints.properties import router as properties_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.reference_data import (
    admin_router as admin_reference_router,
    router as reference_router,
)
from app.config import settings
from app.database import Base, get_db
from app.models.identity import UserRole
from app.models.reference_data import DEFAULT_PROPERTY_CATEGORIES, PropertyCategory
from app.models.user import User
from app.security.sessions import create_user_session


@pytest.fixture
def reference_data_environment(monkeypatch):
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
        users = {
            role: User(
                email=f"{role}@reference-data.example.test",
                canonical_email=f"{role}@reference-data.example.test",
                hashed_password="sha256:placeholder",
                full_name=role.title(),
                account_status="active",
                email_verified_at=datetime.now(timezone.utc),
                is_active=True,
            )
            for role in ("admin", "moderator", "owner")
        }
        db.add_all(users.values())
        db.flush()
        db.add_all(
            UserRole(user_id=user.id, role=role)
            for role, user in users.items()
        )
        db.commit()
        user_ids = {role: user.id for role, user in users.items()}

    app = FastAPI()
    app.include_router(properties_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(reference_router, prefix="/api/v1")
    app.include_router(admin_reference_router, prefix="/api/v1")

    def override_get_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, session_factory, user_ids

    app.dependency_overrides.clear()
    engine.dispose()


def _authenticate(client, session_factory, user_id: int) -> None:
    with session_factory() as db:
        token, _ = create_user_session(db, user_id=user_id)
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)
    client.headers.update({"Origin": "http://testserver"})


def _listing_payload(property_type: str = "house") -> dict[str, str]:
    return {
        "title": "Reference data listing",
        "price": "250000.00",
        "city": "Lilongwe",
        "property_type": property_type,
    }


def test_categories_are_admin_managed_and_control_new_listing_types(
    reference_data_environment,
):
    client, session_factory, user_ids = reference_data_environment
    assert client.get("/api/v1/reference/categories").status_code == 200
    assert client.post(
        "/api/v1/admin/reference/categories",
        json={"slug": "tiny-home", "name": "Tiny Home"},
    ).status_code == 401

    _authenticate(client, session_factory, user_ids["moderator"])
    assert client.get("/api/v1/admin/reference/categories").status_code == 403

    _authenticate(client, session_factory, user_ids["admin"])
    created = client.post(
        "/api/v1/admin/reference/categories",
        json={"slug": "tiny-home", "name": "Tiny Home"},
    )
    assert created.status_code == 201
    assert created.json()["is_active"] is True
    assert client.post(
        "/api/v1/admin/reference/categories",
        json={"slug": "tiny-home", "name": "Duplicate"},
    ).status_code == 409

    _authenticate(client, session_factory, user_ids["owner"])
    assert client.post(
        "/api/v1/properties",
        json=_listing_payload("unconfigured"),
    ).status_code == 422
    listing = client.post("/api/v1/properties", json=_listing_payload("tiny-home"))
    assert listing.status_code == 201
    listing_id = listing.json()["id"]

    _authenticate(client, session_factory, user_ids["admin"])
    disabled = client.patch(
        "/api/v1/admin/reference/categories/tiny-home",
        json={"is_active": False},
    )
    assert disabled.status_code == 200
    action_logs = client.get("/api/v1/admin/action-logs")
    assert action_logs.status_code == 200
    assert [
        (entry["action"], entry["entity_type"], entry["entity_id"])
        for entry in action_logs.json()
    ] == [
        ("update", "property_category", "tiny-home"),
        ("create", "property_category", "tiny-home"),
    ]
    assert action_logs.json()[0]["before_data"] == {
        "name": "Tiny Home",
        "is_active": True,
    }
    assert action_logs.json()[0]["after_data"] == {
        "name": "Tiny Home",
        "is_active": False,
    }
    public_categories = client.get("/api/v1/reference/categories").json()
    assert "tiny-home" not in {category["slug"] for category in public_categories}
    assert "tiny-home" in {
        category["slug"]
        for category in client.get("/api/v1/admin/reference/categories").json()
    }

    _authenticate(client, session_factory, user_ids["owner"])
    assert client.post(
        "/api/v1/properties",
        json=_listing_payload("tiny-home"),
    ).status_code == 422
    assert client.patch(
        f"/api/v1/properties/{listing_id}",
        json={"property_type": "tiny-home"},
    ).status_code == 422
    assert client.patch(
        f"/api/v1/properties/{listing_id}",
        json={"title": "Existing listings remain editable"},
    ).status_code == 200


def test_locations_enforce_hierarchy_and_only_active_records_are_public(
    reference_data_environment,
):
    client, session_factory, user_ids = reference_data_environment
    _authenticate(client, session_factory, user_ids["admin"])

    region = client.post(
        "/api/v1/admin/reference/locations",
        json={
            "slug": "central-region",
            "name": "Central Region",
            "kind": "region",
            "aliases": ["Central"],
        },
    )
    assert region.status_code == 201
    region_id = region.json()["id"]
    district = client.post(
        "/api/v1/admin/reference/locations",
        json={
            "slug": "lilongwe-district",
            "name": "Lilongwe",
            "kind": "district",
            "parent_id": region_id,
        },
    )
    assert district.status_code == 201
    district_id = district.json()["id"]
    city = client.post(
        "/api/v1/admin/reference/locations",
        json={
            "slug": "lilongwe-city",
            "name": "Lilongwe",
            "kind": "city",
            "parent_id": district_id,
        },
    )
    assert city.status_code == 201
    city_id = city.json()["id"]
    neighborhood = client.post(
        "/api/v1/admin/reference/locations",
        json={
            "slug": "area-3",
            "name": "Area 3",
            "kind": "neighborhood",
            "parent_id": city_id,
        },
    )
    assert neighborhood.status_code == 201

    invalid_parent = client.post(
        "/api/v1/admin/reference/locations",
        json={
            "slug": "invalid-city",
            "name": "Invalid City",
            "kind": "city",
            "parent_id": region_id,
        },
    )
    assert invalid_parent.status_code == 422
    assert client.patch(
        f"/api/v1/admin/reference/locations/{region_id}",
        json={"is_active": False},
    ).status_code == 409

    public_city = client.get(
        f"/api/v1/reference/locations?kind=city&parent_id={district_id}"
    )
    assert public_city.status_code == 200
    assert [location["id"] for location in public_city.json()] == [city_id]

    assert client.patch(
        f"/api/v1/admin/reference/locations/{neighborhood.json()['id']}",
        json={"is_active": False},
    ).status_code == 200
    assert client.patch(
        f"/api/v1/admin/reference/locations/{region_id}",
        json={"is_active": False},
    ).status_code == 409

    for location_id in (city_id, district_id, region_id):
        response = client.patch(
            f"/api/v1/admin/reference/locations/{location_id}",
            json={"is_active": False},
        )
        assert response.status_code == 200
    assert client.get("/api/v1/reference/locations").json() == []
    location_logs = client.get("/api/v1/admin/action-logs").json()
    assert len(location_logs) == 8
    assert {
        entry["entity_type"] for entry in location_logs
    } == {"location_reference"}
