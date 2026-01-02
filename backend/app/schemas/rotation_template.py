"""Rotation template schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class RotationTemplateBase(BaseModel):
    """Base rotation template schema."""

    name: str
    activity_type: str  # 'clinic', 'inpatient', 'procedure', 'conference'
    abbreviation: str | None = None
    display_abbreviation: str | None = None  # User-facing code for schedule grid
    font_color: str | None = None
    background_color: str | None = None
    clinic_location: str | None = None
    max_residents: int | None = None
    requires_specialty: str | None = None
    requires_procedure_credential: bool | None = False
    supervision_required: bool | None = True
    max_supervision_ratio: int | None = 4

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, v: str) -> str:
        """Validate activity_type is one of the valid types."""
        # Valid activity types used across the system:
        # - clinic/outpatient: Clinic sessions and outpatient rotations
        # - inpatient: Hospital ward rotations (FMIT, wards)
        # - procedure/procedures: Procedural rotations
        # - conference/education: Educational activities, didactics
        # - absence: Leave, vacation, sick time
        # - off: Days off, recovery days
        # - recovery: Post-call recovery
        valid_types = (
            "clinic",
            "inpatient",
            "procedure",
            "procedures",
            "conference",
            "education",
            "outpatient",
            "absence",
            "off",
            "recovery",
        )
        if v not in valid_types:
            raise ValueError(f"activity_type must be one of {valid_types}")
        return v

    @field_validator("max_residents")
    @classmethod
    def validate_max_residents(cls, v: int | None) -> int | None:
        """Validate max_residents is positive."""
        if v is not None and v < 1:
            raise ValueError("max_residents must be at least 1")
        return v

    @field_validator("max_supervision_ratio")
    @classmethod
    def validate_max_supervision_ratio(cls, v: int | None) -> int | None:
        """Validate supervision ratio is reasonable."""
        if v is not None and (v < 1 or v > 10):
            raise ValueError("max_supervision_ratio must be between 1 and 10")
        return v


class RotationTemplateCreate(RotationTemplateBase):
    """Schema for creating a rotation template."""

    pass


class RotationTemplateUpdate(BaseModel):
    """Schema for updating a rotation template."""

    name: str | None = None
    activity_type: str | None = None
    abbreviation: str | None = None
    display_abbreviation: str | None = None  # User-facing code for schedule grid
    font_color: str | None = None
    background_color: str | None = None
    clinic_location: str | None = None
    max_residents: int | None = None
    requires_specialty: str | None = None
    requires_procedure_credential: bool | None = None
    supervision_required: bool | None = None
    max_supervision_ratio: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate name is not empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("name cannot be empty")
        return v.strip() if v else v

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, v: str | None) -> str | None:
        """Validate activity_type is one of the valid types."""
        if v is not None:
            valid_types = (
                "clinic",
                "inpatient",
                "procedure",
                "procedures",
                "conference",
                "education",
                "outpatient",
                "absence",
                "off",
                "recovery",
            )
            if v not in valid_types:
                raise ValueError(f"activity_type must be one of {valid_types}")
        return v

    @field_validator("max_residents")
    @classmethod
    def validate_max_residents(cls, v: int | None) -> int | None:
        """Validate max_residents is positive."""
        if v is not None and v < 1:
            raise ValueError("max_residents must be at least 1")
        return v

    @field_validator("max_supervision_ratio")
    @classmethod
    def validate_max_supervision_ratio(cls, v: int | None) -> int | None:
        """Validate supervision ratio is reasonable."""
        if v is not None and (v < 1 or v > 10):
            raise ValueError("max_supervision_ratio must be between 1 and 10")
        return v


class RotationTemplateResponse(RotationTemplateBase):
    """Schema for rotation template response."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RotationTemplateListResponse(BaseModel):
    """Schema for list of rotation templates."""

    items: list[RotationTemplateResponse]
    total: int
