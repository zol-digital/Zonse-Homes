from sqlalchemy.exc import OperationalError
from fastapi.testclient import TestClient
from unittest.mock import Mock

import app.main as main
from app.main import app
from app.database import Base


client = TestClient(app)


def test_health_endpoint_returns_healthy_status():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Zonse Homes Backend"}


def test_health_endpoint_does_not_depend_on_database(monkeypatch):
    def fail_database_check():
        raise OperationalError("SELECT 1", {}, Exception("private connection details"))

    monkeypatch.setattr(main, "check_database_connection", fail_database_check)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Zonse Homes Backend"}


def test_application_startup_does_not_create_tables_or_connect_to_database(monkeypatch):
    database_check = Mock(side_effect=AssertionError("unexpected startup database check"))
    create_all = Mock(side_effect=AssertionError("unexpected startup table creation"))
    monkeypatch.setattr(main, "check_database_connection", database_check)
    monkeypatch.setattr(Base.metadata, "create_all", create_all)

    with TestClient(app):
        pass

    database_check.assert_not_called()
    create_all.assert_not_called()


def test_readiness_endpoint_returns_ready_status_when_database_is_reachable(monkeypatch):
    monkeypatch.setattr(main, "check_database_connection", lambda: None)

    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "service": "Zonse Homes Backend"}


def test_readiness_endpoint_returns_503_without_database_details(monkeypatch):
    def fail_database_check():
        raise OperationalError("SELECT 1", {}, Exception("private connection details"))

    monkeypatch.setattr(main, "check_database_connection", fail_database_check)

    response = client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "private connection details" not in response.text
