"""Tests for entropy and information theory functions (pure logic, no DB)."""

import math
from types import SimpleNamespace

import pytest

from app.resilience.thermodynamics.entropy import (
    EntropyMetrics,
    ScheduleEntropyMonitor,
    calculate_schedule_entropy,
    calculate_shannon_entropy,
    conditional_entropy,
    entropy_production_rate,
    mutual_information,
)


def _make_assignment(person_id, rotation_template_id=None, block_id=None):
    """Helper to create a lightweight assignment-like object."""
    return SimpleNamespace(
        person_id=person_id,
        rotation_template_id=rotation_template_id,
        block_id=block_id,
    )


# ── calculate_shannon_entropy ────────────────────────────────────────────


class TestCalculateShannonEntropy:
    def test_empty_list(self):
        assert calculate_shannon_entropy([]) == 0.0

    def test_single_element(self):
        assert calculate_shannon_entropy([1]) == 0.0

    def test_all_same(self):
        """All identical → 0 entropy."""
        assert calculate_shannon_entropy([1, 1, 1, 1]) == 0.0

    def test_two_equal_categories(self):
        """Two categories, equal counts → 1 bit."""
        result = calculate_shannon_entropy([0, 0, 1, 1])
        assert abs(result - 1.0) < 1e-10

    def test_four_equal_categories(self):
        """Four categories, equal counts → 2 bits."""
        result = calculate_shannon_entropy([0, 1, 2, 3])
        assert abs(result - 2.0) < 1e-10

    def test_skewed_distribution(self):
        """Skewed should be less than uniform."""
        uniform = calculate_shannon_entropy([0, 0, 1, 1])
        skewed = calculate_shannon_entropy([0, 0, 0, 1])
        assert skewed < uniform

    def test_string_values(self):
        result = calculate_shannon_entropy(["A", "A", "B", "B"])
        assert abs(result - 1.0) < 1e-10

    def test_non_negative(self):
        """Entropy should always be non-negative."""
        for dist in [[1], [1, 2], [1, 1, 2, 3, 3, 3, 3]]:
            assert calculate_shannon_entropy(dist) >= 0.0

    def test_maximum_entropy_for_n_categories(self):
        """Max entropy for n equally-likely categories is log2(n)."""
        for n in [2, 4, 8, 16]:
            dist = list(range(n))
            expected = math.log2(n)
            assert abs(calculate_shannon_entropy(dist) - expected) < 1e-10


# ── mutual_information ───────────────────────────────────────────────────


class TestMutualInformation:
    def test_empty_lists(self):
        assert mutual_information([], []) == 0.0

    def test_perfect_correlation(self):
        """Perfectly correlated → MI = H(X) = H(Y)."""
        X = [1, 1, 2, 2, 3, 3]
        Y = ["A", "A", "B", "B", "C", "C"]
        mi = mutual_information(X, Y)
        h_x = calculate_shannon_entropy(X)
        assert abs(mi - h_x) < 1e-10

    def test_independent_variables(self):
        """Independent variables → MI ≈ 0 (approximately, for finite samples)."""
        # Use a distribution where X and Y are structurally independent
        X = [1, 1, 2, 2, 1, 1, 2, 2]
        Y = [1, 2, 1, 2, 1, 2, 1, 2]
        mi = mutual_information(X, Y)
        assert mi < 0.01  # Approximately 0

    def test_non_negative(self):
        mi = mutual_information([1, 2, 3], [4, 5, 6])
        assert mi >= 0.0

    def test_different_lengths_raises(self):
        with pytest.raises(ValueError, match="same length"):
            mutual_information([1, 2], [1, 2, 3])

    def test_symmetric(self):
        X = [1, 1, 2, 3]
        Y = ["a", "b", "b", "c"]
        assert abs(mutual_information(X, Y) - mutual_information(Y, X)) < 1e-10


# ── conditional_entropy ──────────────────────────────────────────────────


class TestConditionalEntropy:
    def test_empty_lists(self):
        assert conditional_entropy([], []) == 0.0

    def test_deterministic_relationship(self):
        """If Y perfectly determines X, H(X|Y) = 0."""
        X = [1, 1, 2, 2, 3, 3]
        Y = ["A", "A", "B", "B", "C", "C"]
        result = conditional_entropy(X, Y)
        assert result < 1e-10

    def test_independent_equals_marginal(self):
        """If X ⊥ Y, then H(X|Y) = H(X)."""
        X = [1, 1, 2, 2, 1, 1, 2, 2]
        Y = [1, 2, 1, 2, 1, 2, 1, 2]
        h_cond = conditional_entropy(X, Y)
        h_x = calculate_shannon_entropy(X)
        assert abs(h_cond - h_x) < 0.01

    def test_non_negative(self):
        result = conditional_entropy([1, 2, 3, 4], [1, 1, 2, 2])
        assert result >= 0.0

    def test_different_lengths_raises(self):
        with pytest.raises(ValueError, match="same length"):
            conditional_entropy([1, 2], [1])

    def test_less_than_or_equal_marginal(self):
        """H(X|Y) <= H(X) always."""
        X = [1, 1, 2, 2, 3, 3]
        Y = [1, 1, 2, 2, 2, 3]
        h_cond = conditional_entropy(X, Y)
        h_x = calculate_shannon_entropy(X)
        assert h_cond <= h_x + 1e-10


# ── calculate_schedule_entropy ───────────────────────────────────────────


class TestCalculateScheduleEntropy:
    def test_empty_assignments(self):
        result = calculate_schedule_entropy([])
        assert isinstance(result, EntropyMetrics)
        assert result.person_entropy == 0.0
        assert result.rotation_entropy == 0.0
        assert result.time_entropy == 0.0
        assert result.joint_entropy == 0.0
        assert result.mutual_information == 0.0

    def test_single_assignment(self):
        assignments = [_make_assignment("p1", "r1", "b1")]
        result = calculate_schedule_entropy(assignments)
        assert result.person_entropy == 0.0  # Single category

    def test_uniform_person_distribution(self):
        assignments = [
            _make_assignment("p1", "r1", "b1"),
            _make_assignment("p2", "r1", "b2"),
        ]
        result = calculate_schedule_entropy(assignments)
        assert abs(result.person_entropy - 1.0) < 1e-10  # 2 categories = 1 bit

    def test_rotation_entropy(self):
        assignments = [
            _make_assignment("p1", "r1", "b1"),
            _make_assignment("p1", "r2", "b2"),
        ]
        result = calculate_schedule_entropy(assignments)
        assert abs(result.rotation_entropy - 1.0) < 1e-10

    def test_none_rotation_excluded(self):
        """Assignments with None rotation_template_id should not contribute to rotation entropy."""
        assignments = [
            _make_assignment("p1", None, "b1"),
            _make_assignment("p2", None, "b2"),
        ]
        result = calculate_schedule_entropy(assignments)
        assert result.rotation_entropy == 0.0

    def test_mutual_information_computed(self):
        assignments = [
            _make_assignment("p1", "r1", "b1"),
            _make_assignment("p1", "r1", "b2"),
            _make_assignment("p2", "r2", "b3"),
            _make_assignment("p2", "r2", "b4"),
        ]
        result = calculate_schedule_entropy(assignments)
        assert result.mutual_information >= 0.0

    def test_normalized_entropy_between_0_and_1(self):
        assignments = [
            _make_assignment("p1", "r1", "b1"),
            _make_assignment("p2", "r2", "b2"),
            _make_assignment("p3", "r3", "b3"),
        ]
        result = calculate_schedule_entropy(assignments)
        assert 0.0 <= result.normalized_entropy <= 1.0 + 1e-10


# ── entropy_production_rate ──────────────────────────────────────────────


class TestEntropyProductionRate:
    def test_no_change(self):
        """Same schedule → 0 production rate."""
        assignments = [_make_assignment("p1", "r1", "b1")]
        rate = entropy_production_rate(assignments, assignments)
        assert rate == 0.0

    def test_empty_to_something(self):
        new = [
            _make_assignment("p1", "r1", "b1"),
            _make_assignment("p2", "r2", "b2"),
        ]
        rate = entropy_production_rate([], new)
        assert rate >= 0.0

    def test_non_negative(self):
        """Production rate should always be non-negative."""
        old = [
            _make_assignment("p1", "r1", "b1"),
            _make_assignment("p2", "r2", "b2"),
        ]
        new = [_make_assignment("p1", "r1", "b1")]  # Less diverse
        rate = entropy_production_rate(old, new)
        assert rate >= 0.0  # Even when entropy decreases, production ≥ 0

    def test_custom_time_delta(self):
        old = [_make_assignment("p1", "r1", "b1")]
        new = [
            _make_assignment("p1", "r1", "b1"),
            _make_assignment("p2", "r2", "b2"),
        ]
        rate_1h = entropy_production_rate(old, new, time_delta=1.0)
        rate_2h = entropy_production_rate(old, new, time_delta=2.0)
        # Rate should be halved with doubled time delta
        if rate_1h > 0:
            assert abs(rate_2h - rate_1h / 2) < 1e-10


# ── ScheduleEntropyMonitor ───────────────────────────────────────────────


class TestScheduleEntropyMonitor:
    def test_initial_state(self):
        monitor = ScheduleEntropyMonitor(history_window=10)
        assert monitor.entropy_history == []
        assert monitor.production_rate_history == []
        assert monitor.history_window == 10

    def test_update_adds_entry(self):
        monitor = ScheduleEntropyMonitor()
        assignments = [_make_assignment("p1", "r1", "b1")]
        monitor.update(assignments)
        assert len(monitor.entropy_history) == 1

    def test_multiple_updates(self):
        monitor = ScheduleEntropyMonitor()
        for i in range(5):
            monitor.update([_make_assignment(f"p{i}", "r1", f"b{i}")])
        assert len(monitor.entropy_history) == 5

    def test_history_window_limit(self):
        monitor = ScheduleEntropyMonitor(history_window=3)
        for i in range(5):
            monitor.update([_make_assignment(f"p{i}", "r1", f"b{i}")])
        assert len(monitor.entropy_history) <= 3

    def test_get_entropy_rate_of_change_empty(self):
        monitor = ScheduleEntropyMonitor()
        assert monitor.get_entropy_rate_of_change() == 0.0

    def test_get_entropy_rate_of_change_single(self):
        monitor = ScheduleEntropyMonitor()
        monitor.update([_make_assignment("p1", "r1", "b1")])
        assert monitor.get_entropy_rate_of_change() == 0.0

    def test_detect_critical_slowing_insufficient_data(self):
        monitor = ScheduleEntropyMonitor()
        for i in range(5):
            monitor.update([_make_assignment(f"p{i}", "r1", f"b{i}")])
        assert monitor.detect_critical_slowing() is False  # Need >= 10

    def test_get_current_metrics_empty(self):
        monitor = ScheduleEntropyMonitor()
        metrics = monitor.get_current_metrics()
        assert metrics["current_entropy"] == 0.0
        assert metrics["rate_of_change"] == 0.0
        assert metrics["production_rate"] == 0.0
        assert metrics["critical_slowing"] is False

    def test_get_current_metrics_after_update(self):
        monitor = ScheduleEntropyMonitor()
        monitor.update([_make_assignment("p1", "r1", "b1")])
        metrics = monitor.get_current_metrics()
        assert "current_entropy" in metrics
        assert "measurements" in metrics
        assert metrics["measurements"] == 1

    def test_autocorrelation_insufficient_data(self):
        monitor = ScheduleEntropyMonitor()
        assert monitor._autocorrelation([1.0], lag=1) == 0.0

    def test_autocorrelation_constant_series(self):
        monitor = ScheduleEntropyMonitor()
        result = monitor._autocorrelation([5.0, 5.0, 5.0, 5.0], lag=1)
        assert result == 0.0  # Zero variance → 0 autocorrelation

    def test_autocorrelation_positive(self):
        monitor = ScheduleEntropyMonitor()
        # Slowly increasing series → positive autocorrelation
        result = monitor._autocorrelation([1.0, 2.0, 3.0, 4.0, 5.0], lag=1)
        assert result > 0.0
