"""
MOEA/D: Multi-Objective Evolutionary Algorithm based on Decomposition.

This module implements MOEA/D, which decomposes a multi-objective optimization
problem into a set of scalar subproblems and optimizes them simultaneously.

Key Concepts:
    - Weight vectors define directions in objective space
    - Each weight vector corresponds to a subproblem
    - Neighboring subproblems share information
    - Decomposition converts MOO to single-objective optimization

Decomposition Methods:
    - Weighted Sum: Simple linear combination of objectives
    - Tchebycheff: Minimize maximum weighted deviation from ideal point
    - Penalty Boundary Intersection (PBI): Combines distance and diversity

Multi-Objective Lens - Decomposition:
    MOEA/D recognizes that different regions of the Pareto front represent
    different trade-off preferences. By assigning weight vectors to subproblems,
    MOEA/D ensures uniform coverage of the entire frontier.

    Advantages over NSGA-II:
    - Better scalability to many objectives (>3)
    - More uniform distribution of solutions
    - Explicit control over search direction
    - Natural parallelization via subproblems

Classes:
    - WeightVector: Defines a direction in objective space
    - DecompositionMethod: Strategy for scalarizing objectives
    - MOEADAlgorithm: Main algorithm implementation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, cast
from uuid import UUID

import numpy as np

from .core import (
    DominanceRelation,
    ObjectiveConfig,
    ObjectiveDirection,
    ParetoFrontier,
    Solution,
    SolutionArchive,
    compare_dominance,
)


class DecompositionType(Enum):
    """Type of decomposition approach for scalarization."""

    WEIGHTED_SUM = "weighted_sum"
    TCHEBYCHEFF = "tchebycheff"
    PBI = "pbi"  # Penalty Boundary Intersection
    INVERTED_PBI = "inverted_pbi"
    WEIGHTED_NORM = "weighted_norm"


@dataclass
class WeightVector:
    """
    A weight vector defining a direction in objective space.

    Each weight vector corresponds to a subproblem in MOEA/D. The weights
    define the relative importance of objectives for that subproblem.

    Attributes:
        id: Unique identifier
        weights: Array of weights (one per objective)
        neighbors: Indices of neighboring weight vectors
        current_solution: Best solution found for this subproblem
        subproblem_value: Current scalarized objective value
    """

    id: int
    weights: np.ndarray
    neighbors: list[int] = field(default_factory=list)
    current_solution: Solution | None = None
    subproblem_value: float = float("inf")

    def __post_init__(self) -> None:
        """Normalize weights to sum to 1."""
        total = np.sum(self.weights)
        if total > 0:
            self.weights = self.weights / total


class DecompositionMethod(ABC):
    """
    Abstract base class for decomposition methods.

    A decomposition method converts a multi-objective problem into
    a single scalar value based on a weight vector.
    """

    @abstractmethod
    def scalarize(
        self,
        objective_values: np.ndarray,
        weight: np.ndarray,
        reference_point: np.ndarray,
        **kwargs: Any,
    ) -> float:
        """
        Convert multi-objective values to a single scalar.

        Args:
            objective_values: Array of objective values (minimization form)
            weight: Weight vector for this subproblem
            reference_point: Ideal/reference point (best values)
            **kwargs: Additional method-specific parameters

        Returns:
            Scalar value to minimize
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the decomposition method."""
        pass


class WeightedSumDecomposition(DecompositionMethod):
    """
    Weighted sum decomposition.

    f(x) = sum(w_i * f_i(x))

    Simple and efficient, but cannot find solutions in non-convex
    regions of the Pareto front.
    """

    def scalarize(
        self,
        objective_values: np.ndarray,
        weight: np.ndarray,
        reference_point: np.ndarray,
        **kwargs: Any,
    ) -> float:
        """Weighted sum of objective values."""
        return float(np.sum(weight * objective_values))

    @property
    def name(self) -> str:
        return "weighted_sum"


class TchebycheffDecomposition(DecompositionMethod):
    """
    Tchebycheff decomposition.

    f(x) = max(w_i * |f_i(x) - z_i*|)

    Can find solutions in non-convex regions. The reference point z*
    should be the ideal point (best values for each objective).
    """

    def scalarize(
        self,
        objective_values: np.ndarray,
        weight: np.ndarray,
        reference_point: np.ndarray,
        **kwargs: Any,
    ) -> float:
        """Maximum weighted deviation from reference point."""
        # Avoid zero weights causing division issues
        safe_weight = np.maximum(weight, 1e-10)
        deviations = safe_weight * np.abs(objective_values - reference_point)
        return float(np.max(deviations))

    @property
    def name(self) -> str:
        return "tchebycheff"


class PBIDecomposition(DecompositionMethod):
    """
    Penalty Boundary Intersection (PBI) decomposition.

    f(x) = d1 + theta * d2

    Where:
    - d1: Distance along the weight vector direction
    - d2: Perpendicular distance from weight vector
    - theta: Penalty parameter (default 5.0)

    Balances convergence (d1) and diversity (d2).
    """

    def __init__(self, theta: float = 5.0) -> None:
        """
        Initialize PBI decomposition.

        Args:
            theta: Penalty parameter for diversity term (default 5.0)
        """
        self.theta = theta

    def scalarize(
        self,
        objective_values: np.ndarray,
        weight: np.ndarray,
        reference_point: np.ndarray,
        **kwargs: Any,
    ) -> float:
        """PBI scalarization with convergence and diversity terms."""
        # Vector from reference point to solution
        diff = objective_values - reference_point

        # Normalize weight vector
        weight_norm = np.linalg.norm(weight)
        if weight_norm == 0:
            return float(np.linalg.norm(diff))

        unit_weight = weight / weight_norm

        # d1: projection onto weight direction (convergence)
        d1 = float(np.dot(diff, unit_weight))

        # d2: perpendicular distance (diversity)
        d2 = float(np.linalg.norm(diff - d1 * unit_weight))

        return d1 + self.theta * d2

    @property
    def name(self) -> str:
        return f"pbi_theta{self.theta}"


class WeightedNormDecomposition(DecompositionMethod):
    """
    Weighted Lp norm decomposition.

    f(x) = (sum(w_i * |f_i(x) - z_i*|^p))^(1/p)

    p=1: Weighted sum
    p=2: Weighted Euclidean distance
    p=inf: Tchebycheff
    """

    def __init__(self, p: float = 2.0) -> None:
        """
        Initialize weighted norm decomposition.

        Args:
            p: Norm parameter (default 2.0 for Euclidean)
        """
        self.p = p

    def scalarize(
        self,
        objective_values: np.ndarray,
        weight: np.ndarray,
        reference_point: np.ndarray,
        **kwargs: Any,
    ) -> float:
        """Weighted Lp norm from reference point."""
        deviations = np.abs(objective_values - reference_point)
        weighted = weight * (deviations**self.p)
        return float(np.sum(weighted) ** (1.0 / self.p))

    @property
    def name(self) -> str:
        return f"weighted_l{self.p}_norm"


def generate_weight_vectors(
    n_objectives: int,
    n_vectors: int,
    method: str = "uniform",
) -> list[np.ndarray]:
    """
    Generate uniformly distributed weight vectors.

    Args:
        n_objectives: Number of objectives
        n_vectors: Desired number of weight vectors
        method: Generation method ("uniform", "simplex", "random")

    Returns:
        List of weight vectors (each sums to 1)
    """
    if method == "simplex":
        return _simplex_lattice_design(n_objectives, n_vectors)
    elif method == "random":
        # Random points on simplex
        weights = np.random.dirichlet(np.ones(n_objectives), n_vectors)
        return [w for w in weights]
    else:  # uniform
        return _uniform_weight_design(n_objectives, n_vectors)


def _uniform_weight_design(n_objectives: int, n_vectors: int) -> list[np.ndarray]:
    """Generate uniformly distributed weights using simplex-lattice design."""
    if n_objectives == 2:
        # Simple case: evenly spaced on line
        weights = []
        for i in range(n_vectors):
            w1 = i / max(n_vectors - 1, 1)
            weights.append(np.array([w1, 1 - w1]))
        return weights

        # General case: Das and Dennis method
        # Approximate divisions per axis
    H = 1
    while _n_combinations(H + n_objectives - 1, n_objectives - 1) < n_vectors:
        H += 1

    return _simplex_lattice_design(n_objectives, H)


def _simplex_lattice_design(n_objectives: int, H: int) -> list[np.ndarray]:
    """
    Generate simplex-lattice design for weight vectors.

    H is the number of divisions on each axis.
    """
    weights = []

    def generate_recursive(current: list[float], remaining: int, depth: int) -> None:
        if depth == n_objectives - 1:
            current.append(remaining / H)
            weights.append(np.array(current.copy()))
            current.pop()
            return

        for i in range(remaining + 1):
            current.append(i / H)
            generate_recursive(current, remaining - i, depth + 1)
            current.pop()

    generate_recursive([], H, 0)
    return weights


def _n_combinations(n: int, k: int) -> int:
    """Calculate n choose k."""
    if k > n:
        return 0
    if k == 0 or k == n:
        return 1

    from math import factorial

    return factorial(n) // (factorial(k) * factorial(n - k))


@dataclass
class MOEADConfig:
    """Configuration for MOEA/D algorithm."""

    n_weight_vectors: int = 100
    n_neighbors: int = 20
    decomposition: DecompositionMethod = field(default_factory=TchebycheffDecomposition)
    weight_method: str = "uniform"
    delta: float = 0.9  # Probability to select from neighborhood
    nr: int = 2  # Maximum replacement number
    max_generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.9


class MOEADAlgorithm:
    """
    MOEA/D: Multi-Objective Evolutionary Algorithm based on Decomposition.

    This algorithm decomposes the multi-objective problem into subproblems,
    each defined by a weight vector. Solutions from neighboring subproblems
    are used to generate new candidates, promoting both convergence and
    diversity across the Pareto front.

    Usage:
        # Configure objectives
        objectives = [coverage_obj, equity_obj, resilience_obj]

        # Create algorithm
        moead = MOEADAlgorithm(
            objectives=objectives,
            config=MOEADConfig(n_weight_vectors=100)
        )

        # Run optimization
        archive = moead.optimize(
            initial_solutions=seed_solutions,
            evaluate=evaluate_schedule,
            mutate=mutate_schedule,
            crossover=crossover_schedules
        )
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        config: MOEADConfig | None = None,
    ) -> None:
        """
        Initialize MOEA/D algorithm.

        Args:
            objectives: List of objective configurations
            config: Algorithm configuration (uses defaults if not provided)
        """
        self.objectives = objectives
        self.config = config or MOEADConfig()

        # Filter to actual objectives (not constraints)
        self.active_objectives = [o for o in objectives if not o.is_constraint]
        self.n_objectives = len(self.active_objectives)

        # Initialize weight vectors
        self.weight_vectors: list[WeightVector] = []
        self._initialize_weights()

        # Reference point (ideal values)
        self.reference_point = np.zeros(self.n_objectives)

        # External archive
        self.archive = SolutionArchive(
            max_size=self.config.n_weight_vectors * 2,
            objectives=objectives,
        )

        # Statistics
        self.generation = 0
        self.evaluations = 0

    def _initialize_weights(self) -> None:
        """Initialize weight vectors and neighborhoods."""
        # Generate weight vectors
        raw_weights = generate_weight_vectors(
            self.n_objectives,
            self.config.n_weight_vectors,
            self.config.weight_method,
        )

        # Create WeightVector objects
        self.weight_vectors = [
            WeightVector(id=i, weights=w) for i, w in enumerate(raw_weights)
        ]

        # Compute neighborhoods based on Euclidean distance
        n = len(self.weight_vectors)
        distances = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(
                    self.weight_vectors[i].weights - self.weight_vectors[j].weights
                )
                distances[i, j] = dist
                distances[j, i] = dist

                # Assign neighbors (T closest vectors)
        T = min(self.config.n_neighbors, n - 1)
        for i in range(n):
            # Get indices sorted by distance
            neighbor_indices = np.argsort(distances[i])
            # Skip self (distance 0)
            self.weight_vectors[i].neighbors = neighbor_indices[1 : T + 1].tolist()

    def optimize(
        self,
        initial_solutions: list[Solution],
        evaluate: Callable[[Solution], Solution],
        mutate: Callable[[Solution], Solution],
        crossover: Callable[[Solution, Solution], Solution],
        progress_callback: Callable[[int, SolutionArchive], None] | None = None,
    ) -> SolutionArchive:
        """
        Run MOEA/D optimization.

        Args:
            initial_solutions: Seed solutions to start with
            evaluate: Function to evaluate a solution (fills objective values)
            mutate: Function to mutate a solution
            crossover: Function to cross two solutions
            progress_callback: Optional callback called each generation

        Returns:
            Archive of non-dominated solutions
        """
        # Initialize population from initial solutions
        self._initialize_population(initial_solutions, evaluate)

        # Main evolution loop
        for gen in range(self.config.max_generations):
            self.generation = gen

            # Evolve each subproblem
            for wv in self.weight_vectors:
                # Select parents
                if np.random.random() < self.config.delta:
                    # Select from neighborhood
                    parent_pool = [
                        self.weight_vectors[i].current_solution
                        for i in wv.neighbors
                        if self.weight_vectors[i].current_solution is not None
                    ]
                else:
                    # Select from entire population
                    parent_pool = [
                        w.current_solution
                        for w in self.weight_vectors
                        if w.current_solution is not None
                    ]

                if len(parent_pool) < 2:
                    continue

                    # Generate offspring
                parents = np.random.choice(len(parent_pool), 2, replace=False)
                parent1 = parent_pool[parents[0]]
                parent2 = parent_pool[parents[1]]

                # Crossover
                if np.random.random() < self.config.crossover_rate:
                    offspring = crossover(parent1, parent2)
                else:
                    offspring = parent1.copy()

                    # Mutation
                if np.random.random() < self.config.mutation_rate:
                    offspring = mutate(offspring)

                    # Evaluate
                offspring = evaluate(offspring)
                offspring.generation = gen
                self.evaluations += 1

                # Update reference point
                self._update_reference_point(offspring)

                # Update neighbors
                self._update_neighbors(wv, offspring)

                # Update archive
                self.archive.add(offspring)

            if progress_callback:
                progress_callback(gen, self.archive)

        return self.archive

    def _initialize_population(
        self,
        initial_solutions: list[Solution],
        evaluate: Callable[[Solution], Solution],
    ) -> None:
        """Initialize population for each subproblem."""
        # Evaluate initial solutions if needed
        evaluated = []
        for sol in initial_solutions:
            if not sol.objective_values:
                sol = evaluate(sol)
                self.evaluations += 1
            evaluated.append(sol)

            # Update reference point
        for sol in evaluated:
            self._update_reference_point(sol)

            # Assign solutions to weight vectors
            # Use simple distance-based assignment
        for sol in evaluated:
            obj_vec = self._get_normalized_objectives(sol)

            best_wv = None
            best_value = float("inf")

            for wv in self.weight_vectors:
                value = self.config.decomposition.scalarize(
                    obj_vec, wv.weights, self.reference_point
                )
                if value < best_value:
                    best_value = value
                    best_wv = wv

            if best_wv is not None:
                if best_wv.current_solution is None or value < best_wv.subproblem_value:
                    best_wv.current_solution = sol
                    best_wv.subproblem_value = value

                    # Add to archive
            self.archive.add(sol)

            # Fill remaining weight vectors with random copies
        if evaluated:
            for wv in self.weight_vectors:
                if wv.current_solution is None:
                    wv.current_solution = cast(
                        Solution, np.random.choice(evaluated)
                    ).copy()
                    obj_vec = self._get_normalized_objectives(wv.current_solution)
                    wv.subproblem_value = self.config.decomposition.scalarize(
                        obj_vec, wv.weights, self.reference_point
                    )

    def _get_normalized_objectives(self, solution: Solution) -> np.ndarray:
        """Get normalized objective values (for minimization)."""
        values = []
        for obj in self.active_objectives:
            val = solution.objective_values.get(obj.name, 0.0)

            # Convert to minimization form
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                val = -val

            values.append(val)

        return np.array(values)

    def _update_reference_point(self, solution: Solution) -> None:
        """Update reference point with new solution."""
        obj_vec = self._get_normalized_objectives(solution)

        for i, val in enumerate(obj_vec):
            if val < self.reference_point[i]:
                self.reference_point[i] = val

    def _update_neighbors(self, wv: WeightVector, offspring: Solution) -> None:
        """Update neighboring subproblems with offspring if it's better."""
        obj_vec = self._get_normalized_objectives(offspring)
        offspring_value = self.config.decomposition.scalarize(
            obj_vec, wv.weights, self.reference_point
        )

        # Count replacements
        replacements = 0

        # Try to update neighbors
        neighbor_indices = (
            wv.neighbors
            if np.random.random() < self.config.delta
            else list(range(len(self.weight_vectors)))
        )

        for idx in neighbor_indices:
            if replacements >= self.config.nr:
                break

            neighbor = self.weight_vectors[idx]
            neighbor_value = self.config.decomposition.scalarize(
                obj_vec, neighbor.weights, self.reference_point
            )

            if neighbor_value < neighbor.subproblem_value:
                neighbor.current_solution = offspring.copy()
                neighbor.subproblem_value = neighbor_value
                replacements += 1

    def get_pareto_frontier(self) -> ParetoFrontier:
        """Get the current Pareto frontier from the archive."""
        return self.archive.get_frontier()

    def get_solutions_by_objective(
        self, objective_name: str, top_k: int = 10
    ) -> list[Solution]:
        """Get top solutions for a specific objective."""
        obj = next(
            (o for o in self.active_objectives if o.name == objective_name), None
        )
        if obj is None:
            return []

        solutions = list(self.archive.solutions)
        reverse = obj.direction == ObjectiveDirection.MAXIMIZE

        solutions.sort(
            key=lambda s: s.objective_values.get(objective_name, 0.0),
            reverse=reverse,
        )

        return solutions[:top_k]

    def get_balanced_solutions(self, top_k: int = 10) -> list[Solution]:
        """Get solutions that are balanced across all objectives."""
        # Calculate normalized scores for each solution
        scored = []
        for sol in self.archive.solutions:
            obj_vec = self._get_normalized_objectives(sol)
            # Use distance from ideal as balance metric
            distance = np.linalg.norm(obj_vec - self.reference_point)
            scored.append((distance, sol))

        scored.sort(key=lambda x: x[0])
        return [sol for _, sol in scored[:top_k]]

        # Convenience functions for common decomposition methods


def create_weighted_sum_moead(
    objectives: list[ObjectiveConfig],
    n_weight_vectors: int = 100,
    **kwargs: Any,
) -> MOEADAlgorithm:
    """Create MOEA/D with weighted sum decomposition."""
    config = MOEADConfig(
        n_weight_vectors=n_weight_vectors,
        decomposition=WeightedSumDecomposition(),
        **kwargs,
    )
    return MOEADAlgorithm(objectives, config)


def create_tchebycheff_moead(
    objectives: list[ObjectiveConfig],
    n_weight_vectors: int = 100,
    **kwargs: Any,
) -> MOEADAlgorithm:
    """Create MOEA/D with Tchebycheff decomposition."""
    config = MOEADConfig(
        n_weight_vectors=n_weight_vectors,
        decomposition=TchebycheffDecomposition(),
        **kwargs,
    )
    return MOEADAlgorithm(objectives, config)


def create_pbi_moead(
    objectives: list[ObjectiveConfig],
    n_weight_vectors: int = 100,
    theta: float = 5.0,
    **kwargs: Any,
) -> MOEADAlgorithm:
    """Create MOEA/D with PBI decomposition."""
    config = MOEADConfig(
        n_weight_vectors=n_weight_vectors,
        decomposition=PBIDecomposition(theta=theta),
        **kwargs,
    )
    return MOEADAlgorithm(objectives, config)
