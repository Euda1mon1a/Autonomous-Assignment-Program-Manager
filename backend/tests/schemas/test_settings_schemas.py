"""Tests for settings schemas (Field bounds, defaults)."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.settings import SettingsBase, SettingsCreate, SettingsUpdate


class TestSettingsBase:
    def test_defaults(self):
        r = SettingsBase()
        assert r.scheduling_algorithm == "cp_sat"
        assert r.work_hours_per_week == 80
        assert r.max_consecutive_days == 6
        assert r.min_days_off_per_week == 1
        assert r.pgy1_supervision_ratio == "1:2"
        assert r.pgy2_supervision_ratio == "1:4"
        assert r.pgy3_supervision_ratio == "1:4"
        assert r.enable_weekend_scheduling is True
        assert r.enable_holiday_scheduling is False
        assert r.default_block_duration_hours == 4
        assert r.schedule_lock_date is None

    # --- work_hours_per_week ge=40, le=100 ---

    def test_work_hours_boundaries(self):
        r = SettingsBase(work_hours_per_week=40)
        assert r.work_hours_per_week == 40
        r = SettingsBase(work_hours_per_week=100)
        assert r.work_hours_per_week == 100

    def test_work_hours_below_min(self):
        with pytest.raises(ValidationError):
            SettingsBase(work_hours_per_week=39)

    def test_work_hours_above_max(self):
        with pytest.raises(ValidationError):
            SettingsBase(work_hours_per_week=101)

    # --- max_consecutive_days ge=1, le=7 ---

    def test_max_consecutive_days_boundaries(self):
        r = SettingsBase(max_consecutive_days=1)
        assert r.max_consecutive_days == 1
        r = SettingsBase(max_consecutive_days=7)
        assert r.max_consecutive_days == 7

    def test_max_consecutive_days_below_min(self):
        with pytest.raises(ValidationError):
            SettingsBase(max_consecutive_days=0)

    def test_max_consecutive_days_above_max(self):
        with pytest.raises(ValidationError):
            SettingsBase(max_consecutive_days=8)

    # --- min_days_off_per_week ge=1, le=3 ---

    def test_min_days_off_boundaries(self):
        r = SettingsBase(min_days_off_per_week=1)
        assert r.min_days_off_per_week == 1
        r = SettingsBase(min_days_off_per_week=3)
        assert r.min_days_off_per_week == 3

    def test_min_days_off_below_min(self):
        with pytest.raises(ValidationError):
            SettingsBase(min_days_off_per_week=0)

    def test_min_days_off_above_max(self):
        with pytest.raises(ValidationError):
            SettingsBase(min_days_off_per_week=4)

    # --- default_block_duration_hours ge=1, le=12 ---

    def test_block_duration_boundaries(self):
        r = SettingsBase(default_block_duration_hours=1)
        assert r.default_block_duration_hours == 1
        r = SettingsBase(default_block_duration_hours=12)
        assert r.default_block_duration_hours == 12

    def test_block_duration_below_min(self):
        with pytest.raises(ValidationError):
            SettingsBase(default_block_duration_hours=0)

    def test_block_duration_above_max(self):
        with pytest.raises(ValidationError):
            SettingsBase(default_block_duration_hours=13)

    def test_with_lock_date(self):
        r = SettingsBase(schedule_lock_date=date(2026, 6, 1))
        assert r.schedule_lock_date == date(2026, 6, 1)


class TestSettingsCreate:
    def test_inherits_base(self):
        r = SettingsCreate()
        assert r.work_hours_per_week == 80


class TestSettingsUpdate:
    def test_all_none(self):
        r = SettingsUpdate()
        assert r.scheduling_algorithm is None
        assert r.work_hours_per_week is None
        assert r.max_consecutive_days is None
        assert r.min_days_off_per_week is None
        assert r.enable_weekend_scheduling is None
        assert r.enable_holiday_scheduling is None
        assert r.default_block_duration_hours is None
        assert r.schedule_lock_date is None

    def test_partial_update(self):
        r = SettingsUpdate(work_hours_per_week=60, enable_holiday_scheduling=True)
        assert r.work_hours_per_week == 60
        assert r.enable_holiday_scheduling is True
