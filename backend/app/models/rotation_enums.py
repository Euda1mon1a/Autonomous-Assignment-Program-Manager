"""Enums for rotation template GUI features.

These enums support the rotation template management system with
pattern types, setting types, and preference weights.
"""

from enum import Enum


class RotationPatternType(str, Enum):
    """
    Type of rotation scheduling pattern.

    - REGULAR: Full block with single activity (e.g., full FMIT block)
    - SPLIT: Two activities in fixed sequence (e.g., NF then Elective)
    - MIRRORED: Two cohorts swap mid-block (A: NF→Elec, B: Elec→NF)
    - ALTERNATING: A/B week pattern within block
    """

    REGULAR = "regular"
    SPLIT = "split"
    MIRRORED = "mirrored"
    ALTERNATING = "alternating"


class RotationSettingType(str, Enum):
    """
    Clinical setting for the rotation.

    - INPATIENT: 7-day coverage required, ward-based, includes weekends
    - OUTPATIENT: Weekday clinic only, AM/PM flexible, no weekends
    """

    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"


class PreferenceWeight(str, Enum):
    """
    Weight for soft scheduling preferences.

    Used by the solver to prioritize preferences during optimization.
    Higher weights mean the solver tries harder to satisfy the preference.
    """

    LOW = "low"  # Nice to have, minimal penalty if not satisfied
    MEDIUM = "medium"  # Moderate priority, some penalty
    HIGH = "high"  # Strong preference, significant penalty
    REQUIRED = "required"  # Soft but strongly enforced, high penalty


class ActivityType(str, Enum):
    """
    Activity types for weekly grid cells.

    These are slot-level Activity types (NOT RotationTemplate.rotation_type).
    They populate each AM/PM slot in the 7x2 weekly pattern grid.
    """

    FM_CLINIC = "fm_clinic"
    SPECIALTY = "specialty"
    ELECTIVE = "elective"
    CONFERENCE = "conference"
    INPATIENT = "inpatient"
    CALL = "call"
    PROCEDURE = "procedure"
    OFF = "off"


class TimeOfDay(str, Enum):
    """Time of day for half-day slots."""

    AM = "AM"
    PM = "PM"
