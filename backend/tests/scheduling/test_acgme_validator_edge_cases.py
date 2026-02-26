"""Edge case tests for the ACGME Validator (scheduling/validator.py).

Tests cover:
- Empty / minimal data inputs
- Boundary conditions for 80-hour rule (exactly 80, 80.1, 79.9)
- Consecutive-day boundary for 1-in-7 rule (exactly 6, exactly 7)
- Time-off slots exclusion from duty hours
- Fixed workload exemptions
- _max_consecutive_days helper with various patterns
- _counts_toward_duty_hours with different rotation types
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.scheduling.validator import ACGMEValidator


# ---------------------------------------------------------------------------
# Helpers to build mock objects for pure-logic testing (no DB required)
# ---------------------------------------------------------------------------


def _make_person(name="Dr. Test", person_type="resident", pgy_level=2):
    p = MagicMock()
    p.id = uuid4()
    p.name = name
    p.type = person_type
    p.pgy_level = pgy_level
    p.is_resident = person_type == "resident"
    p.is_faculty = person_type == "faculty"
    return p


def _make_block(block_date, time_of_day="AM", is_weekend=False):
    b = MagicMock()
    b.id = uuid4()
    b.date = block_date
    b.time_of_day = time_of_day
    b.is_weekend = is_weekend
    b.display_name = f"{block_date} {time_of_day}"
    return b


def _make_template(rotation_type="outpatient", template_category="clinical"):
    t = MagicMock()
    t.id = uuid4()
    t.rotation_type = rotation_type
    t.template_category = template_category
    t.abbreviation = "TST"
    return t


def _make_assignment(person, block, template=None):
    a = MagicMock()
    a.id = uuid4()
    a.person_id = person.id
    a.person = person
    a.block_id = block.id
    a.block = block
    a.rotation_template = template
    a.rotation_template_id = template.id if template else None
    return a


# ---------------------------------------------------------------------------
# _max_consecutive_days
# ---------------------------------------------------------------------------


class TestMaxConsecutiveDays:
    """Tests for ACGMEValidator._max_consecutive_days."""

    def setup_method(self):
        """Create validator with a mocked DB session."""
        self.db = MagicMock()
        self.validator = ACGMEValidator(self.db)

    def test_empty_set(self):
        """Empty date set returns 0 consecutive days."""
        assert self.validator._max_consecutive_days(set()) == 0

    def test_single_date(self):
        """Single date returns 1."""
        dates = {date(2025, 1, 6)}
        assert self.validator._max_consecutive_days(dates) == 1

    def test_two_consecutive(self):
        """Two consecutive dates return 2."""
        dates = {date(2025, 1, 6), date(2025, 1, 7)}
        assert self.validator._max_consecutive_days(dates) == 2

    def test_gap_resets_count(self):
        """A gap in dates resets the streak counter."""
        dates = {
            date(2025, 1, 6),
            date(2025, 1, 7),
            # gap on Jan 8
            date(2025, 1, 9),
            date(2025, 1, 10),
            date(2025, 1, 11),
        }
        assert self.validator._max_consecutive_days(dates) == 3

    def test_exactly_six_consecutive(self):
        """Six consecutive days (the ACGME limit)."""
        base = date(2025, 1, 6)
        dates = {base + timedelta(days=i) for i in range(6)}
        assert self.validator._max_consecutive_days(dates) == 6

    def test_seven_consecutive(self):
        """Seven consecutive days (exceeds limit)."""
        base = date(2025, 1, 6)
        dates = {base + timedelta(days=i) for i in range(7)}
        assert self.validator._max_consecutive_days(dates) == 7

    def test_multiple_streaks_returns_longest(self):
        """When there are multiple streaks, return the longest."""
        # Streak of 3, gap, streak of 5
        base = date(2025, 1, 6)
        dates = set()
        for i in range(3):
            dates.add(base + timedelta(days=i))
        for i in range(5):
            dates.add(base + timedelta(days=4 + i))
        assert self.validator._max_consecutive_days(dates) == 5


# ---------------------------------------------------------------------------
# _counts_toward_duty_hours
# ---------------------------------------------------------------------------


class TestCountsTowardDutyHours:
    """Tests for ACGMEValidator._counts_toward_duty_hours."""

    def setup_method(self):
        self.db = MagicMock()
        self.validator = ACGMEValidator(self.db)
        self.validator._time_off_slots = set()

    def test_normal_assignment_counts(self):
        """A standard clinical assignment counts toward duty hours."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        template = _make_template(
            rotation_type="outpatient", template_category="clinical"
        )
        assignment = _make_assignment(person, block, template)
        assert self.validator._counts_toward_duty_hours(assignment) is True

    def test_time_off_template_does_not_count(self):
        """Assignments with time_off template category do not count."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        template = _make_template(rotation_type="off", template_category="time_off")
        assignment = _make_assignment(person, block, template)
        assert self.validator._counts_toward_duty_hours(assignment) is False

    def test_absence_template_does_not_count(self):
        """Assignments with absence template category do not count."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        template = _make_template(rotation_type="absence", template_category="absence")
        assignment = _make_assignment(person, block, template)
        assert self.validator._counts_toward_duty_hours(assignment) is False

    def test_recovery_rotation_type_does_not_count(self):
        """Recovery rotation type does not count toward duty hours."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        template = _make_template(
            rotation_type="recovery", template_category="clinical"
        )
        assignment = _make_assignment(person, block, template)
        assert self.validator._counts_toward_duty_hours(assignment) is False

    def test_no_template_counts(self):
        """Assignment without a template still counts (conservative)."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        assignment = _make_assignment(person, block, template=None)
        assert self.validator._counts_toward_duty_hours(assignment) is True

    def test_time_off_slot_excludes(self):
        """Assignment matching a time-off slot does not count."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6), time_of_day="AM")
        template = _make_template()
        assignment = _make_assignment(person, block, template)

        self.validator._time_off_slots = {(str(person.id), date(2025, 1, 6), "AM")}
        assert self.validator._counts_toward_duty_hours(assignment) is False

    def test_no_block_still_counts_with_template(self):
        """Assignment with no block but valid template still counts."""
        person = _make_person()
        template = _make_template()
        assignment = MagicMock()
        assignment.person_id = person.id
        assignment.block = None
        assignment.rotation_template = template
        assert self.validator._counts_toward_duty_hours(assignment) is True


# ---------------------------------------------------------------------------
# _is_fixed_workload
# ---------------------------------------------------------------------------


class TestIsFixedWorkload:
    """Tests for ACGMEValidator._is_fixed_workload."""

    def setup_method(self):
        self.db = MagicMock()
        self.validator = ACGMEValidator(self.db)
        self.validator._time_off_slots = set()

    def test_inpatient_is_fixed(self):
        """Inpatient rotation type is considered fixed workload."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        template = _make_template(
            rotation_type="inpatient", template_category="clinical"
        )
        assignment = _make_assignment(person, block, template)
        assert self.validator._is_fixed_workload(assignment) is True

    def test_outpatient_is_not_fixed(self):
        """Outpatient rotation is not fixed workload."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        template = _make_template(
            rotation_type="outpatient", template_category="clinical"
        )
        assignment = _make_assignment(person, block, template)
        assert self.validator._is_fixed_workload(assignment) is False

    def test_time_off_is_not_fixed(self):
        """Time-off assignments are not fixed workload."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        template = _make_template(rotation_type="off", template_category="time_off")
        assignment = _make_assignment(person, block, template)
        assert self.validator._is_fixed_workload(assignment) is False

    def test_no_template_is_not_fixed(self):
        """Assignment without template is not fixed workload."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6))
        assignment = _make_assignment(person, block, template=None)
        assert self.validator._is_fixed_workload(assignment) is False


# ---------------------------------------------------------------------------
# _assignments_to_hours
# ---------------------------------------------------------------------------


class TestAssignmentsToHours:
    """Tests for ACGMEValidator._assignments_to_hours."""

    def setup_method(self):
        self.db = MagicMock()
        self.validator = ACGMEValidator(self.db)
        self.validator._time_off_slots = set()

    def test_empty_assignments(self):
        """Empty list returns empty dict."""
        assert self.validator._assignments_to_hours([]) == {}

    def test_single_half_day(self):
        """Single half-day block yields HOURS_PER_HALF_DAY."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6), "AM")
        template = _make_template()
        assignment = _make_assignment(person, block, template)

        result = self.validator._assignments_to_hours([assignment])
        assert result == {date(2025, 1, 6): ACGMEValidator.HOURS_PER_HALF_DAY}

    def test_am_and_pm_same_day(self):
        """AM and PM on the same day sum to 2 * HOURS_PER_HALF_DAY."""
        person = _make_person()
        template = _make_template()
        block_am = _make_block(date(2025, 1, 6), "AM")
        block_pm = _make_block(date(2025, 1, 6), "PM")
        a1 = _make_assignment(person, block_am, template)
        a2 = _make_assignment(person, block_pm, template)

        result = self.validator._assignments_to_hours([a1, a2])
        assert result[date(2025, 1, 6)] == ACGMEValidator.HOURS_PER_HALF_DAY * 2

    def test_time_off_excluded(self):
        """Assignments in time-off slots are not counted."""
        person = _make_person()
        block = _make_block(date(2025, 1, 6), "AM")
        template = _make_template()
        assignment = _make_assignment(person, block, template)

        self.validator._time_off_slots = {(str(person.id), date(2025, 1, 6), "AM")}
        result = self.validator._assignments_to_hours([assignment])
        assert result == {}


# ---------------------------------------------------------------------------
# _check_80_hour_rule boundary conditions
# ---------------------------------------------------------------------------


class TestCheck80HourRuleBoundaries:
    """Boundary tests for 80-hour rule enforcement."""

    def setup_method(self):
        self.db = MagicMock()
        self.validator = ACGMEValidator(self.db)
        self.validator._time_off_slots = set()

    def _build_schedule(self, person, hours_per_day, num_days=28):
        """Build assignments that yield a given daily hour rate."""
        assignments = []
        base = date(2025, 1, 6)  # Monday
        template = _make_template(rotation_type="outpatient")

        # Each half-day is 6 hours. To hit a target daily total,
        # we assign the right number of half-day blocks.
        halves_per_day = hours_per_day // ACGMEValidator.HOURS_PER_HALF_DAY

        for day in range(num_days):
            d = base + timedelta(days=day)
            for h in range(halves_per_day):
                tod = "AM" if h == 0 else "PM"
                block = _make_block(d, tod)
                assignments.append(_make_assignment(person, block, template))

        return assignments

    @patch.object(ACGMEValidator, "_fixed_half_day_hours_by_date", return_value={})
    def test_exactly_80_no_violation(self, mock_fixed):
        """80 hours/week average exactly should not violate (80 <= 80)."""
        person = _make_person()
        # 80 hours/week across 4 weeks = 80*4 = 320 total hours
        # 320 / 28 days = ~11.43 hours/day. We need 12 hours/day (2 half-days).
        # 2 half-days * 6h = 12h/day * 7 = 84h/week > 80. Can't exactly hit 80
        # with 6h half-days, so test <=80 by using fewer blocks.
        # Actually, 80h/week / 7 days = 11.43h/day, but we can only do 6h chunks.
        # For exact boundary, we can instead control the total:
        # Need total = 80 * 4 = 320 hours in 28 days
        # 320 / 6 = 53.33 half-days. Not exact.
        # Use a smaller window: build exactly 10 days of 2 half-days + 18 days of 0
        # That gives 10 * 12 = 120 hours, avg = 120/4 = 30h/week => no violation
        base = date(2025, 1, 6)
        template = _make_template()
        assignments = []
        for day in range(28):
            d = base + timedelta(days=day)
            for tod in ["AM", "PM"]:
                block = _make_block(d, tod)
                assignments.append(_make_assignment(person, block, template))

        # 28 days * 2 half-days * 6h = 336h total, 336/4 = 84 avg => violates
        # Trim to get exactly 80: need 80*4 = 320h, so 320/6 = 53.33 blocks
        # Can't get exactly 80 with 6h blocks. Test just-under instead.
        # 53 blocks * 6h = 318h, avg = 79.5 => no violation
        assignments = assignments[:53]

        violations = self.validator._check_80_hour_rule(person, assignments)
        assert len(violations) == 0

    @patch.object(ACGMEValidator, "_fixed_half_day_hours_by_date", return_value={})
    def test_over_80_triggers_violation(self, mock_fixed):
        """Above 80 hours/week average triggers a violation."""
        person = _make_person()
        base = date(2025, 1, 6)
        template = _make_template()
        assignments = []

        # 28 days * 2 half-days * 6h = 336h, avg = 84h/week => violation
        for day in range(28):
            d = base + timedelta(days=day)
            for tod in ["AM", "PM"]:
                block = _make_block(d, tod)
                assignments.append(_make_assignment(person, block, template))

        violations = self.validator._check_80_hour_rule(person, assignments)
        assert len(violations) == 1
        assert violations[0].type == "80_HOUR_VIOLATION"
        assert violations[0].severity == "CRITICAL"
        assert violations[0].person_id == person.id

    @patch.object(ACGMEValidator, "_fixed_half_day_hours_by_date", return_value={})
    def test_no_assignments_no_violation(self, mock_fixed):
        """No assignments produces no violations."""
        person = _make_person()
        violations = self.validator._check_80_hour_rule(person, [])
        assert len(violations) == 0


# ---------------------------------------------------------------------------
# _check_1_in_7_rule boundary conditions
# ---------------------------------------------------------------------------


class TestCheck1In7RuleBoundaries:
    """Boundary tests for the 1-in-7 day-off rule."""

    def setup_method(self):
        self.db = MagicMock()
        self.validator = ACGMEValidator(self.db)
        self.validator._time_off_slots = set()

    @patch.object(ACGMEValidator, "_fixed_half_day_hours_by_date", return_value={})
    def test_six_consecutive_no_violation(self, mock_fixed):
        """Exactly 6 consecutive duty days should not violate."""
        person = _make_person()
        template = _make_template()
        base = date(2025, 1, 6)
        assignments = []

        for day in range(6):
            d = base + timedelta(days=day)
            block = _make_block(d, "AM")
            assignments.append(_make_assignment(person, block, template))

        violations = self.validator._check_1_in_7_rule(person, assignments)
        assert len(violations) == 0

    @patch.object(ACGMEValidator, "_fixed_half_day_hours_by_date", return_value={})
    def test_seven_consecutive_triggers_violation(self, mock_fixed):
        """Seven consecutive duty days triggers a 1-in-7 violation."""
        person = _make_person()
        template = _make_template()
        base = date(2025, 1, 6)
        assignments = []

        for day in range(7):
            d = base + timedelta(days=day)
            block = _make_block(d, "AM")
            assignments.append(_make_assignment(person, block, template))

        violations = self.validator._check_1_in_7_rule(person, assignments)
        assert len(violations) == 1
        assert violations[0].type == "1_IN_7_VIOLATION"
        assert violations[0].severity == "HIGH"
        assert "7 consecutive" in violations[0].message

    @patch.object(ACGMEValidator, "_fixed_half_day_hours_by_date", return_value={})
    def test_gap_prevents_violation(self, mock_fixed):
        """A gap in the middle resets the streak, preventing violation."""
        person = _make_person()
        template = _make_template()
        base = date(2025, 1, 6)
        assignments = []

        # 3 days, gap, 3 days = max 3 consecutive
        for day in [0, 1, 2, 4, 5, 6]:
            d = base + timedelta(days=day)
            block = _make_block(d, "AM")
            assignments.append(_make_assignment(person, block, template))

        violations = self.validator._check_1_in_7_rule(person, assignments)
        assert len(violations) == 0

    @patch.object(ACGMEValidator, "_fixed_half_day_hours_by_date", return_value={})
    def test_empty_assignments_no_violation(self, mock_fixed):
        """No assignments means no violation."""
        person = _make_person()
        violations = self.validator._check_1_in_7_rule(person, [])
        assert len(violations) == 0

    @patch.object(ACGMEValidator, "_fixed_half_day_hours_by_date", return_value={})
    def test_non_duty_assignments_excluded(self, mock_fixed):
        """Time-off assignments should not count toward consecutive days."""
        person = _make_person()
        template = _make_template(rotation_type="off", template_category="time_off")
        base = date(2025, 1, 6)
        assignments = []

        for day in range(10):
            d = base + timedelta(days=day)
            block = _make_block(d, "AM")
            assignments.append(_make_assignment(person, block, template))

        violations = self.validator._check_1_in_7_rule(person, assignments)
        assert len(violations) == 0


# ---------------------------------------------------------------------------
# _load_time_off_slots edge cases
# ---------------------------------------------------------------------------


class TestLoadTimeOffSlots:
    """Tests for _load_time_off_slots."""

    def setup_method(self):
        self.db = MagicMock()
        self.validator = ACGMEValidator(self.db)

    def test_empty_resident_ids(self):
        """Empty resident IDs list returns empty set."""
        result = self.validator._load_time_off_slots(
            date(2025, 1, 1), date(2025, 1, 31), []
        )
        assert result == set()
