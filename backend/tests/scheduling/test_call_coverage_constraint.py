"""Tests for call coverage constraints (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.call_coverage import (
    OVERNIGHT_CALL_DAYS,
    AdjunctCallExclusionConstraint,
    CallAvailabilityConstraint,
    OvernightCallCoverageConstraint,
    is_overnight_call_day,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", faculty_role=None):
    """Build a mock person with .id, .name, and optional .faculty_role."""
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    if faculty_role is not None:
        ns.faculty_role = faculty_role
    return ns


def _block(bid=None, block_date=None, time_of_day="PM"):
    """Build a mock block with .id, .date, .time_of_day."""
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),  # Monday
        time_of_day=time_of_day,
    )


def _assignment(person_id, block_id, call_type=None):
    """Build a mock assignment."""
    ns = SimpleNamespace(person_id=person_id, block_id=block_id)
    if call_type is not None:
        ns.call_type = call_type
    return ns


def _context(residents=None, blocks=None, faculty=None, templates=None):
    """Build a SchedulingContext."""
    ctx = SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )
    if not hasattr(ctx, "availability"):
        ctx.availability = {}
    return ctx


# ==================== Constants Tests ====================


class TestOvernightCallDaysConstant:
    """Test OVERNIGHT_CALL_DAYS constant."""

    def test_contains_expected_days(self):
        assert {0, 1, 2, 3, 6} == OVERNIGHT_CALL_DAYS

    def test_does_not_contain_friday(self):
        assert 4 not in OVERNIGHT_CALL_DAYS  # Friday

    def test_does_not_contain_saturday(self):
        assert 5 not in OVERNIGHT_CALL_DAYS  # Saturday


# ==================== is_overnight_call_day Tests ====================


class TestIsOvernightCallDay:
    """Test is_overnight_call_day helper function."""

    def test_sunday(self):
        assert is_overnight_call_day(date(2025, 3, 2)) is True

    def test_monday(self):
        assert is_overnight_call_day(date(2025, 3, 3)) is True

    def test_tuesday(self):
        assert is_overnight_call_day(date(2025, 3, 4)) is True

    def test_wednesday(self):
        assert is_overnight_call_day(date(2025, 3, 5)) is True

    def test_thursday(self):
        assert is_overnight_call_day(date(2025, 3, 6)) is True

    def test_friday(self):
        assert is_overnight_call_day(date(2025, 3, 7)) is False

    def test_saturday(self):
        assert is_overnight_call_day(date(2025, 3, 8)) is False


# ==================== OvernightCallCoverageConstraint Init ====================


class TestOvernightCallCoverageInit:
    """Test OvernightCallCoverageConstraint initialization."""

    def test_name(self):
        c = OvernightCallCoverageConstraint()
        assert c.name == "OvernightCallCoverage"

    def test_type(self):
        c = OvernightCallCoverageConstraint()
        assert c.constraint_type == ConstraintType.CALL

    def test_priority(self):
        c = OvernightCallCoverageConstraint()
        assert c.priority == ConstraintPriority.CRITICAL


# ==================== OvernightCallCoverageConstraint validate Tests ====================


class TestOvernightCallCoverageValidate:
    """Test OvernightCallCoverageConstraint.validate method."""

    def test_no_assignments_no_blocks(self):
        """No blocks -> no expected dates -> satisfied."""
        c = OvernightCallCoverageConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert len(result.violations) == 0

    def test_single_monday_covered(self):
        """One Monday block with one call -> satisfied."""
        c = OvernightCallCoverageConstraint()
        fac = _person(name="Dr. A")
        monday = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[monday])

        call_a = _assignment(fac.id, monday.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_monday_no_coverage_violation(self):
        """Monday block with no call -> violation."""
        c = OvernightCallCoverageConstraint()
        monday = _block(block_date=date(2025, 3, 3))
        ctx = _context(blocks=[monday])

        result = c.validate([], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "No overnight call coverage" in result.violations[0].message
        assert result.violations[0].severity == "CRITICAL"

    def test_friday_block_ignored(self):
        """Friday block -> not an overnight call day -> no violation."""
        c = OvernightCallCoverageConstraint()
        friday = _block(block_date=date(2025, 3, 7))
        ctx = _context(blocks=[friday])

        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_saturday_block_ignored(self):
        """Saturday block -> not an overnight call day -> no violation."""
        c = OvernightCallCoverageConstraint()
        saturday = _block(block_date=date(2025, 3, 8))
        ctx = _context(blocks=[saturday])

        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_double_coverage_violation(self):
        """Two faculty assigned to same night -> violation."""
        c = OvernightCallCoverageConstraint()
        fac_a = _person(name="Dr. A")
        fac_b = _person(name="Dr. B")
        monday = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac_a, fac_b], blocks=[monday])

        assignments = [
            _assignment(fac_a.id, monday.id, call_type="overnight"),
            _assignment(fac_b.id, monday.id, call_type="overnight"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "Multiple overnight call" in result.violations[0].message

    def test_multiple_dates_mixed(self):
        """Mon covered, Tue uncovered -> 1 violation."""
        c = OvernightCallCoverageConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac], blocks=[mon, tue])

        call_a = _assignment(fac.id, mon.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "2025-03-04" in result.violations[0].message

    def test_non_overnight_call_type_ignored(self):
        """Day call -> not overnight -> doesn't count as coverage."""
        c = OvernightCallCoverageConstraint()
        fac = _person(name="Dr. A")
        monday = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[monday])

        day_call = _assignment(fac.id, monday.id, call_type="day")
        result = c.validate([day_call], ctx)
        assert result.satisfied is False  # No overnight coverage

    def test_assignment_without_call_type_ignored(self):
        """Regular assignment without call_type doesn't count."""
        c = OvernightCallCoverageConstraint()
        fac = _person(name="Dr. A")
        monday = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac], blocks=[monday])

        regular = _assignment(fac.id, monday.id)
        result = c.validate([regular], ctx)
        assert result.satisfied is False

    def test_full_week_coverage(self):
        """Sun-Thu all covered -> satisfied."""
        c = OvernightCallCoverageConstraint()
        fac = _person(name="Dr. A")
        sun = _block(block_date=date(2025, 3, 2))
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))
        wed = _block(block_date=date(2025, 3, 5))
        thu = _block(block_date=date(2025, 3, 6))
        ctx = _context(faculty=[fac], blocks=[sun, mon, tue, wed, thu])

        assignments = [
            _assignment(fac.id, sun.id, call_type="overnight"),
            _assignment(fac.id, mon.id, call_type="overnight"),
            _assignment(fac.id, tue.id, call_type="overnight"),
            _assignment(fac.id, wed.id, call_type="overnight"),
            _assignment(fac.id, thu.id, call_type="overnight"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_duplicate_date_blocks_counted_once(self):
        """Two blocks on same date -> only one coverage check."""
        c = OvernightCallCoverageConstraint()
        fac = _person(name="Dr. A")
        mon_am = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        mon_pm = _block(block_date=date(2025, 3, 3), time_of_day="PM")
        ctx = _context(faculty=[fac], blocks=[mon_am, mon_pm])

        call_a = _assignment(fac.id, mon_am.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_violation_details_include_date(self):
        """Violation details contain the date string."""
        c = OvernightCallCoverageConstraint()
        monday = _block(block_date=date(2025, 3, 3))
        ctx = _context(blocks=[monday])

        result = c.validate([], ctx)
        assert result.violations[0].details["date"] == "2025-03-03"
        assert result.violations[0].details["expected"] == 1
        assert result.violations[0].details["actual"] == 0

    def test_double_coverage_details_include_person_ids(self):
        """Double coverage violation includes person IDs in details."""
        c = OvernightCallCoverageConstraint()
        fac_a = _person(name="Dr. A")
        fac_b = _person(name="Dr. B")
        monday = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[fac_a, fac_b], blocks=[monday])

        assignments = [
            _assignment(fac_a.id, monday.id, call_type="overnight"),
            _assignment(fac_b.id, monday.id, call_type="overnight"),
        ]
        result = c.validate(assignments, ctx)
        assert len(result.violations[0].details["person_ids"]) == 2


# ==================== AdjunctCallExclusionConstraint Init ====================


class TestAdjunctCallExclusionInit:
    """Test AdjunctCallExclusionConstraint initialization."""

    def test_name(self):
        c = AdjunctCallExclusionConstraint()
        assert c.name == "AdjunctCallExclusion"

    def test_type(self):
        c = AdjunctCallExclusionConstraint()
        assert c.constraint_type == ConstraintType.CALL

    def test_priority(self):
        c = AdjunctCallExclusionConstraint()
        assert c.priority == ConstraintPriority.HIGH


# ==================== AdjunctCallExclusionConstraint validate Tests ====================


class TestAdjunctCallExclusionValidate:
    """Test AdjunctCallExclusionConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = AdjunctCallExclusionConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_non_adjunct_call_ok(self):
        """Core faculty with call -> no violation."""
        c = AdjunctCallExclusionConstraint()
        fac = _person(name="Dr. Core", faculty_role="CORE")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])

        call_a = _assignment(fac.id, block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_adjunct_call_violation(self):
        """Adjunct with call -> violation."""
        c = AdjunctCallExclusionConstraint()
        fac = _person(name="Dr. Adj", faculty_role="ADJUNCT")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])

        call_a = _assignment(fac.id, block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "Adjunct" in result.violations[0].message
        assert result.violations[0].severity == "HIGH"

    def test_adjunct_case_insensitive(self):
        """adjunct (lowercase) -> still a violation."""
        c = AdjunctCallExclusionConstraint()
        fac = _person(name="Dr. Adj", faculty_role="adjunct")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])

        call_a = _assignment(fac.id, block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is False

    def test_adjunct_no_call_type_ok(self):
        """Adjunct with regular assignment (no call_type) -> ok."""
        c = AdjunctCallExclusionConstraint()
        fac = _person(name="Dr. Adj", faculty_role="ADJUNCT")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])

        regular = _assignment(fac.id, block.id)
        result = c.validate([regular], ctx)
        assert result.satisfied is True

    def test_no_faculty_role_ok(self):
        """Faculty without faculty_role attr -> no violation."""
        c = AdjunctCallExclusionConstraint()
        fac = _person(name="Dr. Unknown")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])

        call_a = _assignment(fac.id, block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_unknown_person_id_ignored(self):
        """Assignment with person_id not in faculty -> ignored."""
        c = AdjunctCallExclusionConstraint()
        block = _block()
        ctx = _context(faculty=[], blocks=[block])

        call_a = _assignment(uuid4(), block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_multiple_adjuncts_multiple_violations(self):
        """Two adjuncts with calls -> two violations."""
        c = AdjunctCallExclusionConstraint()
        adj1 = _person(name="Dr. Adj1", faculty_role="ADJUNCT")
        adj2 = _person(name="Dr. Adj2", faculty_role="ADJUNCT")
        block = _block()
        ctx = _context(faculty=[adj1, adj2], blocks=[block])

        assignments = [
            _assignment(adj1.id, block.id, call_type="overnight"),
            _assignment(adj2.id, block.id, call_type="overnight"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2


# ==================== CallAvailabilityConstraint Init ====================


class TestCallAvailabilityInit:
    """Test CallAvailabilityConstraint initialization."""

    def test_name(self):
        c = CallAvailabilityConstraint()
        assert c.name == "CallAvailability"

    def test_type(self):
        c = CallAvailabilityConstraint()
        assert c.constraint_type == ConstraintType.AVAILABILITY

    def test_priority(self):
        c = CallAvailabilityConstraint()
        assert c.priority == ConstraintPriority.CRITICAL


# ==================== CallAvailabilityConstraint validate Tests ====================


class TestCallAvailabilityValidate:
    """Test CallAvailabilityConstraint.validate method."""

    def test_no_assignments_satisfied(self):
        c = CallAvailabilityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_available_faculty_call_ok(self):
        """Faculty available -> no violation."""
        c = CallAvailabilityConstraint()
        fac = _person(name="Dr. A")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])
        ctx.availability = {fac.id: {block.id: {"available": True}}}

        call_a = _assignment(fac.id, block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_unavailable_faculty_call_violation(self):
        """Faculty unavailable -> violation."""
        c = CallAvailabilityConstraint()
        fac = _person(name="Dr. A")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])
        ctx.availability = {fac.id: {block.id: {"available": False}}}

        call_a = _assignment(fac.id, block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "unavailable" in result.violations[0].message
        assert result.violations[0].severity == "CRITICAL"

    def test_no_availability_data_defaults_available(self):
        """No availability entry -> defaults to available -> ok."""
        c = CallAvailabilityConstraint()
        fac = _person(name="Dr. A")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])
        ctx.availability = {}

        call_a = _assignment(fac.id, block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_regular_assignment_ignored(self):
        """Non-call assignment with unavailable faculty -> no violation."""
        c = CallAvailabilityConstraint()
        fac = _person(name="Dr. A")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])
        ctx.availability = {fac.id: {block.id: {"available": False}}}

        regular = _assignment(fac.id, block.id)
        result = c.validate([regular], ctx)
        assert result.satisfied is True

    def test_unknown_faculty_ignored(self):
        """Assignment for unknown faculty -> skipped."""
        c = CallAvailabilityConstraint()
        block = _block()
        ctx = _context(faculty=[], blocks=[block])

        call_a = _assignment(uuid4(), block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_unknown_block_ignored(self):
        """Assignment for unknown block -> skipped."""
        c = CallAvailabilityConstraint()
        fac = _person(name="Dr. A")
        ctx = _context(faculty=[fac], blocks=[])

        call_a = _assignment(fac.id, uuid4(), call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.satisfied is True

    def test_violation_details_include_replacement(self):
        """Violation details contain replacement reason."""
        c = CallAvailabilityConstraint()
        fac = _person(name="Dr. A")
        block = _block()
        ctx = _context(faculty=[fac], blocks=[block])
        ctx.availability = {
            fac.id: {block.id: {"available": False, "replacement": "leave"}}
        }

        call_a = _assignment(fac.id, block.id, call_type="overnight")
        result = c.validate([call_a], ctx)
        assert result.violations[0].details["reason"] == "leave"

    def test_multiple_unavailable_multiple_violations(self):
        """Two unavailable calls -> two violations."""
        c = CallAvailabilityConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac], blocks=[mon, tue])
        ctx.availability = {
            fac.id: {
                mon.id: {"available": False},
                tue.id: {"available": False},
            }
        }

        assignments = [
            _assignment(fac.id, mon.id, call_type="overnight"),
            _assignment(fac.id, tue.id, call_type="overnight"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2
