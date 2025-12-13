"""Rotation template schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class RotationTemplateBase(BaseModel):
    """Base rotation template schema."""
    name: str
    activity_type: str  # 'clinic', 'inpatient', 'procedure', 'conference'
    abbreviation: Optional[str] = None
    clinic_location: Optional[str] = None
    max_residents: Optional[int] = None
    requires_specialty: Optional[str] = None
    requires_procedure_credential: bool = False
    supervision_required: bool = True
    max_supervision_ratio: int = 4


class RotationTemplateCreate(RotationTemplateBase):
    """Schema for creating a rotation template."""
    pass


class RotationTemplateUpdate(BaseModel):
    """Schema for updating a rotation template."""
    name: Optional[str] = None
    activity_type: Optional[str] = None
    abbreviation: Optional[str] = None
    clinic_location: Optional[str] = None
    max_residents: Optional[int] = None
    requires_specialty: Optional[str] = None
    requires_procedure_credential: Optional[bool] = None
    supervision_required: Optional[bool] = None
    max_supervision_ratio: Optional[int] = None


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
