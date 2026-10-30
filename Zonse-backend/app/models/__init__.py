"""Register all application models with SQLAlchemy metadata."""
from app.models.action_token import UserActionToken
from app.models.image import PropertyImage
from app.models.identity import (
    BusinessVerification,
    BusinessVerificationReview,
    Organization,
    OrganizationMembership,
    UserRole,
    VerificationDocument,
    VerificationSubmission,
)
from app.models.property import Property
from app.models.session import UserSession
from app.models.user import User

__all__ = [
    "BusinessVerification",
    "BusinessVerificationReview",
    "Organization",
    "OrganizationMembership",
    "PropertyImage",
    "Property",
    "User",
    "UserActionToken",
    "UserSession",
    "UserRole",
    "UserActionToken",
    "VerificationDocument",
    "VerificationSubmission",
]
