"""
Integration with existing resilience framework.

This module provides hooks to integrate the scheduling catalyst library
with the existing resilience framework components:
- Defense in depth (cascade catalyst system)
- Hub analysis (network catalysts)
- Sacrifice hierarchy (decision catalysts)
- Homeostasis (feedback catalysts)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduling_catalyst.models import (
    ActivationEnergy,
    BarrierType,
    CatalystMechanism,
    CatalystPerson,
    CatalystType,
    EnergyBarrier,
)
from app.scheduling_catalyst.catalysts import CatalystAnalyzer


class DefenseLevelProtocol(Protocol):
    """Protocol for defense level integration."""

    level: int
    name: str
    coverage_threshold: float


class HubMetricsProtocol(Protocol):
    """Protocol for hub analysis integration."""

    person_id: UUID
    composite_score: float
    degree_centrality: float
    betweenness_centrality: float
    unique_services: int


@dataclass
class CatalystDefenseLevel:
    """
    Maps defense levels to catalyst activation thresholds.

    As defense levels escalate, more powerful catalysts become available.
    """

    level: int
    name: str
    catalysts_unlocked: list[str]
    barrier_reduction_bonus: float


# Defense level to catalyst mapping
DEFENSE_CATALYST_MAPPING = {
    1: CatalystDefenseLevel(
        level=1,
        name="PREVENTION",
        catalysts_unlocked=["cross_training", "workload_balancer"],
        barrier_reduction_bonus=0.0,
    ),
    2: CatalystDefenseLevel(
        level=2,
        name="CONTROL",
        catalysts_unlocked=["auto_matcher", "preference_negotiation"],
        barrier_reduction_bonus=0.1,
    ),
    3: CatalystDefenseLevel(
        level=3,
        name="SAFETY_SYSTEMS",
        catalysts_unlocked=["backup_pool", "emergency_override"],
        barrier_reduction_bonus=0.2,
    ),
    4: CatalystDefenseLevel(
        level=4,
        name="CONTAINMENT",
        catalysts_unlocked=["sacrifice_hierarchy", "service_reduction"],
        barrier_reduction_bonus=0.3,
    ),
    5: CatalystDefenseLevel(
        level=5,
        name="EMERGENCY",
        catalysts_unlocked=["external_escalation", "crisis_mode"],
        barrier_reduction_bonus=0.5,
    ),
}


class DefenseIntegration:
    """
    Integrates catalyst system with defense in depth framework.

    Defense levels act as cascade catalysts - each level enables
    more powerful barrier reduction capabilities.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize defense integration."""
        self.db = db

    def get_available_mechanisms(
        self,
        current_level: int,
    ) -> list[CatalystMechanism]:
        """
        Get catalyst mechanisms available at current defense level.

        Args:
            current_level: Current defense level (1-5)

        Returns:
            List of available catalyst mechanisms
        """
        mechanisms: list[CatalystMechanism] = []

        for level in range(1, current_level + 1):
            defense_catalyst = DEFENSE_CATALYST_MAPPING.get(level)
            if not defense_catalyst:
                continue

            for catalyst_id in defense_catalyst.catalysts_unlocked:
                mechanism = self._create_mechanism_for_level(
                    catalyst_id, level, defense_catalyst.barrier_reduction_bonus
                )
                if mechanism:
                    mechanisms.append(mechanism)

        return mechanisms

    def _create_mechanism_for_level(
        self,
        catalyst_id: str,
        level: int,
        bonus: float,
    ) -> Optional[CatalystMechanism]:
        """Create a catalyst mechanism for a specific defense level."""
        mechanism_configs = {
            "cross_training": {
                "name": "Cross-Training Program",
                "barriers": [BarrierType.STERIC],
                "reductions": {BarrierType.STERIC: 0.3 + bonus},
            },
            "workload_balancer": {
                "name": "Workload Balancer",
                "barriers": [BarrierType.THERMODYNAMIC],
                "reductions": {BarrierType.THERMODYNAMIC: 0.4 + bonus},
            },
            "auto_matcher": {
                "name": "Auto-Matcher",
                "barriers": [BarrierType.THERMODYNAMIC, BarrierType.ELECTRONIC],
                "reductions": {
                    BarrierType.THERMODYNAMIC: 0.5 + bonus,
                    BarrierType.ELECTRONIC: 0.3 + bonus,
                },
            },
            "preference_negotiation": {
                "name": "Preference Negotiation",
                "barriers": [BarrierType.THERMODYNAMIC],
                "reductions": {BarrierType.THERMODYNAMIC: 0.4 + bonus},
            },
            "backup_pool": {
                "name": "Backup Pool Activation",
                "barriers": [BarrierType.STERIC, BarrierType.THERMODYNAMIC],
                "reductions": {
                    BarrierType.STERIC: 0.6 + bonus,
                    BarrierType.THERMODYNAMIC: 0.4 + bonus,
                },
            },
            "emergency_override": {
                "name": "Emergency Override",
                "barriers": [BarrierType.KINETIC, BarrierType.ELECTRONIC],
                "reductions": {
                    BarrierType.KINETIC: 0.8 + bonus,
                    BarrierType.ELECTRONIC: 0.6 + bonus,
                },
            },
            "sacrifice_hierarchy": {
                "name": "Sacrifice Hierarchy",
                "barriers": [BarrierType.THERMODYNAMIC, BarrierType.KINETIC],
                "reductions": {
                    BarrierType.THERMODYNAMIC: 0.7 + bonus,
                    BarrierType.KINETIC: 0.5 + bonus,
                },
            },
            "service_reduction": {
                "name": "Service Reduction Protocol",
                "barriers": [BarrierType.THERMODYNAMIC],
                "reductions": {BarrierType.THERMODYNAMIC: 0.8 + bonus},
            },
            "external_escalation": {
                "name": "External Escalation",
                "barriers": [BarrierType.STERIC, BarrierType.ELECTRONIC],
                "reductions": {
                    BarrierType.STERIC: 0.9 + bonus,
                    BarrierType.ELECTRONIC: 0.9 + bonus,
                },
            },
            "crisis_mode": {
                "name": "Crisis Mode",
                "barriers": list(BarrierType),
                "reductions": {bt: 0.9 for bt in BarrierType},
            },
        }

        config = mechanism_configs.get(catalyst_id)
        if not config:
            return None

        return CatalystMechanism(
            mechanism_id=f"{catalyst_id}_level_{level}",
            name=config["name"],
            catalyst_type=CatalystType.HETEROGENEOUS,
            barriers_addressed=config["barriers"],
            reduction_factors={
                bt: min(0.95, r) for bt, r in config["reductions"].items()
            },
            requires_trigger=f"defense_level_{level}",
            is_active=True,
        )

    def calculate_system_activation_energy(
        self,
        coverage_rate: float,
    ) -> ActivationEnergy:
        """
        Calculate system-wide activation energy based on coverage.

        Lower coverage = higher activation energy for changes.

        Args:
            coverage_rate: Current coverage rate (0.0-1.0)

        Returns:
            System activation energy
        """
        # Higher coverage = lower barrier to changes
        base_energy = 1.0 - coverage_rate

        # Apply defense level adjustments
        level = self._coverage_to_level(coverage_rate)
        defense_catalyst = DEFENSE_CATALYST_MAPPING.get(level)
        bonus = defense_catalyst.barrier_reduction_bonus if defense_catalyst else 0.0

        effective_energy = max(0.0, base_energy - bonus)

        return ActivationEnergy(
            value=base_energy,
            catalyzed_value=effective_energy,
            catalyst_effect=bonus,
            components={BarrierType.THERMODYNAMIC: effective_energy},
        )

    def _coverage_to_level(self, coverage_rate: float) -> int:
        """Map coverage rate to defense level."""
        if coverage_rate >= 0.95:
            return 1
        elif coverage_rate >= 0.90:
            return 2
        elif coverage_rate >= 0.80:
            return 3
        elif coverage_rate >= 0.70:
            return 4
        else:
            return 5


class HubIntegration:
    """
    Integrates catalyst system with hub analysis.

    Hub faculty are identified as network catalysts based on their
    centrality metrics and unique service coverage.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize hub integration."""
        self.db = db

    def hub_to_catalyst(
        self,
        hub_metrics: HubMetricsProtocol,
        person_name: str = "Hub Faculty",
    ) -> CatalystPerson:
        """
        Convert hub metrics to a catalyst person.

        Args:
            hub_metrics: Hub analysis metrics
            person_name: Name of the person

        Returns:
            CatalystPerson with catalyst properties derived from hub metrics
        """
        # Calculate catalyst score from hub metrics
        # Higher centrality = better catalyst
        catalyst_score = min(1.0, (
            hub_metrics.composite_score * 0.5 +
            hub_metrics.degree_centrality * 0.3 +
            (1 - hub_metrics.betweenness_centrality) * 0.2  # Lower bottleneck = better
        ))

        # Determine barriers addressed based on unique services
        barriers = [BarrierType.THERMODYNAMIC]  # All hubs help with workload
        if hub_metrics.unique_services >= 2:
            barriers.append(BarrierType.STERIC)  # Can cover multiple services

        # Calculate reduction factors
        base_reduction = hub_metrics.composite_score * 0.8
        reduction_factors = {bt: base_reduction for bt in barriers}

        # Capacity based on current load (inverse of centrality)
        capacity = max(0.1, 1.0 - hub_metrics.betweenness_centrality)

        return CatalystPerson(
            person_id=hub_metrics.person_id,
            name=person_name,
            catalyst_type=CatalystType.HOMOGENEOUS,
            catalyst_score=catalyst_score,
            barriers_addressed=barriers,
            reduction_factors=reduction_factors,
            is_available=True,
            capacity_remaining=capacity,
        )

    def identify_catalyst_hubs(
        self,
        hub_metrics_list: list[HubMetricsProtocol],
        min_score: float = 0.5,
    ) -> list[CatalystPerson]:
        """
        Identify personnel who can act as network catalysts.

        Args:
            hub_metrics_list: List of hub metrics for all personnel
            min_score: Minimum composite score to be considered a catalyst

        Returns:
            List of personnel identified as catalysts
        """
        catalysts: list[CatalystPerson] = []

        for metrics in hub_metrics_list:
            if metrics.composite_score >= min_score:
                catalyst = self.hub_to_catalyst(metrics)
                catalysts.append(catalyst)

        # Sort by catalyst score (highest first)
        catalysts.sort(key=lambda c: c.catalyst_score, reverse=True)
        return catalysts

    def calculate_network_catalyst_capacity(
        self,
        hub_metrics_list: list[HubMetricsProtocol],
    ) -> dict[str, float]:
        """
        Calculate overall network catalyst capacity.

        Returns:
            Dictionary with capacity metrics
        """
        if not hub_metrics_list:
            return {
                "total_capacity": 0.0,
                "average_score": 0.0,
                "catalyst_count": 0,
                "bottleneck_risk": 1.0,
            }

        catalysts = self.identify_catalyst_hubs(hub_metrics_list)
        total_capacity = sum(c.capacity_remaining for c in catalysts)
        avg_score = sum(c.catalyst_score for c in catalysts) / len(catalysts) if catalysts else 0

        # Bottleneck risk based on unique service concentration
        unique_services = [m.unique_services for m in hub_metrics_list]
        max_unique = max(unique_services) if unique_services else 0
        bottleneck_risk = min(1.0, max_unique / 5)  # Risk increases with concentration

        return {
            "total_capacity": total_capacity,
            "average_score": avg_score,
            "catalyst_count": len(catalysts),
            "bottleneck_risk": bottleneck_risk,
        }


class SacrificeIntegration:
    """
    Integrates catalyst system with sacrifice hierarchy.

    The sacrifice hierarchy acts as a decision catalyst during crises,
    providing pre-made decisions that lower decision-making barriers.
    """

    # Activity priority order (from sacrifice_hierarchy.py)
    ACTIVITY_PRIORITY = [
        "PATIENT_SAFETY",
        "ACGME_REQUIREMENTS",
        "CONTINUITY_OF_CARE",
        "EDUCATION_CORE",
        "RESEARCH",
        "ADMINISTRATION",
        "EDUCATION_OPTIONAL",
    ]

    def __init__(self, db: AsyncSession) -> None:
        """Initialize sacrifice integration."""
        self.db = db

    def get_sacrifice_catalyst(
        self,
        utilization_rate: float,
    ) -> CatalystMechanism:
        """
        Get sacrifice hierarchy as a decision catalyst.

        Args:
            utilization_rate: Current system utilization (0.0-1.0)

        Returns:
            Catalyst mechanism representing sacrifice hierarchy
        """
        # Higher utilization = more aggressive sacrifice
        aggressiveness = max(0.0, (utilization_rate - 0.8) / 0.2)

        # Determine which activities can be sacrificed
        sacrificeable = self.ACTIVITY_PRIORITY[-(int(aggressiveness * 4) + 1):]

        reduction = 0.5 + aggressiveness * 0.4  # 0.5 to 0.9

        return CatalystMechanism(
            mechanism_id=f"sacrifice_hierarchy_{int(aggressiveness * 100)}",
            name="Sacrifice Hierarchy Decision Catalyst",
            catalyst_type=CatalystType.HETEROGENEOUS,
            barriers_addressed=[BarrierType.THERMODYNAMIC, BarrierType.KINETIC],
            reduction_factors={
                BarrierType.THERMODYNAMIC: reduction,
                BarrierType.KINETIC: reduction * 0.8,
            },
            requires_trigger="high_utilization",
            is_active=utilization_rate > 0.8,
        )

    def calculate_sacrifice_barrier_reduction(
        self,
        activity_type: str,
        proposed_change: dict[str, Any],
    ) -> float:
        """
        Calculate barrier reduction from sacrificing an activity.

        Lower priority activities provide more reduction.

        Args:
            activity_type: Type of activity being affected
            proposed_change: The proposed schedule change

        Returns:
            Barrier reduction factor (0.0-1.0)
        """
        try:
            priority_index = self.ACTIVITY_PRIORITY.index(activity_type)
        except ValueError:
            priority_index = len(self.ACTIVITY_PRIORITY) - 1

        # Lower priority = higher reduction
        max_index = len(self.ACTIVITY_PRIORITY) - 1
        reduction = priority_index / max_index if max_index > 0 else 0.0

        return reduction


class HomeostasisIntegration:
    """
    Integrates catalyst system with homeostasis framework.

    Feedback loops act as automatic catalysts that maintain
    system stability without external intervention.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize homeostasis integration."""
        self.db = db

    def get_feedback_catalysts(
        self,
        current_metrics: dict[str, float],
        target_metrics: dict[str, float],
    ) -> list[CatalystMechanism]:
        """
        Get feedback loop catalysts based on metric deviations.

        Args:
            current_metrics: Current system metrics
            target_metrics: Target/setpoint metrics

        Returns:
            List of feedback catalysts
        """
        catalysts: list[CatalystMechanism] = []

        for metric_name, current_value in current_metrics.items():
            target_value = target_metrics.get(metric_name, current_value)
            deviation = abs(current_value - target_value)

            if deviation > 0.1:  # Significant deviation
                catalyst = self._create_feedback_catalyst(
                    metric_name, current_value, target_value, deviation
                )
                catalysts.append(catalyst)

        return catalysts

    def _create_feedback_catalyst(
        self,
        metric_name: str,
        current: float,
        target: float,
        deviation: float,
    ) -> CatalystMechanism:
        """Create a feedback catalyst for a specific deviation."""
        direction = "increase" if current < target else "decrease"
        strength = min(0.9, deviation * 2)

        return CatalystMechanism(
            mechanism_id=f"feedback_{metric_name}_{direction}",
            name=f"Feedback Loop: {metric_name}",
            catalyst_type=CatalystType.AUTOCATALYTIC,
            barriers_addressed=[BarrierType.THERMODYNAMIC],
            reduction_factors={BarrierType.THERMODYNAMIC: strength},
            requires_trigger=f"{metric_name}_deviation",
            is_active=True,
        )

    def calculate_homeostatic_energy(
        self,
        current_state: dict[str, float],
        target_state: dict[str, float],
    ) -> ActivationEnergy:
        """
        Calculate activation energy for returning to homeostasis.

        Larger deviations = higher energy required.

        Args:
            current_state: Current system state
            target_state: Target homeostatic state

        Returns:
            Activation energy for restoration
        """
        if not current_state or not target_state:
            return ActivationEnergy(value=0.0)

        total_deviation = 0.0
        metric_count = 0

        for metric, current in current_state.items():
            target = target_state.get(metric)
            if target is not None:
                deviation = abs(current - target)
                total_deviation += deviation
                metric_count += 1

        avg_deviation = total_deviation / metric_count if metric_count > 0 else 0.0
        energy = min(1.0, avg_deviation)

        return ActivationEnergy(
            value=energy,
            components={BarrierType.THERMODYNAMIC: energy},
        )


class ResilienceFrameworkIntegration:
    """
    Unified integration with all resilience framework components.

    Provides a single interface for accessing catalyst capabilities
    across the entire resilience framework.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize unified integration."""
        self.db = db
        self.defense = DefenseIntegration(db)
        self.hub = HubIntegration(db)
        self.sacrifice = SacrificeIntegration(db)
        self.homeostasis = HomeostasisIntegration(db)

    async def get_all_available_catalysts(
        self,
        current_defense_level: int = 1,
        coverage_rate: float = 0.95,
        hub_metrics: Optional[list[HubMetricsProtocol]] = None,
    ) -> dict[str, list[CatalystPerson | CatalystMechanism]]:
        """
        Get all available catalysts from all framework components.

        Args:
            current_defense_level: Current defense level
            coverage_rate: Current coverage rate
            hub_metrics: Optional hub analysis metrics

        Returns:
            Dictionary with catalysts organized by source
        """
        result: dict[str, list[CatalystPerson | CatalystMechanism]] = {
            "defense_mechanisms": [],
            "hub_personnel": [],
            "sacrifice_mechanisms": [],
            "feedback_mechanisms": [],
        }

        # Defense mechanisms
        result["defense_mechanisms"] = self.defense.get_available_mechanisms(
            current_defense_level
        )

        # Hub personnel
        if hub_metrics:
            result["hub_personnel"] = self.hub.identify_catalyst_hubs(hub_metrics)

        # Sacrifice mechanisms
        utilization = 1.0 - coverage_rate
        result["sacrifice_mechanisms"] = [
            self.sacrifice.get_sacrifice_catalyst(utilization)
        ]

        # Feedback mechanisms (placeholder metrics)
        result["feedback_mechanisms"] = self.homeostasis.get_feedback_catalysts(
            {"coverage": coverage_rate},
            {"coverage": 0.95},
        )

        return result

    async def calculate_system_catalyst_capacity(
        self,
        hub_metrics: Optional[list[HubMetricsProtocol]] = None,
    ) -> dict[str, Any]:
        """
        Calculate overall system catalyst capacity.

        Returns:
            Dictionary with capacity metrics
        """
        # Hub capacity
        hub_capacity = self.hub.calculate_network_catalyst_capacity(
            hub_metrics or []
        )

        # Defense level capacity
        defense_levels = list(DEFENSE_CATALYST_MAPPING.values())
        max_mechanisms = sum(len(d.catalysts_unlocked) for d in defense_levels)

        return {
            "hub_capacity": hub_capacity,
            "defense_mechanisms_available": max_mechanisms,
            "total_catalyst_types": len(CatalystType),
            "barrier_types_covered": len(BarrierType),
        }
