"""
Core types and data structures for multi-objective optimization.

This module defines the fundamental building blocks used throughout the
multi-objective framework, including objectives, solutions, dominance
relations, and the Pareto frontier.

Classes:
    - ObjectiveDirection: Minimize or maximize
    - ObjectiveType: Scheduling, resilience, preference, constraint
    - ObjectiveConfig: Configuration for a single objective
    - Solution: A candidate solution with objective values
    - DominanceRelation: Pareto dominance between solutions
    - ParetoFrontier: Collection of non-dominated solutions
    - SolutionArchive: Archive of solutions with bounded size

Multi-Objective Lens - Pareto Optimality:
    A solution x Pareto-dominates solution y if:
    1. x is at least as good as y in all objectives
    2. x is strictly better than y in at least one objective

    The Pareto frontier (or Pareto front) is the set of all non-dominated
    solutions. No solution on the frontier can improve one objective without
    degrading another - they represent fundamental trade-offs.

    In scheduling:
    - Moving along the frontier means accepting trade-offs
    - Points far from the frontier are suboptimal (can improve without cost)
    - The "knee" of the frontier often represents balanced solutions
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Iterator
from uuid import UUID, uuid4

import numpy as np


class ObjectiveDirection(Enum):
    """Direction of optimization for an objective."""

    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class ObjectiveType(Enum):
    """Type of objective for categorization and visualization."""

    # Core scheduling objectives
    COVERAGE = "coverage"
    EQUITY = "equity"
    PREFERENCE = "preference"
    CONTINUITY = "continuity"
    WORKLOAD_BALANCE = "workload_balance"

    # Resilience objectives
    RESILIENCE = "resilience"
    HUB_PROTECTION = "hub_protection"
    BUFFER_CAPACITY = "buffer_capacity"
    ZONE_ISOLATION = "zone_isolation"

    # Compliance objectives
    ACGME_COMPLIANCE = "acgme_compliance"
    SUPERVISION = "supervision"
    DUTY_HOURS = "duty_hours"

    # Call-related objectives
    CALL_EQUITY = "call_equity"
    CALL_SPACING = "call_spacing"

    # Custom/composite objectives
    CUSTOM = "custom"
    COMPOSITE = "composite"


@dataclass
class ObjectiveConfig:
    """
    Configuration for a single optimization objective.

    Attributes:
        name: Unique identifier for the objective
        display_name: Human-readable name
        description: Detailed description for decision makers
        direction: Minimize or maximize
        objective_type: Category of objective
        weight: Default weight for scalarization (0.0 to 1.0)
        reference_point: Ideal value for this objective (for normalization)
        nadir_point: Worst acceptable value (for normalization)
        epsilon: Tolerance for epsilon-dominance
        is_constraint: If True, treated as a constraint rather than objective
        constraint_threshold: Threshold if this is a constraint objective
    """

    name: str
    display_name: str
    description: str
    direction: ObjectiveDirection
    objective_type: ObjectiveType
    weight: float = 1.0
    reference_point: float | None = None
    nadir_point: float | None = None
    epsilon: float = 0.0
    is_constraint: bool = False
    constraint_threshold: float | None = None

    def normalize(self, value: float) -> float:
        """
        Normalize objective value to [0, 1] range.

        Uses reference point (ideal) and nadir point (worst) for scaling.
        Result: 0 = at ideal (reference_point), 1 = at worst (nadir_point)

        For minimization: reference_point < nadir_point (e.g., 0.0 ideal, 1.0 worst)
        For maximization: reference_point > nadir_point (e.g., 1.0 ideal, 0.0 worst)
        """
        if self.reference_point is None or self.nadir_point is None:
            return value

        range_val = abs(self.nadir_point - self.reference_point)
        if range_val == 0:
            return 0.5

        # Normalize to 0 = ideal (reference), 1 = worst (nadir)
        return abs(value - self.reference_point) / range_val

    def denormalize(self, normalized: float) -> float:
        """Convert normalized value back to original scale."""
        if self.reference_point is None or self.nadir_point is None:
            return normalized

        range_val = abs(self.nadir_point - self.reference_point)

        if self.direction == ObjectiveDirection.MINIMIZE:
            return self.reference_point + normalized * range_val
        else:
            return self.nadir_point - normalized * range_val


class DominanceRelation(Enum):
    """Pareto dominance relationship between two solutions."""

    DOMINATES = "dominates"  # First solution dominates second
    DOMINATED = "dominated"  # First solution is dominated by second
    INCOMPARABLE = "incomparable"  # Neither dominates the other
    EQUAL = "equal"  # Solutions are equal in all objectives


@dataclass
class Solution:
    """
    A candidate solution in multi-objective optimization.

    Represents a complete assignment with its objective values, constraint
    violations, and metadata for archive management and visualization.

    Attributes:
        id: Unique identifier
        decision_variables: The actual solution (assignments, etc.)
        objective_values: Dictionary of objective name to value
        normalized_objectives: Normalized values for comparison
        constraint_violations: List of violated constraints
        total_constraint_violation: Aggregate violation magnitude
        is_feasible: Whether all hard constraints are satisfied
        crowding_distance: Distance metric for diversity
        rank: Non-domination rank (0 = Pareto frontier)
        generation: Generation when solution was created
        parent_ids: IDs of parent solutions (for genealogy)
        metadata: Additional solution information
        created_at: Timestamp of creation
    """

    id: UUID = field(default_factory=uuid4)
    decision_variables: dict[str, Any] = field(default_factory=dict)
    objective_values: dict[str, float] = field(default_factory=dict)
    normalized_objectives: dict[str, float] = field(default_factory=dict)
    constraint_violations: list[str] = field(default_factory=list)
    total_constraint_violation: float = 0.0
    is_feasible: bool = True
    crowding_distance: float = float("inf")
    rank: int = 0
    generation: int = 0
    parent_ids: list[UUID] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def get_objective_vector(self, objective_names: list[str]) -> np.ndarray:
        """Get objective values as numpy array in specified order."""
        return np.array([self.objective_values.get(name, 0.0) for name in objective_names])

    def get_normalized_vector(self, objective_names: list[str]) -> np.ndarray:
        """Get normalized objective values as numpy array."""
        return np.array(
            [self.normalized_objectives.get(name, 0.0) for name in objective_names]
        )

    def copy(self) -> "Solution":
        """Create a deep copy of this solution."""
        return Solution(
            id=uuid4(),
            decision_variables=dict(self.decision_variables),
            objective_values=dict(self.objective_values),
            normalized_objectives=dict(self.normalized_objectives),
            constraint_violations=list(self.constraint_violations),
            total_constraint_violation=self.total_constraint_violation,
            is_feasible=self.is_feasible,
            crowding_distance=self.crowding_distance,
            rank=self.rank,
            generation=self.generation,
            parent_ids=[self.id],
            metadata=dict(self.metadata),
        )


def compare_dominance(
    sol1: Solution,
    sol2: Solution,
    objectives: list[ObjectiveConfig],
    consider_constraints: bool = True,
) -> DominanceRelation:
    """
    Compare Pareto dominance between two solutions.

    Args:
        sol1: First solution
        sol2: Second solution
        objectives: List of objective configurations
        consider_constraints: If True, feasible solutions dominate infeasible

    Returns:
        DominanceRelation indicating the relationship
    """
    # Feasibility-first comparison
    if consider_constraints:
        if sol1.is_feasible and not sol2.is_feasible:
            return DominanceRelation.DOMINATES
        if not sol1.is_feasible and sol2.is_feasible:
            return DominanceRelation.DOMINATED
        if not sol1.is_feasible and not sol2.is_feasible:
            # Compare by constraint violation
            if sol1.total_constraint_violation < sol2.total_constraint_violation:
                return DominanceRelation.DOMINATES
            if sol1.total_constraint_violation > sol2.total_constraint_violation:
                return DominanceRelation.DOMINATED

    # Pareto dominance comparison
    better_count = 0
    worse_count = 0
    equal_count = 0

    for obj in objectives:
        if obj.is_constraint:
            continue

        val1 = sol1.objective_values.get(obj.name, 0.0)
        val2 = sol2.objective_values.get(obj.name, 0.0)

        if obj.direction == ObjectiveDirection.MAXIMIZE:
            # Higher is better
            if val1 > val2 + obj.epsilon:
                better_count += 1
            elif val2 > val1 + obj.epsilon:
                worse_count += 1
            else:
                equal_count += 1
        else:
            # Lower is better
            if val1 < val2 - obj.epsilon:
                better_count += 1
            elif val2 < val1 - obj.epsilon:
                worse_count += 1
            else:
                equal_count += 1

    if worse_count == 0 and better_count > 0:
        return DominanceRelation.DOMINATES
    if better_count == 0 and worse_count > 0:
        return DominanceRelation.DOMINATED
    if equal_count == len([o for o in objectives if not o.is_constraint]):
        return DominanceRelation.EQUAL
    return DominanceRelation.INCOMPARABLE


@dataclass
class ParetoFrontier:
    """
    Collection of non-dominated solutions forming the Pareto frontier.

    The Pareto frontier represents the set of optimal trade-offs between
    competing objectives. Each solution on the frontier cannot improve
    one objective without degrading another.

    Attributes:
        solutions: List of non-dominated solutions
        objectives: Configuration of objectives
        reference_point: Reference point for hypervolume calculation
        ideal_point: Best value observed for each objective
        nadir_point: Worst value on the frontier for each objective
        generation: Generation when frontier was computed
    """

    solutions: list[Solution] = field(default_factory=list)
    objectives: list[ObjectiveConfig] = field(default_factory=list)
    reference_point: np.ndarray | None = None
    ideal_point: np.ndarray | None = None
    nadir_point: np.ndarray | None = None
    generation: int = 0

    def add(self, solution: Solution) -> bool:
        """
        Add a solution to the frontier if it's non-dominated.

        Returns True if the solution was added (and dominated solutions removed).
        Returns False if the solution was dominated.
        """
        dominated_by_new = []

        for i, existing in enumerate(self.solutions):
            relation = compare_dominance(solution, existing, self.objectives)

            if relation == DominanceRelation.DOMINATED:
                return False  # New solution is dominated
            elif relation == DominanceRelation.DOMINATES:
                dominated_by_new.append(i)
            elif relation == DominanceRelation.EQUAL:
                return False  # Duplicate

        # Remove dominated solutions
        for i in reversed(dominated_by_new):
            self.solutions.pop(i)

        self.solutions.append(solution)
        self._update_bounds()
        return True

    def _update_bounds(self) -> None:
        """Update ideal and nadir points based on current solutions."""
        if not self.solutions:
            self.ideal_point = None
            self.nadir_point = None
            return

        objective_names = [o.name for o in self.objectives if not o.is_constraint]
        n_objectives = len(objective_names)

        ideal = np.zeros(n_objectives)
        nadir = np.zeros(n_objectives)

        for i, obj in enumerate(self.objectives):
            if obj.is_constraint:
                continue

            values = [s.objective_values.get(obj.name, 0.0) for s in self.solutions]

            if obj.direction == ObjectiveDirection.MINIMIZE:
                ideal[i] = min(values)
                nadir[i] = max(values)
            else:
                ideal[i] = max(values)
                nadir[i] = min(values)

        self.ideal_point = ideal
        self.nadir_point = nadir

    def get_extreme_solutions(self) -> list[Solution]:
        """Get solutions that are extreme in at least one objective."""
        if not self.solutions:
            return []

        extreme = set()
        objective_names = [o.name for o in self.objectives if not o.is_constraint]

        for i, obj in enumerate(self.objectives):
            if obj.is_constraint:
                continue

            values = [(s.objective_values.get(obj.name, 0.0), j) for j, s in enumerate(self.solutions)]

            if obj.direction == ObjectiveDirection.MINIMIZE:
                best_idx = min(values, key=lambda x: x[0])[1]
            else:
                best_idx = max(values, key=lambda x: x[0])[1]

            extreme.add(best_idx)

        return [self.solutions[i] for i in extreme]

    def get_knee_solution(self) -> Solution | None:
        """
        Find the "knee" solution - the point with maximum trade-off curvature.

        The knee represents a balanced solution where small improvements in one
        objective require large sacrifices in others.
        """
        if len(self.solutions) < 3:
            return self.solutions[0] if self.solutions else None

        objective_names = [o.name for o in self.objectives if not o.is_constraint]

        # Normalize all solutions
        normalized = []
        for sol in self.solutions:
            vec = []
            for obj in self.objectives:
                if obj.is_constraint:
                    continue
                val = sol.objective_values.get(obj.name, 0.0)
                vec.append(obj.normalize(val))
            normalized.append(np.array(vec))

        # Find solution with maximum distance from the line connecting extremes
        # This is a simplified knee detection using the trade-off curve approach
        max_distance = 0
        knee_idx = 0

        # Calculate centroid
        centroid = np.mean(normalized, axis=0)

        for i, norm_vec in enumerate(normalized):
            # Distance from centroid (approximation of knee)
            distance = np.linalg.norm(norm_vec - centroid)
            if distance > max_distance:
                max_distance = distance
                knee_idx = i

        return self.solutions[knee_idx]

    def __len__(self) -> int:
        return len(self.solutions)

    def __iter__(self) -> Iterator[Solution]:
        return iter(self.solutions)

    def __getitem__(self, idx: int) -> Solution:
        return self.solutions[idx]


@dataclass
class SolutionArchive:
    """
    Bounded archive of solutions with automatic pruning.

    Maintains a fixed-size collection of solutions, removing least diverse
    or most dominated solutions when capacity is exceeded.

    Attributes:
        max_size: Maximum number of solutions to store
        solutions: List of archived solutions
        objectives: Configuration of objectives
        pruning_method: How to select solutions for removal
    """

    max_size: int = 100
    solutions: list[Solution] = field(default_factory=list)
    objectives: list[ObjectiveConfig] = field(default_factory=list)
    pruning_method: str = "crowding"  # "crowding", "random", "age"

    def add(self, solution: Solution) -> bool:
        """
        Add a solution to the archive.

        Returns True if added, False if rejected (dominated or archive full
        and solution has low diversity).
        """
        # Check if dominated by any existing solution
        for existing in self.solutions:
            relation = compare_dominance(solution, existing, self.objectives)
            if relation == DominanceRelation.DOMINATED or relation == DominanceRelation.EQUAL:
                return False

        # Remove solutions dominated by the new one
        self.solutions = [
            s
            for s in self.solutions
            if compare_dominance(solution, s, self.objectives)
            != DominanceRelation.DOMINATES
        ]

        self.solutions.append(solution)

        # Prune if over capacity
        while len(self.solutions) > self.max_size:
            self._prune_one()

        return True

    def _prune_one(self) -> None:
        """Remove one solution based on pruning method."""
        if not self.solutions:
            return

        if self.pruning_method == "crowding":
            self._update_crowding_distances()
            # Remove solution with minimum crowding distance
            min_idx = min(range(len(self.solutions)), key=lambda i: self.solutions[i].crowding_distance)
            self.solutions.pop(min_idx)

        elif self.pruning_method == "age":
            # Remove oldest solution
            oldest_idx = min(range(len(self.solutions)), key=lambda i: self.solutions[i].created_at)
            self.solutions.pop(oldest_idx)

        else:  # random
            import random

            self.solutions.pop(random.randrange(len(self.solutions)))

    def _update_crowding_distances(self) -> None:
        """Calculate crowding distance for all solutions."""
        if len(self.solutions) <= 2:
            for sol in self.solutions:
                sol.crowding_distance = float("inf")
            return

        n = len(self.solutions)
        objective_names = [o.name for o in self.objectives if not o.is_constraint]

        # Reset distances
        for sol in self.solutions:
            sol.crowding_distance = 0.0

        for obj in self.objectives:
            if obj.is_constraint:
                continue

            # Sort by this objective
            sorted_indices = sorted(
                range(n), key=lambda i: self.solutions[i].objective_values.get(obj.name, 0.0)
            )

            # Boundary solutions get infinite distance
            self.solutions[sorted_indices[0]].crowding_distance = float("inf")
            self.solutions[sorted_indices[-1]].crowding_distance = float("inf")

            # Calculate objective range
            min_val = self.solutions[sorted_indices[0]].objective_values.get(obj.name, 0.0)
            max_val = self.solutions[sorted_indices[-1]].objective_values.get(obj.name, 0.0)
            obj_range = max_val - min_val

            if obj_range == 0:
                continue

            # Calculate crowding for intermediate solutions
            for i in range(1, n - 1):
                idx = sorted_indices[i]
                prev_val = self.solutions[sorted_indices[i - 1]].objective_values.get(
                    obj.name, 0.0
                )
                next_val = self.solutions[sorted_indices[i + 1]].objective_values.get(
                    obj.name, 0.0
                )
                self.solutions[idx].crowding_distance += (next_val - prev_val) / obj_range

    def get_frontier(self) -> ParetoFrontier:
        """Extract the Pareto frontier from the archive."""
        frontier = ParetoFrontier(objectives=self.objectives)
        for solution in self.solutions:
            frontier.add(solution)
        return frontier

    def __len__(self) -> int:
        return len(self.solutions)

    def __iter__(self) -> Iterator[Solution]:
        return iter(self.solutions)


# Common objective configurations for scheduling
SCHEDULING_OBJECTIVES = [
    ObjectiveConfig(
        name="coverage",
        display_name="Coverage",
        description="Percentage of blocks with assigned coverage",
        direction=ObjectiveDirection.MAXIMIZE,
        objective_type=ObjectiveType.COVERAGE,
        weight=1.0,
        reference_point=1.0,  # 100% coverage
        nadir_point=0.0,  # 0% coverage
    ),
    ObjectiveConfig(
        name="equity",
        display_name="Assignment Equity",
        description="Fairness of assignment distribution (Gini coefficient)",
        direction=ObjectiveDirection.MINIMIZE,
        objective_type=ObjectiveType.EQUITY,
        weight=0.8,
        reference_point=0.0,  # Perfect equity
        nadir_point=1.0,  # Complete inequity
    ),
    ObjectiveConfig(
        name="preference_satisfaction",
        display_name="Preference Satisfaction",
        description="Degree to which staff preferences are respected",
        direction=ObjectiveDirection.MAXIMIZE,
        objective_type=ObjectiveType.PREFERENCE,
        weight=0.6,
        reference_point=1.0,  # All preferences satisfied
        nadir_point=0.0,  # No preferences satisfied
    ),
    ObjectiveConfig(
        name="resilience",
        display_name="Resilience Score",
        description="System resilience to staff absence and emergencies",
        direction=ObjectiveDirection.MAXIMIZE,
        objective_type=ObjectiveType.RESILIENCE,
        weight=0.7,
        reference_point=1.0,  # Fully resilient
        nadir_point=0.0,  # No resilience
    ),
    ObjectiveConfig(
        name="call_equity",
        display_name="Call Equity",
        description="Fair distribution of call duties",
        direction=ObjectiveDirection.MINIMIZE,
        objective_type=ObjectiveType.CALL_EQUITY,
        weight=0.5,
        reference_point=0.0,  # Perfect call equity
        nadir_point=1.0,  # Complete inequity
    ),
]
