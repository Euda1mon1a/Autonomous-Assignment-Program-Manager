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
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any, Callable, Optional
from uuid import UUID
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ConstraintPriority(Enum):
    """Priority levels for constraints."""
    CRITICAL = 100  # ACGME compliance, must satisfy
    HIGH = 75       # Important operational constraints
    MEDIUM = 50     # Preferences and soft requirements
    LOW = 25        # Nice-to-have optimizations


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
    # Resilience-aware constraint types
    RESILIENCE = "resilience"
    HUB_PROTECTION = "hub_protection"
    UTILIZATION_BUFFER = "utilization_buffer"


@dataclass
class ConstraintViolation:
    """Represents a constraint violation."""
    constraint_name: str
    constraint_type: ConstraintType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    message: str
    person_id: Optional[UUID] = None
    block_id: Optional[UUID] = None
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
        return float('inf')


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
    faculty: list    # List of Person objects
    blocks: list     # List of Block objects
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

    # Date range
    start_date: Optional[date] = None
    end_date: Optional[date] = None

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
        """Build lookup dictionaries."""
        self.resident_idx = {r.id: i for i, r in enumerate(self.residents)}
        self.block_idx = {b.id: i for i, b in enumerate(self.blocks)}
        self.template_idx = {t.id: i for i, t in enumerate(self.templates)}

        self.blocks_by_date = defaultdict(list)
        for block in self.blocks:
            self.blocks_by_date[block.date].append(block)

    def has_resilience_data(self) -> bool:
        """Check if resilience data has been populated."""
        return bool(self.hub_scores) or self.current_utilization > 0

    def get_hub_score(self, faculty_id: UUID) -> float:
        """Get hub score for faculty (0.0 if not a hub)."""
        return self.hub_scores.get(faculty_id, 0.0)

    def is_n1_vulnerable(self, faculty_id: UUID) -> bool:
        """Check if faculty is a single point of failure."""
        return faculty_id in self.n1_vulnerable_faculty

    def get_preference_strength(self, faculty_id: UUID, slot_type: str) -> float:
        """Get preference trail strength (0.5 neutral if no data)."""
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
        """If resident is absent, they cannot be assigned."""
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
        """If resident is absent, they cannot be assigned."""
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
        """Check for assignments during absences."""
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
                    f"max_per_block_{b_i}"
                )

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """Check for multiple primary assignments per block."""
        violations = []
        block_counts = defaultdict(int)

        for assignment in assignments:
            if assignment.role == "primary":
                block_counts[assignment.block_id] += 1

        for block_id, count in block_counts.items():
            if count > self.max_per_block:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="CRITICAL",
                    message=f"Block has {count} primary assignments (max: {self.max_per_block})",
                    block_id=block_id,
                    details={"count": count, "max": self.max_per_block},
                ))

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )


class EightyHourRuleConstraint(HardConstraint):
    """
    ACGME 80-hour rule: Maximum 80 hours per week, averaged over 4 weeks.
    Each half-day block = 6 hours.
    """

    HOURS_PER_BLOCK = 6
    MAX_WEEKLY_HOURS = 80
    ROLLING_WEEKS = 4

    def __init__(self):
        super().__init__(
            name="80HourRule",
            constraint_type=ConstraintType.DUTY_HOURS,
            priority=ConstraintPriority.CRITICAL,
        )
        # Max blocks per 4-week window: (80 * 4) / 6 = 53.33 -> 53
        self.max_blocks_per_window = (self.MAX_WEEKLY_HOURS * self.ROLLING_WEEKS) // self.HOURS_PER_BLOCK

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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
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

    MAX_CONSECUTIVE_DAYS = 6

    def __init__(self):
        super().__init__(
            name="1in7Rule",
            constraint_type=ConstraintType.CONSECUTIVE_DAYS,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """Enforce max consecutive days."""
        from ortools.sat.python import cp_model

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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
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
    ACGME supervision ratios:
    - PGY-1: 1 faculty : 2 residents
    - PGY-2/3: 1 faculty : 4 residents
    """

    PGY1_RATIO = 2  # 1 faculty per 2 PGY-1
    OTHER_RATIO = 4  # 1 faculty per 4 PGY-2/3

    def __init__(self):
        super().__init__(
            name="SupervisionRatio",
            constraint_type=ConstraintType.SUPERVISION,
            priority=ConstraintPriority.CRITICAL,
        )

    def calculate_required_faculty(self, pgy1_count: int, other_count: int) -> int:
        """Calculate required faculty for resident counts."""
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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
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
        x = variables.get("assignments", {})
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
                        if (r_i := context.resident_idx[r.id], b_i, t_i) in template_vars
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
                            f"capacity_{b_i}_{t_i}_{constraint_count}"
                        )
                        constraint_count += 1

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
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
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH",
                    message=f"{template_names.get(template_id, 'Template')}: {count} assigned (max: {limit})",
                    block_id=block_id,
                    details={"count": count, "limit": limit},
                ))

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
            hasattr(r, 'target_clinical_blocks') and r.target_clinical_blocks is not None
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

                if hasattr(resident, 'target_clinical_blocks') and resident.target_clinical_blocks:
                    target = resident.target_clinical_blocks
                    # Create deviation variable (absolute value approximation)
                    deviation = model.NewIntVar(0, len(context.blocks), f"deviation_{r_i}")
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
            hasattr(r, 'target_clinical_blocks') and r.target_clinical_blocks is not None
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

                if resident_vars and hasattr(resident, 'target_clinical_blocks') and resident.target_clinical_blocks:
                    resident_total = pulp.lpSum(resident_vars)
                    target = resident.target_clinical_blocks

                    # Create deviation variables (absolute value via two inequalities)
                    deviation_pos = pulp.LpVariable(f"deviation_pos_{r_i}", lowBound=0, cat="Integer")
                    deviation_neg = pulp.LpVariable(f"deviation_neg_{r_i}", lowBound=0, cat="Integer")

                    # resident_total - target = deviation_pos - deviation_neg
                    model += resident_total - target == deviation_pos - deviation_neg, f"deviation_def_{r_i}"

                    total_deviation.append(deviation_pos + deviation_neg)

            if total_deviation:
                variables["equity_penalty"] = pulp.lpSum(total_deviation)
            else:
                # No targets set, use original logic
                max_assigns = pulp.LpVariable("max_assignments", lowBound=0, cat="Integer")
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
                            f"equity_{r_i}"
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
                    model += (
                        pulp.lpSum(resident_vars) <= max_assigns,
                        f"equity_{r_i}"
                    )

            variables["equity_penalty"] = max_assigns

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
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
            violations.append(ConstraintViolation(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                severity="MEDIUM",
                message=f"Workload imbalance: {min_count} to {max_count} assignments",
                details={"min": min_count, "max": max_count, "spread": spread},
            ))

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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """Calculate coverage rate."""
        workday_blocks = [b for b in context.blocks if not b.is_weekend]
        assigned_blocks = set(a.block_id for a in assignments)

        coverage_rate = len(assigned_blocks) / len(workday_blocks) if workday_blocks else 0

        violations = []
        if coverage_rate < 0.9:
            violations.append(ConstraintViolation(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                severity="MEDIUM",
                message=f"Coverage rate: {coverage_rate * 100:.1f}%",
                details={"coverage_rate": coverage_rate},
            ))

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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """Calculate continuity score (template changes)."""
        # Group by resident, sorted by date
        by_resident = defaultdict(list)
        for a in assignments:
            for b in context.blocks:
                if b.id == a.block_id:
                    by_resident[a.person_id].append((b.date, a.rotation_template_id))
                    break

        total_changes = 0
        for person_id, date_templates in by_resident.items():
            sorted_dt = sorted(date_templates, key=lambda x: x[0])
            for i in range(1, len(sorted_dt)):
                if sorted_dt[i][1] != sorted_dt[i-1][1]:
                    # Different template on consecutive assignment
                    if (sorted_dt[i][0] - sorted_dt[i-1][0]).days <= 1:
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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """Calculate preference satisfaction."""
        total_preference = 0.0
        max_preference = 0.0

        for a in assignments:
            person_prefs = self.preferences.get(a.person_id, {})
            if a.rotation_template_id:
                pref_score = person_prefs.get(a.rotation_template_id, 0.5)  # Neutral default
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
    HIGH_HUB_THRESHOLD = 0.4      # Above this = significant hub
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
        Add hub protection penalty to objective.

        For each faculty with hub_score > threshold, add penalty
        proportional to their assignment count.
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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
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
                severity = "HIGH" if hub_score >= self.CRITICAL_HUB_THRESHOLD else "MEDIUM"
                violations.append(ConstraintViolation(
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
                ))

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

        Soft constraint: penalize total assignments above threshold.
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

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
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
        available_faculty = len([
            f for f in context.faculty
            if any(
                context.availability.get(f.id, {}).get(b.id, {}).get("available", True)
                for b in context.blocks
            )
        ])

        if available_faculty == 0 or workday_blocks == 0:
            return ConstraintResult(satisfied=True, penalty=0.0)

        # Simplified: each faculty can cover 1 block per day on average
        max_capacity = available_faculty * workday_blocks
        utilization = total_assignments / max_capacity if max_capacity > 0 else 0

        # Calculate penalty
        target = context.target_utilization if context.target_utilization else self.target_utilization

        if utilization <= target:
            penalty = 0.0
            buffer_remaining = target - utilization
        else:
            # Quadratic penalty above threshold
            over_threshold = utilization - target
            penalty = (over_threshold ** 2) * self.weight * 100
            buffer_remaining = 0.0

            # Determine severity based on how far over
            if utilization >= 0.95:
                severity = "CRITICAL"
            elif utilization >= 0.90:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            violations.append(ConstraintViolation(
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
            ))

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=penalty,
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
        """Add a constraint to the manager."""
        self.constraints.append(constraint)
        if isinstance(constraint, HardConstraint):
            self._hard_constraints.append(constraint)
        elif isinstance(constraint, SoftConstraint):
            self._soft_constraints.append(constraint)
        return self

    def remove(self, name: str) -> "ConstraintManager":
        """Remove a constraint by name."""
        self.constraints = [c for c in self.constraints if c.name != name]
        self._hard_constraints = [c for c in self._hard_constraints if c.name != name]
        self._soft_constraints = [c for c in self._soft_constraints if c.name != name]
        return self

    def enable(self, name: str) -> "ConstraintManager":
        """Enable a constraint by name."""
        for c in self.constraints:
            if c.name == name:
                c.enabled = True
        return self

    def disable(self, name: str) -> "ConstraintManager":
        """Disable a constraint by name."""
        for c in self.constraints:
            if c.name == name:
                c.enabled = False
        return self

    def get_enabled(self) -> list[Constraint]:
        """Get all enabled constraints."""
        return [c for c in self.constraints if c.enabled]

    def get_hard_constraints(self) -> list[HardConstraint]:
        """Get enabled hard constraints."""
        return [c for c in self._hard_constraints if c.enabled]

    def get_soft_constraints(self) -> list[SoftConstraint]:
        """Get enabled soft constraints."""
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

        # Soft constraints (optimization)
        manager.add(CoverageConstraint(weight=1000.0))
        manager.add(EquityConstraint(weight=10.0))
        manager.add(ContinuityConstraint(weight=5.0))

        # Resilience-aware soft constraints (disabled by default for backward compatibility)
        manager.add(HubProtectionConstraint(weight=15.0))
        manager.add(UtilizationBufferConstraint(weight=20.0))
        # Disabled by default - enabled when resilience data is provided
        manager.disable("HubProtection")
        manager.disable("UtilizationBuffer")

        return manager

    @classmethod
    def create_resilience_aware(cls, target_utilization: float = 0.80) -> "ConstraintManager":
        """
        Create manager with resilience-aware constraints enabled.

        This configuration:
        - Includes all ACGME compliance constraints
        - Enables hub protection to prevent over-assigning critical faculty
        - Enables utilization buffer to maintain 20% capacity reserve
        - Suitable for systems with ResilienceService integration

        Args:
            target_utilization: Maximum utilization before penalties (default 80%)

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

        # Soft constraints (optimization)
        manager.add(CoverageConstraint(weight=1000.0))
        manager.add(EquityConstraint(weight=10.0))
        manager.add(ContinuityConstraint(weight=5.0))

        # Resilience-aware soft constraints (ENABLED)
        manager.add(HubProtectionConstraint(weight=15.0))
        manager.add(UtilizationBufferConstraint(weight=20.0, target_utilization=target_utilization))

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
