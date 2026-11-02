from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

PlacementType = Literal["area", "homepage"]
PlacementDuration = Literal["weekly", "monthly"]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
LocationName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]


class FeaturedPackageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    placement_type: PlacementType
    duration: PlacementDuration
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Currency = "MWK"
    is_available: bool = False


class FeaturedPackageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: Currency | None = None
    is_available: bool | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(
            field_name in self.model_fields_set
            and getattr(self, field_name) is None
            for field_name in ("price", "currency", "is_available")
        ):
            raise ValueError("Package fields cannot be null")
        return self


class FeaturedPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    placement_type: PlacementType
    duration: PlacementDuration
    price: Decimal
    currency: str
    is_available: bool
    created_at: datetime
    updated_at: datetime


class FeaturedOrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listing_id: int = Field(gt=0)
    package_id: int = Field(gt=0)
    target_city: LocationName | None = None
    target_district: LocationName | None = None
    target_neighborhood: LocationName | None = None


class FeaturedOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    package_id: int
    placement_type: PlacementType
    duration: PlacementDuration
    amount: Decimal
    currency: str
    target_city: str | None
    target_district: str | None
    target_neighborhood: str | None
    payment_status: Literal["pending", "paid", "failed"]
    fulfillment_status: Literal["pending", "fulfilled", "blocked"]
    payment_reference: str | None
    created_at: datetime


class FeaturedSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    homepage_inventory_limit: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def require_inventory_setting(self):
        if "homepage_inventory_limit" not in self.model_fields_set:
            raise ValueError("homepage_inventory_limit must be provided")
        return self


class FeaturedSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    homepage_inventory_limit: int | None
    updated_at: datetime


class FeaturedPromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    listing_id: int
    placement_type: PlacementType
    target_city: str | None
    target_district: str | None
    target_neighborhood: str | None
    starts_at: datetime
    expires_at: datetime
    status: Literal["active", "expired", "cancelled"]
    cancelled_at: datetime | None
    cancelled_by_user_id: int | None
    cancellation_reason: str | None
    views_count: int
    interactions_count: int
    created_at: datetime


class FeaturedOrderAdminResponse(FeaturedOrderResponse):
    advertiser_id: int


class PaymentWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: int = Field(gt=0)
    payment_reference: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)
    ]
    status: Literal["paid", "failed"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Currency


class FeaturedPromotionEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: Literal["view", "interaction"]


class FeaturedPromotionEventResponse(BaseModel):
    recorded: bool


class FeaturedCancellationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
    ]
