from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import StringConstraints
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.api.v1.reference_data import require_active_category
from app.models.featured import FeaturedPromotion
from app.models.property import Property, PropertyStatus
from app.models.user import User
from app.schemas.property import PropertyType, PublicPropertyResponse
from app.security.sessions import get_current_user

router = APIRouter(prefix="/discovery/properties")
featured_router = APIRouter(prefix="/discovery/featured")

_SearchText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
_LocationFilter = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=list[PublicPropertyResponse])
def discover_properties(
    search: _SearchText | None = None,
    intent: Literal["sale", "rent"] | None = None,
    property_type: PropertyType | None = None,
    city: _LocationFilter | None = None,
    district: _LocationFilter | None = None,
    neighborhood: _LocationFilter | None = None,
    min_price: Annotated[
        Decimal | None, Query(gt=0, max_digits=12, decimal_places=2)
    ] = None,
    max_price: Annotated[
        Decimal | None, Query(gt=0, max_digits=12, decimal_places=2)
    ] = None,
    bedrooms: Annotated[int | None, Query(ge=0)] = None,
    bathrooms: Annotated[int | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> list[Property]:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price must be less than or equal to max_price",
        )

    has_location_context = any(
        value is not None for value in (city, district, neighborhood)
    )
    now = datetime.now(timezone.utc)
    area_promotion_id = (
        select(FeaturedPromotion.id)
        .where(
            FeaturedPromotion.listing_id == Property.id,
            FeaturedPromotion.placement_type == "area",
            FeaturedPromotion.status == "active",
            FeaturedPromotion.starts_at <= now,
            FeaturedPromotion.expires_at > now,
        )
    )
    if has_location_context:
        area_promotion_id = area_promotion_id.where(
            FeaturedPromotion.target_city == Property.city
        )
        if district is None:
            area_promotion_id = area_promotion_id.where(
                FeaturedPromotion.target_district.is_(None)
            )
        else:
            area_promotion_id = area_promotion_id.where(
                or_(
                    FeaturedPromotion.target_district.is_(None),
                    func.lower(FeaturedPromotion.target_district)
                    == func.lower(Property.district),
                )
            )
        if neighborhood is None:
            area_promotion_id = area_promotion_id.where(
                FeaturedPromotion.target_neighborhood.is_(None)
            )
        else:
            area_promotion_id = area_promotion_id.where(
                or_(
                    FeaturedPromotion.target_neighborhood.is_(None),
                    func.lower(FeaturedPromotion.target_neighborhood)
                    == func.lower(Property.neighborhood),
                )
            )
    else:
        area_promotion_id = area_promotion_id.where(False)
    area_promotion_id = area_promotion_id.limit(1).correlate(Property).scalar_subquery()
    area_promotion_expiry = (
        select(FeaturedPromotion.expires_at)
        .where(FeaturedPromotion.id == area_promotion_id)
        .scalar_subquery()
    )

    statement = (
        select(Property, area_promotion_expiry.label("featured_expires_at"))
        .options(selectinload(Property.images), selectinload(Property.owner))
        .where(
            Property.status == PropertyStatus.PUBLISHED.value,
            Property.moderator_hidden.is_(False),
        )
    )
    if search is not None:
        pattern = f"%{_escape_like(search)}%"
        statement = statement.where(
            or_(
                Property.title.ilike(pattern, escape="\\"),
                Property.description.ilike(pattern, escape="\\"),
                Property.city.ilike(pattern, escape="\\"),
                Property.district.ilike(pattern, escape="\\"),
                Property.neighborhood.ilike(pattern, escape="\\"),
            )
        )
    if intent is not None:
        statement = statement.where(Property.intent == intent)
    if property_type is not None:
        require_active_category(db, property_type)
        statement = statement.where(Property.property_type == property_type)
    if city is not None:
        statement = statement.where(
            Property.city.ilike(_escape_like(city), escape="\\")
        )
    if district is not None:
        statement = statement.where(
            Property.district.ilike(_escape_like(district), escape="\\")
        )
    if neighborhood is not None:
        statement = statement.where(
            Property.neighborhood.ilike(_escape_like(neighborhood), escape="\\")
        )
    if min_price is not None:
        statement = statement.where(Property.price >= min_price)
    if max_price is not None:
        statement = statement.where(Property.price <= max_price)
    if bedrooms is not None:
        statement = statement.where(Property.bedrooms == bedrooms)
    if bathrooms is not None:
        statement = statement.where(Property.bathrooms == bathrooms)

    statement = (
        statement.order_by(
            case((area_promotion_id.is_not(None), 0), else_=1),
            Property.created_at.desc().nulls_last(),
            Property.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    results = []
    for listing, featured_expires_at in db.execute(statement):
        listing.is_featured = featured_expires_at is not None
        listing.featured_placement = "area" if listing.is_featured else None
        listing.featured_expires_at = featured_expires_at
        results.append(listing)
    return results


@featured_router.get(
    "/homepage",
    response_model=list[PublicPropertyResponse],
)
def discover_homepage_featured_properties(
    limit: Annotated[int, Query(ge=1, le=24)] = 8,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Property]:
    now = datetime.now(timezone.utc)
    statement = (
        select(Property, FeaturedPromotion.expires_at)
        .join(
            FeaturedPromotion,
            FeaturedPromotion.listing_id == Property.id,
        )
        .options(selectinload(Property.images), selectinload(Property.owner))
        .where(
            Property.status == PropertyStatus.PUBLISHED.value,
            Property.moderator_hidden.is_(False),
            FeaturedPromotion.placement_type == "homepage",
            FeaturedPromotion.status == "active",
            FeaturedPromotion.starts_at <= now,
            FeaturedPromotion.expires_at > now,
        )
        .order_by(FeaturedPromotion.starts_at.desc(), FeaturedPromotion.id.desc())
        .limit(limit)
    )
    results = []
    for listing, featured_expires_at in db.execute(statement):
        listing.is_featured = True
        listing.featured_placement = "homepage"
        listing.featured_expires_at = featured_expires_at
        results.append(listing)
    return results
