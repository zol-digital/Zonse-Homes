from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

PropertyTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PropertyPrice = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
PropertyCurrency = Annotated[str, StringConstraints(min_length=3, max_length=3)]
PropertyCity = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PropertyType = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PropertyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: PropertyTitle
    description: str | None = None
    price: PropertyPrice
    currency: PropertyCurrency = "MWK"
    city: PropertyCity
    property_type: PropertyType
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)


class PropertyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: PropertyTitle | None = None
    description: str | None = None
    price: PropertyPrice | None = None
    currency: PropertyCurrency | None = None
    city: PropertyCity | None = None
    property_type: PropertyType | None = None
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_partial_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        for field_name in ("title", "price", "currency", "city", "property_type"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        return self


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    price: Decimal
    currency: str
    city: str
    property_type: str
    bedrooms: int | None
    bathrooms: int | None
    created_at: datetime | None
