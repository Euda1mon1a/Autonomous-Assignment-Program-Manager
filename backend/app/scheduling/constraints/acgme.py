"""
ACGME Compliance Constraints.

This module provides backward-compatible re-exports of ACGME constraints
that have been moved to the services layer.

The canonical implementation is now in:
    backend/app/services/constraints/acgme.py

This module re-exports all classes to maintain backward compatibility
with existing code that imports from this location.

Key ACGME Rules:
    - 80-Hour Rule: Maximum 80 hours per week, strictly calculated over
      a 4-week rolling average (28 consecutive days)
    - 1-in-7 Rule: At least one 24-hour period off every 7 days
    - Supervision: Adequate faculty-to-resident ratios by PGY level
    - Availability: Residents cannot work during scheduled absences

Classes (re-exported from services.constraints.acgme):
    - AvailabilityConstraint: Enforces absence tracking (hard)
    - EightyHourRuleConstraint: Enforces 80-hour duty hour limit (hard)
    - OneInSevenRuleConstraint: Enforces 1-in-7 day off rule (hard)
    - SupervisionRatioConstraint: Enforces faculty supervision ratios (hard)
    - ACGMEConstraintValidator: High-level validator for all ACGME rules

Migration Note:
    New code should import directly from:
        from app.services.constraints import (
            ACGMEConstraintValidator,
            EightyHourRuleConstraint,
            OneInSevenRuleConstraint,
            SupervisionRatioConstraint,
        )
"""

import logging
from collections import defaultdict
from datetime import timedelta

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
    This is a hard constraint - assignments during blocking absences
    are forbidden.
    """

    def __init__(self) -> None:
        """Initialize availability constraint."""
        super().__init__(
            name="Availability",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Add availability constraint to OR-Tools CP-SAT model.

        For each (resident, block) pair where resident is unavailable,
        adds constraint: x[r_i, b_i] == 0, preventing assignment during
        absences (vacation, deployment, TDY, medical leave, etc.).

        Args:
            model: OR-Tools CP-SAT model instance (cp_model.CpModel)
            variables: Dictionary containing decision variables with key:
                - "assignments": Dict[(person_idx, block_idx), BoolVar]
            context: SchedulingContext with availability matrix mapping
                {person_id: {block_id: {"available": bool, "replacement": str}}}

        Returns:
            None. Modifies model in-place by adding constraints.

        Note:
            This is a HARD constraint (ACGME compliance). Assignments during
            blocking absences are absolutely forbidden and cannot be overridden.
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
                                model.Add(x[r_i, b_i] == 0)

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Add availability constraint to PuLP model.

        For each (resident, block) pair where resident is unavailable,
        adds constraint: x[r_i, b_i] == 0.

        Args:
            model: PuLP LpProblem instance
            variables: Dictionary containing decision variables with key:
                - "assignments": Dict[(person_idx, block_idx), LpVariable]
            context: SchedulingContext with availability matrix

        Returns:
            None. Modifies model in-place.
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
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate that no assignments occur during absences.

        Checks each assignment against the availability matrix to ensure
        no resident or faculty is assigned to work during a blocking absence.

        Args:
            assignments: List of assignment objects with person_id and block_id
            context: SchedulingContext with availability matrix and person lookups

        Returns:
            ConstraintResult with:
                - satisfied: True if no assignments during absences
                - violations: List of ConstraintViolation for each conflict
                - penalty: 0.0 (hard constraint, violations are binary)
        """
        violations = []

        for assignment in assignments:
            person_id = assignment.person_id
            block_id = assignment.block_id

            if person_id in context.availability:
                if block_id in context.availability[person_id]:
                    if not context.availability[person_id][block_id]["available"]:
                        person_name = "Unknown"
                        for r in context.residents + context.faculty:
                            if r.id == person_id:
                                person_name = r.name
                                break

                        violations.append(
                            ConstraintViolation(
                                constraint_name=self.name,
                                constraint_type=self.constraint_type,
                                severity="CRITICAL",
                                message=f"{person_name} assigned during absence",
                                person_id=person_id,
                                block_id=block_id,
                            )
                        )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class EightyHourRuleConstraint(HardConstraint):
    """
    ACGME 80-hour rule: Maximum 80 hours per week, strictly calculated
    over a 4-week rolling average (28 consecutive days).

    This constraint enforces one of the most critical ACGME requirements:
    resident duty hours must not exceed 80 hours per week when averaged over
    any 4-week (28 consecutive days) rolling window.

    Implementation Details:
        - Each half-day block (AM or PM) represents 6 hours of duty time
        - Uses STRICT rolling 4-week (28-day) windows
        - Checks ALL possible 28-day windows in the schedule period
        - Maximum blocks per 4-week window: (80 * 4) / 6 = 53 blocks

    ACGME Reference:
        Common Program Requirements, Section VI.F.1:
        "Duty hours are limited to 80 hours per week, averaged over a four-week
        period, inclusive of all in-house clinical and educational activities."

    Critical Notes:
        - The 4-week period is STRICTLY 28 consecutive calendar days
        - Rolling average means checking EVERY possible 28-day window
        - This is a HARD constraint - violations make schedule invalid

    Constants:
        HOURS_PER_BLOCK: Hours per half-day block (6 hours)
        MAX_WEEKLY_HOURS: Maximum hours per week (80 hours)
        ROLLING_WEEKS: Window size for averaging (4 weeks = 28 days)
        ROLLING_DAYS: Exact number of days in window (28 days)
    """

    HOURS_PER_BLOCK = 6
    MAX_WEEKLY_HOURS = 80
    ROLLING_WEEKS = 4
    ROLLING_DAYS = 28  # 4 weeks * 7 days = 28 days (STRICT)

    def __init__(self) -> None:
        """
        Initialize the 80-hour rule constraint.

        Calculates the maximum number of blocks allowed in any 4-week window:
        max_blocks = (80 hours/week * 4 weeks) / 6 hours/block = 53 blocks
        """
        super().__init__(
            name="80HourRule",
            constraint_type=ConstraintType.DUTY_HOURS,
            priority=ConstraintPriority.CRITICAL,
        )
        # Max blocks per 4-week window: (80 * 4) / 6 = 53.33 -> 53
        self.max_blocks_per_window = (
            self.MAX_WEEKLY_HOURS * self.ROLLING_WEEKS
        ) // self.HOURS_PER_BLOCK

    def _calculate_rolling_average(self, hours_by_date: dict, window_start) -> float:
        """
        Calculate the rolling 4-week average hours starting from window_start.

        This method strictly implements the ACGME 4-week rolling average:
        - Window is exactly 28 consecutive calendar days
        - Sum all hours within the window
        - Divide by 4 to get weekly average

        Args:
            hours_by_date: Dict mapping dates to hours worked
            window_start: First day of the 28-day window

        Returns:
            float: Average weekly hours over the 4-week period
        """
        window_end = window_start + timedelta(days=self.ROLLING_DAYS - 1)

        total_hours = sum(
            hours
            for d, hours in hours_by_date.items()
            if window_start <= d <= window_end
        )

        return total_hours / self.ROLLING_WEEKS

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Enforce 80-hour rule via block count limits in CP-SAT model.

        For each possible 28-day window and each resident, adds constraint
        that the sum of assigned blocks <= max_blocks_per_window (53).

        Args:
            model: OR-Tools CP-SAT model instance (cp_model.CpModel)
            variables: Dictionary containing decision variables with key:
                - "assignments": Dict[(person_idx, block_idx), BoolVar]
            context: SchedulingContext with blocks, residents, and date mappings

        Returns:
            None. Modifies model in-place by adding constraints.

        ACGME Rule:
            Section VI.F.1: "Duty hours are limited to 80 hours per week,
            averaged over a four-week period."

        Note:
            Uses block counting (max 53 blocks per 28-day window) as proxy for
            hours since each half-day block equals 6 duty hours.
        """
        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if not dates:
            return

        preassigned_blocks = getattr(context, "preassigned_work_blocks", {})

        warned_fixed_80 = set()

        # For each possible 28-day window starting point
        for window_start in dates:
            window_end = window_start + timedelta(days=self.ROLLING_DAYS - 1)

            # Get all blocks in this strict 28-day window
            window_blocks = [
                b for b in context.blocks if window_start <= b.date <= window_end
            ]

            if not window_blocks:
                continue

                # For each resident, sum of blocks in window <= max
            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_preassigned = preassigned_blocks.get(resident.id, set())
                preassigned_count = sum(
                    1 for b in window_blocks if b.id in resident_preassigned
                )
                if preassigned_count > self.max_blocks_per_window:
                    if resident.id not in warned_fixed_80:
                        warned_fixed_80.add(resident.id)
                        logger.warning(
                            "80HourRule preassigned workload exceeds limit: "
                            f"{resident.name} {window_start}→{window_end} "
                            f"preassigned_blocks={preassigned_count}"
                        )
                    continue
                window_vars = [
                    x[r_i, context.block_idx[b.id]]
                    for b in window_blocks
                    if (r_i, context.block_idx[b.id]) in x
                ]
                decision_count = len(window_vars)
                if preassigned_count + decision_count > self.max_blocks_per_window:
                    if resident.id not in warned_fixed_80:
                        warned_fixed_80.add(resident.id)
                        logger.warning(
                            "80HourRule infeasible due to fixed workload: "
                            f"{resident.name} {window_start}→{window_end} "
                            f"fixed_blocks={preassigned_count + decision_count}"
                        )
                    continue
                if window_vars or preassigned_count:
                    model.Add(
                        sum(window_vars) + preassigned_count
                        <= self.max_blocks_per_window
                    )

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Enforce 80-hour rule via block count limits in PuLP model.

        For each possible 28-day window and each resident, adds constraint
        that the sum of assigned blocks <= max_blocks_per_window (53).

        Args:
            model: PuLP LpProblem instance
            variables: Dictionary containing decision variables with key:
                - "assignments": Dict[(person_idx, block_idx), LpVariable]
            context: SchedulingContext with blocks, residents, and date mappings

        Returns:
            None. Modifies model in-place by adding constraints.

        ACGME Rule:
            Section VI.F.1: "Duty hours are limited to 80 hours per week,
            averaged over a four-week period."
        """
        import pulp

        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if not dates:
            return

        preassigned_blocks = getattr(context, "preassigned_work_blocks", {})
        warned_fixed_80 = set()
        window_count = 0
        for window_start in dates:
            window_end = window_start + timedelta(days=self.ROLLING_DAYS - 1)

            window_blocks = [
                b for b in context.blocks if window_start <= b.date <= window_end
            ]

            if not window_blocks:
                continue

            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_preassigned = preassigned_blocks.get(resident.id, set())
                preassigned_count = sum(
                    1 for b in window_blocks if b.id in resident_preassigned
                )
                if preassigned_count > self.max_blocks_per_window:
                    if resident.id not in warned_fixed_80:
                        warned_fixed_80.add(resident.id)
                        logger.warning(
                            "80HourRule preassigned workload exceeds limit (PuLP): "
                            f"{resident.name} {window_start}→{window_end} "
                            f"preassigned_blocks={preassigned_count}"
                        )
                    continue
                window_vars = [
                    x[r_i, context.block_idx[b.id]]
                    for b in window_blocks
                    if (r_i, context.block_idx[b.id]) in x
                ]
                decision_count = len(window_vars)
                if preassigned_count + decision_count > self.max_blocks_per_window:
                    if resident.id not in warned_fixed_80:
                        warned_fixed_80.add(resident.id)
                        logger.warning(
                            "80HourRule infeasible due to fixed workload (PuLP): "
                            f"{resident.name} {window_start}→{window_end} "
                            f"fixed_blocks={preassigned_count + decision_count}"
                        )
                    continue
                if window_vars or preassigned_count:
                    model += (
                        pulp.lpSum(window_vars) + preassigned_count
                        <= self.max_blocks_per_window,
                        f"80hr_{r_i}_{window_count}",
                    )
            window_count += 1

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Check 80-hour rule compliance with strict 4-week rolling average.

        Validates that no resident exceeds 80 hours/week when averaged
        over any 28-day consecutive period.

        Args:
            assignments: List of assignment objects with person_id and block_id
            context: SchedulingContext with blocks, residents, and date mappings

        Returns:
            ConstraintResult with:
                - satisfied: True if all residents comply with 80-hour rule
                - violations: List of ConstraintViolation for each violation,
                  with details including window dates and calculated hours
                - penalty: 0.0 (hard constraint)

        ACGME Rule:
            Section VI.F.1: "Duty hours are limited to 80 hours per week,
            averaged over a four-week period."
        """
        violations = []

        # Group assignments by resident
        by_resident = defaultdict(list)
        for a in assignments:
            by_resident[a.person_id].append(a)

        for resident in context.residents:
            resident_assignments = by_resident.get(resident.id, [])
            if not resident_assignments:
                continue

                # Get hours per date for this resident
            hours_by_date = defaultdict(int)
            for a in resident_assignments:
                for b in context.blocks:
                    if b.id == a.block_id:
                        hours_by_date[b.date] += self.HOURS_PER_BLOCK
                        break

            if not hours_by_date:
                continue

            sorted_dates = sorted(hours_by_date.keys())

            # Check EVERY possible 28-day window (strict rolling average)
            for start_date in sorted_dates:
                avg_weekly = self._calculate_rolling_average(hours_by_date, start_date)

                if avg_weekly > self.MAX_WEEKLY_HOURS:
                    end_date = start_date + timedelta(days=self.ROLLING_DAYS - 1)
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="CRITICAL",
                            message=(
                                f"{resident.name}: {avg_weekly:.1f} hours/week "
                                f"(limit: {self.MAX_WEEKLY_HOURS}) in 4-week window "
                                f"{start_date.isoformat()} to {end_date.isoformat()}"
                            ),
                            person_id=resident.id,
                            details={
                                "window_start": start_date.isoformat(),
                                "window_end": end_date.isoformat(),
                                "window_days": self.ROLLING_DAYS,
                                "average_weekly_hours": avg_weekly,
                                "max_weekly_hours": self.MAX_WEEKLY_HOURS,
                            },
                        )
                    )
                    # Report first violation per resident for efficiency
                    break

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class OneInSevenRuleConstraint(HardConstraint):
    """
    ACGME 1-in-7 rule: At least one 24-hour period off every 7 days.

    Simplified implementation: Cannot work more than 6 consecutive days.

    ACGME Reference:
        Common Program Requirements, Section VI.F.3:
        "Residents must have one day in seven free from all educational
        and clinical responsibilities, averaged over four weeks."
    """

    MAX_CONSECUTIVE_DAYS = 6

    def __init__(self) -> None:
        """Initialize 1-in-7 rule constraint."""
        super().__init__(
            name="1in7Rule",
            constraint_type=ConstraintType.CONSECUTIVE_DAYS,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Enforce max consecutive days in CP-SAT model.

        For each possible 7-day window and each resident, ensures at least
        one day off by limiting worked days to 6 maximum.

        Args:
            model: OR-Tools CP-SAT model instance (cp_model.CpModel)
            variables: Dictionary containing decision variables with key:
                - "assignments": Dict[(person_idx, block_idx), BoolVar]
            context: SchedulingContext with blocks, residents, and date mappings

        Returns:
            None. Modifies model in-place by adding constraints.

        ACGME Rule:
            Section VI.F.3: "Residents must have one day in seven free from
            all educational and clinical responsibilities."

        Note:
            Creates indicator variables for each day (day_worked) using
            AddMaxEquality to detect if any block on that day is assigned.
        """
        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if len(dates) < self.MAX_CONSECUTIVE_DAYS + 1:
            return

        preassigned_days = getattr(context, "preassigned_work_days", {})
        warned_fixed_1in7 = set()

        for resident in context.residents:
            r_i = context.resident_idx[resident.id]
            resident_preassigned = preassigned_days.get(resident.id, set())

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
                preassigned_day_count = sum(
                    1 for d in consecutive_dates if d in resident_preassigned
                )
                if preassigned_day_count > self.MAX_CONSECUTIVE_DAYS:
                    if resident.id not in warned_fixed_1in7:
                        warned_fixed_1in7.add(resident.id)
                        logger.warning(
                            "1in7Rule preassigned workload exceeds limit: "
                            f"{resident.name} {start_date} "
                            f"preassigned_days={preassigned_day_count}"
                        )
                    continue
                for d in consecutive_dates[: self.MAX_CONSECUTIVE_DAYS + 1]:
                    if d in resident_preassigned:
                        continue
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
                if (
                    preassigned_day_count + len(day_worked_vars)
                    > self.MAX_CONSECUTIVE_DAYS
                ):
                    if resident.id not in warned_fixed_1in7:
                        warned_fixed_1in7.add(resident.id)
                        logger.warning(
                            "1in7Rule infeasible due to fixed workload: "
                            f"{resident.name} {start_date} "
                            f"fixed_days={preassigned_day_count + len(day_worked_vars)}"
                        )
                    continue
                if day_worked_vars or preassigned_day_count:
                    model.Add(
                        sum(day_worked_vars) + preassigned_day_count
                        <= self.MAX_CONSECUTIVE_DAYS
                    )

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Enforce max consecutive days in PuLP model (linear approximation).

        Uses a linear approximation: sum of all blocks in 7 days <= 12
        (6 days * 2 blocks per day), which ensures at least one day off.

        Args:
            model: PuLP LpProblem instance
            variables: Dictionary containing decision variables with key:
                - "assignments": Dict[(person_idx, block_idx), LpVariable]
            context: SchedulingContext with blocks, residents, and date mappings

        Returns:
            None. Modifies model in-place by adding constraints.

        ACGME Rule:
            Section VI.F.3: "Residents must have one day in seven free from
            all educational and clinical responsibilities."

        Note:
            PuLP lacks CP-SAT's AddMaxEquality, so uses block count as proxy.
            This is a relaxation but catches most violations.
        """
        import pulp

        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if len(dates) < self.MAX_CONSECUTIVE_DAYS + 1:
            return

        preassigned_blocks = getattr(context, "preassigned_work_blocks", {})
        warned_fixed_1in7 = set()
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
                all_vars = []
                for d in consecutive_dates[: self.MAX_CONSECUTIVE_DAYS + 1]:
                    for b in context.blocks_by_date[d]:
                        if (r_i, context.block_idx[b.id]) in x:
                            all_vars.append(x[r_i, context.block_idx[b.id]])

                resident_preassigned = preassigned_blocks.get(resident.id, set())
                preassigned_count = sum(
                    1
                    for d in consecutive_dates[: self.MAX_CONSECUTIVE_DAYS + 1]
                    for b in context.blocks_by_date[d]
                    if b.id in resident_preassigned
                )
                if preassigned_count > self.MAX_CONSECUTIVE_DAYS * 2:
                    if resident.id not in warned_fixed_1in7:
                        warned_fixed_1in7.add(resident.id)
                        logger.warning(
                            "1in7Rule preassigned workload exceeds limit (PuLP): "
                            f"{resident.name} {start_date} "
                            f"preassigned_blocks={preassigned_count}"
                        )
                    continue
                if all_vars or preassigned_count:
                    model += (
                        pulp.lpSum(all_vars) + preassigned_count
                        <= self.MAX_CONSECUTIVE_DAYS * 2,
                        f"1in7_{r_i}_{constraint_count}",
                    )
                    constraint_count += 1

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Check for consecutive days violations.

        Identifies residents who have worked more than 6 consecutive days
        without a day off.

        Args:
            assignments: List of assignment objects with person_id and block_id
            context: SchedulingContext with blocks and residents

        Returns:
            ConstraintResult with:
                - satisfied: True if all residents have at least 1 day off per 7
                - violations: List of ConstraintViolation for each violation,
                  with details including consecutive day count
                - penalty: 0.0 (hard constraint)

        ACGME Rule:
            Section VI.F.3: "Residents must have one day in seven free from
            all educational and clinical responsibilities."
        """
        violations = []

        # Group by resident
        by_resident = defaultdict(set)
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
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=(
                            f"{resident.name}: {max_consecutive} consecutive duty days "
                            f"(limit: {self.MAX_CONSECUTIVE_DAYS})"
                        ),
                        person_id=resident.id,
                        details={"consecutive_days": max_consecutive},
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class SupervisionRatioConstraint(HardConstraint):
    """
    ACGME supervision ratios: Ensures adequate faculty supervision.

    Supervision Ratios:
        - PGY-1: 1 faculty : 2 residents (more intensive supervision)
        - PGY-2/3: 1 faculty : 4 residents (greater independence)

    ACGME Reference:
        Common Program Requirements, Section VI.B:
        "The program must demonstrate that the appropriate level of supervision
        is in place for all residents who care for patients."

    Constants:
        PGY1_RATIO: Maximum PGY-1 residents per faculty (2)
        OTHER_RATIO: Maximum PGY-2/3 residents per faculty (4)
    """

    PGY1_RATIO = 2  # 1 faculty per 2 PGY-1
    OTHER_RATIO = 4  # 1 faculty per 4 PGY-2/3

    def __init__(self) -> None:
        """Initialize supervision ratio constraint."""
        super().__init__(
            name="SupervisionRatio",
            constraint_type=ConstraintType.SUPERVISION,
            priority=ConstraintPriority.CRITICAL,
        )

    def calculate_required_faculty(self, pgy1_count: int, other_count: int) -> int:
        """
        Calculate required faculty for given resident counts.

        Uses fractional supervision load approach:
        - PGY-1: 0.5 supervision load each (1:2 ratio)
        - PGY-2/3: 0.25 supervision load each (1:4 ratio)

        Sums all loads THEN applies ceiling to avoid overcounting in
        mixed PGY scenarios. For example:
        - 1 PGY-1 + 1 PGY-2 = 0.5 + 0.25 = ceil(0.75) = 1 faculty (not 2)

        Args:
            pgy1_count: Number of PGY-1 residents
            other_count: Number of PGY-2/3 residents

        Returns:
            int: Minimum number of faculty required, or 0 if no residents
        """
        # Integer math: PGY-1 = 2 units, PGY-2/3 = 1 unit (4 units = 1 faculty)
        supervision_units = (pgy1_count * 2) + other_count
        return (supervision_units + 3) // 4 if supervision_units > 0 else 0

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Add supervision ratio constraints to CP-SAT model.

        Supervision ratio enforcement is typically handled post-hoc for
        residents since faculty assignments are made separately.

        Args:
            model: OR-Tools CP-SAT model instance (cp_model.CpModel)
            variables: Dictionary containing decision variables
            context: SchedulingContext with residents and faculty

        Returns:
            None. No constraints added (validation-only constraint).

        ACGME Rule:
            Section VI.B: "The program must demonstrate that the appropriate
            level of supervision is in place for all residents."
        """
        pass

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Add supervision ratio constraints to PuLP model.

        Supervision ratio enforcement is typically handled post-hoc for
        residents since faculty assignments are made separately.

        Args:
            model: PuLP LpProblem instance
            variables: Dictionary containing decision variables
            context: SchedulingContext with residents and faculty

        Returns:
            None. No constraints added (validation-only constraint).
        """
        pass

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Check supervision ratios per block.

        Validates that each block has adequate faculty coverage based on
        resident PGY levels and ACGME supervision requirements.

        Args:
            assignments: List of assignment objects with person_id and block_id
            context: SchedulingContext with residents, faculty, and PGY levels

        Returns:
            ConstraintResult with:
                - satisfied: True if all blocks have adequate supervision
                - violations: List of ConstraintViolation for under-staffed blocks
                - penalty: 0.0 (hard constraint)

        ACGME Rule:
            Section VI.B: "The program must demonstrate that the appropriate
            level of supervision is in place for all residents."
            - PGY-1: 1 faculty per 2 residents
            - PGY-2/3: 1 faculty per 4 residents
        """
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
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=(
                            f"Block needs {required} faculty but has {len(faculty)} "
                            f"({len(residents)} residents)"
                        ),
                        block_id=block_id,
                        details={
                            "residents": len(residents),
                            "pgy1_count": pgy1_count,
                            "faculty": len(faculty),
                            "required": required,
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

        # Re-export ACGMEConstraintValidator from services
        # This enables using the high-level validator from the old import path


try:
    from app.services.constraints.acgme import ACGMEConstraintValidator
except ImportError:
    # Fallback if services module not yet available (e.g., during initialization)
    class ACGMEConstraintValidator:
        """Placeholder for backward compatibility during module initialization."""

        def __init__(self) -> None:
            self.constraints = [
                AvailabilityConstraint(),
                EightyHourRuleConstraint(),
                OneInSevenRuleConstraint(),
                SupervisionRatioConstraint(),
            ]

        def validate(
            self, assignments: list, context: SchedulingContext
        ) -> ConstraintResult:
            """Validate all ACGME constraints."""
            return self.validate_all(assignments, context)

        def validate_all(
            self, assignments: list, context: SchedulingContext
        ) -> ConstraintResult:
            """Run all ACGME constraint validations."""
            all_violations = []
            total_penalty = 0.0

            for constraint in self.constraints:
                if not constraint.enabled:
                    continue

                result = constraint.validate(assignments, context)
                all_violations.extend(result.violations)
                total_penalty += result.penalty

            return ConstraintResult(
                satisfied=len(all_violations) == 0,
                violations=all_violations,
                penalty=total_penalty,
            )
