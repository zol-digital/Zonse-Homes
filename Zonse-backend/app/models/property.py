from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PropertyStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"
    PAUSED = "paused"
    RENTED = "rented"
    SOLD = "sold"
    EXPIRED = "expired"
    REMOVED = "removed"
    ARCHIVED = "archived"


PROPERTY_STATUS_TRANSITIONS = {
    PropertyStatus.DRAFT: frozenset(
        {PropertyStatus.PENDING_REVIEW, PropertyStatus.REMOVED}
    ),
    PropertyStatus.PENDING_REVIEW: frozenset(
        {
            PropertyStatus.PUBLISHED,
            PropertyStatus.CHANGES_REQUESTED,
            PropertyStatus.REJECTED,
            PropertyStatus.REMOVED,
        }
    ),
    PropertyStatus.PUBLISHED: frozenset(
        {
            PropertyStatus.PAUSED,
            PropertyStatus.RENTED,
            PropertyStatus.SOLD,
            PropertyStatus.EXPIRED,
            PropertyStatus.REMOVED,
        }
    ),
    PropertyStatus.CHANGES_REQUESTED: frozenset(
        {PropertyStatus.DRAFT, PropertyStatus.PENDING_REVIEW, PropertyStatus.REMOVED}
    ),
    PropertyStatus.REJECTED: frozenset(
        {PropertyStatus.DRAFT, PropertyStatus.ARCHIVED, PropertyStatus.REMOVED}
    ),
    PropertyStatus.PAUSED: frozenset(
        {PropertyStatus.PUBLISHED, PropertyStatus.ARCHIVED, PropertyStatus.REMOVED}
    ),
    PropertyStatus.RENTED: frozenset({PropertyStatus.ARCHIVED, PropertyStatus.REMOVED}),
    PropertyStatus.SOLD: frozenset({PropertyStatus.ARCHIVED, PropertyStatus.REMOVED}),
    PropertyStatus.EXPIRED: frozenset(
        {PropertyStatus.ARCHIVED, PropertyStatus.REMOVED}
    ),
    PropertyStatus.REMOVED: frozenset({PropertyStatus.ARCHIVED}),
    PropertyStatus.ARCHIVED: frozenset(),
}


def validate_property_status_transition(
    current_status: str | PropertyStatus,
    new_status: str | PropertyStatus,
) -> None:
    try:
        current = PropertyStatus(current_status)
        target = PropertyStatus(new_status)
    except ValueError as exc:
        raise ValueError("Unknown property status") from exc

    if target not in PROPERTY_STATUS_TRANSITIONS[current]:
        raise ValueError(
            f"Cannot transition property from {current.value} to {target.value}"
        )


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        CheckConstraint(
            "intent IN ('sale', 'rent')",
            name="ck_properties_intent",
        ),
        CheckConstraint(
            "status IN ('draft', 'pending_review', 'published', "
            "'changes_requested', 'rejected', 'paused', 'rented', 'sold', "
            "'expired', 'removed', 'archived')",
            name="ck_properties_status",
        ),
        CheckConstraint(
            "rental_period IS NULL OR rental_period IN "
            "('day', 'week', 'month', 'year')",
            name="ck_properties_rental_period",
        ),
        CheckConstraint(
            "deposit IS NULL OR deposit >= 0",
            name="ck_properties_deposit_nonnegative",
        ),
        CheckConstraint(
            "floor_area IS NULL OR floor_area > 0",
            name="ck_properties_floor_area_positive",
        ),
        CheckConstraint(
            "land_area IS NULL OR land_area > 0",
            name="ck_properties_land_area_positive",
        ),
        CheckConstraint(
            "floor_area_unit IN ('sqm', 'sqft')",
            name="ck_properties_floor_area_unit",
        ),
        CheckConstraint(
            "land_area_unit IN ('sqm', 'sqft', 'acre', 'hectare')",
            name="ck_properties_land_area_unit",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="MWK")
    city = Column(String, nullable=False, index=True)
    property_type = Column(String, nullable=False)
    intent = Column(String(8), nullable=False, default="sale", server_default="sale")
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    negotiable = Column(Boolean, nullable=False, default=False, server_default="false")
    rental_period = Column(String(16), nullable=True)
    deposit = Column(Numeric(12, 2), nullable=True)
    floor_area = Column(Numeric(12, 2), nullable=True)
    floor_area_unit = Column(
        String(8), nullable=False, default="sqm", server_default="sqm"
    )
    land_area = Column(Numeric(12, 2), nullable=True)
    land_area_unit = Column(
        String(8), nullable=False, default="sqm", server_default="sqm"
    )
    amenities = Column(JSON, nullable=False, default=list)
    utilities = Column(JSON, nullable=False, default=list)
    district = Column(String, nullable=True)
    neighborhood = Column(String, nullable=True)
    available_from = Column(Date, nullable=True)
    advertiser_name = Column(String, nullable=True)
    contact_phone = Column(String(32), nullable=True)
    contact_email = Column(String(254), nullable=True)
    show_contact_details = Column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cover_image_id = Column(
        Integer,
        ForeignKey(
            "property_images.id",
            name="fk_properties_cover_image_id_property_images",
            ondelete="SET NULL",
            use_alter=True,
        ),
        nullable=True,
    )
    status = Column(
        String(24),
        nullable=False,
        default=PropertyStatus.DRAFT.value,
        server_default=PropertyStatus.DRAFT.value,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner = relationship("User", backref="properties")
    images = relationship(
        "PropertyImage",
        back_populates="property",
        foreign_keys="PropertyImage.property_id",
        cascade="all, delete-orphan",
    )
