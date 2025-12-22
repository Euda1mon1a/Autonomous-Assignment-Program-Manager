"""
API changelog endpoints.

Provides endpoints for:
- Generating changelogs between API versions
- Managing version history
- Detecting breaking changes
- Generating migration guides
- Suggesting semantic versions
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.changelog.differ import ChangeType
from app.changelog.formatter import OutputFormat
from app.changelog.generator import ChangelogGenerator
from app.schemas.changelog import (
    APIChangeDetail,
    APIDiffResponse,
    APIDiffSummary,
    ChangelogRequest,
    ChangelogResponse,
    ChangelogSchemaRequest,
    MigrationGuideRequest,
    MigrationGuideResponse,
    VersionInfo,
    VersionListResponse,
    VersionSaveRequest,
    VersionSaveResponse,
    VersionSuggestionRequest,
    VersionSuggestionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize changelog generator
# In production, configure storage path via environment variable
changelog_generator = ChangelogGenerator(storage_path="/tmp/api_versions")


@router.get("/versions", response_model=VersionListResponse)
async def list_versions() -> VersionListResponse:
    """
    List all stored API versions.

    Returns a list of all version snapshots stored in the system,
    sorted by date (newest first).

    Returns:
        VersionListResponse with list of versions

    Example Response:
        {
            "versions": [
                {
                    "version": "1.2.0",
                    "saved_at": "2024-01-15T10:30:00",
                    "metadata": {"author": "API Team"}
                },
                {
                    "version": "1.1.0",
                    "saved_at": "2024-01-10T09:00:00",
                    "metadata": {}
                }
            ],
            "count": 2
        }
    """
    versions = changelog_generator.list_versions()

    version_infos = [
        VersionInfo(
            version=v["version"],
            saved_at=v["saved_at"],
            metadata=v.get("metadata", {}),
        )
        for v in versions
    ]

    return VersionListResponse(
        versions=version_infos,
        count=len(version_infos),
    )


@router.post("/versions", response_model=VersionSaveResponse)
async def save_version(request: VersionSaveRequest) -> VersionSaveResponse:
    """
    Save a version snapshot.

    Stores an OpenAPI schema as a versioned snapshot for later comparison.
    If version is not provided, it will be auto-detected from the schema.

    Args:
        request: Version save request with schema and optional metadata

    Returns:
        VersionSaveResponse with saved version info

    Example Request:
        {
            "version": "1.2.0",
            "schema": {...OpenAPI schema...},
            "metadata": {"author": "API Team", "notes": "Added user endpoints"}
        }

    Example Response:
        {
            "version": "1.2.0",
            "message": "Version 1.2.0 saved successfully",
            "saved_at": "2024-01-15T10:30:00.000000"
        }
    """
    try:
        version = changelog_generator.save_current_version(
            current_schema=request.schema,
            version=request.version,
            metadata=request.metadata,
        )

        return VersionSaveResponse(
            version=version,
            message=f"Version {version} saved successfully",
            saved_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error saving version: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to save version snapshot",
        )


@router.post("/generate", response_model=ChangelogResponse)
async def generate_changelog(request: ChangelogRequest) -> ChangelogResponse:
    """
    Generate changelog from stored versions.

    Compares two stored version snapshots and generates a formatted changelog.
    Supports multiple output formats: markdown, json, html.

    Args:
        request: Changelog generation request

    Returns:
        ChangelogResponse with formatted changelog

    Raises:
        HTTPException: If versions not found or generation fails

    Example Request:
        {
            "old_version": "1.0.0",
            "new_version": "1.1.0",
            "output_format": "markdown",
            "include_migration_guide": true
        }

    Example Response:
        {
            "changelog": "# API Changelog...",
            "format": "markdown",
            "old_version": "1.0.0",
            "new_version": "1.1.0",
            "generated_at": "2024-01-15T10:30:00.000000"
        }
    """
    # Validate output format
    try:
        output_format = OutputFormat(request.output_format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format: {request.output_format}. "
            f"Valid formats: markdown, json, html",
        )

    # Generate changelog
    changelog = changelog_generator.generate_from_versions(
        old_version=request.old_version,
        new_version=request.new_version,
        output_format=output_format,
        include_migration_guide=request.include_migration_guide,
    )

    if changelog is None:
        raise HTTPException(
            status_code=404,
            detail=f"One or both versions not found: {request.old_version}, {request.new_version}",
        )

    return ChangelogResponse(
        changelog=changelog,
        format=request.output_format,
        old_version=request.old_version,
        new_version=request.new_version,
        generated_at=datetime.utcnow().isoformat(),
    )


@router.post("/generate/schemas", response_model=ChangelogResponse)
async def generate_changelog_from_schemas(
    request: ChangelogSchemaRequest,
) -> ChangelogResponse:
    """
    Generate changelog from raw OpenAPI schemas.

    Directly compares two OpenAPI schemas without requiring them to be stored.
    Useful for ad-hoc comparisons or CI/CD integration.

    Args:
        request: Request with old and new OpenAPI schemas

    Returns:
        ChangelogResponse with formatted changelog

    Example Request:
        {
            "old_schema": {
                "openapi": "3.0.0",
                "info": {"version": "1.0.0"},
                "paths": {...}
            },
            "new_schema": {
                "openapi": "3.0.0",
                "info": {"version": "1.1.0"},
                "paths": {...}
            },
            "output_format": "markdown",
            "include_migration_guide": true
        }
    """
    # Validate output format
    try:
        output_format = OutputFormat(request.output_format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format: {request.output_format}. "
            f"Valid formats: markdown, json, html",
        )

    try:
        changelog = changelog_generator.generate_changelog(
            old_schema=request.old_schema,
            new_schema=request.new_schema,
            output_format=output_format,
            include_migration_guide=request.include_migration_guide,
        )

        old_version = request.old_schema.get("info", {}).get("version", "unknown")
        new_version = request.new_schema.get("info", {}).get("version", "unknown")

        return ChangelogResponse(
            changelog=changelog,
            format=request.output_format,
            old_version=old_version,
            new_version=new_version,
            generated_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error generating changelog: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate changelog",
        )


@router.post("/diff", response_model=APIDiffResponse)
async def get_api_diff(request: ChangelogRequest) -> APIDiffResponse:
    """
    Get structured diff between two versions.

    Returns a structured representation of all changes between two API versions,
    including breaking change detection and semantic version suggestion.

    Args:
        request: Request with version identifiers

    Returns:
        APIDiffResponse with structured change data

    Example Response:
        {
            "old_version": "1.0.0",
            "new_version": "1.1.0",
            "suggested_version": "1.1.0",
            "summary": {
                "total_changes": 5,
                "breaking_changes": 1,
                "non_breaking_changes": 4,
                "has_breaking_changes": true
            },
            "changes": [...]
        }
    """
    # Load versions
    old_data = changelog_generator.version_history.load_version(request.old_version)
    new_data = changelog_generator.version_history.load_version(request.new_version)

    if not old_data:
        raise HTTPException(
            status_code=404,
            detail=f"Old version not found: {request.old_version}",
        )

    if not new_data:
        raise HTTPException(
            status_code=404,
            detail=f"New version not found: {request.new_version}",
        )

    # Get diff
    diff = changelog_generator.get_diff(
        old_data["schema"],
        new_data["schema"],
    )

    # Convert to response format
    changes = [
        APIChangeDetail(
            type=change.change_type.value,
            path=change.path,
            method=change.method,
            description=change.description,
            breaking=change.breaking,
            old_value=change.old_value,
            new_value=change.new_value,
            migration_guide=change.migration_guide,
        )
        for change in diff.changes
    ]

    summary = APIDiffSummary(
        total_changes=len(diff.changes),
        breaking_changes=len(diff.breaking_changes),
        non_breaking_changes=len(diff.non_breaking_changes),
        has_breaking_changes=diff.has_breaking_changes,
    )

    return APIDiffResponse(
        old_version=diff.old_version,
        new_version=diff.new_version,
        suggested_version=diff.suggest_version_bump(diff.old_version),
        generated_at=datetime.utcnow().isoformat(),
        summary=summary,
        changes=changes,
    )


@router.post("/migration-guide", response_model=MigrationGuideResponse)
async def generate_migration_guide(
    request: MigrationGuideRequest,
) -> MigrationGuideResponse:
    """
    Generate detailed migration guide.

    Creates a comprehensive migration guide for breaking changes between
    two API versions. Includes step-by-step instructions and testing recommendations.

    Args:
        request: Request with version identifiers

    Returns:
        MigrationGuideResponse with Markdown-formatted guide

    Example Response:
        {
            "migration_guide": "# Migration Guide\\n\\n...",
            "old_version": "1.0.0",
            "new_version": "2.0.0",
            "breaking_changes_count": 3,
            "generated_at": "2024-01-15T10:30:00.000000"
        }
    """
    # Load versions
    old_data = changelog_generator.version_history.load_version(request.old_version)
    new_data = changelog_generator.version_history.load_version(request.new_version)

    if not old_data:
        raise HTTPException(
            status_code=404,
            detail=f"Old version not found: {request.old_version}",
        )

    if not new_data:
        raise HTTPException(
            status_code=404,
            detail=f"New version not found: {request.new_version}",
        )

    # Generate migration guide
    migration_guide = changelog_generator.generate_migration_guide(
        old_data["schema"],
        new_data["schema"],
    )

    # Count breaking changes
    diff = changelog_generator.get_diff(
        old_data["schema"],
        new_data["schema"],
    )

    return MigrationGuideResponse(
        migration_guide=migration_guide,
        old_version=request.old_version,
        new_version=request.new_version,
        breaking_changes_count=len(diff.breaking_changes),
        generated_at=datetime.utcnow().isoformat(),
    )


@router.post("/suggest-version", response_model=VersionSuggestionResponse)
async def suggest_version(
    request: VersionSuggestionRequest,
) -> VersionSuggestionResponse:
    """
    Suggest next version number using semantic versioning.

    Analyzes changes between two versions and suggests the appropriate
    next version number based on semantic versioning rules:
    - Major bump (x.0.0): Breaking changes
    - Minor bump (0.x.0): New features (non-breaking)
    - Patch bump (0.0.x): Bug fixes and patches

    Args:
        request: Request with version identifiers

    Returns:
        VersionSuggestionResponse with suggested version and reasoning

    Example Response:
        {
            "current_version": "1.0.0",
            "suggested_version": "2.0.0",
            "reason": "Breaking changes detected",
            "breaking_changes": 2,
            "new_features": 3,
            "patch_changes": 1
        }
    """
    # Load versions
    old_data = changelog_generator.version_history.load_version(request.old_version)
    new_data = changelog_generator.version_history.load_version(request.new_version)

    if not old_data:
        raise HTTPException(
            status_code=404,
            detail=f"Old version not found: {request.old_version}",
        )

    if not new_data:
        raise HTTPException(
            status_code=404,
            detail=f"New version not found: {request.new_version}",
        )

    # Get suggestion
    suggested = changelog_generator.suggest_version(
        old_data["schema"],
        new_data["schema"],
    )

    # Get detailed change counts
    diff = changelog_generator.get_diff(
        old_data["schema"],
        new_data["schema"],
    )

    breaking_count = len(diff.breaking_changes)
    new_features_count = len([
        c for c in diff.changes
        if c.change_type in {
            ChangeType.ENDPOINT_ADDED,
            ChangeType.ENDPOINT_METHOD_ADDED,
            ChangeType.OPTIONAL_PARAM_ADDED,
        }
    ])
    patch_count = len([
        c for c in diff.changes
        if c.change_type in {
            ChangeType.DESCRIPTION_CHANGED,
            ChangeType.EXAMPLE_CHANGED,
        }
    ])

    # Determine reason
    if breaking_count > 0:
        reason = "Breaking changes detected"
    elif new_features_count > 0:
        reason = "New features added (non-breaking)"
    elif patch_count > 0:
        reason = "Documentation or patch-level changes"
    else:
        reason = "No significant changes detected"

    return VersionSuggestionResponse(
        current_version=request.old_version,
        suggested_version=suggested,
        reason=reason,
        breaking_changes=breaking_count,
        new_features=new_features_count,
        patch_changes=patch_count,
    )


@router.get("/current")
async def get_current_schema(request: Request) -> dict[str, Any]:
    """
    Get current OpenAPI schema.

    Returns the current application's OpenAPI schema, which can be used
    for comparison or saved as a version snapshot.

    Returns:
        Current OpenAPI schema

    Example Response:
        {
            "openapi": "3.0.0",
            "info": {
                "title": "Residency Scheduler API",
                "version": "1.0.0"
            },
            "paths": {...}
        }
    """
    # Get current OpenAPI schema from the FastAPI app
    app = request.app
    return app.openapi()


@router.delete("/versions/{version}")
async def delete_version(version: str) -> dict[str, str]:
    """
    Delete a version snapshot.

    Permanently removes a stored version snapshot. This action cannot be undone.

    Args:
        version: Version identifier to delete

    Returns:
        Confirmation message

    Raises:
        HTTPException: If version not found

    Example Response:
        {
            "message": "Version 1.0.0 deleted successfully"
        }
    """
    deleted = changelog_generator.version_history.delete_version(version)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Version not found: {version}",
        )

    return {"message": f"Version {version} deleted successfully"}
