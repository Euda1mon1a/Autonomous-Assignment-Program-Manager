"""Pydantic schemas for changelog API."""

from typing import Any

from pydantic import BaseModel, Field


class ChangelogRequest(BaseModel):
    """Request to generate changelog between two versions."""

    old_version: str = Field(..., description="Previous version identifier")
    new_version: str = Field(..., description="New version identifier")
    output_format: str = Field(
        default="markdown",
        description="Output format: markdown, json, or html",
    )
    include_migration_guide: bool = Field(
        default=True,
        description="Include migration guide for breaking changes",
    )


class ChangelogSchemaRequest(BaseModel):
    """Request to generate changelog from raw OpenAPI schemas."""

    old_schema: dict[str, Any] = Field(..., description="Previous OpenAPI schema")
    new_schema: dict[str, Any] = Field(..., description="New OpenAPI schema")
    output_format: str = Field(
        default="markdown",
        description="Output format: markdown, json, or html",
    )
    include_migration_guide: bool = Field(
        default=True,
        description="Include migration guide for breaking changes",
    )


class VersionSaveRequest(BaseModel):
    """Request to save a version snapshot."""

    version: str | None = Field(
        default=None,
        description="Version identifier (auto-detected from schema if not provided)",
    )
    schema: dict[str, Any] = Field(..., description="OpenAPI schema to save")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata",
    )


class VersionInfo(BaseModel):
    """Information about a stored API version."""

    version: str = Field(..., description="Version identifier")
    saved_at: str = Field(..., description="ISO timestamp when version was saved")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class VersionListResponse(BaseModel):
    """Response containing list of stored versions."""

    versions: list[VersionInfo] = Field(..., description="List of stored versions")
    count: int = Field(..., description="Total number of versions")


class VersionSaveResponse(BaseModel):
    """Response after saving a version."""

    version: str = Field(..., description="Version identifier that was saved")
    message: str = Field(..., description="Success message")
    saved_at: str = Field(..., description="ISO timestamp when saved")


class ChangelogResponse(BaseModel):
    """Response containing generated changelog."""

    changelog: str = Field(..., description="Formatted changelog content")
    format: str = Field(..., description="Output format used")
    old_version: str = Field(..., description="Previous version")
    new_version: str = Field(..., description="New version")
    generated_at: str = Field(..., description="ISO timestamp when generated")


class APIChangeDetail(BaseModel):
    """Details of a single API change."""

    type: str = Field(..., description="Change type")
    path: str = Field(..., description="API endpoint path")
    method: str | None = Field(None, description="HTTP method")
    description: str = Field(..., description="Human-readable description")
    breaking: bool = Field(..., description="Whether this is a breaking change")
    old_value: Any = Field(None, description="Previous value")
    new_value: Any = Field(None, description="New value")
    migration_guide: str | None = Field(
        None,
        description="Migration instructions",
    )


class APIDiffSummary(BaseModel):
    """Summary of API differences."""

    total_changes: int = Field(..., description="Total number of changes")
    breaking_changes: int = Field(..., description="Number of breaking changes")
    non_breaking_changes: int = Field(
        ...,
        description="Number of non-breaking changes",
    )
    has_breaking_changes: bool = Field(
        ...,
        description="Whether any breaking changes exist",
    )


class APIDiffResponse(BaseModel):
    """Response containing structured API diff."""

    old_version: str = Field(..., description="Previous version")
    new_version: str = Field(..., description="New version")
    suggested_version: str = Field(
        ...,
        description="Suggested next version (semantic versioning)",
    )
    generated_at: str = Field(..., description="ISO timestamp when generated")
    summary: APIDiffSummary = Field(..., description="Summary statistics")
    changes: list[APIChangeDetail] = Field(..., description="List of all changes")


class MigrationGuideRequest(BaseModel):
    """Request to generate migration guide."""

    old_version: str = Field(..., description="Previous version identifier")
    new_version: str = Field(..., description="New version identifier")


class MigrationGuideResponse(BaseModel):
    """Response containing migration guide."""

    migration_guide: str = Field(..., description="Markdown-formatted migration guide")
    old_version: str = Field(..., description="Previous version")
    new_version: str = Field(..., description="New version")
    breaking_changes_count: int = Field(
        ...,
        description="Number of breaking changes",
    )
    generated_at: str = Field(..., description="ISO timestamp when generated")


class VersionSuggestionRequest(BaseModel):
    """Request for version number suggestion."""

    old_version: str = Field(..., description="Previous version identifier")
    new_version: str = Field(..., description="New version identifier")


class VersionSuggestionResponse(BaseModel):
    """Response with version suggestion."""

    current_version: str = Field(..., description="Current version")
    suggested_version: str = Field(
        ...,
        description="Suggested next version (semantic versioning)",
    )
    reason: str = Field(..., description="Reason for suggestion")
    breaking_changes: int = Field(..., description="Number of breaking changes")
    new_features: int = Field(..., description="Number of new features")
    patch_changes: int = Field(..., description="Number of patch-level changes")
