"""Call assignment schemas."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, field_validator


class CallTypeSchema(str, Enum):
    """Call type values for API schema validation."""

    OVERNIGHT = "overnight"
    WEEKEND = "weekend"
    BACKUP = "backup"


class CallAssignmentBase(BaseModel):
    """Base call assignment schema."""

    date: date
    person_id: UUID
    call_type: CallTypeSchema
    is_weekend: bool = False
    is_holiday: bool = False

    @field_validator("call_type")
    @classmethod
    def validate_call_type(cls, v: CallTypeSchema) -> CallTypeSchema:
        """Validate call_type is one of the allowed values."""
        if v not in (CallTypeSchema.OVERNIGHT, CallTypeSchema.WEEKEND, CallTypeSchema.BACKUP):
            raise ValueError("call_type must be 'overnight', 'weekend', or 'backup'")
        return v


class CallAssignmentCreate(CallAssignmentBase):
    """Schema for creating a call assignment."""

    pass


class CallAssignmentUpdate(BaseModel):
    """Schema for updating a call assignment."""

    date: date | None = None
    person_id: UUID | None = None
    call_type: CallTypeSchema | None = None
    is_weekend: bool | None = None
    is_holiday: bool | None = None

    @field_validator("call_type")
    @classmethod
    def validate_call_type(cls, v: CallTypeSchema | None) -> CallTypeSchema | None:
        """Validate call_type is one of the allowed values."""
        if v is not None and v not in (
            CallTypeSchema.OVERNIGHT,
            CallTypeSchema.WEEKEND,
            CallTypeSchema.BACKUP,
        ):
            raise ValueError("call_type must be 'overnight', 'weekend', or 'backup'")
        return v


class CallAssignmentResponse(CallAssignmentBase):
    """Schema for call assignment response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CallAssignmentListResponse(BaseModel):
    """Schema for list of call assignments."""

    items: list[CallAssignmentResponse]
    total: int
