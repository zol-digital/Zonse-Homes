from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.featured import (
    FeaturedPlacementPackage,
    FeaturedPromotion,
    FeaturedPromotionEvent,
    FeaturedPromotionOrder,
    FeaturedPromotionSettings,
)
from app.models.property import Property, PropertyStatus
from app.models.user import User
from app.schemas.featured import (
    FeaturedOrderCreate,
    FeaturedOrderResponse,
    FeaturedPackageResponse,
    FeaturedPromotionEventRequest,
    FeaturedPromotionEventResponse,
    PaymentWebhookPayload,
)
from app.security.authorization import require_listing_manager
from app.security.csrf import validate_csrf_origin
from app.security.sessions import get_current_user

router = APIRouter(prefix="/featured", tags=["featured listings"])
logger = logging.getLogger(__name__)
_DURATION_DAYS = {"weekly": 7, "monthly": 30}
_PAYMENT_WEBHOOK_MAX_BYTES = 16_384


@router.get("/packages", response_model=list[FeaturedPackageResponse])
def list_available_packages(
    db: Session = Depends(get_db),
) -> list[FeaturedPlacementPackage]:
    statement = (
        select(FeaturedPlacementPackage)
        .where(FeaturedPlacementPackage.is_available.is_(True))
        .order_by(
            FeaturedPlacementPackage.placement_type,
            FeaturedPlacementPackage.duration,
        )
    )
    return list(db.execute(statement).scalars())


@router.post(
    "/orders",
    response_model=FeaturedOrderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(validate_csrf_origin)],
)
def create_featured_order(
    payload: FeaturedOrderCreate,
    user: User = Depends(require_listing_manager),
    db: Session = Depends(get_db),
) -> FeaturedPromotionOrder:
    listing = db.execute(
        select(Property)
        .where(
            Property.id == payload.listing_id,
            Property.owner_id == user.id,
        )
        .with_for_update()
    ).scalar_one_or_none()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    if listing.status != PropertyStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only approved, published listings may be promoted",
        )

    package = db.execute(
        select(FeaturedPlacementPackage)
        .where(
            FeaturedPlacementPackage.id == payload.package_id,
            FeaturedPlacementPackage.is_available.is_(True),
        )
        .with_for_update()
    ).scalar_one_or_none()
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Featured package not found or unavailable",
        )

    target_city = None
    target_district = None
    target_neighborhood = None
    if package.placement_type == "area":
        if payload.target_city is None or (
            payload.target_city.casefold() != listing.city.casefold()
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Area targeting must match the listing's city",
            )
        if payload.target_district is not None:
            if (
                listing.district is None
                or payload.target_district.casefold() != listing.district.casefold()
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Area targeting must match the listing's district",
                )
            target_district = listing.district
        if payload.target_neighborhood is not None:
            if (
                listing.neighborhood is None
                or payload.target_neighborhood.casefold()
                != listing.neighborhood.casefold()
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Area targeting must match the listing's neighborhood",
                )
            target_neighborhood = listing.neighborhood
        target_city = listing.city
    elif any(
        value is not None
        for value in (
            payload.target_city,
            payload.target_district,
            payload.target_neighborhood,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Homepage packages cannot have area targeting",
        )

    now = datetime.now(timezone.utc)
    active_promotion = db.execute(
        select(FeaturedPromotion.id).where(
            FeaturedPromotion.listing_id == listing.id,
            FeaturedPromotion.placement_type == package.placement_type,
            FeaturedPromotion.status == "active",
            FeaturedPromotion.expires_at > now,
        )
    ).scalar_one_or_none()
    if active_promotion is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This listing already has an active promotion in that placement",
        )

    order = FeaturedPromotionOrder(
        listing_id=listing.id,
        advertiser_id=user.id,
        package_id=package.id,
        placement_type=package.placement_type,
        duration=package.duration,
        amount=package.price,
        currency=package.currency,
        target_city=target_city,
        target_district=target_district,
        target_neighborhood=target_neighborhood,
    )
    try:
        db.add(order)
        db.commit()
        db.refresh(order)
    except SQLAlchemyError:
        db.rollback()
        raise
    return order


@router.get("/orders", response_model=list[FeaturedOrderResponse])
def list_my_featured_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_listing_manager),
    db: Session = Depends(get_db),
) -> list[FeaturedPromotionOrder]:
    statement = (
        select(FeaturedPromotionOrder)
        .where(FeaturedPromotionOrder.advertiser_id == user.id)
        .order_by(
            FeaturedPromotionOrder.created_at.desc(),
            FeaturedPromotionOrder.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars())


@router.post(
    "/promotions/{promotion_id}/events",
    response_model=FeaturedPromotionEventResponse,
    dependencies=[Depends(validate_csrf_origin)],
)
def record_promotion_event(
    promotion_id: int,
    payload: FeaturedPromotionEventRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FeaturedPromotionEventResponse:
    now = datetime.now(timezone.utc)
    promotion = db.execute(
        select(FeaturedPromotion)
        .join(Property, Property.id == FeaturedPromotion.listing_id)
        .where(
            FeaturedPromotion.id == promotion_id,
            FeaturedPromotion.status == "active",
            FeaturedPromotion.starts_at <= now,
            FeaturedPromotion.expires_at > now,
            Property.status == PropertyStatus.PUBLISHED.value,
        )
        .with_for_update()
    ).scalar_one_or_none()
    if promotion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active featured promotion not found",
        )

    event_date = now.date()
    existing = db.execute(
        select(FeaturedPromotionEvent.id).where(
            FeaturedPromotionEvent.promotion_id == promotion.id,
            FeaturedPromotionEvent.user_id == user.id,
            FeaturedPromotionEvent.event_type == payload.event_type,
            FeaturedPromotionEvent.event_date == event_date,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return FeaturedPromotionEventResponse(recorded=False)

    event = FeaturedPromotionEvent(
        promotion_id=promotion.id,
        user_id=user.id,
        event_type=payload.event_type,
        event_date=event_date,
    )
    if payload.event_type == "view":
        promotion.views_count += 1
    else:
        promotion.interactions_count += 1
    try:
        db.add(event)
        db.commit()
    except IntegrityError:
        db.rollback()
        duplicate = db.execute(
            select(FeaturedPromotionEvent.id).where(
                FeaturedPromotionEvent.promotion_id == promotion_id,
                FeaturedPromotionEvent.user_id == user.id,
                FeaturedPromotionEvent.event_type == payload.event_type,
                FeaturedPromotionEvent.event_date == event_date,
            )
        ).scalar_one_or_none()
        if duplicate is not None:
            return FeaturedPromotionEventResponse(recorded=False)
        raise
    except SQLAlchemyError:
        db.rollback()
        raise
    return FeaturedPromotionEventResponse(recorded=True)


@router.post(
    "/payment-webhook",
    status_code=status.HTTP_200_OK,
    summary="Confirm a featured-listing payment using a signed gateway event",
)
async def confirm_featured_payment(
    request: Request,
    x_payment_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    secret = settings.FEATURED_PAYMENT_WEBHOOK_SECRET.encode("utf-8")
    if len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Featured payment confirmation is not configured",
        )
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > _PAYMENT_WEBHOOK_MAX_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Payment event is too large",
                )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content length",
            ) from exc

    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > _PAYMENT_WEBHOOK_MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Payment event is too large",
            )
        body.extend(chunk)
    raw_body = bytes(body)
    signature = (x_payment_signature or "").strip()
    if signature.startswith("sha256="):
        signature = signature.removeprefix("sha256=")
    expected_signature = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid payment signature",
        )
    try:
        event = PaymentWebhookPayload.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid payment event",
        ) from exc

    order = db.execute(
        select(FeaturedPromotionOrder)
        .where(FeaturedPromotionOrder.id == event.order_id)
        .with_for_update()
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Featured order not found",
        )
    if event.amount != order.amount or event.currency != order.currency:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment amount or currency does not match the order",
        )

    if event.status == "failed":
        if order.payment_status == "pending":
            order.payment_status = "failed"
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
        return {"received": True}

    if (
        order.payment_status == "paid"
        and order.payment_reference != event.payment_reference
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order was confirmed with a different payment reference",
        )
    existing_order_promotion = db.execute(
        select(FeaturedPromotion.id).where(
            FeaturedPromotion.order_id == order.id
        )
    ).scalar_one_or_none()
    if existing_order_promotion is not None:
        return {"received": True}
    order.payment_status = "paid"
    order.payment_reference = event.payment_reference
    order.fulfillment_status = "pending"
    now = datetime.now(timezone.utc)
    listing = db.execute(
        select(Property)
        .where(Property.id == order.listing_id)
        .with_for_update()
    ).scalar_one()

    if listing.status != PropertyStatus.PUBLISHED.value:
        order.fulfillment_status = "blocked"
    else:
        db.execute(
            update(FeaturedPromotion)
            .where(
                FeaturedPromotion.listing_id == listing.id,
                FeaturedPromotion.placement_type == order.placement_type,
                FeaturedPromotion.status == "active",
                FeaturedPromotion.expires_at <= now,
            )
            .values(status="expired")
        )
        active_promotion = db.execute(
            select(FeaturedPromotion.id).where(
                FeaturedPromotion.listing_id == listing.id,
                FeaturedPromotion.placement_type == order.placement_type,
                FeaturedPromotion.status == "active",
                FeaturedPromotion.expires_at > now,
            )
        ).scalar_one_or_none()
        if active_promotion is not None:
            order.fulfillment_status = "blocked"
        else:
            if order.placement_type == "homepage":
                promotion_settings = db.execute(
                    select(FeaturedPromotionSettings)
                    .where(FeaturedPromotionSettings.id == 1)
                    .with_for_update()
                ).scalar_one_or_none()
                if promotion_settings is None:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Featured placement settings are not initialized",
                    )
                inventory_limit = promotion_settings.homepage_inventory_limit
                if inventory_limit is not None:
                    active_count = db.execute(
                        select(func.count(FeaturedPromotion.id))
                        .join(Property, Property.id == FeaturedPromotion.listing_id)
                        .where(
                            FeaturedPromotion.placement_type == "homepage",
                            FeaturedPromotion.status == "active",
                            FeaturedPromotion.starts_at <= now,
                            FeaturedPromotion.expires_at > now,
                            Property.status == PropertyStatus.PUBLISHED.value,
                        )
                    ).scalar_one()
                    if active_count >= inventory_limit:
                        order.fulfillment_status = "blocked"

            if order.fulfillment_status != "blocked":
                duration = timedelta(days=_DURATION_DAYS[order.duration])
                promotion = FeaturedPromotion(
                    order_id=order.id,
                    listing_id=listing.id,
                    placement_type=order.placement_type,
                    target_city=order.target_city,
                    target_district=order.target_district,
                    target_neighborhood=order.target_neighborhood,
                    starts_at=now,
                    expires_at=now + duration,
                    status="active",
                )
                db.add(promotion)
                order.fulfillment_status = "fulfilled"

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.exception("Could not fulfill a confirmed featured promotion order")
        raise
    except SQLAlchemyError:
        db.rollback()
        raise
    return {"received": True}
