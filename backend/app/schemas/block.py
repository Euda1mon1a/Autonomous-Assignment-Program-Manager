"""Block schemas."""
from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator


class BlockBase(BaseModel):
    """Base block schema."""
    date: date
    time_of_day: str  # 'AM' or 'PM'
    block_number: int
    is_weekend: bool = False
    is_holiday: bool = False
    holiday_name: Optional[str] = None

    @field_validator("time_of_day")
    @classmethod
    def validate_time_of_day(cls, v: str) -> str:
        if v not in ("AM", "PM"):
            raise ValueError("time_of_day must be 'AM' or 'PM'")
        return v


class BlockCreate(BlockBase):
    """Schema for creating a block."""
    pass


class BlockResponse(BlockBase):
    """Schema for block response."""
    id: UUID

    class Config:
        from_attributes = True


class BlockListResponse(BaseModel):
    """Schema for list of blocks."""
    items: list[BlockResponse]
    total: int
