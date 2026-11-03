"""Add immutable audit records for privileged administrator changes.

Revision ID: 20261103_0012
Revises: 20261103_0011
Create Date: 2026-11-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261103_0012"
down_revision: Union[str, None] = "20261103_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_action_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(action) >= 1",
            name="ck_admin_action_logs_action_not_empty",
        ),
        sa.CheckConstraint(
            "length(entity_type) >= 1",
            name="ck_admin_action_logs_entity_type_not_empty",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_admin_action_logs_actor_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_admin_action_logs"),
    )
    op.create_index(
        "ix_admin_action_logs_actor_id",
        "admin_action_logs",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_admin_action_logs_created_at",
        "admin_action_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_admin_action_logs_entity",
        "admin_action_logs",
        ["entity_type", "entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_admin_action_logs_entity", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_created_at", table_name="admin_action_logs")
    op.drop_index("ix_admin_action_logs_actor_id", table_name="admin_action_logs")
    op.drop_table("admin_action_logs")
