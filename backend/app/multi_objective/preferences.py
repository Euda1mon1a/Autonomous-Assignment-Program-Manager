"""
Preference Articulation Methods for Multi-Objective Optimization.

This module provides methods for incorporating decision maker preferences
into the multi-objective optimization process.

Preference Articulation Approaches:
    1. A Priori: Preferences specified before optimization
    2. A Posteriori: All Pareto solutions presented for selection
    3. Interactive: Preferences refined during optimization

Multi-Objective Lens - When to Articulate:
    The timing of preference articulation affects both solution quality
    and decision maker burden:

    A Priori (Before):
    - Fast: Single optimization run
    - Risk: May miss better solutions outside specified preferences
    - Use when: Decision maker knows exact trade-off preferences

    A Posteriori (After):
    - Complete: Explores entire Pareto front
    - Burden: Decision maker must choose from many options
    - Use when: Problem is new or preferences are unclear

    Interactive (During):
    - Focused: Concentrates search on promising regions
    - Efficient: Balances exploration and exploitation
    - Use when: Complex problems with many objectives

Classes:
    - PreferenceMethod: Base class for preference methods
    - WeightedSum: Simple weighted aggregation
    - ReferencePoint: Goal-based optimization
    - AchievementScalarizing: Achievement scalarizing functions
    - LexicographicOrdering: Priority-based ordering
    - InteractivePreferenceElicitor: Interactive preference refinement
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from uuid import UUID

import numpy as np

from .core import (
    DominanceRelation,
    ObjectiveConfig,
    ObjectiveDirection,
    ParetoFrontier,
    Solution,
    compare_dominance,
)


class PreferenceType(Enum):
    """Type of preference articulation."""

    A_PRIORI = "a_priori"
    A_POSTERIORI = "a_posteriori"
    INTERACTIVE = "interactive"


class ScalarizingFunction(Enum):
    """Types of scalarizing functions."""

    WEIGHTED_SUM = "weighted_sum"
    TCHEBYCHEFF = "tchebycheff"
    AUGMENTED_TCHEBYCHEFF = "augmented_tchebycheff"
    PBI = "pbi"
    WIERZBICKI = "wierzbicki"


@dataclass
class ReferencePoint:
    """
    A reference point (aspiration level) for each objective.

    The decision maker specifies desirable values for each objective.
    Optimization aims to find solutions as close as possible to these goals.

    Attributes:
        values: Target values for each objective
        objective_names: Names of objectives (for ordering)
        is_aspiration: True if targets are aspirations (ideal)
        is_reservation: True if targets are reservations (worst acceptable)
    """

    values: dict[str, float]
    objective_names: list[str] = field(default_factory=list)
    is_aspiration: bool = True
    is_reservation: bool = False

    def to_vector(self, objective_names: list[str] | None = None) -> np.ndarray:
        """Convert to numpy array in specified order."""
        names = objective_names or self.objective_names
        return np.array([self.values.get(name, 0.0) for name in names])

    @classmethod
    def from_solution(cls, solution: Solution) -> "ReferencePoint":
        """Create reference point from a solution's objective values."""
        return cls(
            values=dict(solution.objective_values),
            objective_names=list(solution.objective_values.keys()),
        )


class PreferenceMethod(ABC):
    """
    Abstract base class for preference articulation methods.

    A preference method converts multi-objective values into a single
    score based on decision maker preferences.
    """

    @property
    @abstractmethod
    def preference_type(self) -> PreferenceType:
        """Return the type of preference articulation."""
        pass

    @abstractmethod
    def score(
        self,
        solution: Solution,
        objectives: list[ObjectiveConfig],
    ) -> float:
        """
        Calculate a preference score for the solution.

        Lower scores are generally better (for minimization-based ranking).

        Args:
            solution: Solution to score
            objectives: List of objective configurations

        Returns:
            Preference score (lower is better)
        """
        pass

    def rank_solutions(
        self,
        solutions: list[Solution],
        objectives: list[ObjectiveConfig],
    ) -> list[tuple[Solution, float]]:
        """
        Rank solutions by preference score.

        Args:
            solutions: List of solutions to rank
            objectives: List of objective configurations

        Returns:
            List of (solution, score) tuples, sorted by score (best first)
        """
        scored = [(sol, self.score(sol, objectives)) for sol in solutions]
        scored.sort(key=lambda x: x[1])
        return scored


class WeightedSum(PreferenceMethod):
    """
    Weighted sum preference method.

    score = sum(w_i * f_i)

    Simple and intuitive but cannot find solutions in non-convex
    regions of the Pareto front.
    """

    def __init__(self, weights: dict[str, float]):
        """
        Initialize weighted sum.

        Args:
            weights: Dictionary of objective name to weight
        """
        self.weights = weights
        self._normalize_weights()

    def _normalize_weights(self) -> None:
        """Normalize weights to sum to 1."""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    @property
    def preference_type(self) -> PreferenceType:
        return PreferenceType.A_PRIORI

    def score(
        self,
        solution: Solution,
        objectives: list[ObjectiveConfig],
    ) -> float:
        """Calculate weighted sum score."""
        total = 0.0
        for obj in objectives:
            if obj.is_constraint:
                continue

            value = solution.objective_values.get(obj.name, 0.0)
            weight = self.weights.get(obj.name, 0.0)

            # Normalize to minimization
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                value = -value

            total += weight * value

        return total


class AchievementScalarizing(PreferenceMethod):
    """
    Achievement Scalarizing Function (ASF) for reference point methods.

    Minimizes the maximum weighted deviation from the reference point,
    with an augmentation term for uniqueness.

    ASF(f, z) = max_i(w_i * (f_i - z_i)) + rho * sum(w_i * (f_i - z_i))

    This guarantees finding Pareto-optimal solutions even in non-convex
    regions of the Pareto front.
    """

    def __init__(
        self,
        reference_point: ReferencePoint,
        weights: dict[str, float] | None = None,
        rho: float = 0.0001,
    ):
        """
        Initialize achievement scalarizing function.

        Args:
            reference_point: Target values for objectives
            weights: Optional weights (default: equal weights)
            rho: Augmentation parameter for tie-breaking
        """
        self.reference_point = reference_point
        self.weights = weights or dict.fromkeys(reference_point.objective_names, 1.0)
        self.rho = rho

    @property
    def preference_type(self) -> PreferenceType:
        return PreferenceType.A_PRIORI

    def score(
        self,
        solution: Solution,
        objectives: list[ObjectiveConfig],
    ) -> float:
        """Calculate ASF score."""
        max_deviation = float("-inf")
        sum_deviation = 0.0

        for obj in objectives:
            if obj.is_constraint:
                continue

            value = solution.objective_values.get(obj.name, 0.0)
            target = self.reference_point.values.get(obj.name, 0.0)
            weight = self.weights.get(obj.name, 1.0)

            # Normalize to minimization form
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                value = -value
                target = -target

            deviation = weight * (value - target)
            max_deviation = max(max_deviation, deviation)
            sum_deviation += deviation

        # ASF with augmentation
        return max_deviation + self.rho * sum_deviation


class WierzbickiASF(PreferenceMethod):
    """
    Wierzbicki's Achievement Scalarizing Function.

    Uses both aspiration (goal) and reservation (minimum acceptable)
    reference points to guide the search.

    Particularly useful when the decision maker can specify both
    ideal targets and worst acceptable values.
    """

    def __init__(
        self,
        aspiration: ReferencePoint,
        reservation: ReferencePoint | None = None,
        rho: float = 0.0001,
    ):
        """
        Initialize Wierzbicki ASF.

        Args:
            aspiration: Ideal target values
            reservation: Worst acceptable values (optional)
            rho: Augmentation parameter
        """
        self.aspiration = aspiration
        self.reservation = reservation
        self.rho = rho

    @property
    def preference_type(self) -> PreferenceType:
        return PreferenceType.A_PRIORI

    def score(
        self,
        solution: Solution,
        objectives: list[ObjectiveConfig],
    ) -> float:
        """Calculate Wierzbicki ASF score."""
        max_deviation = float("-inf")
        sum_deviation = 0.0

        for obj in objectives:
            if obj.is_constraint:
                continue

            value = solution.objective_values.get(obj.name, 0.0)
            aspiration = self.aspiration.values.get(obj.name, 0.0)

            # Normalize to minimization form
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                value = -value
                aspiration = -aspiration

            # Calculate deviation
            deviation = value - aspiration

            # If reservation point exists, use relative scaling
            if self.reservation:
                reservation = self.reservation.values.get(obj.name, aspiration)
                if obj.direction == ObjectiveDirection.MAXIMIZE:
                    reservation = -reservation

                range_val = abs(reservation - aspiration)
                if range_val > 0:
                    deviation /= range_val

            max_deviation = max(max_deviation, deviation)
            sum_deviation += max(0, deviation)

        return max_deviation + self.rho * sum_deviation


class LexicographicOrdering(PreferenceMethod):
    """
    Lexicographic ordering of objectives.

    Objectives are optimized in priority order: the first objective
    is optimized first, then the second within solutions that are
    equal in the first, and so on.

    Useful when objectives have a clear priority ordering.
    """

    def __init__(self, priority_order: list[str], epsilon: float = 0.01):
        """
        Initialize lexicographic ordering.

        Args:
            priority_order: Objective names in priority order (highest first)
            epsilon: Tolerance for equality comparison
        """
        self.priority_order = priority_order
        self.epsilon = epsilon

    @property
    def preference_type(self) -> PreferenceType:
        return PreferenceType.A_PRIORI

    def score(
        self,
        solution: Solution,
        objectives: list[ObjectiveConfig],
    ) -> float:
        """
        Calculate lexicographic score.

        Uses a weighted sum where weights decrease exponentially
        with priority level.
        """
        score = 0.0
        multiplier = 1.0

        obj_map = {o.name: o for o in objectives}

        for name in self.priority_order:
            obj = obj_map.get(name)
            if obj is None or obj.is_constraint:
                continue

            value = solution.objective_values.get(name, 0.0)

            # Normalize to [0, 1] range if possible
            if obj.reference_point is not None and obj.nadir_point is not None:
                value = obj.normalize(value)

            # Convert to minimization
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                value = -value

            score += multiplier * value
            multiplier *= 0.001  # Decrease weight for lower priority

        return score

    def compare(
        self,
        sol1: Solution,
        sol2: Solution,
        objectives: list[ObjectiveConfig],
    ) -> int:
        """
        Compare two solutions lexicographically.

        Returns:
            -1 if sol1 is preferred
            0 if equal
            1 if sol2 is preferred
        """
        obj_map = {o.name: o for o in objectives}

        for name in self.priority_order:
            obj = obj_map.get(name)
            if obj is None or obj.is_constraint:
                continue

            val1 = sol1.objective_values.get(name, 0.0)
            val2 = sol2.objective_values.get(name, 0.0)

            diff = val1 - val2

            if obj.direction == ObjectiveDirection.MAXIMIZE:
                diff = -diff

            if diff < -self.epsilon:
                return -1
            if diff > self.epsilon:
                return 1

        return 0


class LightBeamSearch(PreferenceMethod):
    """
    Light Beam Search for focused exploration.

    Projects a "beam" from the ideal point through a reference point
    and finds solutions near this beam. Useful for interactive
    exploration where the decision maker progressively refines preferences.
    """

    def __init__(
        self,
        reference_point: ReferencePoint,
        ideal_point: dict[str, float],
        beam_width: float = 0.1,
    ):
        """
        Initialize light beam search.

        Args:
            reference_point: Direction of the beam
            ideal_point: Starting point of the beam
            beam_width: Width of the search beam (0 to 1)
        """
        self.reference_point = reference_point
        self.ideal_point = ideal_point
        self.beam_width = beam_width

    @property
    def preference_type(self) -> PreferenceType:
        return PreferenceType.INTERACTIVE

    def score(
        self,
        solution: Solution,
        objectives: list[ObjectiveConfig],
    ) -> float:
        """Calculate distance from light beam."""
        # Get vectors
        obj_names = [o.name for o in objectives if not o.is_constraint]

        f = np.array([solution.objective_values.get(n, 0.0) for n in obj_names])
        z = np.array([self.ideal_point.get(n, 0.0) for n in obj_names])
        q = np.array([self.reference_point.values.get(n, 0.0) for n in obj_names])

        # Beam direction
        direction = q - z
        dir_norm = np.linalg.norm(direction)
        if dir_norm == 0:
            return float(np.linalg.norm(f - z))

        direction = direction / dir_norm

        # Vector from ideal to solution
        to_solution = f - z

        # Projection onto beam
        projection = np.dot(to_solution, direction)

        # Perpendicular distance
        perp = to_solution - projection * direction
        perp_distance = np.linalg.norm(perp)

        # Combine: distance along beam + penalty for being off-beam
        return float(projection + (perp_distance / self.beam_width) ** 2)


@dataclass
class PreferenceElicitationState:
    """State for interactive preference elicitation."""

    iteration: int = 0
    current_reference: ReferencePoint | None = None
    reference_history: list[ReferencePoint] = field(default_factory=list)
    selected_solutions: list[Solution] = field(default_factory=list)
    feedback_history: list[dict[str, Any]] = field(default_factory=list)
    is_complete: bool = False


class InteractivePreferenceElicitor:
    """
    Interactive preference elicitation through iterative refinement.

    Guides the decision maker through the Pareto front by:
    1. Presenting representative solutions
    2. Collecting feedback (ratings, comparisons, adjustments)
    3. Refining the search based on feedback
    4. Repeating until satisfied

    This implements a simplified version of NIMBUS/NAUTILUS methods.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        initial_samples: int = 5,
        max_iterations: int = 10,
    ):
        """
        Initialize interactive elicitor.

        Args:
            objectives: List of objective configurations
            initial_samples: Number of solutions to present initially
            max_iterations: Maximum elicitation iterations
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]
        self.initial_samples = initial_samples
        self.max_iterations = max_iterations
        self.state = PreferenceElicitationState()

    def start_elicitation(self, frontier: ParetoFrontier) -> list[Solution]:
        """
        Start the elicitation process.

        Returns a set of representative solutions for the decision maker
        to evaluate.
        """
        self.state = PreferenceElicitationState()

        # Select diverse representatives
        representatives = self._select_representatives(frontier, self.initial_samples)
        return representatives

    def process_feedback(
        self,
        feedback_type: str,
        feedback_data: dict[str, Any],
        current_frontier: ParetoFrontier,
    ) -> list[Solution]:
        """
        Process decision maker feedback and return next set of solutions.

        Feedback types:
        - "rating": Rate each solution 1-5
        - "comparison": Compare pairs of solutions
        - "reference": Specify new reference point
        - "bounds": Set acceptable ranges for objectives
        - "classification": Classify objectives (improve/relax/accept/free)

        Args:
            feedback_type: Type of feedback provided
            feedback_data: The feedback data
            current_frontier: Current Pareto frontier

        Returns:
            New set of solutions based on feedback
        """
        self.state.iteration += 1
        self.state.feedback_history.append(
            {
                "type": feedback_type,
                "data": feedback_data,
                "iteration": self.state.iteration,
            }
        )

        if feedback_type == "rating":
            return self._process_rating_feedback(feedback_data, current_frontier)

        elif feedback_type == "comparison":
            return self._process_comparison_feedback(feedback_data, current_frontier)

        elif feedback_type == "reference":
            return self._process_reference_feedback(feedback_data, current_frontier)

        elif feedback_type == "bounds":
            return self._process_bounds_feedback(feedback_data, current_frontier)

        elif feedback_type == "classification":
            return self._process_classification_feedback(
                feedback_data, current_frontier
            )

        elif feedback_type == "done":
            self.state.is_complete = True
            return list(self.state.selected_solutions)

        return self._select_representatives(current_frontier, self.initial_samples)

    def _process_rating_feedback(
        self,
        feedback: dict[str, Any],
        frontier: ParetoFrontier,
    ) -> list[Solution]:
        """Process solution ratings to infer preferences."""
        ratings = feedback.get("ratings", {})  # {solution_id: rating}

        if not ratings:
            return self._select_representatives(frontier, self.initial_samples)

        # Find best-rated solution
        best_id = max(ratings.keys(), key=lambda k: ratings[k])
        best_solution = next(
            (s for s in frontier.solutions if str(s.id) == best_id), None
        )

        if best_solution:
            self.state.selected_solutions.append(best_solution)

            # Update reference point based on best solution
            self.state.current_reference = ReferencePoint.from_solution(best_solution)
            self.state.reference_history.append(self.state.current_reference)

            # Find solutions near the best one
            return self._find_neighborhood(
                best_solution, frontier, self.initial_samples
            )

        return self._select_representatives(frontier, self.initial_samples)

    def _process_comparison_feedback(
        self,
        feedback: dict[str, Any],
        frontier: ParetoFrontier,
    ) -> list[Solution]:
        """Process pairwise comparisons to infer preferences."""
        comparisons = feedback.get("comparisons", [])

        # Learn weights from comparisons using simple heuristic
        # Each comparison (A > B) suggests objectives where A is better matter more
        inferred_weights = {o.name: 1.0 for o in self.active_objectives}

        for comp in comparisons:
            preferred_id = comp.get("preferred")
            other_id = comp.get("other")

            preferred = next(
                (s for s in frontier.solutions if str(s.id) == preferred_id), None
            )
            other = next((s for s in frontier.solutions if str(s.id) == other_id), None)

            if preferred and other:
                # Increase weight for objectives where preferred is better
                for obj in self.active_objectives:
                    val_p = preferred.objective_values.get(obj.name, 0.0)
                    val_o = other.objective_values.get(obj.name, 0.0)

                    if obj.direction == ObjectiveDirection.MAXIMIZE:
                        if val_p > val_o:
                            inferred_weights[obj.name] *= 1.2
                    else:
                        if val_p < val_o:
                            inferred_weights[obj.name] *= 1.2

        # Normalize weights
        total = sum(inferred_weights.values())
        if total > 0:
            inferred_weights = {k: v / total for k, v in inferred_weights.items()}

        # Use weighted sum to find new representatives
        scorer = WeightedSum(inferred_weights)
        scored = scorer.rank_solutions(list(frontier.solutions), self.objectives)

        return [sol for sol, _ in scored[: self.initial_samples]]

    def _process_reference_feedback(
        self,
        feedback: dict[str, Any],
        frontier: ParetoFrontier,
    ) -> list[Solution]:
        """Process new reference point specification."""
        reference_values = feedback.get("reference", {})

        self.state.current_reference = ReferencePoint(
            values=reference_values,
            objective_names=list(reference_values.keys()),
        )
        self.state.reference_history.append(self.state.current_reference)

        # Find solutions closest to reference
        asf = AchievementScalarizing(self.state.current_reference)
        scored = asf.rank_solutions(list(frontier.solutions), self.objectives)

        return [sol for sol, _ in scored[: self.initial_samples]]

    def _process_bounds_feedback(
        self,
        feedback: dict[str, Any],
        frontier: ParetoFrontier,
    ) -> list[Solution]:
        """Process acceptable bounds for objectives."""
        bounds = feedback.get("bounds", {})  # {obj_name: (min, max)}

        # Filter solutions within bounds
        valid_solutions = []
        for sol in frontier.solutions:
            valid = True
            for obj_name, (lower, upper) in bounds.items():
                val = sol.objective_values.get(obj_name, 0.0)
                if val < lower or val > upper:
                    valid = False
                    break

            if valid:
                valid_solutions.append(sol)

        if not valid_solutions:
            # No solutions in bounds - return closest
            return self._select_representatives(frontier, self.initial_samples)

        # Return diverse subset of valid solutions
        temp_frontier = ParetoFrontier(
            solutions=valid_solutions, objectives=self.objectives
        )
        return self._select_representatives(temp_frontier, self.initial_samples)

    def _process_classification_feedback(
        self,
        feedback: dict[str, Any],
        frontier: ParetoFrontier,
    ) -> list[Solution]:
        """
        Process NIMBUS-style objective classification.

        Classifications:
        - "improve": This objective should improve
        - "relax": Can relax this objective to improve others
        - "accept": Current level is acceptable
        - "free": No preference
        """
        classifications = feedback.get("classifications", {})
        current_solution = feedback.get("current_solution")

        if not current_solution:
            return self._select_representatives(frontier, self.initial_samples)

        # Build reference based on classifications
        reference_values = {}
        for obj in self.active_objectives:
            current_val = current_solution.objective_values.get(obj.name, 0.0)
            classification = classifications.get(obj.name, "free")

            if classification == "improve":
                # Target better than current
                if obj.direction == ObjectiveDirection.MAXIMIZE:
                    reference_values[obj.name] = current_val * 1.1
                else:
                    reference_values[obj.name] = current_val * 0.9

            elif classification == "relax":
                # Allow worse than current
                if obj.direction == ObjectiveDirection.MAXIMIZE:
                    reference_values[obj.name] = current_val * 0.9
                else:
                    reference_values[obj.name] = current_val * 1.1

            else:  # accept or free
                reference_values[obj.name] = current_val

        self.state.current_reference = ReferencePoint(values=reference_values)

        asf = AchievementScalarizing(self.state.current_reference)
        scored = asf.rank_solutions(list(frontier.solutions), self.objectives)

        return [sol for sol, _ in scored[: self.initial_samples]]

    def _select_representatives(
        self, frontier: ParetoFrontier, n: int
    ) -> list[Solution]:
        """Select diverse representative solutions from the frontier."""
        if len(frontier.solutions) <= n:
            return list(frontier.solutions)

        # Include extreme solutions
        extremes = frontier.get_extreme_solutions()
        selected = list(extremes)

        # Include knee solution
        knee = frontier.get_knee_solution()
        if knee and knee not in selected:
            selected.append(knee)

        # Fill remaining with diverse solutions
        remaining = [s for s in frontier.solutions if s not in selected]

        while len(selected) < n and remaining:
            # Select solution most distant from current selection
            best_distance = -1.0
            best_idx = 0

            for i, candidate in enumerate(remaining):
                min_dist = min(self._solution_distance(candidate, s) for s in selected)
                if min_dist > best_distance:
                    best_distance = min_dist
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return selected

    def _find_neighborhood(
        self, center: Solution, frontier: ParetoFrontier, n: int
    ) -> list[Solution]:
        """Find solutions near a center solution."""
        distances = [
            (self._solution_distance(center, s), s)
            for s in frontier.solutions
            if s.id != center.id
        ]
        distances.sort(key=lambda x: x[0])

        # Return closest n solutions plus some diversity
        close = [s for _, s in distances[: n // 2]]
        remaining = [s for _, s in distances[n // 2 :]]

        # Add some diverse ones
        if remaining:
            diverse_indices = np.linspace(0, len(remaining) - 1, n - len(close)).astype(
                int
            )
            close.extend([remaining[i] for i in diverse_indices])

        return close[:n]

    def _solution_distance(self, sol1: Solution, sol2: Solution) -> float:
        """Calculate normalized Euclidean distance between solutions."""
        dist = 0.0
        for obj in self.active_objectives:
            val1 = sol1.objective_values.get(obj.name, 0.0)
            val2 = sol2.objective_values.get(obj.name, 0.0)

            # Normalize using reference and nadir if available
            if obj.reference_point is not None and obj.nadir_point is not None:
                val1 = obj.normalize(val1)
                val2 = obj.normalize(val2)

            dist += (val1 - val2) ** 2

        return float(np.sqrt(dist))

    def get_preference_summary(self) -> dict[str, Any]:
        """Get summary of elicited preferences."""
        return {
            "iterations": self.state.iteration,
            "is_complete": self.state.is_complete,
            "current_reference": (
                self.state.current_reference.values
                if self.state.current_reference
                else None
            ),
            "reference_history": [r.values for r in self.state.reference_history],
            "selected_count": len(self.state.selected_solutions),
            "feedback_count": len(self.state.feedback_history),
        }


class PreferenceArticulator:
    """
    Facade for preference articulation that supports all methods.

    Provides a unified interface for a priori, a posteriori, and
    interactive preference methods.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        method: PreferenceMethod | None = None,
    ):
        """
        Initialize preference articulator.

        Args:
            objectives: List of objective configurations
            method: Optional default preference method
        """
        self.objectives = objectives
        self.method = method

        # Interactive elicitor
        self.elicitor: InteractivePreferenceElicitor | None = None

    def set_method(self, method: PreferenceMethod) -> None:
        """Set the preference method."""
        self.method = method

    def set_weights(self, weights: dict[str, float]) -> None:
        """Set weights for weighted sum preference."""
        self.method = WeightedSum(weights)

    def set_reference_point(
        self,
        reference: ReferencePoint,
        reservation: ReferencePoint | None = None,
    ) -> None:
        """Set reference point for ASF preference."""
        if reservation:
            self.method = WierzbickiASF(reference, reservation)
        else:
            self.method = AchievementScalarizing(reference)

    def set_priority_order(self, priority: list[str]) -> None:
        """Set lexicographic priority ordering."""
        self.method = LexicographicOrdering(priority)

    def start_interactive(self, frontier: ParetoFrontier) -> list[Solution]:
        """Start interactive preference elicitation."""
        self.elicitor = InteractivePreferenceElicitor(self.objectives)
        return self.elicitor.start_elicitation(frontier)

    def continue_interactive(
        self,
        feedback_type: str,
        feedback_data: dict[str, Any],
        frontier: ParetoFrontier,
    ) -> list[Solution]:
        """Continue interactive elicitation with feedback."""
        if not self.elicitor:
            return self.start_interactive(frontier)

        return self.elicitor.process_feedback(feedback_type, feedback_data, frontier)

    def score_solution(self, solution: Solution) -> float:
        """Score a solution using current preference method."""
        if not self.method:
            return 0.0

        return self.method.score(solution, self.objectives)

    def rank_solutions(self, solutions: list[Solution]) -> list[tuple[Solution, float]]:
        """Rank solutions using current preference method."""
        if not self.method:
            return [(s, 0.0) for s in solutions]

        return self.method.rank_solutions(solutions, self.objectives)

    def select_best(
        self,
        frontier: ParetoFrontier,
        n: int = 1,
    ) -> list[Solution]:
        """Select best solutions according to current preferences."""
        if not self.method:
            # Default: return knee and extremes
            result: list[Solution] = []
            knee = frontier.get_knee_solution()
            if knee:
                result.append(knee)
            result.extend(frontier.get_extreme_solutions())
            return result[:n]

        ranked = self.method.rank_solutions(list(frontier.solutions), self.objectives)
        return [sol for sol, _ in ranked[:n]]
