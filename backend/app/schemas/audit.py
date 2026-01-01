"""Audit log schemas.

Pydantic models for audit logging functionality, including log entries,
filters, statistics, and export configurations.
"""

from typing import Any

from pydantic import BaseModel, EmailStr, Field

# ============================================================================
# Core Audit Schemas
# ============================================================================


class AuditUser(BaseModel):
    """User who performed an action."""

    id: str = Field(..., max_length=100, description="User ID")
    name: str = Field(..., min_length=1, max_length=200, description="User name")
    email: EmailStr | None = Field(None, description="User email address")
    role: str | None = Field(None, max_length=50, description="User role")


class FieldChange(BaseModel):
    """Single field change tracking."""

    field: str = Field(..., min_length=1, max_length=100, description="Field name")
    old_value: Any = Field(alias="oldValue", description="Previous value")
    new_value: Any = Field(alias="newValue", description="New value")
    display_name: str | None = Field(
        None, max_length=200, alias="displayName", description="Human-readable field name"
    )

    class Config:
        populate_by_name = True


class AuditLogEntry(BaseModel):
    """Core audit log entry."""

    id: str = Field(..., max_length=100, description="Audit log entry ID")
    timestamp: str = Field(..., description="Timestamp of the event")
    entity_type: str = Field(
        ..., max_length=100, alias="entityType", description="Type of entity affected"
    )
    entity_id: str = Field(
        ..., max_length=100, alias="entityId", description="ID of entity affected"
    )
    entity_name: str | None = Field(
        None, max_length=200, alias="entityName", description="Name of entity"
    )
    action: str = Field(..., max_length=100, description="Action performed")
    severity: str = Field(..., max_length=20, description="Severity level")
    user: AuditUser = Field(..., description="User who performed the action")
    changes: list[FieldChange] | None = Field(None, description="List of field changes")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")
    ip_address: str | None = Field(
        None, max_length=50, alias="ipAddress", description="IP address of user"
    )
    user_agent: str | None = Field(
        None, max_length=500, alias="userAgent", description="Browser user agent"
    )
    session_id: str | None = Field(
        None, max_length=100, alias="sessionId", description="Session ID"
    )
    reason: str | None = Field(None, max_length=500, description="Reason for action")
    acgme_override: bool | None = Field(
        None, alias="acgmeOverride", description="Whether this is an ACGME override"
    )
    acgme_justification: str | None = Field(
        None,
        max_length=1000,
        alias="acgmeJustification",
        description="Justification for ACGME override",
    )

    class Config:
        populate_by_name = True


class AuditLogResponse(BaseModel):
    """Paginated audit log response."""

    items: list[AuditLogEntry]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")

    class Config:
        populate_by_name = True


# ============================================================================
# Filter Schemas
# ============================================================================


class DateRange(BaseModel):
    """Date range for filtering."""

    start: str
    end: str


class AuditLogFilters(BaseModel):
    """Audit log filters for querying."""

    date_range: DateRange | None = Field(None, alias="dateRange", description="Date range filter")
    entity_types: list[str] | None = Field(
        None, max_length=20, alias="entityTypes", description="Entity types to filter (max 20)"
    )
    actions: list[str] | None = Field(
        None, max_length=20, description="Actions to filter (max 20)"
    )
    user_ids: list[str] | None = Field(
        None, max_length=50, alias="userIds", description="User IDs to filter (max 50)"
    )
    severity: list[str] | None = Field(
        None, max_length=10, description="Severity levels to filter (max 10)"
    )
    search_query: str | None = Field(
        None, max_length=200, alias="searchQuery", description="Search query string"
    )
    entity_id: str | None = Field(
        None, max_length=100, alias="entityId", description="Specific entity ID"
    )
    acgme_overrides_only: bool | None = Field(
        None, alias="acgmeOverridesOnly", description="Show only ACGME overrides"
    )

    class Config:
        populate_by_name = True


# ============================================================================
# Statistics Schemas
# ============================================================================


class AuditStatistics(BaseModel):
    """Audit statistics for dashboard."""

    total_entries: int = Field(alias="totalEntries")
    entries_by_action: dict[str, int] = Field(alias="entriesByAction")
    entries_by_entity_type: dict[str, int] = Field(alias="entriesByEntityType")
    entries_by_severity: dict[str, int] = Field(alias="entriesBySeverity")
    acgme_override_count: int = Field(alias="acgmeOverrideCount")
    unique_users: int = Field(alias="uniqueUsers")
    date_range: DateRange = Field(alias="dateRange")

    class Config:
        populate_by_name = True


# ============================================================================
# Export Schemas
# ============================================================================


class AuditExportConfig(BaseModel):
    """Export configuration."""

    format: str  # 'csv', 'json', 'pdf'
    filters: AuditLogFilters | None = None
    include_metadata: bool | None = Field(None, alias="includeMetadata")
    include_changes: bool | None = Field(None, alias="includeChanges")
    date_format: str | None = Field(None, alias="dateFormat")

    class Config:
        populate_by_name = True


# ============================================================================
# Mutation Schemas
# ============================================================================


class MarkReviewedRequest(BaseModel):
    """Request to mark audit entries as reviewed."""

    ids: list[str] = Field(
        ..., min_length=1, max_length=100, description="List of entry IDs to mark (max 100)"
    )
    reviewed_by: str = Field(
        ..., max_length=100, alias="reviewedBy", description="ID of reviewer"
    )
    notes: str | None = Field(None, max_length=1000, description="Review notes")

    class Config:
        populate_by_name = True
