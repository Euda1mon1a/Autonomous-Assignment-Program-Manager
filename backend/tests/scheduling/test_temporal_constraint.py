"""Tests for temporal constraints (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
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


# ==================== Helpers ====================


def _person(pid=None, name="Person", pgy_level=None):
    """Build a mock person."""
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    if pgy_level is not None:
        ns.pgy_level = pgy_level
    return ns


def _block(bid=None, block_date=None, time_of_day="AM"):
    """Build a mock block."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 5),  # Wednesday
        time_of_day=time_of_day,
    )


def _template(tid=None, name="Template", rotation_type=None, abbreviation=None):
    """Build a mock template."""
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
    if rotation_type is not None:
        ns.rotation_type = rotation_type
    if abbreviation is not None:
        ns.abbreviation = abbreviation
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


# ==================== WednesdayAMInternOnlyConstraint ====================


class TestWedAMInternOnlyInit:
    """Test initialization."""

    def test_name(self):
        c = WednesdayAMInternOnlyConstraint()
        assert c.name == "WednesdayAMInternOnly"

    def test_type(self):
        c = WednesdayAMInternOnlyConstraint()
        assert c.constraint_type == ConstraintType.ROTATION

    def test_priority(self):
        c = WednesdayAMInternOnlyConstraint()
        assert c.priority == ConstraintPriority.HIGH

    def test_wednesday_constant(self):
        assert WednesdayAMInternOnlyConstraint.WEDNESDAY == 2


class TestWedAMInternOnlyHelpers:
    """Test helper methods."""

    def test_is_wednesday_am_true(self):
        c = WednesdayAMInternOnlyConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        assert c._is_wednesday_am(b) is True

    def test_is_wednesday_pm_false(self):
        c = WednesdayAMInternOnlyConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        assert c._is_wednesday_am(b) is False

    def test_is_thursday_am_false(self):
        c = WednesdayAMInternOnlyConstraint()
        b = _block(block_date=date(2025, 3, 6), time_of_day="AM")
        assert c._is_wednesday_am(b) is False


class TestWedAMInternOnlyValidate:
    """Test validate method."""

    def test_no_assignments_satisfied(self):
        c = WednesdayAMInternOnlyConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_clinic_templates_satisfied(self):
        """No outpatient templates -> nothing to check."""
        c = WednesdayAMInternOnlyConstraint()
        t = _template(name="Inpatient", rotation_type="inpatient")
        ctx = _context(templates=[t])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_pgy1_on_wednesday_am_clinic_ok(self):
        """PGY-1 on Wednesday AM clinic -> satisfied."""
        c = WednesdayAMInternOnlyConstraint()
        r = _person(name="Intern", pgy_level=1)
        clinic = _template(name="Clinic", rotation_type="outpatient")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[r], blocks=[wed_am], templates=[clinic])

        a = _assignment(r.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pgy2_on_wednesday_am_clinic_violation(self):
        """PGY-2 on Wednesday AM clinic -> violation."""
        c = WednesdayAMInternOnlyConstraint()
        r = _person(name="Dr. PGY2", pgy_level=2)
        clinic = _template(name="Clinic", rotation_type="outpatient")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[r], blocks=[wed_am], templates=[clinic])

        a = _assignment(r.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "PGY-2" in result.violations[0].message
        assert result.violations[0].severity == "HIGH"

    def test_pgy3_on_wednesday_am_clinic_violation(self):
        """PGY-3 on Wednesday AM clinic -> violation."""
        c = WednesdayAMInternOnlyConstraint()
        r = _person(name="Dr. PGY3", pgy_level=3)
        clinic = _template(name="Clinic", rotation_type="outpatient")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[r], blocks=[wed_am], templates=[clinic])

        a = _assignment(r.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False

    def test_pgy2_on_thursday_am_clinic_ok(self):
        """PGY-2 on Thursday AM (not Wednesday) -> satisfied."""
        c = WednesdayAMInternOnlyConstraint()
        r = _person(name="Dr. PGY2", pgy_level=2)
        clinic = _template(name="Clinic", rotation_type="outpatient")
        thu_am = _block(block_date=date(2025, 3, 6), time_of_day="AM")
        ctx = _context(residents=[r], blocks=[thu_am], templates=[clinic])

        a = _assignment(r.id, thu_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pgy2_on_wednesday_am_non_clinic_ok(self):
        """PGY-2 on Wednesday AM inpatient template -> satisfied."""
        c = WednesdayAMInternOnlyConstraint()
        r = _person(name="Dr. PGY2", pgy_level=2)
        inpt = _template(name="Inpatient", rotation_type="inpatient")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[r], blocks=[wed_am], templates=[inpt])

        a = _assignment(r.id, wed_am.id, rotation_template_id=inpt.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_faculty_on_wednesday_am_clinic_ok(self):
        """Faculty (not in residents list) on Wednesday AM clinic -> ok."""
        c = WednesdayAMInternOnlyConstraint()
        fac = _person(name="Dr. Faculty")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(
            residents=[],
            faculty=[fac],
            blocks=[wed_am],
            templates=[clinic],
        )

        a = _assignment(fac.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_violation_details(self):
        """Violation details include pgy_level and date."""
        c = WednesdayAMInternOnlyConstraint()
        r = _person(name="Dr. PGY2", pgy_level=2)
        clinic = _template(name="Clinic", rotation_type="outpatient")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[r], blocks=[wed_am], templates=[clinic])

        a = _assignment(r.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.violations[0].details["pgy_level"] == 2
        assert result.violations[0].details["date"] == "2025-03-05"


# ==================== WednesdayPMSingleFacultyConstraint ====================


class TestWedPMSingleFacultyInit:
    """Test initialization."""

    def test_name(self):
        c = WednesdayPMSingleFacultyConstraint()
        assert c.name == "WednesdayPMSingleFaculty"

    def test_type(self):
        c = WednesdayPMSingleFacultyConstraint()
        assert c.constraint_type == ConstraintType.ROTATION

    def test_priority(self):
        c = WednesdayPMSingleFacultyConstraint()
        assert c.priority == ConstraintPriority.HIGH


class TestWedPMSingleFacultyHelpers:
    """Test _is_regular_wednesday_pm helper."""

    def test_first_wednesday_pm_true(self):
        """March 5, 2025 is 1st Wednesday, day=5."""
        c = WednesdayPMSingleFacultyConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        assert c._is_regular_wednesday_pm(b) is True

    def test_second_wednesday_pm_true(self):
        """March 12, 2025 is 2nd Wednesday, day=12."""
        c = WednesdayPMSingleFacultyConstraint()
        b = _block(block_date=date(2025, 3, 12), time_of_day="PM")
        assert c._is_regular_wednesday_pm(b) is True

    def test_third_wednesday_pm_true(self):
        """March 19, 2025 is 3rd Wednesday, day=19."""
        c = WednesdayPMSingleFacultyConstraint()
        b = _block(block_date=date(2025, 3, 19), time_of_day="PM")
        assert c._is_regular_wednesday_pm(b) is True

    def test_fourth_wednesday_pm_false(self):
        """March 26, 2025 is 4th Wednesday, day=26 (>=22)."""
        c = WednesdayPMSingleFacultyConstraint()
        b = _block(block_date=date(2025, 3, 26), time_of_day="PM")
        assert c._is_regular_wednesday_pm(b) is False

    def test_wednesday_am_false(self):
        c = WednesdayPMSingleFacultyConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        assert c._is_regular_wednesday_pm(b) is False

    def test_thursday_pm_false(self):
        c = WednesdayPMSingleFacultyConstraint()
        b = _block(block_date=date(2025, 3, 6), time_of_day="PM")
        assert c._is_regular_wednesday_pm(b) is False


class TestWedPMSingleFacultyValidate:
    """Test validate method."""

    def test_no_clinic_templates_satisfied(self):
        c = WednesdayPMSingleFacultyConstraint()
        ctx = _context(templates=[_template(rotation_type="inpatient")])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_wednesday_pm_blocks_satisfied(self):
        c = WednesdayPMSingleFacultyConstraint()
        clinic = _template(rotation_type="outpatient")
        thu = _block(block_date=date(2025, 3, 6), time_of_day="PM")
        ctx = _context(blocks=[thu], templates=[clinic])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_exactly_one_faculty_satisfied(self):
        """One faculty on regular Wed PM clinic -> satisfied."""
        c = WednesdayPMSingleFacultyConstraint()
        fac = _person(name="Dr. A")
        clinic = _template(rotation_type="outpatient")
        wed_pm = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(faculty=[fac], blocks=[wed_pm], templates=[clinic])

        a = _assignment(fac.id, wed_pm.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_zero_faculty_violation(self):
        """No faculty on regular Wed PM clinic -> violation."""
        c = WednesdayPMSingleFacultyConstraint()
        fac = _person(name="Dr. A")
        clinic = _template(rotation_type="outpatient")
        wed_pm = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(faculty=[fac], blocks=[wed_pm], templates=[clinic])

        result = c.validate([], ctx)
        assert result.satisfied is False
        assert "0 faculty" in result.violations[0].message

    def test_two_faculty_violation(self):
        """Two faculty on Wed PM clinic -> violation."""
        c = WednesdayPMSingleFacultyConstraint()
        fac_a = _person(name="Dr. A")
        fac_b = _person(name="Dr. B")
        clinic = _template(rotation_type="outpatient")
        wed_pm = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(faculty=[fac_a, fac_b], blocks=[wed_pm], templates=[clinic])

        assignments = [
            _assignment(fac_a.id, wed_pm.id, rotation_template_id=clinic.id),
            _assignment(fac_b.id, wed_pm.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert "2 faculty" in result.violations[0].message

    def test_fourth_wednesday_not_checked(self):
        """4th Wednesday PM -> not regular -> no check."""
        c = WednesdayPMSingleFacultyConstraint()
        clinic = _template(rotation_type="outpatient")
        fourth_wed = _block(block_date=date(2025, 3, 26), time_of_day="PM")
        ctx = _context(blocks=[fourth_wed], templates=[clinic])

        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_resident_not_counted_as_faculty(self):
        """Resident on Wed PM clinic -> not faculty -> not counted."""
        c = WednesdayPMSingleFacultyConstraint()
        res = _person(name="Resident", pgy_level=2)
        fac = _person(name="Dr. A")
        clinic = _template(rotation_type="outpatient")
        wed_pm = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(
            residents=[res],
            faculty=[fac],
            blocks=[wed_pm],
            templates=[clinic],
        )

        # Only resident assigned, not faculty
        a = _assignment(res.id, wed_pm.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False  # 0 faculty in clinic


# ==================== InvertedWednesdayConstraint ====================


class TestInvertedWedInit:
    """Test initialization."""

    def test_name(self):
        c = InvertedWednesdayConstraint()
        assert c.name == "InvertedWednesday"

    def test_type(self):
        c = InvertedWednesdayConstraint()
        assert c.constraint_type == ConstraintType.ROTATION

    def test_priority(self):
        c = InvertedWednesdayConstraint()
        assert c.priority == ConstraintPriority.HIGH


class TestInvertedWedHelpers:
    """Test _is_fourth_wednesday helper."""

    def test_fourth_wednesday_true(self):
        """March 26, 2025 is 4th Wednesday, day=26."""
        c = InvertedWednesdayConstraint()
        b = _block(block_date=date(2025, 3, 26), time_of_day="AM")
        assert c._is_fourth_wednesday(b) is True

    def test_day_22_wednesday_true(self):
        """Day 22 is within 4th Wednesday range."""
        c = InvertedWednesdayConstraint()
        # Jan 22, 2025 is a Wednesday
        b = _block(block_date=date(2025, 1, 22), time_of_day="AM")
        assert c._is_fourth_wednesday(b) is True

    def test_day_28_wednesday_true(self):
        """Day 28 is within 4th Wednesday range."""
        c = InvertedWednesdayConstraint()
        # May 28, 2025 is a Wednesday
        b = _block(block_date=date(2025, 5, 28), time_of_day="AM")
        assert c._is_fourth_wednesday(b) is True

    def test_first_wednesday_false(self):
        """March 5, 2025 is 1st Wednesday (day=5 < 22)."""
        c = InvertedWednesdayConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        assert c._is_fourth_wednesday(b) is False

    def test_thursday_day22_false(self):
        """Day 22 but Thursday -> false."""
        c = InvertedWednesdayConstraint()
        # Jan 23, 2025 is a Thursday (day 23)
        b = _block(block_date=date(2025, 1, 23), time_of_day="AM")
        assert c._is_fourth_wednesday(b) is False


class TestInvertedWedValidate:
    """Test validate method."""

    def test_no_clinic_templates_satisfied(self):
        c = InvertedWednesdayConstraint()
        ctx = _context(templates=[_template(rotation_type="inpatient")])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_fourth_wednesday_satisfied(self):
        """No 4th Wednesday blocks -> nothing to check."""
        c = InvertedWednesdayConstraint()
        clinic = _template(rotation_type="outpatient")
        first_wed = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(blocks=[first_wed], templates=[clinic])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_one_am_one_pm_different_faculty_satisfied(self):
        """4th Wed: 1 faculty AM, 1 different faculty PM -> satisfied."""
        c = InvertedWednesdayConstraint()
        fac_a = _person(name="Dr. A")
        fac_b = _person(name="Dr. B")
        clinic = _template(rotation_type="outpatient")
        fourth_wed_am = _block(block_date=date(2025, 3, 26), time_of_day="AM")
        fourth_wed_pm = _block(block_date=date(2025, 3, 26), time_of_day="PM")
        ctx = _context(
            faculty=[fac_a, fac_b],
            blocks=[fourth_wed_am, fourth_wed_pm],
            templates=[clinic],
        )

        assignments = [
            _assignment(fac_a.id, fourth_wed_am.id, rotation_template_id=clinic.id),
            _assignment(fac_b.id, fourth_wed_pm.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_same_faculty_am_and_pm_violation(self):
        """4th Wed: same faculty AM and PM -> violation."""
        c = InvertedWednesdayConstraint()
        fac = _person(name="Dr. Same")
        clinic = _template(rotation_type="outpatient")
        fourth_wed_am = _block(block_date=date(2025, 3, 26), time_of_day="AM")
        fourth_wed_pm = _block(block_date=date(2025, 3, 26), time_of_day="PM")
        ctx = _context(
            faculty=[fac],
            blocks=[fourth_wed_am, fourth_wed_pm],
            templates=[clinic],
        )

        assignments = [
            _assignment(fac.id, fourth_wed_am.id, rotation_template_id=clinic.id),
            _assignment(fac.id, fourth_wed_pm.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert any("Same faculty" in v.message for v in result.violations)

    def test_zero_am_faculty_violation(self):
        """4th Wed: 0 faculty AM -> violation."""
        c = InvertedWednesdayConstraint()
        fac = _person(name="Dr. A")
        clinic = _template(rotation_type="outpatient")
        fourth_wed_am = _block(block_date=date(2025, 3, 26), time_of_day="AM")
        fourth_wed_pm = _block(block_date=date(2025, 3, 26), time_of_day="PM")
        ctx = _context(
            faculty=[fac],
            blocks=[fourth_wed_am, fourth_wed_pm],
            templates=[clinic],
        )

        # Only PM assigned
        a = _assignment(fac.id, fourth_wed_pm.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert any("AM: 0 faculty" in v.message for v in result.violations)

    def test_zero_pm_faculty_violation(self):
        """4th Wed: 0 faculty PM -> violation."""
        c = InvertedWednesdayConstraint()
        fac = _person(name="Dr. A")
        clinic = _template(rotation_type="outpatient")
        fourth_wed_am = _block(block_date=date(2025, 3, 26), time_of_day="AM")
        fourth_wed_pm = _block(block_date=date(2025, 3, 26), time_of_day="PM")
        ctx = _context(
            faculty=[fac],
            blocks=[fourth_wed_am, fourth_wed_pm],
            templates=[clinic],
        )

        # Only AM assigned
        a = _assignment(fac.id, fourth_wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert any("PM: 0 faculty" in v.message for v in result.violations)

    def test_two_am_faculty_violation(self):
        """4th Wed: 2 faculty AM -> violation."""
        c = InvertedWednesdayConstraint()
        fac_a = _person(name="Dr. A")
        fac_b = _person(name="Dr. B")
        fac_c = _person(name="Dr. C")
        clinic = _template(rotation_type="outpatient")
        fourth_wed_am = _block(block_date=date(2025, 3, 26), time_of_day="AM")
        fourth_wed_pm = _block(block_date=date(2025, 3, 26), time_of_day="PM")
        ctx = _context(
            faculty=[fac_a, fac_b, fac_c],
            blocks=[fourth_wed_am, fourth_wed_pm],
            templates=[clinic],
        )

        assignments = [
            _assignment(fac_a.id, fourth_wed_am.id, rotation_template_id=clinic.id),
            _assignment(fac_b.id, fourth_wed_am.id, rotation_template_id=clinic.id),
            _assignment(fac_c.id, fourth_wed_pm.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert any("AM: 2 faculty" in v.message for v in result.violations)
