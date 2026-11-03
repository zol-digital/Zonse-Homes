"""Add reversible moderator listing hiding and audit actions.

Revision ID: 20261103_0010
Revises: 20261103_0009
Create Date: 2026-11-03
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20261103_0010"
down_revision: Union[str, None] = "20261103_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column(
            "moderator_hidden",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.drop_constraint(
        "ck_moderation_action_logs_action",
        "moderation_action_logs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_moderation_action_logs_action",
        "moderation_action_logs",
        "action IN "
        "('approve', 'request_changes', 'reject', 'remove', 'hide', "
        "'restore', 'review_report')",
    )


def downgrade() -> None:
    if not context.is_offline_mode():
        connection = op.get_bind()
        hidden_count = connection.scalar(
            sa.text("SELECT count(*) FROM properties WHERE moderator_hidden")
        )
        visibility_action_count = connection.scalar(
            sa.text(
                "SELECT count(*) FROM moderation_action_logs "
                "WHERE action IN ('hide', 'restore')"
            )
        )
        if hidden_count or visibility_action_count:
            raise RuntimeError(
                "Cannot downgrade moderator hiding while hidden listings or "
                "visibility audit records exist"
            )

    op.drop_constraint(
        "ck_moderation_action_logs_action",
        "moderation_action_logs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_moderation_action_logs_action",
        "moderation_action_logs",
        "action IN "
        "('approve', 'request_changes', 'reject', 'remove', 'review_report')",
    )
    op.drop_column("properties", "moderator_hidden")
