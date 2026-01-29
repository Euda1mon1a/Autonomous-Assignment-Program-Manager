"""Schedule override schemas for post-release coverage changes."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScheduleOverrideCreate(BaseModel):
    """Create a schedule override for a half-day assignment."""

    half_day_assignment_id: UUID = Field(..., description="Half-day assignment ID")
    override_type: Literal["coverage", "cancellation"] = Field(
        "coverage", description="coverage replaces person, cancellation clears slot"
    )
    replacement_person_id: UUID | None = Field(
        None, description="Replacement person (required for coverage)"
    )
    reason: str | None = Field(
        None, description="Short reason (deployment, sick, urgent)"
    )
    notes: str | None = Field(None, description="Optional notes")
    supersedes_override_id: UUID | None = Field(
        None, description="Optional prior override ID"
    )

    @model_validator(mode="after")
    def validate_replacement(self) -> "ScheduleOverrideCreate":
        if self.override_type == "coverage" and self.replacement_person_id is None:
            raise ValueError("replacement_person_id is required for coverage overrides")
        if (
            self.override_type == "cancellation"
            and self.replacement_person_id is not None
        ):
            raise ValueError(
                "replacement_person_id must be null for cancellation overrides"
            )
        return self


class ScheduleOverrideResponse(BaseModel):
    """Schedule override response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    half_day_assignment_id: UUID
    original_person_id: UUID | None = None
    replacement_person_id: UUID | None = None
    override_type: Literal["coverage", "cancellation"]
    reason: str | None = None
    notes: str | None = None
    effective_date: date
    time_of_day: Literal["AM", "PM"]
    is_active: bool
    created_by_id: UUID | None = None
    created_at: datetime
    deactivated_at: datetime | None = None
    deactivated_by_id: UUID | None = None
    supersedes_override_id: UUID | None = None


class ScheduleOverrideListResponse(BaseModel):
    """List of schedule overrides."""

    overrides: list[ScheduleOverrideResponse]
    total: int
    block_number: int | None = None
    academic_year: int | None = None
    start_date: date | None = None
    end_date: date | None = None
