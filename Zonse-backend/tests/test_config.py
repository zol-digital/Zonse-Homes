from app.config import Settings


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
