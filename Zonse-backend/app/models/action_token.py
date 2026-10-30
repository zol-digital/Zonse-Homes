from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database import Base


class UserActionToken(Base):
    __tablename__ = "user_action_tokens"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('email_verification', 'password_recovery')",
            name="ck_user_action_tokens_purpose",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_user_action_tokens_expiry_after_creation",
        ),
        UniqueConstraint("token_digest", name="uq_user_action_tokens_token_digest"),
        Index(
            "ix_user_action_tokens_user_purpose_created",
            "user_id",
            "purpose",
            "created_at",
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    purpose = Column(String(32), nullable=False)
    token_digest = Column(String(64), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
