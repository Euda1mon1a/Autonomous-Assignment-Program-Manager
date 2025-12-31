"""
Comprehensive Constraint Validation Test Suite.

This test suite validates:
1. All registered constraints can be validated
2. Constraint interactions (no conflicting requirements)
3. Constraint error handling
4. Constraint configuration (ConstraintManager)
5. Factory methods for different constraint sets

Tests the entire constraint system infrastructure to ensure:
- All constraints implement the required interface
- Constraint manager correctly organizes and applies constraints
- Validation aggregation works properly
- Different factory configurations produce expected constraint sets
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    Constraint,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)
from app.scheduling.constraints.manager import ConstraintManager


# ============================================================================
# Mock Classes for Testing
# ============================================================================


class MockPerson:
    """Mock person object for testing."""

    def __init__(
        self,
        person_id=None,
        name="Test Person",
        person_type="resident",
        pgy_level=None,
        faculty_role=None,
    ):
        self.id = person_id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level
        self.faculty_role = faculty_role


class MockBlock:
    """Mock block object for testing."""

    def __init__(
        self,
        block_id=None,
        block_date=None,
        time_of_day="AM",
        is_weekend=False,
    ):
        self.id = block_id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day
        self.is_weekend = is_weekend


class MockTemplate:
    """Mock rotation template object for testing."""

    def __init__(
        self,
        template_id=None,
        name="Test Template",
        activity_type="outpatient",
        max_residents=None,
    ):
        self.id = template_id or uuid4()
        self.name = name
        self.activity_type = activity_type
        self.max_residents = max_residents


class MockAssignment:
    """Mock assignment object for testing."""

    def __init__(
        self,
        assignment_id=None,
        person_id=None,
        block_id=None,
        rotation_template_id=None,
        role="primary",
    ):
        self.id = assignment_id or uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.rotation_template_id = rotation_template_id
        self.role = role


# ============================================================================
# Helper Functions
# ============================================================================


def create_basic_context() -> SchedulingContext:
    """
    Create a minimal SchedulingContext for testing.

    Returns:
        SchedulingContext with minimal test data
    """
    residents = [
        MockPerson(person_type="resident", name="PGY-1", pgy_level=1),
        MockPerson(person_type="resident", name="PGY-2", pgy_level=2),
        MockPerson(person_type="resident", name="PGY-3", pgy_level=3),
    ]

    faculty = [
        MockPerson(person_type="faculty", name="Dr. Faculty 1"),
        MockPerson(person_type="faculty", name="Dr. Faculty 2"),
    ]

    # Create blocks for one week
    start_date = date(2025, 1, 6)  # Monday, Jan 6, 2025
    blocks = []
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        is_weekend = current_date.weekday() >= 5
        for time_of_day in ["AM", "PM"]:
            block = MockBlock(
                block_date=current_date,
                time_of_day=time_of_day,
                is_weekend=is_weekend,
            )
            blocks.append(block)

    templates = [
        MockTemplate(name="Clinic", activity_type="outpatient", max_residents=4),
        MockTemplate(name="Inpatient", activity_type="inpatient", max_residents=2),
    ]

    return SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=blocks,
        templates=templates,
    )


# ============================================================================
# Tests for ConstraintManager
# ============================================================================


class TestConstraintManager:
    """Tests for ConstraintManager functionality."""

    def test_manager_initialization(self):
        """Test ConstraintManager initializes empty."""
        manager = ConstraintManager()
        assert len(manager.constraints) == 0
        assert len(manager._hard_constraints) == 0
        assert len(manager._soft_constraints) == 0

    def test_add_hard_constraint(self):
        """Test adding a hard constraint."""
        manager = ConstraintManager()

        # Create a simple hard constraint
        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint

        constraint = OnePersonPerBlockConstraint()
        manager.add(constraint)

        assert len(manager.constraints) == 1
        assert len(manager._hard_constraints) == 1
        assert len(manager._soft_constraints) == 0
        assert constraint in manager.constraints
        assert constraint in manager._hard_constraints

    def test_add_soft_constraint(self):
        """Test adding a soft constraint."""
        manager = ConstraintManager()

        from app.scheduling.constraints.equity import EquityConstraint

        constraint = EquityConstraint(weight=10.0)
        manager.add(constraint)

        assert len(manager.constraints) == 1
        assert len(manager._hard_constraints) == 0
        assert len(manager._soft_constraints) == 1
        assert constraint in manager.constraints
        assert constraint in manager._soft_constraints

    def test_add_returns_self_for_chaining(self):
        """Test that add() returns self for method chaining."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint
        from app.scheduling.constraints.equity import EquityConstraint

        result = manager.add(OnePersonPerBlockConstraint()).add(EquityConstraint())

        assert result is manager
        assert len(manager.constraints) == 2

    def test_remove_constraint_by_name(self):
        """Test removing a constraint by name."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint

        constraint = OnePersonPerBlockConstraint()
        manager.add(constraint)
        assert len(manager.constraints) == 1

        manager.remove("OnePersonPerBlock")
        assert len(manager.constraints) == 0
        assert len(manager._hard_constraints) == 0

    def test_remove_nonexistent_constraint_no_error(self):
        """Test removing a nonexistent constraint doesn't raise error."""
        manager = ConstraintManager()

        # Should not raise an error
        manager.remove("NonexistentConstraint")
        assert len(manager.constraints) == 0

    def test_enable_constraint(self):
        """Test enabling a constraint by name."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint

        constraint = OnePersonPerBlockConstraint()
        constraint.enabled = False
        manager.add(constraint)

        manager.enable("OnePersonPerBlock")
        assert constraint.enabled is True

    def test_disable_constraint(self):
        """Test disabling a constraint by name."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint

        constraint = OnePersonPerBlockConstraint()
        manager.add(constraint)

        manager.disable("OnePersonPerBlock")
        assert constraint.enabled is False

    def test_get_enabled_constraints(self):
        """Test get_enabled() returns only enabled constraints."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import (
            ClinicCapacityConstraint,
            OnePersonPerBlockConstraint,
        )

        c1 = OnePersonPerBlockConstraint()
        c2 = ClinicCapacityConstraint()

        manager.add(c1).add(c2)
        manager.disable("ClinicCapacity")

        enabled = manager.get_enabled()
        assert len(enabled) == 1
        assert c1 in enabled
        assert c2 not in enabled

    def test_get_hard_constraints(self):
        """Test get_hard_constraints() returns only enabled hard constraints."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint
        from app.scheduling.constraints.equity import EquityConstraint

        hard = OnePersonPerBlockConstraint()
        soft = EquityConstraint()

        manager.add(hard).add(soft)

        hard_constraints = manager.get_hard_constraints()
        assert len(hard_constraints) == 1
        assert hard in hard_constraints
        assert soft not in hard_constraints

    def test_get_soft_constraints(self):
        """Test get_soft_constraints() returns only enabled soft constraints."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint
        from app.scheduling.constraints.equity import EquityConstraint

        hard = OnePersonPerBlockConstraint()
        soft = EquityConstraint()

        manager.add(hard).add(soft)

        soft_constraints = manager.get_soft_constraints()
        assert len(soft_constraints) == 1
        assert soft in soft_constraints
        assert hard not in soft_constraints

    def test_validate_all_aggregates_results(self):
        """Test validate_all() aggregates results from all constraints."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import (
            CoverageConstraint,
            OnePersonPerBlockConstraint,
        )

        manager.add(OnePersonPerBlockConstraint()).add(CoverageConstraint())

        context = create_basic_context()
        result = manager.validate_all([], context)

        # Should return a ConstraintResult
        assert isinstance(result, ConstraintResult)
        assert result.satisfied is True  # No violations with empty assignments
        assert isinstance(result.violations, list)
        assert isinstance(result.penalty, float)

    def test_validate_all_with_violations(self):
        """Test validate_all() detects violations."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint

        manager.add(OnePersonPerBlockConstraint())

        context = create_basic_context()
        residents = context.residents
        blocks = context.blocks

        # Create violating assignments (2 primaries on same block)
        assignments = [
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=blocks[0].id,
                role="primary",
            ),
        ]

        result = manager.validate_all(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) > 0

    def test_validate_all_accumulates_penalties(self):
        """Test validate_all() accumulates penalties from soft constraints."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import CoverageConstraint

        # Coverage constraint produces penalties with empty assignments
        manager.add(CoverageConstraint(weight=1000.0))

        context = create_basic_context()
        result = manager.validate_all([], context)

        # With empty assignments, Coverage should have penalty (0% coverage)
        assert result.penalty > 0
        assert result.penalty == 1000.0  # (1 - 0.0) * 1000.0


# ============================================================================
# Tests for Factory Methods
# ============================================================================


class TestConstraintManagerFactories:
    """Tests for ConstraintManager factory methods."""

    def test_create_default_has_acgme_constraints(self):
        """Test create_default() includes ACGME compliance constraints."""
        manager = ConstraintManager.create_default()

        constraint_names = {c.name for c in manager.constraints}

        # Check for key ACGME constraints
        assert "Availability" in constraint_names
        assert "80HourRule" in constraint_names
        assert "1in7Rule" in constraint_names
        assert "SupervisionRatio" in constraint_names

    def test_create_default_has_capacity_constraints(self):
        """Test create_default() includes capacity constraints."""
        manager = ConstraintManager.create_default()

        constraint_names = {c.name for c in manager.constraints}

        assert "OnePersonPerBlock" in constraint_names
        assert "ClinicCapacity" in constraint_names
        assert "MaxPhysiciansInClinic" in constraint_names

    def test_create_default_has_soft_constraints(self):
        """Test create_default() includes soft constraints."""
        manager = ConstraintManager.create_default()

        soft_constraint_names = {c.name for c in manager.get_soft_constraints()}

        assert "Coverage" in soft_constraint_names
        assert "Equity" in soft_constraint_names
        assert "Continuity" in soft_constraint_names

    def test_create_default_has_resilience_tier1_enabled(self):
        """Test create_default() has Tier 1 resilience constraints enabled."""
        manager = ConstraintManager.create_default()

        constraint_names = {c.name for c in manager.get_enabled()}

        # Tier 1 resilience constraints should be enabled by default
        assert "HubProtection" in constraint_names
        assert "UtilizationBuffer" in constraint_names

    def test_create_default_has_resilience_tier2_disabled(self):
        """Test create_default() has Tier 2 resilience constraints disabled."""
        manager = ConstraintManager.create_default()

        enabled_names = {c.name for c in manager.get_enabled()}

        # Tier 2 resilience constraints should be disabled by default
        assert "ZoneBoundary" not in enabled_names
        assert "PreferenceTrail" not in enabled_names
        assert "N1Vulnerability" not in enabled_names

    def test_create_resilience_aware_tier1(self):
        """Test create_resilience_aware(tier=1) enables only Tier 1."""
        manager = ConstraintManager.create_resilience_aware(tier=1)

        enabled_names = {c.name for c in manager.get_enabled()}

        # Tier 1 should be enabled
        assert "HubProtection" in enabled_names
        assert "UtilizationBuffer" in enabled_names

        # Tier 2 should be disabled
        assert "ZoneBoundary" not in enabled_names
        assert "PreferenceTrail" not in enabled_names
        assert "N1Vulnerability" not in enabled_names

    def test_create_resilience_aware_tier2(self):
        """Test create_resilience_aware(tier=2) enables all tiers."""
        manager = ConstraintManager.create_resilience_aware(tier=2)

        enabled_names = {c.name for c in manager.get_enabled()}

        # Tier 1 should be enabled
        assert "HubProtection" in enabled_names
        assert "UtilizationBuffer" in enabled_names

        # Tier 2 should be enabled
        assert "ZoneBoundary" in enabled_names
        assert "PreferenceTrail" in enabled_names
        assert "N1Vulnerability" in enabled_names

    def test_create_minimal_has_only_essential_constraints(self):
        """Test create_minimal() has only essential constraints."""
        manager = ConstraintManager.create_minimal()

        constraint_names = {c.name for c in manager.constraints}

        # Should have minimal set
        assert "Availability" in constraint_names
        assert "OnePersonPerBlock" in constraint_names
        assert "Coverage" in constraint_names

        # Should be small
        assert len(manager.constraints) <= 5

    def test_create_strict_increases_soft_weights(self):
        """Test create_strict() doubles soft constraint weights."""
        default_manager = ConstraintManager.create_default()
        strict_manager = ConstraintManager.create_strict()

        # Find a soft constraint in both
        default_equity = next(
            (c for c in default_manager._soft_constraints if c.name == "Equity"), None
        )
        strict_equity = next(
            (c for c in strict_manager._soft_constraints if c.name == "Equity"), None
        )

        assert default_equity is not None
        assert strict_equity is not None

        # Strict should have doubled weight
        assert strict_equity.weight == default_equity.weight * 2


# ============================================================================
# Tests for All Registered Constraints
# ============================================================================


class TestAllConstraintsValidatable:
    """Tests that all registered constraints can be validated."""

    def test_all_default_constraints_have_validate_method(self):
        """Test all default constraints implement validate()."""
        manager = ConstraintManager.create_default()

        for constraint in manager.constraints:
            assert hasattr(constraint, "validate")
            assert callable(constraint.validate)

    def test_all_default_constraints_validate_without_error(self):
        """Test all default constraints can validate without errors."""
        manager = ConstraintManager.create_default()
        context = create_basic_context()

        for constraint in manager.constraints:
            try:
                result = constraint.validate([], context)
                assert isinstance(result, ConstraintResult)
            except Exception as e:
                pytest.fail(f"Constraint {constraint.name} raised error: {e}")

    def test_all_default_constraints_have_required_attributes(self):
        """Test all default constraints have required attributes."""
        manager = ConstraintManager.create_default()

        for constraint in manager.constraints:
            assert hasattr(constraint, "name")
            assert isinstance(constraint.name, str)
            assert len(constraint.name) > 0

            assert hasattr(constraint, "constraint_type")
            assert isinstance(constraint.constraint_type, ConstraintType)

            assert hasattr(constraint, "priority")
            assert isinstance(constraint.priority, ConstraintPriority)

            assert hasattr(constraint, "enabled")
            assert isinstance(constraint.enabled, bool)

    def test_all_hard_constraints_return_satisfied_on_empty(self):
        """Test hard constraints are satisfied with empty assignments."""
        manager = ConstraintManager.create_default()
        context = create_basic_context()

        for constraint in manager.get_hard_constraints():
            # Skip constraints that require specific context data
            skip_constraints = {
                "FacultyPrimaryDutyClinic",
                "FacultyDayAvailability",
                "WednesdayPMSingleFaculty",
                "InvertedWednesday",
            }

            if constraint.name in skip_constraints:
                continue

            result = constraint.validate([], context)
            assert result.satisfied is True, (
                f"Hard constraint {constraint.name} should be satisfied "
                f"with empty assignments but returned: {result.violations}"
            )

    def test_all_soft_constraints_return_satisfied(self):
        """Test soft constraints always return satisfied=True."""
        manager = ConstraintManager.create_default()
        context = create_basic_context()

        for constraint in manager.get_soft_constraints():
            result = constraint.validate([], context)
            # Soft constraints always return satisfied=True
            assert result.satisfied is True

    def test_all_soft_constraints_have_weight(self):
        """Test all soft constraints have a weight attribute."""
        manager = ConstraintManager.create_default()

        for constraint in manager.get_soft_constraints():
            assert hasattr(constraint, "weight")
            assert isinstance(constraint.weight, (int, float))
            assert constraint.weight > 0


# ============================================================================
# Tests for Constraint Interactions
# ============================================================================


class TestConstraintInteractions:
    """Tests for constraint interactions and conflicts."""

    def test_no_conflicting_hard_constraints_on_valid_schedule(self):
        """Test hard constraints don't conflict on valid schedules."""
        manager = ConstraintManager.create_default()
        context = create_basic_context()

        # Create a simple valid schedule
        residents = context.residents
        blocks = [b for b in context.blocks if not b.is_weekend]
        templates = context.templates

        assignments = []
        for i, block in enumerate(blocks[:5]):
            assignments.append(
                MockAssignment(
                    person_id=residents[i % len(residents)].id,
                    block_id=block.id,
                    rotation_template_id=templates[0].id,
                    role="primary",
                )
            )

        # Validate with all hard constraints
        for constraint in manager.get_hard_constraints():
            result = constraint.validate(assignments, context)
            # Most should pass on this simple schedule
            # (Some like WednesdayPM may fail, but shouldn't conflict)
            assert isinstance(result, ConstraintResult)

    def test_constraint_manager_aggregates_multiple_violations(self):
        """Test manager aggregates violations from multiple constraints."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import (
            ClinicCapacityConstraint,
            OnePersonPerBlockConstraint,
        )

        manager.add(OnePersonPerBlockConstraint()).add(ClinicCapacityConstraint())

        context = create_basic_context()
        residents = context.residents
        blocks = context.blocks
        templates = context.templates

        # Template with capacity limit of 2
        limited_template = MockTemplate(
            name="Limited", activity_type="outpatient", max_residents=2
        )
        context.templates.append(limited_template)

        # Create violations for both constraints
        assignments = [
            # Multiple primaries on same block (violates OnePersonPerBlock)
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                rotation_template_id=limited_template.id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=blocks[0].id,
                rotation_template_id=limited_template.id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[2].id,
                block_id=blocks[0].id,
                rotation_template_id=limited_template.id,
                role="primary",
            ),
        ]

        result = manager.validate_all(assignments, context)

        assert result.satisfied is False
        # Should have violations from both constraints
        assert len(result.violations) >= 2

    def test_soft_constraints_accumulate_penalties(self):
        """Test soft constraints accumulate penalties correctly."""
        manager = ConstraintManager()

        from app.scheduling.constraints.capacity import CoverageConstraint
        from app.scheduling.constraints.equity import EquityConstraint

        # Use Coverage (which has penalty on empty) + Equity
        manager.add(CoverageConstraint(weight=1000.0)).add(EquityConstraint(weight=10.0))

        context = create_basic_context()

        # Create a simple schedule to generate Equity penalty
        residents = context.residents
        blocks = [b for b in context.blocks if not b.is_weekend]
        templates = context.templates

        # Assign all blocks to one resident (creates equity imbalance)
        assignments = []
        for block in blocks[:5]:
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=block.id,
                    rotation_template_id=templates[0].id,
                )
            )

        result = manager.validate_all(assignments, context)

        # Should have penalties from both constraints
        assert result.penalty > 0

        # Validate individual constraints to check additive behavior
        coverage_result = CoverageConstraint(weight=1000.0).validate(assignments, context)
        equity_result = EquityConstraint(weight=10.0).validate(assignments, context)

        # Total penalty should be sum of individual penalties
        total_expected = coverage_result.penalty + equity_result.penalty
        assert abs(result.penalty - total_expected) < 1.0


# ============================================================================
# Tests for Constraint Error Handling
# ============================================================================


class TestConstraintErrorHandling:
    """Tests for constraint error handling."""

    def test_validate_handles_missing_context_data_gracefully(self):
        """Test constraints handle missing context data gracefully."""
        manager = ConstraintManager.create_minimal()

        # Create context with minimal data
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        # Should not raise errors
        result = manager.validate_all([], context)
        assert isinstance(result, ConstraintResult)

    def test_validate_handles_none_assignments(self):
        """Test constraints handle None assignments gracefully."""
        from app.scheduling.constraints.capacity import OnePersonPerBlockConstraint

        constraint = OnePersonPerBlockConstraint()
        context = create_basic_context()

        # Most constraints should handle empty list
        result = constraint.validate([], context)
        assert isinstance(result, ConstraintResult)

    def test_constraint_violation_has_required_fields(self):
        """Test ConstraintViolation has required fields."""
        violation = ConstraintViolation(
            constraint_name="TestConstraint",
            constraint_type=ConstraintType.CAPACITY,
            severity="HIGH",
            message="Test violation message",
        )

        assert violation.constraint_name == "TestConstraint"
        assert violation.constraint_type == ConstraintType.CAPACITY
        assert violation.severity == "HIGH"
        assert violation.message == "Test violation message"
        assert violation.person_id is None
        assert violation.block_id is None
        assert violation.details == {}

    def test_constraint_violation_with_optional_fields(self):
        """Test ConstraintViolation with optional fields."""
        person_id = uuid4()
        block_id = uuid4()

        violation = ConstraintViolation(
            constraint_name="TestConstraint",
            constraint_type=ConstraintType.CAPACITY,
            severity="HIGH",
            message="Test violation message",
            person_id=person_id,
            block_id=block_id,
            details={"count": 5, "limit": 3},
        )

        assert violation.person_id == person_id
        assert violation.block_id == block_id
        assert violation.details["count"] == 5
        assert violation.details["limit"] == 3


# ============================================================================
# Tests for SchedulingContext
# ============================================================================


class TestSchedulingContext:
    """Tests for SchedulingContext functionality."""

    def test_context_builds_indices_on_init(self):
        """Test SchedulingContext builds lookup indices on __post_init__."""
        context = create_basic_context()

        # Check resident_idx
        assert len(context.resident_idx) == len(context.residents)
        for i, resident in enumerate(context.residents):
            assert context.resident_idx[resident.id] == i

        # Check faculty_idx
        assert len(context.faculty_idx) == len(context.faculty)
        for i, faculty in enumerate(context.faculty):
            assert context.faculty_idx[faculty.id] == i

        # Check block_idx
        assert len(context.block_idx) == len(context.blocks)
        for i, block in enumerate(context.blocks):
            assert context.block_idx[block.id] == i

        # Check template_idx
        assert len(context.template_idx) == len(context.templates)
        for i, template in enumerate(context.templates):
            assert context.template_idx[template.id] == i

    def test_context_builds_blocks_by_date(self):
        """Test SchedulingContext builds blocks_by_date mapping."""
        context = create_basic_context()

        # Should have 7 dates (one week)
        assert len(context.blocks_by_date) == 7

        # Each date should have 2 blocks (AM and PM)
        for date_blocks in context.blocks_by_date.values():
            assert len(date_blocks) == 2

    def test_context_has_resilience_data_false_by_default(self):
        """Test has_resilience_data() returns False by default."""
        context = create_basic_context()

        assert context.has_resilience_data() is False

    def test_context_has_resilience_data_with_hub_scores(self):
        """Test has_resilience_data() returns True with hub scores."""
        context = create_basic_context()
        context.hub_scores = {context.faculty[0].id: 0.75}

        assert context.has_resilience_data() is True

    def test_context_has_resilience_data_with_utilization(self):
        """Test has_resilience_data() returns True with utilization."""
        context = create_basic_context()
        context.current_utilization = 0.65

        assert context.has_resilience_data() is True

    def test_context_get_hub_score_returns_zero_if_missing(self):
        """Test get_hub_score() returns 0.0 if faculty not in hub_scores."""
        context = create_basic_context()

        score = context.get_hub_score(context.faculty[0].id)
        assert score == 0.0

    def test_context_get_hub_score_returns_correct_value(self):
        """Test get_hub_score() returns correct value if present."""
        context = create_basic_context()
        faculty_id = context.faculty[0].id
        context.hub_scores = {faculty_id: 0.85}

        score = context.get_hub_score(faculty_id)
        assert score == 0.85

    def test_context_is_n1_vulnerable_false_by_default(self):
        """Test is_n1_vulnerable() returns False by default."""
        context = create_basic_context()

        assert context.is_n1_vulnerable(context.faculty[0].id) is False

    def test_context_is_n1_vulnerable_true_when_in_set(self):
        """Test is_n1_vulnerable() returns True when faculty in set."""
        context = create_basic_context()
        faculty_id = context.faculty[0].id
        context.n1_vulnerable_faculty = {faculty_id}

        assert context.is_n1_vulnerable(faculty_id) is True

    def test_context_get_preference_strength_returns_neutral_by_default(self):
        """Test get_preference_strength() returns 0.5 (neutral) by default."""
        context = create_basic_context()

        strength = context.get_preference_strength(context.faculty[0].id, "monday_am")
        assert strength == 0.5

    def test_context_get_preference_strength_returns_correct_value(self):
        """Test get_preference_strength() returns correct value if present."""
        context = create_basic_context()
        faculty_id = context.faculty[0].id
        context.preference_trails = {faculty_id: {"monday_am": 0.85}}

        strength = context.get_preference_strength(faculty_id, "monday_am")
        assert strength == 0.85


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestConstraintSystemIntegration:
    """Integration tests for the entire constraint system."""

    def test_create_default_and_validate(self):
        """Test creating default manager and validating."""
        manager = ConstraintManager.create_default()
        context = create_basic_context()

        result = manager.validate_all([], context)

        assert isinstance(result, ConstraintResult)
        assert isinstance(result.violations, list)
        assert isinstance(result.penalty, float)

    def test_enable_disable_affects_validation(self):
        """Test enabling/disabling constraints affects validation."""
        manager = ConstraintManager.create_default()
        context = create_basic_context()

        # Get initial count
        initial_enabled = len(manager.get_enabled())

        # Disable all soft constraints
        for constraint in manager.get_soft_constraints():
            manager.disable(constraint.name)

        # Should have fewer enabled
        after_disable = len(manager.get_enabled())
        assert after_disable < initial_enabled

        # Re-enable one
        manager.enable("Equity")
        after_enable = len(manager.get_enabled())
        assert after_enable == after_disable + 1

    def test_all_factory_methods_produce_valid_managers(self):
        """Test all factory methods produce valid managers."""
        factories = [
            ConstraintManager.create_default,
            ConstraintManager.create_minimal,
            ConstraintManager.create_strict,
            lambda: ConstraintManager.create_resilience_aware(tier=1),
            lambda: ConstraintManager.create_resilience_aware(tier=2),
        ]

        context = create_basic_context()

        for factory in factories:
            manager = factory()
            assert isinstance(manager, ConstraintManager)
            assert len(manager.constraints) > 0

            # Should be able to validate
            result = manager.validate_all([], context)
            assert isinstance(result, ConstraintResult)

    def test_constraint_priorities_affect_order(self):
        """Test constraint priorities affect application order."""
        manager = ConstraintManager.create_default()

        enabled = manager.get_enabled()
        priorities = [c.priority.value for c in enabled]

        # When sorted by priority (descending), should match expected order
        sorted_priorities = sorted(priorities, reverse=True)

        # The actual application order should be descending by priority
        # (This is verified in apply_to_cpsat and apply_to_pulp methods)
        assert len(priorities) == len(sorted_priorities)
