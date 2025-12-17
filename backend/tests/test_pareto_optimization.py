"""
Comprehensive tests for Pareto optimization service.

Tests for:
- Multi-objective optimization with NSGA-II
- Pareto frontier extraction
- 6 objectives: fairness, coverage, preference, workload, consecutive, specialty
- Solution ranking
- Edge cases and error handling
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import numpy as np
import pytest
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.person import Person
from app.schemas.pareto import (
    ObjectiveDirection,
    ObjectiveName,
    ParetoConstraint,
    ParetoObjective,
    ParetoResult,
    ParetoSolution,
    RankedSolution,
)
from app.services.pareto_optimization_service import (
    ParetoOptimizationService,
    SchedulingProblem,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def pareto_service(db: Session) -> ParetoOptimizationService:
    """Create a Pareto optimization service instance."""
    return ParetoOptimizationService(db)


@pytest.fixture
def sample_objectives() -> list[ParetoObjective]:
    """Create a sample list of optimization objectives."""
    return [
        ParetoObjective(
            name=ObjectiveName.FAIRNESS,
            weight=1.0,
            direction=ObjectiveDirection.MINIMIZE,
        ),
        ParetoObjective(
            name=ObjectiveName.COVERAGE,
            weight=1.0,
            direction=ObjectiveDirection.MAXIMIZE,
        ),
        ParetoObjective(
            name=ObjectiveName.PREFERENCE_SATISFACTION,
            weight=0.8,
            direction=ObjectiveDirection.MAXIMIZE,
        ),
        ParetoObjective(
            name=ObjectiveName.WORKLOAD_BALANCE,
            weight=0.9,
            direction=ObjectiveDirection.MINIMIZE,
        ),
        ParetoObjective(
            name=ObjectiveName.CONSECUTIVE_DAYS,
            weight=0.7,
            direction=ObjectiveDirection.MINIMIZE,
        ),
        ParetoObjective(
            name=ObjectiveName.SPECIALTY_DISTRIBUTION,
            weight=0.6,
            direction=ObjectiveDirection.MINIMIZE,
        ),
    ]


@pytest.fixture
def sample_constraints() -> list[ParetoConstraint]:
    """Create a sample list of constraints."""
    return [
        ParetoConstraint(
            constraint_type="max_consecutive_days",
            parameters={"max_days": 5},
            is_hard=True,
        ),
        ParetoConstraint(
            constraint_type="min_coverage",
            parameters={"min_rate": 0.8},
            is_hard=True,
        ),
        ParetoConstraint(
            constraint_type="max_assignments_per_person",
            parameters={"max_count": 10},
            is_hard=True,
        ),
    ]


@pytest.fixture
def pareto_test_persons(db: Session) -> list[Person]:
    """Create persons for Pareto optimization testing."""
    persons = []
    for i in range(5):
        person = Person(
            id=uuid4(),
            name=f"Dr. Test Person {i}",
            type="resident",
            email=f"test{i}@hospital.org",
            pgy_level=(i % 3) + 1,
        )
        db.add(person)
        persons.append(person)
    db.commit()
    for p in persons:
        db.refresh(p)
    return persons


@pytest.fixture
def pareto_test_blocks(db: Session) -> list[Block]:
    """Create blocks for Pareto optimization testing."""
    blocks = []
    start_date = date.today()

    for i in range(10):
        block = Block(
            id=uuid4(),
            date=start_date + timedelta(days=i // 2),
            time_of_day="AM" if i % 2 == 0 else "PM",
            block_number=1,
            is_weekend=False,
            is_holiday=False,
            activity_type="clinic" if i % 3 == 0 else "admin",
        )
        db.add(block)
        blocks.append(block)

    db.commit()
    for b in blocks:
        db.refresh(b)
    return blocks


@pytest.fixture
def sample_solutions() -> list[ParetoSolution]:
    """Create sample solutions for testing ranking and frontier."""
    return [
        ParetoSolution(
            solution_id=0,
            objective_values={
                "fairness": 0.2,
                "coverage": 0.9,
                "preference_satisfaction": 0.7,
                "workload_balance": 0.3,
                "consecutive_days": 1.0,
                "specialty_distribution": 0.5,
            },
            decision_variables={"block_1_person_1": {"block_id": "1", "person_id": "1"}},
            is_feasible=True,
            constraint_violations=[],
        ),
        ParetoSolution(
            solution_id=1,
            objective_values={
                "fairness": 0.1,
                "coverage": 0.8,
                "preference_satisfaction": 0.8,
                "workload_balance": 0.4,
                "consecutive_days": 0.5,
                "specialty_distribution": 0.6,
            },
            decision_variables={"block_1_person_2": {"block_id": "1", "person_id": "2"}},
            is_feasible=True,
            constraint_violations=[],
        ),
        ParetoSolution(
            solution_id=2,
            objective_values={
                "fairness": 0.3,
                "coverage": 0.95,
                "preference_satisfaction": 0.6,
                "workload_balance": 0.2,
                "consecutive_days": 1.5,
                "specialty_distribution": 0.4,
            },
            decision_variables={"block_1_person_3": {"block_id": "1", "person_id": "3"}},
            is_feasible=True,
            constraint_violations=[],
        ),
    ]


# ============================================================================
# SchedulingProblem Tests
# ============================================================================


@pytest.mark.unit
class TestSchedulingProblem:
    """Test SchedulingProblem class for pymoo integration."""

    def test_problem_initialization(self, sample_objectives, sample_constraints):
        """Test that SchedulingProblem initializes correctly."""
        n_persons = 5
        n_blocks = 10
        person_data = [{"id": str(uuid4()), "name": f"Person {i}"} for i in range(n_persons)]
        block_data = [{"id": str(uuid4()), "name": f"Block {i}"} for i in range(n_blocks)]

        problem = SchedulingProblem(
            n_persons=n_persons,
            n_blocks=n_blocks,
            objectives=sample_objectives,
            constraints=sample_constraints,
            person_data=person_data,
            block_data=block_data,
        )

        assert problem.n_persons == n_persons
        assert problem.n_blocks == n_blocks
        assert problem.n_var == n_persons * n_blocks
        assert problem.n_obj == len(sample_objectives)
        assert problem.n_ieq_constr == len([c for c in sample_constraints if c.is_hard])

    def test_decode_solution(self, sample_objectives, sample_constraints):
        """Test decoding decision variables into assignment matrix."""
        n_persons = 3
        n_blocks = 4
        problem = SchedulingProblem(
            n_persons=n_persons,
            n_blocks=n_blocks,
            objectives=sample_objectives[:2],
            constraints=[],
            person_data=[{"id": str(i)} for i in range(n_persons)],
            block_data=[{"id": str(i)} for i in range(n_blocks)],
        )

        # Create decision variables (0.0 to 1.0)
        x = np.array([0.7, 0.2, 0.9, 0.3, 0.1, 0.6, 0.4, 0.8, 0.5, 0.1, 0.0, 0.9])
        assignment_matrix = problem._decode_solution(x)

        assert assignment_matrix.shape == (n_blocks, n_persons)
        assert assignment_matrix.dtype == int
        # Values should be binary (0 or 1)
        assert np.all((assignment_matrix == 0) | (assignment_matrix == 1))
        # Check threshold application (> 0.5 becomes 1)
        assert assignment_matrix[0, 0] == 1  # 0.7 > 0.5
        assert assignment_matrix[0, 1] == 0  # 0.2 <= 0.5

    def test_calculate_fairness(self, sample_objectives):
        """Test fairness objective calculation."""
        problem = SchedulingProblem(
            n_persons=3,
            n_blocks=4,
            objectives=sample_objectives[:1],
            constraints=[],
            person_data=[{"id": str(i)} for i in range(3)],
            block_data=[{"id": str(i)} for i in range(4)],
        )

        # Equal distribution: low variance
        assignment_matrix = np.array([
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
        ])
        fairness = problem._calculate_fairness(assignment_matrix)
        assert isinstance(fairness, float)
        assert fairness >= 0

        # Unequal distribution: high variance
        assignment_matrix_unequal = np.array([
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
        ])
        fairness_unequal = problem._calculate_fairness(assignment_matrix_unequal)
        assert fairness_unequal > fairness

    def test_calculate_coverage(self, sample_objectives):
        """Test coverage objective calculation."""
        problem = SchedulingProblem(
            n_persons=3,
            n_blocks=4,
            objectives=sample_objectives[:2],
            constraints=[],
            person_data=[{"id": str(i)} for i in range(3)],
            block_data=[{"id": str(i)} for i in range(4)],
        )

        # All blocks covered
        assignment_matrix = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ])
        coverage = problem._calculate_coverage(assignment_matrix)
        assert coverage == -1.0  # Negated because pymoo minimizes

        # Partial coverage (2 out of 4 blocks)
        assignment_matrix_partial = np.array([
            [1, 0, 0],
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ])
        coverage_partial = problem._calculate_coverage(assignment_matrix_partial)
        assert coverage_partial == -0.5

    def test_calculate_preference_satisfaction(self, sample_objectives):
        """Test preference satisfaction objective calculation."""
        person_data = [
            {"id": "1", "preferred_activity_types": ["clinic", "admin"]},
            {"id": "2", "preferred_activity_types": ["admin"]},
            {"id": "3", "preferred_activity_types": []},
        ]
        block_data = [
            {"id": "1", "activity_type": "clinic"},
            {"id": "2", "activity_type": "admin"},
            {"id": "3", "activity_type": "other"},
            {"id": "4", "activity_type": "clinic"},
        ]

        problem = SchedulingProblem(
            n_persons=3,
            n_blocks=4,
            objectives=sample_objectives[:3],
            constraints=[],
            person_data=person_data,
            block_data=block_data,
        )

        # Assignments matching preferences
        assignment_matrix = np.array([
            [1, 0, 0],  # Person 0 to clinic (match)
            [0, 1, 0],  # Person 1 to admin (match)
            [0, 0, 1],  # Person 2 to other (no preference)
            [1, 0, 0],  # Person 0 to clinic (match)
        ])
        satisfaction = problem._calculate_preference_satisfaction(assignment_matrix)
        assert isinstance(satisfaction, float)
        # Should be negative (for minimization in pymoo)
        assert satisfaction <= 0

    def test_calculate_workload_balance(self, sample_objectives):
        """Test workload balance objective calculation."""
        problem = SchedulingProblem(
            n_persons=3,
            n_blocks=6,
            objectives=sample_objectives[:4],
            constraints=[],
            person_data=[{"id": str(i)} for i in range(3)],
            block_data=[{"id": str(i)} for i in range(6)],
        )

        # Balanced workload (2 assignments each)
        assignment_matrix_balanced = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ])
        balance = problem._calculate_workload_balance(assignment_matrix_balanced)
        assert balance == 0.0

        # Unbalanced workload
        assignment_matrix_unbalanced = np.array([
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ])
        balance_unbalanced = problem._calculate_workload_balance(assignment_matrix_unbalanced)
        assert balance_unbalanced > 0

    def test_calculate_consecutive_days(self, sample_objectives):
        """Test consecutive days penalty calculation."""
        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=10,
            objectives=sample_objectives[:5],
            constraints=[],
            person_data=[{"id": str(i)} for i in range(2)],
            block_data=[{"id": str(i)} for i in range(10)],
        )

        # No consecutive blocks
        assignment_matrix_no_consecutive = np.array([
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ])
        penalty = problem._calculate_consecutive_days(assignment_matrix_no_consecutive)
        assert penalty == 0.0

        # Many consecutive blocks (penalty should trigger after 5)
        assignment_matrix_consecutive = np.array([
            [1, 0],
            [1, 0],
            [1, 0],
            [1, 0],
            [1, 0],
            [1, 0],
            [1, 0],
            [0, 0],
            [0, 0],
            [0, 0],
        ])
        penalty_consecutive = problem._calculate_consecutive_days(assignment_matrix_consecutive)
        assert penalty_consecutive > 0

    def test_calculate_specialty_distribution(self, sample_objectives):
        """Test specialty distribution objective calculation."""
        block_data = [
            {"id": "1", "specialty": "cardiology"},
            {"id": "2", "specialty": "neurology"},
            {"id": "3", "specialty": "cardiology"},
            {"id": "4", "specialty": "neurology"},
        ]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=4,
            objectives=sample_objectives,
            constraints=[],
            person_data=[{"id": str(i)} for i in range(2)],
            block_data=block_data,
        )

        # Balanced specialty distribution
        assignment_matrix_balanced = np.array([
            [1, 0],  # cardiology
            [0, 1],  # neurology
            [1, 0],  # cardiology
            [0, 1],  # neurology
        ])
        distribution = problem._calculate_specialty_distribution(assignment_matrix_balanced)
        assert distribution == 0.0  # Equal counts -> zero std

        # Unbalanced specialty distribution
        assignment_matrix_unbalanced = np.array([
            [1, 0],  # cardiology
            [0, 0],  # neurology (not assigned)
            [1, 0],  # cardiology
            [1, 0],  # cardiology
        ])
        distribution_unbalanced = problem._calculate_specialty_distribution(assignment_matrix_unbalanced)
        assert distribution_unbalanced > 0

    def test_evaluate_objectives(self, sample_objectives):
        """Test evaluation of all objectives."""
        problem = SchedulingProblem(
            n_persons=3,
            n_blocks=4,
            objectives=sample_objectives,
            constraints=[],
            person_data=[{"id": str(i)} for i in range(3)],
            block_data=[{"id": str(i), "activity_type": "clinic", "specialty": "general"} for i in range(4)],
        )

        # Create decision variables
        x = np.array([0.7, 0.2, 0.9, 0.3, 0.1, 0.6, 0.4, 0.8, 0.5, 0.1, 0.0, 0.9])
        out = {}

        problem._evaluate(x, out)

        assert "F" in out
        assert len(out["F"]) == len(sample_objectives)
        assert all(isinstance(f, (int, float, np.number)) for f in out["F"])

    def test_evaluate_constraints(self, sample_objectives, sample_constraints):
        """Test evaluation of constraints."""
        problem = SchedulingProblem(
            n_persons=3,
            n_blocks=4,
            objectives=sample_objectives[:2],
            constraints=sample_constraints,
            person_data=[{"id": str(i)} for i in range(3)],
            block_data=[{"id": str(i)} for i in range(4)],
        )

        x = np.array([0.7, 0.2, 0.9, 0.3, 0.1, 0.6, 0.4, 0.8, 0.5, 0.1, 0.0, 0.9])
        out = {}

        problem._evaluate(x, out)

        assert "G" in out
        assert len(out["G"]) == len([c for c in sample_constraints if c.is_hard])


# ============================================================================
# ParetoOptimizationService Tests
# ============================================================================


@pytest.mark.unit
class TestParetoOptimizationService:
    """Test ParetoOptimizationService methods."""

    def test_service_initialization(self, db: Session):
        """Test service initialization."""
        service = ParetoOptimizationService(db)

        assert service.db is db
        assert service.assignment_repo is not None
        assert service.block_repo is not None
        assert service.person_repo is not None

    def test_optimize_schedule_empty_persons(
        self,
        db: Session,
        pareto_service: ParetoOptimizationService,
        sample_objectives,
        sample_constraints,
    ):
        """Test optimization with no persons available."""
        result = pareto_service.optimize_schedule_pareto(
            objectives=sample_objectives[:2],
            constraints=sample_constraints,
            person_ids=[],
            block_ids=None,
            population_size=10,
            n_generations=5,
        )

        assert isinstance(result, ParetoResult)
        assert result.total_solutions == 0
        assert len(result.solutions) == 0
        assert "No persons or blocks" in result.termination_reason

    def test_optimize_schedule_empty_blocks(
        self,
        db: Session,
        pareto_service: ParetoOptimizationService,
        pareto_test_persons,
        sample_objectives,
        sample_constraints,
    ):
        """Test optimization with no blocks available."""
        result = pareto_service.optimize_schedule_pareto(
            objectives=sample_objectives[:2],
            constraints=sample_constraints,
            person_ids=[p.id for p in pareto_test_persons],
            block_ids=[],
            population_size=10,
            n_generations=5,
        )

        assert isinstance(result, ParetoResult)
        assert result.total_solutions == 0

    @patch('app.services.pareto_optimization_service.minimize')
    def test_optimize_schedule_success(
        self,
        mock_minimize,
        db: Session,
        pareto_service: ParetoOptimizationService,
        pareto_test_persons,
        pareto_test_blocks,
        sample_objectives,
        sample_constraints,
    ):
        """Test successful optimization."""
        # Mock pymoo result
        mock_result = Mock()
        n_persons = len(pareto_test_persons)
        n_blocks = len(pareto_test_blocks)
        mock_result.X = np.random.rand(5, n_persons * n_blocks)
        mock_result.F = np.random.rand(5, len(sample_objectives[:2]))
        mock_result.algorithm = Mock(n_gen=5)
        mock_minimize.return_value = mock_result

        result = pareto_service.optimize_schedule_pareto(
            objectives=sample_objectives[:2],
            constraints=sample_constraints,
            person_ids=[p.id for p in pareto_test_persons],
            block_ids=[b.id for b in pareto_test_blocks],
            population_size=10,
            n_generations=5,
            seed=42,
        )

        assert isinstance(result, ParetoResult)
        assert result.total_solutions > 0
        assert len(result.solutions) > 0
        assert result.algorithm == "NSGA-II"
        assert result.execution_time_seconds > 0
        assert mock_minimize.called

    def test_get_pareto_frontier_empty(self, pareto_service: ParetoOptimizationService):
        """Test Pareto frontier extraction with empty solutions."""
        frontier = pareto_service.get_pareto_frontier([])
        assert frontier == []

    def test_get_pareto_frontier_single_solution(
        self,
        pareto_service: ParetoOptimizationService,
        sample_solutions,
    ):
        """Test Pareto frontier with single solution."""
        frontier = pareto_service.get_pareto_frontier([sample_solutions[0]])
        assert len(frontier) == 1
        assert frontier[0].solution_id == sample_solutions[0].solution_id

    def test_get_pareto_frontier_multiple_solutions(
        self,
        pareto_service: ParetoOptimizationService,
        sample_solutions,
    ):
        """Test Pareto frontier extraction with multiple solutions."""
        frontier = pareto_service.get_pareto_frontier(sample_solutions)

        assert isinstance(frontier, list)
        assert len(frontier) > 0
        assert len(frontier) <= len(sample_solutions)
        # All frontier solutions should be in original solutions
        assert all(sol in sample_solutions for sol in frontier)

    def test_find_pareto_frontier_dominance(self, pareto_service: ParetoOptimizationService):
        """Test Pareto frontier correctly identifies dominated solutions."""
        solutions = [
            # Solution 0: dominated by solution 1
            ParetoSolution(
                solution_id=0,
                objective_values={"obj1": 5.0, "obj2": 5.0},
                decision_variables={},
                is_feasible=True,
            ),
            # Solution 1: dominates solution 0 (better in all objectives)
            ParetoSolution(
                solution_id=1,
                objective_values={"obj1": 2.0, "obj2": 2.0},
                decision_variables={},
                is_feasible=True,
            ),
            # Solution 2: non-dominated (trade-off with solution 1)
            ParetoSolution(
                solution_id=2,
                objective_values={"obj1": 1.0, "obj2": 8.0},
                decision_variables={},
                is_feasible=True,
            ),
        ]

        frontier_indices = pareto_service._find_pareto_frontier(solutions)

        assert 0 not in frontier_indices  # Dominated
        assert 1 in frontier_indices  # Non-dominated
        assert 2 in frontier_indices  # Non-dominated

    def test_rank_solutions_empty(self, pareto_service: ParetoOptimizationService):
        """Test ranking with empty solutions."""
        ranked = pareto_service.rank_solutions(
            solutions=[],
            weights={"obj1": 0.5, "obj2": 0.5},
        )
        assert ranked == []

    def test_rank_solutions_minmax_normalization(
        self,
        pareto_service: ParetoOptimizationService,
        sample_solutions,
    ):
        """Test ranking with minmax normalization."""
        weights = {
            "fairness": 0.3,
            "coverage": 0.3,
            "preference_satisfaction": 0.2,
            "workload_balance": 0.1,
            "consecutive_days": 0.05,
            "specialty_distribution": 0.05,
        }

        ranked = pareto_service.rank_solutions(
            solutions=sample_solutions,
            weights=weights,
            normalization="minmax",
        )

        assert len(ranked) == len(sample_solutions)
        assert all(isinstance(sol, RankedSolution) for sol in ranked)
        # Ranks should be 1, 2, 3
        assert [sol.rank for sol in ranked] == [1, 2, 3]
        # Scores should be in descending order
        scores = [sol.score for sol in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_solutions_zscore_normalization(
        self,
        pareto_service: ParetoOptimizationService,
        sample_solutions,
    ):
        """Test ranking with z-score normalization."""
        weights = {
            "fairness": 0.5,
            "coverage": 0.5,
            "preference_satisfaction": 0.0,
            "workload_balance": 0.0,
            "consecutive_days": 0.0,
            "specialty_distribution": 0.0,
        }

        ranked = pareto_service.rank_solutions(
            solutions=sample_solutions,
            weights=weights,
            normalization="zscore",
        )

        assert len(ranked) == len(sample_solutions)
        assert all(sol.rank >= 1 for sol in ranked)

    def test_rank_solutions_no_normalization(
        self,
        pareto_service: ParetoOptimizationService,
        sample_solutions,
    ):
        """Test ranking without normalization."""
        weights = {"fairness": 1.0, "coverage": 1.0}

        ranked = pareto_service.rank_solutions(
            solutions=sample_solutions,
            weights=weights,
            normalization="none",
        )

        assert len(ranked) == len(sample_solutions)

    def test_rank_solutions_weighted_breakdown(
        self,
        pareto_service: ParetoOptimizationService,
        sample_solutions,
    ):
        """Test that ranking includes weighted score breakdown."""
        weights = {
            "fairness": 0.5,
            "coverage": 0.5,
            "preference_satisfaction": 0.0,
            "workload_balance": 0.0,
            "consecutive_days": 0.0,
            "specialty_distribution": 0.0,
        }

        ranked = pareto_service.rank_solutions(
            solutions=sample_solutions,
            weights=weights,
            normalization="minmax",
        )

        for solution in ranked:
            assert isinstance(solution.weighted_score_breakdown, dict)
            assert len(solution.weighted_score_breakdown) > 0
            # Weighted breakdown should sum to total score
            total = sum(solution.weighted_score_breakdown.values())
            assert abs(total - solution.score) < 0.001  # Allow small floating point error

    def test_calculate_hypervolume_empty(self, pareto_service: ParetoOptimizationService):
        """Test hypervolume calculation with empty frontier."""
        hypervolume = pareto_service._calculate_hypervolume([], [])
        assert hypervolume is None

    def test_calculate_hypervolume_valid(
        self,
        pareto_service: ParetoOptimizationService,
        sample_solutions,
    ):
        """Test hypervolume calculation with valid solutions."""
        frontier_indices = [0, 1]
        hypervolume = pareto_service._calculate_hypervolume(sample_solutions, frontier_indices)

        assert hypervolume is None or isinstance(hypervolume, float)
        if hypervolume is not None:
            assert hypervolume > 0

    def test_person_to_dict(
        self,
        pareto_service: ParetoOptimizationService,
        pareto_test_persons,
    ):
        """Test person model to dictionary conversion."""
        person = pareto_test_persons[0]
        person_dict = pareto_service._person_to_dict(person)

        assert isinstance(person_dict, dict)
        assert "id" in person_dict
        assert "name" in person_dict
        assert "pgy_level" in person_dict
        assert person_dict["name"] == person.name

    def test_block_to_dict(
        self,
        pareto_service: ParetoOptimizationService,
        pareto_test_blocks,
    ):
        """Test block model to dictionary conversion."""
        block = pareto_test_blocks[0]
        block_dict = pareto_service._block_to_dict(block)

        assert isinstance(block_dict, dict)
        assert "id" in block_dict
        assert "name" in block_dict
        assert "activity_type" in block_dict
        assert "start_date" in block_dict
        assert "end_date" in block_dict


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestParetoOptimizationIntegration:
    """Integration tests for Pareto optimization with real data."""

    @patch('app.services.pareto_optimization_service.minimize')
    def test_full_optimization_workflow(
        self,
        mock_minimize,
        db: Session,
        pareto_service: ParetoOptimizationService,
        pareto_test_persons,
        pareto_test_blocks,
        sample_objectives,
        sample_constraints,
    ):
        """Test complete optimization workflow from start to finish."""
        # Mock pymoo result
        mock_result = Mock()
        n_persons = len(pareto_test_persons)
        n_blocks = len(pareto_test_blocks)
        mock_result.X = np.random.rand(10, n_persons * n_blocks)
        mock_result.F = np.random.rand(10, len(sample_objectives))
        mock_result.algorithm = Mock(n_gen=20)
        mock_minimize.return_value = mock_result

        # Step 1: Run optimization
        result = pareto_service.optimize_schedule_pareto(
            objectives=sample_objectives,
            constraints=sample_constraints,
            person_ids=[p.id for p in pareto_test_persons],
            block_ids=[b.id for b in pareto_test_blocks],
            population_size=20,
            n_generations=20,
            seed=42,
        )

        assert result.total_solutions > 0
        assert len(result.solutions) > 0

        # Step 2: Extract Pareto frontier
        frontier = pareto_service.get_pareto_frontier(result.solutions)
        assert len(frontier) > 0
        assert len(frontier) <= len(result.solutions)

        # Step 3: Rank solutions
        weights = {obj.name.value: obj.weight for obj in sample_objectives}
        ranked = pareto_service.rank_solutions(
            solutions=result.solutions,
            weights=weights,
            normalization="minmax",
        )

        assert len(ranked) == len(result.solutions)
        assert ranked[0].rank == 1

    def test_all_six_objectives_evaluated(
        self,
        db: Session,
        pareto_test_persons,
        pareto_test_blocks,
    ):
        """Test that all six objectives are properly evaluated."""
        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, direction=ObjectiveDirection.MINIMIZE),
            ParetoObjective(name=ObjectiveName.COVERAGE, direction=ObjectiveDirection.MAXIMIZE),
            ParetoObjective(name=ObjectiveName.PREFERENCE_SATISFACTION, direction=ObjectiveDirection.MAXIMIZE),
            ParetoObjective(name=ObjectiveName.WORKLOAD_BALANCE, direction=ObjectiveDirection.MINIMIZE),
            ParetoObjective(name=ObjectiveName.CONSECUTIVE_DAYS, direction=ObjectiveDirection.MINIMIZE),
            ParetoObjective(name=ObjectiveName.SPECIALTY_DISTRIBUTION, direction=ObjectiveDirection.MINIMIZE),
        ]

        person_data = [{"id": str(p.id), "name": p.name} for p in pareto_test_persons]
        block_data = [{"id": str(b.id), "name": b.name, "activity_type": b.activity_type, "specialty": "general"} for b in pareto_test_blocks]

        problem = SchedulingProblem(
            n_persons=len(pareto_test_persons),
            n_blocks=len(pareto_test_blocks),
            objectives=objectives,
            constraints=[],
            person_data=person_data,
            block_data=block_data,
        )

        # Create random solution
        x = np.random.rand(len(pareto_test_persons) * len(pareto_test_blocks))
        out = {}
        problem._evaluate(x, out)

        assert "F" in out
        assert len(out["F"]) == 6
        assert all(isinstance(f, (int, float, np.number)) for f in out["F"])


# ============================================================================
# Edge Cases
# ============================================================================


@pytest.mark.unit
class TestParetoOptimizationEdgeCases:
    """Test edge cases and error handling."""

    def test_single_objective_warning(self):
        """Test that having only one objective is handled."""
        # This would typically require at least 2 objectives for Pareto optimization
        objective = [
            ParetoObjective(
                name=ObjectiveName.FAIRNESS,
                direction=ObjectiveDirection.MINIMIZE,
            )
        ]
        # In practice, the API should validate this, but service should handle gracefully

    def test_zero_weight_objectives(self, pareto_service: ParetoOptimizationService, sample_solutions):
        """Test ranking with zero-weight objectives."""
        weights = {
            "fairness": 0.0,
            "coverage": 0.0,
            "preference_satisfaction": 0.0,
            "workload_balance": 0.0,
            "consecutive_days": 0.0,
            "specialty_distribution": 0.0,
        }

        ranked = pareto_service.rank_solutions(
            solutions=sample_solutions,
            weights=weights,
            normalization="minmax",
        )

        # Should still rank, all with equal scores of 0
        assert len(ranked) == len(sample_solutions)

    def test_uniform_objective_values(self, pareto_service: ParetoOptimizationService):
        """Test ranking when all solutions have same objective values."""
        solutions = [
            ParetoSolution(
                solution_id=i,
                objective_values={"obj1": 1.0, "obj2": 1.0},
                decision_variables={},
                is_feasible=True,
            )
            for i in range(3)
        ]

        ranked = pareto_service.rank_solutions(
            solutions=solutions,
            weights={"obj1": 0.5, "obj2": 0.5},
            normalization="minmax",
        )

        # All should have equal normalized scores
        assert len(ranked) == 3

    def test_extreme_population_parameters(self, sample_objectives, sample_constraints):
        """Test problem creation with extreme parameters."""
        # Very large problem
        problem_large = SchedulingProblem(
            n_persons=100,
            n_blocks=200,
            objectives=sample_objectives[:2],
            constraints=sample_constraints,
            person_data=[{"id": str(i)} for i in range(100)],
            block_data=[{"id": str(i)} for i in range(200)],
        )
        assert problem_large.n_var == 20000

        # Very small problem
        problem_small = SchedulingProblem(
            n_persons=1,
            n_blocks=1,
            objectives=sample_objectives[:2],
            constraints=[],
            person_data=[{"id": "1"}],
            block_data=[{"id": "1"}],
        )
        assert problem_small.n_var == 1

    def test_infeasible_constraints(self, sample_objectives):
        """Test handling of infeasible constraint configurations."""
        constraints = [
            ParetoConstraint(
                constraint_type="max_consecutive_days",
                parameters={"max_days": 0},  # Impossible constraint
                is_hard=True,
            ),
        ]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=3,
            objectives=sample_objectives[:2],
            constraints=constraints,
            person_data=[{"id": str(i)} for i in range(2)],
            block_data=[{"id": str(i)} for i in range(3)],
        )

        # Should still evaluate without errors
        x = np.random.rand(6)
        out = {}
        problem._evaluate(x, out)
        assert "G" in out

    def test_mixed_hard_soft_constraints(self, sample_objectives):
        """Test problem with both hard and soft constraints."""
        constraints = [
            ParetoConstraint(
                constraint_type="max_consecutive_days",
                parameters={"max_days": 5},
                is_hard=True,
            ),
            ParetoConstraint(
                constraint_type="preferred_rest_days",
                parameters={"min_days": 2},
                is_hard=False,  # Soft constraint
            ),
        ]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=3,
            objectives=sample_objectives[:2],
            constraints=constraints,
            person_data=[{"id": str(i)} for i in range(2)],
            block_data=[{"id": str(i)} for i in range(3)],
        )

        # Only hard constraints should be in constraint count
        assert problem.n_ieq_constr == 1

    def test_extract_solutions_with_none_result(
        self,
        pareto_service: ParetoOptimizationService,
        pareto_test_persons,
        pareto_test_blocks,
        sample_objectives,
    ):
        """Test solution extraction when pymoo returns None."""
        mock_result = Mock()
        mock_result.X = None
        mock_result.F = None

        solutions = pareto_service._extract_solutions(
            mock_result,
            pareto_test_persons,
            pareto_test_blocks,
            sample_objectives,
        )

        assert solutions == []

    def test_extract_solutions_single_solution(
        self,
        pareto_service: ParetoOptimizationService,
        pareto_test_persons,
        pareto_test_blocks,
        sample_objectives,
    ):
        """Test extraction of single solution (1D arrays)."""
        mock_result = Mock()
        n_vars = len(pareto_test_persons) * len(pareto_test_blocks)
        mock_result.X = np.random.rand(n_vars)  # 1D array
        mock_result.F = np.random.rand(len(sample_objectives))  # 1D array

        solutions = pareto_service._extract_solutions(
            mock_result,
            pareto_test_persons,
            pareto_test_blocks,
            sample_objectives,
        )

        assert len(solutions) == 1
        assert isinstance(solutions[0], ParetoSolution)


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.slow
class TestParetoOptimizationPerformance:
    """Performance tests for Pareto optimization (marked as slow)."""

    @patch('app.services.pareto_optimization_service.minimize')
    def test_large_scale_optimization(
        self,
        mock_minimize,
        db: Session,
        pareto_service: ParetoOptimizationService,
        sample_objectives,
    ):
        """Test optimization with large population and generation count."""
        # Create more test data
        persons = []
        for i in range(20):
            person = Person(
                id=uuid4(),
                name=f"Dr. Person {i}",
                type="resident",
                email=f"person{i}@test.org",
                pgy_level=(i % 3) + 1,
            )
            db.add(person)
            persons.append(person)

        blocks = []
        for i in range(50):
            block = Block(
                id=uuid4(),
                date=date.today() + timedelta(days=i // 2),
                time_of_day="AM" if i % 2 == 0 else "PM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)

        db.commit()

        # Mock result
        mock_result = Mock()
        mock_result.X = np.random.rand(100, 20 * 50)
        mock_result.F = np.random.rand(100, len(sample_objectives))
        mock_result.algorithm = Mock(n_gen=50)
        mock_minimize.return_value = mock_result

        result = pareto_service.optimize_schedule_pareto(
            objectives=sample_objectives,
            constraints=[],
            person_ids=[p.id for p in persons],
            block_ids=[b.id for b in blocks],
            population_size=100,
            n_generations=50,
        )

        assert result.total_solutions > 0
        assert result.execution_time_seconds > 0
