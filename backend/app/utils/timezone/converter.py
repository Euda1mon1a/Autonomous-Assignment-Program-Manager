"""Timezone conversion utilities for UTC and local time handling."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class TimezoneConverter:
    """
    Utility class for timezone conversions.

    Handles conversions between UTC and local timezones, with special
    support for the default application timezone (Pacific/Honolulu).
    """

    # Default timezone for the application
    DEFAULT_TIMEZONE = "Pacific/Honolulu"

    @classmethod
    def get_timezone(cls, tz_name: str) -> ZoneInfo:
        """
        Get a ZoneInfo object for a timezone name.

        Args:
            tz_name: IANA timezone name (e.g., "Pacific/Honolulu", "America/New_York")

        Returns:
            ZoneInfo: Timezone object

        Raises:
            ValueError: If timezone name is invalid

        Example:
            >>> tz = TimezoneConverter.get_timezone("Pacific/Honolulu")
            >>> tz.key
            'Pacific/Honolulu'
        """
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as e:
            raise ValueError(f"Invalid timezone: {tz_name}") from e

    @classmethod
    def utc_to_local(
        cls,
        dt: datetime,
        tz_name: str | None = None,
    ) -> datetime:
        """
        Convert UTC datetime to local timezone.

        Args:
            dt: Datetime in UTC (naive or aware)
            tz_name: Target timezone name (defaults to Pacific/Honolulu)

        Returns:
            datetime: Datetime in local timezone (aware)

        Example:
            >>> utc_time = datetime(2024, 1, 15, 20, 0)  # 8 PM UTC
            >>> local = TimezoneConverter.utc_to_local(utc_time)
            >>> local.hour
            10  # 10 AM HST (UTC-10)
        """
        tz_name = tz_name or cls.DEFAULT_TIMEZONE
        target_tz = cls.get_timezone(tz_name)

        # Ensure datetime is UTC-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        elif dt.tzinfo != UTC:
            # Convert to UTC first if in different timezone
            dt = dt.astimezone(UTC)

        # Convert to target timezone
        return dt.astimezone(target_tz)

    @classmethod
    def local_to_utc(
        cls,
        dt: datetime,
        tz_name: str | None = None,
    ) -> datetime:
        """
        Convert local datetime to UTC.

        Args:
            dt: Datetime in local timezone (naive or aware)
            tz_name: Source timezone name (defaults to Pacific/Honolulu)

        Returns:
            datetime: Datetime in UTC (aware)

        Example:
            >>> local_time = datetime(2024, 1, 15, 10, 0)  # 10 AM HST
            >>> utc = TimezoneConverter.local_to_utc(local_time)
            >>> utc.hour
            20  # 8 PM UTC (HST+10)
        """
        tz_name = tz_name or cls.DEFAULT_TIMEZONE
        source_tz = cls.get_timezone(tz_name)

        # If naive, assume it's in the source timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=source_tz)
        elif dt.tzinfo != source_tz:
            # If already aware but in different timezone, convert to source first
            dt = dt.astimezone(source_tz)

        # Convert to UTC
        return dt.astimezone(UTC)

    @classmethod
    def convert_between_timezones(
        cls,
        dt: datetime,
        from_tz: str,
        to_tz: str,
    ) -> datetime:
        """
        Convert datetime from one timezone to another.

        Args:
            dt: Datetime to convert (naive or aware)
            from_tz: Source timezone name
            to_tz: Target timezone name

        Returns:
            datetime: Datetime in target timezone (aware)

        Example:
            >>> ny_time = datetime(2024, 1, 15, 15, 0)  # 3 PM Eastern
            >>> hawaii = TimezoneConverter.convert_between_timezones(
            ...     ny_time, "America/New_York", "Pacific/Honolulu"
            ... )
            >>> hawaii.hour
            10  # 10 AM HST
        """
        source_tz = cls.get_timezone(from_tz)
        target_tz = cls.get_timezone(to_tz)

        # Localize if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=source_tz)
        elif dt.tzinfo != source_tz:
            # Convert to source timezone first
            dt = dt.astimezone(source_tz)

        # Convert to target timezone
        return dt.astimezone(target_tz)

    @classmethod
    def now_utc(cls) -> datetime:
        """
        Get current UTC datetime (aware).

        Returns:
            datetime: Current time in UTC

        Example:
            >>> now = TimezoneConverter.now_utc()
            >>> now.tzinfo == timezone.utc
            True
        """
        return datetime.now(UTC)

    @classmethod
    def now_local(cls, tz_name: str | None = None) -> datetime:
        """
        Get current local datetime (aware).

        Args:
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            datetime: Current time in local timezone

        Example:
            >>> local = TimezoneConverter.now_local()
            >>> local.tzinfo.key
            'Pacific/Honolulu'
        """
        tz_name = tz_name or cls.DEFAULT_TIMEZONE
        tz = cls.get_timezone(tz_name)
        return datetime.now(tz)

    @classmethod
    def make_aware(
        cls,
        dt: datetime,
        tz_name: str | None = None,
        is_dst: bool | None = None,
    ) -> datetime:
        """
        Make a naive datetime timezone-aware.

        Args:
            dt: Naive datetime
            tz_name: Timezone name (defaults to Pacific/Honolulu)
            is_dst: DST flag (None=auto, True=DST, False=standard).
                   Only relevant for timezones with DST during ambiguous times.

        Returns:
            datetime: Timezone-aware datetime

        Raises:
            ValueError: If datetime is already aware

        Example:
            >>> naive = datetime(2024, 1, 15, 10, 0)
            >>> aware = TimezoneConverter.make_aware(naive)
            >>> aware.tzinfo.key
            'Pacific/Honolulu'
        """
        if dt.tzinfo is not None:
            raise ValueError("Datetime is already timezone-aware")

        tz_name = tz_name or cls.DEFAULT_TIMEZONE
        tz = cls.get_timezone(tz_name)

        # For timezones with DST, handle ambiguous times
        # ZoneInfo handles this automatically with fold parameter
        return dt.replace(tzinfo=tz)

    @classmethod
    def make_naive(
        cls,
        dt: datetime,
        target_tz: str | None = None,
    ) -> datetime:
        """
        Make a timezone-aware datetime naive.

        Converts to target timezone first, then removes timezone info.

        Args:
            dt: Timezone-aware datetime
            target_tz: Target timezone (defaults to Pacific/Honolulu)

        Returns:
            datetime: Naive datetime in target timezone

        Raises:
            ValueError: If datetime is already naive

        Example:
            >>> utc_time = datetime(2024, 1, 15, 20, 0, tzinfo=timezone.utc)
            >>> naive = TimezoneConverter.make_naive(utc_time)
            >>> naive.hour
            10  # 10 AM HST, naive
        """
        if dt.tzinfo is None:
            raise ValueError("Datetime is already naive")

        target_tz = target_tz or cls.DEFAULT_TIMEZONE

        # Convert to target timezone
        local_dt = cls.convert_between_timezones(
            dt,
            from_tz=dt.tzinfo.key if hasattr(dt.tzinfo, "key") else "UTC",
            to_tz=target_tz,
        )

        # Remove timezone info
        return local_dt.replace(tzinfo=None)

    @classmethod
    def get_utc_offset(cls, tz_name: str, dt: datetime | None = None) -> timedelta:
        """
        Get UTC offset for a timezone at a specific datetime.

        Args:
            tz_name: Timezone name
            dt: Datetime to check (defaults to now)

        Returns:
            timedelta: UTC offset (e.g., -10 hours for HST)

        Example:
            >>> offset = TimezoneConverter.get_utc_offset("Pacific/Honolulu")
            >>> offset.total_seconds() / 3600
            -10.0  # HST is UTC-10
        """
        tz = cls.get_timezone(tz_name)
        dt = dt or datetime.now(tz)

        # Ensure datetime is aware in the target timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)

        return dt.utcoffset()

    @classmethod
    def is_dst(cls, dt: datetime, tz_name: str | None = None) -> bool:
        """
        Check if a datetime is in Daylight Saving Time.

        Args:
            dt: Datetime to check (naive or aware)
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            bool: True if DST is active, False otherwise

        Note:
            Pacific/Honolulu does not observe DST, so this always returns False
            for the default timezone.

        Example:
            >>> summer = datetime(2024, 7, 15, 12, 0)
            >>> TimezoneConverter.is_dst(summer, "America/New_York")
            True  # EDT is active in summer
            >>> TimezoneConverter.is_dst(summer, "Pacific/Honolulu")
            False  # Hawaii has no DST
        """
        tz_name = tz_name or cls.DEFAULT_TIMEZONE
        tz = cls.get_timezone(tz_name)

        # Make aware if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)

        # Check if DST offset is non-zero
        dst = dt.dst()
        return dst is not None and dst.total_seconds() != 0

    @classmethod
    def normalize_datetime_range(
        cls,
        start: datetime,
        end: datetime,
        tz_name: str | None = None,
    ) -> tuple[datetime, datetime]:
        """
        Normalize a datetime range to UTC.

        Ensures both datetimes are timezone-aware and in UTC.

        Args:
            start: Start datetime (naive or aware)
            end: End datetime (naive or aware)
            tz_name: Timezone for naive datetimes (defaults to Pacific/Honolulu)

        Returns:
            tuple[datetime, datetime]: Start and end in UTC (aware)

        Example:
            >>> start = datetime(2024, 1, 1, 0, 0)
            >>> end = datetime(2024, 1, 31, 23, 59)
            >>> utc_start, utc_end = TimezoneConverter.normalize_datetime_range(
            ...     start, end
            ... )
            >>> utc_start.tzinfo == timezone.utc
            True
        """
        tz_name = tz_name or cls.DEFAULT_TIMEZONE

        # Convert start to UTC
        if start.tzinfo is None:
            start = cls.local_to_utc(start, tz_name)
        else:
            start = start.astimezone(UTC)

        # Convert end to UTC
        if end.tzinfo is None:
            end = cls.local_to_utc(end, tz_name)
        else:
            end = end.astimezone(UTC)

        return start, end

    @classmethod
    def today_start_utc(cls, tz_name: str | None = None) -> datetime:
        """
        Get start of today in UTC for a given timezone.

        Returns midnight (00:00:00) in the local timezone, converted to UTC.

        Args:
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            datetime: Start of today in UTC

        Example:
            >>> # If today is Jan 15, 2024 in HST
            >>> start = TimezoneConverter.today_start_utc()
            >>> # Returns Jan 15, 2024 00:00:00 HST converted to UTC
            >>> # which is Jan 15, 2024 10:00:00 UTC
        """
        tz_name = tz_name or cls.DEFAULT_TIMEZONE
        tz = cls.get_timezone(tz_name)

        # Get today in local timezone
        local_now = datetime.now(tz)
        local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Convert to UTC
        return local_start.astimezone(UTC)

    @classmethod
    def today_end_utc(cls, tz_name: str | None = None) -> datetime:
        """
        Get end of today in UTC for a given timezone.

        Returns 23:59:59.999999 in the local timezone, converted to UTC.

        Args:
            tz_name: Timezone name (defaults to Pacific/Honolulu)

        Returns:
            datetime: End of today in UTC

        Example:
            >>> # If today is Jan 15, 2024 in HST
            >>> end = TimezoneConverter.today_end_utc()
            >>> # Returns Jan 15, 2024 23:59:59.999999 HST converted to UTC
        """
        tz_name = tz_name or cls.DEFAULT_TIMEZONE
        tz = cls.get_timezone(tz_name)

        # Get today in local timezone
        local_now = datetime.now(tz)
        local_end = local_now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Convert to UTC
        return local_end.astimezone(UTC)
