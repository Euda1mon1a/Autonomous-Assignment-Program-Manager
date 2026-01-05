"""Import staging schemas for Excel import workflow.

Provides Pydantic schemas for:
- ImportBatch create/response (batch operations)
- StagedAssignment response/update (individual staged rows)
- Import preview and apply operations
"""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ImportBatchStatus(str, Enum):
    """Status of an import batch."""

    STAGED = "staged"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class ConflictResolutionMode(str, Enum):
    """How to handle conflicts during import apply."""

    REPLACE = "replace"  # Delete existing block assignments, insert staged
    MERGE = "merge"  # Keep existing, add new, skip conflicts
    UPSERT = "upsert"  # Update if person+date+slot exists, else insert


class StagedAssignmentStatus(str, Enum):
    """Status of a staged assignment."""

    PENDING = "pending"
    APPROVED = "approved"
    SKIPPED = "skipped"
    APPLIED = "applied"
    FAILED = "failed"


# =============================================================================
# ImportBatch Schemas
# =============================================================================


class ImportBatchCreate(BaseModel):
    """Schema for creating a new import batch."""

    filename: str | None = Field(None, max_length=255, description="Original filename")
    target_block: int | None = Field(
        None, ge=1, le=26, description="Target block number (1-26)"
    )
    target_start_date: date | None = Field(None, description="Target start date")
    target_end_date: date | None = Field(None, description="Target end date")
    notes: str | None = Field(None, max_length=2000, description="Import notes")
    conflict_resolution: ConflictResolutionMode = Field(
        default=ConflictResolutionMode.UPSERT,
        description="How to handle conflicts during apply",
    )

    @field_validator("target_end_date")
    @classmethod
    def validate_date_range(cls, v: date | None, info) -> date | None:
        """Validate end date is after start date."""
        if v is not None and info.data.get("target_start_date") is not None:
            if v < info.data["target_start_date"]:
                raise ValueError("target_end_date must be >= target_start_date")
        return v


class ImportBatchCounts(BaseModel):
    """Aggregated counts for import batch."""

    total: int = Field(0, description="Total staged assignments")
    pending: int = Field(0, description="Pending review")
    approved: int = Field(0, description="Approved for apply")
    skipped: int = Field(0, description="Skipped by user")
    applied: int = Field(0, description="Successfully applied")
    failed: int = Field(0, description="Failed to apply")


class ImportBatchResponse(BaseModel):
    """Schema for import batch response."""

    id: UUID
    created_at: datetime
    created_by_id: UUID | None = None

    # File info
    filename: str | None = None
    file_hash: str | None = None
    file_size_bytes: int | None = None

    # Status
    status: ImportBatchStatus
    conflict_resolution: ConflictResolutionMode

    # Target scope
    target_block: int | None = None
    target_start_date: date | None = None
    target_end_date: date | None = None

    # Metadata
    notes: str | None = None
    row_count: int | None = None
    error_count: int = 0
    warning_count: int = 0

    # Apply tracking
    applied_at: datetime | None = None
    applied_by_id: UUID | None = None
    rollback_available: bool = True
    rollback_expires_at: datetime | None = None

    # Rollback tracking
    rolled_back_at: datetime | None = None
    rolled_back_by_id: UUID | None = None

    # Aggregated counts
    counts: ImportBatchCounts = Field(
        default_factory=ImportBatchCounts,
        description="Aggregated assignment counts by status",
    )

    model_config = ConfigDict(from_attributes=True)


class ImportBatchListItem(BaseModel):
    """Schema for import batch in list view (lightweight)."""

    id: UUID
    created_at: datetime
    filename: str | None = None
    status: ImportBatchStatus
    target_block: int | None = None
    target_start_date: date | None = None
    target_end_date: date | None = None
    row_count: int | None = None
    error_count: int = 0
    counts: ImportBatchCounts = Field(default_factory=ImportBatchCounts)

    model_config = ConfigDict(from_attributes=True)


class ImportBatchList(BaseModel):
    """Schema for paginated import batch list response."""

    items: list[ImportBatchListItem] = Field(..., description="List of import batches")
    total: int = Field(..., description="Total count of batches")
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")


# =============================================================================
# StagedAssignment Schemas
# =============================================================================


class StagedAssignmentResponse(BaseModel):
    """Schema for staged assignment response."""

    id: UUID
    batch_id: UUID

    # Source tracking
    row_number: int | None = None
    sheet_name: str | None = None

    # Raw parsed data
    person_name: str
    assignment_date: date
    slot: str | None = None  # AM/PM or null for full day
    rotation_name: str | None = None
    raw_cell_value: str | None = None

    # Fuzzy match results
    matched_person_id: UUID | None = None
    matched_person_name: str | None = Field(
        None, description="Resolved person name from match"
    )
    person_match_confidence: int | None = Field(
        None, ge=0, le=100, description="Match confidence 0-100"
    )

    matched_rotation_id: UUID | None = None
    matched_rotation_name: str | None = Field(
        None, description="Resolved rotation name from match"
    )
    rotation_match_confidence: int | None = Field(
        None, ge=0, le=100, description="Match confidence 0-100"
    )

    # Conflict detection
    conflict_type: str | None = Field(None, description="none/duplicate/overwrite")
    existing_assignment_id: UUID | None = None

    # Status
    status: StagedAssignmentStatus

    # Validation
    validation_errors: list[dict] | None = None
    validation_warnings: list[dict] | None = None

    # After apply
    created_assignment_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("conflict_type")
    @classmethod
    def validate_conflict_type(cls, v: str | None) -> str | None:
        """Validate conflict_type values."""
        if v is not None and v not in ("none", "duplicate", "overwrite"):
            raise ValueError(
                "conflict_type must be 'none', 'duplicate', or 'overwrite'"
            )
        return v


class StagedAssignmentUpdate(BaseModel):
    """Schema for updating a staged assignment (approve/skip)."""

    status: StagedAssignmentStatus = Field(
        ..., description="New status (approved or skipped)"
    )

    @field_validator("status")
    @classmethod
    def validate_status_transition(
        cls, v: StagedAssignmentStatus
    ) -> StagedAssignmentStatus:
        """Only allow transitioning to approved or skipped."""
        if v not in (StagedAssignmentStatus.APPROVED, StagedAssignmentStatus.SKIPPED):
            raise ValueError("status must be 'approved' or 'skipped'")
        return v


class StagedAssignmentBulkUpdate(BaseModel):
    """Schema for bulk updating staged assignments."""

    ids: list[UUID] = Field(
        ..., min_length=1, max_length=1000, description="Assignment IDs to update"
    )
    status: StagedAssignmentStatus = Field(
        ..., description="New status (approved or skipped)"
    )

    @field_validator("status")
    @classmethod
    def validate_status_transition(
        cls, v: StagedAssignmentStatus
    ) -> StagedAssignmentStatus:
        """Only allow transitioning to approved or skipped."""
        if v not in (StagedAssignmentStatus.APPROVED, StagedAssignmentStatus.SKIPPED):
            raise ValueError("status must be 'approved' or 'skipped'")
        return v


# =============================================================================
# Import Preview Schemas
# =============================================================================


class ImportConflictDetail(BaseModel):
    """Details about a conflict between staged and existing assignment."""

    staged_assignment_id: UUID
    existing_assignment_id: UUID
    person_name: str
    assignment_date: date
    slot: str | None = None
    staged_rotation: str | None = None
    existing_rotation: str | None = None
    conflict_type: str = Field(..., description="duplicate or overwrite")


class ImportPreviewResponse(BaseModel):
    """Schema for import preview - comparison of staged vs existing."""

    batch_id: UUID

    # Summary counts
    new_count: int = Field(0, description="New assignments to create")
    update_count: int = Field(0, description="Existing assignments to update")
    conflict_count: int = Field(0, description="Conflicts requiring review")
    skip_count: int = Field(0, description="Assignments marked as skip")

    # ACGME compliance preview
    acgme_violations: list[str] = Field(
        default_factory=list,
        description="ACGME violations that would occur after apply",
    )

    # Detailed staged assignments (first N for preview)
    staged_assignments: list[StagedAssignmentResponse] = Field(
        default_factory=list, description="Staged assignments (paginated)"
    )

    # Conflict details
    conflicts: list[ImportConflictDetail] = Field(
        default_factory=list, description="Detailed conflict information"
    )

    # Pagination for staged_assignments
    total_staged: int = Field(0, description="Total staged assignments")
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=100)


# =============================================================================
# Import Apply Schemas
# =============================================================================


class ImportApplyRequest(BaseModel):
    """Request schema for applying an import batch."""

    conflict_resolution: ConflictResolutionMode | None = Field(
        None, description="Override conflict resolution mode (optional)"
    )
    dry_run: bool = Field(False, description="If True, validate only without applying")
    validate_acgme: bool = Field(
        True, description="If True, validate ACGME compliance before apply"
    )


class ImportApplyError(BaseModel):
    """Error details for a failed apply operation."""

    staged_assignment_id: UUID
    row_number: int | None = None
    person_name: str
    assignment_date: date
    error_message: str
    error_code: str | None = None


class ImportApplyResponse(BaseModel):
    """Response schema for import apply operation."""

    batch_id: UUID
    status: ImportBatchStatus

    # Result counts
    applied_count: int = Field(0, description="Successfully applied assignments")
    skipped_count: int = Field(0, description="Skipped assignments (user choice)")
    error_count: int = Field(0, description="Failed to apply")

    # Timing
    started_at: datetime
    completed_at: datetime | None = None
    processing_time_ms: float | None = None

    # Errors
    errors: list[ImportApplyError] = Field(
        default_factory=list, description="Detailed error information"
    )

    # ACGME warnings (if any violations were created)
    acgme_warnings: list[str] = Field(
        default_factory=list, description="ACGME warnings after apply"
    )

    # Rollback info
    rollback_available: bool = True
    rollback_expires_at: datetime | None = None

    # Dry run flag
    dry_run: bool = False


# =============================================================================
# Import Rollback Schemas
# =============================================================================


class ImportRollbackRequest(BaseModel):
    """Request schema for rolling back an import batch."""

    reason: str | None = Field(None, max_length=500, description="Reason for rollback")


class ImportRollbackResponse(BaseModel):
    """Response schema for import rollback operation."""

    batch_id: UUID
    status: ImportBatchStatus

    # Result counts
    rolled_back_count: int = Field(0, description="Assignments rolled back")
    failed_count: int = Field(0, description="Failed to rollback")

    # Timing
    rolled_back_at: datetime
    rolled_back_by_id: UUID | None = None

    # Errors (if any)
    errors: list[str] = Field(default_factory=list)
