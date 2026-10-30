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
    assert script_directory.get_current_head() == "20261030_0005"
    assert script_directory.get_revision("20261030_0002").down_revision == "20261030_0001"
    assert script_directory.get_revision("20261030_0003").down_revision == "20261030_0002"
    assert script_directory.get_revision("20261030_0004").down_revision == "20261030_0003"
    assert script_directory.get_revision("20261030_0005").down_revision == "20261030_0004"


def test_all_existing_models_are_registered_once_in_metadata():
    assert set(Base.metadata.tables) == {
        "users",
        "properties",
        "property_images",
        "user_roles",
        "organizations",
        "organization_memberships",
        "business_verifications",
        "verification_submissions",
        "verification_documents",
        "business_verification_reviews",
        "user_sessions",
        "user_action_tokens",
    }
    assert len(Base.registry.mappers) == 12


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
    assert "CREATE TABLE organizations" in result.stdout
    assert "CREATE TABLE business_verifications" in result.stdout
    assert "CREATE TABLE user_sessions" in result.stdout
    assert "CREATE TABLE user_action_tokens" in result.stdout
    assert "ADD COLUMN intent VARCHAR(8) DEFAULT 'sale' NOT NULL" in result.stdout
    assert "ADD COLUMN status VARCHAR(24) DEFAULT 'draft' NOT NULL" in result.stdout
    assert "ADD CONSTRAINT ck_properties_property_type CHECK" not in result.stdout
    assert "ADD CONSTRAINT ck_properties_status CHECK" in result.stdout
    assert "ADD CONSTRAINT ck_properties_deposit_nonnegative CHECK" in result.stdout
    assert "fk_properties_cover_image_id_property_images" in result.stdout
    assert "not-a-real-password" not in result.stdout
    assert "not-a-real-password" not in result.stderr


def test_offline_downgrade_sql_drops_identity_tables_and_user_columns():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261030_0002:20261030_0001",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP TABLE business_verification_reviews" in result.stdout
    assert "DROP TABLE organizations" in result.stdout
    assert "DROP COLUMN canonical_email" in result.stdout


def test_offline_session_downgrade_removes_only_session_schema():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261030_0003:20261030_0002",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP INDEX ix_user_sessions_user_expires" in result.stdout
    assert "DROP TABLE user_sessions" in result.stdout
    assert "DROP TABLE users" not in result.stdout


def test_offline_action_token_downgrade_removes_only_token_schema():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261030_0004:20261030_0003",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP INDEX ix_user_action_tokens_user_purpose_created" in result.stdout
    assert "DROP TABLE user_action_tokens" in result.stdout
    assert "DROP TABLE user_sessions" not in result.stdout
    assert "DROP TABLE users" not in result.stdout


def test_offline_listing_downgrade_removes_only_listing_schema():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261030_0005:20261030_0004",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP CONSTRAINT ck_properties_status" in result.stdout
    assert "DROP CONSTRAINT fk_properties_cover_image_id_property_images" in result.stdout
    assert "DROP COLUMN intent" in result.stdout
    assert "DROP COLUMN cover_image_id" in result.stdout
    assert "DROP TABLE properties" not in result.stdout
    assert "DROP TABLE user_sessions" not in result.stdout
