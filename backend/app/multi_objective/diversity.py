"""
Diversity Preservation Mechanisms for Multi-Objective Optimization.

This module provides mechanisms to maintain diversity in the population
during multi-objective optimization, ensuring good coverage of the
Pareto front.

Diversity Mechanisms:
    1. Crowding Distance: NSGA-II style distance metric
    2. Epsilon-Dominance: Grid-based diversity maintenance
    3. Niching: Similarity-based fitness sharing
    4. Reference Points: NSGA-III style association

Multi-Objective Lens - Why Diversity Matters:
    In multi-objective optimization, we want solutions that:
    - Cover the entire Pareto front (not just one region)
    - Are evenly distributed (no clusters or gaps)
    - Include extreme solutions (boundaries of the front)

    Without diversity preservation:
    - Evolution converges to a small region
    - Decision maker has limited choices
    - Trade-off understanding is incomplete

    In scheduling:
    - Need solutions emphasizing different objectives
    - Coverage of entire feasible trade-off space
    - Options for different operational priorities

Classes:
    - CrowdingDistance: NSGA-II crowding metric
    - EpsilonDominance: Grid-based archiving
    - NichingOperator: Fitness sharing mechanism
    - ReferencePointAssociation: NSGA-III style diversity
    - DiversityMechanism: Combined diversity management
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from .core import (
    DominanceRelation,
    ObjectiveConfig,
    ObjectiveDirection,
    ParetoFrontier,
    Solution,
    compare_dominance,
)


class DiversityMetric(Enum):
    """Types of diversity metrics."""

    CROWDING_DISTANCE = "crowding_distance"
    EPSILON_GRID = "epsilon_grid"
    NICHING = "niching"
    REFERENCE_POINT = "reference_point"


@dataclass
class DiversityStats:
    """Statistics about population diversity."""

    metric_type: DiversityMetric
    mean_distance: float
    min_distance: float
    max_distance: float
    uniformity: float  # 0-1, higher is more uniform
    coverage: float  # 0-1, how much of objective space is covered
    cluster_count: int  # Number of distinct clusters


class CrowdingDistance:
    """
    Crowding Distance Calculator (NSGA-II style).

    Crowding distance measures the density of solutions around a point.
    Solutions with larger crowding distance are in less crowded regions
    and are preferred for diversity.

    For each solution, crowding distance is the sum of the normalized
    distances to neighbors in each objective dimension.
    """

    def __init__(self, objectives: list[ObjectiveConfig]) -> None:
        """
        Initialize crowding distance calculator.

        Args:
            objectives: List of objective configurations
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]

    def calculate(self, solutions: list[Solution]) -> None:
        """
        Calculate crowding distance for all solutions.

        Updates the crowding_distance attribute of each solution in-place.

        Args:
            solutions: List of solutions to calculate distances for
        """
        n = len(solutions)
        if n <= 2:
            for sol in solutions:
                sol.crowding_distance = float("inf")
            return

            # Reset distances
        for sol in solutions:
            sol.crowding_distance = 0.0

            # Calculate for each objective
        for obj in self.active_objectives:
            # Sort by this objective
            sorted_solutions = sorted(
                solutions,
                key=lambda s: s.objective_values.get(obj.name, 0.0),
            )

            # Boundary solutions get infinite distance
            sorted_solutions[0].crowding_distance = float("inf")
            sorted_solutions[-1].crowding_distance = float("inf")

            # Calculate objective range
            min_val = sorted_solutions[0].objective_values.get(obj.name, 0.0)
            max_val = sorted_solutions[-1].objective_values.get(obj.name, 0.0)
            obj_range = max_val - min_val

            if obj_range == 0:
                continue

                # Calculate crowding for intermediate solutions
            for i in range(1, n - 1):
                prev_val = sorted_solutions[i - 1].objective_values.get(obj.name, 0.0)
                next_val = sorted_solutions[i + 1].objective_values.get(obj.name, 0.0)

                sorted_solutions[i].crowding_distance += (
                    next_val - prev_val
                ) / obj_range

    def select_by_crowding(
        self,
        solutions: list[Solution],
        n: int,
    ) -> list[Solution]:
        """
        Select n solutions with highest crowding distance.

        Args:
            solutions: Pool of solutions
            n: Number to select

        Returns:
            Selected solutions
        """
        self.calculate(solutions)
        sorted_solutions = sorted(
            solutions, key=lambda s: s.crowding_distance, reverse=True
        )
        return sorted_solutions[:n]

    def tournament_select(
        self,
        solutions: list[Solution],
        tournament_size: int = 2,
    ) -> Solution:
        """
        Select a solution using binary tournament with crowding distance.

        Args:
            solutions: Pool of solutions
            tournament_size: Number of solutions in tournament

        Returns:
            Selected solution
        """
        import random

        tournament = random.sample(solutions, min(tournament_size, len(solutions)))

        # First compare by rank, then by crowding distance
        tournament.sort(key=lambda s: (s.rank, -s.crowding_distance))
        return tournament[0]


class EpsilonDominance:
    """
    Epsilon-Dominance for grid-based archiving.

    Epsilon-dominance relaxes the dominance relation to maintain
    well-distributed solutions. Solutions are mapped to a grid in
    objective space, and only one solution per grid cell is kept.

    Benefits:
    - Guaranteed diversity (minimum spacing between solutions)
    - Bounded archive size
    - Convergence guarantees
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        epsilon: float | dict[str, float] | None = None,
    ) -> None:
        """
        Initialize epsilon-dominance.

        Args:
            objectives: List of objective configurations
            epsilon: Grid cell size (single value or per-objective dict)
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]

        # Set epsilon values
        if epsilon is None:
            self.epsilon = {o.name: 0.01 for o in self.active_objectives}
        elif isinstance(epsilon, dict):
            self.epsilon = epsilon
        else:
            self.epsilon = {o.name: epsilon for o in self.active_objectives}

    def get_grid_location(self, solution: Solution) -> tuple[int, ...]:
        """
        Get the grid cell location for a solution.

        Args:
            solution: Solution to locate

        Returns:
            Tuple of grid indices for each objective
        """
        location = []
        for obj in self.active_objectives:
            val = solution.objective_values.get(obj.name, 0.0)
            eps = self.epsilon.get(obj.name, 0.01)

            # Handle direction
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                val = -val

            cell = int(val / eps)
            location.append(cell)

        return tuple(location)

    def epsilon_dominates(self, sol_a: Solution, sol_b: Solution) -> bool:
        """
        Check if sol_a epsilon-dominates sol_b.

        A solution epsilon-dominates another if its grid location
        dominates the other's grid location.

        Args:
            sol_a: First solution
            sol_b: Second solution

        Returns:
            True if sol_a epsilon-dominates sol_b
        """
        loc_a = self.get_grid_location(sol_a)
        loc_b = self.get_grid_location(sol_b)

        better_or_equal = all(a <= b for a, b in zip(loc_a, loc_b))
        strictly_better = any(a < b for a, b in zip(loc_a, loc_b))

        return better_or_equal and strictly_better

    def update_archive(
        self,
        archive: list[Solution],
        new_solution: Solution,
    ) -> list[Solution]:
        """
        Update archive with a new solution using epsilon-dominance.

        Args:
            archive: Current archive
            new_solution: Solution to potentially add

        Returns:
            Updated archive
        """
        # Check if new solution is epsilon-dominated
        for sol in archive:
            if self.epsilon_dominates(sol, new_solution):
                return archive  # Reject new solution

                # Remove solutions epsilon-dominated by new solution
        updated = [
            sol for sol in archive if not self.epsilon_dominates(new_solution, sol)
        ]

        # Check grid cell conflict
        new_location = self.get_grid_location(new_solution)
        cell_conflict = None

        for i, sol in enumerate(updated):
            if self.get_grid_location(sol) == new_location:
                cell_conflict = i
                break

        if cell_conflict is not None:
            # Keep the one closer to grid corner (better)
            existing = updated[cell_conflict]
            if self._is_closer_to_corner(new_solution, existing):
                updated[cell_conflict] = new_solution
        else:
            updated.append(new_solution)

        return updated

    def _is_closer_to_corner(self, sol_a: Solution, sol_b: Solution) -> bool:
        """Check if sol_a is closer to the grid corner than sol_b."""
        dist_a = 0.0
        dist_b = 0.0

        for obj in self.active_objectives:
            val_a = sol_a.objective_values.get(obj.name, 0.0)
            val_b = sol_b.objective_values.get(obj.name, 0.0)
            eps = self.epsilon.get(obj.name, 0.01)

            # Handle direction
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                val_a = -val_a
                val_b = -val_b

                # Distance from grid corner
            cell_a = int(val_a / eps)
            cell_b = int(val_b / eps)

            dist_a += abs(val_a - cell_a * eps)
            dist_b += abs(val_b - cell_b * eps)

        return dist_a < dist_b

    def prune_archive(
        self,
        archive: list[Solution],
        max_size: int,
    ) -> list[Solution]:
        """
        Prune archive to maximum size using epsilon-dominance.

        Args:
            archive: Current archive
            max_size: Maximum allowed size

        Returns:
            Pruned archive
        """
        if len(archive) <= max_size:
            return archive

            # Increase epsilon until archive fits
        current_archive = list(archive)
        scale = 1.0

        while len(current_archive) > max_size:
            scale *= 1.1
            scaled_epsilon = {k: v * scale for k, v in self.epsilon.items()}

            # Rebuild archive with larger epsilon
            new_archive: list[Solution] = []
            for sol in archive:
                new_archive = self._update_with_scaled_epsilon(
                    new_archive, sol, scaled_epsilon
                )

            current_archive = new_archive

        return current_archive

    def _update_with_scaled_epsilon(
        self,
        archive: list[Solution],
        solution: Solution,
        epsilon: dict[str, float],
    ) -> list[Solution]:
        """Update archive with scaled epsilon values."""
        # Temporary epsilon dominance with scaled values
        temp_eps = EpsilonDominance(self.objectives, epsilon)
        return temp_eps.update_archive(archive, solution)


class NichingOperator:
    """
    Niching through fitness sharing.

    Solutions in the same niche (similar region of objective space)
    share fitness, reducing the selection probability of crowded regions.
    This encourages exploration of less-crowded areas.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        niche_radius: float = 0.1,
        alpha: float = 1.0,
    ) -> None:
        """
        Initialize niching operator.

        Args:
            objectives: List of objective configurations
            niche_radius: Radius defining a niche (normalized space)
            alpha: Sharing function exponent
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]
        self.niche_radius = niche_radius
        self.alpha = alpha

    def calculate_niche_count(self, solutions: list[Solution]) -> dict[str, float]:
        """
        Calculate niche count for each solution.

        Niche count is the sum of sharing function values with all other
        solutions. Higher niche count = more crowded region.

        Args:
            solutions: List of solutions

        Returns:
            Dictionary mapping solution ID to niche count
        """
        n = len(solutions)
        niche_counts = {}

        for i, sol_i in enumerate(solutions):
            count = 0.0
            for j, sol_j in enumerate(solutions):
                if i != j:
                    distance = self._normalized_distance(sol_i, sol_j)
                    count += self._sharing_function(distance)

            niche_counts[str(sol_i.id)] = count

        return niche_counts

    def _normalized_distance(self, sol_a: Solution, sol_b: Solution) -> float:
        """Calculate normalized Euclidean distance between solutions."""
        dist = 0.0
        for obj in self.active_objectives:
            val_a = sol_a.objective_values.get(obj.name, 0.0)
            val_b = sol_b.objective_values.get(obj.name, 0.0)

            # Normalize if possible
            if obj.reference_point is not None and obj.nadir_point is not None:
                val_a = obj.normalize(val_a)
                val_b = obj.normalize(val_b)

            dist += (val_a - val_b) ** 2

        return float(np.sqrt(dist))

    def _sharing_function(self, distance: float) -> float:
        """
        Calculate sharing function value.

        sh(d) = 1 - (d/sigma)^alpha if d < sigma, else 0
        """
        if distance >= self.niche_radius:
            return 0.0

        return float(1.0 - (distance / self.niche_radius) ** self.alpha)

    def shared_fitness(
        self,
        solutions: list[Solution],
        raw_fitness: dict[str, float],
    ) -> dict[str, float]:
        """
        Calculate shared fitness for all solutions.

        shared_fitness = raw_fitness / niche_count

        Args:
            solutions: List of solutions
            raw_fitness: Raw fitness values (solution ID -> fitness)

        Returns:
            Shared fitness values
        """
        niche_counts = self.calculate_niche_count(solutions)
        shared = {}

        for sol in solutions:
            sol_id = str(sol.id)
            raw = raw_fitness.get(sol_id, 0.0)
            niche = max(niche_counts.get(sol_id, 1.0), 1.0)  # Avoid division by zero
            shared[sol_id] = raw / niche

        return shared


class ReferencePointAssociation:
    """
    Reference point based diversity (NSGA-III style).

    Solutions are associated with reference points uniformly
    distributed in objective space. This ensures good coverage
    of the entire Pareto front.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        n_reference_points: int = 100,
    ) -> None:
        """
        Initialize reference point association.

        Args:
            objectives: List of objective configurations
            n_reference_points: Number of reference points
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]
        self.n_objectives = len(self.active_objectives)

        # Generate reference points
        self.reference_points = self._generate_reference_points(n_reference_points)

    def _generate_reference_points(self, n: int) -> np.ndarray:
        """Generate uniformly distributed reference points on unit simplex."""
        # Das and Dennis's systematic approach
        from .moead import generate_weight_vectors

        weights = generate_weight_vectors(self.n_objectives, n, method="uniform")
        return np.array(weights)

    def associate(
        self,
        solutions: list[Solution],
    ) -> dict[int, list[Solution]]:
        """
        Associate solutions with reference points.

        Each solution is associated with the reference point that
        has the smallest perpendicular distance.

        Args:
            solutions: List of solutions

        Returns:
            Dictionary mapping reference point index to associated solutions
        """
        associations: dict[int, list[Solution]] = {
            i: [] for i in range(len(self.reference_points))
        }

        for sol in solutions:
            # Get normalized objective vector
            obj_vec = self._get_normalized_vector(sol)

            # Find closest reference point
            min_dist = float("inf")
            closest_ref = 0

            for i, ref in enumerate(self.reference_points):
                dist = self._perpendicular_distance(obj_vec, ref)
                if dist < min_dist:
                    min_dist = dist
                    closest_ref = i

            associations[closest_ref].append(sol)

        return associations

    def _get_normalized_vector(self, solution: Solution) -> np.ndarray:
        """Get normalized objective values for a solution."""
        values = []
        for obj in self.active_objectives:
            val = solution.objective_values.get(obj.name, 0.0)

            if obj.reference_point is not None and obj.nadir_point is not None:
                val = obj.normalize(val)

            values.append(val)

        return np.array(values)

    def _perpendicular_distance(
        self,
        point: np.ndarray,
        reference: np.ndarray,
    ) -> float:
        """Calculate perpendicular distance from point to reference line."""
        # Reference line goes from origin through reference point
        ref_norm = np.linalg.norm(reference)
        if ref_norm == 0:
            return float(np.linalg.norm(point))

        unit_ref = reference / ref_norm

        # Projection of point onto reference line
        projection = np.dot(point, unit_ref)

        # Perpendicular distance
        perp = point - projection * unit_ref
        return float(np.linalg.norm(perp))

    def niching_selection(
        self,
        population: list[Solution],
        n_select: int,
    ) -> list[Solution]:
        """
        Select solutions using reference point niching.

        Prioritizes under-represented reference points.

        Args:
            population: Pool of solutions
            n_select: Number to select

        Returns:
            Selected solutions
        """
        associations = self.associate(population)
        selected: list[Solution] = []

        # Track niche counts
        niche_counts = dict.fromkeys(range(len(self.reference_points)), 0)

        while len(selected) < n_select:
            # Find reference point with minimum count
            min_count = min(niche_counts.values())
            candidate_refs = [
                i for i, c in niche_counts.items() if c == min_count and associations[i]
            ]

            if not candidate_refs:
                break

                # Randomly select from candidates
            ref_idx = np.random.choice(candidate_refs)
            candidates = associations[ref_idx]

            if not candidates:
                continue

                # Select closest to reference point
            best = min(
                candidates,
                key=lambda s: self._perpendicular_distance(
                    self._get_normalized_vector(s), self.reference_points[ref_idx]
                ),
            )

            selected.append(best)
            associations[ref_idx].remove(best)
            niche_counts[ref_idx] += 1

        return selected


class DiversityMechanism:
    """
    Combined diversity management system.

    Integrates multiple diversity preservation mechanisms and
    provides a unified interface for population management.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        primary_metric: DiversityMetric = DiversityMetric.CROWDING_DISTANCE,
        epsilon: float = 0.01,
        niche_radius: float = 0.1,
    ) -> None:
        """
        Initialize diversity mechanism.

        Args:
            objectives: List of objective configurations
            primary_metric: Primary diversity metric to use
            epsilon: Epsilon value for epsilon-dominance
            niche_radius: Radius for niching
        """
        self.objectives = objectives
        self.primary_metric = primary_metric

        # Initialize components
        self.crowding = CrowdingDistance(objectives)
        self.epsilon_dom = EpsilonDominance(objectives, epsilon)
        self.niching = NichingOperator(objectives, niche_radius)
        self.reference_points = ReferencePointAssociation(objectives, 100)

    def calculate_diversity(self, solutions: list[Solution]) -> None:
        """
        Calculate diversity metrics for all solutions.

        Updates solution attributes based on primary metric.

        Args:
            solutions: List of solutions
        """
        if self.primary_metric == DiversityMetric.CROWDING_DISTANCE:
            self.crowding.calculate(solutions)

        elif self.primary_metric == DiversityMetric.EPSILON_GRID:
            # Set diversity as grid distance to neighbors
            for sol in solutions:
                location = self.epsilon_dom.get_grid_location(sol)
                neighbors = sum(
                    1
                    for s in solutions
                    if s.id != sol.id
                    and self._grid_adjacent(
                        location, self.epsilon_dom.get_grid_location(s)
                    )
                )
                sol.crowding_distance = 1.0 / (neighbors + 1)

        elif self.primary_metric == DiversityMetric.NICHING:
            niche_counts = self.niching.calculate_niche_count(solutions)
            for sol in solutions:
                sol.crowding_distance = 1.0 / max(
                    niche_counts.get(str(sol.id), 1.0), 1.0
                )

        elif self.primary_metric == DiversityMetric.REFERENCE_POINT:
            associations = self.reference_points.associate(solutions)
            for ref_idx, assoc_sols in associations.items():
                for sol in assoc_sols:
                    # Diversity based on number sharing reference point
                    sol.crowding_distance = 1.0 / len(assoc_sols)

    def _grid_adjacent(self, loc_a: tuple[int, ...], loc_b: tuple[int, ...]) -> bool:
        """Check if two grid locations are adjacent."""
        return all(abs(a - b) <= 1 for a, b in zip(loc_a, loc_b))

    def select(
        self,
        solutions: list[Solution],
        n: int,
    ) -> list[Solution]:
        """
        Select n solutions with good diversity.

        Args:
            solutions: Pool of solutions
            n: Number to select

        Returns:
            Selected solutions
        """
        if self.primary_metric == DiversityMetric.REFERENCE_POINT:
            return self.reference_points.niching_selection(solutions, n)
        else:
            self.calculate_diversity(solutions)
            sorted_solutions = sorted(
                solutions, key=lambda s: s.crowding_distance, reverse=True
            )
            return sorted_solutions[:n]

    def update_archive(
        self,
        archive: list[Solution],
        new_solutions: list[Solution],
        max_size: int,
    ) -> list[Solution]:
        """
        Update archive maintaining diversity.

        Args:
            archive: Current archive
            new_solutions: New solutions to consider
            max_size: Maximum archive size

        Returns:
            Updated archive
        """
        # Combine and remove dominated
        combined = list(archive)
        for sol in new_solutions:
            combined = self.epsilon_dom.update_archive(combined, sol)

            # Prune to max size if needed
        if len(combined) > max_size:
            self.calculate_diversity(combined)
            combined = sorted(
                combined, key=lambda s: s.crowding_distance, reverse=True
            )[:max_size]

        return combined

    def get_diversity_stats(self, solutions: list[Solution]) -> DiversityStats:
        """
        Calculate diversity statistics for a population.

        Args:
            solutions: List of solutions

        Returns:
            Diversity statistics
        """
        if not solutions:
            return DiversityStats(
                metric_type=self.primary_metric,
                mean_distance=0.0,
                min_distance=0.0,
                max_distance=0.0,
                uniformity=0.0,
                coverage=0.0,
                cluster_count=0,
            )

        self.calculate_diversity(solutions)

        distances = [
            s.crowding_distance for s in solutions if s.crowding_distance < float("inf")
        ]

        if not distances:
            distances = [0.0]

            # Calculate uniformity (inverse of distance variance)
        mean_dist = float(np.mean(distances))
        std_dist = float(np.std(distances))
        uniformity = 1.0 / (1.0 + std_dist / max(mean_dist, 1e-10))

        # Estimate coverage using grid cells
        grid_locations = set(self.epsilon_dom.get_grid_location(s) for s in solutions)
        # Estimate total possible cells (crude approximation)
        max_cells = max(1, len(solutions) * 10)
        coverage = len(grid_locations) / max_cells

        # Estimate cluster count using grid adjacency
        cluster_count = self._count_clusters(solutions)

        return DiversityStats(
            metric_type=self.primary_metric,
            mean_distance=float(mean_dist),
            min_distance=float(min(distances)),
            max_distance=float(max(distances)),
            uniformity=uniformity,
            coverage=min(coverage, 1.0),
            cluster_count=cluster_count,
        )

    def _count_clusters(self, solutions: list[Solution]) -> int:
        """Count number of clusters using simple connectivity."""
        if not solutions:
            return 0

        locations = [self.epsilon_dom.get_grid_location(s) for s in solutions]
        visited = [False] * len(solutions)
        clusters = 0

        for i in range(len(solutions)):
            if visited[i]:
                continue

                # BFS from this solution
            clusters += 1
            queue = [i]
            while queue:
                current = queue.pop(0)
                if visited[current]:
                    continue
                visited[current] = True

                for j in range(len(solutions)):
                    if not visited[j] and self._grid_adjacent(
                        locations[current], locations[j]
                    ):
                        queue.append(j)

        return clusters
