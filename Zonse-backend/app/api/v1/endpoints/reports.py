from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property, PropertyStatus
from app.models.report import PropertyReport, ReportStatus
from app.models.user import User
from app.schemas.report import (
    PropertyReportAcknowledgement,
    PropertyReportCreate,
)
from app.security.csrf import validate_csrf_origin
from app.security.report_abuse import (
    digest_reporter_ip,
    lock_report_rate_subjects,
    reject_if_report_limit_reached,
)
from app.security.sessions import get_optional_current_user

router = APIRouter(
    prefix="/properties/{property_id}/reports",
    dependencies=[Depends(validate_csrf_origin)],
)

_OPEN_STATUSES = (
    ReportStatus.NEW.value,
    ReportStatus.INVESTIGATING.value,
    ReportStatus.ESCALATED.value,
)


def _normalized_description(description: str | None) -> str | None:
    if description is None:
        return None
    return re.sub(r"\s+", " ", description).strip().casefold()


def _same_reporter_filters(
    *,
    reporter_user_id: int | None,
    reporter_ip_digest: str,
):
    if reporter_user_id is not None:
        return (PropertyReport.reporter_user_id == reporter_user_id,)
    return (
        PropertyReport.reporter_user_id.is_(None),
        PropertyReport.reporter_ip_digest == reporter_ip_digest,
    )


def _reject_duplicate_report(
    db: Session,
    *,
    listing_id: int,
    reporter_user_id: int | None,
    reporter_ip_digest: str,
    reason_code: str,
    description: str | None,
) -> None:
    reporter_filters = _same_reporter_filters(
        reporter_user_id=reporter_user_id,
        reporter_ip_digest=reporter_ip_digest,
    )
    prior_reports = list(
        db.execute(
            select(PropertyReport)
            .where(
                PropertyReport.listing_id == listing_id,
                *reporter_filters,
            )
            .order_by(PropertyReport.created_at.desc())
            .with_for_update()
        ).scalars()
    )

    if any(report.status in _OPEN_STATUSES for report in prior_reports):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A report for this listing is already under review.",
        )

    normalized_description = _normalized_description(description)
    if any(
        report.reason_code == reason_code
        and _normalized_description(report.description) == normalized_description
        for report in prior_reports
    ):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This report duplicates a previously submitted issue.",
        )


@router.post(
    "",
    response_model=PropertyReportAcknowledgement,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_property_report(
    property_id: int,
    payload: PropertyReportCreate,
    request: Request,
    reporter: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> PropertyReportAcknowledgement:
    reporter_ip_digest = digest_reporter_ip(request)
    reporter_user_id = reporter.id if reporter is not None else None
    lock_report_rate_subjects(
        db,
        reporter_user_id=reporter_user_id,
        reporter_ip_digest=reporter_ip_digest,
    )

    listing = db.execute(
        select(Property)
        .where(
            Property.id == property_id,
            Property.status == PropertyStatus.PUBLISHED.value,
        )
        .with_for_update()
    ).scalar_one_or_none()
    if listing is None:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    _reject_duplicate_report(
        db,
        listing_id=listing.id,
        reporter_user_id=reporter_user_id,
        reporter_ip_digest=reporter_ip_digest,
        reason_code=payload.reason_code,
        description=payload.description,
    )
    reject_if_report_limit_reached(
        db,
        reporter_user_id=reporter_user_id,
        reporter_ip_digest=reporter_ip_digest,
    )

    report = PropertyReport(
        listing_id=listing.id,
        reported_user_id=listing.owner_id,
        reporter_user_id=reporter_user_id,
        reporter_ip_digest=reporter_ip_digest,
        reason_code=payload.reason_code,
        description=payload.description,
        status=ReportStatus.NEW.value,
        created_at=datetime.now(timezone.utc),
    )
    db.add(report)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A duplicate report has already been submitted.",
        ) from exc
    except SQLAlchemyError:
        db.rollback()
        raise

    return PropertyReportAcknowledgement(message="Report received. Thank you.")
