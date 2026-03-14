"""Pydantic schemas for primary duty configuration."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PrimaryDutyConfigCreate(BaseModel):
    """Request to create a primary duty configuration."""

    duty_name: str = Field(..., min_length=1, max_length=100)
    clinic_min_per_week: int = Field(default=0, ge=0, le=20)
    clinic_max_per_week: int = Field(default=10, ge=0, le=20)
    available_days: list[int] = Field(
        default=[0, 1, 2, 3, 4],
        description="Available weekdays (0=Mon, 4=Fri)",
    )

    @field_validator("available_days")
    @classmethod
    def validate_days(cls, v: list[int]) -> list[int]:
        if not all(0 <= d <= 4 for d in v):
            raise ValueError("available_days must contain only values 0-4 (Mon-Fri)")
        return sorted(set(v))

    @model_validator(mode="after")
    def validate_min_max(self) -> "PrimaryDutyConfigCreate":
        if self.clinic_min_per_week > self.clinic_max_per_week:
            raise ValueError(
                f"clinic_min_per_week ({self.clinic_min_per_week}) "
                f"cannot exceed clinic_max_per_week ({self.clinic_max_per_week})"
            )
        return self


class PrimaryDutyConfigUpdate(BaseModel):
    """Request to update a primary duty configuration."""

    duty_name: str | None = Field(default=None, min_length=1, max_length=100)
    clinic_min_per_week: int | None = Field(default=None, ge=0, le=20)
    clinic_max_per_week: int | None = Field(default=None, ge=0, le=20)
    available_days: list[int] | None = Field(default=None)

    @field_validator("available_days")
    @classmethod
    def validate_days(cls, v: list[int] | None) -> list[int] | None:
        if v is not None and not all(0 <= d <= 4 for d in v):
            raise ValueError("available_days must contain only values 0-4 (Mon-Fri)")
        return sorted(set(v)) if v is not None else None


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
