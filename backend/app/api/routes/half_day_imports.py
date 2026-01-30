"""Half-day schedule Excel import routes (staging + diff preview)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.file_security import validate_excel_upload
from app.core.logging import get_logger
from app.core.security import get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.half_day_import import (
    HalfDayImportPreviewResponse,
    HalfDayImportStageResponse,
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
    db=Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> HalfDayImportPreviewResponse:
    service = HalfDayImportService(db)
    metrics, diffs, total = service.preview_batch(batch_id, page, page_size)

    return HalfDayImportPreviewResponse(
        batch_id=batch_id,
        metrics=metrics,
        diffs=diffs,
        total_diffs=total,
        page=page,
        page_size=page_size,
    )
