"""Pydantic schemas for FMIT swap API."""
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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
    source_faculty_id: UUID
    source_week: date
    target_faculty_id: UUID
    target_week: date | None = None
    swap_type: SwapTypeSchema
    reason: str | None = Field(None, max_length=500)

    @field_validator('target_week')
    @classmethod
    def validate_swap_type_consistency(cls, v, info):
        if info.data.get('swap_type') == SwapTypeSchema.ONE_TO_ONE and v is None:
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


class SwapValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    back_to_back_conflict: bool = False
    external_conflict: str | None = None


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
