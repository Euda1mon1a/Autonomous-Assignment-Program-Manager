"""
Tests for call coverage constraints.

Tests the three call coverage constraints:
1. OvernightCallCoverageConstraint - Exactly one faculty per Sun-Thurs night
2. AdjunctCallExclusionConstraint - Prevent adjunct faculty from solver-generated call
3. CallAvailabilityConstraint - Prevent call when faculty unavailable
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.call_coverage import (
    OVERNIGHT_CALL_DAYS,
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
    OvernightCallCoverageConstraint,
)


# ============================================================================
# Mock Classes for Testing
# ============================================================================


class MockPerson:
    """Mock person object for testing."""

    def __init__(
        self,
        person_id=None,
        name="Test Person",
        person_type="faculty",
        faculty_role=None,
    ):
        self.id = person_id or uuid4()
        self.name = name
        self.type = person_type
        self.faculty_role = faculty_role


class MockBlock:
    """Mock block object for testing."""

    def __init__(self, block_id=None, block_date=None, time_of_day="AM"):
        self.id = block_id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day


class MockAssignment:
    """Mock assignment object for testing."""

    def __init__(
        self,
        assignment_id=None,
        person_id=None,
        block_id=None,
        call_type=None,
    ):
        self.id = assignment_id or uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.call_type = call_type


# ============================================================================
# Helper Functions
# ============================================================================


def create_week_of_blocks(start_date=None):
    """
    Create blocks for a full week (Sun-Sat).

    Args:
        start_date: Starting date (defaults to next Monday)

    Returns:
        list[MockBlock]: List of blocks covering one week
    """
    if start_date is None:
        # Start from next Monday
        today = date.today()
        days_ahead = 0 - today.weekday()  # Monday is 0
        if days_ahead <= 0:
            days_ahead += 7
        start_date = today + timedelta(days=days_ahead)

    blocks = []
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        block = MockBlock(block_date=current_date, time_of_day="PM")
        blocks.append(block)

    return blocks


def get_call_nights(blocks):
    """
    Get blocks that should have call coverage (Sun-Thurs).

    Args:
        blocks: List of blocks

    Returns:
        list[MockBlock]: Blocks on overnight call days
    """
    return [b for b in blocks if b.date.weekday() in OVERNIGHT_CALL_DAYS]


def get_non_call_nights(blocks):
    """
    Get blocks that should NOT have call coverage (Fri-Sat).

    Args:
        blocks: List of blocks

    Returns:
        list[MockBlock]: Blocks not on overnight call days
    """
    return [b for b in blocks if b.date.weekday() not in OVERNIGHT_CALL_DAYS]


# ============================================================================
# Tests for OvernightCallCoverageConstraint
# ============================================================================


class TestOvernightCallCoverageConstraint:
    """Tests for overnight call coverage constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = OvernightCallCoverageConstraint()
        assert constraint.name == "OvernightCallCoverage"
        assert constraint.constraint_type == ConstraintType.CALL
        assert constraint.priority == ConstraintPriority.CRITICAL

    def test_validate_empty_assignments(self):
        """Test validate with no assignments returns violations for each night."""
        constraint = OvernightCallCoverageConstraint()
        blocks = create_week_of_blocks()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([], context)

        # Should have violations for each Sun-Thurs night (5 nights)
        call_nights = get_call_nights(blocks)
        assert result.satisfied is False
        assert len(result.violations) == len(call_nights)

        # Each violation should be CRITICAL
        for violation in result.violations:
            assert violation.severity == "CRITICAL"
            assert "No overnight call coverage" in violation.message

    def test_validate_exactly_one_call_per_night(self):
        """Test validate with exactly one call per night passes."""
        constraint = OvernightCallCoverageConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty")

        # Create one call assignment per call night
        call_nights = get_call_nights(blocks)
        assignments = [
            MockAssignment(
                person_id=faculty.id,
                block_id=block.id,
                call_type="overnight",
            )
            for block in call_nights
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_no_call_on_one_night(self):
        """Test validate fails when one night has no call coverage."""
        constraint = OvernightCallCoverageConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty")

        # Create call assignments for all nights except one
        call_nights = get_call_nights(blocks)
        assignments = [
            MockAssignment(
                person_id=faculty.id,
                block_id=block.id,
                call_type="overnight",
            )
            for block in call_nights[:-1]  # Skip last night
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "No overnight call coverage" in result.violations[0].message
        assert result.violations[0].severity == "CRITICAL"

    def test_validate_multiple_calls_same_night(self):
        """Test validate fails when multiple faculty assigned same night."""
        constraint = OvernightCallCoverageConstraint()
        blocks = create_week_of_blocks()
        faculty1 = MockPerson(person_type="faculty", name="Faculty 1")
        faculty2 = MockPerson(person_type="faculty", name="Faculty 2")

        call_nights = get_call_nights(blocks)
        first_night = call_nights[0]

        # Assign two faculty to same night
        assignments = [
            MockAssignment(
                person_id=faculty1.id,
                block_id=first_night.id,
                call_type="overnight",
            ),
            MockAssignment(
                person_id=faculty2.id,
                block_id=first_night.id,
                call_type="overnight",
            ),
        ]

        # Add single coverage for other nights
        for block in call_nights[1:]:
            assignments.append(
                MockAssignment(
                    person_id=faculty1.id,
                    block_id=block.id,
                    call_type="overnight",
                )
            )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty1, faculty2],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "Multiple overnight call assignments" in result.violations[0].message
        assert result.violations[0].severity == "CRITICAL"
        assert result.violations[0].details["actual"] == 2
        assert result.violations[0].details["expected"] == 1

    def test_validate_friday_saturday_ignored(self):
        """Test that Friday and Saturday nights are not checked."""
        constraint = OvernightCallCoverageConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty")

        # Only assign call to Sun-Thurs (not Fri-Sat)
        call_nights = get_call_nights(blocks)
        assignments = [
            MockAssignment(
                person_id=faculty.id,
                block_id=block.id,
                call_type="overnight",
            )
            for block in call_nights
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should pass even though Fri-Sat have no coverage
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_non_call_assignments_ignored(self):
        """Test that non-call assignments don't count toward coverage."""
        constraint = OvernightCallCoverageConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty")

        call_nights = get_call_nights(blocks)

        # Create assignments without call_type
        assignments = [
            MockAssignment(
                person_id=faculty.id,
                block_id=block.id,
                call_type=None,  # Not a call assignment
            )
            for block in call_nights
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        # Should fail because these don't count as call coverage
        assert result.satisfied is False
        assert len(result.violations) == len(call_nights)

    def test_validate_with_specific_weekdays(self):
        """Test that only Mon-Thu + Sunday are checked for coverage."""
        constraint = OvernightCallCoverageConstraint()

        # Create blocks for specific dates
        # 2025-01-06 is Monday
        monday = date(2025, 1, 6)
        tuesday = monday + timedelta(days=1)
        wednesday = monday + timedelta(days=2)
        thursday = monday + timedelta(days=3)
        friday = monday + timedelta(days=4)
        saturday = monday + timedelta(days=5)
        sunday = monday + timedelta(days=6)

        all_days = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
        blocks = [MockBlock(block_date=d) for d in all_days]

        # Verify OVERNIGHT_CALL_DAYS constant
        assert monday.weekday() in OVERNIGHT_CALL_DAYS  # 0
        assert tuesday.weekday() in OVERNIGHT_CALL_DAYS  # 1
        assert wednesday.weekday() in OVERNIGHT_CALL_DAYS  # 2
        assert thursday.weekday() in OVERNIGHT_CALL_DAYS  # 3
        assert friday.weekday() not in OVERNIGHT_CALL_DAYS  # 4
        assert saturday.weekday() not in OVERNIGHT_CALL_DAYS  # 5
        assert sunday.weekday() in OVERNIGHT_CALL_DAYS  # 6

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([], context)

        # Should have exactly 5 violations (Mon-Thu + Sun)
        assert len(result.violations) == 5


# ============================================================================
# Tests for AdjunctCallExclusionConstraint
# ============================================================================


class TestAdjunctCallExclusionConstraint:
    """Tests for adjunct call exclusion constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = AdjunctCallExclusionConstraint()
        assert constraint.name == "AdjunctCallExclusion"
        assert constraint.constraint_type == ConstraintType.CALL
        assert constraint.priority == ConstraintPriority.HIGH

    def test_validate_empty_assignments(self):
        """Test validate with no assignments passes."""
        constraint = AdjunctCallExclusionConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_no_adjuncts(self):
        """Test validate passes when no adjuncts exist."""
        constraint = AdjunctCallExclusionConstraint()
        blocks = create_week_of_blocks()
        core_faculty = MockPerson(
            person_type="faculty",
            name="Core Faculty",
            faculty_role="core",
        )

        call_nights = get_call_nights(blocks)
        assignments = [
            MockAssignment(
                person_id=core_faculty.id,
                block_id=block.id,
                call_type="overnight",
            )
            for block in call_nights
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[core_faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_adjunct_assigned_to_call(self):
        """Test validate fails when adjunct has call assignment."""
        constraint = AdjunctCallExclusionConstraint()
        blocks = create_week_of_blocks()
        adjunct_faculty = MockPerson(
            person_type="faculty",
            name="Dr. Adjunct",
            faculty_role="adjunct",
        )

        call_nights = get_call_nights(blocks)
        first_night = call_nights[0]

        # Assign adjunct to call
        assignment = MockAssignment(
            person_id=adjunct_faculty.id,
            block_id=first_night.id,
            call_type="overnight",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[adjunct_faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([assignment], context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "Adjunct" in result.violations[0].message
        assert "solver-generated call assignment" in result.violations[0].message
        assert result.violations[0].severity == "HIGH"
        assert result.violations[0].person_id == adjunct_faculty.id

    def test_validate_adjunct_uppercase_role(self):
        """Test adjunct detection works with uppercase faculty_role."""
        constraint = AdjunctCallExclusionConstraint()
        blocks = create_week_of_blocks()
        adjunct_faculty = MockPerson(
            person_type="faculty",
            name="Dr. Adjunct",
            faculty_role="ADJUNCT",  # Uppercase
        )

        call_nights = get_call_nights(blocks)
        assignment = MockAssignment(
            person_id=adjunct_faculty.id,
            block_id=call_nights[0].id,
            call_type="overnight",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[adjunct_faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([assignment], context)

        assert result.satisfied is False
        assert len(result.violations) == 1

    def test_validate_mixed_faculty_roles(self):
        """Test validate with mix of adjunct and core faculty."""
        constraint = AdjunctCallExclusionConstraint()
        blocks = create_week_of_blocks()

        core_faculty = MockPerson(
            person_type="faculty",
            name="Dr. Core",
            faculty_role="core",
        )
        adjunct_faculty = MockPerson(
            person_type="faculty",
            name="Dr. Adjunct",
            faculty_role="adjunct",
        )

        call_nights = get_call_nights(blocks)

        assignments = [
            # Core faculty on call - OK
            MockAssignment(
                person_id=core_faculty.id,
                block_id=call_nights[0].id,
                call_type="overnight",
            ),
            # Adjunct on call - Violation
            MockAssignment(
                person_id=adjunct_faculty.id,
                block_id=call_nights[1].id,
                call_type="overnight",
            ),
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[core_faculty, adjunct_faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].person_id == adjunct_faculty.id

    def test_validate_adjunct_non_call_assignment(self):
        """Test adjunct with non-call assignment is allowed."""
        constraint = AdjunctCallExclusionConstraint()
        blocks = create_week_of_blocks()
        adjunct_faculty = MockPerson(
            person_type="faculty",
            name="Dr. Adjunct",
            faculty_role="adjunct",
        )

        # Adjunct has regular assignment, not call
        assignment = MockAssignment(
            person_id=adjunct_faculty.id,
            block_id=blocks[0].id,
            call_type=None,  # Not a call assignment
        )

        context = SchedulingContext(
            residents=[],
            faculty=[adjunct_faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([assignment], context)

        # Should pass - constraint only applies to call assignments
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_faculty_without_role_attribute(self):
        """Test faculty without faculty_role attribute is treated as non-adjunct."""
        constraint = AdjunctCallExclusionConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(
            person_type="faculty",
            name="Dr. NoRole",
            # No faculty_role attribute
        )
        # Remove faculty_role if it exists
        if hasattr(faculty, "faculty_role"):
            delattr(faculty, "faculty_role")

        call_nights = get_call_nights(blocks)
        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=call_nights[0].id,
            call_type="overnight",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([assignment], context)

        # Should pass - no faculty_role means not adjunct
        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# Tests for CallAvailabilityConstraint
# ============================================================================


class TestCallAvailabilityConstraint:
    """Tests for call availability constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = CallAvailabilityConstraint()
        assert constraint.name == "CallAvailability"
        assert constraint.constraint_type == ConstraintType.AVAILABILITY
        assert constraint.priority == ConstraintPriority.CRITICAL

    def test_validate_empty_assignments(self):
        """Test validate with no assignments passes."""
        constraint = CallAvailabilityConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_available_faculty(self):
        """Test validate passes when faculty is available."""
        constraint = CallAvailabilityConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty", name="Dr. Available")

        call_nights = get_call_nights(blocks)
        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=call_nights[0].id,
            call_type="overnight",
        )

        # Faculty is available (no availability restrictions)
        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
            availability={},  # Empty = all available
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_unavailable_faculty_assigned(self):
        """Test validate fails when unavailable faculty assigned to call."""
        constraint = CallAvailabilityConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty", name="Dr. Unavailable")

        call_nights = get_call_nights(blocks)
        first_night = call_nights[0]

        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=first_night.id,
            call_type="overnight",
        )

        # Mark faculty as unavailable for this block
        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
            availability={
                faculty.id: {
                    first_night.id: {
                        "available": False,
                        "replacement": "on leave",
                    }
                }
            },
        )

        result = constraint.validate([assignment], context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "unavailable" in result.violations[0].message
        assert result.violations[0].severity == "CRITICAL"
        assert result.violations[0].person_id == faculty.id
        assert result.violations[0].block_id == first_night.id
        assert result.violations[0].details["reason"] == "on leave"

    def test_validate_faculty_available_explicit_true(self):
        """Test validate passes when availability explicitly set to True."""
        constraint = CallAvailabilityConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty", name="Dr. Available")

        call_nights = get_call_nights(blocks)
        first_night = call_nights[0]

        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=first_night.id,
            call_type="overnight",
        )

        # Explicitly mark as available
        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
            availability={faculty.id: {first_night.id: {"available": True}}},
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_partial_availability(self):
        """Test validate with some blocks available, some not."""
        constraint = CallAvailabilityConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty", name="Dr. PartialAvail")

        call_nights = get_call_nights(blocks)
        night1 = call_nights[0]
        night2 = call_nights[1]
        night3 = call_nights[2]

        assignments = [
            MockAssignment(
                person_id=faculty.id,
                block_id=night1.id,
                call_type="overnight",
            ),
            MockAssignment(
                person_id=faculty.id,
                block_id=night2.id,
                call_type="overnight",
            ),
            MockAssignment(
                person_id=faculty.id,
                block_id=night3.id,
                call_type="overnight",
            ),
        ]

        # night1: available, night2: unavailable, night3: not specified (defaults available)
        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
            availability={
                faculty.id: {
                    night1.id: {"available": True},
                    night2.id: {"available": False, "replacement": "TDY"},
                }
            },
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].block_id == night2.id
        assert result.violations[0].details["reason"] == "TDY"

    def test_validate_non_call_assignment_ignored(self):
        """Test non-call assignments are not checked for availability."""
        constraint = CallAvailabilityConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty", name="Dr. Faculty")

        # Regular assignment (not call)
        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=blocks[0].id,
            call_type=None,  # Not a call assignment
        )

        # Mark as unavailable
        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
            availability={faculty.id: {blocks[0].id: {"available": False}}},
        )

        result = constraint.validate([assignment], context)

        # Should pass - constraint only applies to call assignments
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_faculty_mixed_availability(self):
        """Test validation with multiple faculty with different availability."""
        constraint = CallAvailabilityConstraint()
        blocks = create_week_of_blocks()

        faculty1 = MockPerson(person_type="faculty", name="Dr. One")
        faculty2 = MockPerson(person_type="faculty", name="Dr. Two")

        call_nights = get_call_nights(blocks)
        night1 = call_nights[0]
        night2 = call_nights[1]

        assignments = [
            # Faculty 1 on night 1 - available
            MockAssignment(
                person_id=faculty1.id,
                block_id=night1.id,
                call_type="overnight",
            ),
            # Faculty 2 on night 2 - unavailable
            MockAssignment(
                person_id=faculty2.id,
                block_id=night2.id,
                call_type="overnight",
            ),
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty1, faculty2],
            blocks=blocks,
            templates=[],
            availability={
                faculty1.id: {night1.id: {"available": True}},
                faculty2.id: {
                    night2.id: {"available": False, "replacement": "deployment"}
                },
            },
        )

        result = constraint.validate(assignments, context)

        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].person_id == faculty2.id
        assert result.violations[0].details["reason"] == "deployment"

    def test_validate_missing_block_in_context(self):
        """Test graceful handling when assignment references unknown block."""
        constraint = CallAvailabilityConstraint()
        blocks = create_week_of_blocks()
        faculty = MockPerson(person_type="faculty", name="Dr. Faculty")

        # Assignment references block not in context
        unknown_block_id = uuid4()
        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=unknown_block_id,
            call_type="overnight",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[],
            availability={faculty.id: {unknown_block_id: {"available": False}}},
        )

        result = constraint.validate([assignment], context)

        # Should still detect violation based on availability dict
        assert result.satisfied is False
        assert len(result.violations) == 1

    def test_validate_missing_faculty_in_context(self):
        """Test graceful handling when assignment references unknown faculty."""
        constraint = CallAvailabilityConstraint()
        blocks = create_week_of_blocks()

        # Assignment references faculty not in context
        unknown_faculty_id = uuid4()
        call_nights = get_call_nights(blocks)
        assignment = MockAssignment(
            person_id=unknown_faculty_id,
            block_id=call_nights[0].id,
            call_type="overnight",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[],  # Empty faculty list
            blocks=blocks,
            templates=[],
            availability={},
        )

        result = constraint.validate([assignment], context)

        # Should pass - if faculty not in context, we can't validate
        # (This is a data consistency issue, not a constraint violation)
        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestCallCoverageIntegration:
    """Integration tests for combined call coverage constraints."""

    def test_complete_valid_week(self):
        """Test a complete valid week with all constraints."""
        blocks = create_week_of_blocks()

        # Create faculty mix
        core_faculty1 = MockPerson(
            person_type="faculty",
            name="Dr. Core One",
            faculty_role="core",
        )
        core_faculty2 = MockPerson(
            person_type="faculty",
            name="Dr. Core Two",
            faculty_role="core",
        )
        adjunct_faculty = MockPerson(
            person_type="faculty",
            name="Dr. Adjunct",
            faculty_role="adjunct",
        )

        call_nights = get_call_nights(blocks)

        # Valid assignments: core faculty only, one per night, all available
        assignments = []
        for i, night in enumerate(call_nights):
            # Alternate between two core faculty
            faculty = core_faculty1 if i % 2 == 0 else core_faculty2
            assignments.append(
                MockAssignment(
                    person_id=faculty.id,
                    block_id=night.id,
                    call_type="overnight",
                )
            )

        context = SchedulingContext(
            residents=[],
            faculty=[core_faculty1, core_faculty2, adjunct_faculty],
            blocks=blocks,
            templates=[],
            availability={},  # All available
        )

        # Validate all three constraints
        coverage = OvernightCallCoverageConstraint()
        adjunct_exclusion = AdjunctCallExclusionConstraint()
        availability = CallAvailabilityConstraint()

        coverage_result = coverage.validate(assignments, context)
        adjunct_result = adjunct_exclusion.validate(assignments, context)
        availability_result = availability.validate(assignments, context)

        assert coverage_result.satisfied is True
        assert adjunct_result.satisfied is True
        assert availability_result.satisfied is True

    def test_complete_invalid_week_multiple_violations(self):
        """Test a week with multiple constraint violations."""
        blocks = create_week_of_blocks()

        core_faculty = MockPerson(
            person_type="faculty",
            name="Dr. Core",
            faculty_role="core",
        )
        adjunct_faculty = MockPerson(
            person_type="faculty",
            name="Dr. Adjunct",
            faculty_role="adjunct",
        )

        call_nights = get_call_nights(blocks)

        assignments = [
            # Night 1: Adjunct assigned (violation)
            MockAssignment(
                person_id=adjunct_faculty.id,
                block_id=call_nights[0].id,
                call_type="overnight",
            ),
            # Night 2: Core faculty but unavailable (violation)
            MockAssignment(
                person_id=core_faculty.id,
                block_id=call_nights[1].id,
                call_type="overnight",
            ),
            # Night 3: Two faculty assigned (violation)
            MockAssignment(
                person_id=core_faculty.id,
                block_id=call_nights[2].id,
                call_type="overnight",
            ),
            MockAssignment(
                person_id=adjunct_faculty.id,
                block_id=call_nights[2].id,
                call_type="overnight",
            ),
            # Nights 4-5: No coverage (violations)
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[core_faculty, adjunct_faculty],
            blocks=blocks,
            templates=[],
            availability={
                core_faculty.id: {
                    call_nights[1].id: {"available": False, "replacement": "TDY"}
                }
            },
        )

        coverage = OvernightCallCoverageConstraint()
        adjunct_exclusion = AdjunctCallExclusionConstraint()
        availability = CallAvailabilityConstraint()

        coverage_result = coverage.validate(assignments, context)
        adjunct_result = adjunct_exclusion.validate(assignments, context)
        availability_result = availability.validate(assignments, context)

        # All should have violations
        assert coverage_result.satisfied is False
        assert adjunct_result.satisfied is False
        assert availability_result.satisfied is False

        # Coverage: missing 2 nights + 1 double-booked = 3 violations
        assert len(coverage_result.violations) == 3

        # Adjunct: 2 nights with adjunct assigned
        assert len(adjunct_result.violations) == 2

        # Availability: 1 unavailable faculty assigned
        assert len(availability_result.violations) == 1
