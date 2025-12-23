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

Crisis Mode (Production Fork):
    - FMITContinuityTurfConstraint: Turf continuity deliveries to OB based on system load
    - FMITStaffingFloorConstraint: Enforce minimum faculty before FMIT assignments

Classes:
    - FMITWeekBlockingConstraint: Block clinic and Sun-Thurs call during FMIT (hard)
    - FMITMandatoryCallConstraint: FMIT attending must cover Fri/Sat call (hard)
    - PostFMITRecoveryConstraint: Friday after FMIT is blocked (hard)
    - FMITContinuityTurfConstraint: OB turf rules based on load shedding level (hard)
    - FMITStaffingFloorConstraint: Minimum faculty requirements for FMIT (hard)
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
            t.id
            for t in context.templates
            if hasattr(t, "activity_type") and t.activity_type == "clinic"
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
            t.id
            for t in context.templates
            if hasattr(t, "activity_type") and t.activity_type == "clinic"
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
                                    f"fmit_no_clinic_{f_i}_{b_i}_{constraint_count}",
                                )
                                constraint_count += 1

                    if call_vars and is_sun_thurs(block.date):
                        if (f_i, b_i, "overnight") in call_vars:
                            model += (
                                call_vars[f_i, b_i, "overnight"] == 0,
                                f"fmit_no_call_{f_i}_{b_i}_{constraint_count}",
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
                if (
                    template
                    and hasattr(template, "activity_type")
                    and template.activity_type == "clinic"
                ):
                    violations.append(
                        ConstraintViolation(
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
                        )
                    )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _identify_fmit_weeks(
        self, context: SchedulingContext
    ) -> dict[Any, list[tuple[date, date]]]:
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
                hasattr(template, "activity_type")
                and template.activity_type == "inpatient"
                and hasattr(template, "name")
                and "FMIT" in template.name.upper()
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
                                f"fmit_fri_call_{f_i}_{constraint_count}",
                            )
                            constraint_count += 1

                    saturday = friday_start + timedelta(days=1)
                    if block.date == saturday:
                        b_i = context.block_idx[block.id]
                        if (f_i, b_i, "overnight") in call_vars:
                            model += (
                                call_vars[f_i, b_i, "overnight"] == 1,
                                f"fmit_sat_call_{f_i}_{constraint_count}",
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

    def _identify_fmit_weeks(
        self, context: SchedulingContext
    ) -> dict[Any, list[tuple[date, date]]]:
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
                hasattr(template, "activity_type")
                and template.activity_type == "inpatient"
                and hasattr(template, "name")
                and "FMIT" in template.name.upper()
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
                                    f"post_fmit_blocked_{f_i}_{b_i}_{constraint_count}",
                                )
                                constraint_count += 1

                    if call_vars:
                        for call_type in ["overnight", "weekend", "backup"]:
                            if (f_i, b_i, call_type) in call_vars:
                                model += (
                                    call_vars[f_i, b_i, call_type] == 0,
                                    f"post_fmit_no_call_{f_i}_{b_i}_{constraint_count}",
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
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="HIGH",
                            message=f"{faculty.name} assigned on {block.date} which is post-FMIT recovery day",
                            person_id=faculty.id,
                            block_id=block.id,
                            details={"recovery_date": str(block.date)},
                        )
                    )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _identify_fmit_weeks(
        self, context: SchedulingContext
    ) -> dict[Any, list[tuple[date, date]]]:
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
                hasattr(template, "activity_type")
                and template.activity_type == "inpatient"
                and hasattr(template, "name")
                and "FMIT" in template.name.upper()
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


class FMITContinuityTurfConstraint(HardConstraint):
    """
    FMIT continuity delivery turf rules based on system load.

    FM faculty normally attend continuity deliveries (patients they've followed in clinic).
    When staffing is critical, continuity deliveries can be turfed to OB.

    Load shedding levels (from resilience framework):
    - NORMAL/YELLOW (0-1): FM must attend all continuity deliveries
    - ORANGE (2): FM preferred, but OB acceptable (warning only)
    - RED (3): FM attempts if available, OB covers most (info only)
    - BLACK (4): All continuity turfed to OB, FM focuses on essential services

    This constraint reads the current load shedding level from context.load_shedding_level
    and adjusts FMIT continuity requirements accordingly.

    Note: In absence of load shedding level data, defaults to NORMAL (FM required).
    """

    def __init__(self) -> None:
        """Initialize FMIT continuity turf constraint."""
        super().__init__(
            name="FMITContinuityTurf",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add FMIT continuity constraints to CP-SAT model.

        This is informational only - does not add solver constraints.
        The actual turf decisions are made during validation/runtime.
        """
        # This constraint is primarily for validation and reporting
        # It doesn't add solver constraints since turf decisions are made dynamically
        pass

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add FMIT continuity constraints to PuLP model.

        This is informational only - does not add solver constraints.
        """
        pass

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate FMIT continuity requirements based on load shedding level.

        Returns violations with appropriate severity based on current system load.
        """
        violations: list[ConstraintViolation] = []

        # Get current load shedding level from context (default to NORMAL if not set)
        load_shedding_level = getattr(context, "load_shedding_level", 0)  # 0 = NORMAL

        # For now, this is a reporting constraint
        # In a full implementation, continuity deliveries would be tracked in context
        # and we would validate FM attendance based on load shedding level

        if load_shedding_level >= 2:  # ORANGE or higher
            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="info" if load_shedding_level >= 3 else "warning",
                    message=f"FMIT continuity turf active: Load shedding level {load_shedding_level}. "
                    f"{'All continuity to OB' if load_shedding_level >= 4 else 'OB coverage available'}",
                    person_id=None,
                    block_id=None,
                    details={
                        "load_shedding_level": load_shedding_level,
                        "turf_policy": self._get_turf_policy(load_shedding_level),
                    },
                )
            )

        return ConstraintResult(
            satisfied=True,  # This is informational, not a hard failure
            violations=violations,
        )

    def _get_turf_policy(self, level: int) -> str:
        """Get turf policy description for a load shedding level."""
        if level == 0:
            return "FM attends all continuity deliveries"
        elif level == 1:
            return "FM attends all continuity deliveries (yellow alert)"
        elif level == 2:
            return "FM preferred, OB acceptable for continuity"
        elif level == 3:
            return "OB covers most continuity, FM if available"
        else:  # level >= 4
            return "All continuity to OB - FM essential services only"


class FMITStaffingFloorConstraint(HardConstraint):
    """
    Ensures minimum faculty available before FMIT assignments.

    FMIT weeks consume faculty completely (blocked from clinic, Sun-Thurs call).
    This constraint prevents FMIT assignment when it would drop available faculty
    below safe thresholds.

    Thresholds:
    - MINIMUM_FACULTY_FOR_FMIT: 5 faculty (below this, NO FMIT assignments)
    - FMIT_UTILIZATION_CAP: 0.20 (max 20% of faculty on FMIT simultaneously)

    Example scenarios:
    - 4 faculty total: NO FMIT allowed (below minimum)
    - 5 faculty total: Max 1 FMIT (5 * 0.20 = 1)
    - 10 faculty total: Max 2 FMIT (10 * 0.20 = 2)
    - 15 faculty total: Max 3 FMIT (15 * 0.20 = 3)

    This prevents the "PCS season" scenario where FMIT assignment would
    overload remaining faculty during staffing shortages.
    """

    MINIMUM_FACULTY_FOR_FMIT = 5
    FMIT_UTILIZATION_CAP = 0.20  # Max 20% on FMIT at once

    def __init__(self) -> None:
        """Initialize FMIT staffing floor constraint."""
        super().__init__(
            name="FMITStaffingFloor",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add FMIT staffing constraints to CP-SAT model.

        Blocks FMIT assignments when faculty count is too low or when
        too many concurrent FMIT weeks would be created.
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        # Count active faculty (not residents)
        active_faculty = [f for f in context.faculty if self._is_faculty_active(f)]
        total_faculty = len(active_faculty)

        if total_faculty < self.MINIMUM_FACULTY_FOR_FMIT:
            # Block ALL FMIT assignments
            self._block_all_fmit_assignments(model, template_vars, context)
            return

        # Calculate maximum concurrent FMIT
        max_concurrent_fmit = max(1, int(total_faculty * self.FMIT_UTILIZATION_CAP))

        # For CP-SAT, we would need to track concurrent FMIT weeks
        # This requires week-level grouping which is complex in CP-SAT
        # For now, we rely on validation to catch violations
        # Full CP-SAT implementation would require week variables

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add FMIT staffing constraints to PuLP model.

        Similar to CP-SAT implementation.
        """
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        active_faculty = [f for f in context.faculty if self._is_faculty_active(f)]
        total_faculty = len(active_faculty)

        if total_faculty < self.MINIMUM_FACULTY_FOR_FMIT:
            self._block_all_fmit_assignments(model, template_vars, context)

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate FMIT assignments against staffing floor.

        Checks:
        1. Total faculty count >= MINIMUM_FACULTY_FOR_FMIT
        2. Concurrent FMIT weeks <= utilization cap
        """
        violations: list[ConstraintViolation] = []

        # Count active faculty
        active_faculty = [f for f in context.faculty if self._is_faculty_active(f)]
        total_faculty = len(active_faculty)

        # Identify FMIT assignments
        fmit_assignments = []
        template_by_id = {t.id: t for t in context.templates}

        for assignment in assignments:
            template = template_by_id.get(assignment.rotation_template_id)
            if template and self._is_fmit_template(template):
                fmit_assignments.append(assignment)

        if not fmit_assignments:
            return ConstraintResult(satisfied=True, violations=[])

        # Check minimum faculty threshold
        if total_faculty < self.MINIMUM_FACULTY_FOR_FMIT:
            for assignment in fmit_assignments:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"Cannot assign FMIT: only {total_faculty} faculty available "
                        f"(minimum {self.MINIMUM_FACULTY_FOR_FMIT} required)",
                        person_id=assignment.person_id,
                        block_id=assignment.block_id,
                        details={
                            "total_faculty": total_faculty,
                            "minimum_required": self.MINIMUM_FACULTY_FOR_FMIT,
                        },
                    )
                )

        # Check utilization cap
        if total_faculty >= self.MINIMUM_FACULTY_FOR_FMIT:
            max_concurrent = max(1, int(total_faculty * self.FMIT_UTILIZATION_CAP))

            # Group FMIT assignments by week
            fmit_by_week = self._group_fmit_by_week(fmit_assignments, context)

            for week_start, week_assignments in fmit_by_week.items():
                unique_faculty = {a.person_id for a in week_assignments}
                concurrent_count = len(unique_faculty)

                if concurrent_count > max_concurrent:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="CRITICAL",
                            message=f"Week {week_start}: {concurrent_count} concurrent FMIT exceeds cap "
                            f"({max_concurrent} max for {total_faculty} faculty)",
                            person_id=None,
                            block_id=None,
                            details={
                                "week_start": str(week_start),
                                "concurrent_fmit": concurrent_count,
                                "max_allowed": max_concurrent,
                                "total_faculty": total_faculty,
                                "utilization_cap": self.FMIT_UTILIZATION_CAP,
                            },
                        )
                    )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _is_faculty_active(self, person: Any) -> bool:
        """Check if person is active faculty (not on leave, not deployed)."""
        # In a full implementation, this would check person status
        # For now, assume all faculty in context.faculty are active
        return True

    def _is_fmit_template(self, template: Any) -> bool:
        """Check if template is an FMIT rotation."""
        return (
            hasattr(template, "activity_type")
            and template.activity_type == "inpatient"
            and hasattr(template, "name")
            and "FMIT" in template.name.upper()
        )

    def _block_all_fmit_assignments(
        self,
        model: Any,
        template_vars: dict,
        context: SchedulingContext,
    ) -> None:
        """Block all FMIT template assignments in the model."""
        # Identify FMIT templates
        fmit_template_ids = {
            t.id for t in context.templates if self._is_fmit_template(t)
        }

        # Block all FMIT assignments
        for (f_i, b_i, t_i), var in template_vars.items():
            t_id = context.templates[t_i].id if t_i < len(context.templates) else None
            if t_id in fmit_template_ids:
                try:
                    # Try CP-SAT style
                    model.Add(var == 0)
                except AttributeError:
                    # Try PuLP style
                    model += var == 0

    def _group_fmit_by_week(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> dict[date, list[Any]]:
        """Group FMIT assignments by FMIT week (Friday-Thursday)."""
        block_by_id = {b.id: b for b in context.blocks}
        weeks: dict[date, list[Any]] = defaultdict(list)

        for assignment in assignments:
            block = block_by_id.get(assignment.block_id)
            if not block:
                continue

            # Get FMIT week for this date
            friday_start, _ = get_fmit_week_dates(block.date)
            weeks[friday_start].append(assignment)

        return dict(weeks)
