from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import StringConstraints
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.property import Property, PropertyStatus
from app.schemas.property import PropertyType, PublicPropertyResponse

router = APIRouter(prefix="/discovery/properties")

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

    statement = (
        select(Property)
        .options(selectinload(Property.images))
        .where(Property.status == PropertyStatus.PUBLISHED.value)
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
            Property.created_at.desc().nulls_last(),
            Property.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars())
