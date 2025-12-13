"""Assignment schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator


class AssignmentBase(BaseModel):
    """Base assignment schema."""
    block_id: UUID
    person_id: UUID
    rotation_template_id: Optional[UUID] = None
    role: str  # 'primary', 'supervising', 'backup'
    activity_override: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")
        return v


class AssignmentCreate(AssignmentBase):
    """Schema for creating an assignment."""
    created_by: Optional[str] = None


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment."""
    rotation_template_id: Optional[UUID] = None
    role: Optional[str] = None
    activity_override: Optional[str] = None
    notes: Optional[str] = None


class AssignmentResponse(AssignmentBase):
    """Schema for assignment response."""
    id: UUID
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
