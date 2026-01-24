"""
N-1 Contingency Analysis.

Based on NERC (North American Electric Reliability Corporation) power grid standards:
"The system must remain stable after any single component failure."

For scheduling: Can schedule survive loss of any single resident/faculty?

Detects:
- Single points of failure (SPOF)
- Critical resources
- Coverage vulnerabilities
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

import networkx as nx


@dataclass
class N1FailureScenario:
    """Single-component failure scenario."""

    component_id: str  # Person ID or rotation ID
    component_type: str  # "person", "rotation", "specialty"
    failure_date: date
    affected_slots: int  # Number of slots that become uncovered
    cascade_potential: float  # Probability this triggers cascading failures (0-1)
    recovery_time_hours: float  # Estimated hours to recover
    criticality_score: float  # Overall criticality (0-1)
    backup_available: bool
    backup_ids: list[str]  # Available backup resources
    mitigation_strategy: str


class N1Analyzer:
    """
    Analyze N-1 contingency scenarios.

    Identifies:
    1. Single points of failure (SPOF)
    2. Critical paths in coverage graph
    3. Cascade potential
    4. Backup availability
    """

    def __init__(self) -> None:
        """Initialize N-1 analyzer."""
        self.scenarios: list[N1FailureScenario] = []

    def analyze_person_failure(
        self,
        person_id: str,
        assigned_slots: list[tuple[date, str]],  # (date, rotation_id)
        available_backups: list[str],
        backup_capacity: dict[str, int],  # backup_id -> available slots
    ) -> N1FailureScenario:
        """
        Analyze impact of losing a single person.

        Args:
            person_id: Person to analyze
            assigned_slots: Their current assignments
            available_backups: Potential backup personnel
            backup_capacity: Available capacity for each backup

        Returns:
            N1FailureScenario with impact analysis
        """
        num_affected = len(assigned_slots)

        # Check backup coverage
        viable_backups = []
        for backup_id in available_backups:
            capacity = backup_capacity.get(backup_id, 0)
            if capacity >= num_affected:
                viable_backups.append(backup_id)

        has_backup = len(viable_backups) > 0

        # Calculate criticality
        if num_affected == 0:
            criticality = 0.0
        elif has_backup:
            # Low criticality if backups available
            criticality = min(0.5, num_affected / 20.0)
        else:
            # High criticality if no backups
            criticality = min(1.0, 0.5 + num_affected / 10.0)

        # Estimate recovery time
        if has_backup:
            recovery_hours = 2.0  # Quick swap
        else:
            recovery_hours = num_affected * 4.0  # Need to find coverage

        # Cascade potential - higher if no backups
        cascade_potential = 0.0 if has_backup else min(0.8, num_affected / 15.0)

        # Determine mitigation strategy
        if has_backup:
            mitigation = f"Activate backup: {viable_backups[0]}"
        elif num_affected < 5:
            mitigation = "Distribute shifts among existing staff"
        else:
            mitigation = "Activate emergency staffing protocol"

        # Use first slot date as failure date
        failure_date = assigned_slots[0][0] if assigned_slots else date.today()

        scenario = N1FailureScenario(
            component_id=person_id,
            component_type="person",
            failure_date=failure_date,
            affected_slots=num_affected,
            cascade_potential=cascade_potential,
            recovery_time_hours=recovery_hours,
            criticality_score=criticality,
            backup_available=has_backup,
            backup_ids=viable_backups,
            mitigation_strategy=mitigation,
        )

        self.scenarios.append(scenario)
        return scenario

    def analyze_specialty_failure(
        self,
        specialty: str,
        required_slots: int,
        available_specialists: list[str],
        cross_trained: list[str],  # Personnel cross-trained in this specialty
    ) -> N1FailureScenario:
        """
        Analyze impact of losing a specialty capability.

        Args:
            specialty: Specialty to analyze (e.g., "ultrasound", "intubation")
            required_slots: Number of slots requiring this specialty
            available_specialists: Current specialists
            cross_trained: Cross-trained personnel who can cover

        Returns:
            N1FailureScenario for specialty loss
        """
        # If only one specialist, losing them is critical
        has_backup = len(available_specialists) > 1 or len(cross_trained) > 0

        if len(available_specialists) == 1:
            criticality = 0.9  # Single point of failure
            cascade_potential = 0.7
        elif len(available_specialists) == 2:
            criticality = 0.6  # Limited redundancy
            cascade_potential = 0.4
        else:
            criticality = 0.3  # Multiple specialists
            cascade_potential = 0.1

        recovery_hours = required_slots * 2.0 if has_backup else required_slots * 8.0

        if has_backup:
            mitigation = f"Activate cross-trained personnel: {cross_trained}"
        else:
            mitigation = "Request external coverage from other programs"

        scenario = N1FailureScenario(
            component_id=specialty,
            component_type="specialty",
            failure_date=date.today(),
            affected_slots=required_slots,
            cascade_potential=cascade_potential,
            recovery_time_hours=recovery_hours,
            criticality_score=criticality,
            backup_available=has_backup,
            backup_ids=cross_trained,
            mitigation_strategy=mitigation,
        )

        self.scenarios.append(scenario)
        return scenario

    def find_single_points_of_failure(
        self,
        min_criticality: float = 0.7,
    ) -> list[N1FailureScenario]:
        """
        Find single points of failure (SPOF).

        Args:
            min_criticality: Minimum criticality score to qualify as SPOF

        Returns:
            List of critical N1 scenarios
        """
        return [s for s in self.scenarios if s.criticality_score >= min_criticality]

    def build_dependency_graph(
        self,
        assignments: list[tuple[str, date, str]],  # (person_id, date, rotation_id)
    ) -> nx.DiGraph:
        """
        Build dependency graph for N-1 analysis.

        Nodes: persons, rotations, dates
        Edges: assignment dependencies

        Args:
            assignments: List of (person, date, rotation) tuples

        Returns:
            NetworkX directed graph
        """
        G = nx.DiGraph()

        for person_id, assignment_date, rotation_id in assignments:
            # Add nodes
            G.add_node(person_id, node_type="person")
            G.add_node(rotation_id, node_type="rotation")
            G.add_node(str(assignment_date), node_type="date")

            # Add edges: person -> date -> rotation
            G.add_edge(person_id, str(assignment_date))
            G.add_edge(str(assignment_date), rotation_id)

        return G

    def identify_critical_paths(self, graph: nx.DiGraph) -> list[list[str]]:
        """
        Identify critical paths in dependency graph.

        Critical path: path with no alternative routes (bridge)

        Args:
            graph: Dependency graph

        Returns:
            List of critical path node sequences
        """
        critical_paths = []

        # Find bridges (edges whose removal disconnects graph)
        bridges = list(nx.bridges(graph.to_undirected()))

        for bridge in bridges:
            # Find all paths containing this bridge
            source, target = bridge
            try:
                paths = nx.all_simple_paths(graph, source, target, cutoff=10)
                for path in paths:
                    if len(path) > 2:  # Non-trivial path
                        critical_paths.append(path)
            except nx.NetworkXNoPath:
                continue

        return critical_paths

    def calculate_redundancy_score(
        self,
        person_id: str,
        assignments: list[tuple[date, str]],
        available_backups: int,
    ) -> float:
        """
        Calculate redundancy score for a person.

        Score = available_backups / required_backups
        where required_backups = ceil(assignments / 10)

        Args:
            person_id: Person to analyze
            assignments: Their assignments
            available_backups: Number of available backup personnel

        Returns:
            Redundancy score (0-1+, higher is better)
        """
        num_assignments = len(assignments)
        if num_assignments == 0:
            return 1.0  # Perfect redundancy (not needed)

        # Estimate required backups (1 per 10 shifts)
        required_backups = max(1, num_assignments // 10)

        redundancy = available_backups / required_backups
        return min(1.0, redundancy)

    def get_summary(self) -> dict:
        """Get summary statistics."""
        if not self.scenarios:
            return {
                "total_scenarios": 0,
                "critical_scenarios": 0,
                "avg_criticality": 0.0,
                "spof_count": 0,
            }

        critical_scenarios = [s for s in self.scenarios if s.criticality_score >= 0.7]
        spof_scenarios = [
            s
            for s in self.scenarios
            if s.criticality_score >= 0.9 and not s.backup_available
        ]

        avg_criticality = sum(s.criticality_score for s in self.scenarios) / len(
            self.scenarios
        )

        return {
            "total_scenarios": len(self.scenarios),
            "critical_scenarios": len(critical_scenarios),
            "avg_criticality": round(avg_criticality, 2),
            "spof_count": len(spof_scenarios),
            "scenarios_without_backup": sum(
                1 for s in self.scenarios if not s.backup_available
            ),
        }
