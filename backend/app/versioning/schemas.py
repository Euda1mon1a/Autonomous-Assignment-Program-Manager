"""
Pydantic schemas for data versioning operations.

These schemas define request and response formats for version control operations.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Version Metadata Schemas
# =============================================================================

class VersionMetadataSchema(BaseModel):
    """Schema for version metadata."""
    version_id: int = Field(..., description="Unique version identifier")
    transaction_id: int = Field(..., description="Database transaction ID")
    timestamp: datetime = Field(..., description="When the version was created")
    user_id: str | None = Field(None, description="User who created this version")
    operation: str = Field(..., description="Operation type: create, update, delete")
    tags: list[str] = Field(default_factory=list, description="Tags applied to this version")
    label: str | None = Field(None, description="Human-readable label")
    comment: str | None = Field(None, description="Version comment")
    branch_name: str = Field(default="main", description="Branch this version belongs to")
    parent_version_id: int | None = Field(None, description="Parent version ID")
    is_merge: bool = Field(default=False, description="Whether this is a merge commit")
    merge_source_branch: str | None = Field(None, description="Source branch for merge")
    checksum: str = Field(..., description="SHA-256 checksum of version data")

    class Config:
        from_attributes = True


class VersionHistoryResponse(BaseModel):
    """Response schema for version history queries."""
    entity_type: str
    entity_id: str
    total_versions: int
    versions: list[VersionMetadataSchema]


# =============================================================================
# Version Diff Schemas
# =============================================================================

class FieldChangeSchema(BaseModel):
    """Schema for a single field change."""
    field: str = Field(..., description="Field name")
    type: Literal["added", "removed", "modified"] = Field(..., description="Change type")
    old_value: Any = Field(None, description="Old value")
    new_value: Any = Field(None, description="New value")


class VersionDiffSchema(BaseModel):
    """Schema for version diff results."""
    entity_type: str
    entity_id: str
    from_version: int
    to_version: int
    from_timestamp: datetime
    to_timestamp: datetime
    changes: list[FieldChangeSchema]
    added_fields: list[str]
    removed_fields: list[str]
    modified_fields: list[str]
    change_summary: str


class CompareVersionsRequest(BaseModel):
    """Request schema for comparing versions."""
    entity_type: str = Field(..., description="Type of entity to compare")
    entity_id: UUID | str = Field(..., description="Entity ID")
    from_version: int = Field(..., description="Starting version")
    to_version: int = Field(..., description="Ending version")


# =============================================================================
# Point-in-Time Query Schemas
# =============================================================================

class PointInTimeQuerySchema(BaseModel):
    """Schema for point-in-time query results."""
    entity_type: str
    entity_id: str
    timestamp: datetime
    version_id: int
    data: dict[str, Any]
    existed_at_time: bool


class PointInTimeRequest(BaseModel):
    """Request schema for point-in-time queries."""
    entity_type: str = Field(..., description="Type of entity to query")
    entity_id: UUID | str = Field(..., description="Entity ID")
    timestamp: datetime = Field(..., description="Timestamp to query at")


class PointInTimeBatchRequest(BaseModel):
    """Request schema for batch point-in-time queries."""
    entity_type: str = Field(..., description="Type of entity to query")
    timestamp: datetime = Field(..., description="Timestamp to query at")
    filters: dict[str, Any] = Field(default_factory=dict, description="Optional filters")


# =============================================================================
# Rollback Schemas
# =============================================================================

class RollbackRequest(BaseModel):
    """Request schema for version rollback."""
    entity_type: str = Field(..., description="Type of entity to rollback")
    entity_id: UUID | str = Field(..., description="Entity ID")
    target_version: int = Field(..., description="Version to rollback to")
    reason: str | None = Field(None, description="Reason for rollback")


class RollbackResponse(BaseModel):
    """Response schema for rollback operations."""
    success: bool
    entity_type: str
    entity_id: str
    target_version: int
    rolled_back_by: str
    rolled_back_at: datetime
    reason: str | None


# =============================================================================
# Branch Schemas
# =============================================================================

class VersionBranchSchema(BaseModel):
    """Schema for version branch information."""
    branch_name: str
    created_at: datetime
    created_by: str
    parent_branch: str | None
    base_version_id: int
    head_version_id: int
    description: str | None
    is_active: bool
    tags: list[str]


class CreateBranchRequest(BaseModel):
    """Request schema for creating a branch."""
    parent_branch: str = Field(default="main", description="Parent branch name")
    new_branch_name: str = Field(..., description="New branch name")
    description: str | None = Field(None, description="Branch description")


class BranchInfoSchema(BaseModel):
    """Schema for detailed branch information."""
    branch: VersionBranchSchema
    version_count: int
    entity_count: int
    latest_activity: datetime
    contributors: list[str]
    merge_status: Literal["clean", "conflicts", "merged"]


# =============================================================================
# Merge Conflict Schemas
# =============================================================================

class MergeConflictSchema(BaseModel):
    """Schema for merge conflicts."""
    entity_type: str
    entity_id: str
    field_name: str
    source_value: Any
    target_value: Any
    base_value: Any | None
    conflict_type: Literal["modify-modify", "modify-delete", "delete-modify"]
    resolution_strategy: str | None


class DetectConflictsRequest(BaseModel):
    """Request schema for conflict detection."""
    source_branch: str = Field(..., description="Source branch")
    target_branch: str = Field(..., description="Target branch")
    entity_types: list[str] | None = Field(None, description="Entity types to check")


class DetectConflictsResponse(BaseModel):
    """Response schema for conflict detection."""
    source_branch: str
    target_branch: str
    conflicts: list[MergeConflictSchema]
    conflict_count: int
    can_auto_merge: bool


class ResolveConflictRequest(BaseModel):
    """Request schema for conflict resolution."""
    conflict: MergeConflictSchema
    resolution: str = Field(
        ...,
        description="Resolution strategy: 'source', 'target', 'base', or custom value"
    )


# =============================================================================
# Tagging and Annotation Schemas
# =============================================================================

class TagVersionRequest(BaseModel):
    """Request schema for tagging a version."""
    entity_type: str = Field(..., description="Type of entity")
    entity_id: UUID | str = Field(..., description="Entity ID")
    version_id: int = Field(..., description="Version to tag")
    tag: str = Field(..., description="Tag to add")


class AddCommentRequest(BaseModel):
    """Request schema for adding version comments."""
    entity_type: str = Field(..., description="Type of entity")
    entity_id: UUID | str = Field(..., description="Entity ID")
    version_id: int = Field(..., description="Version to comment on")
    comment: str = Field(..., description="Comment text")


# =============================================================================
# Lineage and Comparison Schemas
# =============================================================================

class EntityLineageSchema(BaseModel):
    """Schema for entity lineage information."""
    entity_type: str
    entity_id: str
    total_versions: int
    created_at: datetime | None
    last_modified: datetime | None
    versions: list[VersionMetadataSchema]
    branches: list[str]


class BranchComparisonSchema(BaseModel):
    """Schema for branch comparison results."""
    branch1: str
    branch2: str
    entity_types: list[str]
    differences: list[dict[str, Any]]
    unique_to_branch1: list[dict[str, Any]]
    unique_to_branch2: list[dict[str, Any]]
    modified_in_both: list[dict[str, Any]]
    identical: list[dict[str, Any]]


class CompareBranchesRequest(BaseModel):
    """Request schema for comparing branches."""
    branch1: str = Field(..., description="First branch")
    branch2: str = Field(..., description="Second branch")
    entity_types: list[str] | None = Field(None, description="Entity types to compare")
