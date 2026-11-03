from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

ReferenceSlug = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    ),
]
ReferenceName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]
CategoryName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
LocationKind = Literal["region", "district", "city", "town", "neighborhood"]
LocationAlias = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]


class PropertyCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PropertyCategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=50,
            pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        ),
    ]
    name: CategoryName


class PropertyCategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: CategoryName | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_update_fields(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field_name in ("name", "is_active"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class LocationReferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    kind: LocationKind
    parent_id: int | None
    aliases: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LocationReferenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: ReferenceSlug
    name: ReferenceName
    kind: LocationKind
    parent_id: int | None = None
    aliases: list[LocationAlias] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def aliases_are_unique(self):
        aliases = [alias.casefold() for alias in self.aliases]
        if len(aliases) != len(set(aliases)):
            raise ValueError("Location aliases must be unique")
        return self


class LocationReferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ReferenceName | None = None
    aliases: list[LocationAlias] | None = Field(default=None, max_length=50)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field_name in ("name", "aliases", "is_active"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        if self.aliases is not None:
            aliases = [alias.casefold() for alias in self.aliases]
            if len(aliases) != len(set(aliases)):
                raise ValueError("Location aliases must be unique")
        return self
