"""
Tests for temporal and time-based constraints.

Tests the three temporal constraints:
1. WednesdayAMInternOnlyConstraint - Wednesday AM clinic for interns only (hard)
2. WednesdayPMSingleFacultyConstraint - Exactly 1 faculty on 1st/2nd/3rd Wed PM (hard)
3. InvertedWednesdayConstraint - 4th Wed has 1 faculty AM, 1 different faculty PM (hard)
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.temporal import (
    InvertedWednesdayConstraint,
    WednesdayAMInternOnlyConstraint,
    WednesdayPMSingleFacultyConstraint,
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
        faculty_role=None,
    ):
        self.id = person_id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level
        self.faculty_role = faculty_role


class MockBlock:
    """Mock block object for testing."""

    def __init__(self, block_id=None, block_date=None, time_of_day="AM"):
        self.id = block_id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day


class MockTemplate:
    """Mock rotation template object for testing."""

    def __init__(
        self,
        template_id=None,
        name="Test Template",
        activity_type="outpatient",
    ):
        self.id = template_id or uuid4()
        self.name = name
        self.activity_type = activity_type


class MockAssignment:
    """Mock assignment object for testing."""

    def __init__(
        self,
        assignment_id=None,
        person_id=None,
        block_id=None,
        rotation_template_id=None,
    ):
        self.id = assignment_id or uuid4()
        self.person_id = person_id
        self.block_id = block_id
        self.rotation_template_id = rotation_template_id


# ============================================================================
# Helper Functions
# ============================================================================


def find_wednesday(year: int, month: int, week_number: int) -> date:
    """
    Find the Nth Wednesday of a specific month.

    Args:
        year: Year
        month: Month (1-12)
        week_number: Which Wednesday (1=first, 2=second, 3=third, 4=fourth)

    Returns:
        date: The date of the specified Wednesday
    """
    # Start from the first day of the month
    first_day = date(year, month, 1)

    # Find first Wednesday (weekday 2)
    days_until_wednesday = (2 - first_day.weekday()) % 7
    first_wednesday = first_day + timedelta(days=days_until_wednesday)

    # Calculate the nth Wednesday
    target_wednesday = first_wednesday + timedelta(weeks=week_number - 1)

    # Ensure it's still in the same month
    if target_wednesday.month != month:
        raise ValueError(f"No {week_number}th Wednesday in {year}-{month}")

    return target_wednesday


def create_wednesday_blocks(year: int, month: int, week_number: int) -> tuple:
    """
    Create AM and PM blocks for a specific Wednesday.

    Args:
        year: Year
        month: Month
        week_number: Which Wednesday (1-4)

    Returns:
        tuple: (am_block, pm_block)
    """
    wednesday = find_wednesday(year, month, week_number)
    am_block = MockBlock(block_date=wednesday, time_of_day="AM")
    pm_block = MockBlock(block_date=wednesday, time_of_day="PM")
    return am_block, pm_block


def create_week_blocks(start_date: date) -> list:
    """
    Create blocks for a full week (Mon-Sun, AM and PM).

    Args:
        start_date: Starting date (should be a Monday)

    Returns:
        list: List of blocks for the week
    """
    blocks = []
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = MockBlock(block_date=current_date, time_of_day=time_of_day)
            blocks.append(block)
    return blocks


# ============================================================================
# Tests for WednesdayAMInternOnlyConstraint
# ============================================================================


class TestWednesdayAMInternOnlyConstraint:
    """Tests for Wednesday AM intern-only constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = WednesdayAMInternOnlyConstraint()
        assert constraint.name == "WednesdayAMInternOnly"
        assert constraint.constraint_type == ConstraintType.ROTATION
        assert constraint.priority == ConstraintPriority.HIGH

    def test_wednesday_constant(self):
        """Test Wednesday constant is correct (2 = Wednesday in Python)."""
        constraint = WednesdayAMInternOnlyConstraint()
        assert constraint.WEDNESDAY == 2
        # Verify with a known Wednesday
        known_wednesday = date(2025, 1, 8)  # Wednesday, Jan 8, 2025
        assert known_wednesday.weekday() == 2

    def test_is_wednesday_am_detection(self):
        """Test _is_wednesday_am correctly identifies Wednesday AM blocks."""
        constraint = WednesdayAMInternOnlyConstraint()

        # Wednesday AM - should be True
        wed_am = MockBlock(block_date=date(2025, 1, 8), time_of_day="AM")
        assert constraint._is_wednesday_am(wed_am) is True

        # Wednesday PM - should be False
        wed_pm = MockBlock(block_date=date(2025, 1, 8), time_of_day="PM")
        assert constraint._is_wednesday_am(wed_pm) is False

        # Tuesday AM - should be False
        tue_am = MockBlock(block_date=date(2025, 1, 7), time_of_day="AM")
        assert constraint._is_wednesday_am(tue_am) is False

        # Thursday AM - should be False
        thu_am = MockBlock(block_date=date(2025, 1, 9), time_of_day="AM")
        assert constraint._is_wednesday_am(thu_am) is False

    def test_validate_empty_assignments(self):
        """Test validate with no assignments passes (no violations)."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[am_block, pm_block],
            templates=[clinic_template],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_intern_on_wednesday_am(self):
        """Test validate passes when PGY-1 assigned to Wednesday AM clinic."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        # Create PGY-1 resident (intern)
        intern = MockPerson(
            person_type="resident",
            name="PGY-1 Resident",
            pgy_level=1,
        )

        # Assign intern to Wednesday AM clinic
        assignment = MockAssignment(
            person_id=intern.id,
            block_id=am_block.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[intern],
            faculty=[],
            blocks=[am_block, pm_block],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_pgy2_on_wednesday_am_violation(self):
        """Test validate fails when PGY-2 assigned to Wednesday AM clinic."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        # Create PGY-2 resident
        pgy2 = MockPerson(
            person_type="resident",
            name="PGY-2 Resident",
            pgy_level=2,
        )

        # Assign PGY-2 to Wednesday AM clinic (violation)
        assignment = MockAssignment(
            person_id=pgy2.id,
            block_id=am_block.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[pgy2],
            faculty=[],
            blocks=[am_block, pm_block],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "PGY-2" in result.violations[0].message
        assert "Wednesday AM clinic" in result.violations[0].message
        assert result.violations[0].severity == "HIGH"
        assert result.violations[0].person_id == pgy2.id
        assert result.violations[0].block_id == am_block.id

    def test_validate_pgy3_on_wednesday_am_violation(self):
        """Test validate fails when PGY-3 assigned to Wednesday AM clinic."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        # Create PGY-3 resident
        pgy3 = MockPerson(
            person_type="resident",
            name="PGY-3 Resident",
            pgy_level=3,
        )

        assignment = MockAssignment(
            person_id=pgy3.id,
            block_id=am_block.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[pgy3],
            faculty=[],
            blocks=[am_block, pm_block],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "PGY-3" in result.violations[0].message

    def test_validate_wednesday_pm_not_checked(self):
        """Test Wednesday PM assignments are not checked by this constraint."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        # PGY-2 on Wednesday PM is OK (constraint only checks AM)
        pgy2 = MockPerson(
            person_type="resident",
            name="PGY-2 Resident",
            pgy_level=2,
        )

        assignment = MockAssignment(
            person_id=pgy2.id,
            block_id=pm_block.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[pgy2],
            faculty=[],
            blocks=[am_block, pm_block],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_non_clinic_template_ignored(self):
        """Test non-clinic templates are not checked."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)

        # Non-clinic template (e.g., inpatient)
        inpatient_template = MockTemplate(
            name="Inpatient Ward",
            activity_type="inpatient",
        )

        # PGY-2 on Wednesday AM inpatient is OK (not clinic)
        pgy2 = MockPerson(
            person_type="resident",
            name="PGY-2 Resident",
            pgy_level=2,
        )

        assignment = MockAssignment(
            person_id=pgy2.id,
            block_id=am_block.id,
            rotation_template_id=inpatient_template.id,
        )

        context = SchedulingContext(
            residents=[pgy2],
            faculty=[],
            blocks=[am_block, pm_block],
            templates=[inpatient_template],
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_faculty_on_wednesday_am_ignored(self):
        """Test faculty assignments are not checked (only residents)."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        # Faculty on Wednesday AM clinic is OK (constraint only checks residents)
        faculty = MockPerson(
            person_type="faculty",
            name="Dr. Faculty",
        )

        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=am_block.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=[am_block, pm_block],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_mixed_pgy_levels(self):
        """Test validation with mix of PGY-1 and PGY-2/3."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        pgy1 = MockPerson(person_type="resident", name="PGY-1", pgy_level=1)
        pgy2 = MockPerson(person_type="resident", name="PGY-2", pgy_level=2)
        pgy3 = MockPerson(person_type="resident", name="PGY-3", pgy_level=3)

        assignments = [
            # PGY-1 on Wed AM - OK
            MockAssignment(
                person_id=pgy1.id,
                block_id=am_block.id,
                rotation_template_id=clinic_template.id,
            ),
            # PGY-2 on Wed AM - Violation
            MockAssignment(
                person_id=pgy2.id,
                block_id=am_block.id,
                rotation_template_id=clinic_template.id,
            ),
            # PGY-3 on Wed AM - Violation
            MockAssignment(
                person_id=pgy3.id,
                block_id=am_block.id,
                rotation_template_id=clinic_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=[pgy1, pgy2, pgy3],
            faculty=[],
            blocks=[am_block, pm_block],
            templates=[clinic_template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 2  # PGY-2 and PGY-3

        violation_persons = {v.person_id for v in result.violations}
        assert pgy2.id in violation_persons
        assert pgy3.id in violation_persons
        assert pgy1.id not in violation_persons

    def test_validate_no_clinic_templates(self):
        """Test early return when no clinic templates exist."""
        constraint = WednesdayAMInternOnlyConstraint()
        am_block, pm_block = create_wednesday_blocks(2025, 1, 1)

        pgy2 = MockPerson(person_type="resident", name="PGY-2", pgy_level=2)

        # Template is not a clinic
        non_clinic_template = MockTemplate(
            name="Admin",
            activity_type="admin",
        )

        assignment = MockAssignment(
            person_id=pgy2.id,
            block_id=am_block.id,
            rotation_template_id=non_clinic_template.id,
        )

        context = SchedulingContext(
            residents=[pgy2],
            faculty=[],
            blocks=[am_block, pm_block],
            templates=[non_clinic_template],
        )

        result = constraint.validate([assignment], context)
        # Should pass because no clinic templates to check
        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# Tests for WednesdayPMSingleFacultyConstraint
# ============================================================================


class TestWednesdayPMSingleFacultyConstraint:
    """Tests for Wednesday PM single faculty constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = WednesdayPMSingleFacultyConstraint()
        assert constraint.name == "WednesdayPMSingleFaculty"
        assert constraint.constraint_type == ConstraintType.ROTATION
        assert constraint.priority == ConstraintPriority.HIGH

    def test_is_regular_wednesday_pm_first_week(self):
        """Test _is_regular_wednesday_pm correctly identifies 1st Wed PM."""
        constraint = WednesdayPMSingleFacultyConstraint()

        # 1st Wednesday PM - should be True
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        assert constraint._is_regular_wednesday_pm(wed1_pm) is True
        assert constraint._is_regular_wednesday_pm(wed1_am) is False

    def test_is_regular_wednesday_pm_fourth_week(self):
        """Test _is_regular_wednesday_pm excludes 4th Wednesday (day >= 22)."""
        constraint = WednesdayPMSingleFacultyConstraint()

        # 4th Wednesday PM - should be False
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        assert wed4_pm.date.day >= 22  # Verify it's 4th week
        assert constraint._is_regular_wednesday_pm(wed4_pm) is False

    def test_is_regular_wednesday_pm_all_weeks(self):
        """Test all Wednesdays in a month (1st, 2nd, 3rd = True, 4th = False)."""
        constraint = WednesdayPMSingleFacultyConstraint()

        # 1st Wednesday
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        assert constraint._is_regular_wednesday_pm(wed1_pm) is True

        # 2nd Wednesday
        wed2_am, wed2_pm = create_wednesday_blocks(2025, 1, 2)
        assert constraint._is_regular_wednesday_pm(wed2_pm) is True

        # 3rd Wednesday
        wed3_am, wed3_pm = create_wednesday_blocks(2025, 1, 3)
        assert constraint._is_regular_wednesday_pm(wed3_pm) is True

        # 4th Wednesday
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        assert constraint._is_regular_wednesday_pm(wed4_pm) is False

    def test_validate_empty_assignments(self):
        """Test validate with no assignments fails (need exactly 1 faculty)."""
        constraint = WednesdayPMSingleFacultyConstraint()
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[wed1_am, wed1_pm],
            templates=[clinic_template],
        )

        result = constraint.validate([], context)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "0 faculty in clinic" in result.violations[0].message
        assert "need exactly 1" in result.violations[0].message
        assert result.violations[0].severity == "HIGH"

    def test_validate_exactly_one_faculty(self):
        """Test validate passes when exactly 1 faculty on Wed PM."""
        constraint = WednesdayPMSingleFacultyConstraint()
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty = MockPerson(person_type="faculty", name="Dr. Faculty")

        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=wed1_pm.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=[wed1_am, wed1_pm],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_two_faculty_violation(self):
        """Test validate fails when 2 faculty on Wed PM (need exactly 1)."""
        constraint = WednesdayPMSingleFacultyConstraint()
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty1 = MockPerson(person_type="faculty", name="Dr. One")
        faculty2 = MockPerson(person_type="faculty", name="Dr. Two")

        assignments = [
            MockAssignment(
                person_id=faculty1.id,
                block_id=wed1_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=faculty2.id,
                block_id=wed1_pm.id,
                rotation_template_id=clinic_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty1, faculty2],
            blocks=[wed1_am, wed1_pm],
            templates=[clinic_template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "2 faculty in clinic" in result.violations[0].message
        assert result.violations[0].details["count"] == 2

    def test_validate_fourth_wednesday_ignored(self):
        """Test 4th Wednesday PM is not checked by this constraint."""
        constraint = WednesdayPMSingleFacultyConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        clinic_template = MockTemplate(activity_type="outpatient")

        # No faculty on 4th Wed PM - should pass (not checked)
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_wednesday_am_ignored(self):
        """Test Wednesday AM is not checked by this constraint."""
        constraint = WednesdayPMSingleFacultyConstraint()
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty = MockPerson(person_type="faculty", name="Dr. Faculty")

        # Faculty on Wed AM (not checked) + no faculty on Wed PM
        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=wed1_am.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=[wed1_am, wed1_pm],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        # Should fail because Wed PM has 0 faculty
        assert result.satisfied is False
        assert len(result.violations) == 1

    def test_validate_non_clinic_template_ignored(self):
        """Test non-clinic templates are not checked."""
        constraint = WednesdayPMSingleFacultyConstraint()
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)

        inpatient_template = MockTemplate(
            name="Inpatient",
            activity_type="inpatient",
        )
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty = MockPerson(person_type="faculty", name="Dr. Faculty")

        # Faculty on Wed PM inpatient (not clinic)
        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=wed1_pm.id,
            rotation_template_id=inpatient_template.id,
        )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=[wed1_am, wed1_pm],
            templates=[clinic_template, inpatient_template],
        )

        result = constraint.validate([assignment], context)
        # Should fail because clinic has 0 faculty
        assert result.satisfied is False

    def test_validate_resident_assignments_ignored(self):
        """Test resident assignments don't count toward faculty coverage."""
        constraint = WednesdayPMSingleFacultyConstraint()
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        resident = MockPerson(person_type="resident", name="PGY-1", pgy_level=1)

        # Resident on Wed PM clinic (doesn't count as faculty)
        assignment = MockAssignment(
            person_id=resident.id,
            block_id=wed1_pm.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[wed1_am, wed1_pm],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        # Should fail because no faculty (resident doesn't count)
        assert result.satisfied is False

    def test_validate_multiple_wednesdays(self):
        """Test validation across multiple regular Wednesdays."""
        constraint = WednesdayPMSingleFacultyConstraint()

        # Create blocks for 1st, 2nd, 3rd Wed
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        wed2_am, wed2_pm = create_wednesday_blocks(2025, 1, 2)
        wed3_am, wed3_pm = create_wednesday_blocks(2025, 1, 3)

        clinic_template = MockTemplate(activity_type="outpatient")
        faculty = MockPerson(person_type="faculty", name="Dr. Faculty")

        assignments = [
            # 1st Wed - 1 faculty (OK)
            MockAssignment(
                person_id=faculty.id,
                block_id=wed1_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            # 2nd Wed - 1 faculty (OK)
            MockAssignment(
                person_id=faculty.id,
                block_id=wed2_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            # 3rd Wed - 0 faculty (Violation)
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=[wed1_am, wed1_pm, wed2_am, wed2_pm, wed3_am, wed3_pm],
            templates=[clinic_template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        assert len(result.violations) == 1  # 3rd Wed missing faculty

    def test_validate_no_clinic_templates(self):
        """Test early return when no clinic templates exist."""
        constraint = WednesdayPMSingleFacultyConstraint()
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)

        non_clinic_template = MockTemplate(
            name="Admin",
            activity_type="admin",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[wed1_am, wed1_pm],
            templates=[non_clinic_template],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# Tests for InvertedWednesdayConstraint
# ============================================================================


class TestInvertedWednesdayConstraint:
    """Tests for inverted (4th) Wednesday constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = InvertedWednesdayConstraint()
        assert constraint.name == "InvertedWednesday"
        assert constraint.constraint_type == ConstraintType.ROTATION
        assert constraint.priority == ConstraintPriority.HIGH

    def test_is_fourth_wednesday_detection(self):
        """Test _is_fourth_wednesday correctly identifies 4th Wed."""
        constraint = InvertedWednesdayConstraint()

        # 4th Wednesday - should be True
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        assert wed4_am.date.day >= 22
        assert constraint._is_fourth_wednesday(wed4_am) is True
        assert constraint._is_fourth_wednesday(wed4_pm) is True

        # 1st Wednesday - should be False
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        assert constraint._is_fourth_wednesday(wed1_am) is False
        assert constraint._is_fourth_wednesday(wed1_pm) is False

        # 2nd Wednesday - should be False
        wed2_am, wed2_pm = create_wednesday_blocks(2025, 1, 2)
        assert constraint._is_fourth_wednesday(wed2_am) is False

        # 3rd Wednesday - should be False
        wed3_am, wed3_pm = create_wednesday_blocks(2025, 1, 3)
        assert constraint._is_fourth_wednesday(wed3_am) is False

    def test_validate_empty_assignments(self):
        """Test validate with no assignments fails (need 1 AM + 1 PM)."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        clinic_template = MockTemplate(activity_type="outpatient")

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template],
        )

        result = constraint.validate([], context)
        assert result.satisfied is False
        # Should have 2 violations (0 AM faculty, 0 PM faculty)
        assert len(result.violations) == 2

    def test_validate_one_faculty_am_one_pm(self):
        """Test validate passes when 1 faculty AM, 1 different faculty PM."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty_am = MockPerson(person_type="faculty", name="Dr. AM")
        faculty_pm = MockPerson(person_type="faculty", name="Dr. PM")

        assignments = [
            MockAssignment(
                person_id=faculty_am.id,
                block_id=wed4_am.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=faculty_pm.id,
                block_id=wed4_pm.id,
                rotation_template_id=clinic_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty_am, faculty_pm],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_same_faculty_am_and_pm_violation(self):
        """Test validate fails when same faculty assigned both AM and PM."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty = MockPerson(person_type="faculty", name="Dr. Both")

        assignments = [
            MockAssignment(
                person_id=faculty.id,
                block_id=wed4_am.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=faculty.id,
                block_id=wed4_pm.id,
                rotation_template_id=clinic_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        # Should have violation for same faculty AM and PM
        assert any("Same faculty AM and PM" in v.message for v in result.violations)
        assert any("must be different" in v.message for v in result.violations)

    def test_validate_zero_faculty_am(self):
        """Test validate fails when 0 faculty on AM (need exactly 1)."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty_pm = MockPerson(person_type="faculty", name="Dr. PM")

        assignment = MockAssignment(
            person_id=faculty_pm.id,
            block_id=wed4_pm.id,
            rotation_template_id=clinic_template.id,
        )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty_pm],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template],
        )

        result = constraint.validate([assignment], context)
        assert result.satisfied is False
        # Should have violation for 0 AM faculty
        assert any("AM: 0 faculty" in v.message for v in result.violations)

    def test_validate_two_faculty_am_violation(self):
        """Test validate fails when 2 faculty on AM (need exactly 1)."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty_am1 = MockPerson(person_type="faculty", name="Dr. AM1")
        faculty_am2 = MockPerson(person_type="faculty", name="Dr. AM2")
        faculty_pm = MockPerson(person_type="faculty", name="Dr. PM")

        assignments = [
            MockAssignment(
                person_id=faculty_am1.id,
                block_id=wed4_am.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=faculty_am2.id,
                block_id=wed4_am.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=faculty_pm.id,
                block_id=wed4_pm.id,
                rotation_template_id=clinic_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty_am1, faculty_am2, faculty_pm],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        # Should have violation for 2 AM faculty
        assert any("AM: 2 faculty" in v.message for v in result.violations)

    def test_validate_two_faculty_pm_violation(self):
        """Test validate fails when 2 faculty on PM (need exactly 1)."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty_am = MockPerson(person_type="faculty", name="Dr. AM")
        faculty_pm1 = MockPerson(person_type="faculty", name="Dr. PM1")
        faculty_pm2 = MockPerson(person_type="faculty", name="Dr. PM2")

        assignments = [
            MockAssignment(
                person_id=faculty_am.id,
                block_id=wed4_am.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=faculty_pm1.id,
                block_id=wed4_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=faculty_pm2.id,
                block_id=wed4_pm.id,
                rotation_template_id=clinic_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[faculty_am, faculty_pm1, faculty_pm2],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template],
        )

        result = constraint.validate(assignments, context)
        assert result.satisfied is False
        # Should have violation for 2 PM faculty
        assert any("PM: 2 faculty" in v.message for v in result.violations)

    def test_validate_non_fourth_wednesday_ignored(self):
        """Test 1st, 2nd, 3rd Wednesdays are not checked."""
        constraint = InvertedWednesdayConstraint()
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        clinic_template = MockTemplate(activity_type="outpatient")

        # No assignments on 1st Wednesday - should pass (not checked)
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[wed1_am, wed1_pm],
            templates=[clinic_template],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_non_clinic_template_ignored(self):
        """Test non-clinic templates are not checked."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)

        inpatient_template = MockTemplate(
            name="Inpatient",
            activity_type="inpatient",
        )
        clinic_template = MockTemplate(activity_type="outpatient")

        faculty = MockPerson(person_type="faculty", name="Dr. Faculty")

        # Faculty on 4th Wed AM inpatient (not clinic)
        assignment = MockAssignment(
            person_id=faculty.id,
            block_id=wed4_am.id,
            rotation_template_id=inpatient_template.id,
        )

        context = SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template, inpatient_template],
        )

        result = constraint.validate([assignment], context)
        # Should fail because clinic has no faculty
        assert result.satisfied is False

    def test_validate_resident_assignments_ignored(self):
        """Test resident assignments don't count toward faculty coverage."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)
        clinic_template = MockTemplate(activity_type="outpatient")

        resident = MockPerson(person_type="resident", name="PGY-1", pgy_level=1)

        assignments = [
            # Residents on both AM and PM (don't count)
            MockAssignment(
                person_id=resident.id,
                block_id=wed4_am.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=resident.id,
                block_id=wed4_pm.id,
                rotation_template_id=clinic_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=[resident],
            faculty=[],
            blocks=[wed4_am, wed4_pm],
            templates=[clinic_template],
        )

        result = constraint.validate(assignments, context)
        # Should fail because no faculty (residents don't count)
        assert result.satisfied is False
        assert len(result.violations) == 2  # 0 AM faculty, 0 PM faculty

    def test_validate_no_clinic_templates(self):
        """Test early return when no clinic templates exist."""
        constraint = InvertedWednesdayConstraint()
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)

        non_clinic_template = MockTemplate(
            name="Admin",
            activity_type="admin",
        )

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[wed4_am, wed4_pm],
            templates=[non_clinic_template],
        )

        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestTemporalConstraintsIntegration:
    """Integration tests for combined temporal constraints."""

    def test_complete_month_all_constraints(self):
        """Test all constraints across a full month of Wednesdays."""
        # Create all 4 Wednesdays in January 2025
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        wed2_am, wed2_pm = create_wednesday_blocks(2025, 1, 2)
        wed3_am, wed3_pm = create_wednesday_blocks(2025, 1, 3)
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)

        all_blocks = [
            wed1_am,
            wed1_pm,
            wed2_am,
            wed2_pm,
            wed3_am,
            wed3_pm,
            wed4_am,
            wed4_pm,
        ]

        clinic_template = MockTemplate(activity_type="outpatient")

        # Create people
        pgy1 = MockPerson(person_type="resident", name="PGY-1", pgy_level=1)
        pgy2 = MockPerson(person_type="resident", name="PGY-2", pgy_level=2)
        faculty1 = MockPerson(person_type="faculty", name="Dr. One")
        faculty2 = MockPerson(person_type="faculty", name="Dr. Two")

        # Valid assignments
        assignments = [
            # 1st Wed AM: PGY-1 only (correct)
            MockAssignment(
                person_id=pgy1.id,
                block_id=wed1_am.id,
                rotation_template_id=clinic_template.id,
            ),
            # 1st Wed PM: 1 faculty (correct)
            MockAssignment(
                person_id=faculty1.id,
                block_id=wed1_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            # 2nd Wed AM: PGY-1 only (correct)
            MockAssignment(
                person_id=pgy1.id,
                block_id=wed2_am.id,
                rotation_template_id=clinic_template.id,
            ),
            # 2nd Wed PM: 1 faculty (correct)
            MockAssignment(
                person_id=faculty2.id,
                block_id=wed2_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            # 3rd Wed AM: PGY-1 only (correct)
            MockAssignment(
                person_id=pgy1.id,
                block_id=wed3_am.id,
                rotation_template_id=clinic_template.id,
            ),
            # 3rd Wed PM: 1 faculty (correct)
            MockAssignment(
                person_id=faculty1.id,
                block_id=wed3_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            # 4th Wed AM: 1 faculty (correct)
            MockAssignment(
                person_id=faculty1.id,
                block_id=wed4_am.id,
                rotation_template_id=clinic_template.id,
            ),
            # 4th Wed PM: 1 different faculty (correct)
            MockAssignment(
                person_id=faculty2.id,
                block_id=wed4_pm.id,
                rotation_template_id=clinic_template.id,
            ),
        ]

        context = SchedulingContext(
            residents=[pgy1, pgy2],
            faculty=[faculty1, faculty2],
            blocks=all_blocks,
            templates=[clinic_template],
        )

        # Validate all constraints
        constraint1 = WednesdayAMInternOnlyConstraint()
        constraint2 = WednesdayPMSingleFacultyConstraint()
        constraint3 = InvertedWednesdayConstraint()

        result1 = constraint1.validate(assignments, context)
        result2 = constraint2.validate(assignments, context)
        result3 = constraint3.validate(assignments, context)

        assert result1.satisfied is True
        assert result2.satisfied is True
        assert result3.satisfied is True

    def test_complete_month_multiple_violations(self):
        """Test multiple constraint violations across a month."""
        # Create all 4 Wednesdays
        wed1_am, wed1_pm = create_wednesday_blocks(2025, 1, 1)
        wed2_am, wed2_pm = create_wednesday_blocks(2025, 1, 2)
        wed3_am, wed3_pm = create_wednesday_blocks(2025, 1, 3)
        wed4_am, wed4_pm = create_wednesday_blocks(2025, 1, 4)

        all_blocks = [
            wed1_am,
            wed1_pm,
            wed2_am,
            wed2_pm,
            wed3_am,
            wed3_pm,
            wed4_am,
            wed4_pm,
        ]

        clinic_template = MockTemplate(activity_type="outpatient")

        pgy1 = MockPerson(person_type="resident", name="PGY-1", pgy_level=1)
        pgy2 = MockPerson(person_type="resident", name="PGY-2", pgy_level=2)
        faculty1 = MockPerson(person_type="faculty", name="Dr. One")
        faculty2 = MockPerson(person_type="faculty", name="Dr. Two")

        # Assignments with violations
        assignments = [
            # 1st Wed AM: PGY-2 (VIOLATION - should be PGY-1 only)
            MockAssignment(
                person_id=pgy2.id,
                block_id=wed1_am.id,
                rotation_template_id=clinic_template.id,
            ),
            # 1st Wed PM: 2 faculty (VIOLATION - should be 1)
            MockAssignment(
                person_id=faculty1.id,
                block_id=wed1_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            MockAssignment(
                person_id=faculty2.id,
                block_id=wed1_pm.id,
                rotation_template_id=clinic_template.id,
            ),
            # 2nd Wed AM: PGY-1 (correct)
            MockAssignment(
                person_id=pgy1.id,
                block_id=wed2_am.id,
                rotation_template_id=clinic_template.id,
            ),
            # 2nd Wed PM: 0 faculty (VIOLATION - should be 1)
            # 4th Wed AM: 0 faculty (VIOLATION - should be 1)
            # 4th Wed PM: 0 faculty (VIOLATION - should be 1)
        ]

        context = SchedulingContext(
            residents=[pgy1, pgy2],
            faculty=[faculty1, faculty2],
            blocks=all_blocks,
            templates=[clinic_template],
        )

        constraint1 = WednesdayAMInternOnlyConstraint()
        constraint2 = WednesdayPMSingleFacultyConstraint()
        constraint3 = InvertedWednesdayConstraint()

        result1 = constraint1.validate(assignments, context)
        result2 = constraint2.validate(assignments, context)
        result3 = constraint3.validate(assignments, context)

        # All should fail
        assert result1.satisfied is False
        assert result2.satisfied is False
        assert result3.satisfied is False

        # Check specific violations
        assert len(result1.violations) >= 1  # PGY-2 on Wed AM
        assert len(result2.violations) >= 2  # 2 faculty on 1st, 0 on 2nd and 3rd
        assert len(result3.violations) >= 2  # 0 AM and 0 PM on 4th Wed
