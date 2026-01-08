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
    week_number: int | None = Field(
        None,
        ge=1,
        le=4,
        description="Week 1-4 within block. NULL = same pattern all weeks",
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
    week_number: int | None = Field(None, ge=1, le=4)
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
    Max 14 patterns per week (7 days x 2 time periods).
    Max 56 patterns total (14 slots × 4 weeks) for week-specific patterns.
    """

    patterns: list[WeeklyPatternCreate] = Field(
        ...,
        max_length=56,
        description="Up to 56 slots (14 per week × 4 weeks)",
    )
    # Optional: specify if all weeks should use the same pattern
    same_pattern_all_weeks: bool = Field(
        True,
        description="If true, week_number is ignored and all weeks use same pattern",
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


# =============================================================================
# Half-Day Requirement Schemas
# =============================================================================


class HalfDayRequirementBase(BaseModel):
    """Base schema for rotation half-day requirements."""

    fm_clinic_halfdays: int = Field(
        default=4,
        ge=0,
        le=14,
        description="Number of FM clinic half-days per block",
    )
    specialty_halfdays: int = Field(
        default=5,
        ge=0,
        le=14,
        description="Number of specialty half-days per block",
    )
    specialty_name: str | None = Field(
        default=None,
        max_length=255,
        description="Name of the specialty (e.g., 'Neurology', 'Dermatology')",
    )
    academics_halfdays: int = Field(
        default=1,
        ge=0,
        le=14,
        description="Number of academic/lecture half-days per block",
    )
    elective_halfdays: int = Field(
        default=0,
        ge=0,
        le=14,
        description="Number of elective/buffer half-days per block",
    )
    min_consecutive_specialty: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Minimum consecutive specialty days to batch together",
    )
    prefer_combined_clinic_days: bool = Field(
        default=True,
        description="Prefer FM + specialty on same day when possible",
    )


class HalfDayRequirementCreate(HalfDayRequirementBase):
    """Schema for creating half-day requirements."""

    pass


class HalfDayRequirementUpdate(BaseModel):
    """Schema for updating half-day requirements (all fields optional)."""

    fm_clinic_halfdays: int | None = Field(default=None, ge=0, le=14)
    specialty_halfdays: int | None = Field(default=None, ge=0, le=14)
    specialty_name: str | None = None
    academics_halfdays: int | None = Field(default=None, ge=0, le=14)
    elective_halfdays: int | None = Field(default=None, ge=0, le=14)
    min_consecutive_specialty: int | None = Field(default=None, ge=1, le=5)
    prefer_combined_clinic_days: bool | None = None


class HalfDayRequirementResponse(HalfDayRequirementBase):
    """Response schema for half-day requirements."""

    id: UUID
    rotation_template_id: UUID
    total_halfdays: int = Field(description="Calculated total half-days")
    is_balanced: bool = Field(
        description="True if total equals standard block (10 half-days)"
    )

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Batch Pattern Update Schemas
# =============================================================================


class BatchPatternSlot(BaseModel):
    """Single slot definition for batch pattern updates."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Sunday, 6=Saturday")
    time_of_day: Literal["AM", "PM"]
    linked_template_id: UUID | None = Field(
        None, description="Template to assign to this slot (null to clear)"
    )
    activity_type: str | None = Field(
        None, max_length=50, description="Activity type override (optional)"
    )
    is_protected: bool | None = Field(None, description="Protected status (optional)")
    notes: str | None = Field(None, max_length=200, description="Slot notes (optional)")


class BatchPatternUpdateRequest(BaseModel):
    """Request schema for bulk updating weekly patterns across multiple templates.

    Supports two modes:
    - overlay: Only modifies specified slots, leaves others unchanged
    - replace: Replaces entire pattern with the provided slots

    Week selection allows applying patterns to specific weeks (1-4) or all weeks.
    """

    template_ids: list[UUID] = Field(
        ..., min_length=1, description="Template IDs to update"
    )
    mode: Literal["overlay", "replace"] = Field(
        "overlay",
        description="overlay=merge with existing, replace=overwrite all",
    )
    slots: list[BatchPatternSlot] = Field(
        ..., min_length=1, max_length=14, description="Slots to apply (max 14 per week)"
    )
    week_numbers: list[int] | None = Field(
        None,
        description="Weeks to apply to (1-4). Null = all weeks / same pattern all weeks",
    )
    dry_run: bool = Field(False, description="Preview changes without applying")


class BatchPatternUpdateResult(BaseModel):
    """Result for a single template in batch update."""

    template_id: UUID
    template_name: str
    success: bool
    slots_modified: int = 0
    error: str | None = None


class BatchPatternUpdateResponse(BaseModel):
    """Response for batch pattern update."""

    total_templates: int
    successful: int
    failed: int
    results: list[BatchPatternUpdateResult]
    dry_run: bool = False
