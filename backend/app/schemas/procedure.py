"""Procedure schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class ProcedureBase(BaseModel):
    """Base procedure schema."""

    name: str
    description: str | None = None
    category: str | None = None  # 'surgical', 'office', 'obstetric', 'clinic'
    specialty: str | None = None  # 'Sports Medicine', 'OB/GYN', etc.
    supervision_ratio: int = 1
    requires_certification: bool = True
    complexity_level: str = "standard"
    min_pgy_level: int = 1
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        """Validate category is one of the valid types."""
        if v is not None:
            valid_categories = ("surgical", "office", "obstetric", "clinic")
            if v not in valid_categories:
                raise ValueError(f"category must be one of {valid_categories}")
        return v

    @field_validator("complexity_level")
    @classmethod
    def validate_complexity(cls, v: str) -> str:
        valid_levels = ("basic", "standard", "advanced", "complex")
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

    name: str | None = None
    description: str | None = None
    category: str | None = None
    specialty: str | None = None
    supervision_ratio: int | None = None
    requires_certification: bool | None = None
    complexity_level: str | None = None
    min_pgy_level: int | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate name is not empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("name cannot be empty")
        return v.strip() if v else v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        """Validate category is one of the valid types."""
        if v is not None:
            valid_categories = ("surgical", "office", "obstetric", "clinic")
            if v not in valid_categories:
                raise ValueError(f"category must be one of {valid_categories}")
        return v

    @field_validator("complexity_level")
    @classmethod
    def validate_complexity(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_levels = ("basic", "standard", "advanced", "complex")
        if v not in valid_levels:
            raise ValueError(f"complexity_level must be one of {valid_levels}")
        return v

    @field_validator("min_pgy_level")
    @classmethod
    def validate_pgy_level(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 1 or v > 3:
            raise ValueError("min_pgy_level must be between 1 and 3")
        return v

    @field_validator("supervision_ratio")
    @classmethod
    def validate_supervision_ratio(cls, v: int | None) -> int | None:
        """Validate supervision_ratio is positive."""
        if v is not None and v < 1:
            raise ValueError("supervision_ratio must be at least 1")
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
    specialty: str | None = None
    category: str | None = None

    class Config:
        from_attributes = True
