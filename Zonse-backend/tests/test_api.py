from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.router import router as api_router
from app.exception_handlers import register_exception_handlers
from app.main import app
from app.models.property import Property
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
        )
    except ValueError as exc:
        assert "price" in str(exc)
        assert "owner_id" in str(exc)
    else:
        raise AssertionError("Invalid property input must be rejected")


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
        bedrooms=2,
        bathrooms=1,
        owner_id=99,
        created_at=datetime(2026, 10, 30, tzinfo=timezone.utc),
    )

    response = PropertyResponse.model_validate(listing)

    assert response.price == Decimal("1000.00")
    assert "owner_id" not in response.model_dump()
    assert "hashed_password" not in response.model_dump()


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
