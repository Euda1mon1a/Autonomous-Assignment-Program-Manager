"""Call override schemas for post-release call coverage changes."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CallOverrideCreate(BaseModel):
    """Create a call override for a call assignment."""

    call_assignment_id: UUID = Field(..., description="Call assignment ID")
    override_type: Literal["coverage"] = Field(
        "coverage", description="coverage replaces person (call must be staffed)"
    )
    replacement_person_id: UUID = Field(
        ..., description="Replacement person (required)"
    )
    reason: str | None = Field(
        None, description="Short reason (deployment, sick, urgent)"
    )
    notes: str | None = Field(None, description="Optional notes")
    supersedes_override_id: UUID | None = Field(
        None, description="Optional prior override ID"
    )


class CallOverrideResponse(BaseModel):
    """Call override response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    call_assignment_id: UUID
    original_person_id: UUID | None = None
    replacement_person_id: UUID
    override_type: Literal["coverage"]
    reason: str | None = None
    notes: str | None = None
    effective_date: date
    call_type: str
    is_active: bool
    created_by_id: UUID | None = None
    created_at: datetime
    deactivated_at: datetime | None = None
    deactivated_by_id: UUID | None = None
    supersedes_override_id: UUID | None = None


class CallOverrideListResponse(BaseModel):
    """List of call overrides."""

    overrides: list[CallOverrideResponse]
    total: int
    block_number: int | None = None
    academic_year: int | None = None
    start_date: date | None = None
    end_date: date | None = None
