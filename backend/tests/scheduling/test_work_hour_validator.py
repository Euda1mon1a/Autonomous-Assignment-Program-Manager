"""Tests for ACGME work hour compliance validator (pure logic, no DB required)."""

from datetime import date, datetime, time, timedelta
from uuid import UUID, uuid4

import pytest

from app.scheduling.validators.work_hour_validator import (
    HOURS_PER_BLOCK,
    MAX_BLOCKS_PER_WINDOW,
    MAX_CONSECUTIVE_HOURS,
    MAX_TOTAL_SHIFT_HOURS,
    MAX_WEEKLY_HOURS,
    MIN_REST_HOURS_AFTER_SHIFT,
    MOONLIGHTING_HOURS_PER_WEEK_WARNING,
    ROLLING_DAYS,
    ROLLING_WEEKS,
    BlockBasedWorkHourCalculator,
    WorkHourValidator,
    WorkHourViolation,
    WorkHourWarning,
)


# ==================== Helpers ====================

PERSON = uuid4()
BASE_DATE = date(2025, 3, 3)  # Monday


def _dates(n: int, start: date = BASE_DATE) -> list[date]:
    """Generate a list of consecutive dates."""
    return [start + timedelta(days=i) for i in range(n)]


def _hours_by_date(hours: float, dates: list[date]) -> dict[date, float]:
    """Create an hours_by_date dict with same hours for all dates."""
    return dict.fromkeys(dates, hours)


def _shift(
    d: date,
    start: str = "07:00",
    end: str = "19:00",
    duration: float = 12.0,
    is_call: bool = False,
) -> dict:
    """Create a shift dict."""
    return {
        "date": d,
        "start_time": start,
        "end_time": end,
        "duration_hours": duration,
        "is_call": is_call,
    }


# ==================== Constants Tests ====================


class TestConstants:
    """Verify ACGME constants are correct."""

    def test_max_weekly_hours(self):
        assert MAX_WEEKLY_HOURS == 80

    def test_rolling_days(self):
        assert ROLLING_DAYS == 28

    def test_rolling_weeks(self):
        assert ROLLING_WEEKS == 4

    def test_hours_per_block(self):
        assert HOURS_PER_BLOCK == 6

    def test_max_blocks_per_window(self):
        # 80 * 4 / 6 = 53.33 -> int 53
        assert MAX_BLOCKS_PER_WINDOW == 53

    def test_max_consecutive_hours(self):
        assert MAX_CONSECUTIVE_HOURS == 24

    def test_max_total_shift_hours(self):
        assert MAX_TOTAL_SHIFT_HOURS == 28

    def test_min_rest_hours(self):
        assert MIN_REST_HOURS_AFTER_SHIFT == 10


# ==================== Dataclass Tests ====================


class TestWorkHourViolation:
    """Test WorkHourViolation dataclass."""

    def test_construction(self):
        v = WorkHourViolation(
            person_id=PERSON,
            violation_type="80_hour",
            severity="CRITICAL",
            message="Over limit",
            date_range=(BASE_DATE, BASE_DATE + timedelta(days=27)),
            hours=85.0,
            limit=80.0,
        )
        assert v.person_id == PERSON
        assert v.violation_type == "80_hour"
        assert v.severity == "CRITICAL"
        assert v.violation_percentage == 0.0  # default

    def test_with_violation_percentage(self):
        v = WorkHourViolation(
            person_id=PERSON,
            violation_type="24_plus_4",
            severity="HIGH",
            message="Shift too long",
            date_range=(BASE_DATE, BASE_DATE),
            hours=30.0,
            limit=28.0,
            violation_percentage=7.14,
        )
        assert v.violation_percentage == pytest.approx(7.14)


class TestWorkHourWarning:
    """Test WorkHourWarning dataclass."""

    def test_construction(self):
        w = WorkHourWarning(
            person_id=PERSON,
            warning_type="approaching_limit",
            message="At 77 hours",
            current_hours=77.0,
            warning_threshold=76.0,
            days_remaining=3,
        )
        assert w.person_id == PERSON
        assert w.warning_type == "approaching_limit"
        assert w.days_remaining == 3


# ==================== WorkHourValidator Init ====================


class TestWorkHourValidatorInit:
    """Test WorkHourValidator initialization."""

    def test_default_values(self):
        v = WorkHourValidator()
        assert v.max_weekly_hours == 80
        assert v.rolling_days == 28
        assert v.rolling_weeks == 4
        assert v.hours_per_block == 6
        assert v.max_blocks_per_window == 53


# ==================== 80-Hour Rolling Average Tests ====================


class TestValidate80HourRollingAverage:
    """Test validate_80_hour_rolling_average method."""

    def test_empty_hours(self):
        v = WorkHourValidator()
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, {})
        assert violations == []
        assert warnings == []

    def test_well_under_limit(self):
        """60 hours/week avg -> no violations or warnings."""
        v = WorkHourValidator()
        dates = _dates(28)
        # 60h/week * 4 weeks = 240h total / 28 days = 8.57h/day
        hours = _hours_by_date(8.57, dates)
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, hours)
        assert violations == []
        assert warnings == []

    def test_exactly_at_limit(self):
        """Exactly 80h/week avg -> no violation (not exceeding)."""
        v = WorkHourValidator()
        dates = _dates(28)
        # 80h/week * 4 weeks = 320h / 28 days = 11.428/day
        hours = _hours_by_date(11.428, dates)
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, hours)
        # At exactly 80, not over, so no violation
        assert violations == []

    def test_over_limit_violation(self):
        """90h/week avg -> CRITICAL violation."""
        v = WorkHourValidator()
        dates = _dates(28)
        # 90h/week * 4 weeks = 360h / 28 days = 12.857/day
        hours = _hours_by_date(12.857, dates)
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, hours)
        assert len(violations) >= 1
        first = violations[0]
        assert first.violation_type == "80_hour"
        assert first.severity in ("CRITICAL", "HIGH")
        assert first.hours > 80

    def test_approaching_limit_warning(self):
        """77h/week avg -> approaching limit warning."""
        v = WorkHourValidator()
        dates = _dates(28)
        # 77h/week * 4 = 308h / 28 = 11.0/day
        hours = _hours_by_date(11.0, dates)
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, hours)
        # 308 / 4 = 77 -> > 76 (95% of 80) -> warning
        assert violations == []
        assert len(warnings) >= 1
        assert warnings[0].warning_type == "approaching_limit"

    def test_slight_over_is_high_severity(self):
        """81h/week avg -> HIGH severity (< 10% over)."""
        v = WorkHourValidator()
        dates = _dates(28)
        # 81h/week * 4 = 324h / 28 = 11.571/day
        hours = _hours_by_date(11.571, dates)
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, hours)
        assert len(violations) >= 1
        # violation_pct = (81-80)/80*100 = 1.25% < 10 -> HIGH
        assert violations[0].severity == "HIGH"

    def test_large_over_is_critical_severity(self):
        """100h/week avg -> CRITICAL severity (25% over)."""
        v = WorkHourValidator()
        dates = _dates(28)
        # 100h/week * 4 = 400h / 28 = 14.286/day
        hours = _hours_by_date(14.286, dates)
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, hours)
        assert len(violations) >= 1
        assert violations[0].severity == "CRITICAL"

    def test_moonlighting_hours_added(self):
        """Moonlighting pushes total over 80h limit."""
        v = WorkHourValidator()
        dates = _dates(28)
        # 75h/week base = 300h / 28 = 10.714/day
        base_hours = _hours_by_date(10.714, dates)
        # 10h/week moonlighting = 40h / 28 = 1.428/day
        moonlight = _hours_by_date(1.428, dates)
        violations, warnings = v.validate_80_hour_rolling_average(
            PERSON, base_hours, moonlight
        )
        # Total: 85h/week -> violation
        assert len(violations) >= 1
        assert violations[0].violation_type == "80_hour"

    def test_moonlighting_on_non_work_days(self):
        """Moonlighting on days not in base hours."""
        v = WorkHourValidator()
        dates = _dates(14)
        base_hours = _hours_by_date(10.0, dates)
        extra_dates = _dates(7, start=BASE_DATE + timedelta(days=14))
        moonlight = _hours_by_date(5.0, extra_dates)
        violations, warnings = v.validate_80_hour_rolling_average(
            PERSON, base_hours, moonlight
        )
        # Should not crash, moonlighting on different days added correctly
        assert isinstance(violations, list)

    def test_single_day_no_violation(self):
        """Single day can't trigger 80h/week violation."""
        v = WorkHourValidator()
        hours = {BASE_DATE: 16.0}
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, hours)
        # 16h in one day, 28-day window -> 16/4 = 4h/week avg -> well under
        assert violations == []

    def test_violation_date_range(self):
        """Violation includes correct date range."""
        v = WorkHourValidator()
        dates = _dates(28)
        hours = _hours_by_date(14.0, dates)  # Way over limit
        violations, warnings = v.validate_80_hour_rolling_average(PERSON, hours)
        assert len(violations) >= 1
        first = violations[0]
        assert first.date_range[0] == dates[0]
        assert first.date_range[1] == dates[0] + timedelta(days=27)


# ==================== 24+4 Rule Tests ====================


class TestValidate24Plus4Rule:
    """Test validate_24_plus_4_rule method."""

    def test_empty_shifts(self):
        v = WorkHourValidator()
        violations, warnings = v.validate_24_plus_4_rule(PERSON, [])
        assert violations == []
        assert warnings == []

    def test_normal_shift_no_issue(self):
        """12-hour shift -> no violation."""
        v = WorkHourValidator()
        shifts = [_shift(BASE_DATE, duration=12.0)]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        assert violations == []
        assert warnings == []

    def test_exactly_24_hours_no_violation(self):
        """24-hour shift -> no violation (at the limit, not over)."""
        v = WorkHourValidator()
        shifts = [_shift(BASE_DATE, duration=24.0)]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        assert violations == []
        assert warnings == []

    def test_25_hours_within_28_no_violation(self):
        """25 hours -> within 24+4 exception, no violation."""
        v = WorkHourValidator()
        shifts = [_shift(BASE_DATE, duration=25.0)]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        assert violations == []

    def test_27_hours_warning(self):
        """27 hours -> within 28h limit but triggers warning (>26h)."""
        v = WorkHourValidator()
        shifts = [_shift(BASE_DATE, duration=27.0)]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        assert violations == []
        assert len(warnings) >= 1
        assert warnings[0].warning_type == "imbalance"
        assert warnings[0].current_hours == 27.0

    def test_28_hours_is_at_limit(self):
        """28 hours -> at max total shift hours, warning."""
        v = WorkHourValidator()
        shifts = [_shift(BASE_DATE, duration=28.0)]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        # 28 == MAX_TOTAL_SHIFT_HOURS (28), duration > 26 -> warning
        assert violations == []
        assert len(warnings) >= 1

    def test_30_hours_violation(self):
        """30 hours -> exceeds 24+4 (28h) limit -> CRITICAL."""
        v = WorkHourValidator()
        shifts = [_shift(BASE_DATE, duration=30.0)]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        assert len(violations) >= 1
        assert violations[0].violation_type == "24_plus_4"
        assert violations[0].severity == "CRITICAL"
        assert violations[0].hours == 30.0
        assert violations[0].limit == 28

    def test_multiple_shifts_mixed(self):
        """Multiple shifts: one normal, one over limit."""
        v = WorkHourValidator()
        shifts = [
            _shift(BASE_DATE, duration=12.0),  # Normal
            _shift(BASE_DATE + timedelta(days=1), duration=30.0),  # Over
        ]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        assert len(violations) == 1

    def test_missing_date_in_violation_skipped(self):
        """Shift without date field doesn't create violation."""
        v = WorkHourValidator()
        shifts = [{"start_time": "07:00", "duration_hours": 30.0}]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        # shift_date is None -> skip creating violation
        assert violations == []

    def test_missing_duration_no_issue(self):
        """Shift without duration_hours -> defaults to 0, no issue."""
        v = WorkHourValidator()
        shifts = [{"date": BASE_DATE, "start_time": "07:00"}]
        violations, warnings = v.validate_24_plus_4_rule(PERSON, shifts)
        assert violations == []
        assert warnings == []


# ==================== Rest Period Tests ====================


class TestValidateRestPeriod:
    """Test validate_rest_period method."""

    def test_empty_shifts(self):
        v = WorkHourValidator()
        violations, warnings = v.validate_rest_period(PERSON, [])
        assert violations == []

    def test_single_shift(self):
        """Single shift -> no rest comparison possible."""
        v = WorkHourValidator()
        shifts = [_shift(BASE_DATE, duration=24.0, is_call=True)]
        violations, warnings = v.validate_rest_period(PERSON, shifts)
        assert violations == []

    def test_adequate_rest(self):
        """24h shift followed by 12h rest -> no violation."""
        v = WorkHourValidator()
        shifts = [
            _shift(BASE_DATE, "07:00", "07:00", duration=24.0, is_call=True),
            _shift(BASE_DATE + timedelta(days=1), "19:00", "07:00", duration=12.0),
        ]
        violations, warnings = v.validate_rest_period(PERSON, shifts)
        assert violations == []

    def test_insufficient_rest_violation(self):
        """24h call shift followed by 4h rest -> violation."""
        v = WorkHourValidator()
        shifts = [
            _shift(BASE_DATE, "07:00", "07:00", duration=24.0, is_call=True),
            _shift(BASE_DATE + timedelta(days=1), "11:00", "23:00", duration=12.0),
        ]
        violations, warnings = v.validate_rest_period(PERSON, shifts)
        assert len(violations) >= 1
        assert violations[0].violation_type == "rest_period"
        assert violations[0].severity == "HIGH"

    def test_short_shift_no_rest_requirement(self):
        """12h non-call shift -> no rest requirement check."""
        v = WorkHourValidator()
        shifts = [
            _shift(BASE_DATE, "07:00", "19:00", duration=12.0),
            _shift(BASE_DATE + timedelta(days=1), "07:00", "19:00", duration=12.0),
        ]
        violations, warnings = v.validate_rest_period(PERSON, shifts)
        # Neither shift is >= 24h or call -> skip
        assert violations == []

    def test_call_shift_triggers_rest_check(self):
        """Call shifts always trigger rest period check regardless of duration."""
        v = WorkHourValidator()
        shifts = [
            _shift(BASE_DATE, "07:00", "19:00", duration=12.0, is_call=True),
            _shift(BASE_DATE, "20:00", "07:00", duration=11.0),
        ]
        violations, warnings = v.validate_rest_period(PERSON, shifts)
        # is_call=True -> rest check triggered even though < 24h
        # Rest: 1h (19:00 to 20:00) -> violation
        assert len(violations) >= 1

    def test_rest_warning_near_limit(self):
        """11h rest after 24h shift -> warning (within 2h of 10h minimum)."""
        v = WorkHourValidator()
        shifts = [
            _shift(BASE_DATE, "07:00", "07:00", duration=24.0, is_call=True),
            _shift(BASE_DATE + timedelta(days=1), "18:00", "06:00", duration=12.0),
        ]
        violations, warnings = v.validate_rest_period(PERSON, shifts)
        # Rest: 11h (07:00 to 18:00) -> approaching limit warning
        if not violations:
            assert len(warnings) >= 1
            assert warnings[0].warning_type == "approaching_limit"

    def test_time_object_parsing(self):
        """Shift with time objects instead of strings."""
        v = WorkHourValidator()
        shifts = [
            {
                "date": BASE_DATE,
                "start_time": time(7, 0),
                "end_time": time(7, 0),
                "duration_hours": 24.0,
                "is_call": True,
            },
            {
                "date": BASE_DATE + timedelta(days=1),
                "start_time": time(10, 0),
                "end_time": time(22, 0),
                "duration_hours": 12.0,
            },
        ]
        violations, warnings = v.validate_rest_period(PERSON, shifts)
        # Should parse time objects correctly without error
        assert isinstance(violations, list)


# ==================== _calculate_rest_hours Tests ====================


class TestCalculateRestHours:
    """Test _calculate_rest_hours private method."""

    def test_same_day_gap(self):
        """Same day, end 12:00 to start 22:00 -> 10 hours."""
        v = WorkHourValidator()
        current = {"date": BASE_DATE, "end_time": "12:00"}
        nxt = {"date": BASE_DATE, "start_time": "22:00"}
        rest = v._calculate_rest_hours(current, nxt)
        assert rest == pytest.approx(10.0)

    def test_next_day_gap(self):
        """End 19:00 day 1, start 07:00 day 2 -> 12 hours."""
        v = WorkHourValidator()
        current = {"date": BASE_DATE, "end_time": "19:00"}
        nxt = {"date": BASE_DATE + timedelta(days=1), "start_time": "07:00"}
        rest = v._calculate_rest_hours(current, nxt)
        assert rest == pytest.approx(12.0)

    def test_missing_end_time_fallback(self):
        """Missing end_time -> fallback to date-based estimate."""
        v = WorkHourValidator()
        current = {"date": BASE_DATE}
        nxt = {"date": BASE_DATE + timedelta(days=1), "start_time": "07:00"}
        rest = v._calculate_rest_hours(current, nxt)
        # Fallback: days_diff * 24 - 12 = 1 * 24 - 12 = 12
        assert rest == pytest.approx(12.0)

    def test_missing_all_times_fallback(self):
        """Both times missing -> fallback to date-based."""
        v = WorkHourValidator()
        current = {"date": BASE_DATE}
        nxt = {"date": BASE_DATE + timedelta(days=2)}
        rest = v._calculate_rest_hours(current, nxt)
        # 2 * 24 - 12 = 36
        assert rest == pytest.approx(36.0)

    def test_missing_dates_returns_zero(self):
        """Missing dates -> returns 0."""
        v = WorkHourValidator()
        current = {"end_time": "19:00"}
        nxt = {"start_time": "07:00"}
        rest = v._calculate_rest_hours(current, nxt)
        assert rest == 0.0

    def test_overnight_call_shift_with_duration(self):
        """Call shift 19:00-07:00 (12h) -> end computed from start + duration."""
        v = WorkHourValidator()
        current = {
            "date": BASE_DATE,
            "start_time": "19:00",
            "end_time": "07:00",
            "duration_hours": 12.0,
            "is_call": True,
        }
        nxt = {
            "date": BASE_DATE + timedelta(days=1),
            "start_time": "12:00",
        }
        rest = v._calculate_rest_hours(current, nxt)
        # Call shift: end = 19:00 + 12h = 07:00 next day
        # Rest: 07:00 to 12:00 = 5h
        assert rest == pytest.approx(5.0)

    def test_overnight_non_call_shift(self):
        """Non-call overnight shift: end_time < start_time -> add 1 day."""
        v = WorkHourValidator()
        current = {
            "date": BASE_DATE,
            "start_time": "20:00",
            "end_time": "06:00",
        }
        nxt = {
            "date": BASE_DATE + timedelta(days=1),
            "start_time": "16:00",
        }
        rest = v._calculate_rest_hours(current, nxt)
        # end_time 06:00 < start_time 20:00 -> overnight, end_time = next day 06:00
        # Rest: 06:00 to 16:00 = 10h
        assert rest == pytest.approx(10.0)

    def test_time_objects(self):
        """Time objects instead of strings work correctly."""
        v = WorkHourValidator()
        current = {"date": BASE_DATE, "end_time": time(18, 0)}
        nxt = {"date": BASE_DATE + timedelta(days=1), "start_time": time(8, 0)}
        rest = v._calculate_rest_hours(current, nxt)
        assert rest == pytest.approx(14.0)

    def test_string_date_parsing(self):
        """String dates (ISO format) are parsed correctly."""
        v = WorkHourValidator()
        current = {"date": "2025-03-03", "end_time": "18:00"}
        nxt = {"date": "2025-03-04", "start_time": "08:00"}
        rest = v._calculate_rest_hours(current, nxt)
        assert rest == pytest.approx(14.0)


# ==================== _ensure_date Tests ====================


class TestEnsureDate:
    """Test _ensure_date helper."""

    def test_none_returns_none(self):
        v = WorkHourValidator()
        assert v._ensure_date(None) is None

    def test_date_returns_date(self):
        v = WorkHourValidator()
        d = date(2025, 3, 1)
        assert v._ensure_date(d) == d

    def test_string_iso_format(self):
        v = WorkHourValidator()
        assert v._ensure_date("2025-03-01") == date(2025, 3, 1)

    def test_invalid_string_returns_none(self):
        v = WorkHourValidator()
        assert v._ensure_date("not-a-date") is None

    def test_unexpected_type_returns_none(self):
        v = WorkHourValidator()
        assert v._ensure_date(12345) is None

    def test_datetime_is_subclass_of_date(self):
        """datetime is a subclass of date, should return as-is."""
        v = WorkHourValidator()
        dt = datetime(2025, 3, 1, 12, 0)
        result = v._ensure_date(dt)
        assert result is dt


# ==================== _parse_time_to_datetime Tests ====================


class TestParseTimeToDatetime:
    """Test _parse_time_to_datetime helper."""

    def test_time_object(self):
        v = WorkHourValidator()
        result = v._parse_time_to_datetime(BASE_DATE, time(14, 30))
        assert result == datetime(2025, 3, 3, 14, 30)

    def test_string_hh_mm(self):
        v = WorkHourValidator()
        result = v._parse_time_to_datetime(BASE_DATE, "14:30")
        assert result == datetime(2025, 3, 3, 14, 30)

    def test_string_hh_mm_ss(self):
        v = WorkHourValidator()
        result = v._parse_time_to_datetime(BASE_DATE, "14:30:45")
        assert result == datetime(2025, 3, 3, 14, 30, 45)

    def test_string_hh_only(self):
        v = WorkHourValidator()
        result = v._parse_time_to_datetime(BASE_DATE, "14")
        assert result == datetime(2025, 3, 3, 14, 0, 0)

    def test_invalid_string_returns_none(self):
        v = WorkHourValidator()
        result = v._parse_time_to_datetime(BASE_DATE, "not-a-time")
        assert result is None

    def test_none_returns_none(self):
        v = WorkHourValidator()
        result = v._parse_time_to_datetime(BASE_DATE, None)
        assert result is None


# ==================== Moonlighting Integration Tests ====================


class TestValidateMoonlightingIntegration:
    """Test validate_moonlighting_integration method."""

    def test_empty_moonlighting(self):
        v = WorkHourValidator()
        violations, warnings = v.validate_moonlighting_integration(PERSON, {})
        assert violations == []
        assert warnings == []

    def test_low_moonlighting_no_warning(self):
        """10h/week moonlighting -> under threshold."""
        v = WorkHourValidator()
        # Week starting Monday March 3
        dates = _dates(7)
        moonlight = _hours_by_date(1.4, dates)  # ~10h total
        violations, warnings = v.validate_moonlighting_integration(PERSON, moonlight)
        assert violations == []
        assert warnings == []

    def test_high_moonlighting_warning(self):
        """25h/week moonlighting -> warning (> 20h threshold)."""
        v = WorkHourValidator()
        dates = _dates(5)  # Weekdays
        moonlight = _hours_by_date(5.0, dates)  # 25h total
        violations, warnings = v.validate_moonlighting_integration(PERSON, moonlight)
        assert len(warnings) >= 1
        assert warnings[0].warning_type == "imbalance"
        assert "moonlighting" in warnings[0].message.lower()

    def test_multiple_weeks(self):
        """Moonlighting across two weeks — each evaluated independently."""
        v = WorkHourValidator()
        week1 = _dates(5, start=date(2025, 3, 3))  # Mon-Fri week 1
        week2 = _dates(5, start=date(2025, 3, 10))  # Mon-Fri week 2
        moonlight = {}
        for d in week1:
            moonlight[d] = 3.0  # 15h week 1 -> under threshold
        for d in week2:
            moonlight[d] = 5.0  # 25h week 2 -> over threshold
        violations, warnings = v.validate_moonlighting_integration(PERSON, moonlight)
        # Only week 2 should trigger warning
        assert len(warnings) >= 1

    def test_exact_threshold_no_warning(self):
        """Exactly 20h/week -> not over threshold."""
        v = WorkHourValidator()
        dates = _dates(5)
        moonlight = _hours_by_date(4.0, dates)  # 20h total
        violations, warnings = v.validate_moonlighting_integration(PERSON, moonlight)
        assert warnings == []

    def test_week_grouping_by_monday(self):
        """Hours group by week starting Monday."""
        v = WorkHourValidator()
        # Sunday March 2 and Monday March 3 should be in different weeks
        moonlight = {
            date(2025, 3, 2): 15.0,  # Sunday -> week starting Feb 24
            date(2025, 3, 3): 15.0,  # Monday -> week starting Mar 3
        }
        violations, warnings = v.validate_moonlighting_integration(PERSON, moonlight)
        # Each week has 15h, both under 20h threshold
        assert warnings == []


# ==================== Severity / Notification Tests ====================


class TestCalculateViolationSeverityLevel:
    """Test calculate_violation_severity_level method."""

    def test_critical_above_10_percent(self):
        v = WorkHourValidator()
        assert v.calculate_violation_severity_level(15.0) == "CRITICAL"

    def test_critical_at_10_percent(self):
        v = WorkHourValidator()
        assert v.calculate_violation_severity_level(10.0) == "CRITICAL"

    def test_high_at_5_percent(self):
        v = WorkHourValidator()
        assert v.calculate_violation_severity_level(5.0) == "HIGH"

    def test_high_between_5_and_10(self):
        v = WorkHourValidator()
        assert v.calculate_violation_severity_level(7.5) == "HIGH"

    def test_medium_below_5(self):
        v = WorkHourValidator()
        assert v.calculate_violation_severity_level(2.0) == "MEDIUM"

    def test_medium_at_zero(self):
        v = WorkHourValidator()
        assert v.calculate_violation_severity_level(0.0) == "MEDIUM"


class TestCreateViolationNotificationLevel:
    """Test create_violation_notification_level method."""

    def test_red_at_80(self):
        v = WorkHourValidator()
        assert v.create_violation_notification_level(80.0) == "red"

    def test_red_over_80(self):
        v = WorkHourValidator()
        assert v.create_violation_notification_level(85.0) == "red"

    def test_orange_at_78(self):
        v = WorkHourValidator()
        assert v.create_violation_notification_level(78.0) == "orange"

    def test_orange_at_79(self):
        v = WorkHourValidator()
        assert v.create_violation_notification_level(79.0) == "orange"

    def test_yellow_at_75(self):
        v = WorkHourValidator()
        assert v.create_violation_notification_level(75.0) == "yellow"

    def test_yellow_at_76(self):
        v = WorkHourValidator()
        assert v.create_violation_notification_level(76.0) == "yellow"

    def test_none_below_75(self):
        v = WorkHourValidator()
        assert v.create_violation_notification_level(70.0) is None

    def test_none_at_zero(self):
        v = WorkHourValidator()
        assert v.create_violation_notification_level(0.0) is None


# ==================== Exemption Eligibility Tests ====================


class TestCheckExemptionEligibility:
    """Test check_exemption_eligibility method."""

    def test_24_plus_4_eligible(self):
        v = WorkHourValidator()
        assert v.check_exemption_eligibility(PERSON, "24_plus_4") is True

    def test_80_hour_not_eligible(self):
        v = WorkHourValidator()
        assert v.check_exemption_eligibility(PERSON, "80_hour") is False

    def test_rest_period_not_eligible(self):
        v = WorkHourValidator()
        assert v.check_exemption_eligibility(PERSON, "rest_period") is False

    def test_moonlighting_not_eligible(self):
        v = WorkHourValidator()
        assert v.check_exemption_eligibility(PERSON, "moonlighting") is False


# ==================== BlockBasedWorkHourCalculator Tests ====================


class TestBlockBasedWorkHourCalculator:
    """Test BlockBasedWorkHourCalculator class."""

    def test_init(self):
        calc = BlockBasedWorkHourCalculator()
        assert calc.standard_hours == 6
        assert calc.intensive_hours == 12

    def test_empty_assignments(self):
        calc = BlockBasedWorkHourCalculator()
        result = calc.calculate_hours_from_assignments([])
        assert result == {}

    def test_single_standard_block(self):
        calc = BlockBasedWorkHourCalculator()
        assignments = [{"block_date": BASE_DATE, "rotation_id": "rot1"}]
        result = calc.calculate_hours_from_assignments(assignments)
        assert result[BASE_DATE] == 6.0

    def test_intensive_rotation(self):
        calc = BlockBasedWorkHourCalculator()
        assignments = [{"block_date": BASE_DATE, "rotation_id": "fmit"}]
        intensity_map = {"fmit": "intensive"}
        result = calc.calculate_hours_from_assignments(assignments, intensity_map)
        assert result[BASE_DATE] == 12.0

    def test_multiple_blocks_same_day(self):
        """Two standard blocks on same day -> 12h."""
        calc = BlockBasedWorkHourCalculator()
        assignments = [
            {"block_date": BASE_DATE, "rotation_id": "am"},
            {"block_date": BASE_DATE, "rotation_id": "pm"},
        ]
        result = calc.calculate_hours_from_assignments(assignments)
        assert result[BASE_DATE] == 12.0

    def test_mixed_intensity_same_day(self):
        """Standard + intensive on same day."""
        calc = BlockBasedWorkHourCalculator()
        assignments = [
            {"block_date": BASE_DATE, "rotation_id": "clinic"},
            {"block_date": BASE_DATE, "rotation_id": "fmit"},
        ]
        intensity_map = {"fmit": "intensive"}
        result = calc.calculate_hours_from_assignments(assignments, intensity_map)
        assert result[BASE_DATE] == 18.0  # 6 + 12

    def test_multiple_days(self):
        calc = BlockBasedWorkHourCalculator()
        dates = _dates(3)
        assignments = [{"block_date": d, "rotation_id": "clinic"} for d in dates]
        result = calc.calculate_hours_from_assignments(assignments)
        assert len(result) == 3
        for d in dates:
            assert result[d] == 6.0

    def test_missing_block_date_skipped(self):
        """Assignment without block_date is skipped."""
        calc = BlockBasedWorkHourCalculator()
        assignments = [
            {"rotation_id": "clinic"},  # Missing block_date
            {"block_date": BASE_DATE, "rotation_id": "clinic"},
        ]
        result = calc.calculate_hours_from_assignments(assignments)
        assert len(result) == 1
        assert result[BASE_DATE] == 6.0

    def test_unknown_rotation_defaults_standard(self):
        """Rotation not in intensity map -> standard hours."""
        calc = BlockBasedWorkHourCalculator()
        assignments = [{"block_date": BASE_DATE, "rotation_id": "unknown"}]
        intensity_map = {"fmit": "intensive"}
        result = calc.calculate_hours_from_assignments(assignments, intensity_map)
        assert result[BASE_DATE] == 6.0

    def test_none_intensity_map_defaults(self):
        """None intensity_map arg defaults to empty dict -> all standard."""
        calc = BlockBasedWorkHourCalculator()
        assignments = [{"block_date": BASE_DATE, "rotation_id": "fmit"}]
        result = calc.calculate_hours_from_assignments(assignments, None)
        assert result[BASE_DATE] == 6.0
