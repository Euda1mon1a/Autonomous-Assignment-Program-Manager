"""Block assignment schemas for leave-eligible rotation scheduling."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssignmentReasonEnum(str, Enum):
    """Reason for block assignment."""

    LEAVE_ELIGIBLE_MATCH = "leave_eligible_match"
    COVERAGE_PRIORITY = "coverage_priority"
    BALANCED = "balanced"
    MANUAL = "manual"
    SPECIALTY_MATCH = "specialty_match"


class BlockAssignmentBase(BaseModel):
    """Base schema for block assignments."""

    block_number: int = Field(..., ge=0, le=13, description="Academic block (0-13)")
    academic_year: int = Field(..., ge=2020, le=2100, description="Academic year")
    resident_id: UUID
    rotation_template_id: UUID | None = None
    has_leave: bool = False
    leave_days: int = Field(default=0, ge=0, description="Number of leave days")
    assignment_reason: str = "balanced"
    notes: str | None = None

    @field_validator("assignment_reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        valid_reasons = [r.value for r in AssignmentReasonEnum]
        if v not in valid_reasons:
            raise ValueError(f"assignment_reason must be one of {valid_reasons}")
        return v

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: str | None) -> str | None:
        """Validate notes are not too long."""
        if v is not None and len(v) > 1000:
            raise ValueError("notes must be less than 1000 characters")
        return v


class BlockAssignmentCreate(BlockAssignmentBase):
    """Schema for creating a block assignment."""

    created_by: str | None = None


class BlockAssignmentUpdate(BaseModel):
    """Schema for updating a block assignment."""

    rotation_template_id: UUID | None = None
    has_leave: bool | None = None
    leave_days: int | None = Field(default=None, ge=0)
    assignment_reason: str | None = None
    notes: str | None = None

    @field_validator("assignment_reason")
    @classmethod
    def validate_reason(cls, v: str | None) -> str | None:
        if v is not None:
            valid_reasons = [r.value for r in AssignmentReasonEnum]
            if v not in valid_reasons:
                raise ValueError(f"assignment_reason must be one of {valid_reasons}")
        return v

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: str | None) -> str | None:
        """Validate notes are not too long."""
        if v is not None and len(v) > 1000:
            raise ValueError("notes must be less than 1000 characters")
        return v


class RotationTemplateInfo(BaseModel):
    """Minimal rotation template info for responses."""

    id: UUID
    name: str
    rotation_type: str
    leave_eligible: bool

    model_config = ConfigDict(from_attributes=True)


class ResidentInfo(BaseModel):
    """Minimal resident info for responses."""

    id: UUID
    name: str
    pgy_level: int | None

    model_config = ConfigDict(from_attributes=True)


class BlockAssignmentResponse(BaseModel):
    """Response schema for block assignment."""

    id: UUID
    block_number: int
    academic_year: int
    resident_id: UUID
    rotation_template_id: UUID | None
    has_leave: bool
    leave_days: int
    assignment_reason: str
    notes: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    # Nested relations (optional, populated when requested)
    resident: ResidentInfo | None = None
    rotation_template: RotationTemplateInfo | None = None

    model_config = ConfigDict(from_attributes=True)


class BlockAssignmentListResponse(BaseModel):
    """Paginated list response for block assignments."""

    items: list[BlockAssignmentResponse]
    total: int
    block_number: int | None = None
    academic_year: int | None = None


# ============================================================================
# Block Scheduler Request/Response Schemas
# ============================================================================


class ResidentLeaveInfo(BaseModel):
    """Resident leave information for a block."""

    resident_id: UUID
    resident_name: str
    pgy_level: int | None
    leave_days: int
    leave_types: list[str]  # e.g., ["vacation", "conference"]


class RotationCapacity(BaseModel):
    """Rotation capacity information."""

    rotation_template_id: UUID
    rotation_name: str
    leave_eligible: bool
    max_residents: int | None
    current_assigned: int
    available_slots: int | None


class BlockScheduleRequest(BaseModel):
    """Request to schedule a block."""

    block_number: int = Field(..., ge=0, le=13)
    academic_year: int = Field(..., ge=2020, le=2100)
    dry_run: bool = Field(
        default=True,
        description="If True, preview assignments without saving",
    )
    include_all_residents: bool = Field(
        default=True,
        description="If True, schedule all residents. If False, only those with leave.",
    )


class AssignmentPreview(BaseModel):
    """Preview of a single assignment."""

    resident_id: UUID
    resident_name: str
    pgy_level: int | None
    rotation_template_id: UUID | None
    rotation_name: str | None
    has_leave: bool
    leave_days: int
    assignment_reason: str
    is_leave_eligible_rotation: bool


class CoverageGap(BaseModel):
    """Identified coverage gap."""

    rotation_template_id: UUID
    rotation_name: str
    required_coverage: int
    assigned_coverage: int
    gap: int
    severity: str  # "critical", "warning", "info"


class LeaveConflict(BaseModel):
    """Leave conflict warning."""

    resident_id: UUID
    resident_name: str
    rotation_name: str
    leave_days: int
    conflict_reason: str  # "non_leave_eligible_rotation", "insufficient_coverage"


class BlockScheduleResponse(BaseModel):
    """Response from block scheduling operation."""

    block_number: int
    academic_year: int
    dry_run: bool
    success: bool
    message: str

    # Preview/Results
    assignments: list[AssignmentPreview]
    total_residents: int
    residents_with_leave: int

    # Warnings and gaps
    coverage_gaps: list[CoverageGap]
    leave_conflicts: list[LeaveConflict]

    # Capacity summary
    rotation_capacities: list[RotationCapacity]


class BlockSchedulerDashboard(BaseModel):
    """Dashboard view for block scheduler."""

    block_number: int
    academic_year: int
    block_start_date: str | None  # ISO date
    block_end_date: str | None  # ISO date

    # Residents summary
    total_residents: int
    residents_with_leave: list[ResidentLeaveInfo]

    # Rotation summary
    rotation_capacities: list[RotationCapacity]
    leave_eligible_rotations: int
    non_leave_eligible_rotations: int

    # Current assignments (if any)
    current_assignments: list[BlockAssignmentResponse]
    unassigned_residents: int
