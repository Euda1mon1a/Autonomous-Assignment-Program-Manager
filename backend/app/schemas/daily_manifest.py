"""Daily Manifest schemas - for "Where is everyone NOW" clinic view."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PersonSummary(BaseModel):
    """Summary of person for manifest display."""
    id: UUID
    name: str
    pgy_level: int | None = Field(None, description="PGY level for residents")


class AssignmentSummary(BaseModel):
    """Summary of an assignment for manifest display."""
    person: PersonSummary
    role: str = Field(..., description="primary, supervising, or backup")
    activity: str = Field(..., description="Activity name or override")


class StaffingSummary(BaseModel):
    """Staffing summary for a location."""
    total: int = Field(..., description="Total number of people")
    residents: int = Field(..., description="Number of residents")
    faculty: int = Field(..., description="Number of faculty")


class LocationManifest(BaseModel):
    """Manifest for a single clinic location."""
    clinic_location: str | None = Field(None, description="Clinic location name")
    time_slots: dict[str, list[AssignmentSummary]] = Field(
        ...,
        description="Time slots (AM/PM) with assignments",
    )
    staffing_summary: StaffingSummary


class DailyManifestResponse(BaseModel):
    """Response for daily manifest endpoint."""
    date: date
    time_of_day: str | None = Field(None, description="AM or PM, or None for all day")
    locations: list[LocationManifest]
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this manifest was generated",
    )
