"""Admin routes for call overrides (coverage layer)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_admin_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.call_override import (
    CallOverrideCreate,
    CallOverrideListResponse,
    CallOverrideResponse,
)
from app.services.call_override_service import get_call_override_service

router = APIRouter()


@router.post(
    "",
    response_model=CallOverrideResponse,
    status_code=201,
    summary="Create call override",
    description="Admin-only: create a coverage override for a call assignment.",
)
async def create_call_override(
    request: CallOverrideCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
) -> CallOverrideResponse:
    service = get_call_override_service(db)
    override = await service.create_override(request, created_by_id=current_user.id)
    await db.commit()
    return CallOverrideResponse.model_validate(override)


@router.get(
    "",
    response_model=CallOverrideListResponse,
    summary="List call overrides",
    description="Admin-only: list call overrides for a block or date range.",
)
async def list_call_overrides(
    block_number: int | None = Query(None, ge=0, le=13, description="Block number"),
    academic_year: int | None = Query(None, description="Academic year (e.g., 2025)"),
    start_date: date | None = Query(None, description="Start date"),
    end_date: date | None = Query(None, description="End date"),
    active_only: bool = Query(True, description="Only active overrides"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
) -> CallOverrideListResponse:
    service = get_call_override_service(db)
    overrides = await service.list_overrides(
        block_number=block_number,
        academic_year=academic_year,
        start_date=start_date,
        end_date=end_date,
        active_only=active_only,
    )
    return CallOverrideListResponse(
        overrides=[CallOverrideResponse.model_validate(o) for o in overrides],
        total=len(overrides),
        block_number=block_number,
        academic_year=academic_year,
        start_date=start_date,
        end_date=end_date,
    )


@router.delete(
    "/{override_id}",
    response_model=CallOverrideResponse,
    summary="Deactivate call override",
    description="Admin-only: deactivate a call override (soft delete).",
)
async def deactivate_call_override(
    override_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
) -> CallOverrideResponse:
    service = get_call_override_service(db)
    override = await service.deactivate_override(
        override_id=override_id,
        deactivated_by_id=current_user.id,
    )
    await db.commit()
    return CallOverrideResponse.model_validate(override)
