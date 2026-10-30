from app.config import Settings
import pytest
from sqlalchemy.engine import make_url


def test_settings_builds_database_uri_when_not_provided(monkeypatch):
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URI", raising=False)
    monkeypatch.setenv("POSTGRES_SERVER", "db")
    monkeypatch.setenv("POSTGRES_USER", "zonse_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "zonse_password")
    monkeypatch.setenv("POSTGRES_DB", "zonse_db")
    monkeypatch.setenv("POSTGRES_PORT", "5432")

    settings = Settings()

    assert settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql+")
    assert "zonse_user:zonse_password@db:5432/zonse_db" in settings.SQLALCHEMY_DATABASE_URI


def test_settings_escapes_special_characters_in_postgres_password(monkeypatch):
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URI", raising=False)
    monkeypatch.setenv("POSTGRES_SERVER", "db")
    monkeypatch.setenv("POSTGRES_USER", "zonse_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss:/?#%word")
    monkeypatch.setenv("POSTGRES_DB", "zonse_db")
    monkeypatch.setenv("POSTGRES_PORT", "5432")

    settings = Settings()

    parsed_url = make_url(settings.SQLALCHEMY_DATABASE_URI)
    assert parsed_url.username == "zonse_user"
    assert parsed_url.password == "p@ss:/?#%word"
    assert parsed_url.host == "db"
    assert parsed_url.database == "zonse_db"


def test_session_settings_default_to_lax_development_cookies(monkeypatch):
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("SESSION_COOKIE_SAMESITE", raising=False)
    monkeypatch.delenv("SESSION_COOKIE_NAME", raising=False)
    monkeypatch.delenv("SESSION_LIFETIME_SECONDS", raising=False)
    monkeypatch.delenv("SESSION_CSRF_TRUSTED_ORIGINS", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")

    settings = Settings()

    assert settings.SESSION_COOKIE_NAME == "zonse_session"
    assert settings.SESSION_LIFETIME_SECONDS == 86400
    assert settings.SESSION_COOKIE_SAMESITE == "lax"
    assert settings.SESSION_COOKIE_SECURE is False
    assert settings.SESSION_CSRF_TRUSTED_ORIGINS == ()


def test_production_session_cookies_are_secure(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    monkeypatch.setenv("SESSION_COOKIE_SAMESITE", "lax")
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URI", raising=False)
    monkeypatch.setenv("POSTGRES_SERVER", "db.example.test")
    monkeypatch.setenv("POSTGRES_USER", "zonse_app")
    monkeypatch.setenv("POSTGRES_PASSWORD", "configured-production-secret")
    monkeypatch.setenv("POSTGRES_DB", "zonse_production")

    settings = Settings()

    assert settings.SESSION_COOKIE_SECURE is True


def test_production_requires_explicit_database_configuration(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URI", raising=False)
    for key in ("POSTGRES_SERVER", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValueError, match="requires explicit database settings"):
        Settings()


@pytest.mark.parametrize(
    "password",
    ["postgres", "zonse_password", "replace_with_a_local_password"],
)
def test_production_rejects_development_database_password_fallbacks(
    monkeypatch,
    password,
):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URI", raising=False)
    monkeypatch.setenv("POSTGRES_SERVER", "db.example.test")
    monkeypatch.setenv("POSTGRES_USER", "zonse_app")
    monkeypatch.setenv("POSTGRES_PASSWORD", password)
    monkeypatch.setenv("POSTGRES_DB", "zonse_production")

    with pytest.raises(ValueError, match="development defaults"):
        Settings()


def test_production_rejects_development_credentials_in_database_uri(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql+psycopg://zonse_user:zonse_password@db.example.test/zonse",
    )

    with pytest.raises(ValueError, match="development defaults"):
        Settings()


def test_production_accepts_explicit_database_uri(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    database_uri = (
        "postgresql+psycopg://zonse_app:strong-secret@db.example.test/zonse"
    )
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", database_uri)

    settings = Settings()

    assert settings.SQLALCHEMY_DATABASE_URI == database_uri


def test_session_cookie_settings_reject_insecure_production_and_invalid_values(
    monkeypatch,
):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    monkeypatch.setenv("POSTGRES_SERVER", "db.example.test")
    monkeypatch.setenv("POSTGRES_USER", "zonse_app")
    monkeypatch.setenv("POSTGRES_PASSWORD", "configured-production-secret")
    monkeypatch.setenv("POSTGRES_DB", "zonse_production")
    monkeypatch.delenv("SQLALCHEMY_DATABASE_URI", raising=False)

    with pytest.raises(ValueError, match="Secure in production"):
        Settings()

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    monkeypatch.setenv("SESSION_COOKIE_SAMESITE", "none")
    with pytest.raises(ValueError, match="SameSite=None"):
        Settings()


def test_session_settings_parse_trusted_origins_and_reject_paths(monkeypatch):
    monkeypatch.setenv(
        "SESSION_CSRF_TRUSTED_ORIGINS",
        "https://app.example.test, http://localhost:5173/",
    )

    settings = Settings()

    assert settings.SESSION_CSRF_TRUSTED_ORIGINS == (
        "https://app.example.test",
        "http://localhost:5173",
    )

    monkeypatch.setenv("SESSION_CSRF_TRUSTED_ORIGINS", "https://example.test/path")
    with pytest.raises(ValueError, match="invalid origin"):
        Settings()


def test_session_settings_reject_invalid_cookie_names(monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_NAME", "session; secure")

    with pytest.raises(ValueError, match="valid cookie name"):
        Settings()
