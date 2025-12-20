"""
ACGME Compliance Constraints.

This module contains constraints that enforce ACGME (Accreditation Council
for Graduate Medical Education) requirements for resident duty hours,
supervision, and work schedules.

Key ACGME Rules:
    - 80-Hour Rule: Maximum 80 hours per week, averaged over 4 weeks
    - 1-in-7 Rule: At least one 24-hour period off every 7 days
    - Supervision: Adequate faculty-to-resident ratios by PGY level
    - Availability: Residents cannot work during scheduled absences

Classes:
    - AvailabilityConstraint: Enforces absence tracking (hard)
    - EightyHourRuleConstraint: Enforces 80-hour duty hour limit (hard)
    - OneInSevenRuleConstraint: Enforces 1-in-7 day off rule (hard)
    - SupervisionRatioConstraint: Enforces faculty supervision ratios (hard)
"""
import logging
from collections import defaultdict
from datetime import timedelta
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


class AvailabilityConstraint(HardConstraint):
    """
    Ensures residents are only assigned to blocks when available.
    Respects absences (vacation, deployment, TDY, etc.)
    """

    def __init__(self) -> None:
        super().__init__(
            name="Availability",
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
        Add availability constraint to OR-Tools CP-SAT model.

        Enforces that residents cannot be assigned to blocks during absences.
        This is a hard constraint - assignments during blocking absences
        (deployment, TDY, extended medical leave) are forbidden.

        Args:
            model: OR-Tools CP-SAT model to add constraints to
            variables: Dictionary containing decision variables:
                      - "assignments": {(resident_idx, block_idx): BoolVar}
            context: SchedulingContext with availability matrix

        Implementation:
            For each (resident, block) pair where resident is unavailable,
            adds constraint: x[r_i, b_i] == 0
        """
        x = variables.get("assignments", {})

        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in context.blocks:
                b_i = context.block_idx[block.id]

                # Check availability
                if resident.id in context.availability:
                    if block.id in context.availability[resident.id]:
                        if not context.availability[resident.id][block.id]["available"]:
                            if (r_i, b_i) in x:
                                model.Add(x[r_i, b_i] == 0)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add availability constraint to PuLP linear programming model.

        Enforces that residents cannot be assigned to blocks during absences.
        This is a hard constraint - assignments during blocking absences
        (deployment, TDY, extended medical leave) are forbidden.

        Args:
            model: PuLP LpProblem to add constraints to
            variables: Dictionary containing decision variables:
                      - "assignments": {(resident_idx, block_idx): LpVariable}
            context: SchedulingContext with availability matrix

        Implementation:
            For each (resident, block) pair where resident is unavailable,
            adds constraint: x[r_i, b_i] == 0
        """
        x = variables.get("assignments", {})

        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            for block in context.blocks:
                b_i = context.block_idx[block.id]

                if resident.id in context.availability:
                    if block.id in context.availability[resident.id]:
                        if not context.availability[resident.id][block.id]["available"]:
                            if (r_i, b_i) in x:
                                model += x[r_i, b_i] == 0, f"avail_{r_i}_{b_i}"

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate that no assignments occur during absences.

        Checks existing assignments to ensure no resident is scheduled during
        a blocking absence (deployment, TDY, extended medical leave).

        Args:
            assignments: List of Assignment objects to validate
            context: SchedulingContext with availability matrix

        Returns:
            ConstraintResult with:
                - satisfied: True if no violations found
                - violations: List of ConstraintViolation objects for each
                            assignment during a blocking absence

        Example:
            >>> result = constraint.validate(assignments, context)
            >>> if not result.satisfied:
            ...     for v in result.violations:
            ...         print(f"ERROR: {v.message}")
        """
        violations = []

        for assignment in assignments:
            person_id = assignment.person_id
            block_id = assignment.block_id

            if person_id in context.availability:
                if block_id in context.availability[person_id]:
                    if not context.availability[person_id][block_id]["available"]:
                        # Find person name
                        person_name = "Unknown"
                        for r in context.residents + context.faculty:
                            if r.id == person_id:
                                person_name = r.name
                                break

                        violations.append(ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="CRITICAL",
                            message=f"{person_name} assigned during absence",
                            person_id=person_id,
                            block_id=block_id,
                        ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class EightyHourRuleConstraint(HardConstraint):
    """
    ACGME 80-hour rule: Maximum 80 hours per week, averaged over 4 weeks.

    This constraint enforces one of the most critical ACGME requirements:
    resident duty hours must not exceed 80 hours per week when averaged over
    any 4-week period.

    Implementation Details:
        - Each half-day block (AM or PM) represents 6 hours of duty time
        - Uses rolling 4-week windows to check all possible time periods
        - Maximum blocks per 4-week window: (80 × 4) / 6 = 53 blocks

    ACGME Reference:
        Common Program Requirements, Section VI.F.1:
        "Duty hours are limited to 80 hours per week, averaged over a four-week
        period, inclusive of all in-house clinical and educational activities."

    Constants:
        HOURS_PER_BLOCK: Hours per half-day block (6 hours)
        MAX_WEEKLY_HOURS: Maximum hours per week (80 hours)
        ROLLING_WEEKS: Window size for averaging (4 weeks)
    """

    HOURS_PER_BLOCK: int = 6
    MAX_WEEKLY_HOURS: int = 80
    ROLLING_WEEKS: int = 4

    def __init__(self) -> None:
        """
        Initialize the 80-hour rule constraint.

        Calculates the maximum number of blocks allowed in any 4-week window:
        max_blocks = (80 hours/week × 4 weeks) / 6 hours/block = 53 blocks
        """
        super().__init__(
            name="80HourRule",
            constraint_type=ConstraintType.DUTY_HOURS,
            priority=ConstraintPriority.CRITICAL,
        )
        # Max blocks per 4-week window: (80 * 4) / 6 = 53.33 -> 53
        self.max_blocks_per_window: int = (self.MAX_WEEKLY_HOURS * self.ROLLING_WEEKS) // self.HOURS_PER_BLOCK

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce 80-hour rule via block count limits."""
        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if not dates:
            return

        # For each possible 28-day window starting point
        for window_start in dates:
            window_end = window_start + timedelta(days=self.ROLLING_WEEKS * 7 - 1)

            # Get all blocks in this window
            window_blocks = [
                b for b in context.blocks
                if window_start <= b.date <= window_end
            ]

            if not window_blocks:
                continue

            # For each resident, sum of blocks in window <= max
            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                window_vars = [
                    x[r_i, context.block_idx[b.id]]
                    for b in window_blocks
                    if (r_i, context.block_idx[b.id]) in x
                ]
                if window_vars:
                    model.Add(sum(window_vars) <= self.max_blocks_per_window)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce 80-hour rule via block count limits."""
        import pulp
        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if not dates:
            return

        window_count = 0
        for window_start in dates:
            window_end = window_start + timedelta(days=self.ROLLING_WEEKS * 7 - 1)

            window_blocks = [
                b for b in context.blocks
                if window_start <= b.date <= window_end
            ]

            if not window_blocks:
                continue

            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                window_vars = [
                    x[r_i, context.block_idx[b.id]]
                    for b in window_blocks
                    if (r_i, context.block_idx[b.id]) in x
                ]
                if window_vars:
                    model += (
                        pulp.lpSum(window_vars) <= self.max_blocks_per_window,
                        f"80hr_{r_i}_{window_count}"
                    )
            window_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check 80-hour rule compliance."""
        violations: list[ConstraintViolation] = []

        # Group assignments by resident
        by_resident: dict[Any, list[Any]] = defaultdict(list)
        for a in assignments:
            by_resident[a.person_id].append(a)

        for resident in context.residents:
            resident_assignments = by_resident.get(resident.id, [])
            if not resident_assignments:
                continue

            # Get dates for this resident
            dates_with_blocks = defaultdict(int)
            for a in resident_assignments:
                # Find block date
                for b in context.blocks:
                    if b.id == a.block_id:
                        dates_with_blocks[b.date] += 1
                        break

            if not dates_with_blocks:
                continue

            sorted_dates = sorted(dates_with_blocks.keys())

            # Check each 28-day window
            for start_date in sorted_dates:
                end_date = start_date + timedelta(days=27)

                total_blocks = sum(
                    count for d, count in dates_with_blocks.items()
                    if start_date <= d <= end_date
                )

                total_hours = total_blocks * self.HOURS_PER_BLOCK
                avg_weekly = total_hours / self.ROLLING_WEEKS

                if avg_weekly > self.MAX_WEEKLY_HOURS:
                    violations.append(ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"{resident.name}: {avg_weekly:.1f} hours/week (limit: {self.MAX_WEEKLY_HOURS})",
                        person_id=resident.id,
                        details={
                            "window_start": start_date.isoformat(),
                            "average_weekly_hours": avg_weekly,
                        },
                    ))
                    break  # One violation per resident is enough

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class OneInSevenRuleConstraint(HardConstraint):
    """
    ACGME 1-in-7 rule: At least one 24-hour period off every 7 days.
    Simplified: Cannot work more than 6 consecutive days.
    """

    MAX_CONSECUTIVE_DAYS: int = 6

    def __init__(self) -> None:
        super().__init__(
            name="1in7Rule",
            constraint_type=ConstraintType.CONSECUTIVE_DAYS,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce max consecutive days."""

        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if len(dates) < self.MAX_CONSECUTIVE_DAYS + 1:
            return

        for resident in context.residents:
            r_i = context.resident_idx[resident.id]

            # Check each possible 7-day window
            for start_idx in range(len(dates)):
                start_date = dates[start_idx]

                # Get 7 consecutive calendar days
                consecutive_dates = []
                for day_offset in range(self.MAX_CONSECUTIVE_DAYS + 1):
                    target_date = start_date + timedelta(days=day_offset)
                    if target_date in context.blocks_by_date:
                        consecutive_dates.append(target_date)

                if len(consecutive_dates) < self.MAX_CONSECUTIVE_DAYS + 1:
                    continue

                # Create indicator variables for each day
                day_worked_vars = []
                for d in consecutive_dates[:self.MAX_CONSECUTIVE_DAYS + 1]:
                    day_blocks = context.blocks_by_date[d]
                    day_vars = [
                        x[r_i, context.block_idx[b.id]]
                        for b in day_blocks
                        if (r_i, context.block_idx[b.id]) in x
                    ]

                    if day_vars:
                        day_worked = model.NewBoolVar(f"day_{r_i}_{d}")
                        model.AddMaxEquality(day_worked, day_vars)
                        day_worked_vars.append(day_worked)

                # At most 6 days worked in any 7-day window
                if len(day_worked_vars) == self.MAX_CONSECUTIVE_DAYS + 1:
                    model.Add(sum(day_worked_vars) <= self.MAX_CONSECUTIVE_DAYS)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Enforce max consecutive days (linear approximation)."""
        import pulp
        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if len(dates) < self.MAX_CONSECUTIVE_DAYS + 1:
            return

        constraint_count = 0
        for resident in context.residents:
            r_i = context.resident_idx[resident.id]

            for start_idx in range(len(dates)):
                start_date = dates[start_idx]

                consecutive_dates = []
                for day_offset in range(self.MAX_CONSECUTIVE_DAYS + 1):
                    target_date = start_date + timedelta(days=day_offset)
                    if target_date in context.blocks_by_date:
                        consecutive_dates.append(target_date)

                if len(consecutive_dates) < self.MAX_CONSECUTIVE_DAYS + 1:
                    continue

                # Sum of all blocks across 7 days <= 6 * 2 (max 2 blocks per day)
                # This is a relaxation, but works for most cases
                all_vars = []
                for d in consecutive_dates[:self.MAX_CONSECUTIVE_DAYS + 1]:
                    for b in context.blocks_by_date[d]:
                        if (r_i, context.block_idx[b.id]) in x:
                            all_vars.append(x[r_i, context.block_idx[b.id]])

                if all_vars:
                    model += (
                        pulp.lpSum(all_vars) <= self.MAX_CONSECUTIVE_DAYS * 2,
                        f"1in7_{r_i}_{constraint_count}"
                    )
                    constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check for consecutive days violations."""
        violations: list[ConstraintViolation] = []

        # Group by resident
        by_resident: dict[Any, set[Any]] = defaultdict(set)
        for a in assignments:
            for b in context.blocks:
                if b.id == a.block_id:
                    by_resident[a.person_id].add(b.date)
                    break

        for resident in context.residents:
            dates = sorted(by_resident.get(resident.id, set()))
            if len(dates) < self.MAX_CONSECUTIVE_DAYS + 1:
                continue

            consecutive = 1
            max_consecutive = 1

            for i in range(1, len(dates)):
                if (dates[i] - dates[i - 1]).days == 1:
                    consecutive += 1
                    max_consecutive = max(max_consecutive, consecutive)
                else:
                    consecutive = 1

            if max_consecutive > self.MAX_CONSECUTIVE_DAYS:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH",
                    message=f"{resident.name}: {max_consecutive} consecutive duty days (limit: {self.MAX_CONSECUTIVE_DAYS})",
                    person_id=resident.id,
                    details={"consecutive_days": max_consecutive},
                ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class SupervisionRatioConstraint(HardConstraint):
    """
    ACGME supervision ratios: Ensures adequate faculty supervision.

    This constraint enforces different faculty-to-resident ratios based on
    PGY level, reflecting the increased supervision needs of junior residents.

    Supervision Ratios:
        - PGY-1: 1 faculty : 2 residents (more intensive supervision)
        - PGY-2/3: 1 faculty : 4 residents (greater independence)

    ACGME Reference:
        Common Program Requirements, Section VI.B:
        "The program must demonstrate that the appropriate level of supervision
        is in place for all residents who care for patients."

    Clinical Context:
        - PGY-1 residents require more direct oversight
        - Senior residents (PGY-2/3) have more clinical autonomy
        - These ratios ensure patient safety and educational quality

    Example:
        For a clinic with 2 PGY-1 and 4 PGY-2/3 residents:
        - PGY-1 faculty needed: ⌈2/2⌉ = 1
        - PGY-2/3 faculty needed: ⌈4/4⌉ = 1
        - Total required: 2 faculty members

    Constants:
        PGY1_RATIO: Maximum PGY-1 residents per faculty (2)
        OTHER_RATIO: Maximum PGY-2/3 residents per faculty (4)
    """

    PGY1_RATIO: int = 2  # 1 faculty per 2 PGY-1
    OTHER_RATIO: int = 4  # 1 faculty per 4 PGY-2/3

    def __init__(self) -> None:
        """
        Initialize supervision ratio constraint.

        Sets constraint priority to CRITICAL as inadequate supervision
        violates ACGME requirements and patient safety standards.
        """
        super().__init__(
            name="SupervisionRatio",
            constraint_type=ConstraintType.SUPERVISION,
            priority=ConstraintPriority.CRITICAL,
        )

    def calculate_required_faculty(self, pgy1_count: int, other_count: int) -> int:
        """
        Calculate required faculty for given resident counts.

        Uses ceiling division to ensure adequate supervision even with
        partial ratios (e.g., 3 PGY-1 residents require 2 faculty).

        Args:
            pgy1_count: Number of PGY-1 residents
            other_count: Number of PGY-2/3 residents

        Returns:
            int: Minimum number of faculty required, or 0 if no residents

        Example:
            >>> calc = SupervisionRatioConstraint()
            >>> calc.calculate_required_faculty(pgy1_count=3, other_count=5)
            3  # 2 for PGY-1 (⌈3/2⌉=2), 2 for others (⌈5/4⌉=2), but max(1,2+2)=3
        """
        from_pgy1 = (pgy1_count + self.PGY1_RATIO - 1) // self.PGY1_RATIO
        from_other = (other_count + self.OTHER_RATIO - 1) // self.OTHER_RATIO
        return max(1, from_pgy1 + from_other) if (pgy1_count + other_count) > 0 else 0

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Supervision ratio is typically handled post-hoc for residents."""
        # This constraint is usually enforced during faculty assignment phase
        # The CP-SAT model focuses on resident assignment
        pass

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Supervision ratio is typically handled post-hoc for residents."""
        pass

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Check supervision ratios per block."""
        violations = []

        # Create person type lookup
        person_types = {}
        pgy_levels = {}
        for r in context.residents:
            person_types[r.id] = "resident"
            pgy_levels[r.id] = r.pgy_level
        for f in context.faculty:
            person_types[f.id] = "faculty"

        # Group by block
        by_block = defaultdict(lambda: {"residents": [], "faculty": []})
        for a in assignments:
            ptype = person_types.get(a.person_id)
            if ptype == "resident":
                by_block[a.block_id]["residents"].append(a.person_id)
            elif ptype == "faculty":
                by_block[a.block_id]["faculty"].append(a.person_id)

        for block_id, personnel in by_block.items():
            residents = personnel["residents"]
            faculty = personnel["faculty"]

            if not residents:
                continue

            pgy1_count = sum(1 for r in residents if pgy_levels.get(r) == 1)
            other_count = len(residents) - pgy1_count

            required = self.calculate_required_faculty(pgy1_count, other_count)

            if len(faculty) < required:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="CRITICAL",
                    message=f"Block needs {required} faculty but has {len(faculty)} ({len(residents)} residents)",
                    block_id=block_id,
                    details={
                        "residents": len(residents),
                        "pgy1_count": pgy1_count,
                        "faculty": len(faculty),
                        "required": required,
                    },
                ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
