"""
Tests for the scheduling solvers.

Tests cover:
- GreedySolver
- CPSATSolver
- PuLPSolver
- HybridSolver
- SolverFactory
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints import (
    ConstraintManager,
    SchedulingContext,
)
from app.scheduling.solvers import (
    CPSATSolver,
    GreedySolver,
    HybridSolver,
    PuLPSolver,
    SolverFactory,
    SolverResult,
)

# ============================================================================
# Test Fixtures
# ============================================================================

class MockPerson:
    """Mock person for testing."""
    def __init__(self, id=None, name="Test Person", person_type="resident", pgy_level=1):
        self.id = id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level


class MockBlock:
    """Mock block for testing."""
    def __init__(self, id=None, block_date=None, time_of_day="AM", is_weekend=False):
        self.id = id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day
        self.is_weekend = is_weekend


class MockTemplate:
    """Mock rotation template for testing."""
    def __init__(self, id=None, name="Test Rotation", max_residents=None, requires_procedure_credential=False):
        self.id = id or uuid4()
        self.name = name
        self.max_residents = max_residents
        self.requires_procedure_credential = requires_procedure_credential


@pytest.fixture
def small_context():
    """Create a small scheduling context for quick tests."""
    residents = [
        MockPerson(name=f"Resident {i}", pgy_level=(i % 3) + 1)
        for i in range(3)
    ]
    faculty = [MockPerson(name="Faculty 1", person_type="faculty", pgy_level=None)]

    # Create blocks for 3 days
    start_date = date(2024, 1, 1)
    blocks = []
    for day_offset in range(3):
        block_date = start_date + timedelta(days=day_offset)
        for tod in ["AM", "PM"]:
            blocks.append(MockBlock(
                block_date=block_date,
                time_of_day=tod,
                is_weekend=False,
            ))

    templates = [MockTemplate(name="Clinic")]

    context = SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=blocks,
        templates=templates,
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
    )

    # Set all as available
    for r in residents:
        context.availability[r.id] = {}
        for b in blocks:
            context.availability[r.id][b.id] = {"available": True, "replacement": None}

    for f in faculty:
        context.availability[f.id] = {}
        for b in blocks:
            context.availability[f.id][b.id] = {"available": True, "replacement": None}

    return context


@pytest.fixture
def medium_context():
    """Create a medium-sized context for solver tests."""
    residents = [
        MockPerson(name=f"Resident {i}", pgy_level=(i % 3) + 1)
        for i in range(6)
    ]
    faculty = [
        MockPerson(name=f"Faculty {i}", person_type="faculty", pgy_level=None)
        for i in range(2)
    ]

    # Create blocks for 2 weeks (exclude weekends)
    start_date = date(2024, 1, 1)
    blocks = []
    for day_offset in range(14):
        block_date = start_date + timedelta(days=day_offset)
        is_weekend = block_date.weekday() >= 5
        for tod in ["AM", "PM"]:
            blocks.append(MockBlock(
                block_date=block_date,
                time_of_day=tod,
                is_weekend=is_weekend,
            ))

    templates = [
        MockTemplate(name="Clinic"),
        MockTemplate(name="Inpatient"),
    ]

    context = SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=blocks,
        templates=templates,
        start_date=start_date,
        end_date=start_date + timedelta(days=13),
    )

    # Set all as available
    for r in residents:
        context.availability[r.id] = {}
        for b in blocks:
            context.availability[r.id][b.id] = {"available": True, "replacement": None}

    for f in faculty:
        context.availability[f.id] = {}
        for b in blocks:
            context.availability[f.id][b.id] = {"available": True, "replacement": None}

    return context


# ============================================================================
# Greedy Solver Tests
# ============================================================================

class TestGreedySolver:
    """Tests for GreedySolver."""

    def test_solve_small_problem(self, small_context):
        """Test solving a small scheduling problem."""
        solver = GreedySolver()
        result = solver.solve(small_context)

        assert result.success is True
        assert len(result.assignments) > 0
        assert result.status in ["feasible", "optimal"]

    def test_solve_produces_valid_assignments(self, small_context):
        """Test that solver produces valid assignments."""
        solver = GreedySolver()
        result = solver.solve(small_context)

        # Check all assignments have valid IDs
        resident_ids = {r.id for r in small_context.residents}
        block_ids = {b.id for b in small_context.blocks}
        template_ids = {t.id for t in small_context.templates}

        for person_id, block_id, template_id in result.assignments:
            assert person_id in resident_ids
            assert block_id in block_ids
            assert template_id in template_ids  # All assignments must have a rotation

    def test_solve_respects_availability(self, small_context):
        """Test that solver respects availability constraints."""
        # Mark first resident as unavailable for first block
        resident = small_context.residents[0]
        block = small_context.blocks[0]
        small_context.availability[resident.id][block.id] = {
            "available": False,
            "replacement": "Leave",
        }

        solver = GreedySolver()
        result = solver.solve(small_context)

        # Check that unavailable resident is not assigned to that block
        for person_id, block_id, _ in result.assignments:
            if block_id == block.id:
                assert person_id != resident.id

    def test_solve_empty_context_fails(self):
        """Test that empty context returns failure."""
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        solver = GreedySolver()
        result = solver.solve(context)

        assert result.success is False

    def test_solve_respects_rotation_capacity(self, small_context):
        """Test that solver respects rotation template capacity limits."""
        # Set max_residents to 1 for the only template
        small_context.templates[0].max_residents = 1

        solver = GreedySolver()
        result = solver.solve(small_context)

        # Count assignments per template per block
        from collections import defaultdict
        template_block_counts = defaultdict(lambda: defaultdict(int))
        for person_id, block_id, template_id in result.assignments:
            template_block_counts[template_id][block_id] += 1

        # Verify no block has more than max_residents for any template
        for template_id, block_counts in template_block_counts.items():
            for block_id, count in block_counts.items():
                assert count <= 1, f"Template {template_id} has {count} residents in block {block_id} (max: 1)"


# ============================================================================
# CP-SAT Solver Tests
# ============================================================================

class TestCPSATSolver:
    """Tests for CPSATSolver."""

    def test_solve_small_problem(self, small_context):
        """Test solving a small scheduling problem."""
        solver = CPSATSolver(timeout_seconds=10)
        result = solver.solve(small_context)

        assert result.success is True
        assert len(result.assignments) > 0

    def test_solve_with_constraints(self, medium_context):
        """Test solving with constraint manager."""
        manager = ConstraintManager.create_default()
        solver = CPSATSolver(
            constraint_manager=manager,
            timeout_seconds=30,
        )

        result = solver.solve(medium_context)

        assert result.success is True
        assert result.solver_status in ["OPTIMAL", "FEASIBLE"]

    def test_solve_returns_statistics(self, small_context):
        """Test that solver returns useful statistics."""
        solver = CPSATSolver(timeout_seconds=10)
        result = solver.solve(small_context)

        assert result.statistics is not None
        assert "total_blocks" in result.statistics
        assert "total_residents" in result.statistics

    def test_solve_assigns_valid_rotations(self, small_context):
        """Test that all assignments have valid rotation template IDs."""
        solver = CPSATSolver(timeout_seconds=10)
        result = solver.solve(small_context)

        template_ids = {t.id for t in small_context.templates}

        for person_id, block_id, template_id in result.assignments:
            assert template_id in template_ids
            assert template_id is not None  # Must have a rotation


# ============================================================================
# PuLP Solver Tests
# ============================================================================

class TestPuLPSolver:
    """Tests for PuLPSolver."""

    def test_solve_small_problem(self, small_context):
        """Test solving a small scheduling problem."""
        solver = PuLPSolver(timeout_seconds=10)
        result = solver.solve(small_context)

        assert result.success is True
        assert len(result.assignments) > 0

    def test_solve_with_constraints(self, small_context):
        """Test solving with constraint manager."""
        manager = ConstraintManager.create_minimal()
        solver = PuLPSolver(
            constraint_manager=manager,
            timeout_seconds=30,
        )

        result = solver.solve(small_context)

        assert result.success is True

    def test_solve_returns_objective_value(self, small_context):
        """Test that solver returns objective value."""
        solver = PuLPSolver(timeout_seconds=10)
        result = solver.solve(small_context)

        # PuLP should return an objective value
        assert result.objective_value is not None

    def test_solve_assigns_valid_rotations(self, small_context):
        """Test that all assignments have valid rotation template IDs."""
        solver = PuLPSolver(timeout_seconds=10)
        result = solver.solve(small_context)

        template_ids = {t.id for t in small_context.templates}

        for person_id, block_id, template_id in result.assignments:
            assert template_id in template_ids
            assert template_id is not None  # Must have a rotation


# ============================================================================
# Hybrid Solver Tests
# ============================================================================

class TestHybridSolver:
    """Tests for HybridSolver."""

    def test_solve_small_problem(self, small_context):
        """Test solving a small scheduling problem."""
        solver = HybridSolver(timeout_seconds=30)
        result = solver.solve(small_context)

        assert result.success is True
        assert len(result.assignments) > 0

    def test_solve_uses_best_approach(self, medium_context):
        """Test that hybrid solver finds a solution."""
        solver = HybridSolver(
            timeout_seconds=60,
            cpsat_timeout=30,
            pulp_timeout=30,
        )

        result = solver.solve(medium_context)

        assert result.success is True


# ============================================================================
# Solver Factory Tests
# ============================================================================

class TestSolverFactory:
    """Tests for SolverFactory."""

    def test_create_greedy_solver(self):
        """Test creating greedy solver."""
        solver = SolverFactory.create("greedy")
        assert isinstance(solver, GreedySolver)

    def test_create_cpsat_solver(self):
        """Test creating CP-SAT solver."""
        solver = SolverFactory.create("cp_sat")
        assert isinstance(solver, CPSATSolver)

    def test_create_pulp_solver(self):
        """Test creating PuLP solver."""
        solver = SolverFactory.create("pulp")
        assert isinstance(solver, PuLPSolver)

    def test_create_hybrid_solver(self):
        """Test creating hybrid solver."""
        solver = SolverFactory.create("hybrid")
        assert isinstance(solver, HybridSolver)

    def test_create_with_constraint_manager(self):
        """Test creating solver with custom constraint manager."""
        manager = ConstraintManager.create_minimal()
        solver = SolverFactory.create("greedy", constraint_manager=manager)

        assert solver.constraint_manager is manager

    def test_create_with_custom_timeout(self):
        """Test creating solver with custom timeout."""
        solver = SolverFactory.create("cp_sat", timeout_seconds=120)
        assert solver.timeout_seconds == 120

    def test_create_unknown_solver_raises(self):
        """Test that unknown solver name raises ValueError."""
        with pytest.raises(ValueError):
            SolverFactory.create("unknown_solver")

    def test_available_solvers_list(self):
        """Test getting list of available solvers."""
        solvers = SolverFactory.available_solvers()

        assert "greedy" in solvers
        assert "cp_sat" in solvers
        assert "pulp" in solvers
        assert "hybrid" in solvers


# ============================================================================
# Solver Result Tests
# ============================================================================

class TestSolverResult:
    """Tests for SolverResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        result = SolverResult(
            success=True,
            assignments=[(uuid4(), uuid4(), uuid4())],
            status="optimal",
            objective_value=100.0,
            runtime_seconds=5.5,
            solver_status="OPTIMAL",
        )

        assert result.success is True
        assert result.status == "optimal"
        assert len(result.assignments) == 1

    def test_create_failure_result(self):
        """Test creating a failure result."""
        result = SolverResult(
            success=False,
            assignments=[],
            status="infeasible",
            solver_status="INFEASIBLE",
        )

        assert result.success is False
        assert len(result.assignments) == 0

    def test_result_repr(self):
        """Test result string representation."""
        result = SolverResult(
            success=True,
            assignments=[(uuid4(), uuid4(), None)],
            status="feasible",
        )

        repr_str = repr(result)
        assert "success=True" in repr_str
        assert "assignments=1" in repr_str


# ============================================================================
# Performance Tests
# ============================================================================

class TestSolverPerformance:
    """Performance tests for solvers."""

    def test_greedy_is_fast(self, medium_context):
        """Test that greedy solver is fast."""
        solver = GreedySolver()
        result = solver.solve(medium_context)

        # Greedy should complete in under 1 second
        assert result.runtime_seconds < 1.0
        assert result.success is True

    def test_solvers_respect_timeout(self, medium_context):
        """Test that solvers respect timeout setting."""
        solver = CPSATSolver(timeout_seconds=5)
        result = solver.solve(medium_context)

        # Solver should complete within timeout (with some buffer)
        assert result.runtime_seconds < 10.0
