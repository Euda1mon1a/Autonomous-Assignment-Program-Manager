"""Service layer for the Annual Rotation Optimizer.

Orchestrates the lifecycle: create plan → optimize → approve → publish.
"""

from __future__ import annotations

import logging
import time
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.annual_rotation import AnnualRotationAssignment, AnnualRotationPlan
from app.models.block_assignment import BlockAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.annual.context import AnnualContext, ResidentInfo
from app.scheduling.annual.pgy_config import (
    ARO_COMBINED_TEMPLATE_MAP,
    FIXED_ASSIGNMENTS,
    PGY_ROTATIONS,
)
from app.scheduling.annual.solver import SolverResult, solve

logger = logging.getLogger(__name__)


async def create_plan(
    academic_year: int,
    name: str,
    solver_time_limit: float,
    created_by: UUID | None,
    db: AsyncSession,
) -> AnnualRotationPlan:
    """Create a new annual rotation plan in draft status."""
    plan = AnnualRotationPlan(
        academic_year=academic_year,
        name=name,
        status="draft",
        solver_time_limit=solver_time_limit,
        created_by=created_by,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def get_plan(plan_id: UUID, db: AsyncSession) -> AnnualRotationPlan:
    """Retrieve a plan with its assignments, raising 404 if not found."""
    stmt = (
        select(AnnualRotationPlan)
        .options(selectinload(AnnualRotationPlan.assignments))
        .where(AnnualRotationPlan.id == plan_id)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annual rotation plan not found",
        )
    return plan


async def list_plans(db: AsyncSession) -> list[AnnualRotationPlan]:
    """List all annual rotation plans, most recent first."""
    stmt = select(AnnualRotationPlan).order_by(AnnualRotationPlan.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_plan(plan_id: UUID, db: AsyncSession) -> None:
    """Delete a plan. Only draft plans can be deleted."""
    plan = await get_plan(plan_id, db)
    if plan.status == "published":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a published plan",
        )
    await db.delete(plan)
    await db.commit()


async def _load_residents(db: AsyncSession) -> dict[int, list[ResidentInfo]]:
    """Load residents from DB, grouped by PGY level."""
    stmt = (
        select(Person)
        .where(Person.type == "resident")
        .where(Person.pgy_level.isnot(None))
    )
    result = await db.execute(stmt)
    people = result.scalars().all()

    residents_by_pgy: dict[int, list[ResidentInfo]] = {}
    for person in people:
        pgy = person.pgy_level
        if pgy not in (1, 2, 3):
            continue
        ri = ResidentInfo(
            person_id=person.id,
            name=person.name,
            pgy=pgy,
        )
        residents_by_pgy.setdefault(pgy, []).append(ri)

    logger.info(
        "ARO: loaded %d residents (%s)",
        sum(len(v) for v in residents_by_pgy.values()),
        {k: len(v) for k, v in residents_by_pgy.items()},
    )
    return residents_by_pgy


async def optimize_plan(
    plan_id: UUID,
    db: AsyncSession,
    solver_time_limit_override: float | None = None,
) -> tuple[AnnualRotationPlan, SolverResult]:
    """Run the CP-SAT solver on a plan.

    1. Loads residents from the DB.
    2. Builds AnnualContext.
    3. Solves.
    4. Saves assignments as AnnualRotationAssignment rows.
    5. Updates plan status to 'optimized'.

    Returns the updated plan and the solver result.
    """
    plan = await get_plan(plan_id, db)

    if plan.status not in ("draft", "optimized"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot optimize a plan with status '{plan.status}'",
        )

    # Load residents
    residents_by_pgy = await _load_residents(db)
    if not residents_by_pgy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No residents found in the database",
        )

    # Build context
    context = AnnualContext(academic_year=plan.academic_year)
    context.residents_by_pgy = residents_by_pgy
    # No leave requests for now — can be added later via leave import
    context.build_indices()

    # Run solver
    time_limit = solver_time_limit_override or plan.solver_time_limit or 30.0
    start_ms = time.monotonic()
    solver_result = solve(context, timeout_seconds=time_limit)
    elapsed_ms = int((time.monotonic() - start_ms) * 1000)

    if solver_result.status not in ("OPTIMAL", "FEASIBLE"):
        # Update plan with failure info but don't save assignments
        plan.solver_status = solver_result.status
        plan.solve_duration_ms = elapsed_ms
        await db.commit()
        await db.refresh(plan)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Solver returned status: {solver_result.status}",
        )

    # Clear existing assignments (re-optimization)
    existing_stmt = select(AnnualRotationAssignment).where(
        AnnualRotationAssignment.plan_id == plan_id
    )
    existing_result = await db.execute(existing_stmt)
    for existing in existing_result.scalars().all():
        await db.delete(existing)
    await db.flush()  # Ensure deletes are applied before re-inserting

    # Save solver assignments
    for assignment in solver_result.assignments:
        db.add(
            AnnualRotationAssignment(
                plan_id=plan_id,
                person_id=assignment.person_id,
                block_number=assignment.block_number,
                rotation_name=assignment.rotation_name,
                is_fixed=assignment.is_fixed,
            )
        )

    # Also add fixed assignments that the solver skips
    for r_idx, resident in enumerate(context.all_residents):
        fixed = FIXED_ASSIGNMENTS.get(resident.pgy, {})
        for block_num, rot_name in fixed.items():
            # Check if solver already produced this (it should for forced vars)
            already_exists = any(
                a.person_id == resident.person_id and a.block_number == block_num
                for a in solver_result.assignments
            )
            if not already_exists:
                db.add(
                    AnnualRotationAssignment(
                        plan_id=plan_id,
                        person_id=resident.person_id,
                        block_number=block_num,
                        rotation_name=rot_name,
                        is_fixed=True,
                    )
                )

    # Update plan metadata
    plan.status = "optimized"
    plan.solver_status = solver_result.status
    plan.objective_value = int(solver_result.objective_value)
    plan.solve_duration_ms = elapsed_ms

    await db.commit()

    # Reload plan with assignments
    plan = await get_plan(plan_id, db)
    return plan, solver_result


async def publish_plan(plan_id: UUID, db: AsyncSession) -> AnnualRotationPlan:
    """Publish a plan by writing assignments to block_assignments.

    Only 'optimized' or 'approved' plans can be published.
    Creates BlockAssignment rows for each assignment in the plan.
    """
    plan = await get_plan(plan_id, db)

    if plan.status not in ("optimized", "approved"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot publish a plan with status '{plan.status}'. "
            f"Must be 'optimized' or 'approved'.",
        )

    if not plan.assignments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan has no assignments to publish",
        )

    # Build abbreviation → template lookup (multi-key: name, abbreviation, display_abbreviation)
    all_templates_stmt = select(RotationTemplate).where(
        ~RotationTemplate.is_archived,
    )
    all_templates_result = await db.execute(all_templates_stmt)
    all_templates = list(all_templates_result.scalars().all())

    # Index by multiple keys for flexible matching
    abbrev_to_template: dict[str, RotationTemplate] = {}
    name_to_template: dict[str, RotationTemplate] = {}
    for t in all_templates:
        if t.abbreviation:
            abbrev_to_template[t.abbreviation.upper()] = t
        if t.display_abbreviation:
            abbrev_to_template[t.display_abbreviation.upper()] = t
        if t.name:
            name_to_template[t.name.upper()] = t

    def _find_template(name: str) -> RotationTemplate | None:
        """Look up template by name, abbreviation, or display_abbreviation."""
        key = name.upper()
        return name_to_template.get(key) or abbrev_to_template.get(key)

    # Build set of combined rotation names from PGY_ROTATIONS
    combined_names = {
        rot.name for rots in PGY_ROTATIONS.values() for rot in rots if rot.is_combined
    }

    # Delete existing block_assignments for this AY + these residents
    # to avoid IntegrityError on the unique constraint
    person_ids = {a.person_id for a in plan.assignments}
    existing_stmt = select(BlockAssignment).where(
        BlockAssignment.academic_year == plan.academic_year,
        BlockAssignment.resident_id.in_(person_ids),
    )
    existing_result = await db.execute(existing_stmt)
    for existing in existing_result.scalars().all():
        await db.delete(existing)
    await db.flush()

    unmapped: set[str] = set()

    # Write to block_assignments
    for assignment in plan.assignments:
        primary_template_id: UUID | None = None
        secondary_template_id: UUID | None = None

        if assignment.rotation_name in combined_names:
            # Combined rotation — use ARO_COMBINED_TEMPLATE_MAP
            mapping = ARO_COMBINED_TEMPLATE_MAP.get(assignment.rotation_name)
            if mapping:
                primary_abbrev, secondary_abbrev = mapping
                primary_tmpl = abbrev_to_template.get(primary_abbrev.upper())
                if primary_tmpl:
                    primary_template_id = primary_tmpl.id
                else:
                    unmapped.add(f"{assignment.rotation_name}→{primary_abbrev}")

                if secondary_abbrev:
                    secondary_tmpl = abbrev_to_template.get(secondary_abbrev.upper())
                    if secondary_tmpl:
                        secondary_template_id = secondary_tmpl.id
                    else:
                        unmapped.add(f"{assignment.rotation_name}→{secondary_abbrev}")
            else:
                unmapped.add(assignment.rotation_name)
        else:
            # Non-combined: try name, abbreviation, display_abbreviation
            tmpl = _find_template(assignment.rotation_name)
            if tmpl:
                primary_template_id = tmpl.id
            else:
                unmapped.add(assignment.rotation_name)

        if secondary_template_id:
            # Two-template split → two rows with block_half
            db.add(
                BlockAssignment(
                    block_number=assignment.block_number,
                    academic_year=plan.academic_year,
                    resident_id=assignment.person_id,
                    rotation_template_id=primary_template_id,
                    block_half=1,
                    assignment_reason="balanced",
                    notes=f"ARO plan: {plan.name}",
                    created_by="annual_rotation_optimizer",
                )
            )
            db.add(
                BlockAssignment(
                    block_number=assignment.block_number,
                    academic_year=plan.academic_year,
                    resident_id=assignment.person_id,
                    rotation_template_id=secondary_template_id,
                    block_half=2,
                    assignment_reason="balanced",
                    notes=f"ARO plan: {plan.name}",
                    created_by="annual_rotation_optimizer",
                )
            )
        else:
            # Non-combined or single combined template → one row
            db.add(
                BlockAssignment(
                    block_number=assignment.block_number,
                    academic_year=plan.academic_year,
                    resident_id=assignment.person_id,
                    rotation_template_id=primary_template_id,
                    assignment_reason="balanced",
                    notes=f"ARO plan: {plan.name}",
                    created_by="annual_rotation_optimizer",
                )
            )

    if unmapped:
        logger.warning(
            "ARO: no RotationTemplate found for rotation names: %s", unmapped
        )

    plan.status = "published"
    await db.commit()
    await db.refresh(plan)

    logger.info(
        "ARO: published plan %s with %d assignments",
        plan_id,
        len(plan.assignments),
    )
    return plan
