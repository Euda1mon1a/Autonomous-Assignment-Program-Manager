"""Audit log schemas.

Pydantic models for audit logging functionality, including log entries,
filters, statistics, and export configurations.
"""

from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Core Audit Schemas
# ============================================================================


class AuditUser(BaseModel):
    """User who performed an action."""

    id: str
    name: str
    email: str | None = None
    role: str | None = None


class FieldChange(BaseModel):
    """Single field change tracking."""

    field: str
    old_value: Any = Field(alias="oldValue")
    new_value: Any = Field(alias="newValue")
    display_name: str | None = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


class AuditLogEntry(BaseModel):
    """Core audit log entry."""

    id: str
    timestamp: str
    entity_type: str = Field(alias="entityType")
    entity_id: str = Field(alias="entityId")
    entity_name: str | None = Field(None, alias="entityName")
    action: str
    severity: str
    user: AuditUser
    changes: list[FieldChange] | None = None
    metadata: dict[str, Any] | None = None
    ip_address: str | None = Field(None, alias="ipAddress")
    user_agent: str | None = Field(None, alias="userAgent")
    session_id: str | None = Field(None, alias="sessionId")
    reason: str | None = None
    acgme_override: bool | None = Field(None, alias="acgmeOverride")
    acgme_justification: str | None = Field(None, alias="acgmeJustification")

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

    date_range: DateRange | None = Field(None, alias="dateRange")
    entity_types: list[str] | None = Field(None, alias="entityTypes")
    actions: list[str] | None = None
    user_ids: list[str] | None = Field(None, alias="userIds")
    severity: list[str] | None = None
    search_query: str | None = Field(None, alias="searchQuery")
    entity_id: str | None = Field(None, alias="entityId")
    acgme_overrides_only: bool | None = Field(None, alias="acgmeOverridesOnly")

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

    ids: list[str]
    reviewed_by: str = Field(alias="reviewedBy")
    notes: str | None = None

    class Config:
        populate_by_name = True
