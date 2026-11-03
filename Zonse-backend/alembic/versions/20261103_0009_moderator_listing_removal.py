"""Allow moderator listing removals in the moderation audit log.

Revision ID: 20261103_0009
Revises: 20261102_0008
Create Date: 2026-11-03
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20261103_0009"
down_revision: Union[str, None] = "20261102_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    if not context.is_offline_mode():
        connection = op.get_bind()
        removal_count = connection.scalar(
            sa.text(
                "SELECT count(*) FROM moderation_action_logs "
                "WHERE action = 'remove'"
            )
        )
        if removal_count:
            raise RuntimeError(
                "Cannot downgrade listing removal audit support while "
                "removal audit records exist"
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
