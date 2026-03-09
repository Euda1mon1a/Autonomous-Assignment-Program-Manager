"""Tests for FM scheduling constraints (pure logic, no DB required).

Note: The validate() methods in WednesdayPMLecConstraint, InternContinuityConstraint,
and NightFloatSlotConstraint construct ConstraintViolation with `entity_id` (not a valid
field) and omit `constraint_type` (a required field). Violation-producing paths will
raise TypeError. Tests cover satisfied paths and helper methods.
"""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.fm_scheduling import (
    LEC_EXEMPT_ROTATIONS,
    NIGHT_FLOAT_ROTATIONS,
    WEDNESDAY,
    InternContinuityConstraint,
    NightFloatSlotConstraint,
    WednesdayPMLecConstraint,
)
from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)


# ==================== Helpers ====================


def _person(pid=None, name="Resident", pgy_level=None):
    """Build a mock person."""
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    if pgy_level is not None:
        ns.pgy_level = pgy_level
    return ns


def _block(bid=None, block_date=None, time_of_day="AM"):
    """Build a mock block."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )


def _template(tid=None, name="Template", abbreviation=None):
    """Build a mock template."""
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
    if abbreviation is not None:
        ns.abbreviation = abbreviation
    return ns


def _rich_assignment(aid=None, block=None, rotation_template=None, resident=None):
    """Build a mock assignment with .block, .rotation_template, .resident attrs."""
    return SimpleNamespace(
        id=aid or uuid4(),
        block=block,
        rotation_template=rotation_template,
        resident=resident,
    )


def _context(residents=None, blocks=None, faculty=None, templates=None):
    """Build a SchedulingContext."""
    return SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )


# ==================== Constants Tests ====================


class TestConstants:
    """Test module-level constants."""

    def test_lec_exempt_rotations(self):
        expected = frozenset(
            [
                "NF",
                "NF-PM",
                "NF-ENDO",
                "NEURO-NF",
                "PNF",
                "LDNF",
                "KAPI-LD",
                "HILO",
                "TDY",
            ]
        )
        assert expected == LEC_EXEMPT_ROTATIONS

    def test_night_float_rotations(self):
        expected = frozenset(["NF", "NF-PM", "NF-ENDO", "NEURO-NF", "PNF"])
        assert expected == NIGHT_FLOAT_ROTATIONS

    def test_wednesday_constant(self):
        assert WEDNESDAY == 2

    def test_night_float_am_patterns(self):
        patterns = NightFloatSlotConstraint.NIGHT_FLOAT_AM_PATTERNS
        assert patterns["NF"] == "OFF-AM"
        assert patterns["NEURO-NF"] == "NEURO"
        assert patterns["LDNF"] == "L&D"
        assert patterns["KAPI-LD"] == "KAP"


# ==================== WednesdayPMLecConstraint Init & Helpers ====================


class TestWednesdayPMLecInit:
    """Test WednesdayPMLecConstraint initialization."""

    def test_name(self):
        c = WednesdayPMLecConstraint()
        assert c.name == "WednesdayPMLec"

    def test_type(self):
        c = WednesdayPMLecConstraint()
        assert c.constraint_type == ConstraintType.ROTATION

    def test_priority(self):
        c = WednesdayPMLecConstraint()
        assert c.priority == ConstraintPriority.HIGH


class TestWednesdayPMLecHelpers:
    """Test WednesdayPMLecConstraint helper methods."""

    def test_is_wednesday_pm_true(self):
        c = WednesdayPMLecConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")  # Wednesday
        assert c._is_wednesday_pm(b) is True

    def test_is_wednesday_am_false(self):
        c = WednesdayPMLecConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        assert c._is_wednesday_pm(b) is False

    def test_is_thursday_pm_false(self):
        c = WednesdayPMLecConstraint()
        b = _block(block_date=date(2025, 3, 6), time_of_day="PM")  # Thursday
        assert c._is_wednesday_pm(b) is False

    def test_is_exempt_nf(self):
        c = WednesdayPMLecConstraint()
        t = _template(abbreviation="NF")
        assert c._is_exempt_rotation(t) is True

    def test_is_exempt_tdy(self):
        c = WednesdayPMLecConstraint()
        t = _template(abbreviation="TDY")
        assert c._is_exempt_rotation(t) is True

    def test_is_not_exempt_clinic(self):
        c = WednesdayPMLecConstraint()
        t = _template(abbreviation="CLINIC")
        assert c._is_exempt_rotation(t) is False

    def test_is_exempt_case_insensitive(self):
        c = WednesdayPMLecConstraint()
        t = _template(abbreviation="nf")
        assert c._is_exempt_rotation(t) is True

    def test_is_exempt_no_abbreviation(self):
        c = WednesdayPMLecConstraint()
        t = _template(name="Something")  # No abbreviation
        assert c._is_exempt_rotation(t) is False


class TestWednesdayPMLecValidate:
    """Test WednesdayPMLecConstraint.validate method (satisfied paths)."""

    def test_no_assignments_satisfied(self):
        c = WednesdayPMLecConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_assignment_without_block_skipped(self):
        """Assignment without .block attr -> skipped."""
        c = WednesdayPMLecConstraint()
        a = SimpleNamespace(rotation_template=_template(abbreviation="CLINIC"))
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_assignment_without_template_skipped(self):
        """Assignment without .rotation_template -> skipped."""
        c = WednesdayPMLecConstraint()
        a = SimpleNamespace(block=_block(block_date=date(2025, 3, 5), time_of_day="PM"))
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_wednesday_pm_lec_pm_satisfied(self):
        """Wednesday PM with LEC-PM -> satisfied."""
        c = WednesdayPMLecConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        t = _template(abbreviation="LEC-PM")
        a = _rich_assignment(block=b, rotation_template=t)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_wednesday_pm_exempt_rotation_satisfied(self):
        """Wednesday PM with NF (exempt) -> satisfied."""
        c = WednesdayPMLecConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        t = _template(abbreviation="NF")
        a = _rich_assignment(block=b, rotation_template=t)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_non_wednesday_non_lec_satisfied(self):
        """Thursday PM with non-LEC -> satisfied (not Wednesday)."""
        c = WednesdayPMLecConstraint()
        b = _block(block_date=date(2025, 3, 6), time_of_day="PM")
        t = _template(abbreviation="CLINIC")
        a = _rich_assignment(block=b, rotation_template=t)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_wednesday_pm_non_lec_non_exempt_violation(self):
        """Wednesday PM with CLINIC (non-exempt, non-LEC) -> violation."""
        c = WednesdayPMLecConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        t = _template(abbreviation="CLINIC")
        a = _rich_assignment(block=b, rotation_template=t)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) > 0


# ==================== InternContinuityConstraint Init & Helpers ====================


class TestInternContinuityInit:
    """Test InternContinuityConstraint initialization."""

    def test_name(self):
        c = InternContinuityConstraint()
        assert c.name == "InternContinuity"

    def test_type(self):
        c = InternContinuityConstraint()
        assert c.constraint_type == ConstraintType.ROTATION

    def test_priority(self):
        c = InternContinuityConstraint()
        assert c.priority == ConstraintPriority.HIGH


class TestInternContinuityHelpers:
    """Test InternContinuityConstraint helper methods."""

    def test_is_wednesday_am_true(self):
        c = InternContinuityConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        assert c._is_wednesday_am(b) is True

    def test_is_wednesday_pm_false(self):
        c = InternContinuityConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="PM")
        assert c._is_wednesday_am(b) is False

    def test_is_thursday_am_false(self):
        c = InternContinuityConstraint()
        b = _block(block_date=date(2025, 3, 6), time_of_day="AM")
        assert c._is_wednesday_am(b) is False


class TestInternContinuityValidate:
    """Test InternContinuityConstraint.validate method (satisfied paths)."""

    def test_no_assignments_satisfied(self):
        c = InternContinuityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_pgy1_wednesday_am_continuity_satisfied(self):
        """PGY-1 on Wednesday AM with C -> satisfied."""
        c = InternContinuityConstraint()
        res = _person(pgy_level=1)
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        t = _template(abbreviation="C")
        a = _rich_assignment(block=b, rotation_template=t, resident=res)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pgy1_wednesday_am_cont_satisfied(self):
        """PGY-1 on Wednesday AM with CONT -> satisfied."""
        c = InternContinuityConstraint()
        res = _person(pgy_level=1)
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        t = _template(abbreviation="CONT")
        a = _rich_assignment(block=b, rotation_template=t, resident=res)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pgy2_wednesday_am_non_continuity_satisfied(self):
        """PGY-2 on Wednesday AM with non-continuity -> satisfied (only checks PGY-1)."""
        c = InternContinuityConstraint()
        res = _person(pgy_level=2)
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        t = _template(abbreviation="CLINIC")
        a = _rich_assignment(block=b, rotation_template=t, resident=res)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pgy1_thursday_am_non_continuity_satisfied(self):
        """PGY-1 on Thursday AM (not Wednesday) -> satisfied."""
        c = InternContinuityConstraint()
        res = _person(pgy_level=1)
        b = _block(block_date=date(2025, 3, 6), time_of_day="AM")
        t = _template(abbreviation="CLINIC")
        a = _rich_assignment(block=b, rotation_template=t, resident=res)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_missing_resident_skipped(self):
        """Assignment without .resident -> skipped."""
        c = InternContinuityConstraint()
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        t = _template(abbreviation="CLINIC")
        a = SimpleNamespace(id=uuid4(), block=b, rotation_template=t)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pgy1_wednesday_am_non_continuity_violation(self):
        """PGY-1 Wednesday AM with CLINIC -> violation."""
        c = InternContinuityConstraint()
        res = _person(pgy_level=1)
        b = _block(block_date=date(2025, 3, 5), time_of_day="AM")
        t = _template(abbreviation="CLINIC")
        a = _rich_assignment(block=b, rotation_template=t, resident=res)
        ctx = _context()
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) > 0


# ==================== NightFloatSlotConstraint Init & Helpers ====================


class TestNightFloatSlotInit:
    """Test NightFloatSlotConstraint initialization."""

    def test_name(self):
        c = NightFloatSlotConstraint()
        assert c.name == "NightFloatSlot"

    def test_type(self):
        c = NightFloatSlotConstraint()
        assert c.constraint_type == ConstraintType.ROTATION

    def test_priority(self):
        c = NightFloatSlotConstraint()
        assert c.priority == ConstraintPriority.HIGH


class TestNightFloatSlotHelpers:
    """Test NightFloatSlotConstraint helper methods."""

    def test_is_am_slot_true(self):
        c = NightFloatSlotConstraint()
        b = _block(time_of_day="AM")
        assert c._is_am_slot(b) is True

    def test_is_am_slot_pm_false(self):
        c = NightFloatSlotConstraint()
        b = _block(time_of_day="PM")
        assert c._is_am_slot(b) is False

    def test_is_am_slot_no_attr_false(self):
        c = NightFloatSlotConstraint()
        b = SimpleNamespace(id=uuid4())
        assert c._is_am_slot(b) is False


class TestNightFloatSlotValidate:
    """Test NightFloatSlotConstraint.validate method (satisfied paths)."""

    def test_no_assignments_satisfied(self):
        c = NightFloatSlotConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_nf_pm_with_off_am_satisfied(self):
        """NF on PM with OFF-AM on AM -> satisfied."""
        c = NightFloatSlotConstraint()
        res = _person(name="Dr. NF")
        day = date(2025, 3, 3)
        am_block = _block(block_date=day, time_of_day="AM")
        pm_block = _block(block_date=day, time_of_day="PM")
        nf_template = _template(abbreviation="NF")
        offam_template = _template(abbreviation="OFF-AM")

        pm_a = _rich_assignment(
            block=pm_block, rotation_template=nf_template, resident=res
        )
        am_a = _rich_assignment(
            block=am_block, rotation_template=offam_template, resident=res
        )
        ctx = _context()
        result = c.validate([pm_a, am_a], ctx)
        assert result.satisfied is True

    def test_non_nf_resident_not_checked(self):
        """Non-NF assignment on PM -> AM slot not checked."""
        c = NightFloatSlotConstraint()
        res = _person(name="Dr. Day")
        day = date(2025, 3, 3)
        am_block = _block(block_date=day, time_of_day="AM")
        pm_block = _block(block_date=day, time_of_day="PM")
        clinic = _template(abbreviation="CLINIC")

        pm_a = _rich_assignment(block=pm_block, rotation_template=clinic, resident=res)
        am_a = _rich_assignment(block=am_block, rotation_template=clinic, resident=res)
        ctx = _context()
        result = c.validate([pm_a, am_a], ctx)
        assert result.satisfied is True

    def test_neuro_nf_with_neuro_am_satisfied(self):
        """NEURO-NF on PM with NEURO on AM -> satisfied."""
        c = NightFloatSlotConstraint()
        res = _person(name="Dr. Neuro")
        day = date(2025, 3, 3)
        am_block = _block(block_date=day, time_of_day="AM")
        pm_block = _block(block_date=day, time_of_day="PM")
        neuro_nf = _template(abbreviation="NEURO-NF")
        neuro = _template(abbreviation="NEURO")

        pm_a = _rich_assignment(
            block=pm_block, rotation_template=neuro_nf, resident=res
        )
        am_a = _rich_assignment(block=am_block, rotation_template=neuro, resident=res)
        ctx = _context()
        result = c.validate([pm_a, am_a], ctx)
        assert result.satisfied is True

    def test_missing_am_assignment_no_error(self):
        """NF on PM but no AM assignment at all -> no AM to check -> satisfied."""
        c = NightFloatSlotConstraint()
        res = _person(name="Dr. NF")
        day = date(2025, 3, 3)
        pm_block = _block(block_date=day, time_of_day="PM")
        nf_template = _template(abbreviation="NF")

        pm_a = _rich_assignment(
            block=pm_block, rotation_template=nf_template, resident=res
        )
        ctx = _context()
        result = c.validate([pm_a], ctx)
        assert result.satisfied is True

    def test_nf_wrong_am_raises(self):
        """NF on PM with wrong AM pattern -> TypeError (known bug)."""
        c = NightFloatSlotConstraint()
        res = _person(name="Dr. NF")
        day = date(2025, 3, 3)
        am_block = _block(block_date=day, time_of_day="AM")
        pm_block = _block(block_date=day, time_of_day="PM")
        nf_template = _template(abbreviation="NF")
        wrong_am = _template(abbreviation="CLINIC")

        pm_a = _rich_assignment(
            block=pm_block, rotation_template=nf_template, resident=res
        )
        am_a = _rich_assignment(
            block=am_block, rotation_template=wrong_am, resident=res
        )
        ctx = _context()
        result = c.validate([pm_a, am_a], ctx)
        assert result.satisfied is False
        assert len(result.violations) > 0
