"""
Pagination schemas for API requests and responses.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field, field_validator


# Generic type for paginated data
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for requests."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        """Validate page_size is within acceptable range."""
        if v > 1000:
            raise ValueError("page_size cannot exceed 1000")
        return v


class OffsetPaginationParams(BaseModel):
    """Offset-based pagination parameters."""

    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(50, ge=1, le=1000, description="Maximum items to return")

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Validate limit is within acceptable range."""
        if v > 1000:
            raise ValueError("limit cannot exceed 1000")
        return v


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters."""

    cursor: str | None = Field(None, description="Cursor for next page")
    limit: int = Field(50, ge=1, le=1000, description="Maximum items to return")

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Validate limit is within acceptable range."""
        if v > 1000:
            raise ValueError("limit cannot exceed 1000")
        return v


class PageInfo(BaseModel):
    """Page information for pagination."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total items across all pages")
    total_pages: int = Field(..., description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with page info."""

    items: list[T] = Field(..., description="Page items")
    page_info: PageInfo = Field(..., description="Pagination information")


class CursorPageInfo(BaseModel):
    """Cursor-based page information."""

    next_cursor: str | None = Field(None, description="Cursor for next page")
    previous_cursor: str | None = Field(None, description="Cursor for previous page")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")
    count: int = Field(..., description="Items in current page")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-paginated response."""

    items: list[T] = Field(..., description="Page items")
    cursor_info: CursorPageInfo = Field(..., description="Cursor pagination information")
