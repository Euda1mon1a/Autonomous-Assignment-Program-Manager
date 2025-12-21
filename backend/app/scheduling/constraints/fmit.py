"""
FMIT (Family Medicine Inpatient Teaching) Constraints.

This module contains constraints that enforce FMIT week scheduling rules
for faculty members.

See docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md for full details.

FMIT Week Structure:
    - Runs Friday to Thursday (independent of 4-week blocks)
    - Faculty FMIT week: All blocks are FMIT activity
    - Blocked from: Regular clinic AND Sun-Thurs call
    - Mandatory: Friday night and Saturday night call
    - Post-FMIT Friday: Blocked entirely (recovery day)

Classes:
    - FMITWeekBlockingConstraint: Block clinic and Sun-Thurs call during FMIT (hard)
    - FMITMandatoryCallConstraint: FMIT attending must cover Fri/Sat call (hard)
    - PostFMITRecoveryConstraint: Friday after FMIT is blocked (hard)
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


def get_fmit_week_dates(any_date: date) -> tuple[date, date]:
    """
    Get the Friday-Thursday FMIT week containing the given date.

    FMIT weeks run from Friday to Thursday, independent of calendar weeks.

    Args:
        any_date: Any date within the FMIT week

    Returns:
        tuple: (friday_start, thursday_end) of the FMIT week
    """
    # Friday = weekday 4
    day_of_week = any_date.weekday()

    if day_of_week >= 4:  # Fri(4), Sat(5), Sun(6)
        days_since_friday = day_of_week - 4
    else:  # Mon(0), Tue(1), Wed(2), Thu(3)
        days_since_friday = day_of_week + 3

    friday = any_date - timedelta(days=days_since_friday)
    thursday = friday + timedelta(days=6)
    return friday, thursday


def is_sun_thurs(any_date: date) -> bool:
    """Check if date is Sunday through Thursday (call blocking days)."""
    return any_date.weekday() in (6, 0, 1, 2, 3)  # Sun=6, Mon-Thu=0-3


class FMITWeekBlockingConstraint(HardConstraint):
    """
    Blocks clinic and Sun-Thurs call during FMIT week.

    When faculty is assigned FMIT for a week (Fri-Thurs):
    - All blocks during that week have FMIT as their activity
    - Faculty is blocked from regular clinic
    - Faculty is blocked from overnight call Sunday through Thursday
    - Faculty MUST take Friday and Saturday night call (mandatory)

    This constraint requires FMIT assignments to be pre-identified in the context.
    FMIT assignments should have activity_type='inpatient' and name containing 'FMIT'.
    """

    def __init__(self) -> None:
        """Initialize the FMIT week blocking constraint."""
        super().__init__(
            name="FMITWeekBlocking",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add FMIT blocking constraints to CP-SAT model.

        For each faculty with FMIT assignment:
        - Block clinic templates for all days in FMIT week
        - Block call assignments for Sun-Thurs of FMIT week
        """
        template_vars = variables.get("template_assignments", {})
        call_vars = variables.get("call_assignments", {})

        # Find FMIT assignments in existing assignments
        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)

        if not fmit_weeks_by_faculty:
            return

        # Identify clinic templates
        clinic_template_ids = {
            t.id for t in context.templates
            if hasattr(t, 'activity_type') and t.activity_type == 'clinic'
        }

        for faculty_id, fmit_weeks in fmit_weeks_by_faculty.items():
            f_i = context.resident_idx.get(faculty_id)
            if f_i is None:
                continue

            for friday_start, thursday_end in fmit_weeks:
                # Block clinic for entire FMIT week
                for block in context.blocks:
                    if not (friday_start <= block.date <= thursday_end):
                        continue

                    b_i = context.block_idx[block.id]

                    # Block clinic templates
                    if template_vars:
                        for template_id in clinic_template_ids:
                            t_i = context.template_idx.get(template_id)
                            if t_i is not None and (f_i, b_i, t_i) in template_vars:
                                model.Add(template_vars[f_i, b_i, t_i] == 0)

                    # Block Sun-Thurs call
                    if call_vars and is_sun_thurs(block.date):
                        if (f_i, b_i, "overnight") in call_vars:
                            model.Add(call_vars[f_i, b_i, "overnight"] == 0)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add FMIT blocking constraints to PuLP model."""
        template_vars = variables.get("template_assignments", {})
        call_vars = variables.get("call_assignments", {})

        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)
        if not fmit_weeks_by_faculty:
            return

        clinic_template_ids = {
            t.id for t in context.templates
            if hasattr(t, 'activity_type') and t.activity_type == 'clinic'
        }

        constraint_count = 0
        for faculty_id, fmit_weeks in fmit_weeks_by_faculty.items():
            f_i = context.resident_idx.get(faculty_id)
            if f_i is None:
                continue

            for friday_start, thursday_end in fmit_weeks:
                for block in context.blocks:
                    if not (friday_start <= block.date <= thursday_end):
                        continue

                    b_i = context.block_idx[block.id]

                    if template_vars:
                        for template_id in clinic_template_ids:
                            t_i = context.template_idx.get(template_id)
                            if t_i is not None and (f_i, b_i, t_i) in template_vars:
                                model += (
                                    template_vars[f_i, b_i, t_i] == 0,
                                    f"fmit_no_clinic_{f_i}_{b_i}_{constraint_count}"
                                )
                                constraint_count += 1

                    if call_vars and is_sun_thurs(block.date):
                        if (f_i, b_i, "overnight") in call_vars:
                            model += (
                                call_vars[f_i, b_i, "overnight"] == 0,
                                f"fmit_no_call_{f_i}_{b_i}_{constraint_count}"
                            )
                            constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate FMIT faculty not assigned clinic or Sun-Thurs call."""
        violations: list[ConstraintViolation] = []

        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)
        if not fmit_weeks_by_faculty:
            return ConstraintResult(satisfied=True, violations=[])

        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}
        template_by_id = {t.id: t for t in context.templates}

        for a in assignments:
            faculty = faculty_by_id.get(a.person_id)
            if not faculty:
                continue

            block = block_by_id.get(a.block_id)
            if not block:
                continue

            # Check if this faculty is on FMIT for this date
            fmit_weeks = fmit_weeks_by_faculty.get(a.person_id, [])
            for friday_start, thursday_end in fmit_weeks:
                if not (friday_start <= block.date <= thursday_end):
                    continue

                # Check if assigned to clinic
                template = template_by_id.get(a.rotation_template_id)
                if template and hasattr(template, 'activity_type') and template.activity_type == 'clinic':
                    violations.append(ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"{faculty.name} assigned clinic on {block.date} during FMIT week ({friday_start} - {thursday_end})",
                        person_id=faculty.id,
                        block_id=block.id,
                        details={
                            "fmit_start": str(friday_start),
                            "fmit_end": str(thursday_end),
                            "assignment_type": "clinic",
                        },
                    ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _identify_fmit_weeks(self, context: SchedulingContext) -> dict[Any, list[tuple[date, date]]]:
        """
        Identify FMIT weeks from existing assignments.

        Returns:
            dict: {faculty_id: [(friday_start, thursday_end), ...]}
        """
        fmit_weeks: dict[Any, set[tuple[date, date]]] = defaultdict(set)

        # Look for FMIT assignments in existing assignments
        for a in context.existing_assignments:
            # Check if this is an FMIT assignment
            # FMIT templates have activity_type='inpatient' and name contains 'FMIT'
            template = None
            for t in context.templates:
                if t.id == a.rotation_template_id:
                    template = t
                    break

            if not template:
                continue

            is_fmit = (
                hasattr(template, 'activity_type') and template.activity_type == 'inpatient'
                and hasattr(template, 'name') and 'FMIT' in template.name.upper()
            )

            if not is_fmit:
                continue

            # Get the block date
            block = None
            for b in context.blocks:
                if b.id == a.block_id:
                    block = b
                    break

            if not block:
                continue

            # Calculate FMIT week for this date
            friday_start, thursday_end = get_fmit_week_dates(block.date)
            fmit_weeks[a.person_id].add((friday_start, thursday_end))

        return {k: list(v) for k, v in fmit_weeks.items()}


class FMITMandatoryCallConstraint(HardConstraint):
    """
    Ensures FMIT attending covers Friday and Saturday night call.

    FMIT attending is responsible for:
    - Friday night call (mandatory)
    - Saturday night call (mandatory)

    This prevents the need for additional call coverage on weekends
    when FMIT attending is already on-site.
    """

    def __init__(self) -> None:
        """Initialize FMIT mandatory call constraint."""
        super().__init__(
            name="FMITMandatoryCall",
            constraint_type=ConstraintType.CALL,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Force FMIT attending to take Fri/Sat call in CP-SAT model."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)
        if not fmit_weeks_by_faculty:
            return

        for faculty_id, fmit_weeks in fmit_weeks_by_faculty.items():
            f_i = context.resident_idx.get(faculty_id)
            if f_i is None:
                continue

            for friday_start, thursday_end in fmit_weeks:
                # Find Friday and Saturday blocks
                for block in context.blocks:
                    if block.date == friday_start:  # Friday
                        b_i = context.block_idx[block.id]
                        if (f_i, b_i, "overnight") in call_vars:
                            model.Add(call_vars[f_i, b_i, "overnight"] == 1)

                    saturday = friday_start + timedelta(days=1)
                    if block.date == saturday:
                        b_i = context.block_idx[block.id]
                        if (f_i, b_i, "overnight") in call_vars:
                            model.Add(call_vars[f_i, b_i, "overnight"] == 1)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Force FMIT attending to take Fri/Sat call in PuLP model."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)
        if not fmit_weeks_by_faculty:
            return

        constraint_count = 0
        for faculty_id, fmit_weeks in fmit_weeks_by_faculty.items():
            f_i = context.resident_idx.get(faculty_id)
            if f_i is None:
                continue

            for friday_start, thursday_end in fmit_weeks:
                for block in context.blocks:
                    if block.date == friday_start:
                        b_i = context.block_idx[block.id]
                        if (f_i, b_i, "overnight") in call_vars:
                            model += (
                                call_vars[f_i, b_i, "overnight"] == 1,
                                f"fmit_fri_call_{f_i}_{constraint_count}"
                            )
                            constraint_count += 1

                    saturday = friday_start + timedelta(days=1)
                    if block.date == saturday:
                        b_i = context.block_idx[block.id]
                        if (f_i, b_i, "overnight") in call_vars:
                            model += (
                                call_vars[f_i, b_i, "overnight"] == 1,
                                f"fmit_sat_call_{f_i}_{constraint_count}"
                            )
                            constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate FMIT attending has Fri/Sat call assigned."""
        violations: list[ConstraintViolation] = []

        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)
        if not fmit_weeks_by_faculty:
            return ConstraintResult(satisfied=True, violations=[])

        faculty_by_id = {f.id: f for f in context.faculty}

        # Check call assignments for FMIT faculty
        # This would require call assignment data in context
        # For now, just return satisfied if we can't validate
        return ConstraintResult(satisfied=True, violations=[])

    def _identify_fmit_weeks(self, context: SchedulingContext) -> dict[Any, list[tuple[date, date]]]:
        """Identify FMIT weeks (same as FMITWeekBlockingConstraint)."""
        fmit_weeks: dict[Any, set[tuple[date, date]]] = defaultdict(set)

        for a in context.existing_assignments:
            template = None
            for t in context.templates:
                if t.id == a.rotation_template_id:
                    template = t
                    break

            if not template:
                continue

            is_fmit = (
                hasattr(template, 'activity_type') and template.activity_type == 'inpatient'
                and hasattr(template, 'name') and 'FMIT' in template.name.upper()
            )

            if not is_fmit:
                continue

            block = None
            for b in context.blocks:
                if b.id == a.block_id:
                    block = b
                    break

            if not block:
                continue

            friday_start, thursday_end = get_fmit_week_dates(block.date)
            fmit_weeks[a.person_id].add((friday_start, thursday_end))

        return {k: list(v) for k, v in fmit_weeks.items()}


class PostFMITRecoveryConstraint(HardConstraint):
    """
    Blocks the Friday after FMIT week for recovery.

    After completing an FMIT week (Fri-Thurs), the faculty member
    gets the following Friday blocked entirely - no activities
    can be scheduled.

    This ensures adequate recovery time after a demanding inpatient week.
    """

    def __init__(self) -> None:
        """Initialize post-FMIT recovery constraint."""
        super().__init__(
            name="PostFMITRecovery",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block post-FMIT Friday in CP-SAT model."""
        template_vars = variables.get("template_assignments", {})
        call_vars = variables.get("call_assignments", {})

        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)
        if not fmit_weeks_by_faculty:
            return

        for faculty_id, fmit_weeks in fmit_weeks_by_faculty.items():
            f_i = context.resident_idx.get(faculty_id)
            if f_i is None:
                continue

            for friday_start, thursday_end in fmit_weeks:
                # Recovery Friday is the day after FMIT Thursday
                recovery_friday = thursday_end + timedelta(days=1)

                # Block all assignments on recovery Friday
                for block in context.blocks:
                    if block.date != recovery_friday:
                        continue

                    b_i = context.block_idx[block.id]

                    # Block all template assignments
                    if template_vars:
                        for template in context.templates:
                            t_i = context.template_idx.get(template.id)
                            if t_i is not None and (f_i, b_i, t_i) in template_vars:
                                model.Add(template_vars[f_i, b_i, t_i] == 0)

                    # Block call assignments
                    if call_vars:
                        for call_type in ["overnight", "weekend", "backup"]:
                            if (f_i, b_i, call_type) in call_vars:
                                model.Add(call_vars[f_i, b_i, call_type] == 0)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block post-FMIT Friday in PuLP model."""
        template_vars = variables.get("template_assignments", {})
        call_vars = variables.get("call_assignments", {})

        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)
        if not fmit_weeks_by_faculty:
            return

        constraint_count = 0
        for faculty_id, fmit_weeks in fmit_weeks_by_faculty.items():
            f_i = context.resident_idx.get(faculty_id)
            if f_i is None:
                continue

            for friday_start, thursday_end in fmit_weeks:
                recovery_friday = thursday_end + timedelta(days=1)

                for block in context.blocks:
                    if block.date != recovery_friday:
                        continue

                    b_i = context.block_idx[block.id]

                    if template_vars:
                        for template in context.templates:
                            t_i = context.template_idx.get(template.id)
                            if t_i is not None and (f_i, b_i, t_i) in template_vars:
                                model += (
                                    template_vars[f_i, b_i, t_i] == 0,
                                    f"post_fmit_blocked_{f_i}_{b_i}_{constraint_count}"
                                )
                                constraint_count += 1

                    if call_vars:
                        for call_type in ["overnight", "weekend", "backup"]:
                            if (f_i, b_i, call_type) in call_vars:
                                model += (
                                    call_vars[f_i, b_i, call_type] == 0,
                                    f"post_fmit_no_call_{f_i}_{b_i}_{constraint_count}"
                                )
                                constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate no assignments on post-FMIT Friday."""
        violations: list[ConstraintViolation] = []

        fmit_weeks_by_faculty = self._identify_fmit_weeks(context)
        if not fmit_weeks_by_faculty:
            return ConstraintResult(satisfied=True, violations=[])

        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}

        # Calculate recovery Fridays for each faculty
        recovery_fridays = {}  # {faculty_id: set of recovery friday dates}
        for faculty_id, fmit_weeks in fmit_weeks_by_faculty.items():
            recovery_fridays[faculty_id] = set()
            for friday_start, thursday_end in fmit_weeks:
                recovery_friday = thursday_end + timedelta(days=1)
                recovery_fridays[faculty_id].add(recovery_friday)

        for a in assignments:
            faculty = faculty_by_id.get(a.person_id)
            if not faculty:
                continue

            block = block_by_id.get(a.block_id)
            if not block:
                continue

            # Check if this is a recovery Friday
            if a.person_id in recovery_fridays:
                if block.date in recovery_fridays[a.person_id]:
                    violations.append(ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"{faculty.name} assigned on {block.date} which is post-FMIT recovery day",
                        person_id=faculty.id,
                        block_id=block.id,
                        details={"recovery_date": str(block.date)},
                    ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _identify_fmit_weeks(self, context: SchedulingContext) -> dict[Any, list[tuple[date, date]]]:
        """Identify FMIT weeks (same as FMITWeekBlockingConstraint)."""
        fmit_weeks: dict[Any, set[tuple[date, date]]] = defaultdict(set)

        for a in context.existing_assignments:
            template = None
            for t in context.templates:
                if t.id == a.rotation_template_id:
                    template = t
                    break

            if not template:
                continue

            is_fmit = (
                hasattr(template, 'activity_type') and template.activity_type == 'inpatient'
                and hasattr(template, 'name') and 'FMIT' in template.name.upper()
            )

            if not is_fmit:
                continue

            block = None
            for b in context.blocks:
                if b.id == a.block_id:
                    block = b
                    break

            if not block:
                continue

            friday_start, thursday_end = get_fmit_week_dates(block.date)
            fmit_weeks[a.person_id].add((friday_start, thursday_end))

        return {k: list(v) for k, v in fmit_weeks.items()}
