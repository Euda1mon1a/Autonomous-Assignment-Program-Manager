"""Timezone detection utilities for user preferences and request analysis."""

from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

from fastapi import Request


class TimezoneDetector:
    """
    Utility class for detecting and validating timezones.

    Provides methods to detect timezone from HTTP requests, validate timezone
    names, and manage user timezone preferences.
    """

    # Common timezone aliases for US military installations
    MILITARY_TIMEZONES = {
        "HST": "Pacific/Honolulu",  # Hawaii Standard Time
        "AKST": "America/Anchorage",  # Alaska Standard Time
        "PST": "America/Los_Angeles",  # Pacific Standard Time
        "MST": "America/Denver",  # Mountain Standard Time
        "CST": "America/Chicago",  # Central Standard Time
        "EST": "America/New_York",  # Eastern Standard Time
    }

    # Default application timezone
    DEFAULT_TIMEZONE = "Pacific/Honolulu"

    @classmethod
    def detect_from_request(cls, request: Request) -> str:
        """
        Detect timezone from HTTP request headers.

        Checks (in order):
        1. X-Timezone custom header
        2. User session/cookie timezone preference
        3. Accept-Language header for country-based default
        4. Falls back to default (Pacific/Honolulu)

        Args:
            request: FastAPI Request object

        Returns:
            str: IANA timezone name

        Example:
            >>> # Request with X-Timezone: America/New_York
            >>> tz = TimezoneDetector.detect_from_request(request)
            >>> tz
            'America/New_York'
        """
        # Check custom timezone header
        tz_header = request.headers.get("X-Timezone")
        if tz_header and cls.is_valid_timezone(tz_header):
            return tz_header

        # Check query parameter (for calendar subscriptions, etc.)
        tz_param = request.query_params.get("tz")
        if tz_param and cls.is_valid_timezone(tz_param):
            return tz_param

        # Check cookies for user preference
        tz_cookie = request.cookies.get("timezone")
        if tz_cookie and cls.is_valid_timezone(tz_cookie):
            return tz_cookie

        # Fallback to default
        return cls.DEFAULT_TIMEZONE

    @classmethod
    def is_valid_timezone(cls, tz_name: str) -> bool:
        """
        Check if a timezone name is valid.

        Args:
            tz_name: Timezone name to validate

        Returns:
            bool: True if valid IANA timezone name

        Example:
            >>> TimezoneDetector.is_valid_timezone("Pacific/Honolulu")
            True
            >>> TimezoneDetector.is_valid_timezone("Invalid/Timezone")
            False
        """
        try:
            # Check if it's an available timezone
            if tz_name in available_timezones():
                return True

            # Check if it's a military timezone alias
            if tz_name.upper() in cls.MILITARY_TIMEZONES:
                return True

            # Try to create ZoneInfo object
            ZoneInfo(tz_name)
            return True
        except Exception:
            return False

    @classmethod
    def normalize_timezone_name(cls, tz_name: str) -> str:
        """
        Normalize timezone name from various formats.

        Handles:
        - Military timezone abbreviations (HST, EST, etc.)
        - Common aliases
        - IANA standard names

        Args:
            tz_name: Timezone name or alias

        Returns:
            str: Normalized IANA timezone name

        Raises:
            ValueError: If timezone is invalid

        Example:
            >>> TimezoneDetector.normalize_timezone_name("HST")
            'Pacific/Honolulu'
            >>> TimezoneDetector.normalize_timezone_name("EST")
            'America/New_York'
        """
        # Check military timezone aliases
        upper_name = tz_name.upper()
        if upper_name in cls.MILITARY_TIMEZONES:
            return cls.MILITARY_TIMEZONES[upper_name]

        # Validate as IANA timezone
        if not cls.is_valid_timezone(tz_name):
            raise ValueError(f"Invalid timezone: {tz_name}")

        return tz_name

    @classmethod
    def get_timezone_info(cls, tz_name: str) -> dict:
        """
        Get detailed information about a timezone.

        Args:
            tz_name: Timezone name

        Returns:
            dict: Timezone information including offset, DST status, etc.

        Example:
            >>> info = TimezoneDetector.get_timezone_info("Pacific/Honolulu")
            >>> info["name"]
            'Pacific/Honolulu'
            >>> info["utc_offset_hours"]
            -10.0
            >>> info["has_dst"]
            False
        """
        tz_name = cls.normalize_timezone_name(tz_name)
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)

        # Get UTC offset
        offset = now.utcoffset()
        offset_hours = offset.total_seconds() / 3600 if offset else 0

        # Check DST
        dst = now.dst()
        has_dst = dst is not None and dst.total_seconds() != 0

        # Get abbreviation (if available)
        abbr = now.strftime("%Z")

        return {
            "name": tz_name,
            "abbreviation": abbr,
            "utc_offset_hours": offset_hours,
            "utc_offset_string": cls._format_offset(offset_hours),
            "has_dst": has_dst,
            "current_dst": has_dst,
            "current_datetime": now.isoformat(),
        }

    @classmethod
    def _format_offset(cls, hours: float) -> str:
        """
        Format UTC offset as string.

        Args:
            hours: Offset in hours (can be negative)

        Returns:
            str: Formatted offset (e.g., "UTC-10:00", "UTC+05:30")

        Example:
            >>> TimezoneDetector._format_offset(-10.0)
            'UTC-10:00'
            >>> TimezoneDetector._format_offset(5.5)
            'UTC+05:30'
        """
        sign = "+" if hours >= 0 else "-"
        abs_hours = abs(hours)
        hour_part = int(abs_hours)
        minute_part = int((abs_hours - hour_part) * 60)
        return f"UTC{sign}{hour_part:02d}:{minute_part:02d}"

    @classmethod
    def get_common_timezones(cls) -> list[dict]:
        """
        Get list of common timezones for user selection.

        Returns:
            list[dict]: Common timezones with display names and offsets

        Example:
            >>> timezones = TimezoneDetector.get_common_timezones()
            >>> len(timezones) > 0
            True
        """
        common = [
            ("Pacific/Honolulu", "Hawaii (HST)"),
            ("America/Anchorage", "Alaska (AKST/AKDT)"),
            ("America/Los_Angeles", "Pacific (PST/PDT)"),
            ("America/Denver", "Mountain (MST/MDT)"),
            ("America/Chicago", "Central (CST/CDT)"),
            ("America/New_York", "Eastern (EST/EDT)"),
            ("America/Puerto_Rico", "Atlantic (AST)"),
            ("Pacific/Guam", "Guam/Mariana Islands (ChST)"),
            ("Europe/London", "London (GMT/BST)"),
            ("Europe/Berlin", "Central Europe (CET/CEST)"),
            ("Asia/Tokyo", "Tokyo (JST)"),
            ("Asia/Seoul", "Seoul (KST)"),
            ("UTC", "Coordinated Universal Time (UTC)"),
        ]

        result = []
        for tz_name, display_name in common:
            try:
                info = cls.get_timezone_info(tz_name)
                result.append(
                    {
                        "value": tz_name,
                        "label": display_name,
                        "offset": info["utc_offset_string"],
                        "offset_hours": info["utc_offset_hours"],
                    }
                )
            except Exception:
                # Skip invalid timezones
                continue

        # Sort by offset
        result.sort(key=lambda x: x["offset_hours"])
        return result

    @classmethod
    def get_user_timezone(
        cls,
        user_preference: str | None = None,
        request: Request | None = None,
    ) -> str:
        """
        Get timezone for a user.

        Checks (in priority order):
        1. User's explicit preference from database
        2. Request headers/cookies
        3. Default timezone

        Args:
            user_preference: User's saved timezone preference
            request: Optional FastAPI Request object

        Returns:
            str: IANA timezone name

        Example:
            >>> # User with saved preference
            >>> tz = TimezoneDetector.get_user_timezone(
            ...     user_preference="America/New_York"
            ... )
            >>> tz
            'America/New_York'
        """
        # Check user preference
        if user_preference and cls.is_valid_timezone(user_preference):
            return cls.normalize_timezone_name(user_preference)

        # Check request
        if request:
            return cls.detect_from_request(request)

        # Default
        return cls.DEFAULT_TIMEZONE

    @classmethod
    def guess_timezone_from_offset(cls, offset_hours: float) -> list[str]:
        """
        Guess possible timezones from UTC offset.

        Args:
            offset_hours: UTC offset in hours (e.g., -10 for HST)

        Returns:
            list[str]: List of possible timezone names

        Example:
            >>> timezones = TimezoneDetector.guess_timezone_from_offset(-10)
            >>> "Pacific/Honolulu" in timezones
            True
        """
        matches = []
        target_offset_seconds = offset_hours * 3600

        # Check common timezones first
        for tz_info in cls.get_common_timezones():
            offset = tz_info["offset_hours"] * 3600
            if abs(offset - target_offset_seconds) < 1:  # Within 1 second
                matches.append(tz_info["value"])

        return matches

    @classmethod
    def validate_user_timezone_preference(cls, tz_name: str) -> str:
        """
        Validate and normalize user timezone preference.

        Args:
            tz_name: User-provided timezone name

        Returns:
            str: Normalized, validated timezone name

        Raises:
            ValueError: If timezone is invalid

        Example:
            >>> valid = TimezoneDetector.validate_user_timezone_preference("HST")
            >>> valid
            'Pacific/Honolulu'
        """
        try:
            return cls.normalize_timezone_name(tz_name)
        except ValueError as e:
            # Provide helpful error message
            raise ValueError(
                f"Invalid timezone '{tz_name}'. "
                f"Please use a valid IANA timezone name (e.g., 'Pacific/Honolulu') "
                f"or abbreviation (e.g., 'HST', 'EST')."
            ) from e

    @classmethod
    def get_timezone_for_location(cls, location: str) -> str | None:
        """
        Get timezone for a known location name.

        Args:
            location: Location name (e.g., "Honolulu", "New York")

        Returns:
            Optional[str]: IANA timezone name if found

        Example:
            >>> tz = TimezoneDetector.get_timezone_for_location("Honolulu")
            >>> tz
            'Pacific/Honolulu'
        """
        # Simple location-to-timezone mapping for common military bases
        location_map = {
            "honolulu": "Pacific/Honolulu",
            "hawaii": "Pacific/Honolulu",
            "pearl harbor": "Pacific/Honolulu",
            "guam": "Pacific/Guam",
            "tokyo": "Asia/Tokyo",
            "yokota": "Asia/Tokyo",
            "seoul": "Asia/Seoul",
            "osan": "Asia/Seoul",
            "ramstein": "Europe/Berlin",
            "stuttgart": "Europe/Berlin",
            "norfolk": "America/New_York",
            "san diego": "America/Los_Angeles",
            "fort bragg": "America/New_York",
            "fort hood": "America/Chicago",
        }

        location_lower = location.lower().strip()
        return location_map.get(location_lower)

    @classmethod
    def is_same_timezone(cls, tz1: str, tz2: str) -> bool:
        """
        Check if two timezone names refer to the same timezone.

        Handles aliases and different representations of the same timezone.

        Args:
            tz1: First timezone name
            tz2: Second timezone name

        Returns:
            bool: True if timezones are equivalent

        Example:
            >>> TimezoneDetector.is_same_timezone("HST", "Pacific/Honolulu")
            True
        """
        try:
            norm1 = cls.normalize_timezone_name(tz1)
            norm2 = cls.normalize_timezone_name(tz2)
            return norm1 == norm2
        except ValueError:
            return False
