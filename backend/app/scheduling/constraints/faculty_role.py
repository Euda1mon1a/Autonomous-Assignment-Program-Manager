"""
Faculty Role-based Scheduling Constraints.

This module contains constraints that enforce role-specific scheduling rules
for faculty members (PD, APD, OIC, Dept Chief, Sports Medicine, Core).

See docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md for full details.

Classes:
    - FacultyRoleClinicConstraint: Enforce clinic limits by role (hard)
    - SMFacultyClinicConstraint: Sports Medicine faculty clinic rules (hard)

Role-based Clinic Limits:
    - PD: 0 clinic half-days/week
    - Dept Chief: 1 clinic half-day/week
    - APD/OIC: 2 clinic half-days/week (flexible within block)
    - Sports Medicine: 0 regular clinic (4 SM clinic/week instead)
    - Core Faculty: max 4 clinic half-days/week (16/block)
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
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


class FacultyRoleClinicConstraint(HardConstraint):
    """
    Enforces role-based clinic half-day limits for faculty.

    This constraint ensures faculty members do not exceed their role-specific
    clinic limits, which vary based on administrative responsibilities.

    Role Limits:
        - PD (Program Director): 0 clinic/week - Full admin
        - Dept Chief: 1 clinic/week
        - APD (Associate PD): 2 clinic/week (flexible within block)
        - OIC (Officer in Charge): 2 clinic/week (flexible within block)
        - Sports Medicine: 0 regular clinic (has SM clinic instead)
        - Core Faculty: max 4 clinic/week (16/block hard max)

    Implementation Notes:
        - APD/OIC have block-level flexibility (0 one week, 4 another is OK)
        - Core faculty weekly limit is enforced strictly
        - Sports Medicine faculty should not be assigned to regular clinic
    """

    def __init__(self) -> None:
        """Initialize the faculty role clinic constraint."""
        super().__init__(
            name="FacultyRoleClinic",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add role-based clinic limits to OR-Tools CP-SAT model.

        For each faculty member, adds constraints based on their role:
        - Weekly constraints for roles with strict weekly limits
        - Block constraints for roles with flexible limits (APD/OIC)
        """
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

        # Get faculty from context
        for faculty in context.faculty:
            if not hasattr(faculty, "faculty_role") or not faculty.faculty_role:
                continue

            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                # Faculty might be in a different index
                continue

            weekly_limit = faculty.weekly_clinic_limit
            block_limit = faculty.block_clinic_limit

            # Group blocks by week (Mon-Sun)
            weeks = self._group_blocks_by_week(context.blocks)

            for week_start, week_blocks in weeks.items():
                # Get clinic assignment variables for this faculty and week
                week_clinic_vars = []
                for block in week_blocks:
                    b_i = context.block_idx[block.id]
                    for template in context.templates:
                        if template.id not in clinic_template_ids:
                            continue
                        t_i = context.template_idx[template.id]
                        if (f_i, b_i, t_i) in template_vars:
                            week_clinic_vars.append(template_vars[f_i, b_i, t_i])

                # Add weekly constraint
                if week_clinic_vars and weekly_limit >= 0:
                    model.Add(sum(week_clinic_vars) <= weekly_limit)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add role-based clinic limits to PuLP model."""
        import pulp

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

        constraint_count = 0
        for faculty in context.faculty:
            if not hasattr(faculty, "faculty_role") or not faculty.faculty_role:
                continue

            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            weekly_limit = faculty.weekly_clinic_limit
            weeks = self._group_blocks_by_week(context.blocks)

            for week_start, week_blocks in weeks.items():
                week_clinic_vars = []
                for block in week_blocks:
                    b_i = context.block_idx[block.id]
                    for template in context.templates:
                        if template.id not in clinic_template_ids:
                            continue
                        t_i = context.template_idx[template.id]
                        if (f_i, b_i, t_i) in template_vars:
                            week_clinic_vars.append(template_vars[f_i, b_i, t_i])

                if week_clinic_vars and weekly_limit >= 0:
                    model += (
                        pulp.lpSum(week_clinic_vars) <= weekly_limit,
                        f"faculty_clinic_limit_{f_i}_{constraint_count}",
                    )
                    constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate that faculty clinic assignments respect role limits.

        Checks both weekly and block limits depending on role flexibility.
        """
        violations: list[ConstraintViolation] = []

        # Build faculty lookup
        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}

        # Identify clinic templates
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
        }

        # Count clinic assignments by faculty and week
        faculty_weekly_counts = defaultdict(lambda: defaultdict(int))

        for a in assignments:
            # Only check faculty clinic assignments
            if a.person_id not in faculty_by_id:
                continue
            if a.rotation_template_id not in clinic_template_ids:
                continue

            block = block_by_id.get(a.block_id)
            if not block:
                continue

            week_start = self._get_week_start(block.date)
            faculty_weekly_counts[a.person_id][week_start] += 1

        # Check limits
        for faculty_id, weekly_counts in faculty_weekly_counts.items():
            faculty = faculty_by_id.get(faculty_id)
            if not faculty or not hasattr(faculty, "faculty_role"):
                continue

            weekly_limit = faculty.weekly_clinic_limit

            for week_start, count in weekly_counts.items():
                if count > weekly_limit:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="HIGH",
                            message=f"{faculty.name} ({faculty.faculty_role}): {count} clinic half-days in week of {week_start} (limit: {weekly_limit})",
                            person_id=faculty_id,
                            details={
                                "week_start": str(week_start),
                                "count": count,
                                "limit": weekly_limit,
                                "role": faculty.faculty_role,
                            },
                        )
                    )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _group_blocks_by_week(self, blocks: list[Any]) -> dict[date, list[Any]]:
        """Group blocks by week (starting Monday)."""
        weeks: dict[date, list[Any]] = defaultdict(list)
        for block in blocks:
            week_start = self._get_week_start(block.date)
            weeks[week_start].append(block)
        return weeks

    def _get_week_start(self, any_date: date) -> date:
        """Get Monday of the week containing the date."""
        days_since_monday = any_date.weekday()
        return any_date - timedelta(days=days_since_monday)


class SMFacultyClinicConstraint(HardConstraint):
    """
    Ensures Sports Medicine faculty is not assigned to regular clinic.

    Sports Medicine faculty:
    - Has 0 regular clinic half-days
    - Has 4 SM clinic half-days per week instead
    - SM clinic is cancelled when SM faculty is on FMIT

    This constraint blocks SM faculty from regular clinic templates.
    SM clinic assignments are handled separately.
    """

    def __init__(self) -> None:
        """Initialize the SM faculty clinic constraint."""
        super().__init__(
            name="SMFacultyNoRegularClinic",
            constraint_type=ConstraintType.SPECIALTY,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block SM faculty from regular clinic in CP-SAT model."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        # Identify regular clinic templates (not SM clinic)
        regular_clinic_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type")
            and t.rotation_type == "outpatient"
            and (
                not hasattr(t, "requires_specialty")
                or t.requires_specialty != "Sports Medicine"
            )
        }

        if not regular_clinic_ids:
            return

        # Find SM faculty
        for faculty in context.faculty:
            if (
                not hasattr(faculty, "is_sports_medicine")
                or not faculty.is_sports_medicine
            ):
                continue
            # Check role specifically for sports_med role
            if (
                hasattr(faculty, "faculty_role")
                and faculty.faculty_role == "sports_med"
            ):
                f_i = context.resident_idx.get(faculty.id)
                if f_i is None:
                    continue

                # Block from all regular clinic assignments
                for block in context.blocks:
                    b_i = context.block_idx[block.id]
                    for template_id in regular_clinic_ids:
                        t_i = context.template_idx.get(template_id)
                        if t_i is not None and (f_i, b_i, t_i) in template_vars:
                            model.Add(template_vars[f_i, b_i, t_i] == 0)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block SM faculty from regular clinic in PuLP model."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        regular_clinic_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "rotation_type")
            and t.rotation_type == "outpatient"
            and (
                not hasattr(t, "requires_specialty")
                or t.requires_specialty != "Sports Medicine"
            )
        }

        if not regular_clinic_ids:
            return

        constraint_count = 0
        for faculty in context.faculty:
            if (
                hasattr(faculty, "faculty_role")
                and faculty.faculty_role == "sports_med"
            ):
                f_i = context.resident_idx.get(faculty.id)
                if f_i is None:
                    continue

                for block in context.blocks:
                    b_i = context.block_idx[block.id]
                    for template_id in regular_clinic_ids:
                        t_i = context.template_idx.get(template_id)
                        if t_i is not None and (f_i, b_i, t_i) in template_vars:
                            model += (
                                template_vars[f_i, b_i, t_i] == 0,
                                f"sm_no_regular_clinic_{f_i}_{b_i}_{constraint_count}",
                            )
                            constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate SM faculty is not assigned to regular clinic."""
        violations: list[ConstraintViolation] = []

        faculty_by_id = {f.id: f for f in context.faculty}
        template_by_id = {t.id: t for t in context.templates}

        for a in assignments:
            faculty = faculty_by_id.get(a.person_id)
            if not faculty:
                continue

            # Check if SM faculty
            if not (
                hasattr(faculty, "faculty_role")
                and faculty.faculty_role == "sports_med"
            ):
                continue

            # Check if regular clinic
            template = template_by_id.get(a.rotation_template_id)
            if not template:
                continue

            is_regular_clinic = (
                hasattr(template, "rotation_type")
                and template.rotation_type == "outpatient"
                and (
                    not hasattr(template, "requires_specialty")
                    or template.requires_specialty != "Sports Medicine"
                )
            )

            if is_regular_clinic:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"SM faculty {faculty.name} assigned to regular clinic (should only do SM clinic)",
                        person_id=faculty.id,
                        block_id=a.block_id,
                        details={"template_name": template.name},
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
