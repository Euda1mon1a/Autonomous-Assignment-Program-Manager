"""Schedule draft schemas for staging workflow.

Provides Pydantic schemas for:
- ScheduleDraft create/response (draft operations)
- DraftAssignment response (staged assignments)
- DraftFlag response/acknowledge (review flags)
- Publish and rollback operations
"""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScheduleDraftStatus(str, Enum):
    """Status of a schedule draft."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ROLLED_BACK = "rolled_back"
    DISCARDED = "discarded"


class DraftSourceType(str, Enum):
    """Source of draft changes."""

    SOLVER = "solver"
    MANUAL = "manual"
    SWAP = "swap"
    IMPORT = "import"


class DraftAssignmentChangeType(str, Enum):
    """Type of change in a draft assignment."""

    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"


class DraftFlagType(str, Enum):
    """Types of flags that require review."""

    CONFLICT = "conflict"
    ACGME_VIOLATION = "acgme_violation"
    COVERAGE_GAP = "coverage_gap"
    MANUAL_REVIEW = "manual_review"


class DraftFlagSeverity(str, Enum):
    """Severity level of a flag."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# =============================================================================
# ScheduleDraft Schemas
# =============================================================================


class ScheduleDraftCreate(BaseModel):
    """Schema for creating a new schedule draft."""

    source_type: DraftSourceType = Field(
        ..., description="Source of the draft (solver, manual, swap, import)"
    )
    target_block: int | None = Field(
        None, ge=1, le=26, description="Target block number (1-26)"
    )
    target_start_date: date = Field(..., description="Start date of draft scope")
    target_end_date: date = Field(..., description="End date of draft scope")
    schedule_run_id: UUID | None = Field(
        None, description="Optional link to schedule_runs for solver drafts"
    )
    notes: str | None = Field(None, max_length=2000, description="Optional notes")

    @field_validator("target_end_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Validate end date is after start date."""
        if info.data.get("target_start_date") and v < info.data["target_start_date"]:
            raise ValueError("target_end_date must be >= target_start_date")
        return v


class ScheduleDraftCounts(BaseModel):
    """Aggregated counts for a schedule draft."""

    assignments_total: int = Field(0, description="Total staged assignments")
    added: int = Field(0, description="New assignments to add")
    modified: int = Field(0, description="Existing assignments to modify")
    deleted: int = Field(0, description="Assignments to delete")
    flags_total: int = Field(0, description="Total flags")
    flags_acknowledged: int = Field(0, description="Acknowledged flags")
    flags_unacknowledged: int = Field(0, description="Unacknowledged flags")


class ScheduleDraftResponse(BaseModel):
    """Schema for schedule draft response."""

    id: UUID
    created_at: datetime
    created_by_id: UUID | None = None

    # Scope
    target_block: int | None = None
    target_start_date: date
    target_end_date: date

    # Status
    status: ScheduleDraftStatus
    source_type: DraftSourceType

    # Source tracking
    source_schedule_run_id: UUID | None = None

    # Publish tracking
    published_at: datetime | None = None
    published_by_id: UUID | None = None

    # Rollback info
    rollback_available: bool = True
    rollback_expires_at: datetime | None = None
    rolled_back_at: datetime | None = None
    rolled_back_by_id: UUID | None = None

    # Metadata
    notes: str | None = None
    change_summary: dict | None = None

    # Flags
    flags_total: int = 0
    flags_acknowledged: int = 0
    override_comment: str | None = None
    override_by_id: UUID | None = None

    # Aggregated counts
    counts: ScheduleDraftCounts = Field(default_factory=ScheduleDraftCounts)

    model_config = ConfigDict(from_attributes=True)


class ScheduleDraftListItem(BaseModel):
    """Schema for schedule draft in list view (lightweight)."""

    id: UUID
    created_at: datetime
    status: ScheduleDraftStatus
    source_type: DraftSourceType
    target_block: int | None = None
    target_start_date: date
    target_end_date: date
    flags_total: int = 0
    flags_acknowledged: int = 0
    counts: ScheduleDraftCounts = Field(default_factory=ScheduleDraftCounts)

    model_config = ConfigDict(from_attributes=True)


class ScheduleDraftList(BaseModel):
    """Schema for paginated schedule draft list response."""

    items: list[ScheduleDraftListItem] = Field(..., description="List of drafts")
    total: int = Field(..., description="Total count of drafts")
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")


# =============================================================================
# DraftAssignment Schemas
# =============================================================================


class DraftAssignmentResponse(BaseModel):
    """Schema for draft assignment response."""

    id: UUID
    draft_id: UUID

    # Assignment data
    person_id: UUID
    person_name: str | None = None
    assignment_date: date
    time_of_day: str | None = None
    activity_code: str | None = None
    rotation_id: UUID | None = None
    rotation_name: str | None = None

    # Change tracking
    change_type: DraftAssignmentChangeType
    existing_assignment_id: UUID | None = None

    # After publish
    created_assignment_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class DraftAssignmentCreate(BaseModel):
    """Schema for adding an assignment to a draft."""

    person_id: UUID = Field(..., description="UUID of the person")
    assignment_date: date = Field(..., description="Date of the assignment")
    time_of_day: str | None = Field(None, description="AM/PM or None for full day")
    activity_code: str | None = Field(None, description="Activity code")
    rotation_id: UUID | None = Field(None, description="Rotation template ID")
    change_type: DraftAssignmentChangeType = Field(
        DraftAssignmentChangeType.ADD, description="Type of change"
    )
    existing_assignment_id: UUID | None = Field(
        None, description="For modify/delete, the existing assignment ID"
    )

    @field_validator("time_of_day")
    @classmethod
    def validate_time_of_day(cls, v: str | None) -> str | None:
        """Validate time_of_day values."""
        if v is not None and v.upper() not in ("AM", "PM"):
            raise ValueError("time_of_day must be 'AM', 'PM', or null")
        return v.upper() if v else None


# =============================================================================
# DraftFlag Schemas
# =============================================================================


class DraftFlagResponse(BaseModel):
    """Schema for draft flag response."""

    id: UUID
    draft_id: UUID

    # Flag details
    flag_type: DraftFlagType
    severity: DraftFlagSeverity
    message: str

    # Related entities
    assignment_id: UUID | None = None
    person_id: UUID | None = None
    person_name: str | None = None
    affected_date: date | None = None

    # Resolution
    acknowledged_at: datetime | None = None
    acknowledged_by_id: UUID | None = None
    resolution_note: str | None = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DraftFlagAcknowledge(BaseModel):
    """Schema for acknowledging a flag."""

    resolution_note: str | None = Field(
        None, max_length=500, description="Optional note about resolution"
    )


class DraftFlagBulkAcknowledge(BaseModel):
    """Schema for bulk acknowledging flags."""

    flag_ids: list[UUID] = Field(
        ..., min_length=1, max_length=100, description="Flag IDs to acknowledge"
    )
    resolution_note: str | None = Field(
        None, max_length=500, description="Optional note about resolution"
    )


# =============================================================================
# Preview Schema
# =============================================================================


class DraftPreviewResponse(BaseModel):
    """Schema for draft preview - comparison of draft vs live."""

    draft_id: UUID

    # Summary counts
    add_count: int = Field(0, description="New assignments to add")
    modify_count: int = Field(0, description="Assignments to modify")
    delete_count: int = Field(0, description="Assignments to delete")

    # Flags
    flags_total: int = Field(0, description="Total flags")
    flags_acknowledged: int = Field(0, description="Acknowledged flags")

    # ACGME compliance preview
    acgme_violations: list[str] = Field(
        default_factory=list,
        description="ACGME violations that would occur after publish",
    )

    # Detailed assignments (paginated)
    assignments: list[DraftAssignmentResponse] = Field(
        default_factory=list, description="Staged assignments"
    )

    # Detailed flags
    flags: list[DraftFlagResponse] = Field(
        default_factory=list, description="Review flags"
    )


# =============================================================================
# Publish Schemas
# =============================================================================


class PublishRequest(BaseModel):
    """Request schema for publishing a draft."""

    override_comment: str | None = Field(
        None,
        max_length=500,
        description="Required for Tier 1 if unacknowledged flags exist",
    )
    validate_acgme: bool = Field(
        True, description="If True, validate ACGME compliance after publish"
    )


class PublishError(BaseModel):
    """Error details for a failed publish operation."""

    draft_assignment_id: UUID
    person_id: UUID
    assignment_date: date
    error_message: str


class PublishResponse(BaseModel):
    """Response schema for publish operation."""

    draft_id: UUID
    status: ScheduleDraftStatus

    # Result counts
    published_count: int = Field(0, description="Successfully published assignments")
    error_count: int = Field(0, description="Failed to publish")

    # Errors
    errors: list[PublishError] = Field(
        default_factory=list, description="Detailed error information"
    )

    # ACGME warnings (if any violations were created)
    acgme_warnings: list[str] = Field(
        default_factory=list, description="ACGME warnings after publish"
    )

    # Rollback info
    rollback_available: bool = True
    rollback_expires_at: datetime | None = None

    message: str = ""


# =============================================================================
# Rollback Schemas
# =============================================================================


class RollbackRequest(BaseModel):
    """Request schema for rolling back a published draft."""

    reason: str | None = Field(None, max_length=500, description="Reason for rollback")


class RollbackResponse(BaseModel):
    """Response schema for rollback operation."""

    draft_id: UUID
    status: ScheduleDraftStatus

    # Result counts
    rolled_back_count: int = Field(0, description="Assignments rolled back")
    failed_count: int = Field(0, description="Failed to rollback")

    # Timing
    rolled_back_at: datetime
    rolled_back_by_id: UUID | None = None

    # Errors (if any)
    errors: list[str] = Field(default_factory=list)

    message: str = ""
