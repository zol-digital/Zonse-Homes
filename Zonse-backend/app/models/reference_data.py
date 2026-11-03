from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.sql import func

from app.database import Base

DEFAULT_PROPERTY_CATEGORIES = {
    "house": "House",
    "apartment": "Apartment",
    "flat": "Flat",
    "plot": "Plot",
    "land": "Land",
    "commercial": "Commercial",
}


class PropertyCategory(Base):
    __tablename__ = "property_categories"

    slug = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class LocationReference(Base):
    __tablename__ = "location_references"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('region', 'district', 'city', 'town', 'neighborhood')",
            name="ck_location_references_kind",
        ),
    )

    id = Column(Integer, primary_key=True)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    kind = Column(String(20), nullable=False)
    parent_id = Column(
        Integer,
        ForeignKey(
            "location_references.id",
            name="fk_location_references_parent_id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )
    aliases = Column(JSON, nullable=False, default=list, server_default="[]")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
