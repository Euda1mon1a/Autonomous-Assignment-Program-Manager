"""
Tests for the modular constraint system.

Tests cover:
- Individual constraint validation
- ConstraintManager composition
- Solver integration
"""
import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import MagicMock

from app.scheduling.constraints import (
    ConstraintManager,
    SchedulingContext,
    ConstraintResult,
    ConstraintViolation,
    ConstraintPriority,
    ConstraintType,
    # Hard constraints
    AvailabilityConstraint,
    OnePersonPerBlockConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
    ClinicCapacityConstraint,
    # Soft constraints
    EquityConstraint,
    CoverageConstraint,
    ContinuityConstraint,
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


class MockAssignment:
    """Mock assignment for testing."""
    def __init__(self, person_id, block_id, role="primary", rotation_template_id=None):
        self.id = uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.role = role
        self.rotation_template_id = rotation_template_id


class MockTemplate:
    """Mock rotation template for testing."""
    def __init__(self, id=None, name="Test Rotation", max_residents=None, requires_procedure_credential=False):
        self.id = id or uuid4()
        self.name = name
        self.max_residents = max_residents
        self.requires_procedure_credential = requires_procedure_credential


@pytest.fixture
def sample_context():
    """Create a sample scheduling context for testing."""
    residents = [
        MockPerson(name="Resident 1", pgy_level=1),
        MockPerson(name="Resident 2", pgy_level=2),
        MockPerson(name="Resident 3", pgy_level=3),
    ]
    faculty = [
        MockPerson(name="Faculty 1", person_type="faculty", pgy_level=None),
        MockPerson(name="Faculty 2", person_type="faculty", pgy_level=None),
    ]

    # Create blocks for a week
    start_date = date(2024, 1, 1)
    blocks = []
    for day_offset in range(7):
        block_date = start_date + timedelta(days=day_offset)
        is_weekend = block_date.weekday() >= 5
        for tod in ["AM", "PM"]:
            blocks.append(MockBlock(
                block_date=block_date,
                time_of_day=tod,
                is_weekend=is_weekend,
            ))

    templates = [MockTemplate(name="Clinic")]

    context = SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=blocks,
        templates=templates,
        start_date=start_date,
        end_date=start_date + timedelta(days=6),
    )

    # Set all residents as available
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
# Availability Constraint Tests
# ============================================================================

class TestAvailabilityConstraint:
    """Tests for AvailabilityConstraint."""

    def test_validate_all_available(self, sample_context):
        """Test validation when all assignments are during available periods."""
        constraint = AvailabilityConstraint()

        # Create valid assignments
        assignments = [
            MockAssignment(
                person_id=sample_context.residents[0].id,
                block_id=sample_context.blocks[0].id,
            )
        ]

        result = constraint.validate(assignments, sample_context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_unavailable_assignment(self, sample_context):
        """Test validation catches assignments during absence."""
        constraint = AvailabilityConstraint()

        # Mark resident as unavailable for first block
        resident = sample_context.residents[0]
        block = sample_context.blocks[0]
        sample_context.availability[resident.id][block.id] = {
            "available": False,
            "replacement": "Vacation",
        }

        # Create invalid assignment
        assignments = [
            MockAssignment(person_id=resident.id, block_id=block.id)
        ]

        result = constraint.validate(assignments, sample_context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"


# ============================================================================
# One Person Per Block Constraint Tests
# ============================================================================

class TestOnePersonPerBlockConstraint:
    """Tests for OnePersonPerBlockConstraint."""

    def test_validate_single_assignment(self, sample_context):
        """Test validation with single assignment per block."""
        constraint = OnePersonPerBlockConstraint()

        assignments = [
            MockAssignment(
                person_id=sample_context.residents[0].id,
                block_id=sample_context.blocks[0].id,
            )
        ]

        result = constraint.validate(assignments, sample_context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_assignments_same_block(self, sample_context):
        """Test validation catches multiple primary assignments."""
        constraint = OnePersonPerBlockConstraint()

        block_id = sample_context.blocks[0].id
        assignments = [
            MockAssignment(
                person_id=sample_context.residents[0].id,
                block_id=block_id,
                role="primary",
            ),
            MockAssignment(
                person_id=sample_context.residents[1].id,
                block_id=block_id,
                role="primary",
            ),
        ]

        result = constraint.validate(assignments, sample_context)

        assert result.satisfied is False
        assert len(result.violations) == 1


# ============================================================================
# 80-Hour Rule Constraint Tests
# ============================================================================

class TestEightyHourRuleConstraint:
    """Tests for EightyHourRuleConstraint."""

    def test_validate_under_limit(self, sample_context):
        """Test validation when hours are under limit."""
        constraint = EightyHourRuleConstraint()

        # Create a few assignments (well under 80 hours/week)
        assignments = [
            MockAssignment(
                person_id=sample_context.residents[0].id,
                block_id=sample_context.blocks[i].id,
            )
            for i in range(4)  # 4 blocks = 24 hours
        ]

        result = constraint.validate(assignments, sample_context)

        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# 1-in-7 Rule Constraint Tests
# ============================================================================

class TestOneInSevenRuleConstraint:
    """Tests for OneInSevenRuleConstraint."""

    def test_validate_with_day_off(self, sample_context):
        """Test validation when resident has days off."""
        constraint = OneInSevenRuleConstraint()

        # Create assignments for 5 days
        resident = sample_context.residents[0]
        workday_blocks = [b for b in sample_context.blocks if not b.is_weekend]

        # Assign to first 5 workdays only
        assignments = [
            MockAssignment(
                person_id=resident.id,
                block_id=workday_blocks[i].id,
            )
            for i in range(min(5, len(workday_blocks)))
        ]

        result = constraint.validate(assignments, sample_context)

        # With only 5 days of assignments in a week, should pass
        assert result.satisfied is True


# ============================================================================
# Supervision Ratio Constraint Tests
# ============================================================================

class TestSupervisionRatioConstraint:
    """Tests for SupervisionRatioConstraint."""

    def test_calculate_required_faculty(self):
        """Test faculty calculation for various resident counts."""
        constraint = SupervisionRatioConstraint()

        # 0 residents = 0 faculty
        assert constraint.calculate_required_faculty(0, 0) == 0

        # 1 PGY-1 = 1 faculty (1:2 ratio)
        assert constraint.calculate_required_faculty(1, 0) == 1

        # 2 PGY-1 = 1 faculty
        assert constraint.calculate_required_faculty(2, 0) == 1

        # 3 PGY-1 = 2 faculty
        assert constraint.calculate_required_faculty(3, 0) == 2

        # 4 PGY-2/3 = 1 faculty (1:4 ratio)
        assert constraint.calculate_required_faculty(0, 4) == 1

        # 5 PGY-2/3 = 2 faculty
        assert constraint.calculate_required_faculty(0, 5) == 2

        # Mixed: 2 PGY-1 + 4 PGY-2/3 = 1 + 1 = 2 faculty
        assert constraint.calculate_required_faculty(2, 4) == 2

    def test_validate_adequate_supervision(self, sample_context):
        """Test validation with adequate faculty supervision."""
        constraint = SupervisionRatioConstraint()

        block = sample_context.blocks[0]
        assignments = [
            # 1 PGY-1 resident
            MockAssignment(
                person_id=sample_context.residents[0].id,  # PGY-1
                block_id=block.id,
                role="primary",
            ),
            # 1 faculty
            MockAssignment(
                person_id=sample_context.faculty[0].id,
                block_id=block.id,
                role="supervising",
            ),
        ]

        result = constraint.validate(assignments, sample_context)

        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# Equity Constraint Tests
# ============================================================================

class TestEquityConstraint:
    """Tests for EquityConstraint (soft constraint)."""

    def test_validate_balanced_workload(self, sample_context):
        """Test validation with balanced assignments."""
        constraint = EquityConstraint()

        # Assign equally to all residents
        assignments = []
        for i, block in enumerate(sample_context.blocks[:6]):
            resident_idx = i % len(sample_context.residents)
            assignments.append(MockAssignment(
                person_id=sample_context.residents[resident_idx].id,
                block_id=block.id,
            ))

        result = constraint.validate(assignments, sample_context)

        # Soft constraint - always "satisfied" but may have penalty
        assert result.satisfied is True
        assert result.penalty >= 0

    def test_validate_imbalanced_workload(self, sample_context):
        """Test validation with imbalanced assignments."""
        constraint = EquityConstraint()

        # Assign all blocks to one resident
        resident = sample_context.residents[0]
        assignments = [
            MockAssignment(person_id=resident.id, block_id=block.id)
            for block in sample_context.blocks[:10]
        ]

        result = constraint.validate(assignments, sample_context)

        # Should have higher penalty for imbalance
        assert result.penalty > 0


# ============================================================================
# Coverage Constraint Tests
# ============================================================================

class TestCoverageConstraint:
    """Tests for CoverageConstraint (soft constraint)."""

    def test_validate_full_coverage(self, sample_context):
        """Test validation with full block coverage."""
        constraint = CoverageConstraint()

        workday_blocks = [b for b in sample_context.blocks if not b.is_weekend]
        assignments = [
            MockAssignment(
                person_id=sample_context.residents[i % len(sample_context.residents)].id,
                block_id=block.id,
            )
            for i, block in enumerate(workday_blocks)
        ]

        result = constraint.validate(assignments, sample_context)

        assert result.satisfied is True
        assert result.penalty == 0  # Full coverage = no penalty

    def test_validate_partial_coverage(self, sample_context):
        """Test validation with partial coverage."""
        constraint = CoverageConstraint()

        # Only assign to first 2 blocks
        assignments = [
            MockAssignment(
                person_id=sample_context.residents[0].id,
                block_id=sample_context.blocks[0].id,
            ),
            MockAssignment(
                person_id=sample_context.residents[1].id,
                block_id=sample_context.blocks[1].id,
            ),
        ]

        result = constraint.validate(assignments, sample_context)

        # Partial coverage = some penalty
        assert result.penalty > 0


# ============================================================================
# ConstraintManager Tests
# ============================================================================

class TestConstraintManager:
    """Tests for ConstraintManager composition."""

    def test_create_default_manager(self):
        """Test default constraint manager creation."""
        manager = ConstraintManager.create_default()

        # Should have hard and soft constraints
        assert len(manager.get_hard_constraints()) > 0
        assert len(manager.get_soft_constraints()) > 0
        assert len(manager.constraints) > 0

    def test_create_minimal_manager(self):
        """Test minimal constraint manager creation."""
        manager = ConstraintManager.create_minimal()

        # Should have fewer constraints
        assert len(manager.constraints) < len(ConstraintManager.create_default().constraints)

    def test_add_and_remove_constraints(self):
        """Test adding and removing constraints."""
        manager = ConstraintManager()

        constraint = AvailabilityConstraint()
        manager.add(constraint)

        assert len(manager.constraints) == 1

        manager.remove(constraint.name)

        assert len(manager.constraints) == 0

    def test_enable_disable_constraints(self):
        """Test enabling and disabling constraints."""
        manager = ConstraintManager()
        constraint = AvailabilityConstraint()
        manager.add(constraint)

        assert constraint.enabled is True

        manager.disable(constraint.name)
        assert constraint.enabled is False

        manager.enable(constraint.name)
        assert constraint.enabled is True

    def test_get_enabled_constraints(self):
        """Test getting only enabled constraints."""
        manager = ConstraintManager.create_default()

        enabled = manager.get_enabled()

        # All constraints should be enabled by default
        assert len(enabled) == len(manager.constraints)

        # Disable one
        manager.disable("Availability")
        enabled = manager.get_enabled()

        assert len(enabled) == len(manager.constraints) - 1

    def test_validate_all_constraints(self, sample_context):
        """Test validating all constraints at once."""
        manager = ConstraintManager.create_default()

        # Create some valid assignments
        assignments = [
            MockAssignment(
                person_id=sample_context.residents[0].id,
                block_id=sample_context.blocks[0].id,
            )
        ]

        result = manager.validate_all(assignments, sample_context)

        assert isinstance(result, ConstraintResult)
        assert isinstance(result.violations, list)


# ============================================================================
# Priority and Type Tests
# ============================================================================

class TestConstraintPriorityAndType:
    """Tests for constraint priority and type enums."""

    def test_priority_ordering(self):
        """Test that priorities have correct ordering."""
        assert ConstraintPriority.CRITICAL.value > ConstraintPriority.HIGH.value
        assert ConstraintPriority.HIGH.value > ConstraintPriority.MEDIUM.value
        assert ConstraintPriority.MEDIUM.value > ConstraintPriority.LOW.value

    def test_constraint_types_exist(self):
        """Test that all expected constraint types exist."""
        expected_types = [
            "availability",
            "duty_hours",
            "consecutive_days",
            "supervision",
            "capacity",
            "equity",
        ]

        for type_name in expected_types:
            assert hasattr(ConstraintType, type_name.upper())


# ============================================================================
# Integration Tests
# ============================================================================

class TestConstraintIntegration:
    """Integration tests for constraint system."""

    def test_full_validation_workflow(self, sample_context):
        """Test complete validation workflow."""
        manager = ConstraintManager.create_default()

        # Create a realistic set of assignments
        assignments = []
        workday_blocks = [b for b in sample_context.blocks if not b.is_weekend]

        for i, block in enumerate(workday_blocks):
            # Rotate through residents
            resident = sample_context.residents[i % len(sample_context.residents)]
            assignments.append(MockAssignment(
                person_id=resident.id,
                block_id=block.id,
                role="primary",
            ))

            # Add faculty supervision
            faculty = sample_context.faculty[i % len(sample_context.faculty)]
            assignments.append(MockAssignment(
                person_id=faculty.id,
                block_id=block.id,
                role="supervising",
            ))

        result = manager.validate_all(assignments, sample_context)

        assert isinstance(result, ConstraintResult)
        # The result should indicate validation status
        assert result.satisfied is not None
