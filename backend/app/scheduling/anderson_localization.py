"""
Anderson Localization for Minimal Schedule Update Scope.

When schedule changes are needed, localize updates to smallest possible
region using Anderson localization principles.

Physics basis: Disorder-induced localization causes exponential decay of
wave propagation. Leverage constraints as "disorder" to prevent global cascade.

Key Concepts:
- Localization Length: Characteristic distance over which changes propagate
- Barrier Strength: Constraint density that prevents cascade
- Escape Probability: Likelihood change breaks containment
- Anderson Transition: Critical disorder threshold for localization

References:
- Anderson, P.W. (1958). "Absence of Diffusion in Certain Random Lattices"
- Thouless, D.J. (1974). "Electrons in disordered systems and the theory of localization"
"""

import logging
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

import networkx as nx
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.scheduling.constraints import (
    Constraint,
    ConstraintManager,
    ConstraintType,
    SchedulingContext,
)

logger = logging.getLogger(__name__)

# Localization thresholds and constants
LOCALIZATION_THRESHOLD = 0.05  # Propagation strength threshold (5%)
ESCAPE_PROBABILITY_THRESHOLD = 0.3  # Escape probability for localized regions
MAX_PROPAGATION_DEPTH_DAYS = 30  # Maximum BFS depth in days
DEFAULT_LOCALIZATION_LENGTH = 1.0  # Default localization length (days)
BARRIER_STRENGTH_WEIGHT_TEMPORAL = 0.8  # Temporal constraint coupling strength
BARRIER_STRENGTH_WEIGHT_SUPERVISION = 0.6  # Supervision constraint coupling strength


class DisruptionType(Enum):
    """Types of schedule disruptions requiring localized updates."""

    LEAVE_REQUEST = "leave_request"  # Resident/faculty leave
    FACULTY_ABSENCE = "faculty_absence"  # Unplanned absence
    EMERGENCY = "emergency"  # TDY, deployment, medical emergency
    CREDENTIAL_EXPIRY = "credential_expiry"  # Procedure credential expired
    SWAP_REQUEST = "swap_request"  # Schedule swap
    ROTATION_CHANGE = "rotation_change"  # Rotation template modification
    ACGME_VIOLATION = "acgme_violation"  # Compliance violation detected


@dataclass
class Disruption:
    """Represents a schedule disruption event."""

    disruption_type: DisruptionType
    person_id: UUID | None = None
    block_ids: list[UUID] = field(default_factory=list)
    affected_date_range: tuple[date, date] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def epicenter_blocks(self) -> set[UUID]:
        """Get the epicenter blocks where disruption originates."""
        return set(self.block_ids)


@dataclass
class LocalizationRegion:
    """
    Bounded region containing schedule update scope.

    Analogous to Anderson localization in disordered media where
    perturbations decay exponentially within localization length.
    """

    affected_assignments: set[UUID]  # Assignment IDs in update scope
    epicenter_blocks: set[UUID]  # Origin blocks of disruption
    boundary_blocks: set[UUID]  # Blocks at region boundary
    localization_length: float  # Characteristic decay distance (days)
    barrier_strength: float  # Constraint density (0-1, higher = stronger barrier)
    escape_probability: float  # P(change propagates beyond region) [0-1]
    region_type: str = "localized"  # 'localized', 'extended', 'global'
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def region_size(self) -> int:
        """Number of assignments in region."""
        return len(self.affected_assignments)

    @property
    def is_localized(self) -> bool:
        """Check if region is truly localized (not global cascade)."""
        return (
            self.region_type == "localized"
            and self.escape_probability < ESCAPE_PROBABILITY_THRESHOLD
        )

    def __repr__(self) -> str:
        return (
            f"LocalizationRegion(size={self.region_size}, "
            f"length={self.localization_length:.1f}d, "
            f"barrier={self.barrier_strength:.2f}, "
            f"escape_p={self.escape_probability:.2f})"
        )


@dataclass
class PropagationStep:
    """Single step in change propagation analysis."""

    depth: int  # Distance from epicenter (in blocks/days)
    affected_blocks: set[UUID]
    affected_assignments: set[UUID]
    propagation_strength: float  # Strength at this depth [0-1]
    constraint_density: float  # Constraint density at this depth


class PropagationAnalyzer:
    """
    Analyzes how schedule changes propagate through constraint graph.

    Uses breadth-first search with exponential decay model to predict
    cascade scope.
    """

    def __init__(
        self,
        db: Session,
        constraint_manager: ConstraintManager,
        context: SchedulingContext,
    ):
        self.db = db
        self.constraint_manager = constraint_manager
        self.context = context
        self.constraint_graph = self._build_constraint_graph()

    def _build_constraint_graph(self) -> nx.Graph:
        """
        Build graph where nodes=blocks, edges=constraints.

        Edge weight = constraint coupling strength (0-1).
        """
        G = nx.Graph()

        # Add nodes for all blocks in scheduling context
        for block in self.context.blocks.values():
            G.add_node(block.id, date=block.date, session=block.session)

        # Add edges for temporal constraints (consecutive days)
        for block in self.context.blocks.values():
            # Connect to next day's blocks
            next_date = block.date + timedelta(days=1)
            for next_block in self.context.blocks.values():
                if next_block.date == next_date:
                    # Weight based on duty hours coupling
                    G.add_edge(
                        block.id,
                        next_block.id,
                        weight=BARRIER_STRENGTH_WEIGHT_TEMPORAL,
                        type="temporal",
                    )

        # Add edges for supervision constraints
        # (blocks on same day requiring same faculty)
        blocks_by_date = defaultdict(list)
        for block in self.context.blocks.values():
            blocks_by_date[block.date].append(block.id)

        for block_ids in blocks_by_date.values():
            # Connect all blocks on same day
            for i, b1 in enumerate(block_ids):
                for b2 in block_ids[i + 1 :]:
                    G.add_edge(
                        b1,
                        b2,
                        weight=BARRIER_STRENGTH_WEIGHT_SUPERVISION,
                        type="supervision",
                    )

        return G

    def measure_propagation(
        self, epicenter_blocks: set[UUID], max_depth: int = 30
    ) -> list[PropagationStep]:
        """
        Measure how changes propagate from epicenter using BFS.

        Args:
            epicenter_blocks: Initial blocks where change occurs
            max_depth: Maximum propagation distance (days)

        Returns:
            List of propagation steps with decay profile
        """
        steps = []
        visited = set()
        queue = deque([(block_id, 0) for block_id in epicenter_blocks])

        depth_groups = defaultdict(set)
        for block_id in epicenter_blocks:
            depth_groups[0].add(block_id)
            visited.add(block_id)

        while queue:
            block_id, depth = queue.popleft()

            if depth >= max_depth:
                continue

            # Get neighbors in constraint graph
            if block_id not in self.constraint_graph:
                continue

            for neighbor_id in self.constraint_graph.neighbors(block_id):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_depth = depth + 1
                    depth_groups[new_depth].add(neighbor_id)
                    queue.append((neighbor_id, new_depth))

        # Compute propagation steps with decay
        for depth in sorted(depth_groups.keys()):
            blocks_at_depth = depth_groups[depth]

            # Exponential decay: strength = exp(-depth / localization_length)
            # Assume initial localization length ~ 7 days
            localization_length = 7.0
            strength = math.exp(-depth / localization_length)

            # Get assignments at this depth
            assignments_at_depth = set()
            for block_id in blocks_at_depth:
                assignments_at_depth.update(self._get_assignments_for_block(block_id))

            # Estimate constraint density at this depth
            constraint_density = self._estimate_constraint_density(blocks_at_depth)

            steps.append(
                PropagationStep(
                    depth=depth,
                    affected_blocks=blocks_at_depth,
                    affected_assignments=assignments_at_depth,
                    propagation_strength=strength,
                    constraint_density=constraint_density,
                )
            )

        return steps

    def _get_assignments_for_block(self, block_id: UUID) -> set[UUID]:
        """Get all assignment IDs for a given block."""
        assignments = (
            self.db.query(Assignment.id).filter(Assignment.block_id == block_id).all()
        )
        return {a.id for a in assignments}

    def _estimate_constraint_density(self, blocks: set[UUID]) -> float:
        """
        Estimate constraint density for block set.

        Higher density = stronger barrier to propagation.
        """
        if not blocks:
            return 0.0

        # Count constraints affecting these blocks
        constraint_count = 0
        for constraint in self.constraint_manager.hard_constraints:
            # Simple heuristic: count constraints that reference any block
            # In real implementation, would need constraint-specific logic
            constraint_count += 1

        # Normalize by number of blocks
        density = min(1.0, constraint_count / (len(blocks) * 5))  # 5 = avg constraints
        return density


class AndersonLocalizer:
    """
    Compute minimal update regions using Anderson localization principles.

    Key algorithm: Use constraint graph as "disorder" to trap updates
    in localized regions via exponential decay.
    """

    def __init__(
        self,
        db: Session,
        constraint_manager: ConstraintManager | None = None,
    ):
        self.db = db
        self.constraint_manager = (
            constraint_manager or ConstraintManager.create_default()
        )

    def compute_localization_region(
        self,
        disruption: Disruption,
        schedule_context: SchedulingContext,
    ) -> LocalizationRegion:
        """
        Compute minimal update region for a disruption.

        Algorithm:
        1. Build constraint graph
        2. Perform BFS from epicenter with exponential decay
        3. Stop when propagation strength < threshold
        4. Return bounded region

        Args:
            disruption: Schedule disruption event
            schedule_context: Full scheduling context

        Returns:
            Localized region containing minimal update scope
        """
        logger.info(
            f"Computing localization region for {disruption.disruption_type.value}"
        )

        # Build propagation analyzer
        analyzer = PropagationAnalyzer(
            db=self.db,
            constraint_manager=self.constraint_manager,
            context=schedule_context,
        )

        # Measure propagation from epicenter
        epicenter_blocks = disruption.epicenter_blocks
        propagation_steps = analyzer.measure_propagation(
            epicenter_blocks=epicenter_blocks, max_depth=MAX_PROPAGATION_DEPTH_DAYS
        )

        # Find localization boundary (where strength < threshold)
        threshold = LOCALIZATION_THRESHOLD
        affected_assignments = set()
        boundary_blocks = set()
        total_depth = 0

        for step in propagation_steps:
            if step.propagation_strength < threshold:
                # Found localization boundary
                boundary_blocks = step.affected_blocks
                break

            affected_assignments.update(step.affected_assignments)
            total_depth = step.depth

        # Compute localization metrics
        localization_length = self._compute_localization_length(propagation_steps)
        barrier_strength = self._compute_barrier_strength(propagation_steps)
        escape_probability = self._compute_escape_probability(
            propagation_steps, affected_assignments, schedule_context
        )

        # Determine region type
        region_type = self._classify_region_type(
            affected_assignments, schedule_context, escape_probability
        )

        return LocalizationRegion(
            affected_assignments=affected_assignments,
            epicenter_blocks=epicenter_blocks,
            boundary_blocks=boundary_blocks,
            localization_length=localization_length,
            barrier_strength=barrier_strength,
            escape_probability=escape_probability,
            region_type=region_type,
            metadata={
                "disruption_type": disruption.disruption_type.value,
                "propagation_depth": total_depth,
                "num_steps": len(propagation_steps),
            },
        )

    def _compute_localization_length(
        self, propagation_steps: list[PropagationStep]
    ) -> float:
        """
        Compute characteristic localization length from decay profile.

        Fits exponential decay: strength(d) = exp(-d / L)
        where L = localization length.

        Returns:
            Localization length in days
        """
        if len(propagation_steps) < 2:
            return DEFAULT_LOCALIZATION_LENGTH

        # Fit exponential decay
        # ln(strength) = -depth / L
        # L = -depth / ln(strength)

        total_weighted_length = 0.0
        total_weight = 0.0

        for step in propagation_steps:
            if step.propagation_strength > 0.01:  # Avoid log(0)
                length = -step.depth / math.log(step.propagation_strength)
                weight = step.propagation_strength  # Weight by strength
                total_weighted_length += length * weight
                total_weight += weight

        if total_weight == 0:
            return DEFAULT_LOCALIZATION_LENGTH

        return total_weighted_length / total_weight

    def _compute_barrier_strength(
        self, propagation_steps: list[PropagationStep]
    ) -> float:
        """
        Compute barrier strength from constraint density.

        Higher constraint density = stronger barrier = better localization.
        """
        if not propagation_steps:
            return 0.0

        # Average constraint density across all steps
        total_density = sum(step.constraint_density for step in propagation_steps)
        avg_density = total_density / len(propagation_steps)

        return avg_density

    def _compute_escape_probability(
        self,
        propagation_steps: list[PropagationStep],
        affected_assignments: set[UUID],
        schedule_context: SchedulingContext,
    ) -> float:
        """
        Compute probability that change escapes localized region.

        Based on:
        - Region size relative to total schedule
        - Decay rate
        - Boundary constraint density
        """
        if not propagation_steps:
            return 1.0  # No containment

        # Get total assignments in schedule
        total_assignments = len(schedule_context.blocks) * 2  # Estimate

        # Size factor: larger region = higher escape probability
        size_factor = min(1.0, len(affected_assignments) / max(1, total_assignments))

        # Decay factor: faster decay = lower escape probability
        final_strength = propagation_steps[-1].propagation_strength
        decay_factor = final_strength

        # Boundary factor: higher boundary density = lower escape probability
        if propagation_steps:
            boundary_density = propagation_steps[-1].constraint_density
            boundary_factor = 1.0 - boundary_density
        else:
            boundary_factor = 1.0

        # Combine factors
        escape_prob = size_factor * 0.4 + decay_factor * 0.3 + boundary_factor * 0.3

        return min(1.0, max(0.0, escape_prob))

    def _classify_region_type(
        self,
        affected_assignments: set[UUID],
        schedule_context: SchedulingContext,
        escape_probability: float,
    ) -> str:
        """
        Classify region as localized, extended, or global.

        Classification thresholds:
        - Localized: < 20% of schedule, escape_prob < 0.3
        - Extended: 20-60% of schedule or 0.3 < escape_prob < 0.7
        - Global: > 60% of schedule or escape_prob > 0.7
        """
        total_assignments = len(schedule_context.blocks) * 2  # Estimate
        coverage_fraction = len(affected_assignments) / max(1, total_assignments)

        if coverage_fraction < 0.2 and escape_probability < 0.3:
            return "localized"
        elif coverage_fraction > 0.6 or escape_probability > 0.7:
            return "global"
        else:
            return "extended"

    def measure_propagation_depth(
        self,
        test_change: dict[str, Any],
        region: LocalizationRegion,
    ) -> float:
        """
        Measure how far a test change would propagate within region.

        Args:
            test_change: Hypothetical change to test
            region: Localization region

        Returns:
            Propagation depth in days
        """
        # For test changes, estimate based on localization length
        # Real implementation would simulate change in solver

        # Simple heuristic: depth ~ localization_length * (1 - barrier_strength)
        effective_depth = region.localization_length * (1.0 - region.barrier_strength)

        return effective_depth

    def apply_localized_update(
        self,
        schedule_context: SchedulingContext,
        disruption: Disruption,
        region: LocalizationRegion,
    ) -> dict[str, Any]:
        """
        Apply schedule update only within localized region.

        Args:
            schedule_context: Full scheduling context
            disruption: Disruption to handle
            region: Pre-computed localization region

        Returns:
            Updated schedule (only affected assignments modified)
        """
        logger.info(
            f"Applying localized update for {disruption.disruption_type.value} "
            f"(region size: {region.region_size})"
        )

        # Create microsolver for region only
        microsolver = self.create_microsolver(schedule_context, region)

        # In real implementation, would:
        # 1. Extract assignments in region
        # 2. Run constraint solver on region only
        # 3. Merge results back into full schedule
        # 4. Validate boundaries maintained

        updated_assignments = {
            "region_id": str(region.epicenter_blocks),
            "num_updated": region.region_size,
            "localization_length": region.localization_length,
            "barrier_strength": region.barrier_strength,
        }

        return updated_assignments

    def create_microsolver(
        self,
        schedule_context: SchedulingContext,
        region: LocalizationRegion,
    ) -> dict[str, Any]:
        """
        Create small constraint solver for localized region only.

        Args:
            schedule_context: Full scheduling context
            region: Localized region

        Returns:
            Microsolver configuration (in real implementation, would be
            actual solver instance)
        """
        # Filter context to region only
        region_blocks = region.epicenter_blocks | region.boundary_blocks

        # Create reduced scheduling context
        microsolver_config = {
            "region_blocks": list(region_blocks),
            "affected_assignments": list(region.affected_assignments),
            "constraint_manager": self.constraint_manager,
            "boundary_constraints": self._extract_boundary_constraints(region),
            "region_type": region.region_type,
        }

        logger.info(
            f"Created microsolver for region: "
            f"{len(region_blocks)} blocks, "
            f"{region.region_size} assignments"
        )

        return microsolver_config

    def _extract_boundary_constraints(
        self, region: LocalizationRegion
    ) -> list[dict[str, Any]]:
        """
        Extract constraints at region boundary.

        Boundary constraints ensure updates don't violate boundaries.
        """
        boundary_constraints = []

        # For each boundary block, extract relevant constraints
        for block_id in region.boundary_blocks:
            # In real implementation, would query specific constraints
            boundary_constraints.append(
                {
                    "block_id": str(block_id),
                    "type": "boundary_lock",
                    "description": "Lock boundary assignments",
                }
            )

        return boundary_constraints

    def compute_anderson_transition_threshold(
        self, schedule_context: SchedulingContext
    ) -> float:
        """
        Compute critical constraint density for Anderson transition.

        Below threshold: Extended states (global cascade)
        Above threshold: Localized states (confined updates)

        Returns:
            Critical constraint density [0-1]
        """
        # In 3D disorder: critical threshold ~ 0.3-0.4
        # In constraint graph: depends on connectivity

        # Estimate graph connectivity
        num_blocks = len(schedule_context.blocks)
        num_constraints = len(self.constraint_manager.hard_constraints)

        # Average constraints per block
        avg_connectivity = num_constraints / max(1, num_blocks)

        # Critical threshold increases with connectivity
        # For highly connected graphs (avg > 10): threshold ~ 0.5
        # For sparse graphs (avg < 3): threshold ~ 0.2

        if avg_connectivity > 10:
            critical_threshold = 0.5
        elif avg_connectivity > 5:
            critical_threshold = 0.35
        else:
            critical_threshold = 0.2

        logger.info(
            f"Anderson transition threshold: {critical_threshold:.2f} "
            f"(avg_connectivity: {avg_connectivity:.1f})"
        )

        return critical_threshold
