"""Half-day schedule Excel import routes (staging + diff preview)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.core.file_security import validate_excel_upload
from app.core.logging import get_logger
from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.half_day_import import (
    HalfDayImportDraftRequest,
    HalfDayImportDraftResponse,
    HalfDayImportPreviewResponse,
    HalfDayImportStageResponse,
    HalfDayDiffType,
)
from app.services.half_day_import_service import HalfDayImportService

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/stage",
    response_model=HalfDayImportStageResponse,
    summary="Stage a Block Template2 schedule for diff",
    description="Upload a Block Template2 Excel file and stage diffs vs live schedule.",
)
async def stage_half_day_import(
    file: UploadFile = File(..., description="Block Template2 xlsx file"),
    block_number: int = Form(..., ge=1, le=26),
    academic_year: int = Form(..., ge=2000),
    notes: str | None = Form(None, max_length=2000),
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> HalfDayImportStageResponse:
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be .xlsx or .xls")

    file_bytes = await file.read()
    try:
        validate_excel_upload(file_bytes, file.filename, file.content_type or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = HalfDayImportService(db)
    try:
        batch, metrics, warnings = service.stage_block_template2(
            file_bytes=file_bytes,
            block_number=block_number,
            academic_year=academic_year,
            created_by_id=current_user.id,
            notes=notes,
            filename=file.filename,
        )
    except Exception as e:
        logger.error(f"Half-day import staging failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

    return HalfDayImportStageResponse(
        success=True,
        batch_id=batch.id,
        created_at=batch.created_at,
        message="Staged half-day schedule diff",
        warnings=warnings,
        diff_metrics=metrics,
    )


@router.get(
    "/batches/{batch_id}/preview",
    response_model=HalfDayImportPreviewResponse,
    summary="Preview staged half-day diffs",
)
async def preview_half_day_import(
    batch_id: UUID,
    page: int = 1,
    page_size: int = 50,
    diff_type: HalfDayDiffType | None = Query(
        default=None, description="Filter by diff type (added/removed/modified)"
    ),
    activity_code: str | None = Query(
        default=None, description="Filter by activity code (exact match)"
    ),
    has_errors: bool | None = Query(
        default=None, description="Filter rows with validation errors"
    ),
    person_id: UUID | None = Query(
        default=None, description="Filter by matched person ID"
    ),
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> HalfDayImportPreviewResponse:
    service = HalfDayImportService(db)
    metrics, diffs, total = service.preview_batch(
        batch_id=batch_id,
        page=page,
        page_size=page_size,
        diff_type=diff_type,
        activity_code=activity_code,
        has_errors=has_errors,
        person_id=person_id,
    )

    return HalfDayImportPreviewResponse(
        batch_id=batch_id,
        metrics=metrics,
        diffs=diffs,
        total_diffs=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/batches/{batch_id}/draft",
    response_model=HalfDayImportDraftResponse,
    summary="Create a schedule draft from staged half-day diffs",
)
async def create_half_day_import_draft(
    batch_id: UUID,
    payload: HalfDayImportDraftRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> HalfDayImportDraftResponse:
    service = HalfDayImportService(db)
    result = service.create_draft_from_batch(
        batch_id=batch_id,
        staged_ids=payload.staged_ids,
        created_by_id=current_user.id,
        notes=payload.notes,
    )
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "message": result.message,
                "error_code": result.error_code,
                "failed_ids": [str(staged_id) for staged_id in result.failed_ids],
            },
        )

    return HalfDayImportDraftResponse(
        success=True,
        batch_id=result.batch_id,
        draft_id=result.draft_id,
        message=result.message,
        total_selected=result.total_selected,
        added=result.added,
        modified=result.modified,
        removed=result.removed,
        skipped=result.skipped,
        failed=result.failed,
        failed_ids=result.failed_ids,
    )
