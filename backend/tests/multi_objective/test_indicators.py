"""Tests for quality indicators for multi-objective optimization (no DB)."""

import numpy as np
import pytest

from app.multi_objective.core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    ParetoFrontier,
    Solution,
)
from app.multi_objective.indicators import (
    EpsilonIndicator,
    GenerationalDistance,
    HypervolumeIndicator,
    InvertedGenerationalDistance,
    MaximumSpread,
    QualityEvaluator,
    QualityReport,
    Spacing,
    SpreadIndicator,
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
    return Solution(objective_values={"coverage": coverage, "equity": equity}, **kw)


def _frontier_with_solutions(
    solutions: list[Solution],
    objectives: list[ObjectiveConfig] | None = None,
) -> ParetoFrontier:
    objs = objectives or _objectives()
    frontier = ParetoFrontier(objectives=objs)
    for sol in solutions:
        frontier.add(sol)
    return frontier


def _non_dominated_3() -> list[Solution]:
    """Three non-dominated solutions (higher coverage = higher/worse equity)."""
    return [
        _solution(0.3, 0.1),
        _solution(0.6, 0.4),
        _solution(0.9, 0.8),
    ]


def _non_dominated_5() -> list[Solution]:
    """Five non-dominated solutions."""
    return [
        _solution(0.2, 0.05),
        _solution(0.4, 0.2),
        _solution(0.6, 0.4),
        _solution(0.8, 0.65),
        _solution(0.95, 0.9),
    ]


# ---------------------------------------------------------------------------
# HypervolumeIndicator
# ---------------------------------------------------------------------------


class TestHypervolumeIndicator:
    def test_name(self):
        hv = HypervolumeIndicator()
        assert hv.name == "hypervolume"

    def test_is_higher_better(self):
        hv = HypervolumeIndicator()
        assert hv.is_higher_better is True

    def test_empty_front(self):
        hv = HypervolumeIndicator()
        front = ParetoFrontier(objectives=_objectives())
        assert hv.calculate(front) == 0.0

    def test_single_solution(self):
        hv = HypervolumeIndicator()
        front = _frontier_with_solutions([_solution(0.5, 0.5)])
        result = hv.calculate(front)
        assert result >= 0.0

    def test_two_solutions(self):
        hv = HypervolumeIndicator()
        front = _frontier_with_solutions(_non_dominated_3()[:2])
        result = hv.calculate(front)
        assert result > 0.0

    def test_more_solutions_larger_hv(self):
        hv = HypervolumeIndicator()
        small = _frontier_with_solutions(_non_dominated_3()[:2])
        large = _frontier_with_solutions(_non_dominated_3())
        hv_small = hv.calculate(small)
        hv_large = hv.calculate(large)
        assert hv_large >= hv_small

    def test_custom_reference_point(self):
        ref = np.array([2.0, 2.0])
        hv = HypervolumeIndicator(reference_point=ref)
        front = _frontier_with_solutions([_solution(0.5, 0.5)])
        result = hv.calculate(front)
        assert result > 0.0

    def test_get_normalized_points_negates_maximize(self):
        hv = HypervolumeIndicator()
        front = _frontier_with_solutions([_solution(0.8, 0.3)])
        points = hv._get_normalized_points(front)
        # coverage MAXIMIZE → negated; equity MINIMIZE → unchanged
        assert points[0, 0] == -0.8
        assert points[0, 1] == 0.3


# ---------------------------------------------------------------------------
# GenerationalDistance
# ---------------------------------------------------------------------------


class TestGenerationalDistance:
    def test_name(self):
        gd = GenerationalDistance()
        assert gd.name == "generational_distance"

    def test_is_higher_better(self):
        gd = GenerationalDistance()
        assert gd.is_higher_better is False

    def test_empty_front(self):
        gd = GenerationalDistance()
        front = ParetoFrontier(objectives=_objectives())
        ref = _frontier_with_solutions(_non_dominated_3())
        assert gd.calculate(front, ref) == float("inf")

    def test_empty_reference(self):
        gd = GenerationalDistance()
        front = _frontier_with_solutions(_non_dominated_3())
        assert gd.calculate(front, None) == float("inf")

    def test_same_front(self):
        gd = GenerationalDistance()
        sols = _non_dominated_3()
        front = _frontier_with_solutions(sols)
        # When front == reference, GD should be 0 (or very close)
        result = gd.calculate(front, front)
        assert result < 1e-10

    def test_distant_front(self):
        gd = GenerationalDistance()
        objs = _objectives()
        front = _frontier_with_solutions([_solution(0.1, 0.01)], objs)
        ref = _frontier_with_solutions([_solution(0.9, 0.8)], objs)
        result = gd.calculate(front, ref)
        assert result > 0

    def test_custom_p(self):
        gd = GenerationalDistance(p=1.0)
        assert gd.p == 1.0


# ---------------------------------------------------------------------------
# InvertedGenerationalDistance
# ---------------------------------------------------------------------------


class TestInvertedGenerationalDistance:
    def test_name(self):
        igd = InvertedGenerationalDistance()
        assert igd.name == "inverted_generational_distance"

    def test_is_higher_better(self):
        igd = InvertedGenerationalDistance()
        assert igd.is_higher_better is False

    def test_empty_front(self):
        igd = InvertedGenerationalDistance()
        front = ParetoFrontier(objectives=_objectives())
        ref = _frontier_with_solutions(_non_dominated_3())
        assert igd.calculate(front, ref) == float("inf")

    def test_same_front(self):
        igd = InvertedGenerationalDistance()
        front = _frontier_with_solutions(_non_dominated_3())
        result = igd.calculate(front, front)
        assert result < 1e-10

    def test_better_coverage_lower_igd(self):
        igd = InvertedGenerationalDistance()
        objs = _objectives()
        ref = _frontier_with_solutions(_non_dominated_5(), objs)
        # Subset vs full set
        partial = _frontier_with_solutions(_non_dominated_5()[:2], objs)
        full = _frontier_with_solutions(_non_dominated_5(), objs)
        igd_partial = igd.calculate(partial, ref)
        igd_full = igd.calculate(full, ref)
        assert igd_full <= igd_partial


# ---------------------------------------------------------------------------
# SpreadIndicator
# ---------------------------------------------------------------------------


class TestSpreadIndicator:
    def test_name(self):
        si = SpreadIndicator()
        assert si.name == "spread"

    def test_is_higher_better(self):
        si = SpreadIndicator()
        assert si.is_higher_better is False

    def test_single_solution(self):
        si = SpreadIndicator()
        front = _frontier_with_solutions([_solution(0.5, 0.5)])
        assert si.calculate(front) == float("inf")

    def test_two_solutions(self):
        si = SpreadIndicator()
        front = _frontier_with_solutions([_solution(0.3, 0.1), _solution(0.9, 0.8)])
        result = si.calculate(front)
        # Two solutions → single distance, spread = 0
        assert result == 0.0

    def test_multiple_solutions(self):
        si = SpreadIndicator()
        front = _frontier_with_solutions(_non_dominated_5())
        result = si.calculate(front)
        assert result >= 0.0

    def test_uniform_spread_low(self):
        si = SpreadIndicator()
        # Evenly spaced solutions should have low spread
        sols = [_solution(0.2 * i, 0.1 * i) for i in range(1, 6)]
        front = _frontier_with_solutions(sols)
        result = si.calculate(front)
        assert result < 1.0  # Fairly uniform


# ---------------------------------------------------------------------------
# EpsilonIndicator
# ---------------------------------------------------------------------------


class TestEpsilonIndicator:
    def test_name_additive(self):
        ei = EpsilonIndicator(additive=True)
        assert ei.name == "epsilon_additive"

    def test_name_multiplicative(self):
        ei = EpsilonIndicator(additive=False)
        assert ei.name == "epsilon_multiplicative"

    def test_is_higher_better(self):
        ei = EpsilonIndicator()
        assert ei.is_higher_better is False

    def test_empty_front(self):
        ei = EpsilonIndicator()
        front = ParetoFrontier(objectives=_objectives())
        ref = _frontier_with_solutions(_non_dominated_3())
        assert ei.calculate(front, ref) == float("inf")

    def test_no_reference(self):
        ei = EpsilonIndicator()
        front = _frontier_with_solutions(_non_dominated_3())
        assert ei.calculate(front, None) == float("inf")

    def test_same_front_additive(self):
        ei = EpsilonIndicator(additive=True)
        front = _frontier_with_solutions(_non_dominated_3())
        result = ei.calculate(front, front)
        # Same front → epsilon = 0
        assert abs(result) < 1e-10

    def test_worse_front_positive_epsilon(self):
        ei = EpsilonIndicator(additive=True)
        objs = _objectives()
        ref = _frontier_with_solutions([_solution(0.9, 0.1)], objs)
        worse = _frontier_with_solutions([_solution(0.3, 0.8)], objs)
        result = ei.calculate(worse, ref)
        # Worse front needs positive shift to dominate reference
        assert result > 0


# ---------------------------------------------------------------------------
# Spacing
# ---------------------------------------------------------------------------


class TestSpacing:
    def test_name(self):
        sp = Spacing()
        assert sp.name == "spacing"

    def test_is_higher_better(self):
        sp = Spacing()
        assert sp.is_higher_better is False

    def test_single_solution(self):
        sp = Spacing()
        front = _frontier_with_solutions([_solution(0.5, 0.5)])
        assert sp.calculate(front) == 0.0

    def test_two_solutions(self):
        sp = Spacing()
        front = _frontier_with_solutions([_solution(0.3, 0.1), _solution(0.9, 0.8)])
        result = sp.calculate(front)
        # Two solutions → one distance, spacing = 0
        assert result == 0.0

    def test_uniform_spacing_low(self):
        sp = Spacing()
        sols = [_solution(0.2 * i, 0.1 * i) for i in range(1, 6)]
        front = _frontier_with_solutions(sols)
        result = sp.calculate(front)
        # Evenly spaced → low spacing
        assert result < 0.5


# ---------------------------------------------------------------------------
# MaximumSpread
# ---------------------------------------------------------------------------


class TestMaximumSpread:
    def test_name(self):
        ms = MaximumSpread()
        assert ms.name == "maximum_spread"

    def test_is_higher_better(self):
        ms = MaximumSpread()
        assert ms.is_higher_better is True

    def test_single_solution(self):
        ms = MaximumSpread()
        front = _frontier_with_solutions([_solution(0.5, 0.5)])
        assert ms.calculate(front) == 0.0

    def test_two_solutions(self):
        ms = MaximumSpread()
        front = _frontier_with_solutions([_solution(0.3, 0.1), _solution(0.9, 0.8)])
        result = ms.calculate(front)
        assert result > 0.0

    def test_wider_front_more_spread(self):
        ms = MaximumSpread()
        objs = _objectives()
        narrow = _frontier_with_solutions(
            [_solution(0.4, 0.3), _solution(0.6, 0.5)], objs
        )
        wide = _frontier_with_solutions(
            [_solution(0.1, 0.05), _solution(0.95, 0.9)], objs
        )
        ms_narrow = ms.calculate(narrow)
        ms_wide = ms.calculate(wide)
        assert ms_wide > ms_narrow


# ---------------------------------------------------------------------------
# QualityReport dataclass
# ---------------------------------------------------------------------------


class TestQualityReport:
    def test_construction(self):
        report = QualityReport(front_size=10)
        assert report.front_size == 10
        assert report.hypervolume is None
        assert report.generational_distance is None

    def test_with_values(self):
        report = QualityReport(
            front_size=5,
            hypervolume=0.8,
            spacing=0.1,
            maximum_spread=1.5,
        )
        assert report.hypervolume == 0.8
        assert report.spacing == 0.1
        assert report.maximum_spread == 1.5

    def test_default_lists(self):
        report = QualityReport(front_size=3)
        assert report.ideal_point == []
        assert report.nadir_point == []
        assert report.objective_names == []


# ---------------------------------------------------------------------------
# QualityEvaluator
# ---------------------------------------------------------------------------


class TestQualityEvaluator:
    def test_default_indicators(self):
        qe = QualityEvaluator()
        assert len(qe.indicators) == 7

    def test_custom_indicators(self):
        qe = QualityEvaluator(indicators=[Spacing(), MaximumSpread()])
        assert len(qe.indicators) == 2

    def test_evaluate_returns_report(self):
        qe = QualityEvaluator()
        front = _frontier_with_solutions(_non_dominated_3())
        report = qe.evaluate(front)
        assert isinstance(report, QualityReport)
        assert report.front_size == 3

    def test_evaluate_fills_hypervolume(self):
        qe = QualityEvaluator()
        front = _frontier_with_solutions(_non_dominated_3())
        report = qe.evaluate(front)
        assert report.hypervolume is not None
        assert report.hypervolume > 0

    def test_evaluate_fills_spacing(self):
        qe = QualityEvaluator()
        front = _frontier_with_solutions(_non_dominated_3())
        report = qe.evaluate(front)
        assert report.spacing is not None

    def test_evaluate_fills_maximum_spread(self):
        qe = QualityEvaluator()
        front = _frontier_with_solutions(_non_dominated_3())
        report = qe.evaluate(front)
        assert report.maximum_spread is not None
        assert report.maximum_spread > 0

    def test_evaluate_with_reference_front(self):
        qe = QualityEvaluator()
        front = _frontier_with_solutions(_non_dominated_3())
        ref = _frontier_with_solutions(_non_dominated_5())
        report = qe.evaluate(front, ref)
        assert report.generational_distance is not None

    def test_compare_fronts(self):
        qe = QualityEvaluator()
        f1 = _frontier_with_solutions(_non_dominated_3())
        f2 = _frontier_with_solutions(_non_dominated_5())
        results = qe.compare_fronts([("run1", f1), ("run2", f2)])
        assert "run1" in results
        assert "run2" in results
        assert isinstance(results["run1"], QualityReport)
        assert isinstance(results["run2"], QualityReport)

    def test_evaluate_objective_names(self):
        qe = QualityEvaluator()
        front = _frontier_with_solutions(_non_dominated_3())
        report = qe.evaluate(front)
        assert "coverage" in report.objective_names
        assert "equity" in report.objective_names
