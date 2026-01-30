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
from app.schemas.cascade_override import (
    CascadeOverridePlanResponse,
    CascadeOverrideRequest,
)
from app.schemas.emergency_deployment import (
    EmergencyDeploymentRequest,
    EmergencyDeploymentResponse,
)
from app.services.cascade_override_service import CascadeOverrideService
from app.services.emergency_deployment_service import get_emergency_deployment_service
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


@router.post(
    "/cascade",
    response_model=CascadeOverridePlanResponse,
    summary="Plan or apply cascade overrides",
    description="Admin-only: build and optionally apply cascade overrides for a deployment.",
)
async def create_cascade_overrides(
    request: CascadeOverrideRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
) -> CascadeOverridePlanResponse:
    service = CascadeOverrideService(db)
    plan = await service.plan_and_apply(request, created_by_id=current_user.id)
    if request.apply and not plan.errors:
        await db.commit()
    return plan


@router.post(
    "/emergency",
    response_model=EmergencyDeploymentResponse,
    summary="Emergency deployment response",
    description=(
        "Admin-only: 'Oh shit' button for emergency deployments. "
        "Assesses fragility and executes tiered repair strategy: "
        "incremental → cascade → fallback. Set dry_run=true to assess only."
    ),
)
async def handle_emergency_deployment(
    request: EmergencyDeploymentRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
) -> EmergencyDeploymentResponse:
    """
    Handle emergency faculty deployment with automatic repair.

    The "Oh Shit" Button:
    1. ASSESS: Calculate fragility score and affected slots
    2. EXECUTE: Try incremental → cascade → fallback based on fragility
    3. VERIFY: Check health and escalate if still broken

    Tiered Strategy:
    - Fragility < 0.3: Incremental repair (fast, surgical)
    - Fragility 0.3-0.6: Cascade with sacrifice hierarchy
    - Fragility >= 0.6: Activate pre-computed fallback

    Use dry_run=true (default) to assess without making changes.
    """
    service = get_emergency_deployment_service(db)
    response = await service.handle_deployment(request, created_by_id=current_user.id)
    if not request.dry_run and response.overall_success:
        await db.commit()
    return response
