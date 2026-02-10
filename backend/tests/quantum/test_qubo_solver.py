"""Tests for QUBO solver pure-logic components (no DB)."""

import os
from unittest.mock import patch

import pytest

from app.scheduling.quantum.qubo_solver import (
    BASE_READS,
    MAX_QUANTUM_VARS,
    MAX_READS,
    MAX_SWEEPS,
    MIN_READS,
    MIN_SWEEPS,
    SWEEPS_PER_VAR,
    QUBOFormulation,
    SimulatedQuantumAnnealingSolver,
    get_quantum_library_status,
    get_quantum_solver_config,
)


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------


class TestModuleConstants:
    def test_min_reads(self):
        assert MIN_READS == 100

    def test_max_reads(self):
        assert MAX_READS == 1000

    def test_base_reads(self):
        assert BASE_READS == 10000

    def test_min_sweeps(self):
        assert MIN_SWEEPS == 1000

    def test_max_sweeps(self):
        assert MAX_SWEEPS == 10000

    def test_sweeps_per_var(self):
        assert SWEEPS_PER_VAR == 10

    def test_max_quantum_vars(self):
        assert MAX_QUANTUM_VARS == 5000


class TestClassConstants:
    def test_hard_constraint_penalty(self):
        assert QUBOFormulation.HARD_CONSTRAINT_PENALTY == 10000.0

    def test_acgme_penalty(self):
        assert QUBOFormulation.ACGME_PENALTY == 5000.0

    def test_soft_constraint_penalty(self):
        assert QUBOFormulation.SOFT_CONSTRAINT_PENALTY == 100.0

    def test_penalty_ordering(self):
        assert (
            QUBOFormulation.HARD_CONSTRAINT_PENALTY
            > QUBOFormulation.ACGME_PENALTY
            > QUBOFormulation.SOFT_CONSTRAINT_PENALTY
        )


# ---------------------------------------------------------------------------
# get_quantum_library_status
# ---------------------------------------------------------------------------


class TestGetQuantumLibraryStatus:
    def test_returns_dict(self):
        status = get_quantum_library_status()
        assert isinstance(status, dict)

    def test_expected_keys(self):
        status = get_quantum_library_status()
        assert "pyqubo" in status
        assert "dwave_samplers" in status
        assert "dwave_system" in status
        assert "qubovert" in status

    def test_values_are_bool(self):
        status = get_quantum_library_status()
        for key, val in status.items():
            assert isinstance(val, bool), f"{key} should be bool"


# ---------------------------------------------------------------------------
# get_quantum_solver_config
# ---------------------------------------------------------------------------


class TestGetQuantumSolverConfig:
    def test_default_disabled(self):
        with patch.dict(os.environ, {}, clear=True):
            config = get_quantum_solver_config()
            assert config["enabled"] is False

    def test_enabled_via_env(self):
        with patch.dict(
            os.environ,
            {"USE_QUANTUM_SOLVER": "true"},
            clear=True,
        ):
            config = get_quantum_solver_config()
            assert config["enabled"] is True

    def test_default_backend_classical(self):
        with patch.dict(os.environ, {}, clear=True):
            config = get_quantum_solver_config()
            assert config["backend"] == "classical"

    def test_quantum_backend(self):
        with patch.dict(
            os.environ,
            {"QUANTUM_SOLVER_BACKEND": "quantum"},
            clear=True,
        ):
            config = get_quantum_solver_config()
            assert config["backend"] == "quantum"

    def test_dwave_token_from_env(self):
        with patch.dict(
            os.environ,
            {"DWAVE_API_TOKEN": "test-token-123"},
            clear=True,
        ):
            config = get_quantum_solver_config()
            assert config["dwave_token"] == "test-token-123"

    def test_no_dwave_token_default(self):
        with patch.dict(os.environ, {}, clear=True):
            config = get_quantum_solver_config()
            assert config["dwave_token"] is None

    def test_libraries_available_included(self):
        config = get_quantum_solver_config()
        assert "libraries_available" in config
        assert isinstance(config["libraries_available"], dict)

    def test_use_quantum_hardware_false_when_disabled(self):
        with patch.dict(
            os.environ,
            {"USE_QUANTUM_SOLVER": "false"},
            clear=True,
        ):
            config = get_quantum_solver_config()
            assert config["use_quantum_hardware"] is False

    def test_use_quantum_hardware_false_without_token(self):
        with patch.dict(
            os.environ,
            {
                "USE_QUANTUM_SOLVER": "true",
                "QUANTUM_SOLVER_BACKEND": "quantum",
            },
            clear=True,
        ):
            config = get_quantum_solver_config()
            # Without D-Wave token or libraries, hardware should be False
            assert config["use_quantum_hardware"] is False

    def test_case_insensitive_enabled(self):
        with patch.dict(
            os.environ,
            {"USE_QUANTUM_SOLVER": "TRUE"},
            clear=True,
        ):
            config = get_quantum_solver_config()
            assert config["enabled"] is True


# ---------------------------------------------------------------------------
# SimulatedQuantumAnnealingSolver — energy computation
# ---------------------------------------------------------------------------


def _make_solver(**kwargs) -> SimulatedQuantumAnnealingSolver:
    """Create a solver with no constraint manager."""
    defaults = {
        "constraint_manager": None,
        "timeout_seconds": 10.0,
        "num_reads": 1,
        "num_sweeps": 10,
        "seed": 42,
    }
    defaults.update(kwargs)
    return SimulatedQuantumAnnealingSolver(**defaults)


class TestComputeEnergy:
    def test_empty_qubo(self):
        solver = _make_solver()
        Q = {}
        sample = {0: 1, 1: 0}
        assert solver._compute_energy(sample, Q) == 0.0

    def test_linear_terms_only(self):
        solver = _make_solver()
        # Q[(i,i)] = linear term
        Q = {(0, 0): 2.0, (1, 1): -3.0}
        sample = {0: 1, 1: 1}
        # energy = 2.0 * 1 + (-3.0) * 1 = -1.0
        assert solver._compute_energy(sample, Q) == -1.0

    def test_linear_term_zero_variable(self):
        solver = _make_solver()
        Q = {(0, 0): 5.0}
        sample = {0: 0}
        assert solver._compute_energy(sample, Q) == 0.0

    def test_quadratic_terms(self):
        solver = _make_solver()
        Q = {(0, 1): 4.0}
        sample = {0: 1, 1: 1}
        assert solver._compute_energy(sample, Q) == 4.0

    def test_quadratic_with_zero(self):
        solver = _make_solver()
        Q = {(0, 1): 4.0}
        sample = {0: 1, 1: 0}
        assert solver._compute_energy(sample, Q) == 0.0

    def test_mixed_terms(self):
        solver = _make_solver()
        Q = {(0, 0): 1.0, (1, 1): -2.0, (0, 1): 3.0}
        sample = {0: 1, 1: 1}
        # energy = 1*1 + (-2)*1 + 3*1*1 = 1 - 2 + 3 = 2.0
        assert solver._compute_energy(sample, Q) == 2.0

    def test_missing_variable_defaults_to_zero(self):
        solver = _make_solver()
        Q = {(0, 0): 5.0, (0, 1): 3.0}
        sample = {0: 1}  # variable 1 missing, defaults to 0
        assert solver._compute_energy(sample, Q) == 5.0

    def test_all_zeros(self):
        solver = _make_solver()
        Q = {(0, 0): 1.0, (1, 1): 2.0, (0, 1): 3.0}
        sample = {0: 0, 1: 0}
        assert solver._compute_energy(sample, Q) == 0.0


class TestComputeDeltaEnergy:
    def test_flip_linear_from_zero_to_one(self):
        solver = _make_solver()
        Q = {(0, 0): 5.0}
        sample = {0: 0}
        # Flipping 0 from 0 to 1: delta = 1, energy_change = 5.0 * 1 = 5.0
        assert solver._compute_delta_energy(sample, Q, 0) == 5.0

    def test_flip_linear_from_one_to_zero(self):
        solver = _make_solver()
        Q = {(0, 0): 5.0}
        sample = {0: 1}
        # Flipping 0 from 1 to 0: delta = -1, energy_change = 5.0 * (-1) = -5.0
        assert solver._compute_delta_energy(sample, Q, 0) == -5.0

    def test_flip_with_quadratic_interaction(self):
        solver = _make_solver()
        Q = {(0, 1): 4.0}
        sample = {0: 0, 1: 1}
        # Flipping var 0 from 0 to 1: delta = 1
        # Quadratic: 4.0 * sample[1] * delta = 4.0 * 1 * 1 = 4.0
        assert solver._compute_delta_energy(sample, Q, 0) == 4.0

    def test_flip_quadratic_other_zero(self):
        solver = _make_solver()
        Q = {(0, 1): 4.0}
        sample = {0: 0, 1: 0}
        # Flipping var 0 from 0 to 1, but var 1 is 0
        # Quadratic: 4.0 * 0 * 1 = 0.0
        assert solver._compute_delta_energy(sample, Q, 0) == 0.0

    def test_delta_consistent_with_energy(self):
        solver = _make_solver()
        Q = {(0, 0): 2.0, (1, 1): -3.0, (0, 1): 1.5}
        sample = {0: 1, 1: 0}
        # Compute actual energy difference
        energy_before = solver._compute_energy(sample, Q)
        delta = solver._compute_delta_energy(sample, Q, 1)
        flipped = sample.copy()
        flipped[1] = 1 - flipped[1]
        energy_after = solver._compute_energy(flipped, Q)
        assert abs(delta - (energy_after - energy_before)) < 1e-10

    def test_delta_multiple_variables(self):
        solver = _make_solver()
        Q = {(0, 0): 1.0, (1, 1): 2.0, (2, 2): 3.0, (0, 1): 0.5, (1, 2): 0.7}
        sample = {0: 1, 1: 0, 2: 1}
        # Test consistency for flipping each variable
        for flip_idx in range(3):
            delta = solver._compute_delta_energy(sample, Q, flip_idx)
            energy_before = solver._compute_energy(sample, Q)
            flipped = sample.copy()
            flipped[flip_idx] = 1 - flipped[flip_idx]
            energy_after = solver._compute_energy(flipped, Q)
            assert abs(delta - (energy_after - energy_before)) < 1e-10


class TestSolvePurePython:
    def test_trivial_qubo_single_variable(self):
        solver = _make_solver(num_reads=5, num_sweeps=50)
        # Single variable with negative linear term: optimal is x=1
        Q = {(0, 0): -10.0}

        class FakeFormulation:
            num_variables = 1

        sample, energy = solver._solve_pure_python(Q, FakeFormulation())
        # With enough reads/sweeps, should find x=1
        assert sample[0] == 1
        assert energy == -10.0

    def test_two_variable_repulsion(self):
        solver = _make_solver(num_reads=10, num_sweeps=100, seed=42)
        # Both variables want to be 1 (negative linear), but high penalty for both=1
        Q = {(0, 0): -5.0, (1, 1): -5.0, (0, 1): 20.0}

        class FakeFormulation:
            num_variables = 2

        sample, energy = solver._solve_pure_python(Q, FakeFormulation())
        # Should pick exactly one variable = 1
        assert sample[0] + sample[1] == 1
        assert energy == -5.0

    def test_reproducibility_with_seed(self):
        Q = {(0, 0): -1.0, (1, 1): -2.0, (0, 1): 0.5}

        class FakeFormulation:
            num_variables = 2

        solver1 = _make_solver(num_reads=3, num_sweeps=20, seed=123)
        sample1, energy1 = solver1._solve_pure_python(Q, FakeFormulation())

        solver2 = _make_solver(num_reads=3, num_sweeps=20, seed=123)
        sample2, energy2 = solver2._solve_pure_python(Q, FakeFormulation())

        assert sample1 == sample2
        assert energy1 == energy2


# ---------------------------------------------------------------------------
# SimulatedQuantumAnnealingSolver — init
# ---------------------------------------------------------------------------


class TestSolverInit:
    def test_default_seed_is_set(self):
        solver = SimulatedQuantumAnnealingSolver(
            constraint_manager=None,
            timeout_seconds=30.0,
            num_reads=10,
            num_sweeps=100,
        )
        assert isinstance(solver.seed, int)
        assert solver.seed >= 0

    def test_custom_seed(self):
        solver = _make_solver(seed=999)
        assert solver.seed == 999

    def test_beta_range(self):
        solver = _make_solver(beta_range=(0.5, 3.0))
        assert solver.beta_range == (0.5, 3.0)

    def test_default_beta_range(self):
        solver = _make_solver()
        assert solver.beta_range == (0.1, 4.2)

    def test_stores_num_reads(self):
        solver = _make_solver(num_reads=50)
        assert solver.num_reads == 50

    def test_stores_num_sweeps(self):
        solver = _make_solver(num_sweeps=500)
        assert solver.num_sweeps == 500


# ---------------------------------------------------------------------------
# create_quantum_solver_from_env
# ---------------------------------------------------------------------------


class TestCreateQuantumSolverFromEnv:
    def test_disabled_returns_none(self):
        from app.scheduling.quantum.qubo_solver import create_quantum_solver_from_env

        with patch.dict(
            os.environ,
            {"USE_QUANTUM_SOLVER": "false"},
            clear=True,
        ):
            solver = create_quantum_solver_from_env()
            assert solver is None

    def test_enabled_classical_returns_sa_solver(self):
        from app.scheduling.quantum.qubo_solver import create_quantum_solver_from_env

        with patch.dict(
            os.environ,
            {
                "USE_QUANTUM_SOLVER": "true",
                "QUANTUM_SOLVER_BACKEND": "classical",
            },
            clear=True,
        ):
            solver = create_quantum_solver_from_env()
            assert isinstance(solver, SimulatedQuantumAnnealingSolver)

    def test_not_enabled_by_default(self):
        from app.scheduling.quantum.qubo_solver import create_quantum_solver_from_env

        with patch.dict(os.environ, {}, clear=True):
            solver = create_quantum_solver_from_env()
            assert solver is None
