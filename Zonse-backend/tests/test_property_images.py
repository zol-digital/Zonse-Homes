from datetime import datetime, timezone
from io import BytesIO
import re

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.properties import router as properties_router
from app.config import settings
from app.database import Base, get_db
from app.exception_handlers import register_exception_handlers
from app.models.identity import UserRole
from app.models.image import PropertyImage
from app.models.property import Property
from app.models.reference_data import DEFAULT_PROPERTY_CATEGORIES, PropertyCategory
from app.models.user import User
from app.security.sessions import create_user_session

_COOKIE_NAME = "zonse_session"
_ORIGIN_HEADERS = {"Origin": "http://testserver"}


@pytest.fixture
def media_environment(tmp_path, monkeypatch):
    upload_directory = tmp_path / "property-media"
    monkeypatch.setattr(settings, "UPLOAD_DIR", upload_directory)
    monkeypatch.setattr(settings, "MAX_IMAGE_UPLOAD_BYTES", 2048)
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
    with session_factory() as db:
        db.add_all(
            PropertyCategory(slug=slug, name=name)
            for slug, name in DEFAULT_PROPERTY_CATEGORIES.items()
        )
        db.commit()

    test_app = FastAPI()
    register_exception_handlers(test_app)
    test_app.include_router(auth_router, prefix="/api/v1")
    test_app.include_router(properties_router, prefix="/api/v1")
    test_app.mount(
        "/uploads",
        StaticFiles(directory=str(upload_directory), check_dir=False),
        name="uploads",
    )

    def override_get_db():
        with session_factory() as db:
            yield db

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as client:
        yield client, session_factory, upload_directory, test_app

    test_app.dependency_overrides.clear()
    engine.dispose()


def _create_user(session_factory, *, email, role="owner"):
    with session_factory() as db:
        user = User(
            email=email,
            canonical_email=email,
            hashed_password="test-hash",
            account_status="active",
            is_active=True,
            email_verified_at=datetime.now(timezone.utc),
            role="client",
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role=role))
        db.commit()
        return user.id


def _issue_cookie(client, session_factory, user_id):
    with session_factory() as db:
        token, _ = create_user_session(db, user_id=user_id)
    client.cookies.set(_COOKIE_NAME, token)


def _create_property(session_factory, owner_id, *, status="draft"):
    with session_factory() as db:
        listing = Property(
            title="Test property",
            price=100000,
            currency="MWK",
            city="Lilongwe",
            property_type="house",
            intent="sale",
            owner_id=owner_id,
            status=status,
        )
        db.add(listing)
        db.commit()
        return listing.id


def _image_bytes(image_format="PNG"):
    image = Image.new("RGB", (4, 3), (20, 120, 200))
    data = BytesIO()
    image.save(data, format=image_format)
    return data.getvalue()


def _upload(
    client,
    property_id,
    *,
    content=None,
    filename="house.png",
    content_type="image/png",
):
    return client.post(
        f"/api/v1/properties/{property_id}/images",
        files={
            "image_file": (
                filename,
                _image_bytes() if content is None else content,
                content_type,
            )
        },
        headers=_ORIGIN_HEADERS,
    )


def _owned_draft(media_environment, *, email="owner@example.test"):
    client, session_factory, upload_directory, test_app = media_environment
    owner_id = _create_user(session_factory, email=email)
    _issue_cookie(client, session_factory, owner_id)
    property_id = _create_property(session_factory, owner_id)
    return client, session_factory, upload_directory, test_app, owner_id, property_id


@pytest.mark.parametrize(
    ("image_format", "filename", "expected_extension"),
    (
        ("JPEG", "house.jpg", ".jpg"),
        ("PNG", "house.png", ".png"),
        ("WEBP", "house.webp", ".webp"),
    ),
)
def test_upload_stores_supported_image_content_and_serves_it(
    media_environment,
    image_format,
    filename,
    expected_extension,
):
    client, session_factory, upload_directory, _, _, property_id = _owned_draft(
        media_environment
    )

    response = _upload(
        client,
        property_id,
        content=_image_bytes(image_format),
        filename=filename,
        content_type="application/octet-stream",
    )

    assert response.status_code == 201
    image = response.json()
    stored_name = image["image_url"].removeprefix("/uploads/")
    assert re.fullmatch(r"[0-9a-f]{32}" + re.escape(expected_extension), stored_name)
    assert image["is_primary"] is False
    assert str(upload_directory) not in response.text
    served_image = client.get(image["image_url"])
    assert served_image.status_code == 200
    assert served_image.content == _image_bytes(image_format)

    with session_factory() as db:
        stored_record = db.get(PropertyImage, image["id"])
        assert stored_record.property_id == property_id


def test_upload_uses_detected_format_instead_of_mime_type_or_filename(
    media_environment,
):
    client, _, upload_directory, _, _, property_id = _owned_draft(media_environment)

    response = _upload(
        client,
        property_id,
        content=_image_bytes("PNG"),
        filename="../../outside.jpg",
        content_type="text/plain",
    )

    assert response.status_code == 201
    assert response.json()["image_url"].endswith(".png")
    assert ".." not in response.json()["image_url"]
    assert not (upload_directory.parent / "outside.jpg").exists()


@pytest.mark.parametrize(
    ("filename", "content_type", "content", "expected_status"),
    (
        ("fake.png", "image/png", b"not an image", 400),
        ("broken.jpg", "image/jpeg", b"\x89PNG\r\n\x1a\nbroken", 400),
        ("empty.png", "image/png", b"", 400),
        ("animated.gif", "image/gif", None, 415),
        ("large.png", "image/png", b"x" * 2049, 413),
    ),
)
def test_upload_rejects_invalid_or_unsupported_content_without_files(
    media_environment,
    filename,
    content_type,
    content,
    expected_status,
):
    client, _, upload_directory, _, _, property_id = _owned_draft(media_environment)
    if filename == "animated.gif":
        content = _image_bytes("GIF")

    response = _upload(
        client,
        property_id,
        content=content,
        filename=filename,
        content_type=content_type,
    )

    assert response.status_code == expected_status
    assert not upload_directory.exists() or list(upload_directory.iterdir()) == []


def test_upload_requires_authentication_and_listing_manager_role(media_environment):
    client, session_factory, _, _, _, property_id = _owned_draft(media_environment)
    client.cookies.clear()

    assert _upload(client, property_id).status_code == 401

    seeker_id = _create_user(
        session_factory,
        email="seeker@example.test",
        role="seeker",
    )
    _issue_cookie(client, session_factory, seeker_id)
    assert _upload(client, property_id).status_code == 403


def test_image_retrieval_and_mutations_are_scoped_to_listing_owner(media_environment):
    client, session_factory, upload_directory, _, owner_id, owned_property_id = (
        _owned_draft(media_environment)
    )
    owned_image = _upload(client, owned_property_id).json()
    other_owner_id = _create_user(
        session_factory,
        email="another-owner@example.test",
    )
    other_property_id = _create_property(session_factory, other_owner_id)

    client.cookies.clear()
    _issue_cookie(client, session_factory, other_owner_id)
    foreign_upload = _upload(client, other_property_id)
    assert foreign_upload.status_code == 201
    foreign_image_id = foreign_upload.json()["id"]
    foreign_path = upload_directory / foreign_upload.json()["image_url"].split("/")[-1]

    client.cookies.clear()
    _issue_cookie(client, session_factory, owner_id)
    own_listing = client.get(f"/api/v1/properties/{owned_property_id}")
    assert own_listing.status_code == 200
    assert own_listing.json()["images"][0]["id"] == owned_image["id"]
    assert client.get(f"/api/v1/properties/{other_property_id}").status_code == 404
    assert _upload(client, other_property_id).status_code == 404
    assert client.put(
        f"/api/v1/properties/{other_property_id}/images/{foreign_image_id}/cover",
        headers=_ORIGIN_HEADERS,
    ).status_code == 404
    assert client.delete(
        f"/api/v1/properties/{other_property_id}/images/{foreign_image_id}",
        headers=_ORIGIN_HEADERS,
    ).status_code == 404

    with session_factory() as db:
        assert db.get(PropertyImage, foreign_image_id) is not None
    assert foreign_path.is_file()


def test_cover_selection_only_accepts_images_from_the_same_property(
    media_environment,
):
    client, session_factory, _, _, owner_id, first_property_id = _owned_draft(
        media_environment
    )
    second_property_id = _create_property(session_factory, owner_id)
    second_image = _upload(client, second_property_id).json()

    response = client.put(
        f"/api/v1/properties/{first_property_id}/images/{second_image['id']}/cover",
        headers=_ORIGIN_HEADERS,
    )

    assert response.status_code == 404
    assert client.delete(
        f"/api/v1/properties/{first_property_id}/images/{second_image['id']}",
        headers=_ORIGIN_HEADERS,
    ).status_code == 404
    with session_factory() as db:
        assert db.get(Property, first_property_id).cover_image_id is None
        assert db.get(PropertyImage, second_image["id"]).is_primary is False
        assert db.get(PropertyImage, second_image["id"]) is not None


def test_cover_selection_and_deletion_keep_cover_relationship_consistent(
    media_environment,
):
    client, session_factory, upload_directory, _, _, property_id = _owned_draft(
        media_environment
    )
    first_image = _upload(client, property_id).json()
    second_image = _upload(client, property_id).json()

    selected = client.put(
        f"/api/v1/properties/{property_id}/images/{first_image['id']}/cover",
        headers=_ORIGIN_HEADERS,
    )
    assert selected.status_code == 200
    assert selected.json()["cover_image_id"] == first_image["id"]
    assert {
        image["id"]: image["is_primary"] for image in selected.json()["images"]
    } == {first_image["id"]: True, second_image["id"]: False}

    first_path = upload_directory / first_image["image_url"].split("/")[-1]
    deleted = client.delete(
        f"/api/v1/properties/{property_id}/images/{first_image['id']}",
        headers=_ORIGIN_HEADERS,
    )
    assert deleted.status_code == 204
    assert not first_path.exists()

    with session_factory() as db:
        listing = db.get(Property, property_id)
        assert listing.cover_image_id is None
        assert db.get(PropertyImage, first_image["id"]) is None
        remaining_image = db.get(PropertyImage, second_image["id"])
        assert remaining_image.is_primary is False


def test_lifecycle_restrictions_apply_to_all_image_mutations(media_environment):
    client, session_factory, upload_directory, _, owner_id, property_id = _owned_draft(
        media_environment
    )
    image = _upload(client, property_id).json()
    with session_factory() as db:
        db.get(Property, property_id).status = "published"
        db.commit()

    assert _upload(client, property_id).status_code == 409
    assert client.put(
        f"/api/v1/properties/{property_id}/images/{image['id']}/cover",
        headers=_ORIGIN_HEADERS,
    ).status_code == 409
    assert client.delete(
        f"/api/v1/properties/{property_id}/images/{image['id']}",
        headers=_ORIGIN_HEADERS,
    ).status_code == 409
    assert len(list(upload_directory.iterdir())) == 1
    with session_factory() as db:
        assert db.get(Property, property_id).owner_id == owner_id
        assert db.get(Property, property_id).cover_image_id is None
        assert db.get(PropertyImage, image["id"]) is not None


def test_upload_database_failure_rolls_back_record_and_file(
    media_environment,
):
    client, session_factory, upload_directory, _, _, property_id = _owned_draft(
        media_environment
    )

    def fail_commit(_session):
        del _session
        raise SQLAlchemyError("synthetic transaction failure")

    event.listen(session_factory, "before_commit", fail_commit)
    try:
        response = _upload(client, property_id)
    finally:
        event.remove(session_factory, "before_commit", fail_commit)

    assert response.status_code == 503
    assert not upload_directory.exists() or list(upload_directory.iterdir()) == []
    with session_factory() as db:
        assert db.execute(select(PropertyImage)).scalars().all() == []


def test_delete_database_failure_restores_file_and_cover_reference(
    media_environment,
):
    client, session_factory, upload_directory, _, _, property_id = _owned_draft(
        media_environment
    )
    image = _upload(client, property_id).json()
    image_path = upload_directory / image["image_url"].split("/")[-1]
    with session_factory() as db:
        listing = db.get(Property, property_id)
        listing.cover_image_id = image["id"]
        db.get(PropertyImage, image["id"]).is_primary = True
        db.commit()

    def fail_commit(_session):
        del _session
        raise SQLAlchemyError("synthetic transaction failure")

    event.listen(session_factory, "before_commit", fail_commit)
    try:
        response = client.delete(
            f"/api/v1/properties/{property_id}/images/{image['id']}",
            headers=_ORIGIN_HEADERS,
        )
    finally:
        event.remove(session_factory, "before_commit", fail_commit)

    assert response.status_code == 503
    assert image_path.is_file()
    assert list(upload_directory.iterdir()) == [image_path]
    with session_factory() as db:
        assert db.get(Property, property_id).cover_image_id == image["id"]
        assert db.get(PropertyImage, image["id"]) is not None


def test_image_routes_are_documented_as_multipart_and_do_not_return_paths(
    media_environment,
):
    client, _, _, test_app, _, property_id = _owned_draft(media_environment)
    upload = _upload(client, property_id)
    assert upload.status_code == 201

    paths = test_app.openapi()["paths"]
    assert "post" in paths["/api/v1/properties/{property_id}/images"]
    assert "put" in paths[
        "/api/v1/properties/{property_id}/images/{image_id}/cover"
    ]
    assert "delete" in paths["/api/v1/properties/{property_id}/images/{image_id}"]
    upload_schema_ref = paths["/api/v1/properties/{property_id}/images"]["post"][
        "requestBody"
    ]["content"]["multipart/form-data"]["schema"]["$ref"]
    upload_schema = test_app.openapi()["components"]["schemas"][
        upload_schema_ref.rsplit("/", 1)[-1]
    ]
    assert upload_schema["properties"]["image_file"]["format"] == "binary"
    assert "property-media" not in upload.text
