"""Add digest-only email verification and password recovery tokens.

Revision ID: 20261030_0004
Revises: 20261030_0003
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261030_0004"
down_revision: Union[str, None] = "20261030_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_action_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "purpose IN ('email_verification', 'password_recovery')",
            name="ck_user_action_tokens_purpose",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_user_action_tokens_expiry_after_creation",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_action_tokens_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_action_tokens"),
        sa.UniqueConstraint(
            "token_digest",
            name="uq_user_action_tokens_token_digest",
        ),
    )
    op.create_index(
        "ix_user_action_tokens_user_purpose_created",
        "user_action_tokens",
        ["user_id", "purpose", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_action_tokens_user_purpose_created",
        table_name="user_action_tokens",
    )
    op.drop_table("user_action_tokens")
