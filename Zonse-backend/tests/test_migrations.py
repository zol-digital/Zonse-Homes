import os
from pathlib import Path
import subprocess
import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

import app.models
from app.database import Base


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_alembic_configuration_loads_and_finds_migrations():
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    script_directory = ScriptDirectory.from_config(config)

    assert Path(script_directory.dir).resolve() == (BACKEND_ROOT / "alembic").resolve()
    assert script_directory.get_current_head() == "20261030_0001"


def test_all_existing_models_are_registered_once_in_metadata():
    assert set(Base.metadata.tables) == {"users", "properties", "property_images"}
    assert len(Base.registry.mappers) == 3


def test_offline_upgrade_generates_valid_initial_migration_sql():
    environment = os.environ.copy()
    environment.pop("SQLALCHEMY_DATABASE_URI", None)
    environment["POSTGRES_SERVER"] = "localhost"
    environment["POSTGRES_USER"] = "migration_test"
    environment["POSTGRES_PASSWORD"] = "not-a-real-password"
    environment["POSTGRES_DB"] = "migration_test"
    environment["POSTGRES_PORT"] = "5432"

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "CREATE TABLE users" in result.stdout
    assert "CREATE TABLE properties" in result.stdout
    assert "CREATE TABLE property_images" in result.stdout
    assert "CREATE UNIQUE INDEX ix_users_email" in result.stdout
    assert "REFERENCES users (id)" in result.stdout
    assert "not-a-real-password" not in result.stdout
    assert "not-a-real-password" not in result.stderr
