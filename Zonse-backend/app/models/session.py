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
from sqlalchemy.orm import relationship

from app.database import Base


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        CheckConstraint(
            "expires_at > created_at",
            name="ck_user_sessions_expiry_after_creation",
        ),
        UniqueConstraint("token_digest", name="uq_user_sessions_token_digest"),
        Index("ix_user_sessions_user_expires", "user_id", "expires_at"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_digest = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
