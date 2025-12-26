"""Rotation template schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RotationTemplateBase(BaseModel):
    """Base rotation template schema."""

    name: str
    activity_type: str  # 'clinic', 'inpatient', 'procedure', 'conference'
    abbreviation: str | None = None
    clinic_location: str | None = None
    max_residents: int | None = None
    requires_specialty: str | None = None
    requires_procedure_credential: bool | None = False
    supervision_required: bool | None = True
    max_supervision_ratio: int | None = 4


class RotationTemplateCreate(RotationTemplateBase):
    """Schema for creating a rotation template."""

    pass


class RotationTemplateUpdate(BaseModel):
    """Schema for updating a rotation template."""

    name: str | None = None
    activity_type: str | None = None
    abbreviation: str | None = None
    clinic_location: str | None = None
    max_residents: int | None = None
    requires_specialty: str | None = None
    requires_procedure_credential: bool | None = None
    supervision_required: bool | None = None
    max_supervision_ratio: int | None = None


class RotationTemplateResponse(RotationTemplateBase):
    """Schema for rotation template response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class RotationTemplateListResponse(BaseModel):
    """Schema for list of rotation templates."""

    items: list[RotationTemplateResponse]
    total: int
