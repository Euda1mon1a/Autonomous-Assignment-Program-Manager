"""Tests for ACGME compliance constraints (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.acgme import (
    AvailabilityConstraint,
    EightyHourRuleConstraint,
    OneInSevenRuleConstraint,
    SupervisionRatioConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Resident", pgy_level=1, **kwargs):
    ns = SimpleNamespace(id=pid or uuid4(), name=name, pgy_level=pgy_level)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _block(bid=None, block_date=None, time_of_day="AM"):
    return SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )


def _assignment(person_id, block_id):
    return SimpleNamespace(person_id=person_id, block_id=block_id)


def _context(residents=None, faculty=None, blocks=None, templates=None, **kwargs):
    ctx = SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
    )
    for k, v in kwargs.items():
        setattr(ctx, k, v)
    return ctx


# ==================== AvailabilityConstraint Init ====================


class TestAvailabilityInit:
    def test_name(self):
        c = AvailabilityConstraint()
        assert c.name == "Availability"

    def test_type(self):
        c = AvailabilityConstraint()
        assert c.constraint_type == ConstraintType.AVAILABILITY

    def test_priority(self):
        c = AvailabilityConstraint()
        assert c.priority == ConstraintPriority.CRITICAL


# ==================== AvailabilityConstraint Validate ====================


class TestAvailabilityValidate:
    def test_no_assignments_satisfied(self):
        c = AvailabilityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_available_assignment_ok(self):
        c = AvailabilityConstraint()
        r = _person(name="Dr. A")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[r], blocks=[b])
        ctx.availability = {r.id: {b.id: {"available": True}}}
        a = _assignment(r.id, b.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_unavailable_assignment_violation(self):
        c = AvailabilityConstraint()
        r = _person(name="Dr. Away")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[r], blocks=[b])
        ctx.availability = {r.id: {b.id: {"available": False}}}
        a = _assignment(r.id, b.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "Dr. Away" in result.violations[0].message
        assert "absence" in result.violations[0].message

    def test_no_availability_data_ok(self):
        """No availability data -> no restrictions -> ok."""
        c = AvailabilityConstraint()
        r = _person(name="Dr. A")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[r], blocks=[b])
        a = _assignment(r.id, b.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_faculty_unavailable_violation(self):
        c = AvailabilityConstraint()
        f = _person(name="Dr. Fac")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[f], blocks=[b])
        ctx.availability = {f.id: {b.id: {"available": False}}}
        a = _assignment(f.id, b.id)
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert "Dr. Fac" in result.violations[0].message

    def test_multiple_violations(self):
        c = AvailabilityConstraint()
        r1 = _person(name="Dr. A")
        r2 = _person(name="Dr. B")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[r1, r2], blocks=[b])
        ctx.availability = {
            r1.id: {b.id: {"available": False}},
            r2.id: {b.id: {"available": False}},
        }
        assignments = [_assignment(r1.id, b.id), _assignment(r2.id, b.id)]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2


# ==================== EightyHourRuleConstraint Init ====================


class TestEightyHourInit:
    def test_name(self):
        c = EightyHourRuleConstraint()
        assert c.name == "80HourRule"

    def test_type(self):
        c = EightyHourRuleConstraint()
        assert c.constraint_type == ConstraintType.DUTY_HOURS

    def test_priority(self):
        c = EightyHourRuleConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_constants(self):
        c = EightyHourRuleConstraint()
        assert c.HOURS_PER_BLOCK == 6
        assert c.MAX_WEEKLY_HOURS == 80
        assert c.ROLLING_WEEKS == 4
        assert c.ROLLING_DAYS == 28

    def test_max_blocks_per_window(self):
        c = EightyHourRuleConstraint()
        # (80 * 4) / 6 = 53.33 -> 53
        assert c.max_blocks_per_window == 53


# ==================== EightyHourRuleConstraint Rolling Average ====================


class TestEightyHourRollingAverage:
    def test_empty_dates(self):
        c = EightyHourRuleConstraint()
        avg = c._calculate_rolling_average({}, date(2025, 3, 3))
        assert avg == 0.0

    def test_single_day(self):
        c = EightyHourRuleConstraint()
        hours = {date(2025, 3, 3): 12}  # 2 blocks = 12 hours
        avg = c._calculate_rolling_average(hours, date(2025, 3, 3))
        # 12 / 4 = 3.0 hours/week
        assert avg == 3.0

    def test_full_week(self):
        c = EightyHourRuleConstraint()
        # 5 days * 12 hours = 60 hours in first week
        hours = {date(2025, 3, 3) + timedelta(days=i): 12 for i in range(5)}
        avg = c._calculate_rolling_average(hours, date(2025, 3, 3))
        # 60 / 4 = 15 hours/week average
        assert avg == 15.0

    def test_outside_window_excluded(self):
        c = EightyHourRuleConstraint()
        hours = {
            date(2025, 3, 3): 12,
            date(2025, 4, 5): 12,  # Outside 28-day window
        }
        avg = c._calculate_rolling_average(hours, date(2025, 3, 3))
        assert avg == 3.0  # Only first day counted


# ==================== EightyHourRuleConstraint Validate ====================


class TestEightyHourValidate:
    def test_no_assignments_satisfied(self):
        c = EightyHourRuleConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_light_schedule_ok(self):
        c = EightyHourRuleConstraint()
        r = _person(name="Dr. A")
        # 5 blocks over 28 days -> way under limit
        blocks = [
            _block(block_date=date(2025, 3, 3) + timedelta(days=i * 5))
            for i in range(5)
        ]
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_heavy_schedule_violation(self):
        """More than 53 blocks in a 28-day window -> violation."""
        c = EightyHourRuleConstraint()
        r = _person(name="Dr. Overwork")
        # 54 blocks over 28 days (AM + PM for 27 days)
        blocks = []
        for i in range(27):
            d = date(2025, 3, 3) + timedelta(days=i)
            blocks.append(_block(block_date=d, time_of_day="AM"))
            blocks.append(_block(block_date=d, time_of_day="PM"))
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        # 54 blocks * 6 hours = 324 hours / 4 weeks = 81 hours/week
        assert result.satisfied is False
        assert result.violations[0].severity == "CRITICAL"
        assert "80" in result.violations[0].message

    def test_no_resident_assignments_ok(self):
        """Assignments for non-resident people are ignored."""
        c = EightyHourRuleConstraint()
        r = _person(name="Dr. A")
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[r], blocks=[b])
        # Assignment for a different person (not in residents list)
        a = _assignment(uuid4(), b.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True


# ==================== OneInSevenRuleConstraint Init ====================


class TestOneInSevenInit:
    def test_name(self):
        c = OneInSevenRuleConstraint()
        assert c.name == "1in7Rule"

    def test_type(self):
        c = OneInSevenRuleConstraint()
        assert c.constraint_type == ConstraintType.CONSECUTIVE_DAYS

    def test_priority(self):
        c = OneInSevenRuleConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_max_consecutive(self):
        c = OneInSevenRuleConstraint()
        assert c.MAX_CONSECUTIVE_DAYS == 6


# ==================== OneInSevenRuleConstraint Validate ====================


class TestOneInSevenValidate:
    def test_no_assignments_satisfied(self):
        c = OneInSevenRuleConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_six_consecutive_ok(self):
        """6 consecutive days is the max allowed."""
        c = OneInSevenRuleConstraint()
        r = _person(name="Dr. A")
        blocks = [
            _block(block_date=date(2025, 3, 3) + timedelta(days=i)) for i in range(6)
        ]
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_seven_consecutive_violation(self):
        """7 consecutive days -> violation."""
        c = OneInSevenRuleConstraint()
        r = _person(name="Dr. Norest")
        blocks = [
            _block(block_date=date(2025, 3, 3) + timedelta(days=i)) for i in range(7)
        ]
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert "7 consecutive" in result.violations[0].message

    def test_gap_in_middle_ok(self):
        """3 days + gap + 3 days -> ok."""
        c = OneInSevenRuleConstraint()
        r = _person(name="Dr. A")
        blocks = []
        for i in range(3):
            blocks.append(_block(block_date=date(2025, 3, 3) + timedelta(days=i)))
        for i in range(3):
            blocks.append(_block(block_date=date(2025, 3, 7) + timedelta(days=i)))
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_few_days_ok(self):
        """Fewer than 7 unique dates -> can't violate."""
        c = OneInSevenRuleConstraint()
        r = _person(name="Dr. A")
        blocks = [
            _block(block_date=date(2025, 3, 3) + timedelta(days=i)) for i in range(5)
        ]
        ctx = _context(residents=[r], blocks=blocks)
        assignments = [_assignment(r.id, b.id) for b in blocks]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True


# ==================== SupervisionRatioConstraint Init ====================


class TestSupervisionInit:
    def test_name(self):
        c = SupervisionRatioConstraint()
        assert c.name == "SupervisionRatio"

    def test_type(self):
        c = SupervisionRatioConstraint()
        assert c.constraint_type == ConstraintType.SUPERVISION

    def test_priority(self):
        c = SupervisionRatioConstraint()
        assert c.priority == ConstraintPriority.CRITICAL

    def test_ratios(self):
        c = SupervisionRatioConstraint()
        assert c.PGY1_RATIO == 2
        assert c.OTHER_RATIO == 4


# ==================== SupervisionRatioConstraint calculate_required_faculty ====================


class TestCalculateRequiredFaculty:
    def test_no_residents(self):
        c = SupervisionRatioConstraint()
        assert c.calculate_required_faculty(0, 0) == 0

    def test_one_pgy1(self):
        c = SupervisionRatioConstraint()
        # 1 PGY-1: 2 units -> (2+3)//4 = 1
        assert c.calculate_required_faculty(1, 0) == 1

    def test_two_pgy1(self):
        c = SupervisionRatioConstraint()
        # 2 PGY-1: 4 units -> (4+3)//4 = 1
        assert c.calculate_required_faculty(2, 0) == 1

    def test_three_pgy1(self):
        c = SupervisionRatioConstraint()
        # 3 PGY-1: 6 units -> (6+3)//4 = 2
        assert c.calculate_required_faculty(3, 0) == 2

    def test_one_other(self):
        c = SupervisionRatioConstraint()
        # 1 PGY-2/3: 1 unit -> (1+3)//4 = 1
        assert c.calculate_required_faculty(0, 1) == 1

    def test_four_other(self):
        c = SupervisionRatioConstraint()
        # 4 PGY-2/3: 4 units -> (4+3)//4 = 1
        assert c.calculate_required_faculty(0, 4) == 1

    def test_five_other(self):
        c = SupervisionRatioConstraint()
        # 5 PGY-2/3: 5 units -> (5+3)//4 = 2
        assert c.calculate_required_faculty(0, 5) == 2

    def test_mixed(self):
        c = SupervisionRatioConstraint()
        # 1 PGY-1 + 1 PGY-2: 2 + 1 = 3 units -> (3+3)//4 = 1
        assert c.calculate_required_faculty(1, 1) == 1

    def test_mixed_larger(self):
        c = SupervisionRatioConstraint()
        # 2 PGY-1 + 4 PGY-2: 4 + 4 = 8 units -> (8+3)//4 = 2
        assert c.calculate_required_faculty(2, 4) == 2


# ==================== SupervisionRatioConstraint Validate ====================


class TestSupervisionValidate:
    def test_no_assignments_satisfied(self):
        c = SupervisionRatioConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_adequate_supervision_ok(self):
        c = SupervisionRatioConstraint()
        r = _person(name="Intern", pgy_level=1)
        f = _person(name="Dr. Fac", pgy_level=0)
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[r], faculty=[f], blocks=[b])
        assignments = [_assignment(r.id, b.id), _assignment(f.id, b.id)]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_insufficient_supervision_violation(self):
        """3 PGY-1 need 2 faculty but only 1 assigned."""
        c = SupervisionRatioConstraint()
        r1 = _person(name="Intern1", pgy_level=1)
        r2 = _person(name="Intern2", pgy_level=1)
        r3 = _person(name="Intern3", pgy_level=1)
        f = _person(name="Dr. Fac", pgy_level=0)
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=[r1, r2, r3], faculty=[f], blocks=[b])
        assignments = [
            _assignment(r1.id, b.id),
            _assignment(r2.id, b.id),
            _assignment(r3.id, b.id),
            _assignment(f.id, b.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert result.violations[0].severity == "CRITICAL"
        assert "2 faculty" in result.violations[0].message

    def test_no_residents_only_faculty_ok(self):
        c = SupervisionRatioConstraint()
        f = _person(name="Dr. Fac", pgy_level=0)
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(faculty=[f], blocks=[b])
        a = _assignment(f.id, b.id)
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_pgy2_needs_less_supervision(self):
        """4 PGY-2 residents need only 1 faculty."""
        c = SupervisionRatioConstraint()
        residents = [_person(name=f"R{i}", pgy_level=2) for i in range(4)]
        f = _person(name="Dr. Fac", pgy_level=0)
        b = _block(block_date=date(2025, 3, 3))
        ctx = _context(residents=residents, faculty=[f], blocks=[b])
        assignments = [_assignment(r.id, b.id) for r in residents] + [
            _assignment(f.id, b.id)
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is True

    def test_multiple_blocks_independent(self):
        """Each block checked independently."""
        c = SupervisionRatioConstraint()
        r = _person(name="Intern", pgy_level=1)
        f = _person(name="Dr. Fac", pgy_level=0)
        b1 = _block(block_date=date(2025, 3, 3), time_of_day="AM")
        b2 = _block(block_date=date(2025, 3, 3), time_of_day="PM")
        ctx = _context(residents=[r], faculty=[f], blocks=[b1, b2])
        # Faculty only on b1, resident on both
        assignments = [
            _assignment(r.id, b1.id),
            _assignment(f.id, b1.id),
            _assignment(r.id, b2.id),  # No faculty on b2
        ]
        result = c.validate(assignments, ctx)
        # b2 has 1 PGY-1 resident, needs 1 faculty but has 0
        assert result.satisfied is False
        assert len(result.violations) == 1
