from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class FeaturedPlacementPackage(Base):
    __tablename__ = "featured_placement_packages"
    __table_args__ = (
        CheckConstraint(
            "placement_type IN ('area', 'homepage')",
            name="ck_featured_packages_placement_type",
        ),
        CheckConstraint(
            "duration IN ('weekly', 'monthly')",
            name="ck_featured_packages_duration",
        ),
        CheckConstraint("price > 0", name="ck_featured_packages_price_positive"),
        CheckConstraint(
            "length(currency) = 3",
            name="ck_featured_packages_currency_length",
        ),
        UniqueConstraint(
            "placement_type",
            "duration",
            name="uq_featured_packages_type_duration",
        ),
    )

    id = Column(Integer, primary_key=True)
    placement_type = Column(String(16), nullable=False)
    duration = Column(String(16), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, server_default="MWK")
    is_available = Column(
        Boolean(),
        nullable=False,
        server_default=text("false"),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class FeaturedPromotionSettings(Base):
    __tablename__ = "featured_promotion_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_featured_settings_singleton"),
        CheckConstraint(
            "homepage_inventory_limit IS NULL OR homepage_inventory_limit > 0",
            name="ck_featured_settings_inventory_positive",
        ),
    )

    id = Column(Integer, primary_key=True, server_default=text("1"))
    homepage_inventory_limit = Column(Integer, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class FeaturedPromotionOrder(Base):
    __tablename__ = "featured_promotion_orders"
    __table_args__ = (
        CheckConstraint(
            "placement_type IN ('area', 'homepage')",
            name="ck_featured_orders_placement_type",
        ),
        CheckConstraint(
            "duration IN ('weekly', 'monthly')",
            name="ck_featured_orders_duration",
        ),
        CheckConstraint("amount > 0", name="ck_featured_orders_amount_positive"),
        CheckConstraint(
            "payment_status IN ('pending', 'paid', 'failed')",
            name="ck_featured_orders_payment_status",
        ),
        CheckConstraint(
            "fulfillment_status IN ('pending', 'fulfilled', 'blocked')",
            name="ck_featured_orders_fulfillment_status",
        ),
        CheckConstraint(
            "(placement_type = 'area' AND target_city IS NOT NULL) OR "
            "(placement_type = 'homepage' AND target_city IS NULL "
            "AND target_district IS NULL AND target_neighborhood IS NULL)",
            name="ck_featured_orders_target_matches_placement",
        ),
        UniqueConstraint(
            "payment_reference",
            name="uq_featured_orders_payment_reference",
        ),
        Index("ix_featured_orders_user_created", "advertiser_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    listing_id = Column(
        Integer,
        ForeignKey("properties.id", ondelete="RESTRICT"),
        nullable=False,
    )
    advertiser_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    package_id = Column(
        Integer,
        ForeignKey("featured_placement_packages.id", ondelete="RESTRICT"),
        nullable=False,
    )
    placement_type = Column(String(16), nullable=False)
    duration = Column(String(16), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    target_city = Column(String, nullable=True)
    target_district = Column(String, nullable=True)
    target_neighborhood = Column(String, nullable=True)
    payment_status = Column(
        String(16),
        nullable=False,
        server_default=text("'pending'"),
    )
    fulfillment_status = Column(
        String(16),
        nullable=False,
        server_default=text("'pending'"),
    )
    payment_reference = Column(String(128), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    listing = relationship("Property")
    advertiser = relationship("User")
    package = relationship("FeaturedPlacementPackage")
    promotion = relationship(
        "FeaturedPromotion",
        back_populates="order",
        uselist=False,
    )


class FeaturedPromotion(Base):
    __tablename__ = "featured_promotions"
    __table_args__ = (
        CheckConstraint(
            "placement_type IN ('area', 'homepage')",
            name="ck_featured_promotions_placement_type",
        ),
        CheckConstraint(
            "status IN ('active', 'expired', 'cancelled')",
            name="ck_featured_promotions_status",
        ),
        CheckConstraint("expires_at > starts_at", name="ck_featured_promotions_dates"),
        CheckConstraint(
            "(status = 'cancelled' AND cancelled_at IS NOT NULL "
            "AND cancelled_by_user_id IS NOT NULL "
            "AND cancellation_reason IS NOT NULL) OR "
            "(status <> 'cancelled' AND cancelled_at IS NULL "
            "AND cancelled_by_user_id IS NULL AND cancellation_reason IS NULL)",
            name="ck_featured_promotions_cancellation",
        ),
        UniqueConstraint(
            "order_id",
            name="uq_featured_promotions_order_id",
        ),
        Index(
            "ix_featured_promotions_active_placement",
            "placement_type",
            "expires_at",
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
        Index(
            "uq_featured_promotions_listing_active_placement",
            "listing_id",
            "placement_type",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer,
        ForeignKey("featured_promotion_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    listing_id = Column(
        Integer,
        ForeignKey("properties.id", ondelete="RESTRICT"),
        nullable=False,
    )
    placement_type = Column(String(16), nullable=False)
    target_city = Column(String, nullable=True)
    target_district = Column(String, nullable=True)
    target_neighborhood = Column(String, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        String(16),
        nullable=False,
        server_default=text("'active'"),
    )
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    cancellation_reason = Column(String(255), nullable=True)
    views_count = Column(Integer, nullable=False, server_default=text("0"))
    interactions_count = Column(Integer, nullable=False, server_default=text("0"))
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    order = relationship("FeaturedPromotionOrder", back_populates="promotion")
    listing = relationship("Property")


class FeaturedPromotionEvent(Base):
    __tablename__ = "featured_promotion_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('view', 'interaction')",
            name="ck_featured_events_event_type",
        ),
        UniqueConstraint(
            "promotion_id",
            "user_id",
            "event_type",
            "event_date",
            name="uq_featured_events_daily_user_event",
        ),
        Index(
            "ix_featured_events_promotion_date",
            "promotion_id",
            "event_date",
        ),
    )

    id = Column(Integer, primary_key=True)
    promotion_id = Column(
        Integer,
        ForeignKey("featured_promotions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type = Column(String(16), nullable=False)
    event_date = Column(Date, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
