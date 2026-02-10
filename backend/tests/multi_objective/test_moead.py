"""Tests for MOEA/D decomposition-based optimization (no DB)."""

import numpy as np
import pytest

from app.multi_objective.core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    Solution,
)
from app.multi_objective.moead import (
    DecompositionType,
    MOEADAlgorithm,
    MOEADConfig,
    PBIDecomposition,
    TchebycheffDecomposition,
    WeightVector,
    WeightedNormDecomposition,
    WeightedSumDecomposition,
    _n_combinations,
    create_pbi_moead,
    create_tchebycheff_moead,
    create_weighted_sum_moead,
    generate_weight_vectors,
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


# ---------------------------------------------------------------------------
# DecompositionType enum
# ---------------------------------------------------------------------------


class TestDecompositionType:
    def test_weighted_sum(self):
        assert DecompositionType.WEIGHTED_SUM.value == "weighted_sum"

    def test_tchebycheff(self):
        assert DecompositionType.TCHEBYCHEFF.value == "tchebycheff"

    def test_pbi(self):
        assert DecompositionType.PBI.value == "pbi"

    def test_member_count(self):
        assert len(DecompositionType) == 5


# ---------------------------------------------------------------------------
# WeightVector
# ---------------------------------------------------------------------------


class TestWeightVector:
    def test_normalizes_weights(self):
        wv = WeightVector(id=0, weights=np.array([2.0, 3.0]))
        assert abs(np.sum(wv.weights) - 1.0) < 1e-10

    def test_normalized_values(self):
        wv = WeightVector(id=0, weights=np.array([1.0, 3.0]))
        assert abs(wv.weights[0] - 0.25) < 1e-10
        assert abs(wv.weights[1] - 0.75) < 1e-10

    def test_already_normalized(self):
        wv = WeightVector(id=0, weights=np.array([0.5, 0.5]))
        assert abs(np.sum(wv.weights) - 1.0) < 1e-10

    def test_default_fields(self):
        wv = WeightVector(id=0, weights=np.array([1.0, 1.0]))
        assert wv.neighbors == []
        assert wv.current_solution is None
        assert wv.subproblem_value == float("inf")

    def test_zero_weights_no_crash(self):
        wv = WeightVector(id=0, weights=np.array([0.0, 0.0]))
        # Should not crash; weights stay as-is
        assert np.all(wv.weights == 0.0)


# ---------------------------------------------------------------------------
# WeightedSumDecomposition
# ---------------------------------------------------------------------------


class TestWeightedSumDecomposition:
    def test_name(self):
        ws = WeightedSumDecomposition()
        assert ws.name == "weighted_sum"

    def test_scalarize_equal_weights(self):
        ws = WeightedSumDecomposition()
        vals = np.array([1.0, 2.0])
        weight = np.array([0.5, 0.5])
        ref = np.array([0.0, 0.0])
        result = ws.scalarize(vals, weight, ref)
        assert abs(result - 1.5) < 1e-10

    def test_scalarize_biased_weight(self):
        ws = WeightedSumDecomposition()
        vals = np.array([1.0, 2.0])
        weight = np.array([1.0, 0.0])
        ref = np.array([0.0, 0.0])
        assert abs(ws.scalarize(vals, weight, ref) - 1.0) < 1e-10

    def test_scalarize_ignores_reference(self):
        ws = WeightedSumDecomposition()
        vals = np.array([3.0, 4.0])
        weight = np.array([0.5, 0.5])
        ref = np.array([100.0, 100.0])
        # Weighted sum doesn't use reference point
        assert abs(ws.scalarize(vals, weight, ref) - 3.5) < 1e-10


# ---------------------------------------------------------------------------
# TchebycheffDecomposition
# ---------------------------------------------------------------------------


class TestTchebycheffDecomposition:
    def test_name(self):
        tc = TchebycheffDecomposition()
        assert tc.name == "tchebycheff"

    def test_scalarize_equal_weights(self):
        tc = TchebycheffDecomposition()
        vals = np.array([1.0, 2.0])
        weight = np.array([0.5, 0.5])
        ref = np.array([0.0, 0.0])
        # max(0.5*1, 0.5*2) = 1.0
        assert abs(tc.scalarize(vals, weight, ref) - 1.0) < 1e-10

    def test_scalarize_at_reference(self):
        tc = TchebycheffDecomposition()
        vals = np.array([0.0, 0.0])
        weight = np.array([0.5, 0.5])
        ref = np.array([0.0, 0.0])
        assert abs(tc.scalarize(vals, weight, ref)) < 1e-10

    def test_scalarize_uses_reference(self):
        tc = TchebycheffDecomposition()
        vals = np.array([3.0, 4.0])
        weight = np.array([0.5, 0.5])
        ref = np.array([1.0, 1.0])
        # max(0.5*|3-1|, 0.5*|4-1|) = max(1.0, 1.5) = 1.5
        assert abs(tc.scalarize(vals, weight, ref) - 1.5) < 1e-10

    def test_scalarize_zero_weight_safe(self):
        tc = TchebycheffDecomposition()
        vals = np.array([1.0, 2.0])
        weight = np.array([0.0, 1.0])
        ref = np.array([0.0, 0.0])
        # Zero weight uses 1e-10, so max(1e-10*1, 1*2) = 2.0
        assert abs(tc.scalarize(vals, weight, ref) - 2.0) < 1e-6


# ---------------------------------------------------------------------------
# PBIDecomposition
# ---------------------------------------------------------------------------


class TestPBIDecomposition:
    def test_name_includes_theta(self):
        pbi = PBIDecomposition(theta=5.0)
        assert "5.0" in pbi.name

    def test_default_theta(self):
        pbi = PBIDecomposition()
        assert pbi.theta == 5.0

    def test_scalarize_on_weight_direction(self):
        pbi = PBIDecomposition(theta=5.0)
        # Solution exactly on the weight direction from reference
        vals = np.array([1.0, 0.0])
        weight = np.array([1.0, 0.0])
        ref = np.array([0.0, 0.0])
        result = pbi.scalarize(vals, weight, ref)
        # d1 = projection onto [1,0] = 1.0, d2 = perp distance = 0
        assert abs(result - 1.0) < 1e-10

    def test_scalarize_off_weight_direction(self):
        pbi = PBIDecomposition(theta=5.0)
        vals = np.array([0.0, 1.0])
        weight = np.array([1.0, 0.0])
        ref = np.array([0.0, 0.0])
        # d1 = dot([0,1], [1,0]) = 0.0, d2 = norm([0,1]-0) = 1.0
        # result = 0 + 5*1 = 5.0
        assert abs(pbi.scalarize(vals, weight, ref) - 5.0) < 1e-10

    def test_scalarize_zero_weight(self):
        pbi = PBIDecomposition()
        vals = np.array([1.0, 1.0])
        weight = np.array([0.0, 0.0])
        ref = np.array([0.0, 0.0])
        # Falls back to norm(diff)
        result = pbi.scalarize(vals, weight, ref)
        assert abs(result - np.sqrt(2)) < 1e-10


# ---------------------------------------------------------------------------
# WeightedNormDecomposition
# ---------------------------------------------------------------------------


class TestWeightedNormDecomposition:
    def test_name_includes_p(self):
        wn = WeightedNormDecomposition(p=2.0)
        assert "2.0" in wn.name

    def test_p1_like_weighted_sum(self):
        wn = WeightedNormDecomposition(p=1.0)
        vals = np.array([3.0, 4.0])
        weight = np.array([0.5, 0.5])
        ref = np.array([0.0, 0.0])
        # (0.5*3 + 0.5*4)^1 = 3.5
        result = wn.scalarize(vals, weight, ref)
        assert abs(result - 3.5) < 1e-10

    def test_p2_euclidean(self):
        wn = WeightedNormDecomposition(p=2.0)
        vals = np.array([3.0, 4.0])
        weight = np.array([1.0, 1.0])
        ref = np.array([0.0, 0.0])
        # (1*9 + 1*16)^0.5 = 5.0
        result = wn.scalarize(vals, weight, ref)
        assert abs(result - 5.0) < 1e-10


# ---------------------------------------------------------------------------
# generate_weight_vectors
# ---------------------------------------------------------------------------


class TestGenerateWeightVectors:
    def test_uniform_2d(self):
        vecs = generate_weight_vectors(2, 5, method="uniform")
        assert len(vecs) == 5
        for v in vecs:
            assert abs(np.sum(v) - 1.0) < 1e-10

    def test_uniform_2d_endpoints(self):
        vecs = generate_weight_vectors(2, 3, method="uniform")
        # Should include [0,1], [0.5,0.5], [1,0]
        assert abs(vecs[0][0] - 0.0) < 1e-10
        assert abs(vecs[-1][0] - 1.0) < 1e-10

    def test_random_method(self):
        np.random.seed(42)
        vecs = generate_weight_vectors(2, 10, method="random")
        assert len(vecs) == 10
        for v in vecs:
            assert abs(np.sum(v) - 1.0) < 1e-10

    def test_simplex_method(self):
        vecs = generate_weight_vectors(2, 5, method="simplex")
        assert len(vecs) > 0
        for v in vecs:
            assert abs(np.sum(v) - 1.0) < 1e-10

    def test_3d_vectors_sum_to_one(self):
        vecs = generate_weight_vectors(3, 10, method="uniform")
        for v in vecs:
            assert abs(np.sum(v) - 1.0) < 1e-10
            assert len(v) == 3


# ---------------------------------------------------------------------------
# _n_combinations
# ---------------------------------------------------------------------------


class TestNCombinations:
    def test_n_choose_0(self):
        assert _n_combinations(5, 0) == 1

    def test_n_choose_n(self):
        assert _n_combinations(5, 5) == 1

    def test_5_choose_2(self):
        assert _n_combinations(5, 2) == 10

    def test_k_greater_than_n(self):
        assert _n_combinations(3, 5) == 0

    def test_10_choose_3(self):
        assert _n_combinations(10, 3) == 120


# ---------------------------------------------------------------------------
# MOEADConfig
# ---------------------------------------------------------------------------


class TestMOEADConfig:
    def test_defaults(self):
        config = MOEADConfig()
        assert config.n_weight_vectors == 100
        assert config.n_neighbors == 20
        assert config.delta == 0.9
        assert config.nr == 2
        assert config.max_generations == 100
        assert config.mutation_rate == 0.1
        assert config.crossover_rate == 0.9

    def test_default_decomposition(self):
        config = MOEADConfig()
        assert isinstance(config.decomposition, TchebycheffDecomposition)

    def test_custom_config(self):
        config = MOEADConfig(
            n_weight_vectors=50,
            max_generations=200,
        )
        assert config.n_weight_vectors == 50
        assert config.max_generations == 200


# ---------------------------------------------------------------------------
# MOEADAlgorithm — init and weight initialization
# ---------------------------------------------------------------------------


class TestMOEADAlgorithmInit:
    def test_creates_weight_vectors(self):
        moead = MOEADAlgorithm(_objectives(), MOEADConfig(n_weight_vectors=10))
        assert len(moead.weight_vectors) > 0

    def test_weight_vectors_have_neighbors(self):
        moead = MOEADAlgorithm(
            _objectives(), MOEADConfig(n_weight_vectors=10, n_neighbors=3)
        )
        for wv in moead.weight_vectors:
            assert len(wv.neighbors) > 0

    def test_reference_point_initialized(self):
        moead = MOEADAlgorithm(_objectives(), MOEADConfig(n_weight_vectors=5))
        assert moead.reference_point.shape == (2,)

    def test_initial_stats(self):
        moead = MOEADAlgorithm(_objectives(), MOEADConfig(n_weight_vectors=5))
        assert moead.generation == 0
        assert moead.evaluations == 0

    def test_get_normalized_objectives_maximization_negated(self):
        moead = MOEADAlgorithm(_objectives(), MOEADConfig(n_weight_vectors=5))
        sol = _solution(0.8, 0.3)
        obj_vec = moead._get_normalized_objectives(sol)
        # coverage MAXIMIZE → -0.8, equity MINIMIZE → 0.3
        assert abs(obj_vec[0] - (-0.8)) < 1e-10
        assert abs(obj_vec[1] - 0.3) < 1e-10

    def test_update_reference_point(self):
        moead = MOEADAlgorithm(_objectives(), MOEADConfig(n_weight_vectors=5))
        sol = _solution(0.8, 0.3)
        moead._update_reference_point(sol)
        # Reference point should be updated to minimum (in minimization form)
        assert moead.reference_point[0] <= -0.8
        assert moead.reference_point[1] <= 0.3


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


class TestFactoryFunctions:
    def test_create_weighted_sum_moead(self):
        moead = create_weighted_sum_moead(_objectives(), n_weight_vectors=10)
        assert isinstance(moead, MOEADAlgorithm)
        assert isinstance(moead.config.decomposition, WeightedSumDecomposition)

    def test_create_tchebycheff_moead(self):
        moead = create_tchebycheff_moead(_objectives(), n_weight_vectors=10)
        assert isinstance(moead.config.decomposition, TchebycheffDecomposition)

    def test_create_pbi_moead(self):
        moead = create_pbi_moead(_objectives(), n_weight_vectors=10, theta=3.0)
        assert isinstance(moead.config.decomposition, PBIDecomposition)
        assert moead.config.decomposition.theta == 3.0

    def test_factory_sets_n_vectors(self):
        moead = create_weighted_sum_moead(_objectives(), n_weight_vectors=20)
        assert moead.config.n_weight_vectors == 20
