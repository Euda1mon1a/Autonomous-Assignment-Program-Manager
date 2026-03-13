from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GraduationRequirementBase(BaseModel):
    """Base schema for graduation requirements."""

    pgy_level: int = Field(
        ..., ge=1, le=7, description="PGY level this requirement applies to"
    )
    rotation_template_id: UUID = Field(
        ..., description="The clinical template/type required"
    )
    min_halves: int = Field(0, ge=0, description="Minimum number of half-days required")
    target_halves: int | None = Field(
        None, ge=0, description="Target number of half-days (optional)"
    )
    by_date: date | None = Field(
        None, description="Date by which requirement must be met (optional)"
    )


class GraduationRequirementCreate(GraduationRequirementBase):
    """Schema for creating a graduation requirement."""

    pass


class GraduationRequirementUpdate(BaseModel):
    """Schema for updating a graduation requirement."""

    min_halves: int | None = Field(None, ge=0)
    target_halves: int | None = Field(None, ge=0)
    by_date: date | None = None


class GraduationRequirementInDBBase(GraduationRequirementBase):
    """Base schema for graduation requirement in DB."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)


class GraduationRequirement(GraduationRequirementInDBBase):
    """Schema for graduation requirement returned to client."""

    created_at: datetime
    updated_at: datetime
