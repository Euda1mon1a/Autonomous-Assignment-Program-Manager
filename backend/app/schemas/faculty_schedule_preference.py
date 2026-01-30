"""Schemas for faculty schedule preferences."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.faculty_schedule_preference import (
    FacultyPreferenceDirection,
    FacultyPreferenceType,
)


class FacultySchedulePreferenceBase(BaseModel):
    person_id: UUID
    preference_type: FacultyPreferenceType
    direction: FacultyPreferenceDirection
    rank: int = Field(..., ge=1, le=2)
    day_of_week: int = Field(..., ge=0, le=6)
    time_of_day: Literal["AM", "PM"] | None = None
    weight: int = Field(6, ge=1, le=100)
    is_active: bool = True
    notes: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_type(self):
        if self.preference_type == FacultyPreferenceType.CLINIC:
            if self.time_of_day is None:
                raise ValueError("Clinic preferences require time_of_day")
        if self.preference_type == FacultyPreferenceType.CALL:
            if self.time_of_day is not None:
                raise ValueError("Call preferences must not include time_of_day")
        return self


class FacultySchedulePreferenceCreate(FacultySchedulePreferenceBase):
    pass


class FacultySchedulePreferenceUpdate(BaseModel):
    preference_type: FacultyPreferenceType | None = None
    direction: FacultyPreferenceDirection | None = None
    rank: int | None = Field(None, ge=1, le=2)
    day_of_week: int | None = Field(None, ge=0, le=6)
    time_of_day: Literal["AM", "PM"] | None = None
    weight: int | None = Field(None, ge=1, le=100)
    is_active: bool | None = None
    notes: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_type(self):
        if self.preference_type == FacultyPreferenceType.CLINIC:
            if self.time_of_day is None:
                raise ValueError("Clinic preferences require time_of_day")
        if self.preference_type == FacultyPreferenceType.CALL:
            if self.time_of_day is not None:
                raise ValueError("Call preferences must not include time_of_day")
        return self


class FacultySchedulePreferenceResponse(FacultySchedulePreferenceBase):
    id: UUID

    class Config:
        from_attributes = True


class FacultySchedulePreferenceListResponse(BaseModel):
    items: list[FacultySchedulePreferenceResponse]
    total: int
    page: int
    page_size: int
