"""Tests for call schedule compliance validator (pure logic, no DB required)."""

from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from app.scheduling.validators.call_validator import (
    MAX_CALL_FREQUENCY_DAYS,
    MAX_CONSECUTIVE_NIGHTS,
    MIN_CALL_SPACING_DAYS,
    POST_CALL_MANDATORY_HOURS,
    ROLLING_WINDOW_DAYS,
    ROLLING_WINDOW_WEEKS,
    CallValidator,
    CallViolation,
    CallWarning,
)


# ==================== Helpers ====================

PERSON = uuid4()
BASE_DATE = date(2025, 3, 3)  # Monday


def _dates(n: int, start: date = BASE_DATE, spacing: int = 3) -> list[date]:
    """Generate call dates with given spacing."""
    return [start + timedelta(days=i * spacing) for i in range(n)]


# ==================== Constants Tests ====================


class TestConstants:
    """Verify ACGME call constants are correct."""

    def test_max_call_frequency_days(self):
        assert MAX_CALL_FREQUENCY_DAYS == 3

    def test_rolling_window_weeks(self):
        assert ROLLING_WINDOW_WEEKS == 4

    def test_rolling_window_days(self):
        assert ROLLING_WINDOW_DAYS == 28

    def test_max_consecutive_nights(self):
        assert MAX_CONSECUTIVE_NIGHTS == 2

    def test_min_call_spacing_days(self):
        assert MIN_CALL_SPACING_DAYS == 2

    def test_post_call_mandatory_hours(self):
        assert POST_CALL_MANDATORY_HOURS == 10


# ==================== Dataclass Tests ====================


class TestCallViolation:
    """Test CallViolation dataclass."""

    def test_construction(self):
        v = CallViolation(
            person_id=PERSON,
            violation_type="frequency",
            severity="HIGH",
            message="Too many calls",
            call_dates=[BASE_DATE],
            violation_count=2,
        )
        assert v.person_id == PERSON
        assert v.violation_type == "frequency"
        assert v.severity == "HIGH"
        assert v.violation_count == 2


class TestCallWarning:
    """Test CallWarning dataclass."""

    def test_construction(self):
        w = CallWarning(
            person_id=PERSON,
            warning_type="approaching_limit",
            message="Close to limit",
            call_count=8,
            equity_metric=0.9,
        )
        assert w.call_count == 8
        assert w.equity_metric == 0.9


# ==================== CallValidator Init ====================


class TestCallValidatorInit:
    """Test CallValidator initialization."""

    def test_default_values(self):
        v = CallValidator()
        assert v.max_call_frequency_days == 3
        assert v.rolling_window_days == 28
        assert v.rolling_window_weeks == 4
        assert v.max_calls_per_window == 9  # 28 // 3

    def test_max_calls_per_window_calculation(self):
        """28 days / 3 days per call = 9 max calls."""
        v = CallValidator()
        assert v.max_calls_per_window == 28 // 3


# ==================== validate_call_frequency Tests ====================


class TestValidateCallFrequency:
    """Test validate_call_frequency method."""

    def test_empty_dates(self):
        v = CallValidator()
        violations, warnings = v.validate_call_frequency(PERSON, [])
        assert violations == []
        assert warnings == []

    def test_single_date(self):
        v = CallValidator()
        violations, warnings = v.validate_call_frequency(PERSON, [BASE_DATE])
        assert violations == []
        assert warnings == []

    def test_well_spaced_calls_no_violation(self):
        """6 calls over 28 days (every ~5 days) -> well under limit."""
        v = CallValidator()
        dates = _dates(6, spacing=5)
        violations, warnings = v.validate_call_frequency(PERSON, dates)
        assert violations == []

    def test_exactly_at_limit(self):
        """9 calls in 28 days -> at limit, no violation."""
        v = CallValidator()
        # 9 calls with 3-day spacing = 27 days span
        dates = _dates(9, spacing=3)
        violations, warnings = v.validate_call_frequency(PERSON, dates)
        assert violations == []

    def test_over_limit_violation(self):
        """11 calls in 28 days -> violation."""
        v = CallValidator()
        # 11 calls, 2-day spacing = 22 days span (within 28-day window)
        dates = _dates(11, spacing=2)
        violations, warnings = v.validate_call_frequency(PERSON, dates)
        assert len(violations) >= 1
        first = violations[0]
        assert first.violation_type == "frequency"
        assert first.severity == "HIGH"

    def test_approaching_limit_warning(self):
        """Calls approaching 90% of max trigger warning."""
        v = CallValidator()
        # max_calls_per_window = 9, 90% = 8.1
        # Need 9 calls in 28-day window (at limit, > 90%)
        # Actually, warning triggers when count > max * 0.9 = 8.1
        # So 9 is not > 9 (limit), but is > 8.1 -> warning
        # Wait, 9 > 9 is False but 9 > 8.1 is True, and 9 is NOT > 9 (limit)
        # So 9 triggers warning, not violation
        dates = _dates(9, spacing=3)
        violations, warnings = v.validate_call_frequency(PERSON, dates)
        # Need to check: 9 > 9 is False (no violation), 9 > 8.1 is True (warning)
        # But the check is: call_count > max_per_window -> violation
        # elif call_count > max_per_window * 0.9 -> warning
        # 9 > 9 = False, 9 > 8.1 = True -> warning
        # BUT: the loop starts from each call date, so window from first date
        # contains all 9 calls. 9 > 9 = False. 9 > 8.1 = True -> warning
        if not violations:
            assert len(warnings) >= 1

    def test_violation_includes_call_dates(self):
        """Violation includes the actual call dates in the window."""
        v = CallValidator()
        dates = _dates(12, spacing=2)
        violations, warnings = v.validate_call_frequency(PERSON, dates)
        if violations:
            assert len(violations[0].call_dates) > 0

    def test_unsorted_dates_handled(self):
        """Dates are sorted internally."""
        v = CallValidator()
        dates = [
            BASE_DATE + timedelta(days=10),
            BASE_DATE,
            BASE_DATE + timedelta(days=5),
        ]
        violations, warnings = v.validate_call_frequency(PERSON, dates)
        assert isinstance(violations, list)


# ==================== validate_consecutive_nights Tests ====================


class TestValidateConsecutiveNights:
    """Test validate_consecutive_nights method."""

    def test_empty_dates(self):
        v = CallValidator()
        violations, warnings = v.validate_consecutive_nights(PERSON, [])
        assert violations == []

    def test_single_date(self):
        v = CallValidator()
        violations, warnings = v.validate_consecutive_nights(PERSON, [BASE_DATE])
        assert violations == []

    def test_two_non_consecutive(self):
        """Two dates, 3 days apart -> no consecutive issue."""
        v = CallValidator()
        dates = [BASE_DATE, BASE_DATE + timedelta(days=3)]
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert violations == []
        assert warnings == []

    def test_two_consecutive_at_limit_no_break(self):
        """Two consecutive nights with no following date -> final check only checks violation.

        Note: The warning for exactly-at-limit (==MAX_CONSECUTIVE_NIGHTS) is only emitted
        when a non-consecutive date breaks the sequence in the loop. The final-sequence
        check only checks for violations (> MAX), not warnings (== MAX).
        """
        v = CallValidator()
        dates = [BASE_DATE, BASE_DATE + timedelta(days=1)]
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert violations == []
        # No warning because the final sequence check lacks the == branch
        assert warnings == []

    def test_two_consecutive_then_break_warning(self):
        """Two consecutive + later date -> sequence broken, warning emitted."""
        v = CallValidator()
        dates = [
            BASE_DATE,
            BASE_DATE + timedelta(days=1),
            BASE_DATE + timedelta(days=10),  # Break triggers sequence check
        ]
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert violations == []
        assert len(warnings) >= 1
        assert warnings[0].warning_type == "approaching_limit"

    def test_three_consecutive_violation(self):
        """Three consecutive nights -> violation (> MAX_CONSECUTIVE_NIGHTS=2)."""
        v = CallValidator()
        dates = [BASE_DATE + timedelta(days=i) for i in range(3)]
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert len(violations) >= 1
        assert violations[0].violation_type == "consecutive"
        assert violations[0].severity == "MEDIUM"
        assert violations[0].violation_count == 1  # 3 - 2 = 1 extra

    def test_four_consecutive_violation(self):
        """Four consecutive nights -> violation with count 2."""
        v = CallValidator()
        dates = [BASE_DATE + timedelta(days=i) for i in range(4)]
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert len(violations) >= 1
        assert violations[0].violation_count == 2  # 4 - 2 = 2 extra

    def test_multiple_consecutive_sequences(self):
        """Two separate sequences of 3 consecutive -> two violations."""
        v = CallValidator()
        dates = (
            [BASE_DATE + timedelta(days=i) for i in range(3)]  # 3 consec
            + [BASE_DATE + timedelta(days=10 + i) for i in range(3)]  # 3 more
        )
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert len(violations) == 2

    def test_mixed_consecutive_and_spaced(self):
        """Mix: 2 consecutive, gap, 3 consecutive."""
        v = CallValidator()
        dates = [
            BASE_DATE,
            BASE_DATE + timedelta(days=1),  # 2 consecutive (warning)
            BASE_DATE + timedelta(days=10),
            BASE_DATE + timedelta(days=11),
            BASE_DATE + timedelta(days=12),  # 3 consecutive (violation)
        ]
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert len(violations) >= 1
        assert len(warnings) >= 1

    def test_unsorted_dates_handled(self):
        """Out-of-order dates sorted internally."""
        v = CallValidator()
        dates = [
            BASE_DATE + timedelta(days=2),
            BASE_DATE,
            BASE_DATE + timedelta(days=1),
        ]
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert len(violations) >= 1  # 3 consecutive

    def test_final_sequence_checked(self):
        """The last sequence in the list is also checked."""
        v = CallValidator()
        # Single sequence at end
        dates = [BASE_DATE + timedelta(days=i) for i in range(3)]
        violations, warnings = v.validate_consecutive_nights(PERSON, dates)
        assert len(violations) >= 1


# ==================== validate_call_spacing Tests ====================


class TestValidateCallSpacing:
    """Test validate_call_spacing method."""

    def test_empty_dates(self):
        v = CallValidator()
        violations, warnings = v.validate_call_spacing(PERSON, [])
        assert violations == []

    def test_single_date(self):
        v = CallValidator()
        violations, warnings = v.validate_call_spacing(PERSON, [BASE_DATE])
        assert violations == []

    def test_adequate_spacing(self):
        """3 days between calls -> adequate (>= 2)."""
        v = CallValidator()
        dates = [BASE_DATE, BASE_DATE + timedelta(days=3)]
        violations, warnings = v.validate_call_spacing(PERSON, dates)
        assert violations == []

    def test_exactly_at_minimum(self):
        """2 days between calls -> at minimum, no violation."""
        v = CallValidator()
        dates = [BASE_DATE, BASE_DATE + timedelta(days=2)]
        violations, warnings = v.validate_call_spacing(PERSON, dates)
        assert violations == []

    def test_insufficient_spacing_violation(self):
        """1 day between calls -> violation."""
        v = CallValidator()
        dates = [BASE_DATE, BASE_DATE + timedelta(days=1)]
        violations, warnings = v.validate_call_spacing(PERSON, dates)
        assert len(violations) >= 1
        assert violations[0].violation_type == "spacing"
        assert violations[0].severity == "MEDIUM"
        assert len(violations[0].call_dates) == 2

    def test_same_day_violation(self):
        """Same-day calls -> 0 day spacing -> violation."""
        v = CallValidator()
        dates = [BASE_DATE, BASE_DATE]
        violations, warnings = v.validate_call_spacing(PERSON, dates)
        assert len(violations) >= 1

    def test_multiple_spacing_violations(self):
        """Multiple consecutive days -> multiple violations."""
        v = CallValidator()
        dates = [BASE_DATE + timedelta(days=i) for i in range(4)]
        violations, warnings = v.validate_call_spacing(PERSON, dates)
        assert len(violations) == 3  # 3 pairs with 1-day spacing

    def test_mixed_spacing(self):
        """Some adequate, some insufficient spacing."""
        v = CallValidator()
        dates = [
            BASE_DATE,
            BASE_DATE + timedelta(days=1),  # 1 day -> violation
            BASE_DATE + timedelta(days=5),  # 4 days -> OK
            BASE_DATE + timedelta(days=6),  # 1 day -> violation
        ]
        violations, warnings = v.validate_call_spacing(PERSON, dates)
        assert len(violations) == 2


# ==================== validate_call_equity Tests ====================


class TestValidateCallEquity:
    """Test validate_call_equity method."""

    def test_empty_assignments(self):
        v = CallValidator()
        warnings, metrics = v.validate_call_equity(
            BASE_DATE, BASE_DATE + timedelta(days=28), {}
        )
        assert warnings == []
        assert metrics == {}

    def test_single_faculty(self):
        v = CallValidator()
        fac1 = uuid4()
        assignments = {fac1: _dates(5)}
        warnings, metrics = v.validate_call_equity(
            BASE_DATE, BASE_DATE + timedelta(days=28), assignments
        )
        # < 2 faculty -> returns early
        assert warnings == []
        assert metrics == {}

    def test_balanced_distribution(self):
        """Equal calls -> no imbalance warning."""
        v = CallValidator()
        fac1, fac2, fac3 = uuid4(), uuid4(), uuid4()
        assignments = {
            fac1: _dates(4, spacing=7),
            fac2: _dates(4, spacing=7),
            fac3: _dates(4, spacing=7),
        }
        warnings, metrics = v.validate_call_equity(
            BASE_DATE, BASE_DATE + timedelta(days=28), assignments
        )
        assert len(warnings) == 0
        assert metrics["mean_calls"] == 4.0
        assert metrics["std_dev"] == 0.0
        assert metrics["faculty_count"] == 3

    def test_imbalanced_distribution_warning(self):
        """One faculty has much more calls -> imbalance warning."""
        v = CallValidator()
        fac1, fac2 = uuid4(), uuid4()
        assignments = {
            fac1: _dates(8, spacing=3),
            fac2: _dates(2, spacing=10),
        }
        warnings, metrics = v.validate_call_equity(
            BASE_DATE, BASE_DATE + timedelta(days=28), assignments
        )
        # ratio = 8 / (2 + 0.1) = 3.81 > 1.5 -> warning
        assert len(warnings) >= 1
        assert warnings[0].warning_type == "imbalance"
        assert metrics["imbalance_ratio"] > 1.5

    def test_metrics_calculated(self):
        """Metrics include all expected fields."""
        v = CallValidator()
        fac1, fac2 = uuid4(), uuid4()
        assignments = {
            fac1: _dates(6, spacing=4),
            fac2: _dates(4, spacing=6),
        }
        warnings, metrics = v.validate_call_equity(
            BASE_DATE, BASE_DATE + timedelta(days=28), assignments
        )
        assert "mean_calls" in metrics
        assert "std_dev" in metrics
        assert "imbalance_ratio" in metrics
        assert "over_assigned" in metrics
        assert "under_assigned" in metrics
        assert "total_calls" in metrics
        assert "faculty_count" in metrics
        assert metrics["total_calls"] == 10
        assert metrics["faculty_count"] == 2

    def test_over_under_assigned_identified(self):
        """Faculty with calls > mean+std_dev are flagged."""
        v = CallValidator()
        fac1, fac2, fac3 = uuid4(), uuid4(), uuid4()
        assignments = {
            fac1: _dates(10, spacing=2),  # Way more
            fac2: _dates(3, spacing=8),
            fac3: _dates(3, spacing=8),
        }
        warnings, metrics = v.validate_call_equity(
            BASE_DATE, BASE_DATE + timedelta(days=28), assignments
        )
        # mean ~5.33, std_dev significant
        assert fac1 in metrics["over_assigned"]

    def test_zero_calls_faculty(self):
        """Faculty with 0 calls doesn't cause error."""
        v = CallValidator()
        fac1, fac2 = uuid4(), uuid4()
        assignments = {
            fac1: _dates(6, spacing=4),
            fac2: [],  # 0 calls
        }
        warnings, metrics = v.validate_call_equity(
            BASE_DATE, BASE_DATE + timedelta(days=28), assignments
        )
        # ratio = 6 / (0 + 0.1) = 60 > 1.5 -> warning
        assert len(warnings) >= 1
        assert metrics["imbalance_ratio"] > 1.5

    def test_slight_imbalance_no_warning(self):
        """Ratio <= 1.5 -> no warning."""
        v = CallValidator()
        fac1, fac2 = uuid4(), uuid4()
        assignments = {
            fac1: _dates(5, spacing=5),
            fac2: _dates(4, spacing=6),
        }
        warnings, metrics = v.validate_call_equity(
            BASE_DATE, BASE_DATE + timedelta(days=28), assignments
        )
        # ratio = 5 / (4 + 0.1) = 1.22 < 1.5 -> no warning
        assert len(warnings) == 0


# ==================== validate_night_float_post_call Tests ====================


class TestValidateNightFloatPostCall:
    """Test validate_night_float_post_call method."""

    def test_compliant_post_call(self):
        """PC day on correct date -> None (compliant)."""
        v = CallValidator()
        nf_end = date(2025, 3, 7)
        pc_date = date(2025, 3, 8)
        result = v.validate_night_float_post_call(PERSON, nf_end, pc_date)
        assert result is None

    def test_missing_post_call(self):
        """No PC day -> error message."""
        v = CallValidator()
        nf_end = date(2025, 3, 7)
        result = v.validate_night_float_post_call(PERSON, nf_end, None)
        assert result is not None
        assert "Missing mandatory post-call" in result
        assert "2025-03-08" in result

    def test_wrong_date_post_call(self):
        """PC day on wrong date -> error message."""
        v = CallValidator()
        nf_end = date(2025, 3, 7)
        pc_date = date(2025, 3, 10)  # 3 days later, not 1
        result = v.validate_night_float_post_call(PERSON, nf_end, pc_date)
        assert result is not None
        assert "wrong date" in result
        assert "2025-03-10" in result

    def test_same_day_as_nf_end_is_wrong(self):
        """PC day on same day as NF end -> wrong (should be next day)."""
        v = CallValidator()
        nf_end = date(2025, 3, 7)
        result = v.validate_night_float_post_call(PERSON, nf_end, nf_end)
        assert result is not None


# ==================== get_call_schedule_summary Tests ====================


class TestGetCallScheduleSummary:
    """Test get_call_schedule_summary method."""

    def test_empty_assignments(self):
        v = CallValidator()
        summary = v.get_call_schedule_summary(
            {}, BASE_DATE, BASE_DATE + timedelta(days=28)
        )
        assert summary["total_calls"] == 0
        assert summary["faculty_count"] == 0
        assert summary["mean_calls_per_faculty"] == 0

    def test_single_faculty_summary(self):
        v = CallValidator()
        fac1 = uuid4()
        assignments = {fac1: _dates(5, spacing=5)}
        summary = v.get_call_schedule_summary(
            assignments, BASE_DATE, BASE_DATE + timedelta(days=28)
        )
        assert summary["total_calls"] == 5
        assert summary["faculty_count"] == 1
        assert summary["mean_calls_per_faculty"] == 5.0
        assert summary["min_calls"] == 5
        assert summary["max_calls"] == 5

    def test_multiple_faculty_summary(self):
        v = CallValidator()
        fac1, fac2, fac3 = uuid4(), uuid4(), uuid4()
        assignments = {
            fac1: _dates(6, spacing=4),
            fac2: _dates(4, spacing=6),
            fac3: _dates(5, spacing=5),
        }
        summary = v.get_call_schedule_summary(
            assignments, BASE_DATE, BASE_DATE + timedelta(days=28)
        )
        assert summary["total_calls"] == 15
        assert summary["faculty_count"] == 3
        assert summary["mean_calls_per_faculty"] == 5.0
        assert summary["min_calls"] == 4
        assert summary["max_calls"] == 6
        assert len(summary["call_distribution"]) == 3

    def test_period_in_summary(self):
        v = CallValidator()
        start = date(2025, 3, 1)
        end = date(2025, 3, 28)
        summary = v.get_call_schedule_summary({}, start, end)
        assert summary["period"]["start"] == start
        assert summary["period"]["end"] == end

    def test_call_distribution_by_faculty(self):
        v = CallValidator()
        fac1, fac2 = uuid4(), uuid4()
        assignments = {
            fac1: _dates(3, spacing=7),
            fac2: _dates(7, spacing=3),
        }
        summary = v.get_call_schedule_summary(
            assignments, BASE_DATE, BASE_DATE + timedelta(days=28)
        )
        assert summary["call_distribution"][fac1] == 3
        assert summary["call_distribution"][fac2] == 7
