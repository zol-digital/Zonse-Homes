"""Add private property reports and report review auditing.

Revision ID: 20261102_0007
Revises: 20261102_0006
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20261102_0007"
down_revision: Union[str, None] = "20261102_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OPEN_STATUSES = "'new', 'investigating', 'escalated'"


def upgrade() -> None:
    op.create_table(
        "property_reports",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=True),
        sa.Column("reported_user_id", sa.Integer(), nullable=True),
        sa.Column("reporter_user_id", sa.Integer(), nullable=True),
        sa.Column("reporter_ip_digest", sa.String(length=64), nullable=False),
        sa.Column("reason_code", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=24),
            server_default="new",
            nullable=False,
        ),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("resolution_code", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "reason_code IN "
            "('suspected_scam', 'duplicate', 'misleading_details', "
            "'wrong_price', 'unavailable', 'inappropriate_content', 'other')",
            name="ck_property_reports_reason_code",
        ),
        sa.CheckConstraint(
            "status IN ('new', 'investigating', 'actioned', 'dismissed', 'escalated')",
            name="ck_property_reports_status",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["properties.id"],
            name="fk_property_reports_listing_id_properties",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reported_user_id"],
            ["users.id"],
            name="fk_property_reports_reported_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_user_id"],
            ["users.id"],
            name="fk_property_reports_reporter_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_user_id"],
            ["users.id"],
            name="fk_property_reports_assigned_to_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_property_reports"),
    )
    op.create_index(
        "ix_property_reports_status_created_at",
        "property_reports",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_property_reports_listing_id",
        "property_reports",
        ["listing_id"],
    )
    op.create_index(
        "ix_property_reports_reporter_user_created_at",
        "property_reports",
        ["reporter_user_id", "created_at"],
    )
    op.create_index(
        "ix_property_reports_reporter_ip_created_at",
        "property_reports",
        ["reporter_ip_digest", "created_at"],
    )
    op.create_index(
        "uq_property_reports_open_user_listing",
        "property_reports",
        ["listing_id", "reporter_user_id"],
        unique=True,
        postgresql_where=sa.text(
            f"reporter_user_id IS NOT NULL AND status IN ({_OPEN_STATUSES})"
        ),
        sqlite_where=sa.text(
            f"reporter_user_id IS NOT NULL AND status IN ({_OPEN_STATUSES})"
        ),
    )
    op.create_index(
        "uq_property_reports_open_guest_listing",
        "property_reports",
        ["listing_id", "reporter_ip_digest"],
        unique=True,
        postgresql_where=sa.text(
            f"reporter_user_id IS NULL AND status IN ({_OPEN_STATUSES})"
        ),
        sqlite_where=sa.text(
            f"reporter_user_id IS NULL AND status IN ({_OPEN_STATUSES})"
        ),
    )

    op.add_column(
        "moderation_action_logs",
        sa.Column("report_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_moderation_action_logs_report_id_property_reports",
        "moderation_action_logs",
        "property_reports",
        ["report_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "ck_moderation_action_logs_action",
        "moderation_action_logs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_moderation_action_logs_action",
        "moderation_action_logs",
        "action IN ('approve', 'request_changes', 'reject', 'review_report')",
    )


def downgrade() -> None:
    if not context.is_offline_mode():
        connection = op.get_bind()
        report_count = connection.scalar(
            sa.text("SELECT count(*) FROM property_reports")
        )
        report_audit_count = connection.scalar(
            sa.text(
                "SELECT count(*) FROM moderation_action_logs "
                "WHERE action = 'review_report'"
            )
        )
        if report_count or report_audit_count:
            raise RuntimeError(
                "Cannot downgrade property reports while report or review "
                "audit records exist"
            )

    op.drop_constraint(
        "ck_moderation_action_logs_action",
        "moderation_action_logs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_moderation_action_logs_action",
        "moderation_action_logs",
        "action IN ('approve', 'request_changes', 'reject')",
    )
    op.drop_constraint(
        "fk_moderation_action_logs_report_id_property_reports",
        "moderation_action_logs",
        type_="foreignkey",
    )
    op.drop_column("moderation_action_logs", "report_id")
    op.drop_index(
        "uq_property_reports_open_guest_listing",
        table_name="property_reports",
    )
    op.drop_index(
        "uq_property_reports_open_user_listing",
        table_name="property_reports",
    )
    op.drop_index(
        "ix_property_reports_reporter_ip_created_at",
        table_name="property_reports",
    )
    op.drop_index(
        "ix_property_reports_reporter_user_created_at",
        table_name="property_reports",
    )
    op.drop_index(
        "ix_property_reports_listing_id",
        table_name="property_reports",
    )
    op.drop_index(
        "ix_property_reports_status_created_at",
        table_name="property_reports",
    )
    op.drop_table("property_reports")
