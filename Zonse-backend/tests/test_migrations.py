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
    assert script_directory.get_current_head() == "20261103_0012"
    assert script_directory.get_revision("20261030_0002").down_revision == "20261030_0001"
    assert script_directory.get_revision("20261030_0003").down_revision == "20261030_0002"
    assert script_directory.get_revision("20261030_0004").down_revision == "20261030_0003"
    assert script_directory.get_revision("20261030_0005").down_revision == "20261030_0004"
    assert script_directory.get_revision("20261102_0006").down_revision == "20261030_0005"
    assert script_directory.get_revision("20261102_0007").down_revision == "20261102_0006"
    assert script_directory.get_revision("20261102_0008").down_revision == "20261102_0007"
    assert script_directory.get_revision("20261103_0009").down_revision == "20261102_0008"
    assert script_directory.get_revision("20261103_0010").down_revision == "20261103_0009"
    assert script_directory.get_revision("20261103_0011").down_revision == "20261103_0010"
    assert script_directory.get_revision("20261103_0012").down_revision == "20261103_0011"


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
        "moderation_action_logs",
        "property_reports",
        "featured_placement_packages",
        "featured_promotion_settings",
        "featured_promotion_orders",
        "featured_promotions",
        "featured_promotion_events",
        "property_categories",
        "location_references",
        "admin_action_logs",
    }
    assert len(Base.registry.mappers) == 22


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
    assert "CREATE TABLE property_categories" in result.stdout
    assert "CREATE TABLE location_references" in result.stdout
    assert "CREATE TABLE admin_action_logs" in result.stdout
    assert "INSERT INTO property_categories" in result.stdout
    assert "CREATE UNIQUE INDEX ix_users_email" in result.stdout
    assert "REFERENCES users (id)" in result.stdout
    assert "CREATE TABLE organizations" in result.stdout
    assert "CREATE TABLE business_verifications" in result.stdout
    assert "CREATE TABLE user_sessions" in result.stdout
    assert "CREATE TABLE user_action_tokens" in result.stdout
    assert "CREATE TABLE moderation_action_logs" in result.stdout
    assert "CREATE TABLE property_reports" in result.stdout
    assert "CREATE TABLE featured_placement_packages" in result.stdout
    assert "CREATE TABLE featured_promotion_orders" in result.stdout
    assert "CREATE TABLE featured_promotions" in result.stdout
    assert "CREATE TABLE featured_promotion_events" in result.stdout
    assert "reporter_ip_digest VARCHAR(64) NOT NULL" in result.stdout
    assert "review_report" in result.stdout
    assert "ADD COLUMN intent VARCHAR(8) DEFAULT 'sale' NOT NULL" in result.stdout
    assert "ADD COLUMN status VARCHAR(24) DEFAULT 'draft' NOT NULL" in result.stdout
    assert "ADD CONSTRAINT ck_properties_property_type CHECK" not in result.stdout
    assert "ADD CONSTRAINT ck_properties_status CHECK" in result.stdout
    assert "ADD CONSTRAINT ck_properties_deposit_nonnegative CHECK" in result.stdout
    assert "fk_properties_cover_image_id_property_images" in result.stdout
    assert "role IN ('seeker', 'owner', 'agent', 'property_manager', 'moderator', 'admin')" in result.stdout
    assert "action IN ('approve', 'request_changes', 'reject')" in result.stdout
    assert (
        "action IN "
        "('approve', 'request_changes', 'reject', 'remove', 'review_report')"
        in result.stdout
    )
    assert (
        "action IN ('approve', 'request_changes', 'reject', 'remove', 'hide', "
        "'restore', 'review_report')" in result.stdout
    )
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


def test_offline_moderation_downgrade_removes_only_moderation_schema():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261102_0006:20261030_0005",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP TABLE moderation_action_logs" in result.stdout
    assert "DROP CONSTRAINT ck_user_roles_role" in result.stdout
    assert (
        "role IN ('seeker', 'owner', 'agent', 'property_manager', 'admin')"
        in result.stdout
    )
    assert "DROP TABLE properties" not in result.stdout
    assert "DROP TABLE users" not in result.stdout


def test_offline_listing_removal_migration_downgrade_restores_prior_action_check():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261103_0009:20261102_0008",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP CONSTRAINT ck_moderation_action_logs_action" in result.stdout
    assert (
        "action IN ('approve', 'request_changes', 'reject', 'review_report')"
        in result.stdout
    )
    assert "DROP TABLE moderation_action_logs" not in result.stdout


def test_offline_moderator_hide_migration_downgrade_restores_prior_schema():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261103_0010:20261103_0009",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP COLUMN moderator_hidden" in result.stdout
    assert "DROP CONSTRAINT ck_moderation_action_logs_action" in result.stdout
    assert (
        "action IN "
        "('approve', 'request_changes', 'reject', 'remove', 'review_report')"
        in result.stdout
    )
    assert "DROP TABLE moderation_action_logs" not in result.stdout


def test_offline_reference_data_downgrade_removes_only_reference_tables():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261103_0011:20261103_0010",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP TABLE location_references" in result.stdout
    assert "DROP TABLE property_categories" in result.stdout
    assert "DROP TABLE properties" not in result.stdout
    assert "DROP TABLE users" not in result.stdout


def test_offline_admin_audit_downgrade_removes_only_admin_audit_table():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261103_0012:20261103_0011",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP TABLE admin_action_logs" in result.stdout
    assert "DROP TABLE moderation_action_logs" not in result.stdout
    assert "DROP TABLE users" not in result.stdout


def test_offline_report_downgrade_removes_only_report_schema():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "downgrade",
            "20261102_0007:20261102_0006",
            "--sql",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DROP TABLE property_reports" in result.stdout
    assert "DROP COLUMN report_id" in result.stdout
    assert "DROP TABLE moderation_action_logs" not in result.stdout
    assert "DROP TABLE properties" not in result.stdout
