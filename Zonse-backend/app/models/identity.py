from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        CheckConstraint(
            "role IN ('seeker', 'owner', 'agent', 'property_manager', 'admin')",
            name="ck_user_roles_role",
        ),
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role = Column(String(32), primary_key=True)

    user = relationship("User", back_populates="assigned_roles")


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint(
            "account_status IN ('pending', 'active', 'suspended', 'disabled')",
            name="ck_organizations_account_status",
        ),
        CheckConstraint(
            "length(country_of_registration) = 2",
            name="ck_organizations_country_code_length",
        ),
        UniqueConstraint(
            "country_of_registration",
            "registration_number",
            name="uq_organizations_country_registration",
        ),
        Index(
            "ix_organizations_registered_business_name",
            "registered_business_name",
        ),
        Index("ix_organizations_account_status", "account_status"),
    )

    id = Column(Integer, primary_key=True)
    registered_business_name = Column(String(255), nullable=False)
    business_type = Column(String(80), nullable=False)
    registration_number = Column(String(100), nullable=False)
    country_of_registration = Column(String(2), nullable=False)
    business_contact_email = Column(String(320), nullable=False)
    business_phone = Column(String(32), nullable=True)
    account_status = Column(
        String(32),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    memberships = relationship(
        "OrganizationMembership",
        back_populates="organization",
    )
    verification = relationship(
        "BusinessVerification",
        back_populates="organization",
        uselist=False,
    )
    verification_submissions = relationship(
        "VerificationSubmission",
        back_populates="organization",
    )


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        CheckConstraint(
            "membership_role IN "
            "('organization_admin', 'authorized_representative', 'advertiser')",
            name="ck_organization_memberships_role",
        ),
        CheckConstraint(
            "membership_status IN ('active', 'suspended', 'revoked')",
            name="ck_organization_memberships_status",
        ),
        UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
        Index(
            "ix_organization_memberships_user_status",
            "user_id",
            "membership_status",
        ),
        Index(
            "ix_organization_memberships_org_status",
            "organization_id",
            "membership_status",
        ),
    )

    id = Column(Integer, primary_key=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    membership_role = Column(String(40), nullable=False)
    membership_status = Column(
        String(20),
        nullable=False,
        default="active",
        server_default=text("'active'"),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="organization_memberships")


class BusinessVerification(Base):
    __tablename__ = "business_verifications"
    __table_args__ = (
        CheckConstraint(
            "current_status IN "
            "('not_submitted', 'pending_review', 'certified', 'rejected', "
            "'suspended', 'expired')",
            name="ck_business_verifications_status",
        ),
    )

    id = Column(Integer, primary_key=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        unique=True,
    )
    current_status = Column(
        String(24),
        nullable=False,
        default="not_submitted",
        server_default=text("'not_submitted'"),
    )
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    organization = relationship("Organization", back_populates="verification")
    reviews = relationship(
        "BusinessVerificationReview",
        back_populates="verification",
    )


class VerificationSubmission(Base):
    __tablename__ = "verification_submissions"
    __table_args__ = (
        CheckConstraint(
            "submission_status IN "
            "('pending_review', 'approved', 'rejected', 'withdrawn')",
            name="ck_verification_submissions_status",
        ),
        Index(
            "ix_verification_submissions_org_submitted_at",
            "organization_id",
            "submitted_at",
        ),
    )

    id = Column(Integer, primary_key=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
    )
    submitted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submission_status = Column(
        String(24),
        nullable=False,
        default="pending_review",
        server_default=text("'pending_review'"),
    )
    submitted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    organization = relationship(
        "Organization",
        back_populates="verification_submissions",
    )
    submitted_by = relationship("User", back_populates="submitted_verifications")
    documents = relationship("VerificationDocument", back_populates="submission")
    reviews = relationship(
        "BusinessVerificationReview",
        back_populates="submission",
    )


class VerificationDocument(Base):
    __tablename__ = "verification_documents"
    __table_args__ = (
        CheckConstraint(
            "document_status IN ('received', 'accepted', 'rejected', 'superseded')",
            name="ck_verification_documents_status",
        ),
        CheckConstraint(
            "lower(private_storage_ref) NOT LIKE 'http://%' "
            "AND lower(private_storage_ref) NOT LIKE 'https://%'",
            name="ck_verification_documents_private_reference",
        ),
        UniqueConstraint(
            "private_storage_ref",
            name="uq_verification_documents_storage_ref",
        ),
    )

    id = Column(Integer, primary_key=True)
    submission_id = Column(
        Integer,
        ForeignKey("verification_submissions.id"),
        nullable=False,
    )
    document_type = Column(String(80), nullable=False)
    private_storage_ref = Column(String(512), nullable=False)
    document_status = Column(
        String(20),
        nullable=False,
        default="received",
        server_default=text("'received'"),
    )
    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    submission = relationship("VerificationSubmission", back_populates="documents")


class BusinessVerificationReview(Base):
    __tablename__ = "business_verification_reviews"
    __table_args__ = (
        CheckConstraint(
            "previous_status IS NULL OR previous_status IN "
            "('not_submitted', 'pending_review', 'certified', 'rejected', "
            "'suspended', 'expired')",
            name="ck_business_verification_reviews_previous_status",
        ),
        CheckConstraint(
            "new_status IN "
            "('not_submitted', 'pending_review', 'certified', 'rejected', "
            "'suspended', 'expired')",
            name="ck_business_verification_reviews_new_status",
        ),
        CheckConstraint(
            "decision IN ('certify', 'reject', 'suspend', 'expire', 'reinstate')",
            name="ck_business_verification_reviews_decision",
        ),
        Index(
            "ix_business_verification_reviews_verification_reviewed_at",
            "verification_id",
            "reviewed_at",
        ),
    )

    id = Column(Integer, primary_key=True)
    verification_id = Column(
        Integer,
        ForeignKey("business_verifications.id"),
        nullable=False,
    )
    submission_id = Column(
        Integer,
        ForeignKey("verification_submissions.id"),
        nullable=True,
    )
    reviewer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    previous_status = Column(String(24), nullable=True)
    new_status = Column(String(24), nullable=False)
    decision = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    verification = relationship("BusinessVerification", back_populates="reviews")
    submission = relationship("VerificationSubmission", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviewed_verifications")
