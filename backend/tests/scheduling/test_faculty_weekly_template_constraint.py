"""Tests for faculty weekly template constraints (pure logic, no DB required)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintType,
    SchedulingContext,
)
from app.scheduling.constraints.faculty_weekly_template import (
    FacultyWeeklyTemplateConstraint,
)


# ==================== Helpers ====================


def _person(pid=None, name="Faculty", **kwargs):
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


def _activity(aid=None, name="Activity"):
    """Build a mock activity."""
    return SimpleNamespace(id=aid or uuid4(), name=name)


def _assignment(person_id, block_id, activity_id=None, time_of_day="AM"):
    """Build a mock faculty assignment with activity and time_of_day."""
    return SimpleNamespace(
        person_id=person_id,
        block_id=block_id,
        activity_id=activity_id,
        time_of_day=time_of_day,
    )


def _context(
    residents=None,
    blocks=None,
    faculty=None,
    templates=None,
    activities=None,
    start_date=None,
):
    """Build a SchedulingContext with optional activities."""
    ctx = SchedulingContext(
        residents=residents or [],
        faculty=faculty or [],
        blocks=blocks or [],
        templates=templates or [],
        activities=activities or [],
    )
    if start_date is not None:
        ctx.start_date = start_date
    return ctx


# ==================== Init Tests ====================


class TestFacultyWeeklyTemplateInit:
    """Test FacultyWeeklyTemplateConstraint initialization."""

    def test_name(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c.name == "FacultyWeeklyTemplate"

    def test_type(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c.constraint_type == ConstraintType.PREFERENCE

    def test_priority(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c.priority == ConstraintPriority.HIGH

    def test_default_weight(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c.weight == 10.0

    def test_custom_weight(self):
        c = FacultyWeeklyTemplateConstraint(weight=25.0)
        assert c.weight == 25.0

    def test_default_templates_empty(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c._templates == {}

    def test_default_overrides_empty(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c._overrides == {}

    def test_custom_templates(self):
        pid = uuid4()
        slots = [{"day_of_week": 1, "time_of_day": "AM", "activity_id": uuid4()}]
        c = FacultyWeeklyTemplateConstraint(templates={pid: slots})
        assert c._templates[pid] == slots


# ==================== _get_week_start Tests ====================


class TestGetWeekStart:
    """Test _get_week_start returns Monday of the week."""

    def test_monday_returns_same(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c._get_week_start(date(2025, 3, 3)) == date(2025, 3, 3)

    def test_wednesday_returns_monday(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c._get_week_start(date(2025, 3, 5)) == date(2025, 3, 3)

    def test_sunday_returns_monday(self):
        c = FacultyWeeklyTemplateConstraint()
        # Sunday 3/9 -> Monday 3/3
        assert c._get_week_start(date(2025, 3, 9)) == date(2025, 3, 3)


# ==================== _get_week_number Tests ====================


class TestGetWeekNumber:
    """Test _get_week_number (1-4 cycling within block rotation)."""

    def test_none_start_returns_one(self):
        c = FacultyWeeklyTemplateConstraint()
        assert c._get_week_number(date(2025, 3, 10), None) == 1

    def test_same_week_as_start(self):
        c = FacultyWeeklyTemplateConstraint()
        # 0 days diff -> week 1
        assert c._get_week_number(date(2025, 3, 3), date(2025, 3, 3)) == 1

    def test_second_week(self):
        c = FacultyWeeklyTemplateConstraint()
        # 7 days -> week 2
        assert c._get_week_number(date(2025, 3, 10), date(2025, 3, 3)) == 2

    def test_third_week(self):
        c = FacultyWeeklyTemplateConstraint()
        # 14 days -> week 3
        assert c._get_week_number(date(2025, 3, 17), date(2025, 3, 3)) == 3

    def test_fourth_week(self):
        c = FacultyWeeklyTemplateConstraint()
        # 21 days -> week 4
        assert c._get_week_number(date(2025, 3, 24), date(2025, 3, 3)) == 4

    def test_fifth_week_cycles_to_one(self):
        c = FacultyWeeklyTemplateConstraint()
        # 28 days -> (28//7) % 4 + 1 = 4 % 4 + 1 = 1
        assert c._get_week_number(date(2025, 3, 31), date(2025, 3, 3)) == 1


# ==================== DOW Convention Tests ====================
# _python_weekday_to_pattern was REMOVED — templates use Python weekday directly.
# See docs/architecture/DOW_CONVENTION_BUG.md and
# tests/scheduling/constraints/test_faculty_weekly_template_dow.py for full coverage.


# ==================== _get_effective_slot Tests ====================


class TestGetEffectiveSlot:
    """Test _get_effective_slot with resolution order."""

    def test_no_templates_returns_none(self):
        c = FacultyWeeklyTemplateConstraint()
        result = c._get_effective_slot(uuid4(), date(2025, 3, 3), 1, "AM", 1)
        assert result is None

    def test_override_takes_precedence(self):
        """Week-specific override beats default template."""
        pid = uuid4()
        template_slot = {
            "day_of_week": 1,
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": uuid4(),
            "is_locked": False,
        }
        override_slot = {
            "day_of_week": 1,
            "time_of_day": "AM",
            "activity_id": uuid4(),
            "is_locked": True,
        }
        # Monday 2025-03-03 -> week_start = 2025-03-03
        c = FacultyWeeklyTemplateConstraint(
            templates={pid: [template_slot]},
            overrides={pid: {date(2025, 3, 3): [override_slot]}},
        )
        result = c._get_effective_slot(pid, date(2025, 3, 3), 1, "AM", 1)
        assert result == override_slot

    def test_week_specific_template_beats_default(self):
        """Week-specific template beats default template."""
        pid = uuid4()
        default_slot = {
            "day_of_week": 1,
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": uuid4(),
        }
        week2_slot = {
            "day_of_week": 1,
            "time_of_day": "AM",
            "week_number": 2,
            "activity_id": uuid4(),
        }
        c = FacultyWeeklyTemplateConstraint(templates={pid: [default_slot, week2_slot]})
        result = c._get_effective_slot(pid, date(2025, 3, 10), 1, "AM", 2)
        assert result == week2_slot

    def test_default_template_used_when_no_specific(self):
        """Default template (week_number=None) used when no week-specific."""
        pid = uuid4()
        default_slot = {
            "day_of_week": 1,
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": uuid4(),
        }
        c = FacultyWeeklyTemplateConstraint(templates={pid: [default_slot]})
        result = c._get_effective_slot(pid, date(2025, 3, 3), 1, "AM", 1)
        assert result == default_slot

    def test_wrong_day_of_week_not_matched(self):
        """Template with different day_of_week isn't returned."""
        pid = uuid4()
        slot = {
            "day_of_week": 2,  # Tuesday
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": uuid4(),
        }
        c = FacultyWeeklyTemplateConstraint(templates={pid: [slot]})
        # Ask for Monday (day_of_week=1)
        result = c._get_effective_slot(pid, date(2025, 3, 3), 1, "AM", 1)
        assert result is None

    def test_wrong_time_of_day_not_matched(self):
        """Template with different time_of_day isn't returned."""
        pid = uuid4()
        slot = {
            "day_of_week": 1,
            "time_of_day": "PM",
            "week_number": None,
            "activity_id": uuid4(),
        }
        c = FacultyWeeklyTemplateConstraint(templates={pid: [slot]})
        result = c._get_effective_slot(pid, date(2025, 3, 3), 1, "AM", 1)
        assert result is None

    def test_caching(self):
        """Second call uses cache."""
        pid = uuid4()
        slot = {
            "day_of_week": 1,
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": uuid4(),
        }
        c = FacultyWeeklyTemplateConstraint(templates={pid: [slot]})
        # First call
        result1 = c._get_effective_slot(pid, date(2025, 3, 3), 1, "AM", 1)
        # Second call (cached)
        result2 = c._get_effective_slot(pid, date(2025, 3, 3), 1, "AM", 1)
        assert result1 is result2


# ==================== clear_cache Tests ====================


class TestClearCache:
    """Test clear_cache method."""

    def test_clears_effective_cache(self):
        pid = uuid4()
        slot = {
            "day_of_week": 1,
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": uuid4(),
        }
        c = FacultyWeeklyTemplateConstraint(templates={pid: [slot]})
        c._get_effective_slot(pid, date(2025, 3, 3), 1, "AM", 1)
        assert len(c._effective_cache) > 0
        c.clear_cache()
        assert len(c._effective_cache) == 0


# ==================== validate Tests ====================


class TestFacultyWeeklyTemplateValidate:
    """Test FacultyWeeklyTemplateConstraint.validate method."""

    def test_no_templates_satisfied(self):
        c = FacultyWeeklyTemplateConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_locked_slot_correct_activity_satisfied(self):
        """Locked slot with correct activity -> no violation."""
        fac = _person(name="Dr. PD")
        act = _activity(name="GME")
        mon = _block(block_date=date(2025, 3, 3))

        # day_of_week=0 (Monday) in Python weekday convention
        slot = {
            "day_of_week": 0,
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": act.id,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]})
        ctx = _context(faculty=[fac], blocks=[mon], activities=[act])

        a = _assignment(fac.id, mon.id, activity_id=act.id, time_of_day="AM")
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_locked_slot_wrong_activity_violation(self):
        """Locked slot assigned wrong activity -> CRITICAL violation."""
        fac = _person(name="Dr. PD")
        gme = _activity(name="GME")
        clinic = _activity(name="Clinic")
        mon = _block(block_date=date(2025, 3, 3))

        slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": gme.id,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]})
        ctx = _context(faculty=[fac], blocks=[mon], activities=[gme, clinic])

        # Assigned clinic instead of GME
        a = _assignment(fac.id, mon.id, activity_id=clinic.id, time_of_day="AM")
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1
        assert result.violations[0].severity == "CRITICAL"
        assert "locked" in result.violations[0].message

    def test_locked_slot_missing_assignment_violation(self):
        """Locked slot with no assignment -> CRITICAL violation."""
        fac = _person(name="Dr. PD")
        gme = _activity(name="GME")
        mon = _block(block_date=date(2025, 3, 3))

        slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": gme.id,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]})
        ctx = _context(faculty=[fac], blocks=[mon], activities=[gme])

        # No assignment at all for this slot
        result = c.validate([], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1

    def test_locked_empty_slot_with_assignment_violation(self):
        """Locked empty slot (activity_id=None) but something assigned -> violation."""
        fac = _person(name="Dr. PD")
        clinic = _activity(name="Clinic")
        mon = _block(block_date=date(2025, 3, 3))

        slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": None,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]})
        ctx = _context(faculty=[fac], blocks=[mon], activities=[clinic])

        a = _assignment(fac.id, mon.id, activity_id=clinic.id, time_of_day="AM")
        result = c.validate([a], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1

    def test_locked_empty_slot_no_assignment_satisfied(self):
        """Locked empty slot with no assignment -> satisfied."""
        fac = _person(name="Dr. PD")
        mon = _block(block_date=date(2025, 3, 3))

        slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": None,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]})
        ctx = _context(faculty=[fac], blocks=[mon])

        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_soft_preference_deviation_penalty(self):
        """Unlocked slot with different activity -> penalty applied."""
        fac = _person(name="Dr. APD")
        clinic = _activity(name="Clinic")
        admin = _activity(name="Admin")
        tue = _block(block_date=date(2025, 3, 4))

        slot = {
            "day_of_week": 1,  # Tuesday = Python weekday 1
            "time_of_day": "PM",
            "week_number": None,
            "activity_id": clinic.id,
            "is_locked": False,
            "priority": 80,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]}, weight=10.0)
        ctx = _context(faculty=[fac], blocks=[tue], activities=[clinic, admin])

        # Assigned admin instead of preferred clinic
        a = _assignment(fac.id, tue.id, activity_id=admin.id, time_of_day="PM")
        result = c.validate([a], ctx)
        assert result.satisfied is True  # Soft constraint
        expected_penalty = 10.0 * (80 / 100.0)
        assert result.penalty == expected_penalty

    def test_soft_preference_matched_no_penalty(self):
        """Unlocked slot with correct activity -> no penalty."""
        fac = _person(name="Dr. APD")
        clinic = _activity(name="Clinic")
        tue = _block(block_date=date(2025, 3, 4))

        slot = {
            "day_of_week": 1,  # Tuesday = Python weekday 1
            "time_of_day": "PM",
            "week_number": None,
            "activity_id": clinic.id,
            "is_locked": False,
            "priority": 80,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]}, weight=10.0)
        ctx = _context(faculty=[fac], blocks=[tue], activities=[clinic])

        a = _assignment(fac.id, tue.id, activity_id=clinic.id, time_of_day="PM")
        result = c.validate([a], ctx)
        assert result.penalty == 0.0

    def test_violation_details(self):
        """Check violation details for locked slot breach."""
        fac = _person(name="Dr. Chief")
        gme = _activity(name="GME")
        clinic = _activity(name="Clinic")
        mon = _block(block_date=date(2025, 3, 3))

        slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": gme.id,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]})
        ctx = _context(faculty=[fac], blocks=[mon], activities=[gme, clinic])

        a = _assignment(fac.id, mon.id, activity_id=clinic.id, time_of_day="AM")
        result = c.validate([a], ctx)
        v = result.violations[0]
        assert v.person_id == fac.id
        assert v.block_id == mon.id
        assert v.details["date"] == "2025-03-03"
        assert v.details["time_of_day"] == "AM"
        assert v.details["is_locked"] is True

    def test_override_used_in_validate(self):
        """Override takes precedence during validation."""
        fac = _person(name="Dr. PD")
        gme = _activity(name="GME")
        clinic = _activity(name="Clinic")
        mon = _block(block_date=date(2025, 3, 3))

        # Default template says GME (locked)
        template_slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": gme.id,
            "is_locked": True,
        }
        # Override says Clinic (locked) for this week
        override_slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "activity_id": clinic.id,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(
            templates={fac.id: [template_slot]},
            overrides={fac.id: {date(2025, 3, 3): [override_slot]}},
        )
        ctx = _context(faculty=[fac], blocks=[mon], activities=[gme, clinic])

        # Assigned clinic (matches override)
        a = _assignment(fac.id, mon.id, activity_id=clinic.id, time_of_day="AM")
        result = c.validate([a], ctx)
        assert result.satisfied is True

    def test_multiple_faculty_violations(self):
        """Multiple faculty with locked slot breaches."""
        fac1 = _person(name="Dr. A")
        fac2 = _person(name="Dr. B")
        gme = _activity(name="GME")
        clinic = _activity(name="Clinic")
        mon = _block(block_date=date(2025, 3, 3))

        slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "week_number": None,
            "activity_id": gme.id,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(
            templates={fac1.id: [slot], fac2.id: [slot]}
        )
        ctx = _context(faculty=[fac1, fac2], blocks=[mon], activities=[gme, clinic])

        # Both assigned clinic instead of GME
        assignments = [
            _assignment(fac1.id, mon.id, activity_id=clinic.id, time_of_day="AM"),
            _assignment(fac2.id, mon.id, activity_id=clinic.id, time_of_day="AM"),
        ]
        result = c.validate(assignments, ctx)
        assert result.satisfied is False
        assert len(result.violations) == 2

    def test_no_faculty_in_context_satisfied(self):
        """No faculty in context -> satisfied."""
        c = FacultyWeeklyTemplateConstraint()
        ctx = _context()
        result = c.validate([], ctx)
        assert result.satisfied is True

    def test_start_date_affects_week_number(self):
        """start_date in context affects week number calculation."""
        fac = _person(name="Dr. A")
        act = _activity(name="GME")
        # Second week: March 10 with start=March 3 -> week 2
        mon_w2 = _block(block_date=date(2025, 3, 10))

        # Week 2-specific template
        slot = {
            "day_of_week": 0,  # Monday = Python weekday 0
            "time_of_day": "AM",
            "week_number": 2,
            "activity_id": act.id,
            "is_locked": True,
        }
        c = FacultyWeeklyTemplateConstraint(templates={fac.id: [slot]})
        ctx = _context(
            faculty=[fac],
            blocks=[mon_w2],
            activities=[act],
            start_date=date(2025, 3, 3),
        )

        # Correct activity assigned
        a = _assignment(fac.id, mon_w2.id, activity_id=act.id, time_of_day="AM")
        result = c.validate([a], ctx)
        assert result.satisfied is True
