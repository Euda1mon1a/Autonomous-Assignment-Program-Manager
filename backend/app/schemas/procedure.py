"""Procedure schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator


class ProcedureBase(BaseModel):
    """Base procedure schema."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None  # 'surgical', 'office', 'obstetric', 'clinic'
    specialty: Optional[str] = None  # 'Sports Medicine', 'OB/GYN', etc.
    supervision_ratio: int = 1
    requires_certification: bool = True
    complexity_level: str = 'standard'
    min_pgy_level: int = 1
    is_active: bool = True

    @field_validator("complexity_level")
    @classmethod
    def validate_complexity(cls, v: str) -> str:
        valid_levels = ('basic', 'standard', 'advanced', 'complex')
        if v not in valid_levels:
            raise ValueError(f"complexity_level must be one of {valid_levels}")
        return v

    @field_validator("min_pgy_level")
    @classmethod
    def validate_pgy_level(cls, v: int) -> int:
        if v < 1 or v > 3:
            raise ValueError("min_pgy_level must be between 1 and 3")
        return v

    @field_validator("supervision_ratio")
    @classmethod
    def validate_supervision_ratio(cls, v: int) -> int:
        if v < 1:
            raise ValueError("supervision_ratio must be at least 1")
        return v


class ProcedureCreate(ProcedureBase):
    """Schema for creating a procedure."""
    pass


class ProcedureUpdate(BaseModel):
    """Schema for updating a procedure."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    specialty: Optional[str] = None
    supervision_ratio: Optional[int] = None
    requires_certification: Optional[bool] = None
    complexity_level: Optional[str] = None
    min_pgy_level: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("complexity_level")
    @classmethod
    def validate_complexity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_levels = ('basic', 'standard', 'advanced', 'complex')
        if v not in valid_levels:
            raise ValueError(f"complexity_level must be one of {valid_levels}")
        return v

    @field_validator("min_pgy_level")
    @classmethod
    def validate_pgy_level(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v < 1 or v > 3:
            raise ValueError("min_pgy_level must be between 1 and 3")
        return v


class ProcedureResponse(ProcedureBase):
    """Schema for procedure response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcedureListResponse(BaseModel):
    """Schema for list of procedures."""
    items: list[ProcedureResponse]
    total: int


class ProcedureSummary(BaseModel):
    """Minimal procedure info for embedding in other responses."""
    id: UUID
    name: str
    specialty: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True
