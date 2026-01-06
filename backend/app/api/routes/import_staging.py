"""
Import staging API routes for Excel import workflow.

Provides endpoints for staging, previewing, applying, and managing
import batches:
- POST /import/stage - Upload Excel, create staged batch
- GET /import/batches - List batches with pagination
- GET /import/batches/{id} - Get batch details
- GET /import/batches/{id}/preview - Preview staged vs existing
- POST /import/batches/{id}/apply - Apply batch to live
- POST /import/batches/{id}/rollback - Rollback applied batch
- DELETE /import/batches/{id} - Reject/delete batch
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.core.file_security import validate_excel_upload
from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.import_staging import ConflictResolutionMode, ImportBatchStatus
from app.models.user import User
from app.schemas.import_staging import (
    ImportApplyRequest,
    ImportApplyResponse,
    ImportBatchCounts,
    ImportBatchList,
    ImportBatchListItem,
    ImportBatchResponse,
    ImportPreviewResponse,
    ImportRollbackRequest,
    ImportRollbackResponse,
    StagedAssignmentResponse,
)
from app.services.import_staging_service import ImportStagingService

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/stage",
    response_model=dict,
    status_code=201,
    summary="Stage an Excel import",
    description="Upload an Excel file and create a staged import batch for review.",
)
async def stage_import(
    file: UploadFile = File(..., description="Excel file to import (.xlsx, .xls)"),
    target_block: int | None = Form(
        None, ge=1, le=26, description="Target academic block number (1-26)"
    ),
    target_start_date: str | None = Form(
        None, description="Target start date (YYYY-MM-DD)"
    ),
    target_end_date: str | None = Form(
        None, description="Target end date (YYYY-MM-DD)"
    ),
    conflict_resolution: str = Form(
        "upsert",
        description="Conflict resolution mode: replace, merge, or upsert",
    ),
    notes: str | None = Form(None, max_length=2000, description="Import notes"),
    sheet_name: str | None = Form(
        None, description="Specific sheet name to parse (default: first sheet)"
    ),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Stage an Excel file for import.

    Parses the uploaded Excel file, performs fuzzy matching for person
    and rotation names, detects conflicts with existing assignments,
    and creates staged records for review before applying.

    The file must have at minimum:
    - person_name (or name, provider, resident) column
    - assignment_date (or date) column

    Optional columns:
    - rotation_name (or rotation, activity)
    - slot (or time, session) - AM/PM
    - raw (or raw_value, cell)

    Returns the batch ID for subsequent preview and apply operations.
    """
    # Validate file extension
    filename = file.filename or "unknown.xlsx"
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext not in ("xlsx", "xls"):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": f"Invalid file extension: .{ext}. Expected .xlsx or .xls",
                "error_code": "INVALID_EXTENSION",
            },
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Failed to read uploaded file",
                "error_code": "READ_ERROR",
            },
        )

    # Check file size (10MB limit)
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail={
                "success": False,
                "error": "File too large. Maximum size is 10MB",
                "error_code": "FILE_TOO_LARGE",
            },
        )

    # Validate file security
    try:
        validate_excel_upload(content, filename, file.content_type or "")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "SECURITY_VALIDATION_FAILED",
            },
        )

    # Parse dates
    from datetime import date as date_type

    start_date = None
    end_date = None
    if target_start_date:
        try:
            start_date = date_type.fromisoformat(target_start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"Invalid start date format: {target_start_date}",
                    "error_code": "INVALID_DATE",
                },
            )
    if target_end_date:
        try:
            end_date = date_type.fromisoformat(target_end_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"Invalid end date format: {target_end_date}",
                    "error_code": "INVALID_DATE",
                },
            )

    # Parse conflict resolution
    try:
        resolution = ConflictResolutionMode(conflict_resolution.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": f"Invalid conflict resolution: {conflict_resolution}",
                "error_code": "INVALID_RESOLUTION",
            },
        )

    # Stage the import
    service = ImportStagingService(db)
    result = await service.stage_import(
        file_bytes=content,
        filename=filename,
        created_by_id=current_user.id,
        target_block=target_block,
        target_start_date=start_date,
        target_end_date=end_date,
        conflict_resolution=resolution,
        notes=notes,
        sheet_name=sheet_name,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": result.message,
                "error_code": result.error_code,
            },
        )

    return {
        "success": True,
        "batch_id": str(result.batch_id),
        "message": result.message,
        "row_count": result.row_count,
        "error_count": result.error_count,
        "warning_count": result.warning_count,
    }


@router.get(
    "/batches",
    response_model=ImportBatchList,
    summary="List import batches",
    description="List all import batches with pagination.",
)
async def list_batches(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List import batches with pagination.

    Supports filtering by status (staged, approved, rejected, applied, rolled_back, failed).
    """
    # Parse status filter
    status_enum = None
    if status:
        try:
            status_enum = ImportBatchStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Invalid status: {status}"},
            )

    service = ImportStagingService(db)
    batches, total = await service.list_batches(
        page=page,
        page_size=page_size,
        status=status_enum,
    )

    # Convert to response format
    items = []
    for batch in batches:
        # Calculate counts
        counts = ImportBatchCounts()
        if batch.staged_assignments:
            for sa in batch.staged_assignments:
                counts.total += 1
                if sa.status.value == "pending":
                    counts.pending += 1
                elif sa.status.value == "approved":
                    counts.approved += 1
                elif sa.status.value == "skipped":
                    counts.skipped += 1
                elif sa.status.value == "applied":
                    counts.applied += 1
                elif sa.status.value == "failed":
                    counts.failed += 1

        items.append(
            ImportBatchListItem(
                id=batch.id,
                created_at=batch.created_at,
                filename=batch.filename,
                status=batch.status,
                target_block=batch.target_block,
                target_start_date=batch.target_start_date,
                target_end_date=batch.target_end_date,
                row_count=batch.row_count,
                error_count=batch.error_count,
                counts=counts,
            )
        )

    return ImportBatchList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        has_previous=page > 1,
    )


@router.get(
    "/batches/{batch_id}",
    response_model=ImportBatchResponse,
    summary="Get batch details",
    description="Get details of a specific import batch.",
)
async def get_batch(
    batch_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get details of a specific import batch."""
    service = ImportStagingService(db)
    batch = await service.get_batch(batch_id)

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Calculate counts
    counts = ImportBatchCounts()
    if batch.staged_assignments:
        for sa in batch.staged_assignments:
            counts.total += 1
            if sa.status.value == "pending":
                counts.pending += 1
            elif sa.status.value == "approved":
                counts.approved += 1
            elif sa.status.value == "skipped":
                counts.skipped += 1
            elif sa.status.value == "applied":
                counts.applied += 1
            elif sa.status.value == "failed":
                counts.failed += 1

    return ImportBatchResponse(
        id=batch.id,
        created_at=batch.created_at,
        created_by_id=batch.created_by_id,
        filename=batch.filename,
        file_hash=batch.file_hash,
        file_size_bytes=batch.file_size_bytes,
        status=batch.status,
        conflict_resolution=batch.conflict_resolution,
        target_block=batch.target_block,
        target_start_date=batch.target_start_date,
        target_end_date=batch.target_end_date,
        notes=batch.notes,
        row_count=batch.row_count,
        error_count=batch.error_count,
        warning_count=batch.warning_count,
        applied_at=batch.applied_at,
        applied_by_id=batch.applied_by_id,
        rollback_available=batch.rollback_available,
        rollback_expires_at=batch.rollback_expires_at,
        rolled_back_at=batch.rolled_back_at,
        rolled_back_by_id=batch.rolled_back_by_id,
        counts=counts,
    )


@router.get(
    "/batches/{batch_id}/preview",
    response_model=ImportPreviewResponse,
    summary="Preview batch",
    description="Preview staged vs existing assignments before applying.",
)
async def preview_batch(
    batch_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Preview a batch before applying.

    Shows staged assignments with conflict detection and ACGME compliance preview.
    Supports pagination for large imports.
    """
    service = ImportStagingService(db)
    result = await service.get_batch_preview(
        batch_id=batch_id,
        page=page,
        page_size=page_size,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Convert staged assignments to response format
    staged_responses = []
    if result.staged_assignments:
        for sa in result.staged_assignments:
            staged_responses.append(
                StagedAssignmentResponse(
                    id=UUID(sa["id"]),
                    batch_id=UUID(sa["batch_id"]),
                    row_number=sa.get("row_number"),
                    sheet_name=sa.get("sheet_name"),
                    person_name=sa["person_name"],
                    assignment_date=sa["assignment_date"],
                    slot=sa.get("slot"),
                    rotation_name=sa.get("rotation_name"),
                    raw_cell_value=sa.get("raw_cell_value"),
                    matched_person_id=UUID(sa["matched_person_id"])
                    if sa.get("matched_person_id")
                    else None,
                    matched_person_name=sa.get("matched_person_name"),
                    person_match_confidence=sa.get("person_match_confidence"),
                    matched_rotation_id=UUID(sa["matched_rotation_id"])
                    if sa.get("matched_rotation_id")
                    else None,
                    matched_rotation_name=sa.get("matched_rotation_name"),
                    rotation_match_confidence=sa.get("rotation_match_confidence"),
                    conflict_type=sa.get("conflict_type"),
                    existing_assignment_id=UUID(sa["existing_assignment_id"])
                    if sa.get("existing_assignment_id")
                    else None,
                    status=sa["status"],
                    validation_errors=sa.get("validation_errors"),
                    validation_warnings=sa.get("validation_warnings"),
                    created_assignment_id=UUID(sa["created_assignment_id"])
                    if sa.get("created_assignment_id")
                    else None,
                )
            )

    return ImportPreviewResponse(
        batch_id=result.batch_id,
        new_count=result.new_count,
        update_count=result.update_count,
        conflict_count=result.conflict_count,
        skip_count=result.skip_count,
        acgme_violations=result.acgme_violations or [],
        staged_assignments=staged_responses,
        conflicts=result.conflicts or [],
        total_staged=result.total_staged,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/batches/{batch_id}/apply",
    response_model=ImportApplyResponse,
    summary="Apply batch",
    description="Apply staged batch to live assignments table.",
)
async def apply_batch(
    batch_id: UUID,
    request: ImportApplyRequest | None = None,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Apply a staged batch to the live assignments table.

    Commits all approved staged assignments according to the conflict
    resolution mode. Supports dry-run mode for validation without apply.
    """
    if request is None:
        request = ImportApplyRequest()

    # Parse conflict resolution if provided
    conflict_resolution = None
    if request.conflict_resolution:
        conflict_resolution = request.conflict_resolution

    service = ImportStagingService(db)
    result = await service.apply_batch(
        batch_id=batch_id,
        applied_by_id=current_user.id,
        conflict_resolution=conflict_resolution,
        dry_run=request.dry_run,
        validate_acgme=request.validate_acgme,
    )

    if not result.success and result.error_code:
        if result.error_code == "BATCH_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Batch not found")
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.message,
                "error_code": result.error_code,
            },
        )

    return ImportApplyResponse(
        batch_id=result.batch_id,
        status=result.status,
        applied_count=result.applied_count,
        skipped_count=result.skipped_count,
        error_count=result.error_count,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        errors=result.errors or [],
        acgme_warnings=result.acgme_warnings or [],
        rollback_available=result.rollback_available,
        rollback_expires_at=result.rollback_expires_at,
        dry_run=request.dry_run,
    )


@router.post(
    "/batches/{batch_id}/rollback",
    response_model=ImportRollbackResponse,
    summary="Rollback batch",
    description="Rollback an applied batch within the 24-hour window.",
)
async def rollback_batch(
    batch_id: UUID,
    request: ImportRollbackRequest | None = None,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Rollback an applied batch.

    Deletes all assignments created by this batch and restores
    the batch to staged status. Only available within 24 hours
    of apply.
    """
    reason = request.reason if request else None

    service = ImportStagingService(db)
    result = await service.rollback_batch(
        batch_id=batch_id,
        rolled_back_by_id=current_user.id,
        reason=reason,
    )

    if not result.success and result.error_code:
        if result.error_code == "BATCH_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Batch not found")
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.message,
                "error_code": result.error_code,
            },
        )

    return ImportRollbackResponse(
        batch_id=result.batch_id,
        status=result.status,
        rolled_back_count=result.rolled_back_count,
        failed_count=result.failed_count,
        rolled_back_at=datetime.utcnow(),
        rolled_back_by_id=current_user.id,
        errors=result.errors or [],
    )


@router.delete(
    "/batches/{batch_id}",
    status_code=204,
    summary="Reject batch",
    description="Reject and delete a batch. Cannot reject applied batches.",
)
async def reject_batch(
    batch_id: UUID,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Reject and delete a batch.

    Marks the batch as rejected and deletes all staged assignments.
    Cannot reject batches that have been applied - use rollback first.
    """
    service = ImportStagingService(db)
    success, message = await service.reject_batch(batch_id)

    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)

    return None  # 204 No Content
