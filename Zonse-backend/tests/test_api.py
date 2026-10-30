from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.router import router as api_router
from app.exception_handlers import register_exception_handlers
from app.models.image import PropertyImage
from app.main import app
from app.models.property import Property, validate_property_status_transition
from app.schemas.property import PropertyCreate, PropertyResponse, PropertyUpdate


def test_application_import_registers_single_versioned_health_router():
    paths = [
        route.path
        for route in app.routes
        if route.path in {"/api/v1/health", "/api/v1/ready"}
    ]

    assert paths.count("/api/v1/health") == 1
    assert paths.count("/api/v1/ready") == 1
    assert api_router.prefix == ""
    assert "/api/v1/health" in app.openapi()["paths"]
    assert "/api/v1/ready" in app.openapi()["paths"]
    assert {
        "get",
        "post",
    }.issubset(app.openapi()["paths"]["/api/v1/properties"])
    assert "/api/v1/properties/{property_id}/submit" in app.openapi()["paths"]
    assert "/api/v1/properties/{property_id}/archive" in app.openapi()["paths"]


def test_property_create_schema_validates_required_fields_and_decimal_money():
    payload = PropertyCreate(
        title="  House  ",
        price="1234.50",
        city=" Lilongwe ",
        property_type="house",
    )

    assert payload.title == "House"
    assert payload.city == "Lilongwe"
    assert payload.price == Decimal("1234.50")
    assert payload.currency == "MWK"


def test_property_create_schema_rejects_invalid_price_and_unknown_fields():
    try:
        PropertyCreate(
            title="House",
            price="-10",
            city="Lilongwe",
            property_type="house",
            owner_id=42,
            status="published",
        )
    except ValueError as exc:
        assert "price" in str(exc)
        assert "owner_id" in str(exc)
        assert "status" in str(exc)
    else:
        raise AssertionError("Invalid property input must be rejected")


def test_property_create_schema_validates_listing_fields_and_private_contact_default():
    payload = PropertyCreate(
        title="Flat",
        price="200000.00",
        city="Lilongwe",
        property_type="flat",
        intent="rent",
        rental_period="month",
        deposit="50000.00",
        floor_area="85.5",
        floor_area_unit="sqm",
        land_area="0.25",
        land_area_unit="acre",
        amenities=[" Balcony ", "Parking"],
        utilities=["Water", "Electricity"],
        available_from="2026-11-01",
        advertiser_name="A. Owner",
        contact_phone="+265 999 123456",
    )

    assert payload.intent == "rent"
    assert payload.rental_period == "month"
    assert payload.deposit == Decimal("50000.00")
    assert payload.floor_area == Decimal("85.5")
    assert payload.land_area == Decimal("0.25")
    assert payload.amenities == ["Balcony", "Parking"]
    assert payload.available_from == date(2026, 11, 1)
    assert payload.show_contact_details is False


def test_property_schemas_reject_unknown_listing_values_and_status_updates():
    with pytest.raises(ValueError):
        PropertyCreate(
            title="House",
            price="1000",
            city="Lilongwe",
            property_type="castle",
        )

    with pytest.raises(ValueError):
        PropertyUpdate(status="published")


def test_property_rental_terms_match_listing_intent():
    with pytest.raises(ValueError, match="only valid for rental listings"):
        PropertyCreate(
            title="House",
            price="1000",
            city="Lilongwe",
            property_type="house",
            intent="sale",
            rental_period="month",
        )

    with pytest.raises(ValueError, match="requires clearing"):
        PropertyUpdate(intent="sale")

    update = PropertyUpdate(intent="sale", rental_period=None, deposit=None)
    assert update.model_dump(exclude_unset=True) == {
        "intent": "sale",
        "rental_period": None,
        "deposit": None,
    }


def test_property_update_schema_supports_partial_updates():
    update = PropertyUpdate(price="2000.25")

    assert update.model_dump(exclude_unset=True) == {"price": Decimal("2000.25")}


def test_property_update_schema_rejects_empty_and_null_required_updates():
    for payload in ({}, {"city": None}):
        try:
            PropertyUpdate.model_validate(payload)
        except ValueError:
            continue
        raise AssertionError("Invalid partial update must be rejected")


def test_property_response_serializes_only_public_model_fields():
    listing = Property(
        id=1,
        title="House",
        description=None,
        price=Decimal("1000.00"),
        currency="MWK",
        city="Lilongwe",
        property_type="house",
        intent="sale",
        bedrooms=2,
        bathrooms=1,
        negotiable=False,
        rental_period=None,
        deposit=None,
        floor_area=None,
        floor_area_unit="sqm",
        land_area=None,
        land_area_unit="sqm",
        amenities=[],
        utilities=[],
        district=None,
        neighborhood=None,
        available_from=None,
        advertiser_name="Private Owner",
        contact_phone="+265 999 123456",
        contact_email="owner@example.test",
        show_contact_details=False,
        owner_id=99,
        cover_image_id=None,
        status="draft",
        created_at=datetime(2026, 10, 30, tzinfo=timezone.utc),
        updated_at=datetime(2026, 10, 30, tzinfo=timezone.utc),
    )

    response = PropertyResponse.model_validate(listing)

    assert response.price == Decimal("1000.00")
    assert response.advertiser_name is None
    assert response.contact_phone is None
    assert response.contact_email is None
    assert "owner_id" not in response.model_dump()
    assert "hashed_password" not in response.model_dump()
    assert "show_contact_details" not in response.model_dump()


def test_property_response_exposes_contact_only_when_enabled():
    listing = Property(
        id=1,
        title="House",
        description=None,
        price=Decimal("1000.00"),
        currency="MWK",
        city="Lilongwe",
        property_type="house",
        intent="sale",
        bedrooms=None,
        bathrooms=None,
        negotiable=False,
        rental_period=None,
        deposit=None,
        floor_area=None,
        floor_area_unit="sqm",
        land_area=None,
        land_area_unit="sqm",
        amenities=[],
        utilities=[],
        district=None,
        neighborhood=None,
        available_from=None,
        advertiser_name="Public Owner",
        contact_phone="+265 999 123456",
        contact_email="owner@example.test",
        show_contact_details=True,
        owner_id=99,
        cover_image_id=None,
        status="published",
    )

    response = PropertyResponse.model_validate(listing)

    assert response.advertiser_name == "Public Owner"
    assert response.contact_phone == "+265 999 123456"
    assert response.contact_email == "owner@example.test"
    assert response.model_dump()["status"] == "published"


def test_property_response_preserves_legacy_property_types_and_nullable_image_flags():
    listing = Property(
        id=1,
        title="Legacy listing",
        description=None,
        price=Decimal("1000.00"),
        currency="MWK",
        city="Lilongwe",
        property_type="legacy-type",
        intent="sale",
        bedrooms=None,
        bathrooms=None,
        negotiable=False,
        rental_period=None,
        deposit=None,
        floor_area=None,
        floor_area_unit="sqm",
        land_area=None,
        land_area_unit="sqm",
        amenities=[],
        utilities=[],
        district=None,
        neighborhood=None,
        available_from=None,
        advertiser_name=None,
        contact_phone=None,
        contact_email=None,
        show_contact_details=False,
        cover_image_id=None,
        owner_id=99,
        status="draft",
        created_at=None,
        updated_at=None,
        images=[
            PropertyImage(
                id=1,
                image_url="https://example.test/legacy.jpg",
                is_primary=None,
                created_at=None,
            )
        ],
    )

    response = PropertyResponse.model_validate(listing)

    assert response.property_type == "legacy-type"
    assert response.images[0].is_primary is None


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("draft", "pending_review"),
        ("published", "paused"),
        ("published", "sold"),
        ("removed", "archived"),
    ],
)
def test_property_status_transition_accepts_approved_lifecycle_edges(current, target):
    validate_property_status_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("draft", "published"),
        ("sold", "published"),
        ("archived", "draft"),
        ("unknown", "draft"),
    ],
)
def test_property_status_transition_rejects_invalid_edges(current, target):
    with pytest.raises(ValueError):
        validate_property_status_transition(current, target)


def _client_with_error_test_routes() -> TestClient:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/missing")
    def missing():
        raise HTTPException(status_code=404, detail="database password")

    @test_app.get("/conflict")
    def conflict():
        raise IntegrityError("statement", "private parameters", Exception("secret"))

    @test_app.get("/database-error")
    def database_error():
        raise SQLAlchemyError("private connection URL")

    @test_app.get("/unexpected")
    def unexpected():
        raise RuntimeError("private token")

    @test_app.get("/validate")
    def validate(count: int):
        return {"count": count}

    return TestClient(test_app, raise_server_exceptions=False)


def test_not_found_error_uses_safe_consistent_response():
    response = _client_with_error_test_routes().get("/missing")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Resource not found"}
    }
    assert "database password" not in response.text


def test_integrity_error_returns_conflict_without_database_details():
    response = _client_with_error_test_routes().get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "conflict", "message": "Resource conflict"}
    }
    assert "private parameters" not in response.text


def test_database_and_unexpected_errors_do_not_expose_internal_details(caplog):
    client = _client_with_error_test_routes()

    database_response = client.get("/database-error")
    unexpected_response = client.get("/unexpected")

    assert database_response.status_code == 503
    assert unexpected_response.status_code == 500
    assert "private connection URL" not in database_response.text
    assert "private token" not in unexpected_response.text
    assert "private connection URL" not in caplog.text
    assert "private token" not in caplog.text
    assert unexpected_response.json() == {
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred",
        }
    }


def test_validation_error_is_consistent_and_does_not_echo_input():
    response = _client_with_error_test_routes().get("/validate?count=not-an-int")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"][0]["location"] == ["query", "count"]
    assert "not-an-int" not in response.text
