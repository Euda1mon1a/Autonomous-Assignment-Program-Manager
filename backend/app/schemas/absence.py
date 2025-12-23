"""Absence schemas."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

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


# Valid types as tuple for validation
VALID_ABSENCE_TYPES = tuple(t.value for t in AbsenceType)


class AbsenceBase(BaseModel):
    """Base absence schema."""

    person_id: UUID
    start_date: date
    end_date: date
    absence_type: str
    deployment_orders: bool = False
    tdy_location: str | None = None
    replacement_activity: str | None = None
    notes: str | None = None

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


class AbsenceCreate(AbsenceBase):
    """
    Schema for creating an absence.

    For admin quick-block workflow (emergency absences):
    - Set return_date_tentative=True when exact return is unknown
    - created_by_id tracks which admin entered the absence
    - end_date defaults should be start_date + 10 days for Hawaii (UI handles this)
    """

    is_blocking: bool | None = None  # Auto-determined if not set
    return_date_tentative: bool = False
    created_by_id: UUID | None = None


class AbsenceUpdate(BaseModel):
    """Schema for updating an absence."""

    start_date: date | None = None
    end_date: date | None = None
    absence_type: str | None = None
    is_blocking: bool | None = None
    return_date_tentative: bool | None = None
    deployment_orders: bool | None = None
    tdy_location: str | None = None
    replacement_activity: str | None = None
    notes: str | None = None

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


class AbsenceResponse(AbsenceBase):
    """Schema for absence response."""

    id: UUID
    is_blocking: bool | None
    return_date_tentative: bool
    created_by_id: UUID | None
    created_at: datetime

    class Config:
        from_attributes = True
