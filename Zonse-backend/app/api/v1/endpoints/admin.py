from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_audit import AdminActionLog
from app.models.featured import (
    FeaturedPlacementPackage,
    FeaturedPromotion,
    FeaturedPromotionOrder,
    FeaturedPromotionSettings,
)
from app.models.identity import UserRole
from app.models.moderation import ModerationActionLog
from app.models.property import Property, PropertyStatus, validate_property_status_transition
from app.models.report import PropertyReport, ReportStatus
from app.models.user import User
from app.schemas.property import PropertyResponse
from app.schemas.featured import (
    FeaturedCancellationRequest,
    FeaturedOrderAdminResponse,
    FeaturedPackageCreate,
    FeaturedPackageResponse,
    FeaturedPackageUpdate,
    FeaturedPromotionResponse,
    FeaturedSettingsResponse,
    FeaturedSettingsUpdate,
)
from app.schemas.report import (
    PropertyReportReviewResponse,
    ReportReviewRequest,
    ReportStatusValue,
)
from app.security.authorization import require_admin, require_moderator
from app.security.csrf import validate_csrf_origin
from app.security.sessions import revoke_all_user_sessions
from app.services.admin_audit import record_admin_action

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(validate_csrf_origin), Depends(require_moderator)],
)


def _validate_featured_package_pricing(
    db: Session,
    *,
    placement_type: str,
    duration: str,
    price: Decimal,
    currency: str,
    excluding_package_id: int | None = None,
) -> None:
    peer_type = "homepage" if placement_type == "area" else "area"
    statement = select(FeaturedPlacementPackage).where(
        FeaturedPlacementPackage.placement_type == peer_type,
        FeaturedPlacementPackage.duration == duration,
    )
    if excluding_package_id is not None:
        statement = statement.where(
            FeaturedPlacementPackage.id != excluding_package_id
        )
    peer = db.execute(statement).scalar_one_or_none()
    if peer is None:
        return
    if currency != peer.currency:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Placement prices for the same duration must use one currency",
        )
    if (
        placement_type == "homepage" and price <= peer.price
    ) or (
        placement_type == "area" and price >= peer.price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Homepage pricing must be higher than area pricing",
        )


class ModerationActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
    ]
    moderator_notes: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=0, max_length=2000),
    ] = None


class ModerationActionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    actor_id: int
    report_id: UUID | None = None
    action: str
    reason: str
    previous_status: str
    new_status: str
    moderator_notes: str | None = None
    created_at: datetime


class ModerationBacklogSummary(BaseModel):
    pending_listings: int
    open_reports: int
    total: int


class AdminDashboardResponse(BaseModel):
    listing_counts_by_status: dict[str, int]
    report_counts_by_status: dict[str, int]
    moderation_backlog: ModerationBacklogSummary


class AdminAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    account_status: str
    is_active: bool
    updated_at: datetime


class AdminActionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int
    action: str
    entity_type: str
    entity_id: str
    before_data: dict[str, Any] | None
    after_data: dict[str, Any] | None
    created_at: datetime


def _get_account_for_update(db: Session, user_id: int) -> User:
    account = db.execute(
        select(User).where(User.id == user_id).with_for_update()
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


@router.post(
    "/accounts/{user_id}/suspend",
    response_model=AdminAccountResponse,
)
def suspend_account(
    user_id: Annotated[int, Path(ge=1)],
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    active_admins = list(
        db.execute(
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .where(
                UserRole.role == "admin",
                User.account_status == "active",
                User.is_active.is_(True),
            )
            .order_by(User.id)
            .with_for_update()
        ).scalars()
    )
    account = _get_account_for_update(db, user_id)
    if account.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Administrators cannot suspend their own account",
        )
    if account.account_status != "active" or not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active accounts can be suspended",
        )
    if account in active_admins and len(active_admins) <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The last active administrator cannot be suspended",
        )

    previous_values = {
        "account_status": account.account_status,
        "is_active": account.is_active,
    }
    account.account_status = "suspended"
    revoke_all_user_sessions(db, account.id, commit=False)
    record_admin_action(
        db,
        actor_id=actor.id,
        action="suspend",
        entity_type="user",
        entity_id=account.id,
        before_data=previous_values,
        after_data={
            "account_status": account.account_status,
            "is_active": account.is_active,
        },
    )
    try:
        db.commit()
        db.refresh(account)
    except SQLAlchemyError:
        db.rollback()
        raise
    return account


@router.post(
    "/accounts/{user_id}/restore",
    response_model=AdminAccountResponse,
)
def restore_account(
    user_id: Annotated[int, Path(ge=1)],
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    account = _get_account_for_update(db, user_id)
    if account.account_status != "suspended":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only suspended accounts can be restored",
        )
    if not account.is_active or account.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account cannot be restored until its existing requirements are met",
        )

    previous_values = {
        "account_status": account.account_status,
        "is_active": account.is_active,
    }
    account.account_status = "active"
    record_admin_action(
        db,
        actor_id=actor.id,
        action="restore",
        entity_type="user",
        entity_id=account.id,
        before_data=previous_values,
        after_data={
            "account_status": account.account_status,
            "is_active": account.is_active,
        },
    )
    try:
        db.commit()
        db.refresh(account)
    except SQLAlchemyError:
        db.rollback()
        raise
    return account


def _get_listing_or_404(db: Session, property_id: int) -> Property:
    statement = (
        select(Property)
        .where(Property.id == property_id)
        .with_for_update()
    )
    listing = db.execute(statement).scalar_one_or_none()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    return listing


def _apply_listing_action(
    db: Session,
    listing: Property,
    actor: User,
    action: str,
    target_status: PropertyStatus,
    reason: str,
    moderator_notes: str | None = None,
) -> Property:
    try:
        validate_property_status_transition(listing.status, target_status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing status transition is not permitted",
        ) from exc

    previous_status = listing.status
    listing.status = target_status.value
    if target_status is PropertyStatus.REMOVED:
        listing.moderator_hidden = False
    entry = ModerationActionLog(
        listing_id=listing.id,
        actor_id=actor.id,
        action=action,
        reason=reason,
        previous_status=previous_status,
        new_status=target_status.value,
        moderator_notes=moderator_notes,
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(listing)
    except SQLAlchemyError:
        db.rollback()
        raise
    return listing


def _record_visibility_action(
    db: Session,
    listing: Property,
    actor: User,
    *,
    action: str,
    reason: str,
    moderator_notes: str | None = None,
) -> Property:
    entry = ModerationActionLog(
        listing_id=listing.id,
        actor_id=actor.id,
        action=action,
        reason=reason,
        previous_status=listing.status,
        new_status=listing.status,
        moderator_notes=moderator_notes,
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(listing)
    except SQLAlchemyError:
        db.rollback()
        raise
    return listing


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    _user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminDashboardResponse:
    listing_counts = {listing_status.value: 0 for listing_status in PropertyStatus}
    for listing_status, count in db.execute(
        select(Property.status, func.count(Property.id)).group_by(Property.status)
    ):
        listing_counts[listing_status] = count

    report_counts = {report_status.value: 0 for report_status in ReportStatus}
    for report_status, count in db.execute(
        select(PropertyReport.status, func.count(PropertyReport.id)).group_by(
            PropertyReport.status
        )
    ):
        report_counts[report_status] = count

    pending_listings = listing_counts[PropertyStatus.PENDING_REVIEW.value]
    open_reports = sum(
        report_counts[report_status.value]
        for report_status in (
            ReportStatus.NEW,
            ReportStatus.INVESTIGATING,
            ReportStatus.ESCALATED,
        )
    )
    return AdminDashboardResponse(
        listing_counts_by_status=listing_counts,
        report_counts_by_status=report_counts,
        moderation_backlog=ModerationBacklogSummary(
            pending_listings=pending_listings,
            open_reports=open_reports,
            total=pending_listings + open_reports,
        ),
    )


@router.get("/moderation/listings", response_model=list[PropertyResponse])
def list_moderation_queue(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Property]:
    statement = (
        select(Property)
        .where(Property.status == PropertyStatus.PENDING_REVIEW.value)
        .order_by(Property.updated_at.desc().nulls_last(), Property.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars())


@router.get("/audit-logs", response_model=list[ModerationActionLogResponse])
def list_audit_logs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[ModerationActionLog]:
    statement = select(ModerationActionLog).order_by(
        ModerationActionLog.created_at.desc(),
        ModerationActionLog.id.desc(),
    ).limit(limit).offset(offset)
    return list(db.execute(statement).scalars())


@router.get(
    "/action-logs",
    response_model=list[AdminActionLogResponse],
)
def list_admin_action_logs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminActionLog]:
    statement = (
        select(AdminActionLog)
        .order_by(AdminActionLog.created_at.desc(), AdminActionLog.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars())


@router.get("/reports", response_model=list[PropertyReportReviewResponse])
def list_property_reports(
    report_status: ReportStatusValue | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[PropertyReport]:
    statement = select(PropertyReport).order_by(
        PropertyReport.created_at.asc(),
        PropertyReport.id.asc(),
    )
    if report_status is not None:
        statement = statement.where(PropertyReport.status == report_status)
    else:
        statement = statement.where(
            PropertyReport.status.in_(
                (
                    ReportStatus.NEW.value,
                    ReportStatus.INVESTIGATING.value,
                    ReportStatus.ESCALATED.value,
                )
            )
        )
    statement = statement.limit(limit).offset(offset)
    return list(db.execute(statement).scalars())


@router.post(
    "/reports/{report_id}/resolve",
    response_model=PropertyReportReviewResponse,
)
def review_property_report(
    report_id: UUID,
    payload: ReportReviewRequest,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
) -> PropertyReport:
    report = db.execute(
        select(PropertyReport)
        .where(PropertyReport.id == report_id)
        .with_for_update()
    ).scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if report.status in {ReportStatus.ACTIONED.value, ReportStatus.DISMISSED.value}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolved reports cannot be changed",
        )
    if report.listing_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report is not associated with a listing",
        )

    previous_status = report.status
    report.status = payload.status
    report.assigned_to_user_id = user.id
    report.resolution_code = payload.resolution_code
    report.resolved_at = (
        datetime.now(timezone.utc)
        if payload.status in {ReportStatus.ACTIONED.value, ReportStatus.DISMISSED.value}
        else None
    )
    db.add(
        ModerationActionLog(
            listing_id=report.listing_id,
            actor_id=user.id,
            report_id=report.id,
            action="review_report",
            reason=payload.reason,
            previous_status=previous_status,
            new_status=report.status,
            moderator_notes=payload.moderator_notes,
        )
    )
    try:
        db.commit()
        db.refresh(report)
    except SQLAlchemyError:
        db.rollback()
        raise
    return report


@router.post("/listings/{property_id}/approve", response_model=PropertyResponse)
def approve_listing(
    property_id: int,
    payload: ModerationActionRequest,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
) -> Property:
    listing = _get_listing_or_404(db, property_id)
    return _apply_listing_action(
        db,
        listing,
        user,
        "approve",
        PropertyStatus.PUBLISHED,
        payload.reason,
        payload.moderator_notes,
    )


@router.post("/listings/{property_id}/request-changes", response_model=PropertyResponse)
def request_changes_for_listing(
    property_id: int,
    payload: ModerationActionRequest,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
) -> Property:
    listing = _get_listing_or_404(db, property_id)
    return _apply_listing_action(
        db,
        listing,
        user,
        "request_changes",
        PropertyStatus.CHANGES_REQUESTED,
        payload.reason,
        payload.moderator_notes,
    )


@router.post("/listings/{property_id}/reject", response_model=PropertyResponse)
def reject_listing(
    property_id: int,
    payload: ModerationActionRequest,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
) -> Property:
    listing = _get_listing_or_404(db, property_id)
    return _apply_listing_action(
        db,
        listing,
        user,
        "reject",
        PropertyStatus.REJECTED,
        payload.reason,
        payload.moderator_notes,
    )


@router.post("/listings/{property_id}/remove", response_model=PropertyResponse)
def remove_listing(
    property_id: int,
    payload: ModerationActionRequest,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
) -> Property:
    listing = _get_listing_or_404(db, property_id)
    return _apply_listing_action(
        db,
        listing,
        user,
        "remove",
        PropertyStatus.REMOVED,
        payload.reason,
        payload.moderator_notes,
    )


@router.post("/listings/{property_id}/hide", response_model=PropertyResponse)
def hide_listing(
    property_id: int,
    payload: ModerationActionRequest,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
) -> Property:
    listing = _get_listing_or_404(db, property_id)
    if listing.moderator_hidden:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing is already hidden by moderation",
        )
    if listing.status != PropertyStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only published listings can be hidden by moderation",
        )

    listing.moderator_hidden = True
    return _record_visibility_action(
        db,
        listing,
        user,
        action="hide",
        reason=payload.reason,
        moderator_notes=payload.moderator_notes,
    )


@router.post("/listings/{property_id}/restore", response_model=PropertyResponse)
def restore_listing(
    property_id: int,
    payload: ModerationActionRequest,
    user: User = Depends(require_moderator),
    db: Session = Depends(get_db),
) -> Property:
    listing = _get_listing_or_404(db, property_id)
    if not listing.moderator_hidden:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing is not hidden by moderation",
        )
    if listing.status == PropertyStatus.REMOVED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permanently removed listings cannot be restored",
        )

    listing.moderator_hidden = False
    return _record_visibility_action(
        db,
        listing,
        user,
        action="restore",
        reason=payload.reason,
        moderator_notes=payload.moderator_notes,
    )


@router.get(
    "/featured/packages",
    response_model=list[FeaturedPackageResponse],
)
def list_featured_packages(
    _user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[FeaturedPlacementPackage]:
    statement = select(FeaturedPlacementPackage).order_by(
        FeaturedPlacementPackage.placement_type,
        FeaturedPlacementPackage.duration,
    )
    return list(db.execute(statement).scalars())


@router.post(
    "/featured/packages",
    response_model=FeaturedPackageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_featured_package(
    payload: FeaturedPackageCreate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> FeaturedPlacementPackage:
    _validate_featured_package_pricing(
        db,
        placement_type=payload.placement_type,
        duration=payload.duration,
        price=payload.price,
        currency=payload.currency,
    )
    package = FeaturedPlacementPackage(**payload.model_dump())
    try:
        db.add(package)
        db.flush()
        record_admin_action(
            db,
            actor_id=user.id,
            action="create",
            entity_type="featured_package",
            entity_id=package.id,
            before_data=None,
            after_data={
                "placement_type": package.placement_type,
                "duration": package.duration,
                "price": package.price,
                "currency": package.currency,
                "is_available": package.is_available,
            },
        )
        db.commit()
        db.refresh(package)
    except IntegrityError as exc:
        db.rollback()
        existing = db.execute(
            select(FeaturedPlacementPackage.id).where(
                FeaturedPlacementPackage.placement_type == payload.placement_type,
                FeaturedPlacementPackage.duration == payload.duration,
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A package already exists for that placement and duration",
            ) from exc
        raise
    except SQLAlchemyError:
        db.rollback()
        raise
    return package


@router.patch(
    "/featured/packages/{package_id}",
    response_model=FeaturedPackageResponse,
)
def update_featured_package(
    package_id: int,
    payload: FeaturedPackageUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> FeaturedPlacementPackage:
    package = db.execute(
        select(FeaturedPlacementPackage)
        .where(FeaturedPlacementPackage.id == package_id)
        .with_for_update()
    ).scalar_one_or_none()
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Featured package not found",
        )
    previous_values = {
        "placement_type": package.placement_type,
        "duration": package.duration,
        "price": package.price,
        "currency": package.currency,
        "is_available": package.is_available,
    }
    changes = payload.model_dump(exclude_unset=True)
    _validate_featured_package_pricing(
        db,
        placement_type=package.placement_type,
        duration=package.duration,
        price=changes.get("price", package.price),
        currency=changes.get("currency", package.currency),
        excluding_package_id=package.id,
    )
    for field_name, value in changes.items():
        setattr(package, field_name, value)
    record_admin_action(
        db,
        actor_id=user.id,
        action="update",
        entity_type="featured_package",
        entity_id=package.id,
        before_data=previous_values,
        after_data={
            "placement_type": package.placement_type,
            "duration": package.duration,
            "price": package.price,
            "currency": package.currency,
            "is_available": package.is_available,
        },
    )
    try:
        db.commit()
        db.refresh(package)
    except SQLAlchemyError:
        db.rollback()
        raise
    return package


@router.get(
    "/featured/settings",
    response_model=FeaturedSettingsResponse,
)
def get_featured_settings(
    _user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> FeaturedPromotionSettings:
    featured_settings = db.get(FeaturedPromotionSettings, 1)
    if featured_settings is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Featured placement settings are not initialized",
        )
    return featured_settings


@router.patch(
    "/featured/settings",
    response_model=FeaturedSettingsResponse,
)
def update_featured_settings(
    payload: FeaturedSettingsUpdate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> FeaturedPromotionSettings:
    featured_settings = db.execute(
        select(FeaturedPromotionSettings)
        .where(FeaturedPromotionSettings.id == 1)
        .with_for_update()
    ).scalar_one_or_none()
    if featured_settings is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Featured placement settings are not initialized",
        )
    previous_values = {
        "homepage_inventory_limit": featured_settings.homepage_inventory_limit,
    }
    featured_settings.homepage_inventory_limit = payload.homepage_inventory_limit
    record_admin_action(
        db,
        actor_id=user.id,
        action="update",
        entity_type="featured_settings",
        entity_id=featured_settings.id,
        before_data=previous_values,
        after_data={
            "homepage_inventory_limit": featured_settings.homepage_inventory_limit,
        },
    )
    try:
        db.commit()
        db.refresh(featured_settings)
    except SQLAlchemyError:
        db.rollback()
        raise
    return featured_settings


@router.get(
    "/featured/promotions",
    response_model=list[FeaturedPromotionResponse],
)
def list_featured_promotions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[FeaturedPromotion]:
    try:
        db.execute(
            update(FeaturedPromotion)
            .where(
                FeaturedPromotion.status == "active",
                FeaturedPromotion.expires_at <= datetime.now(timezone.utc),
            )
            .values(status="expired")
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    statement = (
        select(FeaturedPromotion)
        .order_by(
            FeaturedPromotion.created_at.desc(),
            FeaturedPromotion.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars())


@router.post(
    "/featured/promotions/{promotion_id}/cancel",
    response_model=FeaturedPromotionResponse,
)
def cancel_featured_promotion(
    promotion_id: int,
    payload: FeaturedCancellationRequest,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> FeaturedPromotion:
    promotion = db.execute(
        select(FeaturedPromotion)
        .where(FeaturedPromotion.id == promotion_id)
        .with_for_update()
    ).scalar_one_or_none()
    if promotion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Featured promotion not found",
        )
    now = datetime.now(timezone.utc)
    expires_at = promotion.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if promotion.status != "active" or expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only an active, unexpired promotion may be cancelled",
        )

    promotion.status = "cancelled"
    promotion.cancelled_at = now
    promotion.cancelled_by_user_id = user.id
    promotion.cancellation_reason = payload.reason
    record_admin_action(
        db,
        actor_id=user.id,
        action="cancel",
        entity_type="featured_promotion",
        entity_id=promotion.id,
        before_data={
            "status": "active",
            "cancellation_reason": None,
        },
        after_data={
            "status": promotion.status,
            "cancellation_reason": promotion.cancellation_reason,
        },
    )
    try:
        db.commit()
        db.refresh(promotion)
    except SQLAlchemyError:
        db.rollback()
        raise
    return promotion


@router.get(
    "/featured/orders",
    response_model=list[FeaturedOrderAdminResponse],
)
def list_featured_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[FeaturedPromotionOrder]:
    statement = (
        select(FeaturedPromotionOrder)
        .order_by(
            FeaturedPromotionOrder.created_at.desc(),
            FeaturedPromotionOrder.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars())
