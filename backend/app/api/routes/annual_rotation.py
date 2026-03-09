"""Annual Rotation Optimizer API routes.

CRUD for annual rotation plans plus optimize/publish lifecycle actions.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.annual_rotation import (
    AnnualRotationPlanCreate,
    AnnualRotationPlanResponse,
    AnnualRotationPlanSummary,
    OptimizeRequest,
    OptimizeResponse,
)
from app.services import annual_rotation_service

router = APIRouter()


@router.post("/", response_model=AnnualRotationPlanResponse, status_code=201)
async def create_plan(
    data: AnnualRotationPlanCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnualRotationPlanResponse:
    """Create a new annual rotation plan in draft status."""
    plan = await annual_rotation_service.create_plan(
        academic_year=data.academic_year,
        name=data.name,
        solver_time_limit=data.solver_time_limit,
        created_by=current_user.id,
        db=db,
    )
    return AnnualRotationPlanResponse.model_validate(plan)


@router.get("/", response_model=list[AnnualRotationPlanSummary])
async def list_plans(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AnnualRotationPlanSummary]:
    """List all annual rotation plans."""
    plans = await annual_rotation_service.list_plans(db=db)
    return [AnnualRotationPlanSummary.model_validate(p) for p in plans]


@router.get("/{plan_id}", response_model=AnnualRotationPlanResponse)
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnualRotationPlanResponse:
    """Get a plan with all its assignments."""
    plan = await annual_rotation_service.get_plan(plan_id=plan_id, db=db)
    return AnnualRotationPlanResponse.model_validate(plan)


@router.post("/{plan_id}/optimize", response_model=OptimizeResponse)
async def optimize_plan(
    plan_id: UUID,
    data: OptimizeRequest | None = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> OptimizeResponse:
    """Run the CP-SAT optimizer on a plan.

    Loads residents from the DB, solves, and saves assignments.
    """
    override = data.solver_time_limit if data else None
    plan, solver_result = await annual_rotation_service.optimize_plan(
        plan_id=plan_id,
        db=db,
        solver_time_limit_override=override,
    )
    return OptimizeResponse(
        status=plan.status,
        solver_status=solver_result.status,
        objective_value=int(solver_result.objective_value)
        if solver_result.objective_value
        else None,
        solve_duration_ms=plan.solve_duration_ms,
        leave_satisfied=solver_result.leave_satisfied_count,
        leave_total=solver_result.leave_total_count,
        total_assignments=len(plan.assignments),
        plan=AnnualRotationPlanResponse.model_validate(plan),
    )


@router.post("/{plan_id}/publish", response_model=AnnualRotationPlanResponse)
async def publish_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> AnnualRotationPlanResponse:
    """Publish a plan's assignments to block_assignments."""
    plan = await annual_rotation_service.publish_plan(plan_id=plan_id, db=db)
    return AnnualRotationPlanResponse.model_validate(plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a plan. Published plans cannot be deleted."""
    await annual_rotation_service.delete_plan(plan_id=plan_id, db=db)
