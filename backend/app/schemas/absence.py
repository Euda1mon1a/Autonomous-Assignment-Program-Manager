"""Absence schemas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator


class AbsenceBase(BaseModel):
    """Base absence schema."""
    person_id: UUID
    start_date: date
    end_date: date
    absence_type: str  # 'vacation', 'deployment', 'tdy', 'medical', 'family_emergency', 'conference'
    deployment_orders: bool = False
    tdy_location: str | None = None
    replacement_activity: str | None = None
    notes: str | None = None

    @field_validator("absence_type")
    @classmethod
    def validate_absence_type(cls, v: str) -> str:
        valid_types = ("vacation", "deployment", "tdy", "medical", "family_emergency", "conference")
        if v not in valid_types:
            raise ValueError(f"absence_type must be one of {valid_types}")
        return v

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self


class AbsenceCreate(AbsenceBase):
    """Schema for creating an absence."""
    pass


class AbsenceUpdate(BaseModel):
    """Schema for updating an absence."""
    start_date: date | None = None
    end_date: date | None = None
    absence_type: str | None = None
    deployment_orders: bool | None = None
    tdy_location: str | None = None
    replacement_activity: str | None = None
    notes: str | None = None


class AbsenceResponse(AbsenceBase):
    """Schema for absence response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
