"""
Quality Indicators for Multi-Objective Optimization.

This module provides metrics for evaluating the quality of Pareto fronts
and comparing different optimization runs.

Quality Indicator Categories:
    1. Convergence: How close solutions are to the true Pareto front
    2. Diversity: How well solutions cover the Pareto front
    3. Cardinality: Number of non-dominated solutions
    4. Combined: Metrics that measure both convergence and diversity

Multi-Objective Lens - Evaluating Without Ground Truth:
    Unlike single-objective optimization where we simply compare
    objective values, multi-objective quality is multi-dimensional.

    A good Pareto approximation should:
    - Be close to the true Pareto front (convergence)
    - Cover the entire front (spread)
    - Be evenly distributed (uniformity)
    - Represent the extreme regions (extremity)

    When the true front is unknown:
    - Compare relative to reference fronts from multiple runs
    - Use hypervolume as a unary indicator (no reference needed)
    - Track improvement over generations

Classes:
    - QualityIndicator: Abstract base for all indicators
    - HypervolumeIndicator: Measures dominated hypervolume
    - GenerationalDistance: Average distance to reference front
    - InvertedGenerationalDistance: Coverage of reference front
    - SpreadIndicator: Distribution of solutions
    - EpsilonIndicator: Additive/multiplicative epsilon
    - Spacing: Uniformity of distribution
    - MaximumSpread: Extent of the front
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ParetoFrontier,
    Solution,
)


class QualityIndicator(ABC):
    """
    Abstract base class for quality indicators.

    Quality indicators measure properties of Pareto front approximations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this indicator."""
        pass

    @property
    @abstractmethod
    def is_higher_better(self) -> bool:
        """Return True if higher values indicate better quality."""
        pass

    @abstractmethod
    def calculate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> float:
        """
        Calculate the indicator value.

        Args:
            front: The Pareto front approximation to evaluate
            reference_front: Optional true/reference Pareto front

        Returns:
            The indicator value
        """
        pass


class HypervolumeIndicator(QualityIndicator):
    """
    Hypervolume (HV) indicator - measures dominated hypervolume.

    The hypervolume is the volume of the objective space that is dominated
    by the Pareto front and bounded by a reference point.

    Properties:
    - Larger hypervolume = better front (both convergence and diversity)
    - Reference point should be dominated by all solutions
    - Computationally expensive for many objectives

    This is the only unary indicator that is strictly Pareto compliant,
    meaning a front A has higher HV than B if and only if A dominates B.
    """

    def __init__(self, reference_point: np.ndarray | None = None):
        """
        Initialize hypervolume indicator.

        Args:
            reference_point: Reference point for HV calculation.
                           If None, will be computed from the front.
        """
        self._reference_point = reference_point

    @property
    def name(self) -> str:
        return "hypervolume"

    @property
    def is_higher_better(self) -> bool:
        return True

    def calculate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> float:
        """Calculate hypervolume of the front."""
        if not front.solutions:
            return 0.0

        # Get objective matrix (normalized to minimization)
        points = self._get_normalized_points(front)

        # Determine reference point
        ref_point = self._get_reference_point(points, front)

        # Calculate hypervolume
        return self._calculate_hv(points, ref_point)

    def _get_normalized_points(self, front: ParetoFrontier) -> np.ndarray:
        """Get points as numpy array, normalized to minimization."""
        objective_names = [o.name for o in front.objectives if not o.is_constraint]
        n_solutions = len(front.solutions)
        n_objectives = len(objective_names)

        points = np.zeros((n_solutions, n_objectives))

        for i, sol in enumerate(front.solutions):
            for j, obj in enumerate(front.objectives):
                if obj.is_constraint:
                    continue

                val = sol.objective_values.get(obj.name, 0.0)

                # Convert to minimization form
                if obj.direction == ObjectiveDirection.MAXIMIZE:
                    val = -val

                points[i, j] = val

        return points

    def _get_reference_point(
        self, points: np.ndarray, front: ParetoFrontier
    ) -> np.ndarray:
        """Get or compute reference point."""
        if self._reference_point is not None:
            return self._reference_point

        # Use nadir point + small offset
        nadir = np.max(points, axis=0)
        result: np.ndarray = nadir + 0.1 * np.abs(nadir)
        return result

    def _calculate_hv(self, points: np.ndarray, ref_point: np.ndarray) -> float:
        """
        Calculate hypervolume using WFG algorithm.

        For efficiency, uses dimension-recursive approach.
        """
        n_points, n_dim = points.shape

        if n_points == 0:
            return 0.0

        if n_dim == 1:
            # 1D case: simple interval
            return float(ref_point[0] - np.min(points))

        if n_dim == 2:
            # 2D case: efficient sweep algorithm
            return self._hv_2d(points, ref_point)

        # General case: WFG recursive algorithm
        return self._hv_wfg(points, ref_point)

    def _hv_2d(self, points: np.ndarray, ref_point: np.ndarray) -> float:
        """Calculate 2D hypervolume using sweep algorithm."""
        # Sort by first objective
        sorted_indices = np.argsort(points[:, 0])
        sorted_points = points[sorted_indices]

        hv = 0.0
        prev_x = ref_point[0]
        prev_y = ref_point[1]

        for point in reversed(sorted_points):
            if point[0] < prev_x and point[1] < prev_y:
                hv += (prev_x - point[0]) * (prev_y - point[1])
                prev_x = point[0]

        return hv

    def _hv_wfg(self, points: np.ndarray, ref_point: np.ndarray) -> float:
        """
        Calculate hypervolume using WFG algorithm.

        This is a simplified version for moderate dimensions.
        """
        n_points, n_dim = points.shape

        # Filter points dominated by reference point
        valid = np.all(points <= ref_point, axis=1)
        points = points[valid]

        if len(points) == 0:
            return 0.0

        if len(points) == 1:
            return float(np.prod(ref_point - points[0]))

        # Sort by first objective
        sorted_indices = np.argsort(points[:, 0])
        sorted_points = points[sorted_indices]

        # Recursive calculation
        hv = 0.0
        while len(sorted_points) > 0:
            # Get point with best first objective
            p = sorted_points[0]
            sorted_points = sorted_points[1:]

            # Volume contributed by this point
            if n_dim == 2:
                contrib = (ref_point[0] - p[0]) * (ref_point[1] - p[1])
            else:
                # Recursive for remaining dimensions
                remaining_ref = ref_point[1:]
                remaining_points = sorted_points[:, 1:]
                remaining_points = remaining_points[
                    np.all(remaining_points <= remaining_ref, axis=1)
                ]

                if len(remaining_points) == 0:
                    inner_hv = float(np.prod(remaining_ref - p[1:]))
                else:
                    inner_hv = self._hv_wfg(remaining_points, remaining_ref)

                contrib = (ref_point[0] - p[0]) * inner_hv

            hv += contrib

            # Update reference for remaining points
            ref_point = np.array([p[0]] + list(ref_point[1:]))

        return hv


class GenerationalDistance(QualityIndicator):
    """
    Generational Distance (GD) - measures convergence.

    GD is the average distance from each solution in the approximation
    to the nearest solution in the reference front.

    Lower GD = better convergence to the true front.

    Note: Requires a reference front (usually the true Pareto front
    or best known approximation).
    """

    def __init__(self, p: float = 2.0):
        """
        Initialize generational distance.

        Args:
            p: Power for distance calculation (default 2 = Euclidean)
        """
        self.p = p

    @property
    def name(self) -> str:
        return "generational_distance"

    @property
    def is_higher_better(self) -> bool:
        return False

    def calculate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> float:
        """Calculate generational distance."""
        if not front.solutions or not reference_front or not reference_front.solutions:
            return float("inf")

        # Get point matrices
        approx_points = self._get_normalized_points(front)
        ref_points = self._get_normalized_points(reference_front)

        # Calculate distances to nearest reference point
        distances = []
        for point in approx_points:
            min_dist: float = float("inf")
            for ref in ref_points:
                dist = float(np.linalg.norm(point - ref, ord=self.p))
                min_dist = min(min_dist, dist)
            distances.append(min_dist**self.p)

        # Average distance
        return float((sum(distances) / len(distances)) ** (1.0 / self.p))

    def _get_normalized_points(self, front: ParetoFrontier) -> np.ndarray:
        """Get normalized objective values."""
        objective_names = [o.name for o in front.objectives if not o.is_constraint]
        n_solutions = len(front.solutions)
        n_objectives = len(objective_names)

        points = np.zeros((n_solutions, n_objectives))

        for i, sol in enumerate(front.solutions):
            for j, obj in enumerate(front.objectives):
                if obj.is_constraint:
                    continue

                val = sol.objective_values.get(obj.name, 0.0)

                # Normalize
                if obj.reference_point is not None and obj.nadir_point is not None:
                    val = obj.normalize(val)

                points[i, j] = val

        return points


class InvertedGenerationalDistance(QualityIndicator):
    """
    Inverted Generational Distance (IGD) - measures both convergence and diversity.

    IGD is the average distance from each solution in the reference front
    to the nearest solution in the approximation.

    Lower IGD = better coverage of the true front.

    IGD is preferred over GD because it captures diversity as well as
    convergence.
    """

    def __init__(self, p: float = 2.0):
        """
        Initialize inverted generational distance.

        Args:
            p: Power for distance calculation
        """
        self.p = p

    @property
    def name(self) -> str:
        return "inverted_generational_distance"

    @property
    def is_higher_better(self) -> bool:
        return False

    def calculate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> float:
        """Calculate inverted generational distance."""
        if not front.solutions or not reference_front or not reference_front.solutions:
            return float("inf")

        # Get point matrices
        approx_points = self._get_normalized_points(front)
        ref_points = self._get_normalized_points(reference_front)

        # Calculate distances from reference to nearest approximation
        distances = []
        for ref in ref_points:
            min_dist: float = float("inf")
            for point in approx_points:
                dist = float(np.linalg.norm(ref - point, ord=self.p))
                min_dist = min(min_dist, dist)
            distances.append(min_dist**self.p)

        return float((sum(distances) / len(distances)) ** (1.0 / self.p))

    def _get_normalized_points(self, front: ParetoFrontier) -> np.ndarray:
        """Get normalized objective values."""
        objective_names = [o.name for o in front.objectives if not o.is_constraint]
        n_solutions = len(front.solutions)
        n_objectives = len(objective_names)

        points = np.zeros((n_solutions, n_objectives))

        for i, sol in enumerate(front.solutions):
            for j, obj in enumerate(front.objectives):
                if obj.is_constraint:
                    continue

                val = sol.objective_values.get(obj.name, 0.0)

                if obj.reference_point is not None and obj.nadir_point is not None:
                    val = obj.normalize(val)

                points[i, j] = val

        return points


class SpreadIndicator(QualityIndicator):
    """
    Spread (Delta) indicator - measures diversity and distribution.

    Spread measures how well solutions cover the Pareto front by
    computing distances between consecutive solutions and comparing
    to extreme solutions.

    Lower spread = more uniform distribution.
    """

    @property
    def name(self) -> str:
        return "spread"

    @property
    def is_higher_better(self) -> bool:
        return False

    def calculate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> float:
        """Calculate spread indicator."""
        if len(front.solutions) < 2:
            return float("inf")

        # Get points
        points = self._get_normalized_points(front)

        # For 2D, use simple consecutive distance spread
        if points.shape[1] == 2:
            return self._spread_2d(points)

        # General case: use crowding-based spread
        return self._spread_general(points)

    def _spread_2d(self, points: np.ndarray) -> float:
        """Calculate spread for 2D front."""
        # Sort by first objective
        sorted_indices = np.argsort(points[:, 0])
        sorted_points = points[sorted_indices]

        n = len(sorted_points)

        # Calculate consecutive distances
        distances = []
        for i in range(n - 1):
            dist = np.linalg.norm(sorted_points[i] - sorted_points[i + 1])
            distances.append(dist)

        if not distances:
            return 0.0

        d_mean = np.mean(distances)

        if d_mean == 0:
            return 0.0

        # Calculate spread
        numerator = sum(abs(d - d_mean) for d in distances)
        denominator = (n - 1) * d_mean

        return numerator / denominator if denominator > 0 else 0.0

    def _spread_general(self, points: np.ndarray) -> float:
        """Calculate spread for general dimensions."""
        n = len(points)

        # Calculate all pairwise distances
        distances_to_nearest = []
        for i in range(n):
            min_dist: float = float("inf")
            for j in range(n):
                if i != j:
                    dist = float(np.linalg.norm(points[i] - points[j]))
                    min_dist = min(min_dist, dist)
            distances_to_nearest.append(min_dist)

        d_mean = np.mean(distances_to_nearest)

        if d_mean == 0:
            return 0.0

        # Calculate spread
        variance = sum((d - d_mean) ** 2 for d in distances_to_nearest)
        return float(np.sqrt(variance / n) / d_mean)

    def _get_normalized_points(self, front: ParetoFrontier) -> np.ndarray:
        """Get normalized objective values."""
        objective_names = [o.name for o in front.objectives if not o.is_constraint]
        n_solutions = len(front.solutions)
        n_objectives = len(objective_names)

        points = np.zeros((n_solutions, n_objectives))

        for i, sol in enumerate(front.solutions):
            for j, obj in enumerate(front.objectives):
                if obj.is_constraint:
                    continue

                val = sol.objective_values.get(obj.name, 0.0)

                if obj.reference_point is not None and obj.nadir_point is not None:
                    val = obj.normalize(val)

                points[i, j] = val

        return points


class EpsilonIndicator(QualityIndicator):
    """
    Epsilon indicator - measures domination relationship.

    The epsilon indicator measures the minimum factor by which
    the approximation needs to be multiplied/shifted to dominate
    or be dominated by the reference front.

    Additive: epsilon = min{e : A + e dominates R}
    Multiplicative: epsilon = min{e : A * e dominates R}

    Lower epsilon = closer to dominance relationship.
    """

    def __init__(self, additive: bool = True):
        """
        Initialize epsilon indicator.

        Args:
            additive: If True, use additive epsilon; else multiplicative
        """
        self.additive = additive

    @property
    def name(self) -> str:
        return "epsilon_additive" if self.additive else "epsilon_multiplicative"

    @property
    def is_higher_better(self) -> bool:
        return False

    def calculate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> float:
        """Calculate epsilon indicator."""
        if not front.solutions or not reference_front or not reference_front.solutions:
            return float("inf")

        approx_points = self._get_normalized_points(front)
        ref_points = self._get_normalized_points(reference_front)

        # For each reference point, find minimum epsilon
        max_epsilon = float("-inf")

        for ref in ref_points:
            min_epsilon = float("inf")

            for point in approx_points:
                if self.additive:
                    epsilon = np.max(point - ref)
                else:
                    # Avoid division by zero
                    safe_ref = np.maximum(np.abs(ref), 1e-10)
                    epsilon = np.max(point / safe_ref)

                min_epsilon = min(min_epsilon, epsilon)

            max_epsilon = max(max_epsilon, min_epsilon)

        return max_epsilon

    def _get_normalized_points(self, front: ParetoFrontier) -> np.ndarray:
        """Get normalized objective values."""
        objective_names = [o.name for o in front.objectives if not o.is_constraint]
        n_solutions = len(front.solutions)
        n_objectives = len(objective_names)

        points = np.zeros((n_solutions, n_objectives))

        for i, sol in enumerate(front.solutions):
            for j, obj in enumerate(front.objectives):
                if obj.is_constraint:
                    continue

                val = sol.objective_values.get(obj.name, 0.0)

                # Convert to minimization
                if obj.direction == ObjectiveDirection.MAXIMIZE:
                    val = -val

                points[i, j] = val

        return points


class Spacing(QualityIndicator):
    """
    Spacing indicator - measures uniformity of distribution.

    Spacing measures the variance of distances between consecutive
    solutions. Lower spacing indicates more uniform distribution.
    """

    @property
    def name(self) -> str:
        return "spacing"

    @property
    def is_higher_better(self) -> bool:
        return False

    def calculate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> float:
        """Calculate spacing indicator."""
        if len(front.solutions) < 2:
            return 0.0

        points = self._get_normalized_points(front)
        n = len(points)

        # Calculate minimum distance from each point to others
        d = []
        for i in range(n):
            min_dist = float("inf")
            for j in range(n):
                if i != j:
                    # Use L1 (Manhattan) distance
                    dist = np.sum(np.abs(points[i] - points[j]))
                    min_dist = min(min_dist, dist)
            d.append(min_dist)

        d_mean = np.mean(d)

        # Spacing = standard deviation of distances
        return float(np.sqrt(sum((di - d_mean) ** 2 for di in d) / n))

    def _get_normalized_points(self, front: ParetoFrontier) -> np.ndarray:
        """Get normalized objective values."""
        objective_names = [o.name for o in front.objectives if not o.is_constraint]
        n_solutions = len(front.solutions)
        n_objectives = len(objective_names)

        points = np.zeros((n_solutions, n_objectives))

        for i, sol in enumerate(front.solutions):
            for j, obj in enumerate(front.objectives):
                if obj.is_constraint:
                    continue

                val = sol.objective_values.get(obj.name, 0.0)

                if obj.reference_point is not None and obj.nadir_point is not None:
                    val = obj.normalize(val)

                points[i, j] = val

        return points


class MaximumSpread(QualityIndicator):
    """
    Maximum Spread (MS) indicator - measures extent of the front.

    Maximum spread measures how well the approximation covers the
    extreme regions of the Pareto front.

    Higher MS = better coverage of extremes.
    """

    @property
    def name(self) -> str:
        return "maximum_spread"

    @property
    def is_higher_better(self) -> bool:
        return True

    def calculate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> float:
        """Calculate maximum spread."""
        if len(front.solutions) < 2:
            return 0.0

        points = self._get_normalized_points(front)

        # Calculate extent in each dimension
        extents = []
        for j in range(points.shape[1]):
            extent = np.max(points[:, j]) - np.min(points[:, j])
            extents.append(extent)

        # Maximum spread is the Euclidean norm of extents
        return float(np.sqrt(sum(e**2 for e in extents)))

    def _get_normalized_points(self, front: ParetoFrontier) -> np.ndarray:
        """Get normalized objective values."""
        objective_names = [o.name for o in front.objectives if not o.is_constraint]
        n_solutions = len(front.solutions)
        n_objectives = len(objective_names)

        points = np.zeros((n_solutions, n_objectives))

        for i, sol in enumerate(front.solutions):
            for j, obj in enumerate(front.objectives):
                if obj.is_constraint:
                    continue

                val = sol.objective_values.get(obj.name, 0.0)

                if obj.reference_point is not None and obj.nadir_point is not None:
                    val = obj.normalize(val)

                points[i, j] = val

        return points


@dataclass
class QualityReport:
    """Comprehensive quality report for a Pareto front."""

    front_size: int
    hypervolume: float | None = None
    generational_distance: float | None = None
    inverted_generational_distance: float | None = None
    spread: float | None = None
    epsilon: float | None = None
    spacing: float | None = None
    maximum_spread: float | None = None
    ideal_point: list[float] = field(default_factory=list)
    nadir_point: list[float] = field(default_factory=list)
    objective_names: list[str] = field(default_factory=list)


class QualityEvaluator:
    """
    Evaluates Pareto front quality using multiple indicators.

    Provides a comprehensive assessment of convergence, diversity,
    and distribution for algorithm comparison.
    """

    def __init__(
        self,
        indicators: list[QualityIndicator] | None = None,
        reference_point: np.ndarray | None = None,
    ):
        """
        Initialize quality evaluator.

        Args:
            indicators: List of indicators to calculate (default: all)
            reference_point: Reference point for hypervolume
        """
        if indicators is None:
            indicators = [
                HypervolumeIndicator(reference_point),
                GenerationalDistance(),
                InvertedGenerationalDistance(),
                SpreadIndicator(),
                EpsilonIndicator(),
                Spacing(),
                MaximumSpread(),
            ]

        self.indicators = indicators

    def evaluate(
        self,
        front: ParetoFrontier,
        reference_front: ParetoFrontier | None = None,
    ) -> QualityReport:
        """
        Evaluate quality of a Pareto front.

        Args:
            front: The Pareto front to evaluate
            reference_front: Optional reference front for comparison

        Returns:
            QualityReport with all indicator values
        """
        report = QualityReport(
            front_size=len(front.solutions),
            objective_names=[o.name for o in front.objectives if not o.is_constraint],
        )

        # Set ideal and nadir points
        if front.ideal_point is not None:
            report.ideal_point = front.ideal_point.tolist()
        if front.nadir_point is not None:
            report.nadir_point = front.nadir_point.tolist()

        # Calculate each indicator
        for indicator in self.indicators:
            try:
                value = indicator.calculate(front, reference_front)

                if indicator.name == "hypervolume":
                    report.hypervolume = value
                elif indicator.name == "generational_distance":
                    report.generational_distance = value
                elif indicator.name == "inverted_generational_distance":
                    report.inverted_generational_distance = value
                elif indicator.name == "spread":
                    report.spread = value
                elif indicator.name.startswith("epsilon"):
                    report.epsilon = value
                elif indicator.name == "spacing":
                    report.spacing = value
                elif indicator.name == "maximum_spread":
                    report.maximum_spread = value

            except Exception:
                # Skip failed indicators
                pass

        return report

    def compare_fronts(
        self,
        fronts: list[tuple[str, ParetoFrontier]],
        reference_front: ParetoFrontier | None = None,
    ) -> dict[str, QualityReport]:
        """
        Compare multiple Pareto fronts.

        Args:
            fronts: List of (name, front) tuples
            reference_front: Optional reference front

        Returns:
            Dictionary of name to QualityReport
        """
        return {name: self.evaluate(front, reference_front) for name, front in fronts}
