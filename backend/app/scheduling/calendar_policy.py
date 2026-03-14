"""
Centralized calendar policy for overnight call and FMIT scheduling.

Single source of truth for:
- Which weekdays have overnight call (default: Sun-Thu → {0, 1, 2, 3, 6})
- FMIT week start weekday (default: Friday → 4)

These values are stored in application_settings and loaded once per
scheduling run. Constraint modules and services import from here
instead of hardcoding weekday sets.
"""

import logging
from datetime import date

logger = logging.getLogger(__name__)

# Canonical defaults (match historical hardcoded values).
_DEFAULT_OVERNIGHT_CALL_WEEKDAYS: set[int] = {0, 1, 2, 3, 6}  # Mon-Thu + Sun
_DEFAULT_FMIT_WEEK_START_WEEKDAY: int = 4  # Friday

# Module-level state — overridden by load_from_settings() / async variant.
_overnight_call_weekdays: set[int] = set(_DEFAULT_OVERNIGHT_CALL_WEEKDAYS)
_fmit_week_start_weekday: int = _DEFAULT_FMIT_WEEK_START_WEEKDAY


def get_overnight_call_weekdays() -> set[int]:
    """Return the set of weekdays that require overnight call coverage."""
    return _overnight_call_weekdays


def get_fmit_week_start_weekday() -> int:
    """Return the weekday number for the start of an FMIT week."""
    return _fmit_week_start_weekday


def is_overnight_call_day(d: date) -> bool:
    """Check if a date requires overnight call assignment."""
    return d.weekday() in _overnight_call_weekdays


def _apply_settings(settings) -> None:
    """Apply calendar policy fields from an ApplicationSettings row."""
    global _overnight_call_weekdays, _fmit_week_start_weekday

    weekdays = getattr(settings, "overnight_call_weekdays", None)
    if weekdays is not None and isinstance(weekdays, list):
        _overnight_call_weekdays = set(weekdays)
        logger.debug("Loaded overnight_call_weekdays from DB: %s", weekdays)

    fmit_start = getattr(settings, "fmit_week_start_weekday", None)
    if fmit_start is not None:
        _fmit_week_start_weekday = fmit_start
        logger.debug("Loaded fmit_week_start_weekday from DB: %d", fmit_start)


def load_from_settings(db_session) -> None:
    """
    Load calendar policy from application_settings (sync session).

    Called once per scheduling run (engine.py) to override module defaults.
    Falls back to hardcoded defaults if settings are missing or DB unavailable.
    """
    global _overnight_call_weekdays, _fmit_week_start_weekday

    # Always reset to defaults first (prevents stale values on DB failure)
    _overnight_call_weekdays = set(_DEFAULT_OVERNIGHT_CALL_WEEKDAYS)
    _fmit_week_start_weekday = _DEFAULT_FMIT_WEEK_START_WEEKDAY

    try:
        from app.models.settings import ApplicationSettings

        settings = db_session.query(ApplicationSettings).first()
        if settings is None:
            return

        _apply_settings(settings)

    except Exception:
        logger.warning("Failed to load calendar policy from DB, using defaults")


async def async_load_from_settings(db_session) -> None:
    """
    Load calendar policy from application_settings (async session).

    Async counterpart of :func:`load_from_settings` for use in FastAPI
    services that hold an ``AsyncSession``.
    """
    global _overnight_call_weekdays, _fmit_week_start_weekday

    # Always reset to defaults first (prevents stale values on DB failure)
    _overnight_call_weekdays = set(_DEFAULT_OVERNIGHT_CALL_WEEKDAYS)
    _fmit_week_start_weekday = _DEFAULT_FMIT_WEEK_START_WEEKDAY

    try:
        from sqlalchemy import select as sa_select

        from app.models.settings import ApplicationSettings

        result = await db_session.execute(sa_select(ApplicationSettings).limit(1))
        settings = result.scalar_one_or_none()
        if settings is None:
            return

        _apply_settings(settings)

    except Exception:
        logger.warning("Failed to load calendar policy from DB, using defaults")
