"""Extended schemas for rotation template GUI features.

These schemas support the visual rotation template editor with:
- Weekly pattern grid (7x2 AM/PM slots)
- Split/mirrored rotation configuration
- Scheduling preferences (soft constraints)
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Weekly Pattern Schemas
# =============================================================================


class WeeklyPatternBase(BaseModel):
    """Base schema for weekly pattern slots."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Sunday, 6=Saturday")
    time_of_day: Literal["AM", "PM"]
    activity_type: str = Field(
        ...,
        max_length=50,
        description="fm_clinic, specialty, elective, conference, inpatient, call, procedure, off",
    )
    linked_template_id: UUID | None = None
    is_protected: bool = False
    notes: str | None = Field(None, max_length=200)


class WeeklyPatternCreate(WeeklyPatternBase):
    """Schema for creating a weekly pattern slot."""

    pass


class WeeklyPatternUpdate(BaseModel):
    """Schema for updating a weekly pattern slot."""

    activity_type: str | None = Field(None, max_length=50)
    linked_template_id: UUID | None = None
    is_protected: bool | None = None
    notes: str | None = Field(None, max_length=200)


class WeeklyPatternResponse(WeeklyPatternBase):
    """Schema for weekly pattern response."""

    id: UUID
    rotation_template_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeeklyGridUpdate(BaseModel):
    """Schema for updating the entire 7x2 weekly grid at once.

    This replaces all existing patterns with the provided ones.
    Max 14 patterns (7 days x 2 time periods).
    """

    patterns: list[WeeklyPatternCreate] = Field(
        ...,
        max_length=14,
        description="Up to 14 slots (7 days x 2 time periods)",
    )


# =============================================================================
# Rotation Preference Schemas
# =============================================================================


class RotationPreferenceBase(BaseModel):
    """Base schema for rotation preferences."""

    preference_type: str = Field(
        ...,
        max_length=50,
        description="full_day_grouping, consecutive_specialty, avoid_isolated, preferred_days, avoid_friday_pm, balance_weekly",
    )
    weight: Literal["low", "medium", "high", "required"] = "medium"
    config_json: dict = Field(default_factory=dict)
    is_active: bool = True
    description: str | None = Field(None, max_length=200)


class RotationPreferenceCreate(RotationPreferenceBase):
    """Schema for creating a preference."""

    pass


class RotationPreferenceUpdate(BaseModel):
    """Schema for updating a preference."""

    weight: Literal["low", "medium", "high", "required"] | None = None
    config_json: dict | None = None
    is_active: bool | None = None
    description: str | None = Field(None, max_length=200)


class RotationPreferenceResponse(RotationPreferenceBase):
    """Schema for preference response."""

    id: UUID
    rotation_template_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Extended Rotation Template Schemas
# =============================================================================


class RotationTemplateGUIFields(BaseModel):
    """Additional fields for rotation template GUI."""

    pattern_type: Literal["regular", "split", "mirrored", "alternating"] = "regular"
    setting_type: Literal["inpatient", "outpatient"] = "outpatient"
    paired_template_id: UUID | None = None
    split_day: int | None = Field(
        None, ge=1, le=27, description="Day where split occurs (1-27)"
    )
    is_mirror_primary: bool = True


class RotationTemplateExtendedCreate(BaseModel):
    """Schema for creating rotation template with GUI fields."""

    # Core fields
    name: str
    activity_type: str
    abbreviation: str | None = None
    font_color: str | None = None
    background_color: str | None = None
    leave_eligible: bool = True

    # Clinic constraints
    clinic_location: str | None = None
    max_residents: int | None = None
    requires_specialty: str | None = None
    requires_procedure_credential: bool = False

    # ACGME
    supervision_required: bool = True
    max_supervision_ratio: int = 4

    # GUI fields
    pattern_type: Literal["regular", "split", "mirrored", "alternating"] = "regular"
    setting_type: Literal["inpatient", "outpatient"] = "outpatient"
    paired_template_id: UUID | None = None
    split_day: int | None = Field(None, ge=1, le=27)
    is_mirror_primary: bool = True


class RotationTemplateExtendedResponse(BaseModel):
    """Extended response including patterns and preferences."""

    # Core fields
    id: UUID
    name: str
    activity_type: str
    abbreviation: str | None = None
    font_color: str | None = None
    background_color: str | None = None
    leave_eligible: bool

    # Clinic constraints
    clinic_location: str | None = None
    max_residents: int | None = None
    requires_specialty: str | None = None
    requires_procedure_credential: bool

    # ACGME
    supervision_required: bool
    max_supervision_ratio: int | None

    # GUI fields
    pattern_type: str = "regular"
    setting_type: str = "outpatient"
    paired_template_id: UUID | None = None
    split_day: int | None = None
    is_mirror_primary: bool = True

    # Nested data
    weekly_patterns: list[WeeklyPatternResponse] = []
    preferences: list[RotationPreferenceResponse] = []

    # Computed summary
    half_day_summary: dict[str, int] | None = None

    # Timestamps
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Split Rotation Schemas
# =============================================================================


class SplitRotationTemplateConfig(BaseModel):
    """Configuration for one half of a split rotation."""

    name: str
    activity_type: str
    abbreviation: str | None = None
    font_color: str | None = None
    background_color: str | None = None


class SplitRotationCreate(BaseModel):
    """Schema for creating a split or mirrored rotation pair.

    For mirrored rotations with create_mirror=True, automatically
    generates Cohort B templates with swapped first/second half.
    """

    primary_template: SplitRotationTemplateConfig
    secondary_template: SplitRotationTemplateConfig
    pattern_type: Literal["split", "mirrored"]
    split_day: int = Field(14, ge=1, le=27, description="Day where split occurs")
    create_mirror: bool = Field(
        False,
        description="If true, auto-generate cohort B with swapped halves",
    )

    # Shared properties for both templates
    leave_eligible: bool = True
    supervision_required: bool = True
    max_supervision_ratio: int = 4


class SplitRotationResponse(BaseModel):
    """Response for split rotation creation."""

    primary: RotationTemplateExtendedResponse
    secondary: RotationTemplateExtendedResponse
    cohort_b_primary: RotationTemplateExtendedResponse | None = None
    cohort_b_secondary: RotationTemplateExtendedResponse | None = None


# =============================================================================
# Preview Schemas
# =============================================================================


class PreviewGridCell(BaseModel):
    """Single cell in preview grid."""

    date: str  # ISO date string
    time_of_day: Literal["AM", "PM"]
    activity_type: str
    abbreviation: str | None = None
    background_color: str | None = None
    font_color: str | None = None


class PreviewWeek(BaseModel):
    """One week of preview data."""

    week_number: int
    start_date: str
    cells: list[PreviewGridCell]


class RotationPreviewResponse(BaseModel):
    """Response for rotation preview generation."""

    template_id: UUID
    template_name: str
    weeks: list[PreviewWeek]
    total_half_days: dict[str, int]  # Summary by activity type


# =============================================================================
# Half-Day Summary Schema
# =============================================================================


class HalfDaySummary(BaseModel):
    """Summary of half-day allocation for a rotation template."""

    fm_clinic: int = 0
    specialty: int = 0
    elective: int = 0
    conference: int = 0
    inpatient: int = 0
    call: int = 0
    procedure: int = 0
    off: int = 0
    total: int = 0

    @classmethod
    def from_patterns(cls, patterns: list[WeeklyPatternResponse]) -> "HalfDaySummary":
        """Calculate summary from list of patterns."""
        summary = cls()
        for pattern in patterns:
            activity = pattern.activity_type
            if hasattr(summary, activity):
                setattr(summary, activity, getattr(summary, activity) + 1)
            summary.total += 1
        return summary
