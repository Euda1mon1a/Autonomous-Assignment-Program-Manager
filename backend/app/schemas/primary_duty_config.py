"""Pydantic schemas for primary duty configuration."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PrimaryDutyConfigCreate(BaseModel):
    """Request to create a primary duty configuration."""

    duty_name: str = Field(..., min_length=1, max_length=100)
    clinic_min_per_week: int = Field(default=0, ge=0)
    clinic_max_per_week: int = Field(default=10, ge=0)
    available_days: list[int] = Field(
        default=[0, 1, 2, 3, 4],
        description="Available weekdays (0=Mon, 4=Fri)",
    )


class PrimaryDutyConfigUpdate(BaseModel):
    """Request to update a primary duty configuration."""

    duty_name: str | None = Field(default=None, min_length=1, max_length=100)
    clinic_min_per_week: int | None = Field(default=None, ge=0)
    clinic_max_per_week: int | None = Field(default=None, ge=0)
    available_days: list[int] | None = Field(default=None)


class PrimaryDutyConfigResponse(BaseModel):
    """Response for a primary duty configuration."""

    id: UUID
    duty_name: str
    clinic_min_per_week: int
    clinic_max_per_week: int
    available_days: list[int]
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
