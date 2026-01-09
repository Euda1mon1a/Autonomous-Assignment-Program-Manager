"""Faculty activity schemas for weekly templates and overrides.

Faculty Weekly Activity Editor:
- Templates: Default weekly patterns per faculty member (7x2 grid)
- Overrides: Week-specific exceptions to templates
- Effective: Merged view of template + overrides for a specific week
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.activity import ActivityResponse


# =============================================================================
# Template Schemas
# =============================================================================


class FacultyTemplateSlotBase(BaseModel):
    """Base schema for a faculty template slot."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Sunday, 6=Saturday")
    time_of_day: Literal["AM", "PM"] = Field(..., description="AM or PM")
    week_number: int | None = Field(
        None, ge=1, le=4, description="Week 1-4, or null for all weeks"
    )
    activity_id: UUID | None = Field(None, description="Activity UUID or null")
    is_locked: bool = Field(False, description="HARD constraint - solver cannot change")
    priority: int = Field(50, ge=0, le=100, description="Soft preference 0-100")
    notes: str | None = Field(None, description="Optional notes")


class FacultyTemplateSlotCreate(FacultyTemplateSlotBase):
    """Schema for creating/updating a template slot."""

    pass


class FacultyTemplateSlotResponse(FacultyTemplateSlotBase):
    """Schema for template slot response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    person_id: UUID
    activity: ActivityResponse | None = None
    created_at: datetime
    updated_at: datetime


class FacultyTemplateUpdateRequest(BaseModel):
    """Schema for bulk template update."""

    slots: list[FacultyTemplateSlotCreate] = Field(
        ..., description="List of slots to create/update"
    )
    clear_existing: bool = Field(
        False, description="Delete all existing slots before applying"
    )


class FacultyTemplateResponse(BaseModel):
    """Schema for full template response."""

    person_id: UUID
    person_name: str
    faculty_role: str | None
    slots: list[FacultyTemplateSlotResponse]
    total_slots: int


# =============================================================================
# Override Schemas
# =============================================================================


class FacultyOverrideBase(BaseModel):
    """Base schema for a faculty override."""

    effective_date: date = Field(..., description="Monday of the week")
    day_of_week: int = Field(..., ge=0, le=6, description="0=Sunday, 6=Saturday")
    time_of_day: Literal["AM", "PM"] = Field(..., description="AM or PM")
    activity_id: UUID | None = Field(None, description="Activity UUID or null to clear")
    is_locked: bool = Field(False, description="HARD constraint for this week")
    override_reason: str | None = Field(None, description="Why this override exists")


class FacultyOverrideCreate(FacultyOverrideBase):
    """Schema for creating an override."""

    pass


class FacultyOverrideResponse(FacultyOverrideBase):
    """Schema for override response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    person_id: UUID
    activity: ActivityResponse | None = None
    created_by: UUID | None = None
    created_at: datetime


class FacultyOverridesListResponse(BaseModel):
    """Schema for list of overrides."""

    person_id: UUID
    week_start: date
    overrides: list[FacultyOverrideResponse]
    total: int


# =============================================================================
# Effective Week Schemas
# =============================================================================


class EffectiveSlot(BaseModel):
    """Schema for an effective slot (merged template + override)."""

    day_of_week: int = Field(..., ge=0, le=6)
    time_of_day: Literal["AM", "PM"]
    activity_id: UUID | None = None
    activity: ActivityResponse | None = None
    is_locked: bool = False
    priority: int = 50
    source: Literal["template", "override"] | None = None
    notes: str | None = None


class EffectiveWeekResponse(BaseModel):
    """Schema for effective week response."""

    person_id: UUID
    person_name: str
    faculty_role: str | None
    week_start: date
    week_number: int
    slots: list[EffectiveSlot]


# =============================================================================
# Permission Schemas
# =============================================================================


class PermittedActivitiesResponse(BaseModel):
    """Schema for permitted activities by role."""

    faculty_role: str
    activities: list[ActivityResponse]
    default_activities: list[ActivityResponse]


# =============================================================================
# Matrix View Schemas
# =============================================================================


class FacultyWeekSlots(BaseModel):
    """Schema for a single week's slots for one faculty member."""

    week_start: date
    slots: list[EffectiveSlot]


class FacultyMatrixRow(BaseModel):
    """Schema for a single faculty member in the matrix."""

    person_id: UUID
    name: str
    faculty_role: str | None
    weeks: list[FacultyWeekSlots]


class FacultyMatrixResponse(BaseModel):
    """Schema for full faculty matrix response."""

    start_date: date
    end_date: date
    faculty: list[FacultyMatrixRow]
    total_faculty: int
