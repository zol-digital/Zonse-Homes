"""Public user schemas without credential or internal identity fields."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from typing_extensions import Annotated

from app.security.credentials import normalize_email
from app.security.passwords import validate_password

EmailValue = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
FullNameValue = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ProfileNameValue = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
ProfilePhoneValue = Annotated[str, StringConstraints(strip_whitespace=True, max_length=32)]
TokenValue = Annotated[str, StringConstraints(min_length=1, max_length=256)]


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailValue
    password: str = Field(min_length=12)
    full_name: FullNameValue | None = None
    phone_number: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailValue
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class EmailAddressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailValue

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class EmailVerificationConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: TokenValue


class PasswordRecoveryConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: TokenValue
    new_password: str = Field(min_length=12, max_length=1024)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password(value)


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: ProfileNameValue | None = None
    phone_number: ProfilePhoneValue | None = None


class AccountActionResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    phone_number: str | None
    account_status: str
    email_verified_at: datetime | None
    phone_verified_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class AuthenticatedUserResponse(UserResponse):
    roles: list[str]
