"""Register all application models with SQLAlchemy metadata."""

from app.models.image import PropertyImage
from app.models.property import Property
from app.models.user import User

__all__ = ["PropertyImage", "Property", "User"]
