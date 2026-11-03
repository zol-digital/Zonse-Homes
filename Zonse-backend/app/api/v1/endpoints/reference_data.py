from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reference_data import LocationReference, PropertyCategory
from app.models.user import User
from app.schemas.reference_data import (
    LocationKind,
    LocationReferenceCreate,
    LocationReferenceResponse,
    LocationReferenceUpdate,
    PropertyCategoryCreate,
    PropertyCategoryResponse,
    PropertyCategoryUpdate,
)
from app.security.authorization import require_admin
from app.security.csrf import validate_csrf_origin
from app.services.admin_audit import record_admin_action

router = APIRouter(prefix="/reference")
admin_router = APIRouter(
    prefix="/admin/reference",
    dependencies=[Depends(validate_csrf_origin), Depends(require_admin)],
)

_PARENT_KINDS = {
    "region": None,
    "district": frozenset({"region"}),
    "city": frozenset({"district"}),
    "town": frozenset({"district"}),
    "neighborhood": frozenset({"city", "town"}),
}


def _commit(
    db: Session,
    *,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: int | str,
    before_data: dict | None,
    after_data: dict | None,
) -> None:
    try:
        record_admin_action(
            db,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_data=before_data,
            after_data=after_data,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reference data conflicts with an existing record",
        ) from exc
    except SQLAlchemyError:
        db.rollback()
        raise


def _get_location_or_404(db: Session, location_id: int) -> LocationReference:
    location = db.get(LocationReference, location_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
    return location


def _validate_location_parent(
    db: Session,
    *,
    kind: str,
    parent_id: int | None,
    active: bool = True,
) -> None:
    expected_parent_kinds = _PARENT_KINDS[kind]
    if expected_parent_kinds is None:
        if parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Regions cannot have a parent location",
            )
        return
    if parent_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{kind.capitalize()} locations require a parent",
        )

    parent = _get_location_or_404(db, parent_id)
    if parent.kind not in expected_parent_kinds:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{kind.capitalize()} locations require a valid parent type",
        )
    if active and not parent.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active location must have an active parent",
        )


@router.get("/categories", response_model=list[PropertyCategoryResponse])
def list_public_categories(
    db: Session = Depends(get_db),
) -> list[PropertyCategory]:
    statement = (
        select(PropertyCategory)
        .where(PropertyCategory.is_active.is_(True))
        .order_by(func.lower(PropertyCategory.name), PropertyCategory.slug)
    )
    return list(db.execute(statement).scalars())


@router.get("/locations", response_model=list[LocationReferenceResponse])
def list_public_locations(
    kind: LocationKind | None = None,
    parent_id: Annotated[int | None, Query(ge=1)] = None,
    db: Session = Depends(get_db),
) -> list[LocationReference]:
    statement = select(LocationReference).where(LocationReference.is_active.is_(True))
    if kind is not None:
        statement = statement.where(LocationReference.kind == kind)
    if parent_id is not None:
        statement = statement.where(LocationReference.parent_id == parent_id)
    statement = statement.order_by(
        LocationReference.kind,
        func.lower(LocationReference.name),
        LocationReference.id,
    )
    return list(db.execute(statement).scalars())


@admin_router.get("/categories", response_model=list[PropertyCategoryResponse])
def list_admin_categories(
    db: Session = Depends(get_db),
) -> list[PropertyCategory]:
    statement = select(PropertyCategory).order_by(
        func.lower(PropertyCategory.name), PropertyCategory.slug
    )
    return list(db.execute(statement).scalars())


@admin_router.post(
    "/categories",
    response_model=PropertyCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: PropertyCategoryCreate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PropertyCategory:
    category = PropertyCategory(**payload.model_dump())
    db.add(category)
    _commit(
        db,
        actor_id=actor.id,
        action="create",
        entity_type="property_category",
        entity_id=category.slug,
        before_data=None,
        after_data={"slug": category.slug, "name": category.name, "is_active": True},
    )
    db.refresh(category)
    return category


@admin_router.patch(
    "/categories/{category_slug}",
    response_model=PropertyCategoryResponse,
)
def update_category(
    category_slug: str,
    payload: PropertyCategoryUpdate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PropertyCategory:
    category = db.get(PropertyCategory, category_slug)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_active") is False and category.is_active:
        active_count = db.scalar(
            select(func.count(PropertyCategory.slug)).where(
                PropertyCategory.is_active.is_(True)
            )
        )
        if active_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="At least one property category must remain active",
            )
    previous_values = {
        "name": category.name,
        "is_active": category.is_active,
    }
    for field_name, value in changes.items():
        setattr(category, field_name, value)
    _commit(
        db,
        actor_id=actor.id,
        action="update",
        entity_type="property_category",
        entity_id=category.slug,
        before_data=previous_values,
        after_data={
            "name": category.name,
            "is_active": category.is_active,
        },
    )
    db.refresh(category)
    return category


@admin_router.get("/locations", response_model=list[LocationReferenceResponse])
def list_admin_locations(
    kind: LocationKind | None = None,
    parent_id: Annotated[int | None, Query(ge=1)] = None,
    db: Session = Depends(get_db),
) -> list[LocationReference]:
    statement = select(LocationReference)
    if kind is not None:
        statement = statement.where(LocationReference.kind == kind)
    if parent_id is not None:
        statement = statement.where(LocationReference.parent_id == parent_id)
    statement = statement.order_by(
        LocationReference.kind,
        func.lower(LocationReference.name),
        LocationReference.id,
    )
    return list(db.execute(statement).scalars())


@admin_router.post(
    "/locations",
    response_model=LocationReferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    payload: LocationReferenceCreate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> LocationReference:
    _validate_location_parent(
        db,
        kind=payload.kind,
        parent_id=payload.parent_id,
    )
    location = LocationReference(**payload.model_dump())
    db.add(location)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reference data conflicts with an existing record",
        ) from exc
    _commit(
        db,
        actor_id=actor.id,
        action="create",
        entity_type="location_reference",
        entity_id=location.id,
        before_data=None,
        after_data={
            "slug": location.slug,
            "name": location.name,
            "kind": location.kind,
            "parent_id": location.parent_id,
            "aliases": location.aliases,
            "is_active": location.is_active,
        },
    )
    db.refresh(location)
    return location


@admin_router.patch(
    "/locations/{location_id}",
    response_model=LocationReferenceResponse,
)
def update_location(
    location_id: int,
    payload: LocationReferenceUpdate,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> LocationReference:
    location = _get_location_or_404(db, location_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_active") is True and not location.is_active:
        _validate_location_parent(
            db,
            kind=location.kind,
            parent_id=location.parent_id,
        )
    if changes.get("is_active") is False and location.is_active:
        active_child_id = db.scalar(
            select(LocationReference.id)
            .where(
                LocationReference.parent_id == location.id,
                LocationReference.is_active.is_(True),
            )
            .limit(1)
        )
        if active_child_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deactivate active child locations first",
            )
    previous_values = {
        "name": location.name,
        "aliases": location.aliases,
        "is_active": location.is_active,
    }
    for field_name, value in changes.items():
        setattr(location, field_name, value)
    _commit(
        db,
        actor_id=actor.id,
        action="update",
        entity_type="location_reference",
        entity_id=location.id,
        before_data=previous_values,
        after_data={
            "name": location.name,
            "aliases": location.aliases,
            "is_active": location.is_active,
        },
    )
    db.refresh(location)
    return location
