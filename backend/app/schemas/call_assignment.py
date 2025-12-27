"""Call assignment schemas for overnight and weekend call."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CallAssignmentBase(BaseModel):
    """Base call assignment schema."""

    date: date
    person_id: UUID
    call_type: str = Field(
        default="overnight", description="overnight, weekend, or backup"
    )
    is_weekend: bool = False
    is_holiday: bool = False

    @field_validator("call_type")
    @classmethod
    def validate_call_type(cls, v: str) -> str:
        if v not in ("overnight", "weekend", "backup"):
            raise ValueError("call_type must be 'overnight', 'weekend', or 'backup'")
        return v


class CallAssignmentCreate(CallAssignmentBase):
    """Schema for creating a call assignment."""

    pass


class CallAssignmentUpdate(BaseModel):
    """Schema for updating a call assignment."""

    call_type: str | None = None
    is_weekend: bool | None = None
    is_holiday: bool | None = None

    @field_validator("call_type")
    @classmethod
    def validate_call_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ("overnight", "weekend", "backup"):
            raise ValueError("call_type must be 'overnight', 'weekend', or 'backup'")
        return v


class CallAssignmentResponse(CallAssignmentBase):
    """Schema for call assignment response."""

    id: UUID
    created_at: datetime

    # Enriched fields for display
    person_name: str | None = Field(None, description="Faculty member's name")
    day_of_week: str | None = Field(None, description="Day of week (e.g., 'Sunday')")

    class Config:
        from_attributes = True


class CallAssignmentWithPerson(CallAssignmentResponse):
    """Call assignment with full person details."""

    faculty_role: str | None = Field(
        None, description="Faculty role (PD, APD, Core, etc.)"
    )
    pgy_level: int | None = Field(None, description="PGY level if resident")


class CallCoverageReport(BaseModel):
    """Coverage report for a date range."""

    start_date: date
    end_date: date
    total_nights: int = Field(description="Total Sun-Thurs nights in range")
    covered_nights: int = Field(description="Nights with call assignment")
    uncovered_nights: int = Field(description="Nights without coverage")
    coverage_percentage: float = Field(description="Percentage covered")
    gaps: list[date] = Field(default_factory=list, description="Dates without coverage")


class CallEquityReport(BaseModel):
    """Equity report showing call distribution across faculty."""

    year: int
    faculty_counts: list[dict] = Field(
        description="List of {person_id, name, sunday_calls, weekday_calls, total_calls}"
    )
    sunday_stats: dict = Field(
        description="Sunday call statistics (min, max, mean, stddev)"
    )
    weekday_stats: dict = Field(
        description="Weekday call statistics (min, max, mean, stddev)"
    )
    equity_score: float = Field(
        description="0-1 score where 1 is perfect equity",
        ge=0.0,
        le=1.0,
    )


class BulkCallAssignmentCreate(BaseModel):
    """Schema for bulk creating call assignments from solver output."""

    assignments: list[CallAssignmentCreate]
    schedule_run_id: UUID | None = Field(
        None, description="Link to schedule generation run"
    )
    replace_existing: bool = Field(
        default=True,
        description="Delete existing call assignments in date range before creating",
    )
