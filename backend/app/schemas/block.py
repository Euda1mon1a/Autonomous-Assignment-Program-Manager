"""Block schemas."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.validators.date_validators import validate_academic_year_date


class BlockBase(BaseModel):
    """Base block schema."""

    date: date
    time_of_day: str  # 'AM' or 'PM'
    block_number: int
    is_weekend: bool = False
    is_holiday: bool = False
    holiday_name: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        """Validate date is within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

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

    model_config = ConfigDict(from_attributes=True)


class BlockListResponse(BaseModel):
    """Schema for list of blocks."""

    items: list[BlockResponse]
    total: int
