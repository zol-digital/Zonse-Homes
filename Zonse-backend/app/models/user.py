from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Index, Integer, String, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "account_status IN "
            "('pending_verification', 'active', 'suspended', 'disabled')",
            name="ck_users_account_status",
        ),
        CheckConstraint(
            "account_status != 'active' OR email_verified_at IS NOT NULL",
            name="ck_users_active_requires_verified_email",
        ),
        CheckConstraint(
            "canonical_email IS NULL OR canonical_email = lower(trim(canonical_email))",
            name="ck_users_canonical_email_normalized",
        ),
        CheckConstraint(
            "phone_verified_at IS NULL OR phone_number IS NOT NULL",
            name="ck_users_phone_verification_requires_phone",
        ),
        Index("uq_users_canonical_email", "canonical_email", unique=True),
        Index("ix_users_phone_number", "phone_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="client")  # client, agent, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    canonical_email = Column(String(320), nullable=True)
    phone_number = Column(String(32), nullable=True)
    account_status = Column(
        String(32),
        nullable=False,
        default="pending_verification",
        server_default=text("'pending_verification'"),
    )
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    phone_verified_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    assigned_roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    organization_memberships = relationship(
        "OrganizationMembership",
        back_populates="user",
    )
    submitted_verifications = relationship(
        "VerificationSubmission",
        back_populates="submitted_by",
    )
    reviewed_verifications = relationship(
        "BusinessVerificationReview",
        back_populates="reviewer",
    )