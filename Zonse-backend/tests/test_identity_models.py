from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.models
from app.database import Base
from app.models.identity import (
    BusinessVerification,
    BusinessVerificationReview,
    Organization,
    OrganizationMembership,
    UserRole,
    VerificationDocument,
    VerificationSubmission,
)
from app.models.user import User


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _new_user(email="member@example.test"):
    return User(email=email, hashed_password="test-hash-not-for-authentication")


def _new_organization():
    return Organization(
        registered_business_name="Example Property Company",
        business_type="property_company",
        registration_number="REG-001",
        country_of_registration="MW",
        business_contact_email="contact@example.test",
    )


def test_user_identity_fields_are_additive_and_have_safe_defaults(db_session):
    user = _new_user()
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.account_status == "pending_verification"
    assert user.canonical_email is None
    assert user.phone_number is None
    assert user.email_verified_at is None
    assert user.phone_verified_at is None
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.is_active is True
    assert user.role == "client"
    assert user.properties == []

    user.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
    db_session.commit()
    user.full_name = "Updated Name"
    db_session.commit()
    db_session.refresh(user)
    assert user.updated_at > datetime(2000, 1, 1)


def test_user_account_status_constraint_rejects_unknown_value(db_session):
    db_session.add(
        User(
            email="invalid-status@example.test",
            hashed_password="test-hash",
            account_status="unknown",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_email_is_required_and_canonical_email_is_unique_when_present(db_session):
    with pytest.raises(IntegrityError):
        db_session.add(User(email=None, hashed_password="test-hash"))
        db_session.commit()
    db_session.rollback()

    db_session.add_all(
        [
            User(
                email="first@example.test",
                canonical_email="first@example.test",
                hashed_password="test-hash",
            ),
            User(
                email="second@example.test",
                canonical_email="first@example.test",
                hashed_password="test-hash",
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_active_user_requires_verified_email_and_canonical_email_is_normalized(
    db_session,
):
    db_session.add(
        User(
            email="active@example.test",
            hashed_password="test-hash",
            account_status="active",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(
        User(
            email="unverified@example.test",
            hashed_password="test-hash",
            canonical_email=" MixedCase@example.test ",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_roles_allow_multiple_valid_values_and_reject_duplicates(db_session):
    user = _new_user()
    user.assigned_roles.extend(
        [UserRole(role="seeker"), UserRole(role="owner"), UserRole(role="admin")]
    )
    db_session.add(user)
    db_session.commit()

    assert {assigned.role for assigned in user.assigned_roles} == {
        "seeker",
        "owner",
        "admin",
    }

    with pytest.raises(IntegrityError):
        db_session.execute(
            insert(UserRole).values(user_id=user.id, role="owner")
        )
    db_session.rollback()


def test_role_constraint_rejects_unknown_role(db_session):
    user = _new_user()
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role="superuser"))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_organization_membership_constraints_and_revocation(db_session):
    user = _new_user()
    organization = _new_organization()
    membership = OrganizationMembership(
        organization=organization,
        user=user,
        membership_role="authorized_representative",
    )
    db_session.add(membership)
    db_session.commit()

    assert membership.membership_status == "active"
    membership.membership_status = "revoked"
    db_session.commit()
    assert membership.membership_status == "revoked"

    db_session.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            membership_role="advertiser",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.parametrize(
    "membership_role,membership_status",
    [
        ("owner", "active"),
        ("advertiser", "pending"),
    ],
)
def test_membership_constraints_reject_invalid_values(
    db_session,
    membership_role,
    membership_status,
):
    user = _new_user()
    organization = _new_organization()
    db_session.add_all([user, organization])
    db_session.flush()
    db_session.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            membership_role=membership_role,
            membership_status=membership_status,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.parametrize(
    "status",
    [
        "not_submitted",
        "pending_review",
        "certified",
        "rejected",
        "suspended",
        "expired",
    ],
)
def test_business_verification_accepts_approved_statuses(db_session, status):
    organization = _new_organization()
    verification = BusinessVerification(
        organization=organization,
        current_status=status,
    )
    db_session.add(verification)
    db_session.commit()

    assert verification.organization_id == organization.id


def test_business_verification_rejects_unknown_status(db_session):
    db_session.add(
        BusinessVerification(
            organization=_new_organization(),
            current_status="approved",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_submission_documents_and_review_history_have_relationships(db_session):
    submitter = _new_user("submitter@example.test")
    reviewer = _new_user("reviewer@example.test")
    organization = _new_organization()
    verification = BusinessVerification(
        organization=organization,
        current_status="certified",
        submitted_at=datetime.now(timezone.utc),
        reviewed_at=datetime.now(timezone.utc),
        expires_at=datetime(2027, 10, 30, tzinfo=timezone.utc),
    )
    submission = VerificationSubmission(
        organization=organization,
        submitted_by=submitter,
        submission_status="approved",
    )
    document = VerificationDocument(
        submission=submission,
        document_type="business_registration",
        private_storage_ref="private-object-ref-001",
    )
    review = BusinessVerificationReview(
        verification=verification,
        submission=submission,
        reviewer=reviewer,
        previous_status="pending_review",
        new_status="certified",
        decision="certify",
        reason="Registration reviewed",
    )
    db_session.add_all([verification, submission, document, review])
    db_session.commit()

    assert verification.reviews == [review]
    assert submission.documents == [document]
    assert review.reviewer is reviewer
    assert review.submission is submission
    assert document.private_storage_ref == "private-object-ref-001"


def test_verification_document_and_review_constraints_reject_invalid_values(db_session):
    submitter = _new_user("submitter@example.test")
    organization = _new_organization()
    submission = VerificationSubmission(
        organization=organization,
        submitted_by=submitter,
    )
    db_session.add(submission)
    db_session.flush()
    db_session.add(
        VerificationDocument(
            submission_id=submission.id,
            document_type="registration",
            private_storage_ref="private-object-ref-invalid",
            document_status="public",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.parametrize(
    "storage_reference",
    ["http://public.example.test/document", "https://public.example.test/document"],
)
def test_verification_document_rejects_public_url_references(
    db_session,
    storage_reference,
):
    submission = VerificationSubmission(
        organization=_new_organization(),
        submitted_by=_new_user(),
    )
    db_session.add(submission)
    db_session.flush()
    db_session.add(
        VerificationDocument(
            submission_id=submission.id,
            document_type="registration",
            private_storage_ref=storage_reference,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_verification_relations_enforce_foreign_keys(db_session):
    db_session.add(
        OrganizationMembership(
            organization_id=999,
            user_id=999,
            membership_role="advertiser",
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
