"""
Activity Assignment Solver using CP-SAT.

This solver assigns activities (C, LEC, ADV, etc.) to half-day slots
that don't already have locked assignments (preload/manual).

The existing CPSATSolver handles rotation-level assignment (which resident
gets which rotation). This solver handles activity-level assignment within
a rotation (which half-day slot gets C vs LEC vs ADV).

Decision Variables:
    a[person_id, date, time_of_day, activity_id] = 1 if person assigned activity at slot

Constraints:
    1. One activity per slot per person
    2. Skip locked slots (source=preload or source=manual)
    3. Activity distribution respects rotation_activity_requirements
    4. Total activity counts respect min/max from requirements
    5. LEC/ADV are expected to be preloaded (locked) and are not assigned here
"""

import time
from collections import defaultdict
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.activity import Activity, ActivityCategory
from app.models.block_assignment import BlockAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import Person
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.models.rotation_template import RotationTemplate
from app.utils.academic_blocks import get_block_dates
from app.utils.activity_locking import is_activity_preloaded
from app.utils.activity_naming import activity_code_from_name, activity_display_abbrev

logger = get_logger(__name__)

# Default weekly activity requirements (per week) when none are configured
DEFAULT_WEEKLY_C_MIN = 2
DEFAULT_WEEKLY_C_MAX = 4
DEFAULT_WEEKLY_SPECIALTY_MIN = 3
DEFAULT_WEEKLY_SPECIALTY_MAX = 4

# Day index cutoff for secondary rotations (day 15+ uses secondary)
BLOCK_HALF_DAY = 14

# Rotation activity types considered outpatient for activity solving
OUTPATIENT_ACTIVITY_TYPES = {"clinic", "outpatient"}


class CPSATActivitySolver:
    """
    CP-SAT solver for assigning activities to half-day slots.

    This solver operates on HalfDayAssignment records that were created
    by the expansion service but don't have activity_id set (or have
    source='solver' which can be overwritten).

    The solver respects:
    - Locked slots (source=preload or manual) - never touched
    - rotation_activity_requirements - determines which activities to assign
    - LEC/ADV are preloaded and therefore excluded from solver assignments
    """

    def __init__(
        self,
        session: Session,
        timeout_seconds: float = 60.0,
        num_workers: int = 4,
    ):
        self.session = session
        self.timeout_seconds = timeout_seconds
        self.num_workers = num_workers
        self._activity_cache: dict[str, Activity] = {}

    def solve(
        self,
        block_number: int,
        academic_year: int,
    ) -> dict[str, Any]:
        """
        Assign activities to half-day slots for a block.

        Args:
            block_number: Academic block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)

        Returns:
            Dictionary with:
                - success: True if solution found
                - assignments_updated: Number of slots with activity assigned
                - status: "optimal", "feasible", or "infeasible"
                - runtime_seconds: Solver runtime
        """
        try:
            from ortools.sat.python import cp_model
        except ImportError:
            logger.error("OR-Tools not installed. Run: pip install ortools>=9.8")
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "OR-Tools not installed",
            }

        start_time = time.time()

        # Get block date range
        block_dates = get_block_dates(block_number, academic_year)
        start_date = block_dates.start_date
        end_date = block_dates.end_date

        logger.info(
            f"Activity solver starting for Block {block_number}: "
            f"{start_date} to {end_date}"
        )

        # Load unlocked half-day slots
        slots = self._load_unlocked_slots(start_date, end_date)
        if not slots:
            logger.info("No unlocked slots to assign")
            return {
                "success": True,
                "assignments_updated": 0,
                "status": "no_work",
                "message": "All slots are locked or no slots exist",
            }

        logger.info(f"Found {len(slots)} unlocked slots to assign")

        # Resolve active rotation template per slot and week number
        slot_meta: dict[int, dict[str, Any]] = {}
        templates_by_id: dict[UUID, RotationTemplate] = {}
        for s_i, slot in enumerate(slots):
            template = self._get_active_rotation_template(
                slot.block_assignment, slot.date, start_date
            )
            if template:
                templates_by_id[template.id] = template
            week_number = self._get_week_number(slot.date, start_date)
            slot_meta[s_i] = {
                "person_id": slot.person_id,
                "template_id": template.id if template else None,
                "week": week_number,
            }

        # Load activity requirements for templates in scope
        requirements_by_template = self._load_activity_requirements(
            set(templates_by_id.keys())
        )

        # Ensure default requirements + rotation activities for outpatient templates
        requirements_by_template = self._ensure_default_requirements(
            templates_by_id, requirements_by_template
        )

        # Load activities after any default creation
        all_activities = self._load_activities()
        if not all_activities:
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "No activities found",
            }

        activity_by_id = {a.id: a for a in all_activities}

        # Candidate activities for solver: exclude preloaded/protected/time_off
        assignable_activities = [
            a for a in all_activities if not is_activity_preloaded(a)
        ]
        assignable_ids = {a.id for a in assignable_activities}
        if not assignable_ids:
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "No assignable activities (all locked/preloaded)",
            }

        # Get key activities
        clinic_activity = self._get_activity_by_code(
            "fm_clinic"
        ) or self._get_activity_by_code("C")

        # Create the CP model
        model = cp_model.CpModel()

        # Build allowed activity sets per template
        allowed_by_template: dict[UUID, list[UUID]] = {}
        for template_id, reqs in requirements_by_template.items():
            allowed_ids = []
            for req in reqs:
                if req.activity_id in assignable_ids and not is_activity_preloaded(
                    req.activity
                ):
                    allowed_ids.append(req.activity_id)
            # Deduplicate while preserving order
            seen = set()
            deduped = []
            for act_id in allowed_ids:
                if act_id not in seen:
                    seen.add(act_id)
                    deduped.append(act_id)
            if deduped:
                allowed_by_template[template_id] = deduped

        # Fallback: if a template has no requirements, allow all assignables
        fallback_allowed = sorted(
            assignable_ids,
            key=lambda act_id: activity_by_id.get(act_id).code
            if act_id in activity_by_id
            else "",
        )

        # ==================================================
        # DECISION VARIABLES
        # a[slot_idx, activity_id] = 1 if slot gets activity
        # ==================================================
        a: dict[tuple[int, UUID], Any] = {}
        slot_allowed: dict[int, list[UUID]] = {}

        for s_i, slot in enumerate(slots):
            template_id = slot_meta[s_i]["template_id"]
            allowed = allowed_by_template.get(template_id) if template_id else None
            if not allowed:
                if template_id:
                    logger.warning(
                        f"No activity requirements for template {template_id}, "
                        "falling back to all assignable activities"
                    )
                allowed = fallback_allowed
            slot_allowed[s_i] = allowed

            for act_id in allowed:
                act_code = (
                    activity_by_id.get(act_id).code
                    if act_id in activity_by_id
                    else "act"
                )
                safe_code = act_code.replace("-", "_")
                a[s_i, act_id] = model.NewBoolVar(f"a_{s_i}_{safe_code}")

        # ==================================================
        # CONSTRAINTS
        # ==================================================

        # Constraint 1: Exactly one activity per slot
        for s_i, allowed in slot_allowed.items():
            model.Add(sum(a[s_i, act_id] for act_id in allowed) == 1)

        # Constraint 2: Activity requirements (per week, per person, per rotation)
        slots_by_key: dict[tuple[UUID, UUID, int], list[int]] = defaultdict(list)
        for s_i, meta in slot_meta.items():
            template_id = meta["template_id"]
            if not template_id:
                continue
            key = (meta["person_id"], template_id, meta["week"])
            slots_by_key[key].append(s_i)

        locked_counts: dict[tuple[UUID, UUID, int, UUID], int] = defaultdict(int)
        person_ids = {meta["person_id"] for meta in slot_meta.values()}
        locked_slots = self._load_locked_slots(start_date, end_date, person_ids)
        for locked in locked_slots:
            if not locked.activity_id:
                continue
            template = self._get_active_rotation_template(
                locked.block_assignment, locked.date, start_date
            )
            if not template:
                continue
            week_number = self._get_week_number(locked.date, start_date)
            locked_counts[
                (locked.person_id, template.id, week_number, locked.activity_id)
            ] += 1

        constraint_count = 0
        for (person_id, template_id, week), slot_indices in slots_by_key.items():
            reqs = requirements_by_template.get(template_id, [])
            if not reqs:
                continue
            for req in reqs:
                if req.activity_id not in assignable_ids:
                    continue
                if req.applicable_weeks and week not in req.applicable_weeks:
                    continue

                vars_for_req = [
                    a[s_i, req.activity_id]
                    for s_i in slot_indices
                    if req.activity_id in slot_allowed[s_i]
                ]
                if not vars_for_req:
                    continue

                locked_count = locked_counts.get(
                    (person_id, template_id, week, req.activity_id), 0
                )
                min_needed = max(0, req.min_halfdays - locked_count)
                max_allowed = max(0, req.max_halfdays - locked_count)

                if min_needed > len(vars_for_req):
                    logger.warning(
                        "Clamping min requirement for person=%s template=%s "
                        "week=%s activity=%s: min=%s available=%s",
                        person_id,
                        template_id,
                        week,
                        req.activity_id,
                        min_needed,
                        len(vars_for_req),
                    )
                    min_needed = len(vars_for_req)

                if max_allowed < 0:
                    max_allowed = 0
                if max_allowed > len(vars_for_req):
                    max_allowed = len(vars_for_req)

                model.Add(sum(vars_for_req) >= min_needed)
                model.Add(sum(vars_for_req) <= max_allowed)
                constraint_count += 1

        if constraint_count:
            logger.info(f"Added {constraint_count} activity requirement constraints")

        # ==================================================
        # CONSTRAINT: Physical Capacity (Max 6 per slot)
        # Session 136: Clinic has limited exam rooms
        # Includes baseline occupancy from locked/preloaded slots.
        # ==================================================
        MAX_PHYSICAL_CAPACITY = 6

        # Group slots by (date, time_of_day)
        slot_groups: dict[tuple[date, str], list[int]] = defaultdict(list)
        for s_i, slot in enumerate(slots):
            key = (slot.date, slot.time_of_day)
            slot_groups[key].append(s_i)

        # Baseline occupancy from locked/preloaded slots not in solver
        slot_ids = {slot.id for slot in slots}
        baseline_capacity: dict[tuple[date, str], int] = defaultdict(int)
        baseline_stmt = (
            select(HalfDayAssignment)
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .where(
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
                Activity.counts_toward_physical_capacity == True,  # noqa: E712
            )
        )
        for assignment in self.session.execute(baseline_stmt).scalars():
            if assignment.id in slot_ids:
                continue  # handled by solver
            baseline_capacity[(assignment.date, assignment.time_of_day)] += 1

        # For each time slot, sum(clinical activities) + baseline <= MAX
        clinical_activity_ids = {
            activity.id
            for activity in assignable_activities
            if activity.counts_toward_physical_capacity
        }
        if clinical_activity_ids:
            for (slot_date, time_of_day), slot_indices in slot_groups.items():
                # Skip weekends
                if slot_date.weekday() >= 5:
                    continue

                # Sum of clinical assignments for this slot
                slot_clinic_sum = sum(
                    a[s_i, act_id]
                    for s_i in slot_indices
                    for act_id in slot_allowed[s_i]
                    if act_id in clinical_activity_ids
                )

                baseline = baseline_capacity.get((slot_date, time_of_day), 0)
                # Hard constraint: at most 6 in clinic per slot
                model.Add(slot_clinic_sum + baseline <= MAX_PHYSICAL_CAPACITY)

            logger.info(
                f"Added physical capacity constraint (max {MAX_PHYSICAL_CAPACITY}) "
                f"for {len(slot_groups)} time slots with baseline occupancy"
            )

        # ==================================================
        # OBJECTIVE: Maximize clinic (C) assignments
        # (Most slots should be clinic for outpatient rotations)
        # Constraint above limits this to respect physical capacity
        # ==================================================
        if clinic_activity and clinic_activity.id in assignable_ids:
            clinic_id = clinic_activity.id
            clinic_count = sum(
                a[s_i, clinic_id]
                for s_i in slot_allowed
                if clinic_id in slot_allowed[s_i]
            )
            model.Maximize(clinic_count)

        # ==================================================
        # SOLVE
        # ==================================================
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.timeout_seconds
        solver.parameters.num_search_workers = self.num_workers

        status = solver.Solve(model)
        runtime = time.time() - start_time

        status_name = solver.StatusName(status)
        logger.info(f"Activity solver status: {status_name} ({runtime:.2f}s)")

        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "infeasible",
                "solver_status": status_name,
                "runtime_seconds": runtime,
            }

        # ==================================================
        # EXTRACT SOLUTION & UPDATE DATABASE
        # ==================================================
        updated = 0
        for s_i, slot in enumerate(slots):
            for act_id in slot_allowed[s_i]:
                if solver.Value(a[s_i, act_id]) == 1:
                    slot.activity_id = act_id
                    slot.source = AssignmentSource.SOLVER.value
                    updated += 1
                    break

        self.session.flush()
        logger.info(f"Activity solver updated {updated} slots")

        return {
            "success": True,
            "assignments_updated": updated,
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "solver_status": status_name,
            "runtime_seconds": runtime,
        }

    def _load_activities(self) -> list[Activity]:
        """Load all active (non-archived) activities."""
        stmt = select(Activity).where(~Activity.is_archived)
        result = self.session.execute(stmt)
        activities = list(result.scalars().all())

        # Cache for lookup
        for activity in activities:
            self._activity_cache[activity.code] = activity
            if activity.display_abbreviation:
                self._activity_cache[activity.display_abbreviation] = activity

        return activities

    def _get_activity_by_code(self, code: str) -> Activity | None:
        """Get activity by code from cache."""
        return self._activity_cache.get(code)

    def _get_week_number(self, slot_date: date, block_start: date) -> int:
        """Get week number (1-4) for a slot within a block."""
        days_into_block = (slot_date - block_start).days
        return (days_into_block // 7) + 1

    def _get_active_rotation_template(
        self,
        block_assignment: BlockAssignment | None,
        slot_date: date,
        block_start: date,
    ) -> RotationTemplate | None:
        """Resolve primary vs secondary rotation for a given slot date."""
        if not block_assignment:
            return None
        if block_assignment.secondary_rotation_template_id:
            day_in_block = (slot_date - block_start).days + 1
            if day_in_block > BLOCK_HALF_DAY:
                return block_assignment.secondary_rotation_template
        return block_assignment.rotation_template

    def _ensure_activity(
        self,
        name: str,
        code: str,
        display_abbreviation: str,
        activity_category: str,
        counts_toward_physical_capacity: bool,
        font_color: str | None = None,
        background_color: str | None = None,
    ) -> Activity:
        """Find or create an activity by name/code."""
        stmt = select(Activity).where(Activity.name == name)
        activity = self.session.execute(stmt).scalars().first()
        if activity:
            return activity

        stmt = select(Activity).where(Activity.code.ilike(code))
        activity = self.session.execute(stmt).scalars().first()
        if activity:
            return activity

        activity = Activity(
            name=name,
            code=code,
            display_abbreviation=display_abbreviation,
            activity_category=activity_category,
            font_color=font_color,
            background_color=background_color,
            requires_supervision=True,
            is_protected=False,
            counts_toward_clinical_hours=True,
            provides_supervision=False,
            counts_toward_physical_capacity=counts_toward_physical_capacity,
            display_order=0,
        )
        self.session.add(activity)
        self.session.flush()

        # Update cache for lookups
        self._activity_cache[activity.code] = activity
        if activity.display_abbreviation:
            self._activity_cache[activity.display_abbreviation] = activity

        logger.info(f"Created activity '{activity.name}' (code={activity.code})")
        return activity

    def _ensure_rotation_activity(self, template: RotationTemplate) -> Activity:
        """Ensure a specialty activity exists for this rotation template."""
        code = activity_code_from_name(template.name)
        display_abbrev = activity_display_abbrev(
            template.name,
            template.display_abbreviation,
            template.abbreviation,
        )
        return self._ensure_activity(
            name=template.name,
            code=code,
            display_abbreviation=display_abbrev,
            activity_category=ActivityCategory.CLINICAL.value,
            counts_toward_physical_capacity=True,
            font_color=template.font_color,
            background_color=template.background_color,
        )

    def _ensure_default_requirements(
        self,
        templates_by_id: dict[UUID, RotationTemplate],
        requirements_by_template: dict[UUID, list[RotationActivityRequirement]],
    ) -> dict[UUID, list[RotationActivityRequirement]]:
        """Create default weekly activity requirements for outpatient templates."""
        created = 0

        for template_id, template in templates_by_id.items():
            existing = requirements_by_template.get(template_id, [])
            if existing:
                continue
            if (template.activity_type or "").lower() not in OUTPATIENT_ACTIVITY_TYPES:
                continue

            clinic_activity = self._ensure_activity(
                name="FM Clinic",
                code="fm_clinic",
                display_abbreviation="C",
                activity_category=ActivityCategory.CLINICAL.value,
                counts_toward_physical_capacity=True,
            )
            specialty_activity = self._ensure_rotation_activity(template)

            reqs: list[RotationActivityRequirement] = []
            for week in (1, 2, 3, 4):
                reqs.append(
                    RotationActivityRequirement(
                        rotation_template_id=template.id,
                        activity_id=clinic_activity.id,
                        min_halfdays=DEFAULT_WEEKLY_C_MIN,
                        max_halfdays=DEFAULT_WEEKLY_C_MAX,
                        applicable_weeks=[week],
                        prefer_full_days=True,
                        priority=80,
                    )
                )
                reqs.append(
                    RotationActivityRequirement(
                        rotation_template_id=template.id,
                        activity_id=specialty_activity.id,
                        min_halfdays=DEFAULT_WEEKLY_SPECIALTY_MIN,
                        max_halfdays=DEFAULT_WEEKLY_SPECIALTY_MAX,
                        applicable_weeks=[week],
                        prefer_full_days=True,
                        priority=80,
                    )
                )

            self.session.add_all(reqs)
            self.session.flush()
            requirements_by_template[template_id] = reqs
            created += len(reqs)

            logger.info(
                f"Created default activity requirements for template {template.name}"
            )

        if created:
            logger.info(f"Created {created} default activity requirements")

        return requirements_by_template

    def _load_slots(
        self,
        start_date: date,
        end_date: date,
        sources: list[str],
        person_ids: set[UUID] | None = None,
    ) -> list[HalfDayAssignment]:
        """Load half-day slots with relationships and source filter."""
        stmt = (
            select(HalfDayAssignment)
            .options(
                selectinload(HalfDayAssignment.activity),
                selectinload(HalfDayAssignment.block_assignment).selectinload(
                    BlockAssignment.rotation_template
                ),
                selectinload(HalfDayAssignment.block_assignment).selectinload(
                    BlockAssignment.secondary_rotation_template
                ),
            )
            .join(Person, HalfDayAssignment.person_id == Person.id)
            .where(
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
                HalfDayAssignment.source.in_(sources),
                Person.type != "faculty",
            )
        )
        if person_ids:
            stmt = stmt.where(HalfDayAssignment.person_id.in_(person_ids))
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def _load_unlocked_slots(
        self, start_date: date, end_date: date
    ) -> list[HalfDayAssignment]:
        """Load half-day slots that can be assigned activities.

        IMPORTANT: Excludes faculty slots. Faculty assignments are handled by
        FacultyAssignmentExpansionService and should NOT be overwritten by
        the activity solver. Faculty get admin time (GME/DFM), not solver activities.
        """
        return self._load_slots(
            start_date,
            end_date,
            [AssignmentSource.SOLVER.value, AssignmentSource.TEMPLATE.value],
        )

    def _load_locked_slots(
        self,
        start_date: date,
        end_date: date,
        person_ids: set[UUID],
    ) -> list[HalfDayAssignment]:
        """Load locked (preload/manual) slots for baseline counts."""
        return self._load_slots(
            start_date,
            end_date,
            [AssignmentSource.PRELOAD.value, AssignmentSource.MANUAL.value],
            person_ids=person_ids,
        )

    def _load_activity_requirements(
        self, template_ids: set[UUID]
    ) -> dict[UUID, list[RotationActivityRequirement]]:
        """Load rotation activity requirements for specific templates."""
        if not template_ids:
            return {}

        stmt = (
            select(RotationActivityRequirement)
            .where(RotationActivityRequirement.rotation_template_id.in_(template_ids))
            .options(
                selectinload(RotationActivityRequirement.activity),
                selectinload(RotationActivityRequirement.rotation_template),
            )
        )
        result = self.session.execute(stmt)
        requirements = list(result.scalars().all())

        by_template: dict[UUID, list[RotationActivityRequirement]] = defaultdict(list)
        for req in requirements:
            by_template[req.rotation_template_id].append(req)
        return by_template


def solve_activities(
    session: Session,
    block_number: int,
    academic_year: int,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    """
    Convenience function to run activity solver.

    Args:
        session: Database session
        block_number: Block number (1-13)
        academic_year: Academic year
        timeout_seconds: Solver timeout

    Returns:
        Solver result dictionary
    """
    solver = CPSATActivitySolver(session, timeout_seconds=timeout_seconds)
    return solver.solve(block_number, academic_year)
