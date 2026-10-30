from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

PropertyTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PropertyPrice = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
PropertyCurrency = Annotated[str, StringConstraints(min_length=3, max_length=3)]
PropertyCity = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PropertyType = Literal["house", "apartment", "flat", "plot", "land", "commercial"]
PropertyIntent = Literal["sale", "rent"]
RentalPeriod = Literal["day", "week", "month", "year"]
AreaUnit = Literal["sqm", "sqft"]
LandAreaUnit = Literal["sqm", "sqft", "acre", "hectare"]
PropertyStatusValue = Literal[
    "draft",
    "pending_review",
    "published",
    "changes_requested",
    "rejected",
    "paused",
    "rented",
    "sold",
    "expired",
    "removed",
    "archived",
]
ListEntry = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ContactName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ContactPhone = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)
]
ContactEmail = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=254)
]


class PropertyImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    is_primary: bool | None
    created_at: datetime | None


class PropertyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: PropertyTitle
    description: str | None = None
    price: PropertyPrice
    currency: PropertyCurrency = "MWK"
    city: PropertyCity
    property_type: PropertyType
    intent: PropertyIntent = "sale"
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    negotiable: bool = False
    rental_period: RentalPeriod | None = None
    deposit: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    floor_area: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    floor_area_unit: AreaUnit = "sqm"
    land_area: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    land_area_unit: LandAreaUnit = "sqm"
    amenities: list[ListEntry] = Field(default_factory=list)
    utilities: list[ListEntry] = Field(default_factory=list)
    district: str | None = None
    neighborhood: str | None = None
    available_from: date | None = None
    advertiser_name: ContactName | None = None
    contact_phone: ContactPhone | None = None
    contact_email: ContactEmail | None = None
    show_contact_details: bool = False

    @model_validator(mode="after")
    def validate_rental_terms(self):
        if self.intent == "sale" and (
            self.rental_period is not None or self.deposit is not None
        ):
            raise ValueError("Rental terms are only valid for rental listings")
        return self


class PropertyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: PropertyTitle | None = None
    description: str | None = None
    price: PropertyPrice | None = None
    currency: PropertyCurrency | None = None
    city: PropertyCity | None = None
    property_type: PropertyType | None = None
    intent: PropertyIntent | None = None
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    negotiable: bool | None = None
    rental_period: RentalPeriod | None = None
    deposit: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    floor_area: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    floor_area_unit: AreaUnit | None = None
    land_area: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    land_area_unit: LandAreaUnit | None = None
    amenities: list[ListEntry] | None = None
    utilities: list[ListEntry] | None = None
    district: str | None = None
    neighborhood: str | None = None
    available_from: date | None = None
    advertiser_name: ContactName | None = None
    contact_phone: ContactPhone | None = None
    contact_email: ContactEmail | None = None
    show_contact_details: bool | None = None

    @model_validator(mode="after")
    def validate_partial_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        for field_name in ("title", "price", "currency", "city", "property_type", "intent"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        if "intent" in self.model_fields_set and self.intent == "sale":
            rental_fields = ("rental_period", "deposit")
            if any(
                field_name not in self.model_fields_set
                or getattr(self, field_name) is not None
                for field_name in rental_fields
            ):
                raise ValueError(
                    "Changing to sale intent requires clearing rental_period and deposit"
                )

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
    intent: PropertyIntent
    bedrooms: int | None
    bathrooms: int | None
    negotiable: bool
    rental_period: RentalPeriod | None
    deposit: Decimal | None
    floor_area: Decimal | None
    floor_area_unit: AreaUnit
    land_area: Decimal | None
    land_area_unit: LandAreaUnit
    amenities: list[str]
    utilities: list[str]
    district: str | None
    neighborhood: str | None
    available_from: date | None
    advertiser_name: str | None
    contact_phone: str | None
    contact_email: str | None
    show_contact_details: bool = Field(exclude=True)
    cover_image_id: int | None
    images: list[PropertyImageResponse] = Field(default_factory=list)
    status: PropertyStatusValue
    created_at: datetime | None
    updated_at: datetime | None

    @model_validator(mode="after")
    def apply_contact_privacy(self):
        if not self.show_contact_details:
            self.advertiser_name = None
            self.contact_phone = None
            self.contact_email = None
        return self
