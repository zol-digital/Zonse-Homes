"""Add user identity, organization, and business verification foundations.

Revision ID: 20261030_0002
Revises: 20261030_0001
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261030_0002"
down_revision: Union[str, None] = "20261030_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


VERIFICATION_STATUSES = (
    "'not_submitted', 'pending_review', 'certified', 'rejected', 'suspended', 'expired'"
)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("canonical_email", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("phone_number", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "account_status",
            sa.String(length=32),
            server_default="pending_verification",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.execute(
        "UPDATE users SET account_status = 'disabled' WHERE is_active IS FALSE"
    )
    op.create_check_constraint(
        "ck_users_account_status",
        "users",
        "account_status IN "
        "('pending_verification', 'active', 'suspended', 'disabled')",
    )
    op.create_check_constraint(
        "ck_users_active_requires_verified_email",
        "users",
        "account_status != 'active' OR email_verified_at IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_users_canonical_email_normalized",
        "users",
        "canonical_email IS NULL OR canonical_email = lower(trim(canonical_email))",
    )
    op.create_check_constraint(
        "ck_users_phone_verification_requires_phone",
        "users",
        "phone_verified_at IS NULL OR phone_number IS NOT NULL",
    )
    op.create_index("uq_users_canonical_email", "users", ["canonical_email"], unique=True)
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=False)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "role IN ('seeker', 'owner', 'agent', 'property_manager', 'admin')",
            name="ck_user_roles_role",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_roles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "role", name="pk_user_roles"),
    )

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("registered_business_name", sa.String(length=255), nullable=False),
        sa.Column("business_type", sa.String(length=80), nullable=False),
        sa.Column("registration_number", sa.String(length=100), nullable=False),
        sa.Column("country_of_registration", sa.String(length=2), nullable=False),
        sa.Column("business_contact_email", sa.String(length=320), nullable=False),
        sa.Column("business_phone", sa.String(length=32), nullable=True),
        sa.Column(
            "account_status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "account_status IN ('pending', 'active', 'suspended', 'disabled')",
            name="ck_organizations_account_status",
        ),
        sa.CheckConstraint(
            "length(country_of_registration) = 2",
            name="ck_organizations_country_code_length",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_organizations"),
        sa.UniqueConstraint(
            "country_of_registration",
            "registration_number",
            name="uq_organizations_country_registration",
        ),
    )
    op.create_index(
        "ix_organizations_registered_business_name",
        "organizations",
        ["registered_business_name"],
        unique=False,
    )
    op.create_index(
        "ix_organizations_account_status",
        "organizations",
        ["account_status"],
        unique=False,
    )

    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("membership_role", sa.String(length=40), nullable=False),
        sa.Column(
            "membership_status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "membership_role IN "
            "('organization_admin', 'authorized_representative', 'advertiser')",
            name="ck_organization_memberships_role",
        ),
        sa.CheckConstraint(
            "membership_status IN ('active', 'suspended', 'revoked')",
            name="ck_organization_memberships_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_memberships_organization_id_organizations",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_organization_memberships_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_organization_memberships"),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_membership_org_user",
        ),
    )
    op.create_index(
        "ix_organization_memberships_user_status",
        "organization_memberships",
        ["user_id", "membership_status"],
        unique=False,
    )
    op.create_index(
        "ix_organization_memberships_org_status",
        "organization_memberships",
        ["organization_id", "membership_status"],
        unique=False,
    )

    op.create_table(
        "business_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column(
            "current_status",
            sa.String(length=24),
            server_default="not_submitted",
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"current_status IN ({VERIFICATION_STATUSES})",
            name="ck_business_verifications_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_business_verifications_organization_id_organizations",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_business_verifications"),
        sa.UniqueConstraint("organization_id", name="uq_business_verifications_organization"),
    )

    op.create_table(
        "verification_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "submission_status",
            sa.String(length=24),
            server_default="pending_review",
            nullable=False,
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "submission_status IN "
            "('pending_review', 'approved', 'rejected', 'withdrawn')",
            name="ck_verification_submissions_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_verification_submissions_organization_id_organizations",
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_user_id"],
            ["users.id"],
            name="fk_verification_submissions_submitted_by_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_verification_submissions"),
    )
    op.create_index(
        "ix_verification_submissions_org_submitted_at",
        "verification_submissions",
        ["organization_id", "submitted_at"],
        unique=False,
    )

    op.create_table(
        "verification_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("private_storage_ref", sa.String(length=512), nullable=False),
        sa.Column(
            "document_status",
            sa.String(length=20),
            server_default="received",
            nullable=False,
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "document_status IN ('received', 'accepted', 'rejected', 'superseded')",
            name="ck_verification_documents_status",
        ),
        sa.CheckConstraint(
            "lower(private_storage_ref) NOT LIKE 'http://%' "
            "AND lower(private_storage_ref) NOT LIKE 'https://%'",
            name="ck_verification_documents_private_reference",
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["verification_submissions.id"],
            name="fk_verification_documents_submission",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_verification_documents"),
        sa.UniqueConstraint(
            "private_storage_ref",
            name="uq_verification_documents_storage_ref",
        ),
    )

    op.create_table(
        "business_verification_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("verification_id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=True),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(length=24), nullable=True),
        sa.Column("new_status", sa.String(length=24), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"previous_status IS NULL OR previous_status IN ({VERIFICATION_STATUSES})",
            name="ck_business_verification_reviews_previous_status",
        ),
        sa.CheckConstraint(
            f"new_status IN ({VERIFICATION_STATUSES})",
            name="ck_business_verification_reviews_new_status",
        ),
        sa.CheckConstraint(
            "decision IN ('certify', 'reject', 'suspend', 'expire', 'reinstate')",
            name="ck_business_verification_reviews_decision",
        ),
        sa.ForeignKeyConstraint(
            ["verification_id"],
            ["business_verifications.id"],
            name="fk_bvr_verification",
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["verification_submissions.id"],
            name="fk_bvr_submission",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_user_id"],
            ["users.id"],
            name="fk_bvr_reviewer",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_business_verification_reviews"),
    )
    op.create_index(
        "ix_business_verification_reviews_verification_reviewed_at",
        "business_verification_reviews",
        ["verification_id", "reviewed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_business_verification_reviews_verification_reviewed_at",
        table_name="business_verification_reviews",
    )
    op.drop_table("business_verification_reviews")
    op.drop_table("verification_documents")
    op.drop_index(
        "ix_verification_submissions_org_submitted_at",
        table_name="verification_submissions",
    )
    op.drop_table("verification_submissions")
    op.drop_table("business_verifications")
    op.drop_index(
        "ix_organization_memberships_org_status",
        table_name="organization_memberships",
    )
    op.drop_index(
        "ix_organization_memberships_user_status",
        table_name="organization_memberships",
    )
    op.drop_table("organization_memberships")
    op.drop_index(
        "ix_organizations_account_status",
        table_name="organizations",
    )
    op.drop_index(
        "ix_organizations_registered_business_name",
        table_name="organizations",
    )
    op.drop_table("organizations")
    op.drop_table("user_roles")
    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_index("uq_users_canonical_email", table_name="users")
    op.drop_constraint("ck_users_account_status", "users", type_="check")
    op.drop_constraint(
        "ck_users_phone_verification_requires_phone",
        "users",
        type_="check",
    )
    op.drop_constraint(
        "ck_users_canonical_email_normalized",
        "users",
        type_="check",
    )
    op.drop_constraint(
        "ck_users_active_requires_verified_email",
        "users",
        type_="check",
    )
    op.drop_column("users", "updated_at")
    op.drop_column("users", "phone_verified_at")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "account_status")
    op.drop_column("users", "phone_number")
    op.drop_column("users", "canonical_email")
