"""
N-2 Contingency Analysis.

Based on power grid N-2 standards: "System must remain stable after any two concurrent component failures."

For scheduling: Can schedule survive simultaneous loss of any two residents/faculty?

N-2 failures are more severe than N-1:
- Lower probability but catastrophic impact
- Often reveals hidden interdependencies
- Tests true system resilience
"""

import logging
from dataclasses import dataclass
from datetime import date
from itertools import combinations
from typing import Optional

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class N2FailureScenario:
    """Two-component concurrent failure scenario."""

    component1_id: str
    component2_id: str
    component_type: str  # "person", "specialty", "rotation"
    failure_date: date
    affected_slots: int
    cascade_probability: float  # Probability of total cascade (0-1)
    recovery_time_hours: float
    criticality_score: float  # 0-1, higher = more critical
    backup_available: bool
    backup_ids: list[str]
    mitigation_strategy: str
    interdependency_type: str  # "independent", "correlated", "coupled"


class N2Analyzer:
    """
    Analyze N-2 contingency scenarios.

    More sophisticated than N-1:
    - Examines combinatorial failures
    - Detects correlated failures (common cause)
    - Identifies coupled systems
    - Calculates cascade probabilities
    """

    def __init__(self):
        """Initialize N-2 analyzer."""
        self.scenarios: list[N2FailureScenario] = []

    def analyze_dual_person_failure(
        self,
        person1_id: str,
        person2_id: str,
        person1_slots: list[tuple[date, str]],
        person2_slots: list[tuple[date, str]],
        available_backups: list[str],
        backup_capacity: dict[str, int],
        correlation: float = 0.0,  # 0-1, correlation between failures
    ) -> N2FailureScenario:
        """
        Analyze impact of losing two people simultaneously.

        Args:
            person1_id: First person
            person2_id: Second person
            person1_slots: Person 1 assignments
            person2_slots: Person 2 assignments
            available_backups: Available backup personnel
            backup_capacity: Capacity for each backup
            correlation: Failure correlation (0=independent, 1=fully correlated)

        Returns:
            N2FailureScenario with impact analysis
        """
        logger.info("Analyzing N-2 dual failure: %s and %s (correlation: %.2f)", person1_id, person2_id, correlation)
        total_affected = len(person1_slots) + len(person2_slots)

        # Check for overlapping assignments (increases severity)
        overlap = self._find_slot_overlap(person1_slots, person2_slots)
        if overlap:
            logger.warning("N-2 scenario has %d overlapping slots - increased severity", len(overlap))
            total_affected += len(overlap) * 2  # Double penalty for overlap

        # Determine interdependency type
        if correlation > 0.7:
            interdependency = "coupled"  # Failures likely to occur together
        elif correlation > 0.3:
            interdependency = "correlated"  # Some connection
        else:
            interdependency = "independent"

        logger.debug("Interdependency type: %s, total affected slots: %d", interdependency, total_affected)

        # Check backup coverage
        viable_backups = []
        for backup_id in available_backups:
            capacity = backup_capacity.get(backup_id, 0)
            if capacity >= total_affected:
                viable_backups.append(backup_id)

        has_backup = len(viable_backups) > 0

        if not has_backup:
            logger.error("CRITICAL: N-2 scenario with no viable backups for %d affected slots", total_affected)

        # Calculate criticality (N-2 is inherently more critical)
        base_criticality = 0.6  # N-2 starts higher than N-1
        if total_affected > 20:
            criticality = min(1.0, base_criticality + 0.4)
        elif has_backup:
            criticality = base_criticality
        else:
            criticality = min(1.0, base_criticality + total_affected / 50.0)

        # Add correlation penalty
        criticality = min(1.0, criticality + correlation * 0.2)

        # Cascade probability - much higher for N-2
        if has_backup:
            cascade_prob = 0.2 + correlation * 0.3
        else:
            cascade_prob = 0.5 + correlation * 0.4

        # Recovery time
        if has_backup:
            recovery_hours = total_affected * 0.5  # Parallel recovery
        else:
            recovery_hours = total_affected * 6.0  # Serial recovery

        # Mitigation strategy
        if has_backup:
            mitigation = f"Activate {len(viable_backups)} backup personnel"
        elif interdependency == "coupled":
            mitigation = "EMERGENCY: Activate mutual aid agreement with other programs"
        else:
            mitigation = "Activate emergency staffing + reduce non-critical services"

        failure_date = person1_slots[0][0] if person1_slots else date.today()

        scenario = N2FailureScenario(
            component1_id=person1_id,
            component2_id=person2_id,
            component_type="person",
            failure_date=failure_date,
            affected_slots=total_affected,
            cascade_probability=cascade_prob,
            recovery_time_hours=recovery_hours,
            criticality_score=criticality,
            backup_available=has_backup,
            backup_ids=viable_backups,
            mitigation_strategy=mitigation,
            interdependency_type=interdependency,
        )

        self.scenarios.append(scenario)
        return scenario

    def analyze_all_n2_combinations(
        self,
        personnel: list[str],
        assignments: dict[str, list[tuple[date, str]]],
        available_backups: list[str],
        backup_capacity: dict[str, int],
        max_combinations: int = 100,
    ) -> list[N2FailureScenario]:
        """
        Analyze all possible N-2 failure combinations.

        Warning: Combinatorially expensive! For n personnel, generates C(n,2) = n(n-1)/2 scenarios.

        Args:
            personnel: List of person IDs
            assignments: Map of person_id -> list of assignments
            available_backups: Available backup personnel
            backup_capacity: Capacity for each backup
            max_combinations: Maximum number of combinations to analyze

        Returns:
            List of N2 failure scenarios, sorted by criticality
        """
        scenarios = []

        # Generate all 2-combinations
        for person1, person2 in combinations(personnel, 2):
            if len(scenarios) >= max_combinations:
                break

            person1_slots = assignments.get(person1, [])
            person2_slots = assignments.get(person2, [])

            # Skip if both have no assignments
            if not person1_slots and not person2_slots:
                continue

            # Estimate correlation based on assignment overlap
            correlation = self._estimate_correlation(person1_slots, person2_slots)

            scenario = self.analyze_dual_person_failure(
                person1_id=person1,
                person2_id=person2,
                person1_slots=person1_slots,
                person2_slots=person2_slots,
                available_backups=available_backups,
                backup_capacity=backup_capacity,
                correlation=correlation,
            )

            scenarios.append(scenario)

        # Sort by criticality
        scenarios.sort(key=lambda s: s.criticality_score, reverse=True)
        return scenarios

    def _find_slot_overlap(
        self,
        slots1: list[tuple[date, str]],
        slots2: list[tuple[date, str]],
    ) -> list[tuple[date, str]]:
        """Find overlapping slots between two people."""
        set1 = set(slots1)
        set2 = set(slots2)
        return list(set1.intersection(set2))

    def _estimate_correlation(
        self,
        slots1: list[tuple[date, str]],
        slots2: list[tuple[date, str]],
    ) -> float:
        """
        Estimate correlation between two personnel.

        Based on:
        - Assignment overlap
        - Similar rotations
        - Same specialty
        """
        if not slots1 or not slots2:
            return 0.0

        # Calculate Jaccard similarity of rotations
        rotations1 = set(rot for _, rot in slots1)
        rotations2 = set(rot for _, rot in slots2)

        intersection = len(rotations1.intersection(rotations2))
        union = len(rotations1.union(rotations2))

        if union == 0:
            return 0.0

        similarity = intersection / union

        # Correlation is similarity (0-1)
        return min(1.0, similarity)

    def find_catastrophic_n2_scenarios(
        self,
        min_criticality: float = 0.85,
    ) -> list[N2FailureScenario]:
        """
        Find catastrophic N-2 scenarios.

        These are scenarios where:
        - Criticality >= min_criticality
        - No backup available OR
        - High cascade probability

        Args:
            min_criticality: Minimum criticality threshold

        Returns:
            List of catastrophic scenarios
        """
        catastrophic = []

        for scenario in self.scenarios:
            is_catastrophic = (
                scenario.criticality_score >= min_criticality
                or (not scenario.backup_available and scenario.criticality_score >= 0.7)
                or scenario.cascade_probability >= 0.7
            )

            if is_catastrophic:
                catastrophic.append(scenario)

        return sorted(catastrophic, key=lambda s: s.criticality_score, reverse=True)

    def calculate_n2_resilience_score(self) -> float:
        """
        Calculate overall N-2 resilience score.

        Score = 1.0 - (weighted average of N-2 criticalities)

        Returns:
            Resilience score (0-1, higher is better)
        """
        if not self.scenarios:
            return 1.0  # Perfect score if no scenarios analyzed

        # Weight by cascade probability
        weighted_sum = sum(
            s.criticality_score * (1.0 + s.cascade_probability) for s in self.scenarios
        )
        total_weight = sum(1.0 + s.cascade_probability for s in self.scenarios)

        avg_criticality = weighted_sum / total_weight if total_weight > 0 else 0.0

        return max(0.0, 1.0 - avg_criticality)

    def identify_common_cause_failures(
        self,
        correlation_threshold: float = 0.7,
    ) -> list[tuple[str, str, float]]:
        """
        Identify pairs with common cause failure risk.

        Common cause: Two components likely to fail together
        (e.g., both deployed, both sick, same specialty shortage)

        Args:
            correlation_threshold: Minimum correlation for common cause

        Returns:
            List of (component1, component2, correlation) tuples
        """
        common_cause = []

        for scenario in self.scenarios:
            if scenario.interdependency_type == "coupled":
                # Estimate correlation from cascade probability
                correlation = scenario.cascade_probability
                if correlation >= correlation_threshold:
                    common_cause.append(
                        (scenario.component1_id, scenario.component2_id, correlation)
                    )

        return common_cause

    def build_n2_vulnerability_matrix(
        self,
        personnel: list[str],
    ) -> dict[tuple[str, str], float]:
        """
        Build N-2 vulnerability matrix.

        Returns dict mapping (person1, person2) -> criticality score

        Args:
            personnel: List of person IDs

        Returns:
            Dict of {(person1, person2): criticality}
        """
        matrix = {}

        for scenario in self.scenarios:
            key = (scenario.component1_id, scenario.component2_id)
            matrix[key] = scenario.criticality_score

        return matrix

    def get_summary(self) -> dict:
        """Get N-2 analysis summary."""
        if not self.scenarios:
            return {
                "total_scenarios": 0,
                "catastrophic_scenarios": 0,
                "avg_criticality": 0.0,
                "resilience_score": 1.0,
                "coupled_pairs": 0,
            }

        catastrophic = self.find_catastrophic_n2_scenarios()
        coupled_scenarios = [
            s for s in self.scenarios if s.interdependency_type == "coupled"
        ]
        resilience_score = self.calculate_n2_resilience_score()

        avg_criticality = sum(s.criticality_score for s in self.scenarios) / len(
            self.scenarios
        )

        return {
            "total_scenarios": len(self.scenarios),
            "catastrophic_scenarios": len(catastrophic),
            "avg_criticality": round(avg_criticality, 2),
            "resilience_score": round(resilience_score, 2),
            "coupled_pairs": len(coupled_scenarios),
            "scenarios_without_backup": sum(
                1 for s in self.scenarios if not s.backup_available
            ),
            "high_cascade_risk": sum(
                1 for s in self.scenarios if s.cascade_probability >= 0.7
            ),
        }
