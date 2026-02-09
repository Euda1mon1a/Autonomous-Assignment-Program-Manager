"""Tests for halfday requirement constraints (pure logic, no DB required).

Note: HalfDayRequirementConstraint.validate has a bug - it calls
_get_template_ids_by_activity() which doesn't exist (only
_get_template_ids_by_rotation_type is defined). This raises AttributeError
when requirements are non-empty. Tested with pytest.raises(AttributeError).
"""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.halfday_requirement import (
    HalfDayRequirementConstraint,
    WeekendWorkConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Resident"):
    """Build a mock person."""
    return SimpleNamespace(id=pid or uuid4(), name=name)


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


def _context(
    residents=None,
    blocks=None,
    faculty=None,
    templates=None,
    start_date=None,
    end_date=None,
):
    """Build a SchedulingContext."""
    ctx = SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )
    if start_date is not None:
        ctx.start_date = start_date
    if end_date is not None:
        ctx.end_date = end_date
    return ctx


# ==================== WeekendWorkConstraint Init ====================


class TestWeekendWorkInit:
    """Test WeekendWorkConstraint initialization."""

    def test_name(self):
        c = WeekendWorkConstraint()
        assert c.name == "WeekendWork"

    def test_type(self):
        c = WeekendWorkConstraint()
        assert c.constraint_type == ConstraintType.AVAILABILITY

    def test_priority(self):
        c = WeekendWorkConstraint()
        assert c.priority == ConstraintPriority.HIGH

    def test_default_config_empty(self):
        c = WeekendWorkConstraint()
        assert c._weekend_config == {}

    def test_config_from_init(self):
        tid = uuid4()
        c = WeekendWorkConstraint(template_weekend_config={tid: True})
        assert c._weekend_config[tid] is True


# ==================== _is_weekend Tests ====================


class TestIsWeekend:
    """Test _is_weekend helper."""

    def test_monday_not_weekend(self):
        c = WeekendWorkConstraint()
        b = _block(block_date=date(2025, 3, 3))  # Monday
        assert c._is_weekend(b) is False

    def test_friday_not_weekend(self):
        c = WeekendWorkConstraint()
        b = _block(block_date=date(2025, 3, 7))  # Friday
        assert c._is_weekend(b) is False

    def test_saturday_is_weekend(self):
        c = WeekendWorkConstraint()
        b = _block(block_date=date(2025, 3, 8))  # Saturday
        assert c._is_weekend(b) is True

    def test_sunday_is_weekend(self):
        c = WeekendWorkConstraint()
        b = _block(block_date=date(2025, 3, 9))  # Sunday
        assert c._is_weekend(b) is True

    def test_block_without_date(self):
        c = WeekendWorkConstraint()
        b = SimpleNamespace(id=uuid4(), time_of_day="AM")
        assert c._is_weekend(b) is False


# ==================== _includes_weekend Tests ====================


class TestIncludesWeekend:
    """Test _includes_weekend helper."""

    def test_from_config_dict(self):
        tid = uuid4()
        c = WeekendWorkConstraint(template_weekend_config={tid: True})
        ctx = _context()
        assert c._includes_weekend(tid, ctx) is True

    def test_from_template_attribute(self):
        t = _template(name="Night Float", includes_weekend_work=True)
        c = WeekendWorkConstraint()
        ctx = _context(templates=[t])
        assert c._includes_weekend(t.id, ctx) is True

    def test_default_false(self):
        t = _template(name="Clinic")  # No includes_weekend_work
        c = WeekendWorkConstraint()
        ctx = _context(templates=[t])
        assert c._includes_weekend(t.id, ctx) is False

    def test_unknown_template_false(self):
        c = WeekendWorkConstraint()
        ctx = _context()
        assert c._includes_weekend(uuid4(), ctx) is False

    def test_config_overrides_template(self):
        """Config dict takes precedence over template attribute."""
        t = _template(name="NF", includes_weekend_work=True)
        c = WeekendWorkConstraint(template_weekend_config={t.id: False})
        ctx = _context(templates=[t])
        assert c._includes_weekend(t.id, ctx) is False


# ==================== WeekendWorkConstraint validate Tests ====================


class TestWeekendWorkValidate:
    """Test WeekendWorkConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = WeekendWorkConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_weekday_assignment_satisfied(self):
        """Assignment on weekday -> no violation."""
        c = WeekendWorkConstraint()
        res = _person(name="R1")
        clinic = _template(name="Clinic")
        b = _block(block_date=date(2025, 3, 3))  # Monday
        ctx = _context(residents=[res], blocks=[b], templates=[clinic])

        a = _assignment(res.id, b.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_weekend_with_weekend_rotation_satisfied(self):
        """Weekend assignment on weekend-enabled rotation -> no violation."""
        c = WeekendWorkConstraint()
        res = _person(name="R1")
        nf = _template(name="Night Float", includes_weekend_work=True)
        sat = _block(block_date=date(2025, 3, 8))  # Saturday
        ctx = _context(residents=[res], blocks=[sat], templates=[nf])

        a = _assignment(res.id, sat.id, rotation_template_id=nf.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_weekend_with_non_weekend_rotation_violation(self):
        """Weekend assignment on non-weekend rotation -> HIGH violation."""
        c = WeekendWorkConstraint()
        res = _person(name="R1")
        clinic = _template(name="Clinic")  # No includes_weekend_work
        sat = _block(block_date=date(2025, 3, 8))  # Saturday
        ctx = _context(residents=[res], blocks=[sat], templates=[clinic])

        a = _assignment(res.id, sat.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "HIGH"
        assert "weekend" in result.violations[0].message

    def test_violation_details(self):
        c = WeekendWorkConstraint()
        res = _person(name="Dr. Smith")
        clinic = _template(name="FM Clinic")
        sun = _block(block_date=date(2025, 3, 9))  # Sunday
        ctx = _context(residents=[res], blocks=[sun], templates=[clinic])

        a = _assignment(res.id, sun.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        v = result.violations[0]
        assert v.details["date"] == "2025-03-09"
        assert v.details["day"] == "Sunday"
        assert v.details["template"] == "FM Clinic"
        assert v.person_id == res.id
        assert v.block_id == sun.id

    def test_config_overrides_in_validate(self):
        """Config dict used to check weekend work in validate."""
        clinic = _template(name="Clinic")
        c = WeekendWorkConstraint(template_weekend_config={clinic.id: True})
        res = _person(name="R1")
        sat = _block(block_date=date(2025, 3, 8))
        ctx = _context(residents=[res], blocks=[sat], templates=[clinic])

        a = _assignment(res.id, sat.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_unknown_template_skipped(self):
        """Assignment with unknown template_id is skipped."""
        c = WeekendWorkConstraint()
        res = _person(name="R1")
        sat = _block(block_date=date(2025, 3, 8))
        ctx = _context(residents=[res], blocks=[sat])

        a = _assignment(res.id, sat.id, rotation_template_id=uuid4())
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_multiple_weekend_violations(self):
        """Two weekend assignments on non-weekend rotations -> two violations."""
        c = WeekendWorkConstraint()
        res = _person(name="R1")
        clinic = _template(name="Clinic")
        sat = _block(block_date=date(2025, 3, 8))
        sun = _block(block_date=date(2025, 3, 9))
        ctx = _context(residents=[res], blocks=[sat, sun], templates=[clinic])

        assignments = [
            _assignment(res.id, sat.id, rotation_template_id=clinic.id),
            _assignment(res.id, sun.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2


# ==================== HalfDayRequirementConstraint Init ====================


class TestHalfDayRequirementInit:
    """Test HalfDayRequirementConstraint initialization."""

    def test_name(self):
        c = HalfDayRequirementConstraint()
        assert c.name == "HalfDayRequirement"

    def test_type(self):
        c = HalfDayRequirementConstraint()
        assert c.constraint_type == ConstraintType.CAPACITY

    def test_priority(self):
        c = HalfDayRequirementConstraint()
        assert c.priority == ConstraintPriority.MEDIUM

    def test_default_weight(self):
        c = HalfDayRequirementConstraint()
        assert c.weight == 50.0

    def test_custom_weight(self):
        c = HalfDayRequirementConstraint(weight=75.0)
        assert c.weight == 75.0

    def test_default_requirements_empty(self):
        c = HalfDayRequirementConstraint()
        assert c._requirements == {}


# ==================== get_requirement Tests ====================


class TestGetRequirement:
    """Test get_requirement method."""

    def test_known_template(self):
        tid = uuid4()
        req = {"fm_clinic_halfdays": 4, "specialty_halfdays": 5}
        c = HalfDayRequirementConstraint(halfday_requirements={tid: req})
        assert c.get_requirement(tid) == req

    def test_unknown_template(self):
        c = HalfDayRequirementConstraint()
        assert c.get_requirement(uuid4()) is None


# ==================== _get_template_ids_by_rotation_type Tests ====================


class TestGetTemplateIdsByRotationType:
    """Test _get_template_ids_by_rotation_type helper."""

    def test_groups_by_rotation_type(self):
        c = HalfDayRequirementConstraint()
        clinic = _template(name="Clinic", rotation_type="outpatient")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        ctx = _context(templates=[clinic, fmit])
        result = c._get_template_ids_by_rotation_type(ctx)
        assert clinic.id in result["outpatient"]
        assert fmit.id in result["inpatient"]

    def test_unknown_rotation_type(self):
        """Templates without rotation_type default to 'unknown'."""
        c = HalfDayRequirementConstraint()
        t = _template(name="T1")  # No rotation_type
        ctx = _context(templates=[t])
        result = c._get_template_ids_by_rotation_type(ctx)
        assert t.id in result["unknown"]

    def test_empty_templates(self):
        c = HalfDayRequirementConstraint()
        ctx = _context()
        result = c._get_template_ids_by_rotation_type(ctx)
        assert len(result) == 0


# ==================== _get_rotation_block_range Tests ====================


class TestGetRotationBlockRange:
    """Test _get_rotation_block_range helper."""

    def test_from_context_dates(self):
        c = HalfDayRequirementConstraint()
        ctx = _context(
            start_date=date(2025, 3, 3),
            end_date=date(2025, 3, 30),
        )
        result = c._get_rotation_block_range(ctx)
        assert result == (date(2025, 3, 3), date(2025, 3, 30))

    def test_from_blocks(self):
        c = HalfDayRequirementConstraint()
        b1 = _block(block_date=date(2025, 3, 3))
        b2 = _block(block_date=date(2025, 3, 28))
        ctx = _context(blocks=[b1, b2])
        result = c._get_rotation_block_range(ctx)
        assert result == (date(2025, 3, 3), date(2025, 3, 28))

    def test_no_dates_no_blocks(self):
        c = HalfDayRequirementConstraint()
        ctx = _context()
        assert c._get_rotation_block_range(ctx) is None


# ==================== HalfDayRequirementConstraint validate Tests ====================


class TestHalfDayRequirementValidate:
    """Test HalfDayRequirementConstraint.validate method.

    Note: validate calls self._get_template_ids_by_activity() which doesn't exist
    (only _get_template_ids_by_rotation_type is defined). This raises AttributeError
    when self._requirements is non-empty.
    """

    def test_no_requirements_satisfied(self):
        """No requirements -> satisfied with zero penalty."""
        c = HalfDayRequirementConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_with_requirements_raises_attribute_error(self):
        """Bug: validate calls _get_template_ids_by_activity which doesn't exist."""
        tid = uuid4()
        c = HalfDayRequirementConstraint(
            halfday_requirements={tid: {"fm_clinic_halfdays": 4}}
        )
        res = _person(name="R1")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block()
        ctx = _context(residents=[res], blocks=[b], templates=[clinic])

        a = _assignment(res.id, b.id, rotation_template_id=clinic.id)
        with pytest.raises(AttributeError, match="_get_template_ids_by_activity"):
            c.validate([a], ctx)
