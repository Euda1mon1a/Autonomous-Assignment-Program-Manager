"""
ACGME Compliance Constraints Service.

This module provides constraints that enforce ACGME (Accreditation Council
for Graduate Medical Education) requirements for resident duty hours,
supervision, and work schedules.

Key ACGME Rules:
    - 80-Hour Rule: Maximum 80 hours per week, strictly calculated over
      a 4-week rolling average (28 consecutive days)
    - 1-in-7 Rule: At least one 24-hour period off every 7 days
    - Supervision: Adequate faculty-to-resident ratios by PGY level
    - Availability: Residents cannot work during scheduled absences

Classes:
    - ACGMEConstraintValidator: High-level validator interface for all ACGME rules
    - AvailabilityConstraint: Enforces absence tracking (hard)
    - EightyHourRuleConstraint: Enforces 80-hour duty hour limit (hard)
    - OneInSevenRuleConstraint: Enforces 1-in-7 day off rule (hard)
    - SupervisionRatioConstraint: Enforces faculty supervision ratios (hard)

ACGME Reference:
    Common Program Requirements, Section VI:
    https://www.acgme.org/globalassets/pfassets/programrequirements/cprresidency_2022v3.pdf
"""
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

logger = logging.getLogger(__name__)


# =============================================================================
# Base Types (compatible with scheduling.constraints.base)
# =============================================================================


class ConstraintPriority:
    """Priority levels for constraints."""

    CRITICAL = 100  # ACGME compliance, must satisfy
    HIGH = 75  # Important operational constraints
    MEDIUM = 50  # Preferences and soft requirements
    LOW = 25  # Nice-to-have optimizations


class ConstraintType:
    """Types of constraints for categorization."""

    AVAILABILITY = "availability"
    DUTY_HOURS = "duty_hours"
    CONSECUTIVE_DAYS = "consecutive_days"
    SUPERVISION = "supervision"


@dataclass
class ConstraintViolation:
    """Represents a constraint violation."""

    constraint_name: str
    constraint_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    message: str
    person_id: UUID | None = None
    block_id: UUID | None = None
    details: dict = field(default_factory=dict)


@dataclass
class ConstraintResult:
    """Result of applying a constraint."""

    satisfied: bool
    violations: list[ConstraintViolation] = field(default_factory=list)
    penalty: float = 0.0  # For soft constraints


# =============================================================================
# Validator Protocol (interface compatibility)
# =============================================================================


@runtime_checkable
class Validator(Protocol):
    """
    Protocol for constraint validators.

    This protocol defines the interface that all validators must implement
    to ensure compatibility with the scheduling system.
    """

    def validate(self, assignments: list, context: "SchedulingContext") -> ConstraintResult:
        """
        Validate constraint against assignments.

        Args:
            assignments: List of Assignment objects to validate
            context: SchedulingContext with scheduling data

        Returns:
            ConstraintResult indicating if constraint is satisfied
        """
        ...


@dataclass
class SchedulingContext:
    """
    Minimal scheduling context for constraint evaluation.

    This is a simplified version of the full SchedulingContext from
    scheduling.constraints.base, containing only the fields needed
    for ACGME constraint validation.
    """

    residents: list = field(default_factory=list)
    faculty: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    templates: list = field(default_factory=list)
    resident_idx: dict = field(default_factory=dict)
    block_idx: dict = field(default_factory=dict)
    blocks_by_date: dict = field(default_factory=dict)
    availability: dict = field(default_factory=dict)

    def __post_init__(self):
        """Build lookup dictionaries for fast constraint evaluation."""
        if self.residents and not self.resident_idx:
            self.resident_idx = {r.id: i for i, r in enumerate(self.residents)}
        if self.blocks and not self.block_idx:
            self.block_idx = {b.id: i for i, b in enumerate(self.blocks)}
        if self.blocks and not self.blocks_by_date:
            self.blocks_by_date = defaultdict(list)
            for block in self.blocks:
                self.blocks_by_date[block.date].append(block)


# =============================================================================
# Base Constraint Class
# =============================================================================


class HardConstraint:
    """
    Hard constraint that must be satisfied.

    Violations result in infeasible solutions. All ACGME constraints
    are hard constraints since they are regulatory requirements.
    """

    def __init__(
        self,
        name: str,
        constraint_type: str,
        priority: int = ConstraintPriority.CRITICAL,
        enabled: bool = True,
    ):
        """
        Initialize hard constraint.

        Args:
            name: Unique name for this constraint
            constraint_type: Type of constraint (from ConstraintType)
            priority: Priority level (from ConstraintPriority)
            enabled: Whether constraint is active
        """
        self.name = name
        self.constraint_type = constraint_type
        self.priority = priority
        self.enabled = enabled

    def get_penalty(self) -> float:
        """Hard constraints have infinite penalty when violated."""
        return float("inf")

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext) -> None:
        """Add constraint to OR-Tools CP-SAT model."""
        raise NotImplementedError("Subclass must implement add_to_cpsat")

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext) -> None:
        """Add constraint to PuLP model."""
        raise NotImplementedError("Subclass must implement add_to_pulp")

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """Validate constraint against assignments."""
        raise NotImplementedError("Subclass must implement validate")


# =============================================================================
# ACGME Constraint Implementations
# =============================================================================


class AvailabilityConstraint(HardConstraint):
    """
    Ensures residents are only assigned to blocks when available.

    Respects absences (vacation, deployment, TDY, medical leave, etc.)
    This is a hard constraint - assignments during blocking absences
    are forbidden.
    """

    def __init__(self):
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
        adds constraint: x[r_i, b_i] == 0

        Args:
            model: OR-Tools CP-SAT model
            variables: Dict with "assignments" decision variables
            context: SchedulingContext with availability matrix
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

        Args:
            model: PuLP LpProblem
            variables: Dict with "assignments" decision variables
            context: SchedulingContext with availability matrix
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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Validate that no assignments occur during absences.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with availability matrix

        Returns:
            ConstraintResult with violations for assignments during absences
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
    over a 4-week rolling average.

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

    def __init__(self):
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

    def _calculate_rolling_average(
        self, hours_by_date: dict[date, int], window_start: date
    ) -> float:
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
            model: OR-Tools CP-SAT model
            variables: Dict with "assignments" decision variables
            context: SchedulingContext with blocks and residents
        """
        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if not dates:
            return

        # For each possible 28-day window starting point
        for window_start in dates:
            window_end = window_start + timedelta(days=self.ROLLING_DAYS - 1)

            # Get all blocks in this strict 28-day window
            window_blocks = [
                b
                for b in context.blocks
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

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Enforce 80-hour rule via block count limits in PuLP model.

        Args:
            model: PuLP LpProblem
            variables: Dict with "assignments" decision variables
            context: SchedulingContext with blocks and residents
        """
        import pulp

        x = variables.get("assignments", {})
        dates = sorted(context.blocks_by_date.keys())

        if not dates:
            return

        window_count = 0
        for window_start in dates:
            window_end = window_start + timedelta(days=self.ROLLING_DAYS - 1)

            window_blocks = [
                b
                for b in context.blocks
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
                        f"80hr_{r_i}_{window_count}",
                    )
            window_count += 1

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Check 80-hour rule compliance with strict 4-week rolling average.

        Validates that no resident exceeds 80 hours/week when averaged
        over any 28-day consecutive period.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with blocks and residents

        Returns:
            ConstraintResult with violations for exceeded hour limits
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

    def __init__(self):
        """Initialize 1-in-7 rule constraint."""
        super().__init__(
            name="1in7Rule",
            constraint_type=ConstraintType.CONSECUTIVE_DAYS,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Enforce max consecutive days in CP-SAT model.

        Creates indicator variables for each day worked and constrains
        that at most 6 days can be worked in any 7-day window.

        Args:
            model: OR-Tools CP-SAT model
            variables: Dict with "assignments" decision variables
            context: SchedulingContext with blocks and residents
        """
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
                for d in consecutive_dates[: self.MAX_CONSECUTIVE_DAYS + 1]:
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

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext) -> None:
        """
        Enforce max consecutive days in PuLP model (linear approximation).

        Args:
            model: PuLP LpProblem
            variables: Dict with "assignments" decision variables
            context: SchedulingContext with blocks and residents
        """
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
                all_vars = []
                for d in consecutive_dates[: self.MAX_CONSECUTIVE_DAYS + 1]:
                    for b in context.blocks_by_date[d]:
                        if (r_i, context.block_idx[b.id]) in x:
                            all_vars.append(x[r_i, context.block_idx[b.id]])

                if all_vars:
                    model += (
                        pulp.lpSum(all_vars) <= self.MAX_CONSECUTIVE_DAYS * 2,
                        f"1in7_{r_i}_{constraint_count}",
                    )
                    constraint_count += 1

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Check for consecutive days violations.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with blocks and residents

        Returns:
            ConstraintResult with violations for exceeded consecutive days
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

    This constraint enforces different faculty-to-resident ratios based on
    PGY level, reflecting the increased supervision needs of junior residents.

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

    def __init__(self):
        """Initialize supervision ratio constraint."""
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
        """
        from_pgy1 = (pgy1_count + self.PGY1_RATIO - 1) // self.PGY1_RATIO
        from_other = (other_count + self.OTHER_RATIO - 1) // self.OTHER_RATIO
        return max(1, from_pgy1 + from_other) if (pgy1_count + other_count) > 0 else 0

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext) -> None:
        """Supervision ratio is typically handled post-hoc for residents."""
        # This constraint is usually enforced during faculty assignment phase
        pass

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext) -> None:
        """Supervision ratio is typically handled post-hoc for residents."""
        pass

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Check supervision ratios per block.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with faculty and residents

        Returns:
            ConstraintResult with violations for inadequate supervision
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


# =============================================================================
# High-Level Validator
# =============================================================================


class ACGMEConstraintValidator:
    """
    High-level ACGME constraint validator.

    Provides a unified interface for validating all ACGME constraints
    at once. This class implements the Validator protocol and can be
    used as a drop-in replacement in existing code.

    Example:
        >>> validator = ACGMEConstraintValidator()
        >>> context = SchedulingContext(residents=residents, blocks=blocks)
        >>> result = validator.validate_all(assignments, context)
        >>> if not result.satisfied:
        ...     for v in result.violations:
        ...         print(f"VIOLATION: {v.message}")
    """

    def __init__(self):
        """Initialize with all ACGME constraints."""
        self.constraints = [
            AvailabilityConstraint(),
            EightyHourRuleConstraint(),
            OneInSevenRuleConstraint(),
            SupervisionRatioConstraint(),
        ]

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Validate all ACGME constraints.

        This method implements the Validator protocol.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with scheduling data

        Returns:
            ConstraintResult with all violations aggregated
        """
        return self.validate_all(assignments, context)

    def validate_all(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Run all ACGME constraint validations.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with scheduling data

        Returns:
            ConstraintResult with:
                - satisfied: True if all constraints pass
                - violations: Aggregated list of all violations
                - penalty: Sum of all penalties
        """
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

    def validate_80_hour_rule(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate only the 80-hour rule constraint.

        Uses strict 4-week (28-day) rolling average calculation.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with scheduling data

        Returns:
            ConstraintResult for 80-hour rule only
        """
        constraint = EightyHourRuleConstraint()
        return constraint.validate(assignments, context)

    def validate_1_in_7_rule(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate only the 1-in-7 rule constraint.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with scheduling data

        Returns:
            ConstraintResult for 1-in-7 rule only
        """
        constraint = OneInSevenRuleConstraint()
        return constraint.validate(assignments, context)

    def validate_supervision(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate only the supervision ratio constraint.

        Args:
            assignments: List of Assignment objects
            context: SchedulingContext with scheduling data

        Returns:
            ConstraintResult for supervision ratios only
        """
        constraint = SupervisionRatioConstraint()
        return constraint.validate(assignments, context)
