"""Tests for post-call auto-assignment constraint (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.fmit import is_sun_thurs
from app.scheduling.constraints.post_call import PostCallAutoAssignmentConstraint


# ==================== Helpers ====================


def _person(pid=None, name="Faculty"):
    """Build a mock person with .id and .name."""
    return SimpleNamespace(id=pid or uuid4(), name=name)


def _block(bid=None, block_date=None, time_of_day="AM"):
    """Build a mock block with .id, .date, .time_of_day."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )


def _template(tid=None, name="Template", abbreviation=None):
    """Build a mock template with .id, .name, .abbreviation."""
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
    if abbreviation is not None:
        ns.abbreviation = abbreviation
    return ns


def _assignment(person_id, block_id, rotation_template_id=None, call_type=None):
    """Build a mock assignment."""
    ns = SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        rotation_template_id=rotation_template_id,
    )
    if call_type is not None:
        ns.call_type = call_type
    return ns


def _context(residents=None, blocks=None, faculty=None, templates=None):
    """Build a SchedulingContext."""
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )


# ==================== is_sun_thurs Tests ====================


class TestIsSunThurs:
    """Test is_sun_thurs helper from fmit module."""

    def test_sunday(self):
        assert is_sun_thurs(date(2025, 3, 2)) is True  # Sunday

    def test_monday(self):
        assert is_sun_thurs(date(2025, 3, 3)) is True  # Monday

    def test_tuesday(self):
        assert is_sun_thurs(date(2025, 3, 4)) is True  # Tuesday

    def test_wednesday(self):
        assert is_sun_thurs(date(2025, 3, 5)) is True  # Wednesday

    def test_thursday(self):
        assert is_sun_thurs(date(2025, 3, 6)) is True  # Thursday

    def test_friday(self):
        assert is_sun_thurs(date(2025, 3, 7)) is False  # Friday

    def test_saturday(self):
        assert is_sun_thurs(date(2025, 3, 8)) is False  # Saturday


# ==================== PostCallAutoAssignmentConstraint Init ====================


class TestPostCallConstraintInit:
    """Test PostCallAutoAssignmentConstraint initialization."""

    def test_defaults(self):
        c = PostCallAutoAssignmentConstraint()
        assert c.weight == 35.0
        assert c.name == "PostCallAutoAssignment"
        assert c.constraint_type == ConstraintType.CALL
        assert c.priority == ConstraintPriority.HIGH

    def test_custom_weight(self):
        c = PostCallAutoAssignmentConstraint(weight=50.0)
        assert c.weight == 50.0

    def test_activity_constants(self):
        assert PostCallAutoAssignmentConstraint.PCAT_ACTIVITY == "PCAT"
        assert PostCallAutoAssignmentConstraint.DO_ACTIVITY == "DO"


# ==================== _find_template_id Tests ====================


class TestFindTemplateId:
    """Test _find_template_id helper method."""

    def test_find_by_name(self):
        c = PostCallAutoAssignmentConstraint()
        pcat_template = _template(name="PCAT")
        ctx = _context(templates=[pcat_template])
        result = c._find_template_id(ctx, "PCAT")
        assert result == pcat_template.id

    def test_find_by_abbreviation(self):
        c = PostCallAutoAssignmentConstraint()
        do_template = _template(name="Direct Observation", abbreviation="DO")
        ctx = _context(templates=[do_template])
        result = c._find_template_id(ctx, "DO")
        assert result == do_template.id

    def test_case_insensitive(self):
        c = PostCallAutoAssignmentConstraint()
        pcat_template = _template(name="pcat")
        ctx = _context(templates=[pcat_template])
        result = c._find_template_id(ctx, "PCAT")
        assert result == pcat_template.id

    def test_not_found(self):
        c = PostCallAutoAssignmentConstraint()
        ctx = _context(templates=[_template(name="Other")])
        result = c._find_template_id(ctx, "PCAT")
        assert result is None

    def test_prefix_match_for_pcat(self):
        """PCAT-AM matches when looking for PCAT."""
        c = PostCallAutoAssignmentConstraint()
        pcat_am = _template(name="PCAT-AM")
        ctx = _context(templates=[pcat_am])
        result = c._find_template_id(ctx, "PCAT")
        assert result == pcat_am.id

    def test_prefix_match_for_do(self):
        """DO-PM matches when looking for DO."""
        c = PostCallAutoAssignmentConstraint()
        do_pm = _template(name="DO-PM")
        ctx = _context(templates=[do_pm])
        result = c._find_template_id(ctx, "DO")
        assert result == do_pm.id

    def test_empty_templates(self):
        c = PostCallAutoAssignmentConstraint()
        ctx = _context(templates=[])
        result = c._find_template_id(ctx, "PCAT")
        assert result is None


# ==================== _group_blocks_by_date_time Tests ====================


class TestGroupBlocksByDateTime:
    """Test _group_blocks_by_date_time helper method."""

    def test_groups_by_date_and_time(self):
        c = PostCallAutoAssignmentConstraint()
        b1 = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        b2 = _block(block_date=date(2025, 3, 3), time_of_day="PM")
        b3 = _block(block_date=date(2025, 3, 4), time_of_day="AM")
        ctx = _context(blocks=[b1, b2, b3])

        result = c._group_blocks_by_date_time(ctx)
        assert len(result[(date(2025, 3, 3), "AM")]) == 1
        assert len(result[(date(2025, 3, 3), "PM")]) == 1
        assert len(result[(date(2025, 3, 4), "AM")]) == 1

    def test_empty_blocks(self):
        c = PostCallAutoAssignmentConstraint()
        ctx = _context(blocks=[])
        result = c._group_blocks_by_date_time(ctx)
        assert len(result) == 0


# ==================== _extract_call_assignments Tests ====================


class TestExtractCallAssignments:
    """Test _extract_call_assignments helper method."""

    def test_extracts_overnight_calls(self):
        c = PostCallAutoAssignmentConstraint()
        ctx = _context()
        call_a = _assignment(uuid4(), uuid4(), call_type="overnight")
        regular_a = _assignment(uuid4(), uuid4())
        result = c._extract_call_assignments([call_a, regular_a], ctx)
        assert len(result) == 1
        assert result[0] is call_a

    def test_ignores_non_overnight(self):
        c = PostCallAutoAssignmentConstraint()
        ctx = _context()
        day_call = _assignment(uuid4(), uuid4(), call_type="day")
        result = c._extract_call_assignments([day_call], ctx)
        assert len(result) == 0

    def test_empty_assignments(self):
        c = PostCallAutoAssignmentConstraint()
        ctx = _context()
        result = c._extract_call_assignments([], ctx)
        assert len(result) == 0


# ==================== _is_exempt_block Tests ====================


class TestIsExemptBlock:
    """Test _is_exempt_block helper method."""

    def test_not_exempt_by_default(self):
        c = PostCallAutoAssignmentConstraint()
        fac = _person()
        b1 = _block()
        ctx = _context()
        assert c._is_exempt_block(fac.id, b1, ctx) is False

    def test_exempt_if_locked(self):
        c = PostCallAutoAssignmentConstraint()
        fac = _person()
        b1 = _block()
        ctx = _context()
        ctx.locked_blocks = {(fac.id, b1.id)}
        assert c._is_exempt_block(fac.id, b1, ctx) is True

    def test_exempt_if_unavailable(self):
        c = PostCallAutoAssignmentConstraint()
        fac = _person()
        b1 = _block()
        ctx = _context()
        ctx.availability = {fac.id: {b1.id: {"available": False}}}
        assert c._is_exempt_block(fac.id, b1, ctx) is True

    def test_not_exempt_if_available(self):
        c = PostCallAutoAssignmentConstraint()
        fac = _person()
        b1 = _block()
        ctx = _context()
        ctx.availability = {fac.id: {b1.id: {"available": True}}}
        assert c._is_exempt_block(fac.id, b1, ctx) is False


# ==================== validate Tests ====================


class TestPostCallValidate:
    """Test PostCallAutoAssignmentConstraint.validate method."""

    def test_no_call_assignments_satisfied(self):
        """No overnight call -> always satisfied."""
        c = PostCallAutoAssignmentConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_call_on_wednesday_missing_pcat_and_do(self):
        """Wed call, no PCAT/DO on Thu -> 2 violations."""
        c = PostCallAutoAssignmentConstraint()
        fac = _person(name="Dr. Smith")
        wednesday = date(2025, 3, 5)  # Wednesday
        thursday = date(2025, 3, 6)

        call_block = _block(block_date=wednesday, time_of_day="PM")
        am_block = _block(block_date=thursday, time_of_day="AM")
        pm_block = _block(block_date=thursday, time_of_day="PM")
        pcat_template = _template(name="PCAT")
        do_template = _template(name="DO")

        ctx = _context(
            faculty=[fac],
            blocks=[call_block, am_block, pm_block],
            templates=[pcat_template, do_template],
        )

        # Only the call assignment, no PCAT/DO
        call_a = _assignment(fac.id, call_block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2
        assert any("PCAT" in v.message for v in result.violations)
        assert any("DO" in v.message for v in result.violations)

    def test_call_on_wednesday_with_pcat_and_do(self):
        """Wed call with proper PCAT/DO on Thu -> satisfied."""
        c = PostCallAutoAssignmentConstraint()
        fac = _person(name="Dr. Smith")
        wednesday = date(2025, 3, 5)
        thursday = date(2025, 3, 6)

        call_block = _block(block_date=wednesday, time_of_day="PM")
        am_block = _block(block_date=thursday, time_of_day="AM")
        pm_block = _block(block_date=thursday, time_of_day="PM")
        pcat_template = _template(name="PCAT")
        do_template = _template(name="DO")

        ctx = _context(
            faculty=[fac],
            blocks=[call_block, am_block, pm_block],
            templates=[pcat_template, do_template],
        )

        assignments = [
            _assignment(fac.id, call_block.id, call_type="overnight"),
            _assignment(fac.id, am_block.id, rotation_template_id=pcat_template.id),
            _assignment(fac.id, pm_block.id, rotation_template_id=do_template.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_call_on_friday_not_checked(self):
        """Friday call -> not Sun-Thurs -> no violations."""
        c = PostCallAutoAssignmentConstraint()
        fac = _person(name="Dr. Smith")
        friday = date(2025, 3, 7)

        call_block = _block(block_date=friday, time_of_day="PM")
        ctx = _context(
            faculty=[fac],
            blocks=[call_block],
            templates=[_template(name="PCAT"), _template(name="DO")],
        )

        call_a = _assignment(fac.id, call_block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_no_pcat_do_templates_no_violations(self):
        """No PCAT/DO templates defined -> no violations."""
        c = PostCallAutoAssignmentConstraint()
        fac = _person()
        wednesday = date(2025, 3, 5)

        call_block = _block(block_date=wednesday, time_of_day="PM")
        ctx = _context(
            faculty=[fac],
            blocks=[call_block],
            templates=[_template(name="Clinic")],  # No PCAT or DO
        )

        call_a = _assignment(fac.id, call_block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        # No PCAT/DO templates -> can't detect missing assignments
        assert result.satisfied is True

    def test_penalty_on_violations(self):
        """Violations produce non-zero penalty."""
        c = PostCallAutoAssignmentConstraint(weight=35.0)
        fac = _person(name="Dr. Smith")
        wednesday = date(2025, 3, 5)
        thursday = date(2025, 3, 6)

        call_block = _block(block_date=wednesday, time_of_day="PM")
        am_block = _block(block_date=thursday, time_of_day="AM")
        pm_block = _block(block_date=thursday, time_of_day="PM")

        ctx = _context(
            faculty=[fac],
            blocks=[call_block, am_block, pm_block],
            templates=[_template(name="PCAT"), _template(name="DO")],
        )

        call_a = _assignment(fac.id, call_block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.penalty > 0

    def test_exempt_block_no_violation(self):
        """Locked next-day block -> no violation for that block."""
        c = PostCallAutoAssignmentConstraint()
        fac = _person(name="Dr. Smith")
        wednesday = date(2025, 3, 5)
        thursday = date(2025, 3, 6)

        call_block = _block(block_date=wednesday, time_of_day="PM")
        am_block = _block(block_date=thursday, time_of_day="AM")
        pm_block = _block(block_date=thursday, time_of_day="PM")

        ctx = _context(
            faculty=[fac],
            blocks=[call_block, am_block, pm_block],
            templates=[_template(name="PCAT"), _template(name="DO")],
        )
        # Lock both next-day blocks
        ctx.locked_blocks = {(fac.id, am_block.id), (fac.id, pm_block.id)}

        call_a = _assignment(fac.id, call_block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True
