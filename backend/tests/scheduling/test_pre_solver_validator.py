"""
Tests for Pre-Solver Constraint Saturation Validator.

Tests the validation logic that runs before solver execution to catch
obviously infeasible problems early.
"""

import uuid
from datetime import date, timedelta

import pytest

from app.scheduling.constraints import SchedulingContext
from app.scheduling.pre_solver_validator import (
    PreSolverValidationResult,
    PreSolverValidator,
)


# Mock objects for testing
class MockPerson:
    """Mock Person for testing."""

    def __init__(self, name: str = "Test Person", person_type: str = "resident"):
        self.id = uuid.uuid4()
        self.name = name
        self.type = person_type


class MockBlock:
    """Mock Block for testing."""

    def __init__(
        self,
        block_date: date,
        time_of_day: str = "AM",
        is_weekend: bool = False,
    ):
        self.id = uuid.uuid4()
        self.date = block_date
        self.time_of_day = time_of_day
        self.is_weekend = is_weekend


class MockTemplate:
    """Mock RotationTemplate for testing."""

    def __init__(self, name: str, activity_type: str = "outpatient"):
        self.id = uuid.uuid4()
        self.name = name
        self.activity_type = activity_type


class MockAssignment:
    """Mock Assignment for testing."""

    def __init__(self, person_id: uuid.UUID, block_id: uuid.UUID):
        self.id = uuid.uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.rotation_template_id = uuid.uuid4()


class TestPreSolverValidationResult:
    """Tests for PreSolverValidationResult dataclass."""

    def test_initialization_defaults(self):
        """Test that defaults are set correctly."""
        result = PreSolverValidationResult(feasible=True)

        assert result.feasible is True
        assert result.issues == []
        assert result.complexity_estimate == 0
        assert result.recommendations == []
        assert result.warnings == []
        assert result.statistics == {}

    def test_initialization_with_values(self):
        """Test initialization with custom values."""
        result = PreSolverValidationResult(
            feasible=False,
            issues=["Issue 1", "Issue 2"],
            complexity_estimate=50000,
            recommendations=["Fix issue 1"],
            warnings=["Warning 1"],
            statistics={"key": "value"},
        )

        assert result.feasible is False
        assert len(result.issues) == 2
        assert result.complexity_estimate == 50000
        assert len(result.recommendations) == 1
        assert len(result.warnings) == 1
        assert result.statistics["key"] == "value"

    def test_repr(self):
        """Test string representation."""
        result = PreSolverValidationResult(
            feasible=True,
            complexity_estimate=10000,
        )

        repr_str = repr(result)
        assert "FEASIBLE" in repr_str
        assert "10000" in repr_str

        result.feasible = False
        result.issues = ["Issue 1"]
        repr_str = repr(result)
        assert "INFEASIBLE" in repr_str
        assert "1 issues" in repr_str


class TestPreSolverValidator:
    """Tests for PreSolverValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return PreSolverValidator()

    @pytest.fixture
    def basic_context(self):
        """Create a basic valid scheduling context."""
        # Create 3 residents
        residents = [MockPerson(f"Resident {i}", "resident") for i in range(1, 4)]

        # Create 1 week of blocks (Mon-Fri, AM/PM = 10 blocks)
        base_date = date(2025, 1, 6)  # Monday
        blocks = []
        for day_offset in range(5):
            block_date = base_date + timedelta(days=day_offset)
            blocks.append(MockBlock(block_date, "AM", is_weekend=False))
            blocks.append(MockBlock(block_date, "PM", is_weekend=False))

        # Create 2 templates
        templates = [
            MockTemplate("Clinic", "outpatient"),
            MockTemplate("Procedures", "outpatient"),
        ]

        return SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=templates,
            start_date=base_date,
            end_date=base_date + timedelta(days=4),
        )

    def test_validate_empty_residents(self, validator):
        """Test validation fails when no residents."""
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[MockBlock(date(2025, 1, 1))],
            templates=[MockTemplate("Clinic")],
        )

        result = validator.validate_saturation(context)

        assert result.feasible is False
        assert any("No residents" in issue for issue in result.issues)
        assert len(result.recommendations) > 0

    def test_validate_empty_blocks(self, validator):
        """Test validation fails when no blocks."""
        context = SchedulingContext(
            residents=[MockPerson()],
            faculty=[],
            blocks=[],
            templates=[MockTemplate("Clinic")],
        )

        result = validator.validate_saturation(context)

        assert result.feasible is False
        assert any("No blocks" in issue for issue in result.issues)

    def test_validate_empty_templates(self, validator):
        """Test validation fails when no templates."""
        context = SchedulingContext(
            residents=[MockPerson()],
            faculty=[],
            blocks=[MockBlock(date(2025, 1, 1))],
            templates=[],
        )

        result = validator.validate_saturation(context)

        assert result.feasible is False
        assert any("No rotation templates" in issue for issue in result.issues)

    def test_validate_basic_feasible_problem(self, validator, basic_context):
        """Test that a basic feasible problem passes validation."""
        result = validator.validate_saturation(basic_context)

        assert result.feasible is True
        assert len(result.issues) == 0
        assert result.complexity_estimate > 0
        assert "num_residents" in result.statistics
        assert result.statistics["num_residents"] == 3

    def test_validate_insufficient_coverage(self, validator):
        """Test detection of insufficient personnel coverage."""
        # 1 resident, 10 blocks = can only cover 10 slots, but need 10
        # This is exactly at capacity (ratio = 1.0), which is below MIN_PERSONNEL_RATIO
        resident = MockPerson()
        base_date = date(2025, 1, 6)
        blocks = [
            MockBlock(base_date + timedelta(days=i), "AM", is_weekend=False)
            for i in range(10)
        ]

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[MockTemplate("Clinic")],
            start_date=base_date,
            end_date=base_date + timedelta(days=9),
        )

        result = validator.validate_saturation(context, min_coverage_per_block=1)

        # Should warn about tight coverage (ratio = 1.0 < 1.2)
        assert len(result.warnings) > 0
        assert any("Tight personnel coverage" in w for w in result.warnings)

    def test_validate_resident_with_no_availability(self, validator):
        """Test detection of residents with zero availability."""
        residents = [MockPerson("Available"), MockPerson("Unavailable")]
        base_date = date(2025, 1, 6)
        blocks = [MockBlock(base_date, "AM"), MockBlock(base_date, "PM")]

        # Mark second resident as completely unavailable
        availability = {
            residents[1].id: {
                blocks[0].id: {"available": False},
                blocks[1].id: {"available": False},
            }
        }

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[MockTemplate("Clinic")],
            availability=availability,
            start_date=base_date,
            end_date=base_date,
        )

        result = validator.validate_saturation(context)

        assert result.feasible is False
        assert any(
            "Unavailable" in issue and "zero availability" in issue
            for issue in result.issues
        )

    def test_validate_block_with_no_available_residents(self, validator):
        """Test detection of blocks with no available residents."""
        residents = [MockPerson(f"R{i}") for i in range(2)]
        base_date = date(2025, 1, 6)
        blocks = [MockBlock(base_date, "AM"), MockBlock(base_date, "PM")]

        # Mark all residents unavailable for the first block
        availability = {
            residents[0].id: {blocks[0].id: {"available": False}},
            residents[1].id: {blocks[0].id: {"available": False}},
        }

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[MockTemplate("Clinic")],
            availability=availability,
            start_date=base_date,
            end_date=base_date,
        )

        result = validator.validate_saturation(context)

        assert result.feasible is False
        assert any("has no available residents" in issue for issue in result.issues)

    def test_complexity_estimation_low(self, validator):
        """Test complexity estimation for small problems."""
        # 2 residents × 2 blocks × 1 template = 4 variables
        residents = [MockPerson(f"R{i}") for i in range(2)]
        blocks = [MockBlock(date(2025, 1, 6), "AM") for _ in range(2)]
        templates = [MockTemplate("Clinic")]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=templates,
        )

        result = validator.validate_saturation(context)

        assert result.statistics["complexity_level"] == "LOW"
        assert result.complexity_estimate < validator.COMPLEXITY_MEDIUM

    def test_complexity_estimation_high(self, validator):
        """Test complexity estimation for large problems."""
        # 20 residents × 100 blocks × 5 templates = 10,000 variables
        residents = [MockPerson(f"R{i}") for i in range(20)]
        base_date = date(2025, 1, 1)
        blocks = [
            MockBlock(base_date + timedelta(days=i // 2), "AM" if i % 2 == 0 else "PM")
            for i in range(100)
        ]
        templates = [MockTemplate(f"Template{i}") for i in range(5)]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=templates,
        )

        result = validator.validate_saturation(context)

        # Should be at least MEDIUM complexity
        assert result.complexity_estimate >= validator.COMPLEXITY_MEDIUM

    def test_existing_assignments_over_constrained(self, validator):
        """Test detection of over-constrained problems from existing assignments."""
        residents = [MockPerson()]
        base_date = date(2025, 1, 6)
        blocks = [MockBlock(base_date + timedelta(days=i), "AM") for i in range(5)]

        # Pre-assign 4 out of 5 blocks (80%)
        existing = [MockAssignment(residents[0].id, blocks[i].id) for i in range(4)]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[MockTemplate("Clinic")],
            existing_assignments=existing,
        )

        result = validator.validate_saturation(context)

        # Should warn about limited optimization room
        assert any("pre-assigned" in w for w in result.warnings)

    def test_estimate_complexity_method(self, validator):
        """Test the estimate_complexity helper method."""
        # Test various sizes
        assert validator.estimate_complexity(100, 50) == 5000
        assert validator.estimate_complexity(1000, 500) == 500000
        assert validator.estimate_complexity(0, 100) == 0

    def test_detect_conflicts_convenience_method(self, validator):
        """Test the detect_conflicts convenience method."""
        # Create infeasible context
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[MockBlock(date(2025, 1, 1))],
            templates=[MockTemplate("Clinic")],
        )

        conflicts = validator.detect_conflicts(context)

        assert len(conflicts) > 0
        assert isinstance(conflicts, list)
        assert all(isinstance(c, str) for c in conflicts)

    def test_statistics_gathering(self, validator, basic_context):
        """Test that statistics are properly gathered."""
        result = validator.validate_saturation(basic_context)

        stats = result.statistics
        assert "num_residents" in stats
        assert "num_blocks" in stats
        assert "num_workday_blocks" in stats
        assert "num_templates" in stats
        assert "availability_rate" in stats
        assert "complexity_level" in stats

        # Check values
        assert stats["num_residents"] == 3
        assert stats["num_workday_blocks"] == 10
        assert stats["num_templates"] == 2
        assert 0.0 <= stats["availability_rate"] <= 1.0

    def test_over_assignment_detection(self, validator):
        """Test detection of over-assignment scenarios."""
        # 1 resident needs to cover 20 blocks, but max is 90% = 18 blocks
        resident = MockPerson()
        base_date = date(2025, 1, 1)
        blocks = [
            MockBlock(base_date + timedelta(days=i // 2), "AM" if i % 2 == 0 else "PM")
            for i in range(20)
        ]

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=blocks,
            templates=[MockTemplate("Clinic")],
        )

        result = validator.validate_saturation(context, min_coverage_per_block=1)

        # Should detect over-assignment (1 resident × 20 blocks × 0.9 = 18, but need 20)
        assert any("Over-assignment" in issue for issue in result.issues)

    def test_recommendations_provided(self, validator):
        """Test that recommendations are provided for issues."""
        # Create infeasible scenario
        context = SchedulingContext(
            residents=[MockPerson()],
            faculty=[],
            blocks=[MockBlock(date(2025, 1, 1) + timedelta(days=i)) for i in range(30)],
            templates=[MockTemplate("Clinic")],
        )

        result = validator.validate_saturation(context, min_coverage_per_block=2)

        # Should have issues and recommendations
        if result.issues:
            assert len(result.recommendations) > 0

    def test_availability_with_partial_absences(self, validator):
        """Test handling of residents with partial availability."""
        residents = [MockPerson(f"R{i}") for i in range(3)]
        base_date = date(2025, 1, 6)
        blocks = [MockBlock(base_date + timedelta(days=i), "AM") for i in range(10)]

        # One resident available for only 20% of blocks
        availability = {
            residents[0].id: {
                blocks[i].id: {"available": False}
                for i in range(8)  # Unavailable for 8 out of 10
            }
        }

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[MockTemplate("Clinic")],
            availability=availability,
        )

        result = validator.validate_saturation(context)

        # Should warn about low availability
        assert any("only available for" in w for w in result.warnings)

    def test_weekend_blocks_excluded(self, validator):
        """Test that weekend blocks are properly excluded from calculations."""
        residents = [MockPerson()]
        base_date = date(2025, 1, 6)  # Monday
        blocks = [
            MockBlock(base_date, "AM", is_weekend=False),
            MockBlock(base_date + timedelta(days=1), "AM", is_weekend=False),
            MockBlock(base_date + timedelta(days=5), "AM", is_weekend=True),  # Saturday
            MockBlock(base_date + timedelta(days=6), "AM", is_weekend=True),  # Sunday
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[MockTemplate("Clinic")],
        )

        result = validator.validate_saturation(context)

        # Should only count 2 workday blocks
        assert result.statistics["num_workday_blocks"] == 2
        assert result.statistics["num_blocks"] == 4

    def test_hour_balance_warning(self, validator):
        """Test warning for residents with limited availability."""
        residents = [MockPerson("Limited Availability")]
        base_date = date(2025, 1, 6)
        blocks = [MockBlock(base_date + timedelta(days=i), "AM") for i in range(10)]

        # Resident only available for 30% of blocks (below 50% threshold)
        availability = {
            residents[0].id: {
                blocks[i].id: {"available": False}
                for i in range(7)  # Unavailable for 7 out of 10
            }
        }

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[MockTemplate("Clinic")],
            availability=availability,
        )

        result = validator.validate_saturation(context)

        # Should warn about low availability
        assert any(
            "only available for" in w and "absences may cause" in w
            for w in result.warnings
        )
