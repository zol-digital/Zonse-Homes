"""Add moderation audit logs and moderator role support.

Revision ID: 20261102_0006
Revises: 20261030_0005
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261102_0006"
down_revision: Union[str, None] = "20261030_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_user_roles_role", "user_roles", type_="check")
    op.create_check_constraint(
        "ck_user_roles_role",
        "user_roles",
        "role IN ('seeker', 'owner', 'agent', 'property_manager', 'moderator', 'admin')",
    )

    op.create_table(
        "moderation_action_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("previous_status", sa.String(length=24), nullable=False),
        sa.Column("new_status", sa.String(length=24), nullable=False),
        sa.Column("moderator_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "action IN ('approve', 'request_changes', 'reject')",
            name="ck_moderation_action_logs_action",
        ),
        sa.CheckConstraint(
            "length(reason) >= 1",
            name="ck_moderation_action_logs_reason_not_empty",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["properties.id"],
            name="fk_moderation_action_logs_listing_id_properties",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_moderation_action_logs_actor_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_moderation_action_logs"),
    )
    op.create_index(
        "ix_moderation_action_logs_listing_id",
        "moderation_action_logs",
        ["listing_id"],
        unique=False,
    )
    op.create_index(
        "ix_moderation_action_logs_created_at",
        "moderation_action_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_moderation_action_logs_created_at", table_name="moderation_action_logs")
    op.drop_index("ix_moderation_action_logs_listing_id", table_name="moderation_action_logs")
    op.drop_table("moderation_action_logs")
    op.drop_constraint("ck_user_roles_role", "user_roles", type_="check")
    op.create_check_constraint(
        "ck_user_roles_role",
        "user_roles",
        "role IN ('seeker', 'owner', 'agent', 'property_manager', 'admin')",
    )
