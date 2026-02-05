"""Settings API routes with database persistence."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_admin_user, get_current_active_user
from app.db.session import get_db
from app.models.settings import ApplicationSettings
from app.models.user import User
from app.schemas.settings import SettingsBase, SettingsResponse, SettingsUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

# Default settings for initialization
DEFAULT_SETTINGS = {
    "scheduling_algorithm": "cp_sat",
    "work_hours_per_week": 80,
    "max_consecutive_days": 6,
    "min_days_off_per_week": 1,
    "pgy1_supervision_ratio": "1:2",
    "pgy2_supervision_ratio": "1:4",
    "pgy3_supervision_ratio": "1:4",
    "enable_weekend_scheduling": True,
    "enable_holiday_scheduling": False,
    "default_block_duration_hours": 4,
    "schedule_lock_date": None,
}


async def get_or_create_settings(db: Session) -> ApplicationSettings:
    """Get settings from database, creating default if none exist."""
    result = db.execute(select(ApplicationSettings))
    settings = result.scalar_one_or_none()
    if settings is None:
        logger.info("No settings found, creating defaults")
        settings = ApplicationSettings(**DEFAULT_SETTINGS)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SettingsResponse:
    """Get current application settings."""
    settings = await get_or_create_settings(db)
    return SettingsResponse(**settings.to_dict())


@router.post("", response_model=SettingsResponse)
async def update_settings(
    settings_in: SettingsBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> SettingsResponse:
    """Update application settings (full replacement)."""
    if not get_settings().DEBUG and settings_in.scheduling_algorithm != "cp_sat":
        raise HTTPException(
            status_code=400,
            detail="Only CP-SAT is allowed in production settings.",
        )
    settings = await get_or_create_settings(db)
    previous_lock_date = settings.schedule_lock_date

    # Update all fields
    for field, value in settings_in.model_dump().items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)

    if previous_lock_date != settings.schedule_lock_date:
        from app.services.schedule_draft_service import ScheduleDraftService

        ScheduleDraftService(db).reflag_lock_window_for_all_drafts()

    logger.info(
        "Settings updated: algorithm=%s, work_hours=%d",
        settings.scheduling_algorithm,
        settings.work_hours_per_week,
    )
    return SettingsResponse(**settings.to_dict())


@router.patch("", response_model=SettingsResponse)
async def patch_settings(
    settings_in: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> SettingsResponse:
    """Partially update application settings."""
    settings = await get_or_create_settings(db)
    previous_lock_date = settings.schedule_lock_date

    # Only update provided fields
    update_data = settings_in.model_dump(exclude_unset=True)
    if not update_data:
        return SettingsResponse(**settings.to_dict())

    if (
        not get_settings().DEBUG
        and update_data.get("scheduling_algorithm")
        and update_data["scheduling_algorithm"] != "cp_sat"
    ):
        raise HTTPException(
            status_code=400,
            detail="Only CP-SAT is allowed in production settings.",
        )

    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)

    if previous_lock_date != settings.schedule_lock_date:
        from app.services.schedule_draft_service import ScheduleDraftService

        ScheduleDraftService(db).reflag_lock_window_for_all_drafts()

    logger.info("Settings patched: %s", list(update_data.keys()))
    return SettingsResponse(**settings.to_dict())


@router.delete("", status_code=204)
async def reset_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
) -> None:
    """Reset settings to defaults."""
    settings = await get_or_create_settings(db)
    previous_lock_date = settings.schedule_lock_date

    # Reset all fields to defaults
    for field, value in DEFAULT_SETTINGS.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    db.commit()

    if previous_lock_date != settings.schedule_lock_date:
        from app.services.schedule_draft_service import ScheduleDraftService

        ScheduleDraftService(db).reflag_lock_window_for_all_drafts()

    logger.info("Settings reset to defaults")
