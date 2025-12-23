"""Batch operation schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BatchOperationType(str, Enum):
    """Batch operation types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class BatchOperationStatus(str, Enum):
    """Batch operation status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some operations succeeded, some failed


class BatchAssignmentCreate(BaseModel):
    """Schema for batch assignment creation item."""

    block_id: UUID
    person_id: UUID
    rotation_template_id: UUID | None = None
    role: str  # 'primary', 'supervising', 'backup'
    activity_override: str | None = None
    notes: str | None = None
    override_reason: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")
        return v


class BatchAssignmentUpdate(BaseModel):
    """Schema for batch assignment update item."""

    assignment_id: UUID
    rotation_template_id: UUID | None = None
    role: str | None = None
    activity_override: str | None = None
    notes: str | None = None
    override_reason: str | None = None
    updated_at: datetime  # Required for optimistic locking

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")
        return v


class BatchAssignmentDelete(BaseModel):
    """Schema for batch assignment deletion item."""

    assignment_id: UUID
    soft_delete: bool = Field(
        default=False,
        description="If True, mark as deleted but don't remove from database",
    )


class BatchCreateRequest(BaseModel):
    """Request schema for batch create operations."""

    assignments: list[BatchAssignmentCreate] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of assignments to create (max 1000)",
    )
    dry_run: bool = Field(
        default=False, description="If True, validate only without creating"
    )
    rollback_on_error: bool = Field(
        default=True, description="If True, rollback all changes if any operation fails"
    )
    created_by: str | None = None
    validate_acgme: bool = Field(
        default=True,
        description="If True, validate ACGME compliance for all assignments",
    )


class BatchUpdateRequest(BaseModel):
    """Request schema for batch update operations."""

    assignments: list[BatchAssignmentUpdate] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of assignments to update (max 1000)",
    )
    dry_run: bool = Field(
        default=False, description="If True, validate only without updating"
    )
    rollback_on_error: bool = Field(
        default=True, description="If True, rollback all changes if any operation fails"
    )
    validate_acgme: bool = Field(
        default=True,
        description="If True, validate ACGME compliance for all assignments",
    )


class BatchDeleteRequest(BaseModel):
    """Request schema for batch delete operations."""

    assignments: list[BatchAssignmentDelete] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of assignments to delete (max 1000)",
    )
    dry_run: bool = Field(
        default=False, description="If True, validate only without deleting"
    )
    rollback_on_error: bool = Field(
        default=True, description="If True, rollback all changes if any operation fails"
    )


class BatchOperationResult(BaseModel):
    """Result for a single operation in a batch."""

    index: int = Field(..., description="Index of the operation in the batch")
    success: bool
    assignment_id: UUID | None = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)


class BatchResponse(BaseModel):
    """Response schema for batch operations."""

    operation_id: UUID = Field(..., description="Unique ID for this batch operation")
    operation_type: BatchOperationType
    status: BatchOperationStatus
    total: int = Field(..., description="Total number of operations requested")
    succeeded: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: list[BatchOperationResult] = Field(
        default_factory=list, description="Detailed results for each operation"
    )
    errors: list[str] = Field(default_factory=list, description="Global errors")
    warnings: list[str] = Field(default_factory=list, description="Global warnings")
    dry_run: bool = Field(default=False, description="Whether this was a dry run")
    created_at: datetime
    completed_at: datetime | None = None
    processing_time_ms: float | None = Field(
        None, description="Time taken to process the batch in milliseconds"
    )


class BatchStatusResponse(BaseModel):
    """Response schema for batch status query."""

    operation_id: UUID
    operation_type: BatchOperationType
    status: BatchOperationStatus
    total: int
    succeeded: int
    failed: int
    progress_percentage: float = Field(
        ..., description="Percentage of operations completed (0-100)"
    )
    created_at: datetime
    completed_at: datetime | None = None
    estimated_completion: datetime | None = Field(
        None, description="Estimated completion time (only for in-progress operations)"
    )


class BatchValidationResult(BaseModel):
    """Validation result for batch operations."""

    valid: bool
    total_operations: int
    validation_errors: list[str] = Field(default_factory=list)
    operation_errors: list[BatchOperationResult] = Field(
        default_factory=list, description="Per-operation validation errors"
    )
    acgme_warnings: list[str] = Field(
        default_factory=list, description="ACGME compliance warnings"
    )
