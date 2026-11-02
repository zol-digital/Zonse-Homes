"""Add featured placement packages, orders, promotions and analytics.

Revision ID: 20261102_0008
Revises: 20261102_0007
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261102_0008"
down_revision: Union[str, None] = "20261102_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "featured_placement_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("placement_type", sa.String(length=16), nullable=False),
        sa.Column("duration", sa.String(length=16), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3),
            server_default="MWK",
            nullable=False,
        ),
        sa.Column(
            "is_available",
            sa.Boolean(),
            server_default=sa.text("false"),
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
            "placement_type IN ('area', 'homepage')",
            name="ck_featured_packages_placement_type",
        ),
        sa.CheckConstraint(
            "duration IN ('weekly', 'monthly')",
            name="ck_featured_packages_duration",
        ),
        sa.CheckConstraint("price > 0", name="ck_featured_packages_price_positive"),
        sa.CheckConstraint(
            "length(currency) = 3",
            name="ck_featured_packages_currency_length",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_featured_placement_packages"),
        sa.UniqueConstraint(
            "placement_type",
            "duration",
            name="uq_featured_packages_type_duration",
        ),
    )
    op.create_table(
        "featured_promotion_settings",
        sa.Column("id", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("homepage_inventory_limit", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_featured_settings_singleton"),
        sa.CheckConstraint(
            "homepage_inventory_limit IS NULL OR homepage_inventory_limit > 0",
            name="ck_featured_settings_inventory_positive",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_featured_promotion_settings"),
    )
    settings_table = sa.table(
        "featured_promotion_settings",
        sa.column("id", sa.Integer()),
        sa.column("homepage_inventory_limit", sa.Integer()),
    )
    op.bulk_insert(
        settings_table,
        [{"id": 1, "homepage_inventory_limit": None}],
    )
    op.create_table(
        "featured_promotion_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("advertiser_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("placement_type", sa.String(length=16), nullable=False),
        sa.Column("duration", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("target_city", sa.String(), nullable=True),
        sa.Column("target_district", sa.String(), nullable=True),
        sa.Column("target_neighborhood", sa.String(), nullable=True),
        sa.Column(
            "payment_status",
            sa.String(length=16),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "fulfillment_status",
            sa.String(length=16),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("payment_reference", sa.String(length=128), nullable=True),
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
            "placement_type IN ('area', 'homepage')",
            name="ck_featured_orders_placement_type",
        ),
        sa.CheckConstraint(
            "duration IN ('weekly', 'monthly')",
            name="ck_featured_orders_duration",
        ),
        sa.CheckConstraint("amount > 0", name="ck_featured_orders_amount_positive"),
        sa.CheckConstraint(
            "payment_status IN ('pending', 'paid', 'failed')",
            name="ck_featured_orders_payment_status",
        ),
        sa.CheckConstraint(
            "fulfillment_status IN ('pending', 'fulfilled', 'blocked')",
            name="ck_featured_orders_fulfillment_status",
        ),
        sa.CheckConstraint(
            "(placement_type = 'area' AND target_city IS NOT NULL) OR "
            "(placement_type = 'homepage' AND target_city IS NULL "
            "AND target_district IS NULL AND target_neighborhood IS NULL)",
            name="ck_featured_orders_target_matches_placement",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["properties.id"],
            name="fk_featured_promotion_orders_listing_id_properties",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["advertiser_id"],
            ["users.id"],
            name="fk_featured_promotion_orders_advertiser_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["featured_placement_packages.id"],
            name="fk_featured_promotion_orders_package_id_packages",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_featured_promotion_orders"),
        sa.UniqueConstraint(
            "payment_reference",
            name="uq_featured_orders_payment_reference",
        ),
    )
    op.create_index(
        "ix_featured_orders_user_created",
        "featured_promotion_orders",
        ["advertiser_id", "created_at"],
    )
    op.create_table(
        "featured_promotions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("placement_type", sa.String(length=16), nullable=False),
        sa.Column("target_city", sa.String(), nullable=True),
        sa.Column("target_district", sa.String(), nullable=True),
        sa.Column("target_neighborhood", sa.String(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by_user_id", sa.Integer(), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=255), nullable=True),
        sa.Column(
            "views_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "interactions_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "placement_type IN ('area', 'homepage')",
            name="ck_featured_promotions_placement_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'expired', 'cancelled')",
            name="ck_featured_promotions_status",
        ),
        sa.CheckConstraint(
            "expires_at > starts_at",
            name="ck_featured_promotions_dates",
        ),
        sa.CheckConstraint(
            "(status = 'cancelled' AND cancelled_at IS NOT NULL "
            "AND cancelled_by_user_id IS NOT NULL "
            "AND cancellation_reason IS NOT NULL) OR "
            "(status <> 'cancelled' AND cancelled_at IS NULL "
            "AND cancelled_by_user_id IS NULL AND cancellation_reason IS NULL)",
            name="ck_featured_promotions_cancellation",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["featured_promotion_orders.id"],
            name="fk_featured_promotions_order_id_orders",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["properties.id"],
            name="fk_featured_promotions_listing_id_properties",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["cancelled_by_user_id"],
            ["users.id"],
            name="fk_featured_promotions_cancelled_by_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_featured_promotions"),
        sa.UniqueConstraint(
            "order_id",
            name="uq_featured_promotions_order_id",
        ),
    )
    op.create_index(
        "ix_featured_promotions_active_placement",
        "featured_promotions",
        ["placement_type", "expires_at"],
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "uq_featured_promotions_listing_active_placement",
        "featured_promotions",
        ["listing_id", "placement_type"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "featured_promotion_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("promotion_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=16), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ('view', 'interaction')",
            name="ck_featured_events_event_type",
        ),
        sa.ForeignKeyConstraint(
            ["promotion_id"],
            ["featured_promotions.id"],
            name="fk_featured_promotion_events_promotion_id_promotions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_featured_promotion_events_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_featured_promotion_events"),
        sa.UniqueConstraint(
            "promotion_id",
            "user_id",
            "event_type",
            "event_date",
            name="uq_featured_events_daily_user_event",
        ),
    )
    op.create_index(
        "ix_featured_events_promotion_date",
        "featured_promotion_events",
        ["promotion_id", "event_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_featured_events_promotion_date",
        table_name="featured_promotion_events",
    )
    op.drop_table("featured_promotion_events")
    op.drop_index(
        "uq_featured_promotions_listing_active_placement",
        table_name="featured_promotions",
    )
    op.drop_index(
        "ix_featured_promotions_active_placement",
        table_name="featured_promotions",
    )
    op.drop_table("featured_promotions")
    op.drop_index(
        "ix_featured_orders_user_created",
        table_name="featured_promotion_orders",
    )
    op.drop_table("featured_promotion_orders")
    op.drop_table("featured_promotion_settings")
    op.drop_table("featured_placement_packages")
