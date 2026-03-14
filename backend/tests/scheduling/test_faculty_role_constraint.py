"""Tests for faculty role constraints (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.faculty_role import (
    FacultyRoleClinicConstraint,
    SMFacultyClinicConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", **kwargs):
    """Build a mock person with optional attributes."""
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _block(bid=None, block_date=None, time_of_day="AM"):
    """Build a mock block."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )


def _template(tid=None, name="Template", **kwargs):
    """Build a mock template with optional attributes."""
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _assignment(person_id, block_id, rotation_template_id=None):
    """Build a mock assignment."""
    return SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
    )


def _context(residents=None, blocks=None, faculty=None, templates=None):
    """Build a SchedulingContext."""
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )


# ==================== FacultyRoleClinicConstraint Init ====================


class TestFacultyRoleClinicInit:
    """Test FacultyRoleClinicConstraint initialization."""

    def test_name(self):
        c = FacultyRoleClinicConstraint()
        assert c.name == "FacultyRoleClinic"

    def test_type(self):
        c = FacultyRoleClinicConstraint()
        assert c.constraint_type == ConstraintType.CAPACITY

    def test_priority(self):
        c = FacultyRoleClinicConstraint()
        assert c.priority == ConstraintPriority.HIGH


# ==================== _get_week_start Tests ====================


class TestGetWeekStart:
    """Test _get_week_start helper (returns Monday of the week)."""

    def test_monday_returns_itself(self):
        c = FacultyRoleClinicConstraint()
        monday = date(2025, 3, 3)  # Monday
        assert c._get_week_start(monday) == monday

    def test_tuesday_returns_monday(self):
        c = FacultyRoleClinicConstraint()
        tuesday = date(2025, 3, 4)
        assert c._get_week_start(tuesday) == date(2025, 3, 3)

    def test_wednesday_returns_monday(self):
        c = FacultyRoleClinicConstraint()
        wednesday = date(2025, 3, 5)
        assert c._get_week_start(wednesday) == date(2025, 3, 3)

    def test_friday_returns_monday(self):
        c = FacultyRoleClinicConstraint()
        friday = date(2025, 3, 7)
        assert c._get_week_start(friday) == date(2025, 3, 3)

    def test_sunday_returns_monday(self):
        c = FacultyRoleClinicConstraint()
        sunday = date(2025, 3, 9)
        assert c._get_week_start(sunday) == date(2025, 3, 3)

    def test_next_monday_returns_itself(self):
        c = FacultyRoleClinicConstraint()
        next_mon = date(2025, 3, 10)
        assert c._get_week_start(next_mon) == next_mon


# ==================== _group_blocks_by_week Tests ====================


class TestGroupBlocksByWeek:
    """Test _group_blocks_by_week helper."""

    def test_same_week_single_group(self):
        c = FacultyRoleClinicConstraint()
        b1 = _block(block_date=date(2025, 3, 3))  # Mon
        b2 = _block(block_date=date(2025, 3, 5))  # Wed
        b3 = _block(block_date=date(2025, 3, 7))  # Fri
        result = c._group_blocks_by_week([b1, b2, b3])
        assert len(result) == 1
        assert len(result[date(2025, 3, 3)]) == 3

    def test_two_weeks_two_groups(self):
        c = FacultyRoleClinicConstraint()
        b1 = _block(block_date=date(2025, 3, 3))  # Week 1
        b2 = _block(block_date=date(2025, 3, 10))  # Week 2
        result = c._group_blocks_by_week([b1, b2])
        assert len(result) == 2
        assert date(2025, 3, 3) in result
        assert date(2025, 3, 10) in result

    def test_empty_blocks(self):
        c = FacultyRoleClinicConstraint()
        result = c._group_blocks_by_week([])
        assert len(result) == 0


# ==================== _get_effective_clinic_limits Tests ====================


class TestGetEffectiveClinicLimits:
    """Test _get_effective_clinic_limits helper."""

    def test_person_specific_max_used(self):
        """Person-specific max > 0 takes precedence."""
        c = FacultyRoleClinicConstraint()
        f = _person(
            weekly_clinic_limit=4,
            max_clinic_halfdays_per_week=3,
        )
        min_limit, max_limit = c._get_effective_clinic_limits(f)
        assert max_limit == 3
        assert min_limit == 0  # default min

    def test_person_specific_max_and_min(self):
        """Both person-specific max and min used."""
        c = FacultyRoleClinicConstraint()
        f = _person(
            weekly_clinic_limit=4,
            max_clinic_halfdays_per_week=3,
            min_clinic_halfdays_per_week=2,
        )
        min_limit, max_limit = c._get_effective_clinic_limits(f)
        assert max_limit == 3
        assert min_limit == 2

    def test_person_max_zero_is_intentional(self):
        """Person-specific max == 0 is intentional (e.g., PD, Adjunct)."""
        c = FacultyRoleClinicConstraint()
        f = _person(
            weekly_clinic_limit=4,
            max_clinic_halfdays_per_week=0,
        )
        min_limit, max_limit = c._get_effective_clinic_limits(f)
        assert max_limit == 0  # DB value of 0 is respected, not a fallback
        assert min_limit == 0

    def test_person_max_none_falls_back(self):
        """Person-specific max == None falls back to role-based."""
        c = FacultyRoleClinicConstraint()
        f = _person(
            weekly_clinic_limit=2,
            max_clinic_halfdays_per_week=None,
        )
        min_limit, max_limit = c._get_effective_clinic_limits(f)
        assert max_limit == 2
        assert min_limit == 0

    def test_no_person_attrs_falls_back(self):
        """No person-specific attrs at all falls back to role-based."""
        c = FacultyRoleClinicConstraint()
        f = _person(weekly_clinic_limit=1)
        min_limit, max_limit = c._get_effective_clinic_limits(f)
        assert max_limit == 1
        assert min_limit == 0

    def test_person_min_only_no_effect(self):
        """Person min set but max not set -> still role-based."""
        c = FacultyRoleClinicConstraint()
        f = _person(
            weekly_clinic_limit=4,
            min_clinic_halfdays_per_week=2,
        )
        min_limit, max_limit = c._get_effective_clinic_limits(f)
        assert max_limit == 4
        assert min_limit == 0  # min only used with person-specific max


# ==================== FacultyRoleClinicConstraint validate Tests ====================


class TestFacultyRoleClinicValidate:
    """Test FacultyRoleClinicConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = FacultyRoleClinicConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_non_clinic_template_satisfied(self):
        """Assignments to non-clinic template are not counted."""
        c = FacultyRoleClinicConstraint()
        fac = _person(
            name="Dr. Core",
            faculty_role="core",
            weekly_clinic_limit=4,
        )
        t = _template(name="FMIT")  # No rotation_type -> not clinic
        b1 = _block()
        ctx = _context(faculty=[fac], blocks=[b1], templates=[t])

        a = _assignment(fac.id, b1.id, rotation_template_id=t.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_within_max_limit_satisfied(self):
        """Faculty within weekly max -> satisfied."""
        c = FacultyRoleClinicConstraint()
        fac = _person(
            name="Dr. Core",
            faculty_role="core",
            weekly_clinic_limit=4,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 3))  # Mon
        b2 = _block(block_date=date(2025, 3, 4))  # Tue
        ctx = _context(faculty=[fac], blocks=[b1, b2], templates=[clinic])

        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=clinic.id),
            _assignment(fac.id, b2.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_exceeds_role_max_violation(self):
        """Faculty exceeds role-based weekly max -> HIGH violation."""
        c = FacultyRoleClinicConstraint()
        fac = _person(
            name="Dr. Chief",
            faculty_role="dept_chief",
            weekly_clinic_limit=1,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        # Two clinic blocks same week
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac], blocks=[b1, b2], templates=[clinic])

        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=clinic.id),
            _assignment(fac.id, b2.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert "Dr. Chief" in result.violations[0].message
        assert "role" in result.violations[0].details["limit_source"]

    def test_exceeds_person_specific_max_violation(self):
        """Faculty exceeds person-specific max -> violation with 'person' source."""
        c = FacultyRoleClinicConstraint()
        fac = _person(
            name="Dr. Custom",
            faculty_role="core",
            weekly_clinic_limit=4,
            max_clinic_halfdays_per_week=2,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 4))
        b3 = _block(block_date=date(2025, 3, 5))
        ctx = _context(faculty=[fac], blocks=[b1, b2, b3], templates=[clinic])

        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=clinic.id),
            _assignment(fac.id, b2.id, rotation_template_id=clinic.id),
            _assignment(fac.id, b3.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert result.violations[0].details["limit_source"] == "person"

    def test_person_min_violation(self):
        """Person-specific min > count -> MEDIUM violation."""
        c = FacultyRoleClinicConstraint()
        fac = _person(
            name="Dr. Min",
            faculty_role="core",
            weekly_clinic_limit=4,
            max_clinic_halfdays_per_week=4,
            min_clinic_halfdays_per_week=3,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[b1], templates=[clinic])

        # Only 1 clinic half-day, min is 3
        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"
        assert result.violations[0].details["violation_type"] == "under_minimum"

    def test_no_min_enforcement_for_role_based(self):
        """Role-based limits have min=0, so no min violation."""
        c = FacultyRoleClinicConstraint()
        fac = _person(
            name="Dr. Core",
            faculty_role="core",
            weekly_clinic_limit=4,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[b1], templates=[clinic])

        # 1 clinic half-day but no min enforced for role-based
        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_non_faculty_assignment_skipped(self):
        """Assignments for non-faculty (residents) are skipped."""
        c = FacultyRoleClinicConstraint()
        res = _person(name="Resident")  # Not in faculty list
        fac = _person(
            name="Dr. Core",
            faculty_role="core",
            weekly_clinic_limit=1,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 4))
        ctx = _context(
            residents=[res], faculty=[fac], blocks=[b1, b2], templates=[clinic]
        )

        # Resident has 2 clinic blocks, faculty limit is 1 — no violation for resident
        assignments = [
            _assignment(res.id, b1.id, rotation_template_id=clinic.id),
            _assignment(res.id, b2.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_faculty_without_role_skipped(self):
        """Faculty without faculty_role attribute is skipped in limit check."""
        c = FacultyRoleClinicConstraint()
        fac = _person(name="Dr. NoRole")  # No faculty_role
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac], blocks=[b1, b2], templates=[clinic])

        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=clinic.id),
            _assignment(fac.id, b2.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_violation_details_correct(self):
        """Violation details include all expected fields."""
        c = FacultyRoleClinicConstraint()
        fac = _person(
            name="Dr. PD",
            faculty_role="pd",
            weekly_clinic_limit=0,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 5))  # Wed in week of Mon 3/3
        ctx = _context(faculty=[fac], blocks=[b1], templates=[clinic])

        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        v = result.violations[0]
        assert v.details["week_start"] == "2025-03-03"
        assert v.details["count"] == 1
        assert v.details["max_limit"] == 0
        assert v.details["role"] == "pd"
        assert v.person_id == fac.id

    def test_multiple_weeks_one_violation(self):
        """Violation only for week that exceeds limit."""
        c = FacultyRoleClinicConstraint()
        fac = _person(
            name="Dr. Chief",
            faculty_role="dept_chief",
            weekly_clinic_limit=1,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        # Week 1: 1 block (ok)
        b1 = _block(block_date=date(2025, 3, 3))
        # Week 2: 2 blocks (violation)
        b2 = _block(block_date=date(2025, 3, 10))
        b3 = _block(block_date=date(2025, 3, 11))
        ctx = _context(faculty=[fac], blocks=[b1, b2, b3], templates=[clinic])

        assignments = [
            _assignment(fac.id, b1.id, rotation_template_id=clinic.id),
            _assignment(fac.id, b2.id, rotation_template_id=clinic.id),
            _assignment(fac.id, b3.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].details["week_start"] == "2025-03-10"

    def test_two_faculty_one_exceeds(self):
        """Two faculty, only one exceeds -> 1 violation."""
        c = FacultyRoleClinicConstraint()
        fac1 = _person(
            name="Dr. A",
            faculty_role="core",
            weekly_clinic_limit=2,
        )
        fac2 = _person(
            name="Dr. B",
            faculty_role="core",
            weekly_clinic_limit=1,
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac1, fac2], blocks=[b1, b2], templates=[clinic])

        assignments = [
            # Dr. A: 2 clinics (within limit of 2)
            _assignment(fac1.id, b1.id, rotation_template_id=clinic.id),
            _assignment(fac1.id, b2.id, rotation_template_id=clinic.id),
            # Dr. B: 2 clinics (exceeds limit of 1)
            _assignment(fac2.id, b1.id, rotation_template_id=clinic.id),
            _assignment(fac2.id, b2.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "Dr. B" in result.violations[0].message


# ==================== SMFacultyClinicConstraint Init ====================


class TestSMFacultyClinicInit:
    """Test SMFacultyClinicConstraint initialization."""

    def test_name(self):
        c = SMFacultyClinicConstraint()
        assert c.name == "SMFacultyNoRegularClinic"

    def test_type(self):
        c = SMFacultyClinicConstraint()
        assert c.constraint_type == ConstraintType.SPECIALTY

    def test_priority(self):
        c = SMFacultyClinicConstraint()
        assert c.priority == ConstraintPriority.HIGH


# ==================== SMFacultyClinicConstraint validate Tests ====================


class TestSMFacultyClinicValidate:
    """Test SMFacultyClinicConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = SMFacultyClinicConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_non_sm_faculty_on_regular_clinic_satisfied(self):
        """Non-SM faculty on regular clinic -> no violation."""
        c = SMFacultyClinicConstraint()
        fac = _person(name="Dr. Core", faculty_role="core")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block()
        ctx = _context(faculty=[fac], blocks=[b1], templates=[clinic])

        a = _assignment(fac.id, b1.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_sm_faculty_on_sm_clinic_satisfied(self):
        """SM faculty on SM clinic (requires_specialty) -> no violation."""
        c = SMFacultyClinicConstraint()
        fac = _person(name="Dr. SM", faculty_role="sports_med")
        sm_clinic = _template(
            name="SM Clinic",
            rotation_type="outpatient",
            requires_specialty="Sports Medicine",
        )
        b1 = _block()
        ctx = _context(faculty=[fac], blocks=[b1], templates=[sm_clinic])

        a = _assignment(fac.id, b1.id, rotation_template_id=sm_clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_sm_faculty_on_non_clinic_template_satisfied(self):
        """SM faculty on non-clinic template -> no violation."""
        c = SMFacultyClinicConstraint()
        fac = _person(name="Dr. SM", faculty_role="sports_med")
        fmit = _template(name="FMIT")  # No rotation_type
        b1 = _block()
        ctx = _context(faculty=[fac], blocks=[b1], templates=[fmit])

        a = _assignment(fac.id, b1.id, rotation_template_id=fmit.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_sm_faculty_on_regular_clinic_violation(self):
        """SM faculty on regular clinic -> violation."""
        c = SMFacultyClinicConstraint()
        fac = _person(name="Dr. SM", faculty_role="sports_med")
        clinic = _template(name="Regular Clinic", rotation_type="outpatient")
        b1 = _block()
        ctx = _context(faculty=[fac], blocks=[b1], templates=[clinic])

        a = _assignment(fac.id, b1.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert "regular clinic" in result.violations[0].message

    def test_violation_details_include_template(self):
        """Violation details include template_name."""
        c = SMFacultyClinicConstraint()
        fac = _person(name="Dr. SM", faculty_role="sports_med")
        clinic = _template(name="Wed Clinic", rotation_type="outpatient")
        b1 = _block()
        ctx = _context(faculty=[fac], blocks=[b1], templates=[clinic])

        a = _assignment(fac.id, b1.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.violations[0].details["template_name"] == "Wed Clinic"
        assert result.violations[0].person_id == fac.id
        assert result.violations[0].block_id == b1.id

    def test_multiple_sm_faculty_on_regular_clinic(self):
        """Two SM faculty on regular clinic -> two violations."""
        c = SMFacultyClinicConstraint()
        fac1 = _person(name="Dr. SM1", faculty_role="sports_med")
        fac2 = _person(name="Dr. SM2", faculty_role="sports_med")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block()
        ctx = _context(faculty=[fac1, fac2], blocks=[b1], templates=[clinic])

        assignments = [
            _assignment(fac1.id, b1.id, rotation_template_id=clinic.id),
            _assignment(fac2.id, b1.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2

    def test_sm_faculty_no_role_attr_no_violation(self):
        """Faculty without faculty_role attr -> not detected as SM."""
        c = SMFacultyClinicConstraint()
        fac = _person(name="Dr. NoRole")  # No faculty_role
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block()
        ctx = _context(faculty=[fac], blocks=[b1], templates=[clinic])

        a = _assignment(fac.id, b1.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_template_not_in_context_skipped(self):
        """Assignment with unknown template -> no violation."""
        c = SMFacultyClinicConstraint()
        fac = _person(name="Dr. SM", faculty_role="sports_med")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b1 = _block()
        ctx = _context(faculty=[fac], blocks=[b1], templates=[clinic])

        # Assignment references unknown template
        a = _assignment(fac.id, b1.id, rotation_template_id=uuid4())
        result = c.validate([a], ctx)
        assert result.satisfied is True
