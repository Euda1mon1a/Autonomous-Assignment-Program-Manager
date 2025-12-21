"""Timezone-aware formatting utilities for display and serialization."""
from datetime import date, datetime, time, timezone
from typing import Optional, Union

from app.utils.timezone.converter import TimezoneConverter
from app.utils.timezone.detector import TimezoneDetector


class TimezoneFormatter:
    """
    Utility class for formatting datetimes with timezone awareness.

    Provides methods for:
    - Human-readable datetime formatting
    - ISO 8601 formatting
    - Relative time displays
    - Date range formatting
    """

    # Common format strings
    FORMAT_DATETIME_FULL = "%Y-%m-%d %H:%M:%S %Z"  # 2024-01-15 10:30:00 HST
    FORMAT_DATETIME_SHORT = "%Y-%m-%d %H:%M"  # 2024-01-15 10:30
    FORMAT_DATE_ONLY = "%Y-%m-%d"  # 2024-01-15
    FORMAT_TIME_ONLY = "%H:%M:%S"  # 10:30:00
    FORMAT_TIME_SHORT = "%H:%M"  # 10:30
    FORMAT_DISPLAY_FULL = "%B %d, %Y at %I:%M %p %Z"  # January 15, 2024 at 10:30 AM HST
    FORMAT_DISPLAY_SHORT = "%b %d, %Y %I:%M %p"  # Jan 15, 2024 10:30 AM

    @classmethod
    def format_datetime(
        cls,
        dt: datetime,
        tz_name: Optional[str] = None,
        format_string: Optional[str] = None,
        include_timezone: bool = True,
    ) -> str:
        """
        Format datetime for display.

        Args:
            dt: Datetime to format (naive or aware)
            tz_name: Target timezone (defaults to Pacific/Honolulu)
            format_string: Custom format string (defaults to full datetime)
            include_timezone: Whether to include timezone abbreviation

        Returns:
            str: Formatted datetime string

        Example:
            >>> dt = datetime(2024, 1, 15, 20, 0, tzinfo=timezone.utc)
            >>> formatted = TimezoneFormatter.format_datetime(dt)
            >>> # Returns "2024-01-15 10:00:00 HST"
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE
        format_string = format_string or (
            cls.FORMAT_DATETIME_FULL if include_timezone else cls.FORMAT_DATETIME_SHORT
        )

        # Convert to target timezone
        if dt.tzinfo is None:
            local_dt = TimezoneConverter.make_aware(dt, tz_name)
        else:
            local_dt = TimezoneConverter.utc_to_local(dt, tz_name)

        return local_dt.strftime(format_string)

    @classmethod
    def format_date(
        cls,
        d: Union[date, datetime],
        format_string: Optional[str] = None,
    ) -> str:
        """
        Format date for display.

        Args:
            d: Date or datetime to format
            format_string: Custom format string (defaults to YYYY-MM-DD)

        Returns:
            str: Formatted date string

        Example:
            >>> d = date(2024, 1, 15)
            >>> formatted = TimezoneFormatter.format_date(d)
            >>> formatted
            '2024-01-15'
        """
        format_string = format_string or cls.FORMAT_DATE_ONLY

        if isinstance(d, datetime):
            d = d.date()

        return d.strftime(format_string)

    @classmethod
    def format_time(
        cls,
        t: Union[time, datetime],
        format_string: Optional[str] = None,
        include_seconds: bool = False,
    ) -> str:
        """
        Format time for display.

        Args:
            t: Time or datetime to format
            format_string: Custom format string
            include_seconds: Whether to include seconds

        Returns:
            str: Formatted time string

        Example:
            >>> t = time(14, 30, 0)
            >>> formatted = TimezoneFormatter.format_time(t)
            >>> formatted
            '14:30'
        """
        if format_string is None:
            format_string = (
                cls.FORMAT_TIME_ONLY if include_seconds else cls.FORMAT_TIME_SHORT
            )

        if isinstance(t, datetime):
            t = t.time()

        return t.strftime(format_string)

    @classmethod
    def format_iso8601(
        cls,
        dt: datetime,
        tz_name: Optional[str] = None,
        utc: bool = False,
    ) -> str:
        """
        Format datetime as ISO 8601 string.

        Args:
            dt: Datetime to format
            tz_name: Target timezone (defaults to Pacific/Honolulu)
            utc: If True, convert to UTC; if False, use tz_name

        Returns:
            str: ISO 8601 formatted string

        Example:
            >>> dt = datetime(2024, 1, 15, 10, 0)
            >>> iso = TimezoneFormatter.format_iso8601(dt, utc=True)
            >>> # Returns "2024-01-15T20:00:00+00:00"
        """
        if utc:
            # Convert to UTC
            if dt.tzinfo is None:
                tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE
                dt_utc = TimezoneConverter.local_to_utc(dt, tz_name)
            else:
                dt_utc = dt.astimezone(timezone.utc)
            return dt_utc.isoformat()
        else:
            # Convert to target timezone
            tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE
            if dt.tzinfo is None:
                local_dt = TimezoneConverter.make_aware(dt, tz_name)
            else:
                local_dt = TimezoneConverter.utc_to_local(dt, tz_name)
            return local_dt.isoformat()

    @classmethod
    def format_relative(
        cls,
        dt: datetime,
        reference: Optional[datetime] = None,
        tz_name: Optional[str] = None,
    ) -> str:
        """
        Format datetime as relative time (e.g., "2 hours ago", "in 3 days").

        Args:
            dt: Datetime to format
            reference: Reference datetime (defaults to now)
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            str: Relative time string

        Example:
            >>> past = datetime.now() - timedelta(hours=2)
            >>> relative = TimezoneFormatter.format_relative(past)
            >>> relative
            '2 hours ago'
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE

        # Get reference time
        if reference is None:
            reference = TimezoneConverter.now_utc()

        # Normalize both to UTC
        if dt.tzinfo is None:
            dt = TimezoneConverter.local_to_utc(dt, tz_name)
        else:
            dt = dt.astimezone(timezone.utc)

        if reference.tzinfo is None:
            reference = TimezoneConverter.local_to_utc(reference, tz_name)
        else:
            reference = reference.astimezone(timezone.utc)

        # Calculate difference
        delta = reference - dt
        seconds = delta.total_seconds()

        # Determine if past or future
        if seconds > 0:
            suffix = "ago"
        else:
            suffix = "from now"
            seconds = abs(seconds)

        # Format based on magnitude
        if seconds < 60:
            return f"{int(seconds)} seconds {suffix}"
        elif seconds < 3600:  # Less than 1 hour
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} {suffix}"
        elif seconds < 86400:  # Less than 1 day
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"
        elif seconds < 604800:  # Less than 1 week
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} {suffix}"
        elif seconds < 2592000:  # Less than 30 days
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} {suffix}"
        elif seconds < 31536000:  # Less than 1 year
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} {suffix}"
        else:
            years = int(seconds / 31536000)
            return f"{years} year{'s' if years != 1 else ''} {suffix}"

    @classmethod
    def format_date_range(
        cls,
        start: Union[date, datetime],
        end: Union[date, datetime],
        include_time: bool = False,
        tz_name: Optional[str] = None,
    ) -> str:
        """
        Format a date range for display.

        Args:
            start: Start date/datetime
            end: End date/datetime
            include_time: Whether to include time
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            str: Formatted date range string

        Example:
            >>> start = date(2024, 1, 15)
            >>> end = date(2024, 1, 19)
            >>> formatted = TimezoneFormatter.format_date_range(start, end)
            >>> # Returns "January 15 - 19, 2024"
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE

        # Convert datetime to date if not including time
        if not include_time:
            if isinstance(start, datetime):
                start = start.date()
            if isinstance(end, datetime):
                end = end.date()

        # Same day
        if isinstance(start, date) and isinstance(end, date) and start == end:
            return cls.format_date(start, "%B %d, %Y")

        # Same month and year
        if (
            isinstance(start, date)
            and isinstance(end, date)
            and start.year == end.year
            and start.month == end.month
        ):
            return f"{start.strftime('%B')} {start.day} - {end.day}, {start.year}"

        # Same year
        if isinstance(start, date) and isinstance(end, date) and start.year == end.year:
            return (
                f"{start.strftime('%B %d')} - {end.strftime('%B %d')}, {start.year}"
            )

        # Different years or include time
        if include_time and isinstance(start, datetime) and isinstance(end, datetime):
            start_str = cls.format_datetime(start, tz_name, cls.FORMAT_DISPLAY_SHORT)
            end_str = cls.format_datetime(end, tz_name, cls.FORMAT_DISPLAY_SHORT)
            return f"{start_str} - {end_str}"
        else:
            start_str = cls.format_date(start, "%B %d, %Y")
            end_str = cls.format_date(end, "%B %d, %Y")
            return f"{start_str} - {end_str}"

    @classmethod
    def format_for_user(
        cls,
        dt: datetime,
        user_tz: Optional[str] = None,
        style: str = "full",
    ) -> str:
        """
        Format datetime for user display based on their timezone preference.

        Args:
            dt: Datetime to format
            user_tz: User's timezone preference
            style: Format style ("full", "short", "relative", "iso")

        Returns:
            str: Formatted datetime string

        Example:
            >>> dt = datetime(2024, 1, 15, 20, 0, tzinfo=timezone.utc)
            >>> formatted = TimezoneFormatter.format_for_user(
            ...     dt, user_tz="America/New_York", style="full"
            ... )
            >>> # Returns "January 15, 2024 at 03:00 PM EST"
        """
        user_tz = user_tz or TimezoneConverter.DEFAULT_TIMEZONE

        if style == "full":
            return cls.format_datetime(dt, user_tz, cls.FORMAT_DISPLAY_FULL)
        elif style == "short":
            return cls.format_datetime(dt, user_tz, cls.FORMAT_DISPLAY_SHORT)
        elif style == "relative":
            return cls.format_relative(dt, tz_name=user_tz)
        elif style == "iso":
            return cls.format_iso8601(dt, user_tz)
        else:
            return cls.format_datetime(dt, user_tz)

    @classmethod
    def format_timezone_info(cls, tz_name: str) -> str:
        """
        Format timezone information for display.

        Args:
            tz_name: Timezone name

        Returns:
            str: Formatted timezone info string

        Example:
            >>> info = TimezoneFormatter.format_timezone_info("Pacific/Honolulu")
            >>> # Returns "Pacific/Honolulu (HST, UTC-10:00)"
        """
        try:
            info = TimezoneDetector.get_timezone_info(tz_name)
            return (
                f"{info['name']} ({info['abbreviation']}, "
                f"{info['utc_offset_string']})"
            )
        except Exception:
            return tz_name

    @classmethod
    def format_block_time(
        cls,
        block_date: date,
        time_of_day: str,
        tz_name: Optional[str] = None,
        include_date: bool = True,
    ) -> str:
        """
        Format a clinic block time for display.

        Args:
            block_date: Date of the block
            time_of_day: "AM" or "PM"
            tz_name: Timezone name (defaults to Pacific/Honolulu)
            include_date: Whether to include the date

        Returns:
            str: Formatted block time string

        Example:
            >>> formatted = TimezoneFormatter.format_block_time(
            ...     date(2024, 1, 15), "AM"
            ... )
            >>> # Returns "January 15, 2024 - AM (8:00 AM - 12:00 PM)"
        """
        time_ranges = {
            "AM": "8:00 AM - 12:00 PM",
            "PM": "1:00 PM - 5:00 PM",
        }

        time_range = time_ranges.get(time_of_day.upper(), "Unknown")

        if include_date:
            date_str = cls.format_date(block_date, "%B %d, %Y")
            return f"{date_str} - {time_of_day.upper()} ({time_range})"
        else:
            return f"{time_of_day.upper()} ({time_range})"

    @classmethod
    def format_duration(cls, seconds: float, precise: bool = False) -> str:
        """
        Format a duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds
            precise: If True, show all components; if False, show largest unit

        Returns:
            str: Formatted duration string

        Example:
            >>> duration = TimezoneFormatter.format_duration(3665)
            >>> duration
            '1 hour, 1 minute, 5 seconds'
            >>> duration = TimezoneFormatter.format_duration(3665, precise=False)
            >>> duration
            '1 hour'
        """
        if seconds < 0:
            return "0 seconds"

        components = []

        # Years
        years = int(seconds // 31536000)
        if years > 0:
            components.append(f"{years} year{'s' if years != 1 else ''}")
            seconds %= 31536000

        # Days
        days = int(seconds // 86400)
        if days > 0:
            components.append(f"{days} day{'s' if days != 1 else ''}")
            seconds %= 86400

        # Hours
        hours = int(seconds // 3600)
        if hours > 0:
            components.append(f"{hours} hour{'s' if hours != 1 else ''}")
            seconds %= 3600

        # Minutes
        minutes = int(seconds // 60)
        if minutes > 0:
            components.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            seconds %= 60

        # Seconds
        if seconds > 0 or not components:
            components.append(f"{int(seconds)} second{'s' if seconds != 1 else ''}")

        if not precise and components:
            return components[0]

        return ", ".join(components)

    @classmethod
    def format_api_response(
        cls,
        dt: datetime,
        tz_name: Optional[str] = None,
        include_offset: bool = True,
    ) -> dict:
        """
        Format datetime for API response (multiple formats).

        Args:
            dt: Datetime to format
            tz_name: Timezone name (defaults to Pacific/Honolulu)
            include_offset: Whether to include UTC offset info

        Returns:
            dict: Multiple formatted representations

        Example:
            >>> dt = datetime(2024, 1, 15, 10, 0)
            >>> response = TimezoneFormatter.format_api_response(dt)
            >>> response.keys()
            dict_keys(['iso8601', 'display', 'timestamp', 'timezone', ...])
        """
        tz_name = tz_name or TimezoneConverter.DEFAULT_TIMEZONE

        # Ensure datetime is aware
        if dt.tzinfo is None:
            dt = TimezoneConverter.make_aware(dt, tz_name)
        else:
            dt = TimezoneConverter.utc_to_local(dt, tz_name)

        result = {
            "iso8601": cls.format_iso8601(dt, tz_name),
            "iso8601_utc": cls.format_iso8601(dt, utc=True),
            "display": cls.format_datetime(dt, tz_name, cls.FORMAT_DISPLAY_FULL),
            "display_short": cls.format_datetime(dt, tz_name, cls.FORMAT_DISPLAY_SHORT),
            "timestamp": int(dt.timestamp()),
            "timezone": tz_name,
        }

        if include_offset:
            info = TimezoneDetector.get_timezone_info(tz_name)
            result["utc_offset"] = info["utc_offset_string"]
            result["utc_offset_hours"] = info["utc_offset_hours"]

        return result
