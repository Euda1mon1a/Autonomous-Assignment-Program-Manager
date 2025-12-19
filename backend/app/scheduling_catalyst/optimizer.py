"""
Transition state optimizer for schedule changes.

This module finds optimal pathways for schedule changes, analogous to
finding the lowest-energy reaction pathway in chemistry. It considers:
- All barriers in the path
- Available catalysts
- Intermediate states
- Reversibility requirements
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduling_catalyst.barriers import BarrierDetector, BarrierWeights
from app.scheduling_catalyst.catalysts import CatalystAnalyzer, CatalystRecommendation
from app.scheduling_catalyst.models import (
    ActivationEnergy,
    BarrierType,
    CatalystMechanism,
    CatalystPerson,
    CatalystType,
    EnergyBarrier,
    ReactionPathway,
    ReactionType,
    ScheduleReaction,
    TransitionState,
)


@dataclass
class PathwayResult:
    """
    Result of pathway optimization.

    Attributes:
        success: Whether a feasible pathway was found
        pathway: The optimal pathway (if found)
        alternative_pathways: Other viable pathways
        blocking_barriers: Barriers that prevent any pathway
        recommendations: Suggestions for making infeasible changes feasible
    """

    success: bool
    pathway: Optional[ReactionPathway] = None
    alternative_pathways: list[ReactionPathway] = field(default_factory=list)
    blocking_barriers: list[EnergyBarrier] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class OptimizationConfig:
    """
    Configuration for pathway optimization.

    Attributes:
        max_catalysts: Maximum catalysts to apply to a single barrier
        max_pathways: Maximum alternative pathways to consider
        energy_threshold: Maximum acceptable activation energy
        prefer_mechanisms: Prefer automated mechanisms over personnel
        allow_multi_step: Allow multi-step transition pathways
    """

    max_catalysts: int = 3
    max_pathways: int = 5
    energy_threshold: float = 0.8
    prefer_mechanisms: bool = True
    allow_multi_step: bool = True


class TransitionOptimizer:
    """
    Optimizes transition pathways for schedule changes.

    Finds the lowest-energy path from current state to target state,
    applying catalysts to reduce barriers where possible.
    """

    def __init__(
        self,
        db: AsyncSession,
        config: Optional[OptimizationConfig] = None,
        barrier_weights: Optional[BarrierWeights] = None,
    ) -> None:
        """
        Initialize the optimizer.

        Args:
            db: Database session
            config: Optimization configuration
            barrier_weights: Custom barrier weights
        """
        self.db = db
        self.config = config or OptimizationConfig()
        self.barrier_detector = BarrierDetector(db, barrier_weights)
        self.catalyst_analyzer = CatalystAnalyzer(db)

    async def find_optimal_pathway(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
        available_catalysts: Optional[list[CatalystPerson | CatalystMechanism]] = None,
    ) -> PathwayResult:
        """
        Find the optimal transition pathway for a schedule change.

        Args:
            assignment_id: ID of assignment to change
            proposed_change: Description of proposed change
            available_catalysts: Pre-selected catalysts (optional)

        Returns:
            PathwayResult with optimal pathway and alternatives
        """
        # Step 1: Detect all barriers
        barriers = await self.barrier_detector.detect_all_barriers(
            assignment_id, proposed_change
        )

        # Step 2: Check for absolute barriers
        absolute_barriers = [b for b in barriers if b.is_absolute]
        if absolute_barriers:
            return PathwayResult(
                success=False,
                blocking_barriers=absolute_barriers,
                recommendations=self._generate_blocking_recommendations(absolute_barriers),
            )

        # Step 3: Calculate initial activation energy
        initial_energy = self.barrier_detector.calculate_activation_energy()

        # Step 4: If energy is already low enough, return simple pathway
        if initial_energy.value <= self.config.energy_threshold:
            pathway = self._create_simple_pathway(
                assignment_id, proposed_change, barriers, initial_energy
            )
            return PathwayResult(success=True, pathway=pathway)

        # Step 5: Find catalysts
        if available_catalysts is None:
            recommendation = await self.catalyst_analyzer.recommend_catalysts(barriers)
            catalysts_to_use = [m.catalyst for m in recommendation.recommended_catalysts]
        else:
            catalysts_to_use = available_catalysts

        # Step 6: Build optimized pathway
        pathway = await self._build_optimized_pathway(
            assignment_id, proposed_change, barriers, catalysts_to_use
        )

        # Step 7: Check if pathway is feasible
        if pathway.effective_activation_energy <= self.config.energy_threshold:
            # Find alternatives if requested
            alternatives = []
            if self.config.max_pathways > 1:
                alternatives = await self._find_alternative_pathways(
                    assignment_id, proposed_change, barriers
                )

            return PathwayResult(
                success=True,
                pathway=pathway,
                alternative_pathways=alternatives,
            )

        # Step 8: Pathway not feasible, generate recommendations
        return PathwayResult(
            success=False,
            pathway=pathway,  # Include partial pathway
            blocking_barriers=[
                b for b in barriers if b.energy_contribution > 0.5
            ],
            recommendations=self._generate_infeasibility_recommendations(
                barriers, pathway
            ),
        )

    async def optimize_swap(
        self,
        requester_id: UUID,
        target_id: UUID,
        assignment_id: UUID,
    ) -> PathwayResult:
        """
        Optimize a swap between two personnel.

        Swaps are reversible reactions with specific catalyst patterns.

        Args:
            requester_id: Person initiating the swap
            target_id: Person to swap with
            assignment_id: Assignment to swap

        Returns:
            PathwayResult for the swap
        """
        proposed_change = {
            "change_type": "swap",
            "requester_id": str(requester_id),
            "new_person_id": target_id,
            "other_person_consented": False,  # Will check
        }

        result = await self.find_optimal_pathway(assignment_id, proposed_change)

        # Swaps need special handling for reversibility
        if result.success and result.pathway:
            result.pathway = self._add_reversibility_info(result.pathway)

        return result

    async def optimize_emergency_coverage(
        self,
        assignment_id: UUID,
        emergency_type: str,
    ) -> PathwayResult:
        """
        Optimize emergency coverage changes.

        Emergency changes have special catalysts available (override codes).

        Args:
            assignment_id: Assignment needing coverage
            emergency_type: Type of emergency (sick_call, deployment, etc.)

        Returns:
            PathwayResult with emergency-optimized pathway
        """
        proposed_change = {
            "change_type": "emergency_coverage",
            "emergency_type": emergency_type,
            "override_code": emergency_type.upper(),
        }

        # Emergency override mechanism
        emergency_catalyst = CatalystMechanism(
            mechanism_id=f"emergency_{emergency_type}",
            name=f"Emergency Override ({emergency_type})",
            catalyst_type=CatalystType.ENZYMATIC,
            barriers_addressed=[BarrierType.KINETIC, BarrierType.ELECTRONIC],
            reduction_factors={
                BarrierType.KINETIC: 0.9,
                BarrierType.ELECTRONIC: 0.8,
            },
            is_active=True,
        )

        return await self.find_optimal_pathway(
            assignment_id,
            proposed_change,
            available_catalysts=[emergency_catalyst],
        )

    async def calculate_reaction_kinetics(
        self,
        pathway: ReactionPathway,
    ) -> ScheduleReaction:
        """
        Calculate reaction kinetics for a pathway.

        Determines rate constants, half-life, and other kinetic parameters.

        Args:
            pathway: The reaction pathway

        Returns:
            ScheduleReaction with kinetics information
        """
        # Rate constant inversely related to activation energy
        # Higher energy = slower reaction
        rate_constant = 1.0 / (1.0 + pathway.effective_activation_energy * 10)

        # Half-life (time for 50% probability of completion)
        # Based on rate constant and complexity
        half_life_minutes = int(60 / rate_constant)

        # Determine reaction type from pathway
        reaction_type = self._infer_reaction_type(pathway)

        return ScheduleReaction(
            reaction_id=str(uuid4()),
            reaction_type=reaction_type,
            reactants=[pathway.initial_state],
            products=[pathway.target_state],
            pathway=pathway,
            rate_constant=rate_constant,
            half_life=half_life_minutes,
            is_reversible=True,
            reversal_window=1440,  # 24 hours
        )

    def _create_simple_pathway(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
        barriers: list[EnergyBarrier],
        energy: ActivationEnergy,
    ) -> ReactionPathway:
        """Create a simple direct pathway (no catalysts needed)."""
        return ReactionPathway(
            pathway_id=str(uuid4()),
            initial_state={"assignment_id": str(assignment_id)},
            target_state=proposed_change,
            barriers=barriers,
            total_activation_energy=energy.value,
            effective_activation_energy=energy.value,
            estimated_duration=30,  # 30 minutes for simple changes
        )

    async def _build_optimized_pathway(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
        barriers: list[EnergyBarrier],
        catalysts: list[CatalystPerson | CatalystMechanism],
    ) -> ReactionPathway:
        """Build an optimized pathway with catalysts applied."""
        pathway = ReactionPathway(
            pathway_id=str(uuid4()),
            initial_state={"assignment_id": str(assignment_id)},
            target_state=proposed_change,
            barriers=barriers,
            total_activation_energy=sum(b.energy_contribution for b in barriers),
        )

        # Apply catalysts in order of effectiveness
        sorted_catalysts = sorted(
            catalysts,
            key=lambda c: c.catalyst_score if isinstance(c, CatalystPerson) else 0.8,
            reverse=True,
        )

        for catalyst in sorted_catalysts[: self.config.max_catalysts]:
            pathway.add_catalyst(catalyst)

        # If multi-step allowed and energy still high, add transition states
        if (
            self.config.allow_multi_step
            and pathway.effective_activation_energy > self.config.energy_threshold * 0.8
        ):
            transition_states = self._generate_transition_states(pathway)
            pathway.transition_states = transition_states

        # Estimate duration based on complexity
        base_duration = 30  # minutes
        catalyst_speedup = 0.8 ** len(pathway.catalysts_applied)
        transition_overhead = 15 * len(pathway.transition_states)
        pathway.estimated_duration = int(
            base_duration * catalyst_speedup + transition_overhead
        )

        return pathway

    async def _find_alternative_pathways(
        self,
        assignment_id: UUID,
        proposed_change: dict[str, Any],
        barriers: list[EnergyBarrier],
    ) -> list[ReactionPathway]:
        """Find alternative pathways with different catalyst combinations."""
        alternatives: list[ReactionPathway] = []

        # Get all available catalysts
        recommendation = await self.catalyst_analyzer.recommend_catalysts(barriers)

        # Try different catalyst subsets
        all_catalysts = [m.catalyst for m in recommendation.recommended_catalysts]

        for i in range(min(len(all_catalysts), self.config.max_pathways - 1)):
            # Skip first catalyst to get alternative
            subset = all_catalysts[i + 1 :]
            if subset:
                alt_pathway = await self._build_optimized_pathway(
                    assignment_id, proposed_change, barriers, subset
                )
                if alt_pathway.effective_activation_energy <= 1.0:
                    alternatives.append(alt_pathway)

        return alternatives

    def _generate_transition_states(
        self,
        pathway: ReactionPathway,
    ) -> list[TransitionState]:
        """Generate intermediate transition states for complex pathways."""
        states: list[TransitionState] = []

        # Group barriers by type
        barriers_by_type: dict[BarrierType, list[EnergyBarrier]] = {}
        for barrier in pathway.barriers:
            bt = barrier.barrier_type
            if bt not in barriers_by_type:
                barriers_by_type[bt] = []
            barriers_by_type[bt].append(barrier)

        # Create transition state for each barrier type
        energy_so_far = 0.0
        for bt, type_barriers in barriers_by_type.items():
            type_energy = sum(b.energy_contribution for b in type_barriers)
            energy_so_far += type_energy

            states.append(
                TransitionState(
                    state_id=f"{pathway.pathway_id}_{bt.value}",
                    description=f"Overcome {bt.value} barriers",
                    assignments={"barriers_cleared": bt.value},
                    energy_level=energy_so_far / pathway.total_activation_energy,
                    is_stable=False,
                    duration=10,  # 10 minutes per transition
                )
            )

        return states

    def _add_reversibility_info(
        self,
        pathway: ReactionPathway,
    ) -> ReactionPathway:
        """Add reversibility information to a swap pathway."""
        # Add a metastable intermediate representing the 24-hour window
        rollback_state = TransitionState(
            state_id=f"{pathway.pathway_id}_rollback_window",
            description="Within 24-hour rollback window",
            assignments={"rollback_available": True},
            energy_level=pathway.effective_activation_energy * 0.1,
            is_stable=True,  # Metastable - can stay here
            duration=1440,  # 24 hours
        )

        pathway.transition_states.append(rollback_state)
        return pathway

    def _infer_reaction_type(self, pathway: ReactionPathway) -> ReactionType:
        """Infer the reaction type from pathway target state."""
        target = pathway.target_state
        change_type = target.get("change_type", "modification")

        type_mapping = {
            "swap": ReactionType.SWAP,
            "reassignment": ReactionType.REASSIGNMENT,
            "cancellation": ReactionType.CANCELLATION,
            "creation": ReactionType.CREATION,
            "emergency_coverage": ReactionType.REASSIGNMENT,
        }

        return type_mapping.get(change_type, ReactionType.MODIFICATION)

    def _generate_blocking_recommendations(
        self,
        barriers: list[EnergyBarrier],
    ) -> list[str]:
        """Generate recommendations for overcoming blocking barriers."""
        recommendations: list[str] = []

        for barrier in barriers:
            if barrier.barrier_type == BarrierType.REGULATORY:
                if "acgme" in barrier.source.lower():
                    recommendations.append(
                        f"ACGME violation cannot be overridden. "
                        f"Consider adjusting other assignments to maintain compliance."
                    )
            elif barrier.barrier_type == BarrierType.ELECTRONIC:
                if "consent" in barrier.source.lower():
                    recommendations.append(
                        f"Obtain consent from the other party before proceeding."
                    )
            elif barrier.barrier_type == BarrierType.STERIC:
                if "credential" in barrier.source.lower():
                    recommendations.append(
                        f"Required credentials are missing. "
                        f"Consider a different assignee or expedite credentialing."
                    )

        if not recommendations:
            recommendations.append(
                "This change cannot proceed due to immutable constraints. "
                "Consider an alternative approach."
            )

        return recommendations

    def _generate_infeasibility_recommendations(
        self,
        barriers: list[EnergyBarrier],
        pathway: ReactionPathway,
    ) -> list[str]:
        """Generate recommendations for reducing pathway energy."""
        recommendations: list[str] = []

        # Identify highest-energy barriers not addressed
        unaddressed = []
        addressed_types = set()
        for catalyst in pathway.catalysts_applied:
            if isinstance(catalyst, CatalystPerson):
                addressed_types.update(catalyst.barriers_addressed)
            else:
                addressed_types.update(catalyst.barriers_addressed)

        for barrier in barriers:
            if barrier.barrier_type not in addressed_types:
                unaddressed.append(barrier)

        for barrier in sorted(unaddressed, key=lambda b: b.energy_contribution, reverse=True)[:3]:
            if barrier.barrier_type == BarrierType.KINETIC:
                recommendations.append(
                    f"Request freeze horizon override from a coordinator."
                )
            elif barrier.barrier_type == BarrierType.THERMODYNAMIC:
                recommendations.append(
                    f"Use auto-matcher to find better swap candidates."
                )
            elif barrier.barrier_type == BarrierType.ELECTRONIC:
                recommendations.append(
                    f"Obtain coordinator approval to proceed."
                )

        if not recommendations:
            recommendations.append(
                f"Current activation energy ({pathway.effective_activation_energy:.2f}) "
                f"exceeds threshold ({self.config.energy_threshold:.2f}). "
                f"Additional catalysts needed."
            )

        return recommendations


class BatchOptimizer:
    """
    Optimizes multiple schedule changes together.

    Useful for finding globally optimal solutions when multiple
    changes are being considered simultaneously.
    """

    def __init__(
        self,
        db: AsyncSession,
        config: Optional[OptimizationConfig] = None,
    ) -> None:
        """Initialize the batch optimizer."""
        self.db = db
        self.config = config or OptimizationConfig()
        self.single_optimizer = TransitionOptimizer(db, config)

    async def optimize_batch(
        self,
        changes: list[tuple[UUID, dict[str, Any]]],
    ) -> list[PathwayResult]:
        """
        Optimize multiple changes together.

        Args:
            changes: List of (assignment_id, proposed_change) tuples

        Returns:
            List of PathwayResults for each change
        """
        results: list[PathwayResult] = []

        # First pass: get individual results
        for assignment_id, proposed_change in changes:
            result = await self.single_optimizer.find_optimal_pathway(
                assignment_id, proposed_change
            )
            results.append(result)

        # Second pass: check for catalyst conflicts
        used_catalysts: set[UUID] = set()
        for result in results:
            if result.pathway:
                for catalyst in result.pathway.catalysts_applied:
                    if isinstance(catalyst, CatalystPerson):
                        if catalyst.person_id in used_catalysts:
                            # Catalyst already used - need to find alternative
                            result.recommendations.append(
                                f"Catalyst {catalyst.name} already committed to another change."
                            )
                        else:
                            used_catalysts.add(catalyst.person_id)

        return results

    async def find_optimal_order(
        self,
        changes: list[tuple[UUID, dict[str, Any]]],
    ) -> list[int]:
        """
        Find the optimal order to execute changes.

        Some changes may be easier after others complete.

        Args:
            changes: List of changes to order

        Returns:
            List of indices in optimal execution order
        """
        results = await self.optimize_batch(changes)

        # Sort by activation energy (easiest first)
        indexed_energies = [
            (i, r.pathway.effective_activation_energy if r.pathway else 1.0)
            for i, r in enumerate(results)
        ]
        indexed_energies.sort(key=lambda x: x[1])

        return [i for i, _ in indexed_energies]
