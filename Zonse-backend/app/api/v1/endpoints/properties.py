from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import (
    Property,
    PropertyStatus,
    validate_property_status_transition,
)
from app.models.user import User
from app.schemas.property import PropertyCreate, PropertyResponse, PropertyUpdate
from app.security.authorization import require_listing_manager, require_property_owner
from app.security.csrf import validate_csrf_origin

router = APIRouter(
    prefix="/properties",
    dependencies=[Depends(validate_csrf_origin), Depends(require_listing_manager)],
)

_EDITABLE_STATUSES = frozenset(
    {PropertyStatus.DRAFT, PropertyStatus.CHANGES_REQUESTED}
)


def _save_listing(db: Session, listing: Property) -> Property:
    try:
        db.add(listing)
        db.commit()
        db.refresh(listing)
    except SQLAlchemyError:
        db.rollback()
        raise
    return listing


def _transition_listing(
    db: Session,
    listing: Property,
    target_status: PropertyStatus,
) -> Property:
    try:
        validate_property_status_transition(listing.status, target_status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing status transition is not permitted",
        ) from exc

    listing.status = target_status.value
    return _save_listing(db, listing)


@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: PropertyCreate,
    user: User = Depends(require_listing_manager),
    db: Session = Depends(get_db),
) -> Property:
    listing = Property(**payload.model_dump(), owner_id=user.id)
    return _save_listing(db, listing)


@router.get("", response_model=list[PropertyResponse])
def list_my_listings(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_listing_manager),
    db: Session = Depends(get_db),
) -> list[Property]:
    statement = (
        select(Property)
        .where(Property.owner_id == user.id)
        .order_by(Property.created_at.desc().nulls_last(), Property.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars())


@router.get("/{property_id}", response_model=PropertyResponse)
def get_listing(
    listing: Property = Depends(require_property_owner),
) -> Property:
    return listing


@router.patch("/{property_id}", response_model=PropertyResponse)
def update_listing(
    payload: PropertyUpdate,
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> Property:
    if PropertyStatus(listing.status) not in _EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing cannot be edited in its current status",
        )

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(listing, field_name, value)
    return _save_listing(db, listing)


@router.post("/{property_id}/submit", response_model=PropertyResponse)
def submit_listing(
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> Property:
    return _transition_listing(db, listing, PropertyStatus.PENDING_REVIEW)


@router.post("/{property_id}/pause", response_model=PropertyResponse)
def pause_listing(
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> Property:
    return _transition_listing(db, listing, PropertyStatus.PAUSED)


@router.post("/{property_id}/mark-rented", response_model=PropertyResponse)
def mark_listing_rented(
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> Property:
    if listing.intent != "rent":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only rental listings can be marked rented",
        )
    return _transition_listing(db, listing, PropertyStatus.RENTED)


@router.post("/{property_id}/mark-sold", response_model=PropertyResponse)
def mark_listing_sold(
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> Property:
    if listing.intent != "sale":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only sale listings can be marked sold",
        )
    return _transition_listing(db, listing, PropertyStatus.SOLD)


@router.post("/{property_id}/archive", response_model=PropertyResponse)
def archive_listing(
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> Property:
    return _transition_listing(db, listing, PropertyStatus.ARCHIVED)
