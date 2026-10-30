from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="MWK")
    city = Column(String, nullable=False, index=True)  # e.g., Lilongwe, Blantyre
    property_type = Column(String, nullable=False)  # e.g., house, apartment, commercial, land
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", backref="properties")
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")