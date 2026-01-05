"""Resident weekly requirement schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ResidentWeeklyRequirementBase(BaseModel):
    """Base schema for resident weekly requirements."""

    fm_clinic_min_per_week: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Minimum FM clinic half-days per week (ACGME: 2 for outpatient)",
    )
    fm_clinic_max_per_week: int = Field(
        default=3, ge=0, le=10, description="Maximum FM clinic half-days per week"
    )
    specialty_min_per_week: int = Field(
        default=0, ge=0, le=10, description="Minimum specialty half-days per week"
    )
    specialty_max_per_week: int = Field(
        default=10, ge=0, le=10, description="Maximum specialty half-days per week"
    )
    academics_required: bool = Field(
        default=True, description="Whether academic time (Wed AM) is required"
    )
    protected_slots: dict[str, str] = Field(
        default_factory=dict,
        description="Protected slots mapping (e.g., {'wed_am': 'conference'})",
    )
    allowed_clinic_days: list[int] = Field(
        default_factory=list,
        description="Allowed clinic days (0=Mon, 4=Fri). Empty = all weekdays allowed",
    )
    specialty_name: str | None = Field(
        default=None, max_length=255, description="Specialty name (e.g., 'Neurology')"
    )
    description: str | None = Field(
        default=None, max_length=1024, description="Optional notes about requirements"
    )

    @field_validator("protected_slots")
    @classmethod
    def validate_protected_slots(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate protected_slots keys are valid slot identifiers."""
        valid_days = ["mon", "tue", "wed", "thu", "fri"]
        valid_times = ["am", "pm"]

        for slot_key in v.keys():
            parts = slot_key.lower().split("_")
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid slot key '{slot_key}'. Format: 'day_time' (e.g., 'wed_am')"
                )
            if parts[0] not in valid_days:
                raise ValueError(
                    f"Invalid day '{parts[0]}' in slot key. Must be one of {valid_days}"
                )
            if parts[1] not in valid_times:
                raise ValueError(
                    f"Invalid time '{parts[1]}' in slot key. Must be 'am' or 'pm'"
                )

        return v

    @field_validator("allowed_clinic_days")
    @classmethod
    def validate_allowed_days(cls, v: list[int]) -> list[int]:
        """Validate allowed_clinic_days are valid weekday integers."""
        for day in v:
            if day < 0 or day > 4:
                raise ValueError(
                    f"Invalid day {day}. Must be 0-4 (Monday=0, Friday=4)"
                )
        return sorted(set(v))  # Remove duplicates and sort

    @model_validator(mode="after")
    def validate_ranges(self) -> "ResidentWeeklyRequirementBase":
        """Validate that min values are less than or equal to max values."""
        if self.fm_clinic_min_per_week > self.fm_clinic_max_per_week:
            raise ValueError(
                f"fm_clinic_min_per_week ({self.fm_clinic_min_per_week}) cannot exceed "
                f"fm_clinic_max_per_week ({self.fm_clinic_max_per_week})"
            )
        if self.specialty_min_per_week > self.specialty_max_per_week:
            raise ValueError(
                f"specialty_min_per_week ({self.specialty_min_per_week}) cannot exceed "
                f"specialty_max_per_week ({self.specialty_max_per_week})"
            )
        return self


class ResidentWeeklyRequirementCreate(ResidentWeeklyRequirementBase):
    """Schema for creating a resident weekly requirement."""

    rotation_template_id: UUID = Field(
        ..., description="UUID of the rotation template this applies to"
    )


class ResidentWeeklyRequirementUpdate(BaseModel):
    """Schema for updating a resident weekly requirement (all fields optional)."""

    fm_clinic_min_per_week: int | None = Field(
        default=None,
        ge=0,
        le=10,
        description="Minimum FM clinic half-days per week",
    )
    fm_clinic_max_per_week: int | None = Field(
        default=None, ge=0, le=10, description="Maximum FM clinic half-days per week"
    )
    specialty_min_per_week: int | None = Field(
        default=None, ge=0, le=10, description="Minimum specialty half-days per week"
    )
    specialty_max_per_week: int | None = Field(
        default=None, ge=0, le=10, description="Maximum specialty half-days per week"
    )
    academics_required: bool | None = Field(
        default=None, description="Whether academic time is required"
    )
    protected_slots: dict[str, str] | None = Field(
        default=None, description="Protected slots mapping"
    )
    allowed_clinic_days: list[int] | None = Field(
        default=None, description="Allowed clinic days"
    )
    specialty_name: str | None = Field(
        default=None, max_length=255, description="Specialty name"
    )
    description: str | None = Field(
        default=None, max_length=1024, description="Optional notes"
    )

    @field_validator("protected_slots")
    @classmethod
    def validate_protected_slots(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """Validate protected_slots keys if provided."""
        if v is None:
            return v

        valid_days = ["mon", "tue", "wed", "thu", "fri"]
        valid_times = ["am", "pm"]

        for slot_key in v.keys():
            parts = slot_key.lower().split("_")
            if len(parts) != 2:
                raise ValueError(f"Invalid slot key '{slot_key}'")
            if parts[0] not in valid_days or parts[1] not in valid_times:
                raise ValueError(f"Invalid slot key '{slot_key}'")

        return v

    @field_validator("allowed_clinic_days")
    @classmethod
    def validate_allowed_days(cls, v: list[int] | None) -> list[int] | None:
        """Validate allowed_clinic_days if provided."""
        if v is None:
            return v
        for day in v:
            if day < 0 or day > 4:
                raise ValueError(f"Invalid day {day}. Must be 0-4")
        return sorted(set(v))


class ResidentWeeklyRequirementResponse(ResidentWeeklyRequirementBase):
    """Schema for resident weekly requirement response."""

    id: UUID
    rotation_template_id: UUID
    created_at: datetime
    updated_at: datetime

    # Computed properties
    total_min_halfdays: int = Field(description="Minimum half-days required per week")
    total_max_halfdays: int = Field(description="Maximum half-days allowed per week")
    is_valid_range: bool = Field(description="Whether min/max ranges are valid")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_computed(cls, obj) -> "ResidentWeeklyRequirementResponse":
        """Create response with computed properties from ORM object."""
        return cls(
            id=obj.id,
            rotation_template_id=obj.rotation_template_id,
            fm_clinic_min_per_week=obj.fm_clinic_min_per_week,
            fm_clinic_max_per_week=obj.fm_clinic_max_per_week,
            specialty_min_per_week=obj.specialty_min_per_week,
            specialty_max_per_week=obj.specialty_max_per_week,
            academics_required=obj.academics_required,
            protected_slots=obj.protected_slots or {},
            allowed_clinic_days=obj.allowed_clinic_days or [],
            specialty_name=obj.specialty_name,
            description=obj.description,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            total_min_halfdays=obj.total_min_halfdays,
            total_max_halfdays=obj.total_max_halfdays,
            is_valid_range=obj.is_valid_range,
        )


class ResidentWeeklyRequirementListResponse(BaseModel):
    """Schema for list of resident weekly requirements."""

    items: list[ResidentWeeklyRequirementResponse]
    total: int


class ResidentWeeklyRequirementWithTemplate(ResidentWeeklyRequirementResponse):
    """Response including the associated rotation template name."""

    template_name: str = Field(description="Name of the associated rotation template")
    template_activity_type: str = Field(
        description="Activity type of the rotation template"
    )
