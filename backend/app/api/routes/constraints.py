"""
Constraint Management API Routes

DB-backed constraint configuration. The constraint_configurations table is the
single source of truth — seeded from ConstraintManager instances, read by the
engine at schedule generation time.

Endpoints:
    GET /api/v1/constraints - List all constraints (from DB)
    GET /api/v1/constraints/enabled - List enabled constraints
    GET /api/v1/constraints/disabled - List disabled constraints
    GET /api/v1/constraints/{name} - Get single constraint
    PATCH /api/v1/constraints/{name} - Update enabled/weight (persisted to DB)
    POST /api/v1/constraints/{name}/enable - Enable a constraint
    POST /api/v1/constraints/{name}/disable - Disable a constraint
    POST /api/v1/constraints/preset/{preset} - Apply a preset
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.role_filter import require_admin
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.constraint_config import ConstraintConfiguration
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["constraints"])

# Map DB string priority to numeric (frontend expects int)
PRIORITY_TO_INT: dict[str, int] = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
}


class ConstraintStatusResponse(BaseModel):
    """Response model for constraint status."""

    name: str
    enabled: bool
    weight: float
    priority: int
    category: str
    description: str | None


class ConstraintListResponse(BaseModel):
    """Response model for constraint list."""

    constraints: list[ConstraintStatusResponse]
    total: int
    enabled_count: int
    disabled_count: int


class ConstraintEnableResponse(BaseModel):
    """Response model for enable/disable operations."""

    success: bool
    message: str
    constraint: ConstraintStatusResponse


class ConstraintUpdateRequest(BaseModel):
    """Request model for updating constraint configuration."""

    enabled: bool | None = None
    weight: float | None = None


class ConstraintUpdateResponse(BaseModel):
    """Response model for constraint updates."""

    success: bool
    message: str
    constraint: ConstraintStatusResponse


class PresetApplyResponse(BaseModel):
    """Response model for preset application."""

    success: bool
    message: str
    enabled_constraints: list[str]
    disabled_constraints: list[str]


def _db_to_response(row: ConstraintConfiguration) -> ConstraintStatusResponse:
    """Convert DB row to response model."""
    return ConstraintStatusResponse(
        name=row.name,
        enabled=row.enabled,
        weight=row.weight,
        priority=PRIORITY_TO_INT.get(row.priority, 3),
        category=row.category,
        description=row.description,
    )


def _ensure_seeded(db: Session) -> None:
    """Auto-seed constraint_configurations if table is empty."""
    count = db.query(ConstraintConfiguration).count()
    if count > 0:
        return
    logger.info(
        "constraint_configurations table is empty — auto-seeding from ConstraintManager"
    )
    from app.scheduling.constraints import ConstraintManager
    from app.scheduling.constraints.base import HardConstraint

    try:
        # Import seed logic inline to avoid circular imports at module level
        from seed_constraints import _get_category

        manager = ConstraintManager.create_default(profile="faculty")
        for constraint in manager.constraints:
            is_soft = not isinstance(constraint, HardConstraint)
            db.add(
                ConstraintConfiguration(
                    name=constraint.name,
                    enabled=constraint.enabled,
                    weight=constraint.weight if is_soft else 1.0,
                    priority=constraint.priority.name,
                    category=_get_category(constraint.name),
                    description=f"{'Soft' if is_soft else 'Hard'} constraint: {constraint.name}",
                )
            )
        db.commit()
        logger.info("Auto-seeded %d constraints", len(manager.constraints))
    except Exception as e:
        db.rollback()
        logger.warning("Auto-seed failed: %s", e)


def _get_or_404(db: Session, name: str) -> ConstraintConfiguration:
    """Get constraint by name or raise 404."""
    _ensure_seeded(db)
    row = (
        db.query(ConstraintConfiguration)
        .filter(ConstraintConfiguration.name == name)
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Constraint '{name}' not found",
        )
    return row


@router.get("", response_model=list[ConstraintStatusResponse])
def list_constraints(
    db: Session = Depends(get_db),
) -> list[ConstraintStatusResponse]:
    """List all constraints from DB."""
    _ensure_seeded(db)
    rows = (
        db.query(ConstraintConfiguration)
        .order_by(ConstraintConfiguration.category, ConstraintConfiguration.name)
        .all()
    )
    return [_db_to_response(r) for r in rows]


@router.get("/enabled", response_model=list[ConstraintStatusResponse])
def list_enabled_constraints(
    db: Session = Depends(get_db),
) -> list[ConstraintStatusResponse]:
    """List enabled constraints."""
    rows = (
        db.query(ConstraintConfiguration)
        .filter(ConstraintConfiguration.enabled.is_(True))
        .order_by(ConstraintConfiguration.category, ConstraintConfiguration.name)
        .all()
    )
    return [_db_to_response(r) for r in rows]


@router.get("/disabled", response_model=list[ConstraintStatusResponse])
def list_disabled_constraints(
    db: Session = Depends(get_db),
) -> list[ConstraintStatusResponse]:
    """List disabled constraints."""
    rows = (
        db.query(ConstraintConfiguration)
        .filter(ConstraintConfiguration.enabled.is_(False))
        .order_by(ConstraintConfiguration.category, ConstraintConfiguration.name)
        .all()
    )
    return [_db_to_response(r) for r in rows]


@router.get("/category/{category}", response_model=list[ConstraintStatusResponse])
def list_constraints_by_category(
    category: str,
    db: Session = Depends(get_db),
) -> list[ConstraintStatusResponse]:
    """List constraints by category."""
    rows = (
        db.query(ConstraintConfiguration)
        .filter(ConstraintConfiguration.category == category.upper())
        .order_by(ConstraintConfiguration.name)
        .all()
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No constraints found for category '{category}'",
        )
    return [_db_to_response(r) for r in rows]


@router.get("/{name}", response_model=ConstraintStatusResponse)
def get_constraint(
    name: str,
    db: Session = Depends(get_db),
) -> ConstraintStatusResponse:
    """Get a single constraint by name."""
    return _db_to_response(_get_or_404(db, name))


@router.patch("/{name}", response_model=ConstraintUpdateResponse)
def update_constraint(
    name: str,
    body: ConstraintUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> ConstraintUpdateResponse:
    """Update constraint enabled/weight. Persisted to DB, read by engine at next generation."""
    row = _get_or_404(db, name)

    if body.enabled is not None:
        row.enabled = body.enabled
    if body.weight is not None:
        if body.weight < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight must be non-negative",
            )
        row.weight = body.weight

    row.updated_by = current_user.username if current_user else None
    db.commit()
    db.refresh(row)

    logger.info(
        "Constraint '%s' updated by %s: enabled=%s, weight=%s",
        name,
        row.updated_by,
        row.enabled,
        row.weight,
    )

    return ConstraintUpdateResponse(
        success=True,
        message=f"Constraint '{name}' updated",
        constraint=_db_to_response(row),
    )


@router.post("/{name}/enable", response_model=ConstraintEnableResponse)
def enable_constraint(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> ConstraintEnableResponse:
    """Enable a constraint."""
    row = _get_or_404(db, name)
    row.enabled = True
    row.updated_by = current_user.username if current_user else None
    db.commit()
    db.refresh(row)
    logger.info("Enabled constraint via API: %s", name)
    return ConstraintEnableResponse(
        success=True,
        message=f"Constraint '{name}' enabled",
        constraint=_db_to_response(row),
    )


@router.post("/{name}/disable", response_model=ConstraintEnableResponse)
def disable_constraint(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> ConstraintEnableResponse:
    """Disable a constraint."""
    row = _get_or_404(db, name)
    row.enabled = False
    row.updated_by = current_user.username if current_user else None
    db.commit()
    db.refresh(row)
    logger.info("Disabled constraint via API: %s", name)
    return ConstraintEnableResponse(
        success=True,
        message=f"Constraint '{name}' disabled",
        constraint=_db_to_response(row),
    )


# Preset definitions — which constraints to enable/disable per preset
PRESETS: dict[str, dict[str, list[str]]] = {
    "minimal": {
        "enable": [
            "80HourRule",
            "1in7Rule",
            "Availability",
            "SupervisionRatio",
            "Coverage",
        ],
        "disable_rest": True,
    },
    "strict": {
        "enable_all": True,
    },
    "resilience_tier1": {
        "enable": ["HubProtection", "UtilizationBuffer"],
    },
    "resilience_tier2": {
        "enable": [
            "HubProtection",
            "UtilizationBuffer",
            "ZoneBoundary",
            "PreferenceTrail",
            "N1Vulnerability",
        ],
    },
    "call_scheduling": {
        "enable": [
            "CallAvailability",
            "CallSpacing",
            "NoConsecutiveCall",
            "OvernightCallCoverage",
            "OvernightCallGeneration",
            "PostCallAutoAssignment",
            "EscalatingCallEquity",
            "WeekdayCallEquity",
            "SundayCallEquity",
            "HolidayCallEquity",
        ],
    },
}


@router.post("/preset/{preset}", response_model=PresetApplyResponse)
def apply_constraint_preset(
    preset: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> PresetApplyResponse:
    """Apply a constraint preset (persisted to DB)."""
    _ensure_seeded(db)
    if preset not in PRESETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid preset: {preset}. Valid: {list(PRESETS.keys())}",
        )

    config = PRESETS[preset]
    all_rows = db.query(ConstraintConfiguration).all()

    if config.get("enable_all"):
        for row in all_rows:
            row.enabled = True
    elif config.get("disable_rest"):
        enable_set = set(config.get("enable", []))
        for row in all_rows:
            row.enabled = row.name in enable_set
    else:
        enable_set = set(config.get("enable", []))
        for row in all_rows:
            if row.name in enable_set:
                row.enabled = True

    db.commit()

    enabled = [r.name for r in all_rows if r.enabled]
    disabled = [r.name for r in all_rows if not r.enabled]

    logger.info("Applied constraint preset '%s' by %s", preset, current_user.username)

    return PresetApplyResponse(
        success=True,
        message=f"Preset '{preset}' applied",
        enabled_constraints=enabled,
        disabled_constraints=disabled,
    )
