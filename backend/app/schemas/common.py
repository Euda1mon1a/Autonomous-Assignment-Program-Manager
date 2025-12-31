"""
Common base schemas for API requests and responses.

Provides reusable schema components:
- Base response models
- Error response models
- Success response models
- Metadata schemas
"""

from datetime import datetime
from typing import Any, Generic, TypeVar, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Generic type for response data
T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail schema."""

    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: str | None = Field(None, description="Error code")
    details: list[ErrorDetail] | None = Field(
        None, description="Detailed error information"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response schema."""

    success: bool = Field(True, description="Always true for success")
    data: T = Field(..., description="Response data")
    message: str | None = Field(None, description="Optional success message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class MetadataSchema(BaseModel):
    """Metadata for responses."""

    total: int = Field(..., description="Total count of items")
    page: int | None = Field(None, description="Current page number")
    page_size: int | None = Field(None, description="Items per page")
    total_pages: int | None = Field(None, description="Total number of pages")
    has_next: bool | None = Field(None, description="Has next page")
    has_previous: bool | None = Field(None, description="Has previous page")


class ListResponse(BaseModel, Generic[T]):
    """Standard paginated list response schema."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total count of items")
    page: int | None = Field(None, description="Current page number")
    page_size: int | None = Field(None, description="Items per page")
    total_pages: int | None = Field(None, description="Total number of pages")

    class Config:
        from_attributes = True


class IdResponse(BaseModel):
    """Simple ID response for create operations."""

    id: UUID = Field(..., description="Created resource ID")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )


class StatusResponse(BaseModel):
    """Simple status response."""

    status: str = Field(..., description="Operation status")
    message: str | None = Field(None, description="Status message")


class CountResponse(BaseModel):
    """Simple count response."""

    count: int = Field(..., description="Count of items")


class BulkOperationResult(BaseModel):
    """Result of bulk operation."""

    total: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    errors: list[dict] | None = Field(None, description="Errors for failed items")


class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at timestamps."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AuditMixin(TimestampMixin):
    """Mixin for audit fields."""

    created_by: str | None = Field(None, description="User who created the record")
    updated_by: str | None = Field(None, description="User who last updated the record")


class SoftDeleteMixin(BaseModel):
    """Mixin for soft delete support."""

    deleted_at: datetime | None = Field(None, description="Deletion timestamp")
    deleted_by: str | None = Field(None, description="User who deleted the record")
    is_deleted: bool = Field(False, description="Soft delete flag")


class VersionedMixin(BaseModel):
    """Mixin for optimistic locking."""

    version: int = Field(1, description="Version number for optimistic locking")


class BaseSchema(TimestampMixin):
    """Base schema with timestamps."""

    id: UUID = Field(..., description="Resource ID")

    class Config:
        from_attributes = True


class BaseAuditedSchema(AuditMixin):
    """Base schema with audit fields."""

    id: UUID = Field(..., description="Resource ID")

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Health status")
    version: str | None = Field(None, description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )
    dependencies: dict[str, str] | None = Field(
        None, description="Status of dependencies (database, redis, etc.)"
    )
