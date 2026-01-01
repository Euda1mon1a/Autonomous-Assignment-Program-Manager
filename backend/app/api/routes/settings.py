"""Settings API routes with database persistence."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_admin_user, get_current_active_user
from app.db.session import get_async_db
from app.models.settings import ApplicationSettings
from app.models.user import User
from app.schemas.settings import SettingsBase, SettingsResponse, SettingsUpdate

logger = logging.getLogger(__name__)
router = APIRouter()

# Default settings for initialization
DEFAULT_SETTINGS = {
    "scheduling_algorithm": "greedy",
    "work_hours_per_week": 80,
    "max_consecutive_days": 6,
    "min_days_off_per_week": 1,
    "pgy1_supervision_ratio": "1:2",
    "pgy2_supervision_ratio": "1:4",
    "pgy3_supervision_ratio": "1:4",
    "enable_weekend_scheduling": True,
    "enable_holiday_scheduling": False,
    "default_block_duration_hours": 4,
}


async def get_or_create_settings(db: AsyncSession) -> ApplicationSettings:
    """Get settings from database, creating default if none exist."""
    result = await db.execute(select(ApplicationSettings))
    settings = result.scalar_one_or_none()
    if settings is None:
        logger.info("No settings found, creating defaults")
        settings = ApplicationSettings(**DEFAULT_SETTINGS)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current application settings."""
    settings = await get_or_create_settings(db)
    return SettingsResponse(**settings.to_dict())


@router.post("", response_model=SettingsResponse)
async def update_settings(
    settings_in: SettingsBase,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """Update application settings (full replacement)."""
    settings = await get_or_create_settings(db)

    # Update all fields
    for field, value in settings_in.model_dump().items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(settings)

    logger.info(
        "Settings updated: algorithm=%s, work_hours=%d",
        settings.scheduling_algorithm,
        settings.work_hours_per_week,
    )
    return SettingsResponse(**settings.to_dict())


@router.patch("", response_model=SettingsResponse)
async def patch_settings(
    settings_in: SettingsUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """Partially update application settings."""
    settings = await get_or_create_settings(db)

    # Only update provided fields
    update_data = settings_in.model_dump(exclude_unset=True)
    if not update_data:
        return SettingsResponse(**settings.to_dict())

    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(settings)

    logger.info("Settings patched: %s", list(update_data.keys()))
    return SettingsResponse(**settings.to_dict())


@router.delete("", status_code=204)
async def reset_settings(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_admin_user),
):
    """Reset settings to defaults."""
    settings = await get_or_create_settings(db)

    # Reset all fields to defaults
    for field, value in DEFAULT_SETTINGS.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    await db.commit()

    logger.info("Settings reset to defaults")
