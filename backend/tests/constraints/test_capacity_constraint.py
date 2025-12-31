"""
Tests for capacity and coverage constraints.

Tests the four capacity constraints:
1. OnePersonPerBlockConstraint - Max one primary resident per block
2. ClinicCapacityConstraint - Rotation template capacity limits
3. MaxPhysiciansInClinicConstraint - Physical space limits for clinic
4. CoverageConstraint - Maximize block coverage (soft constraint)
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.capacity import (
    ClinicCapacityConstraint,
    CoverageConstraint,
    MaxPhysiciansInClinicConstraint,
    OnePersonPerBlockConstraint,
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
        person_type="resident",
        pgy_level=None,
    ):
        self.id = person_id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level


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


def create_week_of_blocks(start_date=None):
    """
    Create blocks for a full week (Mon-Sun).

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
        is_weekend = current_date.weekday() >= 5
        # Create AM and PM blocks
        for time_of_day in ["AM", "PM"]:
            block = MockBlock(
                block_date=current_date,
                time_of_day=time_of_day,
                is_weekend=is_weekend,
            )
            blocks.append(block)

    return blocks


def create_residents(count=3):
    """
    Create multiple resident persons.

    Args:
        count: Number of residents to create

    Returns:
        list[MockPerson]: List of resident objects
    """
    residents = []
    for i in range(count):
        resident = MockPerson(
            name=f"Dr. Resident {i + 1}",
            person_type="resident",
            pgy_level=(i % 3) + 1,  # PGY-1, PGY-2, PGY-3
        )
        residents.append(resident)
    return residents


def create_faculty(count=2):
    """
    Create multiple faculty persons.

    Args:
        count: Number of faculty to create

    Returns:
        list[MockPerson]: List of faculty objects
    """
    faculty = []
    for i in range(count):
        fac = MockPerson(
            name=f"Dr. Faculty {i + 1}",
            person_type="faculty",
        )
        faculty.append(fac)
    return faculty


# ============================================================================
# Tests for OnePersonPerBlockConstraint
# ============================================================================


class TestOnePersonPerBlockConstraint:
    """Tests for one person per block constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = OnePersonPerBlockConstraint()
        assert constraint.name == "OnePersonPerBlock"
        assert constraint.constraint_type == ConstraintType.CAPACITY
        assert constraint.priority == ConstraintPriority.CRITICAL
        assert constraint.max_per_block == 1

    def test_constraint_initialization_custom_max(self):
        """Test constraint initialization with custom max_per_block."""
        constraint = OnePersonPerBlockConstraint(max_per_block=2)
        assert constraint.max_per_block == 2

    def test_validate_empty_assignments(self):
        """Test validate with no assignments passes."""
        constraint = OnePersonPerBlockConstraint()
        blocks = create_week_of_blocks()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_one_primary_per_block(self):
        """Test validate passes with one primary assignment per block."""
        constraint = OnePersonPerBlockConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=2)

        # Assign different residents to different blocks
        assignments = [
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=blocks[1].id,
                role="primary",
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_primaries_same_block(self):
        """Test validate fails with multiple primary assignments to same block."""
        constraint = OnePersonPerBlockConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=2)

        # Assign both residents to same block as primary
        first_block = blocks[0]
        assignments = [
            MockAssignment(
                person_id=residents[0].id,
                block_id=first_block.id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=first_block.id,
                role="primary",
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert result.violations[0].block_id == first_block.id
        assert result.violations[0].details["count"] == 2
        assert result.violations[0].details["max"] == 1

    def test_validate_three_primaries_same_block(self):
        """Test validate fails with three primary assignments to same block."""
        constraint = OnePersonPerBlockConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=3)

        first_block = blocks[0]
        assignments = [
            MockAssignment(
                person_id=residents[0].id,
                block_id=first_block.id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=first_block.id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[2].id,
                block_id=first_block.id,
                role="primary",
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].details["count"] == 3

    def test_validate_non_primary_assignments_ignored(self):
        """Test that non-primary assignments don't count toward limit."""
        constraint = OnePersonPerBlockConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=2)

        first_block = blocks[0]
        assignments = [
            MockAssignment(
                person_id=residents[0].id,
                block_id=first_block.id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=first_block.id,
                role="backup",  # Not primary
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)
        # Should pass because only one primary assignment
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_blocks_with_violations(self):
        """Test validate detects violations across multiple blocks."""
        constraint = OnePersonPerBlockConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=4)

        assignments = [
            # Block 0: 2 primaries (violation)
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
            # Block 1: 1 primary (ok)
            MockAssignment(
                person_id=residents[2].id,
                block_id=blocks[1].id,
                role="primary",
            ),
            # Block 2: 2 primaries (violation)
            MockAssignment(
                person_id=residents[2].id,
                block_id=blocks[2].id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[3].id,
                block_id=blocks[2].id,
                role="primary",
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 2
        # Verify both blocks are reported
        violated_blocks = {v.block_id for v in result.violations}
        assert blocks[0].id in violated_blocks
        assert blocks[2].id in violated_blocks

    def test_validate_custom_max_per_block(self):
        """Test validate with custom max_per_block value."""
        constraint = OnePersonPerBlockConstraint(max_per_block=2)
        blocks = create_week_of_blocks()
        residents = create_residents(count=3)

        first_block = blocks[0]
        assignments = [
            MockAssignment(
                person_id=residents[0].id,
                block_id=first_block.id,
                role="primary",
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=first_block.id,
                role="primary",
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        # Should pass with max_per_block=2
        result = constraint.validate(assignments, context)
        assert result.satisfied is True

        # Add third assignment - should fail
        assignments.append(
            MockAssignment(
                person_id=residents[2].id,
                block_id=first_block.id,
                role="primary",
            )
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert result.violations[0].details["count"] == 3
        assert result.violations[0].details["max"] == 2


# ============================================================================
# Tests for ClinicCapacityConstraint
# ============================================================================


class TestClinicCapacityConstraint:
    """Tests for clinic capacity constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = ClinicCapacityConstraint()
        assert constraint.name == "ClinicCapacity"
        assert constraint.constraint_type == ConstraintType.CAPACITY
        assert constraint.priority == ConstraintPriority.HIGH

    def test_validate_empty_assignments(self):
        """Test validate with no assignments passes."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        templates = [MockTemplate(name="Clinic", max_residents=4)]

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=templates,
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_no_template_limits(self):
        """Test validate passes when templates have no capacity limits."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=5)
        template = MockTemplate(name="Unlimited", max_residents=None)

        # Assign all residents to same block/template
        assignments = [
            MockAssignment(
                person_id=r.id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            )
            for r in residents
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        # Should pass because template has no max_residents limit
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_within_capacity_limit(self):
        """Test validate passes when assignments are within capacity."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=3)
        template = MockTemplate(name="Sports Med", max_residents=4)

        # Assign 3 residents to template with max 4
        assignments = [
            MockAssignment(
                person_id=r.id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            )
            for r in residents
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_at_capacity_limit(self):
        """Test validate passes when assignments exactly meet capacity."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=4)
        template = MockTemplate(name="Sports Med", max_residents=4)

        # Assign exactly 4 residents to template with max 4
        assignments = [
            MockAssignment(
                person_id=r.id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            )
            for r in residents
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_exceeds_capacity_limit(self):
        """Test validate fails when assignments exceed capacity."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=5)
        template = MockTemplate(name="Sports Med", max_residents=4)

        # Assign 5 residents to template with max 4
        first_block = blocks[0]
        assignments = [
            MockAssignment(
                person_id=r.id,
                block_id=first_block.id,
                rotation_template_id=template.id,
            )
            for r in residents
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert result.violations[0].block_id == first_block.id
        assert result.violations[0].details["count"] == 5
        assert result.violations[0].details["limit"] == 4
        assert "Sports Med" in result.violations[0].message

    def test_validate_multiple_templates_different_blocks(self):
        """Test validate with different templates on different blocks."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=6)
        template1 = MockTemplate(name="Template 1", max_residents=3)
        template2 = MockTemplate(name="Template 2", max_residents=2)

        assignments = [
            # Block 0, Template 1: 3 residents (at limit, ok)
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                rotation_template_id=template1.id,
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=blocks[0].id,
                rotation_template_id=template1.id,
            ),
            MockAssignment(
                person_id=residents[2].id,
                block_id=blocks[0].id,
                rotation_template_id=template1.id,
            ),
            # Block 1, Template 2: 2 residents (at limit, ok)
            MockAssignment(
                person_id=residents[3].id,
                block_id=blocks[1].id,
                rotation_template_id=template2.id,
            ),
            MockAssignment(
                person_id=residents[4].id,
                block_id=blocks[1].id,
                rotation_template_id=template2.id,
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template1, template2],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_same_template_different_blocks(self):
        """Test validate with same template on different blocks."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=6)
        template = MockTemplate(name="Clinic", max_residents=3)

        assignments = [
            # Block 0: 3 residents (ok)
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[2].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            ),
            # Block 1: 3 residents (ok)
            MockAssignment(
                person_id=residents[3].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[4].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[5].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        # Should pass - capacity applies per block
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_violations(self):
        """Test validate detects violations across multiple blocks and templates."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=8)
        template1 = MockTemplate(name="Template 1", max_residents=2)
        template2 = MockTemplate(name="Template 2", max_residents=2)

        assignments = [
            # Block 0, Template 1: 3 residents (violation)
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                rotation_template_id=template1.id,
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=blocks[0].id,
                rotation_template_id=template1.id,
            ),
            MockAssignment(
                person_id=residents[2].id,
                block_id=blocks[0].id,
                rotation_template_id=template1.id,
            ),
            # Block 1, Template 2: 4 residents (violation)
            MockAssignment(
                person_id=residents[3].id,
                block_id=blocks[1].id,
                rotation_template_id=template2.id,
            ),
            MockAssignment(
                person_id=residents[4].id,
                block_id=blocks[1].id,
                rotation_template_id=template2.id,
            ),
            MockAssignment(
                person_id=residents[5].id,
                block_id=blocks[1].id,
                rotation_template_id=template2.id,
            ),
            MockAssignment(
                person_id=residents[6].id,
                block_id=blocks[1].id,
                rotation_template_id=template2.id,
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template1, template2],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 2

    def test_validate_zero_capacity_limit(self):
        """Test validate ignores templates with max_residents=0."""
        constraint = ClinicCapacityConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=5)
        template = MockTemplate(name="No Limit", max_residents=0)

        # Assign residents to template with max_residents=0
        assignments = [
            MockAssignment(
                person_id=r.id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            )
            for r in residents
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        # max_residents=0 is treated as no limit
        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# Tests for MaxPhysiciansInClinicConstraint
# ============================================================================


class TestMaxPhysiciansInClinicConstraint:
    """Tests for max physicians in clinic constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = MaxPhysiciansInClinicConstraint()
        assert constraint.name == "MaxPhysiciansInClinic"
        assert constraint.constraint_type == ConstraintType.CAPACITY
        assert constraint.priority == ConstraintPriority.HIGH
        assert constraint.max_physicians == 6

    def test_constraint_initialization_custom_max(self):
        """Test constraint initialization with custom max_physicians."""
        constraint = MaxPhysiciansInClinicConstraint(max_physicians=8)
        assert constraint.max_physicians == 8

    def test_validate_empty_assignments(self):
        """Test validate with no assignments passes."""
        constraint = MaxPhysiciansInClinicConstraint()
        blocks = create_week_of_blocks()
        template = MockTemplate(
            name="Clinic",
            activity_type="outpatient",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_no_clinic_templates(self):
        """Test validate passes when no clinic templates exist."""
        constraint = MaxPhysiciansInClinicConstraint()
        blocks = create_week_of_blocks()
        residents = create_residents(count=10)
        # Template is not outpatient type
        template = MockTemplate(name="Inpatient", activity_type="inpatient")

        assignments = [
            MockAssignment(
                person_id=r.id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            )
            for r in residents
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        # Should pass because no clinic templates
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_within_physician_limit(self):
        """Test validate passes when physicians are within limit."""
        constraint = MaxPhysiciansInClinicConstraint(max_physicians=6)
        blocks = create_week_of_blocks()
        residents = create_residents(count=4)
        faculty = create_faculty(count=2)
        template = MockTemplate(name="Clinic", activity_type="outpatient")

        # Assign 4 residents + 2 faculty = 6 physicians (at limit)
        assignments = []
        for r in residents:
            assignments.append(
                MockAssignment(
                    person_id=r.id,
                    block_id=blocks[0].id,
                    rotation_template_id=template.id,
                )
            )
        for f in faculty:
            assignments.append(
                MockAssignment(
                    person_id=f.id,
                    block_id=blocks[0].id,
                    rotation_template_id=template.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=faculty,
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_exceeds_physician_limit(self):
        """Test validate fails when physicians exceed limit."""
        constraint = MaxPhysiciansInClinicConstraint(max_physicians=6)
        blocks = create_week_of_blocks()
        residents = create_residents(count=5)
        faculty = create_faculty(count=3)
        template = MockTemplate(name="Clinic", activity_type="outpatient")

        # Assign 5 residents + 3 faculty = 8 physicians (exceeds limit of 6)
        first_block = blocks[0]
        assignments = []
        for r in residents:
            assignments.append(
                MockAssignment(
                    person_id=r.id,
                    block_id=first_block.id,
                    rotation_template_id=template.id,
                )
            )
        for f in faculty:
            assignments.append(
                MockAssignment(
                    person_id=f.id,
                    block_id=first_block.id,
                    rotation_template_id=template.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=faculty,
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert result.violations[0].block_id == first_block.id
        assert result.violations[0].details["count"] == 8
        assert result.violations[0].details["limit"] == 6

    def test_validate_only_residents_in_clinic(self):
        """Test validate with only residents in clinic."""
        constraint = MaxPhysiciansInClinicConstraint(max_physicians=4)
        blocks = create_week_of_blocks()
        residents = create_residents(count=3)
        template = MockTemplate(name="Clinic", activity_type="outpatient")

        assignments = [
            MockAssignment(
                person_id=r.id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            )
            for r in residents
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_only_faculty_in_clinic(self):
        """Test validate with only faculty in clinic."""
        constraint = MaxPhysiciansInClinicConstraint(max_physicians=4)
        blocks = create_week_of_blocks()
        faculty = create_faculty(count=3)
        template = MockTemplate(name="Clinic", activity_type="outpatient")

        assignments = [
            MockAssignment(
                person_id=f.id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            )
            for f in faculty
        ]

        context = SchedulingContext(
            residents=[],
            faculty=faculty,
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_blocks_separate_counts(self):
        """Test validate counts physicians per block separately."""
        constraint = MaxPhysiciansInClinicConstraint(max_physicians=4)
        blocks = create_week_of_blocks()
        residents = create_residents(count=8)
        template = MockTemplate(name="Clinic", activity_type="outpatient")

        assignments = [
            # Block 0: 4 residents (at limit, ok)
            MockAssignment(
                person_id=residents[0].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[2].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[3].id,
                block_id=blocks[0].id,
                rotation_template_id=template.id,
            ),
            # Block 1: 4 residents (at limit, ok)
            MockAssignment(
                person_id=residents[4].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[5].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[6].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
            ),
            MockAssignment(
                person_id=residents[7].id,
                block_id=blocks[1].id,
                rotation_template_id=template.id,
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        # Should pass - each block counted separately
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_multiple_clinic_templates_combined(self):
        """Test validate combines counts from multiple clinic templates."""
        constraint = MaxPhysiciansInClinicConstraint(max_physicians=5)
        blocks = create_week_of_blocks()
        residents = create_residents(count=6)
        template1 = MockTemplate(
            name="Sports Med",
            activity_type="outpatient",
        )
        template2 = MockTemplate(
            name="Primary Care",
            activity_type="outpatient",
        )

        # Assign to same block but different clinic templates
        first_block = blocks[0]
        assignments = [
            MockAssignment(
                person_id=residents[0].id,
                block_id=first_block.id,
                rotation_template_id=template1.id,
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=first_block.id,
                rotation_template_id=template1.id,
            ),
            MockAssignment(
                person_id=residents[2].id,
                block_id=first_block.id,
                rotation_template_id=template1.id,
            ),
            MockAssignment(
                person_id=residents[3].id,
                block_id=first_block.id,
                rotation_template_id=template2.id,
            ),
            MockAssignment(
                person_id=residents[4].id,
                block_id=first_block.id,
                rotation_template_id=template2.id,
            ),
            MockAssignment(
                person_id=residents[5].id,
                block_id=first_block.id,
                rotation_template_id=template2.id,
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template1, template2],
        )

        result = constraint.validate(assignments, context)
        # Should fail - total 6 physicians across both clinics exceeds limit of 5
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].details["count"] == 6

    def test_validate_mixed_clinic_non_clinic_templates(self):
        """Test validate only counts clinic template assignments."""
        constraint = MaxPhysiciansInClinicConstraint(max_physicians=4)
        blocks = create_week_of_blocks()
        residents = create_residents(count=6)
        clinic_template = MockTemplate(
            name="Clinic",
            activity_type="outpatient",
        )
        inpatient_template = MockTemplate(
            name="Inpatient",
            activity_type="inpatient",
        )

        first_block = blocks[0]
        assignments = [
            # 3 in clinic (within limit)
            MockAssignment(
                person_id=residents[0].id,
                block_id=first_block.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=residents[1].id,
                block_id=first_block.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=residents[2].id,
                block_id=first_block.id,
                rotation_template_id=clinic_template.id,
            ),
            # 3 in inpatient (should not count)
            MockAssignment(
                person_id=residents[3].id,
                block_id=first_block.id,
                rotation_template_id=inpatient_template.id,
            ),
            MockAssignment(
                person_id=residents[4].id,
                block_id=first_block.id,
                rotation_template_id=inpatient_template.id,
            ),
            MockAssignment(
                person_id=residents[5].id,
                block_id=first_block.id,
                rotation_template_id=inpatient_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[clinic_template, inpatient_template],
        )

        result = constraint.validate(assignments, context)
        # Should pass - only clinic assignments count
        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# Tests for CoverageConstraint (Soft Constraint)
# ============================================================================


class TestCoverageConstraint:
    """Tests for coverage soft constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = CoverageConstraint()
        assert constraint.name == "Coverage"
        assert constraint.constraint_type == ConstraintType.CAPACITY
        assert constraint.priority == ConstraintPriority.HIGH
        assert constraint.weight == 1000.0

    def test_constraint_initialization_custom_weight(self):
        """Test constraint initialization with custom weight."""
        constraint = CoverageConstraint(weight=500.0)
        assert constraint.weight == 500.0

    def test_validate_empty_assignments(self):
        """Test validate with no assignments calculates 0% coverage."""
        constraint = CoverageConstraint()
        blocks = create_week_of_blocks()

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        result = constraint.validate([], context)
        # Soft constraint always returns satisfied=True
        assert result.satisfied is True
        # Should have violation for low coverage
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"
        assert "0.0%" in result.violations[0].message
        # Penalty should be (1 - 0.0) * 1000.0 = 1000.0
        assert result.penalty == 1000.0

    def test_validate_full_coverage(self):
        """Test validate with 100% coverage has no penalty."""
        constraint = CoverageConstraint()
        blocks = create_week_of_blocks()
        # Filter out weekend blocks
        workday_blocks = [b for b in blocks if not b.is_weekend]
        residents = create_residents(count=len(workday_blocks))
        template = MockTemplate(name="Clinic")

        # Assign to all workday blocks
        assignments = []
        for i, block in enumerate(workday_blocks):
            assignments.append(
                MockAssignment(
                    person_id=residents[i % len(residents)].id,
                    block_id=block.id,
                    rotation_template_id=template.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0
        assert result.penalty == 0.0

    def test_validate_partial_coverage(self):
        """Test validate with partial coverage calculates correct penalty."""
        constraint = CoverageConstraint(weight=1000.0)
        blocks = create_week_of_blocks()
        workday_blocks = [b for b in blocks if not b.is_weekend]
        residents = create_residents(count=2)
        template = MockTemplate(name="Clinic")

        # Assign to half of workday blocks
        half_count = len(workday_blocks) // 2
        assignments = []
        for i in range(half_count):
            assignments.append(
                MockAssignment(
                    person_id=residents[i % len(residents)].id,
                    block_id=workday_blocks[i].id,
                    rotation_template_id=template.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True

        # Coverage rate should be approximately 0.5
        # Penalty = (1 - coverage_rate) * weight
        expected_penalty = (1 - 0.5) * 1000.0
        assert abs(result.penalty - expected_penalty) < 100.0  # Allow some margin

    def test_validate_high_coverage_no_violation(self):
        """Test validate with >90% coverage has no violation message."""
        constraint = CoverageConstraint()
        blocks = create_week_of_blocks()
        workday_blocks = [b for b in blocks if not b.is_weekend]
        residents = create_residents(count=len(workday_blocks))
        template = MockTemplate(name="Clinic")

        # Assign to 95% of workday blocks
        coverage_count = int(len(workday_blocks) * 0.95)
        assignments = []
        for i in range(coverage_count):
            assignments.append(
                MockAssignment(
                    person_id=residents[i % len(residents)].id,
                    block_id=workday_blocks[i].id,
                    rotation_template_id=template.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        # Should have no violation message for >90% coverage
        assert len(result.violations) == 0

    def test_validate_low_coverage_has_violation(self):
        """Test validate with <90% coverage has violation message."""
        constraint = CoverageConstraint()
        blocks = create_week_of_blocks()
        workday_blocks = [b for b in blocks if not b.is_weekend]
        residents = create_residents(count=2)
        template = MockTemplate(name="Clinic")

        # Assign to 50% of workday blocks (< 90%)
        coverage_count = len(workday_blocks) // 2
        assignments = []
        for i in range(coverage_count):
            assignments.append(
                MockAssignment(
                    person_id=residents[i % len(residents)].id,
                    block_id=workday_blocks[i].id,
                    rotation_template_id=template.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True  # Soft constraints always satisfied
        # Should have violation message for <90% coverage
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"
        assert "Coverage rate" in result.violations[0].message

    def test_validate_weekends_excluded_from_coverage(self):
        """Test validate excludes weekend blocks from coverage calculation."""
        constraint = CoverageConstraint()
        blocks = create_week_of_blocks()
        workday_blocks = [b for b in blocks if not b.is_weekend]
        weekend_blocks = [b for b in blocks if b.is_weekend]
        residents = create_residents(count=len(workday_blocks))
        template = MockTemplate(name="Clinic")

        # Only assign to workday blocks, leave weekends empty
        assignments = []
        for i, block in enumerate(workday_blocks):
            assignments.append(
                MockAssignment(
                    person_id=residents[i % len(residents)].id,
                    block_id=block.id,
                    rotation_template_id=template.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        # Should be 100% coverage (weekends don't count)
        assert result.satisfied is True
        assert len(result.violations) == 0
        assert result.penalty == 0.0

    def test_validate_duplicate_block_assignments(self):
        """Test validate counts each unique block only once."""
        constraint = CoverageConstraint()
        blocks = create_week_of_blocks()
        workday_blocks = [b for b in blocks if not b.is_weekend]
        residents = create_residents(count=2)
        template = MockTemplate(name="Clinic")

        # Assign multiple residents to same blocks
        assignments = []
        for block in workday_blocks[:3]:
            # Assign two residents to same block
            assignments.append(
                MockAssignment(
                    person_id=residents[0].id,
                    block_id=block.id,
                    rotation_template_id=template.id,
                )
            )
            assignments.append(
                MockAssignment(
                    person_id=residents[1].id,
                    block_id=block.id,
                    rotation_template_id=template.id,
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        result = constraint.validate(assignments, context)
        # Coverage should be 3 / total_workdays, not 6 / total_workdays
        assert result.satisfied is True
        # Penalty should reflect only 3 unique blocks covered
        expected_coverage = 3 / len(workday_blocks)
        expected_penalty = (1 - expected_coverage) * constraint.weight
        assert abs(result.penalty - expected_penalty) < 1.0


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestCapacityConstraintsIntegration:
    """Integration tests for combined capacity constraints."""

    def test_all_constraints_valid_scenario(self):
        """Test all capacity constraints with a valid scenario."""
        blocks = create_week_of_blocks()
        workday_blocks = [b for b in blocks if not b.is_weekend]
        residents = create_residents(count=4)
        faculty = create_faculty(count=2)
        template = MockTemplate(
            name="Sports Med",
            activity_type="outpatient",
            max_residents=4,
        )

        # Create valid assignments:
        # - One resident per block (satisfies OnePersonPerBlock)
        # - Within template capacity (satisfies ClinicCapacity)
        # - Within physician limit (satisfies MaxPhysiciansInClinic)
        # - Good coverage (satisfies Coverage)
        assignments = []
        for i, block in enumerate(workday_blocks[:8]):
            # Alternate residents
            resident = residents[i % len(residents)]
            assignments.append(
                MockAssignment(
                    person_id=resident.id,
                    block_id=block.id,
                    rotation_template_id=template.id,
                    role="primary",
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=faculty,
            blocks=blocks,
            templates=[template],
        )

        # Validate all constraints
        one_per_block = OnePersonPerBlockConstraint()
        clinic_capacity = ClinicCapacityConstraint()
        max_physicians = MaxPhysiciansInClinicConstraint()
        coverage = CoverageConstraint()

        result1 = one_per_block.validate(assignments, context)
        result2 = clinic_capacity.validate(assignments, context)
        result3 = max_physicians.validate(assignments, context)
        result4 = coverage.validate(assignments, context)

        assert result1.satisfied is True
        assert result2.satisfied is True
        assert result3.satisfied is True
        assert result4.satisfied is True

    def test_multiple_constraint_violations(self):
        """Test scenario with multiple capacity constraint violations."""
        blocks = create_week_of_blocks()
        residents = create_residents(count=10)
        template = MockTemplate(
            name="Small Clinic",
            activity_type="outpatient",
            max_residents=2,
        )

        # Create scenario with multiple violations:
        # - Multiple primaries per block
        # - Exceeds template capacity
        # - Exceeds physician limit
        first_block = blocks[0]
        assignments = []
        for resident in residents:
            assignments.append(
                MockAssignment(
                    person_id=resident.id,
                    block_id=first_block.id,
                    rotation_template_id=template.id,
                    role="primary",
                )
            )

        context = SchedulingContext(
            residents=residents,
            faculty=[],
            blocks=blocks,
            templates=[template],
        )

        # Validate all constraints
        one_per_block = OnePersonPerBlockConstraint()
        clinic_capacity = ClinicCapacityConstraint()
        max_physicians = MaxPhysiciansInClinicConstraint()

        result1 = one_per_block.validate(assignments, context)
        result2 = clinic_capacity.validate(assignments, context)
        result3 = max_physicians.validate(assignments, context)

        # All should fail
        assert result1.satisfied is False  # 10 primaries in one block
        assert result2.satisfied is False  # 10 > template max of 2
        assert result3.satisfied is False  # 10 > default max of 6
