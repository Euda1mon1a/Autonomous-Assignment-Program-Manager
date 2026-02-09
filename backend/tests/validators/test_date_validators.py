"""Tests for date validators (pure logic, no DB)."""

from datetime import date, datetime, timedelta

import pytest

from app.validators.common import ValidationError
from app.validators.date_validators import (
    validate_date_not_null,
    validate_date_range,
    validate_date_in_range,
    validate_academic_year_date,
    validate_academic_year_dates,
    validate_block_date,
    validate_acgme_work_period,
    validate_future_date,
    validate_past_date,
    validate_time_between_dates,
    validate_week_number,
    validate_session_time,
)


# ── validate_date_not_null ──────────────────────────────────────────────


class TestValidateDateNotNull:
    def test_date_passes(self):
        d = date(2026, 1, 15)
        assert validate_date_not_null(d) == d

    def test_datetime_converted(self):
        dt = datetime(2026, 1, 15, 10, 30)
        result = validate_date_not_null(dt)
        assert result == date(2026, 1, 15)
        assert isinstance(result, date)

    def test_none_rejected(self):
        with pytest.raises(ValidationError, match="null"):
            validate_date_not_null(None)

    def test_wrong_type(self):
        with pytest.raises(ValidationError, match="date"):
            validate_date_not_null("2026-01-15")

    def test_custom_field_name(self):
        with pytest.raises(ValidationError, match="Start date"):
            validate_date_not_null(None, field_name="Start date")


# ── validate_date_range ─────────────────────────────────────────────────


class TestValidateDateRange:
    def test_valid_range(self):
        start, end = validate_date_range(date(2026, 1, 1), date(2026, 1, 31))
        assert start == date(2026, 1, 1)
        assert end == date(2026, 1, 31)

    def test_same_day_allowed(self):
        start, end = validate_date_range(
            date(2026, 1, 1), date(2026, 1, 1), allow_same_day=True
        )
        assert start == end

    def test_same_day_rejected(self):
        with pytest.raises(ValidationError, match="same"):
            validate_date_range(
                date(2026, 1, 1), date(2026, 1, 1), allow_same_day=False
            )

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="before"):
            validate_date_range(date(2026, 2, 1), date(2026, 1, 1))

    def test_max_days_ok(self):
        start, end = validate_date_range(date(2026, 1, 1), date(2026, 1, 8), max_days=7)
        assert (end - start).days == 7

    def test_max_days_exceeded(self):
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_date_range(date(2026, 1, 1), date(2026, 1, 9), max_days=7)

    def test_datetime_converted(self):
        start, end = validate_date_range(
            datetime(2026, 1, 1, 8, 0), datetime(2026, 1, 31, 17, 0)
        )
        assert isinstance(start, date)
        assert isinstance(end, date)


# ── validate_date_in_range ──────────────────────────────────────────────


class TestValidateDateInRange:
    def test_within_range(self):
        result = validate_date_in_range(
            date(2026, 1, 15), date(2026, 1, 1), date(2026, 1, 31)
        )
        assert result == date(2026, 1, 15)

    def test_at_start(self):
        result = validate_date_in_range(
            date(2026, 1, 1), date(2026, 1, 1), date(2026, 1, 31)
        )
        assert result == date(2026, 1, 1)

    def test_at_end(self):
        result = validate_date_in_range(
            date(2026, 1, 31), date(2026, 1, 1), date(2026, 1, 31)
        )
        assert result == date(2026, 1, 31)

    def test_before_range(self):
        with pytest.raises(ValidationError, match="between"):
            validate_date_in_range(
                date(2025, 12, 31), date(2026, 1, 1), date(2026, 1, 31)
            )

    def test_after_range(self):
        with pytest.raises(ValidationError, match="between"):
            validate_date_in_range(
                date(2026, 2, 1), date(2026, 1, 1), date(2026, 1, 31)
            )


# ── validate_academic_year_date ─────────────────────────────────────────


class TestValidateAcademicYearDate:
    def test_today_valid(self):
        assert validate_academic_year_date(date.today()) == date.today()

    def test_within_5_years_future(self):
        d = date.today() + timedelta(days=365 * 4)
        assert validate_academic_year_date(d) == d

    def test_within_5_years_past(self):
        d = date.today() - timedelta(days=365 * 4)
        assert validate_academic_year_date(d) == d

    def test_over_5_years_future(self):
        d = date.today() + timedelta(days=365 * 6)
        with pytest.raises(ValidationError, match="future"):
            validate_academic_year_date(d)

    def test_over_5_years_past(self):
        d = date.today() - timedelta(days=365 * 6)
        with pytest.raises(ValidationError, match="past"):
            validate_academic_year_date(d)

    def test_none_rejected(self):
        with pytest.raises(ValidationError):
            validate_academic_year_date(None)


# ── validate_academic_year_dates ────────────────────────────────────────


class TestValidateAcademicYearDates:
    def test_365_days(self):
        start, end = validate_academic_year_dates(date(2025, 7, 1), date(2026, 6, 30))
        assert start == date(2025, 7, 1)
        assert end == date(2026, 6, 30)

    def test_366_days_leap(self):
        # 2024 is a leap year: July 1 2023 to June 30 2024 = 366 days
        start, end = validate_academic_year_dates(date(2023, 7, 1), date(2024, 6, 30))
        assert start == date(2023, 7, 1)

    def test_too_short(self):
        with pytest.raises(ValidationError, match="365 or 366"):
            validate_academic_year_dates(date(2026, 1, 1), date(2026, 6, 30))

    def test_too_long(self):
        with pytest.raises(ValidationError, match="365 or 366"):
            validate_academic_year_dates(date(2025, 1, 1), date(2026, 6, 30))

    def test_same_day_rejected(self):
        with pytest.raises(ValidationError, match="same"):
            validate_academic_year_dates(date(2026, 1, 1), date(2026, 1, 1))


# ── validate_block_date ─────────────────────────────────────────────────


class TestValidateBlockDate:
    def test_today_valid(self):
        assert validate_block_date(date.today()) == date.today()

    def test_over_5_years_past(self):
        d = date.today() - timedelta(days=365 * 6)
        with pytest.raises(ValidationError, match="past"):
            validate_block_date(d)

    def test_over_5_years_future(self):
        d = date.today() + timedelta(days=365 * 6)
        with pytest.raises(ValidationError, match="future"):
            validate_block_date(d)

    def test_none_rejected(self):
        with pytest.raises(ValidationError):
            validate_block_date(None)


# ── validate_acgme_work_period ──────────────────────────────────────────


class TestValidateAcgmeWorkPeriod:
    def test_single_day(self):
        start, end = validate_acgme_work_period(date(2026, 1, 15), date(2026, 1, 15))
        assert start == end

    def test_7_day_period(self):
        start, end = validate_acgme_work_period(date(2026, 1, 1), date(2026, 1, 7))
        assert (end - start).days == 6

    def test_28_day_period(self):
        start, end = validate_acgme_work_period(date(2026, 1, 1), date(2026, 1, 28))
        assert (end - start).days == 27

    def test_exceeds_28_days(self):
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_acgme_work_period(date(2026, 1, 1), date(2026, 1, 30))

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="before"):
            validate_acgme_work_period(date(2026, 2, 1), date(2026, 1, 1))


# ── validate_future_date ────────────────────────────────────────────────


class TestValidateFutureDate:
    def test_tomorrow_ok(self):
        d = date.today() + timedelta(days=1)
        assert validate_future_date(d) == d

    def test_today_allowed_by_default(self):
        assert validate_future_date(date.today()) == date.today()

    def test_today_rejected_strict(self):
        with pytest.raises(ValidationError, match="future"):
            validate_future_date(date.today(), allow_today=False)

    def test_past_rejected(self):
        d = date.today() - timedelta(days=1)
        with pytest.raises(ValidationError, match="past"):
            validate_future_date(d)


# ── validate_past_date ──────────────────────────────────────────────────


class TestValidatePastDate:
    def test_yesterday_ok(self):
        d = date.today() - timedelta(days=1)
        assert validate_past_date(d) == d

    def test_today_allowed_by_default(self):
        assert validate_past_date(date.today()) == date.today()

    def test_today_rejected_strict(self):
        with pytest.raises(ValidationError, match="past"):
            validate_past_date(date.today(), allow_today=False)

    def test_future_rejected(self):
        d = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError, match="future"):
            validate_past_date(d)


# ── validate_time_between_dates ─────────────────────────────────────────


class TestValidateTimeBetweenDates:
    def test_date_objects(self):
        delta = validate_time_between_dates(date(2026, 1, 1), date(2026, 1, 2))
        assert delta.days == 1

    def test_datetime_objects(self):
        delta = validate_time_between_dates(
            datetime(2026, 1, 1, 8, 0), datetime(2026, 1, 1, 20, 0)
        )
        assert delta.total_seconds() == 12 * 3600

    def test_min_hours_ok(self):
        delta = validate_time_between_dates(
            datetime(2026, 1, 1, 8, 0),
            datetime(2026, 1, 1, 20, 0),
            min_hours=8,
        )
        assert delta.total_seconds() == 12 * 3600

    def test_min_hours_violated(self):
        with pytest.raises(ValidationError, match="less than minimum"):
            validate_time_between_dates(
                datetime(2026, 1, 1, 8, 0),
                datetime(2026, 1, 1, 10, 0),
                min_hours=8,
            )

    def test_max_hours_ok(self):
        validate_time_between_dates(
            datetime(2026, 1, 1, 8, 0),
            datetime(2026, 1, 1, 16, 0),
            max_hours=24,
        )

    def test_max_hours_violated(self):
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_time_between_dates(
                datetime(2026, 1, 1, 8, 0),
                datetime(2026, 1, 3, 8, 0),
                max_hours=24,
            )


# ── validate_week_number ────────────────────────────────────────────────


class TestValidateWeekNumber:
    def test_valid_week(self):
        assert validate_week_number(1) == 1

    def test_week_53(self):
        assert validate_week_number(53) == 53

    def test_below_min(self):
        with pytest.raises(ValidationError, match="between 1 and 53"):
            validate_week_number(0)

    def test_above_max(self):
        with pytest.raises(ValidationError, match="between 1 and 53"):
            validate_week_number(54)

    def test_not_integer(self):
        with pytest.raises(ValidationError, match="integer"):
            validate_week_number("1")

    def test_year_with_52_weeks(self):
        # 2026 has 53 weeks in ISO calendar? Let's just test a known year
        # Most years have 52 weeks; some have 53
        # Use validate with a year that has only 52 weeks
        # 2026 starts on Thursday, so it has 53 weeks
        # 2025 starts on Wednesday — also 52 weeks
        # Let's test week 53 for a year that only has 52 weeks
        last_week_2025 = date(2025, 12, 28).isocalendar()[1]
        if last_week_2025 < 53:
            with pytest.raises(ValidationError, match="does not exist"):
                validate_week_number(53, year=2025)


# ── validate_session_time ───────────────────────────────────────────────


class TestValidateSessionTime:
    def test_am(self):
        assert validate_session_time("AM") == "AM"

    def test_pm(self):
        assert validate_session_time("PM") == "PM"

    def test_lowercase_am(self):
        assert validate_session_time("am") == "AM"

    def test_lowercase_pm(self):
        assert validate_session_time("pm") == "PM"

    def test_with_whitespace(self):
        assert validate_session_time("  am  ") == "AM"

    def test_empty(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_session_time("")

    def test_invalid(self):
        with pytest.raises(ValidationError, match="AM.*PM"):
            validate_session_time("NOON")
