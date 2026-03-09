"""
Annual Rotation Optimizer (ARO) tools for the Scheduler MCP server.

Provides MCP tools for creating, listing, optimizing, and publishing
annual rotation plans via the FastAPI backend.
"""

import logging

from pydantic import BaseModel, Field

from .api_client import get_api_client

logger = logging.getLogger(__name__)


# =============================================================================
# Response Models
# =============================================================================


class AnnualPlanAssignment(BaseModel):
    """A single rotation assignment within an annual plan."""

    id: str = Field(..., description="Assignment UUID")
    resident_name: str = Field("", description="Resident name")
    block_number: int = Field(..., description="Block number (1-13)")
    rotation_name: str = Field("", description="Rotation name")
    is_fixed: bool = Field(False, description="Whether this is a fixed assignment")


class AnnualPlanInfo(BaseModel):
    """Detailed information about an annual rotation plan."""

    id: str = Field(..., description="Plan UUID")
    academic_year: int = Field(..., description="Academic year (e.g. 2026)")
    name: str = Field(..., description="Plan name")
    status: str = Field(..., description="Plan status (draft/optimized/published)")
    solver_time_limit: float | None = Field(None, description="Solver time limit in seconds")
    solve_duration_ms: int | None = Field(None, description="Actual solve duration in ms")
    created_at: str = Field("", description="Creation timestamp")
    assignments: list[AnnualPlanAssignment] = Field(
        default_factory=list, description="Plan assignments"
    )


class AnnualPlanSummary(BaseModel):
    """Summary of an annual rotation plan (no assignments)."""

    id: str = Field(..., description="Plan UUID")
    academic_year: int = Field(..., description="Academic year")
    name: str = Field(..., description="Plan name")
    status: str = Field(..., description="Plan status")
    created_at: str = Field("", description="Creation timestamp")
    assignment_count: int = Field(0, description="Number of assignments")


class CreatePlanResult(BaseModel):
    """Result of creating an annual plan."""

    success: bool = Field(..., description="Whether plan was created")
    plan: AnnualPlanInfo | None = Field(None, description="Created plan details")
    error: str | None = Field(None, description="Error message if failed")


class ListPlansResult(BaseModel):
    """Result of listing annual plans."""

    plans: list[AnnualPlanSummary] = Field(default_factory=list, description="Plans")
    total_count: int = Field(0, description="Total number of plans")


class GetPlanResult(BaseModel):
    """Result of getting a specific plan."""

    success: bool = Field(..., description="Whether plan was found")
    plan: AnnualPlanInfo | None = Field(None, description="Plan details")
    error: str | None = Field(None, description="Error message if failed")


class OptimizeResult(BaseModel):
    """Result of optimizing an annual plan."""

    success: bool = Field(..., description="Whether optimization succeeded")
    status: str = Field("", description="Plan status after optimization")
    solver_status: str = Field("", description="CP-SAT solver status")
    objective_value: int | None = Field(None, description="Objective function value")
    solve_duration_ms: int | None = Field(None, description="Solve time in ms")
    leave_satisfied: int | None = Field(None, description="Leave requests satisfied")
    leave_total: int | None = Field(None, description="Total leave requests")
    total_assignments: int = Field(0, description="Total assignments created")
    error: str | None = Field(None, description="Error message if failed")


class PublishResult(BaseModel):
    """Result of publishing an annual plan."""

    success: bool = Field(..., description="Whether publish succeeded")
    plan: AnnualPlanInfo | None = Field(None, description="Published plan")
    error: str | None = Field(None, description="Error message if failed")


# =============================================================================
# Helper
# =============================================================================


def _parse_plan_info(data: dict) -> AnnualPlanInfo:
    """Parse API response into AnnualPlanInfo."""
    assignments = []
    for a in data.get("assignments", []):
        assignments.append(
            AnnualPlanAssignment(
                id=str(a.get("id", "")),
                resident_name=a.get("resident_name", ""),
                block_number=a.get("block_number", 0),
                rotation_name=a.get("rotation_name", ""),
                is_fixed=a.get("is_fixed", False),
            )
        )
    return AnnualPlanInfo(
        id=str(data.get("id", "")),
        academic_year=data.get("academic_year", 0),
        name=data.get("name", ""),
        status=data.get("status", ""),
        solver_time_limit=data.get("solver_time_limit"),
        solve_duration_ms=data.get("solve_duration_ms"),
        created_at=str(data.get("created_at", "")),
        assignments=assignments,
    )


# =============================================================================
# Tool Functions
# =============================================================================


async def create_annual_plan(
    academic_year: int,
    name: str,
    solver_time_limit: float = 30.0,
) -> CreatePlanResult:
    """
    Create a new annual rotation plan in draft status.

    Args:
        academic_year: Academic year (e.g. 2026 for AY 26-27)
        name: Descriptive name for the plan
        solver_time_limit: CP-SAT solver time limit in seconds (default 30)

    Returns:
        CreatePlanResult with plan details or error
    """
    try:
        client = await get_api_client()
        result = await client.create_annual_plan(
            academic_year=academic_year,
            name=name,
            solver_time_limit=solver_time_limit,
        )
        plan = _parse_plan_info(result)
        logger.info(f"Created annual plan: {plan.id} ({plan.name})")
        return CreatePlanResult(success=True, plan=plan)
    except Exception as e:
        logger.error(f"Failed to create annual plan: {e}")
        return CreatePlanResult(success=False, error=str(e))


async def list_annual_plans() -> ListPlansResult:
    """
    List all annual rotation plans.

    Returns:
        ListPlansResult with plan summaries
    """
    try:
        client = await get_api_client()
        results = await client.list_annual_plans()
        plans = []
        for p in results:
            plans.append(
                AnnualPlanSummary(
                    id=str(p.get("id", "")),
                    academic_year=p.get("academic_year", 0),
                    name=p.get("name", ""),
                    status=p.get("status", ""),
                    created_at=str(p.get("created_at", "")),
                    assignment_count=p.get("assignment_count", 0),
                )
            )
        return ListPlansResult(plans=plans, total_count=len(plans))
    except Exception as e:
        logger.error(f"Failed to list annual plans: {e}")
        return ListPlansResult(plans=[], total_count=0)


async def get_annual_plan(plan_id: str) -> GetPlanResult:
    """
    Get a specific annual rotation plan with all assignments.

    Args:
        plan_id: UUID of the plan to retrieve

    Returns:
        GetPlanResult with full plan details
    """
    try:
        client = await get_api_client()
        result = await client.get_annual_plan(plan_id)
        plan = _parse_plan_info(result)
        return GetPlanResult(success=True, plan=plan)
    except Exception as e:
        logger.error(f"Failed to get annual plan {plan_id}: {e}")
        return GetPlanResult(success=False, error=str(e))


async def optimize_annual_plan(
    plan_id: str,
    solver_time_limit: float | None = None,
) -> OptimizeResult:
    """
    Run the CP-SAT optimizer on an annual rotation plan.

    Loads residents from DB, solves rotation assignments, and saves results.
    Can take up to 300 seconds for large plans.

    Args:
        plan_id: UUID of the plan to optimize
        solver_time_limit: Override solver time limit (seconds)

    Returns:
        OptimizeResult with solver status and assignment counts
    """
    try:
        client = await get_api_client()
        result = await client.optimize_annual_plan(
            plan_id=plan_id,
            solver_time_limit=solver_time_limit,
        )
        logger.info(
            f"Optimized annual plan {plan_id}: "
            f"status={result.get('solver_status')}, "
            f"assignments={result.get('total_assignments', 0)}"
        )
        return OptimizeResult(
            success=True,
            status=result.get("status", ""),
            solver_status=result.get("solver_status", ""),
            objective_value=result.get("objective_value"),
            solve_duration_ms=result.get("solve_duration_ms"),
            leave_satisfied=result.get("leave_satisfied"),
            leave_total=result.get("leave_total"),
            total_assignments=result.get("total_assignments", 0),
        )
    except Exception as e:
        logger.error(f"Failed to optimize annual plan {plan_id}: {e}")
        return OptimizeResult(success=False, error=str(e))


async def publish_annual_plan(plan_id: str) -> PublishResult:
    """
    Publish an annual plan's assignments to block_assignments.

    This writes the optimized rotation assignments into the operational
    schedule tables. Only optimized plans can be published.

    Args:
        plan_id: UUID of the plan to publish

    Returns:
        PublishResult with published plan details
    """
    try:
        client = await get_api_client()
        result = await client.publish_annual_plan(plan_id)
        plan = _parse_plan_info(result)
        logger.info(f"Published annual plan {plan_id}")
        return PublishResult(success=True, plan=plan)
    except Exception as e:
        logger.error(f"Failed to publish annual plan {plan_id}: {e}")
        return PublishResult(success=False, error=str(e))
