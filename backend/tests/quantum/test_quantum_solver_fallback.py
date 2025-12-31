"""
Tests for quantum solver graceful fallback behavior.

Verifies that the quantum solver correctly handles:
1. Missing D-Wave libraries
2. Missing API tokens
3. Invalid API tokens
4. D-Wave service unavailable
5. Graceful fallback to classical simulated annealing
"""

import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.person import Person
from app.scheduling.constraints import SchedulingContext
from app.scheduling.quantum.qubo_solver import (
    QuantumInspiredSolver,
    SimulatedQuantumAnnealingSolver,
    get_quantum_library_status,
    get_quantum_solver_config,
    create_quantum_solver_from_env,
)


@pytest.fixture
def mock_context():
    """Create minimal scheduling context for testing."""
    from datetime import date, timedelta
    from app.models.block import Block
    from app.models.rotation_template import RotationTemplate

    # Create minimal context
    residents = [
        Person(
            id=uuid4(),
            name=f"Resident {i}",
            email=f"res{i}@test.com",
            role="RESIDENT",
        )
        for i in range(3)
    ]

    start_date = date(2025, 1, 1)
    blocks = [
        Block(
            id=uuid4(),
            date=start_date + timedelta(days=i),
            session="AM",
            is_weekend=(start_date + timedelta(days=i)).weekday() >= 5,
        )
        for i in range(10)
    ]

    templates = [
        RotationTemplate(
            id=uuid4(),
            name="Clinic",
            rotation_type="clinic",
            activity_type="outpatient",
            requires_procedure_credential=False,
        )
    ]

    context = SchedulingContext(
        blocks=blocks,
        residents=residents,
        faculty=[],
        templates=templates,
    )

    return context


class TestQuantumLibraryStatus:
    """Test quantum library availability detection."""

    def test_get_library_status(self):
        """Test library status detection returns dict."""
        status = get_quantum_library_status()

        assert isinstance(status, dict)
        assert "pyqubo" in status
        assert "dwave_samplers" in status
        assert "dwave_system" in status
        assert "qubovert" in status

        # All values should be boolean
        for key, value in status.items():
            assert isinstance(value, bool)


class TestQuantumSolverConfig:
    """Test quantum solver environment configuration."""

    def test_config_disabled_by_default(self):
        """Test quantum solver disabled when USE_QUANTUM_SOLVER not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_quantum_solver_config()

            assert config["enabled"] is False
            assert config["backend"] == "classical"
            assert config["dwave_token"] is None
            assert config["use_quantum_hardware"] is False

    def test_config_enabled_classical(self):
        """Test classical mode configuration."""
        with patch.dict(
            os.environ,
            {
                "USE_QUANTUM_SOLVER": "true",
                "QUANTUM_SOLVER_BACKEND": "classical",
            },
        ):
            config = get_quantum_solver_config()

            assert config["enabled"] is True
            assert config["backend"] == "classical"
            assert config["use_quantum_hardware"] is False

    def test_config_quantum_hardware_with_token(self):
        """Test quantum hardware mode with token."""
        with patch.dict(
            os.environ,
            {
                "USE_QUANTUM_SOLVER": "true",
                "QUANTUM_SOLVER_BACKEND": "quantum",
                "DWAVE_API_TOKEN": "test_token_123",
            },
        ):
            config = get_quantum_solver_config()

            assert config["enabled"] is True
            assert config["backend"] == "quantum"
            assert config["dwave_token"] == "test_token_123"
            # use_quantum_hardware depends on library availability

    def test_config_quantum_hardware_without_token(self):
        """Test quantum hardware mode fails without token."""
        with patch.dict(
            os.environ,
            {
                "USE_QUANTUM_SOLVER": "true",
                "QUANTUM_SOLVER_BACKEND": "quantum",
            },
        ):
            config = get_quantum_solver_config()

            assert config["enabled"] is True
            assert config["backend"] == "quantum"
            assert config["dwave_token"] is None
            assert config["use_quantum_hardware"] is False  # Token missing


class TestCreateQuantumSolverFromEnv:
    """Test quantum solver factory from environment."""

    def test_create_solver_disabled(self):
        """Test returns None when disabled."""
        with patch.dict(os.environ, {"USE_QUANTUM_SOLVER": "false"}):
            solver = create_quantum_solver_from_env()
            assert solver is None

    def test_create_solver_classical(self):
        """Test creates classical SA solver."""
        with patch.dict(
            os.environ,
            {
                "USE_QUANTUM_SOLVER": "true",
                "QUANTUM_SOLVER_BACKEND": "classical",
            },
        ):
            solver = create_quantum_solver_from_env()

            assert solver is not None
            assert isinstance(solver, SimulatedQuantumAnnealingSolver)

    def test_create_solver_quantum_without_token(self):
        """Test falls back to classical without token."""
        with patch.dict(
            os.environ,
            {
                "USE_QUANTUM_SOLVER": "true",
                "QUANTUM_SOLVER_BACKEND": "quantum",
            },
        ):
            solver = create_quantum_solver_from_env()

            # Should fall back to classical SA
            assert solver is not None
            assert isinstance(solver, SimulatedQuantumAnnealingSolver)


class TestQuantumInspiredSolverInit:
    """Test QuantumInspiredSolver initialization."""

    def test_init_without_quantum_hardware(self):
        """Test solver initializes in classical mode by default."""
        solver = QuantumInspiredSolver()

        assert solver.use_quantum_hardware is False
        assert solver.dwave_token is None

    def test_init_quantum_hardware_without_token(self):
        """Test quantum hardware request fails without token."""
        solver = QuantumInspiredSolver(use_quantum_hardware=True)

        # Should disable quantum hardware due to missing token
        assert solver.use_quantum_hardware is False

    def test_init_quantum_hardware_with_token(self):
        """Test quantum hardware enabled with token."""
        solver = QuantumInspiredSolver(
            use_quantum_hardware=True, dwave_token="test_token"
        )

        # use_quantum_hardware depends on library availability
        # If libraries missing, should still be False
        # If libraries present, should be True
        assert isinstance(solver.use_quantum_hardware, bool)
        assert solver.dwave_token == "test_token"


class TestSimulatedQuantumAnnealingSolver:
    """Test classical simulated annealing solver."""

    def test_solver_basic_solve(self, mock_context):
        """Test solver can solve basic problem."""
        solver = SimulatedQuantumAnnealingSolver(
            timeout_seconds=5.0, num_reads=10, num_sweeps=100
        )

        result = solver.solve(mock_context)

        assert result.success is True
        assert result.solver_status == "simulated_annealing"
        assert result.random_seed is not None
        assert result.runtime_seconds > 0
        assert "num_variables" in result.statistics
        assert "library" in result.statistics

    def test_solver_with_dwave_samplers_available(self, mock_context):
        """Test solver uses D-Wave samplers if available."""
        solver = SimulatedQuantumAnnealingSolver(
            timeout_seconds=5.0, num_reads=10, num_sweeps=100
        )

        result = solver.solve(mock_context)

        # Should complete regardless of library availability
        assert result.success is True
        assert result.statistics["library"] in ["dwave-samplers", "pure_python"]


class TestQuantumInspiredSolverFallback:
    """Test quantum solver graceful fallback."""

    def test_solve_classical_mode(self, mock_context):
        """Test solving in classical mode."""
        solver = QuantumInspiredSolver(use_quantum_hardware=False)

        result = solver.solve(mock_context)

        assert result.success is True
        assert result.solver_status == "simulated_annealing"

    @patch("app.scheduling.quantum.qubo_solver.DWAVE_SYSTEM_AVAILABLE", False)
    def test_solve_quantum_mode_libraries_unavailable(self, mock_context):
        """Test fallback when D-Wave libraries unavailable."""
        solver = QuantumInspiredSolver(
            use_quantum_hardware=True, dwave_token="test_token"
        )

        # Should have disabled quantum hardware during init
        assert solver.use_quantum_hardware is False

        result = solver.solve(mock_context)

        assert result.success is True
        assert result.solver_status == "simulated_annealing"

    def test_solve_quantum_mode_no_token(self, mock_context):
        """Test fallback when token missing."""
        solver = QuantumInspiredSolver(use_quantum_hardware=True, dwave_token=None)

        # Should have disabled quantum hardware during init
        assert solver.use_quantum_hardware is False

        result = solver.solve(mock_context)

        assert result.success is True

    @patch("app.scheduling.quantum.qubo_solver.DWAVE_SYSTEM_AVAILABLE", True)
    def test_solve_dwave_connection_fails(self, mock_context):
        """Test fallback when D-Wave connection fails."""
        # Mock D-Wave sampler to raise exception
        with patch(
            "app.scheduling.quantum.qubo_solver.DWaveSampler"
        ) as mock_sampler:
            mock_sampler.side_effect = Exception("Connection timeout")

            solver = QuantumInspiredSolver(
                use_quantum_hardware=True, dwave_token="test_token"
            )

            result = solver.solve(mock_context)

            # Should succeed with classical fallback
            assert result.success is True
            assert result.solver_status == "classical_fallback"
            assert result.statistics["used_quantum"] is False


class TestQUBOSolverWithMockDWave:
    """Test QUBO solver with mocked D-Wave."""

    @pytest.fixture
    def mock_dwave_response(self):
        """Create mock D-Wave response."""
        mock_response = MagicMock()
        mock_response.first.sample = {0: 1, 1: 0, 2: 1}
        mock_response.first.energy = -42.0
        return mock_response

    @patch("app.scheduling.quantum.qubo_solver.DWAVE_SYSTEM_AVAILABLE", True)
    @patch("app.scheduling.quantum.qubo_solver.PYQUBO_AVAILABLE", False)
    def test_quantum_solver_with_mock_dwave(self, mock_context, mock_dwave_response):
        """Test quantum solver with mocked D-Wave hardware."""
        with patch(
            "app.scheduling.quantum.qubo_solver.EmbeddingComposite"
        ) as mock_composite:
            mock_sampler = MagicMock()
            mock_sampler.sample_qubo.return_value = mock_dwave_response
            mock_composite.return_value = mock_sampler

            solver = QuantumInspiredSolver(
                use_quantum_hardware=True, dwave_token="test_token"
            )

            result = solver.solve(mock_context)

            assert result.success is True
            assert result.solver_status == "dwave_quantum"
            assert result.statistics["used_quantum"] is True
            assert result.statistics["backend"] == "dwave"


def test_solver_error_handling(mock_context):
    """Test solver handles errors gracefully."""
    # Create solver with minimal settings
    solver = SimulatedQuantumAnnealingSolver(
        timeout_seconds=1.0, num_reads=1, num_sweeps=10
    )

    # Should not raise exception even with tight timeout
    result = solver.solve(mock_context)

    assert result is not None
    assert hasattr(result, "success")
    assert hasattr(result, "solver_status")


def test_solver_with_empty_context():
    """Test solver handles empty context gracefully."""
    from app.scheduling.constraints import SchedulingContext

    empty_context = SchedulingContext(blocks=[], residents=[], faculty=[], templates=[])

    solver = SimulatedQuantumAnnealingSolver()
    result = solver.solve(empty_context)

    assert result.success is False
    assert result.status == "empty"
    assert result.solver_status == "No variables to optimize"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
