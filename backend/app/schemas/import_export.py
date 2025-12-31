"""
Import/export schemas for data exchange.

Provides schemas for:
- CSV import/export
- JSON import/export
- Excel import/export
- Data templates
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ImportFormat(str, Enum):
    """Import file format."""

    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


class ExportFormat(str, Enum):
    """Export file format."""

    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"


class ImportRequest(BaseModel):
    """Request for data import."""

    format: ImportFormat = Field(..., description="Import file format")
    data: str = Field(..., description="Base64-encoded file data or raw data")
    entity_type: str = Field(..., description="Type of entity being imported")
    options: dict | None = Field(None, description="Import options")
    validate_only: bool = Field(False, description="Only validate, don't import")

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity_type is valid."""
        valid_types = [
            "person",
            "assignment",
            "block",
            "rotation_template",
            "certification",
        ]
        if v not in valid_types:
            raise ValueError(f"entity_type must be one of {valid_types}")
        return v


class ExportRequest(BaseModel):
    """Request for data export."""

    format: ExportFormat = Field(..., description="Export file format")
    entity_type: str = Field(..., description="Type of entity to export")
    filters: dict | None = Field(None, description="Filters to apply")
    fields: list[str] | None = Field(None, description="Fields to include (None = all)")
    include_related: bool = Field(False, description="Include related entities")

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity_type is valid."""
        valid_types = [
            "person",
            "assignment",
            "block",
            "rotation_template",
            "certification",
            "swap",
        ]
        if v not in valid_types:
            raise ValueError(f"entity_type must be one of {valid_types}")
        return v


class ImportValidationError(BaseModel):
    """Validation error during import."""

    row: int = Field(..., description="Row number (1-indexed)")
    field: str | None = Field(None, description="Field with error")
    message: str = Field(..., description="Error message")
    severity: str = Field(..., description="Error severity (error, warning)")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity is valid."""
        if v not in ("error", "warning"):
            raise ValueError("severity must be 'error' or 'warning'")
        return v


class ImportValidationResult(BaseModel):
    """Result of import validation."""

    is_valid: bool = Field(..., description="Whether data is valid for import")
    total_rows: int = Field(..., description="Total rows in import file")
    valid_rows: int = Field(..., description="Valid rows")
    invalid_rows: int = Field(..., description="Invalid rows")
    warnings: list[ImportValidationError] = Field([], description="Validation warnings")
    errors: list[ImportValidationError] = Field([], description="Validation errors")


class ImportResult(BaseModel):
    """Result of data import."""

    total_rows: int = Field(..., description="Total rows processed")
    imported: int = Field(..., description="Successfully imported rows")
    skipped: int = Field(..., description="Skipped rows")
    failed: int = Field(..., description="Failed rows")
    errors: list[ImportValidationError] = Field([], description="Import errors")
    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="Import start time"
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Import completion time"
    )


class ExportResult(BaseModel):
    """Result of data export."""

    format: ExportFormat = Field(..., description="Export format")
    filename: str = Field(..., description="Generated filename")
    data: str = Field(..., description="Base64-encoded file data or download URL")
    size_bytes: int = Field(..., description="File size in bytes")
    row_count: int = Field(..., description="Number of rows exported")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Export generation time"
    )


class ImportTemplate(BaseModel):
    """Import template definition."""

    entity_type: str = Field(..., description="Type of entity")
    format: ImportFormat = Field(..., description="Template format")
    required_fields: list[str] = Field(..., description="Required fields")
    optional_fields: list[str] = Field([], description="Optional fields")
    field_descriptions: dict[str, str] = Field({}, description="Field descriptions")
    example_data: list[dict] | None = Field(None, description="Example rows")


class ScheduleImportRequest(BaseModel):
    """Request for importing schedule data."""

    academic_year: str = Field(..., description="Academic year (e.g., '2024-2025')")
    format: ImportFormat = Field(..., description="Import format")
    data: str = Field(..., description="Import data")
    overwrite_existing: bool = Field(
        False, description="Overwrite existing assignments"
    )
    validate_acgme: bool = Field(True, description="Validate ACGME compliance")


class ScheduleExportRequest(BaseModel):
    """Request for exporting schedule data."""

    start_date: str = Field(..., description="Start date for export")
    end_date: str = Field(..., description="End date for export")
    format: ExportFormat = Field(..., description="Export format")
    include_person_details: bool = Field(True, description="Include person details")
    include_rotation_details: bool = Field(True, description="Include rotation details")
    group_by: str | None = Field(
        None, description="Group by field (person, date, rotation)"
    )

    @field_validator("group_by")
    @classmethod
    def validate_group_by(cls, v: str | None) -> str | None:
        """Validate group_by is valid."""
        if v is not None and v not in ("person", "date", "rotation"):
            raise ValueError("group_by must be 'person', 'date', or 'rotation'")
        return v


class PersonImportRow(BaseModel):
    """Schema for person import row."""

    name: str = Field(..., description="Person name")
    type: str = Field(..., description="Person type (resident, faculty)")
    email: str | None = Field(None, description="Email address")
    pgy_level: int | None = Field(None, description="PGY level (1-3)")
    faculty_role: str | None = Field(None, description="Faculty role")
    specialties: str | None = Field(None, description="Specialties (comma-separated)")
    primary_duty: str | None = Field(None, description="Primary duty")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate type is valid."""
        if v not in ("resident", "faculty"):
            raise ValueError("type must be 'resident' or 'faculty'")
        return v


class AssignmentImportRow(BaseModel):
    """Schema for assignment import row."""

    person_name: str = Field(..., description="Person name")
    date: str = Field(..., description="Assignment date (YYYY-MM-DD)")
    session: str = Field(..., description="Session (AM, PM)")
    rotation_name: str = Field(..., description="Rotation name")
    role: str = Field("primary", description="Assignment role")
    notes: str | None = Field(None, description="Assignment notes")

    @field_validator("session")
    @classmethod
    def validate_session(cls, v: str) -> str:
        """Validate session is valid."""
        v_upper = v.upper()
        if v_upper not in ("AM", "PM"):
            raise ValueError("session must be 'AM' or 'PM'")
        return v_upper

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is valid."""
        if v not in ("primary", "supervising", "backup"):
            raise ValueError("role must be 'primary', 'supervising', or 'backup'")
        return v
