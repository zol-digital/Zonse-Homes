"""Argon2id password hashing and password-policy helpers."""

from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError, UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher
from argon2 import extract_parameters
from argon2.exceptions import HashingError, InvalidHashError
from argon2.low_level import Type

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_BYTES = 1024
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST_KIB = 65536
ARGON2_PARALLELISM = 4
ARGON2_HASH_LENGTH = 32
ARGON2_SALT_LENGTH = 16

_ARGON2ID_PREFIX = "$argon2id$"
_argon2id_hasher = Argon2Hasher(
    time_cost=ARGON2_TIME_COST,
    memory_cost=ARGON2_MEMORY_COST_KIB,
    parallelism=ARGON2_PARALLELISM,
    hash_len=ARGON2_HASH_LENGTH,
    salt_len=ARGON2_SALT_LENGTH,
    type=Type.ID,
)
_password_hash = PasswordHash((_argon2id_hasher,))


class PasswordHashingError(RuntimeError):
    """Raised when the configured hasher cannot complete a safe operation."""


def _validate_password_input(password: object) -> str:
    if not isinstance(password, str):
        raise ValueError("Password must be text")

    try:
        encoded = password.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Password contains invalid Unicode") from None

    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must contain at least {MIN_PASSWORD_LENGTH} characters"
        )
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password must not exceed {MAX_PASSWORD_BYTES} UTF-8 bytes"
        )
    return password


def validate_password(password: object) -> str:
    """Validate a new password and return it without normalization or truncation."""
    return _validate_password_input(password)


def _is_supported_argon2id_hash(stored_hash: object) -> bool:
    if not isinstance(stored_hash, str) or not stored_hash.startswith(
        _ARGON2ID_PREFIX
    ):
        return False

    try:
        if not _argon2id_hasher.identify(stored_hash):
            return False
        parameters = extract_parameters(stored_hash)
    except (InvalidHashError, ValueError, PwdlibError):
        return False

    return (
        parameters.type is Type.ID
        and parameters.time_cost <= ARGON2_TIME_COST
        and parameters.memory_cost <= ARGON2_MEMORY_COST_KIB
        and parameters.parallelism <= ARGON2_PARALLELISM
        and parameters.hash_len <= ARGON2_HASH_LENGTH
        and parameters.salt_len <= ARGON2_SALT_LENGTH
    )


def hash_password(password: object) -> str:
    """Hash a new password with the configured Argon2id parameters."""
    validated_password = validate_password(password)
    try:
        return _password_hash.hash(validated_password)
    except (HashingError, PwdlibError):
        raise PasswordHashingError("Password hashing failed") from None


def verify_password(password: object, stored_hash: object) -> bool:
    """Verify an Argon2id hash; unknown or malformed formats fail closed."""
    try:
        validated_password = validate_password(password)
    except ValueError:
        return False

    if not _is_supported_argon2id_hash(stored_hash):
        return False

    try:
        return _password_hash.verify(validated_password, stored_hash)
    except (UnknownHashError, PwdlibError):
        return False


def password_hash_needs_rehash(stored_hash: object) -> bool:
    """Return whether a hash is unsupported or differs from current Argon2id settings.

    A true result does not mean an unsupported legacy hash is verifiable. Only
    replace a stored value after `verify_password_and_update` authenticates it.
    """
    if not _is_supported_argon2id_hash(stored_hash):
        return True

    try:
        return _argon2id_hasher.check_needs_rehash(stored_hash)
    except (UnknownHashError, PwdlibError):
        return True


def verify_password_and_update(
    password: object,
    stored_hash: object,
) -> tuple[bool, str | None]:
    """Authenticate and return a replacement hash only after successful verification."""
    try:
        validated_password = validate_password(password)
    except ValueError:
        return False, None

    if not _is_supported_argon2id_hash(stored_hash):
        return False, None

    try:
        return _password_hash.verify_and_update(validated_password, stored_hash)
    except (UnknownHashError, PwdlibError):
        return False, None
