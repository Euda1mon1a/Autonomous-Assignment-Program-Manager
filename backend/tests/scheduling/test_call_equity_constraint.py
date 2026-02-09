"""Tests for call equity and preference constraints (pure logic, no DB required)."""

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.models.faculty_schedule_preference import (
    FacultyPreferenceDirection,
    FacultyPreferenceType,
)
from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.call_equity import (
    CallNightBeforeLeaveConstraint,
    CallSpacingConstraint,
    DeptChiefWednesdayPreferenceConstraint,
    FacultyCallPreferenceConstraint,
    HolidayCallEquityConstraint,
    SundayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    WeekdayCallEquityConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", **kwargs):
    ns = SimpleNamespace(id=pid or uuid4(), name=name)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _block(bid=None, block_date=None, time_of_day="AM", **kwargs):
    ns = SimpleNamespace(
        id=bid or uuid4(),
        date=block_date or date(2025, 3, 3),
        time_of_day=time_of_day,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _call_assignment(person_id, block_id, call_type="overnight", **kwargs):
    ns = SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        call_type=call_type,
    )
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _context(faculty=None, blocks=None, **kwargs):
    ctx = SchedulingContext(
        residents=[],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=[],
    )
    for k, v in kwargs.items():
        setattr(ctx, k, v)
    return ctx


# ==================== SundayCallEquityConstraint Tests ====================


class TestSundayCallEquityInit:
    def test_name(self):
        c = SundayCallEquityConstraint()
        assert c.name == "SundayCallEquity"

    def test_type(self):
        c = SundayCallEquityConstraint()
        assert c.constraint_type == ConstraintType.EQUITY

    def test_priority(self):
        c = SundayCallEquityConstraint()
        assert c.priority == ConstraintPriority.MEDIUM

    def test_default_weight(self):
        c = SundayCallEquityConstraint()
        assert c.weight == 10.0

    def test_custom_weight(self):
        c = SundayCallEquityConstraint(weight=20.0)
        assert c.weight == 20.0


class TestSundayCallEquityValidate:
    def test_no_assignments_satisfied(self):
        c = SundayCallEquityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_equal_sunday_counts_no_penalty(self):
        """Equal distribution -> zero variance -> zero penalty."""
        c = SundayCallEquityConstraint(weight=10.0)
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        sun1 = _block(block_date=date(2025, 3, 9))  # Sunday
        sun2 = _block(block_date=date(2025, 3, 16))  # Sunday
        ctx = _context(faculty=[fac1, fac2], blocks=[sun1, sun2])

        assignments = [
            _call_assignment(fac1.id, sun1.id),
            _call_assignment(fac2.id, sun2.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_unequal_sunday_counts_penalty(self):
        """Unequal distribution -> non-zero variance penalty."""
        c = SundayCallEquityConstraint(weight=10.0)
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        sun1 = _block(block_date=date(2025, 3, 9))
        sun2 = _block(block_date=date(2025, 3, 16))
        sun3 = _block(block_date=date(2025, 3, 23))
        ctx = _context(faculty=[fac1, fac2], blocks=[sun1, sun2, sun3])

        # fac1 gets 2 calls, fac2 gets 1 -> variance > 0
        assignments = [
            _call_assignment(fac1.id, sun1.id),
            _call_assignment(fac1.id, sun2.id),
            _call_assignment(fac2.id, sun3.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty > 0

    def test_imbalance_violation(self):
        """Range > 2 produces MEDIUM violation."""
        c = SundayCallEquityConstraint()
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")

        # 5 Sundays: fac1 gets 4, fac2 gets 1 -> range 4-1=3 > 2
        sundays = [
            _block(block_date=date(2025, 3, 9) + timedelta(weeks=i)) for i in range(5)
        ]
        ctx = _context(faculty=[fac1, fac2], blocks=sundays)
        assignments = [_call_assignment(fac1.id, s.id) for s in sundays[:4]] + [
            _call_assignment(fac2.id, sundays[4].id)
        ]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"

    def test_non_sunday_ignored(self):
        """Non-Sunday blocks are ignored."""
        c = SundayCallEquityConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))  # Monday
        ctx = _context(faculty=[fac], blocks=[mon])
        a = _call_assignment(fac.id, mon.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_non_overnight_ignored(self):
        """Non-overnight call types are ignored."""
        c = SundayCallEquityConstraint()
        fac = _person(name="Dr. A")
        sun = _block(block_date=date(2025, 3, 9))
        ctx = _context(faculty=[fac], blocks=[sun])
        a = _call_assignment(fac.id, sun.id, call_type="backup")
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_non_faculty_ignored(self):
        """Assignments for non-faculty persons are ignored."""
        c = SundayCallEquityConstraint()
        fac = _person(name="Dr. A")
        sun = _block(block_date=date(2025, 3, 9))
        ctx = _context(faculty=[fac], blocks=[sun])
        a = _call_assignment(uuid4(), sun.id)  # Unknown person
        result = c.validate([a], ctx)
        assert result.penalty == 0.0


# ==================== HolidayCallEquityConstraint Tests ====================


class TestHolidayCallEquityInit:
    def test_name(self):
        c = HolidayCallEquityConstraint()
        assert c.name == "HolidayCallEquity"

    def test_default_weight(self):
        c = HolidayCallEquityConstraint()
        assert c.weight == 7.0


class TestHolidayCallEquityValidate:
    def test_no_assignments_satisfied(self):
        c = HolidayCallEquityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_holiday_on_block(self):
        """Holiday call counted from block.is_holiday."""
        c = HolidayCallEquityConstraint()
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        h1 = _block(block_date=date(2025, 12, 25), is_holiday=True)
        h2 = _block(block_date=date(2026, 1, 1), is_holiday=True)
        h3 = _block(block_date=date(2025, 7, 4), is_holiday=True)
        ctx = _context(faculty=[fac1, fac2], blocks=[h1, h2, h3])

        # fac1 gets 2, fac2 gets 1 -> variance > 0
        assignments = [
            _call_assignment(fac1.id, h1.id),
            _call_assignment(fac1.id, h2.id),
            _call_assignment(fac2.id, h3.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty > 0

    def test_holiday_on_assignment(self):
        """Holiday call counted from assignment.is_holiday."""
        c = HolidayCallEquityConstraint()
        fac = _person(name="Dr. A")
        b = _block(block_date=date(2025, 7, 4))
        ctx = _context(faculty=[fac], blocks=[b])
        a = _call_assignment(fac.id, b.id, is_holiday=True)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0  # Single count, zero variance

    def test_non_holiday_ignored(self):
        """Non-holiday blocks produce no penalty."""
        c = HolidayCallEquityConstraint()
        fac = _person(name="Dr. A")
        b = _block(block_date=date(2025, 3, 3))  # Regular day
        ctx = _context(faculty=[fac], blocks=[b])
        a = _call_assignment(fac.id, b.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_holiday_imbalance_violation(self):
        """Range > 1 produces LOW violation."""
        c = HolidayCallEquityConstraint()
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        # fac1 gets 3, fac2 gets 1 -> range 3-1=2 > 1
        holidays = [
            _block(block_date=date(2025, 12, 25), is_holiday=True),
            _block(block_date=date(2026, 1, 1), is_holiday=True),
            _block(block_date=date(2025, 7, 4), is_holiday=True),
            _block(block_date=date(2025, 11, 27), is_holiday=True),
        ]
        ctx = _context(faculty=[fac1, fac2], blocks=holidays)
        assignments = [
            _call_assignment(fac1.id, holidays[0].id),
            _call_assignment(fac1.id, holidays[1].id),
            _call_assignment(fac1.id, holidays[2].id),
            _call_assignment(fac2.id, holidays[3].id),
        ]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 1
        assert result.violations[0].severity == "LOW"


# ==================== WeekdayCallEquityConstraint Tests ====================


class TestWeekdayCallEquityInit:
    def test_name(self):
        c = WeekdayCallEquityConstraint()
        assert c.name == "WeekdayCallEquity"

    def test_default_weight(self):
        c = WeekdayCallEquityConstraint()
        assert c.weight == 5.0


class TestWeekdayCallEquityValidate:
    def test_no_assignments_satisfied(self):
        c = WeekdayCallEquityConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_mon_thurs_counted(self):
        """Mon-Thurs overnight calls are counted."""
        c = WeekdayCallEquityConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))  # Monday
        tue = _block(block_date=date(2025, 3, 4))  # Tuesday
        ctx = _context(faculty=[fac], blocks=[mon, tue])
        assignments = [
            _call_assignment(fac.id, mon.id),
            _call_assignment(fac.id, tue.id),
        ]
        result = c.validate(assignments, ctx)
        # Single faculty, zero variance
        assert result.penalty == 0.0

    def test_friday_excluded(self):
        """Friday (weekday 4) is excluded from Mon-Thurs pool."""
        c = WeekdayCallEquityConstraint()
        fac = _person(name="Dr. A")
        fri = _block(block_date=date(2025, 3, 7))  # Friday
        ctx = _context(faculty=[fac], blocks=[fri])
        a = _call_assignment(fac.id, fri.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_sunday_excluded(self):
        """Sunday is excluded from weekday pool."""
        c = WeekdayCallEquityConstraint()
        fac = _person(name="Dr. A")
        sun = _block(block_date=date(2025, 3, 9))  # Sunday
        ctx = _context(faculty=[fac], blocks=[sun])
        a = _call_assignment(fac.id, sun.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_weekday_imbalance_violation(self):
        """Range > 3 produces MEDIUM violation."""
        c = WeekdayCallEquityConstraint()
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        # 6 Monday blocks: fac1 gets 5, fac2 gets 1 -> range 5-1=4 > 3
        blocks = [
            _block(block_date=date(2025, 3, 3) + timedelta(weeks=i)) for i in range(6)
        ]
        ctx = _context(faculty=[fac1, fac2], blocks=blocks)
        assignments = [_call_assignment(fac1.id, b.id) for b in blocks[:5]] + [
            _call_assignment(fac2.id, blocks[5].id)
        ]
        result = c.validate(assignments, ctx)
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"


# ==================== FacultyCallPreferenceConstraint Tests ====================


class TestFacultyCallPreferenceInit:
    def test_name(self):
        c = FacultyCallPreferenceConstraint()
        assert c.name == "FacultyCallPreference"

    def test_type(self):
        c = FacultyCallPreferenceConstraint()
        assert c.constraint_type == ConstraintType.PREFERENCE

    def test_default_weight(self):
        c = FacultyCallPreferenceConstraint()
        assert c.weight == 1.0


class TestFacultyCallPreferenceValidate:
    def test_no_preferences_satisfied(self):
        c = FacultyCallPreferenceConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_avoid_day_penalty(self):
        """Call on avoided day -> penalty."""
        c = FacultyCallPreferenceConstraint(weight=1.0)
        fac = _person(name="Dr. A")
        pref = SimpleNamespace(
            person_id=fac.id,
            is_active=True,
            preference_type=FacultyPreferenceType.CALL,
            direction=FacultyPreferenceDirection.AVOID,
            day_of_week=0,  # Monday
            weight=5,
        )
        ctx = _context(faculty=[fac], faculty_schedule_preferences=[pref])

        # Assignment on Monday with date attribute (validate uses assignment.date)
        a = SimpleNamespace(
            person_id=fac.id,
            block_id=uuid4(),
            call_type="overnight",
            date=date(2025, 3, 3),  # Monday
        )
        result = c.validate([a], ctx)
        assert result.penalty == 5.0  # weight=1.0 * pref_weight=5

    def test_prefer_day_no_penalty(self):
        """Call on preferred day -> no penalty (prefer ≠ avoid)."""
        c = FacultyCallPreferenceConstraint()
        fac = _person(name="Dr. A")
        pref = SimpleNamespace(
            person_id=fac.id,
            is_active=True,
            preference_type=FacultyPreferenceType.CALL,
            direction=FacultyPreferenceDirection.PREFER,
            day_of_week=0,
            weight=5,
        )
        ctx = _context(faculty=[fac], faculty_schedule_preferences=[pref])
        a = SimpleNamespace(
            person_id=fac.id,
            block_id=uuid4(),
            call_type="overnight",
            date=date(2025, 3, 3),
        )
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_backup_call_ignored(self):
        """Backup call type is ignored."""
        c = FacultyCallPreferenceConstraint()
        fac = _person(name="Dr. A")
        pref = SimpleNamespace(
            person_id=fac.id,
            is_active=True,
            preference_type=FacultyPreferenceType.CALL,
            direction=FacultyPreferenceDirection.AVOID,
            day_of_week=0,
            weight=5,
        )
        ctx = _context(faculty=[fac], faculty_schedule_preferences=[pref])
        a = SimpleNamespace(
            person_id=fac.id,
            block_id=uuid4(),
            call_type="backup",
            date=date(2025, 3, 3),
        )
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_different_day_no_penalty(self):
        """Call on a different day than avoided -> no penalty."""
        c = FacultyCallPreferenceConstraint()
        fac = _person(name="Dr. A")
        pref = SimpleNamespace(
            person_id=fac.id,
            is_active=True,
            preference_type=FacultyPreferenceType.CALL,
            direction=FacultyPreferenceDirection.AVOID,
            day_of_week=0,  # Monday
            weight=5,
        )
        ctx = _context(faculty=[fac], faculty_schedule_preferences=[pref])
        a = SimpleNamespace(
            person_id=fac.id,
            block_id=uuid4(),
            call_type="overnight",
            date=date(2025, 3, 4),  # Tuesday
        )
        result = c.validate([a], ctx)
        assert result.penalty == 0.0


# ==================== TuesdayCallPreferenceConstraint Tests ====================


class TestTuesdayCallPreferenceInit:
    def test_name(self):
        c = TuesdayCallPreferenceConstraint()
        assert c.name == "TuesdayCallPreference"

    def test_default_weight(self):
        c = TuesdayCallPreferenceConstraint()
        assert c.weight == 2.0


class TestTuesdayCallPreferenceValidate:
    def test_no_assignments_satisfied(self):
        c = TuesdayCallPreferenceConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_pd_on_tuesday_penalty(self):
        """PD with avoid_tuesday_call on Tuesday -> penalty."""
        c = TuesdayCallPreferenceConstraint(weight=2.0)
        pd = _person(
            name="Dr. PD",
            faculty_role="pd",
            avoid_tuesday_call=True,
        )
        tue = _block(block_date=date(2025, 3, 4))  # Tuesday
        ctx = _context(faculty=[pd], blocks=[tue])
        a = _call_assignment(pd.id, tue.id)
        result = c.validate([a], ctx)
        assert result.penalty == 2.0
        assert len(result.violations) == 1
        assert result.violations[0].severity == "LOW"

    def test_regular_faculty_tuesday_no_penalty(self):
        """Faculty without avoid_tuesday_call -> no penalty."""
        c = TuesdayCallPreferenceConstraint()
        fac = _person(name="Dr. Core", faculty_role="core")
        tue = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac], blocks=[tue])
        a = _call_assignment(fac.id, tue.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_pd_on_monday_no_penalty(self):
        """PD on non-Tuesday -> no penalty."""
        c = TuesdayCallPreferenceConstraint()
        pd = _person(name="Dr. PD", faculty_role="pd", avoid_tuesday_call=True)
        mon = _block(block_date=date(2025, 3, 3))  # Monday
        ctx = _context(faculty=[pd], blocks=[mon])
        a = _call_assignment(pd.id, mon.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_non_overnight_ignored(self):
        """Non-overnight call on Tuesday -> no penalty."""
        c = TuesdayCallPreferenceConstraint()
        pd = _person(name="Dr. PD", faculty_role="pd", avoid_tuesday_call=True)
        tue = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[pd], blocks=[tue])
        a = _call_assignment(pd.id, tue.id, call_type="backup")
        result = c.validate([a], ctx)
        assert result.penalty == 0.0


# ==================== CallNightBeforeLeaveConstraint Tests ====================


class TestCallNightBeforeLeaveInit:
    def test_name(self):
        c = CallNightBeforeLeaveConstraint()
        assert c.name == "CallNightBeforeLeave"

    def test_default_weight(self):
        c = CallNightBeforeLeaveConstraint()
        assert c.weight == 2.0


class TestCallNightBeforeLeaveValidate:
    def test_no_assignments_satisfied(self):
        c = CallNightBeforeLeaveConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_call_before_leave_penalty(self):
        """Overnight call before unavailable next day -> penalty."""
        c = CallNightBeforeLeaveConstraint(weight=2.0)
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac], blocks=[mon, tue])
        # Mark Tuesday as unavailable
        ctx.availability = {fac.id: {tue.id: {"available": False}}}
        ctx.blocks_by_date = {date(2025, 3, 3): [mon], date(2025, 3, 4): [tue]}

        a = _call_assignment(fac.id, mon.id)
        result = c.validate([a], ctx)
        assert result.penalty == 2.0
        assert len(result.violations) == 1
        assert "leave" in result.violations[0].message

    def test_call_before_available_no_penalty(self):
        """Overnight call before available next day -> no penalty."""
        c = CallNightBeforeLeaveConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac], blocks=[mon, tue])
        ctx.availability = {fac.id: {tue.id: {"available": True}}}
        ctx.blocks_by_date = {date(2025, 3, 3): [mon], date(2025, 3, 4): [tue]}

        a = _call_assignment(fac.id, mon.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_no_next_day_blocks_no_penalty(self):
        """No blocks on next day -> no penalty."""
        c = CallNightBeforeLeaveConstraint()
        fac = _person(name="Dr. A")
        fri = _block(block_date=date(2025, 3, 7))  # Friday, no Saturday blocks
        ctx = _context(faculty=[fac], blocks=[fri])
        ctx.blocks_by_date = {date(2025, 3, 7): [fri]}

        a = _call_assignment(fac.id, fri.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_non_overnight_ignored(self):
        """Non-overnight call before leave -> no penalty."""
        c = CallNightBeforeLeaveConstraint()
        fac = _person(name="Dr. A")
        mon = _block(block_date=date(2025, 3, 3))
        tue = _block(block_date=date(2025, 3, 4))
        ctx = _context(faculty=[fac], blocks=[mon, tue])
        ctx.availability = {fac.id: {tue.id: {"available": False}}}
        ctx.blocks_by_date = {date(2025, 3, 3): [mon], date(2025, 3, 4): [tue]}

        a = _call_assignment(fac.id, mon.id, call_type="backup")
        result = c.validate([a], ctx)
        assert result.penalty == 0.0


# ==================== CallSpacingConstraint Tests ====================


class TestCallSpacingInit:
    def test_name(self):
        c = CallSpacingConstraint()
        assert c.name == "CallSpacing"

    def test_type(self):
        c = CallSpacingConstraint()
        assert c.constraint_type == ConstraintType.EQUITY

    def test_default_weight(self):
        c = CallSpacingConstraint()
        assert c.weight == 8.0


class TestCallSpacingValidate:
    def test_no_assignments_satisfied(self):
        c = CallSpacingConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_back_to_back_weeks_penalty(self):
        """Call in consecutive weeks -> MEDIUM violation + penalty."""
        c = CallSpacingConstraint(weight=8.0)
        fac = _person(name="Dr. A")
        week1 = _block(block_date=date(2025, 3, 3))  # Week 10
        week2 = _block(block_date=date(2025, 3, 10))  # Week 11
        ctx = _context(faculty=[fac], blocks=[week1, week2])

        assignments = [
            _call_assignment(fac.id, week1.id),
            _call_assignment(fac.id, week2.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 8.0
        assert len(result.violations) == 1
        assert result.violations[0].severity == "MEDIUM"
        assert "back-to-back" in result.violations[0].message

    def test_spaced_weeks_no_penalty(self):
        """Call in non-consecutive weeks -> no penalty."""
        c = CallSpacingConstraint()
        fac = _person(name="Dr. A")
        week1 = _block(block_date=date(2025, 3, 3))  # Week 10
        week3 = _block(block_date=date(2025, 3, 17))  # Week 12 (skip week 11)
        ctx = _context(faculty=[fac], blocks=[week1, week3])

        assignments = [
            _call_assignment(fac.id, week1.id),
            _call_assignment(fac.id, week3.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_different_faculty_no_penalty(self):
        """Back-to-back weeks but different faculty -> no penalty."""
        c = CallSpacingConstraint()
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        week1 = _block(block_date=date(2025, 3, 3))
        week2 = _block(block_date=date(2025, 3, 10))
        ctx = _context(faculty=[fac1, fac2], blocks=[week1, week2])

        assignments = [
            _call_assignment(fac1.id, week1.id),
            _call_assignment(fac2.id, week2.id),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_non_overnight_ignored(self):
        """Non-overnight call type not counted for spacing."""
        c = CallSpacingConstraint()
        fac = _person(name="Dr. A")
        week1 = _block(block_date=date(2025, 3, 3))
        week2 = _block(block_date=date(2025, 3, 10))
        ctx = _context(faculty=[fac], blocks=[week1, week2])

        assignments = [
            _call_assignment(fac.id, week1.id, call_type="backup"),
            _call_assignment(fac.id, week2.id, call_type="backup"),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0


# ==================== DeptChiefWednesdayPreferenceConstraint Tests ====================


class TestDeptChiefWednesdayInit:
    def test_name(self):
        c = DeptChiefWednesdayPreferenceConstraint()
        assert c.name == "DeptChiefWednesdayPreference"

    def test_type(self):
        c = DeptChiefWednesdayPreferenceConstraint()
        assert c.constraint_type == ConstraintType.PREFERENCE

    def test_default_weight(self):
        c = DeptChiefWednesdayPreferenceConstraint()
        assert c.weight == 1.0


class TestDeptChiefWednesdayValidate:
    def test_no_assignments_satisfied(self):
        c = DeptChiefWednesdayPreferenceConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_dept_chief_wednesday_bonus(self):
        """Dept Chief on Wednesday -> negative penalty (bonus)."""
        c = DeptChiefWednesdayPreferenceConstraint(weight=1.0)
        chief = _person(
            name="Dr. Chief",
            faculty_role="dept_chief",
            prefer_wednesday_call=True,
        )
        wed = _block(block_date=date(2025, 3, 5))  # Wednesday
        ctx = _context(faculty=[chief], blocks=[wed])
        a = _call_assignment(chief.id, wed.id)
        result = c.validate([a], ctx)
        assert result.penalty == -1.0  # Bonus

    def test_non_chief_no_bonus(self):
        """Regular faculty on Wednesday -> no bonus."""
        c = DeptChiefWednesdayPreferenceConstraint()
        fac = _person(name="Dr. Core", faculty_role="core")
        wed = _block(block_date=date(2025, 3, 5))
        ctx = _context(faculty=[fac], blocks=[wed])
        a = _call_assignment(fac.id, wed.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_dept_chief_non_wednesday_no_bonus(self):
        """Dept Chief on non-Wednesday -> no bonus."""
        c = DeptChiefWednesdayPreferenceConstraint()
        chief = _person(
            name="Dr. Chief",
            faculty_role="dept_chief",
            prefer_wednesday_call=True,
        )
        mon = _block(block_date=date(2025, 3, 3))  # Monday
        ctx = _context(faculty=[chief], blocks=[mon])
        a = _call_assignment(chief.id, mon.id)
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_non_overnight_ignored(self):
        """Non-overnight call -> no bonus."""
        c = DeptChiefWednesdayPreferenceConstraint()
        chief = _person(
            name="Dr. Chief",
            faculty_role="dept_chief",
            prefer_wednesday_call=True,
        )
        wed = _block(block_date=date(2025, 3, 5))
        ctx = _context(faculty=[chief], blocks=[wed])
        a = _call_assignment(chief.id, wed.id, call_type="backup")
        result = c.validate([a], ctx)
        assert result.penalty == 0.0
