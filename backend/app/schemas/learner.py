"""Pydantic schemas for learner (med student / rotating intern) API."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LearnerTrackBase(BaseModel):
    track_number: int = Field(ge=1, le=7)
    default_fmit_week: int = Field(ge=1, le=4)
    description: str | None = None


class LearnerTrackCreate(LearnerTrackBase):
    pass


class LearnerTrackResponse(LearnerTrackBase):
    id: UUID

    model_config = {"from_attributes": True}


class LearnerCreate(BaseModel):
    name: str
    email: str | None = None
    type: str = Field(pattern="^(med_student|rotating_intern)$")
    learner_type: str = Field(pattern="^(MS|TY|PSYCH)$")
    med_school: str | None = None
    ms_year: int | None = Field(default=None, ge=3, le=4)
    requires_fmit: bool = True


class LearnerResponse(BaseModel):
    id: UUID
    name: str
    type: str
    learner_type: str | None
    med_school: str | None
    ms_year: int | None
    requires_fmit: bool | None
    rotation_start_date: datetime | None
    rotation_end_date: datetime | None

    model_config = {"from_attributes": True}


class LearnerToTrackCreate(BaseModel):
    learner_id: UUID
    track_id: UUID
    start_date: date
    end_date: date
    requires_fmit: bool = True


class LearnerToTrackResponse(BaseModel):
    id: UUID
    learner_id: UUID
    track_id: UUID
    start_date: date
    end_date: date
    requires_fmit: bool

    model_config = {"from_attributes": True}


class LearnerAssignmentCreate(BaseModel):
    learner_id: UUID
    block_id: UUID
    parent_assignment_id: UUID | None = None
    activity_type: str
    day_of_week: int = Field(ge=0, le=4)
    time_of_day: str = Field(pattern="^(AM|PM)$")
    source: str = "manual"


class LearnerAssignmentResponse(BaseModel):
    id: UUID
    learner_id: UUID
    block_id: UUID
    parent_assignment_id: UUID | None
    activity_type: str
    day_of_week: int
    time_of_day: str
    source: str

    model_config = {"from_attributes": True}
