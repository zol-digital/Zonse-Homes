import logging

import pytest
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from argon2 import extract_parameters
from argon2.exceptions import HashingError
from argon2.low_level import Type

from app.models.user import User
from app.schemas.user import UserResponse
import app.security.passwords as passwords
from app.security.passwords import (
    MAX_PASSWORD_BYTES,
    MIN_PASSWORD_LENGTH,
    hash_password,
    password_hash_needs_rehash,
    validate_password,
    verify_password,
    verify_password_and_update,
)

PASSWORD = "correct horse battery staple"
ANOTHER_PASSWORD = "different correct password"


def test_hash_uses_configured_argon2id_and_verifies_password(caplog):
    caplog.set_level(logging.DEBUG)

    encoded_hash = hash_password(PASSWORD)
    parameters = extract_parameters(encoded_hash)

    assert encoded_hash.startswith("$argon2id$")
    assert parameters.type is Type.ID
    assert parameters.time_cost == 3
    assert parameters.memory_cost == 65536
    assert parameters.parallelism == 4
    assert parameters.hash_len == 32
    assert parameters.salt_len == 16
    assert verify_password(PASSWORD, encoded_hash)
    assert not verify_password(ANOTHER_PASSWORD, encoded_hash)
    assert PASSWORD not in caplog.text
    assert encoded_hash not in caplog.text


def test_hashes_for_same_password_are_salted_independently():
    first_hash = hash_password(PASSWORD)
    second_hash = hash_password(PASSWORD)

    assert first_hash != second_hash
    assert verify_password(PASSWORD, first_hash)
    assert verify_password(PASSWORD, second_hash)


@pytest.mark.parametrize(
    "password",
    [
        "",
        "short",
        "x" * (MAX_PASSWORD_BYTES + 1),
        "surrogate-\ud800-value",
    ],
)
def test_invalid_password_inputs_are_rejected_without_truncation(password):
    with pytest.raises(ValueError):
        validate_password(password)

    with pytest.raises(ValueError):
        hash_password(password)

    assert not verify_password(password, "$argon2id$malformed")


def test_password_policy_accepts_minimum_and_maximum_valid_lengths():
    minimum_password = "x" * MIN_PASSWORD_LENGTH
    maximum_password = "🙂" * (MAX_PASSWORD_BYTES // len("🙂".encode("utf-8")))

    assert validate_password(minimum_password) == minimum_password
    assert len(maximum_password.encode("utf-8")) == MAX_PASSWORD_BYTES
    assert validate_password(maximum_password) == maximum_password


def test_unicode_passwords_are_verified_without_unicode_normalization():
    composed = "Café-house-passphrase"
    decomposed = "Cafe\u0301-house-passphrase"
    encoded_hash = hash_password(composed)
    decomposed_hash = hash_password(decomposed)

    assert verify_password(composed, encoded_hash)
    assert not verify_password(decomposed, encoded_hash)
    assert verify_password(decomposed, decomposed_hash)


@pytest.mark.parametrize(
    "stored_hash",
    [
        "",
        "not-a-password-hash",
        "$2b$12$unsupported-format",
        "$argon2id$malformed",
        "$argon2id$v=19$m=65536,t=3,p=4$!!!!$!!!!",
        "$argon2id$v=19$m=999999999,t=3,p=4$c2FsdHNhbHQ$YWJjZA",
        None,
        123,
    ],
)
def test_unknown_or_malformed_hashes_fail_closed(stored_hash):
    assert not verify_password(PASSWORD, stored_hash)
    assert password_hash_needs_rehash(stored_hash)
    assert verify_password_and_update(PASSWORD, stored_hash) == (False, None)


def test_hash_rehash_detection_and_verified_upgrade():
    current_hash = hash_password(PASSWORD)
    old_parameters_hasher = Argon2Hasher(
        time_cost=1,
        memory_cost=8192,
        parallelism=1,
        hash_len=32,
        salt_len=16,
        type=Type.ID,
    )
    outdated_hash = PasswordHash((old_parameters_hasher,)).hash(PASSWORD)

    assert not password_hash_needs_rehash(current_hash)
    assert password_hash_needs_rehash(outdated_hash)
    assert verify_password_and_update(ANOTHER_PASSWORD, outdated_hash) == (
        False,
        None,
    )

    verified, replacement_hash = verify_password_and_update(PASSWORD, outdated_hash)

    assert verified
    assert replacement_hash is not None
    assert replacement_hash.startswith("$argon2id$")
    assert verify_password(PASSWORD, replacement_hash)
    assert not password_hash_needs_rehash(replacement_hash)


def test_hashing_library_errors_are_sanitized_and_not_logged(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(
        passwords._password_hash,
        "hash",
        lambda _password: (_ for _ in ()).throw(HashingError("sensitive input")),
    )

    with pytest.raises(passwords.PasswordHashingError) as error:
        hash_password(PASSWORD)

    assert str(error.value) == "Password hashing failed"
    assert PASSWORD not in str(error.value)
    assert "sensitive input" not in str(error.value)
    assert PASSWORD not in caplog.text
    assert "sensitive input" not in caplog.text


def test_public_user_schema_excludes_hash_and_internal_canonical_email():
    user = User(
        id=1,
        email="public@example.test",
        hashed_password="must-not-serialize",
        canonical_email="public@example.test",
        full_name="Example User",
        phone_number=None,
        account_status="pending_verification",
    )

    response = UserResponse.model_validate(user).model_dump()

    assert response["email"] == "public@example.test"
    assert "hashed_password" not in response
    assert "canonical_email" not in response
    assert "must-not-serialize" not in repr(response)
