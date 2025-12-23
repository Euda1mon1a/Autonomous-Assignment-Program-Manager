"""
Catalyst identification and scoring for schedule changes.

This module identifies personnel and mechanisms that can act as catalysts
to lower energy barriers for schedule changes. It integrates with:
- Hub analysis (network catalysts)
- User roles (authorization catalysts)
- Backup pools (coverage catalysts)
- Credentials (qualification catalysts)
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduling_catalyst.models import (
    BarrierType,
    CatalystMechanism,
    CatalystPerson,
    CatalystType,
    EnergyBarrier,
)


@dataclass
class CatalystMatch:
    """
    A matched catalyst for a specific barrier.

    Attributes:
        catalyst: The catalyst (person or mechanism)
        barrier: The barrier it addresses
        reduction: How much energy reduction it provides
        confidence: Confidence in this match (0.0-1.0)
    """

    catalyst: CatalystPerson | CatalystMechanism
    barrier: EnergyBarrier
    reduction: float
    confidence: float = 1.0


@dataclass
class CatalystRecommendation:
    """
    Recommendation for addressing barriers with catalysts.

    Attributes:
        barriers: Barriers to address
        recommended_catalysts: Ordered list of catalyst matches
        total_reduction: Expected total energy reduction
        residual_energy: Energy remaining after catalysis
        is_feasible: Whether barriers can be overcome
    """

    barriers: list[EnergyBarrier]
    recommended_catalysts: list[CatalystMatch]
    total_reduction: float
    residual_energy: float
    is_feasible: bool


class CatalystScorer:
    """
    Scores potential catalysts for their effectiveness.

    Uses multiple factors to determine how effective a catalyst
    would be at lowering specific barriers.
    """

    # Weights for different scoring factors
    AVAILABILITY_WEIGHT = 0.3
    CAPABILITY_WEIGHT = 0.4
    CAPACITY_WEIGHT = 0.2
    HISTORY_WEIGHT = 0.1

    @staticmethod
    def score_person_catalyst(
        person: CatalystPerson,
        barrier: EnergyBarrier,
        context: dict[str, Any] | None = None,
    ) -> float:
        """
        Score a person's effectiveness as a catalyst for a barrier.

        Args:
            person: The potential catalyst
            barrier: The barrier to address
            context: Optional context (history, preferences, etc.)

        Returns:
            Score from 0.0 (ineffective) to 1.0 (highly effective)
        """
        if not person.can_address_barrier(barrier):
            return 0.0

        scores = []

        # Availability score
        availability = 1.0 if person.is_available else 0.0
        scores.append(availability * CatalystScorer.AVAILABILITY_WEIGHT)

        # Capability score (base catalyst score)
        capability = person.catalyst_score
        scores.append(capability * CatalystScorer.CAPABILITY_WEIGHT)

        # Capacity score (how much capacity remains)
        capacity = person.capacity_remaining
        scores.append(capacity * CatalystScorer.CAPACITY_WEIGHT)

        # History score (if context provided)
        history_score = 0.5  # Default neutral
        if context and "success_rate" in context:
            history_score = context["success_rate"]
        scores.append(history_score * CatalystScorer.HISTORY_WEIGHT)

        return sum(scores)

    @staticmethod
    def score_mechanism_catalyst(
        mechanism: CatalystMechanism,
        barrier: EnergyBarrier,
    ) -> float:
        """
        Score a mechanism's effectiveness as a catalyst.

        Args:
            mechanism: The potential catalyst mechanism
            barrier: The barrier to address

        Returns:
            Score from 0.0 (ineffective) to 1.0 (highly effective)
        """
        if not mechanism.can_address_barrier(barrier):
            return 0.0

        if not mechanism.is_active:
            return 0.0

        # Mechanisms get scored based on reduction factor
        reduction = mechanism.reduction_factors.get(barrier.barrier_type, 0.0)
        return reduction

    @staticmethod
    def calculate_combined_reduction(
        catalysts: list[CatalystPerson | CatalystMechanism],
        barrier: EnergyBarrier,
    ) -> float:
        """
        Calculate combined reduction from multiple catalysts.

        Catalysts have diminishing returns when stacked.

        Args:
            catalysts: List of catalysts to apply
            barrier: The barrier being addressed

        Returns:
            Combined reduction factor (0.0-1.0)
        """
        if not catalysts or not barrier.can_be_catalyzed:
            return 0.0

        remaining = barrier.energy_contribution

        for catalyst in catalysts:
            if isinstance(catalyst, CatalystPerson):
                reduction = catalyst.reduction_for_barrier(barrier)
            else:
                reduction = catalyst.reduction_factors.get(barrier.barrier_type, 0.0)

            remaining *= 1 - reduction

        total_reduction = barrier.energy_contribution - remaining
        return (
            total_reduction / barrier.energy_contribution
            if barrier.energy_contribution > 0
            else 0.0
        )


class CatalystAnalyzer:
    """
    Analyzes and identifies catalysts for schedule changes.

    Integrates with the existing codebase to find personnel and
    mechanisms that can lower barriers.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the catalyst analyzer.

        Args:
            db: Database session
        """
        self.db = db
        self.scorer = CatalystScorer()

    async def find_person_catalysts(
        self,
        barriers: list[EnergyBarrier],
        limit: int = 10,
    ) -> list[CatalystPerson]:
        """
        Find personnel who can act as catalysts for barriers.

        Args:
            barriers: Barriers to address
            limit: Maximum number of catalysts to return

        Returns:
            List of potential catalyst personnel
        """
        catalysts: list[CatalystPerson] = []

        # Get barrier types that need catalysts
        barrier_types = {b.barrier_type for b in barriers if b.can_be_catalyzed}

        # Find coordinators (electronic barrier catalysts)
        if BarrierType.ELECTRONIC in barrier_types:
            coordinators = await self._find_coordinators()
            catalysts.extend(coordinators)

        # Find hub faculty (thermodynamic/steric catalysts)
        if (
            BarrierType.THERMODYNAMIC in barrier_types
            or BarrierType.STERIC in barrier_types
        ):
            hubs = await self._find_hub_faculty()
            catalysts.extend(hubs)

        # Find available backup personnel
        backups = await self._find_backup_personnel()
        catalysts.extend(backups)

        # Remove duplicates by person_id
        seen: set[UUID] = set()
        unique_catalysts: list[CatalystPerson] = []
        for cat in catalysts:
            if cat.person_id not in seen:
                seen.add(cat.person_id)
                unique_catalysts.append(cat)

        return unique_catalysts[:limit]

    async def find_mechanism_catalysts(
        self,
        barriers: list[EnergyBarrier],
    ) -> list[CatalystMechanism]:
        """
        Find mechanisms that can act as catalysts for barriers.

        Args:
            barriers: Barriers to address

        Returns:
            List of available catalyst mechanisms
        """
        mechanisms: list[CatalystMechanism] = []

        barrier_types = {b.barrier_type for b in barriers if b.can_be_catalyzed}

        # Auto-matcher for thermodynamic barriers
        if BarrierType.THERMODYNAMIC in barrier_types:
            mechanisms.append(
                CatalystMechanism(
                    mechanism_id="auto_matcher",
                    name="Swap Auto-Matcher",
                    catalyst_type=CatalystType.HETEROGENEOUS,
                    barriers_addressed=[BarrierType.THERMODYNAMIC],
                    reduction_factors={BarrierType.THERMODYNAMIC: 0.6},
                    is_active=True,
                )
            )

        # Emergency override codes for kinetic barriers
        if BarrierType.KINETIC in barrier_types:
            mechanisms.append(
                CatalystMechanism(
                    mechanism_id="emergency_override",
                    name="Emergency Override Code",
                    catalyst_type=CatalystType.ENZYMATIC,
                    barriers_addressed=[BarrierType.KINETIC],
                    reduction_factors={BarrierType.KINETIC: 0.8},
                    requires_trigger="emergency_reason_code",
                    is_active=True,
                )
            )

        # Defense escalation for multiple barrier types
        mechanisms.append(
            CatalystMechanism(
                mechanism_id="defense_escalation",
                name="Defense Level Escalation",
                catalyst_type=CatalystType.HETEROGENEOUS,
                barriers_addressed=[
                    BarrierType.KINETIC,
                    BarrierType.ELECTRONIC,
                    BarrierType.THERMODYNAMIC,
                ],
                reduction_factors={
                    BarrierType.KINETIC: 0.5,
                    BarrierType.ELECTRONIC: 0.4,
                    BarrierType.THERMODYNAMIC: 0.3,
                },
                requires_trigger="coverage_threshold",
                is_active=True,
            )
        )

        # Backup pool activation
        mechanisms.append(
            CatalystMechanism(
                mechanism_id="backup_pool",
                name="Backup Pool Activation",
                catalyst_type=CatalystType.HOMOGENEOUS,
                barriers_addressed=[BarrierType.STERIC, BarrierType.THERMODYNAMIC],
                reduction_factors={
                    BarrierType.STERIC: 0.7,
                    BarrierType.THERMODYNAMIC: 0.5,
                },
                is_active=True,
            )
        )

        return mechanisms

    async def recommend_catalysts(
        self,
        barriers: list[EnergyBarrier],
    ) -> CatalystRecommendation:
        """
        Generate catalyst recommendations for a set of barriers.

        Args:
            barriers: Barriers to address

        Returns:
            Recommendation with matched catalysts
        """
        # Find all available catalysts
        person_catalysts = await self.find_person_catalysts(barriers)
        mechanism_catalysts = await self.find_mechanism_catalysts(barriers)

        # Match catalysts to barriers
        matches: list[CatalystMatch] = []

        for barrier in barriers:
            if not barrier.can_be_catalyzed:
                continue

            best_match: CatalystMatch | None = None
            best_score = 0.0

            # Check person catalysts
            for person in person_catalysts:
                if person.can_address_barrier(barrier):
                    score = self.scorer.score_person_catalyst(person, barrier)
                    reduction = person.reduction_for_barrier(barrier)
                    if score > best_score:
                        best_score = score
                        best_match = CatalystMatch(
                            catalyst=person,
                            barrier=barrier,
                            reduction=reduction,
                            confidence=score,
                        )

            # Check mechanism catalysts
            for mechanism in mechanism_catalysts:
                if mechanism.can_address_barrier(barrier):
                    score = self.scorer.score_mechanism_catalyst(mechanism, barrier)
                    reduction = mechanism.reduction_factors.get(
                        barrier.barrier_type, 0.0
                    )
                    if score > best_score:
                        best_score = score
                        best_match = CatalystMatch(
                            catalyst=mechanism,
                            barrier=barrier,
                            reduction=reduction,
                            confidence=score,
                        )

            if best_match:
                matches.append(best_match)

        # Calculate totals
        total_barrier_energy = sum(b.energy_contribution for b in barriers)
        total_reduction = sum(
            m.reduction * m.barrier.energy_contribution for m in matches
        )
        residual_energy = max(0.0, total_barrier_energy - total_reduction)

        # Check absolute barriers
        has_absolute = any(b.is_absolute for b in barriers)

        return CatalystRecommendation(
            barriers=barriers,
            recommended_catalysts=matches,
            total_reduction=total_reduction,
            residual_energy=residual_energy,
            is_feasible=not has_absolute and residual_energy < 1.0,
        )

    async def _find_coordinators(self) -> list[CatalystPerson]:
        """Find coordinator users who can authorize changes."""
        # Would query users with coordinator/admin roles
        # Placeholder implementation
        return [
            CatalystPerson(
                person_id=UUID("00000000-0000-0000-0000-000000000001"),
                name="Schedule Coordinator",
                catalyst_type=CatalystType.ENZYMATIC,
                catalyst_score=0.9,
                barriers_addressed=[BarrierType.ELECTRONIC, BarrierType.KINETIC],
                reduction_factors={
                    BarrierType.ELECTRONIC: 0.9,
                    BarrierType.KINETIC: 0.7,
                },
                is_available=True,
                capacity_remaining=0.8,
            )
        ]

    async def _find_hub_faculty(self) -> list[CatalystPerson]:
        """Find hub faculty with high network centrality."""
        # Would integrate with hub_analysis.py
        # Placeholder implementation
        return [
            CatalystPerson(
                person_id=UUID("00000000-0000-0000-0000-000000000002"),
                name="Hub Faculty Member",
                catalyst_type=CatalystType.HOMOGENEOUS,
                catalyst_score=0.75,
                barriers_addressed=[BarrierType.THERMODYNAMIC, BarrierType.STERIC],
                reduction_factors={
                    BarrierType.THERMODYNAMIC: 0.6,
                    BarrierType.STERIC: 0.5,
                },
                is_available=True,
                capacity_remaining=0.6,
            )
        ]

    async def _find_backup_personnel(self) -> list[CatalystPerson]:
        """Find personnel in backup pools."""
        # Would query backup pool members
        # Placeholder implementation
        return [
            CatalystPerson(
                person_id=UUID("00000000-0000-0000-0000-000000000003"),
                name="Backup Pool Member",
                catalyst_type=CatalystType.HOMOGENEOUS,
                catalyst_score=0.6,
                barriers_addressed=[BarrierType.STERIC],
                reduction_factors={
                    BarrierType.STERIC: 0.8,
                },
                is_available=True,
                capacity_remaining=1.0,
            )
        ]

    async def get_catalyst_statistics(self) -> dict[str, Any]:
        """
        Get statistics about available catalysts.

        Returns:
            Dictionary with catalyst availability and capacity metrics
        """
        # Mock barriers to find all catalyst types
        all_barrier_types = list(BarrierType)
        mock_barriers = [
            EnergyBarrier(
                barrier_type=bt,
                name=f"Mock {bt.value}",
                description="For statistics",
                energy_contribution=0.5,
            )
            for bt in all_barrier_types
        ]

        persons = await self.find_person_catalysts(mock_barriers, limit=100)
        mechanisms = await self.find_mechanism_catalysts(mock_barriers)

        person_by_type: dict[str, int] = {}
        for person in persons:
            for bt in person.barriers_addressed:
                key = bt.value
                person_by_type[key] = person_by_type.get(key, 0) + 1

        mechanism_by_type: dict[str, int] = {}
        for mech in mechanisms:
            for bt in mech.barriers_addressed:
                key = bt.value
                mechanism_by_type[key] = mechanism_by_type.get(key, 0) + 1

        total_capacity = sum(p.capacity_remaining for p in persons)
        available_count = sum(1 for p in persons if p.is_available)

        return {
            "person_catalysts": {
                "total": len(persons),
                "available": available_count,
                "total_capacity": total_capacity,
                "by_barrier_type": person_by_type,
            },
            "mechanism_catalysts": {
                "total": len(mechanisms),
                "active": sum(1 for m in mechanisms if m.is_active),
                "by_barrier_type": mechanism_by_type,
            },
            "coverage": {
                bt.value: (
                    person_by_type.get(bt.value, 0) + mechanism_by_type.get(bt.value, 0)
                )
                for bt in all_barrier_types
            },
        }
