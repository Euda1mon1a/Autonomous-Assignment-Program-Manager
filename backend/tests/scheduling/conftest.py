"""
Pytest fixtures for scheduling tests.

Block 10 date constants and helper fixtures for TDD testing.
"""

from datetime import date

import pytest


# ============================================================================
# Block 10 Date Constants
# ============================================================================

BLOCK_10_START = date(2026, 3, 12)  # Thursday
BLOCK_10_END = date(2026, 4, 8)  # Wednesday
MID_BLOCK_DATE = date(2026, 3, 23)  # Monday (start of second half)
LAST_WEDNESDAY = date(2026, 4, 8)


# ============================================================================
# Rotation Pattern Helpers (synthetic data)
# ============================================================================

# Synthetic resident rotation patterns for testing scheduling rules.
# These encode the SAME rotation patterns that the scheduling engine must
# produce, but with synthetic names (no PII).
SYNTHETIC_RESIDENTS = {
    "Alpha, Resident": {"pgy": 1, "rotation1": "KAP", "rotation2": None},
    "Bravo, Resident": {"pgy": 2, "rotation1": "LDNF", "rotation2": None},
    "Charlie, Resident": {"pgy": 1, "rotation1": "PROC", "rotation2": None},
    "Delta, Resident": {"pgy": 1, "rotation1": "IM", "rotation2": None},
    "Echo, Resident": {"pgy": 3, "rotation1": "NEURO", "rotation2": "NF"},
    "Foxtrot, Resident": {"pgy": 1, "rotation1": "Peds Ward", "rotation2": "Peds NF"},
    "Golf, Resident": {"pgy": 1, "rotation1": "Peds NF", "rotation2": "Peds Ward"},
    "Hotel, Resident": {"pgy": 1, "rotation1": "FMC", "rotation2": None},
    "India, Resident": {"pgy": 2, "rotation1": "FMC", "rotation2": None},
}
