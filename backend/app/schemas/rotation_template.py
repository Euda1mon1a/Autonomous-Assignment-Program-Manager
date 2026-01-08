"""Rotation template schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TemplateCategory(str, Enum):
    """
    Template categories for UI grouping and filtering.

    - rotation: Clinical work (clinic, inpatient, outpatient, procedure)
    - time_off: ACGME-protected rest (off, recovery) - does NOT count toward away-from-program
    - absence: Days away from program (absence activity type) - counts toward 28-day limit
    - educational: Structured learning (conference, education, lecture)
    """

    ROTATION = "rotation"
    TIME_OFF = "time_off"
    ABSENCE = "absence"
    EDUCATIONAL = "educational"


# Valid categories as tuple for validation
VALID_TEMPLATE_CATEGORIES = tuple(c.value for c in TemplateCategory)


class RotationTemplateBase(BaseModel):
    """Base rotation template schema."""

    name: str
    activity_type: str  # 'clinic', 'inpatient', 'procedure', 'conference', 'lecture', etc.
    template_category: str = Field(
        default="rotation",
        description="Category for UI grouping: rotation, time_off, absence, educational",
    )
    abbreviation: str | None = None
    display_abbreviation: str | None = None  # User-facing code for schedule grid
    font_color: str | None = None
    background_color: str | None = None
    clinic_location: str | None = None
    max_residents: int | None = None
    requires_specialty: str | None = None
    requires_procedure_credential: bool | None = False
    supervision_required: bool | None = True
    max_supervision_ratio: int | None = 4

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, v: str) -> str:
        """Validate activity_type is one of the valid types."""
        # Valid activity types used across the system:
        # - clinic/outpatient: Clinic sessions and outpatient rotations
        # - inpatient: Hospital ward rotations (FMIT, wards)
        # - procedure/procedures: Procedural rotations
        # - conference/education/lecture: Educational activities, didactics
        # - absence: Leave, vacation, sick time
        # - off: Days off, recovery days
        # - recovery: Post-call recovery
        valid_types = (
            "clinic",
            "inpatient",
            "procedure",
            "procedures",
            "conference",
            "education",
            "lecture",
            "outpatient",
            "absence",
            "off",
            "recovery",
            # Legacy/alternate names
            "academic",
            "clinical",
            "leave",
        )
        if v not in valid_types:
            raise ValueError(f"activity_type must be one of {valid_types}")
        return v

    @field_validator("max_residents")
    @classmethod
    def validate_max_residents(cls, v: int | None) -> int | None:
        """Validate max_residents is positive."""
        if v is not None and v < 1:
            raise ValueError("max_residents must be at least 1")
        return v

    @field_validator("max_supervision_ratio")
    @classmethod
    def validate_max_supervision_ratio(cls, v: int | None) -> int | None:
        """Validate supervision ratio is reasonable."""
        if v is not None and (v < 1 or v > 10):
            raise ValueError("max_supervision_ratio must be between 1 and 10")
        return v

    @field_validator("template_category")
    @classmethod
    def validate_template_category(cls, v: str) -> str:
        """Validate template_category is one of the valid categories."""
        if v not in VALID_TEMPLATE_CATEGORIES:
            raise ValueError(f"template_category must be one of {VALID_TEMPLATE_CATEGORIES}")
        return v


class RotationTemplateCreate(RotationTemplateBase):
    """Schema for creating a rotation template."""

    pass


class RotationTemplateUpdate(BaseModel):
    """Schema for updating a rotation template."""

    name: str | None = None
    activity_type: str | None = None
    template_category: str | None = None
    abbreviation: str | None = None
    display_abbreviation: str | None = None  # User-facing code for schedule grid
    font_color: str | None = None
    background_color: str | None = None
    clinic_location: str | None = None
    max_residents: int | None = None
    requires_specialty: str | None = None
    requires_procedure_credential: bool | None = None
    supervision_required: bool | None = None
    max_supervision_ratio: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate name is not empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("name cannot be empty")
        return v.strip() if v else v

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, v: str | None) -> str | None:
        """Validate activity_type is one of the valid types."""
        if v is not None:
            valid_types = (
                "clinic",
                "inpatient",
                "procedure",
                "procedures",
                "conference",
                "education",
                "lecture",
                "outpatient",
                "absence",
                "off",
                "recovery",
                # Legacy/alternate names
                "academic",
                "clinical",
                "leave",
            )
            if v not in valid_types:
                raise ValueError(f"activity_type must be one of {valid_types}")
        return v

    @field_validator("template_category")
    @classmethod
    def validate_template_category(cls, v: str | None) -> str | None:
        """Validate template_category is one of the valid categories."""
        if v is not None and v not in VALID_TEMPLATE_CATEGORIES:
            raise ValueError(f"template_category must be one of {VALID_TEMPLATE_CATEGORIES}")
        return v

    @field_validator("max_residents")
    @classmethod
    def validate_max_residents(cls, v: int | None) -> int | None:
        """Validate max_residents is positive."""
        if v is not None and v < 1:
            raise ValueError("max_residents must be at least 1")
        return v

    @field_validator("max_supervision_ratio")
    @classmethod
    def validate_max_supervision_ratio(cls, v: int | None) -> int | None:
        """Validate supervision ratio is reasonable."""
        if v is not None and (v < 1 or v > 10):
            raise ValueError("max_supervision_ratio must be between 1 and 10")
        return v


class RotationTemplateResponse(RotationTemplateBase):
    """Schema for rotation template response."""

    id: UUID
    created_at: datetime
    # Archive fields
    is_archived: bool = False
    archived_at: datetime | None = None
    archived_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class RotationTemplateListResponse(BaseModel):
    """Schema for list of rotation templates."""

    items: list[RotationTemplateResponse]
    total: int


# =============================================================================
# Batch Operation Schemas
# =============================================================================


class BatchTemplateDeleteRequest(BaseModel):
    """Request schema for batch delete of rotation templates.

    Performs atomic deletion of multiple templates - all succeed or all fail.
    """

    template_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of template IDs to delete (max 100)",
    )
    dry_run: bool = Field(
        default=False, description="If True, validate only without deleting"
    )


class BatchTemplateUpdateItem(BaseModel):
    """Single template update in a batch operation."""

    template_id: UUID
    updates: RotationTemplateUpdate


class BatchTemplateUpdateRequest(BaseModel):
    """Request schema for batch update of rotation templates.

    Performs atomic update of multiple templates - all succeed or all fail.
    """

    templates: list[BatchTemplateUpdateItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of template updates (max 100)",
    )
    dry_run: bool = Field(
        default=False, description="If True, validate only without updating"
    )


class BatchOperationResult(BaseModel):
    """Result for a single operation in a batch."""

    index: int = Field(..., description="Index of the operation in the batch")
    template_id: UUID
    success: bool
    error: str | None = None


class BatchTemplateResponse(BaseModel):
    """Response schema for batch template operations."""

    operation_type: str  # "delete", "update", "create", "archive", "restore"
    total: int = Field(..., description="Total number of operations requested")
    succeeded: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: list[BatchOperationResult] = Field(
        default_factory=list, description="Detailed results for each operation"
    )
    dry_run: bool = Field(default=False, description="Whether this was a dry run")
    created_ids: list[UUID] | None = Field(
        default=None, description="IDs of created templates (for create operations)"
    )


# =============================================================================
# Bulk Create Schemas
# =============================================================================


class BatchTemplateCreateRequest(BaseModel):
    """Request schema for batch create of rotation templates.

    Performs atomic creation of multiple templates - all succeed or all fail.
    """

    templates: list[RotationTemplateCreate] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of templates to create (max 100)",
    )
    dry_run: bool = Field(
        default=False, description="If True, validate only without creating"
    )


# =============================================================================
# Archive/Restore Schemas
# =============================================================================


class BatchArchiveRequest(BaseModel):
    """Request schema for batch archive of rotation templates."""

    template_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of template IDs to archive (max 100)",
    )
    dry_run: bool = Field(
        default=False, description="If True, validate only without archiving"
    )


class BatchRestoreRequest(BaseModel):
    """Request schema for batch restore of rotation templates."""

    template_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of template IDs to restore (max 100)",
    )
    dry_run: bool = Field(
        default=False, description="If True, validate only without restoring"
    )


# =============================================================================
# Export Schema
# =============================================================================


class TemplateExportRequest(BaseModel):
    """Request schema for exporting rotation templates."""

    template_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of template IDs to export (max 100)",
    )
    include_patterns: bool = Field(
        default=True, description="Include weekly patterns in export"
    )
    include_preferences: bool = Field(
        default=True, description="Include preferences in export"
    )


class TemplateExportData(BaseModel):
    """Single template export data."""

    template: RotationTemplateResponse
    patterns: list[dict] | None = None
    preferences: list[dict] | None = None


class TemplateExportResponse(BaseModel):
    """Response schema for template export."""

    templates: list[TemplateExportData]
    exported_at: datetime
    total: int


# =============================================================================
# Conflict Detection Schema
# =============================================================================


class ConflictCheckRequest(BaseModel):
    """Request for checking conflicts before operations."""

    template_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Template IDs to check for conflicts",
    )
    operation: str = Field(
        ..., description="Operation type: 'delete', 'archive', 'update'"
    )


class TemplateConflict(BaseModel):
    """Single conflict item."""

    template_id: UUID
    template_name: str
    conflict_type: str  # "has_assignments", "name_collision", "referenced_by"
    description: str
    severity: str = "warning"  # "warning", "error"
    blocking: bool = False


class ConflictCheckResponse(BaseModel):
    """Response for conflict check."""

    has_conflicts: bool
    conflicts: list[TemplateConflict]
    can_proceed: bool  # False if any blocking conflicts
