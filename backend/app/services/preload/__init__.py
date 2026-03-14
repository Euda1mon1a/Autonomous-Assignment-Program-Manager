"""Preload sub-package — shared logic for sync and async preload services."""

from .activity_cache import ActivityCache
from .constants import (
    CLINIC_PATTERN_CODES,
    INTERN_CONTINUITY_EXEMPT_ROTATIONS,
    KAP_ROTATIONS,
    LEC_EXEMPT_ROTATIONS,
    NIGHT_FLOAT_ROTATIONS,
    OFFSITE_ROTATIONS,
    ROTATION_ALIASES,
    ROTATION_TO_ACTIVITY,
    SATURDAY_OFF_ROTATIONS,
    canonical_rotation_code,
    get_continuity_exempt_codes,
    get_lec_exempt_codes,
    get_offsite_codes,
    get_saturday_off_codes,
)
from .date_helpers import is_last_wednesday, pattern_day_of_week, pattern_week_number
from .rotation_codes import (
    get_hilo_codes,
    get_kap_codes,
    get_ldnf_codes,
    get_nf_codes,
    get_rotation_codes,
    get_rotation_preload_codes,
    is_intern_continuity_exempt,
    is_lec_exempt,
)
from .template_cache import TemplateCache

__all__ = [
    "ActivityCache",
    "CLINIC_PATTERN_CODES",
    "INTERN_CONTINUITY_EXEMPT_ROTATIONS",
    "KAP_ROTATIONS",
    "LEC_EXEMPT_ROTATIONS",
    "NIGHT_FLOAT_ROTATIONS",
    "OFFSITE_ROTATIONS",
    "ROTATION_ALIASES",
    "ROTATION_TO_ACTIVITY",
    "SATURDAY_OFF_ROTATIONS",
    "TemplateCache",
    "canonical_rotation_code",
    "get_continuity_exempt_codes",
    "get_hilo_codes",
    "get_kap_codes",
    "get_lec_exempt_codes",
    "get_ldnf_codes",
    "get_nf_codes",
    "get_offsite_codes",
    "get_rotation_codes",
    "get_rotation_preload_codes",
    "get_saturday_off_codes",
    "is_intern_continuity_exempt",
    "is_last_wednesday",
    "is_lec_exempt",
    "pattern_day_of_week",
    "pattern_week_number",
]
