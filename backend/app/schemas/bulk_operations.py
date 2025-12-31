"""
Bulk operation schemas for batch processing.

Provides schemas for:
- Bulk create
- Bulk update
- Bulk delete
- Batch operations
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BulkCreateRequest(BaseModel):
    """Request for bulk create operation."""

    items: list[dict] = Field(
        ..., description="List of items to create", min_length=1, max_length=1000
    )

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[dict]) -> list[dict]:
        """Validate items list is not too long."""
        if len(v) > 1000:
            raise ValueError("Cannot create more than 1000 items in one request")
        return v


class BulkUpdateRequest(BaseModel):
    """Request for bulk update operation."""

    updates: list[dict] = Field(
        ...,
        description="List of updates (each with id and fields to update)",
        min_length=1,
        max_length=1000,
    )

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, v: list[dict]) -> list[dict]:
        """Validate updates list is not too long."""
        if len(v) > 1000:
            raise ValueError("Cannot update more than 1000 items in one request")
        # Validate each update has an id
        for idx, update in enumerate(v):
            if "id" not in update:
                raise ValueError(f"Update at index {idx} is missing 'id' field")
        return v


class BulkDeleteRequest(BaseModel):
    """Request for bulk delete operation."""

    ids: list[UUID] = Field(
        ..., description="List of IDs to delete", min_length=1, max_length=1000
    )

    soft_delete: bool = Field(False, description="Use soft delete (if supported)")

    @field_validator("ids")
    @classmethod
    def validate_ids(cls, v: list[UUID]) -> list[UUID]:
        """Validate IDs list is not too long."""
        if len(v) > 1000:
            raise ValueError("Cannot delete more than 1000 items in one request")
        return v


class ItemResult(BaseModel):
    """Result for individual item in bulk operation."""

    index: int = Field(..., description="Index in original request")
    success: bool = Field(..., description="Whether operation succeeded")
    id: UUID | None = Field(None, description="Resource ID (for successful creates)")
    error: str | None = Field(None, description="Error message (for failures)")
    error_code: str | None = Field(None, description="Error code (for failures)")


class BulkOperationResponse(BaseModel):
    """Response for bulk operation."""

    total: int = Field(..., description="Total items in request")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    results: list[ItemResult] = Field(..., description="Per-item results")
    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="Operation start time"
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Operation completion time"
    )


class BatchAssignmentCreate(BaseModel):
    """Batch create assignments."""

    person_id: UUID = Field(..., description="Person being assigned")
    block_ids: list[UUID] = Field(
        ..., description="List of block IDs to assign", min_length=1, max_length=100
    )
    rotation_template_id: UUID | None = Field(None, description="Rotation template")
    role: str = Field("primary", description="Assignment role")
    notes: str | None = Field(None, description="Assignment notes")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is valid."""
        if v not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")
        return v


class BatchAssignmentDelete(BaseModel):
    """Batch delete assignments."""

    person_id: UUID = Field(..., description="Person whose assignments to delete")
    start_date: str = Field(..., description="Start date for deletion range")
    end_date: str = Field(..., description="End date for deletion range")
    rotation_template_id: UUID | None = Field(
        None, description="Optional: only delete assignments for this rotation"
    )


class BulkSwapApproval(BaseModel):
    """Bulk approve swap requests."""

    swap_ids: list[UUID] = Field(
        ..., description="List of swap IDs to approve", min_length=1, max_length=100
    )
    approved_by: str = Field(..., description="User approving the swaps")
    notes: str | None = Field(None, description="Approval notes")

    @field_validator("swap_ids")
    @classmethod
    def validate_swap_ids(cls, v: list[UUID]) -> list[UUID]:
        """Validate swap_ids list is not too long."""
        if len(v) > 100:
            raise ValueError("Cannot approve more than 100 swaps in one request")
        return v


class BulkCredentialUpdate(BaseModel):
    """Bulk update credentials."""

    updates: list[dict] = Field(
        ..., description="List of credential updates", min_length=1, max_length=500
    )

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, v: list[dict]) -> list[dict]:
        """Validate updates structure."""
        if len(v) > 500:
            raise ValueError("Cannot update more than 500 credentials in one request")

        for idx, update in enumerate(v):
            required_fields = ["person_id", "credential_name", "expires_at"]
            missing = [f for f in required_fields if f not in update]
            if missing:
                raise ValueError(
                    f"Update at index {idx} is missing required fields: {missing}"
                )
        return v


class AsyncBulkOperationRequest(BaseModel):
    """Request for asynchronous bulk operation."""

    operation_type: str = Field(..., description="Type of bulk operation")
    items: list[dict] = Field(
        ..., description="List of items to process", min_length=1, max_length=10000
    )
    callback_url: str | None = Field(
        None, description="URL to call when operation completes"
    )

    @field_validator("operation_type")
    @classmethod
    def validate_operation_type(cls, v: str) -> str:
        """Validate operation_type is valid."""
        valid_types = ["create", "update", "delete", "import"]
        if v not in valid_types:
            raise ValueError(f"operation_type must be one of {valid_types}")
        return v


class AsyncBulkOperationStatus(BaseModel):
    """Status of asynchronous bulk operation."""

    operation_id: UUID = Field(..., description="Operation ID")
    status: str = Field(
        ..., description="Operation status (pending, running, completed, failed)"
    )
    total: int = Field(..., description="Total items to process")
    processed: int = Field(..., description="Items processed so far")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    started_at: datetime = Field(..., description="Operation start time")
    completed_at: datetime | None = Field(None, description="Operation completion time")
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is valid."""
        valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v
