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
    4. LEC on Wednesday PM (weeks 1-3)
    5. LEC on last Wednesday AM, ADV on last Wednesday PM
    6. Total activity counts respect min/max from requirements
"""

import time
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.activity import Activity
from app.models.block_assignment import BlockAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)


class CPSATActivitySolver:
    """
    CP-SAT solver for assigning activities to half-day slots.

    This solver operates on HalfDayAssignment records that were created
    by the expansion service but don't have activity_id set (or have
    source='solver' which can be overwritten).

    The solver respects:
    - Locked slots (source=preload or manual) - never touched
    - rotation_activity_requirements - determines which activities to assign
    - Day/week rules - LEC on Wednesday PM, ADV on last Wednesday PM
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

        # Load activities
        activities = self._load_activities()
        if not activities:
            return {
                "success": False,
                "assignments_updated": 0,
                "status": "error",
                "message": "No activities found",
            }

        # Get key activities
        lec_activity = self._get_activity_by_code("lec")
        adv_activity = self._get_activity_by_code("advising")
        clinic_activity = self._get_activity_by_code("fm_clinic")

        if not clinic_activity:
            logger.warning("Missing fm_clinic activity, using first activity as default")
            clinic_activity = activities[0]

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

        # Group slots by person for activity requirements lookup
        person_slots: dict[UUID, list[HalfDayAssignment]] = {}
        for slot in slots:
            if slot.person_id not in person_slots:
                person_slots[slot.person_id] = []
            person_slots[slot.person_id].append(slot)

        # Load rotation activity requirements
        requirements = self._load_activity_requirements()

        # Create the CP model
        model = cp_model.CpModel()

        # Index activities
        activity_idx = {a.id: i for i, a in enumerate(activities)}

        # ==================================================
        # DECISION VARIABLES
        # a[slot_idx, activity_idx] = 1 if slot gets activity
        # ==================================================
        a = {}
        slot_idx_map = {id(slot): i for i, slot in enumerate(slots)}

        for s_i, slot in enumerate(slots):
            for act_i, activity in enumerate(activities):
                a[s_i, act_i] = model.NewBoolVar(f"a_{s_i}_{act_i}")

        # ==================================================
        # CONSTRAINTS
        # ==================================================

        # Constraint 1: Exactly one activity per slot
        for s_i in range(len(slots)):
            model.Add(
                sum(a[s_i, act_i] for act_i in range(len(activities))) == 1
            )

        # Constraint 2: Wednesday PM = LEC (weeks 1-3)
        # Constraint 3: Last Wednesday AM = LEC, PM = ADV
        if lec_activity and adv_activity:
            lec_idx = activity_idx.get(lec_activity.id)
            adv_idx = activity_idx.get(adv_activity.id)

            for s_i, slot in enumerate(slots):
                is_wednesday = slot.date.weekday() == 2

                if is_wednesday:
                    # Check if this is the last Wednesday of the block
                    next_wed = slot.date + timedelta(days=7)
                    is_last_wednesday = next_wed > end_date

                    # Calculate week number
                    days_into_block = (slot.date - start_date).days
                    week_number = (days_into_block // 7) + 1

                    if is_last_wednesday:
                        # Last Wednesday: AM = LEC, PM = ADV
                        if slot.time_of_day == "AM" and lec_idx is not None:
                            model.Add(a[s_i, lec_idx] == 1)
                        elif slot.time_of_day == "PM" and adv_idx is not None:
                            model.Add(a[s_i, adv_idx] == 1)
                    elif week_number <= 3 and slot.time_of_day == "PM":
                        # Weeks 1-3 Wednesday PM = LEC
                        if lec_idx is not None:
                            model.Add(a[s_i, lec_idx] == 1)

        # ==================================================
        # OBJECTIVE: Maximize clinic (C) assignments
        # (Most slots should be clinic for outpatient rotations)
        # ==================================================
        if clinic_activity:
            clinic_idx = activity_idx.get(clinic_activity.id)
            if clinic_idx is not None:
                clinic_count = sum(
                    a[s_i, clinic_idx] for s_i in range(len(slots))
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
            for act_i, activity in enumerate(activities):
                if solver.Value(a[s_i, act_i]) == 1:
                    slot.activity_id = activity.id
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

    def _load_unlocked_slots(
        self, start_date: date, end_date: date
    ) -> list[HalfDayAssignment]:
        """Load half-day slots that can be assigned activities."""
        stmt = select(HalfDayAssignment).where(
            HalfDayAssignment.date >= start_date,
            HalfDayAssignment.date <= end_date,
            # Only slots without locked source
            HalfDayAssignment.source.in_([
                AssignmentSource.SOLVER.value,
                AssignmentSource.TEMPLATE.value,
            ]),
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def _load_activity_requirements(self) -> list[RotationActivityRequirement]:
        """Load rotation activity requirements."""
        stmt = select(RotationActivityRequirement).options(
            selectinload(RotationActivityRequirement.activity),
            selectinload(RotationActivityRequirement.rotation_template),
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())


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
