from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ModerationActionLog(Base):
    __tablename__ = "moderation_action_logs"
    __table_args__ = (
        CheckConstraint(
            "action IN ('approve', 'request_changes', 'reject', 'review_report')",
            name="ck_moderation_action_logs_action",
        ),
        CheckConstraint(
            "length(reason) >= 1",
            name="ck_moderation_action_logs_reason_not_empty",
        ),
        Index("ix_moderation_action_logs_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    listing_id = Column(
        Integer,
        ForeignKey(
            "properties.id",
            name="fk_moderation_action_logs_listing_id_properties",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    actor_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_moderation_action_logs_actor_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    report_id = Column(
        ForeignKey(
            "property_reports.id",
            name="fk_moderation_action_logs_report_id_property_reports",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    action = Column(String(32), nullable=False)
    reason = Column(String(255), nullable=False)
    previous_status = Column(String(24), nullable=False)
    new_status = Column(String(24), nullable=False)
    moderator_notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    listing = relationship("Property", backref="moderation_actions")
    actor = relationship("User", backref="moderation_actions")
    report = relationship("PropertyReport", backref="moderation_actions")
