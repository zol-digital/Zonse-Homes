from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

ReportReasonValue = Literal[
    "suspected_scam",
    "duplicate",
    "misleading_details",
    "wrong_price",
    "unavailable",
    "inappropriate_content",
    "other",
]
ReportStatusValue = Literal[
    "new",
    "investigating",
    "actioned",
    "dismissed",
    "escalated",
]
ReportDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]


class PropertyReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_code: ReportReasonValue
    description: ReportDescription | None = None


class PropertyReportAcknowledgement(BaseModel):
    message: Literal["Report received. Thank you."]


class ReportReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["investigating", "actioned", "dismissed", "escalated"]
    reason: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
    ]
    resolution_code: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=64),
    ] = None
    moderator_notes: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    ] = None


class PropertyReportReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    listing_id: int | None
    reported_user_id: int | None
    reporter_user_id: int | None
    reason_code: ReportReasonValue
    description: str | None
    status: ReportStatusValue
    assigned_to_user_id: int | None
    resolution_code: str | None
    created_at: datetime
    resolved_at: datetime | None
