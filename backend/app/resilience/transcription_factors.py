"""
Transcription Factor Scheduler (TFS) - Bio-Inspired Constraint Regulation.

This module implements gene regulatory network concepts as a novel approach to
scheduling constraint management. Unlike traditional constraint systems where
all constraints are evaluated independently, TFS models constraints as "genes"
that are regulated by "transcription factors" which can activate or repress them
based on context.

BIOLOGICAL CONCEPTS APPLIED:

1. Central Dogma (DNA → RNA → Protein):
   - DNA: Constraint definitions (the "genome" of the scheduler)
   - Transcription: Converting rules into active constraint instances
   - Protein: The actual assignment decisions affecting the system

2. Transcription Factors (TFs):
   - Regulatory proteins that bind to specific DNA sequences
   - Can ACTIVATE (increase constraint weight) or REPRESS (decrease/disable)
   - Have binding affinity (strength of influence)
   - Work combinatorially (multiple TFs needed for specific outcomes)

3. Promoter Architecture:
   - Different "genes" (constraints) have different regulatory requirements
   - Some require single TF (simple activation)
   - Some require multiple TFs (AND logic)
   - Some activate with any of several TFs (OR logic)

4. Gene Regulatory Networks (GRNs):
   - TFs form networks with feedback loops
   - Feed-forward loops amplify signals
   - Negative feedback stabilizes
   - Cascade effects (one TF activates another)

5. Chromatin State / Epigenetics:
   - System state changes which constraints are "accessible"
   - During normal operation: all constraints active
   - During crisis: some constraints "silenced" for flexibility

6. Master Regulators:
   - Some TFs control entire gene programs
   - Patient safety = master regulator (always active)
   - Creates hierarchical control

7. Signal Transduction:
   - External events trigger TF activation cascades
   - Deployment → Military TF activates → Emergency constraints enabled

This provides:
- Context-sensitive constraint weighting
- Emergent behavior from simple rules
- Graceful degradation under stress
- Self-organizing regulatory responses
"""

import logging
import math
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND TYPES
# =============================================================================


class TFType(str, Enum):
    """Types of transcription factors."""

    ACTIVATOR = "activator"  # Increases constraint weight/priority
    REPRESSOR = "repressor"  # Decreases constraint weight or disables
    DUAL = "dual"  # Can act as either based on context
    PIONEER = "pioneer"  # Can open "closed chromatin" (enable disabled constraints)
    MASTER = "master"  # Controls entire regulatory programs


class BindingLogic(str, Enum):
    """Logic for combining multiple TF bindings."""

    AND = "and"  # All TFs must bind
    OR = "or"  # Any TF can activate
    MAJORITY = "majority"  # >50% of TFs must bind
    THRESHOLD = "threshold"  # Sum of binding strengths must exceed threshold
    SEQUENTIAL = "sequential"  # TFs must bind in order


class ChromatinState(str, Enum):
    """Accessibility state of a constraint (epigenetic metaphor)."""

    OPEN = "open"  # Fully accessible, can be regulated
    POISED = "poised"  # Partially accessible, quick to activate
    CLOSED = "closed"  # Inaccessible, requires pioneer TF
    SILENCED = "silenced"  # Permanently off (e.g., during crisis)


class SignalStrength(str, Enum):
    """Strength of an incoming signal."""

    WEAK = "weak"  # 0.0 - 0.3
    MODERATE = "moderate"  # 0.3 - 0.6
    STRONG = "strong"  # 0.6 - 0.8
    MAXIMAL = "maximal"  # 0.8 - 1.0


class LoopType(str, Enum):
    """Types of regulatory loops."""

    POSITIVE_FEEDBACK = "positive_feedback"  # Amplifies signal
    NEGATIVE_FEEDBACK = "negative_feedback"  # Stabilizes
    FEED_FORWARD_COHERENT = "feed_forward_coherent"  # Amplifies with delay
    FEED_FORWARD_INCOHERENT = "feed_forward_incoherent"  # Pulse generator
    BISTABLE_SWITCH = "bistable_switch"  # Two stable states


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================


@dataclass
class BindingSite:
    """
    A regulatory region where transcription factors can bind.

    Analogous to promoter/enhancer regions in DNA. Each constraint
    has binding sites that determine which TFs can regulate it.
    """

    id: UUID
    name: str
    tf_types_accepted: list[TFType]  # Which TF types can bind here
    binding_affinity: float = 1.0  # Base affinity (0.0 - 1.0)
    is_enhancer: bool = False  # Enhancers boost effect
    is_silencer: bool = False  # Silencers reduce effect
    distance_from_core: float = 0.0  # Distant sites have weaker effect

    def get_effective_affinity(self, tf_affinity: float) -> float:
        """Calculate effective binding strength."""
        distance_factor = math.exp(-0.1 * self.distance_from_core)
        base = self.binding_affinity * tf_affinity * distance_factor

        if self.is_enhancer:
            return min(1.0, base * 1.5)
        elif self.is_silencer:
            return base * 0.5
        return base


@dataclass
class TranscriptionFactor:
    """
    A regulatory factor that controls constraint expression.

    TFs bind to specific binding sites on constraints and either
    activate (increase weight) or repress (decrease/disable) them.
    They can work alone or combinatorially with other TFs.
    """

    id: UUID
    name: str
    description: str
    tf_type: TFType

    # Binding properties
    binding_affinity: float = 0.7  # How strongly this TF binds (0.0 - 1.0)
    specificity: float = 0.8  # How specific to target sites (0.0 - 1.0)

    # Regulatory effect
    activation_strength: float = 1.0  # For activators: multiplier on weight
    repression_strength: float = 0.5  # For repressors: multiplier reduction

    # Expression level (how much of this TF is "present")
    expression_level: float = 0.0  # 0.0 = absent, 1.0 = maximally expressed
    basal_expression: float = 0.1  # Minimum expression level
    max_expression: float = 1.0

    # Dynamics
    half_life_hours: float = 24.0  # How quickly TF degrades
    induction_delay_hours: float = 0.5  # Time to respond to signal
    last_induced: datetime = field(default_factory=datetime.now)

    # Targets this TF regulates
    target_constraint_ids: list[UUID] = field(default_factory=list)

    # Other TFs this TF regulates (for cascade effects)
    target_tf_ids: list[UUID] = field(default_factory=list)

    # Conditions for activation
    activation_conditions: dict[str, Any] = field(default_factory=dict)

    def induce(self, signal_strength: float = 1.0):
        """
        Induce TF expression in response to a signal.

        Args:
            signal_strength: Strength of inducing signal (0.0 - 1.0)
        """
        # Sigmoid response to signal
        response = 1.0 / (1.0 + math.exp(-5 * (signal_strength - 0.5)))
        new_level = (
            self.basal_expression
            + (self.max_expression - self.basal_expression) * response
        )

        old_level = self.expression_level
        self.expression_level = min(self.max_expression, new_level)
        self.last_induced = datetime.now()

        logger.debug(
            f"TF {self.name} induced: {old_level:.2f} -> {self.expression_level:.2f}"
        )

    def decay(self, hours_elapsed: float):
        """
        Apply natural decay to TF expression.

        Args:
            hours_elapsed: Hours since last decay calculation
        """
        if hours_elapsed <= 0:
            return

        # Exponential decay toward basal level
        decay_rate = math.log(2) / self.half_life_hours
        decay_factor = math.exp(-decay_rate * hours_elapsed)

        # Decay toward basal, not zero
        above_basal = self.expression_level - self.basal_expression
        self.expression_level = self.basal_expression + (above_basal * decay_factor)

    def get_effective_strength(self) -> float:
        """Get current regulatory strength based on expression level."""
        if self.tf_type == TFType.ACTIVATOR:
            return self.activation_strength * self.expression_level
        elif self.tf_type == TFType.REPRESSOR:
            return self.repression_strength * self.expression_level
        else:  # DUAL, PIONEER, MASTER
            return self.expression_level

    @property
    def is_active(self) -> bool:
        """Whether this TF has meaningful expression."""
        return self.expression_level > 0.2

    @property
    def signal_strength_category(self) -> SignalStrength:
        """Categorical expression level."""
        if self.expression_level < 0.3:
            return SignalStrength.WEAK
        elif self.expression_level < 0.6:
            return SignalStrength.MODERATE
        elif self.expression_level < 0.8:
            return SignalStrength.STRONG
        else:
            return SignalStrength.MAXIMAL


@dataclass
class PromoterArchitecture:
    """
    Defines the regulatory requirements for a constraint.

    Each constraint has a "promoter" that specifies:
    - Which TFs can regulate it
    - What logic combines multiple TF bindings
    - Threshold for activation
    """

    id: UUID
    constraint_id: UUID
    constraint_name: str

    # Binding sites where TFs can attach
    binding_sites: list[BindingSite] = field(default_factory=list)

    # Required TFs (by ID)
    required_activators: list[UUID] = field(default_factory=list)
    optional_activators: list[UUID] = field(default_factory=list)
    repressors: list[UUID] = field(default_factory=list)

    # Binding logic
    activator_logic: BindingLogic = BindingLogic.OR
    activation_threshold: float = 0.5  # For THRESHOLD logic

    # Chromatin state
    chromatin_state: ChromatinState = ChromatinState.OPEN

    # Output properties
    base_weight: float = 1.0  # Default constraint weight
    min_weight: float = 0.0  # Can't go below this
    max_weight: float = 10.0  # Can't exceed this

    def calculate_activation(
        self,
        bound_tfs: dict[UUID, float],  # TF ID -> binding strength
    ) -> tuple[float, str]:
        """
        Calculate constraint activation level based on bound TFs.

        Args:
            bound_tfs: Dict of TF ID to effective binding strength

        Returns:
            Tuple of (activation_level, explanation)
        """
        # Check chromatin state
        if self.chromatin_state == ChromatinState.SILENCED:
            return 0.0, "Silenced - constraint disabled"
        elif self.chromatin_state == ChromatinState.CLOSED:
            # Need pioneer TF to open
            has_pioneer = False
            for tf_id, strength in bound_tfs.items():
                # Pioneer check would go here
                pass
            if not has_pioneer:
                return 0.0, "Closed chromatin - requires pioneer TF"

        # Calculate activator contribution
        activator_signals = []
        for tf_id in self.required_activators + self.optional_activators:
            if tf_id in bound_tfs:
                activator_signals.append(bound_tfs[tf_id])

        if not activator_signals:
            activator_contribution = 0.0
        elif self.activator_logic == BindingLogic.AND:
            # All required must be present
            if len([s for s in activator_signals if s > 0.2]) < len(
                self.required_activators
            ):
                return 0.0, "AND logic: missing required activators"
            activator_contribution = min(activator_signals)
        elif self.activator_logic == BindingLogic.OR:
            activator_contribution = max(activator_signals)
        elif self.activator_logic == BindingLogic.MAJORITY:
            active_count = sum(1 for s in activator_signals if s > 0.3)
            total = len(self.required_activators) + len(self.optional_activators)
            if active_count > total / 2:
                activator_contribution = sum(activator_signals) / len(activator_signals)
            else:
                return 0.0, "MAJORITY logic: insufficient activators"
        elif self.activator_logic == BindingLogic.THRESHOLD:
            total_strength = sum(activator_signals)
            if total_strength >= self.activation_threshold:
                activator_contribution = total_strength / len(activator_signals)
            else:
                return (
                    0.0,
                    f"THRESHOLD logic: {total_strength:.2f} < {self.activation_threshold:.2f}",
                )
        else:
            activator_contribution = sum(activator_signals) / max(
                1, len(activator_signals)
            )

        # Calculate repressor contribution
        repressor_signals = []
        for tf_id in self.repressors:
            if tf_id in bound_tfs:
                repressor_signals.append(bound_tfs[tf_id])

        repressor_contribution = max(repressor_signals) if repressor_signals else 0.0

        # Final activation: activators - repressors
        activation = max(0.0, activator_contribution - repressor_contribution)

        explanation = (
            f"Activation={activation:.2f} "
            f"(activators={activator_contribution:.2f}, repressors={repressor_contribution:.2f})"
        )

        return activation, explanation

    def get_effective_weight(
        self,
        activation_level: float,
    ) -> float:
        """Convert activation level to constraint weight."""
        # Sigmoid mapping for smooth transition
        weight = self.base_weight * activation_level
        return max(self.min_weight, min(self.max_weight, weight))


@dataclass
class RegulatoryEdge:
    """
    An edge in the gene regulatory network.

    Represents one TF regulating one target (constraint or another TF).
    """

    id: UUID
    source_tf_id: UUID
    target_id: UUID  # Either constraint ID or TF ID
    target_type: str  # "constraint" or "tf"

    edge_type: TFType  # ACTIVATOR or REPRESSOR
    strength: float = 1.0  # Edge weight
    delay_hours: float = 0.0  # Time delay for effect

    # Conditions for this edge to be active
    conditions: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class RegulatoryLoop:
    """
    A detected regulatory loop (motif) in the network.
    """

    id: UUID
    loop_type: LoopType
    description: str

    # TFs and constraints involved
    tf_ids: list[UUID]
    constraint_ids: list[UUID]
    edges: list[RegulatoryEdge]

    # Analysis
    detected_at: datetime = field(default_factory=datetime.now)
    stability: str = "unknown"  # "stable", "oscillating", "bistable"
    period_hours: float | None = None  # For oscillations


@dataclass
class SignalEvent:
    """
    An external event that triggers TF induction.
    """

    id: UUID
    event_type: str
    description: str
    timestamp: datetime

    # Which TFs this signal induces
    target_tf_ids: list[UUID]
    signal_strength: float = 1.0

    # Propagation
    propagated: bool = False
    cascade_depth: int = 0


@dataclass
class GRNState:
    """
    Snapshot of the gene regulatory network state.
    """

    timestamp: datetime

    # TF expression levels
    tf_expressions: dict[UUID, float]

    # Constraint weights after regulation
    constraint_weights: dict[UUID, float]

    # Active loops
    active_loops: list[UUID]

    # Overall metrics
    total_activation: float
    total_repression: float
    network_entropy: float  # Measure of regulatory diversity


# =============================================================================
# MAIN SERVICE CLASS
# =============================================================================


class TranscriptionFactorScheduler:
    """
    Gene Regulatory Network-based constraint scheduler.

    This service manages transcription factors and their regulatory
    relationships to constraints. It provides context-sensitive
    constraint weighting that responds to system conditions.

    Usage:
        tfs = TranscriptionFactorScheduler()

        # Define TFs
        military_tf = tfs.create_tf("MilitaryEmergency", TFType.ACTIVATOR, ...)

        # Link to constraints
        tfs.link_tf_to_constraint(military_tf.id, emergency_constraint_id)

        # When event occurs, induce TF
        tfs.process_signal(SignalEvent(event_type="deployment", ...))

        # Get adjusted weights for scheduling
        weights = tfs.get_constraint_weights()
    """

    def __init__(self):
        self.transcription_factors: dict[UUID, TranscriptionFactor] = {}
        self.promoters: dict[UUID, PromoterArchitecture] = (
            {}
        )  # constraint_id -> promoter
        self.edges: dict[UUID, RegulatoryEdge] = {}
        self.detected_loops: list[RegulatoryLoop] = []

        # Signal handlers
        self.signal_handlers: dict[str, Callable[[SignalEvent], list[UUID]]] = {}

        # History for analysis
        self.state_history: list[GRNState] = []
        self.signal_history: list[SignalEvent] = []

        # Indexes
        self._tf_by_name: dict[str, UUID] = {}
        self._edges_by_source: dict[UUID, list[UUID]] = defaultdict(list)
        self._edges_by_target: dict[UUID, list[UUID]] = defaultdict(list)

        # Initialize default TFs
        self._initialize_default_tfs()

    def _initialize_default_tfs(self):
        """Create default transcription factors for common scenarios."""

        # Master Regulator: Patient Safety (always active)
        self.create_tf(
            name="PatientSafety_MR",
            tf_type=TFType.MASTER,
            description="Master regulator ensuring patient safety constraints always active",
            binding_affinity=1.0,
            basal_expression=1.0,  # Always expressed
            activation_conditions={"always": True},
        )

        # Master Regulator: ACGME Compliance
        self.create_tf(
            name="ACGMECompliance_MR",
            tf_type=TFType.MASTER,
            description="Master regulator for ACGME compliance requirements",
            binding_affinity=1.0,
            basal_expression=0.9,
            activation_conditions={"always": True},
        )

        # Activator: Military Emergency
        self.create_tf(
            name="MilitaryEmergency_TF",
            tf_type=TFType.ACTIVATOR,
            description="Activates emergency coverage constraints during deployments",
            binding_affinity=0.9,
            basal_expression=0.0,  # Only active when induced
            activation_strength=2.0,  # Strong activation
            half_life_hours=168,  # 1 week
            activation_conditions={
                "event_types": ["deployment", "mobilization", "tdy"]
            },
        )

        # Activator: Holiday Coverage
        self.create_tf(
            name="HolidayCoverage_TF",
            tf_type=TFType.ACTIVATOR,
            description="Activates holiday coverage constraints",
            binding_affinity=0.8,
            basal_expression=0.0,
            activation_strength=1.5,
            half_life_hours=48,
            activation_conditions={"event_types": ["holiday", "federal_holiday"]},
        )

        # Repressor: Crisis Mode
        self.create_tf(
            name="CrisisMode_TF",
            tf_type=TFType.REPRESSOR,
            description="Represses non-essential constraints during crisis",
            binding_affinity=0.95,
            basal_expression=0.0,
            repression_strength=0.8,
            half_life_hours=72,
            activation_conditions={
                "event_types": ["crisis", "pandemic", "mass_casualty"]
            },
        )

        # Repressor: Low Staffing
        self.create_tf(
            name="LowStaffing_TF",
            tf_type=TFType.REPRESSOR,
            description="Relaxes soft constraints when staffing is low",
            binding_affinity=0.7,
            basal_expression=0.0,
            repression_strength=0.5,
            half_life_hours=24,
            activation_conditions={"utilization_above": 0.85},
        )

        # Activator: High Workload Protection
        self.create_tf(
            name="WorkloadProtection_TF",
            tf_type=TFType.ACTIVATOR,
            description="Activates workload balancing constraints when imbalance detected",
            binding_affinity=0.8,
            basal_expression=0.3,
            activation_strength=1.5,
            half_life_hours=48,
            activation_conditions={"workload_variance_above": 0.2},
        )

        # Pioneer: Recovery Mode
        self.create_tf(
            name="RecoveryMode_TF",
            tf_type=TFType.PIONEER,
            description="Can re-enable silenced constraints after crisis",
            binding_affinity=0.9,
            basal_expression=0.0,
            half_life_hours=72,
            activation_conditions={"event_types": ["crisis_end", "recovery"]},
        )

        # Dual: Flexibility TF
        self.create_tf(
            name="Flexibility_TF",
            tf_type=TFType.DUAL,
            description="Can activate OR repress based on context",
            binding_affinity=0.6,
            basal_expression=0.5,
            half_life_hours=24,
            activation_conditions={"adaptive": True},
        )

        logger.info(
            f"Initialized {len(self.transcription_factors)} default transcription factors"
        )

    # -------------------------------------------------------------------------
    # TF Management
    # -------------------------------------------------------------------------

    def create_tf(
        self,
        name: str,
        tf_type: TFType,
        description: str = "",
        binding_affinity: float = 0.7,
        basal_expression: float = 0.1,
        max_expression: float = 1.0,
        activation_strength: float = 1.0,
        repression_strength: float = 0.5,
        half_life_hours: float = 24.0,
        activation_conditions: dict = None,
    ) -> TranscriptionFactor:
        """
        Create a new transcription factor.

        Args:
            name: Unique name for the TF
            tf_type: Type (activator, repressor, etc.)
            description: Human-readable description
            binding_affinity: How strongly it binds (0-1)
            basal_expression: Minimum expression level
            max_expression: Maximum expression level
            activation_strength: For activators, multiplier effect
            repression_strength: For repressors, reduction effect
            half_life_hours: Decay rate
            activation_conditions: Conditions for automatic activation

        Returns:
            Created TranscriptionFactor
        """
        tf = TranscriptionFactor(
            id=uuid4(),
            name=name,
            description=description,
            tf_type=tf_type,
            binding_affinity=binding_affinity,
            basal_expression=basal_expression,
            max_expression=max_expression,
            expression_level=basal_expression,
            activation_strength=activation_strength,
            repression_strength=repression_strength,
            half_life_hours=half_life_hours,
            activation_conditions=activation_conditions or {},
        )

        self.transcription_factors[tf.id] = tf
        self._tf_by_name[name] = tf.id

        logger.info(f"Created TF: {name} ({tf_type.value})")
        return tf

    def get_tf_by_name(self, name: str) -> TranscriptionFactor | None:
        """Get a TF by its name."""
        tf_id = self._tf_by_name.get(name)
        return self.transcription_factors.get(tf_id) if tf_id else None

    def induce_tf(self, tf_id: UUID, signal_strength: float = 1.0):
        """
        Induce a transcription factor.

        Args:
            tf_id: ID of TF to induce
            signal_strength: Strength of inducing signal
        """
        tf = self.transcription_factors.get(tf_id)
        if tf:
            tf.induce(signal_strength)

            # Propagate to downstream TFs (cascade)
            self._propagate_cascade(tf_id, signal_strength * 0.8)

    def _propagate_cascade(
        self, source_tf_id: UUID, signal_strength: float, depth: int = 0
    ):
        """Propagate TF induction through cascade."""
        if depth > 5 or signal_strength < 0.1:  # Prevent infinite loops
            return

        source_tf = self.transcription_factors.get(source_tf_id)
        if not source_tf:
            return

        for target_tf_id in source_tf.target_tf_ids:
            target_tf = self.transcription_factors.get(target_tf_id)
            if target_tf:
                target_tf.induce(signal_strength)
                self._propagate_cascade(target_tf_id, signal_strength * 0.7, depth + 1)

    def decay_all_tfs(self, hours_elapsed: float = 1.0):
        """Apply decay to all TFs."""
        for tf in self.transcription_factors.values():
            tf.decay(hours_elapsed)

    # -------------------------------------------------------------------------
    # Promoter/Constraint Linking
    # -------------------------------------------------------------------------

    def create_promoter(
        self,
        constraint_id: UUID,
        constraint_name: str,
        base_weight: float = 1.0,
        activator_logic: BindingLogic = BindingLogic.OR,
        chromatin_state: ChromatinState = ChromatinState.OPEN,
    ) -> PromoterArchitecture:
        """
        Create a promoter architecture for a constraint.

        Args:
            constraint_id: ID of the constraint being regulated
            constraint_name: Name for logging
            base_weight: Default constraint weight
            activator_logic: How multiple activators combine
            chromatin_state: Initial accessibility

        Returns:
            Created PromoterArchitecture
        """
        promoter = PromoterArchitecture(
            id=uuid4(),
            constraint_id=constraint_id,
            constraint_name=constraint_name,
            base_weight=base_weight,
            activator_logic=activator_logic,
            chromatin_state=chromatin_state,
        )

        self.promoters[constraint_id] = promoter

        logger.debug(f"Created promoter for constraint: {constraint_name}")
        return promoter

    def link_tf_to_constraint(
        self,
        tf_id: UUID,
        constraint_id: UUID,
        as_activator: bool = True,
        required: bool = False,
        edge_strength: float = 1.0,
    ):
        """
        Link a TF to regulate a constraint.

        Args:
            tf_id: ID of the transcription factor
            constraint_id: ID of the constraint
            as_activator: True for activation, False for repression
            required: Whether this TF is required (for AND logic)
            edge_strength: Strength of regulatory relationship
        """
        tf = self.transcription_factors.get(tf_id)
        if not tf:
            logger.warning(f"TF {tf_id} not found")
            return

        # Ensure promoter exists
        if constraint_id not in self.promoters:
            self.create_promoter(constraint_id, f"constraint_{constraint_id}")

        promoter = self.promoters[constraint_id]

        # Add TF to promoter
        if as_activator:
            if required:
                if tf_id not in promoter.required_activators:
                    promoter.required_activators.append(tf_id)
            else:
                if tf_id not in promoter.optional_activators:
                    promoter.optional_activators.append(tf_id)
        else:
            if tf_id not in promoter.repressors:
                promoter.repressors.append(tf_id)

        # Add to TF's targets
        if constraint_id not in tf.target_constraint_ids:
            tf.target_constraint_ids.append(constraint_id)

        # Create regulatory edge
        edge = RegulatoryEdge(
            id=uuid4(),
            source_tf_id=tf_id,
            target_id=constraint_id,
            target_type="constraint",
            edge_type=TFType.ACTIVATOR if as_activator else TFType.REPRESSOR,
            strength=edge_strength,
        )

        self.edges[edge.id] = edge
        self._edges_by_source[tf_id].append(edge.id)
        self._edges_by_target[constraint_id].append(edge.id)

        logger.debug(
            f"Linked TF {tf.name} -> constraint {constraint_id} "
            f"({'activator' if as_activator else 'repressor'})"
        )

    def link_tf_to_tf(
        self,
        source_tf_id: UUID,
        target_tf_id: UUID,
        as_activator: bool = True,
        edge_strength: float = 1.0,
    ):
        """
        Link one TF to regulate another (for cascade effects).

        Args:
            source_tf_id: ID of regulating TF
            target_tf_id: ID of regulated TF
            as_activator: True for activation, False for repression
            edge_strength: Strength of regulatory relationship
        """
        source_tf = self.transcription_factors.get(source_tf_id)
        target_tf = self.transcription_factors.get(target_tf_id)

        if not source_tf or not target_tf:
            logger.warning("One or both TFs not found")
            return

        # Add to source's targets
        if target_tf_id not in source_tf.target_tf_ids:
            source_tf.target_tf_ids.append(target_tf_id)

        # Create edge
        edge = RegulatoryEdge(
            id=uuid4(),
            source_tf_id=source_tf_id,
            target_id=target_tf_id,
            target_type="tf",
            edge_type=TFType.ACTIVATOR if as_activator else TFType.REPRESSOR,
            strength=edge_strength,
        )

        self.edges[edge.id] = edge
        self._edges_by_source[source_tf_id].append(edge.id)
        self._edges_by_target[target_tf_id].append(edge.id)

        logger.debug(
            f"Linked TF {source_tf.name} -> TF {target_tf.name} "
            f"({'activator' if as_activator else 'repressor'})"
        )

    # -------------------------------------------------------------------------
    # Signal Processing
    # -------------------------------------------------------------------------

    def register_signal_handler(
        self,
        event_type: str,
        handler: Callable[[SignalEvent], list[UUID]],
    ):
        """
        Register a handler for a signal type.

        Handler receives the signal and returns list of TF IDs to induce.
        """
        self.signal_handlers[event_type] = handler

    def process_signal(self, signal: SignalEvent):
        """
        Process an incoming signal event.

        This is the main entry point for external events triggering
        regulatory responses.

        Args:
            signal: The signal event to process
        """
        logger.info(
            f"Processing signal: {signal.event_type} (strength={signal.signal_strength})"
        )

        self.signal_history.append(signal)

        # Check registered handlers
        handler = self.signal_handlers.get(signal.event_type)
        if handler:
            tf_ids = handler(signal)
            signal.target_tf_ids.extend(tf_ids)

        # Auto-detect TFs that respond to this event type
        for tf in self.transcription_factors.values():
            conditions = tf.activation_conditions

            # Check event type match
            if "event_types" in conditions:
                if signal.event_type in conditions["event_types"]:
                    if tf.id not in signal.target_tf_ids:
                        signal.target_tf_ids.append(tf.id)

        # Induce all target TFs
        for tf_id in signal.target_tf_ids:
            self.induce_tf(tf_id, signal.signal_strength)

        signal.propagated = True

        logger.info(f"Signal induced {len(signal.target_tf_ids)} TFs")

    def create_signal(
        self,
        event_type: str,
        description: str = "",
        signal_strength: float = 1.0,
    ) -> SignalEvent:
        """
        Create and process a signal event.

        Convenience method to create a signal and immediately process it.
        """
        signal = SignalEvent(
            id=uuid4(),
            event_type=event_type,
            description=description,
            timestamp=datetime.now(),
            target_tf_ids=[],
            signal_strength=signal_strength,
        )

        self.process_signal(signal)
        return signal

    # -------------------------------------------------------------------------
    # Constraint Weight Calculation
    # -------------------------------------------------------------------------

    def get_constraint_weights(
        self,
        constraint_ids: list[UUID] = None,
    ) -> dict[UUID, tuple[float, str]]:
        """
        Calculate current constraint weights based on TF states.

        This is the main output method - it returns adjusted weights
        for all constraints based on current regulatory state.

        Args:
            constraint_ids: Specific constraints to calculate (None = all)

        Returns:
            Dict of constraint_id -> (weight, explanation)
        """
        results = {}

        target_ids = constraint_ids or list(self.promoters.keys())

        for constraint_id in target_ids:
            promoter = self.promoters.get(constraint_id)
            if not promoter:
                continue

            # Calculate bound TF strengths
            bound_tfs = {}
            all_tf_ids = (
                promoter.required_activators
                + promoter.optional_activators
                + promoter.repressors
            )

            for tf_id in all_tf_ids:
                tf = self.transcription_factors.get(tf_id)
                if tf and tf.is_active:
                    # Calculate effective binding
                    binding_strength = tf.binding_affinity * tf.expression_level
                    bound_tfs[tf_id] = binding_strength

            # Calculate activation
            activation, explanation = promoter.calculate_activation(bound_tfs)

            # Convert to weight
            weight = promoter.get_effective_weight(activation)

            results[constraint_id] = (weight, explanation)

        return results

    def get_weight_for_constraint(
        self,
        constraint_id: UUID,
    ) -> tuple[float, str]:
        """
        Get current weight for a single constraint.

        Returns:
            Tuple of (weight, explanation)
        """
        weights = self.get_constraint_weights([constraint_id])
        return weights.get(constraint_id, (1.0, "No regulatory data"))

    # -------------------------------------------------------------------------
    # Chromatin State Management
    # -------------------------------------------------------------------------

    def set_chromatin_state(
        self,
        constraint_id: UUID,
        state: ChromatinState,
    ):
        """
        Set the chromatin state for a constraint.

        This allows external systems to enable/disable constraints
        at the regulatory level.
        """
        promoter = self.promoters.get(constraint_id)
        if promoter:
            old_state = promoter.chromatin_state
            promoter.chromatin_state = state
            logger.info(
                f"Chromatin state for {promoter.constraint_name}: "
                f"{old_state.value} -> {state.value}"
            )

    def silence_constraints(self, constraint_ids: list[UUID]):
        """Silence (completely disable) multiple constraints."""
        for cid in constraint_ids:
            self.set_chromatin_state(cid, ChromatinState.SILENCED)

    def open_constraints(self, constraint_ids: list[UUID]):
        """Re-open silenced constraints."""
        for cid in constraint_ids:
            self.set_chromatin_state(cid, ChromatinState.OPEN)

    # -------------------------------------------------------------------------
    # Network Analysis
    # -------------------------------------------------------------------------

    def detect_loops(self) -> list[RegulatoryLoop]:
        """
        Detect regulatory loops (network motifs) in the GRN.

        Returns:
            List of detected RegulatoryLoops
        """
        loops = []

        # Build adjacency for analysis
        tf_targets: dict[UUID, set[UUID]] = defaultdict(set)
        for edge in self.edges.values():
            if edge.target_type == "tf":
                tf_targets[edge.source_tf_id].add(edge.target_id)

        # Detect simple feedback loops (A -> B -> A)
        for tf_id in self.transcription_factors:
            for target_id in tf_targets[tf_id]:
                if tf_id in tf_targets[target_id]:
                    # Found feedback loop

                    # Determine type based on edge types
                    edge_1 = self._get_edge(tf_id, target_id)
                    edge_2 = self._get_edge(target_id, tf_id)

                    if edge_1 and edge_2:
                        if (
                            edge_1.edge_type == TFType.ACTIVATOR
                            and edge_2.edge_type == TFType.ACTIVATOR
                        ):
                            loop_type = LoopType.POSITIVE_FEEDBACK
                        elif (
                            edge_1.edge_type == TFType.REPRESSOR
                            or edge_2.edge_type == TFType.REPRESSOR
                        ):
                            loop_type = LoopType.NEGATIVE_FEEDBACK
                        else:
                            loop_type = LoopType.BISTABLE_SWITCH

                        tf1 = self.transcription_factors[tf_id]
                        tf2 = self.transcription_factors[target_id]

                        loop = RegulatoryLoop(
                            id=uuid4(),
                            loop_type=loop_type,
                            description=f"Feedback: {tf1.name} <-> {tf2.name}",
                            tf_ids=[tf_id, target_id],
                            constraint_ids=[],
                            edges=[edge_1, edge_2],
                            stability=(
                                "stable"
                                if loop_type == LoopType.NEGATIVE_FEEDBACK
                                else "potentially_unstable"
                            ),
                        )
                        loops.append(loop)

        # Detect feed-forward loops (A -> B, A -> C, B -> C)
        for tf_a in self.transcription_factors:
            targets_a = tf_targets[tf_a]
            for tf_b in targets_a:
                if tf_b not in self.transcription_factors:
                    continue
                targets_b = tf_targets[tf_b]

                # Find common targets
                for target_c in targets_a & targets_b:
                    edge_ab = self._get_edge(tf_a, tf_b)
                    edge_ac = self._get_edge(tf_a, target_c)
                    edge_bc = self._get_edge(tf_b, target_c)

                    if edge_ab and edge_ac and edge_bc:
                        # Determine if coherent or incoherent
                        same_direction = (edge_ac.edge_type == edge_bc.edge_type) == (
                            edge_ab.edge_type == TFType.ACTIVATOR
                        )

                        loop_type = (
                            LoopType.FEED_FORWARD_COHERENT
                            if same_direction
                            else LoopType.FEED_FORWARD_INCOHERENT
                        )

                        tfa = self.transcription_factors[tf_a]
                        tfb = self.transcription_factors.get(tf_b)

                        loop = RegulatoryLoop(
                            id=uuid4(),
                            loop_type=loop_type,
                            description=f"Feed-forward: {tfa.name} -> {tfb.name if tfb else tf_b} -> {target_c}",
                            tf_ids=(
                                [tf_a, tf_b]
                                if tf_b in self.transcription_factors
                                else [tf_a]
                            ),
                            constraint_ids=(
                                [target_c] if target_c in self.promoters else []
                            ),
                            edges=[edge_ab, edge_ac, edge_bc],
                        )
                        loops.append(loop)

        self.detected_loops = loops
        logger.info(f"Detected {len(loops)} regulatory loops")
        return loops

    def _get_edge(self, source_id: UUID, target_id: UUID) -> RegulatoryEdge | None:
        """Get edge between two nodes."""
        for edge_id in self._edges_by_source[source_id]:
            edge = self.edges[edge_id]
            if edge.target_id == target_id:
                return edge
        return None

    # -------------------------------------------------------------------------
    # State Management
    # -------------------------------------------------------------------------

    def snapshot_state(self) -> GRNState:
        """
        Take a snapshot of current GRN state.

        Useful for analysis and debugging.
        """
        tf_expressions = {
            tf_id: tf.expression_level
            for tf_id, tf in self.transcription_factors.items()
        }

        weights = self.get_constraint_weights()
        constraint_weights = {cid: w for cid, (w, _) in weights.items()}

        # Calculate metrics
        total_activation = sum(
            tf.expression_level
            for tf in self.transcription_factors.values()
            if tf.tf_type == TFType.ACTIVATOR
        )
        total_repression = sum(
            tf.expression_level
            for tf in self.transcription_factors.values()
            if tf.tf_type == TFType.REPRESSOR
        )

        # Network entropy (diversity of expression)
        expressions = list(tf_expressions.values())
        if expressions:
            mean_exp = sum(expressions) / len(expressions)
            if mean_exp > 0:
                variance = sum((e - mean_exp) ** 2 for e in expressions) / len(
                    expressions
                )
                entropy = math.log(1 + variance)
            else:
                entropy = 0.0
        else:
            entropy = 0.0

        state = GRNState(
            timestamp=datetime.now(),
            tf_expressions=tf_expressions,
            constraint_weights=constraint_weights,
            active_loops=[loop.id for loop in self.detected_loops],
            total_activation=total_activation,
            total_repression=total_repression,
            network_entropy=entropy,
        )

        self.state_history.append(state)

        # Keep history manageable
        if len(self.state_history) > 1000:
            self.state_history = self.state_history[-500:]

        return state

    def get_status(self) -> dict[str, Any]:
        """
        Get comprehensive status of the TF scheduler.

        Returns:
            Dict with status information
        """
        active_tfs = [tf for tf in self.transcription_factors.values() if tf.is_active]

        master_tfs = [tf for tf in active_tfs if tf.tf_type == TFType.MASTER]

        # Take snapshot
        state = self.snapshot_state()

        # Count regulated constraints
        regulated = len([w for w in state.constraint_weights.values() if w != 1.0])

        return {
            "timestamp": datetime.now().isoformat(),
            "total_tfs": len(self.transcription_factors),
            "active_tfs": len(active_tfs),
            "master_regulators_active": len(master_tfs),
            "total_constraints_regulated": len(self.promoters),
            "constraints_with_modified_weight": regulated,
            "regulatory_edges": len(self.edges),
            "detected_loops": len(self.detected_loops),
            "total_activation": state.total_activation,
            "total_repression": state.total_repression,
            "network_entropy": state.network_entropy,
            "recent_signals": len([s for s in self.signal_history[-10:]]),
            "active_tf_names": [tf.name for tf in active_tfs],
        }

    def get_tf_expression_report(self) -> list[dict]:
        """Get expression levels for all TFs."""
        return [
            {
                "name": tf.name,
                "type": tf.tf_type.value,
                "expression": tf.expression_level,
                "strength_category": tf.signal_strength_category.value,
                "is_active": tf.is_active,
                "targets": len(tf.target_constraint_ids) + len(tf.target_tf_ids),
            }
            for tf in sorted(
                self.transcription_factors.values(), key=lambda t: -t.expression_level
            )
        ]
