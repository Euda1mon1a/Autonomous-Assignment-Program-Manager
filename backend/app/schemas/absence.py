"""Absence schemas."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.validators.date_validators import validate_academic_year_date


class AbsenceType(str, Enum):
    """
    Valid absence types with Hawaii-appropriate defaults.

    Blocking types (person cannot be assigned during absence):
    - deployment, tdy, family_emergency, bereavement, emergency_leave,
      convalescent, maternity_paternity

    Duration-based blocking:
    - medical (>7 days), sick (>3 days)

    Non-blocking (tracked but doesn't prevent assignment):
    - vacation, conference
    """

    VACATION = "vacation"
    DEPLOYMENT = "deployment"
    TDY = "tdy"
    MEDICAL = "medical"
    FAMILY_EMERGENCY = "family_emergency"
    CONFERENCE = "conference"
    # New types (Hawaii-appropriate)
    BEREAVEMENT = "bereavement"
    EMERGENCY_LEAVE = "emergency_leave"
    SICK = "sick"
    CONVALESCENT = "convalescent"
    MATERNITY_PATERNITY = "maternity_paternity"
    # Military-specific types
    TRAINING = "training"
    MILITARY_DUTY = "military_duty"


# Valid types as tuple for validation
VALID_ABSENCE_TYPES = tuple(t.value for t in AbsenceType)


class AbsenceBase(BaseModel):
    """Base absence schema."""

    person_id: UUID = Field(..., description="Person UUID")
    start_date: date = Field(..., description="Absence start date")
    end_date: date = Field(..., description="Absence end date")
    absence_type: str = Field(..., description="Type of absence")
    deployment_orders: bool | None = Field(
        default=False, description="Whether deployment orders exist"
    )
    tdy_location: str | None = Field(
        None, max_length=200, description="TDY location (if applicable)"
    )
    replacement_activity: str | None = Field(
        None, max_length=200, description="Replacement activity (if applicable)"
    )
    notes: str | None = Field(None, max_length=1000, description="Absence notes")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date) -> date:
        """Validate dates are within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

    @field_validator("absence_type")
    @classmethod
    def validate_absence_type(cls, v: str) -> str:
        if v not in VALID_ABSENCE_TYPES:
            raise ValueError(f"absence_type must be one of {VALID_ABSENCE_TYPES}")
        return v

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self

    @field_validator("notes")
    @classmethod
    def validate_notes_length(cls, v: str | None) -> str | None:
        """Validate notes field length."""
        if v is not None and len(v) > 2000:
            raise ValueError("notes must be less than 2000 characters")
        return v


class AbsenceCreate(AbsenceBase):
    """
    Schema for creating an absence.

    For admin quick-block workflow (emergency absences):
    - Set return_date_tentative=True when exact return is unknown
    - created_by_id tracks which admin entered the absence
    - end_date defaults should be start_date + 10 days for Hawaii (UI handles this)

    Away-from-program tracking:
    - Residents: defaults to True (all absence time counts toward 28-day limit)
    - Faculty: should always be False (no away-from-program tracking)
    - Admin can override if needed
    """

    is_blocking: bool | None = None  # Auto-determined if not set
    return_date_tentative: bool = False
    created_by_id: UUID | None = None
    is_away_from_program: bool = Field(
        default=True,
        description="Whether this absence counts toward away-from-program limit (28 days/year for residents)",
    )


class AbsenceUpdate(BaseModel):
    """Schema for updating an absence."""

    start_date: date | None = Field(None, description="Absence start date")
    end_date: date | None = Field(None, description="Absence end date")
    absence_type: str | None = Field(None, description="Type of absence")
    is_blocking: bool | None = Field(None, description="Whether absence is blocking")
    return_date_tentative: bool | None = Field(
        None, description="Whether return date is tentative"
    )
    is_away_from_program: bool | None = Field(
        None, description="Whether this counts toward away-from-program limit"
    )
    deployment_orders: bool | None = Field(
        None, description="Whether deployment orders exist"
    )
    tdy_location: str | None = Field(
        None, max_length=200, description="TDY location (if applicable)"
    )
    replacement_activity: str | None = Field(
        None, max_length=200, description="Replacement activity (if applicable)"
    )
    notes: str | None = Field(None, max_length=1000, description="Absence notes")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date | None) -> date | None:
        """Validate dates are within academic year bounds."""
        if v is not None:
            return validate_academic_year_date(v, field_name="date")
        return v

    @field_validator("absence_type")
    @classmethod
    def validate_absence_type(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_ABSENCE_TYPES:
            raise ValueError(f"absence_type must be one of {VALID_ABSENCE_TYPES}")
        return v

    @field_validator("notes")
    @classmethod
    def validate_notes_length(cls, v: str | None) -> str | None:
        """Validate notes field length."""
        if v is not None and len(v) > 2000:
            raise ValueError("notes must be less than 2000 characters")
        return v


class AbsenceResponse(AbsenceBase):
    """Schema for absence response."""

    id: UUID
    is_blocking: bool | None
    return_date_tentative: bool
    is_away_from_program: bool = Field(
        description="Whether this counts toward away-from-program limit (28 days/year)"
    )
    created_by_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AbsenceListResponse(BaseModel):
    """Schema for paginated absence list response."""

    items: list[AbsenceResponse]
    total: int
    page: int | None = None
    page_size: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Bulk Import Schemas
# ============================================================================


class AbsenceBulkCreate(BaseModel):
    """Schema for bulk absence creation.

    Accepts a list of AbsenceCreate items to be validated and created.
    """

    absences: list[AbsenceCreate] = Field(
        ..., description="List of absences to create", min_length=1, max_length=500
    )


class AbsenceValidationError(BaseModel):
    """Schema for individual absence validation error."""

    index: int = Field(..., description="Index of the absence in the input list")
    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    absence_data: dict | None = Field(None, description="Original absence data")


class AbsenceBulkPreview(BaseModel):
    """Schema for bulk absence preview response.

    Returns validated absences and any validation errors found.
    """

    valid: list[AbsenceCreate] = Field(
        default_factory=list, description="Absences that passed validation"
    )
    errors: list[AbsenceValidationError] = Field(
        default_factory=list, description="Validation errors"
    )
    summary: dict = Field(
        default_factory=dict,
        description="Summary counts (by type, date range, person count)",
    )


class AbsenceBulkApply(BaseModel):
    """Schema for bulk absence apply response.

    Reports results of applying validated absences.
    """

    created: int = Field(0, description="Number of absences successfully created")
    skipped: int = Field(0, description="Number of absences skipped (e.g., duplicates)")
    errors: list[AbsenceValidationError] = Field(
        default_factory=list, description="Errors encountered during apply"
    )


# ============================================================================
# Away-From-Program Tracking Schemas
# ============================================================================


class ThresholdStatus(str, Enum):
    """Threshold status for away-from-program tracking."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


class AwayAbsenceDetail(BaseModel):
    """Detail of an absence contributing to away-from-program count."""

    id: str
    start_date: str
    end_date: str
    absence_type: str
    days: int = Field(..., description="Days counted toward away-from-program")


class AwayFromProgramSummary(BaseModel):
    """Summary of a resident's away-from-program status.

    Used to track progress toward the 28-day annual limit.
    Exceeding this limit requires training extension.
    """

    person_id: str
    academic_year: str = Field(..., description="Academic year (e.g., '2025-2026')")
    days_used: int = Field(..., description="Total days away from program this year")
    days_remaining: int = Field(..., description="Days remaining before limit (max 0)")
    threshold_status: ThresholdStatus = Field(
        ..., description="Current status: ok, warning, critical, exceeded"
    )
    max_days: int = Field(default=28, description="Maximum allowed days per year")
    warning_days: int = Field(default=21, description="Warning threshold (75%)")
    absences: list[AwayAbsenceDetail] = Field(
        default_factory=list, description="Absences contributing to count"
    )


class AwayFromProgramCheck(BaseModel):
    """Response for threshold check (before creating new absence)."""

    current_days: int = Field(..., description="Current days used")
    projected_days: int = Field(..., description="Days if new absence is added")
    threshold_status: ThresholdStatus
    days_remaining: int
    max_days: int = 28
    warning_days: int = 21


class AllResidentsAwayStatus(BaseModel):
    """Away-from-program status for all residents (compliance dashboard)."""

    academic_year: str
    residents: list[AwayFromProgramSummary]
    summary: dict = Field(
        default_factory=dict,
        description="Summary: counts by status (ok, warning, critical, exceeded)",
    )
