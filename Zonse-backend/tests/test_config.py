from app.config import Settings
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
