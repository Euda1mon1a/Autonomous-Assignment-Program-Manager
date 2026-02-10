"""Tests for preference articulation methods (no DB)."""

from __future__ import annotations

import numpy as np
import pytest

from app.multi_objective.core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    ParetoFrontier,
    Solution,
)
from app.multi_objective.preferences import (
    AchievementScalarizing,
    InteractivePreferenceElicitor,
    LexicographicOrdering,
    LightBeamSearch,
    PreferenceArticulator,
    PreferenceElicitationState,
    PreferenceType,
    ReferencePoint,
    ScalarizingFunction,
    WeightedSum,
    WierzbickiASF,
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


def _solution(coverage: float, equity: float) -> Solution:
    return Solution(objective_values={"coverage": coverage, "equity": equity})


def _frontier(solutions: list[Solution] | None = None) -> ParetoFrontier:
    if solutions is None:
        solutions = [
            _solution(0.9, 0.5),
            _solution(0.7, 0.2),
            _solution(0.5, 0.1),
            _solution(0.8, 0.3),
        ]
    return ParetoFrontier(solutions=solutions, objectives=_objectives())


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestPreferenceType:
    def test_values(self):
        assert PreferenceType.A_PRIORI.value == "a_priori"
        assert PreferenceType.A_POSTERIORI.value == "a_posteriori"
        assert PreferenceType.INTERACTIVE.value == "interactive"


class TestScalarizingFunction:
    def test_values(self):
        assert ScalarizingFunction.WEIGHTED_SUM.value == "weighted_sum"
        assert ScalarizingFunction.TCHEBYCHEFF.value == "tchebycheff"
        assert ScalarizingFunction.PBI.value == "pbi"
        assert ScalarizingFunction.WIERZBICKI.value == "wierzbicki"

    def test_member_count(self):
        assert len(ScalarizingFunction) == 5


# ---------------------------------------------------------------------------
# ReferencePoint
# ---------------------------------------------------------------------------


class TestReferencePoint:
    def test_construction(self):
        rp = ReferencePoint(values={"coverage": 0.9, "equity": 0.1})
        assert rp.values["coverage"] == 0.9
        assert rp.is_aspiration is True
        assert rp.is_reservation is False

    def test_to_vector(self):
        rp = ReferencePoint(
            values={"coverage": 0.9, "equity": 0.1},
            objective_names=["coverage", "equity"],
        )
        vec = rp.to_vector()
        assert abs(vec[0] - 0.9) < 1e-10
        assert abs(vec[1] - 0.1) < 1e-10

    def test_to_vector_custom_order(self):
        rp = ReferencePoint(values={"coverage": 0.9, "equity": 0.1})
        vec = rp.to_vector(["equity", "coverage"])
        assert abs(vec[0] - 0.1) < 1e-10
        assert abs(vec[1] - 0.9) < 1e-10

    def test_to_vector_missing_key(self):
        rp = ReferencePoint(values={"coverage": 0.9})
        vec = rp.to_vector(["coverage", "equity"])
        assert abs(vec[1] - 0.0) < 1e-10

    def test_from_solution(self):
        sol = _solution(0.8, 0.3)
        rp = ReferencePoint.from_solution(sol)
        assert rp.values["coverage"] == 0.8
        assert rp.values["equity"] == 0.3


# ---------------------------------------------------------------------------
# WeightedSum
# ---------------------------------------------------------------------------


class TestWeightedSum:
    def test_preference_type(self):
        ws = WeightedSum({"coverage": 0.5, "equity": 0.5})
        assert ws.preference_type == PreferenceType.A_PRIORI

    def test_normalizes_weights(self):
        ws = WeightedSum({"coverage": 2.0, "equity": 3.0})
        assert abs(ws.weights["coverage"] - 0.4) < 1e-10
        assert abs(ws.weights["equity"] - 0.6) < 1e-10

    def test_score_equal_weights(self):
        ws = WeightedSum({"coverage": 1.0, "equity": 1.0})
        sol = _solution(0.8, 0.3)
        score = ws.score(sol, _objectives())
        # coverage: MAXIMIZE -> -0.8, equity: MINIMIZE -> 0.3
        # score = 0.5*(-0.8) + 0.5*(0.3) = -0.25
        assert abs(score - (-0.25)) < 1e-10

    def test_score_coverage_only(self):
        ws = WeightedSum({"coverage": 1.0, "equity": 0.0})
        sol = _solution(0.8, 0.3)
        score = ws.score(sol, _objectives())
        # 1.0 * (-0.8) = -0.8
        assert abs(score - (-0.8)) < 1e-10

    def test_rank_solutions(self):
        ws = WeightedSum({"coverage": 1.0, "equity": 0.0})
        solutions = [_solution(0.5, 0.1), _solution(0.9, 0.5)]
        ranked = ws.rank_solutions(solutions, _objectives())
        # Higher coverage is better (MAXIMIZE -> -value -> lower score)
        assert ranked[0][0].objective_values["coverage"] == 0.9

    def test_rank_preserves_all(self):
        ws = WeightedSum({"coverage": 0.5, "equity": 0.5})
        solutions = [_solution(0.5, 0.1), _solution(0.9, 0.5), _solution(0.7, 0.2)]
        ranked = ws.rank_solutions(solutions, _objectives())
        assert len(ranked) == 3


# ---------------------------------------------------------------------------
# AchievementScalarizing
# ---------------------------------------------------------------------------


class TestAchievementScalarizing:
    def test_preference_type(self):
        rp = ReferencePoint(
            values={"coverage": 0.9, "equity": 0.1},
            objective_names=["coverage", "equity"],
        )
        asf = AchievementScalarizing(rp)
        assert asf.preference_type == PreferenceType.A_PRIORI

    def test_at_reference_point(self):
        rp = ReferencePoint(
            values={"coverage": 0.8, "equity": 0.3},
            objective_names=["coverage", "equity"],
        )
        asf = AchievementScalarizing(rp, rho=0.0)
        sol = _solution(0.8, 0.3)
        score = asf.score(sol, _objectives())
        # All deviations are 0 -> max_deviation = 0, sum_deviation = 0
        assert abs(score) < 1e-10

    def test_worse_than_reference(self):
        rp = ReferencePoint(
            values={"coverage": 0.9, "equity": 0.1},
            objective_names=["coverage", "equity"],
        )
        asf = AchievementScalarizing(rp, rho=0.0)
        sol = _solution(0.5, 0.5)
        score = asf.score(sol, _objectives())
        # coverage: MAXIMIZE -> -0.5 vs -0.9, deviation = 1.0*((-0.5)-(-0.9)) = 0.4
        # equity: MINIMIZE -> 0.5 vs 0.1, deviation = 1.0*(0.5-0.1) = 0.4
        # max_deviation = 0.4
        assert score > 0

    def test_better_than_reference(self):
        rp = ReferencePoint(
            values={"coverage": 0.5, "equity": 0.5},
            objective_names=["coverage", "equity"],
        )
        asf = AchievementScalarizing(rp, rho=0.0)
        sol = _solution(0.9, 0.1)
        score = asf.score(sol, _objectives())
        # coverage: -0.9 vs -0.5, deviation = 1.0*(-0.9-(-0.5)) = -0.4
        # equity: 0.1 vs 0.5, deviation = 1.0*(0.1-0.5) = -0.4
        # max_deviation = -0.4
        assert score < 0

    def test_augmentation_term(self):
        rp = ReferencePoint(
            values={"coverage": 0.8, "equity": 0.3},
            objective_names=["coverage", "equity"],
        )
        asf_no_aug = AchievementScalarizing(rp, rho=0.0)
        asf_aug = AchievementScalarizing(rp, rho=0.1)
        sol = _solution(0.8, 0.3)
        assert abs(asf_no_aug.score(sol, _objectives())) < 1e-10
        assert abs(asf_aug.score(sol, _objectives())) < 1e-10  # Both 0 at ref


# ---------------------------------------------------------------------------
# WierzbickiASF
# ---------------------------------------------------------------------------


class TestWierzbickiASF:
    def test_preference_type(self):
        aspiration = ReferencePoint(values={"coverage": 0.9, "equity": 0.1})
        asf = WierzbickiASF(aspiration)
        assert asf.preference_type == PreferenceType.A_PRIORI

    def test_at_aspiration(self):
        aspiration = ReferencePoint(values={"coverage": 0.8, "equity": 0.3})
        asf = WierzbickiASF(aspiration, rho=0.0)
        sol = _solution(0.8, 0.3)
        score = asf.score(sol, _objectives())
        assert abs(score) < 1e-10

    def test_with_reservation(self):
        aspiration = ReferencePoint(values={"coverage": 0.9, "equity": 0.1})
        reservation = ReferencePoint(values={"coverage": 0.5, "equity": 0.5})
        asf = WierzbickiASF(aspiration, reservation, rho=0.0)
        sol = _solution(0.7, 0.3)
        score = asf.score(sol, _objectives())
        # Deviations are scaled by range (reservation - aspiration)
        assert isinstance(score, float)


# ---------------------------------------------------------------------------
# LexicographicOrdering
# ---------------------------------------------------------------------------


class TestLexicographicOrdering:
    def test_preference_type(self):
        lex = LexicographicOrdering(["coverage", "equity"])
        assert lex.preference_type == PreferenceType.A_PRIORI

    def test_score_primary_dominates(self):
        lex = LexicographicOrdering(["coverage", "equity"])
        sol_good = _solution(0.9, 0.3)
        sol_bad = _solution(0.5, 0.3)
        # Use objectives without reference/nadir to avoid normalization
        # (normalization + MAXIMIZE negation double-counts direction)
        bare_objs = [
            ObjectiveConfig(
                name="coverage",
                display_name="Coverage",
                description="Coverage",
                direction=ObjectiveDirection.MAXIMIZE,
                objective_type=ObjectiveType.COVERAGE,
                weight=0.5,
            ),
            ObjectiveConfig(
                name="equity",
                display_name="Equity",
                description="Equity",
                direction=ObjectiveDirection.MINIMIZE,
                objective_type=ObjectiveType.EQUITY,
                weight=0.5,
            ),
        ]
        # MAXIMIZE -> -value: -0.9 < -0.5, so sol_good has lower (better) score
        assert lex.score(sol_good, bare_objs) < lex.score(sol_bad, bare_objs)

    def test_compare_prefers_first(self):
        lex = LexicographicOrdering(["coverage", "equity"])
        sol1 = _solution(0.9, 0.5)
        sol2 = _solution(0.5, 0.1)
        assert lex.compare(sol1, sol2, _objectives()) == -1

    def test_compare_prefers_second(self):
        lex = LexicographicOrdering(["coverage", "equity"])
        sol1 = _solution(0.5, 0.1)
        sol2 = _solution(0.9, 0.5)
        assert lex.compare(sol1, sol2, _objectives()) == 1

    def test_compare_equal(self):
        lex = LexicographicOrdering(["coverage", "equity"], epsilon=0.01)
        sol1 = _solution(0.8, 0.3)
        sol2 = _solution(0.8, 0.3)
        assert lex.compare(sol1, sol2, _objectives()) == 0

    def test_compare_tiebreak_on_second(self):
        lex = LexicographicOrdering(["coverage", "equity"], epsilon=0.01)
        sol1 = _solution(0.8, 0.2)
        sol2 = _solution(0.8, 0.5)
        # Same coverage, sol1 has better equity (MINIMIZE -> lower is better)
        assert lex.compare(sol1, sol2, _objectives()) == -1


# ---------------------------------------------------------------------------
# LightBeamSearch
# ---------------------------------------------------------------------------


class TestLightBeamSearch:
    def test_preference_type(self):
        rp = ReferencePoint(values={"coverage": 0.9, "equity": 0.1})
        lbs = LightBeamSearch(rp, {"coverage": 1.0, "equity": 0.0})
        assert lbs.preference_type == PreferenceType.INTERACTIVE

    def test_score_on_beam(self):
        rp = ReferencePoint(values={"coverage": 1.0, "equity": 0.0})
        ideal = {"coverage": 0.0, "equity": 0.0}
        lbs = LightBeamSearch(rp, ideal, beam_width=0.1)
        # Solution on beam direction (coverage axis)
        sol = _solution(0.5, 0.0)
        score = lbs.score(sol, _objectives())
        assert isinstance(score, float)

    def test_score_off_beam_higher(self):
        rp = ReferencePoint(values={"coverage": 1.0, "equity": 0.0})
        ideal = {"coverage": 0.0, "equity": 0.0}
        lbs = LightBeamSearch(rp, ideal, beam_width=0.1)
        sol_on = _solution(0.5, 0.0)
        sol_off = _solution(0.5, 0.5)
        # Off-beam should have higher score (worse)
        assert lbs.score(sol_off, _objectives()) > lbs.score(sol_on, _objectives())

    def test_zero_direction(self):
        rp = ReferencePoint(values={"coverage": 0.0, "equity": 0.0})
        ideal = {"coverage": 0.0, "equity": 0.0}
        lbs = LightBeamSearch(rp, ideal)
        sol = _solution(0.5, 0.5)
        score = lbs.score(sol, _objectives())
        # Falls back to norm(f - z)
        assert score > 0


# ---------------------------------------------------------------------------
# PreferenceElicitationState
# ---------------------------------------------------------------------------


class TestPreferenceElicitationState:
    def test_defaults(self):
        state = PreferenceElicitationState()
        assert state.iteration == 0
        assert state.current_reference is None
        assert state.reference_history == []
        assert state.selected_solutions == []
        assert state.feedback_history == []
        assert state.is_complete is False


# ---------------------------------------------------------------------------
# InteractivePreferenceElicitor
# ---------------------------------------------------------------------------


class TestInteractivePreferenceElicitor:
    def test_init(self):
        ipe = InteractivePreferenceElicitor(_objectives())
        assert ipe.initial_samples == 5
        assert ipe.max_iterations == 10
        assert ipe.state.iteration == 0

    def test_start_elicitation(self):
        ipe = InteractivePreferenceElicitor(_objectives(), initial_samples=3)
        frontier = _frontier()
        reps = ipe.start_elicitation(frontier)
        assert len(reps) <= 3
        assert ipe.state.iteration == 0

    def test_done_feedback(self):
        ipe = InteractivePreferenceElicitor(_objectives())
        frontier = _frontier()
        ipe.start_elicitation(frontier)
        result = ipe.process_feedback("done", {}, frontier)
        assert ipe.state.is_complete is True

    def test_reference_feedback(self):
        ipe = InteractivePreferenceElicitor(_objectives(), initial_samples=2)
        frontier = _frontier()
        ipe.start_elicitation(frontier)
        result = ipe.process_feedback(
            "reference",
            {"reference": {"coverage": 0.8, "equity": 0.2}},
            frontier,
        )
        assert len(result) <= 2
        assert ipe.state.current_reference is not None
        assert ipe.state.iteration == 1

    def test_bounds_feedback(self):
        ipe = InteractivePreferenceElicitor(_objectives(), initial_samples=3)
        frontier = _frontier()
        ipe.start_elicitation(frontier)
        result = ipe.process_feedback(
            "bounds",
            {"bounds": {"coverage": (0.6, 1.0), "equity": (0.0, 0.4)}},
            frontier,
        )
        assert isinstance(result, list)

    def test_unknown_feedback_type(self):
        ipe = InteractivePreferenceElicitor(_objectives(), initial_samples=3)
        frontier = _frontier()
        ipe.start_elicitation(frontier)
        result = ipe.process_feedback("unknown", {}, frontier)
        assert isinstance(result, list)

    def test_get_preference_summary(self):
        ipe = InteractivePreferenceElicitor(_objectives())
        summary = ipe.get_preference_summary()
        assert summary["iterations"] == 0
        assert summary["is_complete"] is False
        assert summary["current_reference"] is None

    def test_solution_distance(self):
        ipe = InteractivePreferenceElicitor(_objectives())
        sol1 = _solution(0.8, 0.3)
        sol2 = _solution(0.8, 0.3)
        assert ipe._solution_distance(sol1, sol2) == pytest.approx(0.0)

    def test_solution_distance_nonzero(self):
        ipe = InteractivePreferenceElicitor(_objectives())
        sol1 = _solution(1.0, 0.0)
        sol2 = _solution(0.0, 1.0)
        dist = ipe._solution_distance(sol1, sol2)
        assert dist > 0


# ---------------------------------------------------------------------------
# PreferenceArticulator
# ---------------------------------------------------------------------------


class TestPreferenceArticulator:
    def test_init_no_method(self):
        pa = PreferenceArticulator(_objectives())
        assert pa.method is None

    def test_set_weights(self):
        pa = PreferenceArticulator(_objectives())
        pa.set_weights({"coverage": 0.7, "equity": 0.3})
        assert isinstance(pa.method, WeightedSum)

    def test_set_reference_point(self):
        pa = PreferenceArticulator(_objectives())
        rp = ReferencePoint(values={"coverage": 0.9, "equity": 0.1})
        pa.set_reference_point(rp)
        assert isinstance(pa.method, AchievementScalarizing)

    def test_set_reference_with_reservation(self):
        pa = PreferenceArticulator(_objectives())
        aspiration = ReferencePoint(values={"coverage": 0.9, "equity": 0.1})
        reservation = ReferencePoint(values={"coverage": 0.5, "equity": 0.5})
        pa.set_reference_point(aspiration, reservation)
        assert isinstance(pa.method, WierzbickiASF)

    def test_set_priority_order(self):
        pa = PreferenceArticulator(_objectives())
        pa.set_priority_order(["coverage", "equity"])
        assert isinstance(pa.method, LexicographicOrdering)

    def test_score_no_method(self):
        pa = PreferenceArticulator(_objectives())
        sol = _solution(0.8, 0.3)
        assert pa.score_solution(sol) == 0.0

    def test_score_with_method(self):
        pa = PreferenceArticulator(_objectives())
        pa.set_weights({"coverage": 1.0, "equity": 0.0})
        sol = _solution(0.8, 0.3)
        score = pa.score_solution(sol)
        assert score != 0.0

    def test_rank_no_method(self):
        pa = PreferenceArticulator(_objectives())
        solutions = [_solution(0.8, 0.3)]
        ranked = pa.rank_solutions(solutions)
        assert ranked[0][1] == 0.0

    def test_rank_with_method(self):
        pa = PreferenceArticulator(_objectives())
        pa.set_weights({"coverage": 1.0, "equity": 0.0})
        solutions = [_solution(0.5, 0.1), _solution(0.9, 0.5)]
        ranked = pa.rank_solutions(solutions)
        assert ranked[0][0].objective_values["coverage"] == 0.9

    def test_select_best_no_method(self):
        pa = PreferenceArticulator(_objectives())
        frontier = _frontier()
        best = pa.select_best(frontier, n=2)
        assert len(best) <= 2

    def test_select_best_with_method(self):
        pa = PreferenceArticulator(_objectives())
        pa.set_weights({"coverage": 1.0, "equity": 0.0})
        frontier = _frontier()
        best = pa.select_best(frontier, n=1)
        assert len(best) == 1

    def test_start_interactive(self):
        pa = PreferenceArticulator(_objectives())
        frontier = _frontier()
        reps = pa.start_interactive(frontier)
        assert isinstance(reps, list)
        assert pa.elicitor is not None

    def test_continue_interactive_without_start(self):
        pa = PreferenceArticulator(_objectives())
        frontier = _frontier()
        result = pa.continue_interactive("reference", {}, frontier)
        assert isinstance(result, list)
        assert pa.elicitor is not None
