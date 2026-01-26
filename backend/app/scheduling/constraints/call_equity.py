"""
Call Equity and Preference Constraints.

This module contains constraints for fair call distribution and
role-based call preferences.

See docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md for full details.

Equity Constraints (track cumulative counts, minimize deviation):
    - SundayCallEquityConstraint: Sunday tracked separately (worst day)
    - WeekdayCallEquityConstraint: Mon-Thurs tracked together

Preference Constraints (soft penalties/bonuses):
    - TuesdayCallPreferenceConstraint: PD/APD avoid Tuesday (academics)
    - DeptChiefWednesdayPreferenceConstraint: Dept Chief prefers Wednesday

Call Schedule Overview:
    - Friday/Saturday night: FMIT attending (mandatory, handled in fmit.py)
    - Sunday night: Separate equity pool (worst day)
    - Mon-Thurs nights: Combined equity pool
"""

import logging
from collections import defaultdict
from typing import Any

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class SundayCallEquityConstraint(SoftConstraint):
    """
    Ensures fair distribution of Sunday overnight call.

    Sunday is considered the worst call day because:
    - Disrupts weekend rest
    - Monday morning is busy
    - Higher patient volume from weekend

    This constraint tracks Sunday call counts separately and penalizes
    schedules where some faculty have significantly more Sunday calls.

    The penalty increases quadratically with deviation from the mean,
    encouraging even distribution.
    """

    def __init__(self, weight: float = 10.0) -> None:
        """
        Initialize Sunday call equity constraint.

        Args:
            weight: Penalty weight for deviation (default 10.0 - high priority)
        """
        super().__init__(
            name="SundayCallEquity",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """
        Add Sunday call equity to CP-SAT objective.

        Minimizes the maximum Sunday call count across faculty to promote
        even distribution.
        """
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        # Find Sunday blocks
        sunday_blocks = [b for b in context.blocks if b.date.weekday() == 6]  # Sunday

        if not sunday_blocks:
            return

        # Count Sunday calls per call-eligible faculty
        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        faculty_sunday_counts = {}
        for faculty in call_eligible_faculty:
            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            sunday_vars = []
            for block in sunday_blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") in call_vars:
                    sunday_vars.append(call_vars[f_i, b_i, "overnight"])

            if sunday_vars:
                faculty_sunday_counts[f_i] = sunday_vars

        if not faculty_sunday_counts:
            return

        # Create max count variable and minimize it
        max_sunday = model.NewIntVar(0, len(sunday_blocks), "max_sunday_calls")
        for f_i, vars_list in faculty_sunday_counts.items():
            model.Add(sum(vars_list) <= max_sunday)

        # Add to objective (minimize max)
        objective_vars = variables.get("objective_terms", [])
        objective_vars.append((max_sunday, int(self.weight)))
        variables["objective_terms"] = objective_vars

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add Sunday call equity to PuLP objective."""
        import pulp

        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        sunday_blocks = [b for b in context.blocks if b.date.weekday() == 6]

        if not sunday_blocks:
            return

        # Track Sunday calls per call-eligible faculty and add variance penalty
        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        faculty_counts = []
        for faculty in call_eligible_faculty:
            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            sunday_vars = []
            for block in sunday_blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") in call_vars:
                    sunday_vars.append(call_vars[f_i, b_i, "overnight"])

            if sunday_vars:
                faculty_counts.append(pulp.lpSum(sunday_vars))

        # Minimize variance through auxiliary constraints
        # (PuLP doesn't handle quadratic well, so we minimize max)
        if faculty_counts:
            max_calls = pulp.LpVariable("max_sunday_calls", lowBound=0, cat="Integer")
            for count in faculty_counts:
                model += count <= max_calls, f"sunday_max_{len(faculty_counts)}"

            # Add to objective
            if "objective" in variables:
                variables["objective"] += self.weight * max_calls

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """
        Validate Sunday call distribution and calculate penalty.

        Returns penalty based on deviation from mean Sunday call count.
        """
        # Count Sunday calls per faculty
        faculty_by_id: dict[Any, Any] = {f.id: f for f in context.faculty}
        block_by_id: dict[Any, Any] = {b.id: b for b in context.blocks}

        sunday_counts = defaultdict(int)

        for a in assignments:
            if a.person_id not in faculty_by_id:
                continue

            block = block_by_id.get(a.block_id)
            if not block or block.date.weekday() != 6:
                continue

            # Check if this is an overnight call assignment
            if hasattr(a, "call_type") and a.call_type == "overnight":
                sunday_counts[a.person_id] += 1

        if not sunday_counts:
            return ConstraintResult(satisfied=True, penalty=0.0)

        # Calculate penalty based on variance
        counts = list(sunday_counts.values())
        mean_count = sum(counts) / len(counts) if counts else 0
        variance = (
            sum((c - mean_count) ** 2 for c in counts) / len(counts) if counts else 0
        )

        penalty = variance * self.weight

        violations = []
        max_count = max(counts) if counts else 0
        min_count = min(counts) if counts else 0

        if max_count - min_count > 2:  # More than 2 difference is concerning
            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="MEDIUM",
                    message=f"Sunday call imbalance: range {min_count}-{max_count} (variance: {variance:.2f})",
                    details={
                        "min_count": min_count,
                        "max_count": max_count,
                        "variance": variance,
                    },
                )
            )

        return ConstraintResult(
            satisfied=True,  # Soft constraint, always "satisfied"
            violations=violations,
            penalty=penalty,
        )


class WeekdayCallEquityConstraint(SoftConstraint):
    """
    Ensures fair distribution of Mon-Thurs overnight call.

    Monday through Thursday calls are tracked together as a combined
    equity pool. This constraint penalizes schedules where some faculty
    have significantly more weekday calls than others.
    """

    def __init__(self, weight: float = 5.0) -> None:
        """
        Initialize weekday call equity constraint.

        Args:
            weight: Penalty weight (default 5.0 - lower than Sunday)
        """
        super().__init__(
            name="WeekdayCallEquity",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add weekday call equity to CP-SAT objective."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        # Find Mon-Thurs blocks (weekday 0-3)
        weekday_blocks = [
            b
            for b in context.blocks
            if b.date.weekday() in (0, 1, 2, 3)  # Mon-Thurs
        ]

        if not weekday_blocks:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        faculty_weekday_counts = {}
        for faculty in call_eligible_faculty:
            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            weekday_vars = []
            for block in weekday_blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") in call_vars:
                    weekday_vars.append(call_vars[f_i, b_i, "overnight"])

            if weekday_vars:
                faculty_weekday_counts[f_i] = weekday_vars

        if not faculty_weekday_counts:
            return

        # Minimize max weekday calls
        max_weekday = model.NewIntVar(0, len(weekday_blocks), "max_weekday_calls")
        for f_i, vars_list in faculty_weekday_counts.items():
            model.Add(sum(vars_list) <= max_weekday)

        objective_vars = variables.get("objective_terms", [])
        objective_vars.append((max_weekday, int(self.weight)))
        variables["objective_terms"] = objective_vars

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add weekday call equity to PuLP objective."""
        import pulp

        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        weekday_blocks = [b for b in context.blocks if b.date.weekday() in (0, 1, 2, 3)]

        if not weekday_blocks:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        faculty_counts = []
        for faculty in call_eligible_faculty:
            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            weekday_vars = []
            for block in weekday_blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") in call_vars:
                    weekday_vars.append(call_vars[f_i, b_i, "overnight"])

            if weekday_vars:
                faculty_counts.append(pulp.lpSum(weekday_vars))

        if faculty_counts:
            max_calls = pulp.LpVariable("max_weekday_calls", lowBound=0, cat="Integer")
            for i, count in enumerate(faculty_counts):
                model += count <= max_calls, f"weekday_max_{i}"

            if "objective" in variables:
                variables["objective"] += self.weight * max_calls

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate weekday call distribution."""
        faculty_by_id: dict[Any, Any] = {f.id: f for f in context.faculty}
        block_by_id: dict[Any, Any] = {b.id: b for b in context.blocks}

        weekday_counts = defaultdict(int)

        for a in assignments:
            if a.person_id not in faculty_by_id:
                continue

            block = block_by_id.get(a.block_id)
            if not block or block.date.weekday() not in (0, 1, 2, 3):
                continue

            if hasattr(a, "call_type") and a.call_type == "overnight":
                weekday_counts[a.person_id] += 1

        if not weekday_counts:
            return ConstraintResult(satisfied=True, penalty=0.0)

        counts = list(weekday_counts.values())
        mean_count = sum(counts) / len(counts) if counts else 0
        variance = (
            sum((c - mean_count) ** 2 for c in counts) / len(counts) if counts else 0
        )

        penalty = variance * self.weight

        violations = []
        max_count = max(counts) if counts else 0
        min_count = min(counts) if counts else 0

        if max_count - min_count > 3:
            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="MEDIUM",
                    message=f"Weekday call imbalance: range {min_count}-{max_count}",
                    details={
                        "min_count": min_count,
                        "max_count": max_count,
                        "variance": variance,
                    },
                )
            )

        return ConstraintResult(
            satisfied=True,
            violations=violations,
            penalty=penalty,
        )


class TuesdayCallPreferenceConstraint(SoftConstraint):
    """
    Soft preference to avoid PD and APD on Tuesday call.

    Program Director and Associate Program Director have academic
    commitments that make Tuesday call less desirable (teaching,
    conferences, etc.).

    This constraint adds a penalty when PD or APD is assigned
    Tuesday overnight call, but doesn't prohibit it if necessary.
    """

    def __init__(self, weight: float = 2.0) -> None:
        """
        Initialize Tuesday call preference constraint.

        Args:
            weight: Penalty weight (default 2.0 - operational preference)
        """
        super().__init__(
            name="TuesdayCallPreference",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add Tuesday avoidance penalty for PD/APD to CP-SAT objective."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        # Find Tuesday blocks (weekday 1)
        tuesday_blocks = [b for b in context.blocks if b.date.weekday() == 1]  # Tuesday

        if not tuesday_blocks:
            return

        # Find PD and APD faculty (call-eligible)
        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        penalty_vars = []
        for faculty in call_eligible_faculty:
            if (
                not hasattr(faculty, "avoid_tuesday_call")
                or not faculty.avoid_tuesday_call
            ):
                continue

            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in tuesday_blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") in call_vars:
                    penalty_vars.append(call_vars[f_i, b_i, "overnight"])

        if penalty_vars:
            objective_vars = variables.get("objective_terms", [])
            for var in penalty_vars:
                objective_vars.append((var, int(self.weight)))
            variables["objective_terms"] = objective_vars

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add Tuesday avoidance penalty for PD/APD to PuLP objective."""
        import pulp

        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        tuesday_blocks = [b for b in context.blocks if b.date.weekday() == 1]

        if not tuesday_blocks:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        penalty_vars: list[Any] = []
        for faculty in call_eligible_faculty:
            if (
                not hasattr(faculty, "avoid_tuesday_call")
                or not faculty.avoid_tuesday_call
            ):
                continue

            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in tuesday_blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") in call_vars:
                    penalty_vars.append(call_vars[f_i, b_i, "overnight"])

        if penalty_vars and "objective" in variables:
            variables["objective"] += self.weight * pulp.lpSum(penalty_vars)

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate and penalize PD/APD Tuesday call assignments."""
        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}

        violations = []
        penalty = 0.0

        for a in assignments:
            faculty = faculty_by_id.get(a.person_id)
            if not faculty:
                continue

            if (
                not hasattr(faculty, "avoid_tuesday_call")
                or not faculty.avoid_tuesday_call
            ):
                continue

            block = block_by_id.get(a.block_id)
            if not block or block.date.weekday() != 1:
                continue

            if hasattr(a, "call_type") and a.call_type == "overnight":
                penalty += self.weight
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="LOW",
                        message=f"{faculty.name} ({faculty.faculty_role}) assigned Tuesday call on {block.date}",
                        person_id=faculty.id,
                        block_id=block.id,
                        details={
                            "date": str(block.date),
                            "role": faculty.faculty_role,
                        },
                    )
                )

        return ConstraintResult(
            satisfied=True,
            violations=violations,
            penalty=penalty,
        )


class CallSpacingConstraint(SoftConstraint):
    """
    Penalizes back-to-back call weeks for the same faculty.

    When a faculty member takes call in consecutive weeks, this constraint
    adds a penalty to encourage better spacing. This helps with:
    - Burnout prevention (avoids call fatigue)
    - Schedule equity (spreads call burden more evenly)
    - Work-life balance (allows recovery time between call weeks)

    The penalty applies when the same faculty has call assignments in
    adjacent weeks (e.g., call on Week 1 Sunday and Week 2 Monday).
    """

    def __init__(self, weight: float = 8.0) -> None:
        """
        Initialize call spacing constraint.

        Args:
            weight: Penalty weight (default 8.0 - moderately high to encourage spacing)
        """
        super().__init__(
            name="CallSpacing",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add back-to-back call penalty to CP-SAT objective."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        # Group blocks by week (using ISO week number)
        blocks_by_week: dict[tuple[int, int], list[Any]] = defaultdict(list)
        for block in context.blocks:
            iso_year, iso_week, _ = block.date.isocalendar()
            blocks_by_week[(iso_year, iso_week)].append(block)

        # Sort weeks
        sorted_weeks = sorted(blocks_by_week.keys())
        if len(sorted_weeks) < 2:
            return

        # For each faculty, penalize consecutive week calls
        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        penalty_vars = []
        for faculty in call_eligible_faculty:
            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            # Check each pair of consecutive weeks
            for i in range(len(sorted_weeks) - 1):
                week1 = sorted_weeks[i]
                week2 = sorted_weeks[i + 1]

                # Get call vars for this faculty in each week
                week1_calls = []
                for block in blocks_by_week[week1]:
                    b_i = context.block_idx.get(block.id)
                    if b_i is not None and (f_i, b_i, "overnight") in call_vars:
                        week1_calls.append(call_vars[f_i, b_i, "overnight"])

                week2_calls = []
                for block in blocks_by_week[week2]:
                    b_i = context.block_idx.get(block.id)
                    if b_i is not None and (f_i, b_i, "overnight") in call_vars:
                        week2_calls.append(call_vars[f_i, b_i, "overnight"])

                if week1_calls and week2_calls:
                    # Create indicator for "has call in both weeks"
                    has_week1 = model.NewBoolVar(f"call_week1_{f_i}_{week1}")
                    has_week2 = model.NewBoolVar(f"call_week2_{f_i}_{week2}")

                    # has_week1 = 1 if any call in week1
                    model.AddMaxEquality(has_week1, week1_calls)
                    model.AddMaxEquality(has_week2, week2_calls)

                    # back_to_back = has_week1 AND has_week2
                    back_to_back = model.NewBoolVar(f"btb_{f_i}_{week1}")
                    model.AddMultiplicationEquality(
                        back_to_back, [has_week1, has_week2]
                    )

                    penalty_vars.append(back_to_back)

        if penalty_vars:
            objective_vars = variables.get("objective_terms", [])
            for var in penalty_vars:
                objective_vars.append((var, int(self.weight)))
            variables["objective_terms"] = objective_vars

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add back-to-back call penalty to PuLP objective."""
        import pulp

        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        blocks_by_week: dict[tuple[int, int], list[Any]] = defaultdict(list)
        for block in context.blocks:
            iso_year, iso_week, _ = block.date.isocalendar()
            blocks_by_week[(iso_year, iso_week)].append(block)

        sorted_weeks = sorted(blocks_by_week.keys())
        if len(sorted_weeks) < 2:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        constraint_count = 0
        for faculty in call_eligible_faculty:
            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for i in range(len(sorted_weeks) - 1):
                week1 = sorted_weeks[i]
                week2 = sorted_weeks[i + 1]

                week1_calls = []
                for block in blocks_by_week[week1]:
                    b_i = context.block_idx.get(block.id)
                    if b_i is not None and (f_i, b_i, "overnight") in call_vars:
                        week1_calls.append(call_vars[f_i, b_i, "overnight"])

                week2_calls = []
                for block in blocks_by_week[week2]:
                    b_i = context.block_idx.get(block.id)
                    if b_i is not None and (f_i, b_i, "overnight") in call_vars:
                        week2_calls.append(call_vars[f_i, b_i, "overnight"])

                if week1_calls and week2_calls:
                    # Create indicator variables
                    has_week1 = pulp.LpVariable(
                        f"has_call_w1_{f_i}_{constraint_count}", cat="Binary"
                    )
                    has_week2 = pulp.LpVariable(
                        f"has_call_w2_{f_i}_{constraint_count}", cat="Binary"
                    )

                    # has_week = 1 if any call in that week
                    # sum(calls) >= 1 implies has_week = 1
                    M = len(week1_calls)  # Big-M for week1
                    model += pulp.lpSum(week1_calls) <= M * has_week1
                    model += pulp.lpSum(week1_calls) >= has_week1

                    M = len(week2_calls)
                    model += pulp.lpSum(week2_calls) <= M * has_week2
                    model += pulp.lpSum(week2_calls) >= has_week2

                    # back_to_back penalty linearization
                    # We want to penalize when both = 1
                    # Add (has_week1 + has_week2 - 1) capped at 0
                    # Or simply: penalty = has_week1 + has_week2 - 1 when both are 1
                    # Use auxiliary variable
                    btb = pulp.LpVariable(f"btb_{f_i}_{constraint_count}", cat="Binary")
                    # btb = 1 iff has_week1 = 1 AND has_week2 = 1
                    model += btb <= has_week1
                    model += btb <= has_week2
                    model += btb >= has_week1 + has_week2 - 1

                    if "objective" in variables:
                        variables["objective"] += self.weight * btb

                    constraint_count += 1

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate and calculate penalty for back-to-back call weeks."""
        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}

        # Group call assignments by faculty and week
        calls_by_faculty_week: dict[Any, dict[tuple[int, int], int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for assignment in assignments:
            has_call = hasattr(assignment, "call_type")
            if not has_call or assignment.call_type != "overnight":
                continue

            if assignment.person_id not in faculty_by_id:
                continue

            block = block_by_id.get(assignment.block_id)
            if not block:
                continue

            iso_year, iso_week, _ = block.date.isocalendar()
            calls_by_faculty_week[assignment.person_id][(iso_year, iso_week)] += 1

        violations = []
        penalty = 0.0

        for faculty_id, week_calls in calls_by_faculty_week.items():
            sorted_weeks = sorted(week_calls.keys())

            for i in range(len(sorted_weeks) - 1):
                week1 = sorted_weeks[i]
                week2 = sorted_weeks[i + 1]

                # Check if weeks are consecutive
                # (same year and adjacent week, or year rollover)
                is_consecutive = False
                if (
                    week1[0] == week2[0]
                    and week2[1] == week1[1] + 1
                    or week1[0] + 1 == week2[0]
                    and week1[1] >= 52
                    and week2[1] == 1
                ):
                    is_consecutive = True

                if is_consecutive and week_calls[week1] > 0 and week_calls[week2] > 0:
                    penalty += self.weight
                    faculty = faculty_by_id.get(faculty_id)
                    name = faculty.name if faculty else "Faculty"
                    msg = f"{name} has back-to-back call: week {week1[1]}/{week2[1]}"
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="MEDIUM",
                            message=msg,
                            person_id=faculty_id,
                            details={
                                "week1": f"{week1[0]}-W{week1[1]:02d}",
                                "week2": f"{week2[0]}-W{week2[1]:02d}",
                            },
                        )
                    )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=penalty,
        )


class DeptChiefWednesdayPreferenceConstraint(SoftConstraint):
    """
    Soft preference for Department Chief to take Wednesday call.

    This is a personal preference of the current Department Chief.
    The constraint provides a small bonus (negative penalty) when
    Dept Chief is assigned Wednesday call.

    This is the lowest priority constraint and should not significantly
    impact schedule quality.
    """

    def __init__(self, weight: float = 1.0) -> None:
        """
        Initialize Wednesday preference constraint.

        Args:
            weight: Bonus weight (default 1.0 - personal preference, lowest)
        """
        super().__init__(
            name="DeptChiefWednesdayPreference",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add Wednesday bonus for Dept Chief to CP-SAT objective."""
        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        # Find Wednesday blocks (weekday 2)
        wednesday_blocks = [
            b
            for b in context.blocks
            if b.date.weekday() == 2  # Wednesday
        ]

        if not wednesday_blocks:
            return

        # Find Dept Chief (call-eligible)
        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        bonus_vars = []
        for faculty in call_eligible_faculty:
            if (
                not hasattr(faculty, "prefer_wednesday_call")
                or not faculty.prefer_wednesday_call
            ):
                continue

            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in wednesday_blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") in call_vars:
                    bonus_vars.append(call_vars[f_i, b_i, "overnight"])

        if bonus_vars:
            # Negative weight = bonus (minimize objective, so negative helps)
            objective_vars = variables.get("objective_terms", [])
            for var in bonus_vars:
                objective_vars.append((var, -int(self.weight)))
            variables["objective_terms"] = objective_vars

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add Wednesday bonus for Dept Chief to PuLP objective."""
        import pulp

        call_vars = variables.get("call_assignments", {})
        if not call_vars:
            return

        wednesday_blocks = [b for b in context.blocks if b.date.weekday() == 2]

        if not wednesday_blocks:
            return

        call_eligible_faculty = getattr(
            context, "call_eligible_faculty", context.faculty
        )
        call_faculty_idx = getattr(
            context,
            "call_eligible_faculty_idx",
            {f.id: i for i, f in enumerate(call_eligible_faculty)},
        )

        bonus_vars: list[Any] = []
        for faculty in call_eligible_faculty:
            if (
                not hasattr(faculty, "prefer_wednesday_call")
                or not faculty.prefer_wednesday_call
            ):
                continue

            f_i = call_faculty_idx.get(faculty.id)
            if f_i is None:
                continue

            for block in wednesday_blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i, "overnight") in call_vars:
                    bonus_vars.append(call_vars[f_i, b_i, "overnight"])

        if bonus_vars and "objective" in variables:
            # Negative = bonus
            variables["objective"] -= self.weight * pulp.lpSum(bonus_vars)

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Calculate bonus for Dept Chief Wednesday call."""
        faculty_by_id = {f.id: f for f in context.faculty}
        block_by_id = {b.id: b for b in context.blocks}

        bonus = 0.0

        for a in assignments:
            faculty = faculty_by_id.get(a.person_id)
            if not faculty:
                continue

            if (
                not hasattr(faculty, "prefer_wednesday_call")
                or not faculty.prefer_wednesday_call
            ):
                continue

            block = block_by_id.get(a.block_id)
            if not block or block.date.weekday() != 2:
                continue

            if hasattr(a, "call_type") and a.call_type == "overnight":
                bonus += self.weight

        # Return negative penalty (bonus)
        return ConstraintResult(
            satisfied=True,
            violations=[],
            penalty=-bonus,
        )
