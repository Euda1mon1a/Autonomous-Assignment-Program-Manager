"""
Base Constraint Classes and Infrastructure.

This module provides the foundational classes for the constraint system:
- Enums: ConstraintPriority, ConstraintType
- Dataclasses: ConstraintViolation, ConstraintResult, SchedulingContext
- Base Classes: Constraint, HardConstraint, SoftConstraint
- Manager: ConstraintManager for composing and managing constraints
"""
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

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
                all_satisfied = False

        return ConstraintResult(
            satisfied=all_satisfied,
            violations=all_violations,
            penalty=total_penalty,
        )

    @classmethod
    def create_default(cls) -> "ConstraintManager":
        """
        Create manager with default ACGME constraints.

        NOTE: This method imports constraint classes locally to avoid circular imports.
        The actual constraint instances are imported from their respective modules
        when this method is called.
        """
        # Import constraint classes here to avoid circular imports
        from app.scheduling.constraints.time_constraints import (
            AvailabilityConstraint,
            WednesdayAMInternOnlyConstraint,
        )
        from app.scheduling.constraints.capacity_constraints import (
            OnePersonPerBlockConstraint,
            ClinicCapacityConstraint,
            MaxPhysiciansInClinicConstraint,
            CoverageConstraint,
        )
        from app.scheduling.constraints.acgme_constraints import (
            EightyHourRuleConstraint,
            OneInSevenRuleConstraint,
            SupervisionRatioConstraint,
        )
        from app.scheduling.constraints.custom_constraints import (
            EquityConstraint,
            ContinuityConstraint,
            HubProtectionConstraint,
            UtilizationBufferConstraint,
            ZoneBoundaryConstraint,
            PreferenceTrailConstraint,
            N1VulnerabilityConstraint,
        )

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
        # Import constraint classes here to avoid circular imports
        from app.scheduling.constraints.time_constraints import (
            AvailabilityConstraint,
            WednesdayAMInternOnlyConstraint,
        )
        from app.scheduling.constraints.capacity_constraints import (
            OnePersonPerBlockConstraint,
            ClinicCapacityConstraint,
            MaxPhysiciansInClinicConstraint,
            CoverageConstraint,
        )
        from app.scheduling.constraints.acgme_constraints import (
            EightyHourRuleConstraint,
            OneInSevenRuleConstraint,
            SupervisionRatioConstraint,
        )
        from app.scheduling.constraints.custom_constraints import (
            EquityConstraint,
            ContinuityConstraint,
            HubProtectionConstraint,
            UtilizationBufferConstraint,
            ZoneBoundaryConstraint,
            PreferenceTrailConstraint,
            N1VulnerabilityConstraint,
        )

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
        manager.add(UtilizationBufferConstraint(weight=20.0, target_utilization=target_utilization))

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
        # Import constraint classes here to avoid circular imports
        from app.scheduling.constraints.time_constraints import AvailabilityConstraint
        from app.scheduling.constraints.capacity_constraints import (
            OnePersonPerBlockConstraint,
            CoverageConstraint,
        )

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
