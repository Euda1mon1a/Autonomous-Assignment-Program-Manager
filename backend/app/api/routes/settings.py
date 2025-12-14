"""Settings API routes."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.schemas.settings import SettingsBase, SettingsUpdate, SettingsResponse

router = APIRouter()

# Settings file path (in production, use database)
SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "settings.json"

# Default settings matching SettingsBase
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


def load_settings() -> dict:
    """Load settings from file or return defaults."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except (json.JSONDecodeError, IOError):
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Save settings to file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


@router.get("", response_model=SettingsResponse)
def get_settings():
    """Get current application settings."""
    settings = load_settings()
    return SettingsResponse(**settings)


@router.post("", response_model=SettingsResponse)
def update_settings(settings_in: SettingsBase):
    """Update application settings (full replacement)."""
    settings_data = settings_in.model_dump()
    save_settings(settings_data)
    return SettingsResponse(**settings_data)


@router.patch("", response_model=SettingsResponse)
def patch_settings(settings_in: SettingsUpdate):
    """Partially update application settings."""
    current_settings = load_settings()
    update_data = settings_in.model_dump(exclude_unset=True)

    # Validate the merged settings
    merged = {**current_settings, **update_data}
    validated = SettingsBase(**merged)

    save_settings(validated.model_dump())
    return SettingsResponse(**validated.model_dump())


@router.delete("", status_code=204)
def reset_settings():
    """Reset settings to defaults."""
    save_settings(DEFAULT_SETTINGS.copy())
