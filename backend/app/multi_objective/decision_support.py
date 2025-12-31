"""
Decision Support for Multi-Objective Optimization.

This module provides tools for decision makers to navigate, understand,
and select from Pareto-optimal solutions.

Decision Support Components:
    1. Trade-off Analysis: Quantify trade-offs between objectives
    2. Solution Explorer: Navigate the solution space
    3. Preference Elicitor: Extract preferences from decisions
    4. What-if Analysis: Explore consequences of choices

Multi-Objective Lens - Supporting Human Decisions:
    The goal of multi-objective optimization is not to remove human
    judgment but to inform it. Decision support tools should:

    - Make trade-offs explicit and quantifiable
    - Present complex information in digestible form
    - Allow exploration without commitment
    - Support iterative refinement of preferences

    In scheduling contexts:
    - Coordinator needs to understand coverage vs. equity trade-offs
    - Faculty want to see preference satisfaction implications
    - Administrators need compliance risk visibility

Classes:
    - TradeOffAnalyzer: Analyze and quantify trade-offs
    - SolutionExplorer: Navigate and filter solutions
    - PreferenceElicitor: Extract preferences from choices
    - DecisionMaker: Complete decision support interface
    - WhatIfAnalyzer: Hypothetical scenario exploration
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import UUID, uuid4

import numpy as np

from .core import (
    DominanceRelation,
    ObjectiveConfig,
    ObjectiveDirection,
    ParetoFrontier,
    Solution,
    compare_dominance,
)
from .indicators import HypervolumeIndicator, QualityEvaluator, QualityReport
from .preferences import (
    AchievementScalarizing,
    InteractivePreferenceElicitor,
    PreferenceArticulator,
    ReferencePoint,
    WeightedSum,
)


class NavigationDirection(Enum):
    """Direction for navigating the Pareto front."""

    TOWARD_OBJECTIVE = "toward_objective"
    AWAY_FROM_OBJECTIVE = "away_from_objective"
    BALANCED = "balanced"
    EXTREME = "extreme"


@dataclass
class TradeOff:
    """Represents a trade-off between two objectives."""

    objective_improved: str
    objective_degraded: str
    improvement_amount: float
    degradation_amount: float
    trade_off_rate: float  # degradation per unit improvement
    solution_from: UUID
    solution_to: UUID
    is_favorable: bool  # True if improvement > degradation (normalized)


@dataclass
class SolutionComparison:
    """Comparison between two solutions."""

    solution_a: Solution
    solution_b: Solution
    dominance: DominanceRelation
    objective_differences: dict[str, float]
    trade_offs: list[TradeOff]
    recommended: Solution | None
    recommendation_reason: str


@dataclass
class NavigationStep:
    """A step in solution space navigation."""

    from_solution: Solution
    to_solution: Solution
    direction: NavigationDirection
    objective_focus: str | None
    step_size: float  # Distance moved in objective space
    remaining_options: int  # How many more solutions in this direction


class TradeOffAnalyzer:
    """
    Analyzes trade-offs between objectives on the Pareto front.

    Helps decision makers understand the cost of improving one
    objective in terms of degradation in others.
    """

    def __init__(self, objectives: list[ObjectiveConfig]):
        """
        Initialize trade-off analyzer.

        Args:
            objectives: List of objective configurations
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]

    def analyze_trade_off(
        self,
        sol_from: Solution,
        sol_to: Solution,
    ) -> list[TradeOff]:
        """
        Analyze trade-offs when moving from one solution to another.

        Args:
            sol_from: Starting solution
            sol_to: Target solution

        Returns:
            List of trade-offs (improvements paired with degradations)
        """
        improvements = []
        degradations = []

        for obj in self.active_objectives:
            val_from = sol_from.objective_values.get(obj.name, 0.0)
            val_to = sol_to.objective_values.get(obj.name, 0.0)

            diff = val_to - val_from

            # Normalize to [0,1] if possible
            if obj.reference_point is not None and obj.nadir_point is not None:
                norm_from = obj.normalize(val_from)
                norm_to = obj.normalize(val_to)
                norm_diff = norm_to - norm_from
            else:
                norm_diff = diff

            if obj.direction == ObjectiveDirection.MAXIMIZE:
                if diff > 0:
                    improvements.append((obj.name, diff, abs(norm_diff)))
                elif diff < 0:
                    degradations.append((obj.name, abs(diff), abs(norm_diff)))
            else:
                if diff < 0:
                    improvements.append((obj.name, abs(diff), abs(norm_diff)))
                elif diff > 0:
                    degradations.append((obj.name, diff, abs(norm_diff)))

        # Create trade-off pairs
        trade_offs = []
        for imp_name, imp_val, imp_norm in improvements:
            for deg_name, deg_val, deg_norm in degradations:
                rate = deg_norm / imp_norm if imp_norm > 0 else float("inf")
                trade_offs.append(
                    TradeOff(
                        objective_improved=imp_name,
                        objective_degraded=deg_name,
                        improvement_amount=imp_val,
                        degradation_amount=deg_val,
                        trade_off_rate=rate,
                        solution_from=sol_from.id,
                        solution_to=sol_to.id,
                        is_favorable=rate < 1.0,
                    )
                )

        return trade_offs

    def find_favorable_trade_offs(
        self,
        frontier: ParetoFrontier,
        objective: str,
        max_degradation: float = 0.1,
    ) -> list[tuple[Solution, list[TradeOff]]]:
        """
        Find solutions with favorable trade-offs for improving an objective.

        Args:
            frontier: Pareto frontier
            objective: Objective to improve
            max_degradation: Maximum normalized degradation in any other objective

        Returns:
            List of (solution, trade-offs) with favorable trade-offs
        """
        obj_config = next(
            (o for o in self.active_objectives if o.name == objective), None
        )
        if obj_config is None:
            return []

        # Find current best in objective
        solutions = list(frontier.solutions)
        if obj_config.direction == ObjectiveDirection.MAXIMIZE:
            solutions.sort(
                key=lambda s: s.objective_values.get(objective, 0.0), reverse=True
            )
        else:
            solutions.sort(key=lambda s: s.objective_values.get(objective, 0.0))

        best = solutions[0]

        # Find solutions with favorable trade-offs from other solutions
        favorable = []
        for sol in solutions[1:]:
            trade_offs = self.analyze_trade_off(sol, best)

            # Check if all degradations are within limit
            max_deg = max(
                (t.trade_off_rate for t in trade_offs if not t.is_favorable),
                default=0.0,
            )

            if max_deg <= max_degradation:
                favorable.append((best, trade_offs))

        return favorable

    def calculate_marginal_rate_of_substitution(
        self,
        frontier: ParetoFrontier,
        objective_a: str,
        objective_b: str,
    ) -> list[tuple[Solution, float]]:
        """
        Calculate marginal rate of substitution (MRS) along the front.

        MRS is the rate at which objective_b must decrease to increase
        objective_a by one unit while staying on the Pareto front.

        Args:
            frontier: Pareto frontier
            objective_a: Objective to increase
            objective_b: Objective that decreases

        Returns:
            List of (solution, MRS) tuples
        """
        solutions = list(frontier.solutions)

        # Sort by objective_a
        obj_a = next(o for o in self.active_objectives if o.name == objective_a)
        if obj_a.direction == ObjectiveDirection.MAXIMIZE:
            solutions.sort(key=lambda s: s.objective_values.get(objective_a, 0.0))
        else:
            solutions.sort(
                key=lambda s: s.objective_values.get(objective_a, 0.0), reverse=True
            )

        mrs_values = []
        for i in range(len(solutions) - 1):
            sol_1 = solutions[i]
            sol_2 = solutions[i + 1]

            delta_a = abs(
                sol_2.objective_values.get(objective_a, 0.0)
                - sol_1.objective_values.get(objective_a, 0.0)
            )
            delta_b = abs(
                sol_2.objective_values.get(objective_b, 0.0)
                - sol_1.objective_values.get(objective_b, 0.0)
            )

            mrs = delta_b / delta_a if delta_a > 0 else float("inf")
            mrs_values.append((sol_1, mrs))

        return mrs_values


class SolutionExplorer:
    """
    Navigate and explore the Pareto front.

    Provides intuitive navigation through objective space with
    filters, sorting, and neighborhood exploration.
    """

    def __init__(
        self,
        frontier: ParetoFrontier,
        objectives: list[ObjectiveConfig],
    ):
        """
        Initialize solution explorer.

        Args:
            frontier: Pareto frontier to explore
            objectives: Objective configurations
        """
        self.frontier = frontier
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]

        # Current position in exploration
        self.current_solution: Solution | None = None
        self.exploration_history: list[Solution] = []
        self.bookmarks: list[Solution] = []

    def start_at_knee(self) -> Solution | None:
        """Start exploration at the knee solution."""
        self.current_solution = self.frontier.get_knee_solution()
        if self.current_solution:
            self.exploration_history = [self.current_solution]
        return self.current_solution

    def start_at_extreme(self, objective: str) -> Solution | None:
        """Start exploration at extreme of given objective."""
        obj = next((o for o in self.active_objectives if o.name == objective), None)
        if obj is None:
            return None

        solutions = list(self.frontier.solutions)

        if obj.direction == ObjectiveDirection.MAXIMIZE:
            best = max(solutions, key=lambda s: s.objective_values.get(objective, 0.0))
        else:
            best = min(solutions, key=lambda s: s.objective_values.get(objective, 0.0))

        self.current_solution = best
        self.exploration_history = [best]
        return best

    def navigate(
        self,
        direction: NavigationDirection,
        objective: str | None = None,
        step_count: int = 1,
    ) -> list[NavigationStep]:
        """
        Navigate in a direction from current solution.

        Args:
            direction: Direction to navigate
            objective: Objective to move toward/away from
            step_count: Number of steps to take

        Returns:
            List of navigation steps taken
        """
        if self.current_solution is None:
            return []

        steps = []
        current = self.current_solution

        for _ in range(step_count):
            next_sol = self._find_next_solution(current, direction, objective)
            if next_sol is None:
                break

            step = NavigationStep(
                from_solution=current,
                to_solution=next_sol,
                direction=direction,
                objective_focus=objective,
                step_size=self._calculate_distance(current, next_sol),
                remaining_options=self._count_remaining(next_sol, direction, objective),
            )
            steps.append(step)

            current = next_sol
            self.exploration_history.append(current)

        self.current_solution = current
        return steps

    def _find_next_solution(
        self,
        current: Solution,
        direction: NavigationDirection,
        objective: str | None,
    ) -> Solution | None:
        """Find next solution in the given direction."""
        candidates = [s for s in self.frontier.solutions if s.id != current.id]

        if not candidates:
            return None

        if direction == NavigationDirection.TOWARD_OBJECTIVE and objective:
            obj = next((o for o in self.active_objectives if o.name == objective), None)
            if obj is None:
                return None

            current_val = current.objective_values.get(objective, 0.0)

            # Filter to better solutions
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                better = [
                    s
                    for s in candidates
                    if s.objective_values.get(objective, 0.0) > current_val
                ]
            else:
                better = [
                    s
                    for s in candidates
                    if s.objective_values.get(objective, 0.0) < current_val
                ]

            if not better:
                return None

            # Return nearest better solution
            return min(better, key=lambda s: self._calculate_distance(current, s))

        elif direction == NavigationDirection.AWAY_FROM_OBJECTIVE and objective:
            obj = next((o for o in self.active_objectives if o.name == objective), None)
            if obj is None:
                return None

            current_val = current.objective_values.get(objective, 0.0)

            # Filter to worse solutions in this objective
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                worse = [
                    s
                    for s in candidates
                    if s.objective_values.get(objective, 0.0) < current_val
                ]
            else:
                worse = [
                    s
                    for s in candidates
                    if s.objective_values.get(objective, 0.0) > current_val
                ]

            if not worse:
                return None

            return min(worse, key=lambda s: self._calculate_distance(current, s))

        elif direction == NavigationDirection.BALANCED:
            # Move toward knee
            knee = self.frontier.get_knee_solution()
            if knee and knee.id != current.id:
                return min(
                    candidates,
                    key=lambda s: self._calculate_distance(s, knee)
                    if knee
                    else float("inf"),
                )
            return min(candidates, key=lambda s: self._calculate_distance(current, s))

        else:  # EXTREME
            # Move toward nearest extreme
            extremes = self.frontier.get_extreme_solutions()
            if not extremes:
                return None

            nearest_extreme = min(
                extremes, key=lambda e: self._calculate_distance(current, e)
            )
            if nearest_extreme.id == current.id:
                # Already at an extreme, find furthest
                return max(
                    candidates, key=lambda s: self._calculate_distance(current, s)
                )

            # Move toward the extreme
            return min(
                candidates,
                key=lambda s: self._calculate_distance(s, nearest_extreme),
            )

    def _calculate_distance(self, sol1: Solution, sol2: Solution) -> float:
        """Calculate normalized distance between solutions."""
        dist = 0.0
        for obj in self.active_objectives:
            val1 = sol1.objective_values.get(obj.name, 0.0)
            val2 = sol2.objective_values.get(obj.name, 0.0)

            if obj.reference_point is not None and obj.nadir_point is not None:
                val1 = obj.normalize(val1)
                val2 = obj.normalize(val2)

            dist += (val1 - val2) ** 2

        return np.sqrt(dist)

    def _count_remaining(
        self,
        current: Solution,
        direction: NavigationDirection,
        objective: str | None,
    ) -> int:
        """Count how many more steps are possible in this direction."""
        # Simple heuristic: count solutions in the direction
        count = 0
        for s in self.frontier.solutions:
            if s.id == current.id:
                continue

            next_sol = self._find_next_solution(s, direction, objective)
            if next_sol:
                count += 1

        return count

    def filter_by_bounds(
        self,
        bounds: dict[str, tuple[float, float]],
    ) -> list[Solution]:
        """
        Filter solutions within specified bounds.

        Args:
            bounds: Dictionary of objective name to (min, max) bounds

        Returns:
            List of solutions within all bounds
        """
        result = []
        for sol in self.frontier.solutions:
            valid = True
            for obj_name, (lower, upper) in bounds.items():
                val = sol.objective_values.get(obj_name, 0.0)
                if val < lower or val > upper:
                    valid = False
                    break

            if valid:
                result.append(sol)

        return result

    def get_neighborhood(self, center: Solution, radius: float = 0.1) -> list[Solution]:
        """
        Get solutions within a radius of a center solution.

        Args:
            center: Center solution
            radius: Maximum normalized distance

        Returns:
            List of solutions within radius
        """
        neighbors = []
        for sol in self.frontier.solutions:
            if sol.id == center.id:
                continue

            dist = self._calculate_distance(center, sol)
            if dist <= radius:
                neighbors.append(sol)

        return neighbors

    def bookmark(self, solution: Solution | None = None) -> None:
        """Bookmark current or specified solution."""
        sol = solution or self.current_solution
        if sol and sol not in self.bookmarks:
            self.bookmarks.append(sol)

    def compare_bookmarks(self) -> list[SolutionComparison]:
        """Compare all bookmarked solutions pairwise."""
        comparisons = []
        analyzer = TradeOffAnalyzer(self.objectives)

        for i in range(len(self.bookmarks)):
            for j in range(i + 1, len(self.bookmarks)):
                sol_a = self.bookmarks[i]
                sol_b = self.bookmarks[j]

                dominance = compare_dominance(sol_a, sol_b, self.objectives)
                trade_offs = analyzer.analyze_trade_off(sol_a, sol_b)

                # Calculate objective differences
                differences = {}
                for obj in self.active_objectives:
                    val_a = sol_a.objective_values.get(obj.name, 0.0)
                    val_b = sol_b.objective_values.get(obj.name, 0.0)
                    differences[obj.name] = val_a - val_b

                # Recommend based on dominance
                if dominance == DominanceRelation.DOMINATES:
                    recommended = sol_a
                    reason = f"{sol_a.id} dominates {sol_b.id}"
                elif dominance == DominanceRelation.DOMINATED:
                    recommended = sol_b
                    reason = f"{sol_b.id} dominates {sol_a.id}"
                else:
                    recommended = None
                    reason = "Neither solution dominates - trade-off exists"

                comparisons.append(
                    SolutionComparison(
                        solution_a=sol_a,
                        solution_b=sol_b,
                        dominance=dominance,
                        objective_differences=differences,
                        trade_offs=trade_offs,
                        recommended=recommended,
                        recommendation_reason=reason,
                    )
                )

        return comparisons


class PreferenceElicitor:
    """
    Extracts and refines preferences from decision maker choices.

    Learns weights and reference points from comparisons and selections.
    """

    def __init__(self, objectives: list[ObjectiveConfig]):
        """
        Initialize preference elicitor.

        Args:
            objectives: List of objective configurations
        """
        self.objectives = objectives
        self.active_objectives = [o for o in objectives if not o.is_constraint]

        # Learned preferences
        self.inferred_weights: dict[str, float] = {
            o.name: 1.0 / len(self.active_objectives) for o in self.active_objectives
        }
        self.reference_point: dict[str, float] = {}

        # History
        self.comparisons: list[
            tuple[Solution, Solution, int]
        ] = []  # (a, b, preferred: 0=a, 1=b)
        self.selections: list[Solution] = []

    def record_comparison(
        self, solution_a: Solution, solution_b: Solution, preferred: int
    ) -> None:
        """
        Record a pairwise comparison.

        Args:
            solution_a: First solution
            solution_b: Second solution
            preferred: 0 if A preferred, 1 if B preferred
        """
        self.comparisons.append((solution_a, solution_b, preferred))
        self._update_weights_from_comparison(solution_a, solution_b, preferred)

    def record_selection(self, solution: Solution) -> None:
        """Record a solution selection."""
        self.selections.append(solution)
        self._update_reference_from_selection(solution)

    def _update_weights_from_comparison(
        self, sol_a: Solution, sol_b: Solution, preferred: int
    ) -> None:
        """Update inferred weights based on comparison."""
        preferred_sol = sol_a if preferred == 0 else sol_b
        other_sol = sol_b if preferred == 0 else sol_a

        for obj in self.active_objectives:
            val_p = preferred_sol.objective_values.get(obj.name, 0.0)
            val_o = other_sol.objective_values.get(obj.name, 0.0)

            # If preferred is better in this objective, increase weight
            if obj.direction == ObjectiveDirection.MAXIMIZE:
                if val_p > val_o:
                    self.inferred_weights[obj.name] *= 1.1
                elif val_p < val_o:
                    self.inferred_weights[obj.name] *= 0.9
            else:
                if val_p < val_o:
                    self.inferred_weights[obj.name] *= 1.1
                elif val_p > val_o:
                    self.inferred_weights[obj.name] *= 0.9

        # Normalize weights
        total = sum(self.inferred_weights.values())
        if total > 0:
            self.inferred_weights = {
                k: v / total for k, v in self.inferred_weights.items()
            }

    def _update_reference_from_selection(self, solution: Solution) -> None:
        """Update reference point based on selection."""
        for obj in self.active_objectives:
            val = solution.objective_values.get(obj.name, 0.0)

            if obj.name not in self.reference_point:
                self.reference_point[obj.name] = val
            else:
                # Moving average
                self.reference_point[obj.name] = (
                    0.7 * self.reference_point[obj.name] + 0.3 * val
                )

    def get_preference_model(self) -> PreferenceArticulator:
        """Get a preference articulator based on learned preferences."""
        articulator = PreferenceArticulator(self.objectives)

        if self.reference_point:
            ref = ReferencePoint(
                values=self.reference_point,
                objective_names=list(self.reference_point.keys()),
            )
            articulator.set_reference_point(ref)
        else:
            articulator.set_weights(self.inferred_weights)

        return articulator


@dataclass
class WhatIfScenario:
    """A what-if scenario for exploration."""

    name: str
    description: str
    objective_adjustments: dict[str, float]  # Multipliers for objectives
    constraint_changes: dict[str, float]  # Changes to constraint thresholds
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WhatIfResult:
    """Result of a what-if analysis."""

    scenario: WhatIfScenario
    original_frontier: ParetoFrontier
    modified_frontier: ParetoFrontier
    hypervolume_change: float
    solution_count_change: int
    new_solutions: list[Solution]
    lost_solutions: list[Solution]
    impact_summary: str


class WhatIfAnalyzer:
    """
    Analyze hypothetical scenarios and their impact on solutions.

    Helps decision makers understand consequences of changing
    objectives or constraints.
    """

    def __init__(
        self,
        objectives: list[ObjectiveConfig],
        evaluate_fn: Callable[[Solution, dict[str, float]], Solution],
    ):
        """
        Initialize what-if analyzer.

        Args:
            objectives: List of objective configurations
            evaluate_fn: Function to re-evaluate solutions with modified objectives
        """
        self.objectives = objectives
        self.evaluate_fn = evaluate_fn
        self.hv_indicator = HypervolumeIndicator()

    def analyze_scenario(
        self,
        scenario: WhatIfScenario,
        original_frontier: ParetoFrontier,
    ) -> WhatIfResult:
        """
        Analyze the impact of a what-if scenario.

        Args:
            scenario: The scenario to analyze
            original_frontier: Current Pareto frontier

        Returns:
            Analysis results
        """
        # Re-evaluate solutions with modified objectives
        modified_solutions = []
        for sol in original_frontier.solutions:
            modified = self.evaluate_fn(sol, scenario.objective_adjustments)
            modified_solutions.append(modified)

        # Create modified frontier
        modified_frontier = ParetoFrontier(objectives=self.objectives)
        for sol in modified_solutions:
            modified_frontier.add(sol)

        # Calculate metrics
        orig_hv = self.hv_indicator.calculate(original_frontier)
        mod_hv = self.hv_indicator.calculate(modified_frontier)
        hv_change = mod_hv - orig_hv

        # Find new and lost solutions
        orig_ids = {s.id for s in original_frontier.solutions}
        mod_ids = {s.id for s in modified_frontier.solutions}

        new_solutions = [s for s in modified_frontier.solutions if s.id not in orig_ids]
        lost_solutions = [s for s in original_frontier.solutions if s.id not in mod_ids]

        # Generate summary
        if hv_change > 0:
            impact = f"Positive impact: +{hv_change:.2%} hypervolume"
        elif hv_change < 0:
            impact = f"Negative impact: {hv_change:.2%} hypervolume"
        else:
            impact = "Neutral impact"

        return WhatIfResult(
            scenario=scenario,
            original_frontier=original_frontier,
            modified_frontier=modified_frontier,
            hypervolume_change=hv_change,
            solution_count_change=len(modified_frontier) - len(original_frontier),
            new_solutions=new_solutions,
            lost_solutions=lost_solutions,
            impact_summary=impact,
        )


class DecisionMaker:
    """
    Complete decision support interface.

    Integrates trade-off analysis, exploration, preference elicitation,
    and what-if analysis into a cohesive decision support system.
    """

    def __init__(
        self,
        frontier: ParetoFrontier,
        objectives: list[ObjectiveConfig],
    ):
        """
        Initialize decision maker.

        Args:
            frontier: Pareto frontier
            objectives: Objective configurations
        """
        self.frontier = frontier
        self.objectives = objectives

        # Initialize components
        self.trade_off_analyzer = TradeOffAnalyzer(objectives)
        self.explorer = SolutionExplorer(frontier, objectives)
        self.preference_elicitor = PreferenceElicitor(objectives)
        self.quality_evaluator = QualityEvaluator()

        # Decision state
        self.selected_solution: Solution | None = None
        self.decision_history: list[dict[str, Any]] = []

    def get_overview(self) -> dict[str, Any]:
        """Get an overview of the decision space."""
        quality = self.quality_evaluator.evaluate(self.frontier)

        return {
            "frontier_size": len(self.frontier),
            "objectives": [o.name for o in self.objectives if not o.is_constraint],
            "quality": {
                "hypervolume": quality.hypervolume,
                "spread": quality.spread,
                "spacing": quality.spacing,
            },
            "knee_solution": self.frontier.get_knee_solution(),
            "extreme_solutions": self.frontier.get_extreme_solutions(),
            "ideal_point": (
                self.frontier.ideal_point.tolist()
                if self.frontier.ideal_point is not None
                else None
            ),
            "nadir_point": (
                self.frontier.nadir_point.tolist()
                if self.frontier.nadir_point is not None
                else None
            ),
        }

    def recommend_starting_point(self) -> Solution | None:
        """Recommend a good starting point for exploration."""
        # Start at knee if no preferences
        if not self.preference_elicitor.selections:
            return self.frontier.get_knee_solution()

        # Use learned preferences
        articulator = self.preference_elicitor.get_preference_model()
        ranked = articulator.rank_solutions(list(self.frontier.solutions))

        return ranked[0][0] if ranked else None

    def compare_solutions(self, sol_a: Solution, sol_b: Solution) -> SolutionComparison:
        """Compare two solutions in detail."""
        dominance = compare_dominance(sol_a, sol_b, self.objectives)
        trade_offs = self.trade_off_analyzer.analyze_trade_off(sol_a, sol_b)

        differences = {}
        for obj in self.objectives:
            if obj.is_constraint:
                continue
            val_a = sol_a.objective_values.get(obj.name, 0.0)
            val_b = sol_b.objective_values.get(obj.name, 0.0)
            differences[obj.name] = val_a - val_b

        if dominance == DominanceRelation.DOMINATES:
            recommended = sol_a
            reason = "Solution A dominates B in all objectives"
        elif dominance == DominanceRelation.DOMINATED:
            recommended = sol_b
            reason = "Solution B dominates A in all objectives"
        else:
            recommended = None
            reason = "Neither dominates - trade-off required"

        return SolutionComparison(
            solution_a=sol_a,
            solution_b=sol_b,
            dominance=dominance,
            objective_differences=differences,
            trade_offs=trade_offs,
            recommended=recommended,
            recommendation_reason=reason,
        )

    def record_preference(
        self,
        sol_a: Solution,
        sol_b: Solution,
        preferred: int,
    ) -> None:
        """Record a preference between two solutions."""
        self.preference_elicitor.record_comparison(sol_a, sol_b, preferred)

        self.decision_history.append(
            {
                "type": "comparison",
                "solution_a": str(sol_a.id),
                "solution_b": str(sol_b.id),
                "preferred": preferred,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def select_solution(self, solution: Solution) -> None:
        """Select a solution as the final choice."""
        self.selected_solution = solution
        self.preference_elicitor.record_selection(solution)

        self.decision_history.append(
            {
                "type": "selection",
                "solution": str(solution.id),
                "objective_values": solution.objective_values,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_recommendation(self) -> tuple[Solution | None, str]:
        """
        Get a recommended solution based on learned preferences.

        Returns:
            Tuple of (recommended solution, explanation)
        """
        if (
            not self.preference_elicitor.comparisons
            and not self.preference_elicitor.selections
        ):
            knee = self.frontier.get_knee_solution()
            return knee, "Balanced knee solution (no preferences recorded yet)"

        articulator = self.preference_elicitor.get_preference_model()
        ranked = articulator.rank_solutions(list(self.frontier.solutions))

        if not ranked:
            return None, "No solutions available"

        best = ranked[0][0]

        # Explain recommendation
        weights = self.preference_elicitor.inferred_weights
        top_objectives = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
        explanation = (
            f"Based on your preferences, prioritizing: "
            f"{', '.join(f'{name} ({w:.1%})' for name, w in top_objectives)}"
        )

        return best, explanation

    def get_decision_summary(self) -> dict[str, Any]:
        """Get summary of the decision process."""
        return {
            "comparisons_made": len(self.preference_elicitor.comparisons),
            "selections_made": len(self.preference_elicitor.selections),
            "inferred_weights": self.preference_elicitor.inferred_weights,
            "reference_point": self.preference_elicitor.reference_point,
            "selected_solution": (
                {
                    "id": str(self.selected_solution.id),
                    "objectives": self.selected_solution.objective_values,
                }
                if self.selected_solution
                else None
            ),
            "history_length": len(self.decision_history),
        }
