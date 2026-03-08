"""Enumeration endpoints for frontend dropdowns.

Provides valid options for configuration fields so the frontend
can populate dropdowns without hardcoding values.
"""

from enum import Enum

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.activity import ActivityCategory
from app.models.inpatient_preload import InpatientRotationType
from app.scheduling.constraints.config import ConstraintCategory

router = APIRouter(prefix="/enums", tags=["enums"])


def _enum_to_options(enum_class: type[Enum]) -> list[dict[str, str]]:
    """Convert an enum to a list of {value, label} options."""
    return [
        {"value": member.value, "label": member.name.replace("_", " ").title()}
        for member in enum_class
    ]


@router.get("/scheduling-algorithms")
async def get_scheduling_algorithms() -> list[dict[str, str]]:
    """Get available scheduling algorithms for dropdown."""
    settings = get_settings()
    if not settings.DEBUG:
        return [{"value": "cp_sat", "label": "CP-SAT (Canonical)"}]
    return [
        {"value": "greedy", "label": "Greedy (Fast heuristic)"},
        {"value": "cp_sat", "label": "CP-SAT (Optimal, slower)"},
        {"value": "pulp", "label": "PuLP (Linear programming)"},
        {"value": "hybrid", "label": "Hybrid (CP-SAT + PuLP)"},
    ]


@router.get("/activity-categories")
async def get_activity_categories() -> list[dict[str, str]]:
    """Get available activity categories for dropdown."""
    return _enum_to_options(ActivityCategory)


@router.get("/rotation-types")
async def get_rotation_types() -> list[dict[str, str]]:
    """Get available inpatient rotation types for dropdown."""
    return _enum_to_options(InpatientRotationType)


@router.get("/pgy-levels")
async def get_pgy_levels() -> list[dict[str, str]]:
    """Get PGY levels for dropdown (1-8, supports fellowship levels)."""
    return [
        {"value": "1", "label": "PGY-1 (Intern)"},
        {"value": "2", "label": "PGY-2"},
        {"value": "3", "label": "PGY-3 (Chief)"},
        {"value": "4", "label": "PGY-4"},
        {"value": "5", "label": "PGY-5"},
        {"value": "6", "label": "PGY-6"},
        {"value": "7", "label": "PGY-7"},
        {"value": "8", "label": "PGY-8"},
    ]


@router.get("/constraint-categories")
async def get_constraint_categories() -> list[dict[str, str]]:
    """Get constraint categories for dropdown."""
    return _enum_to_options(ConstraintCategory)


@router.get("/person-types")
async def get_person_types() -> list[dict[str, str]]:
    """Get person types for dropdown."""
    return [
        {"value": "resident", "label": "Resident"},
        {"value": "faculty", "label": "Faculty"},
    ]


@router.get("/freeze-scopes")
async def get_freeze_scopes() -> list[dict[str, str]]:
    """Get freeze scope options for settings dropdown."""
    return [
        {"value": "none", "label": "None (All changes allowed)"},
        {"value": "non_emergency_only", "label": "Non-emergency only"},
        {
            "value": "all_changes_require_override",
            "label": "All changes require override",
        },
    ]
