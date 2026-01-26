"""Tests for ParetoOptimizationService."""

from datetime import date, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import numpy as np
import pytest

from app.models.block import Block
from app.models.person import Person
from app.schemas.pareto import (
    ObjectiveDirection,
    ObjectiveName,
    ParetoConstraint,
    ParetoObjective,
    ParetoSolution,
)
from app.services.pareto_optimization_service import (
    ParetoOptimizationService,
    SchedulingProblem,
)


class TestSchedulingProblem:
    """Test suite for SchedulingProblem class."""

    def test_initialization(self):
        """Test SchedulingProblem initialization."""
        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0),
        ]
        constraints = [
            ParetoConstraint(
                constraint_type="max_consecutive_days",
                parameters={"max_days": 5},
                is_hard=True,
            )
        ]
        person_data = [{"id": "1", "name": "Dr. A", "pgy_level": 1}]
        block_data = [{"id": "1", "name": "Block 1", "rotation_type": "clinic"}]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=1,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        assert problem.n_persons == 1
        assert problem.n_blocks == 1
        assert len(problem.objectives_config) == 2
        assert len(problem.constraints_config) == 1
        assert problem.n_var == 1  # 1 person * 1 block
        assert problem.n_obj == 2
        assert problem.n_ieq_constr == 1

    def test_decode_solution_single_assignment(self):
        """Test decoding solution with single assignment."""
        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0),
        ]
        constraints = []
        person_data = [{"id": "1", "name": "Dr. A"}]
        block_data = [{"id": "1", "name": "Block 1"}]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Solution with values above threshold (0.5)
        x = np.array([0.8, 0.2])
        matrix = problem._decode_solution(x)

        assert matrix.shape == (2, 1)  # 2 blocks, 1 person
        assert matrix[0, 0] == 1  # 0.8 > 0.5
        assert matrix[1, 0] == 0  # 0.2 < 0.5

    def test_decode_solution_multiple_assignments(self):
        """Test decoding solution with multiple persons and blocks."""
        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
        ]
        constraints = []
        person_data = [{"id": "1"}, {"id": "2"}]
        block_data = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=3,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # 6 decision variables (3 blocks * 2 persons)
        x = np.array([0.9, 0.1, 0.6, 0.4, 0.7, 0.3])
        matrix = problem._decode_solution(x)

        assert matrix.shape == (3, 2)
        # Expected matrix:
        # Block 0: [1, 0] (0.9 > 0.5, 0.1 < 0.5)
        # Block 1: [1, 0] (0.6 > 0.5, 0.4 < 0.5)
        # Block 2: [1, 0] (0.7 > 0.5, 0.3 < 0.5)
        assert matrix[0, 0] == 1 and matrix[0, 1] == 0
        assert matrix[1, 0] == 1 and matrix[1, 1] == 0
        assert matrix[2, 0] == 1 and matrix[2, 1] == 0

    def test_calculate_fairness_equal_distribution(self):
        """Test fairness calculation with equal distribution."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}, {"id": "2"}]
        block_data = [{"id": "1"}, {"id": "2"}]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Equal assignments: each person gets 1 assignment
        assignment_matrix = np.array([[1, 0], [0, 1]])
        fairness = problem._calculate_fairness(assignment_matrix)

        # Perfect fairness should be close to 0
        assert fairness == 0.0

    def test_calculate_fairness_unequal_distribution(self):
        """Test fairness calculation with unequal distribution."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}, {"id": "2"}]
        block_data = [{"id": "1"}, {"id": "2"}]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Unequal: person 0 gets both assignments
        assignment_matrix = np.array([[1, 0], [1, 0]])
        fairness = problem._calculate_fairness(assignment_matrix)

        # Should have non-zero fairness score (coefficient of variation)
        assert fairness > 0.0

    def test_calculate_coverage_full(self):
        """Test coverage calculation with full coverage."""
        objectives = [ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}]
        block_data = [{"id": "1"}, {"id": "2"}]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # All blocks covered
        assignment_matrix = np.array([[1], [1]])
        coverage = problem._calculate_coverage(assignment_matrix)

        # Coverage is negated for minimization, so should be -1.0
        assert coverage == -1.0

    def test_calculate_coverage_partial(self):
        """Test coverage calculation with partial coverage."""
        objectives = [ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}]
        block_data = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=3,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Only first block covered
        assignment_matrix = np.array([[1], [0], [0]])
        coverage = problem._calculate_coverage(assignment_matrix)

        # 1/3 coverage = 0.333..., negated = -0.333...
        assert coverage == pytest.approx(-1 / 3)

    def test_calculate_preference_satisfaction_with_match(self):
        """Test preference satisfaction with matching preferences."""
        objectives = [
            ParetoObjective(name=ObjectiveName.PREFERENCE_SATISFACTION, weight=1.0)
        ]
        constraints = []
        person_data = [
            {"id": "1", "preferred_rotation_types": ["clinic", "procedures"]}
        ]
        block_data = [
            {"id": "1", "rotation_type": "clinic"},
            {"id": "2", "rotation_type": "inpatient"},
        ]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Person assigned to both blocks
        assignment_matrix = np.array([[1], [1]])
        satisfaction = problem._calculate_preference_satisfaction(assignment_matrix)

        # 1 match out of 2 assignments = 0.5, negated = -0.5
        assert satisfaction == -0.5

    def test_calculate_preference_satisfaction_no_preferences(self):
        """Test preference satisfaction with no preference data."""
        objectives = [
            ParetoObjective(name=ObjectiveName.PREFERENCE_SATISFACTION, weight=1.0)
        ]
        constraints = []
        person_data = [{"id": "1"}]
        block_data = [{"id": "1"}]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=1,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        assignment_matrix = np.array([[1]])
        satisfaction = problem._calculate_preference_satisfaction(assignment_matrix)

        # No preferences means 0 satisfaction
        assert satisfaction == 0.0

    def test_calculate_workload_balance_equal(self):
        """Test workload balance with equal workload."""
        objectives = [ParetoObjective(name=ObjectiveName.WORKLOAD_BALANCE, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}, {"id": "2"}]
        block_data = [{"id": "1"}, {"id": "2"}]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Equal workload: each person gets 1 assignment
        assignment_matrix = np.array([[1, 0], [0, 1]])
        balance = problem._calculate_workload_balance(assignment_matrix)

        # Perfectly balanced: max - min = 1 - 1 = 0
        assert balance == 0.0

    def test_calculate_workload_balance_unequal(self):
        """Test workload balance with unequal workload."""
        objectives = [ParetoObjective(name=ObjectiveName.WORKLOAD_BALANCE, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}, {"id": "2"}]
        block_data = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=3,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Unbalanced: person 0 gets 3, person 1 gets 0
        assignment_matrix = np.array([[1, 0], [1, 0], [1, 0]])
        balance = problem._calculate_workload_balance(assignment_matrix)

        # max - min = 3 - 0 = 3
        assert balance == 3.0

    def test_calculate_consecutive_days_no_penalty(self):
        """Test consecutive days with no penalty."""
        objectives = [ParetoObjective(name=ObjectiveName.CONSECUTIVE_DAYS, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}]
        block_data = [{"id": str(i)} for i in range(5)]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=5,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # 5 consecutive days (no penalty since threshold is 5)
        assignment_matrix = np.array([[1], [1], [1], [1], [1]])
        penalty = problem._calculate_consecutive_days(assignment_matrix)

        # No penalty for 5 or less consecutive
        assert penalty == 0.0

    def test_calculate_consecutive_days_with_penalty(self):
        """Test consecutive days with penalty for too many consecutive."""
        objectives = [ParetoObjective(name=ObjectiveName.CONSECUTIVE_DAYS, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}]
        block_data = [{"id": str(i)} for i in range(10)]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=10,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # 10 consecutive days
        assignment_matrix = np.ones((10, 1), dtype=int)
        penalty = problem._calculate_consecutive_days(assignment_matrix)

        # Penalty for 6th, 7th, 8th, 9th, 10th day
        # (6-5)^2 + (7-5)^2 + (8-5)^2 + (9-5)^2 + (10-5)^2
        # = 1 + 4 + 9 + 16 + 25 = 55
        assert penalty == 55.0

    def test_calculate_consecutive_days_with_breaks(self):
        """Test consecutive days with breaks."""
        objectives = [ParetoObjective(name=ObjectiveName.CONSECUTIVE_DAYS, weight=1.0)]
        constraints = []
        person_data = [{"id": "1"}]
        block_data = [{"id": str(i)} for i in range(8)]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=8,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # 3 consecutive, break, 3 consecutive (no penalty)
        assignment_matrix = np.array([[1], [1], [1], [0], [1], [1], [1], [0]])
        penalty = problem._calculate_consecutive_days(assignment_matrix)

        assert penalty == 0.0

    def test_calculate_specialty_distribution_balanced(self):
        """Test specialty distribution with balanced distribution."""
        objectives = [
            ParetoObjective(name=ObjectiveName.SPECIALTY_DISTRIBUTION, weight=1.0)
        ]
        constraints = []
        person_data = [{"id": "1"}]
        block_data = [
            {"id": "1", "specialty": "cardiology"},
            {"id": "2", "specialty": "neurology"},
        ]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Balanced: 1 assignment per specialty
        assignment_matrix = np.array([[1], [1]])
        distribution = problem._calculate_specialty_distribution(assignment_matrix)

        # std of [1, 1] = 0
        assert distribution == 0.0

    def test_calculate_specialty_distribution_unbalanced(self):
        """Test specialty distribution with unbalanced distribution."""
        objectives = [
            ParetoObjective(name=ObjectiveName.SPECIALTY_DISTRIBUTION, weight=1.0)
        ]
        constraints = []
        person_data = [{"id": "1"}]
        block_data = [
            {"id": "1", "specialty": "cardiology"},
            {"id": "2", "specialty": "cardiology"},
            {"id": "3", "specialty": "neurology"},
        ]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=3,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Unbalanced: 2 cardiology, 1 neurology
        assignment_matrix = np.array([[1], [1], [1]])
        distribution = problem._calculate_specialty_distribution(assignment_matrix)

        # std of [2, 1] = 0.5
        assert distribution == pytest.approx(0.5)

    def test_evaluate_objectives(self):
        """Test _evaluate method calculates objectives correctly."""
        objectives = [
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
        ]
        constraints = []
        person_data = [{"id": "1"}, {"id": "2"}]
        block_data = [{"id": "1"}, {"id": "2"}]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Perfect solution: equal distribution, full coverage
        x = np.array([0.9, 0.1, 0.1, 0.9])
        out = {}
        problem._evaluate(x, out)

        assert "F" in out
        assert len(out["F"]) == 2
        # Fairness should be 0 (perfect balance)
        assert out["F"][0] == 0.0
        # Coverage: _calculate_coverage returns -1.0, then negated for MAXIMIZE = 1.0
        assert out["F"][1] == 1.0

    def test_evaluate_constraints_max_consecutive_days_satisfied(self):
        """Test constraint evaluation when max consecutive days is satisfied."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = [
            ParetoConstraint(
                constraint_type="max_consecutive_days",
                parameters={"max_days": 3},
                is_hard=True,
            )
        ]
        person_data = [{"id": "1"}]
        block_data = [{"id": str(i)} for i in range(5)]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=5,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # 2 consecutive, break, 2 consecutive (satisfies constraint)
        x = np.array([0.9, 0.9, 0.1, 0.9, 0.9])
        out = {}
        problem._evaluate(x, out)

        assert "G" in out
        # No violation
        assert out["G"][0] == 0.0

    def test_evaluate_constraints_max_consecutive_days_violated(self):
        """Test constraint evaluation when max consecutive days is violated."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = [
            ParetoConstraint(
                constraint_type="max_consecutive_days",
                parameters={"max_days": 3},
                is_hard=True,
            )
        ]
        person_data = [{"id": "1"}]
        block_data = [{"id": str(i)} for i in range(6)]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=6,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # 6 consecutive days (violates max of 3)
        x = np.ones(6) * 0.9
        out = {}
        problem._evaluate(x, out)

        assert "G" in out
        # Violation: days 4, 5, 6 exceed the limit
        # (4-3) + (5-3) + (6-3) = 1 + 2 + 3 = 6
        assert out["G"][0] == 6.0

    def test_evaluate_constraints_min_coverage_satisfied(self):
        """Test constraint evaluation when min coverage is satisfied."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = [
            ParetoConstraint(
                constraint_type="min_coverage",
                parameters={"min_rate": 0.5},
                is_hard=True,
            )
        ]
        person_data = [{"id": "1"}]
        block_data = [{"id": "1"}, {"id": "2"}]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=2,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # 100% coverage (satisfies 50% minimum)
        x = np.array([0.9, 0.9])
        out = {}
        problem._evaluate(x, out)

        assert "G" in out
        assert out["G"][0] == 0.0

    def test_evaluate_constraints_min_coverage_violated(self):
        """Test constraint evaluation when min coverage is violated."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = [
            ParetoConstraint(
                constraint_type="min_coverage",
                parameters={"min_rate": 0.8},
                is_hard=True,
            )
        ]
        person_data = [{"id": "1"}]
        block_data = [{"id": str(i)} for i in range(10)]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=10,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Only 50% coverage (violates 80% minimum)
        x = np.array([0.9, 0.9, 0.9, 0.9, 0.9, 0.1, 0.1, 0.1, 0.1, 0.1])
        out = {}
        problem._evaluate(x, out)

        assert "G" in out
        # Violation: 0.8 - 0.5 = 0.3
        assert out["G"][0] == pytest.approx(0.3)

    def test_evaluate_constraints_max_assignments_per_person_satisfied(self):
        """Test constraint when max assignments per person is satisfied."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = [
            ParetoConstraint(
                constraint_type="max_assignments_per_person",
                parameters={"max_count": 3},
                is_hard=True,
            )
        ]
        person_data = [{"id": "1"}, {"id": "2"}]
        block_data = [{"id": str(i)} for i in range(4)]

        problem = SchedulingProblem(
            n_persons=2,
            n_blocks=4,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Each person gets 2 assignments (< 3 max)
        x = np.array([0.9, 0.1, 0.9, 0.1, 0.1, 0.9, 0.1, 0.9])
        out = {}
        problem._evaluate(x, out)

        assert "G" in out
        assert out["G"][0] == 0.0

    def test_evaluate_constraints_max_assignments_per_person_violated(self):
        """Test constraint when max assignments per person is violated."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = [
            ParetoConstraint(
                constraint_type="max_assignments_per_person",
                parameters={"max_count": 2},
                is_hard=True,
            )
        ]
        person_data = [{"id": "1"}]
        block_data = [{"id": str(i)} for i in range(5)]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=5,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # Person gets 5 assignments (exceeds max of 2)
        x = np.ones(5) * 0.9
        out = {}
        problem._evaluate(x, out)

        assert "G" in out
        # Violation: 5 - 2 = 3
        assert out["G"][0] == 3.0

    def test_evaluate_soft_constraints_ignored(self):
        """Test that soft constraints are not included in constraint violations."""
        objectives = [ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0)]
        constraints = [
            ParetoConstraint(
                constraint_type="max_consecutive_days",
                parameters={"max_days": 3},
                is_hard=False,  # Soft constraint
            )
        ]
        person_data = [{"id": "1"}]
        block_data = [{"id": str(i)} for i in range(6)]

        problem = SchedulingProblem(
            n_persons=1,
            n_blocks=6,
            objectives=objectives,
            constraints=constraints,
            person_data=person_data,
            block_data=block_data,
        )

        # 6 consecutive days (would violate if hard)
        x = np.ones(6) * 0.9
        out = {}
        problem._evaluate(x, out)

        # Soft constraints should not be in G
        assert "G" not in out


class TestParetoOptimizationService:
    """Test suite for ParetoOptimizationService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def mock_persons(self):
        """Create mock person objects."""
        persons = []
        for i in range(3):
            person = Mock(spec=Person)
            person.id = uuid4()
            person.name = f"Dr. Person {i + 1}"
            person.pgy_level = i + 1
            person.preferred_rotation_types = ["clinic"]
            persons.append(person)
        return persons

    @pytest.fixture
    def mock_blocks(self):
        """Create mock block objects."""
        blocks = []
        start_date = date.today()
        for i in range(5):
            block = Mock(spec=Block)
            block.id = uuid4()
            block.name = f"Block {i + 1}"
            block.rotation_type = "clinic"
            block.specialty = "general"
            block.start_date = start_date + timedelta(days=i)
            block.end_date = start_date + timedelta(days=i)
            blocks.append(block)
        return blocks

    @pytest.fixture
    def service(self, mock_db):
        """Create ParetoOptimizationService instance."""
        return ParetoOptimizationService(mock_db)

    def test_service_initialization(self, mock_db):
        """Test service initialization."""
        service = ParetoOptimizationService(mock_db)

        assert service.db == mock_db
        assert service.assignment_repo is not None
        assert service.block_repo is not None
        assert service.person_repo is not None

    @patch("app.services.pareto_optimization_service.minimize")
    def test_optimize_schedule_pareto_success(
        self, mock_minimize, service, mock_persons, mock_blocks
    ):
        """Test successful Pareto optimization."""
        # Mock repository methods
        service.person_repo.list_all = Mock(return_value=mock_persons)
        service.block_repo.list_all = Mock(return_value=mock_blocks)

        # Mock pymoo result
        # 3 persons * 5 blocks = 15 decision variables
        mock_result = Mock()
        mock_result.X = np.array(
            [
                [
                    0.9,
                    0.1,
                    0.8,
                    0.2,
                    0.7,
                    0.3,
                    0.6,
                    0.4,
                    0.5,
                    0.5,
                    0.8,
                    0.2,
                    0.7,
                    0.3,
                    0.6,
                ]
            ]
        )
        mock_result.F = np.array([[0.1, -0.9]])
        mock_result.algorithm = Mock()
        mock_result.algorithm.n_gen = 50
        mock_minimize.return_value = mock_result

        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0),
        ]
        constraints = []

        result = service.optimize_schedule_pareto(
            objectives=objectives,
            constraints=constraints,
            population_size=10,
            n_generations=50,
            seed=42,
        )

        assert result is not None
        assert result.total_solutions > 0
        assert len(result.solutions) > 0
        assert result.execution_time_seconds >= 0
        assert result.algorithm == "NSGA-II"

    def test_optimize_schedule_pareto_no_persons(self, service):
        """Test optimization with no persons available."""
        service.person_repo.list_all = Mock(return_value=[])
        service.block_repo.list_all = Mock(return_value=[])

        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0),
        ]
        constraints = []

        result = service.optimize_schedule_pareto(
            objectives=objectives,
            constraints=constraints,
        )

        assert result.total_solutions == 0
        assert len(result.solutions) == 0
        assert result.termination_reason == "No persons or blocks available"

    def test_optimize_schedule_pareto_no_blocks(self, service, mock_persons):
        """Test optimization with no blocks available."""
        service.person_repo.list_all = Mock(return_value=mock_persons)
        service.block_repo.list_all = Mock(return_value=[])

        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0),
        ]
        constraints = []

        result = service.optimize_schedule_pareto(
            objectives=objectives,
            constraints=constraints,
        )

        assert result.total_solutions == 0
        assert len(result.solutions) == 0
        assert result.termination_reason == "No persons or blocks available"

    @patch("app.services.pareto_optimization_service.minimize")
    def test_optimize_schedule_pareto_with_person_filter(
        self, mock_minimize, service, mock_persons, mock_blocks
    ):
        """Test optimization with person_ids filter."""
        # Mock get_by_id to return specific person
        service.person_repo.get_by_id = Mock(return_value=mock_persons[0])
        service.block_repo.list_all = Mock(return_value=mock_blocks)

        # Mock pymoo result
        mock_result = Mock()
        mock_result.X = np.array([[0.9] * 5])
        mock_result.F = np.array([[0.1, -0.9]])
        mock_result.algorithm = Mock()
        mock_result.algorithm.n_gen = 10
        mock_minimize.return_value = mock_result

        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0),
        ]

        result = service.optimize_schedule_pareto(
            objectives=objectives,
            constraints=[],
            person_ids=[mock_persons[0].id],
        )

        service.person_repo.get_by_id.assert_called()
        assert result is not None

    @patch("app.services.pareto_optimization_service.minimize")
    def test_optimize_schedule_pareto_with_block_filter(
        self, mock_minimize, service, mock_persons, mock_blocks
    ):
        """Test optimization with block_ids filter."""
        service.person_repo.list_all = Mock(return_value=mock_persons)
        service.block_repo.get_by_id = Mock(return_value=mock_blocks[0])

        # Mock pymoo result
        mock_result = Mock()
        mock_result.X = np.array([[0.9, 0.1, 0.8]])
        mock_result.F = np.array([[0.1, -0.9]])
        mock_result.algorithm = Mock()
        mock_result.algorithm.n_gen = 10
        mock_minimize.return_value = mock_result

        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0),
        ]

        result = service.optimize_schedule_pareto(
            objectives=objectives,
            constraints=[],
            block_ids=[mock_blocks[0].id],
        )

        service.block_repo.get_by_id.assert_called()
        assert result is not None

    def test_get_pareto_frontier_empty_solutions(self, service):
        """Test getting Pareto frontier with empty solutions list."""
        solutions = []
        frontier = service.get_pareto_frontier(solutions)

        assert len(frontier) == 0

    def test_get_pareto_frontier_single_solution(self, service):
        """Test getting Pareto frontier with single solution."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"fairness": 0.5, "coverage": 0.8},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            )
        ]

        frontier = service.get_pareto_frontier(solutions)

        assert len(frontier) == 1
        assert frontier[0].solution_id == 0

    def test_get_pareto_frontier_multiple_non_dominated(self, service):
        """Test getting Pareto frontier with multiple non-dominated solutions."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"fairness": 0.1, "coverage": 0.9},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
            ParetoSolution(
                solution_id=1,
                objective_values={"fairness": 0.9, "coverage": 0.1},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]

        frontier = service.get_pareto_frontier(solutions)

        # Both solutions are on the frontier (trade-off between objectives)
        assert len(frontier) == 2

    def test_get_pareto_frontier_with_dominated_solution(self, service):
        """Test getting Pareto frontier with dominated solution."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"fairness": 0.1, "coverage": 0.1},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
            ParetoSolution(
                solution_id=1,
                objective_values={"fairness": 0.5, "coverage": 0.5},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]

        frontier = service.get_pareto_frontier(solutions)

        # Solution 0 dominates solution 1 (better in both objectives)
        assert len(frontier) == 1
        assert frontier[0].solution_id == 0

    def test_rank_solutions_empty_list(self, service):
        """Test ranking with empty solutions list."""
        solutions = []
        weights = {"fairness": 1.0, "coverage": 1.0}

        ranked = service.rank_solutions(solutions, weights)

        assert len(ranked) == 0

    def test_rank_solutions_minmax_normalization(self, service):
        """Test ranking with minmax normalization."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"fairness": 0.0, "coverage": 1.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
            ParetoSolution(
                solution_id=1,
                objective_values={"fairness": 1.0, "coverage": 0.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]
        weights = {"fairness": 0.5, "coverage": 0.5}

        ranked = service.rank_solutions(solutions, weights, normalization="minmax")

        assert len(ranked) == 2
        # Check ranks are assigned
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2
        # Check scores are calculated
        assert ranked[0].score >= ranked[1].score

    def test_rank_solutions_zscore_normalization(self, service):
        """Test ranking with z-score normalization."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"fairness": 0.0, "coverage": 1.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
            ParetoSolution(
                solution_id=1,
                objective_values={"fairness": 1.0, "coverage": 0.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]
        weights = {"fairness": 0.5, "coverage": 0.5}

        ranked = service.rank_solutions(solutions, weights, normalization="zscore")

        assert len(ranked) == 2
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2

    def test_rank_solutions_no_normalization(self, service):
        """Test ranking without normalization."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"fairness": 10.0, "coverage": 5.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
            ParetoSolution(
                solution_id=1,
                objective_values={"fairness": 5.0, "coverage": 10.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]
        weights = {"fairness": 1.0, "coverage": 0.5}

        ranked = service.rank_solutions(solutions, weights, normalization="none")

        assert len(ranked) == 2
        # Solution 0: 10*1.0 + 5*0.5 = 12.5
        # Solution 1: 5*1.0 + 10*0.5 = 10.0
        assert ranked[0].solution_id == 0
        assert ranked[0].score == pytest.approx(12.5)
        assert ranked[1].solution_id == 1
        assert ranked[1].score == pytest.approx(10.0)

    def test_rank_solutions_with_missing_weights(self, service):
        """Test ranking with missing weights for some objectives."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"fairness": 1.0, "coverage": 1.0, "balance": 1.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]
        weights = {"fairness": 1.0}  # Missing coverage and balance

        ranked = service.rank_solutions(solutions, weights, normalization="none")

        assert len(ranked) == 1
        # Only fairness is weighted
        assert ranked[0].score == pytest.approx(1.0)

    def test_rank_solutions_weighted_breakdown(self, service):
        """Test that weighted score breakdown is populated."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"fairness": 1.0, "coverage": 2.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]
        weights = {"fairness": 0.5, "coverage": 1.0}

        ranked = service.rank_solutions(solutions, weights, normalization="none")

        assert len(ranked[0].weighted_score_breakdown) == 2
        assert "fairness" in ranked[0].weighted_score_breakdown
        assert "coverage" in ranked[0].weighted_score_breakdown

    def test_find_pareto_frontier_empty(self, service):
        """Test _find_pareto_frontier with empty solutions."""
        solutions = []
        frontier_indices = service._find_pareto_frontier(solutions)

        assert len(frontier_indices) == 0

    def test_find_pareto_frontier_dominance_checking(self, service):
        """Test dominance checking in _find_pareto_frontier."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"obj1": 1.0, "obj2": 1.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
            ParetoSolution(
                solution_id=1,
                objective_values={"obj1": 2.0, "obj2": 2.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
            ParetoSolution(
                solution_id=2,
                objective_values={"obj1": 1.0, "obj2": 2.0},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]

        frontier_indices = service._find_pareto_frontier(solutions)

        # Solution 0 dominates both solution 1 and solution 2 (better in all objectives)
        # Only solution 0 should be on the frontier
        assert len(frontier_indices) == 1
        assert 0 in frontier_indices
        assert 1 not in frontier_indices
        assert 2 not in frontier_indices

    def test_calculate_hypervolume_empty_frontier(self, service):
        """Test hypervolume calculation with empty frontier."""
        solutions = []
        frontier_indices = []

        hypervolume = service._calculate_hypervolume(solutions, frontier_indices)

        assert hypervolume is None

    def test_calculate_hypervolume_with_solutions(self, service):
        """Test hypervolume calculation with valid solutions."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"obj1": 0.1, "obj2": 0.9},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
            ParetoSolution(
                solution_id=1,
                objective_values={"obj1": 0.9, "obj2": 0.1},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]
        frontier_indices = [0, 1]

        hypervolume = service._calculate_hypervolume(solutions, frontier_indices)

        # Should return a positive value
        assert hypervolume is not None
        assert hypervolume > 0

    def test_calculate_hypervolume_exception_handling(self, service):
        """Test hypervolume calculation handles exceptions gracefully."""
        solutions = [
            ParetoSolution(
                solution_id=0,
                objective_values={"obj1": float("inf"), "obj2": 0.1},
                decision_variables={},
                is_feasible=True,
                constraint_violations=[],
            ),
        ]
        frontier_indices = [0]

        # Should handle invalid values gracefully
        hypervolume = service._calculate_hypervolume(solutions, frontier_indices)

        # Should return None on exception or 0.0 if HV handles inf values
        assert hypervolume is None or hypervolume == 0.0

    def test_person_to_dict(self, service, mock_persons):
        """Test _person_to_dict conversion."""
        person = mock_persons[0]
        person_dict = service._person_to_dict(person)

        assert person_dict["id"] == str(person.id)
        assert person_dict["name"] == person.name
        assert person_dict["pgy_level"] == person.pgy_level
        assert "preferred_rotation_types" in person_dict

    def test_block_to_dict(self, service, mock_blocks):
        """Test _block_to_dict conversion."""
        block = mock_blocks[0]
        block_dict = service._block_to_dict(block)

        assert block_dict["id"] == str(block.id)
        assert block_dict["name"] == block.name
        assert block_dict["rotation_type"] == block.rotation_type
        assert block_dict["specialty"] == block.specialty

    def test_extract_solutions_no_results(self, service, mock_persons, mock_blocks):
        """Test _extract_solutions with no results."""
        mock_result = Mock()
        mock_result.X = None
        mock_result.F = None

        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
        ]

        solutions = service._extract_solutions(
            mock_result, mock_persons, mock_blocks, objectives
        )

        assert len(solutions) == 0

    def test_extract_solutions_single_solution(
        self, service, mock_persons, mock_blocks
    ):
        """Test _extract_solutions with single solution."""
        mock_result = Mock()
        # Single solution (1D array)
        mock_result.X = np.array([0.9, 0.1, 0.8, 0.2, 0.7] * 3)
        mock_result.F = np.array([0.1, -0.9])

        objectives = [
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
        ]

        solutions = service._extract_solutions(
            mock_result, mock_persons, mock_blocks, objectives
        )

        assert len(solutions) == 1
        assert solutions[0].solution_id == 0
        assert "fairness" in solutions[0].objective_values
        assert "coverage" in solutions[0].objective_values
        # Coverage is maximized, so -0.9 becomes 0.9
        assert solutions[0].objective_values["coverage"] == pytest.approx(0.9)

    def test_extract_solutions_multiple_solutions(
        self, service, mock_persons, mock_blocks
    ):
        """Test _extract_solutions with multiple solutions."""
        mock_result = Mock()
        # Multiple solutions (2D array)
        n_vars = len(mock_persons) * len(mock_blocks)
        mock_result.X = np.random.rand(3, n_vars)
        mock_result.F = np.array([[0.1, -0.9], [0.2, -0.8], [0.3, -0.7]])

        objectives = [
            ParetoObjective(name=ObjectiveName.FAIRNESS, weight=1.0),
            ParetoObjective(name=ObjectiveName.COVERAGE, weight=1.0),
        ]

        solutions = service._extract_solutions(
            mock_result, mock_persons, mock_blocks, objectives
        )

        assert len(solutions) == 3
        assert all(sol.is_feasible for sol in solutions)

    def test_get_persons_with_filter(self, service, mock_persons):
        """Test _get_persons with person_ids filter."""
        service.person_repo.get_by_id = Mock(return_value=mock_persons[0])

        person_ids = [mock_persons[0].id]
        persons = service._get_persons(person_ids)

        service.person_repo.get_by_id.assert_called_with(mock_persons[0].id)
        assert len(persons) == 1

    def test_get_persons_without_filter(self, service, mock_persons):
        """Test _get_persons without filter."""
        service.person_repo.list_all = Mock(return_value=mock_persons)

        persons = service._get_persons(None)

        service.person_repo.list_all.assert_called_once()
        assert len(persons) == 3

    def test_get_blocks_with_filter(self, service, mock_blocks):
        """Test _get_blocks with block_ids filter."""
        service.block_repo.get_by_id = Mock(return_value=mock_blocks[0])

        block_ids = [mock_blocks[0].id]
        blocks = service._get_blocks(block_ids)

        service.block_repo.get_by_id.assert_called_with(mock_blocks[0].id)
        assert len(blocks) == 1

    def test_get_blocks_without_filter(self, service, mock_blocks):
        """Test _get_blocks without filter."""
        service.block_repo.list_all = Mock(return_value=mock_blocks)

        blocks = service._get_blocks(None)

        service.block_repo.list_all.assert_called_once()
        assert len(blocks) == 5
