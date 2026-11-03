from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.database import Base, get_db
from app.main import app
from app.models.identity import (
    BusinessVerification,
    Organization,
    OrganizationMembership,
)
from app.models.property import Property, PropertyStatus
from app.models.reference_data import DEFAULT_PROPERTY_CATEGORIES, PropertyCategory
from app.models.user import User


@pytest.fixture
def discovery_client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, expire_on_commit=False)

    with test_session() as db:
        db.add_all(
            PropertyCategory(slug=slug, name=name)
            for slug, name in DEFAULT_PROPERTY_CATEGORIES.items()
        )
        db.add(
            User(
                id=1,
                email="owner@example.test",
                hashed_password="private-hash",
                full_name="Private Account Name",
                phone_number="private-account-phone",
            )
        )
        db.commit()

    def override_get_db():
        with test_session() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)
    try:
        yield TestClient(app), test_session
    finally:
        engine.dispose()


def _add_listing(
    session_factory,
    *,
    listing_id: int,
    created_at: datetime,
    status: str = PropertyStatus.PUBLISHED.value,
    **overrides,
) -> None:
    values = {
        "id": listing_id,
        "title": "Garden home",
        "description": "Quiet home by the lake",
        "price": Decimal("1000.00"),
        "currency": "MWK",
        "city": "Lilongwe",
        "property_type": "house",
        "intent": "sale",
        "bedrooms": 3,
        "bathrooms": 2,
        "negotiable": False,
        "rental_period": None,
        "deposit": None,
        "floor_area": None,
        "floor_area_unit": "sqm",
        "land_area": None,
        "land_area_unit": "sqm",
        "amenities": [],
        "utilities": [],
        "district": "Area 3",
        "neighborhood": "Old Town",
        "available_from": None,
        "advertiser_name": "Public Advertiser",
        "contact_phone": "+265 999 123456",
        "contact_email": "advertiser@example.test",
        "show_contact_details": False,
        "owner_id": 1,
        "cover_image_id": None,
        "status": status,
        "created_at": created_at,
        "updated_at": created_at,
    }
    values.update(overrides)
    with session_factory() as db:
        db.add(Property(**values))
        db.commit()


def _seed_published_listings(session_factory) -> None:
    _add_listing(
        session_factory,
        listing_id=1,
        created_at=datetime(2026, 10, 29, 10, tzinfo=timezone.utc),
    )
    _add_listing(
        session_factory,
        listing_id=2,
        created_at=datetime(2026, 10, 30, 11, tzinfo=timezone.utc),
        title="Central apartment",
        description="Bright rental near shops",
        price=Decimal("2000.00"),
        city="Blantyre",
        property_type="flat",
        intent="rent",
        bedrooms=2,
        bathrooms=1,
        district="Ndirande",
        neighborhood="Namiwawa",
    )
    _add_listing(
        session_factory,
        listing_id=3,
        created_at=datetime(2026, 10, 30, 11, tzinfo=timezone.utc),
        title="Residential plot",
        description="Open lot",
        price=Decimal("3000.00"),
        property_type="plot",
        bedrooms=None,
        bathrooms=None,
        district="Area 1",
        neighborhood="City Center",
    )


def test_anonymous_visitor_can_retrieve_published_properties_without_credentials(
    discovery_client,
):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    response = client.get("/api/v1/discovery/properties")

    assert response.status_code == 200
    assert [listing["id"] for listing in response.json()] == [3, 2, 1]
    assert all(listing["verification_labels"] == [] for listing in response.json())
    assert not client.cookies


def test_public_verification_label_reflects_only_confirmed_account_email(
    discovery_client,
):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    with session_factory() as db:
        owner = db.get(User, 1)
        owner.email_verified_at = datetime.now(timezone.utc)
        owner.phone_number = "+265991000001"
        owner.phone_verified_at = datetime.now(timezone.utc)
        organization = Organization(
            registered_business_name="Example Property Company",
            business_type="property_company",
            registration_number="REG-001",
            country_of_registration="MW",
            business_contact_email="company@example.test",
            account_status="active",
        )
        db.add(organization)
        db.flush()
        db.add_all(
            [
                OrganizationMembership(
                    organization_id=organization.id,
                    user_id=owner.id,
                    membership_role="authorized_representative",
                ),
                BusinessVerification(
                    organization_id=organization.id,
                    current_status="certified",
                ),
            ]
        )
        db.commit()

    response = client.get("/api/v1/discovery/properties")

    assert response.status_code == 200
    listings = response.json()
    assert all(
        listing["verification_labels"] == ["Account email confirmed"]
        for listing in listings
    )
    assert all(
        label not in {"Phone confirmed", "Business certified", "Property verified"}
        for listing in listings
        for label in listing["verification_labels"]
    )
    assert all(
        {
            "email",
            "email_verified_at",
            "phone_number",
            "phone_verified_at",
            "private_storage_ref",
            "verification_documents",
        }.isdisjoint(listing)
        for listing in listings
    )


def test_discovery_openapi_is_public_and_advertiser_list_route_is_unchanged(
    discovery_client,
):
    client, _ = discovery_client

    specification = client.get("/api/v1/openapi.json").json()
    operation = specification["paths"]["/api/v1/discovery/properties"]["get"]
    parameter_names = {parameter["name"] for parameter in operation["parameters"]}
    response_ref = operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["items"]["$ref"]
    response_fields = specification["components"]["schemas"][
        response_ref.rsplit("/", 1)[-1]
    ]["properties"]

    assert "security" not in operation
    assert {"search", "intent", "property_type", "limit", "offset"} <= parameter_names
    assert {
        "status",
        "owner_id",
        "show_contact_details",
        "cover_image_id",
    }.isdisjoint(response_fields)
    assert "verification_labels" in response_fields
    assert {
        "email",
        "email_verified_at",
        "phone_number",
        "phone_verified_at",
        "private_storage_ref",
        "verification_documents",
    }.isdisjoint(response_fields)
    advertiser_response = specification["components"]["schemas"]["PropertyResponse"][
        "properties"
    ]
    assert {
        "email_verified_at",
        "phone_verified_at",
        "private_storage_ref",
        "verification_documents",
    }.isdisjoint(advertiser_response)
    assert "/api/v1/properties" in specification["paths"]
    assert client.get("/api/v1/properties").status_code == 401


def test_discovery_excludes_every_non_published_status(discovery_client):
    client, session_factory = discovery_client
    for listing_id, listing_status in enumerate(PropertyStatus, start=1):
        _add_listing(
            session_factory,
            listing_id=listing_id,
            created_at=datetime(2026, 10, 30, 12, tzinfo=timezone.utc),
            status=listing_status.value,
        )

    response = client.get("/api/v1/discovery/properties")

    assert response.status_code == 200
    assert [listing["id"] for listing in response.json()] == [
        next(
            listing_id
            for listing_id, listing_status in enumerate(PropertyStatus, start=1)
            if listing_status is PropertyStatus.PUBLISHED
        )
    ]


def test_discovery_excludes_moderator_hidden_published_listings(discovery_client):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)
    with session_factory() as db:
        listing = db.get(Property, 2)
        listing.moderator_hidden = True
        db.commit()

    response = client.get("/api/v1/discovery/properties")

    assert response.status_code == 200
    assert [listing["id"] for listing in response.json()] == [3, 1]


@pytest.mark.parametrize(
    ("search", "expected_id"),
    [
        ("Garden home", 1),
        ("lake", 1),
        ("Blantyre", 2),
        ("Area 3", 1),
        ("Old Town", 1),
    ],
)
def test_search_matches_title_description_and_location(
    discovery_client, search, expected_id
):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    response = client.get(
        "/api/v1/discovery/properties",
        params={"search": search},
    )

    assert response.status_code == 200
    assert [listing["id"] for listing in response.json()] == [expected_id]


@pytest.mark.parametrize(
    ("filters", "expected_ids"),
    [
        ({"intent": "rent"}, [2]),
        ({"property_type": "flat"}, [2]),
        ({"city": "lilongwe"}, [3, 1]),
        ({"district": "ndirande"}, [2]),
        ({"neighborhood": "namiwawa"}, [2]),
        ({"bedrooms": 2}, [2]),
        ({"bathrooms": 2}, [1]),
    ],
)
def test_each_discovery_filter_works_independently(
    discovery_client, filters, expected_ids
):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    response = client.get("/api/v1/discovery/properties", params=filters)

    assert response.status_code == 200
    assert [listing["id"] for listing in response.json()] == expected_ids


@pytest.mark.parametrize(
    ("filters", "expected_ids"),
    [
        ({"min_price": "1000.00"}, [3, 2, 1]),
        ({"max_price": "1000.00"}, [1]),
        ({"min_price": "1000.00", "max_price": "1000.00"}, [1]),
    ],
)
def test_price_filters_include_boundaries(discovery_client, filters, expected_ids):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    response = client.get("/api/v1/discovery/properties", params=filters)

    assert response.status_code == 200
    assert [listing["id"] for listing in response.json()] == expected_ids


def test_discovery_filters_combine_together(discovery_client):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    response = client.get(
        "/api/v1/discovery/properties",
        params={
            "search": "Bright",
            "intent": "rent",
            "property_type": "flat",
            "city": "Blantyre",
            "district": "Ndirande",
            "neighborhood": "Namiwawa",
            "min_price": "2000.00",
            "max_price": "2000.00",
            "bedrooms": 2,
            "bathrooms": 1,
        },
    )

    assert response.status_code == 200
    assert [listing["id"] for listing in response.json()] == [2]


def test_discovery_pagination_is_newest_first_and_has_stable_tie_breaker(
    discovery_client,
):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    first_page = client.get(
        "/api/v1/discovery/properties",
        params={"limit": 2, "offset": 0},
    )
    second_page = client.get(
        "/api/v1/discovery/properties",
        params={"limit": 2, "offset": 2},
    )

    first_ids = [listing["id"] for listing in first_page.json()]
    second_ids = [listing["id"] for listing in second_page.json()]
    assert first_ids == [3, 2]
    assert second_ids == [1]
    assert set(first_ids).isdisjoint(second_ids)


def test_discovery_returns_empty_list_when_nothing_matches(discovery_client):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    unmatched = client.get(
        "/api/v1/discovery/properties",
        params={"search": "No matching home"},
    )
    wildcard = client.get(
        "/api/v1/discovery/properties",
        params={"search": "%"},
    )

    assert unmatched.status_code == 200
    assert unmatched.json() == []
    assert wildcard.status_code == 200
    assert wildcard.json() == []


def test_public_response_suppresses_private_contacts_and_owner_account_data(
    discovery_client,
):
    client, session_factory = discovery_client
    _add_listing(
        session_factory,
        listing_id=1,
        created_at=datetime(2026, 10, 30, 12, tzinfo=timezone.utc),
    )

    listing = client.get("/api/v1/discovery/properties").json()[0]

    assert listing["advertiser_name"] is None
    assert listing["contact_phone"] is None
    assert listing["contact_email"] is None
    for private_field in (
        "show_contact_details",
        "owner_id",
        "owner",
        "status",
        "cover_image_id",
        "hashed_password",
        "email",
        "phone_number",
        "account_status",
    ):
        assert private_field not in listing


def test_public_contact_values_are_returned_only_when_visibility_is_enabled(
    discovery_client,
):
    client, session_factory = discovery_client
    _add_listing(
        session_factory,
        listing_id=1,
        created_at=datetime(2026, 10, 30, 12, tzinfo=timezone.utc),
        show_contact_details=True,
    )

    listing = client.get("/api/v1/discovery/properties").json()[0]

    assert listing["advertiser_name"] == "Public Advertiser"
    assert listing["contact_phone"] == "+265 999 123456"
    assert listing["contact_email"] == "advertiser@example.test"


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
        "search=%20%20",
        "intent=purchase",
        "property_type=castle",
        "city=%20%20",
        "min_price=-1",
        "max_price=10000000000",
        "min_price=2000&max_price=1000",
        "bedrooms=-1",
        "bathrooms=-1",
    ],
)
def test_invalid_discovery_filters_and_pagination_return_validation_errors(
    discovery_client, query
):
    client, _ = discovery_client

    response = client.get(f"/api/v1/discovery/properties?{query}")

    assert response.status_code == 422


def test_discovery_endpoint_is_read_only(discovery_client):
    client, session_factory = discovery_client
    _seed_published_listings(session_factory)

    assert client.get("/api/v1/discovery/properties").status_code == 200
    assert client.post("/api/v1/discovery/properties").status_code == 405
    assert client.patch("/api/v1/discovery/properties").status_code == 405
    assert client.delete("/api/v1/discovery/properties").status_code == 405

    with session_factory() as db:
        listing = db.execute(select(Property).where(Property.id == 1)).scalar_one()
        assert listing.status == PropertyStatus.PUBLISHED.value
        assert listing.title == "Garden home"
