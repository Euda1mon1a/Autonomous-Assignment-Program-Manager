"""Tests for diversity preservation mechanisms (no DB)."""

import numpy as np
import pytest

from app.multi_objective.core import (
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    Solution,
)
from app.multi_objective.diversity import (
    CrowdingDistance,
    DiversityMechanism,
    DiversityMetric,
    DiversityStats,
    EpsilonDominance,
    NichingOperator,
    ReferencePointAssociation,
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


# ---------------------------------------------------------------------------
# DiversityMetric enum
# ---------------------------------------------------------------------------


class TestDiversityMetric:
    def test_crowding_distance_value(self):
        assert DiversityMetric.CROWDING_DISTANCE.value == "crowding_distance"

    def test_epsilon_grid_value(self):
        assert DiversityMetric.EPSILON_GRID.value == "epsilon_grid"

    def test_niching_value(self):
        assert DiversityMetric.NICHING.value == "niching"

    def test_reference_point_value(self):
        assert DiversityMetric.REFERENCE_POINT.value == "reference_point"

    def test_member_count(self):
        assert len(DiversityMetric) == 4


# ---------------------------------------------------------------------------
# DiversityStats dataclass
# ---------------------------------------------------------------------------


class TestDiversityStats:
    def test_construction(self):
        stats = DiversityStats(
            metric_type=DiversityMetric.CROWDING_DISTANCE,
            mean_distance=0.5,
            min_distance=0.1,
            max_distance=1.0,
            uniformity=0.8,
            coverage=0.6,
            cluster_count=3,
        )
        assert stats.metric_type == DiversityMetric.CROWDING_DISTANCE
        assert stats.mean_distance == 0.5
        assert stats.min_distance == 0.1
        assert stats.max_distance == 1.0
        assert stats.uniformity == 0.8
        assert stats.coverage == 0.6
        assert stats.cluster_count == 3


# ---------------------------------------------------------------------------
# CrowdingDistance
# ---------------------------------------------------------------------------


class TestCrowdingDistance:
    def test_init_stores_objectives(self):
        objs = _objectives()
        cd = CrowdingDistance(objs)
        assert len(cd.objectives) == 2
        assert len(cd.active_objectives) == 2

    def test_init_excludes_constraints(self):
        objs = _objectives()
        objs[0] = ObjectiveConfig(
            name="cov",
            display_name="C",
            description="c",
            direction=ObjectiveDirection.MAXIMIZE,
            objective_type=ObjectiveType.COVERAGE,
            is_constraint=True,
        )
        cd = CrowdingDistance(objs)
        assert len(cd.active_objectives) == 1

    def test_calculate_empty(self):
        cd = CrowdingDistance(_objectives())
        cd.calculate([])  # no crash

    def test_calculate_single_solution(self):
        cd = CrowdingDistance(_objectives())
        sol = _solution(0.5, 0.3)
        cd.calculate([sol])
        assert sol.crowding_distance == float("inf")

    def test_calculate_two_solutions(self):
        cd = CrowdingDistance(_objectives())
        s1 = _solution(0.3, 0.8)
        s2 = _solution(0.9, 0.2)
        cd.calculate([s1, s2])
        assert s1.crowding_distance == float("inf")
        assert s2.crowding_distance == float("inf")

    def test_calculate_three_solutions(self):
        cd = CrowdingDistance(_objectives())
        s1 = _solution(0.2, 0.9)
        s2 = _solution(0.5, 0.5)
        s3 = _solution(0.8, 0.1)
        cd.calculate([s1, s2, s3])
        # Boundary solutions get inf
        assert s1.crowding_distance == float("inf")
        assert s3.crowding_distance == float("inf")
        # Middle solution gets finite distance
        assert s2.crowding_distance > 0
        assert s2.crowding_distance < float("inf")

    def test_calculate_uniform_objective_range_zero(self):
        cd = CrowdingDistance(_objectives())
        s1 = _solution(0.5, 0.1)
        s2 = _solution(0.5, 0.5)
        s3 = _solution(0.5, 0.9)
        cd.calculate([s1, s2, s3])
        # Coverage range is 0, only equity contributes

    def test_select_by_crowding(self):
        cd = CrowdingDistance(_objectives())
        sols = [_solution(0.1 * i, 0.9 - 0.1 * i) for i in range(5)]
        selected = cd.select_by_crowding(sols, 2)
        assert len(selected) == 2
        # Boundary solutions (highest crowding distance) should be selected
        assert all(s.crowding_distance == float("inf") for s in selected)

    def test_select_by_crowding_request_more_than_available(self):
        cd = CrowdingDistance(_objectives())
        sols = [_solution(0.3, 0.7), _solution(0.7, 0.3)]
        selected = cd.select_by_crowding(sols, 5)
        assert len(selected) == 2

    def test_tournament_select_returns_one(self):
        cd = CrowdingDistance(_objectives())
        sols = [_solution(0.2, 0.8), _solution(0.5, 0.5), _solution(0.8, 0.2)]
        for s in sols:
            s.rank = 0
        cd.calculate(sols)
        winner = cd.tournament_select(sols, tournament_size=2)
        assert isinstance(winner, Solution)


# ---------------------------------------------------------------------------
# EpsilonDominance
# ---------------------------------------------------------------------------


class TestEpsilonDominance:
    def test_default_epsilon(self):
        ed = EpsilonDominance(_objectives())
        assert ed.epsilon["coverage"] == 0.01
        assert ed.epsilon["equity"] == 0.01

    def test_custom_epsilon_float(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.05)
        assert ed.epsilon["coverage"] == 0.05
        assert ed.epsilon["equity"] == 0.05

    def test_custom_epsilon_dict(self):
        ed = EpsilonDominance(_objectives(), epsilon={"coverage": 0.1, "equity": 0.02})
        assert ed.epsilon["coverage"] == 0.1
        assert ed.epsilon["equity"] == 0.02

    def test_get_grid_location(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        sol = _solution(0.5, 0.3)
        loc = ed.get_grid_location(sol)
        assert isinstance(loc, tuple)
        assert len(loc) == 2

    def test_get_grid_location_maximize_negates(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        sol = _solution(0.5, 0.3)
        loc = ed.get_grid_location(sol)
        # coverage is MAXIMIZE so negated: int(-0.5 / 0.1) = -5
        # equity is MINIMIZE so direct: int(0.3 / 0.1) = int(2.999...) = 2
        assert loc == (-5, 2)

    def test_get_grid_location_different_solutions(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        sol1 = _solution(0.2, 0.8)
        sol2 = _solution(0.8, 0.2)
        loc1 = ed.get_grid_location(sol1)
        loc2 = ed.get_grid_location(sol2)
        assert loc1 != loc2

    def test_epsilon_dominates_clear_case(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        # Better in both: higher coverage (MAXIMIZE) and lower equity (MINIMIZE)
        better = _solution(0.9, 0.1)
        worse = _solution(0.2, 0.8)
        assert ed.epsilon_dominates(better, worse)

    def test_epsilon_dominates_not_reverse(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        better = _solution(0.9, 0.1)
        worse = _solution(0.2, 0.8)
        assert not ed.epsilon_dominates(worse, better)

    def test_epsilon_dominates_same_grid_cell(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        s1 = _solution(0.51, 0.31)
        s2 = _solution(0.52, 0.32)
        # Same grid cell — neither epsilon-dominates
        loc1 = ed.get_grid_location(s1)
        loc2 = ed.get_grid_location(s2)
        if loc1 == loc2:
            assert not ed.epsilon_dominates(s1, s2)

    def test_update_archive_adds_to_empty(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        archive = ed.update_archive([], _solution(0.5, 0.5))
        assert len(archive) == 1

    def test_update_archive_rejects_dominated(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        archive = [_solution(0.9, 0.1)]
        updated = ed.update_archive(archive, _solution(0.2, 0.8))
        assert len(updated) == 1  # rejected

    def test_update_archive_removes_dominated_existing(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        archive = [_solution(0.2, 0.8)]
        updated = ed.update_archive(archive, _solution(0.9, 0.1))
        assert len(updated) == 1
        # The new better solution should be in the archive
        assert updated[0].objective_values["coverage"] == 0.9

    def test_update_archive_non_dominated_pair(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        archive = [_solution(0.3, 0.1)]
        updated = ed.update_archive(archive, _solution(0.9, 0.8))
        # Both non-dominated, different grid cells
        assert len(updated) == 2

    def test_prune_archive_within_limit(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.1)
        archive = [_solution(0.3, 0.1), _solution(0.9, 0.8)]
        pruned = ed.prune_archive(archive, max_size=5)
        assert len(pruned) == 2

    def test_prune_archive_reduces_size(self):
        ed = EpsilonDominance(_objectives(), epsilon=0.01)
        archive = [_solution(0.1 * i, 0.9 - 0.1 * i) for i in range(1, 9)]
        pruned = ed.prune_archive(archive, max_size=3)
        assert len(pruned) <= 3


# ---------------------------------------------------------------------------
# NichingOperator
# ---------------------------------------------------------------------------


class TestNichingOperator:
    def test_init_defaults(self):
        n = NichingOperator(_objectives())
        assert n.niche_radius == 0.1
        assert n.alpha == 1.0

    def test_init_custom(self):
        n = NichingOperator(_objectives(), niche_radius=0.5, alpha=2.0)
        assert n.niche_radius == 0.5
        assert n.alpha == 2.0

    def test_sharing_function_zero_distance(self):
        n = NichingOperator(_objectives(), niche_radius=0.5)
        # sh(0) = 1 - (0/0.5)^1 = 1.0
        assert n._sharing_function(0.0) == 1.0

    def test_sharing_function_at_radius(self):
        n = NichingOperator(_objectives(), niche_radius=0.5)
        # sh(0.5) = 0 (at boundary)
        assert n._sharing_function(0.5) == 0.0

    def test_sharing_function_beyond_radius(self):
        n = NichingOperator(_objectives(), niche_radius=0.5)
        assert n._sharing_function(1.0) == 0.0

    def test_sharing_function_midway(self):
        n = NichingOperator(_objectives(), niche_radius=1.0, alpha=1.0)
        # sh(0.5) = 1 - (0.5/1.0)^1 = 0.5
        assert abs(n._sharing_function(0.5) - 0.5) < 1e-10

    def test_sharing_function_alpha_2(self):
        n = NichingOperator(_objectives(), niche_radius=1.0, alpha=2.0)
        # sh(0.5) = 1 - (0.5)^2 = 1 - 0.25 = 0.75
        assert abs(n._sharing_function(0.5) - 0.75) < 1e-10

    def test_normalized_distance_same_solution(self):
        n = NichingOperator(_objectives())
        s = _solution(0.5, 0.5)
        assert n._normalized_distance(s, s) == 0.0

    def test_normalized_distance_different_solutions(self):
        n = NichingOperator(_objectives())
        s1 = _solution(0.0, 0.0)
        s2 = _solution(1.0, 1.0)
        dist = n._normalized_distance(s1, s2)
        assert dist > 0

    def test_calculate_niche_count_single(self):
        n = NichingOperator(_objectives(), niche_radius=0.5)
        s = _solution(0.5, 0.5)
        counts = n.calculate_niche_count([s])
        assert counts[str(s.id)] == 0.0  # no neighbors

    def test_calculate_niche_count_distant_pair(self):
        n = NichingOperator(_objectives(), niche_radius=0.01)
        s1 = _solution(0.1, 0.1)
        s2 = _solution(0.9, 0.9)
        counts = n.calculate_niche_count([s1, s2])
        # Very far apart with tiny radius — niche counts should be ~0
        assert counts[str(s1.id)] < 0.01
        assert counts[str(s2.id)] < 0.01

    def test_calculate_niche_count_close_pair(self):
        n = NichingOperator(_objectives(), niche_radius=10.0)
        s1 = _solution(0.5, 0.5)
        s2 = _solution(0.51, 0.51)
        counts = n.calculate_niche_count([s1, s2])
        # Very close, large radius — high niche count
        assert counts[str(s1.id)] > 0.5

    def test_shared_fitness_reduces_crowded(self):
        n = NichingOperator(_objectives(), niche_radius=10.0)
        # Use 3+ close solutions so niche count sums exceed 1.0
        s1 = _solution(0.5, 0.5)
        s2 = _solution(0.51, 0.51)
        s3 = _solution(0.52, 0.52)
        raw = {str(s1.id): 1.0, str(s2.id): 1.0, str(s3.id): 1.0}
        shared = n.shared_fitness([s1, s2, s3], raw)
        # With 3 close neighbors, niche count > 1.0 so shared < raw
        assert shared[str(s1.id)] < 1.0
        assert shared[str(s2.id)] < 1.0

    def test_shared_fitness_preserves_isolated(self):
        n = NichingOperator(_objectives(), niche_radius=0.001)
        s1 = _solution(0.1, 0.1)
        s2 = _solution(0.9, 0.9)
        raw = {str(s1.id): 2.0, str(s2.id): 3.0}
        shared = n.shared_fitness([s1, s2], raw)
        # Far apart, tiny radius — niche count ~0, shared ≈ raw/1.0
        assert abs(shared[str(s1.id)] - 2.0) < 0.1
        assert abs(shared[str(s2.id)] - 3.0) < 0.1


# ---------------------------------------------------------------------------
# ReferencePointAssociation
# ---------------------------------------------------------------------------


class TestReferencePointAssociation:
    def test_init_creates_reference_points(self):
        rpa = ReferencePointAssociation(_objectives(), n_reference_points=10)
        assert rpa.reference_points.shape[0] > 0
        assert rpa.reference_points.shape[1] == 2

    def test_perpendicular_distance_on_line(self):
        rpa = ReferencePointAssociation(_objectives(), n_reference_points=10)
        ref = np.array([1.0, 0.0])
        point = np.array([3.0, 0.0])  # on the reference line
        dist = rpa._perpendicular_distance(point, ref)
        assert abs(dist) < 1e-10

    def test_perpendicular_distance_off_line(self):
        rpa = ReferencePointAssociation(_objectives(), n_reference_points=10)
        ref = np.array([1.0, 0.0])
        point = np.array([1.0, 1.0])  # 1 unit off the x-axis
        dist = rpa._perpendicular_distance(point, ref)
        assert abs(dist - 1.0) < 1e-10

    def test_perpendicular_distance_zero_ref(self):
        rpa = ReferencePointAssociation(_objectives(), n_reference_points=10)
        ref = np.array([0.0, 0.0])
        point = np.array([1.0, 1.0])
        dist = rpa._perpendicular_distance(point, ref)
        assert abs(dist - np.linalg.norm(point)) < 1e-10

    def test_associate_returns_dict(self):
        rpa = ReferencePointAssociation(_objectives(), n_reference_points=10)
        sols = [_solution(0.3, 0.7), _solution(0.7, 0.3)]
        assoc = rpa.associate(sols)
        assert isinstance(assoc, dict)
        # All solutions should be associated with some reference point
        total = sum(len(v) for v in assoc.values())
        assert total == 2

    def test_niching_selection_returns_solutions(self):
        np.random.seed(42)
        rpa = ReferencePointAssociation(_objectives(), n_reference_points=10)
        sols = [_solution(0.1 * i, 0.9 - 0.1 * i) for i in range(1, 8)]
        selected = rpa.niching_selection(sols, 3)
        # At least some solutions are selected
        assert len(selected) >= 1
        assert all(isinstance(s, Solution) for s in selected)


# ---------------------------------------------------------------------------
# DiversityMechanism
# ---------------------------------------------------------------------------


class TestDiversityMechanism:
    def test_init_default_metric(self):
        dm = DiversityMechanism(_objectives())
        assert dm.primary_metric == DiversityMetric.CROWDING_DISTANCE

    def test_init_custom_metric(self):
        dm = DiversityMechanism(
            _objectives(), primary_metric=DiversityMetric.EPSILON_GRID
        )
        assert dm.primary_metric == DiversityMetric.EPSILON_GRID

    def test_grid_adjacent_true(self):
        dm = DiversityMechanism(_objectives())
        assert dm._grid_adjacent((0, 0), (1, 0)) is True
        assert dm._grid_adjacent((0, 0), (0, 1)) is True
        assert dm._grid_adjacent((0, 0), (1, 1)) is True

    def test_grid_adjacent_false(self):
        dm = DiversityMechanism(_objectives())
        assert dm._grid_adjacent((0, 0), (2, 0)) is False
        assert dm._grid_adjacent((0, 0), (0, 2)) is False

    def test_calculate_diversity_crowding(self):
        dm = DiversityMechanism(
            _objectives(), primary_metric=DiversityMetric.CROWDING_DISTANCE
        )
        sols = [_solution(0.2, 0.8), _solution(0.5, 0.5), _solution(0.8, 0.2)]
        dm.calculate_diversity(sols)
        # Boundary solutions get inf
        assert sols[0].crowding_distance == float("inf")
        assert sols[2].crowding_distance == float("inf")

    def test_calculate_diversity_epsilon_grid(self):
        dm = DiversityMechanism(
            _objectives(), primary_metric=DiversityMetric.EPSILON_GRID
        )
        sols = [_solution(0.2, 0.8), _solution(0.8, 0.2)]
        dm.calculate_diversity(sols)
        # Each solution gets a diversity value
        for s in sols:
            assert s.crowding_distance > 0

    def test_calculate_diversity_niching(self):
        dm = DiversityMechanism(_objectives(), primary_metric=DiversityMetric.NICHING)
        sols = [_solution(0.2, 0.8), _solution(0.8, 0.2)]
        dm.calculate_diversity(sols)
        for s in sols:
            assert s.crowding_distance > 0

    def test_select_returns_correct_count(self):
        dm = DiversityMechanism(_objectives())
        sols = [_solution(0.1 * i, 0.9 - 0.1 * i) for i in range(1, 8)]
        selected = dm.select(sols, 3)
        assert len(selected) == 3

    def test_update_archive_adds_non_dominated(self):
        dm = DiversityMechanism(_objectives())
        archive = [_solution(0.3, 0.1)]
        new = [_solution(0.9, 0.8)]
        updated = dm.update_archive(archive, new, max_size=10)
        assert len(updated) == 2

    def test_update_archive_prunes_to_max(self):
        dm = DiversityMechanism(_objectives())
        archive = [_solution(0.1 * i, 0.9 - 0.1 * i) for i in range(1, 8)]
        new = [_solution(0.05, 0.95)]
        updated = dm.update_archive(archive, new, max_size=3)
        assert len(updated) <= 3

    def test_get_diversity_stats_empty(self):
        dm = DiversityMechanism(_objectives())
        stats = dm.get_diversity_stats([])
        assert isinstance(stats, DiversityStats)
        assert stats.mean_distance == 0.0
        assert stats.cluster_count == 0

    def test_get_diversity_stats_populated(self):
        dm = DiversityMechanism(_objectives())
        sols = [_solution(0.2, 0.8), _solution(0.5, 0.5), _solution(0.8, 0.2)]
        stats = dm.get_diversity_stats(sols)
        assert stats.metric_type == DiversityMetric.CROWDING_DISTANCE
        assert stats.cluster_count >= 1
        assert 0.0 <= stats.uniformity <= 1.0
        assert 0.0 <= stats.coverage <= 1.0

    def test_count_clusters_empty(self):
        dm = DiversityMechanism(_objectives())
        assert dm._count_clusters([]) == 0

    def test_count_clusters_single(self):
        dm = DiversityMechanism(_objectives())
        assert dm._count_clusters([_solution(0.5, 0.5)]) == 1

    def test_count_clusters_far_apart(self):
        dm = DiversityMechanism(_objectives(), epsilon=0.01)
        sols = [_solution(0.1, 0.9), _solution(0.9, 0.1)]
        clusters = dm._count_clusters(sols)
        # Very different grid cells, should be separate clusters
        assert clusters == 2

    def test_select_with_reference_point_metric(self):
        np.random.seed(42)
        dm = DiversityMechanism(
            _objectives(), primary_metric=DiversityMetric.REFERENCE_POINT
        )
        sols = [_solution(0.1 * i, 0.9 - 0.1 * i) for i in range(1, 8)]
        selected = dm.select(sols, 3)
        assert len(selected) == 3
