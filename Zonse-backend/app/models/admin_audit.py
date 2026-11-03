from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.sql import func

from app.database import Base


class AdminActionLog(Base):
    __tablename__ = "admin_action_logs"
    __table_args__ = (
        CheckConstraint(
            "length(action) >= 1",
            name="ck_admin_action_logs_action_not_empty",
        ),
        CheckConstraint(
            "length(entity_type) >= 1",
            name="ck_admin_action_logs_entity_type_not_empty",
        ),
        Index("ix_admin_action_logs_created_at", "created_at"),
        Index("ix_admin_action_logs_entity", "entity_type", "entity_id"),
    )

    id = Column(Integer, primary_key=True)
    actor_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_admin_action_logs_actor_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    action = Column(String(64), nullable=False)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(String(80), nullable=False)
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
