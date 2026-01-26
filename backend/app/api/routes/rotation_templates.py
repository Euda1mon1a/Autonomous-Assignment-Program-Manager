"""Rotation template API routes.

Provides endpoints for:
- CRUD operations on rotation templates
- Batch operations (delete, update, create, archive, restore)
- Weekly pattern management (GET/PUT for patterns)
- Rotation preference management (GET/PUT for preferences)
- Export and conflict detection

IMPORTANT: Route order matters in FastAPI. Specific paths like "/batch" must be
defined BEFORE parametric paths like "/{template_id}" to avoid path conflicts.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.schemas.rotation_template import (
    BatchArchiveRequest,
    BatchRestoreRequest,
    BatchTemplateCreateRequest,
    BatchTemplateDeleteRequest,
    BatchTemplateResponse,
    BatchTemplateUpdateRequest,
    ConflictCheckRequest,
    ConflictCheckResponse,
    RotationTemplateCreate,
    RotationTemplateListResponse,
    RotationTemplateResponse,
    RotationTemplateUpdate,
    TemplateConflict,
    TemplateExportRequest,
    TemplateExportResponse,
    TemplateExportData,
)
from app.schemas.rotation_template_gui import (
    BatchPatternUpdateRequest,
    BatchPatternUpdateResponse,
    HalfDayRequirementCreate,
    HalfDayRequirementResponse,
    RotationPreferenceCreate,
    RotationPreferenceResponse,
    WeeklyGridUpdate,
    WeeklyPatternResponse,
)
from app.schemas.activity import (
    ActivityRequirementCreate,
    ActivityRequirementResponse,
)
from app.services.rotation_template_service import RotationTemplateService
from app.services.activity_service import ActivityService

router = APIRouter()


# =============================================================================
# Collection-level endpoints (no path parameters)
# These MUST come before parametric routes to avoid path conflicts
# =============================================================================


@router.get("", response_model=RotationTemplateListResponse)
async def list_rotation_templates(
    activity_type: str | None = Query(
        None, description="Filter by rotation category (activity_type)"
    ),
    include_archived: bool = Query(
        False, description="Include archived templates in results"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RotationTemplateListResponse:
    """List all rotation templates, optionally filtered by rotation category.

    By default, archived templates are excluded. Use include_archived=true to see all templates.

    Args:
        activity_type: Filter by rotation category (e.g., 'clinic', 'inpatient')
        include_archived: Include archived templates (default: False)
        db: Database session
        current_user: Current authenticated user

    Returns:
        RotationTemplateListResponse with filtered templates
    """
    query = select(RotationTemplate)

    # Exclude archived templates by default
    if not include_archived:
        query = query.where(RotationTemplate.is_archived == False)

    if activity_type:
        query = query.where(RotationTemplate.activity_type == activity_type)

    query = query.order_by(RotationTemplate.name)
    result = db.execute(query)
    templates = list(result.scalars().all())
    return RotationTemplateListResponse(
        items=[RotationTemplateResponse.model_validate(t) for t in templates],
        total=len(templates),
    )


@router.post("", response_model=RotationTemplateResponse, status_code=201)
async def create_rotation_template(
    template_in: RotationTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RotationTemplate:
    """Create a new rotation template. Requires authentication."""
    template = RotationTemplate(**template_in.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


# =============================================================================
# Batch Operation Endpoints
# These MUST come before /{template_id} routes to avoid path conflicts
# =============================================================================


@router.delete("/batch", response_model=BatchTemplateResponse)
async def batch_delete_rotation_templates(
    request: BatchTemplateDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchTemplateResponse:
    """Delete multiple rotation templates atomically.

    Features:
    - Delete up to 100 templates at once
    - Dry-run mode for validation without deleting
    - Atomic operation (all or nothing)

    Args:
        request: BatchTemplateDeleteRequest with list of template IDs
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchTemplateResponse with operation results

    Raises:
        HTTPException: 400 if any template not found

    Example:
        ```json
        {
          "template_ids": ["uuid1", "uuid2", "uuid3"],
          "dry_run": false
        }
        ```
    """
    service = RotationTemplateService(db)

    try:
        result = await service.batch_delete(request.template_ids, request.dry_run)

        # If any failed, return 400
        if result["failed"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch delete operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        await service.commit()
        return BatchTemplateResponse(**result)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/batch", response_model=BatchTemplateResponse)
async def batch_update_rotation_templates(
    request: BatchTemplateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchTemplateResponse:
    """Update multiple rotation templates atomically.

    Features:
    - Update up to 100 templates at once
    - Each template can have different update values
    - Dry-run mode for validation without updating
    - Atomic operation (all or nothing)

    Args:
        request: BatchTemplateUpdateRequest with list of template updates
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchTemplateResponse with operation results

    Raises:
        HTTPException: 400 if any template not found or validation fails

    Example:
        ```json
        {
          "templates": [
            {
              "template_id": "uuid1",
              "updates": {"max_residents": 5, "supervision_required": true}
            },
            {
              "template_id": "uuid2",
              "updates": {"activity_type": "inpatient"}
            }
          ],
          "dry_run": false
        }
        ```
    """
    service = RotationTemplateService(db)

    try:
        # Convert request to dict format expected by service
        updates = [
            {
                "template_id": item.template_id,
                "updates": item.updates.model_dump(exclude_unset=True),
            }
            for item in request.templates
        ]

        result = await service.batch_update(updates, request.dry_run)

        # If any failed, return 400
        if result["failed"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch update operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        await service.commit()
        return BatchTemplateResponse(**result)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch", response_model=BatchTemplateResponse, status_code=201)
async def batch_create_rotation_templates(
    request: BatchTemplateCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchTemplateResponse:
    """Create multiple rotation templates atomically.

    Features:
    - Create up to 100 templates at once
    - Each template validated independently
    - Checks for duplicate names in batch and database
    - Dry-run mode for validation without creating
    - Atomic operation (all or nothing)

    Args:
        request: BatchTemplateCreateRequest with list of templates
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchTemplateResponse with operation results and created_ids

    Raises:
        HTTPException: 400 if validation fails or duplicates found

    Example:
        ```json
        {
          "templates": [
            {"name": "New Clinic", "activity_type": "clinic"},
            {"name": "New Inpatient", "activity_type": "inpatient"}
          ],
          "dry_run": false
        }
        ```
    """
    service = RotationTemplateService(db)

    try:
        # Convert Pydantic models to dicts
        templates_data = [t.model_dump() for t in request.templates]

        result = await service.batch_create(templates_data, request.dry_run)

        # If any failed, return 400
        if result["failed"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch create operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        await service.commit()
        return BatchTemplateResponse(**result)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/conflicts", response_model=ConflictCheckResponse)
async def check_batch_conflicts(
    request: ConflictCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConflictCheckResponse:
    """Check for conflicts before performing batch operations.

    Useful for preview before destructive operations like delete or archive.
    Checks for:
    - Existing assignments referencing templates
    - Related patterns/preferences that would be affected

    Args:
        request: ConflictCheckRequest with template IDs and operation type
        db: Database session
        current_user: Current authenticated user

    Returns:
        ConflictCheckResponse with list of conflicts and can_proceed flag
    """
    service = RotationTemplateService(db)

    result = await service.check_conflicts(request.template_ids, request.operation)

    return ConflictCheckResponse(
        has_conflicts=result["has_conflicts"],
        conflicts=[TemplateConflict(**c) for c in result["conflicts"]],
        can_proceed=result["can_proceed"],
    )


@router.post("/export", response_model=TemplateExportResponse)
async def export_rotation_templates(
    request: TemplateExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TemplateExportResponse:
    """Export rotation templates with their patterns and preferences.

    Creates a JSON export suitable for backup or transfer to another system.

    Args:
        request: TemplateExportRequest with template IDs and options
        db: Database session
        current_user: Current authenticated user

    Returns:
        TemplateExportResponse with template data, patterns, and preferences
    """
    from datetime import datetime

    service = RotationTemplateService(db)

    result = await service.export_templates(
        request.template_ids,
        request.include_patterns,
        request.include_preferences,
    )

    return TemplateExportResponse(
        templates=[
            TemplateExportData(
                template=t["template"],
                patterns=t.get("patterns"),
                preferences=t.get("preferences"),
            )
            for t in result["templates"]
        ],
        exported_at=datetime.fromisoformat(result["exported_at"]),
        total=result["total"],
    )


@router.put("/batch/archive", response_model=BatchTemplateResponse)
async def batch_archive_rotation_templates(
    request: BatchArchiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchTemplateResponse:
    """Archive multiple rotation templates atomically (soft delete).

    Features:
    - Archive up to 100 templates at once
    - Dry-run mode for validation without archiving
    - Atomic operation (all or nothing)
    - Archived templates excluded from default queries

    Args:
        request: BatchArchiveRequest with list of template IDs
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchTemplateResponse with operation results

    Raises:
        HTTPException: 400 if any template not found or already archived
    """
    service = RotationTemplateService(db)

    try:
        result = await service.batch_archive(
            request.template_ids, str(current_user.id), request.dry_run
        )

        # If any failed, return 400
        if result["failed"] > 0:
            # Convert UUIDs to strings for JSON serialization
            serializable_results = [
                {
                    "index": r["index"],
                    "template_id": str(r["template_id"]),
                    "success": r["success"],
                    "error": r.get("error"),
                }
                for r in result["results"]
            ]
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch archive operation failed",
                    "failed": result["failed"],
                    "results": serializable_results,
                },
            )

        await service.commit()
        return BatchTemplateResponse(**result)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/batch/restore", response_model=BatchTemplateResponse)
async def batch_restore_rotation_templates(
    request: BatchRestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchTemplateResponse:
    """Restore multiple archived rotation templates atomically.

    Features:
    - Restore up to 100 templates at once
    - Dry-run mode for validation without restoring
    - Atomic operation (all or nothing)
    - Restored templates visible in default queries

    Args:
        request: BatchRestoreRequest with list of template IDs
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchTemplateResponse with operation results

    Raises:
        HTTPException: 400 if any template not found or not archived
    """
    service = RotationTemplateService(db)

    try:
        result = await service.batch_restore(request.template_ids, request.dry_run)

        # If any failed, return 400
        if result["failed"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch restore operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        await service.commit()
        return BatchTemplateResponse(**result)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/batch/patterns", response_model=BatchPatternUpdateResponse)
async def batch_update_patterns(
    request: BatchPatternUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchPatternUpdateResponse:
    """Bulk update weekly patterns across multiple templates.

    Supports two modes:
    - **overlay**: Only modifies specified slots, leaves others unchanged.
      Use this to add/change specific slots (e.g., "Add Academics to Wed PM").
    - **replace**: Replaces entire pattern with the provided slots.
      Use this to set a complete new pattern.

    Week targeting allows applying changes to specific weeks (1-4) or all weeks.

    Features:
    - Update patterns on up to 100 templates at once
    - Dry-run mode for validation without updating
    - Week-specific targeting
    - Atomic operation (all or nothing)

    Args:
        request: BatchPatternUpdateRequest with:
            - template_ids: List of template UUIDs to update
            - mode: "overlay" or "replace"
            - slots: List of BatchPatternSlot to apply
            - week_numbers: Optional list of weeks (1-4) to target
            - dry_run: Optional boolean (default False)
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchPatternUpdateResponse with operation results

    Raises:
        HTTPException: 400 if validation fails or templates not found

    Example (Overlay - add Academics to Wed PM for weeks 1-3):
        ```json
        {
          "template_ids": ["uuid1", "uuid2", "uuid3"],
          "mode": "overlay",
          "slots": [
            {"day_of_week": 3, "time_of_day": "PM", "linked_template_id": "academics-uuid"}
          ],
          "week_numbers": [1, 2, 3],
          "dry_run": false
        }
        ```
    """
    service = RotationTemplateService(db)

    try:
        result = await service.batch_update_weekly_patterns(
            template_ids=request.template_ids,
            mode=request.mode,
            slots=[slot.model_dump() for slot in request.slots],
            week_numbers=request.week_numbers,
            dry_run=request.dry_run,
        )

        # If any failed, return 400
        if result["failed"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch pattern update operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        if not request.dry_run:
            await service.commit()

        return BatchPatternUpdateResponse(**result, dry_run=request.dry_run)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/batch/preferences", response_model=BatchTemplateResponse)
async def batch_apply_preferences(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BatchTemplateResponse:
    """Apply the same preferences to multiple templates atomically.

    Useful for bulk operations like applying standard preference
    configurations to all templates of a certain type.

    Features:
    - Apply preferences to up to 100 templates at once
    - Dry-run mode for validation without updating
    - Atomic operation (all or nothing)
    - Preference validation before application

    Args:
        request: Dict with:
            - template_ids: List of template UUIDs
            - preferences: List of RotationPreferenceCreate
            - dry_run: Optional boolean (default False)
        db: Database session
        current_user: Current authenticated user

    Returns:
        BatchTemplateResponse with operation results

    Raises:
        HTTPException: 400 if validation fails or templates not found
    """
    from app.schemas.rotation_template_gui import RotationPreferenceCreate

    service = RotationTemplateService(db)

    try:
        # Parse request
        template_ids = [UUID(tid) for tid in request.get("template_ids", [])]
        preferences_data = request.get("preferences", [])
        dry_run = request.get("dry_run", False)

        # Convert preferences to Pydantic models
        preferences = [RotationPreferenceCreate(**p) for p in preferences_data]

        result = await service.batch_apply_preferences(
            template_ids, preferences, dry_run
        )

        # If any failed, return 400
        if result["failed"] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Batch apply preferences operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        await service.commit()
        return BatchTemplateResponse(**result)

    except HTTPException:
        await service.rollback()
        raise
    except Exception as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Single Template Endpoints (parametric paths)
# These MUST come after /batch routes to avoid path conflicts
# =============================================================================


@router.get("/{template_id}", response_model=RotationTemplateResponse)
async def get_rotation_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RotationTemplateResponse:
    """Get a rotation template by ID. Requires authentication."""
    template = (
        db.execute(select(RotationTemplate).where(RotationTemplate.id == template_id))
    ).scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")
    return template


@router.put("/{template_id}/archive", response_model=RotationTemplateResponse)
async def archive_rotation_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RotationTemplateResponse:
    """Archive a rotation template (soft delete).

    Archived templates are excluded from default queries but can be
    restored later. Use this instead of hard delete to preserve data.

    Args:
        template_id: UUID of the rotation template
        db: Database session
        current_user: Current authenticated user

    Returns:
        Archived RotationTemplateResponse

    Raises:
        404: Template not found
        400: Template already archived
    """
    service = RotationTemplateService(db)

    try:
        template = await service.archive_template(template_id, str(current_user.id))
        await service.commit()
        return template
    except ValueError as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{template_id}/restore", response_model=RotationTemplateResponse)
async def restore_rotation_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RotationTemplateResponse:
    """Restore an archived rotation template.

    Restores a previously archived template, making it visible
    in default queries again.

    Args:
        template_id: UUID of the rotation template
        db: Database session
        current_user: Current authenticated user

    Returns:
        Restored RotationTemplateResponse

    Raises:
        404: Template not found
        400: Template not archived
    """
    service = RotationTemplateService(db)

    try:
        template = await service.restore_template(template_id)
        await service.commit()
        return template
    except ValueError as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{template_id}/history")
async def get_rotation_template_history(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get version history for a rotation template.

    Returns all historical versions of the template tracked by SQLAlchemy-Continuum.
    Each version includes:
    - Version number (transaction_id)
    - Timestamp (transaction.issued_at)
    - User who made the change (transaction.user_id)
    - Changed fields (modified properties)

    Args:
        template_id: UUID of the rotation template
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of version history entries

    Raises:
        404: Template not found
    """
    service = RotationTemplateService(db)

    # Verify template exists
    template = await service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    # Get version history
    # Note: This requires the template to have __versioned__ = {} in the model
    versions = []
    try:
        # Access versions relationship created by SQLAlchemy-Continuum
        if hasattr(template, "versions"):
            for version in template.versions:
                version_data = {
                    "version_id": version.transaction_id,
                    "timestamp": version.transaction.issued_at.isoformat()
                    if version.transaction.issued_at
                    else None,
                    "user_id": version.transaction.user_id
                    if hasattr(version.transaction, "user_id")
                    else None,
                    "operation_type": version.operation_type
                    if hasattr(version, "operation_type")
                    else None,
                    "changed_fields": version.changeset
                    if hasattr(version, "changeset")
                    else {},
                }
                versions.append(version_data)
    except Exception as e:
        # If versioning not configured or error accessing versions
        logger = get_logger(__name__)
        logger.warning(
            f"Error accessing version history for template {template_id}: {str(e)}"
        )
        versions = []

    return {
        "template_id": str(template_id),
        "template_name": template.name,
        "version_count": len(versions),
        "versions": versions,
    }


@router.put("/{template_id}", response_model=RotationTemplateResponse)
async def update_rotation_template(
    template_id: UUID,
    template_in: RotationTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RotationTemplateResponse:
    """Update an existing rotation template. Requires authentication."""
    template = (
        db.execute(select(RotationTemplate).where(RotationTemplate.id == template_id))
    ).scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=204)
async def delete_rotation_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a rotation template. Requires authentication."""
    template = (
        db.execute(select(RotationTemplate).where(RotationTemplate.id == template_id))
    ).scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    db.delete(template)
    db.commit()


# =============================================================================
# Weekly Pattern Endpoints
# =============================================================================


@router.get("/{template_id}/patterns", response_model=list[WeeklyPatternResponse])
async def get_weekly_patterns(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list:
    """Get all weekly patterns for a rotation template.

    Returns the 7x2 weekly grid of AM/PM slots defining the rotation pattern.
    Each pattern includes day of week, time of day, and assigned activity type.

    Args:
        template_id: UUID of the rotation template

    Returns:
        List of WeeklyPatternResponse with all patterns for the template

    Raises:
        404: Template not found
    """
    service = RotationTemplateService(db)

    # Verify template exists
    template = await service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    patterns = await service.get_patterns_by_template_id(template_id)
    return patterns


@router.put("/{template_id}/patterns", response_model=list[WeeklyPatternResponse])
async def replace_weekly_patterns(
    template_id: UUID,
    grid_update: WeeklyGridUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list:
    """Atomically replace all weekly patterns for a rotation template.

    This endpoint performs an atomic replacement:
    1. Deletes all existing patterns for the template
    2. Creates new patterns from the provided list
    3. Returns the newly created patterns

    Use this for the visual grid editor to save the entire pattern at once.

    Args:
        template_id: UUID of the rotation template
        grid_update: WeeklyGridUpdate with list of patterns (max 14)

    Returns:
        List of newly created WeeklyPatternResponse

    Raises:
        404: Template not found
        400: Validation error (duplicate slots, invalid data)
    """
    service = RotationTemplateService(db)

    try:
        patterns = await service.replace_patterns(template_id, grid_update.patterns)
        await service.commit()
        return patterns
    except ValueError as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Half-Day Requirement Endpoints
# =============================================================================


@router.get(
    "/{template_id}/halfday-requirements",
    response_model=HalfDayRequirementResponse | None,
)
async def get_halfday_requirements(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get half-day requirements for a rotation template.

    Returns the activity distribution requirements that the solver uses to
    determine how many half-days should be allocated to each activity type
    (FM clinic, specialty, academics, elective).

    Args:
        template_id: UUID of the rotation template

    Returns:
        HalfDayRequirementResponse or null if not configured

    Raises:
        404: Template not found
    """
    service = RotationTemplateService(db)

    # Verify template exists
    template = await service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    requirements = await service.get_halfday_requirements(template_id)
    return requirements


@router.put(
    "/{template_id}/halfday-requirements",
    response_model=HalfDayRequirementResponse,
)
async def upsert_halfday_requirements(
    template_id: UUID,
    requirements: HalfDayRequirementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create or update half-day requirements for a rotation template.

    This endpoint creates new requirements if none exist, or updates existing ones.
    The requirements define how many half-days should be allocated to each
    activity type per 4-week block.

    Example: Neurology Elective might have:
    - fm_clinic_halfdays: 4
    - specialty_halfdays: 5
    - academics_halfdays: 1
    - Total: 10 half-days per block

    Args:
        template_id: UUID of the rotation template
        requirements: HalfDayRequirementCreate with distribution settings

    Returns:
        HalfDayRequirementResponse with created/updated requirements

    Raises:
        404: Template not found
        400: Validation error
    """
    service = RotationTemplateService(db)

    # Verify template exists
    template = await service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    try:
        result = await service.upsert_halfday_requirements(template_id, requirements)
        await service.commit()
        return result
    except ValueError as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Rotation Preference Endpoints
# =============================================================================


@router.get(
    "/{template_id}/preferences", response_model=list[RotationPreferenceResponse]
)
async def get_rotation_preferences(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all scheduling preferences for a rotation template.

    Preferences are soft constraints that guide the scheduling optimizer.
    Each preference has a type, weight (low/medium/high/required), and
    optional configuration parameters.

    Args:
        template_id: UUID of the rotation template

    Returns:
        List of RotationPreferenceResponse with all preferences

    Raises:
        404: Template not found
    """
    service = RotationTemplateService(db)

    # Verify template exists
    template = await service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    preferences = await service.get_preferences_by_template_id(template_id)
    return preferences


@router.put(
    "/{template_id}/preferences", response_model=list[RotationPreferenceResponse]
)
async def replace_rotation_preferences(
    template_id: UUID,
    preferences: list[RotationPreferenceCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Atomically replace all preferences for a rotation template.

    This endpoint performs an atomic replacement:
    1. Deletes all existing preferences for the template
    2. Creates new preferences from the provided list
    3. Returns the newly created preferences

    Valid preference types:
    - full_day_grouping: Prefer AM+PM of same activity
    - consecutive_specialty: Group specialty sessions
    - avoid_isolated: Avoid single orphaned half-day sessions
    - preferred_days: Prefer specific activities on specific days
    - avoid_friday_pm: Keep Friday PM open as travel buffer
    - balance_weekly: Distribute activities evenly

    Args:
        template_id: UUID of the rotation template
        preferences: List of RotationPreferenceCreate

    Returns:
        List of newly created RotationPreferenceResponse

    Raises:
        404: Template not found
        400: Validation error (invalid type, duplicate types, etc.)
    """
    service = RotationTemplateService(db)

    try:
        new_preferences = await service.replace_preferences(template_id, preferences)
        await service.commit()
        return new_preferences
    except ValueError as e:
        await service.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Activity Requirement Endpoints (Dynamic per-activity requirements)
# =============================================================================


@router.get(
    "/{template_id}/activity-requirements",
    response_model=list[ActivityRequirementResponse],
)
async def get_activity_requirements(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all activity requirements for a rotation template.

    Activity requirements define how many half-days of each activity
    should be scheduled per block. Includes soft constraints like
    priority, min/max, preferred days, etc.

    Args:
        template_id: UUID of the rotation template

    Returns:
        List of ActivityRequirementResponse with activity details

    Raises:
        404: Template not found
    """
    activity_service = ActivityService(db)
    template_service = RotationTemplateService(db)

    # Verify template exists
    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    requirements = await activity_service.list_requirements_for_template(template_id)
    return [ActivityRequirementResponse.model_validate(r) for r in requirements]


@router.put(
    "/{template_id}/activity-requirements",
    response_model=list[ActivityRequirementResponse],
)
async def replace_activity_requirements(
    template_id: UUID,
    requirements: list[ActivityRequirementCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Atomically replace all activity requirements for a rotation template.

    This endpoint performs an atomic replacement:
    1. Deletes all existing requirements for the template
    2. Creates new requirements from the provided list
    3. Returns the newly created requirements

    Each requirement specifies:
    - activity_id: Which activity (FM Clinic, Specialty, LEC, etc.)
    - min_halfdays: Minimum half-days required
    - max_halfdays: Maximum half-days allowed
    - target_halfdays: Preferred count (for soft optimization)
    - applicable_weeks: [1,2,3,4] or null for all weeks
    - priority: 0-100 (higher = more important)
    - prefer_full_days, preferred_days, avoid_days: Scheduling preferences

    Args:
        template_id: UUID of the rotation template
        requirements: List of ActivityRequirementCreate

    Returns:
        List of newly created ActivityRequirementResponse

    Raises:
        404: Template not found
        400: Validation error (invalid activity, etc.)
    """
    activity_service = ActivityService(db)

    try:
        new_requirements = await activity_service.update_requirements_bulk(
            template_id, requirements
        )
        db.commit()
        return [ActivityRequirementResponse.model_validate(r) for r in new_requirements]
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{template_id}/activity-requirements",
    response_model=ActivityRequirementResponse,
    status_code=201,
)
async def add_activity_requirement(
    template_id: UUID,
    requirement: ActivityRequirementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a single activity requirement to a rotation template.

    Use this to add a new activity requirement without replacing all existing ones.

    Args:
        template_id: UUID of the rotation template
        requirement: ActivityRequirementCreate data

    Returns:
        Created ActivityRequirementResponse

    Raises:
        404: Template or activity not found
        400: Duplicate requirement or validation error
    """
    activity_service = ActivityService(db)

    try:
        new_requirement = await activity_service.create_requirement(
            template_id, requirement
        )
        db.commit()
        return ActivityRequirementResponse.model_validate(new_requirement)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{template_id}/activity-requirements/{requirement_id}",
    status_code=204,
)
async def delete_activity_requirement(
    template_id: UUID,
    requirement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a single activity requirement.

    Args:
        template_id: UUID of the rotation template (for validation)
        requirement_id: UUID of the requirement to delete

    Raises:
        404: Requirement not found
    """
    activity_service = ActivityService(db)

    # Verify requirement exists and belongs to this template
    requirement = await activity_service.get_requirement_by_id(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Activity requirement not found")
    if requirement.rotation_template_id != template_id:
        raise HTTPException(
            status_code=404,
            detail="Activity requirement not found for this template",
        )

    await activity_service.delete_requirement(requirement_id)
    db.commit()
