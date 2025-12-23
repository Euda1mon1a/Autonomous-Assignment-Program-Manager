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

        # Count Sunday calls per faculty
        faculty_sunday_counts = {}
        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
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

        # Track Sunday calls per faculty and add variance penalty
        faculty_counts = []
        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
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
            b for b in context.blocks if b.date.weekday() in (0, 1, 2, 3)  # Mon-Thurs
        ]

        if not weekday_blocks:
            return

        faculty_weekday_counts = {}
        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
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

        faculty_counts = []
        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
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

        # Find PD and APD faculty
        penalty_vars = []
        for faculty in context.faculty:
            if (
                not hasattr(faculty, "avoid_tuesday_call")
                or not faculty.avoid_tuesday_call
            ):
                continue

            f_i = context.resident_idx.get(faculty.id)
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

        penalty_vars: list[Any] = []
        for faculty in context.faculty:
            if (
                not hasattr(faculty, "avoid_tuesday_call")
                or not faculty.avoid_tuesday_call
            ):
                continue

            f_i = context.resident_idx.get(faculty.id)
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
            b for b in context.blocks if b.date.weekday() == 2  # Wednesday
        ]

        if not wednesday_blocks:
            return

        # Find Dept Chief
        bonus_vars = []
        for faculty in context.faculty:
            if (
                not hasattr(faculty, "prefer_wednesday_call")
                or not faculty.prefer_wednesday_call
            ):
                continue

            f_i = context.resident_idx.get(faculty.id)
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

        bonus_vars: list[Any] = []
        for faculty in context.faculty:
            if (
                not hasattr(faculty, "prefer_wednesday_call")
                or not faculty.prefer_wednesday_call
            ):
                continue

            f_i = context.resident_idx.get(faculty.id)
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
