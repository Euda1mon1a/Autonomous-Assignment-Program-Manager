"""Tests for resident weekly clinic constraints (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.resident_weekly_clinic import (
    ResidentAcademicTimeConstraint,
    ResidentClinicDayPreferenceConstraint,
    ResidentWeeklyClinicConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Resident", **kwargs):
    """Build a mock person."""
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


def _assignment(person_id, block_id, rotation_template_id=None, **kwargs):
    """Build a mock assignment."""
    ns = SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _context(residents=None, blocks=None, faculty=None, templates=None):
    """Build a SchedulingContext."""
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )


# ==================== ResidentWeeklyClinicConstraint Init ====================


class TestWeeklyClinicInit:
    """Test ResidentWeeklyClinicConstraint initialization."""

    def test_name(self):
        c = ResidentWeeklyClinicConstraint()
        assert c.name == "ResidentWeeklyClinic"

    def test_type(self):
        c = ResidentWeeklyClinicConstraint()
        assert c.constraint_type == ConstraintType.CAPACITY

    def test_priority(self):
        c = ResidentWeeklyClinicConstraint()
        assert c.priority == ConstraintPriority.HIGH

    def test_default_requirements_empty(self):
        c = ResidentWeeklyClinicConstraint()
        assert c._weekly_requirements == {}

    def test_custom_requirements(self):
        tid = uuid4()
        req = {"fm_clinic_min_per_week": 2, "fm_clinic_max_per_week": 5}
        c = ResidentWeeklyClinicConstraint(weekly_requirements={tid: req})
        assert c._weekly_requirements[tid] == req


# ==================== get_requirement Tests ====================


class TestGetRequirement:
    """Test get_requirement method."""

    def test_known_template(self):
        tid = uuid4()
        req = {"fm_clinic_min_per_week": 3}
        c = ResidentWeeklyClinicConstraint(weekly_requirements={tid: req})
        assert c.get_requirement(tid) == req

    def test_unknown_template(self):
        c = ResidentWeeklyClinicConstraint()
        assert c.get_requirement(uuid4()) is None


# ==================== _get_fm_clinic_template_ids Tests ====================


class TestGetFmClinicTemplateIds:
    """Test _get_fm_clinic_template_ids helper."""

    def test_outpatient_included(self):
        c = ResidentWeeklyClinicConstraint()
        clinic = _template(name="FM Clinic", rotation_type="outpatient")
        ctx = _context(templates=[clinic])
        ids = c._get_fm_clinic_template_ids(ctx)
        assert clinic.id in ids

    def test_inpatient_excluded(self):
        c = ResidentWeeklyClinicConstraint()
        fmit = _template(name="FMIT", rotation_type="inpatient")
        ctx = _context(templates=[fmit])
        ids = c._get_fm_clinic_template_ids(ctx)
        assert fmit.id not in ids

    def test_no_rotation_type_excluded(self):
        c = ResidentWeeklyClinicConstraint()
        t = _template(name="Unknown")  # No rotation_type
        ctx = _context(templates=[t])
        ids = c._get_fm_clinic_template_ids(ctx)
        assert len(ids) == 0

    def test_empty_templates(self):
        c = ResidentWeeklyClinicConstraint()
        ctx = _context()
        ids = c._get_fm_clinic_template_ids(ctx)
        assert len(ids) == 0


# ==================== _get_week_start Tests ====================


class TestGetWeekStart:
    """Test _get_week_start returns Monday of the week."""

    def test_monday_returns_same(self):
        c = ResidentWeeklyClinicConstraint()
        assert c._get_week_start(date(2025, 3, 3)) == date(2025, 3, 3)

    def test_wednesday_returns_monday(self):
        c = ResidentWeeklyClinicConstraint()
        assert c._get_week_start(date(2025, 3, 5)) == date(2025, 3, 3)

    def test_friday_returns_monday(self):
        c = ResidentWeeklyClinicConstraint()
        assert c._get_week_start(date(2025, 3, 7)) == date(2025, 3, 3)

    def test_sunday_returns_monday(self):
        c = ResidentWeeklyClinicConstraint()
        # Sunday 3/9 -> Monday 3/3
        assert c._get_week_start(date(2025, 3, 9)) == date(2025, 3, 3)

    def test_saturday_returns_monday(self):
        c = ResidentWeeklyClinicConstraint()
        # Saturday 3/8 -> Monday 3/3
        assert c._get_week_start(date(2025, 3, 8)) == date(2025, 3, 3)


# ==================== _group_blocks_by_week Tests ====================


class TestGroupBlocksByWeek:
    """Test _group_blocks_by_week helper."""

    def test_single_week(self):
        c = ResidentWeeklyClinicConstraint()
        mon = _block(block_date=date(2025, 3, 3))
        wed = _block(block_date=date(2025, 3, 5))
        fri = _block(block_date=date(2025, 3, 7))
        weeks = c._group_blocks_by_week([mon, wed, fri])
        assert len(weeks) == 1
        assert date(2025, 3, 3) in weeks
        assert len(weeks[date(2025, 3, 3)]) == 3

    def test_two_weeks(self):
        c = ResidentWeeklyClinicConstraint()
        week1 = _block(block_date=date(2025, 3, 3))
        week2 = _block(block_date=date(2025, 3, 10))
        weeks = c._group_blocks_by_week([week1, week2])
        assert len(weeks) == 2

    def test_empty_blocks(self):
        c = ResidentWeeklyClinicConstraint()
        weeks = c._group_blocks_by_week([])
        assert len(weeks) == 0


# ==================== _get_resident_current_rotation Tests ====================


class TestGetResidentCurrentRotation:
    """Test _get_resident_current_rotation helper."""

    def test_finds_rotation_in_same_week(self):
        c = ResidentWeeklyClinicConstraint()
        res = _person(name="R1")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        mon = _block(block_date=date(2025, 3, 3))
        a = _assignment(res.id, mon.id, rotation_template_id=clinic.id)
        block_by_id = {mon.id: mon}
        result = c._get_resident_current_rotation(
            res.id, date(2025, 3, 3), [a], block_by_id
        )
        assert result == clinic.id

    def test_returns_none_for_different_week(self):
        c = ResidentWeeklyClinicConstraint()
        res = _person(name="R1")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        # Assignment on March 10 (Monday of next week)
        next_week = _block(block_date=date(2025, 3, 10))
        a = _assignment(res.id, next_week.id, rotation_template_id=clinic.id)
        block_by_id = {next_week.id: next_week}
        result = c._get_resident_current_rotation(
            res.id, date(2025, 3, 3), [a], block_by_id
        )
        assert result is None

    def test_returns_none_for_different_resident(self):
        c = ResidentWeeklyClinicConstraint()
        res1 = _person(name="R1")
        res2 = _person(name="R2")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        mon = _block(block_date=date(2025, 3, 3))
        a = _assignment(res1.id, mon.id, rotation_template_id=clinic.id)
        block_by_id = {mon.id: mon}
        result = c._get_resident_current_rotation(
            res2.id, date(2025, 3, 3), [a], block_by_id
        )
        assert result is None

    def test_returns_none_for_no_assignments(self):
        c = ResidentWeeklyClinicConstraint()
        result = c._get_resident_current_rotation(uuid4(), date(2025, 3, 3), [], {})
        assert result is None

    def test_returns_none_for_unknown_block(self):
        c = ResidentWeeklyClinicConstraint()
        res = _person(name="R1")
        a = _assignment(res.id, uuid4(), rotation_template_id=uuid4())
        result = c._get_resident_current_rotation(res.id, date(2025, 3, 3), [a], {})
        assert result is None


# ==================== ResidentWeeklyClinicConstraint validate Tests ====================


class TestWeeklyClinicValidate:
    """Test ResidentWeeklyClinicConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = ResidentWeeklyClinicConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_requirements_satisfied(self):
        """No weekly requirements configured -> satisfied."""
        c = ResidentWeeklyClinicConstraint()
        res = _person(name="R1")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        mon = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[res], blocks=[mon], templates=[clinic])
        a = _assignment(res.id, mon.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_below_minimum_violation(self):
        """Resident has 1 clinic but min is 2 -> HIGH violation."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        req = {"fm_clinic_min_per_week": 2, "fm_clinic_max_per_week": 5}
        c = ResidentWeeklyClinicConstraint(weekly_requirements={fmit.id: req})

        res = _person(name="R1")
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))

        ctx = _context(residents=[res], blocks=[mon, tue], templates=[clinic, fmit])

        # FMIT assignment first so _get_resident_current_rotation finds it
        assignments = [
            _assignment(res.id, tue.id, rotation_template_id=fmit.id),
            _assignment(res.id, mon.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert "minimum" in result.violations[0].message

    def test_above_maximum_violation(self):
        """Resident has 4 clinic but max is 3 -> HIGH violation."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        req = {"fm_clinic_min_per_week": 1, "fm_clinic_max_per_week": 3}
        c = ResidentWeeklyClinicConstraint(weekly_requirements={fmit.id: req})

        res = _person(name="R1")
        mon_am = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        mon_pm = _block(block_date=date(2025, 3, 3), time_of_day="PM")
        tue_am = _block(block_date=date(2025, 3, 4), time_of_day="AM")
        tue_pm = _block(block_date=date(2025, 3, 4), time_of_day="PM")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")

        ctx = _context(
            residents=[res],
            blocks=[mon_am, mon_pm, tue_am, tue_pm, wed_am],
            templates=[clinic, fmit],
        )

        # FMIT assignment first so _get_resident_current_rotation finds it
        assignments = [
            _assignment(res.id, wed_am.id, rotation_template_id=fmit.id),
            _assignment(res.id, mon_am.id, rotation_template_id=clinic.id),
            _assignment(res.id, mon_pm.id, rotation_template_id=clinic.id),
            _assignment(res.id, tue_am.id, rotation_template_id=clinic.id),
            _assignment(res.id, tue_pm.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "exceeds maximum" in result.violations[0].message

    def test_within_bounds_satisfied(self):
        """Resident has 2 clinic, min=2, max=5 -> satisfied."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        req = {"fm_clinic_min_per_week": 2, "fm_clinic_max_per_week": 5}
        c = ResidentWeeklyClinicConstraint(weekly_requirements={fmit.id: req})

        res = _person(name="R1")
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))
        wed = _block(block_date=date(2025, 3, 5))

        ctx = _context(
            residents=[res], blocks=[mon, tue, wed], templates=[clinic, fmit]
        )

        assignments = [
            _assignment(res.id, wed.id, rotation_template_id=fmit.id),
            _assignment(res.id, mon.id, rotation_template_id=clinic.id),
            _assignment(res.id, tue.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_violation_details(self):
        """Check violation details contain expected keys."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        req = {"fm_clinic_min_per_week": 3, "fm_clinic_max_per_week": 5}
        c = ResidentWeeklyClinicConstraint(weekly_requirements={fmit.id: req})

        res = _person(name="Dr. Smith")
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))

        ctx = _context(residents=[res], blocks=[mon, tue], templates=[clinic, fmit])

        assignments = [
            _assignment(res.id, tue.id, rotation_template_id=fmit.id),
            _assignment(res.id, mon.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 1
        v = result.violations[0]
        assert v.person_id == res.id
        assert "week_start" in v.details
        assert v.details["count"] == 1
        assert v.details["minimum"] == 3

    def test_non_resident_assignment_skipped(self):
        """Assignments for unknown persons are skipped."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        c = ResidentWeeklyClinicConstraint()
        res = _person(name="R1")
        mon = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[res], blocks=[mon], templates=[clinic])

        # Assignment for a non-resident
        a = _assignment(uuid4(), mon.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True


# ==================== ResidentAcademicTimeConstraint Init ====================


class TestAcademicTimeInit:
    """Test ResidentAcademicTimeConstraint initialization."""

    def test_name(self):
        c = ResidentAcademicTimeConstraint()
        assert c.name == "ResidentAcademicTime"

    def test_type(self):
        c = ResidentAcademicTimeConstraint()
        assert c.constraint_type == ConstraintType.AVAILABILITY

    def test_priority(self):
        c = ResidentAcademicTimeConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_default_requirements_empty(self):
        c = ResidentAcademicTimeConstraint()
        assert c._weekly_requirements == {}

    def test_custom_requirements(self):
        tid = uuid4()
        req = {"academics_required": True}
        c = ResidentAcademicTimeConstraint(weekly_requirements={tid: req})
        assert c._weekly_requirements[tid] == req


# ==================== _is_academic_slot Tests ====================


class TestIsAcademicSlot:
    """Test _is_academic_slot helper (Wednesday AM)."""

    def test_wednesday_am_is_academic(self):
        c = ResidentAcademicTimeConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")  # Wednesday
        assert c._is_academic_slot(b) is True

    def test_wednesday_pm_not_academic(self):
        c = ResidentAcademicTimeConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        assert c._is_academic_slot(b) is False

    def test_monday_am_not_academic(self):
        c = ResidentAcademicTimeConstraint()
        b = _block(block_date=date(2025, 3, 3), time_of_day="AM")  # Monday
        assert c._is_academic_slot(b) is False

    def test_thursday_am_not_academic(self):
        c = ResidentAcademicTimeConstraint()
        b = _block(block_date=date(2025, 3, 6), time_of_day="AM")  # Thursday
        assert c._is_academic_slot(b) is False

    def test_block_without_date(self):
        c = ResidentAcademicTimeConstraint()
        b = SimpleNamespace(id=uuid4(), time_of_day="AM")  # No date
        assert c._is_academic_slot(b) is False

    def test_block_without_time_of_day(self):
        c = ResidentAcademicTimeConstraint()
        b = SimpleNamespace(id=uuid4(), date=date(2025, 3, 5))  # No time_of_day
        assert c._is_academic_slot(b) is False


# ==================== _get_clinic_template_ids Tests ====================


class TestGetClinicTemplateIds:
    """Test _get_clinic_template_ids helper."""

    def test_outpatient_included(self):
        c = ResidentAcademicTimeConstraint()
        clinic = _template(name="Clinic", rotation_type="outpatient")
        ctx = _context(templates=[clinic])
        ids = c._get_clinic_template_ids(ctx)
        assert clinic.id in ids

    def test_inpatient_excluded(self):
        c = ResidentAcademicTimeConstraint()
        fmit = _template(name="FMIT", rotation_type="inpatient")
        ctx = _context(templates=[fmit])
        ids = c._get_clinic_template_ids(ctx)
        assert len(ids) == 0

    def test_empty_templates(self):
        c = ResidentAcademicTimeConstraint()
        ctx = _context()
        ids = c._get_clinic_template_ids(ctx)
        assert len(ids) == 0


# ==================== ResidentAcademicTimeConstraint validate Tests ====================


class TestAcademicTimeValidate:
    """Test ResidentAcademicTimeConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = ResidentAcademicTimeConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_clinic_on_wednesday_am_with_academic_required(self):
        """Clinic on Wed AM with academics_required -> CRITICAL violation."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"academics_required": True}
        c = ResidentAcademicTimeConstraint(weekly_requirements={clinic.id: req})
        res = _person(name="R1")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[res], blocks=[wed_am], templates=[clinic])

        a = _assignment(res.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "Wednesday AM" in result.violations[0].message

    def test_clinic_on_wednesday_pm_no_violation(self):
        """Clinic on Wed PM -> no violation."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"academics_required": True}
        c = ResidentAcademicTimeConstraint(weekly_requirements={clinic.id: req})
        res = _person(name="R1")
        wed_pm = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(residents=[res], blocks=[wed_pm], templates=[clinic])

        a = _assignment(res.id, wed_pm.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_clinic_on_monday_am_no_violation(self):
        """Clinic on Mon AM -> no violation (not Wednesday)."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"academics_required": True}
        c = ResidentAcademicTimeConstraint(weekly_requirements={clinic.id: req})
        res = _person(name="R1")
        mon_am = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        ctx = _context(residents=[res], blocks=[mon_am], templates=[clinic])

        a = _assignment(res.id, mon_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_no_requirements_no_violation(self):
        """No weekly requirements -> no violations."""
        c = ResidentAcademicTimeConstraint()
        clinic = _template(name="Clinic", rotation_type="outpatient")
        res = _person(name="R1")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[res], blocks=[wed_am], templates=[clinic])

        a = _assignment(res.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_academics_not_required_no_violation(self):
        """academics_required=False -> no violation on Wed AM clinic."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"academics_required": False}
        c = ResidentAcademicTimeConstraint(weekly_requirements={clinic.id: req})
        res = _person(name="R1")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[res], blocks=[wed_am], templates=[clinic])

        a = _assignment(res.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_non_clinic_on_wednesday_am_no_violation(self):
        """Non-clinic rotation on Wed AM -> no violation."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        req = {"academics_required": True}
        c = ResidentAcademicTimeConstraint(weekly_requirements={fmit.id: req})
        res = _person(name="R1")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[res], blocks=[wed_am], templates=[clinic, fmit])

        a = _assignment(res.id, wed_am.id, rotation_template_id=fmit.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_violation_details(self):
        """Check violation details."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"academics_required": True}
        c = ResidentAcademicTimeConstraint(weekly_requirements={clinic.id: req})
        res = _person(name="Dr. Jones")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[res], blocks=[wed_am], templates=[clinic])

        a = _assignment(res.id, wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        v = result.violations[0]
        assert v.person_id == res.id
        assert v.block_id == wed_am.id
        assert v.details["date"] == "2025-03-05"
        assert v.details["time_of_day"] == "AM"

    def test_non_resident_skipped(self):
        """Assignments for unknown persons are skipped."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"academics_required": True}
        c = ResidentAcademicTimeConstraint(weekly_requirements={clinic.id: req})
        res = _person(name="R1")
        wed_am = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        ctx = _context(residents=[res], blocks=[wed_am], templates=[clinic])

        # Assignment for unknown person
        a = _assignment(uuid4(), wed_am.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True


# ==================== ResidentClinicDayPreferenceConstraint Init ====================


class TestClinicDayPreferenceInit:
    """Test ResidentClinicDayPreferenceConstraint initialization."""

    def test_name(self):
        c = ResidentClinicDayPreferenceConstraint()
        assert c.name == "ResidentClinicDayPreference"

    def test_type(self):
        c = ResidentClinicDayPreferenceConstraint()
        assert c.constraint_type == ConstraintType.PREFERENCE

    def test_priority(self):
        c = ResidentClinicDayPreferenceConstraint()
        assert c.priority == ConstraintPriority.LOW

    def test_default_weight(self):
        c = ResidentClinicDayPreferenceConstraint()
        assert c.weight == 10.0

    def test_custom_weight(self):
        c = ResidentClinicDayPreferenceConstraint(weight=25.0)
        assert c.weight == 25.0

    def test_default_requirements_empty(self):
        c = ResidentClinicDayPreferenceConstraint()
        assert c._weekly_requirements == {}


# ==================== ResidentClinicDayPreferenceConstraint validate Tests ====================


class TestClinicDayPreferenceValidate:
    """Test ResidentClinicDayPreferenceConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = ResidentClinicDayPreferenceConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_no_requirements_zero_penalty(self):
        """No weekly requirements -> zero penalty."""
        c = ResidentClinicDayPreferenceConstraint()
        clinic = _template(name="Clinic", rotation_type="outpatient")
        res = _person(name="R1")
        mon = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[res], blocks=[mon], templates=[clinic])

        a = _assignment(res.id, mon.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_allowed_day_zero_penalty(self):
        """Clinic on allowed day -> zero penalty."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        # Monday=0, Tuesday=1 allowed
        req = {"allowed_clinic_days": [0, 1]}
        c = ResidentClinicDayPreferenceConstraint(weekly_requirements={uuid4(): req})
        res = _person(name="R1")
        mon = _block(block_date=date(2025, 3, 3))  # Monday (weekday 0)
        ctx = _context(residents=[res], blocks=[mon], templates=[clinic])

        a = _assignment(res.id, mon.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_non_allowed_day_penalized(self):
        """Clinic on non-allowed day -> penalty applied."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        # Only Monday=0, Tuesday=1 allowed, Wednesday=2 not allowed
        req = {"allowed_clinic_days": [0, 1]}
        c = ResidentClinicDayPreferenceConstraint(
            weight=10.0, weekly_requirements={uuid4(): req}
        )
        res = _person(name="R1")
        wed = _block(block_date=date(2025, 3, 5))  # Wednesday (weekday 2)
        ctx = _context(residents=[res], blocks=[wed], templates=[clinic])

        a = _assignment(res.id, wed.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True  # Soft constraint always satisfied
        assert result.penalty == 10.0

    def test_multiple_non_allowed_days_cumulative(self):
        """Multiple clinic assignments on non-allowed days -> cumulative penalty."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"allowed_clinic_days": [0]}  # Only Monday
        c = ResidentClinicDayPreferenceConstraint(
            weight=10.0, weekly_requirements={uuid4(): req}
        )
        res = _person(name="R1")
        wed = _block(block_date=date(2025, 3, 5))  # Wednesday
        thu = _block(block_date=date(2025, 3, 6))  # Thursday
        ctx = _context(residents=[res], blocks=[wed, thu], templates=[clinic])

        assignments = [
            _assignment(res.id, wed.id, rotation_template_id=clinic.id),
            _assignment(res.id, thu.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 20.0

    def test_non_clinic_assignment_no_penalty(self):
        """Non-clinic assignment on non-allowed day -> no penalty."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        req = {"allowed_clinic_days": [0]}  # Only Monday
        c = ResidentClinicDayPreferenceConstraint(weekly_requirements={uuid4(): req})
        res = _person(name="R1")
        wed = _block(block_date=date(2025, 3, 5))  # Wednesday
        ctx = _context(residents=[res], blocks=[wed], templates=[clinic, fmit])

        # FMIT assignment, not clinic
        a = _assignment(res.id, wed.id, rotation_template_id=fmit.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_non_resident_skipped(self):
        """Assignment for unknown person -> skipped."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"allowed_clinic_days": [0]}
        c = ResidentClinicDayPreferenceConstraint(weekly_requirements={uuid4(): req})
        res = _person(name="R1")
        wed = _block(block_date=date(2025, 3, 5))
        ctx = _context(residents=[res], blocks=[wed], templates=[clinic])

        a = _assignment(uuid4(), wed.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_empty_allowed_days_no_penalty(self):
        """Empty allowed_clinic_days list -> no penalty (no restriction)."""
        clinic = _template(name="Clinic", rotation_type="outpatient")
        req = {"allowed_clinic_days": []}
        c = ResidentClinicDayPreferenceConstraint(weekly_requirements={uuid4(): req})
        res = _person(name="R1")
        wed = _block(block_date=date(2025, 3, 5))
        ctx = _context(residents=[res], blocks=[wed], templates=[clinic])

        a = _assignment(res.id, wed.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0
