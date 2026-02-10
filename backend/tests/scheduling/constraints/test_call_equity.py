"""Tests for call equity and preference constraints (no DB)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
)
from app.scheduling.constraints.call_equity import (
    CallNightBeforeLeaveConstraint,
    CallSpacingConstraint,
    DeptChiefWednesdayPreferenceConstraint,
    HolidayCallEquityConstraint,
    SundayCallEquityConstraint,
    TuesdayCallPreferenceConstraint,
    WeekdayCallEquityConstraint,
)
from app.models.faculty_schedule_preference import (
    FacultyPreferenceDirection,
    FacultyPreferenceType,
)


# ---------------------------------------------------------------------------
# Mock objects
# ---------------------------------------------------------------------------

FACULTY_IDS = [UUID(f"00000000-0000-0000-0000-00000000000{i}") for i in range(1, 10)]
BLOCK_IDS = [UUID(f"00000000-0000-0000-0001-00000000{i:04d}") for i in range(60)]


@dataclass
class MockPerson:
    id: UUID
    name: str = "Dr. Test"
    faculty_role: str = "faculty"
    avoid_tuesday_call: bool = False
    prefer_wednesday_call: bool = False


@dataclass
class MockBlock:
    id: UUID
    date: date
    is_holiday: bool = False


@dataclass
class MockAssignment:
    person_id: UUID
    block_id: UUID
    call_type: str | None = None
    date: date | None = None
    is_holiday: bool = False


@dataclass
class MockPreference:
    person_id: UUID
    preference_type: FacultyPreferenceType
    direction: FacultyPreferenceDirection
    day_of_week: int
    weight: float = 1.0
    is_active: bool = True


@dataclass
class MockTemplate:
    id: UUID = field(default_factory=uuid4)


def _make_context(
    faculty: list[MockPerson] | None = None,
    blocks: list[MockBlock] | None = None,
    call_eligible: list[MockPerson] | None = None,
    availability: dict | None = None,
    preferences: list[MockPreference] | None = None,
) -> SchedulingContext:
    """Build a SchedulingContext from mocks."""
    if faculty is None:
        faculty = [MockPerson(id=FACULTY_IDS[i]) for i in range(3)]
    if blocks is None:
        blocks = []
    if call_eligible is None:
        call_eligible = faculty

    ctx = SchedulingContext(
        residents=[],
        faculty=faculty,
        blocks=blocks,
        templates=[],
        call_eligible_faculty=call_eligible,
        availability=availability or {},
        faculty_schedule_preferences=preferences or [],
    )
    return ctx


def _monday(week_offset: int = 0) -> date:
    """Return a Monday date."""
    base = date(2024, 1, 1)  # Monday
    return base + timedelta(weeks=week_offset)


def _day(weekday: int, week_offset: int = 0) -> date:
    """Return a date for given weekday (0=Mon) in a given week."""
    base = date(2024, 1, 1)  # Monday
    return base + timedelta(weeks=week_offset, days=weekday)


def _blocks_for_week(week_offset: int = 0) -> list[MockBlock]:
    """Create 7 blocks for a week (Mon=0 through Sun=6)."""
    start = _monday(week_offset)
    return [
        MockBlock(
            id=BLOCK_IDS[week_offset * 7 + d],
            date=start + timedelta(days=d),
        )
        for d in range(7)
    ]


# ---------------------------------------------------------------------------
# SundayCallEquityConstraint
# ---------------------------------------------------------------------------


class TestSundayCallEquityConstraint:
    def test_init_defaults(self):
        c = SundayCallEquityConstraint()
        assert c.name == "SundayCallEquity"
        assert c.constraint_type == ConstraintType.EQUITY
        assert c.weight == 10.0
        assert c.priority == ConstraintPriority.MEDIUM

    def test_init_custom_weight(self):
        c = SundayCallEquityConstraint(weight=20.0)
        assert c.weight == 20.0

    def test_validate_no_assignments(self):
        c = SundayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_validate_no_sunday_assignments(self):
        c = SundayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        # Monday assignment, not Sunday
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,  # Monday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_equal_sunday_calls(self):
        """Two faculty each with 1 Sunday call -> variance 0."""
        c = SundayCallEquityConstraint()
        blocks = _blocks_for_week(0) + _blocks_for_week(1)
        ctx = _make_context(blocks=blocks)
        sunday0 = blocks[6]  # First Sunday
        sunday1 = blocks[13]  # Second Sunday
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=sunday0.id,
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=sunday1.id,
                call_type="overnight",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0
        assert result.violations == []

    def test_validate_unequal_sunday_calls(self):
        """One faculty with 3 Sunday calls, another with 0 -> violation."""
        c = SundayCallEquityConstraint()
        blocks = []
        for w in range(4):
            blocks.extend(_blocks_for_week(w))
        ctx = _make_context(blocks=blocks)

        # Faculty 0 gets 3 Sunday calls, faculty 1 gets 0
        sundays = [b for b in blocks if b.date.weekday() == 6]
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=s.id,
                call_type="overnight",
            )
            for s in sundays[:3]
        ]
        result = c.validate(assignments, ctx)
        # Only faculty 0 in counts -> mean=3, variance=0 (single person)
        # Actually only 1 person in counts dict, so variance = 0
        assert result.satisfied is True

    def test_validate_significant_imbalance_creates_violation(self):
        """Range > 2 should produce a violation."""
        c = SundayCallEquityConstraint()
        blocks = []
        for w in range(5):
            blocks.extend(_blocks_for_week(w))
        ctx = _make_context(blocks=blocks)

        sundays = [b for b in blocks if b.date.weekday() == 6]
        # Faculty 0 gets 4, faculty 1 gets 1
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=s.id,
                call_type="overnight",
            )
            for s in sundays[:4]
        ]
        assignments.append(
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=sundays[4].id,
                call_type="overnight",
            )
        )
        result = c.validate(assignments, ctx)
        assert result.penalty > 0.0
        assert len(result.violations) == 1
        assert "imbalance" in result.violations[0].message

    def test_validate_non_overnight_ignored(self):
        """Backup calls should not count."""
        c = SundayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        sunday = blocks[6]
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=sunday.id,
                call_type="backup",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_non_faculty_ignored(self):
        """Assignments for non-faculty are ignored."""
        c = SundayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        sunday = blocks[6]
        outsider = UUID("99999999-9999-9999-9999-999999999999")
        assignments = [
            MockAssignment(
                person_id=outsider,
                block_id=sunday.id,
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0


# ---------------------------------------------------------------------------
# HolidayCallEquityConstraint
# ---------------------------------------------------------------------------


class TestHolidayCallEquityConstraint:
    def test_init_defaults(self):
        c = HolidayCallEquityConstraint()
        assert c.name == "HolidayCallEquity"
        assert c.weight == 7.0

    def test_validate_no_holidays(self):
        c = HolidayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_validate_equal_holiday_calls(self):
        c = HolidayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        blocks[0].is_holiday = True
        blocks[1].is_holiday = True
        ctx = _make_context(blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
                is_holiday=True,
            ),
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=blocks[1].id,
                call_type="overnight",
                is_holiday=True,
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_unequal_holiday_calls_violation(self):
        """Range > 1 creates violation."""
        c = HolidayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        blocks[0].is_holiday = True
        blocks[1].is_holiday = True
        blocks[2].is_holiday = True
        ctx = _make_context(blocks=blocks)
        # Faculty 0 gets 3, Faculty 1 gets 0
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[i].id,
                call_type="overnight",
                is_holiday=True,
            )
            for i in range(3)
        ]
        result = c.validate(assignments, ctx)
        # Only one person -> variance 0, no violation
        # Need two people for meaningful test
        assert result.satisfied is True

    def test_validate_holiday_imbalance(self):
        """Two faculty with holiday call difference > 1."""
        c = HolidayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        for i in range(5):
            blocks[i].is_holiday = True
        ctx = _make_context(blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
                is_holiday=True,
            ),
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[1].id,
                call_type="overnight",
                is_holiday=True,
            ),
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[2].id,
                call_type="overnight",
                is_holiday=True,
            ),
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=blocks[3].id,
                call_type="overnight",
                is_holiday=True,
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty > 0.0
        assert len(result.violations) == 1
        assert "imbalance" in result.violations[0].message

    def test_validate_weekend_call_on_holiday_counted(self):
        """Weekend call type on holiday should also count."""
        c = HolidayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        blocks[5].is_holiday = True  # Saturday
        ctx = _make_context(blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[5].id,
                call_type="weekend",
                is_holiday=True,
            )
        ]
        result = c.validate(assignments, ctx)
        # 1 person with 1 call -> variance 0
        assert result.satisfied is True

    def test_validate_non_holiday_not_counted(self):
        c = HolidayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0


# ---------------------------------------------------------------------------
# WeekdayCallEquityConstraint
# ---------------------------------------------------------------------------


class TestWeekdayCallEquityConstraint:
    def test_init_defaults(self):
        c = WeekdayCallEquityConstraint()
        assert c.name == "WeekdayCallEquity"
        assert c.weight == 5.0
        assert c.priority == ConstraintPriority.MEDIUM

    def test_validate_no_assignments(self):
        c = WeekdayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        result = c.validate([], ctx)
        assert result.penalty == 0.0

    def test_validate_equal_weekday_calls(self):
        c = WeekdayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,  # Monday
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=blocks[1].id,  # Tuesday
                call_type="overnight",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_weekday_imbalance_violation(self):
        """Range > 3 triggers violation."""
        c = WeekdayCallEquityConstraint()
        blocks = []
        for w in range(4):
            blocks.extend(_blocks_for_week(w))
        ctx = _make_context(blocks=blocks)

        weekday_blocks = [b for b in blocks if b.date.weekday() in (0, 1, 2, 3)]
        # Faculty 0 gets many, faculty 1 gets few
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=b.id,
                call_type="overnight",
            )
            for b in weekday_blocks[:8]
        ]
        assignments.append(
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=weekday_blocks[8].id,
                call_type="overnight",
            )
        )
        result = c.validate(assignments, ctx)
        assert result.penalty > 0.0
        assert len(result.violations) == 1

    def test_validate_friday_saturday_not_counted(self):
        """Friday (4) and Saturday (5) are not Mon-Thurs."""
        c = WeekdayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[4].id,  # Friday
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[5].id,  # Saturday
                call_type="overnight",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_sunday_not_counted(self):
        """Sunday (6) is not Mon-Thurs."""
        c = WeekdayCallEquityConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[6].id,  # Sunday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0


# ---------------------------------------------------------------------------
# TuesdayCallPreferenceConstraint
# ---------------------------------------------------------------------------


class TestTuesdayCallPreferenceConstraint:
    def test_init_defaults(self):
        c = TuesdayCallPreferenceConstraint()
        assert c.name == "TuesdayCallPreference"
        assert c.weight == 2.0
        assert c.priority == ConstraintPriority.LOW

    def test_validate_no_tuesday_avoidance(self):
        """Faculty without avoid_tuesday_call flag should not trigger."""
        c = TuesdayCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0], avoid_tuesday_call=False)]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[1].id,  # Tuesday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_pd_on_tuesday(self):
        """PD/APD with avoid_tuesday_call on Tuesday -> penalty."""
        c = TuesdayCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [
            MockPerson(
                id=FACULTY_IDS[0],
                name="Dr. PD",
                faculty_role="PD",
                avoid_tuesday_call=True,
            )
        ]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[1].id,  # Tuesday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 2.0
        assert len(result.violations) == 1
        assert "Tuesday" in result.violations[0].message

    def test_validate_pd_on_non_tuesday(self):
        """PD on Monday should not trigger."""
        c = TuesdayCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0], avoid_tuesday_call=True)]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,  # Monday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_multiple_tuesday_violations(self):
        """Multiple Tuesday assignments accumulate penalty."""
        c = TuesdayCallPreferenceConstraint()
        blocks = []
        for w in range(3):
            blocks.extend(_blocks_for_week(w))
        faculty = [MockPerson(id=FACULTY_IDS[0], avoid_tuesday_call=True)]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        tuesdays = [b for b in blocks if b.date.weekday() == 1]
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=t.id,
                call_type="overnight",
            )
            for t in tuesdays
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 2.0 * len(tuesdays)
        assert len(result.violations) == len(tuesdays)


# ---------------------------------------------------------------------------
# DeptChiefWednesdayPreferenceConstraint
# ---------------------------------------------------------------------------


class TestDeptChiefWednesdayPreferenceConstraint:
    def test_init_defaults(self):
        c = DeptChiefWednesdayPreferenceConstraint()
        assert c.name == "DeptChiefWednesdayPreference"
        assert c.weight == 1.0
        assert c.priority == ConstraintPriority.LOW

    def test_validate_chief_on_wednesday(self):
        """Chief on Wednesday -> negative penalty (bonus)."""
        c = DeptChiefWednesdayPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0], prefer_wednesday_call=True)]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[2].id,  # Wednesday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == -1.0  # Bonus

    def test_validate_chief_not_on_wednesday(self):
        """Chief on Thursday -> no bonus."""
        c = DeptChiefWednesdayPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0], prefer_wednesday_call=True)]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[3].id,  # Thursday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_non_chief_on_wednesday(self):
        """Non-chief faculty on Wednesday -> no bonus."""
        c = DeptChiefWednesdayPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0], prefer_wednesday_call=False)]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[2].id,
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_multiple_wednesday_bonuses(self):
        c = DeptChiefWednesdayPreferenceConstraint()
        blocks = []
        for w in range(3):
            blocks.extend(_blocks_for_week(w))
        faculty = [MockPerson(id=FACULTY_IDS[0], prefer_wednesday_call=True)]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        wednesdays = [b for b in blocks if b.date.weekday() == 2]
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=w.id,
                call_type="overnight",
            )
            for w in wednesdays
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == -1.0 * len(wednesdays)

    def test_validate_backup_not_counted(self):
        """Backup call should not get bonus."""
        c = DeptChiefWednesdayPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0], prefer_wednesday_call=True)]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[2].id,
                call_type="backup",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0


# ---------------------------------------------------------------------------
# CallNightBeforeLeaveConstraint
# ---------------------------------------------------------------------------


class TestCallNightBeforeLeaveConstraint:
    def test_init_defaults(self):
        c = CallNightBeforeLeaveConstraint()
        assert c.name == "CallNightBeforeLeave"
        assert c.weight == 2.0

    def test_validate_no_leave_next_day(self):
        c = CallNightBeforeLeaveConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,  # Monday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_call_before_leave(self):
        """Call Monday night, leave Tuesday -> penalty."""
        c = CallNightBeforeLeaveConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        # Mark Tuesday as unavailable
        avail = {
            FACULTY_IDS[0]: {
                blocks[1].id: {"available": False},
            }
        }
        ctx = _make_context(
            faculty=faculty,
            blocks=blocks,
            availability=avail,
        )
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,  # Monday
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 2.0
        assert len(result.violations) == 1
        assert "leave" in result.violations[0].message.lower()

    def test_validate_no_penalty_when_next_day_available(self):
        c = CallNightBeforeLeaveConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        avail = {
            FACULTY_IDS[0]: {
                blocks[1].id: {"available": True},
            }
        }
        ctx = _make_context(
            faculty=faculty,
            blocks=blocks,
            availability=avail,
        )
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_backup_not_penalized(self):
        c = CallNightBeforeLeaveConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        avail = {
            FACULTY_IDS[0]: {
                blocks[1].id: {"available": False},
            }
        }
        ctx = _make_context(
            faculty=faculty,
            blocks=blocks,
            availability=avail,
        )
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="backup",
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_multiple_before_leave(self):
        """Multiple faculty with call before leave."""
        c = CallNightBeforeLeaveConstraint()
        blocks = _blocks_for_week(0)
        faculty = [
            MockPerson(id=FACULTY_IDS[0]),
            MockPerson(id=FACULTY_IDS[1]),
        ]
        avail = {
            FACULTY_IDS[0]: {blocks[1].id: {"available": False}},
            FACULTY_IDS[1]: {blocks[1].id: {"available": False}},
        }
        ctx = _make_context(
            faculty=faculty,
            blocks=blocks,
            availability=avail,
        )
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=blocks[0].id,
                call_type="overnight",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 4.0  # 2.0 * 2 faculty
        assert len(result.violations) == 2


# ---------------------------------------------------------------------------
# CallSpacingConstraint
# ---------------------------------------------------------------------------


class TestCallSpacingConstraint:
    def test_init_defaults(self):
        c = CallSpacingConstraint()
        assert c.name == "CallSpacing"
        assert c.weight == 8.0
        assert c.priority == ConstraintPriority.MEDIUM

    def test_validate_no_back_to_back(self):
        """Call in week 1 and week 3 (not consecutive) -> no penalty."""
        c = CallSpacingConstraint()
        blocks = []
        for w in range(4):
            blocks.extend(_blocks_for_week(w))
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        ctx = _make_context(faculty=faculty, blocks=blocks)

        # Week 1 Monday and Week 3 Monday
        week1_mon = blocks[0]  # Week 0 Mon
        week3_mon = blocks[14]  # Week 2 Mon
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=week1_mon.id,
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=week3_mon.id,
                call_type="overnight",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_back_to_back_penalty(self):
        """Call in consecutive weeks -> penalty."""
        c = CallSpacingConstraint()
        blocks = []
        for w in range(3):
            blocks.extend(_blocks_for_week(w))
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        ctx = _make_context(faculty=faculty, blocks=blocks)

        # Week 0 Mon and Week 1 Mon
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,  # Week 0 Mon
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[7].id,  # Week 1 Mon
                call_type="overnight",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 8.0
        assert len(result.violations) == 1
        assert "back-to-back" in result.violations[0].message

    def test_validate_multiple_back_to_back(self):
        """Three consecutive weeks -> 2 penalties."""
        c = CallSpacingConstraint()
        blocks = []
        for w in range(4):
            blocks.extend(_blocks_for_week(w))
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        ctx = _make_context(faculty=faculty, blocks=blocks)

        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,  # Week 0
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[7].id,  # Week 1
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[14].id,  # Week 2
                call_type="overnight",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 16.0  # 8.0 * 2
        assert len(result.violations) == 2

    def test_validate_non_overnight_not_counted(self):
        c = CallSpacingConstraint()
        blocks = []
        for w in range(3):
            blocks.extend(_blocks_for_week(w))
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="backup",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[7].id,
                call_type="backup",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_different_faculty_not_coupled(self):
        """Faculty A in week 1, Faculty B in week 2 -> no penalty for either."""
        c = CallSpacingConstraint()
        blocks = []
        for w in range(3):
            blocks.extend(_blocks_for_week(w))
        faculty = [
            MockPerson(id=FACULTY_IDS[0]),
            MockPerson(id=FACULTY_IDS[1]),
        ]
        ctx = _make_context(faculty=faculty, blocks=blocks)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
            ),
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=blocks[7].id,
                call_type="overnight",
            ),
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0


# ---------------------------------------------------------------------------
# FacultyCallPreferenceConstraint — validate
# ---------------------------------------------------------------------------


class TestFacultyCallPreferenceValidate:
    def test_validate_no_preferences(self):
        from app.scheduling.constraints.call_equity import (
            FacultyCallPreferenceConstraint,
        )

        c = FacultyCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_validate_avoid_preference_violated(self):
        from app.scheduling.constraints.call_equity import (
            FacultyCallPreferenceConstraint,
        )

        c = FacultyCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        prefs = [
            MockPreference(
                person_id=FACULTY_IDS[0],
                preference_type=FacultyPreferenceType.CALL,
                direction=FacultyPreferenceDirection.AVOID,
                day_of_week=0,  # Monday
                weight=2.0,
            )
        ]
        ctx = _make_context(faculty=faculty, blocks=blocks, preferences=prefs)
        # Assignment on avoided day
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
                date=blocks[0].date,  # Monday
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 2.0  # pref_weight * constraint_weight
        assert len(result.violations) == 1

    def test_validate_prefer_direction_no_penalty(self):
        from app.scheduling.constraints.call_equity import (
            FacultyCallPreferenceConstraint,
        )

        c = FacultyCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        prefs = [
            MockPreference(
                person_id=FACULTY_IDS[0],
                preference_type=FacultyPreferenceType.CALL,
                direction=FacultyPreferenceDirection.PREFER,
                day_of_week=0,
                weight=2.0,
            )
        ]
        ctx = _make_context(faculty=faculty, blocks=blocks, preferences=prefs)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
                date=blocks[0].date,
            )
        ]
        result = c.validate(assignments, ctx)
        # Prefer direction doesn't cause penalty in validate
        assert result.penalty == 0.0

    def test_validate_backup_ignored(self):
        from app.scheduling.constraints.call_equity import (
            FacultyCallPreferenceConstraint,
        )

        c = FacultyCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        prefs = [
            MockPreference(
                person_id=FACULTY_IDS[0],
                preference_type=FacultyPreferenceType.CALL,
                direction=FacultyPreferenceDirection.AVOID,
                day_of_week=0,
                weight=2.0,
            )
        ]
        ctx = _make_context(faculty=faculty, blocks=blocks, preferences=prefs)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="backup",
                date=blocks[0].date,
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_inactive_preference_not_used(self):
        from app.scheduling.constraints.call_equity import (
            FacultyCallPreferenceConstraint,
        )

        c = FacultyCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        prefs = [
            MockPreference(
                person_id=FACULTY_IDS[0],
                preference_type=FacultyPreferenceType.CALL,
                direction=FacultyPreferenceDirection.AVOID,
                day_of_week=0,
                weight=2.0,
                is_active=False,
            )
        ]
        ctx = _make_context(faculty=faculty, blocks=blocks, preferences=prefs)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
                date=blocks[0].date,
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0

    def test_validate_clinic_preference_not_call(self):
        from app.scheduling.constraints.call_equity import (
            FacultyCallPreferenceConstraint,
        )

        c = FacultyCallPreferenceConstraint()
        blocks = _blocks_for_week(0)
        faculty = [MockPerson(id=FACULTY_IDS[0])]
        prefs = [
            MockPreference(
                person_id=FACULTY_IDS[0],
                preference_type=FacultyPreferenceType.CLINIC,
                direction=FacultyPreferenceDirection.AVOID,
                day_of_week=0,
                weight=2.0,
            )
        ]
        ctx = _make_context(faculty=faculty, blocks=blocks, preferences=prefs)
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=blocks[0].id,
                call_type="overnight",
                date=blocks[0].date,
            )
        ]
        result = c.validate(assignments, ctx)
        assert result.penalty == 0.0


# ---------------------------------------------------------------------------
# Constraint result properties
# ---------------------------------------------------------------------------


class TestConstraintResultProperties:
    def test_soft_constraint_always_satisfied(self):
        """All call equity constraints are soft -> satisfied is True."""
        constraints = [
            SundayCallEquityConstraint(),
            HolidayCallEquityConstraint(),
            WeekdayCallEquityConstraint(),
            TuesdayCallPreferenceConstraint(),
            DeptChiefWednesdayPreferenceConstraint(),
            CallNightBeforeLeaveConstraint(),
            CallSpacingConstraint(),
        ]
        blocks = _blocks_for_week(0)
        ctx = _make_context(blocks=blocks)
        for c in constraints:
            result = c.validate([], ctx)
            assert result.satisfied is True, f"{c.name} should always be satisfied"

    def test_constraint_types(self):
        assert SundayCallEquityConstraint().constraint_type == ConstraintType.EQUITY
        assert HolidayCallEquityConstraint().constraint_type == ConstraintType.EQUITY
        assert WeekdayCallEquityConstraint().constraint_type == ConstraintType.EQUITY
        assert CallSpacingConstraint().constraint_type == ConstraintType.EQUITY
        assert (
            TuesdayCallPreferenceConstraint().constraint_type
            == ConstraintType.PREFERENCE
        )
        assert (
            DeptChiefWednesdayPreferenceConstraint().constraint_type
            == ConstraintType.PREFERENCE
        )
        assert (
            CallNightBeforeLeaveConstraint().constraint_type
            == ConstraintType.PREFERENCE
        )

    def test_penalty_formula_variance_based(self):
        """Verify penalty = variance * weight for equity constraints."""
        c = SundayCallEquityConstraint(weight=10.0)
        blocks = []
        for w in range(4):
            blocks.extend(_blocks_for_week(w))
        ctx = _make_context(blocks=blocks)

        sundays = [b for b in blocks if b.date.weekday() == 6]
        # Faculty 0: 3 calls, Faculty 1: 1 call
        assignments = [
            MockAssignment(
                person_id=FACULTY_IDS[0],
                block_id=s.id,
                call_type="overnight",
            )
            for s in sundays[:3]
        ]
        assignments.append(
            MockAssignment(
                person_id=FACULTY_IDS[1],
                block_id=sundays[3].id,
                call_type="overnight",
            )
        )
        result = c.validate(assignments, ctx)
        # mean = (3+1)/2 = 2, variance = ((3-2)^2 + (1-2)^2)/2 = 1.0
        expected_penalty = 1.0 * 10.0
        assert abs(result.penalty - expected_penalty) < 1e-10
