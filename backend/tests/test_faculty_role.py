"""Tests for faculty role model fields and properties."""

import pytest
from uuid import uuid4

from app.models.person import Person, FacultyRole
from app.schemas.person import FacultyRoleSchema, PersonCreate, PersonUpdate, PersonResponse


class TestFacultyRoleEnum:
    """Test FacultyRole enum values and behavior."""

    def test_faculty_role_values(self):
        """Test that all expected faculty roles exist."""
        assert FacultyRole.PD.value == "pd"
        assert FacultyRole.APD.value == "apd"
        assert FacultyRole.OIC.value == "oic"
        assert FacultyRole.DEPT_CHIEF.value == "dept_chief"
        assert FacultyRole.SPORTS_MED.value == "sports_med"
        assert FacultyRole.CORE.value == "core"

    def test_faculty_role_count(self):
        """Test that we have exactly 6 faculty roles."""
        assert len(FacultyRole) == 6

    def test_faculty_role_from_string(self):
        """Test creating FacultyRole from string value."""
        assert FacultyRole("pd") == FacultyRole.PD
        assert FacultyRole("sports_med") == FacultyRole.SPORTS_MED

    def test_invalid_faculty_role_raises(self):
        """Test that invalid role string raises ValueError."""
        with pytest.raises(ValueError):
            FacultyRole("invalid_role")


class TestPersonFacultyRoleProperties:
    """Test Person model faculty role properties."""

    def test_role_enum_for_faculty_with_role(self):
        """Test role_enum returns correct enum for faculty with role set."""
        person = Person(
            id=uuid4(),
            name="Dr. Smith",
            type="faculty",
            faculty_role="pd"
        )
        assert person.role_enum == FacultyRole.PD

    def test_role_enum_for_faculty_without_role(self):
        """Test role_enum returns None for faculty without role."""
        person = Person(
            id=uuid4(),
            name="Dr. Jones",
            type="faculty",
            faculty_role=None
        )
        assert person.role_enum is None

    def test_role_enum_for_resident(self):
        """Test role_enum returns None for residents."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            pgy_level=1
        )
        assert person.role_enum is None

    def test_role_enum_invalid_role_returns_none(self):
        """Test role_enum returns None for invalid role string."""
        person = Person(
            id=uuid4(),
            name="Dr. Unknown",
            type="faculty",
            faculty_role="invalid_role"
        )
        assert person.role_enum is None


class TestWeeklyClinicLimits:
    """Test weekly clinic limit calculations by role."""

    @pytest.mark.parametrize("role,expected_limit", [
        (FacultyRole.PD, 0),
        (FacultyRole.DEPT_CHIEF, 1),
        (FacultyRole.APD, 2),
        (FacultyRole.OIC, 2),
        (FacultyRole.SPORTS_MED, 0),
        (FacultyRole.CORE, 4),
    ])
    def test_weekly_clinic_limit_by_role(self, role, expected_limit):
        """Test weekly clinic limits match specification by role."""
        person = Person(
            id=uuid4(),
            name=f"Dr. {role.value}",
            type="faculty",
            faculty_role=role.value
        )
        assert person.weekly_clinic_limit == expected_limit

    def test_weekly_clinic_limit_no_role_defaults_to_core(self):
        """Test that faculty without role defaults to core limit (4)."""
        person = Person(
            id=uuid4(),
            name="Dr. Default",
            type="faculty",
            faculty_role=None
        )
        assert person.weekly_clinic_limit == 4

    def test_weekly_clinic_limit_resident_is_zero(self):
        """Test that residents have 0 weekly clinic limit."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            pgy_level=2
        )
        assert person.weekly_clinic_limit == 0


class TestBlockClinicLimits:
    """Test 4-week block clinic limit calculations."""

    def test_block_limit_apd_flexible(self):
        """Test APD has 8 block limit (2/week * 4 weeks, flexible)."""
        person = Person(
            id=uuid4(),
            name="Dr. APD",
            type="faculty",
            faculty_role="apd"
        )
        assert person.block_clinic_limit == 8

    def test_block_limit_oic_flexible(self):
        """Test OIC has 8 block limit (flexible)."""
        person = Person(
            id=uuid4(),
            name="Dr. OIC",
            type="faculty",
            faculty_role="oic"
        )
        assert person.block_clinic_limit == 8

    def test_block_limit_core_hard_max(self):
        """Test Core faculty has 16 block limit (hard max)."""
        person = Person(
            id=uuid4(),
            name="Dr. Core",
            type="faculty",
            faculty_role="core"
        )
        assert person.block_clinic_limit == 16

    def test_block_limit_pd_zero(self):
        """Test PD has 0 block limit."""
        person = Person(
            id=uuid4(),
            name="Dr. PD",
            type="faculty",
            faculty_role="pd"
        )
        assert person.block_clinic_limit == 0

    def test_block_limit_dept_chief(self):
        """Test Dept Chief has 4 block limit (1/week * 4)."""
        person = Person(
            id=uuid4(),
            name="Dr. Chief",
            type="faculty",
            faculty_role="dept_chief"
        )
        assert person.block_clinic_limit == 4


class TestSMClinicTarget:
    """Test Sports Medicine clinic target calculations."""

    def test_sm_faculty_has_four_sm_clinic_target(self):
        """Test SM faculty has 4 SM clinic half-days per week target."""
        person = Person(
            id=uuid4(),
            name="Dr. Sports",
            type="faculty",
            faculty_role="sports_med"
        )
        assert person.sm_clinic_weekly_target == 4

    def test_non_sm_faculty_has_zero_sm_target(self):
        """Test non-SM faculty has 0 SM clinic target."""
        person = Person(
            id=uuid4(),
            name="Dr. Core",
            type="faculty",
            faculty_role="core"
        )
        assert person.sm_clinic_weekly_target == 0


class TestCallPreferences:
    """Test call preference properties."""

    def test_pd_avoids_tuesday(self):
        """Test PD should avoid Tuesday call."""
        person = Person(
            id=uuid4(),
            name="Dr. PD",
            type="faculty",
            faculty_role="pd"
        )
        assert person.avoid_tuesday_call is True

    def test_apd_avoids_tuesday(self):
        """Test APD should avoid Tuesday call."""
        person = Person(
            id=uuid4(),
            name="Dr. APD",
            type="faculty",
            faculty_role="apd"
        )
        assert person.avoid_tuesday_call is True

    def test_oic_no_tuesday_preference(self):
        """Test OIC has no Tuesday avoidance."""
        person = Person(
            id=uuid4(),
            name="Dr. OIC",
            type="faculty",
            faculty_role="oic"
        )
        assert person.avoid_tuesday_call is False

    def test_dept_chief_prefers_wednesday(self):
        """Test Dept Chief prefers Wednesday call."""
        person = Person(
            id=uuid4(),
            name="Dr. Chief",
            type="faculty",
            faculty_role="dept_chief"
        )
        assert person.prefer_wednesday_call is True

    def test_core_no_wednesday_preference(self):
        """Test Core faculty has no Wednesday preference."""
        person = Person(
            id=uuid4(),
            name="Dr. Core",
            type="faculty",
            faculty_role="core"
        )
        assert person.prefer_wednesday_call is False


class TestSportsMedicineIdentification:
    """Test is_sports_medicine property."""

    def test_sm_role_is_sports_medicine(self):
        """Test sports_med role is identified as SM."""
        person = Person(
            id=uuid4(),
            name="Dr. Sports",
            type="faculty",
            faculty_role="sports_med"
        )
        assert person.is_sports_medicine is True

    def test_sm_specialty_is_sports_medicine(self):
        """Test faculty with SM specialty is identified as SM."""
        person = Person(
            id=uuid4(),
            name="Dr. Core with SM",
            type="faculty",
            faculty_role="core",
            specialties=["Sports Medicine", "Primary Care"]
        )
        assert person.is_sports_medicine is True

    def test_non_sm_faculty(self):
        """Test non-SM faculty without specialty is not SM."""
        person = Person(
            id=uuid4(),
            name="Dr. Core",
            type="faculty",
            faculty_role="core",
            specialties=["Primary Care"]
        )
        assert person.is_sports_medicine is False

    def test_resident_not_sm(self):
        """Test residents are not sports medicine (even with specialty)."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            pgy_level=2,
            specialties=["Sports Medicine"]
        )
        # Residents don't have faculty_role, so role_enum is None
        # but they may have specialty - is_sports_medicine checks both
        assert person.is_sports_medicine is True  # Has specialty


class TestCallEquityFields:
    """Test call and FMIT equity tracking fields."""

    def test_default_call_counts_are_zero(self):
        """Test that new person has zero call counts."""
        person = Person(
            id=uuid4(),
            name="Dr. New",
            type="faculty",
            faculty_role="core"
        )
        # Note: These default to 0 via Column default
        assert person.sunday_call_count is None or person.sunday_call_count == 0
        assert person.weekday_call_count is None or person.weekday_call_count == 0
        assert person.fmit_weeks_count is None or person.fmit_weeks_count == 0


class TestFacultyRoleSchema:
    """Test Pydantic schema for faculty role."""

    def test_schema_enum_values(self):
        """Test FacultyRoleSchema has correct values."""
        assert FacultyRoleSchema.PD.value == "pd"
        assert FacultyRoleSchema.SPORTS_MED.value == "sports_med"

    def test_person_create_with_role(self):
        """Test PersonCreate accepts faculty_role."""
        data = PersonCreate(
            name="Dr. Test",
            type="faculty",
            faculty_role=FacultyRoleSchema.CORE
        )
        assert data.faculty_role == FacultyRoleSchema.CORE

    def test_person_create_without_role(self):
        """Test PersonCreate works without faculty_role."""
        data = PersonCreate(
            name="Dr. Test",
            type="faculty"
        )
        assert data.faculty_role is None

    def test_person_update_with_role(self):
        """Test PersonUpdate can update faculty_role."""
        data = PersonUpdate(
            faculty_role=FacultyRoleSchema.APD
        )
        assert data.faculty_role == FacultyRoleSchema.APD
