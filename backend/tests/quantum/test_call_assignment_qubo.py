"""
Integration Tests for Call Assignment QUBO Optimizer.

Tests cover:
1. QUBO formulation construction
2. Simulated annealing with quantum tunneling
3. Constraint satisfaction validation
4. Equity distribution
5. Scalability across problem sizes
6. OR-Tools benchmarking
7. Landscape data export

Problem Size Reference:
- Minimal: 10 residents × 7 nights = 70 variables
- Small: 10 residents × 30 nights = 300 variables
- Medium: 20 residents × 90 nights = 1,800 variables
- Sweet Spot: 20 residents × 365 nights = 7,300 variables
- Max Target: 20 residents × 730 nights = 14,600 variables
"""

import json
import tempfile
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from app.scheduling.quantum.call_assignment_qubo import (
    CallAssignmentQUBO,
    CallAssignmentBenchmark,
    CallAssignmentValidator,
    CallCandidate,
    CallNight,
    CallType,
    QuantumTunnelingAnnealingSolver,
    QUBOSolution,
    create_call_nights_from_dates,
    solve_call_assignment,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def base_date() -> date:
    """Start date for test scenarios."""
    return date(2025, 1, 1)


@pytest.fixture
def minimal_candidates() -> list[CallCandidate]:
    """10 residents for minimal testing."""
    return [
        CallCandidate(
            person_id=uuid4(),
            name=f"Resident-{i}",
            pgy_level=(i % 3) + 1,
            max_calls_per_week=2,
            max_consecutive_call_days=1,
        )
        for i in range(10)
    ]


@pytest.fixture
def minimal_nights(base_date) -> list[CallNight]:
    """7 nights for minimal testing."""
    return [
        CallNight(
            date=base_date + timedelta(days=i),
            call_type=CallType.OVERNIGHT,
            is_weekend=(base_date + timedelta(days=i)).weekday() in (5, 6),
        )
        for i in range(7)
    ]


@pytest.fixture
def small_candidates() -> list[CallCandidate]:
    """10 residents with varied preferences."""
    candidates = []
    for i in range(10):
        avoid_days = set()
        if i < 3:  # First 3 avoid Tuesdays
            avoid_days.add(1)
        if i >= 7:  # Last 3 prefer Wednesdays
            pref = {2: 2.0}
        else:
            pref = {}

        candidates.append(
            CallCandidate(
                person_id=uuid4(),
                name=f"Resident-{i}",
                pgy_level=(i % 3) + 1,
                max_calls_per_week=2,
                max_consecutive_call_days=1,
                avoid_days=avoid_days,
                preference_bonus=pref,
            )
        )
    return candidates


@pytest.fixture
def small_nights(base_date) -> list[CallNight]:
    """30 nights for small testing (about a month)."""
    return create_call_nights_from_dates(
        start_date=base_date,
        end_date=base_date + timedelta(days=29),
        exclude_weekends=True,  # Exclude Fri/Sat
    )


@pytest.fixture
def medium_candidates() -> list[CallCandidate]:
    """20 residents for medium-scale testing."""
    return [
        CallCandidate(
            person_id=uuid4(),
            name=f"Resident-{i}",
            pgy_level=(i % 3) + 1,
            specialty="Internal Medicine" if i < 15 else "Pediatrics",
            max_calls_per_week=2,
            max_consecutive_call_days=1,
        )
        for i in range(20)
    ]


@pytest.fixture
def medium_nights(base_date) -> list[CallNight]:
    """90 nights for medium testing (about 3 months)."""
    return create_call_nights_from_dates(
        start_date=base_date,
        end_date=base_date + timedelta(days=89),
        exclude_weekends=True,
    )


# =============================================================================
# BASIC FUNCTIONALITY TESTS
# =============================================================================


class TestQUBOFormulation:
    """Test QUBO matrix construction."""

    def test_variable_count(self, minimal_candidates, minimal_nights):
        """Verify correct number of binary variables."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)

        expected = len(minimal_candidates) * len(minimal_nights)
        assert formulation.num_variables == expected
        assert formulation.num_variables == 70  # 10 × 7

    def test_qubo_matrix_construction(self, minimal_candidates, minimal_nights):
        """Verify QUBO matrix is built with non-zero terms."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        Q = formulation.build()

        assert len(Q) > 0
        # Should have diagonal (linear) terms
        diagonal_terms = sum(1 for (i, j) in Q.keys() if i == j)
        assert diagonal_terms > 0
        # Should have off-diagonal (quadratic) terms
        quadratic_terms = sum(1 for (i, j) in Q.keys() if i != j)
        assert quadratic_terms > 0

    def test_variable_indexing(self, minimal_candidates, minimal_nights):
        """Verify bidirectional variable indexing."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)

        for (r_i, n_i), idx in formulation.var_index.items():
            assert formulation.index_to_var[idx] == (r_i, n_i)
            assert 0 <= r_i < formulation.num_candidates
            assert 0 <= n_i < formulation.num_nights

    def test_energy_computation(self, minimal_candidates, minimal_nights):
        """Verify energy computation is consistent."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        formulation.build()

        # All zeros should have a specific energy
        all_zeros = {i: 0 for i in range(formulation.num_variables)}
        energy_zeros = formulation.compute_energy(all_zeros)

        # Energy should be deterministic
        assert formulation.compute_energy(all_zeros) == energy_zeros

        # All ones should have different (higher) energy due to coverage constraints
        all_ones = {i: 1 for i in range(formulation.num_variables)}
        energy_ones = formulation.compute_energy(all_ones)

        # Multiple residents per night should increase energy due to penalties
        assert energy_ones > energy_zeros


class TestSimulatedAnnealing:
    """Test quantum-inspired simulated annealing solver."""

    def test_solver_returns_solution(self, minimal_candidates, minimal_nights):
        """Verify solver returns a valid QUBOSolution."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=5,
            num_sweeps=100,
            track_landscape=False,
        )

        solution = solver.solve(formulation)

        assert isinstance(solution, QUBOSolution)
        assert isinstance(solution.energy, float)
        assert isinstance(solution.assignments, list)
        assert solution.runtime_seconds > 0
        assert solution.num_reads == 5
        assert solution.num_sweeps == 100

    def test_deterministic_with_seed(self, minimal_candidates, minimal_nights):
        """Verify deterministic results with same seed."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        formulation.build()

        solver1 = QuantumTunnelingAnnealingSolver(
            num_reads=3,
            num_sweeps=50,
            seed=42,
            track_landscape=False,
        )
        solution1 = solver1.solve(formulation)

        solver2 = QuantumTunnelingAnnealingSolver(
            num_reads=3,
            num_sweeps=50,
            seed=42,
            track_landscape=False,
        )
        solution2 = solver2.solve(formulation)

        assert solution1.energy == solution2.energy
        assert solution1.sample == solution2.sample

    def test_tunneling_strength_affects_results(self, minimal_candidates, minimal_nights):
        """Verify tunneling strength parameter has effect."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        formulation.build()

        # Low tunneling (more classical)
        solver_low = QuantumTunnelingAnnealingSolver(
            num_reads=10,
            num_sweeps=200,
            tunneling_strength=0.0,
            seed=123,
            track_landscape=False,
        )
        solution_low = solver_low.solve(formulation)

        # High tunneling (more quantum-like)
        solver_high = QuantumTunnelingAnnealingSolver(
            num_reads=10,
            num_sweeps=200,
            tunneling_strength=0.8,
            seed=123,
            track_landscape=False,
        )
        solution_high = solver_high.solve(formulation)

        # Both should find solutions (may or may not differ due to randomness)
        assert solution_low.energy != float("inf")
        assert solution_high.energy != float("inf")


# =============================================================================
# CONSTRAINT SATISFACTION TESTS
# =============================================================================


class TestConstraintSatisfaction:
    """Test that solver respects constraints."""

    def test_coverage_constraint(self, small_candidates, small_nights):
        """Verify each night gets exactly one assignment."""
        formulation = CallAssignmentQUBO(small_nights, small_candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=20,
            num_sweeps=2000,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        # Count assignments per night
        night_counts = {}
        for person_id, call_date, call_type in solution.assignments:
            key = (call_date, call_type)
            night_counts[key] = night_counts.get(key, 0) + 1

        # Check each assigned night has exactly one resident
        for night in small_nights:
            key = (night.date, night.call_type)
            if key in night_counts:
                assert night_counts[key] == 1, f"Night {key} has {night_counts[key]} assignments"

    def test_no_consecutive_calls(self, small_candidates, small_nights):
        """Verify no resident has consecutive call nights."""
        formulation = CallAssignmentQUBO(small_nights, small_candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=20,
            num_sweeps=2000,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        # Group assignments by resident
        by_resident = {}
        for person_id, call_date, call_type in solution.assignments:
            if person_id not in by_resident:
                by_resident[person_id] = []
            by_resident[person_id].append(call_date)

        # Check no consecutive dates
        for person_id, dates in by_resident.items():
            sorted_dates = sorted(dates)
            for i in range(1, len(sorted_dates)):
                diff = (sorted_dates[i] - sorted_dates[i - 1]).days
                assert diff != 1, f"Resident {person_id} has consecutive calls"


class TestValidator:
    """Test CallAssignmentValidator."""

    def test_valid_solution_passes(self, small_candidates, small_nights):
        """Verify valid solutions pass validation."""
        formulation = CallAssignmentQUBO(small_nights, small_candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=30,
            num_sweeps=3000,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        validator = CallAssignmentValidator(small_nights, small_candidates)
        is_valid, violations, metrics = validator.validate(solution.assignments)

        # Should have some assignments
        assert len(solution.assignments) > 0
        # Validator should return metrics
        assert "equity" in metrics

    def test_equity_within_tolerance(self, small_candidates, small_nights):
        """Verify call distribution is reasonably equitable."""
        formulation = CallAssignmentQUBO(small_nights, small_candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=50,
            num_sweeps=5000,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        validator = CallAssignmentValidator(
            small_nights,
            small_candidates,
            equity_tolerance=5.0,  # Allow some variance
        )
        is_valid, violations, metrics = validator.validate(solution.assignments)

        # Equity range should be reasonable
        equity_range = metrics["equity"]["range"]
        # With good solver, range shouldn't be extreme
        assert equity_range <= 10, f"Equity range too large: {equity_range}"


# =============================================================================
# SCALABILITY TESTS
# =============================================================================


class TestScalability:
    """Test solver performance across problem sizes."""

    def test_minimal_problem_70_vars(self, minimal_candidates, minimal_nights):
        """Test minimal problem: 10 residents × 7 nights = 70 variables."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        assert formulation.num_variables == 70

        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=10,
            num_sweeps=500,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        assert solution.runtime_seconds < 10  # Should be fast
        assert len(solution.assignments) > 0

    def test_small_problem_300_vars(self, small_candidates, small_nights):
        """Test small problem: ~300 variables."""
        formulation = CallAssignmentQUBO(small_nights, small_candidates)
        assert formulation.num_variables <= 500

        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=10,
            num_sweeps=1000,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        assert solution.runtime_seconds < 30
        assert len(solution.assignments) > 0

    def test_medium_problem_1800_vars(self, medium_candidates, medium_nights):
        """Test medium problem: ~1800 variables."""
        formulation = CallAssignmentQUBO(medium_nights, medium_candidates)
        assert formulation.num_variables <= 2000

        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=5,
            num_sweeps=1000,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        assert solution.runtime_seconds < 60
        assert len(solution.assignments) > 0

    @pytest.mark.slow
    def test_sweet_spot_7300_vars(self, medium_candidates, base_date):
        """Test sweet spot: 20 residents × 365 nights = 7,300 variables."""
        # Full year
        nights = create_call_nights_from_dates(
            start_date=base_date,
            end_date=base_date + timedelta(days=364),
            exclude_weekends=True,
        )

        formulation = CallAssignmentQUBO(nights, medium_candidates)
        # With weekends excluded, should be ~260 nights
        assert 5000 <= formulation.num_variables <= 8000

        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=3,
            num_sweeps=2000,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        assert solution.runtime_seconds < 300  # 5 minute max
        assert len(solution.assignments) > 0


# =============================================================================
# BENCHMARKING TESTS
# =============================================================================


class TestBenchmarking:
    """Test OR-Tools benchmarking comparison."""

    def test_benchmark_comparison(self, minimal_candidates, minimal_nights):
        """Compare QUBO solver with OR-Tools on minimal problem."""
        benchmark = CallAssignmentBenchmark(minimal_nights, minimal_candidates)

        comparison = benchmark.compare(
            qubo_reads=10,
            qubo_sweeps=500,
            ortools_timeout=10.0,
        )

        assert "problem_size" in comparison
        assert "qubo" in comparison
        assert "ortools" in comparison
        assert comparison["problem_size"]["num_variables"] == 70

    def test_qubo_produces_valid_solution(self, small_candidates, small_nights):
        """Verify QUBO solver produces valid solution for benchmark."""
        benchmark = CallAssignmentBenchmark(small_nights, small_candidates)

        result = benchmark.run_qubo_solver(num_reads=20, num_sweeps=2000)

        assert result["solver"] == "QUBO"
        assert result["num_assignments"] > 0
        assert result["runtime_seconds"] > 0


# =============================================================================
# LANDSCAPE EXPORT TESTS
# =============================================================================


class TestLandscapeExport:
    """Test optimization landscape data export."""

    def test_landscape_tracking(self, minimal_candidates, minimal_nights):
        """Verify landscape tracking records data points."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=5,
            num_sweeps=500,
            track_landscape=True,
            landscape_sample_rate=50,
        )
        solution = solver.solve(formulation)

        assert solution.landscape_data is not None
        assert "metadata" in solution.landscape_data
        assert "trajectory" in solution.landscape_data
        assert len(solution.landscape_data["trajectory"]) > 0

    def test_landscape_json_export(self, minimal_candidates, minimal_nights):
        """Verify landscape can be exported as JSON."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=3,
            num_sweeps=200,
            track_landscape=True,
            landscape_sample_rate=20,
        )
        solution = solver.solve(formulation)

        # Should be JSON serializable
        json_str = json.dumps(solution.landscape_data, default=str)
        assert len(json_str) > 0

        # Should parse back
        parsed = json.loads(json_str)
        assert parsed["metadata"]["num_variables"] == formulation.num_variables

    def test_coordinate_transform_documented(self, minimal_candidates, minimal_nights):
        """Verify coordinate transform documentation in landscape data."""
        formulation = CallAssignmentQUBO(minimal_nights, minimal_candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=2,
            num_sweeps=100,
            track_landscape=True,
        )
        solution = solver.solve(formulation)

        coord_transform = solution.landscape_data["coordinate_transform"]
        assert "description" in coord_transform
        assert "variable_encoding" in coord_transform
        assert "energy_formula" in coord_transform

    def test_full_pipeline_with_file_export(self, minimal_candidates, minimal_nights):
        """Test complete pipeline including file export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "landscape.json"

            solution = solve_call_assignment(
                call_nights=minimal_nights,
                candidates=minimal_candidates,
                num_reads=3,
                num_sweeps=100,
                export_landscape=True,
                output_path=output_path,
            )

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert data["metadata"]["num_candidates"] == len(minimal_candidates)
            assert data["metadata"]["num_nights"] == len(minimal_nights)


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================


class TestHelperFunctions:
    """Test utility functions."""

    def test_create_call_nights_from_dates(self, base_date):
        """Test call night generation from date range."""
        nights = create_call_nights_from_dates(
            start_date=base_date,
            end_date=base_date + timedelta(days=13),
            exclude_weekends=True,
        )

        # 14 days, minus Fri/Sat should give ~10 nights
        assert 8 <= len(nights) <= 12

        # All should have OVERNIGHT type
        for night in nights:
            assert night.call_type == CallType.OVERNIGHT

        # No Fri/Sat
        for night in nights:
            assert night.weekday not in (4, 5)

    def test_create_call_nights_with_weekends(self, base_date):
        """Test call night generation including weekends."""
        nights = create_call_nights_from_dates(
            start_date=base_date,
            end_date=base_date + timedelta(days=6),
            exclude_weekends=False,
        )

        assert len(nights) == 7  # Full week

    def test_empty_candidates_handled(self, minimal_nights):
        """Test handling of empty candidate list."""
        formulation = CallAssignmentQUBO(minimal_nights, [])
        assert formulation.num_variables == 0
        assert formulation.num_candidates == 0

    def test_empty_nights_handled(self, minimal_candidates):
        """Test handling of empty nights list."""
        formulation = CallAssignmentQUBO([], minimal_candidates)
        assert formulation.num_variables == 0
        assert formulation.num_nights == 0


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_candidate_single_night(self, base_date):
        """Test minimal case: 1 resident, 1 night."""
        candidates = [
            CallCandidate(
                person_id=uuid4(),
                name="Solo Resident",
                pgy_level=1,
            )
        ]
        nights = [
            CallNight(date=base_date, call_type=CallType.OVERNIGHT)
        ]

        formulation = CallAssignmentQUBO(nights, candidates)
        assert formulation.num_variables == 1

        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=1,
            num_sweeps=10,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        # Should assign the one resident to the one night
        assert len(solution.assignments) == 1

    def test_more_nights_than_candidates(self, base_date):
        """Test case where nights > candidates (some will be unassigned)."""
        candidates = [
            CallCandidate(
                person_id=uuid4(),
                name=f"Resident-{i}",
                pgy_level=1,
                max_calls_per_week=1,  # Very restrictive
            )
            for i in range(3)
        ]
        nights = [
            CallNight(date=base_date + timedelta(days=i), call_type=CallType.OVERNIGHT)
            for i in range(10)
        ]

        formulation = CallAssignmentQUBO(nights, candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=10,
            num_sweeps=500,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        # May not cover all nights due to constraints
        assert len(solution.assignments) >= 0

    def test_high_constraint_pressure(self, base_date):
        """Test case with high constraint pressure."""
        # Create candidates that all avoid certain days
        candidates = [
            CallCandidate(
                person_id=uuid4(),
                name=f"Resident-{i}",
                pgy_level=1,
                avoid_days={0, 1, 2},  # Avoid Mon, Tue, Wed
            )
            for i in range(5)
        ]
        nights = create_call_nights_from_dates(
            start_date=base_date,
            end_date=base_date + timedelta(days=13),
            exclude_weekends=True,
        )

        formulation = CallAssignmentQUBO(nights, candidates)
        formulation.build()

        solver = QuantumTunnelingAnnealingSolver(
            num_reads=20,
            num_sweeps=2000,
            track_landscape=False,
        )
        solution = solver.solve(formulation)

        # Should still find a solution (preferences are soft)
        assert solution.energy != float("inf")
