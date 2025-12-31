"""
Overnight Call Coverage Constraints.

This module contains hard constraints for ensuring overnight call coverage.

Constraints:
    - OvernightCallCoverageConstraint: Exactly one faculty per Sun-Thurs night
    - AdjunctCallExclusionConstraint: Exclude adjunct faculty from solver-generated call
    - CallAvailabilityConstraint: Respect faculty unavailability

Coverage Pattern:
    - Sunday night (Sun PM to Mon AM): Faculty overnight call
    - Monday night (Mon PM to Tue AM): Faculty overnight call
    - Tuesday night (Tue PM to Wed AM): Faculty overnight call
    - Wednesday night (Wed PM to Thu AM): Faculty overnight call
    - Thursday night (Thu PM to Fri AM): Faculty overnight call
    - Friday-Saturday (Fri PM to Sun PM): FMIT faculty (not solver-generated)
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

# Weekdays for overnight call (Mon=0, Tue=1, Wed=2, Thu=3, Sun=6)
# Note: The call is FOR that night, meaning the faculty covers overnight INTO next day
OVERNIGHT_CALL_DAYS = {0, 1, 2, 3, 6}  # Mon-Thu + Sunday


def is_overnight_call_day(date) -> bool:
    """
    Check if a date is an overnight call day.

    Overnight call happens Sun-Thu nights.
    Friday-Saturday nights are covered by FMIT faculty (not solver-generated).

    Args:
        date: A date object to check

    Returns:
        True if the date is a Sun-Thu (overnight call day), False otherwise
    """
    return date.weekday() in OVERNIGHT_CALL_DAYS


class OvernightCallCoverageConstraint(HardConstraint):
    """
    Ensures exactly one faculty member is on overnight call each Sun-Thurs night.

    This is a hard constraint - every night MUST have coverage.

    The constraint enforces:
    - Exactly one faculty assigned per night (not zero, not two+)
    - Only Sun-Thurs nights (Fri-Sat handled by FMIT)

    Variables Expected:
        call_assignments: dict[(faculty_idx, block_idx, "overnight"), BoolVar]
    """

    def __init__(self) -> None:
        super().__init__(
            name="OvernightCallCoverage",
            constraint_type=ConstraintType.CALL,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add exactly-one-per-night constraint to CP-SAT model."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            logger.warning("No call variables found, skipping coverage constraint")
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )

        # Group blocks by date (we only need one assignment per date)
        dates_covered = set()
        for block in context.blocks:
            if block.date.weekday() not in OVERNIGHT_CALL_DAYS:
                continue  # Skip Fri-Sat
            if block.date in dates_covered:
                continue  # Only process each date once
            dates_covered.add(block.date)

            b_i = context.block_idx[block.id]

            # Collect all call variables for this date
            date_call_vars = []
            for f_i in range(len(call_eligible_faculty)):
                if (f_i, b_i, "overnight") in call_vars:
                    date_call_vars.append(call_vars[f_i, b_i, "overnight"])

            if date_call_vars:
                # Exactly one faculty on call this night
                model.Add(sum(date_call_vars) == 1)
                logger.debug(
                    f"Added coverage constraint for {block.date}: "
                    f"{len(date_call_vars)} eligible faculty"
                )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add exactly-one-per-night constraint to PuLP model."""
        import pulp

        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )

        dates_covered = set()
        for block in context.blocks:
            if block.date.weekday() not in OVERNIGHT_CALL_DAYS:
                continue
            if block.date in dates_covered:
                continue
            dates_covered.add(block.date)

            b_i = context.block_idx[block.id]

            date_call_vars = []
            for f_i in range(len(call_eligible_faculty)):
                if (f_i, b_i, "overnight") in call_vars:
                    date_call_vars.append(call_vars[f_i, b_i, "overnight"])

            if date_call_vars:
                model += (
                    pulp.lpSum(date_call_vars) == 1,
                    f"call_coverage_{block.date}",
                )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate that every Sun-Thurs night has exactly one call assignment."""
        from collections import defaultdict

        block_by_id = {b.id: b for b in context.blocks}

        # Count call assignments per date
        calls_per_date: dict = defaultdict(list)

        for assignment in assignments:
            if (
                not hasattr(assignment, "call_type")
                or assignment.call_type != "overnight"
            ):
                continue

            block = block_by_id.get(assignment.block_id)
            if not block:
                continue

            if block.date.weekday() not in OVERNIGHT_CALL_DAYS:
                continue

            calls_per_date[block.date].append(assignment.person_id)

        # Check each expected date
        violations = []
        dates_checked = set()

        for block in context.blocks:
            if block.date.weekday() not in OVERNIGHT_CALL_DAYS:
                continue
            if block.date in dates_checked:
                continue
            dates_checked.add(block.date)

            call_count = len(calls_per_date.get(block.date, []))

            if call_count == 0:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"No overnight call coverage for {block.date}",
                        block_id=block.id,
                        details={"date": str(block.date), "expected": 1, "actual": 0},
                    )
                )
            elif call_count > 1:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"Multiple overnight call assignments for {block.date}",
                        block_id=block.id,
                        details={
                            "date": str(block.date),
                            "expected": 1,
                            "actual": call_count,
                            "person_ids": [str(p) for p in calls_per_date[block.date]],
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class AdjunctCallExclusionConstraint(HardConstraint):
    """
    Prevents adjunct faculty from being auto-assigned overnight call.

    Adjuncts can be manually added to call via API after solver runs,
    but the solver should not include them in optimization.

    This ensures the solver doesn't count on adjunct availability.
    """

    def __init__(self) -> None:
        super().__init__(
            name="AdjunctCallExclusion",
            constraint_type=ConstraintType.CALL,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Force adjunct call variables to 0 in CP-SAT."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        for faculty in call_eligible_faculty:
            # Check if adjunct
            faculty_role = getattr(faculty, "faculty_role", None)
            if faculty_role and faculty_role.upper() == "ADJUNCT":
                f_i = call_faculty_idx.get(faculty.id)
                if f_i is None:
                    continue

                # Block all call assignments for this adjunct
                for block in context.blocks:
                    b_i = context.block_idx[block.id]
                    if (f_i, b_i, "overnight") in call_vars:
                        model.Add(call_vars[f_i, b_i, "overnight"] == 0)
                        logger.debug(
                            f"Blocked adjunct {faculty.name} from call on {block.date}"
                        )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Force adjunct call variables to 0 in PuLP."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        for faculty in call_eligible_faculty:
            faculty_role = getattr(faculty, "faculty_role", None)
            if faculty_role and faculty_role.upper() == "ADJUNCT":
                f_i = call_faculty_idx.get(faculty.id)
                if f_i is None:
                    continue

                for block in context.blocks:
                    b_i = context.block_idx[block.id]
                    if (f_i, b_i, "overnight") in call_vars:
                        model += (
                            call_vars[f_i, b_i, "overnight"] == 0,
                            f"adjunct_exclusion_{f_i}_{b_i}",
                        )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate no adjuncts have solver-generated call assignments."""
        faculty_by_id = {f.id: f for f in context.faculty}
        violations = []

        for assignment in assignments:
            if (
                not hasattr(assignment, "call_type")
                or assignment.call_type != "overnight"
            ):
                continue

            faculty = faculty_by_id.get(assignment.person_id)
            if not faculty:
                continue

            faculty_role = getattr(faculty, "faculty_role", None)
            if faculty_role and faculty_role.upper() == "ADJUNCT":
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"Adjunct {faculty.name} has solver-generated call assignment",
                        person_id=faculty.id,
                        details={"faculty_role": faculty_role},
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class CallAvailabilityConstraint(HardConstraint):
    """
    Prevents call assignment when faculty is unavailable.

    Checks the availability matrix for absences, leave, or other
    blocking assignments that would prevent overnight call.
    """

    def __init__(self) -> None:
        super().__init__(
            name="CallAvailability",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block call when faculty unavailable in CP-SAT."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        for faculty in call_eligible_faculty:
            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            # Check availability for each block
            faculty_availability = context.availability.get(faculty.id, {})

            for block in context.blocks:
                if block.date.weekday() not in OVERNIGHT_CALL_DAYS:
                    continue

                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") not in call_vars:
                    continue

                # Check if unavailable
                block_avail = faculty_availability.get(block.id, {})
                if not block_avail.get("available", True):
                    model.Add(call_vars[f_i, b_i, "overnight"] == 0)
                    logger.debug(
                        f"Blocked unavailable {faculty.name} from call on {block.date}"
                    )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Block call when faculty unavailable in PuLP."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        for faculty in call_eligible_faculty:
            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_availability = context.availability.get(faculty.id, {})

            for block in context.blocks:
                if block.date.weekday() not in OVERNIGHT_CALL_DAYS:
                    continue

                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") not in call_vars:
                    continue

                block_avail = faculty_availability.get(block.id, {})
                if not block_avail.get("available", True):
                    model += (
                        call_vars[f_i, b_i, "overnight"] == 0,
                        f"call_unavail_{f_i}_{b_i}",
                    )

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate no call assignments during unavailable periods."""
        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}
        violations = []

        for assignment in assignments:
            if (
                not hasattr(assignment, "call_type")
                or assignment.call_type != "overnight"
            ):
                continue

            faculty = faculty_by_id.get(assignment.person_id)
            block = block_by_id.get(assignment.block_id)

            if not faculty or not block:
                continue

            # Check availability
            faculty_availability = context.availability.get(faculty.id, {})
            block_avail = faculty_availability.get(block.id, {})

            if not block_avail.get("available", True):
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"{faculty.name} assigned call on {block.date} but unavailable",
                        person_id=faculty.id,
                        block_id=block.id,
                        details={
                            "reason": block_avail.get("replacement", "unavailable"),
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
