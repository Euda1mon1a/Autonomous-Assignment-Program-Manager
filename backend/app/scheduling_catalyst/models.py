"""
Core models for the Scheduling Catalyst library.

This module defines the fundamental data structures that map chemistry
concepts to scheduling:

- ActivationEnergy: Quantified difficulty of a schedule change
- EnergyBarrier: Obstacles preventing schedule changes
- CatalystPerson: Personnel who can lower barriers
- CatalystMechanism: System mechanisms that lower barriers
- TransitionState: Intermediate state during schedule change
- ReactionPathway: Complete path from current to target state
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class BarrierType(str, Enum):
    """
    Classification of energy barriers in scheduling.

    Maps to chemistry barrier types:
    - KINETIC: Time-based barriers (freeze horizons, notice periods)
    - THERMODYNAMIC: Equilibrium barriers (workload balance, preferences)
    - STERIC: Structural barriers (credential requirements, qualifications)
    - ELECTRONIC: Authorization barriers (role permissions, approvals)
    - REGULATORY: Compliance barriers (ACGME rules, legal requirements)
    """

    KINETIC = "kinetic"  # Time-based: freeze horizons, notice periods
    THERMODYNAMIC = "thermodynamic"  # Equilibrium: workload balance
    STERIC = "steric"  # Structural: credentials, qualifications
    ELECTRONIC = "electronic"  # Authorization: role permissions
    REGULATORY = "regulatory"  # Compliance: ACGME, legal


class CatalystType(str, Enum):
    """
    Classification of catalysts in scheduling.

    Maps to chemistry catalyst types:
    - HOMOGENEOUS: Same phase (personnel within the schedule)
    - HETEROGENEOUS: Different phase (external systems, automation)
    - ENZYMATIC: Highly specific (role-based permissions)
    - AUTOCATALYTIC: Self-reinforcing (cross-training cascades)
    """

    HOMOGENEOUS = "homogeneous"  # Personnel catalysts (coordinators)
    HETEROGENEOUS = "heterogeneous"  # System catalysts (auto-matcher)
    ENZYMATIC = "enzymatic"  # Role-specific catalysts (credentials)
    AUTOCATALYTIC = "autocatalytic"  # Self-reinforcing (training cascades)


class ReactionType(str, Enum):
    """
    Types of schedule changes (reactions).
    """

    SWAP = "swap"  # Exchange assignments between personnel
    REASSIGNMENT = "reassignment"  # Move assignment to different person
    CANCELLATION = "cancellation"  # Remove assignment
    CREATION = "creation"  # New assignment
    MODIFICATION = "modification"  # Change assignment parameters


@dataclass
class ActivationEnergy:
    """
    Quantified measure of difficulty for a schedule change.

    In chemistry, activation energy (Ea) is the minimum energy required
    to start a reaction. Here, it represents the cumulative difficulty
    of overcoming all barriers to a schedule change.

    Attributes:
        value: Normalized activation energy (0.0 = trivial, 1.0 = impossible)
        components: Breakdown by barrier type
        catalyzed_value: Energy after catalyst application
        catalyst_effect: Reduction achieved by catalysts
    """

    value: float  # 0.0 to 1.0, normalized
    components: dict[BarrierType, float] = field(default_factory=dict)
    catalyzed_value: Optional[float] = None
    catalyst_effect: float = 0.0

    def __post_init__(self) -> None:
        """Validate energy values are in valid range."""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Activation energy must be 0.0-1.0, got {self.value}")
        if self.catalyzed_value is not None and not 0.0 <= self.catalyzed_value <= 1.0:
            raise ValueError(
                f"Catalyzed energy must be 0.0-1.0, got {self.catalyzed_value}"
            )

    @property
    def is_feasible(self) -> bool:
        """Check if the reaction is feasible (Ea < 1.0)."""
        effective = self.catalyzed_value if self.catalyzed_value is not None else self.value
        return effective < 1.0

    @property
    def effective_energy(self) -> float:
        """Return the effective activation energy after catalysis."""
        return self.catalyzed_value if self.catalyzed_value is not None else self.value

    @property
    def reduction_percentage(self) -> float:
        """Calculate percentage reduction from catalysis."""
        if self.catalyzed_value is None or self.value == 0:
            return 0.0
        return (self.value - self.catalyzed_value) / self.value * 100


@dataclass
class EnergyBarrier:
    """
    An obstacle preventing or hindering a schedule change.

    Represents a specific barrier that contributes to activation energy.

    Attributes:
        barrier_type: Classification of the barrier
        name: Human-readable name
        description: Detailed explanation
        energy_contribution: How much this barrier adds to Ea (0.0-1.0)
        is_absolute: If True, barrier cannot be overcome by catalysts
        source: What created this barrier (e.g., "freeze_horizon", "acgme_rule")
        metadata: Additional context-specific data
    """

    barrier_type: BarrierType
    name: str
    description: str
    energy_contribution: float  # 0.0 to 1.0
    is_absolute: bool = False  # Some barriers cannot be catalyzed
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate energy contribution."""
        if not 0.0 <= self.energy_contribution <= 1.0:
            raise ValueError(
                f"Energy contribution must be 0.0-1.0, got {self.energy_contribution}"
            )

    @property
    def can_be_catalyzed(self) -> bool:
        """Check if this barrier can be lowered by a catalyst."""
        return not self.is_absolute


@dataclass
class CatalystPerson:
    """
    A person who can lower energy barriers for schedule changes.

    In chemistry, a catalyst lowers activation energy without being consumed.
    Personnel catalysts enable schedule changes through their:
    - Authorization level (coordinators can override)
    - Skills/credentials (can cover for others)
    - Network position (hub faculty)

    Attributes:
        person_id: Unique identifier for the person
        name: Person's name
        catalyst_type: Classification of catalyst behavior
        catalyst_score: Overall catalyst effectiveness (0.0-1.0)
        barriers_addressed: Which barrier types this person can reduce
        reduction_factors: How much each barrier type is reduced
        is_available: Whether currently available to act as catalyst
        capacity_remaining: How much catalyst capacity remains (for load)
    """

    person_id: UUID
    name: str
    catalyst_type: CatalystType
    catalyst_score: float  # 0.0 to 1.0, effectiveness
    barriers_addressed: list[BarrierType] = field(default_factory=list)
    reduction_factors: dict[BarrierType, float] = field(default_factory=dict)
    is_available: bool = True
    capacity_remaining: float = 1.0  # 0.0 = fully utilized

    def __post_init__(self) -> None:
        """Validate catalyst score."""
        if not 0.0 <= self.catalyst_score <= 1.0:
            raise ValueError(f"Catalyst score must be 0.0-1.0, got {self.catalyst_score}")

    def can_address_barrier(self, barrier: EnergyBarrier) -> bool:
        """Check if this catalyst can address a specific barrier."""
        if not barrier.can_be_catalyzed:
            return False
        return barrier.barrier_type in self.barriers_addressed

    def reduction_for_barrier(self, barrier: EnergyBarrier) -> float:
        """Calculate energy reduction for a specific barrier."""
        if not self.can_address_barrier(barrier):
            return 0.0
        base_reduction = self.reduction_factors.get(barrier.barrier_type, 0.5)
        # Scale by availability and remaining capacity
        return base_reduction * self.capacity_remaining if self.is_available else 0.0


@dataclass
class CatalystMechanism:
    """
    A system mechanism that can lower energy barriers.

    Unlike personnel catalysts, these are automated or structural:
    - Auto-matching algorithms
    - Override reason codes
    - Defense level escalation
    - Backup pool activation

    Attributes:
        mechanism_id: Unique identifier
        name: Mechanism name
        catalyst_type: Classification
        barriers_addressed: Which barrier types this addresses
        reduction_factors: How much each barrier type is reduced
        requires_trigger: What activates this mechanism
        is_active: Whether mechanism is currently operational
    """

    mechanism_id: str
    name: str
    catalyst_type: CatalystType
    barriers_addressed: list[BarrierType] = field(default_factory=list)
    reduction_factors: dict[BarrierType, float] = field(default_factory=dict)
    requires_trigger: Optional[str] = None
    is_active: bool = True

    def can_address_barrier(self, barrier: EnergyBarrier) -> bool:
        """Check if this mechanism can address a specific barrier."""
        if not barrier.can_be_catalyzed:
            return False
        return barrier.barrier_type in self.barriers_addressed


@dataclass
class TransitionState:
    """
    An intermediate configuration during a schedule change.

    In chemistry, the transition state is the highest-energy point along
    the reaction pathway. Here, it represents a temporary schedule
    configuration that must be achieved before the final state.

    Attributes:
        state_id: Unique identifier
        description: What this state represents
        assignments: Assignment configuration at this state
        energy_level: Energy at this state (relative to initial)
        is_stable: Whether this is a metastable intermediate
        duration: How long this state must persist
    """

    state_id: str
    description: str
    assignments: dict[str, Any]  # Assignment configuration
    energy_level: float  # Relative to initial state
    is_stable: bool = False  # Metastable intermediates
    duration: Optional[int] = None  # Minutes this state persists

    @property
    def is_transition(self) -> bool:
        """Check if this is a true transition state (unstable)."""
        return not self.is_stable


@dataclass
class ReactionPathway:
    """
    A complete path from current schedule state to target state.

    Represents a specific route through the energy landscape, including
    all barriers, catalysts, and transition states.

    Attributes:
        pathway_id: Unique identifier
        initial_state: Starting schedule configuration
        target_state: Desired schedule configuration
        transition_states: Intermediate states along the path
        barriers: All barriers encountered
        catalysts_applied: Catalysts used to lower barriers
        total_activation_energy: Sum of all barrier contributions
        effective_activation_energy: After catalyst reduction
        estimated_duration: Time to complete the transition
    """

    pathway_id: str
    initial_state: dict[str, Any]
    target_state: dict[str, Any]
    transition_states: list[TransitionState] = field(default_factory=list)
    barriers: list[EnergyBarrier] = field(default_factory=list)
    catalysts_applied: list[CatalystPerson | CatalystMechanism] = field(
        default_factory=list
    )
    total_activation_energy: float = 0.0
    effective_activation_energy: float = 0.0
    estimated_duration: Optional[int] = None  # Minutes

    @property
    def is_feasible(self) -> bool:
        """Check if this pathway is feasible."""
        return self.effective_activation_energy < 1.0

    @property
    def catalyst_efficiency(self) -> float:
        """Calculate overall catalyst efficiency."""
        if self.total_activation_energy == 0:
            return 0.0
        reduction = self.total_activation_energy - self.effective_activation_energy
        return reduction / self.total_activation_energy

    def add_catalyst(
        self, catalyst: CatalystPerson | CatalystMechanism
    ) -> None:
        """Add a catalyst and recalculate effective energy."""
        self.catalysts_applied.append(catalyst)
        self._recalculate_effective_energy()

    def _recalculate_effective_energy(self) -> None:
        """Recalculate effective activation energy with all catalysts."""
        remaining_barriers: dict[BarrierType, float] = {}

        # Sum barriers by type
        for barrier in self.barriers:
            bt = barrier.barrier_type
            if bt not in remaining_barriers:
                remaining_barriers[bt] = 0.0
            remaining_barriers[bt] += barrier.energy_contribution

        # Apply catalyst reductions
        for catalyst in self.catalysts_applied:
            for barrier_type, contribution in list(remaining_barriers.items()):
                if isinstance(catalyst, CatalystPerson):
                    reduction = catalyst.reduction_factors.get(barrier_type, 0.0)
                else:
                    reduction = catalyst.reduction_factors.get(barrier_type, 0.0)
                remaining_barriers[barrier_type] = contribution * (1 - reduction)

        self.effective_activation_energy = min(1.0, sum(remaining_barriers.values()))


@dataclass
class ScheduleReaction:
    """
    A complete schedule change reaction with kinetics.

    Combines the reaction type, pathway, and timing information.

    Attributes:
        reaction_id: Unique identifier
        reaction_type: Type of schedule change
        reactants: Initial assignments involved
        products: Final assignments produced
        pathway: The reaction pathway taken
        rate_constant: How fast this reaction proceeds (arbitrary units)
        half_life: Time for 50% completion (if applicable)
        is_reversible: Whether this reaction can be reversed
        reversal_window: Time window for reversal (minutes)
    """

    reaction_id: str
    reaction_type: ReactionType
    reactants: list[dict[str, Any]]  # Initial assignments
    products: list[dict[str, Any]]  # Final assignments
    pathway: ReactionPathway
    rate_constant: float = 1.0
    half_life: Optional[int] = None
    is_reversible: bool = True
    reversal_window: int = 1440  # 24 hours in minutes

    @property
    def gibbs_free_energy(self) -> float:
        """
        Calculate the Gibbs free energy change (spontaneity).

        Negative = favorable (products more stable)
        Positive = unfavorable (requires energy input)
        """
        # Simplified: based on workload balance improvement
        return self.pathway.effective_activation_energy - 0.5

    @property
    def is_spontaneous(self) -> bool:
        """Check if reaction is thermodynamically favorable."""
        return self.gibbs_free_energy < 0
