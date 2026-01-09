"""
Pydantic schemas for block assignment import/export.

Supports:
- CSV import (block_number, rotation_abbrev, resident_name)
- Excel import (.xlsx via /parse-xlsx endpoint)
- Multi-format export (CSV, XLSX)
"""

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ImportFormat(str, Enum):
    """Supported import file formats."""

    CSV = "csv"
    XLSX = "xlsx"


class MatchStatus(str, Enum):
    """Status of row matching during preview."""

    MATCHED = "matched"  # All fields matched
    UNKNOWN_ROTATION = "unknown_rotation"  # Rotation not found
    UNKNOWN_RESIDENT = "unknown_resident"  # Resident not found
    DUPLICATE = "duplicate"  # Assignment already exists
    INVALID = "invalid"  # Validation error


class DuplicateAction(str, Enum):
    """Action to take for duplicate assignments."""

    SKIP = "skip"  # Skip the duplicate row
    UPDATE = "update"  # Update existing assignment


# ============================================================================
# Import Preview Schemas
# ============================================================================


class BlockAssignmentPreviewItem(BaseModel):
    """Single row preview with match status."""

    row_number: int = Field(..., description="Row number in source file (1-indexed)")
    block_number: int = Field(..., description="Block number (0-13)")
    rotation_input: str = Field(..., description="Rotation as entered in source")
    resident_display: str = Field(
        ..., description="Anonymized resident display (e.g., 'S*****, J***')"
    )

    # Match results
    match_status: MatchStatus = Field(..., description="Overall match status")
    matched_rotation_id: UUID | None = Field(None, description="Matched rotation template ID")
    matched_rotation_name: str | None = Field(
        None, description="Matched rotation display name"
    )
    rotation_confidence: float = Field(
        1.0, ge=0.0, le=1.0, description="Rotation match confidence"
    )
    matched_resident_id: UUID | None = Field(None, description="Matched resident ID")
    resident_confidence: float = Field(
        1.0, ge=0.0, le=1.0, description="Resident match confidence"
    )

    # Duplicate handling
    is_duplicate: bool = Field(False, description="True if assignment already exists")
    existing_assignment_id: UUID | None = Field(
        None, description="ID of existing assignment if duplicate"
    )
    duplicate_action: DuplicateAction = Field(
        DuplicateAction.SKIP, description="Action for duplicates"
    )

    # Validation messages
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")


class UnknownRotationItem(BaseModel):
    """Unknown rotation requiring template creation."""

    abbreviation: str = Field(..., description="Rotation abbreviation from source")
    occurrences: int = Field(..., description="Number of rows with this abbreviation")
    suggested_name: str | None = Field(
        None, description="Suggested full name based on abbreviation"
    )


class BlockAssignmentPreviewResponse(BaseModel):
    """Full preview response for import validation."""

    preview_id: str = Field(..., description="Unique ID for this preview session")
    academic_year: int = Field(..., description="Auto-calculated or specified academic year")
    format_detected: ImportFormat = Field(..., description="Detected import format")

    # Preview items
    items: list[BlockAssignmentPreviewItem] = Field(
        default_factory=list, description="Preview items"
    )

    # Summary statistics
    total_rows: int = Field(0, description="Total rows parsed")
    matched_count: int = Field(0, description="Fully matched rows")
    unknown_rotation_count: int = Field(0, description="Rows with unknown rotation")
    unknown_resident_count: int = Field(0, description="Rows with unknown resident")
    duplicate_count: int = Field(0, description="Duplicate rows")
    invalid_count: int = Field(0, description="Invalid rows")

    # Unknown rotations for inline creation
    unknown_rotations: list[UnknownRotationItem] = Field(
        default_factory=list, description="Unknown rotations for template creation"
    )

    # Parsing warnings
    warnings: list[str] = Field(default_factory=list, description="Parsing warnings")


# ============================================================================
# Import Request/Result Schemas
# ============================================================================


class BlockAssignmentImportRequest(BaseModel):
    """Request to execute import after preview."""

    preview_id: str = Field(..., description="Preview ID from preview response")
    academic_year: int = Field(..., description="Academic year for assignments")

    # Options
    skip_duplicates: bool = Field(True, description="Skip duplicate assignments")
    update_duplicates: bool = Field(
        False, description="Update existing duplicates (overrides skip_duplicates)"
    )
    import_unmatched: bool = Field(
        False, description="Import rows with warnings (low confidence matches)"
    )

    # Override actions for specific rows
    row_overrides: dict[int, DuplicateAction] = Field(
        default_factory=dict, description="Per-row duplicate action overrides"
    )


class BlockAssignmentImportResult(BaseModel):
    """Result of import execution."""

    success: bool = Field(..., description="True if import completed")
    academic_year: int = Field(..., description="Academic year imported")

    # Counts
    total_rows: int = Field(0, description="Total rows processed")
    imported_count: int = Field(0, description="Successfully imported")
    updated_count: int = Field(0, description="Updated existing")
    skipped_count: int = Field(0, description="Skipped (duplicates/errors)")
    failed_count: int = Field(0, description="Failed to import")

    # Error details (row numbers only, no PII)
    failed_rows: list[int] = Field(
        default_factory=list, description="Row numbers that failed"
    )
    error_messages: list[str] = Field(
        default_factory=list, description="Error messages (no PII)"
    )

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Quick Template Creation Schemas
# ============================================================================


class QuickTemplateCreateRequest(BaseModel):
    """Minimal request to create rotation template during import."""

    abbreviation: str = Field(
        ..., min_length=1, max_length=20, description="Rotation abbreviation"
    )
    name: str = Field(
        ..., min_length=1, max_length=100, description="Full rotation name"
    )
    activity_type: str = Field(
        "outpatient",
        description="Activity type (clinic, inpatient, procedures, etc.)",
    )
    leave_eligible: bool = Field(
        True, description="Whether rotation is leave-eligible"
    )

    @field_validator("activity_type")
    @classmethod
    def validate_activity_type(cls, v: str) -> str:
        """Validate activity type."""
        valid = [
            "clinic",
            "inpatient",
            "outpatient",
            "procedures",
            "call",
            "education",
            "off",
            "conference",
        ]
        if v.lower() not in valid:
            raise ValueError(f"activity_type must be one of {valid}")
        return v.lower()


class QuickTemplateCreateResponse(BaseModel):
    """Response after creating a template."""

    id: UUID = Field(..., description="Created template ID")
    abbreviation: str = Field(..., description="Template abbreviation")
    name: str = Field(..., description="Template name")
    activity_type: str = Field(..., description="Activity type")


# ============================================================================
# Export Schemas
# ============================================================================


class ExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    XLSX = "xlsx"


class BlockAssignmentExportRequest(BaseModel):
    """Request for block assignment export."""

    format: ExportFormat = Field(ExportFormat.CSV, description="Export format")
    academic_year: int = Field(..., description="Academic year to export")

    # Filters
    block_numbers: list[int] | None = Field(
        None, description="Specific blocks to export (None = all)"
    )
    rotation_ids: list[UUID] | None = Field(
        None, description="Filter by rotation IDs"
    )
    resident_ids: list[UUID] | None = Field(
        None, description="Filter by resident IDs"
    )

    # Options
    include_pgy_level: bool = Field(True, description="Include PGY level column")
    include_leave_status: bool = Field(False, description="Include leave status column")
    group_by: Literal["block", "resident", "rotation"] | None = Field(
        None, description="Group results by field"
    )


class BlockAssignmentExportResult(BaseModel):
    """Result of export operation."""

    success: bool = Field(..., description="Export succeeded")
    format: ExportFormat = Field(..., description="Export format")
    filename: str = Field(..., description="Generated filename")
    row_count: int = Field(..., description="Number of rows exported")
    download_url: str | None = Field(
        None, description="URL to download file (for large exports)"
    )
    data: str | None = Field(
        None, description="Base64-encoded file data (for small exports)"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Upload Request Schema (for direct CSV content)
# ============================================================================


class BlockAssignmentUploadRequest(BaseModel):
    """Request to upload CSV content directly (paste or file read)."""

    content: str = Field(..., description="CSV content")
    academic_year: int | None = Field(
        None, description="Academic year (None = auto-detect)"
    )
    format: ImportFormat = Field(ImportFormat.CSV, description="Content format")

    # Format hints
    block_number: int | None = Field(
        None, description="Block number if importing by-block format"
    )
    rotation_id: UUID | None = Field(
        None, description="Rotation ID if importing by-rotation format"
    )
