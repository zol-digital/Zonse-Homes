import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.database import get_db
from app.models.image import PropertyImage
from app.models.property import (
    Property,
    PropertyStatus,
    validate_property_status_transition,
)
from app.models.user import User
from app.schemas.property import (
    PropertyCreate,
    PropertyImageResponse,
    PropertyResponse,
    PropertyUpdate,
)
from app.security.authorization import require_listing_manager, require_property_owner
from app.security.csrf import validate_csrf_origin
from app.storage import managed_image_path, store_property_image

router = APIRouter(
    prefix="/properties",
    dependencies=[Depends(validate_csrf_origin), Depends(require_listing_manager)],
)

_EDITABLE_STATUSES = frozenset(
    {PropertyStatus.DRAFT, PropertyStatus.CHANGES_REQUESTED}
)
logger = logging.getLogger(__name__)


def _require_editable_listing(listing: Property) -> None:
    if PropertyStatus(listing.status) not in _EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing cannot be edited in its current status",
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
    _require_editable_listing(listing)

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(listing, field_name, value)
    return _save_listing(db, listing)


@router.post(
    "/{property_id}/images",
    response_model=PropertyImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_property_image(
    image_file: UploadFile = File(...),
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> PropertyImage:
    _require_editable_listing(listing)
    image_url, stored_path = store_property_image(image_file)
    image = PropertyImage(
        property_id=listing.id,
        image_url=image_url,
        is_primary=False,
    )
    try:
        db.add(image)
        db.flush()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Could not remove a property image after database failure")
        raise
    return image


@router.put(
    "/{property_id}/images/{image_id}/cover",
    response_model=PropertyResponse,
)
def select_cover_image(
    image_id: int,
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> Property:
    _require_editable_listing(listing)
    images = list(
        db.execute(
            select(PropertyImage).where(PropertyImage.property_id == listing.id)
        ).scalars()
    )
    selected_image = next((image for image in images if image.id == image_id), None)
    if selected_image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    listing.cover_image_id = selected_image.id
    for image in images:
        image.is_primary = image.id == selected_image.id
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return listing


@router.delete(
    "/{property_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_property_image(
    image_id: int,
    listing: Property = Depends(require_property_owner),
    db: Session = Depends(get_db),
) -> Response:
    _require_editable_listing(listing)
    image = db.execute(
        select(PropertyImage).where(
            PropertyImage.id == image_id,
            PropertyImage.property_id == listing.id,
        )
    ).scalar_one_or_none()
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    stored_path = managed_image_path(image.image_url)
    staged_delete_path = None
    if stored_path is not None:
        staged_delete_path = stored_path.with_name(
            f".{stored_path.name}.{uuid4().hex}.deleting"
        )
        try:
            stored_path.rename(staged_delete_path)
        except FileNotFoundError:
            staged_delete_path = None

    if listing.cover_image_id == image.id:
        listing.cover_image_id = None
    try:
        db.delete(image)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        if staged_delete_path is not None:
            try:
                staged_delete_path.rename(stored_path)
            except OSError:
                logger.exception("Could not restore a property image after rollback")
        raise

    if staged_delete_path is not None:
        try:
            staged_delete_path.unlink(missing_ok=True)
        except OSError as exc:
            logger.exception("Could not remove a deleted property image file")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image record was removed but file cleanup failed",
            ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
