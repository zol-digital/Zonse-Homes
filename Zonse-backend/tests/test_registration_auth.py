from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.v1.endpoints.auth import router as auth_router
from app.database import Base
from app.database import get_db
from app.models.user import User
from app.schemas.user import RegisterUserRequest
from app.security.auth import AuthenticationError, DuplicateUserError, authenticate_user, register_user
from app.security.passwords import hash_password


@pytest.fixture
def sqlite_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_register_user_hashes_password_and_normalizes_email(sqlite_session):
    user = register_user(
        sqlite_session,
        email="  User.Name@Example.com  ",
        password="correct horse battery staple",
        full_name="  Jane Doe  ",
        phone_number=" +265 991 000 001 ",
    )

    sqlite_session.refresh(user)
    assert user.email == "user.name@example.com"
    assert user.canonical_email == "user.name@example.com"
    assert user.hashed_password.startswith("$argon2id$")
    assert user.hashed_password != "correct horse battery staple"
    assert user.full_name == "Jane Doe"
    assert user.phone_number == "+265 991 000 001".strip()
    assert user.account_status == "pending_verification"
    assert user.role == "client"
    assert user.is_active is True


def test_register_user_assigns_default_seeker_role_without_privileged_override(sqlite_session):
    user = register_user(
        sqlite_session,
        email="seeker@example.com",
        password="correct horse battery staple",
    )
    sqlite_session.refresh(user)

    assert user.role == "client"
    assert {assigned.role for assigned in user.assigned_roles} == {"seeker"}

    with pytest.raises(ValidationError):
        RegisterUserRequest.model_validate(
            {
                "email": "blocked@example.com",
                "password": "correct horse battery staple",
                "role": "admin",
            }
        )


def test_register_user_rejects_case_variant_duplicates(sqlite_session):
    register_user(sqlite_session, email="first@example.com", password="correct horse battery staple")

    with pytest.raises(DuplicateUserError):
        register_user(sqlite_session, email="First@Example.com", password="different horse battery staple")


def test_register_user_rollback_and_unique_constraint_protection(sqlite_session):
    sqlite_session.add(User(email="dup@example.com", hashed_password=hash_password("correct horse battery staple")))
    sqlite_session.commit()

    with pytest.raises(DuplicateUserError):
        register_user(sqlite_session, email="dup@example.com", password="correct horse battery staple")


def test_authenticate_user_accepts_correct_credentials_for_active_verified_account(sqlite_session):
    password = "correct horse battery staple"
    user = register_user(sqlite_session, email="active@example.com", password=password)
    user.account_status = "active"
    user.email_verified_at = datetime.now(timezone.utc)
    sqlite_session.add(user)
    sqlite_session.commit()

    authenticated = authenticate_user(sqlite_session, email="ACTIVE@example.com", password=password)
    assert authenticated.id == user.id
    assert authenticated.account_status == "active"


def test_authenticate_user_rejects_invalid_unknown_and_ineligible_accounts(sqlite_session):
    good_password = "correct horse battery staple"
    register_user(sqlite_session, email="known@example.com", password=good_password)

    with pytest.raises(AuthenticationError):
        authenticate_user(sqlite_session, email="known@example.com", password="wrong-password")

    with pytest.raises(AuthenticationError):
        authenticate_user(sqlite_session, email="missing@example.com", password=good_password)

    pending = register_user(sqlite_session, email="pending@example.com", password=good_password)
    pending.account_status = "pending_verification"
    pending.email_verified_at = None
    sqlite_session.add(pending)
    sqlite_session.commit()

    with pytest.raises(AuthenticationError):
        authenticate_user(sqlite_session, email="pending@example.com", password=good_password)

    disabled = register_user(sqlite_session, email="disabled@example.com", password=good_password)
    disabled.account_status = "disabled"
    disabled.email_verified_at = datetime.now(timezone.utc)
    sqlite_session.add(disabled)
    sqlite_session.commit()

    with pytest.raises(AuthenticationError):
        authenticate_user(sqlite_session, email="disabled@example.com", password=good_password)


def test_authenticate_user_rehashes_verified_hashes_after_success(sqlite_session):
    password = "correct horse battery staple"
    old_parameters_hasher = Argon2Hasher(
        time_cost=1,
        memory_cost=8192,
        parallelism=1,
        hash_len=32,
        salt_len=16,
    )
    outdated_hash = PasswordHash((old_parameters_hasher,)).hash(password)

    user = User(
        email="rehash@example.com",
        canonical_email="rehash@example.com",
        hashed_password=outdated_hash,
        account_status="active",
        email_verified_at=datetime.now(timezone.utc),
        is_active=True,
    )
    sqlite_session.add(user)
    sqlite_session.commit()

    authenticated = authenticate_user(sqlite_session, email="rehash@example.com", password=password)
    sqlite_session.refresh(authenticated)

    assert authenticated.id == user.id
    assert authenticated.hashed_password.startswith("$argon2id$")
    assert authenticated.hashed_password != outdated_hash


def test_auth_register_endpoint_returns_safe_payload_and_duplicate_conflict():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    test_app = FastAPI()
    test_app.include_router(auth_router, prefix="/api/v1")
    test_app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(test_app)
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "api-user@example.com",
                "password": "correct horse battery staple",
                "full_name": "API User",
            },
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["email"] == "api-user@example.com"
        assert "hashed_password" not in payload
        assert payload["account_status"] == "pending_verification"

        duplicate = client.post(
            "/api/v1/auth/register",
            json={
                "email": "API-USER@example.com",
                "password": "another correct horse battery staple",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"] == "This email is already registered"
    finally:
        test_app.dependency_overrides.clear()
        engine.dispose()
