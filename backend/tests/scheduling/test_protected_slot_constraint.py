"""Tests for protected slot constraint (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.protected_slot import ProtectedSlotConstraint


# ==================== Helpers ====================


def _person(pid=None, name="Resident"):
    """Build a mock person."""
    return SimpleNamespace(id=pid or uuid4(), name=name)


def _block(bid=None, block_date=None, time_of_day="AM", **kwargs):
    """Build a mock block with optional attributes."""
    ns = SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


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


# ==================== Init Tests ====================


class TestProtectedSlotInit:
    """Test ProtectedSlotConstraint initialization."""

    def test_name(self):
        c = ProtectedSlotConstraint()
        assert c.name == "ProtectedSlot"

    def test_type(self):
        c = ProtectedSlotConstraint()
        assert c.constraint_type == ConstraintType.AVAILABILITY

    def test_priority(self):
        c = ProtectedSlotConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_default_patterns_empty(self):
        c = ProtectedSlotConstraint()
        assert c._protected_patterns == {}

    def test_patterns_from_init(self):
        tid = uuid4()
        patterns = {tid: [{"day_of_week": 3, "time_of_day": "PM"}]}
        c = ProtectedSlotConstraint(protected_patterns=patterns)
        assert c._protected_patterns == patterns


# ==================== get_protected_patterns Tests ====================


class TestGetProtectedPatterns:
    """Test get_protected_patterns method."""

    def test_returns_patterns_for_known_template(self):
        tid = uuid4()
        patterns_list = [{"day_of_week": 3, "time_of_day": "PM"}]
        c = ProtectedSlotConstraint(protected_patterns={tid: patterns_list})
        assert c.get_protected_patterns(tid) == patterns_list

    def test_returns_empty_for_unknown_template(self):
        c = ProtectedSlotConstraint()
        assert c.get_protected_patterns(uuid4()) == []


# ==================== _is_protected_slot Tests ====================


class TestIsProtectedSlot:
    """Test _is_protected_slot helper.

    Pattern day_of_week convention: 0=Sunday, 1=Monday, ..., 6=Saturday
    Python weekday() convention: 0=Monday, ..., 6=Sunday
    """

    def test_monday_match(self):
        """Pattern day 1 (Monday) matches Python weekday 0."""
        c = ProtectedSlotConstraint()
        b = _block(block_date=date(2025, 3, 3), time_of_day="AM")  # Monday
        pattern = {"day_of_week": 1, "time_of_day": "AM"}
        assert c._is_protected_slot(b, pattern) is True

    def test_wednesday_pm_match(self):
        """Pattern day 3 (Wednesday) matches Python weekday 2."""
        c = ProtectedSlotConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")  # Wednesday
        pattern = {"day_of_week": 3, "time_of_day": "PM"}
        assert c._is_protected_slot(b, pattern) is True

    def test_sunday_match(self):
        """Pattern day 0 (Sunday) matches Python weekday 6."""
        c = ProtectedSlotConstraint()
        b = _block(block_date=date(2025, 3, 9), time_of_day="AM")  # Sunday
        pattern = {"day_of_week": 0, "time_of_day": "AM"}
        assert c._is_protected_slot(b, pattern) is True

    def test_saturday_match(self):
        """Pattern day 6 (Saturday) matches Python weekday 5."""
        c = ProtectedSlotConstraint()
        b = _block(block_date=date(2025, 3, 8), time_of_day="AM")  # Saturday
        pattern = {"day_of_week": 6, "time_of_day": "AM"}
        assert c._is_protected_slot(b, pattern) is True

    def test_wrong_day_no_match(self):
        c = ProtectedSlotConstraint()
        b = _block(block_date=date(2025, 3, 4), time_of_day="AM")  # Tuesday
        pattern = {"day_of_week": 3, "time_of_day": "AM"}  # Wednesday
        assert c._is_protected_slot(b, pattern) is False

    def test_wrong_time_no_match(self):
        c = ProtectedSlotConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")  # Wed AM
        pattern = {"day_of_week": 3, "time_of_day": "PM"}  # Wed PM
        assert c._is_protected_slot(b, pattern) is False

    def test_week_number_match(self):
        """Block week_number matches pattern week_number."""
        c = ProtectedSlotConstraint()
        b = _block(
            block_date=date(2025, 3, 3),
            time_of_day="AM",
            week_number=2,
        )
        pattern = {"day_of_week": 1, "time_of_day": "AM", "week_number": 2}
        assert c._is_protected_slot(b, pattern) is True

    def test_week_number_mismatch(self):
        """Block week 1 != pattern week 3."""
        c = ProtectedSlotConstraint()
        b = _block(
            block_date=date(2025, 3, 3),
            time_of_day="AM",
            week_number=1,
        )
        pattern = {"day_of_week": 1, "time_of_day": "AM", "week_number": 3}
        assert c._is_protected_slot(b, pattern) is False

    def test_no_week_number_on_block_ignores_check(self):
        """Block without week_number attr: week check passes."""
        c = ProtectedSlotConstraint()
        b = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        pattern = {"day_of_week": 1, "time_of_day": "AM", "week_number": 2}
        # block_week is None -> no mismatch -> True
        assert c._is_protected_slot(b, pattern) is True

    def test_block_without_date_attr(self):
        """Block without date attribute returns False."""
        c = ProtectedSlotConstraint()
        b = SimpleNamespace(id=uuid4(), time_of_day="AM")  # No date attr
        pattern = {"day_of_week": 1, "time_of_day": "AM"}
        assert c._is_protected_slot(b, pattern) is False


# ==================== _get_conflicting_templates Tests ====================


class TestGetConflictingTemplates:
    """Test _get_conflicting_templates helper."""

    def test_different_rotation_type_conflicts(self):
        c = ProtectedSlotConstraint()
        clinic = _template(name="Clinic", rotation_type="outpatient")
        ctx = _context(templates=[clinic])
        result = c._get_conflicting_templates("lecture", ctx)
        assert clinic.id in result

    def test_same_rotation_type_no_conflict(self):
        c = ProtectedSlotConstraint()
        lec = _template(name="Lecture", rotation_type="lecture")
        ctx = _context(templates=[lec])
        result = c._get_conflicting_templates("lecture", ctx)
        assert len(result) == 0

    def test_template_without_rotation_type_not_included(self):
        """Templates without rotation_type attr are not conflicting."""
        c = ProtectedSlotConstraint()
        t = _template(name="FMIT")  # No rotation_type
        ctx = _context(templates=[t])
        result = c._get_conflicting_templates("lecture", ctx)
        assert len(result) == 0

    def test_multiple_templates_mixed(self):
        c = ProtectedSlotConstraint()
        lec = _template(name="Lecture", rotation_type="lecture")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        fmit = _template(name="FMIT", rotation_type="inpatient")
        ctx = _context(templates=[lec, clinic, fmit])
        result = c._get_conflicting_templates("lecture", ctx)
        assert clinic.id in result
        assert fmit.id in result
        assert lec.id not in result


# ==================== _get_patterns Tests ====================


class TestGetPatterns:
    """Test _get_patterns helper (instance vs context)."""

    def test_uses_instance_patterns(self):
        tid = uuid4()
        patterns = {tid: [{"day_of_week": 4}]}
        c = ProtectedSlotConstraint(protected_patterns=patterns)
        ctx = _context()
        assert c._get_patterns(ctx) == patterns

    def test_falls_back_to_context(self):
        c = ProtectedSlotConstraint()
        ctx = _context()
        tid = uuid4()
        ctx.protected_patterns = {tid: [{"day_of_week": 4}]}
        result = c._get_patterns(ctx)
        assert tid in result

    def test_no_patterns_anywhere(self):
        c = ProtectedSlotConstraint()
        ctx = _context()
        assert c._get_patterns(ctx) == {}


# ==================== validate Tests ====================


class TestProtectedSlotValidate:
    """Test ProtectedSlotConstraint.validate method."""

    def test_no_patterns_satisfied(self):
        c = ProtectedSlotConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_assignments_satisfied(self):
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [
                    {"day_of_week": 3, "time_of_day": "PM", "activity_type": "lecture"}
                ]
            }
        )
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_matching_activity_satisfied(self):
        """Assignment rotation_type matches protected activity -> no violation."""
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [
                    {"day_of_week": 3, "time_of_day": "PM", "activity_type": "lecture"}
                ]
            }
        )
        res = _person(name="Resident A")
        lec = _template(name="Lecture", rotation_type="lecture")
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")  # Wed PM
        ctx = _context(residents=[res], blocks=[b], templates=[lec])

        a = _assignment(res.id, b.id, rotation_template_id=lec.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_conflicting_activity_violation(self):
        """Assignment rotation_type != protected activity -> CRITICAL violation."""
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [
                    {"day_of_week": 3, "time_of_day": "PM", "activity_type": "lecture"}
                ]
            }
        )
        res = _person(name="Resident A")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")  # Wed PM
        ctx = _context(residents=[res], blocks=[b], templates=[clinic])

        a = _assignment(res.id, b.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "protected" in result.violations[0].message
        assert "lecture" in result.violations[0].message

    def test_non_protected_slot_satisfied(self):
        """Assignment on non-protected slot -> no violation."""
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [
                    {"day_of_week": 3, "time_of_day": "PM", "activity_type": "lecture"}
                ]
            }
        )
        res = _person(name="Resident A")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block(block_date=date(2025, 3, 4), time_of_day="AM")  # Tue AM
        ctx = _context(residents=[res], blocks=[b], templates=[clinic])

        a = _assignment(res.id, b.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_violation_details(self):
        """Violation includes date, time_of_day, protected_activity, assigned type."""
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [
                    {"day_of_week": 3, "time_of_day": "PM", "activity_type": "lecture"}
                ]
            }
        )
        res = _person(name="Dr. Smith")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(residents=[res], blocks=[b], templates=[clinic])

        a = _assignment(res.id, b.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        v = result.violations[0]
        assert v.details["date"] == "2025-03-05"
        assert v.details["time_of_day"] == "PM"
        assert v.details["protected_activity"] == "lecture"
        assert v.details["assigned_rotation_type"] == "outpatient"
        assert v.person_id == res.id
        assert v.block_id == b.id

    def test_multiple_violations(self):
        """Two residents on protected slot -> two violations."""
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [
                    {"day_of_week": 3, "time_of_day": "PM", "activity_type": "lecture"}
                ]
            }
        )
        res1 = _person(name="R1")
        res2 = _person(name="R2")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(residents=[res1, res2], blocks=[b], templates=[clinic])

        assignments = [
            _assignment(res1.id, b.id, rotation_template_id=clinic.id),
            _assignment(res2.id, b.id, rotation_template_id=clinic.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2

    def test_unknown_resident_skipped(self):
        """Assignment for person not in residents list is skipped."""
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [
                    {"day_of_week": 3, "time_of_day": "PM", "activity_type": "lecture"}
                ]
            }
        )
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(blocks=[b], templates=[clinic])

        a = _assignment(uuid4(), b.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pattern_without_activity_type_skipped(self):
        """Pattern with empty activity_type is skipped."""
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [{"day_of_week": 3, "time_of_day": "PM", "activity_type": ""}]
            }
        )
        res = _person(name="R1")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        ctx = _context(residents=[res], blocks=[b], templates=[clinic])

        a = _assignment(res.id, b.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_weekend_off_protection(self):
        """Weekend off pattern: Saturday clinic assignment -> violation."""
        tid = uuid4()
        c = ProtectedSlotConstraint(
            protected_patterns={
                tid: [
                    {"day_of_week": 6, "time_of_day": "AM", "activity_type": "off"},
                    {"day_of_week": 6, "time_of_day": "PM", "activity_type": "off"},
                    {"day_of_week": 0, "time_of_day": "AM", "activity_type": "off"},
                    {"day_of_week": 0, "time_of_day": "PM", "activity_type": "off"},
                ]
            }
        )
        res = _person(name="R1")
        clinic = _template(name="Clinic", rotation_type="outpatient")
        sat = _block(block_date=date(2025, 3, 8), time_of_day="AM")  # Saturday
        ctx = _context(residents=[res], blocks=[sat], templates=[clinic])

        a = _assignment(res.id, sat.id, rotation_template_id=clinic.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
