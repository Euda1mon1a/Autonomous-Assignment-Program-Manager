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

# Module-level defaults (match historical hardcoded values).
# Overridden by load_from_settings() at engine startup.
_overnight_call_weekdays: set[int] = {0, 1, 2, 3, 6}  # Mon-Thu + Sun
_fmit_week_start_weekday: int = 4  # Friday


def get_overnight_call_weekdays() -> set[int]:
    """Return the set of weekdays that require overnight call coverage."""
    return _overnight_call_weekdays


def get_fmit_week_start_weekday() -> int:
    """Return the weekday number for the start of an FMIT week."""
    return _fmit_week_start_weekday


def is_overnight_call_day(d: date) -> bool:
    """Check if a date requires overnight call assignment."""
    return d.weekday() in _overnight_call_weekdays


def load_from_settings(db_session) -> None:
    """
    Load calendar policy from application_settings.

    Called once per scheduling run (engine.py) to override module defaults.
    Falls back to hardcoded defaults if settings are missing or DB unavailable.
    """
    global _overnight_call_weekdays, _fmit_week_start_weekday

    try:
        from app.models.settings import ApplicationSettings

        settings = db_session.query(ApplicationSettings).first()
        if settings is None:
            return

        weekdays = getattr(settings, "overnight_call_weekdays", None)
        if weekdays is not None and isinstance(weekdays, list):
            _overnight_call_weekdays = set(weekdays)
            logger.debug("Loaded overnight_call_weekdays from DB: %s", weekdays)

        fmit_start = getattr(settings, "fmit_week_start_weekday", None)
        if fmit_start is not None:
            _fmit_week_start_weekday = fmit_start
            logger.debug("Loaded fmit_week_start_weekday from DB: %d", fmit_start)

    except Exception:
        logger.warning("Failed to load calendar policy from DB, using defaults")
