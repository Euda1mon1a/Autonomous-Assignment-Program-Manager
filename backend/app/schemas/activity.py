"""Activity schemas for slot-level schedule events.

Activities are distinct from Rotations:
- Rotation = Multi-week block assignment (e.g., "Neurology" for 4 weeks)
- Activity = Slot-level event (e.g., "FM Clinic AM", "LEC Wednesday PM")
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ActivityCategory(str, Enum):
    """Categories for activities to enable filtering and business logic."""

    CLINICAL = "clinical"
    EDUCATIONAL = "educational"
    ADMINISTRATIVE = "administrative"
    TIME_OFF = "time_off"


# Valid categories as tuple for validation
VALID_ACTIVITY_CATEGORIES = tuple(c.value for c in ActivityCategory)


class ActivityBase(BaseModel):
    """Base activity schema with shared fields."""

    name: str = Field(
        ..., description="Human-readable name (e.g., 'FM Clinic', 'Lecture')"
    )
    code: str = Field(
        ...,
        max_length=50,
        description="Stable identifier for solver (e.g., 'fm_clinic')",
    )
    display_abbreviation: str | None = Field(
        None,
        max_length=20,
        description="Short code for UI grid (e.g., 'C', 'LEC')",
    )
    activity_category: str = Field(
        ...,
        description="Category: clinical, educational, administrative, time_off",
    )
    procedure_id: UUID | None = Field(
        None,
        description="Optional procedure ID for credentialed activities (e.g., VAS, SM)",
    )
    font_color: str | None = Field(None, description="Tailwind color class for text")
    background_color: str | None = Field(
        None, description="Tailwind color class for background"
    )
    requires_supervision: bool = Field(
        True, description="ACGME supervision requirement"
    )
    is_protected: bool = Field(False, description="True for locked slots (e.g., LEC)")
    counts_toward_clinical_hours: bool = Field(
        True, description="ACGME clinical hour limit"
    )
    display_order: int = Field(0, description="Sort order for UI")
    capacity_units: int | None = Field(
        None,
        ge=0,
        description="FMC physical capacity units consumed by this activity (0 for non-physical)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate code format."""
        if not v or not v.strip():
            raise ValueError("code cannot be empty")
        v = v.strip().lower()
        # Code should be lowercase alphanumeric with underscores or hyphens
        # Hyphens needed for codes like LV-PM, C-AM, W-AM, FMIT-R
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError(
                "code must be lowercase alphanumeric with underscores or hyphens only"
            )
        return v

    @field_validator("activity_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate activity category."""
        if v not in VALID_ACTIVITY_CATEGORIES:
            raise ValueError(
                f"activity_category must be one of: {VALID_ACTIVITY_CATEGORIES}"
            )
        return v


class ActivityCreate(ActivityBase):
    """Schema for creating a new activity."""

    pass


class ActivityUpdate(BaseModel):
    """Schema for updating an activity. All fields optional."""

    name: str | None = None
    code: str | None = None
    display_abbreviation: str | None = None
    activity_category: str | None = None
    font_color: str | None = None
    background_color: str | None = None
    requires_supervision: bool | None = None
    is_protected: bool | None = None
    counts_toward_clinical_hours: bool | None = None
    display_order: int | None = None
    capacity_units: int | None = None
    procedure_id: UUID | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str | None) -> str | None:
        """Validate code format if provided."""
        if v is None:
            return v
        v = v.strip().lower()
        # Hyphens needed for codes like LV-PM, C-AM, W-AM, FMIT-R
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError(
                "code must be lowercase alphanumeric with underscores or hyphens only"
            )
        return v

    @field_validator("activity_category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        """Validate activity category if provided."""
        if v is None:
            return v
        if v not in VALID_ACTIVITY_CATEGORIES:
            raise ValueError(
                f"activity_category must be one of: {VALID_ACTIVITY_CATEGORIES}"
            )
        return v


class ActivityResponse(ActivityBase):
    """Schema for activity response with all fields."""

    id: UUID
    is_archived: bool = False
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    """Schema for list of activities."""

    activities: list[ActivityResponse]
    total: int


# ============================================================================
# Activity Requirement Schemas
# ============================================================================


class ActivityRequirementBase(BaseModel):
    """Base schema for activity requirements."""

    activity_id: UUID = Field(..., description="The activity this requirement is for")
    min_halfdays: int = Field(0, ge=0, le=28, description="Minimum half-days required")
    max_halfdays: int = Field(14, ge=0, le=28, description="Maximum half-days allowed")
    target_halfdays: int | None = Field(
        None, ge=0, le=28, description="Preferred count"
    )
    applicable_weeks: list[int] | None = Field(
        None,
        description="Week numbers [1,2,3,4] or null for all weeks",
    )
    prefer_full_days: bool = Field(True, description="Prefer AM+PM together")
    preferred_days: list[int] | None = Field(
        None,
        description="Preferred day numbers [1-5 for Mon-Fri]",
    )
    avoid_days: list[int] | None = Field(
        None,
        description="Days to avoid [0,6 for Sun,Sat]",
    )
    priority: int = Field(
        50, ge=0, le=100, description="0-100, higher = more important"
    )

    @field_validator("applicable_weeks")
    @classmethod
    def validate_weeks(cls, v: list[int] | None) -> list[int] | None:
        """Validate week numbers are 1-4."""
        if v is None:
            return v
        for week in v:
            if week < 1 or week > 4:
                raise ValueError("Week numbers must be 1-4")
        return sorted(set(v))  # Remove duplicates and sort

    @field_validator("preferred_days", "avoid_days")
    @classmethod
    def validate_days(cls, v: list[int] | None) -> list[int] | None:
        """Validate day numbers are 0-6."""
        if v is None:
            return v
        for day in v:
            if day < 0 or day > 6:
                raise ValueError("Day numbers must be 0-6 (0=Sun, 6=Sat)")
        return sorted(set(v))


class ActivityRequirementCreate(ActivityRequirementBase):
    """Schema for creating an activity requirement."""

    pass


class ActivityRequirementUpdate(BaseModel):
    """Schema for updating an activity requirement."""

    min_halfdays: int | None = Field(None, ge=0, le=28)
    max_halfdays: int | None = Field(None, ge=0, le=28)
    target_halfdays: int | None = Field(None, ge=0, le=28)
    applicable_weeks: list[int] | None = None
    prefer_full_days: bool | None = None
    preferred_days: list[int] | None = None
    avoid_days: list[int] | None = None
    priority: int | None = Field(None, ge=0, le=100)


class ActivityRequirementResponse(ActivityRequirementBase):
    """Schema for activity requirement response."""

    id: UUID
    rotation_template_id: UUID
    activity: ActivityResponse  # Nested activity data
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityRequirementListResponse(BaseModel):
    """Schema for list of activity requirements."""

    requirements: list[ActivityRequirementResponse]
    total_halfdays: int  # Sum of target_halfdays across all requirements


class ActivityRequirementBulkUpdate(BaseModel):
    """Schema for bulk updating activity requirements."""

    requirements: list[ActivityRequirementCreate]
