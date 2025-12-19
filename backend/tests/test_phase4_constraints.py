"""Tests for Phase 4 constraints: SM alignment and Post-call assignments."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.scheduling.constraints.sports_medicine import SMResidentFacultyAlignmentConstraint
from app.scheduling.constraints.post_call import PostCallAutoAssignmentConstraint
from app.scheduling.constraints.fmit import is_sun_thurs
from app.scheduling.constraints.base import (
    ConstraintResult,
    ConstraintViolation,
    SchedulingContext,
)


class TestSMResidentFacultyAlignmentConstraint:
    """Tests for SM resident/faculty alignment constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = SMResidentFacultyAlignmentConstraint()
        assert constraint.name == "SMResidentFacultyAlignment"
        assert constraint.priority.value == 75  # HIGH

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = SMResidentFacultyAlignmentConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_validate_no_sm_templates(self):
        """Test validate returns satisfied when no SM templates exist."""
        constraint = SMResidentFacultyAlignmentConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],  # No SM templates
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_sm_faculty_detection_by_role(self):
        """Test that SM faculty is detected by faculty_role field."""
        constraint = SMResidentFacultyAlignmentConstraint()

        # Create mock faculty with sports_med role
        class MockFaculty:
            def __init__(self, faculty_role=None, is_sports_medicine=False):
                self.id = uuid4()
                self.faculty_role = faculty_role
                self.is_sports_medicine = is_sports_medicine

        context = SchedulingContext(
            residents=[],
            faculty=[
                MockFaculty(faculty_role='sports_med'),
                MockFaculty(faculty_role='core'),
            ],
            blocks=[],
            templates=[],
        )

        sm_faculty = constraint._get_sm_faculty(context)
        assert len(sm_faculty) == 1
        assert sm_faculty[0].faculty_role == 'sports_med'

    def test_sm_faculty_detection_by_flag(self):
        """Test that SM faculty is detected by is_sports_medicine flag."""
        constraint = SMResidentFacultyAlignmentConstraint()

        class MockFaculty:
            def __init__(self, is_sports_medicine=False):
                self.id = uuid4()
                self.is_sports_medicine = is_sports_medicine

        context = SchedulingContext(
            residents=[],
            faculty=[
                MockFaculty(is_sports_medicine=True),
                MockFaculty(is_sports_medicine=False),
            ],
            blocks=[],
            templates=[],
        )

        sm_faculty = constraint._get_sm_faculty(context)
        assert len(sm_faculty) == 1
        assert sm_faculty[0].is_sports_medicine is True

    def test_sm_template_detection_by_specialty(self):
        """Test SM templates detected by requires_specialty field."""
        constraint = SMResidentFacultyAlignmentConstraint()

        class MockTemplate:
            def __init__(self, name, requires_specialty=None):
                self.id = uuid4()
                self.name = name
                self.requires_specialty = requires_specialty

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[
                MockTemplate("SM Clinic", requires_specialty="Sports Medicine"),
                MockTemplate("Regular Clinic"),
            ],
        )

        sm_templates = constraint._get_sm_template_ids(context)
        assert len(sm_templates) == 1

    def test_sm_template_detection_by_name(self):
        """Test SM templates detected by name containing 'Sports Medicine'."""
        constraint = SMResidentFacultyAlignmentConstraint()

        class MockTemplate:
            def __init__(self, name):
                self.id = uuid4()
                self.name = name

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[
                MockTemplate("Sports Medicine Clinic"),
                MockTemplate("Regular Clinic"),
            ],
        )

        sm_templates = constraint._get_sm_template_ids(context)
        assert len(sm_templates) == 1


class TestPostCallAutoAssignmentConstraint:
    """Tests for post-call auto-assignment constraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes with correct properties."""
        constraint = PostCallAutoAssignmentConstraint()
        assert constraint.name == "PostCallAutoAssignment"
        assert constraint.priority.value == 75  # HIGH
        assert constraint.PCAT_ACTIVITY == "PCAT"
        assert constraint.DO_ACTIVITY == "DO"

    def test_validate_empty_assignments(self):
        """Test validate returns satisfied for empty assignments."""
        constraint = PostCallAutoAssignmentConstraint()
        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )
        result = constraint.validate([], context)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_pcat_template_detection(self):
        """Test PCAT template is found by name."""
        constraint = PostCallAutoAssignmentConstraint()

        class MockTemplate:
            def __init__(self, name, abbreviation=None):
                self.id = uuid4()
                self.name = name
                self.abbreviation = abbreviation

        pcat_template = MockTemplate("PCAT", abbreviation="PCAT")
        do_template = MockTemplate("DO", abbreviation="DO")
        regular = MockTemplate("Regular Clinic")

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[pcat_template, do_template, regular],
        )

        found_pcat = constraint._find_template_id(context, "PCAT")
        found_do = constraint._find_template_id(context, "DO")

        assert found_pcat == pcat_template.id
        assert found_do == do_template.id

    def test_template_detection_by_abbreviation(self):
        """Test template detection works with abbreviation field."""
        constraint = PostCallAutoAssignmentConstraint()

        class MockTemplate:
            def __init__(self, name, abbreviation=None):
                self.id = uuid4()
                self.name = name
                self.abbreviation = abbreviation

        template = MockTemplate("Post-Call Attending", abbreviation="PCAT")

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[template],
        )

        found = constraint._find_template_id(context, "PCAT")
        assert found == template.id

    def test_next_day_calculation(self):
        """Test that next day after call is correctly calculated."""
        # Sunday call -> Monday post-call
        sunday = date(2025, 1, 5)
        monday = sunday + timedelta(days=1)
        assert monday == date(2025, 1, 6)
        assert monday.weekday() == 0  # Monday

        # Thursday call -> Friday post-call
        thursday = date(2025, 1, 9)
        friday = thursday + timedelta(days=1)
        assert friday == date(2025, 1, 10)
        assert friday.weekday() == 4  # Friday

    def test_sun_thurs_call_days(self):
        """Test that only Sun-Thurs are valid overnight call days for post-call."""
        # Sun-Thurs should trigger post-call assignments
        sunday = date(2025, 1, 5)
        monday = date(2025, 1, 6)
        tuesday = date(2025, 1, 7)
        wednesday = date(2025, 1, 8)
        thursday = date(2025, 1, 9)

        assert is_sun_thurs(sunday) is True
        assert is_sun_thurs(monday) is True
        assert is_sun_thurs(tuesday) is True
        assert is_sun_thurs(wednesday) is True
        assert is_sun_thurs(thursday) is True

        # Friday/Saturday call handled by FMIT - no post-call assignments
        friday = date(2025, 1, 3)
        saturday = date(2025, 1, 4)

        assert is_sun_thurs(friday) is False
        assert is_sun_thurs(saturday) is False

    def test_blocks_grouped_by_date_time(self):
        """Test block grouping by date and time_of_day."""
        constraint = PostCallAutoAssignmentConstraint()

        class MockBlock:
            def __init__(self, block_date, time_of_day):
                self.id = uuid4()
                self.date = block_date
                self.time_of_day = time_of_day

        monday = date(2025, 1, 6)
        blocks = [
            MockBlock(monday, "AM"),
            MockBlock(monday, "PM"),
            MockBlock(monday + timedelta(days=1), "AM"),
        ]

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=blocks,
            templates=[],
        )

        grouped = constraint._group_blocks_by_date_time(context)

        assert len(grouped[(monday, "AM")]) == 1
        assert len(grouped[(monday, "PM")]) == 1
        assert len(grouped[(monday + timedelta(days=1), "AM")]) == 1


class TestPostCallConstraintValidation:
    """Test post-call constraint validation scenarios."""

    def test_extract_call_assignments_empty(self):
        """Test extraction returns empty list when no call assignments."""
        constraint = PostCallAutoAssignmentConstraint()

        class MockAssignment:
            def __init__(self):
                self.id = uuid4()
                # No call_type attribute

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        assignments = [MockAssignment()]
        call_assignments = constraint._extract_call_assignments(assignments, context)
        assert len(call_assignments) == 0

    def test_extract_call_assignments_overnight(self):
        """Test extraction finds overnight call assignments."""
        constraint = PostCallAutoAssignmentConstraint()

        class MockCallAssignment:
            def __init__(self, call_type):
                self.id = uuid4()
                self.call_type = call_type

        context = SchedulingContext(
            residents=[],
            faculty=[],
            blocks=[],
            templates=[],
        )

        assignments = [
            MockCallAssignment("overnight"),
            MockCallAssignment("day"),
        ]
        call_assignments = constraint._extract_call_assignments(assignments, context)
        assert len(call_assignments) == 1
        assert call_assignments[0].call_type == "overnight"


class TestPhase4Integration:
    """Integration tests for Phase 4 constraints working together."""

    def test_sm_and_post_call_constraints_independent(self):
        """Test that SM alignment and post-call constraints are independent."""
        sm_constraint = SMResidentFacultyAlignmentConstraint()
        post_call_constraint = PostCallAutoAssignmentConstraint()

        # Both should have different names
        assert sm_constraint.name != post_call_constraint.name

        # Both should be hard constraints
        assert sm_constraint.__class__.__bases__[0].__name__ == "HardConstraint"
        assert post_call_constraint.__class__.__bases__[0].__name__ == "HardConstraint"

        # Both should have HIGH priority
        assert sm_constraint.priority.value == 75
        assert post_call_constraint.priority.value == 75

    def test_constraints_can_be_imported_from_package(self):
        """Test constraints are properly exported from package."""
        from app.scheduling.constraints import (
            SMResidentFacultyAlignmentConstraint,
            PostCallAutoAssignmentConstraint,
        )

        assert SMResidentFacultyAlignmentConstraint is not None
        assert PostCallAutoAssignmentConstraint is not None
