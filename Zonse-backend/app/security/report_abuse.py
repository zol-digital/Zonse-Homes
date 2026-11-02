from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import ipaddress
import math
import struct

from fastapi import HTTPException, Request, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.report import PropertyReport

REPORT_WINDOW = timedelta(hours=24)
USER_REPORT_LIMIT = 3
IP_REPORT_LIMIT = 10


def digest_reporter_ip(request: Request) -> str:
    if request.client is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine report submission source",
        )

    try:
        normalized_ip = str(ipaddress.ip_address(request.client.host))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine report submission source",
        ) from exc

    return hmac.new(
        settings.REPORT_IP_HASH_SECRET.encode("utf-8"),
        normalized_ip.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def _lock_key(scope: str, value: str) -> tuple[int, int]:
    lock_digest = hashlib.sha256(f"report:{scope}:{value}".encode("utf-8")).digest()
    return struct.unpack(">ii", lock_digest[:8])


def lock_report_rate_subjects(
    db: Session,
    *,
    reporter_user_id: int | None,
    reporter_ip_digest: str,
) -> None:
    if db.bind is None or db.bind.dialect.name != "postgresql":
        return

    subjects = [("ip", reporter_ip_digest)]
    if reporter_user_id is not None:
        subjects.append(("user", str(reporter_user_id)))

    lock_keys = sorted(_lock_key(scope, value) for scope, value in subjects)
    for key_one, key_two in lock_keys:
        db.execute(
            text("SELECT pg_advisory_xact_lock(:key_one, :key_two)"),
            {"key_one": key_one, "key_two": key_two},
        )


def reject_if_report_limit_reached(
    db: Session,
    *,
    reporter_user_id: int | None,
    reporter_ip_digest: str,
    now: datetime | None = None,
) -> None:
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - REPORT_WINDOW
    active_limits: list[tuple[int, datetime]] = []

    def count_since(statement) -> tuple[int, datetime | None]:
        count, oldest = db.execute(statement).one()
        if oldest is not None and oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=timezone.utc)
        return count, oldest

    if reporter_user_id is not None:
        user_count, oldest_user_report = count_since(
            select(
                func.count(PropertyReport.id),
                func.min(PropertyReport.created_at),
            ).where(
                PropertyReport.reporter_user_id == reporter_user_id,
                PropertyReport.created_at >= cutoff,
            )
        )
        if user_count >= USER_REPORT_LIMIT and oldest_user_report is not None:
            active_limits.append((USER_REPORT_LIMIT, oldest_user_report))

    ip_count, oldest_ip_report = count_since(
        select(
            func.count(PropertyReport.id),
            func.min(PropertyReport.created_at),
        ).where(
            PropertyReport.reporter_ip_digest == reporter_ip_digest,
            PropertyReport.created_at >= cutoff,
        )
    )
    if ip_count >= IP_REPORT_LIMIT and oldest_ip_report is not None:
        active_limits.append((IP_REPORT_LIMIT, oldest_ip_report))

    if not active_limits:
        return

    retry_at = max(oldest + REPORT_WINDOW for _, oldest in active_limits)
    retry_after = max(1, math.ceil((retry_at - current_time).total_seconds()))
    db.rollback()
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Report submission limit reached. Try again later.",
        headers={"Retry-After": str(retry_after)},
    )
