"""Helpers for deriving Activity codes and display abbreviations."""

from __future__ import annotations

import re

MAX_DISPLAY_ABBREV_LEN = 20


def activity_code_from_name(name: str) -> str:
    """Create a stable activity code from a rotation/activity name."""
    base = (name or "").strip().lower()
    if not base:
        return "activity"
    base = re.sub(r"[\\s/\\-]+", "_", base)
    base = re.sub(r"[^a-z0-9_]+", "", base)
    base = base.strip("_")
    return base or "activity"


def activity_display_abbrev(
    name: str,
    display_abbreviation: str | None = None,
    abbreviation: str | None = None,
) -> str:
    """Pick a display abbreviation, favoring explicit template values."""
    candidate = (display_abbreviation or abbreviation or name or "").strip()
    if not candidate:
        candidate = "ACT"
    candidate = candidate.upper()
    if len(candidate) > MAX_DISPLAY_ABBREV_LEN:
        candidate = candidate[:MAX_DISPLAY_ABBREV_LEN]
    return candidate
