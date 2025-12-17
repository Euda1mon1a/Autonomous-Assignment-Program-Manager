"""Audit log schemas.

Pydantic models for audit logging functionality, including log entries,
filters, statistics, and export configurations.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


# ============================================================================
# Core Audit Schemas
# ============================================================================


class AuditUser(BaseModel):
    """User who performed an action."""
    id: str
    name: str
    email: Optional[str] = None
    role: Optional[str] = None


class FieldChange(BaseModel):
    """Single field change tracking."""
    field: str
    old_value: Any = Field(alias="oldValue")
    new_value: Any = Field(alias="newValue")
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


class AuditLogEntry(BaseModel):
    """Core audit log entry."""
    id: str
    timestamp: str
    entity_type: str = Field(alias="entityType")
    entity_id: str = Field(alias="entityId")
    entity_name: Optional[str] = Field(None, alias="entityName")
    action: str
    severity: str
    user: AuditUser
    changes: Optional[List[FieldChange]] = None
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, alias="ipAddress")
    user_agent: Optional[str] = Field(None, alias="userAgent")
    session_id: Optional[str] = Field(None, alias="sessionId")
    reason: Optional[str] = None
    acgme_override: Optional[bool] = Field(None, alias="acgmeOverride")
    acgme_justification: Optional[str] = Field(None, alias="acgmeJustification")

    class Config:
        populate_by_name = True


class AuditLogResponse(BaseModel):
    """Paginated audit log response."""
    items: List[AuditLogEntry]
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
    date_range: Optional[DateRange] = Field(None, alias="dateRange")
    entity_types: Optional[List[str]] = Field(None, alias="entityTypes")
    actions: Optional[List[str]] = None
    user_ids: Optional[List[str]] = Field(None, alias="userIds")
    severity: Optional[List[str]] = None
    search_query: Optional[str] = Field(None, alias="searchQuery")
    entity_id: Optional[str] = Field(None, alias="entityId")
    acgme_overrides_only: Optional[bool] = Field(None, alias="acgmeOverridesOnly")

    class Config:
        populate_by_name = True


# ============================================================================
# Statistics Schemas
# ============================================================================


class AuditStatistics(BaseModel):
    """Audit statistics for dashboard."""
    total_entries: int = Field(alias="totalEntries")
    entries_by_action: Dict[str, int] = Field(alias="entriesByAction")
    entries_by_entity_type: Dict[str, int] = Field(alias="entriesByEntityType")
    entries_by_severity: Dict[str, int] = Field(alias="entriesBySeverity")
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
    filters: Optional[AuditLogFilters] = None
    include_metadata: Optional[bool] = Field(None, alias="includeMetadata")
    include_changes: Optional[bool] = Field(None, alias="includeChanges")
    date_format: Optional[str] = Field(None, alias="dateFormat")

    class Config:
        populate_by_name = True


# ============================================================================
# Mutation Schemas
# ============================================================================


class MarkReviewedRequest(BaseModel):
    """Request to mark audit entries as reviewed."""
    ids: List[str]
    reviewed_by: str = Field(alias="reviewedBy")
    notes: Optional[str] = None

    class Config:
        populate_by_name = True
