"""Schemas for institutional events."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.institutional_event import (
    InstitutionalEventScope,
    InstitutionalEventType,
)


class InstitutionalEventBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    event_type: InstitutionalEventType
    start_date: date
    end_date: date
    time_of_day: Literal["AM", "PM"] | None = None
    applies_to: InstitutionalEventScope = InstitutionalEventScope.ALL
    applies_to_inpatient: bool = False
    activity_id: UUID
    notes: str | None = Field(None, max_length=2000)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class InstitutionalEventCreate(InstitutionalEventBase):
    pass


class InstitutionalEventUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    event_type: InstitutionalEventType | None = None
    start_date: date | None = None
    end_date: date | None = None
    time_of_day: Literal["AM", "PM"] | None = None
    applies_to: InstitutionalEventScope | None = None
    applies_to_inpatient: bool | None = None
    activity_id: UUID | None = None
    notes: str | None = Field(None, max_length=2000)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class InstitutionalEventResponse(InstitutionalEventBase):
    id: UUID

    class Config:
        from_attributes = True


class InstitutionalEventListResponse(BaseModel):
    items: list[InstitutionalEventResponse]
    total: int
    page: int
    page_size: int
