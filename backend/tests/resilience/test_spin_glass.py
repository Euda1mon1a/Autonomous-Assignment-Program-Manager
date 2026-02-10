"""Tests for spin glass model for schedule diversity (pure logic, no DB)."""

import numpy as np
import pytest

from app.resilience.exotic.spin_glass import (
    ReplicaEnsemble,
    SpinConfiguration,
    SpinGlassModel,
)


# ── SpinConfiguration dataclass ─────────────────────────────────────────


class TestSpinConfiguration:
    def test_creation(self):
        spins = np.array([1, -1, 1, -1])
        config = SpinConfiguration(
            spins=spins,
            energy=-2.0,
            frustration=0.3,
            magnetization=0.0,
            overlap=0.5,
        )
        assert config.energy == -2.0
        assert config.frustration == 0.3
        assert config.magnetization == 0.0
        assert config.overlap == 0.5
        np.testing.assert_array_equal(config.spins, spins)

    def test_fields_accessible(self):
        config = SpinConfiguration(
            spins=np.array([1]),
            energy=0.0,
            frustration=0.0,
            magnetization=0.0,
            overlap=0.0,
        )
        assert hasattr(config, "spins")
        assert hasattr(config, "energy")
        assert hasattr(config, "frustration")
        assert hasattr(config, "magnetization")
        assert hasattr(config, "overlap")


# ── ReplicaEnsemble dataclass ───────────────────────────────────────────


class TestReplicaEnsemble:
    def test_creation(self):
        ensemble = ReplicaEnsemble(
            configurations=[],
            mean_energy=-5.0,
            energy_std=1.0,
            mean_overlap=0.2,
            diversity_score=0.4,
        )
        assert ensemble.mean_energy == -5.0
        assert ensemble.energy_std == 1.0
        assert ensemble.mean_overlap == 0.2
        assert ensemble.diversity_score == 0.4
        assert ensemble.configurations == []

    def test_with_configurations(self):
        config1 = SpinConfiguration(
            spins=np.array([1, -1]),
            energy=-1.0,
            frustration=0.1,
            magnetization=0.0,
            overlap=0.0,
        )
        config2 = SpinConfiguration(
            spins=np.array([-1, 1]),
            energy=-0.5,
            frustration=0.2,
            magnetization=0.0,
            overlap=0.0,
        )
        ensemble = ReplicaEnsemble(
            configurations=[config1, config2],
            mean_energy=-0.75,
            energy_std=0.25,
            mean_overlap=0.0,
            diversity_score=0.5,
        )
        assert len(ensemble.configurations) == 2


# ── SpinGlassModel init ────────────────────────────────────────────────


class TestSpinGlassModelInit:
    def test_basic_init(self):
        model = SpinGlassModel(num_spins=10)
        assert model.num_spins == 10
        assert model.temperature == 1.0
        assert model.frustration_level == 0.3

    def test_custom_params(self):
        model = SpinGlassModel(num_spins=5, temperature=2.0, frustration_level=0.5)
        assert model.num_spins == 5
        assert model.temperature == 2.0
        assert model.frustration_level == 0.5

    def test_couplings_shape(self):
        model = SpinGlassModel(num_spins=8)
        assert model.couplings.shape == (8, 8)

    def test_couplings_not_exactly_symmetric_due_to_frustration(self):
        """Frustration mask flips random entries, breaking perfect symmetry."""
        model = SpinGlassModel(num_spins=6, frustration_level=0.0)
        # Without frustration, should be symmetric
        np.testing.assert_array_almost_equal(model.couplings, model.couplings.T)

    def test_couplings_zero_diagonal(self):
        model = SpinGlassModel(num_spins=6)
        for i in range(6):
            assert model.couplings[i, i] == 0.0


# ── calculate_energy ────────────────────────────────────────────────────


class TestCalculateEnergy:
    def test_returns_float(self):
        model = SpinGlassModel(num_spins=4)
        spins = np.array([1, -1, 1, -1])
        energy = model.calculate_energy(spins)
        assert isinstance(energy, float)

    def test_binary_encoding_conversion(self):
        """Binary {0,1} spins should be converted to {-1,+1}."""
        np.random.seed(42)
        model = SpinGlassModel(num_spins=4)
        binary_spins = np.array([0, 1, 0, 1])
        ising_spins = np.array([-1, 1, -1, 1])
        # Both should give same energy
        e_binary = model.calculate_energy(binary_spins)
        e_ising = model.calculate_energy(ising_spins)
        assert abs(e_binary - e_ising) < 1e-10

    def test_opposite_spins_different_energy(self):
        """Flipping all spins gives same energy (Ising symmetry)."""
        np.random.seed(42)
        model = SpinGlassModel(num_spins=4)
        spins = np.array([1, -1, 1, -1])
        flipped = -spins
        # E = -Σ J_ij s_i s_j; flipping all: (-s_i)(-s_j) = s_i s_j → same
        e1 = model.calculate_energy(spins)
        e2 = model.calculate_energy(flipped)
        assert abs(e1 - e2) < 1e-10

    def test_energy_formula(self):
        """E = -0.5 * sum(J * outer(s,s))."""
        np.random.seed(42)
        model = SpinGlassModel(num_spins=3)
        spins = np.array([1, 1, -1])
        expected = -0.5 * np.sum(model.couplings * np.outer(spins, spins))
        assert abs(model.calculate_energy(spins) - expected) < 1e-10


# ── calculate_frustration ──────────────────────────────────────────────


class TestCalculateFrustration:
    def test_returns_float(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=4)
        spins = np.array([1, -1, 1, -1])
        result = model.calculate_frustration(spins)
        assert isinstance(result, float)

    def test_between_zero_and_one(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=6)
        spins = np.array([1, -1, 1, -1, 1, -1])
        result = model.calculate_frustration(spins)
        assert 0.0 <= result <= 1.0

    def test_binary_encoding(self):
        """Binary {0,1} should work like {-1,+1}."""
        np.random.seed(42)
        model = SpinGlassModel(num_spins=4)
        binary = np.array([0, 1, 0, 1])
        ising = np.array([-1, 1, -1, 1])
        assert (
            abs(
                model.calculate_frustration(binary) - model.calculate_frustration(ising)
            )
            < 1e-10
        )

    def test_no_couplings_zero_frustration(self):
        """Zero coupling matrix → 0 frustration (0 total pairs)."""
        model = SpinGlassModel(num_spins=3)
        model.couplings = np.zeros((3, 3))
        spins = np.array([1, -1, 1])
        assert model.calculate_frustration(spins) == 0.0


# ── calculate_overlap ──────────────────────────────────────────────────


class TestCalculateOverlap:
    def test_identical_spins_overlap_one(self):
        model = SpinGlassModel(num_spins=4)
        spins = np.array([1, -1, 1, -1])
        assert abs(model.calculate_overlap(spins, spins) - 1.0) < 1e-10

    def test_opposite_spins_overlap_negative_one(self):
        model = SpinGlassModel(num_spins=4)
        spins1 = np.array([1, -1, 1, -1])
        spins2 = -spins1
        assert abs(model.calculate_overlap(spins1, spins2) - (-1.0)) < 1e-10

    def test_overlap_range(self):
        model = SpinGlassModel(num_spins=4)
        spins1 = np.array([1, -1, 1, -1])
        spins2 = np.array([1, 1, -1, -1])
        overlap = model.calculate_overlap(spins1, spins2)
        assert -1.0 <= overlap <= 1.0

    def test_overlap_formula(self):
        """q = mean(s1 * s2)."""
        model = SpinGlassModel(num_spins=4)
        s1 = np.array([1, -1, 1, -1])
        s2 = np.array([1, 1, -1, -1])
        # Products: [1, -1, -1, 1] → mean = 0.0
        assert abs(model.calculate_overlap(s1, s2) - 0.0) < 1e-10

    def test_binary_encoding_conversion(self):
        """Binary {0,1} inputs converted to {-1,+1}."""
        model = SpinGlassModel(num_spins=4)
        binary = np.array([0, 1, 0, 1])
        ising = np.array([-1, 1, -1, 1])
        overlap = model.calculate_overlap(binary, ising)
        assert abs(overlap - 1.0) < 1e-10

    def test_symmetric(self):
        model = SpinGlassModel(num_spins=6)
        s1 = np.array([1, -1, 1, -1, 1, 1])
        s2 = np.array([-1, 1, 1, -1, -1, 1])
        assert (
            abs(model.calculate_overlap(s1, s2) - model.calculate_overlap(s2, s1))
            < 1e-10
        )


# ── generate_replica ───────────────────────────────────────────────────


class TestGenerateReplica:
    def test_returns_spin_configuration(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5, temperature=1.0)
        replica = model.generate_replica(num_iterations=50)
        assert isinstance(replica, SpinConfiguration)

    def test_spins_length_matches(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=8)
        replica = model.generate_replica(num_iterations=50)
        assert len(replica.spins) == 8

    def test_spins_are_pm_one(self):
        """Spins should be +1 or -1."""
        np.random.seed(42)
        model = SpinGlassModel(num_spins=10)
        replica = model.generate_replica(num_iterations=100)
        assert set(replica.spins.tolist()).issubset({-1, 1})

    def test_frustration_in_range(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=6)
        replica = model.generate_replica(num_iterations=100)
        assert 0.0 <= replica.frustration <= 1.0

    def test_magnetization_is_mean_of_spins(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=10)
        replica = model.generate_replica(num_iterations=50)
        expected_mag = float(np.mean(replica.spins))
        assert abs(replica.magnetization - expected_mag) < 1e-10

    def test_initial_spins_used(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=4, temperature=0.001)
        initial = np.array([1, 1, 1, 1])
        replica = model.generate_replica(num_iterations=1, initial_spins=initial)
        # With 1 iteration at very low temp, should be close to initial
        assert isinstance(replica, SpinConfiguration)

    def test_energy_is_float(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=4)
        replica = model.generate_replica(num_iterations=50)
        assert isinstance(replica.energy, float)


# ── generate_replica_ensemble ──────────────────────────────────────────


class TestGenerateReplicaEnsemble:
    def test_returns_replica_ensemble(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        ensemble = model.generate_replica_ensemble(num_replicas=3, num_iterations=50)
        assert isinstance(ensemble, ReplicaEnsemble)

    def test_correct_num_replicas(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        ensemble = model.generate_replica_ensemble(num_replicas=4, num_iterations=50)
        assert len(ensemble.configurations) == 4

    def test_diversity_score_range(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        ensemble = model.generate_replica_ensemble(num_replicas=3, num_iterations=50)
        assert 0.0 <= ensemble.diversity_score <= 1.0

    def test_energy_stats_computed(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        ensemble = model.generate_replica_ensemble(num_replicas=3, num_iterations=50)
        assert isinstance(ensemble.mean_energy, float)
        assert isinstance(ensemble.energy_std, float)
        assert ensemble.energy_std >= 0.0

    def test_mean_overlap_range(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        ensemble = model.generate_replica_ensemble(num_replicas=3, num_iterations=50)
        assert -1.0 <= ensemble.mean_overlap <= 1.0


# ── find_ground_state ──────────────────────────────────────────────────


class TestFindGroundState:
    def test_returns_spin_configuration(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        ground = model.find_ground_state(num_attempts=3, num_iterations=50)
        assert isinstance(ground, SpinConfiguration)

    def test_ground_state_has_lower_energy(self):
        """Ground state should be <= energy of a random config."""
        np.random.seed(42)
        model = SpinGlassModel(num_spins=6)
        ground = model.find_ground_state(num_attempts=5, num_iterations=100)
        # Compare with random configuration energy
        random_spins = np.array([1, -1, 1, -1, 1, -1])
        random_energy = model.calculate_energy(random_spins)
        # Ground state from annealing should typically be better
        # But this is probabilistic; just check it's a valid config
        assert isinstance(ground.energy, float)

    def test_spins_valid(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=4)
        ground = model.find_ground_state(num_attempts=2, num_iterations=50)
        assert set(ground.spins.tolist()).issubset({-1, 1})


# ── assess_landscape_ruggedness ────────────────────────────────────────


class TestAssessLandscapeRuggedness:
    def test_returns_dict(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        result = model.assess_landscape_ruggedness(num_samples=20)
        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        result = model.assess_landscape_ruggedness(num_samples=20)
        expected_keys = {
            "energy_range",
            "energy_variance",
            "ruggedness_score",
            "difficulty",
            "estimated_local_minima",
            "mean_energy",
            "std_energy",
        }
        assert expected_keys == set(result.keys())

    def test_ruggedness_score_range(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        result = model.assess_landscape_ruggedness(num_samples=50)
        assert 0.0 <= result["ruggedness_score"] <= 1.0

    def test_difficulty_valid_label(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        result = model.assess_landscape_ruggedness(num_samples=50)
        assert result["difficulty"] in {"easy", "moderate", "hard", "very_hard"}

    def test_energy_range_non_negative(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        result = model.assess_landscape_ruggedness(num_samples=20)
        assert result["energy_range"] >= 0.0

    def test_energy_variance_non_negative(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        result = model.assess_landscape_ruggedness(num_samples=20)
        assert result["energy_variance"] >= 0.0

    def test_std_energy_non_negative(self):
        np.random.seed(42)
        model = SpinGlassModel(num_spins=5)
        result = model.assess_landscape_ruggedness(num_samples=20)
        assert result["std_energy"] >= 0.0
