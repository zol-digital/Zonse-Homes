from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReportReason(StrEnum):
    SUSPECTED_SCAM = "suspected_scam"
    DUPLICATE = "duplicate"
    MISLEADING_DETAILS = "misleading_details"
    WRONG_PRICE = "wrong_price"
    UNAVAILABLE = "unavailable"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    OTHER = "other"


class ReportStatus(StrEnum):
    NEW = "new"
    INVESTIGATING = "investigating"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


_OPEN_STATUSES = "'new', 'investigating', 'escalated'"


class PropertyReport(Base):
    __tablename__ = "property_reports"
    __table_args__ = (
        CheckConstraint(
            "reason_code IN "
            "('suspected_scam', 'duplicate', 'misleading_details', "
            "'wrong_price', 'unavailable', 'inappropriate_content', 'other')",
            name="ck_property_reports_reason_code",
        ),
        CheckConstraint(
            "status IN ('new', 'investigating', 'actioned', 'dismissed', 'escalated')",
            name="ck_property_reports_status",
        ),
        Index(
            "ix_property_reports_status_created_at",
            "status",
            "created_at",
        ),
        Index(
            "ix_property_reports_listing_id",
            "listing_id",
        ),
        Index(
            "ix_property_reports_reporter_user_created_at",
            "reporter_user_id",
            "created_at",
        ),
        Index(
            "ix_property_reports_reporter_ip_created_at",
            "reporter_ip_digest",
            "created_at",
        ),
        Index(
            "uq_property_reports_open_user_listing",
            "listing_id",
            "reporter_user_id",
            unique=True,
            postgresql_where=text(
                f"reporter_user_id IS NOT NULL AND status IN ({_OPEN_STATUSES})"
            ),
            sqlite_where=text(
                f"reporter_user_id IS NOT NULL AND status IN ({_OPEN_STATUSES})"
            ),
        ),
        Index(
            "uq_property_reports_open_guest_listing",
            "listing_id",
            "reporter_ip_digest",
            unique=True,
            postgresql_where=text(
                f"reporter_user_id IS NULL AND status IN ({_OPEN_STATUSES})"
            ),
            sqlite_where=text(
                f"reporter_user_id IS NULL AND status IN ({_OPEN_STATUSES})"
            ),
        ),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    listing_id = Column(
        ForeignKey(
            "properties.id",
            name="fk_property_reports_listing_id_properties",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    reported_user_id = Column(
        ForeignKey(
            "users.id",
            name="fk_property_reports_reported_user_id_users",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    reporter_user_id = Column(
        ForeignKey(
            "users.id",
            name="fk_property_reports_reporter_user_id_users",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    reporter_ip_digest = Column(String(64), nullable=False)
    reason_code = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(24),
        nullable=False,
        default=ReportStatus.NEW.value,
        server_default=ReportStatus.NEW.value,
    )
    assigned_to_user_id = Column(
        ForeignKey(
            "users.id",
            name="fk_property_reports_assigned_to_user_id_users",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    resolution_code = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    listing = relationship("Property", backref="reports")
    reporter = relationship("User", foreign_keys=[reporter_user_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
