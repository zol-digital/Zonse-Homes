"""Add administrator-managed property categories and locations.

Revision ID: 20261103_0011
Revises: 20261103_0010
Create Date: 2026-11-03
"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20261103_0011"
down_revision: Union[str, None] = "20261103_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "property_categories",
        sa.Column("slug", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.bulk_insert(
        sa.table(
            "property_categories",
            sa.column("slug", sa.String(length=50)),
            sa.column("name", sa.String(length=100)),
        ),
        [
            {"slug": "house", "name": "House"},
            {"slug": "apartment", "name": "Apartment"},
            {"slug": "flat", "name": "Flat"},
            {"slug": "plot", "name": "Plot"},
            {"slug": "land", "name": "Land"},
            {"slug": "commercial", "name": "Commercial"},
        ],
    )
    op.create_table(
        "location_references",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column(
            "aliases",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('region', 'district', 'city', 'town', 'neighborhood')",
            name="ck_location_references_kind",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["location_references.id"],
            name="fk_location_references_parent_id",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_location_references_slug",
        "location_references",
        ["slug"],
        unique=True,
    )
    op.create_index(
        "ix_location_references_parent_id",
        "location_references",
        ["parent_id"],
    )


def downgrade() -> None:
    if not context.is_offline_mode():
        connection = op.get_bind()
        location_count = connection.scalar(
            sa.text("SELECT count(*) FROM location_references")
        )
        customized_category_count = connection.scalar(
            sa.text(
                "SELECT count(*) FROM property_categories WHERE NOT ("
                "(slug = 'house' AND name = 'House' AND is_active) OR "
                "(slug = 'apartment' AND name = 'Apartment' AND is_active) OR "
                "(slug = 'flat' AND name = 'Flat' AND is_active) OR "
                "(slug = 'plot' AND name = 'Plot' AND is_active) OR "
                "(slug = 'land' AND name = 'Land' AND is_active) OR "
                "(slug = 'commercial' AND name = 'Commercial' AND is_active)"
                ")"
            )
        )
        if location_count or customized_category_count:
            raise RuntimeError(
                "Cannot downgrade while administrator-managed reference data "
                "contains locations or customized categories"
            )

    op.drop_index("ix_location_references_parent_id", table_name="location_references")
    op.drop_index("ix_location_references_slug", table_name="location_references")
    op.drop_table("location_references")
    op.drop_table("property_categories")
