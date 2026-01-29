"""Admin routes for schedule overrides (coverage layer)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_admin_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.schedule_override import (
    ScheduleOverrideCreate,
    ScheduleOverrideListResponse,
    ScheduleOverrideResponse,
)
from app.services.schedule_override_service import get_schedule_override_service

router = APIRouter()


@router.post(
    "",
    response_model=ScheduleOverrideResponse,
    status_code=201,
    summary="Create schedule override",
    description="Admin-only: create a coverage or cancellation override for a released slot.",
)
async def create_schedule_override(
    request: ScheduleOverrideCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
) -> ScheduleOverrideResponse:
    service = get_schedule_override_service(db)
    override = await service.create_override(request, created_by_id=current_user.id)
    await db.commit()
    return ScheduleOverrideResponse.model_validate(override)


@router.get(
    "",
    response_model=ScheduleOverrideListResponse,
    summary="List schedule overrides",
    description="Admin-only: list overrides for a block or date range.",
)
async def list_schedule_overrides(
    block_number: int | None = Query(None, ge=0, le=13, description="Block number"),
    academic_year: int | None = Query(None, description="Academic year (e.g., 2025)"),
    start_date: date | None = Query(None, description="Start date"),
    end_date: date | None = Query(None, description="End date"),
    active_only: bool = Query(True, description="Only active overrides"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
) -> ScheduleOverrideListResponse:
    service = get_schedule_override_service(db)
    overrides = await service.list_overrides(
        block_number=block_number,
        academic_year=academic_year,
        start_date=start_date,
        end_date=end_date,
        active_only=active_only,
    )
    return ScheduleOverrideListResponse(
        overrides=[ScheduleOverrideResponse.model_validate(o) for o in overrides],
        total=len(overrides),
        block_number=block_number,
        academic_year=academic_year,
        start_date=start_date,
        end_date=end_date,
    )


@router.delete(
    "/{override_id}",
    response_model=ScheduleOverrideResponse,
    summary="Deactivate schedule override",
    description="Admin-only: deactivate an override (soft delete).",
)
async def deactivate_schedule_override(
    override_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
) -> ScheduleOverrideResponse:
    service = get_schedule_override_service(db)
    override = await service.deactivate_override(
        override_id=override_id,
        deactivated_by_id=current_user.id,
    )
    await db.commit()
    return ScheduleOverrideResponse.model_validate(override)
