from datetime import date

from pydantic import ConfigDict, BaseModel, Field


class SettingsBase(BaseModel):
    scheduling_algorithm: str = Field(
        default="cp_sat",
        description="Algorithm (cp_sat is canonical; other values allowed only in DEBUG)",
    )
    work_hours_per_week: int = Field(default=80, ge=40, le=100)
    max_consecutive_days: int = Field(default=6, ge=1, le=7)
    min_days_off_per_week: int = Field(default=1, ge=1, le=3)
    pgy1_supervision_ratio: str = Field(default="1:2")
    pgy2_supervision_ratio: str = Field(default="1:4")
    pgy3_supervision_ratio: str = Field(default="1:4")
    enable_weekend_scheduling: bool = True
    enable_holiday_scheduling: bool = False
    default_block_duration_hours: int = Field(default=4, ge=1, le=12)
    schedule_lock_date: date | None = Field(
        default=None,
        description="Lock date for system-initiated changes (null = no lock)",
    )
    overnight_call_weekdays: list[int] = Field(
        default=[0, 1, 2, 3, 6],
        description="Weekdays requiring overnight call coverage (0=Mon, 6=Sun)",
    )
    fmit_week_start_weekday: int = Field(
        default=4,
        ge=0,
        le=6,
        description="Weekday FMIT week starts (4=Friday)",
    )


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
    schedule_lock_date: date | None = None
    overnight_call_weekdays: list[int] | None = None
    fmit_week_start_weekday: int | None = None


class SettingsResponse(SettingsBase):
    model_config = ConfigDict(from_attributes=True)
