"""Person schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class PersonBase(BaseModel):
    """Base person schema."""
    name: str
    type: str  # 'resident' or 'faculty'
    email: EmailStr | None = None
    pgy_level: int | None = None
    performs_procedures: bool = False
    specialties: list[str] | None = None
    primary_duty: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("resident", "faculty"):
            raise ValueError("type must be 'resident' or 'faculty'")
        return v

    @field_validator("pgy_level")
    @classmethod
    def validate_pgy_level(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 3):
            raise ValueError("pgy_level must be between 1 and 3")
        return v


class PersonCreate(PersonBase):
    """Schema for creating a person."""
    pass


class PersonUpdate(BaseModel):
    """Schema for updating a person."""
    name: str | None = None
    email: EmailStr | None = None
    pgy_level: int | None = None
    performs_procedures: bool | None = None
    specialties: list[str] | None = None
    primary_duty: str | None = None


class PersonResponse(PersonBase):
    """Schema for person response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PersonListResponse(BaseModel):
    """Schema for list of persons."""
    items: list[PersonResponse]
    total: int
