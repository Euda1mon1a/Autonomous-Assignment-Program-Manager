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


class WednesdayPMSingleFacultyConstraint(HardConstraint):
    """
    Ensures exactly 1 faculty is assigned to clinic on Wednesday PM.

    On 1st, 2nd, 3rd Wednesday each month, residents have PM academics
    (Lecture, Clinic Meeting, Simulation). One faculty must cover clinic.

    Note: This does NOT apply to 4th Wednesday (inverted schedule).
    """

    WEDNESDAY = 2

    def __init__(self) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="WednesdayPMSingleFaculty",
            constraint_type=ConstraintType.ROTATION,
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
        """Enforce exactly 1 faculty in clinic on regular Wed PM."""
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

            # Exactly 1 faculty in clinic
            if faculty_clinic_vars:
                model.Add(sum(faculty_clinic_vars) == 1)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce exactly 1 faculty in clinic on regular Wed PM (PuLP)."""
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

            # Exactly 1 faculty in clinic
            if faculty_clinic_vars:
                model += (
                    pulp.lpSum(faculty_clinic_vars) == 1,
                    f"wed_pm_single_faculty_{b_i}",
                )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check that exactly 1 faculty covers regular Wed PM clinic."""
        violations: list[ConstraintViolation] = []

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
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"Wed PM {block.date}: {len(faculty_in_clinic)} faculty in clinic (need exactly 1)",
                        block_id=block.id,
                        details={
                            "count": len(faculty_in_clinic),
                            "date": str(block.date),
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class InvertedWednesdayConstraint(HardConstraint):
    """
    Ensures 4th Wednesday has single faculty AM and different faculty PM.

    On inverted (4th) Wednesday:
    - Residents have Lecture AM, Advising PM (no clinic)
    - AM: Exactly 1 faculty in clinic
    - PM: Exactly 1 DIFFERENT faculty in clinic

    Faculty assignments should be equitable across the year.
    """

    WEDNESDAY = 2

    def __init__(self) -> None:
        """Initialize the constraint."""
        super().__init__(
            name="InvertedWednesday",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def _is_fourth_wednesday(self, block: Any) -> bool:
        """Check if block is exactly the 4th Wednesday of month."""
        if not hasattr(block, "date"):
            return False
        if block.date.weekday() != self.WEDNESDAY:
            return False
        # 4th Wednesday: day 22-28 only (5th would be 29-31)
        return 22 <= block.date.day <= 28

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce 1 faculty AM, 1 different faculty PM on 4th Wednesday."""
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

        # Group 4th Wednesday blocks by date and time
        fourth_wed_groups: dict[str, dict[str, list]] = {}
        for block in context.blocks:
            if not self._is_fourth_wednesday(block):
                continue
            date_str = str(block.date)
            if date_str not in fourth_wed_groups:
                fourth_wed_groups[date_str] = {"AM": [], "PM": []}
            tod = getattr(block, "time_of_day", "AM")
            fourth_wed_groups[date_str][tod].append(block)

        for date_str, blocks_by_time in fourth_wed_groups.items():
            am_blocks = blocks_by_time.get("AM", [])
            pm_blocks = blocks_by_time.get("PM", [])

            am_vars = []
            pm_vars = []

            # Collect AM faculty clinic variables
            for block in am_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    if template.id not in clinic_template_ids:
                        continue
                    t_i = context.template_idx[template.id]
                    for f in context.faculty:
                        f_i = context.faculty_idx.get(f.id)
                        if f_i is not None and (f_i, b_i, t_i) in faculty_template_vars:
                            am_vars.append((f.id, faculty_template_vars[f_i, b_i, t_i]))

            # Collect PM faculty clinic variables
            for block in pm_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    if template.id not in clinic_template_ids:
                        continue
                    t_i = context.template_idx[template.id]
                    for f in context.faculty:
                        f_i = context.faculty_idx.get(f.id)
                        if f_i is not None and (f_i, b_i, t_i) in faculty_template_vars:
                            pm_vars.append((f.id, faculty_template_vars[f_i, b_i, t_i]))

            # Exactly 1 faculty AM
            if am_vars:
                model.Add(sum(v for _, v in am_vars) == 1)

            # Exactly 1 faculty PM
            if pm_vars:
                model.Add(sum(v for _, v in pm_vars) == 1)

            # Different faculty AM vs PM (if same faculty in both, sum <= 1)
            if am_vars and pm_vars:
                faculty_in_both = set(f for f, _ in am_vars) & set(
                    f for f, _ in pm_vars
                )
                for fac_id in faculty_in_both:
                    am_v = [v for f, v in am_vars if f == fac_id]
                    pm_v = [v for f, v in pm_vars if f == fac_id]
                    if am_v and pm_v:
                        # Cannot have same faculty both AM and PM
                        model.Add(sum(am_v) + sum(pm_v) <= 1)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce 1 faculty AM, 1 different faculty PM on 4th Wednesday (PuLP)."""
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

        fourth_wed_groups: dict[str, dict[str, list]] = {}
        for block in context.blocks:
            if not self._is_fourth_wednesday(block):
                continue
            date_str = str(block.date)
            if date_str not in fourth_wed_groups:
                fourth_wed_groups[date_str] = {"AM": [], "PM": []}
            tod = getattr(block, "time_of_day", "AM")
            fourth_wed_groups[date_str][tod].append(block)

        for date_str, blocks_by_time in fourth_wed_groups.items():
            am_blocks = blocks_by_time.get("AM", [])
            pm_blocks = blocks_by_time.get("PM", [])

            am_vars = []
            pm_vars = []

            for block in am_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    if template.id not in clinic_template_ids:
                        continue
                    t_i = context.template_idx[template.id]
                    for f in context.faculty:
                        f_i = context.faculty_idx.get(f.id)
                        if f_i is not None and (f_i, b_i, t_i) in faculty_template_vars:
                            am_vars.append((f.id, faculty_template_vars[f_i, b_i, t_i]))

            for block in pm_blocks:
                b_i = context.block_idx[block.id]
                for template in context.templates:
                    if template.id not in clinic_template_ids:
                        continue
                    t_i = context.template_idx[template.id]
                    for f in context.faculty:
                        f_i = context.faculty_idx.get(f.id)
                        if f_i is not None and (f_i, b_i, t_i) in faculty_template_vars:
                            pm_vars.append((f.id, faculty_template_vars[f_i, b_i, t_i]))

            # Exactly 1 faculty AM
            if am_vars:
                model += (
                    pulp.lpSum(v for _, v in am_vars) == 1,
                    f"inv_wed_am_{date_str}",
                )

            # Exactly 1 faculty PM
            if pm_vars:
                model += (
                    pulp.lpSum(v for _, v in pm_vars) == 1,
                    f"inv_wed_pm_{date_str}",
                )

            # Different faculty AM vs PM
            if am_vars and pm_vars:
                fac_both = set(f for f, _ in am_vars) & set(f for f, _ in pm_vars)
                for fac_id in fac_both:
                    am_v = [v for f, v in am_vars if f == fac_id]
                    pm_v = [v for f, v in pm_vars if f == fac_id]
                    if am_v and pm_v:
                        model += (
                            pulp.lpSum(am_v) + pulp.lpSum(pm_v) <= 1,
                            f"inv_wed_diff_{date_str}_{fac_id}",
                        )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check 4th Wed has 1 faculty AM, 1 different faculty PM."""
        violations: list[ConstraintViolation] = []

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        # Early return if no clinic templates
        if not clinic_template_ids:
            return ConstraintResult(satisfied=True, violations=[])

        faculty_ids = {f.id for f in context.faculty}

        # Group 4th Wednesday blocks by date
        fourth_wed_dates: dict[str, dict[str, list]] = {}
        for block in context.blocks:
            if not self._is_fourth_wednesday(block):
                continue
            date_str = str(block.date)
            if date_str not in fourth_wed_dates:
                fourth_wed_dates[date_str] = {"AM": [], "PM": []}
            fourth_wed_dates[date_str][block.time_of_day].append(block)

        for date_str, blocks_by_time in fourth_wed_dates.items():
            am_faculty = set()
            pm_faculty = set()

            for block in blocks_by_time.get("AM", []):
                for a in assignments:
                    if (
                        a.block_id == block.id
                        and a.person_id in faculty_ids
                        and a.rotation_template_id in clinic_template_ids
                    ):
                        am_faculty.add(a.person_id)

            for block in blocks_by_time.get("PM", []):
                for a in assignments:
                    if (
                        a.block_id == block.id
                        and a.person_id in faculty_ids
                        and a.rotation_template_id in clinic_template_ids
                    ):
                        pm_faculty.add(a.person_id)

            # Check AM = exactly 1
            if len(am_faculty) != 1:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"4th Wed {date_str} AM: {len(am_faculty)} faculty (need 1)",
                        details={
                            "date": date_str,
                            "time": "AM",
                            "count": len(am_faculty),
                        },
                    )
                )

            # Check PM = exactly 1
            if len(pm_faculty) != 1:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"4th Wed {date_str} PM: {len(pm_faculty)} faculty (need 1)",
                        details={
                            "date": date_str,
                            "time": "PM",
                            "count": len(pm_faculty),
                        },
                    )
                )

            # Check AM != PM (different faculty)
            if am_faculty and pm_faculty and am_faculty == pm_faculty:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"4th Wed {date_str}: Same faculty AM and PM (must be different)",
                        details={"date": date_str, "faculty": list(am_faculty)},
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
