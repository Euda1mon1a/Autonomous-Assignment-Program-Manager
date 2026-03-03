"""
Temporal and Time-based Constraints.

This module contains constraints related to specific time periods,
days of the week, and scheduling patterns.

Classes:
    - WednesdayAMInternOnlyConstraint: Wednesday AM clinic for interns only (hard)
"""

import logging
from typing import Any

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class WednesdayAMInternOnlyConstraint(HardConstraint):
    """
    Ensures Wednesday morning clinic is staffed by interns (PGY-1) only.

    Wednesday morning is continuity clinic day for interns. This protected
    time allows them to maintain longitudinal patient relationships and
    should not be disrupted by PGY-2/3 resident assignments.

    Faculty supervision is still required per supervision ratios.

    Note: Rare exceptions may be needed - the constraint can be disabled
    for specific blocks if necessary.
    """

    WEDNESDAY = 2  # Python weekday: Monday=0, Tuesday=1, Wednesday=2

    def __init__(self) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="WednesdayAMInternOnly",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def _is_wednesday_am(self, block: Any) -> bool:
        """Check if a block is Wednesday AM."""
        return (
            hasattr(block, "date")
            and block.date.weekday() == self.WEDNESDAY
            and block.time_of_day == "AM"
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Prevent non-intern assignments on Wednesday AM."""
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        # Identify clinic templates
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            return

        # Get PGY levels for residents
        pgy_levels = {r.id: r.pgy_level for r in context.residents}

        count = 0
        # For Wednesday AM blocks, prevent non-PGY-1 clinic assignments
        for block in context.blocks:
            if not self._is_wednesday_am(block):
                continue

            b_i = context.block_idx[block.id]

            for template in context.templates:
                if template.id not in clinic_template_ids:
                    continue

                t_i = context.template_idx[template.id]

                for r in context.residents:
                    # Skip PGY-1 (they are allowed)
                    if pgy_levels.get(r.id) == 1:
                        continue

                    r_i = context.resident_idx[r.id]
                    if (r_i, b_i, t_i) in template_vars:
                        # Force non-intern to 0 on Wednesday AM clinic
                        model.Add(template_vars[r_i, b_i, t_i] == 0)
                        count += 1

        logger.info("Added %d WednesdayAMInternOnly constraints", count)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Prevent non-intern assignments on Wednesday AM using PuLP."""
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            return

        pgy_levels = {r.id: r.pgy_level for r in context.residents}

        for block in context.blocks:
            if not self._is_wednesday_am(block):
                continue

            b_i = context.block_idx[block.id]

            for template in context.templates:
                if template.id not in clinic_template_ids:
                    continue

                t_i = context.template_idx[template.id]

                for r in context.residents:
                    if pgy_levels.get(r.id) == 1:
                        continue

                    r_i = context.resident_idx[r.id]
                    if (r_i, b_i, t_i) in template_vars:
                        model += (
                            template_vars[(r_i, b_i, t_i)] == 0,
                            f"wed_am_intern_only_{r_i}_{b_i}_{t_i}",
                        )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check that Wednesday AM clinic has only interns."""
        violations: list[ConstraintViolation] = []

        # Build lookup tables
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        if not clinic_template_ids:
            return ConstraintResult(satisfied=True, violations=[])

        pgy_levels = {r.id: r.pgy_level for r in context.residents}
        resident_names = {r.id: r.name for r in context.residents}
        block_info = {b.id: b for b in context.blocks}

        for a in assignments:
            # Only check clinic assignments
            if a.rotation_template_id not in clinic_template_ids:
                continue

            # Only check resident assignments (not faculty)
            if a.person_id not in pgy_levels:
                continue

            block = block_info.get(a.block_id)
            if not block or not self._is_wednesday_am(block):
                continue

            # Check if resident is NOT PGY-1
            pgy = pgy_levels.get(a.person_id)
            if pgy and pgy != 1:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"PGY-{pgy} resident {resident_names.get(a.person_id, 'Unknown')} assigned to Wednesday AM clinic on {block.date}",
                        person_id=a.person_id,
                        block_id=a.block_id,
                        details={"pgy_level": pgy, "date": str(block.date)},
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class WednesdayPMSingleFacultyConstraint(SoftConstraint):
    """
    Prefers exactly 1 faculty assigned to clinic on Wednesday PM.

    On 1st, 2nd, 3rd Wednesday each month, residents have PM academics
    (Lecture, Clinic Meeting, Simulation). One faculty should cover clinic.

    Soft constraint: penalizes deviation from exactly 1 faculty.
    Prevents INFEASIBLE when preload conflicts arise (was hard prior to PR #1228).

    Note: This does NOT apply to 4th Wednesday (inverted schedule).
    """

    WEDNESDAY = 2

    def __init__(self, weight: float = 50.0) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="WednesdayPMSingleFaculty",
            constraint_type=ConstraintType.ROTATION,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def _is_regular_wednesday_pm(self, block: Any) -> bool:
        """Check if block is 1st/2nd/3rd Wednesday PM."""
        if not hasattr(block, "date"):
            return False
        if block.date.weekday() != self.WEDNESDAY:
            return False
        if getattr(block, "time_of_day", None) != "PM":
            return False
        # Check if 4th Wednesday (day 22-28)
        if block.date.day >= 22:
            return False
        return True

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Penalize deviation from exactly 1 faculty in clinic on regular Wed PM."""
        faculty_template_vars = variables.get("faculty_template_assignments", {})
        if not faculty_template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }
        if not clinic_template_ids:
            return

        objective_terms = variables.setdefault("objective_terms", [])
        count = 0
        for block in context.blocks:
            if not self._is_regular_wednesday_pm(block):
                continue

            b_i = context.block_idx[block.id]
            faculty_clinic_vars = []

            for template in context.templates:
                if template.id not in clinic_template_ids:
                    continue
                t_i = context.template_idx[template.id]

                for f in context.faculty:
                    f_i = context.faculty_idx.get(f.id)
                    if f_i is not None and (f_i, b_i, t_i) in faculty_template_vars:
                        faculty_clinic_vars.append(faculty_template_vars[f_i, b_i, t_i])

            if faculty_clinic_vars:
                n = len(faculty_clinic_vars)
                # IntVar for the sum of clinic assignments this Wed PM
                sum_var = model.NewIntVar(0, n, f"wed_pm_sum_{b_i}")
                model.Add(sum_var == sum(faculty_clinic_vars))

                # Deviation from target of 1: |sum - 1|
                dev_var = model.NewIntVar(0, n, f"wed_pm_dev_{b_i}")
                model.AddAbsEquality(dev_var, sum_var - 1)

                objective_terms.append((dev_var, int(self.weight)))
                count += 1

        logger.info("Added %d WednesdayPMSingleFaculty soft penalties", count)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Penalize deviation from exactly 1 faculty in clinic on regular Wed PM (PuLP)."""
        import pulp

        faculty_template_vars = variables.get("faculty_template_assignments", {})
        if not faculty_template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }
        if not clinic_template_ids:
            return

        objective_terms = variables.setdefault("objective_terms", [])

        for block in context.blocks:
            if not self._is_regular_wednesday_pm(block):
                continue

            b_i = context.block_idx[block.id]
            faculty_clinic_vars = []

            for template in context.templates:
                if template.id not in clinic_template_ids:
                    continue
                t_i = context.template_idx[template.id]

                for f in context.faculty:
                    f_i = context.faculty_idx.get(f.id)
                    if f_i is not None and (f_i, b_i, t_i) in faculty_template_vars:
                        faculty_clinic_vars.append(faculty_template_vars[f_i, b_i, t_i])

            if faculty_clinic_vars:
                sum_expr = pulp.lpSum(faculty_clinic_vars)
                # Decompose |sum - 1| into over + under
                over = pulp.LpVariable(f"wed_pm_over_{b_i}", lowBound=0, cat="Integer")
                under = pulp.LpVariable(
                    f"wed_pm_under_{b_i}", lowBound=0, cat="Integer"
                )
                model += (sum_expr == 1 + over - under, f"wed_pm_dev_{b_i}")

                objective_terms.append((over, int(self.weight)))
                objective_terms.append((under, int(self.weight)))

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check faculty count on regular Wed PM clinic (soft — always satisfied)."""
        violations: list[ConstraintViolation] = []
        total_penalty = 0.0

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        # Early return if no clinic templates
        if not clinic_template_ids:
            return ConstraintResult(satisfied=True, violations=[])

        faculty_ids = {f.id for f in context.faculty}

        # Group assignments by block
        for block in context.blocks:
            if not self._is_regular_wednesday_pm(block):
                continue

            faculty_in_clinic = [
                a
                for a in assignments
                if a.block_id == block.id
                and a.person_id in faculty_ids
                and a.rotation_template_id in clinic_template_ids
            ]

            if len(faculty_in_clinic) != 1:
                deviation = abs(len(faculty_in_clinic) - 1)
                total_penalty += self.weight * deviation
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message=f"Wed PM {block.date}: {len(faculty_in_clinic)} faculty in clinic (prefer exactly 1)",
                        block_id=block.id,
                        details={
                            "count": len(faculty_in_clinic),
                            "date": str(block.date),
                        },
                    )
                )

        return ConstraintResult(
            satisfied=True,  # Soft constraint — never causes infeasibility
            violations=violations,
            penalty=total_penalty,
        )


class InvertedWednesdayConstraint(SoftConstraint):
    """
    Ensures final Wednesday has single faculty AM and different faculty PM.

    On the final Wednesday (often called "inverted" or "5th Wednesday"):
    - Residents have Lecture AM, Advising PM (no clinic)
    - AM: Exactly 1 faculty in clinic
    - PM: Exactly 1 DIFFERENT faculty in clinic

    This is implemented as a soft constraint so it doesn't cause INFEASIBLE states
    if leave or other hard constraints prevent the exact coverage.
    """

    WEDNESDAY = 2

    def __init__(self, weight: float = 50.0) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="InvertedWednesday",
            constraint_type=ConstraintType.ROTATION,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def _is_final_wednesday(self, block, context) -> bool:
        """Check if block is exactly the final Wednesday of the scheduling context."""
        if not hasattr(block, "date"):
            return False
        if block.date.weekday() != self.WEDNESDAY:
            return False
        if not context.end_date:
            return False
        # If it's a Wednesday in the last 7 days of the context
        return (context.end_date - block.date).days < 7

    def add_to_cpsat(
        self,
        model,
        variables,
        context,
    ) -> None:
        """Enforce 1 faculty AM, 1 different faculty PM on final Wednesday."""
        fac_clinic = variables.get("fac_clinic", {})
        if not fac_clinic:
            return

        # Group final Wednesday blocks by date and time
        final_wed_groups = {}
        for block in context.blocks:
            if not self._is_final_wednesday(block, context):
                continue
            date_str = str(block.date)
            if date_str not in final_wed_groups:
                final_wed_groups[date_str] = {"AM": [], "PM": []}
            tod = getattr(block, "time_of_day", "AM")
            final_wed_groups[date_str][tod].append(block)

        objective_terms = variables.setdefault("objective_terms", [])
        penalty_weight = int(self.weight)

        for date_str, blocks_by_time in final_wed_groups.items():
            am_blocks = blocks_by_time.get("AM", [])
            pm_blocks = blocks_by_time.get("PM", [])

            am_vars = []
            pm_vars = []

            # Collect AM faculty clinic variables
            for block in am_blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue
                for f in context.faculty:
                    f_i = context.faculty_idx.get(f.id)
                    if f_i is not None and (f_i, b_i) in fac_clinic:
                        am_vars.append(fac_clinic[f_i, b_i])

            # Collect PM faculty clinic variables
            for block in pm_blocks:
                b_i = context.block_idx.get(block.id)
                if b_i is None:
                    continue
                for f in context.faculty:
                    f_i = context.faculty_idx.get(f.id)
                    if f_i is not None and (f_i, b_i) in fac_clinic:
                        pm_vars.append(fac_clinic[f_i, b_i])

            # Exactly 1 faculty AM
            if am_vars:
                am_sum = model.NewIntVar(
                    0, len(am_vars), f"final_wed_am_sum_{date_str}"
                )
                model.Add(am_sum == sum(am_vars))
                am_dev = model.NewIntVar(
                    0, len(am_vars), f"final_wed_am_dev_{date_str}"
                )
                model.AddAbsEquality(am_dev, am_sum - 1)
                objective_terms.append((am_dev, penalty_weight))

            # Exactly 1 faculty PM
            if pm_vars:
                pm_sum = model.NewIntVar(
                    0, len(pm_vars), f"final_wed_pm_sum_{date_str}"
                )
                model.Add(pm_sum == sum(pm_vars))
                pm_dev = model.NewIntVar(
                    0, len(pm_vars), f"final_wed_pm_dev_{date_str}"
                )
                model.AddAbsEquality(pm_dev, pm_sum - 1)
                objective_terms.append((pm_dev, penalty_weight))

            # Different faculty AM vs PM
            if am_vars and pm_vars:
                am_b_i = context.block_idx[am_blocks[0].id]
                pm_b_i = context.block_idx[pm_blocks[0].id]
                for f in context.faculty:
                    f_i = context.faculty_idx.get(f.id)
                    if (
                        f_i is not None
                        and (f_i, am_b_i) in fac_clinic
                        and (f_i, pm_b_i) in fac_clinic
                    ):
                        both_on = model.NewBoolVar(f"final_wed_both_{f_i}_{date_str}")
                        model.AddBoolAnd(
                            [fac_clinic[f_i, am_b_i], fac_clinic[f_i, pm_b_i]]
                        ).OnlyEnforceIf(both_on)
                        model.AddBoolOr(
                            [
                                fac_clinic[f_i, am_b_i].Not(),
                                fac_clinic[f_i, pm_b_i].Not(),
                            ]
                        ).OnlyEnforceIf(both_on.Not())
                        objective_terms.append((both_on, penalty_weight))

    def add_to_pulp(self, model, variables, context) -> None:
        pass  # CP-SAT only

    def validate(self, assignments, context) -> ConstraintResult:
        violations = []
        faculty_ids = {f.id for f in context.faculty}

        final_wed_dates = {}
        for block in context.blocks:
            if not self._is_final_wednesday(block, context):
                continue
            date_str = str(block.date)
            if date_str not in final_wed_dates:
                final_wed_dates[date_str] = {"AM": [], "PM": []}
            final_wed_dates[date_str][block.time_of_day].append(block)

        total_penalty = 0.0

        for date_str, blocks_by_time in final_wed_dates.items():
            am_faculty = set()
            pm_faculty = set()

            for block in blocks_by_time.get("AM", []):
                for a in assignments:
                    if (
                        a.block_id == block.id
                        and a.person_id in faculty_ids
                        and a.activity_code
                        in ("C", "fm_clinic", "cv", "sm_clinic", "c40")
                    ):
                        am_faculty.add(a.person_id)

            for block in blocks_by_time.get("PM", []):
                for a in assignments:
                    if (
                        a.block_id == block.id
                        and a.person_id in faculty_ids
                        and a.activity_code
                        in ("C", "fm_clinic", "cv", "sm_clinic", "c40")
                    ):
                        pm_faculty.add(a.person_id)

            if len(am_faculty) != 1:
                total_penalty += self.weight * abs(len(am_faculty) - 1)
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message=f"Final Wed {date_str} AM: {len(am_faculty)} faculty (need 1)",
                        details={
                            "date": date_str,
                            "time": "AM",
                            "count": len(am_faculty),
                        },
                    )
                )

            if len(pm_faculty) != 1:
                total_penalty += self.weight * abs(len(pm_faculty) - 1)
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message=f"Final Wed {date_str} PM: {len(pm_faculty)} faculty (need 1)",
                        details={
                            "date": date_str,
                            "time": "PM",
                            "count": len(pm_faculty),
                        },
                    )
                )

            if am_faculty and pm_faculty and am_faculty == pm_faculty:
                total_penalty += self.weight
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM",
                        message=f"Final Wed {date_str}: Same faculty AM and PM",
                        details={"date": date_str, "faculty": list(am_faculty)},
                    )
                )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )
