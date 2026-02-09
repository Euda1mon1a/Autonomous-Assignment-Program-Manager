"""Tests for NightFloatPostCallConstraint (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.night_float_post_call import (
    NightFloatPostCallConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Resident"):
    """Build a mock person with .id and .name."""
    return SimpleNamespace(id=pid or uuid4(), name=name)


def _block(
    bid=None, block_date=None, time_of_day="AM", block_number=None, block_half=None
):
    """Build a mock block with .id, .date, .time_of_day, and optional block_number/block_half."""
    ns = SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )
    if block_number is not None:
        ns.block_number = block_number
    if block_half is not None:
        ns.block_half = block_half
    return ns


def _template(tid=None, name="Template", abbreviation=None):
    """Build a mock template with .id, .name, .abbreviation."""
    ns = SimpleNamespace(id=tid or uuid4(), name=name)
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


# ==================== Init Tests ====================


class TestNightFloatPostCallInit:
    """Test NightFloatPostCallConstraint initialization."""

    def test_name(self):
        c = NightFloatPostCallConstraint()
        assert c.name == "NightFloatPostCall"

    def test_type(self):
        c = NightFloatPostCallConstraint()
        assert c.constraint_type == ConstraintType.ROTATION

    def test_priority(self):
        c = NightFloatPostCallConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_constants(self):
        assert NightFloatPostCallConstraint.NF_ABBREVIATION == "NF"
        assert NightFloatPostCallConstraint.PC_ABBREVIATION == "PC"


# ==================== _find_template_id Tests ====================


class TestFindTemplateId:
    """Test _find_template_id helper method."""

    def test_find_by_abbreviation(self):
        c = NightFloatPostCallConstraint()
        nf = _template(name="Night Float", abbreviation="NF")
        ctx = _context(templates=[nf])
        assert c._find_template_id(ctx, "NF") == nf.id

    def test_find_by_name_fallback(self):
        c = NightFloatPostCallConstraint()
        nf = _template(name="NF")  # No abbreviation
        ctx = _context(templates=[nf])
        assert c._find_template_id(ctx, "NF") == nf.id

    def test_case_insensitive(self):
        c = NightFloatPostCallConstraint()
        nf = _template(name="Night Float", abbreviation="nf")
        ctx = _context(templates=[nf])
        assert c._find_template_id(ctx, "NF") == nf.id

    def test_not_found(self):
        c = NightFloatPostCallConstraint()
        ctx = _context(templates=[_template(name="Other")])
        assert c._find_template_id(ctx, "NF") is None

    def test_empty_templates(self):
        c = NightFloatPostCallConstraint()
        ctx = _context(templates=[])
        assert c._find_template_id(ctx, "NF") is None

    def test_abbreviation_preferred_over_name(self):
        """Abbreviation match should find the correct template even with different name."""
        c = NightFloatPostCallConstraint()
        t1 = _template(name="Night Float Rotation", abbreviation="NF")
        t2 = _template(name="NF-Something")
        ctx = _context(templates=[t1, t2])
        # Should find t1 first (abbreviation match)
        assert c._find_template_id(ctx, "NF") == t1.id


# ==================== _group_blocks_by_date_time Tests ====================


class TestGroupBlocksByDateTime:
    """Test _group_blocks_by_date_time helper method."""

    def test_groups_correctly(self):
        c = NightFloatPostCallConstraint()
        b1 = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        b2 = _block(block_date=date(2025, 3, 3), time_of_day="PM")
        b3 = _block(block_date=date(2025, 3, 4), time_of_day="AM")
        ctx = _context(blocks=[b1, b2, b3])

        result = c._group_blocks_by_date_time(ctx)
        assert len(result[(date(2025, 3, 3), "AM")]) == 1
        assert len(result[(date(2025, 3, 3), "PM")]) == 1
        assert len(result[(date(2025, 3, 4), "AM")]) == 1

    def test_empty_blocks(self):
        c = NightFloatPostCallConstraint()
        ctx = _context(blocks=[])
        result = c._group_blocks_by_date_time(ctx)
        assert len(result) == 0

    def test_multiple_blocks_same_date_time(self):
        """Two blocks with same (date, time_of_day) go in same group."""
        c = NightFloatPostCallConstraint()
        b1 = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        b2 = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        ctx = _context(blocks=[b1, b2])

        result = c._group_blocks_by_date_time(ctx)
        assert len(result[(date(2025, 3, 3), "AM")]) == 2


# ==================== _get_block_half_transition_days Tests ====================


class TestGetBlockHalfTransitionDays:
    """Test _get_block_half_transition_days helper method."""

    def test_no_block_number_no_transitions(self):
        """Blocks without block_number/block_half -> no transitions detected."""
        c = NightFloatPostCallConstraint()
        b1 = _block(block_date=date(2025, 3, 3))  # No block_number
        ctx = _context(blocks=[b1])

        result = c._get_block_half_transition_days(ctx)
        assert len(result) == 0

    def test_single_block_half(self):
        """One block-half with a last day -> transition on next day."""
        c = NightFloatPostCallConstraint()
        # Block 7, half 1: days 1-14 (e.g. March 3-16)
        blocks = [
            _block(
                block_date=date(2025, 3, 3) + timedelta(days=i),
                time_of_day="AM",
                block_number=7,
                block_half=1,
            )
            for i in range(14)
        ]
        ctx = _context(blocks=blocks)

        result = c._get_block_half_transition_days(ctx)
        # Last day is March 16, transition is March 17
        assert date(2025, 3, 17) in result
        # The last-day blocks should be in the result
        last_day_blocks = result[date(2025, 3, 17)]
        assert len(last_day_blocks) == 1  # Only 1 block on March 16 (AM only)

    def test_two_block_halves(self):
        """Two block-halves produce two transition days."""
        c = NightFloatPostCallConstraint()
        half1_blocks = [
            _block(
                block_date=date(2025, 3, 3) + timedelta(days=i),
                time_of_day="AM",
                block_number=7,
                block_half=1,
            )
            for i in range(14)
        ]
        half2_blocks = [
            _block(
                block_date=date(2025, 3, 17) + timedelta(days=i),
                time_of_day="AM",
                block_number=7,
                block_half=2,
            )
            for i in range(14)
        ]
        ctx = _context(blocks=half1_blocks + half2_blocks)

        result = c._get_block_half_transition_days(ctx)
        # Half 1 last day: March 16, transition: March 17
        # Half 2 last day: March 30, transition: March 31
        assert date(2025, 3, 17) in result
        assert date(2025, 3, 31) in result

    def test_am_and_pm_on_last_day(self):
        """Both AM and PM blocks on last day appear in result."""
        c = NightFloatPostCallConstraint()
        last_day = date(2025, 3, 16)
        blocks = [
            _block(
                block_date=last_day,
                time_of_day="AM",
                block_number=7,
                block_half=1,
            ),
            _block(
                block_date=last_day,
                time_of_day="PM",
                block_number=7,
                block_half=1,
            ),
        ]
        ctx = _context(blocks=blocks)

        result = c._get_block_half_transition_days(ctx)
        transition = date(2025, 3, 17)
        assert transition in result
        assert len(result[transition]) == 2


# ==================== validate Tests ====================


class TestNightFloatPostCallValidate:
    """Test NightFloatPostCallConstraint.validate method."""

    def test_no_nf_or_pc_templates_satisfied(self):
        """No NF/PC templates -> can't validate -> satisfied."""
        c = NightFloatPostCallConstraint()
        ctx = _context(templates=[_template(name="Other")])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_no_assignments_satisfied(self):
        """No assignments with NF/PC templates defined -> satisfied."""
        c = NightFloatPostCallConstraint()
        nf = _template(name="NF")
        pc = _template(name="PC")
        ctx = _context(templates=[nf, pc])
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_nf_without_pc_on_transition_day_violations(self):
        """NF on last day of block-half, no PC next day -> 2 violations (AM+PM)."""
        c = NightFloatPostCallConstraint()
        res = _person(name="Dr. Night")
        nf = _template(name="NF")
        pc = _template(name="PC")

        # Block 7 half 1: March 3 only (single day for simplicity)
        nf_block = _block(
            block_date=date(2025, 3, 3),
            time_of_day="PM",
            block_number=7,
            block_half=1,
        )
        # Next day blocks (transition day)
        next_am = _block(block_date=date(2025, 3, 4), time_of_day="AM")
        next_pm = _block(block_date=date(2025, 3, 4), time_of_day="PM")

        ctx = _context(
            residents=[res],
            blocks=[nf_block, next_am, next_pm],
            templates=[nf, pc],
        )

        # Only NF assignment, no PC
        nf_a = _assignment(res.id, nf_block.id, rotation_template_id=nf.id)
        result = c.validate([nf_a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2
        assert all(v.severity == "CRITICAL" for v in result.violations)
        am_violation = [v for v in result.violations if "AM" in v.message]
        pm_violation = [v for v in result.violations if "PM" in v.message]
        assert len(am_violation) == 1
        assert len(pm_violation) == 1

    def test_nf_with_pc_both_halves_satisfied(self):
        """NF on last day with PC for both AM and PM -> satisfied."""
        c = NightFloatPostCallConstraint()
        res = _person(name="Dr. Night")
        nf = _template(name="NF")
        pc = _template(name="PC")

        nf_block = _block(
            block_date=date(2025, 3, 3),
            time_of_day="PM",
            block_number=7,
            block_half=1,
        )
        next_am = _block(block_date=date(2025, 3, 4), time_of_day="AM")
        next_pm = _block(block_date=date(2025, 3, 4), time_of_day="PM")

        ctx = _context(
            residents=[res],
            blocks=[nf_block, next_am, next_pm],
            templates=[nf, pc],
        )

        assignments = [
            _assignment(res.id, nf_block.id, rotation_template_id=nf.id),
            _assignment(res.id, next_am.id, rotation_template_id=pc.id),
            _assignment(res.id, next_pm.id, rotation_template_id=pc.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_nf_with_only_am_pc_one_violation(self):
        """NF with PC AM but no PC PM -> 1 violation for PM."""
        c = NightFloatPostCallConstraint()
        res = _person(name="Dr. Night")
        nf = _template(name="NF")
        pc = _template(name="PC")

        nf_block = _block(
            block_date=date(2025, 3, 3),
            time_of_day="PM",
            block_number=7,
            block_half=1,
        )
        next_am = _block(block_date=date(2025, 3, 4), time_of_day="AM")
        next_pm = _block(block_date=date(2025, 3, 4), time_of_day="PM")

        ctx = _context(
            residents=[res],
            blocks=[nf_block, next_am, next_pm],
            templates=[nf, pc],
        )

        assignments = [
            _assignment(res.id, nf_block.id, rotation_template_id=nf.id),
            _assignment(res.id, next_am.id, rotation_template_id=pc.id),
            # Missing PM PC
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "PM" in result.violations[0].message

    def test_non_nf_assignment_not_checked(self):
        """Non-NF assignment on transition day -> no violation."""
        c = NightFloatPostCallConstraint()
        res = _person(name="Dr. Day")
        nf = _template(name="NF")
        pc = _template(name="PC")
        clinic = _template(name="Clinic")

        clinic_block = _block(
            block_date=date(2025, 3, 3),
            time_of_day="AM",
            block_number=7,
            block_half=1,
        )

        ctx = _context(
            residents=[res],
            blocks=[clinic_block],
            templates=[nf, pc, clinic],
        )

        # Clinic assignment on transition-adjacent day (not NF)
        clinic_a = _assignment(res.id, clinic_block.id, rotation_template_id=clinic.id)
        result = c.validate([clinic_a], ctx)
        assert result.satisfied is True

    def test_nf_not_on_transition_day_no_violation(self):
        """NF assignment NOT on last day of block-half -> no violation."""
        c = NightFloatPostCallConstraint()
        res = _person(name="Dr. Night")
        nf = _template(name="NF")
        pc = _template(name="PC")

        # Block with two days in same half; NF on first day, not last
        day1 = _block(
            block_date=date(2025, 3, 3),
            time_of_day="PM",
            block_number=7,
            block_half=1,
        )
        day2 = _block(
            block_date=date(2025, 3, 4),
            time_of_day="PM",
            block_number=7,
            block_half=1,
        )

        ctx = _context(
            residents=[res],
            blocks=[day1, day2],
            templates=[nf, pc],
        )

        # NF on day1 (not the last day of half), no PC on day2
        nf_a = _assignment(res.id, day1.id, rotation_template_id=nf.id)
        result = c.validate([nf_a], ctx)
        # day2 is the last day (March 4), transition would be March 5
        # day1 (March 3) is NOT a transition boundary block
        assert result.satisfied is True

    def test_violation_details(self):
        """Violation details include nf_end_date and expected_pc_date."""
        c = NightFloatPostCallConstraint()
        res = _person(name="Dr. Night")
        nf = _template(name="NF")
        pc = _template(name="PC")

        nf_block = _block(
            block_date=date(2025, 3, 3),
            time_of_day="PM",
            block_number=7,
            block_half=1,
        )
        next_am = _block(block_date=date(2025, 3, 4), time_of_day="AM")
        next_pm = _block(block_date=date(2025, 3, 4), time_of_day="PM")

        ctx = _context(
            residents=[res],
            blocks=[nf_block, next_am, next_pm],
            templates=[nf, pc],
        )

        nf_a = _assignment(res.id, nf_block.id, rotation_template_id=nf.id)
        result = c.validate([nf_a], ctx)

        am_v = [v for v in result.violations if v.details["time_of_day"] == "AM"][0]
        assert am_v.details["nf_end_date"] == "2025-03-03"
        assert am_v.details["expected_pc_date"] == "2025-03-04"

    def test_unknown_resident_skipped(self):
        """Assignment with person_id not in residents -> skipped."""
        c = NightFloatPostCallConstraint()
        nf = _template(name="NF")
        pc = _template(name="PC")

        nf_block = _block(
            block_date=date(2025, 3, 3),
            time_of_day="PM",
            block_number=7,
            block_half=1,
        )

        ctx = _context(
            residents=[],
            blocks=[nf_block],
            templates=[nf, pc],
        )

        nf_a = _assignment(uuid4(), nf_block.id, rotation_template_id=nf.id)
        result = c.validate([nf_a], ctx)
        assert result.satisfied is True

    def test_unknown_block_skipped(self):
        """Assignment with block_id not in blocks -> skipped."""
        c = NightFloatPostCallConstraint()
        res = _person(name="Dr. Night")
        nf = _template(name="NF")
        pc = _template(name="PC")

        ctx = _context(
            residents=[res],
            blocks=[],
            templates=[nf, pc],
        )

        nf_a = _assignment(res.id, uuid4(), rotation_template_id=nf.id)
        result = c.validate([nf_a], ctx)
        assert result.satisfied is True
