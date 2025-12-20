"""Timezone-aware scheduling utilities for business hours and date calculations."""
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from app.utils.timezone.converter import TimezoneConverter


class TimezoneAwareScheduler:
    """
    Utility class for timezone-aware scheduling operations.

    Provides methods for:
    - Business hours calculations
    - Date range generation
    - Work schedule normalization
    - Cross-timezone meeting scheduling
    """

    # Default business hours (24-hour format)
    DEFAULT_BUSINESS_START = time(8, 0)  # 8:00 AM
    DEFAULT_BUSINESS_END = time(17, 0)  # 5:00 PM

    # Medical facility typical hours
    CLINIC_HOURS_AM_START = time(8, 0)  # 8:00 AM
    CLINIC_HOURS_AM_END = time(12, 0)  # 12:00 PM (noon)
    CLINIC_HOURS_PM_START = time(13, 0)  # 1:00 PM
    CLINIC_HOURS_PM_END = time(17, 0)  # 5:00 PM

    @classmethod
    def is_business_hours(
        cls,
        dt: datetime,
        tz_name: Optional[str] = None,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        include_weekends: bool = False,
    ) -> bool:
        """
        Check if a datetime falls within business hours.

        Args:
            dt: Datetime to check (naive or aware)
            tz_name: Timezone name (defaults to Pacific/Honolulu)
            start_time: Business start time (defaults to 8:00 AM)
            end_time: Business end time (defaults to 5:00 PM)
            include_weekends: Whether to include weekends

        Returns:
            bool: True if within business hours

        Example:
            >>> dt = datetime(2024, 1, 15, 10, 0)  # Monday 10 AM
            >>> TimezoneAwareScheduler.is_business_hours(dt)
            True
            >>> dt = datetime(2024, 1, 15, 18, 0)  # Monday 6 PM
            >>> TimezoneAwareScheduler.is_business_hours(dt)
            False
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE
        start_time = start_time or cls.DEFAULT_BUSINESS_START
        end_time = end_time or cls.DEFAULT_BUSINESS_END

        # Convert to local timezone
        if dt.tzinfo is None:
            local_dt = TimezoneConverter.make_aware(dt, tz_name)
        else:
            local_dt = TimezoneConverter.convert_between_timezones(
                dt, dt.tzinfo.key if hasattr(dt.tzinfo, "key") else "UTC", tz_name
            )

        # Check weekday
        if not include_weekends and local_dt.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        # Check time of day
        current_time = local_dt.time()
        return start_time <= current_time <= end_time

    @classmethod
    def get_next_business_day(
        cls,
        reference_date: date,
        tz_name: Optional[str] = None,
        include_weekends: bool = False,
    ) -> date:
        """
        Get the next business day after a reference date.

        Args:
            reference_date: Starting date
            tz_name: Timezone name (for holiday calculations)
            include_weekends: Whether weekends are business days

        Returns:
            date: Next business day

        Example:
            >>> # Friday
            >>> friday = date(2024, 1, 19)
            >>> next_day = TimezoneAwareScheduler.get_next_business_day(friday)
            >>> # Returns Monday (skips weekend)
            >>> next_day == date(2024, 1, 22)
            True
        """
        next_day = reference_date + timedelta(days=1)

        # Skip weekends if not included
        if not include_weekends:
            while next_day.weekday() >= 5:  # Saturday or Sunday
                next_day += timedelta(days=1)

        return next_day

    @classmethod
    def get_business_days_between(
        cls,
        start_date: date,
        end_date: date,
        include_weekends: bool = False,
    ) -> int:
        """
        Calculate number of business days between two dates.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            include_weekends: Whether to include weekends

        Returns:
            int: Number of business days

        Example:
            >>> start = date(2024, 1, 15)  # Monday
            >>> end = date(2024, 1, 19)  # Friday
            >>> days = TimezoneAwareScheduler.get_business_days_between(
            ...     start, end
            ... )
            >>> days
            5
        """
        if start_date > end_date:
            return 0

        if include_weekends:
            return (end_date - start_date).days + 1

        business_days = 0
        current = start_date

        while current <= end_date:
            if current.weekday() < 5:  # Monday=0, Friday=4
                business_days += 1
            current += timedelta(days=1)

        return business_days

    @classmethod
    def generate_date_range(
        cls,
        start_date: date,
        end_date: date,
        include_weekends: bool = True,
    ) -> list[date]:
        """
        Generate list of dates between start and end.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            include_weekends: Whether to include weekends

        Returns:
            list[date]: List of dates

        Example:
            >>> start = date(2024, 1, 15)
            >>> end = date(2024, 1, 17)
            >>> dates = TimezoneAwareScheduler.generate_date_range(
            ...     start, end
            ... )
            >>> len(dates)
            3
        """
        dates = []
        current = start_date

        while current <= end_date:
            if include_weekends or current.weekday() < 5:
                dates.append(current)
            current += timedelta(days=1)

        return dates

    @classmethod
    def is_clinic_am_block(cls, dt: datetime, tz_name: Optional[str] = None) -> bool:
        """
        Check if datetime falls in AM clinic block (8 AM - 12 PM).

        Args:
            dt: Datetime to check
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            bool: True if in AM block

        Example:
            >>> dt = datetime(2024, 1, 15, 10, 0)  # 10 AM
            >>> TimezoneAwareScheduler.is_clinic_am_block(dt)
            True
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE

        # Convert to local timezone
        if dt.tzinfo is None:
            local_dt = TimezoneConverter.make_aware(dt, tz_name)
        else:
            local_dt = TimezoneConverter.convert_between_timezones(
                dt, dt.tzinfo.key if hasattr(dt.tzinfo, "key") else "UTC", tz_name
            )

        current_time = local_dt.time()
        return cls.CLINIC_HOURS_AM_START <= current_time < cls.CLINIC_HOURS_AM_END

    @classmethod
    def is_clinic_pm_block(cls, dt: datetime, tz_name: Optional[str] = None) -> bool:
        """
        Check if datetime falls in PM clinic block (1 PM - 5 PM).

        Args:
            dt: Datetime to check
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            bool: True if in PM block

        Example:
            >>> dt = datetime(2024, 1, 15, 14, 0)  # 2 PM
            >>> TimezoneAwareScheduler.is_clinic_pm_block(dt)
            True
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE

        # Convert to local timezone
        if dt.tzinfo is None:
            local_dt = TimezoneConverter.make_aware(dt, tz_name)
        else:
            local_dt = TimezoneConverter.convert_between_timezones(
                dt, dt.tzinfo.key if hasattr(dt.tzinfo, "key") else "UTC", tz_name
            )

        current_time = local_dt.time()
        return cls.CLINIC_HOURS_PM_START <= current_time < cls.CLINIC_HOURS_PM_END

    @classmethod
    def get_block_start_end(
        cls,
        block_date: date,
        time_of_day: str,
        tz_name: Optional[str] = None,
    ) -> tuple[datetime, datetime]:
        """
        Get start and end datetime for a clinic block.

        Args:
            block_date: Date of the block
            time_of_day: "AM" or "PM"
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            tuple[datetime, datetime]: Start and end times (timezone-aware)

        Example:
            >>> start, end = TimezoneAwareScheduler.get_block_start_end(
            ...     date(2024, 1, 15), "AM"
            ... )
            >>> start.hour
            8
            >>> end.hour
            12
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE
        tz = ZoneInfo(tz_name)

        if time_of_day.upper() == "AM":
            start = datetime.combine(block_date, cls.CLINIC_HOURS_AM_START, tzinfo=tz)
            end = datetime.combine(block_date, cls.CLINIC_HOURS_AM_END, tzinfo=tz)
        else:  # PM
            start = datetime.combine(block_date, cls.CLINIC_HOURS_PM_START, tzinfo=tz)
            end = datetime.combine(block_date, cls.CLINIC_HOURS_PM_END, tzinfo=tz)

        return start, end

    @classmethod
    def normalize_to_business_hours(
        cls,
        dt: datetime,
        tz_name: Optional[str] = None,
        direction: str = "next",
    ) -> datetime:
        """
        Normalize a datetime to business hours.

        If datetime is outside business hours, moves it to the start/end
        of business hours.

        Args:
            dt: Datetime to normalize
            tz_name: Timezone name (defaults to Pacific/Honolulu)
            direction: "next" (round up) or "previous" (round down)

        Returns:
            datetime: Normalized datetime

        Example:
            >>> # 6 PM (after business hours)
            >>> dt = datetime(2024, 1, 15, 18, 0)
            >>> normalized = TimezoneAwareScheduler.normalize_to_business_hours(
            ...     dt, direction="next"
            ... )
            >>> # Returns 8 AM next business day
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE

        # Convert to local timezone
        if dt.tzinfo is None:
            local_dt = TimezoneConverter.make_aware(dt, tz_name)
        else:
            local_dt = TimezoneConverter.convert_between_timezones(
                dt, dt.tzinfo.key if hasattr(dt.tzinfo, "key") else "UTC", tz_name
            )

        # If weekend, move to next/previous weekday
        if local_dt.weekday() >= 5:
            if direction == "next":
                # Move to Monday
                days_ahead = 7 - local_dt.weekday()
                local_dt = local_dt + timedelta(days=days_ahead)
                local_dt = local_dt.replace(
                    hour=cls.DEFAULT_BUSINESS_START.hour,
                    minute=cls.DEFAULT_BUSINESS_START.minute,
                    second=0,
                    microsecond=0,
                )
            else:
                # Move to Friday
                days_back = local_dt.weekday() - 4
                local_dt = local_dt - timedelta(days=days_back)
                local_dt = local_dt.replace(
                    hour=cls.DEFAULT_BUSINESS_END.hour,
                    minute=cls.DEFAULT_BUSINESS_END.minute,
                    second=0,
                    microsecond=0,
                )
            return local_dt

        # Check if before business hours
        if local_dt.time() < cls.DEFAULT_BUSINESS_START:
            local_dt = local_dt.replace(
                hour=cls.DEFAULT_BUSINESS_START.hour,
                minute=cls.DEFAULT_BUSINESS_START.minute,
                second=0,
                microsecond=0,
            )
        # Check if after business hours
        elif local_dt.time() > cls.DEFAULT_BUSINESS_END:
            if direction == "next":
                # Move to next business day start
                next_day = cls.get_next_business_day(local_dt.date())
                local_dt = datetime.combine(
                    next_day, cls.DEFAULT_BUSINESS_START, tzinfo=ZoneInfo(tz_name)
                )
            else:
                # Move to current day end
                local_dt = local_dt.replace(
                    hour=cls.DEFAULT_BUSINESS_END.hour,
                    minute=cls.DEFAULT_BUSINESS_END.minute,
                    second=0,
                    microsecond=0,
                )

        return local_dt

    @classmethod
    def find_overlapping_hours(
        cls,
        tz1: str,
        tz2: str,
        start_time1: Optional[time] = None,
        end_time1: Optional[time] = None,
        start_time2: Optional[time] = None,
        end_time2: Optional[time] = None,
    ) -> Optional[tuple[time, time]]:
        """
        Find overlapping business hours between two timezones.

        Useful for scheduling meetings across timezones.

        Args:
            tz1: First timezone name
            tz2: Second timezone name
            start_time1: Business start in tz1 (defaults to 8:00 AM)
            end_time1: Business end in tz1 (defaults to 5:00 PM)
            start_time2: Business start in tz2 (defaults to 8:00 AM)
            end_time2: Business end in tz2 (defaults to 5:00 PM)

        Returns:
            Optional[tuple[time, time]]: Overlapping hours in tz1, or None

        Example:
            >>> # Find overlap between Hawaii and New York business hours
            >>> overlap = TimezoneAwareScheduler.find_overlapping_hours(
            ...     "Pacific/Honolulu", "America/New_York"
            ... )
            >>> # Returns overlapping time range in Hawaii time
        """
        start_time1 = start_time1 or cls.DEFAULT_BUSINESS_START
        end_time1 = end_time1 or cls.DEFAULT_BUSINESS_END
        start_time2 = start_time2 or cls.DEFAULT_BUSINESS_START
        end_time2 = end_time2 or cls.DEFAULT_BUSINESS_END

        # Use today as reference
        ref_date = date.today()

        # Create datetime objects in each timezone
        dt1_start = datetime.combine(ref_date, start_time1, tzinfo=ZoneInfo(tz1))
        dt1_end = datetime.combine(ref_date, end_time1, tzinfo=ZoneInfo(tz1))
        dt2_start = datetime.combine(ref_date, start_time2, tzinfo=ZoneInfo(tz2))
        dt2_end = datetime.combine(ref_date, end_time2, tzinfo=ZoneInfo(tz2))

        # Convert tz2 times to tz1
        dt2_start_in_tz1 = dt2_start.astimezone(ZoneInfo(tz1))
        dt2_end_in_tz1 = dt2_end.astimezone(ZoneInfo(tz1))

        # Find overlap
        overlap_start = max(dt1_start, dt2_start_in_tz1)
        overlap_end = min(dt1_end, dt2_end_in_tz1)

        # Check if there's actual overlap
        if overlap_start >= overlap_end:
            return None

        return overlap_start.time(), overlap_end.time()

    @classmethod
    def calculate_hours_in_period(
        cls,
        start: datetime,
        end: datetime,
        tz_name: Optional[str] = None,
        business_hours_only: bool = False,
    ) -> float:
        """
        Calculate total hours in a time period.

        Args:
            start: Start datetime
            end: End datetime
            tz_name: Timezone name (for business hours calculation)
            business_hours_only: Count only business hours

        Returns:
            float: Total hours

        Example:
            >>> start = datetime(2024, 1, 15, 8, 0)
            >>> end = datetime(2024, 1, 15, 17, 0)
            >>> hours = TimezoneAwareScheduler.calculate_hours_in_period(
            ...     start, end
            ... )
            >>> hours
            9.0
        """
        if business_hours_only:
            # Complex calculation - count only business hours
            tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE

            # Normalize to UTC
            start_utc, end_utc = TimezoneConverter.normalize_datetime_range(
                start, end, tz_name
            )

            total_hours = 0.0
            current = start_utc

            # Iterate through each hour
            while current < end_utc:
                if cls.is_business_hours(current, tz_name):
                    # Add the fraction of this hour that's in range
                    hour_end = min(
                        current + timedelta(hours=1), end_utc
                    )
                    hours_in_segment = (hour_end - current).total_seconds() / 3600
                    total_hours += hours_in_segment

                current += timedelta(hours=1)

            return total_hours
        else:
            # Simple total hours
            return (end - start).total_seconds() / 3600
