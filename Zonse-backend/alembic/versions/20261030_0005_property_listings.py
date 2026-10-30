"""Add listing-management fields to properties.

Revision ID: 20261030_0005
Revises: 20261030_0004
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261030_0005"
down_revision: Union[str, None] = "20261030_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("intent", sa.String(length=8), server_default="sale", nullable=False),
    )
    op.add_column(
        "properties",
        sa.Column(
            "negotiable",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column("properties", sa.Column("rental_period", sa.String(length=16)))
    op.add_column("properties", sa.Column("deposit", sa.Numeric(12, 2)))
    op.add_column("properties", sa.Column("floor_area", sa.Numeric(12, 2)))
    op.add_column(
        "properties",
        sa.Column(
            "floor_area_unit",
            sa.String(length=8),
            server_default="sqm",
            nullable=False,
        ),
    )
    op.add_column("properties", sa.Column("land_area", sa.Numeric(12, 2)))
    op.add_column(
        "properties",
        sa.Column(
            "land_area_unit",
            sa.String(length=8),
            server_default="sqm",
            nullable=False,
        ),
    )
    op.add_column(
        "properties",
        sa.Column(
            "amenities",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )
    op.add_column(
        "properties",
        sa.Column(
            "utilities",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
    )
    op.add_column("properties", sa.Column("district", sa.String()))
    op.add_column("properties", sa.Column("neighborhood", sa.String()))
    op.add_column("properties", sa.Column("available_from", sa.Date()))
    op.add_column("properties", sa.Column("advertiser_name", sa.String()))
    op.add_column("properties", sa.Column("contact_phone", sa.String(length=32)))
    op.add_column("properties", sa.Column("contact_email", sa.String(length=254)))
    op.add_column(
        "properties",
        sa.Column(
            "show_contact_details",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column("properties", sa.Column("cover_image_id", sa.Integer()))
    op.add_column(
        "properties",
        sa.Column(
            "status",
            sa.String(length=24),
            server_default="draft",
            nullable=False,
        ),
    )
    op.add_column(
        "properties",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_properties_cover_image_id_property_images",
        "properties",
        "property_images",
        ["cover_image_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_properties_intent",
        "properties",
        "intent IN ('sale', 'rent')",
    )
    op.create_check_constraint(
        "ck_properties_status",
        "properties",
        "status IN ('draft', 'pending_review', 'published', "
        "'changes_requested', 'rejected', 'paused', 'rented', 'sold', "
        "'expired', 'removed', 'archived')",
    )
    op.create_check_constraint(
        "ck_properties_rental_period",
        "properties",
        "rental_period IS NULL OR rental_period IN ('day', 'week', 'month', 'year')",
    )
    op.create_check_constraint(
        "ck_properties_deposit_nonnegative",
        "properties",
        "deposit IS NULL OR deposit >= 0",
    )
    op.create_check_constraint(
        "ck_properties_floor_area_positive",
        "properties",
        "floor_area IS NULL OR floor_area > 0",
    )
    op.create_check_constraint(
        "ck_properties_land_area_positive",
        "properties",
        "land_area IS NULL OR land_area > 0",
    )
    op.create_check_constraint(
        "ck_properties_floor_area_unit",
        "properties",
        "floor_area_unit IN ('sqm', 'sqft')",
    )
    op.create_check_constraint(
        "ck_properties_land_area_unit",
        "properties",
        "land_area_unit IN ('sqm', 'sqft', 'acre', 'hectare')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_properties_land_area_unit", "properties", type_="check")
    op.drop_constraint("ck_properties_floor_area_unit", "properties", type_="check")
    op.drop_constraint("ck_properties_land_area_positive", "properties", type_="check")
    op.drop_constraint("ck_properties_floor_area_positive", "properties", type_="check")
    op.drop_constraint("ck_properties_deposit_nonnegative", "properties", type_="check")
    op.drop_constraint("ck_properties_rental_period", "properties", type_="check")
    op.drop_constraint("ck_properties_status", "properties", type_="check")
    op.drop_constraint("ck_properties_intent", "properties", type_="check")
    op.drop_constraint(
        "fk_properties_cover_image_id_property_images",
        "properties",
        type_="foreignkey",
    )
    op.drop_column("properties", "updated_at")
    op.drop_column("properties", "status")
    op.drop_column("properties", "cover_image_id")
    op.drop_column("properties", "show_contact_details")
    op.drop_column("properties", "contact_email")
    op.drop_column("properties", "contact_phone")
    op.drop_column("properties", "advertiser_name")
    op.drop_column("properties", "available_from")
    op.drop_column("properties", "neighborhood")
    op.drop_column("properties", "district")
    op.drop_column("properties", "utilities")
    op.drop_column("properties", "amenities")
    op.drop_column("properties", "land_area_unit")
    op.drop_column("properties", "land_area")
    op.drop_column("properties", "floor_area_unit")
    op.drop_column("properties", "floor_area")
    op.drop_column("properties", "deposit")
    op.drop_column("properties", "rental_period")
    op.drop_column("properties", "negotiable")
    op.drop_column("properties", "intent")
