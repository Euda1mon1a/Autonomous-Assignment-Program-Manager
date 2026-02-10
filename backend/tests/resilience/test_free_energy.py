"""Tests for free energy and energy landscape analysis (pure logic, no DB)."""

import math
from types import SimpleNamespace

import numpy as np
import pytest

from app.resilience.thermodynamics.free_energy import (
    EnergyLandscapeAnalyzer,
    FreeEnergyMetrics,
    LandscapeFeatures,
    _calculate_configuration_entropy,
    _calculate_internal_energy,
    adaptive_temperature,
    boltzmann_probability,
    calculate_free_energy,
)


def _make_assignment(
    person_id, rotation_template_id=None, score=None, has_violation=False
):
    """Helper to create a lightweight assignment-like object."""
    return SimpleNamespace(
        person_id=person_id,
        rotation_template_id=rotation_template_id,
        score=score,
        has_violation=has_violation,
    )


# ── FreeEnergyMetrics dataclass ─────────────────────────────────────────


class TestFreeEnergyMetrics:
    def test_default_values(self):
        m = FreeEnergyMetrics()
        assert m.free_energy == 0.0
        assert m.internal_energy == 0.0
        assert m.entropy_term == 0.0
        assert m.temperature == 1.0
        assert m.constraint_violations == 0
        assert m.configuration_entropy == 0.0

    def test_custom_values(self):
        m = FreeEnergyMetrics(
            free_energy=-5.0,
            internal_energy=3.0,
            entropy_term=8.0,
            temperature=2.0,
            constraint_violations=4,
            configuration_entropy=4.0,
        )
        assert m.free_energy == -5.0
        assert m.constraint_violations == 4


# ── LandscapeFeatures dataclass ─────────────────────────────────────────


class TestLandscapeFeatures:
    def test_default_values(self):
        f = LandscapeFeatures()
        assert f.num_local_minima == 0
        assert f.basin_depths == []
        assert f.ruggedness == 0.0
        assert f.barrier_heights == []
        assert f.gradient_norms == []

    def test_custom_values(self):
        f = LandscapeFeatures(
            num_local_minima=3,
            basin_depths=[1.0, 2.0],
            ruggedness=0.5,
        )
        assert f.num_local_minima == 3
        assert len(f.basin_depths) == 2


# ── _calculate_internal_energy ──────────────────────────────────────────


class TestCalculateInternalEnergy:
    def test_empty_assignments(self):
        assert _calculate_internal_energy([]) == 0.0

    def test_single_assignment_no_score(self):
        """Single assignment with no score or violation has zero imbalance."""
        assignments = [_make_assignment("p1")]
        result = _calculate_internal_energy(assignments)
        # Single person: variance = 0, no score penalty, no violation
        assert result == 0.0

    def test_balanced_assignments(self):
        """Balanced workload: 2 assignments each for 2 people."""
        assignments = [
            _make_assignment("p1"),
            _make_assignment("p1"),
            _make_assignment("p2"),
            _make_assignment("p2"),
        ]
        result = _calculate_internal_energy(assignments)
        # Mean=2, variance=0 → energy from imbalance = 0
        assert result == 0.0

    def test_imbalanced_workload(self):
        """Imbalanced workload increases energy."""
        assignments = [
            _make_assignment("p1"),
            _make_assignment("p1"),
            _make_assignment("p1"),
            _make_assignment("p2"),
        ]
        result = _calculate_internal_energy(assignments)
        # Mean=2, counts=[3,1], variance = ((1)^2 + (-1)^2)/2 = 1.0
        # Energy = 1.0 * 0.1 = 0.1
        assert abs(result - 0.1) < 1e-10

    def test_score_penalty(self):
        """Lower score increases energy."""
        assignments = [_make_assignment("p1", score=0.5)]
        # (1.0 - 0.5) * 0.5 = 0.25
        result = _calculate_internal_energy(assignments)
        assert abs(result - 0.25) < 1e-10

    def test_perfect_score_no_penalty(self):
        """Score of 1.0 adds no energy."""
        assignments = [_make_assignment("p1", score=1.0)]
        result = _calculate_internal_energy(assignments)
        assert result == 0.0

    def test_violation_adds_energy(self):
        """Violation flag adds 1.0 energy."""
        assignments = [_make_assignment("p1", has_violation=True)]
        result = _calculate_internal_energy(assignments)
        assert result == 1.0

    def test_combined_penalties(self):
        """Score + violation combine additively."""
        assignments = [_make_assignment("p1", score=0.0, has_violation=True)]
        # Score penalty: (1.0 - 0.0) * 0.5 = 0.5
        # Violation: 1.0
        # Total: 1.5
        result = _calculate_internal_energy(assignments)
        assert abs(result - 1.5) < 1e-10

    def test_no_person_id_excluded_from_imbalance(self):
        """Assignments without person_id don't count for imbalance."""
        assignments = [_make_assignment(None), _make_assignment(None)]
        result = _calculate_internal_energy(assignments)
        assert result == 0.0


# ── _calculate_configuration_entropy ────────────────────────────────────


class TestCalculateConfigurationEntropy:
    def test_empty_assignments(self):
        assert _calculate_configuration_entropy([]) == 0.0

    def test_single_assignment(self):
        assignments = [_make_assignment("p1", "r1")]
        result = _calculate_configuration_entropy(assignments)
        # Single config → entropy = 0
        assert result == 0.0

    def test_two_identical_configs(self):
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p1", "r1"),
        ]
        result = _calculate_configuration_entropy(assignments)
        # One category → 0 entropy
        assert result == 0.0

    def test_two_different_configs(self):
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
        ]
        result = _calculate_configuration_entropy(assignments)
        # Two equal categories → log(2) ≈ 0.693 (natural log)
        assert abs(result - math.log(2)) < 1e-10

    def test_four_different_configs(self):
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
            _make_assignment("p3", "r3"),
            _make_assignment("p4", "r4"),
        ]
        result = _calculate_configuration_entropy(assignments)
        assert abs(result - math.log(4)) < 1e-10

    def test_non_negative(self):
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p1", "r2"),
            _make_assignment("p2", "r1"),
        ]
        result = _calculate_configuration_entropy(assignments)
        assert result >= 0.0

    def test_skewed_distribution_lower(self):
        uniform = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
        ]
        skewed = [
            _make_assignment("p1", "r1"),
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
        ]
        assert _calculate_configuration_entropy(
            skewed
        ) < _calculate_configuration_entropy(uniform)


# ── calculate_free_energy ───────────────────────────────────────────────


class TestCalculateFreeEnergy:
    def test_empty_assignments(self):
        result = calculate_free_energy([])
        assert isinstance(result, FreeEnergyMetrics)
        assert result.free_energy == 0.0
        assert result.internal_energy == 0.0
        assert result.entropy_term == 0.0

    def test_helmholtz_relation(self):
        """F = U - TS."""
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
        ]
        result = calculate_free_energy(assignments, temperature=2.0)
        expected_f = (
            result.internal_energy - result.temperature * result.configuration_entropy
        )
        assert abs(result.free_energy - expected_f) < 1e-10

    def test_temperature_stored(self):
        result = calculate_free_energy([], temperature=5.0)
        assert result.temperature == 5.0

    def test_zero_temperature_clamped(self):
        """T=0 is clamped to 0.001."""
        result = calculate_free_energy([], temperature=0.0)
        assert result.temperature == 0.001

    def test_negative_temperature_clamped(self):
        result = calculate_free_energy([], temperature=-5.0)
        assert result.temperature == 0.001

    def test_violations_counted(self):
        assignments = [
            _make_assignment("p1", has_violation=True),
            _make_assignment("p2", has_violation=False),
            _make_assignment("p3", has_violation=True),
        ]
        result = calculate_free_energy(assignments)
        assert result.constraint_violations == 2

    def test_high_temperature_favors_entropy(self):
        """At high T, entropy dominates → lower free energy."""
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
            _make_assignment("p3", "r3"),
        ]
        low_t = calculate_free_energy(assignments, temperature=0.01)
        high_t = calculate_free_energy(assignments, temperature=100.0)
        assert high_t.free_energy < low_t.free_energy

    def test_entropy_term_positive(self):
        """Entropy term (TS) should be non-negative."""
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
        ]
        result = calculate_free_energy(assignments, temperature=1.0)
        assert result.entropy_term >= 0.0


# ── adaptive_temperature ────────────────────────────────────────────────


class TestAdaptiveTemperature:
    def test_exponential_iteration_zero(self):
        assert (
            adaptive_temperature(0, initial_temp=10.0, schedule="exponential") == 10.0
        )

    def test_exponential_decreasing(self):
        temps = [
            adaptive_temperature(
                i, initial_temp=10.0, cooling_rate=0.9, schedule="exponential"
            )
            for i in range(5)
        ]
        for i in range(1, len(temps)):
            assert temps[i] <= temps[i - 1]

    def test_exponential_formula(self):
        """T(t) = T0 * rate^t."""
        t = adaptive_temperature(
            3, initial_temp=10.0, cooling_rate=0.5, schedule="exponential"
        )
        expected = 10.0 * 0.5**3
        assert abs(t - expected) < 1e-10

    def test_linear_iteration_zero(self):
        assert adaptive_temperature(0, initial_temp=10.0, schedule="linear") == 10.0

    def test_linear_formula(self):
        """T(t) = T0 - rate * t."""
        t = adaptive_temperature(
            3, initial_temp=10.0, cooling_rate=2.0, schedule="linear"
        )
        expected = 10.0 - 2.0 * 3  # 4.0
        assert abs(t - expected) < 1e-10

    def test_linear_floors_at_min_temp(self):
        t = adaptive_temperature(
            100, initial_temp=10.0, cooling_rate=1.0, schedule="linear", min_temp=0.5
        )
        assert t == 0.5

    def test_logarithmic_formula(self):
        """T(t) = T0 / log(t + 2)."""
        t = adaptive_temperature(0, initial_temp=10.0, schedule="logarithmic")
        expected = 10.0 / math.log(2)
        assert abs(t - expected) < 1e-10

    def test_cauchy_formula(self):
        """T(t) = T0 / (1 + t)."""
        t = adaptive_temperature(4, initial_temp=10.0, schedule="cauchy")
        expected = 10.0 / 5
        assert abs(t - expected) < 1e-10

    def test_boltzmann_formula(self):
        """T(t) = T0 / (1 + log(1 + t))."""
        t = adaptive_temperature(4, initial_temp=10.0, schedule="boltzmann")
        expected = 10.0 / (1 + math.log(5))
        assert abs(t - expected) < 1e-10

    def test_unknown_schedule_defaults_exponential(self):
        unknown = adaptive_temperature(
            3, initial_temp=10.0, cooling_rate=0.9, schedule="unknown"
        )
        exp = adaptive_temperature(
            3, initial_temp=10.0, cooling_rate=0.9, schedule="exponential"
        )
        assert unknown == exp

    def test_negative_iteration_clamped(self):
        t = adaptive_temperature(-5, initial_temp=10.0, schedule="exponential")
        assert t == 10.0

    def test_min_temp_enforced(self):
        """Temperature never goes below min_temp."""
        t = adaptive_temperature(
            1000,
            initial_temp=10.0,
            cooling_rate=0.5,
            schedule="exponential",
            min_temp=0.01,
        )
        assert t == 0.01

    def test_all_schedules_decreasing(self):
        """All schedules should generally decrease with iteration."""
        for sched in ["exponential", "linear", "logarithmic", "cauchy", "boltzmann"]:
            t0 = adaptive_temperature(0, initial_temp=10.0, schedule=sched)
            t100 = adaptive_temperature(100, initial_temp=10.0, schedule=sched)
            assert t100 <= t0, f"{sched} should decrease"


# ── boltzmann_probability ───────────────────────────────────────────────


class TestBoltzmannProbability:
    def test_negative_delta_always_accept(self):
        """Improvements always accepted: P = 1.0."""
        assert boltzmann_probability(-5.0, 1.0) == 1.0

    def test_zero_delta_always_accept(self):
        assert boltzmann_probability(0.0, 1.0) == 1.0

    def test_positive_delta_less_than_one(self):
        """Worsening accepted with probability < 1."""
        p = boltzmann_probability(1.0, 1.0)
        assert 0.0 < p < 1.0

    def test_zero_temperature_never_accept(self):
        assert boltzmann_probability(5.0, 0.0) == 0.0

    def test_negative_temperature_never_accept(self):
        assert boltzmann_probability(5.0, -1.0) == 0.0

    def test_high_temperature_approaches_one(self):
        """At very high T, P → 1 even for large ΔE."""
        p = boltzmann_probability(1.0, 1e6)
        assert p > 0.999

    def test_low_temperature_approaches_zero(self):
        """At very low T, P → 0 for positive ΔE."""
        p = boltzmann_probability(10.0, 0.001)
        assert p < 0.001

    def test_exact_formula(self):
        """P = exp(-ΔE / T)."""
        p = boltzmann_probability(2.0, 3.0)
        expected = math.exp(-2.0 / 3.0)
        assert abs(p - expected) < 1e-10

    def test_large_delta_underflow_protection(self):
        """Very large ΔE/T → 0 without crashing."""
        p = boltzmann_probability(1e6, 0.001)
        assert p == 0.0

    def test_probability_between_0_and_1(self):
        for delta in [0.1, 1.0, 5.0, 50.0]:
            for temp in [0.01, 0.1, 1.0, 10.0]:
                p = boltzmann_probability(delta, temp)
                assert 0.0 <= p <= 1.0


# ── EnergyLandscapeAnalyzer ────────────────────────────────────────────


class TestEnergyLandscapeAnalyzer:
    def test_init_default_sample_size(self):
        analyzer = EnergyLandscapeAnalyzer()
        assert analyzer.sample_size == 100

    def test_init_custom_sample_size(self):
        analyzer = EnergyLandscapeAnalyzer(sample_size=50)
        assert analyzer.sample_size == 50

    def test_analyze_empty_assignments(self):
        analyzer = EnergyLandscapeAnalyzer()
        result = analyzer.analyze_landscape([])
        assert result["current_energy"] == 0.0
        assert result["is_local_minimum"] is True
        assert isinstance(result["features"], LandscapeFeatures)

    def test_analyze_single_assignment(self):
        analyzer = EnergyLandscapeAnalyzer(sample_size=10)
        assignments = [_make_assignment("p1", "r1")]
        result = analyzer.analyze_landscape(assignments)
        assert "current_energy" in result
        assert "is_local_minimum" in result
        assert "features" in result

    def test_analyze_returns_features(self):
        analyzer = EnergyLandscapeAnalyzer(sample_size=5)
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
            _make_assignment("p3", "r3"),
        ]
        result = analyzer.analyze_landscape(assignments)
        features = result["features"]
        assert isinstance(features, LandscapeFeatures)
        assert len(features.gradient_norms) > 0

    def test_analyze_has_all_keys(self):
        analyzer = EnergyLandscapeAnalyzer(sample_size=5)
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
        ]
        result = analyzer.analyze_landscape(assignments)
        expected_keys = {
            "features",
            "current_energy",
            "is_local_minimum",
            "estimated_basin_size",
            "mean_barrier_height",
            "mean_gradient",
            "landscape_ruggedness",
        }
        assert expected_keys == set(result.keys())

    def test_perturb_single_returns_same(self):
        analyzer = EnergyLandscapeAnalyzer()
        assignments = [_make_assignment("p1")]
        result = analyzer._perturb_assignments(assignments)
        assert len(result) == 1

    def test_perturb_preserves_length(self):
        analyzer = EnergyLandscapeAnalyzer()
        assignments = [_make_assignment(f"p{i}") for i in range(20)]
        result = analyzer._perturb_assignments(assignments)
        assert len(result) == 20

    def test_find_local_minima(self):
        analyzer = EnergyLandscapeAnalyzer()
        assignments = [
            _make_assignment("p1", "r1", score=0.5),
            _make_assignment("p2", "r2", score=0.8),
        ]
        minima = analyzer.find_local_minima(assignments, max_iterations=10)
        assert len(minima) >= 1
        assert "energy" in minima[0]
        assert "is_minimum" in minima[0]

    def test_find_local_minima_empty(self):
        analyzer = EnergyLandscapeAnalyzer()
        minima = analyzer.find_local_minima([], max_iterations=10)
        assert len(minima) >= 1

    def test_ruggedness_non_negative(self):
        analyzer = EnergyLandscapeAnalyzer(sample_size=5)
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
            _make_assignment("p3", "r3"),
        ]
        result = analyzer.analyze_landscape(assignments)
        assert result["landscape_ruggedness"] >= 0.0

    def test_deterministic_with_seed(self):
        """Analyzer uses seeded RNG for reproducibility."""
        a1 = EnergyLandscapeAnalyzer(sample_size=5)
        a2 = EnergyLandscapeAnalyzer(sample_size=5)
        assignments = [
            _make_assignment("p1", "r1"),
            _make_assignment("p2", "r2"),
        ]
        r1 = a1.analyze_landscape(assignments)
        r2 = a2.analyze_landscape(assignments)
        assert r1["current_energy"] == r2["current_energy"]
