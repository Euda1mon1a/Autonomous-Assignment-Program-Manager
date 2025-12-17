
from pydantic import BaseModel, Field


class SettingsBase(BaseModel):
    scheduling_algorithm: str = Field(default="greedy", description="Algorithm: greedy, min_conflicts, cp_sat")
    work_hours_per_week: int = Field(default=80, ge=40, le=100)
    max_consecutive_days: int = Field(default=6, ge=1, le=7)
    min_days_off_per_week: int = Field(default=1, ge=1, le=3)
    pgy1_supervision_ratio: str = Field(default="1:2")
    pgy2_supervision_ratio: str = Field(default="1:4")
    pgy3_supervision_ratio: str = Field(default="1:4")
    enable_weekend_scheduling: bool = True
    enable_holiday_scheduling: bool = False
    default_block_duration_hours: int = Field(default=4, ge=1, le=12)

class SettingsCreate(SettingsBase):
    pass

class SettingsUpdate(BaseModel):
    scheduling_algorithm: str | None = None
    work_hours_per_week: int | None = None
    max_consecutive_days: int | None = None
    min_days_off_per_week: int | None = None
    pgy1_supervision_ratio: str | None = None
    pgy2_supervision_ratio: str | None = None
    pgy3_supervision_ratio: str | None = None
    enable_weekend_scheduling: bool | None = None
    enable_holiday_scheduling: bool | None = None
    default_block_duration_hours: int | None = None

class SettingsResponse(SettingsBase):
    class Config:
        from_attributes = True
