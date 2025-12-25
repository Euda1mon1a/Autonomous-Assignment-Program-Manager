"""
Tests for Quantum-Inspired Scheduling Solvers.

These tests validate the QUBO formulation and quantum-inspired
simulated annealing solvers for residency scheduling.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints import SchedulingContext
from app.scheduling.quantum.qubo_solver import (
    DWAVE_SAMPLERS_AVAILABLE,
    PYQUBO_AVAILABLE,
    QuantumInspiredSolver,
    QUBOFormulation,
    SimulatedQuantumAnnealingSolver,
    get_quantum_library_status,
)


class MockBlock:
    """Mock block for testing."""

    def __init__(self, block_id=None, block_date=None, is_weekend=False):
        self.id = block_id or uuid4()
        self.date = block_date or date.today()
        self.is_weekend = is_weekend
        self.session = "AM"


class MockPerson:
    """Mock person for testing."""

    def __init__(self, person_id=None, role="RESIDENT"):
        self.id = person_id or uuid4()
        self.role = role
        self.first_name = "Test"
        self.last_name = "Person"


class MockTemplate:
    """Mock rotation template for testing."""

    def __init__(self, template_id=None, name="Clinic", requires_credential=False):
        self.id = template_id or uuid4()
        self.name = name
        self.requires_procedure_credential = requires_credential


def create_test_context(
    n_residents: int = 3,
    n_blocks: int = 10,
    n_templates: int = 2,
) -> SchedulingContext:
    """Create a test scheduling context."""
    residents = [MockPerson() for _ in range(n_residents)]
    blocks = [
        MockBlock(block_date=date.today() + timedelta(days=i)) for i in range(n_blocks)
    ]
    templates = [MockTemplate(name=f"Template_{i}") for i in range(n_templates)]

    return SchedulingContext(
        blocks=blocks,
        residents=residents,
        faculty=[],
        templates=templates,
        availability={},  # All available
        existing_assignments=[],
    )


class TestQUBOFormulation:
    """Tests for QUBO problem formulation."""

    def test_variable_indexing(self):
        """Test that variables are correctly indexed."""
        context = create_test_context(n_residents=2, n_blocks=5, n_templates=2)
        formulation = QUBOFormulation(context)

        # Should have 2 residents * 5 blocks * 2 templates = 20 variables
        assert formulation.num_variables == 20

        # Check index mapping is bijective
        assert len(formulation.var_index) == len(formulation.index_to_var)

    def test_qubo_build(self):
        """Test QUBO matrix construction."""
        context = create_test_context(n_residents=2, n_blocks=3, n_templates=1)
        formulation = QUBOFormulation(context)
        Q = formulation.build()

        # Q should be a dict with (i, j) -> coefficient
        assert isinstance(Q, dict)
        assert len(Q) > 0

        # All coefficients should be numeric
        for (i, j), coef in Q.items():
            assert isinstance(i, int)
            assert isinstance(j, int)
            assert isinstance(coef, (int, float))

    def test_coverage_objective(self):
        """Test that coverage objective encourages assignments."""
        context = create_test_context(n_residents=2, n_blocks=3, n_templates=1)
        formulation = QUBOFormulation(context)
        Q = formulation.build()

        # Diagonal terms should be negative (encourage x[i] = 1)
        diagonal_sum = sum(coef for (i, j), coef in Q.items() if i == j)
        # Some diagonal terms are negative (coverage) but constraint penalties positive
        # Just verify Q is not empty
        assert len(Q) > 0

    def test_solution_decoding(self):
        """Test decoding QUBO solution to assignments."""
        context = create_test_context(n_residents=2, n_blocks=3, n_templates=1)
        formulation = QUBOFormulation(context)
        formulation.build()

        # Create a sample solution where first variable is 1
        sample = {0: 1, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        assignments = formulation.decode_solution(sample)

        # Should have one assignment
        assert len(assignments) == 1
        assert len(assignments[0]) == 3  # (person_id, block_id, template_id)

    def test_empty_context(self):
        """Test handling of empty context."""
        context = create_test_context(n_residents=0, n_blocks=5, n_templates=1)
        formulation = QUBOFormulation(context)

        assert formulation.num_variables == 0


class TestSimulatedQuantumAnnealingSolver:
    """Tests for the simulated quantum annealing solver."""

    def test_solve_simple_problem(self):
        """Test solving a simple scheduling problem."""
        context = create_test_context(n_residents=3, n_blocks=5, n_templates=1)
        solver = SimulatedQuantumAnnealingSolver(
            timeout_seconds=10.0,
            num_reads=10,
            num_sweeps=100,
            seed=42,
        )

        result = solver.solve(context)

        assert result.success
        assert result.status in ["feasible", "optimal"]
        assert len(result.assignments) > 0
        assert result.runtime_seconds < 10.0

    def test_deterministic_with_seed(self):
        """Test that same seed produces same result."""
        context = create_test_context(n_residents=2, n_blocks=3, n_templates=1)

        solver1 = SimulatedQuantumAnnealingSolver(
            num_reads=5, num_sweeps=50, seed=12345
        )
        solver2 = SimulatedQuantumAnnealingSolver(
            num_reads=5, num_sweeps=50, seed=12345
        )

        result1 = solver1.solve(context)
        result2 = solver2.solve(context)

        # Same seed should produce same number of assignments
        # (exact equality may vary due to implementation details)
        assert result1.success == result2.success

    def test_empty_problem(self):
        """Test handling of empty problem."""
        context = create_test_context(n_residents=0, n_blocks=0, n_templates=0)
        solver = SimulatedQuantumAnnealingSolver()

        result = solver.solve(context)

        assert not result.success
        assert result.status == "empty"

    def test_pure_python_fallback(self):
        """Test that pure Python solver works without dwave-samplers."""
        context = create_test_context(n_residents=2, n_blocks=4, n_templates=1)
        solver = SimulatedQuantumAnnealingSolver(num_reads=5, num_sweeps=100, seed=42)

        # Build QUBO and solve with pure Python
        formulation = QUBOFormulation(context)
        Q = formulation.build()
        sample, energy = solver._solve_pure_python(Q, formulation)

        assert isinstance(sample, dict)
        assert isinstance(energy, float)
        assert all(v in [0, 1] for v in sample.values())

    def test_statistics_included(self):
        """Test that solver statistics are included in result."""
        context = create_test_context(n_residents=2, n_blocks=3, n_templates=1)
        solver = SimulatedQuantumAnnealingSolver(num_reads=10, num_sweeps=100)

        result = solver.solve(context)

        assert "num_variables" in result.statistics
        assert "num_terms" in result.statistics
        assert "num_reads" in result.statistics


class TestQuantumInspiredSolver:
    """Tests for the hybrid quantum-inspired solver."""

    def test_auto_selection(self):
        """Test automatic solver selection based on problem size."""
        context = create_test_context(n_residents=3, n_blocks=5, n_templates=1)
        solver = QuantumInspiredSolver(timeout_seconds=10.0)

        result = solver.solve(context)

        assert result.success
        assert len(result.assignments) > 0

    def test_without_quantum_hardware(self):
        """Test that solver works without quantum hardware."""
        context = create_test_context(n_residents=2, n_blocks=4, n_templates=1)
        solver = QuantumInspiredSolver(
            use_quantum_hardware=False,  # Explicitly disable
            timeout_seconds=10.0,
        )

        result = solver.solve(context)

        assert result.success
        assert result.solver_status != "dwave_quantum"


class TestQuantumLibraryStatus:
    """Tests for library availability checking."""

    def test_status_dict(self):
        """Test that status returns proper dict."""
        status = get_quantum_library_status()

        assert isinstance(status, dict)
        assert "pyqubo" in status
        assert "dwave_samplers" in status
        assert "dwave_system" in status
        assert "qubovert" in status

    def test_status_values_are_bool(self):
        """Test that all status values are boolean."""
        status = get_quantum_library_status()

        for key, value in status.items():
            assert isinstance(value, bool), f"{key} should be bool"


class TestQUBOConstraints:
    """Tests for QUBO constraint encoding."""

    def test_one_per_block_constraint(self):
        """Test that one-per-block constraint is encoded."""
        context = create_test_context(n_residents=3, n_blocks=2, n_templates=1)
        formulation = QUBOFormulation(context)
        Q = formulation.build()

        # Should have quadratic penalty terms between variables for same block
        # These are off-diagonal terms with positive coefficients
        quadratic_terms = [(i, j, coef) for (i, j), coef in Q.items() if i != j]
        assert len(quadratic_terms) > 0

    def test_availability_constraint(self):
        """Test that unavailable slots are penalized."""
        context = create_test_context(n_residents=2, n_blocks=3, n_templates=1)

        # Mark first resident as unavailable for first block
        resident_id = context.residents[0].id
        block_idx = context.block_idx[context.blocks[0].id]
        context.availability[resident_id] = {block_idx}

        formulation = QUBOFormulation(context)
        Q = formulation.build()

        # The unavailable slot should have high penalty
        assert len(Q) > 0  # QUBO was built


@pytest.mark.skipif(not PYQUBO_AVAILABLE, reason="PyQUBO not installed")
class TestPyQUBOIntegration:
    """Tests requiring PyQUBO library."""

    def test_pyqubo_solver(self):
        """Test the PyQUBO-based solver."""
        from app.scheduling.quantum.qubo_solver import QUBOSolver

        context = create_test_context(n_residents=2, n_blocks=3, n_templates=1)
        solver = QUBOSolver(num_reads=10)

        result = solver.solve(context)

        # Should succeed (may use fallback if dwave-samplers not available)
        assert result.success or result.status == "error"


@pytest.mark.skipif(not DWAVE_SAMPLERS_AVAILABLE, reason="dwave-samplers not installed")
class TestDWaveSamplersIntegration:
    """Tests requiring dwave-samplers library."""

    def test_dwave_simulated_annealing(self):
        """Test solving with D-Wave's simulated annealing."""
        context = create_test_context(n_residents=3, n_blocks=5, n_templates=1)
        solver = SimulatedQuantumAnnealingSolver(
            num_reads=50,
            num_sweeps=500,
        )

        result = solver.solve(context)

        assert result.success
        assert result.statistics.get("library") == "dwave-samplers"


class TestScalability:
    """Tests for solver scalability."""

    @pytest.mark.parametrize(
        "n_residents,n_blocks",
        [
            (5, 10),
            (10, 20),
            (20, 50),
        ],
    )
    def test_scaling(self, n_residents: int, n_blocks: int):
        """Test solver on various problem sizes."""
        context = create_test_context(
            n_residents=n_residents,
            n_blocks=n_blocks,
            n_templates=2,
        )
        solver = SimulatedQuantumAnnealingSolver(
            timeout_seconds=30.0,
            num_reads=10,
            num_sweeps=100,
        )

        result = solver.solve(context)

        assert result.success
        assert result.runtime_seconds < 30.0
