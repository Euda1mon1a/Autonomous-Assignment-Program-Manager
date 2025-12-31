"""Tests for schedule generation optimizer components."""
import pytest
from datetime import date, timedelta

from app.scheduling.optimizer.constraint_pruning import (
    ConstraintPruner,
    prune_infeasible_assignments,
)
from app.scheduling.optimizer.solution_cache import SolutionCache
from app.scheduling.optimizer.parallel_solver import ParallelSolver, SolverResult


def create_test_persons():
    """Create test person data."""
    return [
        {
            "id": "resident_1",
            "name": "Dr. Smith",
            "type": "resident",
            "pgy_level": 1,
            "specialties": ["Family Medicine"],
        },
        {
            "id": "resident_2",
            "name": "Dr. Jones",
            "type": "resident",
            "pgy_level": 2,
            "specialties": ["Family Medicine", "Sports Medicine"],
        },
        {
            "id": "faculty_1",
            "name": "Dr. Brown",
            "type": "faculty",
            "specialties": ["Family Medicine"],
        },
    ]


def create_test_rotations():
    """Create test rotation data."""
    return [
        {
            "id": "clinic",
            "name": "Clinic",
            "allowed_person_types": ["resident", "faculty"],
            "min_pgy_level": 1,
        },
        {
            "id": "procedures",
            "name": "Procedures",
            "allowed_person_types": ["resident"],
            "min_pgy_level": 2,
            "required_specialties": ["Sports Medicine"],
        },
        {
            "id": "admin",
            "name": "Administration",
            "allowed_person_types": ["faculty"],
        },
    ]


def create_test_blocks():
    """Create test block data."""
    today = date.today()
    return [
        {
            "id": f"block_{i}",
            "date": today + timedelta(days=i),
            "is_am": True,
        }
        for i in range(10)
    ]


def test_constraint_pruner():
    """Test constraint pruning reduces search space."""
    pruner = ConstraintPruner()

    persons = create_test_persons()
    rotations = create_test_rotations()
    blocks = create_test_blocks()

    result = pruner.prune_assignments(persons, rotations, blocks)

    # Should have pruned some assignments
    assert result["pruned_count"] > 0
    assert result["total_evaluated"] > len(result["feasible_assignments"])
    assert result["reduction_ratio"] > 0

    # Check pruning reasons
    assert "pgy_level_too_low" in result["pruning_reasons"]
    assert "specialty_mismatch" in result["pruning_reasons"]


def test_constraint_pruner_person_type_restriction():
    """Test pruning based on person type."""
    pruner = ConstraintPruner()

    persons = [
        {"id": "resident_1", "type": "resident", "pgy_level": 1},
        {"id": "faculty_1", "type": "faculty"},
    ]

    rotations = [
        {
            "id": "resident_only",
            "allowed_person_types": ["resident"],
        },
    ]

    blocks = [{"id": "block_1", "date": date.today(), "is_am": True}]

    result = pruner.prune_assignments(persons, rotations, blocks)

    # Faculty should be pruned from resident-only rotation
    assert "person_type_mismatch" in result["pruning_reasons"]


def test_constraint_pruner_pgy_level():
    """Test pruning based on PGY level."""
    pruner = ConstraintPruner()

    persons = [
        {"id": "pgy1", "type": "resident", "pgy_level": 1},
        {"id": "pgy3", "type": "resident", "pgy_level": 3},
    ]

    rotations = [
        {
            "id": "advanced",
            "allowed_person_types": ["resident"],
            "min_pgy_level": 2,
        },
    ]

    blocks = [{"id": "block_1", "date": date.today(), "is_am": True}]

    result = pruner.prune_assignments(persons, rotations, blocks)

    # PGY1 should be pruned
    assert result["pruning_reasons"]["pgy_level_too_low"] == 1


def test_constraint_pruner_estimate_reduction():
    """Test search space reduction estimation."""
    pruner = ConstraintPruner()

    persons = create_test_persons()
    rotations = create_test_rotations()
    blocks = create_test_blocks()

    result = pruner.prune_assignments(persons, rotations, blocks)
    estimation = pruner.estimate_search_space_reduction(result)

    assert estimation["total_combinations"] > 0
    assert estimation["remaining_combinations"] < estimation["total_combinations"]
    assert estimation["estimated_search_space_reduction_factor"] > 1.0


@pytest.mark.asyncio
async def test_solution_cache():
    """Test solution caching."""
    cache = SolutionCache()

    persons = create_test_persons()
    rotations = create_test_rotations()
    blocks = create_test_blocks()
    constraints = {"max_hours_per_week": 80}

    # Generate problem hash
    problem_hash = cache.generate_problem_hash(
        persons, rotations, blocks, constraints
    )

    assert len(problem_hash) > 0

    # Cache a solution
    solution = {"assignments": [{"person_id": "resident_1"}]}
    await cache.set_solution(problem_hash, solution)

    # Retrieve cached solution
    cached = await cache.get_solution(problem_hash)

    assert cached == solution


@pytest.mark.asyncio
async def test_solution_cache_different_problems():
    """Test different problems generate different hashes."""
    cache = SolutionCache()

    persons = create_test_persons()
    rotations = create_test_rotations()
    blocks = create_test_blocks()

    constraints1 = {"max_hours_per_week": 80}
    constraints2 = {"max_hours_per_week": 70}

    hash1 = cache.generate_problem_hash(persons, rotations, blocks, constraints1)
    hash2 = cache.generate_problem_hash(persons, rotations, blocks, constraints2)

    # Different constraints should generate different hashes
    assert hash1 != hash2


@pytest.mark.asyncio
async def test_solution_cache_partial():
    """Test partial solution caching."""
    cache = SolutionCache()

    problem_hash = "test_hash_123"
    start_date = date.today()
    end_date = start_date + timedelta(days=7)
    date_range = (start_date, end_date)

    partial_solution = {"assignments": [{"date": start_date.isoformat()}]}

    # Cache partial solution
    await cache.set_partial_solution(problem_hash, date_range, partial_solution)

    # Retrieve partial solution
    cached = await cache.get_partial_solution(problem_hash, date_range)

    assert cached == partial_solution


@pytest.mark.asyncio
async def test_parallel_solver():
    """Test parallel solver execution."""
    solver = ParallelSolver(num_solvers=3, timeout_seconds=5)

    async def mock_solver(problem_data: dict, solver_id: int) -> dict:
        """Mock solver that returns different objective values."""
        import asyncio
        await asyncio.sleep(0.1)

        return {
            "objective_value": 100 + solver_id,
            "iterations": 50,
            "assignments": [],
        }

    problem_data = {"test": "data"}

    result = await solver.solve(problem_data, mock_solver)

    assert result.success
    assert result.objective_value == 100  # Best (lowest) should be from solver 0
    assert result.solver_id == 0


@pytest.mark.asyncio
async def test_parallel_solver_timeout():
    """Test parallel solver timeout handling."""
    solver = ParallelSolver(num_solvers=2, timeout_seconds=1)

    async def slow_solver(problem_data: dict, solver_id: int) -> dict:
        """Solver that times out."""
        import asyncio
        await asyncio.sleep(10)  # Will timeout
        return {"objective_value": 100}

    problem_data = {"test": "data"}

    result = await solver.solve(problem_data, slow_solver)

    assert not result.success
    assert result.error == "All solvers failed"


@pytest.mark.asyncio
async def test_parallel_solver_with_strategies():
    """Test parallel solver with different strategies."""
    solver = ParallelSolver(num_solvers=3)

    async def mock_solver(problem_data: dict, solver_id: int) -> dict:
        """Mock solver that uses strategy from problem data."""
        import asyncio
        await asyncio.sleep(0.1)

        strategy = problem_data.get("heuristic", "default")
        objective = 100 if strategy == "greedy" else 150

        return {
            "objective_value": objective,
            "iterations": 50,
            "strategy": strategy,
        }

    problem_data = {"test": "data"}

    strategies = [
        {"heuristic": "greedy"},
        {"heuristic": "random"},
        {"heuristic": "balanced"},
    ]

    result = await solver.solve(problem_data, mock_solver, strategies)

    assert result.success
    assert result.objective_value == 100  # Greedy should win
    assert result.solution["strategy"] == "greedy"


def test_prune_infeasible_assignments():
    """Test utility function for pruning."""
    persons = create_test_persons()
    rotations = create_test_rotations()
    blocks = create_test_blocks()

    result = prune_infeasible_assignments(persons, rotations, blocks)

    assert "feasible_assignments" in result
    assert "pruned_count" in result
    assert "reduction_ratio" in result
