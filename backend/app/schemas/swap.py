"""Pydantic schemas for FMIT swap API."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.validators.date_validators import validate_academic_year_date


class SwapStatusSchema(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class SwapTypeSchema(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ABSORB = "absorb"


class SwapExecuteRequest(BaseModel):
    source_faculty_id: UUID = Field(..., description="ID of faculty member requesting swap")
    source_week: date = Field(..., description="Week date for source faculty")
    target_faculty_id: UUID = Field(
        ..., description="ID of faculty member to swap with"
    )
    target_week: date | None = Field(
        None, description="Week date for target faculty (required for one-to-one swaps)"
    )
    swap_type: SwapTypeSchema = Field(..., description="Type of swap (one-to-one or absorb)")
    reason: str | None = Field(
        None, min_length=1, max_length=500, description="Reason for swap request"
    )

    @field_validator("source_week", "target_week")
    @classmethod
    def validate_dates_in_range(cls, v: date | None) -> date | None:
        """Validate dates are within academic year bounds."""
        if v is not None:
            return validate_academic_year_date(v, field_name="date")
        return v

    @field_validator("target_week")
    @classmethod
    def validate_swap_type_consistency(cls, v, info):
        if info.data.get("swap_type") == SwapTypeSchema.ONE_TO_ONE and v is None:
            raise ValueError("target_week required for one-to-one swaps")
        return v


class SwapApprovalRequest(BaseModel):
    approved: bool
    notes: str | None = Field(None, max_length=500)


class SwapRollbackRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)


class SwapHistoryFilter(BaseModel):
    faculty_id: UUID | None = None
    status: SwapStatusSchema | None = None
    start_date: date | None = None
    end_date: date | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates_in_range(cls, v: date | None) -> date | None:
        """Validate dates are within academic year bounds."""
        if v is not None:
            return validate_academic_year_date(v, field_name="date")
        return v


class SwapValidationResult(BaseModel):
    valid: bool = Field(..., description="Whether swap is valid")
    errors: list[str] = Field(default_factory=list, description="List of validation errors")
    warnings: list[str] = Field(
        default_factory=list, description="List of validation warnings"
    )
    back_to_back_conflict: bool = Field(
        False, description="Whether swap creates back-to-back shifts"
    )
    external_conflict: str | None = Field(
        None, min_length=1, max_length=500, description="External conflict description"
    )


class SwapRecordResponse(BaseModel):
    id: UUID
    source_faculty_id: UUID
    source_faculty_name: str
    source_week: date
    target_faculty_id: UUID
    target_faculty_name: str
    target_week: date | None
    swap_type: SwapTypeSchema
    status: SwapStatusSchema
    reason: str | None
    requested_at: datetime
    executed_at: datetime | None

    class Config:
        from_attributes = True


class SwapExecuteResponse(BaseModel):
    success: bool
    swap_id: UUID | None = None
    message: str
    validation: SwapValidationResult


class SwapHistoryResponse(BaseModel):
    items: list[SwapRecordResponse]
    total: int
    page: int
    page_size: int
    pages: int
