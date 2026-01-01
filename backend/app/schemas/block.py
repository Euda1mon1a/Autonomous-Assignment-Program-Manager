"""Block schemas."""

from datetime import date as date_type
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.validators.date_validators import validate_academic_year_date


class BlockBase(BaseModel):
    """Base block schema."""

    date: date_type = Field(..., description="Date of the block")
    time_of_day: str = Field(
        ..., description="Time of day: AM or PM", pattern="^(AM|PM)$"
    )
    block_number: int = Field(
        ..., ge=1, le=730, description="Block number in academic year (1-730)"
    )
    is_weekend: bool = Field(False, description="Whether this block falls on a weekend")
    is_holiday: bool = Field(False, description="Whether this block is a holiday")
    holiday_name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Name of the holiday if applicable",
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date_type) -> date_type:
        """Validate date is within academic year bounds."""
        return validate_academic_year_date(v, field_name="date")

    @field_validator("time_of_day")
    @classmethod
    def validate_time_of_day(cls, v: str) -> str:
        if v not in ("AM", "PM"):
            raise ValueError("time_of_day must be 'AM' or 'PM'")
        return v

    @field_validator("block_number")
    @classmethod
    def validate_block_number(cls, v: int) -> int:
        """Validate block_number is within valid range."""
        if v < 0 or v > 13:
            raise ValueError("block_number must be between 0 and 13")
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

    items: list[BlockResponse] = Field(..., description="List of block responses")
    total: int = Field(..., ge=0, description="Total number of blocks")
