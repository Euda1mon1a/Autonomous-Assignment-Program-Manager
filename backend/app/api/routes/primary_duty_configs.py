"""API routes for primary duty configuration management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.role_filter import require_admin
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.primary_duty_config import PrimaryDutyConfiguration
from app.models.user import User
from app.schemas.primary_duty_config import (
    PrimaryDutyConfigCreate,
    PrimaryDutyConfigResponse,
    PrimaryDutyConfigUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[PrimaryDutyConfigResponse])
def list_primary_duty_configs(
    db: Session = Depends(get_db),
) -> list[PrimaryDutyConfigResponse]:
    """List all primary duty configurations."""
    rows = (
        db.query(PrimaryDutyConfiguration)
        .order_by(PrimaryDutyConfiguration.duty_name)
        .all()
    )
    return [PrimaryDutyConfigResponse.model_validate(r) for r in rows]


@router.get("/{config_id}", response_model=PrimaryDutyConfigResponse)
def get_primary_duty_config(
    config_id: UUID,
    db: Session = Depends(get_db),
) -> PrimaryDutyConfigResponse:
    """Get a single primary duty configuration."""
    row = db.query(PrimaryDutyConfiguration).filter_by(id=config_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Primary duty config '{config_id}' not found",
        )
    return PrimaryDutyConfigResponse.model_validate(row)


@router.post("/", response_model=PrimaryDutyConfigResponse, status_code=201)
def create_primary_duty_config(
    body: PrimaryDutyConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> PrimaryDutyConfigResponse:
    """Create a new primary duty configuration."""
    existing = (
        db.query(PrimaryDutyConfiguration).filter_by(duty_name=body.duty_name).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duty name '{body.duty_name}' already exists",
        )

    if body.clinic_min_per_week > body.clinic_max_per_week:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"clinic_min_per_week ({body.clinic_min_per_week}) cannot exceed clinic_max_per_week ({body.clinic_max_per_week})",
        )
    if not all(0 <= d <= 4 for d in body.available_days):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="available_days must contain only values 0-4 (Mon-Fri)",
        )

    row = PrimaryDutyConfiguration(
        duty_name=body.duty_name,
        clinic_min_per_week=body.clinic_min_per_week,
        clinic_max_per_week=body.clinic_max_per_week,
        available_days=body.available_days,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("Created primary duty config: %s", body.duty_name)
    return PrimaryDutyConfigResponse.model_validate(row)


@router.patch("/{config_id}", response_model=PrimaryDutyConfigResponse)
def update_primary_duty_config(
    config_id: UUID,
    body: PrimaryDutyConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> PrimaryDutyConfigResponse:
    """Update a primary duty configuration."""
    row = db.query(PrimaryDutyConfiguration).filter_by(id=config_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Primary duty config '{config_id}' not found",
        )

    if body.duty_name is not None and body.duty_name != row.duty_name:
        existing = (
            db.query(PrimaryDutyConfiguration)
            .filter_by(duty_name=body.duty_name)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duty name '{body.duty_name}' already exists",
            )
        row.duty_name = body.duty_name

    if body.clinic_min_per_week is not None:
        row.clinic_min_per_week = body.clinic_min_per_week
    if body.clinic_max_per_week is not None:
        row.clinic_max_per_week = body.clinic_max_per_week

    # Validate min <= max
    effective_min = (
        body.clinic_min_per_week
        if body.clinic_min_per_week is not None
        else row.clinic_min_per_week
    )
    effective_max = (
        body.clinic_max_per_week
        if body.clinic_max_per_week is not None
        else row.clinic_max_per_week
    )
    if effective_min > effective_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"clinic_min_per_week ({effective_min}) cannot exceed clinic_max_per_week ({effective_max})",
        )

    if body.available_days is not None:
        if not all(0 <= d <= 4 for d in body.available_days):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="available_days must contain only values 0-4 (Mon-Fri)",
            )
        row.available_days = body.available_days

    db.commit()
    db.refresh(row)
    logger.info("Updated primary duty config: %s", row.duty_name)
    return PrimaryDutyConfigResponse.model_validate(row)


@router.delete("/{config_id}", status_code=204)
def delete_primary_duty_config(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
) -> None:
    """Delete a primary duty configuration."""
    row = db.query(PrimaryDutyConfiguration).filter_by(id=config_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Primary duty config '{config_id}' not found",
        )
    db.delete(row)
    db.commit()
    logger.info("Deleted primary duty config: %s", row.duty_name)
