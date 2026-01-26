"""
Modular Constraint Definitions for Residency Scheduling.

This module provides a flexible, composable constraint system that can be used
with multiple solvers (OR-Tools CP-SAT, PuLP, custom algorithms).

Constraint Types:
- Hard Constraints: Must be satisfied (ACGME rules, availability, capacity)
- Soft Constraints: Should be optimized (preferences, equity, continuity)

Architecture:
- Constraint: Base class defining the interface
- HardConstraint: Constraints that must be satisfied
- SoftConstraint: Constraints with weights for optimization
- ConstraintManager: Composes and manages constraints for solvers
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class ConstraintPriority(Enum):
    """Priority levels for constraints."""

    CRITICAL = 100  # ACGME compliance, must satisfy
    HIGH = 75  # Important operational constraints
    MEDIUM = 50  # Preferences and soft requirements
    LOW = 25  # Nice-to-have optimizations


class ConstraintType(Enum):
    """Types of constraints for categorization."""

    AVAILABILITY = "availability"
    DUTY_HOURS = "duty_hours"
    CONSECUTIVE_DAYS = "consecutive_days"
    SUPERVISION = "supervision"
    CAPACITY = "capacity"
    ROTATION = "rotation"
    PREFERENCE = "preference"
    EQUITY = "equity"
    CONTINUITY = "continuity"
    CALL = "call"
    SPECIALTY = "specialty"
    # Resilience-aware constraint types (Tier 1)
    RESILIENCE = "resilience"
    HUB_PROTECTION = "hub_protection"
    UTILIZATION_BUFFER = "utilization_buffer"
    # Resilience-aware constraint types (Tier 2)
    ZONE_BOUNDARY = "zone_boundary"
    PREFERENCE_TRAIL = "preference_trail"
    N1_VULNERABILITY = "n1_vulnerability"


@dataclass
class ConstraintViolation:
    """Represents a constraint violation."""

    constraint_name: str
    constraint_type: ConstraintType
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


class Constraint(ABC):
    """
    Base class for all constraints.

    Constraints can be applied to:
    - OR-Tools CP-SAT models (add_to_cpsat)
    - PuLP models (add_to_pulp)
    - Direct validation (validate)
    """

    def __init__(
        self,
        name: str,
        constraint_type: ConstraintType,
        priority: ConstraintPriority = ConstraintPriority.MEDIUM,
        enabled: bool = True,
    ):
        self.name = name
        self.constraint_type = constraint_type
        self.priority = priority
        self.enabled = enabled

    @abstractmethod
    def add_to_cpsat(
        self,
        model: Any,
        variables: dict,
        context: "SchedulingContext",
    ) -> None:
        """Add constraint to OR-Tools CP-SAT model."""
        pass

    @abstractmethod
    def add_to_pulp(
        self,
        model: Any,
        variables: dict,
        context: "SchedulingContext",
    ) -> None:
        """Add constraint to PuLP model."""
        pass

    @abstractmethod
    def validate(
        self,
        assignments: list,
        context: "SchedulingContext",
    ) -> ConstraintResult:
        """Validate constraint against assignments."""
        pass


class HardConstraint(Constraint):
    """
    Hard constraint that must be satisfied.
    Violations result in infeasible solutions.
    """

    def get_penalty(self) -> float:
        """Hard constraints have infinite penalty when violated."""
        return float("inf")


class SoftConstraint(Constraint):
    """
    Soft constraint that should be optimized.
    Violations add penalty to objective function.
    """

    def __init__(
        self,
        name: str,
        constraint_type: ConstraintType,
        weight: float = 1.0,
        priority: ConstraintPriority = ConstraintPriority.MEDIUM,
        enabled: bool = True,
    ):
        super().__init__(name, constraint_type, priority, enabled)
        self.weight = weight

    def get_penalty(self, violation_count: int = 1) -> float:
        """Calculate penalty based on weight and violations."""
        return self.weight * violation_count * self.priority.value


@dataclass
class SchedulingContext:
    """
    Context object containing all data needed for constraint evaluation.
    Passed to constraints to avoid database queries during solving.

    Resilience Integration (Tier 1):
    - hub_scores: Faculty hub vulnerability scores from network analysis
    - current_utilization: System utilization rate (target: <0.80)
    - n1_vulnerable_faculty: Faculty whose loss creates N-1 failure
    - preference_trails: Stigmergy preference data for soft optimization
    - zone_assignments: Faculty zone assignments for blast radius isolation
    """

    residents: list  # List of Person objects
    faculty: list  # List of Person objects
    blocks: list  # List of Block objects
    templates: list  # List of RotationTemplate objects

    # Lookup dictionaries for fast access
    resident_idx: dict[UUID, int] = field(default_factory=dict)
    block_idx: dict[UUID, int] = field(default_factory=dict)
    template_idx: dict[UUID, int] = field(default_factory=dict)
    blocks_by_date: dict[date, list] = field(default_factory=dict)

    # Availability matrix: {person_id: {block_id: {'available': bool, 'replacement': str}}}
    availability: dict[UUID, dict[UUID, dict]] = field(default_factory=dict)

    # Existing assignments (for incremental scheduling)
    existing_assignments: list = field(default_factory=list)

    # Locked blocks (preload/manual half-day slots mapped to block IDs)
    locked_blocks: set[tuple[UUID, UUID]] = field(default_factory=set)

    # Date range
    start_date: date | None = None
    end_date: date | None = None

    # =========================================================================
    # Resilience Data (populated by ResilienceService)
    # =========================================================================

    # Hub vulnerability scores: {faculty_id: composite_score (0.0-1.0)}
    # Higher scores = more critical = should be protected from over-assignment
    hub_scores: dict[UUID, float] = field(default_factory=dict)

    # Current system utilization rate (0.0-1.0)
    # Target: <0.80 to maintain 20% buffer per queuing theory
    current_utilization: float = 0.0

    # Faculty whose loss creates N-1 vulnerability (single point of failure)
    n1_vulnerable_faculty: set[UUID] = field(default_factory=set)

    # Preference trails from stigmergy: {faculty_id: {slot_type: strength}}
    # Used to weight assignments based on learned preferences
    preference_trails: dict[UUID, dict[str, float]] = field(default_factory=dict)

    # Zone assignments: {faculty_id: zone_id}
    # For blast radius isolation - faculty should primarily work in their zone
    zone_assignments: dict[UUID, UUID] = field(default_factory=dict)

    # Block zone assignments: {block_id: zone_id}
    # Maps blocks to zones for cross-zone penalty calculation
    block_zones: dict[UUID, UUID] = field(default_factory=dict)

    # Target utilization for buffer constraint (default 80%)
    target_utilization: float = 0.80

    def __post_init__(self):
        """
        Build lookup dictionaries and indices for fast constraint evaluation.

        This method is called automatically after dataclass initialization.
        It creates optimized lookup structures to avoid O(n) searches during
        constraint evaluation, significantly improving solver performance.

        Creates:
            - resident_idx: Maps resident UUID to array index for decision variables
            - block_idx: Maps block UUID to array index for decision variables
            - template_idx: Maps template UUID to array index for decision variables
            - blocks_by_date: Groups blocks by date for temporal constraint evaluation
        """
        self.resident_idx = {r.id: i for i, r in enumerate(self.residents)}
        self.block_idx = {b.id: i for i, b in enumerate(self.blocks)}
        self.template_idx = {t.id: i for i, t in enumerate(self.templates)}

        self.blocks_by_date = defaultdict(list)
        for block in self.blocks:
            self.blocks_by_date[block.date].append(block)

    def has_resilience_data(self) -> bool:
        """
        Check if resilience data has been populated in this context.

        Resilience data includes hub scores, utilization rates, N-1 vulnerability
        analysis, preference trails, and zone assignments. If this returns True,
        resilience-aware constraints can be activated.

        Returns:
            bool: True if any resilience data is present, False otherwise

        Example:
            >>> if context.has_resilience_data():
            ...     constraint_manager.enable("HubProtection")
        """
        return bool(self.hub_scores) or self.current_utilization > 0

    def get_hub_score(self, faculty_id: UUID) -> float:
        """
        Get hub vulnerability score for a faculty member.

        Hub scores range from 0.0 to 1.0, where higher scores indicate more
        critical "hub" faculty whose loss would significantly impact the system.
        These scores are computed by the ResilienceService using network centrality
        analysis.

        Args:
            faculty_id: UUID of the faculty member

        Returns:
            float: Hub score (0.0-1.0). Returns 0.0 if faculty is not a hub
                  or if resilience data is unavailable.

        Example:
            >>> hub_score = context.get_hub_score(faculty_id)
            >>> if hub_score > 0.6:
            ...     print("Critical hub - protect from over-assignment")
        """
        return self.hub_scores.get(faculty_id, 0.0)

    def is_n1_vulnerable(self, faculty_id: UUID) -> bool:
        """
        Check if faculty is a single point of failure (N-1 vulnerable).

        N-1 vulnerability means the schedule cannot survive the loss of this
        faculty member. This is identified through contingency analysis by the
        ResilienceService.

        Args:
            faculty_id: UUID of the faculty member to check

        Returns:
            bool: True if this faculty is a single point of failure, False otherwise

        Example:
            >>> if context.is_n1_vulnerable(faculty_id):
            ...     logger.warning(f"Faculty {faculty_id} is critical - no backup coverage")
        """
        return faculty_id in self.n1_vulnerable_faculty

    def get_preference_strength(self, faculty_id: UUID, slot_type: str) -> float:
        """
        Get preference trail strength for a faculty member and slot type.

        Preference trails are learned from historical scheduling patterns using
        stigmergy (swarm intelligence). Strength values indicate how strongly
        a faculty member prefers or avoids a particular slot type.

        Args:
            faculty_id: UUID of the faculty member
            slot_type: Type of slot (e.g., "monday_am", "friday_pm")

        Returns:
            float: Preference strength (0.0-1.0):
                  - 0.0-0.3: Strong avoidance
                  - 0.3-0.7: Neutral
                  - 0.7-1.0: Strong preference
                  Returns 0.5 (neutral) if no data available

        Example:
            >>> strength = context.get_preference_strength(faculty_id, "monday_am")
            >>> if strength > 0.7:
            ...     print("Faculty strongly prefers Monday mornings")
        """
        faculty_prefs = self.preference_trails.get(faculty_id, {})
        return faculty_prefs.get(slot_type, 0.5)


# =============================================================================
# HARD CONSTRAINTS - ACGME Compliance
# =============================================================================


class AvailabilityConstraint(HardConstraint):
    """
    Ensures residents are only assigned to blocks when available.
    Respects absences (vacation, deployment, TDY, etc.)
    """

    def __init__(self):
        super().__init__(
            name="Availability",
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
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

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
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
        self, assignments: list, context: SchedulingContext
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


class OnePersonPerBlockConstraint(HardConstraint):
    """
    Ensures at most one primary resident assigned per block.
    (Faculty supervision is separate)
    """

    def __init__(self, max_per_block: int = 1):
        super().__init__(
            name="OnePersonPerBlock",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.CRITICAL,
        )
        self.max_per_block = max_per_block

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """At most max_per_block residents per block."""
        x = variables.get("assignments", {})

        for block in context.blocks:
            b_i = context.block_idx[block.id]
            resident_vars = [
                x[context.resident_idx[r.id], b_i]
                for r in context.residents
                if (context.resident_idx[r.id], b_i) in x
            ]
            if resident_vars:
                model.Add(sum(resident_vars) <= self.max_per_block)

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """At most max_per_block residents per block."""
        import pulp

        x = variables.get("assignments", {})

        for block in context.blocks:
            b_i = context.block_idx[block.id]
            resident_vars = [
                x[context.resident_idx[r.id], b_i]
                for r in context.residents
                if (context.resident_idx[r.id], b_i) in x
            ]
            if resident_vars:
                model += (
                    pulp.lpSum(resident_vars) <= self.max_per_block,
                    f"max_per_block_{b_i}",
                )

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Check for multiple primary assignments per block."""
        violations = []
        block_counts = defaultdict(int)

        for assignment in assignments:
            if assignment.role == "primary":
                block_counts[assignment.block_id] += 1

        for block_id, count in block_counts.items():
            if count > self.max_per_block:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"Block has {count} primary assignments (max: {self.max_per_block})",
                        block_id=block_id,
                        details={"count": count, "max": self.max_per_block},
                    )
                )

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

    HOURS_PER_BLOCK = 6
    MAX_WEEKLY_HOURS = 80
    ROLLING_WEEKS = 4

    def __init__(self):
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
        self.max_blocks_per_window = (
            self.MAX_WEEKLY_HOURS * self.ROLLING_WEEKS
        ) // self.HOURS_PER_BLOCK

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
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
                b for b in context.blocks if window_start <= b.date <= window_end
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

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
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
                b for b in context.blocks if window_start <= b.date <= window_end
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

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Check 80-hour rule compliance."""
        violations = []

        # Group assignments by resident
        by_resident = defaultdict(list)
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
                    count
                    for d, count in dates_with_blocks.items()
                    if start_date <= d <= end_date
                )

                total_hours = total_blocks * self.HOURS_PER_BLOCK
                avg_weekly = total_hours / self.ROLLING_WEEKS

                if avg_weekly > self.MAX_WEEKLY_HOURS:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="CRITICAL",
                            message=f"{resident.name}: {avg_weekly:.1f} hours/week (limit: {self.MAX_WEEKLY_HOURS})",
                            person_id=resident.id,
                            details={
                                "window_start": start_date.isoformat(),
                                "average_weekly_hours": avg_weekly,
                            },
                        )
                    )
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

    MAX_CONSECUTIVE_DAYS = 6

    def __init__(self):
        super().__init__(
            name="1in7Rule",
            constraint_type=ConstraintType.CONSECUTIVE_DAYS,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
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

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
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

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Check for consecutive days violations."""
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
                        message=f"{resident.name}: {max_consecutive} consecutive duty days (limit: {self.MAX_CONSECUTIVE_DAYS})",
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

    PGY1_RATIO = 2  # 1 faculty per 2 PGY-1
    OTHER_RATIO = 4  # 1 faculty per 4 PGY-2/3

    def __init__(self):
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

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Supervision ratio is typically handled post-hoc for residents."""
        # This constraint is usually enforced during faculty assignment phase
        # The CP-SAT model focuses on resident assignment
        pass

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Supervision ratio is typically handled post-hoc for residents."""
        pass

    def validate(
        self, assignments: list, context: SchedulingContext
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
                violations.append(
                    ConstraintViolation(
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
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class ClinicCapacityConstraint(HardConstraint):
    """
    Ensures clinic capacity limits are respected.
    Each rotation template may have a max_residents limit.
    """

    def __init__(self):
        super().__init__(
            name="ClinicCapacity",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Enforce template capacity limits per block."""
        variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})  # (r, b, t) -> var

        if not template_vars:
            return  # No template-specific variables

        # Group by (block, template)
        for block in context.blocks:
            b_i = context.block_idx[block.id]
            for template in context.templates:
                if template.max_residents and template.max_residents > 0:
                    t_i = context.template_idx[template.id]

                    template_block_vars = [
                        template_vars[r_i, b_i, t_i]
                        for r in context.residents
                        if (r_i := context.resident_idx[r.id], b_i, t_i)
                        in template_vars
                    ]

                    if template_block_vars:
                        model.Add(sum(template_block_vars) <= template.max_residents)

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Enforce template capacity limits per block."""
        import pulp

        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        constraint_count = 0
        for block in context.blocks:
            b_i = context.block_idx[block.id]
            for template in context.templates:
                if template.max_residents and template.max_residents > 0:
                    t_i = context.template_idx[template.id]

                    template_block_vars = [
                        template_vars[(context.resident_idx[r.id], b_i, t_i)]
                        for r in context.residents
                        if (context.resident_idx[r.id], b_i, t_i) in template_vars
                    ]

                    if template_block_vars:
                        model += (
                            pulp.lpSum(template_block_vars) <= template.max_residents,
                            f"capacity_{b_i}_{t_i}_{constraint_count}",
                        )
                        constraint_count += 1

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Check capacity violations."""
        violations = []

        # Group by (block, template)
        by_block_template = defaultdict(int)
        for a in assignments:
            if a.rotation_template_id:
                by_block_template[(a.block_id, a.rotation_template_id)] += 1

        template_limits = {t.id: t.max_residents for t in context.templates}
        template_names = {t.id: t.name for t in context.templates}

        for (block_id, template_id), count in by_block_template.items():
            limit = template_limits.get(template_id)
            if limit and count > limit:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"{template_names.get(template_id, 'Template')}: {count} assigned (max: {limit})",
                        block_id=block_id,
                        details={"count": count, "limit": limit},
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class MaxPhysiciansInClinicConstraint(HardConstraint):
    """
    Ensures physical space limitations are respected.

    Maximum number of physicians (faculty + residents combined) allowed
    in clinic at any one time, regardless of role or PGY level.

    This is a physical space constraint - the clinic can only accommodate
    a limited number of providers simultaneously.

    Default: 6 physicians maximum per clinic session (AM or PM).
    """

    def __init__(self, max_physicians: int = 6):
        """
        Initialize the constraint.

        Args:
            max_physicians: Maximum providers allowed in clinic per session.
                           Default is 6.
        """
        super().__init__(
            name="MaxPhysiciansInClinic",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )
        self.max_physicians = max_physicians

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Enforce maximum physicians per clinic block."""
        x = variables.get("assignments", {})
        template_vars = variables.get("template_assignments", {})

        if not x and not template_vars:
            return

        # Identify clinic templates
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "activity_type") and t.activity_type == "outpatient"
        }

        if not clinic_template_ids:
            return  # No clinic templates defined

        # For each block, sum all clinic assignments (residents + faculty)
        for block in context.blocks:
            b_i = context.block_idx[block.id]
            clinic_vars = []

            # Collect resident assignments to clinic templates
            if template_vars:
                for template in context.templates:
                    if template.id in clinic_template_ids:
                        t_i = context.template_idx[template.id]
                        for r in context.residents:
                            r_i = context.resident_idx[r.id]
                            if (r_i, b_i, t_i) in template_vars:
                                clinic_vars.append(template_vars[r_i, b_i, t_i])

            # Faculty assignments are typically handled post-hoc,
            # but if faculty variables exist, include them
            faculty_vars = variables.get("faculty_assignments", {})
            if faculty_vars:
                for f in context.faculty:
                    f_i = context.faculty_idx.get(f.id)
                    if f_i is not None and (f_i, b_i) in faculty_vars:
                        clinic_vars.append(faculty_vars[f_i, b_i])

            if clinic_vars:
                model.Add(sum(clinic_vars) <= self.max_physicians)

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Enforce maximum physicians per clinic block using PuLP."""
        import pulp

        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "activity_type") and t.activity_type == "outpatient"
        }

        if not clinic_template_ids:
            return

        constraint_count = 0
        for block in context.blocks:
            b_i = context.block_idx[block.id]
            clinic_vars = []

            for template in context.templates:
                if template.id in clinic_template_ids:
                    t_i = context.template_idx[template.id]
                    for r in context.residents:
                        r_i = context.resident_idx[r.id]
                        if (r_i, b_i, t_i) in template_vars:
                            clinic_vars.append(template_vars[(r_i, b_i, t_i)])

            if clinic_vars:
                model += (
                    pulp.lpSum(clinic_vars) <= self.max_physicians,
                    f"max_physicians_clinic_{b_i}_{constraint_count}",
                )
                constraint_count += 1

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Check maximum physicians in clinic per block."""
        violations = []

        # Identify clinic templates
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "activity_type") and t.activity_type == "outpatient"
        }

        if not clinic_template_ids:
            return ConstraintResult(satisfied=True, violations=[])

        # Count all persons (faculty + residents) per clinic block
        by_block = defaultdict(int)
        for a in assignments:
            if a.rotation_template_id in clinic_template_ids:
                by_block[a.block_id] += 1

        # Check limits
        block_dates = {b.id: (b.date, b.time_of_day) for b in context.blocks}

        for block_id, count in by_block.items():
            if count > self.max_physicians:
                block_info = block_dates.get(block_id, ("Unknown", "Unknown"))
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH",
                        message=f"Clinic has {count} physicians on {block_info[0]} {block_info[1]} (max: {self.max_physicians})",
                        block_id=block_id,
                        details={"count": count, "limit": self.max_physicians},
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


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

    def __init__(self):
        """Initialize the constraint."""
        super().__init__(
            name="WednesdayAMInternOnly",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def _is_wednesday_am(self, block) -> bool:
        """Check if a block is Wednesday AM."""
        return (
            hasattr(block, "date")
            and block.date.weekday() == self.WEDNESDAY
            and block.time_of_day == "AM"
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Prevent non-intern assignments on Wednesday AM."""
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        # Identify clinic templates
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "activity_type") and t.activity_type == "outpatient"
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

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Prevent non-intern assignments on Wednesday AM using PuLP."""
        template_vars = variables.get("template_assignments", {})

        if not template_vars:
            return

        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "activity_type") and t.activity_type == "outpatient"
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
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Check that Wednesday AM clinic has only interns."""
        violations = []

        # Build lookup tables
        clinic_template_ids = {
            t.id
            for t in context.templates
            if hasattr(t, "activity_type") and t.activity_type == "outpatient"
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


# =============================================================================
# SOFT CONSTRAINTS - Optimization
# =============================================================================


class EquityConstraint(SoftConstraint):
    """
    Balances workload across residents.

    Now supports heterogeneous targets:
    - If resident has target_clinical_blocks set, penalizes deviation from that target
    - Otherwise, uses global average for equity

    This fixes the homogeneity assumption where all residents were expected
    to work the same number of blocks.
    """

    def __init__(self, weight: float = 10.0):
        super().__init__(
            name="Equity",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Add equity objective to model with support for individual targets."""
        x = variables.get("assignments", {})

        if not x:
            return

        # Check if residents have individual targets
        has_individual_targets = any(
            hasattr(r, "target_clinical_blocks")
            and r.target_clinical_blocks is not None
            for r in context.residents
        )

        if has_individual_targets:
            # Use individual targets - penalize deviation from each resident's target
            total_deviation = 0
            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_total = sum(
                    x[r_i, context.block_idx[b.id]]
                    for b in context.blocks
                    if (r_i, context.block_idx[b.id]) in x
                )

                if (
                    hasattr(resident, "target_clinical_blocks")
                    and resident.target_clinical_blocks
                ):
                    target = resident.target_clinical_blocks
                    # Create deviation variable (absolute value approximation)
                    deviation = model.NewIntVar(
                        0, len(context.blocks), f"deviation_{r_i}"
                    )
                    model.Add(deviation >= resident_total - target)
                    model.Add(deviation >= target - resident_total)
                    total_deviation += deviation

            variables["equity_penalty"] = total_deviation
        else:
            # Fall back to original equity logic (minimize max assignments)
            max_assigns = model.NewIntVar(0, len(context.blocks), "max_assignments")

            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_total = sum(
                    x[r_i, context.block_idx[b.id]]
                    for b in context.blocks
                    if (r_i, context.block_idx[b.id]) in x
                )
                model.Add(resident_total <= max_assigns)

            variables["equity_penalty"] = max_assigns

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add equity objective to model with support for individual targets."""
        import pulp

        x = variables.get("assignments", {})

        if not x:
            return

        # Check if residents have individual targets
        has_individual_targets = any(
            hasattr(r, "target_clinical_blocks")
            and r.target_clinical_blocks is not None
            for r in context.residents
        )

        if has_individual_targets:
            # Use individual targets - penalize deviation from each resident's target
            total_deviation = []

            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_vars = [
                    x[r_i, context.block_idx[b.id]]
                    for b in context.blocks
                    if (r_i, context.block_idx[b.id]) in x
                ]

                if (
                    resident_vars
                    and hasattr(resident, "target_clinical_blocks")
                    and resident.target_clinical_blocks
                ):
                    resident_total = pulp.lpSum(resident_vars)
                    target = resident.target_clinical_blocks

                    # Create deviation variables (absolute value via two inequalities)
                    deviation_pos = pulp.LpVariable(
                        f"deviation_pos_{r_i}", lowBound=0, cat="Integer"
                    )
                    deviation_neg = pulp.LpVariable(
                        f"deviation_neg_{r_i}", lowBound=0, cat="Integer"
                    )

                    # resident_total - target = deviation_pos - deviation_neg
                    model += (
                        resident_total - target == deviation_pos - deviation_neg,
                        f"deviation_def_{r_i}",
                    )

                    total_deviation.append(deviation_pos + deviation_neg)

            if total_deviation:
                variables["equity_penalty"] = pulp.lpSum(total_deviation)
            else:
                # No targets set, use original logic
                max_assigns = pulp.LpVariable(
                    "max_assignments", lowBound=0, cat="Integer"
                )
                for resident in context.residents:
                    r_i = context.resident_idx[resident.id]
                    resident_vars = [
                        x[r_i, context.block_idx[b.id]]
                        for b in context.blocks
                        if (r_i, context.block_idx[b.id]) in x
                    ]
                    if resident_vars:
                        model += (
                            pulp.lpSum(resident_vars) <= max_assigns,
                            f"equity_{r_i}",
                        )
                variables["equity_penalty"] = max_assigns
        else:
            # Fall back to original equity logic (minimize max assignments)
            max_assigns = pulp.LpVariable("max_assignments", lowBound=0, cat="Integer")

            for resident in context.residents:
                r_i = context.resident_idx[resident.id]
                resident_vars = [
                    x[r_i, context.block_idx[b.id]]
                    for b in context.blocks
                    if (r_i, context.block_idx[b.id]) in x
                ]
                if resident_vars:
                    model += (pulp.lpSum(resident_vars) <= max_assigns, f"equity_{r_i}")

            variables["equity_penalty"] = max_assigns

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Calculate equity score."""
        by_resident = defaultdict(int)
        for a in assignments:
            if a.person_id in context.resident_idx:
                by_resident[a.person_id] += 1

        if not by_resident:
            return ConstraintResult(satisfied=True, penalty=0.0)

        counts = list(by_resident.values())
        max_count = max(counts)
        min_count = min(counts)
        spread = max_count - min_count

        # Penalty based on spread
        penalty = spread * self.weight

        violations = []
        if spread > len(context.blocks) // len(context.residents):
            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="MEDIUM",
                    message=f"Workload imbalance: {min_count} to {max_count} assignments",
                    details={"min": min_count, "max": max_count, "spread": spread},
                )
            )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=penalty,
        )


class CoverageConstraint(SoftConstraint):
    """
    Maximizes block coverage (number of assigned blocks).
    Primary optimization objective.
    """

    def __init__(self, weight: float = 1000.0):
        super().__init__(
            name="Coverage",
            constraint_type=ConstraintType.CAPACITY,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Add coverage to objective."""
        x = variables.get("assignments", {})

        if not x:
            return

        total = sum(x.values())
        variables["coverage_bonus"] = total

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add coverage to objective."""
        import pulp

        x = variables.get("assignments", {})

        if not x:
            return

        variables["coverage_bonus"] = pulp.lpSum(x.values())

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Calculate coverage rate."""
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        assigned_blocks = {a.block_id for a in assignments}

        coverage_rate = (
            len(assigned_blocks) / len(workday_blocks) if workday_blocks else 0
        )

        violations = []
        if coverage_rate < 0.9:
            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="MEDIUM",
                    message=f"Coverage rate: {coverage_rate * 100:.1f}%",
                    details={"coverage_rate": coverage_rate},
                )
            )

        return ConstraintResult(
            satisfied=True,
            violations=violations,
            penalty=(1 - coverage_rate) * self.weight,
        )


class ContinuityConstraint(SoftConstraint):
    """
    Encourages schedule continuity - residents staying in same rotation
    for consecutive blocks when appropriate.
    """

    def __init__(self, weight: float = 5.0):
        super().__init__(
            name="Continuity",
            constraint_type=ConstraintType.CONTINUITY,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Continuity is complex for CP-SAT, handled via preference."""
        # This would require tracking template assignments across consecutive blocks
        # For simplicity, we handle this in post-processing or validation
        pass

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Continuity is complex for PuLP, handled via preference."""
        pass

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Calculate continuity score (template changes)."""
        # Group by resident, sorted by date
        by_resident = defaultdict(list)
        for a in assignments:
            for b in context.blocks:
                if b.id == a.block_id:
                    by_resident[a.person_id].append((b.date, a.rotation_template_id))
                    break

        total_changes = 0
        for _person_id, date_templates in by_resident.items():
            sorted_dt = sorted(date_templates, key=lambda x: x[0])
            for i in range(1, len(sorted_dt)):
                if sorted_dt[i][1] != sorted_dt[i - 1][1]:
                    # Different template on consecutive assignment
                    if (sorted_dt[i][0] - sorted_dt[i - 1][0]).days <= 1:
                        total_changes += 1

        return ConstraintResult(
            satisfied=True,
            violations=[],
            penalty=total_changes * self.weight,
        )


class PreferenceConstraint(SoftConstraint):
    """
    Handles resident preferences for specific rotations, times, or blocks.
    Preferences are stored as a dictionary: {person_id: {rotation_id: preference_score}}
    """

    def __init__(
        self,
        preferences: dict[UUID, dict[UUID, float]] = None,
        weight: float = 2.0,
    ):
        super().__init__(
            name="Preferences",
            constraint_type=ConstraintType.PREFERENCE,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )
        self.preferences = preferences or {}

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Add preference bonus to objective."""
        # Would require template-specific assignment variables
        pass

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add preference bonus to objective."""
        pass

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """Calculate preference satisfaction."""
        total_preference = 0.0
        max_preference = 0.0

        for a in assignments:
            person_prefs = self.preferences.get(a.person_id, {})
            if a.rotation_template_id:
                pref_score = person_prefs.get(
                    a.rotation_template_id, 0.5
                )  # Neutral default
                total_preference += pref_score
                max_preference += 1.0

        if max_preference == 0:
            return ConstraintResult(satisfied=True, penalty=0.0)

        satisfaction = total_preference / max_preference
        penalty = (1 - satisfaction) * self.weight * len(assignments)

        return ConstraintResult(
            satisfied=True,
            violations=[],
            penalty=penalty,
        )


# =============================================================================
# RESILIENCE-AWARE SOFT CONSTRAINTS
# =============================================================================


class HubProtectionConstraint(SoftConstraint):
    """
    Protects hub faculty from over-assignment.

    Network theory shows that scale-free networks (common in organizations)
    are robust to random failure but extremely vulnerable to hub removal.
    This constraint distributes load away from critical "hub" faculty.

    Rationale:
    - Hub faculty cover unique services or are hard to replace
    - Over-assigning hubs increases systemic risk
    - If a hub becomes unavailable, the system may fail N-1 analysis

    Implementation:
    - Penalizes assignments to faculty with high hub scores
    - Penalty scales with hub_score * assignment_count
    - Critical hubs (score > 0.6) get 2x penalty multiplier
    """

    # Hub score thresholds
    HIGH_HUB_THRESHOLD = 0.4  # Above this = significant hub
    CRITICAL_HUB_THRESHOLD = 0.6  # Above this = critical hub (2x penalty)

    def __init__(self, weight: float = 15.0):
        super().__init__(
            name="HubProtection",
            constraint_type=ConstraintType.HUB_PROTECTION,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add hub protection penalty to CP-SAT model objective function.

        For each faculty with hub_score > HIGH_HUB_THRESHOLD (0.4), adds a penalty
        to the objective function that scales with:
        - Hub score (0.4-1.0)
        - Assignment count
        - Criticality multiplier (2x for scores > 0.6)

        This creates economic pressure in the optimization to distribute work
        away from critical hub faculty, improving system resilience.

        Args:
            model: OR-Tools CP-SAT model
            variables: Dictionary with "assignments" decision variables
            context: SchedulingContext with hub_scores populated

        Implementation:
            - For each hub faculty (score > 0.4):
              - Sum their assignments across all blocks
              - Multiply by (hub_score × multiplier × 100) as integer factor
              - Add to penalty variable in objective function
            - Critical hubs (score > 0.6) get 2× multiplier

        Example:
            Faculty with hub_score=0.7 assigned to 10 blocks:
            penalty = 10 × (0.7 × 2.0 × 100) = 1400 penalty units

        Note:
            Only active when context.hub_scores is populated by ResilienceService
        """
        x = variables.get("assignments", {})

        if not x or not context.hub_scores:
            return  # No resilience data available

        total_hub_penalty = 0

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            hub_score = context.get_hub_score(faculty.id)
            if hub_score < self.HIGH_HUB_THRESHOLD:
                continue  # Not a hub, no penalty

            # Count assignments to this faculty
            faculty_vars = [
                x[f_i, context.block_idx[b.id]]
                for b in context.blocks
                if (f_i, context.block_idx[b.id]) in x
            ]

            if not faculty_vars:
                continue

            # Penalty multiplier based on hub criticality
            multiplier = 2.0 if hub_score >= self.CRITICAL_HUB_THRESHOLD else 1.0

            # Create penalty variable
            faculty_total = sum(faculty_vars)
            # Scale penalty by hub_score and multiplier
            penalty_factor = int(hub_score * multiplier * 100)
            total_hub_penalty += faculty_total * penalty_factor

        if total_hub_penalty:
            variables["hub_penalty"] = total_hub_penalty

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add hub protection penalty to PuLP model."""
        import pulp

        x = variables.get("assignments", {})

        if not x or not context.hub_scores:
            return

        penalty_terms = []

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            hub_score = context.get_hub_score(faculty.id)
            if hub_score < self.HIGH_HUB_THRESHOLD:
                continue

            faculty_vars = [
                x[f_i, context.block_idx[b.id]]
                for b in context.blocks
                if (f_i, context.block_idx[b.id]) in x
            ]

            if faculty_vars:
                multiplier = 2.0 if hub_score >= self.CRITICAL_HUB_THRESHOLD else 1.0
                penalty_factor = hub_score * multiplier
                penalty_terms.append(pulp.lpSum(faculty_vars) * penalty_factor)

        if penalty_terms:
            variables["hub_penalty"] = pulp.lpSum(penalty_terms)

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate hub protection and calculate penalty.

        Reports:
        - Which hubs are over-assigned
        - Total hub concentration risk
        """
        violations = []
        total_penalty = 0.0

        if not context.hub_scores:
            return ConstraintResult(satisfied=True, penalty=0.0)

        # Count assignments per faculty
        faculty_counts = defaultdict(int)
        for a in assignments:
            faculty_counts[a.person_id] += 1

        # Calculate average assignments
        if faculty_counts:
            avg_assignments = sum(faculty_counts.values()) / len(faculty_counts)
        else:
            avg_assignments = 0

        for faculty in context.faculty:
            hub_score = context.get_hub_score(faculty.id)
            if hub_score < self.HIGH_HUB_THRESHOLD:
                continue

            count = faculty_counts.get(faculty.id, 0)
            multiplier = 2.0 if hub_score >= self.CRITICAL_HUB_THRESHOLD else 1.0

            # Calculate penalty
            penalty = count * hub_score * multiplier * self.weight
            total_penalty += penalty

            # Report if hub is over-assigned (> average)
            if count > avg_assignments * 1.2:  # 20% above average
                severity = (
                    "HIGH" if hub_score >= self.CRITICAL_HUB_THRESHOLD else "MEDIUM"
                )
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity=severity,
                        message=f"Hub faculty {faculty.name} (score={hub_score:.2f}) has {count} assignments (avg={avg_assignments:.1f})",
                        person_id=faculty.id,
                        details={
                            "hub_score": hub_score,
                            "assignment_count": count,
                            "average_assignments": avg_assignments,
                            "is_critical_hub": hub_score >= self.CRITICAL_HUB_THRESHOLD,
                        },
                    )
                )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )


class UtilizationBufferConstraint(SoftConstraint):
    """
    Maintains capacity buffer to absorb unexpected demand.

    Based on queuing theory (Erlang-C): wait times increase exponentially
    as utilization approaches 100%. The 80% threshold provides buffer for:
    - Unexpected absences
    - Emergency coverage needs
    - Surge demand

    Rationale:
    - At 80% utilization, wait times are manageable
    - At 90%+, small disturbances cause cascade failures
    - 20% buffer = "defense in depth" against surprises

    Implementation:
    - Calculates effective utilization from assignment count
    - Penalizes schedules that exceed target utilization
    - Penalty increases sharply above threshold (quadratic)
    """

    def __init__(self, weight: float = 20.0, target_utilization: float = 0.80):
        super().__init__(
            name="UtilizationBuffer",
            constraint_type=ConstraintType.UTILIZATION_BUFFER,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )
        self.target_utilization = target_utilization

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add utilization buffer constraint to CP-SAT model.

        Implements queuing theory-based capacity management: penalizes schedules
        that exceed the target utilization threshold (default 80%). Based on
        Erlang-C formula which shows that wait times increase exponentially
        as utilization approaches 100%.

        The 80% threshold provides a 20% buffer for:
        - Unexpected absences (illness, family emergencies)
        - Surge demand (patient volume spikes, special events)
        - Emergency coverage needs

        Args:
            model: OR-Tools CP-SAT model
            variables: Dictionary with "assignments" decision variables
            context: SchedulingContext with target_utilization setting

        Implementation:
            1. Calculate safe capacity: max_capacity × target_utilization
            2. Sum all assignments across faculty and blocks
            3. Create over_utilization variable: max(0, total - safe_capacity)
            4. Add to objective function as penalty

        Example:
            System with 10 faculty, 100 blocks, 80% target:
            - Max capacity: 10 × 100 = 1000 assignment-blocks
            - Safe capacity: 1000 × 0.80 = 800 assignment-blocks
            - If schedule has 850 assignments: penalty = 50 units
            - If schedule has 900 assignments: penalty = 100 units

        Queuing Theory Rationale:
            At 80% utilization: average wait times are acceptable
            At 90% utilization: wait times increase 3-5x
            At 95%+ utilization: system experiences cascade failures

        Note:
            Uses linear penalty in CP-SAT (quadratic is too complex).
            Validation step uses quadratic penalty for more accurate assessment.
        """
        x = variables.get("assignments", {})

        if not x:
            return

        # Calculate maximum safe assignments
        # Max capacity = faculty * blocks_per_faculty
        # Safe capacity = max_capacity * target_utilization
        max_blocks_per_faculty = len(context.blocks)
        max_capacity = len(context.faculty) * max_blocks_per_faculty
        safe_capacity = int(max_capacity * context.target_utilization)

        # Sum all assignments
        total_assignments = sum(x.values())

        # Create over-utilization variable
        over_util = model.NewIntVar(0, max_capacity, "over_utilization")
        model.Add(over_util >= total_assignments - safe_capacity)
        model.Add(over_util >= 0)

        # Quadratic-ish penalty: over_util * over_util is complex in CP-SAT
        # Use linear approximation with higher weight for large overages
        variables["utilization_penalty"] = over_util

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add utilization buffer constraint to PuLP model."""
        import pulp

        x = variables.get("assignments", {})

        if not x:
            return

        max_blocks_per_faculty = len(context.blocks)
        max_capacity = len(context.faculty) * max_blocks_per_faculty
        safe_capacity = int(max_capacity * context.target_utilization)

        total_assignments = pulp.lpSum(x.values())

        # Over-utilization slack variable
        over_util = pulp.LpVariable("over_utilization", lowBound=0, cat="Integer")
        model += over_util >= total_assignments - safe_capacity, "utilization_slack"

        variables["utilization_penalty"] = over_util

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate utilization buffer and calculate penalty.

        Reports:
        - Current utilization rate
        - Buffer remaining
        - Whether in danger zone
        """
        violations = []

        # Calculate utilization
        # This is a simplified calculation - actual would consider
        # faculty-specific availability
        total_assignments = len([a for a in assignments if a.role == "primary"])
        workday_blocks = len([b for b in context.blocks if not b.is_weekend])

        # Capacity = faculty who can work * average available blocks
        available_faculty = len(
            [
                f
                for f in context.faculty
                if any(
                    context.availability.get(f.id, {})
                    .get(b.id, {})
                    .get("available", True)
                    for b in context.blocks
                )
            ]
        )

        if available_faculty == 0 or workday_blocks == 0:
            return ConstraintResult(satisfied=True, penalty=0.0)

        # Simplified: each faculty can cover 1 block per day on average
        max_capacity = available_faculty * workday_blocks
        utilization = total_assignments / max_capacity if max_capacity > 0 else 0

        # Calculate penalty
        target = (
            context.target_utilization
            if context.target_utilization
            else self.target_utilization
        )

        if utilization <= target:
            penalty = 0.0
            buffer_remaining = target - utilization
        else:
            # Quadratic penalty above threshold
            over_threshold = utilization - target
            penalty = (over_threshold**2) * self.weight * 100
            buffer_remaining = 0.0

            # Determine severity based on how far over
            if utilization >= 0.95:
                severity = "CRITICAL"
            elif utilization >= 0.90:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity=severity,
                    message=f"Utilization {utilization:.0%} exceeds target {target:.0%} (buffer exhausted)",
                    details={
                        "utilization_rate": utilization,
                        "target_utilization": target,
                        "buffer_remaining": buffer_remaining,
                        "total_assignments": total_assignments,
                        "max_capacity": max_capacity,
                        "danger_zone": utilization >= 0.90,
                    },
                )
            )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=penalty,
        )


# =============================================================================
# TIER 2: STRATEGIC RESILIENCE CONSTRAINTS
# =============================================================================


class ZoneBoundaryConstraint(SoftConstraint):
    """
    Respects blast radius zone boundaries in scheduling.

    AWS Architecture Pattern: Failures should be contained within defined
    boundaries ("cells" or "availability zones"). A problem in one area
    cannot propagate to affect others.

    Rationale:
    - Each zone has dedicated faculty as primary coverage
    - Cross-zone assignments weaken isolation
    - When Zone A fails, Zones B and C should continue unaffected

    Implementation:
    - Penalizes assignments where faculty zone != block zone
    - Severity increases with containment level (soft → lockdown)
    - Critical zones (e.g., inpatient) have higher penalties
    """

    # Zone type priority multipliers
    ZONE_PRIORITY = {
        "inpatient": 2.0,  # Critical - highest isolation
        "outpatient": 1.5,  # Important
        "on_call": 1.5,  # Important
        "education": 1.0,  # Standard
        "research": 0.8,  # Flexible
        "admin": 0.5,  # Most flexible
    }

    def __init__(self, weight: float = 12.0):
        super().__init__(
            name="ZoneBoundary",
            constraint_type=ConstraintType.ZONE_BOUNDARY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add zone boundary penalty to CP-SAT model.

        For each assignment where faculty_zone != block_zone, add penalty.
        """
        x = variables.get("assignments", {})

        if not x or not context.zone_assignments or not context.block_zones:
            return  # No zone data available

        total_zone_penalty = 0

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_zone = context.zone_assignments.get(faculty.id)
            if not faculty_zone:
                continue  # Faculty not assigned to a zone

            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i) not in x:
                    continue

                block_zone = context.block_zones.get(block.id)
                if not block_zone:
                    continue  # Block not in a zone

                # Penalty if zones don't match
                if faculty_zone != block_zone:
                    penalty_factor = 10  # Base penalty for cross-zone
                    total_zone_penalty += x[f_i, b_i] * penalty_factor

        if total_zone_penalty:
            variables["zone_penalty"] = total_zone_penalty

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add zone boundary penalty to PuLP model."""
        import pulp

        x = variables.get("assignments", {})

        if not x or not context.zone_assignments or not context.block_zones:
            return

        penalty_terms = []

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_zone = context.zone_assignments.get(faculty.id)
            if not faculty_zone:
                continue

            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i) not in x:
                    continue

                block_zone = context.block_zones.get(block.id)
                if block_zone and faculty_zone != block_zone:
                    penalty_factor = 10
                    penalty_terms.append(x[f_i, b_i] * penalty_factor)

        if penalty_terms:
            variables["zone_penalty"] = pulp.lpSum(penalty_terms)

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate zone boundary compliance.

        Reports:
        - Cross-zone assignment count
        - Which zones are being violated
        - Total isolation breach penalty
        """
        violations = []
        total_penalty = 0.0

        if not context.zone_assignments or not context.block_zones:
            return ConstraintResult(satisfied=True, penalty=0.0)

        cross_zone_count = 0
        zone_violation_details = defaultdict(int)

        for assignment in assignments:
            faculty_zone = context.zone_assignments.get(assignment.person_id)
            block_zone = context.block_zones.get(assignment.block_id)

            if faculty_zone and block_zone and faculty_zone != block_zone:
                cross_zone_count += 1
                zone_violation_details[(str(faculty_zone), str(block_zone))] += 1
                total_penalty += self.weight

        if cross_zone_count > 0:
            # Determine severity based on percentage
            total_assignments = len(assignments)
            cross_zone_pct = (
                cross_zone_count / total_assignments if total_assignments > 0 else 0
            )

            if cross_zone_pct >= 0.20:
                severity = "HIGH"
            elif cross_zone_pct >= 0.10:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity=severity,
                    message=f"{cross_zone_count} cross-zone assignments ({cross_zone_pct:.0%} of total) - blast radius isolation weakened",
                    details={
                        "cross_zone_count": cross_zone_count,
                        "total_assignments": total_assignments,
                        "cross_zone_percentage": cross_zone_pct,
                        "zone_violations": dict(zone_violation_details),
                    },
                )
            )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )


class PreferenceTrailConstraint(SoftConstraint):
    """
    Uses stigmergy preference trails for assignment optimization.

    Swarm Intelligence Pattern (Biology/AI): Individual agents following
    simple rules can collectively solve complex problems through indirect
    coordination. Ants find shortest paths without central planning by
    depositing and following pheromone trails.

    Rationale:
    - Preference trails encode learned faculty preferences
    - Strong trails indicate consistent preference/avoidance
    - Following trails improves satisfaction without explicit rules

    Implementation:
    - Rewards assignments matching strong preference trails
    - Penalizes assignments matching strong avoidance trails
    - Trail strength (0-1) modulates reward/penalty
    """

    # Trail strength thresholds
    STRONG_TRAIL_THRESHOLD = 0.6  # Above this = strong signal
    WEAK_TRAIL_THRESHOLD = 0.3  # Below this = ignore

    def __init__(self, weight: float = 8.0):
        super().__init__(
            name="PreferenceTrail",
            constraint_type=ConstraintType.PREFERENCE_TRAIL,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add preference trail bonus/penalty to CP-SAT model.

        For each (faculty, block), check if matching preference trail exists.
        """
        x = variables.get("assignments", {})

        if not x or not context.preference_trails:
            return  # No preference data available

        total_trail_score = 0

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_prefs = context.preference_trails.get(faculty.id, {})
            if not faculty_prefs:
                continue

            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i) not in x:
                    continue

                # Determine slot type from block
                slot_type = (
                    f"{block.date.strftime('%A').lower()}_{block.time_of_day.lower()}"
                )

                # Check if we have a preference for this slot type
                trail_strength = faculty_prefs.get(slot_type, 0.5)

                if trail_strength >= self.STRONG_TRAIL_THRESHOLD:
                    # Bonus for matching strong preference
                    bonus = int((trail_strength - 0.5) * 20)
                    total_trail_score += x[f_i, b_i] * bonus
                elif trail_strength <= (1.0 - self.STRONG_TRAIL_THRESHOLD):
                    # Penalty for matching strong avoidance (low trail = avoidance)
                    penalty = int((0.5 - trail_strength) * 20)
                    total_trail_score -= x[f_i, b_i] * penalty

        if total_trail_score:
            variables["trail_bonus"] = total_trail_score

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add preference trail bonus/penalty to PuLP model."""
        import pulp

        x = variables.get("assignments", {})

        if not x or not context.preference_trails:
            return

        bonus_terms = []
        penalty_terms = []

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_prefs = context.preference_trails.get(faculty.id, {})
            if not faculty_prefs:
                continue

            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i) not in x:
                    continue

                slot_type = (
                    f"{block.date.strftime('%A').lower()}_{block.time_of_day.lower()}"
                )
                trail_strength = faculty_prefs.get(slot_type, 0.5)

                if trail_strength >= self.STRONG_TRAIL_THRESHOLD:
                    bonus = (trail_strength - 0.5) * 2
                    bonus_terms.append(x[f_i, b_i] * bonus)
                elif trail_strength <= (1.0 - self.STRONG_TRAIL_THRESHOLD):
                    penalty = (0.5 - trail_strength) * 2
                    penalty_terms.append(x[f_i, b_i] * penalty)

        if bonus_terms:
            variables["trail_bonus"] = pulp.lpSum(bonus_terms)
        if penalty_terms:
            variables["trail_penalty"] = pulp.lpSum(penalty_terms)

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate preference trail alignment.

        Reports:
        - How well assignments align with preference trails
        - Assignments against strong avoidance trails
        """
        violations = []
        total_penalty = 0.0

        if not context.preference_trails:
            return ConstraintResult(satisfied=True, penalty=0.0)

        aligned_count = 0
        misaligned_count = 0
        total_checked = 0

        for assignment in assignments:
            faculty_prefs = context.preference_trails.get(assignment.person_id, {})
            if not faculty_prefs:
                continue

            # Get block for slot type
            block = None
            for b in context.blocks:
                if b.id == assignment.block_id:
                    block = b
                    break

            if not block:
                continue

            slot_type = (
                f"{block.date.strftime('%A').lower()}_{block.time_of_day.lower()}"
            )
            trail_strength = faculty_prefs.get(slot_type, 0.5)
            total_checked += 1

            if trail_strength >= self.STRONG_TRAIL_THRESHOLD:
                aligned_count += 1
            elif trail_strength <= (1.0 - self.STRONG_TRAIL_THRESHOLD):
                misaligned_count += 1
                total_penalty += (0.5 - trail_strength) * self.weight

        if total_checked > 0:
            alignment_rate = aligned_count / total_checked
            misalignment_rate = misaligned_count / total_checked

            # Report if significant misalignment
            if misaligned_count > 0 and misalignment_rate >= 0.10:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="MEDIUM" if misalignment_rate >= 0.20 else "LOW",
                        message=f"{misaligned_count} assignments against preference trails ({misalignment_rate:.0%})",
                        details={
                            "aligned_count": aligned_count,
                            "misaligned_count": misaligned_count,
                            "total_checked": total_checked,
                            "alignment_rate": alignment_rate,
                            "misalignment_rate": misalignment_rate,
                        },
                    )
                )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )


class N1VulnerabilityConstraint(SoftConstraint):
    """
    Prevents schedules that create single points of failure.

    Power Grid N-1 Pattern: The system must survive the loss of any single
    component. Applied to scheduling: no service should depend on exactly
    one faculty member being available.

    Rationale:
    - N-1 compliance = schedule survives any single faculty absence
    - Single points of failure cause cascade risks
    - Cross-training and redundancy improve resilience

    Implementation:
    - Penalizes assignments that create N-1 vulnerabilities
    - Higher penalty for critical services/time slots
    - Identifies faculty who are sole coverage providers
    """

    def __init__(self, weight: float = 25.0):
        super().__init__(
            name="N1Vulnerability",
            constraint_type=ConstraintType.N1_VULNERABILITY,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add N-1 vulnerability penalty to CP-SAT model.

        For blocks where only one faculty could be assigned, add penalty.
        This encourages solutions with redundancy.
        """
        x = variables.get("assignments", {})

        if not x:
            return

        # For each block, count how many faculty could cover it
        # If only 1 faculty assigned and no alternatives, that's N-1 vulnerable
        total_n1_penalty = 0

        for block in context.blocks:
            b_i = context.block_idx[block.id]

            # Count available faculty for this block
            available_for_block = []
            for faculty in context.faculty:
                f_i = context.resident_idx.get(faculty.id)
                if f_i is None:
                    continue

                # Check availability
                is_available = (
                    context.availability.get(faculty.id, {})
                    .get(block.id, {})
                    .get("available", True)
                )

                if is_available and (f_i, b_i) in x:
                    available_for_block.append((f_i, faculty.id))

            # If only 1-2 faculty available, add penalty for assignments
            if len(available_for_block) <= 2:
                for f_i, _ in available_for_block:
                    # Penalty scaled by scarcity: 1 available = high, 2 = medium
                    scarcity_factor = 3 - len(available_for_block)  # 2 or 1
                    total_n1_penalty += x[f_i, b_i] * scarcity_factor * 10

        if total_n1_penalty:
            variables["n1_penalty"] = total_n1_penalty

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add N-1 vulnerability penalty to PuLP model."""
        import pulp

        x = variables.get("assignments", {})

        if not x:
            return

        penalty_terms = []

        for block in context.blocks:
            b_i = context.block_idx[block.id]

            available_for_block = []
            for faculty in context.faculty:
                f_i = context.resident_idx.get(faculty.id)
                if f_i is None:
                    continue

                is_available = (
                    context.availability.get(faculty.id, {})
                    .get(block.id, {})
                    .get("available", True)
                )

                if is_available and (f_i, b_i) in x:
                    available_for_block.append(f_i)

            if len(available_for_block) <= 2:
                scarcity_factor = 3 - len(available_for_block)
                for f_i in available_for_block:
                    penalty_terms.append(x[f_i, b_i] * scarcity_factor)

        if penalty_terms:
            variables["n1_penalty"] = pulp.lpSum(penalty_terms)

    def validate(
        self, assignments: list, context: SchedulingContext
    ) -> ConstraintResult:
        """
        Validate N-1 compliance of the schedule.

        Reports:
        - Blocks that are N-1 vulnerable (single coverage)
        - Faculty who are single points of failure
        - Overall N-1 compliance rate
        """
        violations = []
        total_penalty = 0.0

        # Analyze each block for redundancy
        block_coverage = defaultdict(list)
        for assignment in assignments:
            block_coverage[assignment.block_id].append(assignment.person_id)

        n1_vulnerable_blocks = []
        sole_providers = defaultdict(int)

        for block in context.blocks:
            providers = block_coverage.get(block.id, [])

            if len(providers) == 1:
                n1_vulnerable_blocks.append(block.id)
                sole_providers[providers[0]] += 1
                total_penalty += self.weight

        # Also check faculty in n1_vulnerable_faculty set
        for faculty_id in context.n1_vulnerable_faculty:
            if faculty_id in sole_providers:
                # Already counted in sole_providers
                continue
            # Check how many assignments this faculty has
            faculty_assignments = [a for a in assignments if a.person_id == faculty_id]
            if faculty_assignments:
                # Add extra penalty for known N-1 vulnerable faculty
                total_penalty += len(faculty_assignments) * self.weight * 0.5

        # Report violations
        if n1_vulnerable_blocks:
            vulnerability_rate = (
                len(n1_vulnerable_blocks) / len(context.blocks) if context.blocks else 0
            )

            if vulnerability_rate >= 0.20:
                severity = "CRITICAL"
            elif vulnerability_rate >= 0.10:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity=severity,
                    message=f"{len(n1_vulnerable_blocks)} blocks have single-point-of-failure coverage ({vulnerability_rate:.0%})",
                    details={
                        "n1_vulnerable_blocks": len(n1_vulnerable_blocks),
                        "total_blocks": len(context.blocks),
                        "vulnerability_rate": vulnerability_rate,
                        "sole_provider_counts": dict(sole_providers),
                        "n1_pass": len(n1_vulnerable_blocks) == 0,
                    },
                )
            )

        # Report sole providers
        for faculty_id, sole_count in sole_providers.items():
            faculty_name = "Unknown"
            for f in context.faculty:
                if f.id == faculty_id:
                    faculty_name = f.name
                    break

            if sole_count >= 3:  # Report faculty who are sole provider for 3+ blocks
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="HIGH" if sole_count >= 5 else "MEDIUM",
                        message=f"Faculty {faculty_name} is sole provider for {sole_count} blocks - single point of failure risk",
                        person_id=faculty_id,
                        details={
                            "sole_coverage_blocks": sole_count,
                            "recommendation": "Cross-train backup faculty",
                        },
                    )
                )

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )


# =============================================================================
# CONSTRAINT MANAGER
# =============================================================================


class ConstraintManager:
    """
    Manages a collection of constraints for scheduling.

    Features:
    - Composable constraint sets
    - Priority-based ordering
    - Easy enable/disable
    - Validation aggregation
    """

    def __init__(self):
        self.constraints: list[Constraint] = []
        self._hard_constraints: list[HardConstraint] = []
        self._soft_constraints: list[SoftConstraint] = []

    def add(self, constraint: Constraint) -> "ConstraintManager":
        """
        Add a constraint to the manager.

        Constraints are automatically categorized as hard or soft based on
        their class type. Returns self to allow method chaining.

        Args:
            constraint: Constraint instance to add (HardConstraint or SoftConstraint)

        Returns:
            ConstraintManager: Self for method chaining

        Example:
            >>> manager = ConstraintManager()
            >>> manager.add(AvailabilityConstraint())\\
            ...        .add(EightyHourRuleConstraint())\\
            ...        .add(EquityConstraint(weight=10.0))
        """
        self.constraints.append(constraint)
        if isinstance(constraint, HardConstraint):
            self._hard_constraints.append(constraint)
        elif isinstance(constraint, SoftConstraint):
            self._soft_constraints.append(constraint)
        return self

    def remove(self, name: str) -> "ConstraintManager":
        """
        Remove a constraint by name.

        Returns self to allow method chaining. If constraint name is not found,
        no error is raised (idempotent operation).

        Args:
            name: Name of the constraint to remove (e.g., "80HourRule")

        Returns:
            ConstraintManager: Self for method chaining

        Example:
            >>> manager.remove("Continuity").remove("Preferences")
        """
        self.constraints = [c for c in self.constraints if c.name != name]
        self._hard_constraints = [c for c in self._hard_constraints if c.name != name]
        self._soft_constraints = [c for c in self._soft_constraints if c.name != name]
        return self

    def enable(self, name: str) -> "ConstraintManager":
        """
        Enable a constraint by name.

        Enabled constraints are applied during solving and validation.
        Returns self to allow method chaining.

        Args:
            name: Name of the constraint to enable (e.g., "HubProtection")

        Returns:
            ConstraintManager: Self for method chaining

        Example:
            >>> # Enable resilience constraints when data is available
            >>> if context.has_resilience_data():
            ...     manager.enable("HubProtection")\\
            ...            .enable("UtilizationBuffer")
        """
        for c in self.constraints:
            if c.name == name:
                c.enabled = True
        return self

    def disable(self, name: str) -> "ConstraintManager":
        """
        Disable a constraint by name.

        Disabled constraints are skipped during solving and validation.
        Returns self to allow method chaining.

        Args:
            name: Name of the constraint to disable (e.g., "Continuity")

        Returns:
            ConstraintManager: Self for method chaining

        Example:
            >>> # Disable soft constraints for faster solving
            >>> manager.disable("Continuity")\\
            ...        .disable("Preferences")
        """
        for c in self.constraints:
            if c.name == name:
                c.enabled = False
        return self

    def get_enabled(self) -> list[Constraint]:
        """
        Get all enabled constraints.

        Returns:
            list[Constraint]: List of enabled constraints (both hard and soft)

        Example:
            >>> enabled = manager.get_enabled()
            >>> print(f"Active constraints: {[c.name for c in enabled]}")
        """
        return [c for c in self.constraints if c.enabled]

    def get_hard_constraints(self) -> list[HardConstraint]:
        """
        Get enabled hard constraints.

        Hard constraints must be satisfied for a valid schedule. These typically
        enforce ACGME requirements, availability, and capacity limits.

        Returns:
            list[HardConstraint]: List of enabled hard constraints

        Example:
            >>> hard = manager.get_hard_constraints()
            >>> print(f"Must satisfy: {[c.name for c in hard]}")
        """
        return [c for c in self._hard_constraints if c.enabled]

    def get_soft_constraints(self) -> list[SoftConstraint]:
        """
        Get enabled soft constraints.

        Soft constraints are optimization objectives (equity, coverage, continuity).
        They have weights and contribute to the objective function.

        Returns:
            list[SoftConstraint]: List of enabled soft constraints

        Example:
            >>> soft = manager.get_soft_constraints()
            >>> total_weight = sum(c.weight for c in soft)
            >>> print(f"Optimization weights: {total_weight}")
        """
        return [c for c in self._soft_constraints if c.enabled]

    def apply_to_cpsat(
        self,
        model,
        variables: dict,
        context: SchedulingContext,
    ) -> None:
        """Apply all enabled constraints to CP-SAT model."""
        for constraint in sorted(self.get_enabled(), key=lambda c: -c.priority.value):
            try:
                constraint.add_to_cpsat(model, variables, context)
                logger.debug(f"Applied constraint to CP-SAT: {constraint.name}")
            except Exception as e:
                logger.error(f"Error applying {constraint.name} to CP-SAT: {e}")

    def apply_to_pulp(
        self,
        model,
        variables: dict,
        context: SchedulingContext,
    ) -> None:
        """Apply all enabled constraints to PuLP model."""
        for constraint in sorted(self.get_enabled(), key=lambda c: -c.priority.value):
            try:
                constraint.add_to_pulp(model, variables, context)
                logger.debug(f"Applied constraint to PuLP: {constraint.name}")
            except Exception as e:
                logger.error(f"Error applying {constraint.name} to PuLP: {e}")

    def validate_all(
        self,
        assignments: list,
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate all constraints and aggregate results."""
        all_violations = []
        total_penalty = 0.0
        all_satisfied = True

        for constraint in self.get_enabled():
            try:
                result = constraint.validate(assignments, context)
                all_violations.extend(result.violations)
                total_penalty += result.penalty
                if not result.satisfied:
                    all_satisfied = False
            except Exception as e:
                logger.error(f"Error validating {constraint.name}: {e}")

        return ConstraintResult(
            satisfied=all_satisfied,
            violations=all_violations,
            penalty=total_penalty,
        )

    @classmethod
    def create_default(cls) -> "ConstraintManager":
        """Create manager with default ACGME constraints."""
        manager = cls()

        # Hard constraints (ACGME compliance)
        manager.add(AvailabilityConstraint())
        manager.add(OnePersonPerBlockConstraint())
        manager.add(EightyHourRuleConstraint())
        manager.add(OneInSevenRuleConstraint())
        manager.add(SupervisionRatioConstraint())
        manager.add(ClinicCapacityConstraint())
        manager.add(MaxPhysiciansInClinicConstraint())
        manager.add(WednesdayAMInternOnlyConstraint())

        # Soft constraints (optimization)
        manager.add(CoverageConstraint(weight=1000.0))
        manager.add(EquityConstraint(weight=10.0))
        manager.add(ContinuityConstraint(weight=5.0))

        # Tier 1: Resilience-aware soft constraints (disabled by default for backward compatibility)
        manager.add(HubProtectionConstraint(weight=15.0))
        manager.add(UtilizationBufferConstraint(weight=20.0))
        # Tier 2: Strategic resilience constraints (disabled by default)
        manager.add(ZoneBoundaryConstraint(weight=12.0))
        manager.add(PreferenceTrailConstraint(weight=8.0))
        manager.add(N1VulnerabilityConstraint(weight=25.0))
        # Disabled by default - enabled when resilience data is provided
        manager.disable("HubProtection")
        manager.disable("UtilizationBuffer")
        manager.disable("ZoneBoundary")
        manager.disable("PreferenceTrail")
        manager.disable("N1Vulnerability")

        return manager

    @classmethod
    def create_resilience_aware(
        cls,
        target_utilization: float = 0.80,
        tier: int = 2,
    ) -> "ConstraintManager":
        """
        Create manager with resilience-aware constraints enabled.

        This configuration:
        - Includes all ACGME compliance constraints
        - Tier 1: Hub protection, utilization buffer
        - Tier 2: Zone boundaries, preference trails, N-1 vulnerability
        - Suitable for systems with ResilienceService integration

        Args:
            target_utilization: Maximum utilization before penalties (default 80%)
            tier: Maximum tier to enable (1 or 2, default 2)

        Returns:
            ConstraintManager with resilience constraints enabled
        """
        manager = cls()

        # Hard constraints (ACGME compliance)
        manager.add(AvailabilityConstraint())
        manager.add(OnePersonPerBlockConstraint())
        manager.add(EightyHourRuleConstraint())
        manager.add(OneInSevenRuleConstraint())
        manager.add(SupervisionRatioConstraint())
        manager.add(ClinicCapacityConstraint())
        manager.add(MaxPhysiciansInClinicConstraint())
        manager.add(WednesdayAMInternOnlyConstraint())

        # Soft constraints (optimization)
        manager.add(CoverageConstraint(weight=1000.0))
        manager.add(EquityConstraint(weight=10.0))
        manager.add(ContinuityConstraint(weight=5.0))

        # Tier 1: Core resilience constraints (ENABLED)
        manager.add(HubProtectionConstraint(weight=15.0))
        manager.add(
            UtilizationBufferConstraint(
                weight=20.0, target_utilization=target_utilization
            )
        )

        # Tier 2: Strategic resilience constraints
        manager.add(ZoneBoundaryConstraint(weight=12.0))
        manager.add(PreferenceTrailConstraint(weight=8.0))
        manager.add(N1VulnerabilityConstraint(weight=25.0))

        # Only enable Tier 2 if requested
        if tier < 2:
            manager.disable("ZoneBoundary")
            manager.disable("PreferenceTrail")
            manager.disable("N1Vulnerability")

        return manager

    @classmethod
    def create_minimal(cls) -> "ConstraintManager":
        """Create manager with minimal constraints (fast solving)."""
        manager = cls()

        manager.add(AvailabilityConstraint())
        manager.add(OnePersonPerBlockConstraint())
        manager.add(CoverageConstraint(weight=1000.0))

        return manager

    @classmethod
    def create_strict(cls) -> "ConstraintManager":
        """Create manager with all constraints enabled at high weight."""
        manager = cls.create_default()

        # Increase soft constraint weights
        for c in manager._soft_constraints:
            c.weight *= 2

        return manager
