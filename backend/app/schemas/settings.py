"""Settings schemas."""
from typing import Optional
from pydantic import BaseModel, field_validator


class SettingsBase(BaseModel):
    """Base settings schema with ACGME and scheduling configuration."""

    # Scheduling algorithm
    scheduling_algorithm: str = "greedy"  # 'greedy', 'min_conflicts', 'cp_sat'

    # Work hours
    work_hours_per_week: int = 80  # ACGME max
    max_consecutive_days: int = 6  # Max days before required day off

    # Supervision ratios (faculty per N residents)
    pgy1_supervision_ratio: int = 2  # 1:2 for PGY-1
    pgy2_supervision_ratio: int = 4  # 1:4 for PGY-2/3

    # Academic year settings
    academic_year_start: Optional[str] = "2024-07-01"
    academic_year_end: Optional[str] = "2025-06-30"
    block_duration_days: int = 28

    @field_validator("scheduling_algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        valid_algorithms = ("greedy", "min_conflicts", "cp_sat")
        if v not in valid_algorithms:
            raise ValueError(f"scheduling_algorithm must be one of: {valid_algorithms}")
        return v

    @field_validator("work_hours_per_week")
    @classmethod
    def validate_work_hours(cls, v: int) -> int:
        if v < 1 or v > 168:
            raise ValueError("work_hours_per_week must be between 1 and 168")
        return v

    @field_validator("max_consecutive_days")
    @classmethod
    def validate_consecutive_days(cls, v: int) -> int:
        if v < 1 or v > 14:
            raise ValueError("max_consecutive_days must be between 1 and 14")
        return v

    @field_validator("pgy1_supervision_ratio", "pgy2_supervision_ratio")
    @classmethod
    def validate_supervision_ratio(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("supervision ratio must be between 1 and 10")
        return v

    @field_validator("block_duration_days")
    @classmethod
    def validate_block_duration(cls, v: int) -> int:
        if v < 1 or v > 365:
            raise ValueError("block_duration_days must be between 1 and 365")
        return v


class SettingsCreate(SettingsBase):
    """Schema for creating/updating settings."""
    pass


class SettingsUpdate(BaseModel):
    """Schema for partial settings update."""
    scheduling_algorithm: Optional[str] = None
    work_hours_per_week: Optional[int] = None
    max_consecutive_days: Optional[int] = None
    pgy1_supervision_ratio: Optional[int] = None
    pgy2_supervision_ratio: Optional[int] = None
    academic_year_start: Optional[str] = None
    academic_year_end: Optional[str] = None
    block_duration_days: Optional[int] = None


class SettingsResponse(SettingsBase):
    """Schema for settings response."""

    class Config:
        from_attributes = True
