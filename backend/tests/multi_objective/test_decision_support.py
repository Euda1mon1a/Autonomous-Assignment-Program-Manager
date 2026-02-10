"""Tests for multi-objective decision support (pure logic, no DB)."""

import pytest

from app.multi_objective.core import (
    DominanceRelation,
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    ParetoFrontier,
    Solution,
    compare_dominance,
)
from app.multi_objective.decision_support import (
    DecisionMaker,
    NavigationDirection,
    NavigationStep,
    PreferenceElicitor,
    SolutionComparison,
    SolutionExplorer,
    TradeOff,
    TradeOffAnalyzer,
    WhatIfAnalyzer,
    WhatIfResult,
    WhatIfScenario,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _obj_coverage() -> ObjectiveConfig:
    return ObjectiveConfig(
        name="coverage",
        display_name="Coverage",
        description="Schedule coverage",
        direction=ObjectiveDirection.MAXIMIZE,
        objective_type=ObjectiveType.COVERAGE,
        weight=0.5,
        reference_point=1.0,
        nadir_point=0.0,
    )


def _obj_equity() -> ObjectiveConfig:
    return ObjectiveConfig(
        name="equity",
        display_name="Equity",
        description="Workload equity",
        direction=ObjectiveDirection.MINIMIZE,
        objective_type=ObjectiveType.EQUITY,
        weight=0.5,
        reference_point=0.0,
        nadir_point=1.0,
    )


def _objectives() -> list[ObjectiveConfig]:
    return [_obj_coverage(), _obj_equity()]


def _solution(coverage: float, equity: float, **kw) -> Solution:
    return Solution(
        objective_values={"coverage": coverage, "equity": equity},
        **kw,
    )


def _frontier_with_solutions(
    solutions: list[Solution],
    objectives: list[ObjectiveConfig] | None = None,
) -> ParetoFrontier:
    objs = objectives or _objectives()
    frontier = ParetoFrontier(objectives=objs)
    for sol in solutions:
        frontier.add(sol)
    return frontier


# ---------------------------------------------------------------------------
# NavigationDirection enum
# ---------------------------------------------------------------------------


class TestNavigationDirection:
    def test_values(self):
        assert NavigationDirection.TOWARD_OBJECTIVE.value == "toward_objective"
        assert NavigationDirection.AWAY_FROM_OBJECTIVE.value == "away_from_objective"
        assert NavigationDirection.BALANCED.value == "balanced"
        assert NavigationDirection.EXTREME.value == "extreme"

    def test_all_members(self):
        assert len(NavigationDirection) == 4


# ---------------------------------------------------------------------------
# TradeOff dataclass
# ---------------------------------------------------------------------------


class TestTradeOffDataclass:
    def test_fields(self):
        sol_a = _solution(0.9, 0.3)
        sol_b = _solution(0.7, 0.1)
        t = TradeOff(
            objective_improved="equity",
            objective_degraded="coverage",
            improvement_amount=0.2,
            degradation_amount=0.2,
            trade_off_rate=1.0,
            solution_from=sol_a.id,
            solution_to=sol_b.id,
            is_favorable=False,
        )
        assert t.objective_improved == "equity"
        assert t.objective_degraded == "coverage"
        assert t.improvement_amount == 0.2
        assert t.degradation_amount == 0.2
        assert t.trade_off_rate == 1.0
        assert not t.is_favorable


# ---------------------------------------------------------------------------
# SolutionComparison dataclass
# ---------------------------------------------------------------------------


class TestSolutionComparisonDataclass:
    def test_fields(self):
        sol_a = _solution(0.9, 0.1)
        sol_b = _solution(0.7, 0.3)
        comp = SolutionComparison(
            solution_a=sol_a,
            solution_b=sol_b,
            dominance=DominanceRelation.DOMINATES,
            objective_differences={"coverage": 0.2, "equity": -0.2},
            trade_offs=[],
            recommended=sol_a,
            recommendation_reason="A dominates B",
        )
        assert comp.solution_a is sol_a
        assert comp.dominance == DominanceRelation.DOMINATES
        assert comp.recommended is sol_a


# ---------------------------------------------------------------------------
# NavigationStep dataclass
# ---------------------------------------------------------------------------


class TestNavigationStepDataclass:
    def test_fields(self):
        sol_a = _solution(0.5, 0.5)
        sol_b = _solution(0.7, 0.3)
        step = NavigationStep(
            from_solution=sol_a,
            to_solution=sol_b,
            direction=NavigationDirection.TOWARD_OBJECTIVE,
            objective_focus="coverage",
            step_size=0.3,
            remaining_options=2,
        )
        assert step.from_solution is sol_a
        assert step.to_solution is sol_b
        assert step.direction == NavigationDirection.TOWARD_OBJECTIVE
        assert step.objective_focus == "coverage"
        assert step.step_size == 0.3
        assert step.remaining_options == 2


# ---------------------------------------------------------------------------
# TradeOffAnalyzer
# ---------------------------------------------------------------------------


class TestTradeOffAnalyzerInit:
    def test_stores_objectives(self):
        objs = _objectives()
        analyzer = TradeOffAnalyzer(objs)
        assert len(analyzer.objectives) == 2
        assert len(analyzer.active_objectives) == 2

    def test_filters_constraints(self):
        constraint = ObjectiveConfig(
            name="duty_hours",
            display_name="Duty",
            description="Duty hours constraint",
            direction=ObjectiveDirection.MINIMIZE,
            objective_type=ObjectiveType.DUTY_HOURS,
            is_constraint=True,
        )
        objs = _objectives() + [constraint]
        analyzer = TradeOffAnalyzer(objs)
        assert len(analyzer.active_objectives) == 2


class TestAnalyzeTradeOff:
    def test_improvement_and_degradation(self):
        analyzer = TradeOffAnalyzer(_objectives())
        # sol_a: coverage=0.7, equity=0.3
        # sol_b: coverage=0.9, equity=0.5
        # Moving from a to b: coverage improves (MAX), equity degrades (MIN: 0.5>0.3)
        sol_a = _solution(0.7, 0.3)
        sol_b = _solution(0.9, 0.5)
        trade_offs = analyzer.analyze_trade_off(sol_a, sol_b)
        assert len(trade_offs) == 1
        assert trade_offs[0].objective_improved == "coverage"
        assert trade_offs[0].objective_degraded == "equity"

    def test_no_trade_off_when_dominating(self):
        analyzer = TradeOffAnalyzer(_objectives())
        # sol_a: coverage=0.7, equity=0.5
        # sol_b: coverage=0.9, equity=0.3 (better in both)
        sol_a = _solution(0.7, 0.5)
        sol_b = _solution(0.9, 0.3)
        trade_offs = analyzer.analyze_trade_off(sol_a, sol_b)
        # No degradation => no trade-off pairs
        assert len(trade_offs) == 0

    def test_favorable_when_rate_below_one(self):
        analyzer = TradeOffAnalyzer(_objectives())
        sol_a = _solution(0.5, 0.5)
        sol_b = _solution(0.9, 0.6)  # big coverage gain, small equity loss
        trade_offs = analyzer.analyze_trade_off(sol_a, sol_b)
        assert len(trade_offs) == 1
        assert trade_offs[0].is_favorable  # rate < 1.0

    def test_equal_solutions_no_trade_offs(self):
        analyzer = TradeOffAnalyzer(_objectives())
        sol_a = _solution(0.5, 0.5)
        sol_b = _solution(0.5, 0.5)
        trade_offs = analyzer.analyze_trade_off(sol_a, sol_b)
        assert len(trade_offs) == 0


class TestFindFavorableTradeOffs:
    def test_returns_empty_for_unknown_objective(self):
        analyzer = TradeOffAnalyzer(_objectives())
        frontier = _frontier_with_solutions([_solution(0.5, 0.5)])
        result = analyzer.find_favorable_trade_offs(frontier, "nonexistent")
        assert result == []

    def test_finds_favorable(self):
        analyzer = TradeOffAnalyzer(_objectives())
        sols = [
            _solution(0.9, 0.1),  # best coverage
            _solution(0.5, 0.5),
            _solution(0.1, 0.9),
        ]
        frontier = _frontier_with_solutions(sols)
        # Find favorable trade-offs for improving coverage
        result = analyzer.find_favorable_trade_offs(
            frontier, "coverage", max_degradation=10.0
        )
        # Should return pairs with best coverage solution
        assert isinstance(result, list)


class TestMarginalRateOfSubstitution:
    def test_calculates_mrs(self):
        analyzer = TradeOffAnalyzer(_objectives())
        sols = [
            _solution(0.3, 0.1),
            _solution(0.6, 0.4),
            _solution(0.9, 0.8),
        ]
        frontier = _frontier_with_solutions(sols)
        mrs = analyzer.calculate_marginal_rate_of_substitution(
            frontier, "coverage", "equity"
        )
        assert isinstance(mrs, list)
        assert len(mrs) == 2  # n-1 pairs

    def test_mrs_tuples_contain_solution_and_float(self):
        analyzer = TradeOffAnalyzer(_objectives())
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4)]
        frontier = _frontier_with_solutions(sols)
        mrs = analyzer.calculate_marginal_rate_of_substitution(
            frontier, "coverage", "equity"
        )
        assert len(mrs) == 1
        sol, rate = mrs[0]
        assert isinstance(sol, Solution)
        assert isinstance(rate, float)


# ---------------------------------------------------------------------------
# SolutionExplorer
# ---------------------------------------------------------------------------


class TestSolutionExplorerInit:
    def test_initial_state(self):
        frontier = _frontier_with_solutions([_solution(0.5, 0.5)])
        explorer = SolutionExplorer(frontier, _objectives())
        assert explorer.current_solution is None
        assert explorer.exploration_history == []
        assert explorer.bookmarks == []


class TestStartAtKnee:
    def test_sets_current_solution(self):
        sols = [_solution(0.3, 0.1), _solution(0.5, 0.5), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        knee = explorer.start_at_knee()
        assert knee is not None
        assert explorer.current_solution is knee
        assert len(explorer.exploration_history) == 1


class TestStartAtExtreme:
    def test_maximize_extreme(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        extreme = explorer.start_at_extreme("coverage")
        assert extreme is not None
        # Should be the solution with highest coverage
        assert extreme.objective_values["coverage"] == 0.9

    def test_minimize_extreme(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        extreme = explorer.start_at_extreme("equity")
        assert extreme is not None
        # Should be solution with lowest equity (minimize)
        assert extreme.objective_values["equity"] == 0.1

    def test_unknown_objective_returns_none(self):
        frontier = _frontier_with_solutions([_solution(0.5, 0.5)])
        explorer = SolutionExplorer(frontier, _objectives())
        result = explorer.start_at_extreme("nonexistent")
        assert result is None


class TestNavigate:
    def test_no_current_returns_empty(self):
        frontier = _frontier_with_solutions([_solution(0.5, 0.5)])
        explorer = SolutionExplorer(frontier, _objectives())
        steps = explorer.navigate(NavigationDirection.BALANCED)
        assert steps == []

    def test_toward_objective(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        explorer.start_at_extreme("equity")  # starts at equity=0.1 (best for MIN)
        steps = explorer.navigate(
            NavigationDirection.TOWARD_OBJECTIVE,
            objective="equity",
            step_count=1,
        )
        # From best equity (0.1), TOWARD means finding equity < 0.1 => none
        assert isinstance(steps, list)

    def test_navigate_balanced(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        explorer.start_at_extreme("coverage")  # starts at 0.9 coverage
        steps = explorer.navigate(NavigationDirection.BALANCED, step_count=1)
        assert isinstance(steps, list)


class TestFilterByBounds:
    def test_filters_within_bounds(self):
        # Non-dominated: higher coverage = higher equity (worse for MINIMIZE)
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        # Only solutions with coverage 0.4-0.7
        result = explorer.filter_by_bounds({"coverage": (0.4, 0.7)})
        assert len(result) == 1
        assert result[0].objective_values["coverage"] == 0.6

    def test_empty_when_no_match(self):
        # Non-dominated pair
        sols = [_solution(0.3, 0.1), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        result = explorer.filter_by_bounds({"coverage": (0.4, 0.8)})
        assert len(result) == 0

    def test_multiple_bounds(self):
        # Non-dominated set
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        result = explorer.filter_by_bounds(
            {"coverage": (0.5, 1.0), "equity": (0.0, 0.5)}
        )
        assert len(result) == 1  # only (0.6, 0.4)


class TestGetNeighborhood:
    def test_returns_nearby_solutions(self):
        # Non-dominated: (0.5, 0.3), (0.52, 0.32), (0.9, 0.8) — all on Pareto front
        sols = [_solution(0.5, 0.3), _solution(0.52, 0.32), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        center = frontier.solutions[0]
        neighbors = explorer.get_neighborhood(center, radius=0.1)
        # The nearby solution should be within radius
        assert len(neighbors) >= 1

    def test_excludes_center(self):
        sols = [_solution(0.5, 0.5)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        center = frontier.solutions[0]
        neighbors = explorer.get_neighborhood(center, radius=10.0)
        assert center not in neighbors


class TestBookmarks:
    def test_bookmark_current(self):
        frontier = _frontier_with_solutions(
            [_solution(0.5, 0.3), _solution(0.9, 0.8), _solution(0.3, 0.1)]
        )
        explorer = SolutionExplorer(frontier, _objectives())
        explorer.start_at_knee()
        explorer.bookmark()
        assert len(explorer.bookmarks) == 1

    def test_bookmark_specific(self):
        sols = [_solution(0.5, 0.3), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        explorer.bookmark(frontier.solutions[0])
        assert len(explorer.bookmarks) == 1

    def test_no_duplicate_bookmarks(self):
        sols = [_solution(0.5, 0.5)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        sol = frontier.solutions[0]
        explorer.bookmark(sol)
        explorer.bookmark(sol)
        assert len(explorer.bookmarks) == 1

    def test_bookmark_none_without_current(self):
        frontier = _frontier_with_solutions([_solution(0.5, 0.5)])
        explorer = SolutionExplorer(frontier, _objectives())
        explorer.bookmark()  # no current solution
        assert len(explorer.bookmarks) == 0


class TestCompareBookmarks:
    def test_pairwise_comparisons(self):
        # Non-dominated set for Pareto frontier
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        explorer = SolutionExplorer(frontier, _objectives())
        for sol in frontier.solutions:
            explorer.bookmark(sol)
        comparisons = explorer.compare_bookmarks()
        # 3 choose 2 = 3 comparisons
        assert len(comparisons) == 3
        for comp in comparisons:
            assert isinstance(comp, SolutionComparison)

    def test_empty_bookmarks(self):
        frontier = _frontier_with_solutions([_solution(0.5, 0.5)])
        explorer = SolutionExplorer(frontier, _objectives())
        comparisons = explorer.compare_bookmarks()
        assert comparisons == []


# ---------------------------------------------------------------------------
# PreferenceElicitor
# ---------------------------------------------------------------------------


class TestPreferenceElicitorInit:
    def test_equal_initial_weights(self):
        elicitor = PreferenceElicitor(_objectives())
        assert len(elicitor.inferred_weights) == 2
        assert abs(elicitor.inferred_weights["coverage"] - 0.5) < 0.01
        assert abs(elicitor.inferred_weights["equity"] - 0.5) < 0.01

    def test_empty_history(self):
        elicitor = PreferenceElicitor(_objectives())
        assert elicitor.comparisons == []
        assert elicitor.selections == []
        assert elicitor.reference_point == {}


class TestRecordComparison:
    def test_records_comparison(self):
        elicitor = PreferenceElicitor(_objectives())
        sol_a = _solution(0.9, 0.5)
        sol_b = _solution(0.5, 0.1)
        elicitor.record_comparison(sol_a, sol_b, preferred=0)
        assert len(elicitor.comparisons) == 1

    def test_updates_weights_prefer_coverage(self):
        elicitor = PreferenceElicitor(_objectives())
        # Prefer solution with better coverage (MAX) and worse equity (MIN)
        sol_a = _solution(0.9, 0.5)  # better coverage, worse equity
        sol_b = _solution(0.5, 0.1)  # worse coverage, better equity
        elicitor.record_comparison(sol_a, sol_b, preferred=0)
        # Coverage weight should increase, equity weight decrease
        assert (
            elicitor.inferred_weights["coverage"] > elicitor.inferred_weights["equity"]
        )

    def test_updates_weights_prefer_equity(self):
        elicitor = PreferenceElicitor(_objectives())
        sol_a = _solution(0.9, 0.5)
        sol_b = _solution(0.5, 0.1)
        elicitor.record_comparison(sol_a, sol_b, preferred=1)
        # Now equity weight should be higher
        assert (
            elicitor.inferred_weights["equity"] > elicitor.inferred_weights["coverage"]
        )

    def test_weights_sum_to_one(self):
        elicitor = PreferenceElicitor(_objectives())
        sol_a = _solution(0.9, 0.5)
        sol_b = _solution(0.5, 0.1)
        elicitor.record_comparison(sol_a, sol_b, preferred=0)
        total = sum(elicitor.inferred_weights.values())
        assert abs(total - 1.0) < 0.001


class TestRecordSelection:
    def test_records_selection(self):
        elicitor = PreferenceElicitor(_objectives())
        sol = _solution(0.7, 0.3)
        elicitor.record_selection(sol)
        assert len(elicitor.selections) == 1

    def test_updates_reference_point(self):
        elicitor = PreferenceElicitor(_objectives())
        sol = _solution(0.7, 0.3)
        elicitor.record_selection(sol)
        assert "coverage" in elicitor.reference_point
        assert "equity" in elicitor.reference_point
        assert elicitor.reference_point["coverage"] == 0.7

    def test_moving_average_reference(self):
        elicitor = PreferenceElicitor(_objectives())
        elicitor.record_selection(_solution(1.0, 0.0))
        elicitor.record_selection(_solution(0.0, 1.0))
        # Second selection: 0.7 * 1.0 + 0.3 * 0.0 = 0.7
        assert abs(elicitor.reference_point["coverage"] - 0.7) < 0.01


class TestGetPreferenceModel:
    def test_returns_articulator(self):
        elicitor = PreferenceElicitor(_objectives())
        model = elicitor.get_preference_model()
        assert model is not None

    def test_uses_reference_when_available(self):
        elicitor = PreferenceElicitor(_objectives())
        elicitor.record_selection(_solution(0.8, 0.2))
        model = elicitor.get_preference_model()
        assert model is not None


# ---------------------------------------------------------------------------
# WhatIfScenario / WhatIfResult dataclasses
# ---------------------------------------------------------------------------


class TestWhatIfScenario:
    def test_fields(self):
        scenario = WhatIfScenario(
            name="test",
            description="Test scenario",
            objective_adjustments={"coverage": 1.5},
            constraint_changes={},
        )
        assert scenario.name == "test"
        assert scenario.description == "Test scenario"
        assert scenario.objective_adjustments == {"coverage": 1.5}
        assert scenario.created_at is not None


class TestWhatIfResult:
    def test_fields(self):
        scenario = WhatIfScenario(
            name="t", description="d", objective_adjustments={}, constraint_changes={}
        )
        frontier = _frontier_with_solutions([_solution(0.5, 0.5)])
        result = WhatIfResult(
            scenario=scenario,
            original_frontier=frontier,
            modified_frontier=frontier,
            hypervolume_change=0.0,
            solution_count_change=0,
            new_solutions=[],
            lost_solutions=[],
            impact_summary="Neutral impact",
        )
        assert result.hypervolume_change == 0.0
        assert result.impact_summary == "Neutral impact"


# ---------------------------------------------------------------------------
# WhatIfAnalyzer
# ---------------------------------------------------------------------------


class TestWhatIfAnalyzer:
    def test_analyze_scenario(self):
        objs = _objectives()

        def evaluate_fn(sol: Solution, adjustments: dict) -> Solution:
            new_vals = {}
            for k, v in sol.objective_values.items():
                multiplier = adjustments.get(k, 1.0)
                new_vals[k] = v * multiplier
            return Solution(objective_values=new_vals)

        analyzer = WhatIfAnalyzer(objs, evaluate_fn)
        frontier = _frontier_with_solutions(
            [_solution(0.5, 0.3), _solution(0.8, 0.6), _solution(0.3, 0.1)]
        )
        scenario = WhatIfScenario(
            name="boost_coverage",
            description="Increase coverage weight",
            objective_adjustments={"coverage": 1.2},
            constraint_changes={},
        )
        result = analyzer.analyze_scenario(scenario, frontier)
        assert isinstance(result, WhatIfResult)
        assert result.scenario is scenario
        assert result.original_frontier is frontier
        assert isinstance(result.impact_summary, str)

    def test_positive_hypervolume_change(self):
        objs = _objectives()

        def evaluate_fn(sol: Solution, adjustments: dict) -> Solution:
            new_vals = {}
            for k, v in sol.objective_values.items():
                new_vals[k] = v * adjustments.get(k, 1.0)
            return Solution(objective_values=new_vals)

        analyzer = WhatIfAnalyzer(objs, evaluate_fn)
        frontier = _frontier_with_solutions([_solution(0.5, 0.5)])
        scenario = WhatIfScenario(
            name="improve",
            description="Improve both",
            objective_adjustments={"coverage": 2.0, "equity": 0.5},
            constraint_changes={},
        )
        result = analyzer.analyze_scenario(scenario, frontier)
        # Result should have some impact summary
        assert "impact" in result.impact_summary.lower()


# ---------------------------------------------------------------------------
# DecisionMaker
# ---------------------------------------------------------------------------


class TestDecisionMakerInit:
    def test_creates_components(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        assert dm.trade_off_analyzer is not None
        assert dm.explorer is not None
        assert dm.preference_elicitor is not None
        assert dm.selected_solution is None
        assert dm.decision_history == []


class TestGetOverview:
    def test_returns_dict(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        overview = dm.get_overview()
        assert isinstance(overview, dict)
        assert "frontier_size" in overview
        assert "objectives" in overview
        assert "quality" in overview
        assert "knee_solution" in overview

    def test_frontier_size(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        overview = dm.get_overview()
        assert overview["frontier_size"] == len(frontier)


class TestRecommendStartingPoint:
    def test_returns_knee_without_preferences(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        rec = dm.recommend_starting_point()
        assert rec is not None
        assert isinstance(rec, Solution)

    def test_uses_preferences_when_available(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        dm.select_solution(frontier.solutions[0])
        rec = dm.recommend_starting_point()
        assert rec is not None


class TestCompareSolutions:
    def test_dominating(self):
        # Create two solutions directly (not via frontier which filters dominated)
        sol_good = _solution(0.9, 0.2)  # better in both: higher coverage, lower equity
        sol_bad = _solution(0.3, 0.8)  # worse in both
        # Use a frontier with the good solution only
        frontier = _frontier_with_solutions([sol_good])
        dm = DecisionMaker(frontier, _objectives())
        comp = dm.compare_solutions(sol_good, sol_bad)
        assert isinstance(comp, SolutionComparison)
        assert comp.dominance == DominanceRelation.DOMINATES
        assert comp.recommended is sol_good
        assert "dominates" in comp.recommendation_reason.lower()

    def test_incomparable(self):
        # Non-dominated pair: trade-off between coverage and equity
        sols = [_solution(0.9, 0.8), _solution(0.3, 0.2)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        comp = dm.compare_solutions(frontier.solutions[0], frontier.solutions[1])
        assert comp.dominance == DominanceRelation.INCOMPARABLE
        assert comp.recommended is None
        assert "trade-off" in comp.recommendation_reason.lower()


class TestRecordPreference:
    def test_records_in_history(self):
        # Non-dominated pair
        sols = [_solution(0.3, 0.1), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        dm.record_preference(frontier.solutions[0], frontier.solutions[1], 0)
        assert len(dm.decision_history) == 1
        assert dm.decision_history[0]["type"] == "comparison"

    def test_updates_elicitor(self):
        sols = [_solution(0.3, 0.1), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        dm.record_preference(frontier.solutions[0], frontier.solutions[1], 0)
        assert len(dm.preference_elicitor.comparisons) == 1


class TestSelectSolution:
    def test_sets_selected(self):
        sols = [_solution(0.5, 0.5)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        dm.select_solution(frontier.solutions[0])
        assert dm.selected_solution is frontier.solutions[0]

    def test_records_in_history(self):
        sols = [_solution(0.5, 0.5)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        dm.select_solution(frontier.solutions[0])
        assert len(dm.decision_history) == 1
        assert dm.decision_history[0]["type"] == "selection"

    def test_updates_elicitor_selections(self):
        sols = [_solution(0.5, 0.5)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        dm.select_solution(frontier.solutions[0])
        assert len(dm.preference_elicitor.selections) == 1


class TestGetRecommendation:
    def test_knee_when_no_preferences(self):
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        sol, explanation = dm.get_recommendation()
        assert "knee" in explanation.lower() or "no preferences" in explanation.lower()

    def test_preference_based_recommendation(self):
        # Non-dominated set
        sols = [_solution(0.3, 0.1), _solution(0.6, 0.4), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        # Record preference for high-coverage solution over low-coverage
        dm.record_preference(frontier.solutions[2], frontier.solutions[0], 0)
        sol, explanation = dm.get_recommendation()
        assert sol is not None
        assert "prioritizing" in explanation.lower()


class TestGetDecisionSummary:
    def test_initial_summary(self):
        sols = [_solution(0.5, 0.5)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        summary = dm.get_decision_summary()
        assert summary["comparisons_made"] == 0
        assert summary["selections_made"] == 0
        assert summary["selected_solution"] is None
        assert summary["history_length"] == 0

    def test_summary_after_actions(self):
        # Non-dominated pair
        sols = [_solution(0.3, 0.1), _solution(0.9, 0.8)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        dm.record_preference(frontier.solutions[0], frontier.solutions[1], 0)
        dm.select_solution(frontier.solutions[0])
        summary = dm.get_decision_summary()
        assert summary["comparisons_made"] == 1
        assert summary["selections_made"] == 1
        assert summary["selected_solution"] is not None
        assert summary["history_length"] == 2

    def test_inferred_weights_present(self):
        sols = [_solution(0.5, 0.5)]
        frontier = _frontier_with_solutions(sols)
        dm = DecisionMaker(frontier, _objectives())
        summary = dm.get_decision_summary()
        assert "coverage" in summary["inferred_weights"]
        assert "equity" in summary["inferred_weights"]
