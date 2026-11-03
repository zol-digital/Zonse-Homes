"""Register all application models with SQLAlchemy metadata."""
from app.models.action_token import UserActionToken
from app.models.admin_audit import AdminActionLog
from app.models.featured import (
    FeaturedPlacementPackage,
    FeaturedPromotion,
    FeaturedPromotionEvent,
    FeaturedPromotionOrder,
    FeaturedPromotionSettings,
)
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
from app.models.moderation import ModerationActionLog
from app.models.property import Property
from app.models.reference_data import LocationReference, PropertyCategory
from app.models.report import PropertyReport
from app.models.session import UserSession
from app.models.user import User

__all__ = [
    "BusinessVerification",
    "BusinessVerificationReview",
    "AdminActionLog",
    "FeaturedPlacementPackage",
    "FeaturedPromotion",
    "FeaturedPromotionEvent",
    "FeaturedPromotionOrder",
    "FeaturedPromotionSettings",
    "Organization",
    "OrganizationMembership",
    "PropertyImage",
    "Property",
    "PropertyCategory",
    "LocationReference",
    "PropertyReport",
    "User",
    "UserActionToken",
    "UserSession",
    "UserRole",
    "ModerationActionLog",
    "VerificationDocument",
    "VerificationSubmission",
]
