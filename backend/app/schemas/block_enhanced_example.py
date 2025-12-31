"""
Enhanced block schemas with comprehensive validation.

This is an EXAMPLE file showing how to enhance the block.py schema
with comprehensive validation, documentation, and examples.

BEFORE implementing these changes:
1. Review with team
2. Ensure backward compatibility
3. Update tests
4. Update API documentation
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.validators.date_validators import validate_academic_year_date


class BlockBase(BaseModel):
    """Base block schema with comprehensive validation."""

    date: date = Field(
        ...,
        description=(
            "Block date (must be within current academic year). "
            "Format: YYYY-MM-DD (ISO 8601)"
        ),
        examples=["2025-01-15"],
    )

    time_of_day: str = Field(
        ...,
        pattern="^(AM|PM)$",
        description="Time of day: 'AM' (morning) or 'PM' (afternoon)",
        examples=["AM"],
    )

    block_number: int = Field(
        ...,
        ge=1,
        le=730,
        description=(
            "Block number (1-730). Academic year has 365 days × 2 sessions "
            "(AM/PM) = 730 total blocks."
        ),
        examples=[1, 365, 730],
    )

    is_weekend: bool = Field(
        default=False, description="True if block falls on Saturday or Sunday"
    )

    is_holiday: bool = Field(
        default=False, description="True if block is a federal/military holiday"
    )

    holiday_name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description=(
            "Name of holiday if is_holiday=True. "
            "Examples: 'Christmas', 'Independence Day', 'Thanksgiving'"
        ),
        examples=["Christmas", "Independence Day", None],
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date) -> date:
        """
        Validate date is within academic year bounds.

        Academic year runs from July 1 to June 30 of the following year.

        Args:
            v: Date to validate

        Returns:
            Validated date

        Raises:
            ValueError: If date is outside academic year bounds
        """
        return validate_academic_year_date(v, field_name="date")

    @field_validator("time_of_day")
    @classmethod
    def validate_time_of_day(cls, v: str) -> str:
        """
        Validate time_of_day is AM or PM.

        Args:
            v: Time of day string

        Returns:
            Validated time of day (uppercase)

        Raises:
            ValueError: If time_of_day is not AM or PM
        """
        v = v.upper()  # Normalize to uppercase
        if v not in ("AM", "PM"):
            raise ValueError(f"time_of_day must be 'AM' or 'PM', got: {v}")
        return v

    @field_validator("block_number")
    @classmethod
    def validate_block_number_range(cls, v: int) -> int:
        """
        Validate block number is in valid range.

        Block numbers run from 1 to 730 (365 days × 2 sessions).

        Args:
            v: Block number

        Returns:
            Validated block number

        Raises:
            ValueError: If block number is out of range
        """
        if not (1 <= v <= 730):
            raise ValueError(f"block_number must be between 1 and 730, got: {v}")
        return v

    @field_validator("holiday_name")
    @classmethod
    def sanitize_holiday_name(cls, v: str | None) -> str | None:
        """
        Sanitize holiday name to prevent XSS.

        Removes HTML tags and trims whitespace.

        Args:
            v: Holiday name

        Returns:
            Sanitized holiday name
        """
        if v is not None:
            import re

            # Remove HTML tags
            v = re.sub(r"<[^>]*>", "", v)
            # Trim whitespace
            v = v.strip()
            # Ensure not empty after sanitization
            if not v:
                return None
        return v

    @model_validator(mode="after")
    def validate_holiday_consistency(self):
        """
        Validate holiday fields are consistent.

        If is_holiday=True, holiday_name should be set.
        If is_holiday=False, holiday_name should be None.

        Returns:
            Self after validation

        Raises:
            ValueError: If holiday fields are inconsistent
        """
        if self.is_holiday and not self.holiday_name:
            raise ValueError("holiday_name is required when is_holiday=True")

        if not self.is_holiday and self.holiday_name:
            raise ValueError("holiday_name must be None when is_holiday=False")

        return self

    @model_validator(mode="after")
    def validate_weekend_consistency(self):
        """
        Validate is_weekend matches date's day of week.

        Returns:
            Self after validation

        Raises:
            ValueError: If is_weekend doesn't match actual day
        """
        actual_is_weekend = self.date.weekday() >= 5  # 5=Saturday, 6=Sunday

        if self.is_weekend != actual_is_weekend:
            day_name = self.date.strftime("%A")
            raise ValueError(
                f"is_weekend={self.is_weekend} but date is {day_name}. "
                f"Expected is_weekend={actual_is_weekend}"
            )

        return self


class BlockCreate(BlockBase):
    """
    Schema for creating a block.

    All fields are validated according to BlockBase constraints.
    """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Regular Weekday AM Block",
                    "description": "Standard morning block on a weekday",
                    "value": {
                        "date": "2025-01-15",
                        "time_of_day": "AM",
                        "block_number": 1,
                        "is_weekend": False,
                        "is_holiday": False,
                        "holiday_name": None,
                    },
                },
                {
                    "title": "Holiday Block",
                    "description": "Christmas Day morning block",
                    "value": {
                        "date": "2025-12-25",
                        "time_of_day": "AM",
                        "block_number": 365,
                        "is_weekend": False,
                        "is_holiday": True,
                        "holiday_name": "Christmas",
                    },
                },
                {
                    "title": "Weekend PM Block",
                    "description": "Saturday afternoon block",
                    "value": {
                        "date": "2025-01-18",
                        "time_of_day": "PM",
                        "block_number": 7,
                        "is_weekend": True,
                        "is_holiday": False,
                        "holiday_name": None,
                    },
                },
            ]
        }
    }


class BlockUpdate(BaseModel):
    """
    Schema for updating a block.

    All fields are optional for partial updates.
    """

    is_holiday: bool | None = Field(None, description="Update holiday status")

    holiday_name: str | None = Field(
        None, min_length=2, max_length=100, description="Update holiday name"
    )

    @model_validator(mode="after")
    def validate_holiday_update_consistency(self):
        """
        Validate holiday updates are consistent.

        If is_holiday is set to False, holiday_name should be None.

        Returns:
            Self after validation

        Raises:
            ValueError: If update is inconsistent
        """
        if self.is_holiday is False and self.holiday_name is not None:
            raise ValueError("holiday_name must be None when is_holiday=False")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Mark as Holiday",
                    "description": "Update block to mark as holiday",
                    "value": {"is_holiday": True, "holiday_name": "New Year's Day"},
                },
                {
                    "title": "Remove Holiday Status",
                    "description": "Update block to remove holiday status",
                    "value": {"is_holiday": False, "holiday_name": None},
                },
            ]
        }
    }


class BlockResponse(BlockBase):
    """
    Schema for block response.

    Includes all block data plus the database ID.
    """

    id: UUID = Field(
        ...,
        description="Unique block identifier (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    class Config:
        from_attributes = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "date": "2025-01-15",
                    "time_of_day": "AM",
                    "block_number": 1,
                    "is_weekend": False,
                    "is_holiday": False,
                    "holiday_name": None,
                },
                {
                    "id": "660e8400-e29b-41d4-a716-446655440001",
                    "date": "2025-12-25",
                    "time_of_day": "PM",
                    "block_number": 366,
                    "is_weekend": False,
                    "is_holiday": True,
                    "holiday_name": "Christmas",
                },
            ]
        }
    }


class BlockListResponse(BaseModel):
    """
    Schema for paginated list of blocks.

    Used for GET /blocks endpoints that return multiple blocks.
    """

    items: list[BlockResponse] = Field(
        ..., description="List of blocks in current page"
    )

    total: int = Field(..., ge=0, description="Total number of blocks matching filter")

    page: int | None = Field(None, ge=1, description="Current page number (1-indexed)")

    page_size: int | None = Field(
        None, ge=1, le=500, description="Number of items per page (max 500)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "date": "2025-01-15",
                            "time_of_day": "AM",
                            "block_number": 1,
                            "is_weekend": False,
                            "is_holiday": False,
                            "holiday_name": None,
                        },
                        {
                            "id": "660e8400-e29b-41d4-a716-446655440001",
                            "date": "2025-01-15",
                            "time_of_day": "PM",
                            "block_number": 2,
                            "is_weekend": False,
                            "is_holiday": False,
                            "holiday_name": None,
                        },
                    ],
                    "total": 730,
                    "page": 1,
                    "page_size": 100,
                }
            ]
        }
    }


class BlockFilterParams(BaseModel):
    """
    Schema for block filter query parameters.

    Used for filtering blocks in list endpoints.
    """

    start_date: date | None = Field(
        None, description="Filter blocks from this date (inclusive)"
    )

    end_date: date | None = Field(
        None, description="Filter blocks until this date (inclusive)"
    )

    time_of_day: str | None = Field(
        None, pattern="^(AM|PM)$", description="Filter by time of day: 'AM' or 'PM'"
    )

    is_weekend: bool | None = Field(
        None, description="Filter weekend blocks (true) or weekday blocks (false)"
    )

    is_holiday: bool | None = Field(
        None, description="Filter holiday blocks (true) or non-holiday blocks (false)"
    )

    page: int = Field(1, ge=1, description="Page number (1-indexed)")

    page_size: int = Field(100, ge=1, le=500, description="Items per page (max 500)")

    @model_validator(mode="after")
    def validate_date_range(self):
        """
        Validate start_date and end_date are logical.

        Returns:
            Self after validation

        Raises:
            ValueError: If end_date is before start_date
        """
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("end_date must be on or after start_date")

            # Limit date range to 1 year
            days = (self.end_date - self.start_date).days + 1
            if days > 365:
                raise ValueError(f"Date range ({days} days) cannot exceed 365 days")

        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Filter Weekday Blocks in January",
                    "value": {
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31",
                        "time_of_day": None,
                        "is_weekend": False,
                        "is_holiday": None,
                        "page": 1,
                        "page_size": 100,
                    },
                },
                {
                    "title": "Filter All Holidays",
                    "value": {
                        "start_date": None,
                        "end_date": None,
                        "time_of_day": None,
                        "is_weekend": None,
                        "is_holiday": True,
                        "page": 1,
                        "page_size": 50,
                    },
                },
            ]
        }
    }
