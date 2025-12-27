"""
Tests for Faculty Primary Duty Clinic Constraints.

Tests the Airtable-driven constraints for faculty clinic assignments:
- FacultyPrimaryDutyClinicConstraint (min/max clinic half-days)
- FacultyDayAvailabilityConstraint (day-of-week availability)
- FacultyClinicEquitySoftConstraint (optimization toward target)
"""

import uuid
from collections import namedtuple
from datetime import date, timedelta

import pytest

from app.scheduling.constraints.base import SchedulingContext
from app.scheduling.constraints.primary_duty import (
    FacultyClinicEquitySoftConstraint,
    FacultyDayAvailabilityConstraint,
    FacultyPrimaryDutyClinicConstraint,
    PrimaryDutyConfig,
    load_primary_duties_config,
)


# Simple mock objects for testing
class MockPerson:
    """Mock Person for testing."""

    def __init__(
        self,
        name: str = "Test Faculty",
        person_type: str = "faculty",
        primary_duty: str | None = None,
    ):
        self.id = uuid.uuid4()
        self.name = name
        self.type = person_type
        self.primary_duty = primary_duty


class MockBlock:
    """Mock Block for testing."""

    def __init__(self, block_date: date, time_of_day: str = "am"):
        self.id = uuid.uuid4()
        self.date = block_date
        self.time_of_day = time_of_day


class MockTemplate:
    """Mock RotationTemplate for testing."""

    def __init__(self, name: str, activity_type: str = "outpatient"):
        self.id = uuid.uuid4()
        self.name = name
        self.activity_type = activity_type


# Named tuple for mock assignments
MockAssignment = namedtuple(
    "MockAssignment", ["person_id", "block_id", "rotation_template_id"]
)


class TestPrimaryDutyConfig:
    """Tests for PrimaryDutyConfig parsing."""

    def test_from_airtable_record_basic(self):
        """Test parsing a basic Airtable record."""
        record = {
            "id": "rec123",
            "fields": {
                "primaryDuty": "Faculty Alpha",
                "Clinic Minimum Half-Days Per Week": 2,
                "Clinic Maximum Half-Days Per Week": 4,
                "availableMonday": True,
                "availableTuesday": True,
                "availableWednesday": False,
                "availableThursday": True,
                "availableFriday": True,
            },
        }

        config = PrimaryDutyConfig.from_airtable_record(record)

        assert config.duty_id == "rec123"
        assert config.duty_name == "Faculty Alpha"
        assert config.clinic_min_per_week == 2
        assert config.clinic_max_per_week == 4
        assert config.available_days == {0, 1, 3, 4}  # Mon, Tue, Thu, Fri
        assert 2 not in config.available_days  # Wed not available

    def test_from_airtable_record_defaults(self):
        """Test that missing fields get default values."""
        record = {
            "id": "rec456",
            "fields": {
                "primaryDuty": "Deployed Alpha",
                # No clinic fields, no availability
            },
        }

        config = PrimaryDutyConfig.from_airtable_record(record)

        assert config.duty_name == "Deployed Alpha"
        assert config.clinic_min_per_week == 0  # Default
        assert config.clinic_max_per_week == 10  # Default
        assert config.available_days == {0, 1, 2, 3, 4}  # All weekdays

    def test_from_airtable_record_with_templates(self):
        """Test parsing record with clinic templates."""
        record = {
            "id": "rec789",
            "fields": {
                "primaryDuty": "Faculty Bravo",
                "attendingClinicTemplates": ["recA", "recB", "recC"],
                "Faculty": ["recFac1"],
            },
        }

        config = PrimaryDutyConfig.from_airtable_record(record)

        assert config.allowed_clinic_templates == {"recA", "recB", "recC"}
        assert config.faculty_ids == ["recFac1"]


class TestLoadPrimaryDutiesConfig:
    """Tests for loading configuration from JSON."""

    def test_load_from_default_path(self):
        """Test loading from the default sanitized_primary_duties.json."""
        configs = load_primary_duties_config()

        # Should have loaded some records (if file exists)
        if configs:
            assert len(configs) > 0
            # Check that we can access by name
            assert "Faculty Alpha" in configs or "Program Director" in configs

    def test_load_from_missing_file(self, tmp_path):
        """Test graceful handling of missing file."""
        missing_path = tmp_path / "nonexistent.json"
        configs = load_primary_duties_config(missing_path)

        assert configs == {}


class TestFacultyPrimaryDutyClinicConstraint:
    """Tests for FacultyPrimaryDutyClinicConstraint."""

    @pytest.fixture
    def duty_configs(self):
        """Create test duty configs."""
        return {
            "Faculty Alpha": PrimaryDutyConfig(
                duty_id="rec1",
                duty_name="Faculty Alpha",
                clinic_min_per_week=2,
                clinic_max_per_week=4,
            ),
            "Program Director": PrimaryDutyConfig(
                duty_id="rec2",
                duty_name="Program Director",
                clinic_min_per_week=0,
                clinic_max_per_week=0,
            ),
        }

    @pytest.fixture
    def constraint(self, duty_configs):
        """Create constraint with test configs."""
        return FacultyPrimaryDutyClinicConstraint(duty_configs=duty_configs)

    @pytest.fixture
    def context(self):
        """Create a basic scheduling context for testing."""
        # Create faculty
        faculty_alpha = MockPerson("Dr. Alpha", "faculty", "Faculty Alpha")
        faculty_pd = MockPerson("Dr. PD", "faculty", "Program Director")

        # Create a week of blocks (Mon-Fri, AM/PM)
        base_date = date(2025, 1, 6)  # A Monday
        blocks = []
        for day_offset in range(5):  # Mon-Fri
            block_date = base_date + timedelta(days=day_offset)
            blocks.append(MockBlock(block_date, "am"))
            blocks.append(MockBlock(block_date, "pm"))

        # Create templates
        clinic_template = MockTemplate("FM Clinic", "outpatient")
        inpatient_template = MockTemplate("Inpatient", "inpatient")

        return SchedulingContext(
            residents=[],
            faculty=[faculty_alpha, faculty_pd],
            blocks=blocks,
            templates=[clinic_template, inpatient_template],
        )

    def test_validate_meets_minimum(self, constraint, context):
        """Test that meeting minimum requirement passes."""
        faculty = context.faculty[0]  # Faculty Alpha (min 2)
        clinic_template = context.templates[0]

        # Assign 3 clinic sessions (meets min of 2)
        assignments = [
            MockAssignment(faculty.id, context.blocks[0].id, clinic_template.id),
            MockAssignment(faculty.id, context.blocks[1].id, clinic_template.id),
            MockAssignment(faculty.id, context.blocks[2].id, clinic_template.id),
        ]

        result = constraint.validate(assignments, context)

        assert result.satisfied
        assert len(result.violations) == 0

    def test_validate_below_minimum(self, constraint, context):
        """Test that being below minimum creates violation."""
        faculty = context.faculty[0]  # Faculty Alpha (min 2)
        clinic_template = context.templates[0]

        # Assign only 1 clinic session (below min of 2)
        assignments = [
            MockAssignment(faculty.id, context.blocks[0].id, clinic_template.id),
        ]

        result = constraint.validate(assignments, context)

        assert not result.satisfied
        assert len(result.violations) >= 1
        assert "minimum" in result.violations[0].message.lower()

    def test_validate_exceeds_maximum(self, constraint, context):
        """Test that exceeding maximum creates violation."""
        faculty = context.faculty[0]  # Faculty Alpha (max 4)
        clinic_template = context.templates[0]

        # Assign 5 clinic sessions (exceeds max of 4)
        assignments = [
            MockAssignment(faculty.id, context.blocks[i].id, clinic_template.id)
            for i in range(5)
        ]

        result = constraint.validate(assignments, context)

        assert not result.satisfied
        assert len(result.violations) >= 1
        assert "exceeds" in result.violations[0].message.lower()

    def test_validate_pd_no_clinic(self, constraint, context):
        """Test that PD with 0 max can't have clinic assignments."""
        pd_faculty = context.faculty[1]  # Program Director (max 0)
        clinic_template = context.templates[0]

        # Assign 1 clinic session (exceeds max of 0)
        assignments = [
            MockAssignment(pd_faculty.id, context.blocks[0].id, clinic_template.id),
        ]

        result = constraint.validate(assignments, context)

        assert not result.satisfied
        assert len(result.violations) >= 1

    def test_validate_ignores_inpatient(self, constraint, context):
        """Test that inpatient assignments are not counted as clinic."""
        faculty = context.faculty[0]
        inpatient_template = context.templates[1]

        # Assign only inpatient (should not satisfy clinic minimum)
        assignments = [
            MockAssignment(faculty.id, context.blocks[0].id, inpatient_template.id),
            MockAssignment(faculty.id, context.blocks[1].id, inpatient_template.id),
        ]

        result = constraint.validate(assignments, context)

        # Should fail because clinic minimum not met
        assert not result.satisfied


class TestFacultyDayAvailabilityConstraint:
    """Tests for FacultyDayAvailabilityConstraint."""

    @pytest.fixture
    def duty_configs(self):
        """Create test duty configs with day restrictions."""
        return {
            "Faculty Alpha": PrimaryDutyConfig(
                duty_id="rec1",
                duty_name="Faculty Alpha",
                available_days={0, 1, 3, 4},  # Mon, Tue, Thu, Fri (no Wed)
            ),
        }

    @pytest.fixture
    def constraint(self, duty_configs):
        """Create constraint with test configs."""
        return FacultyDayAvailabilityConstraint(duty_configs=duty_configs)

    @pytest.fixture
    def context(self):
        """Create context with a week of blocks."""
        faculty = MockPerson("Dr. Alpha", "faculty", "Faculty Alpha")

        # Create blocks for Mon-Fri
        base_date = date(2025, 1, 6)  # Monday
        blocks = []
        for day_offset in range(5):
            block_date = base_date + timedelta(days=day_offset)
            blocks.append(MockBlock(block_date, "am"))

        clinic_template = MockTemplate("FM Clinic", "outpatient")

        return SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[clinic_template],
        )

    def test_validate_available_day(self, constraint, context):
        """Test assignment on available day passes."""
        faculty = context.faculty[0]
        clinic_template = context.templates[0]
        monday_block = context.blocks[0]  # Monday is available

        assignments = [
            MockAssignment(faculty.id, monday_block.id, clinic_template.id),
        ]

        result = constraint.validate(assignments, context)

        assert result.satisfied
        assert len(result.violations) == 0

    def test_validate_unavailable_day(self, constraint, context):
        """Test assignment on unavailable day creates violation."""
        faculty = context.faculty[0]
        clinic_template = context.templates[0]
        wednesday_block = context.blocks[2]  # Wednesday is NOT available

        assignments = [
            MockAssignment(faculty.id, wednesday_block.id, clinic_template.id),
        ]

        result = constraint.validate(assignments, context)

        assert not result.satisfied
        assert len(result.violations) == 1
        assert "wednesday" in result.violations[0].message.lower()


class TestFacultyClinicEquitySoftConstraint:
    """Tests for FacultyClinicEquitySoftConstraint (soft constraint)."""

    @pytest.fixture
    def duty_configs(self):
        """Create test duty configs."""
        return {
            "Faculty Alpha": PrimaryDutyConfig(
                duty_id="rec1",
                duty_name="Faculty Alpha",
                clinic_min_per_week=2,
                clinic_max_per_week=4,
                # Target = (2+4)//2 = 3
            ),
        }

    @pytest.fixture
    def constraint(self, duty_configs):
        """Create constraint with test configs."""
        return FacultyClinicEquitySoftConstraint(weight=15.0, duty_configs=duty_configs)

    @pytest.fixture
    def context(self):
        """Create context for testing."""
        faculty = MockPerson("Dr. Alpha", "faculty", "Faculty Alpha")

        base_date = date(2025, 1, 6)  # Monday
        blocks = []
        for day_offset in range(5):
            block_date = base_date + timedelta(days=day_offset)
            blocks.append(MockBlock(block_date, "am"))
            blocks.append(MockBlock(block_date, "pm"))

        clinic_template = MockTemplate("FM Clinic", "outpatient")

        return SchedulingContext(
            residents=[],
            faculty=[faculty],
            blocks=blocks,
            templates=[clinic_template],
        )

    def test_soft_constraint_always_satisfied(self, constraint, context):
        """Test that soft constraints are always 'satisfied'."""
        faculty = context.faculty[0]
        clinic_template = context.templates[0]

        # Below target (target is 3)
        assignments = [
            MockAssignment(faculty.id, context.blocks[0].id, clinic_template.id),
        ]

        result = constraint.validate(assignments, context)

        # Soft constraints return satisfied=True
        assert result.satisfied
        # But there should be a penalty
        assert result.penalty > 0

    def test_at_target_no_penalty(self, constraint, context):
        """Test that being at target has low/no penalty."""
        faculty = context.faculty[0]
        clinic_template = context.templates[0]

        # At target (3 assignments)
        assignments = [
            MockAssignment(faculty.id, context.blocks[0].id, clinic_template.id),
            MockAssignment(faculty.id, context.blocks[1].id, clinic_template.id),
            MockAssignment(faculty.id, context.blocks[2].id, clinic_template.id),
        ]

        result = constraint.validate(assignments, context)

        assert result.satisfied
        assert result.penalty == 0  # At target = no penalty
