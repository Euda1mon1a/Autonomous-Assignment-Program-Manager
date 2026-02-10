"""Tests for QUBO solver fatigue integration (no DB)."""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.frms.qubo_integration import (
    FatigueQUBOConfig,
    FatigueQUBOIntegration,
    create_fatigue_qubo_solver,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _block(d: date, tod: str = "AM") -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), date=d, time_of_day=tod)


# ---------------------------------------------------------------------------
# FatigueQUBOConfig — defaults
# ---------------------------------------------------------------------------


class TestFatigueQUBOConfigDefaults:
    def test_fatigue_penalty_base(self):
        cfg = FatigueQUBOConfig()
        assert cfg.fatigue_penalty_base == 100.0

    def test_wocl_penalty_multiplier(self):
        cfg = FatigueQUBOConfig()
        assert cfg.wocl_penalty_multiplier == 2.0

    def test_consecutive_day_penalty(self):
        cfg = FatigueQUBOConfig()
        assert cfg.consecutive_day_penalty == 50.0

    def test_night_shift_cluster_bonus_is_negative(self):
        cfg = FatigueQUBOConfig()
        assert cfg.night_shift_cluster_bonus < 0

    def test_effectiveness_threshold(self):
        cfg = FatigueQUBOConfig()
        assert cfg.effectiveness_threshold == 77.0

    def test_critical_threshold(self):
        cfg = FatigueQUBOConfig()
        assert cfg.critical_threshold == 70.0

    def test_all_features_enabled(self):
        cfg = FatigueQUBOConfig()
        assert cfg.enable_circadian is True
        assert cfg.enable_consecutive_days is True
        assert cfg.enable_night_clustering is True
        assert cfg.enable_recovery_requirements is True


# ---------------------------------------------------------------------------
# FatigueQUBOConfig — custom values
# ---------------------------------------------------------------------------


class TestFatigueQUBOConfigCustom:
    def test_custom_penalty_base(self):
        cfg = FatigueQUBOConfig(fatigue_penalty_base=200.0)
        assert cfg.fatigue_penalty_base == 200.0

    def test_custom_thresholds(self):
        cfg = FatigueQUBOConfig(
            effectiveness_threshold=80.0,
            critical_threshold=65.0,
        )
        assert cfg.effectiveness_threshold == 80.0
        assert cfg.critical_threshold == 65.0

    def test_disable_features(self):
        cfg = FatigueQUBOConfig(
            enable_circadian=False,
            enable_consecutive_days=False,
            enable_night_clustering=False,
            enable_recovery_requirements=False,
        )
        assert cfg.enable_circadian is False
        assert cfg.enable_consecutive_days is False
        assert cfg.enable_night_clustering is False
        assert cfg.enable_recovery_requirements is False


# ---------------------------------------------------------------------------
# FatigueQUBOIntegration — construction
# ---------------------------------------------------------------------------


class TestFatigueQUBOIntegrationInit:
    def test_default_config(self):
        integ = FatigueQUBOIntegration()
        assert integ.config.fatigue_penalty_base == 100.0

    def test_custom_config(self):
        cfg = FatigueQUBOConfig(fatigue_penalty_base=500.0)
        integ = FatigueQUBOIntegration(config=cfg)
        assert integ.config.fatigue_penalty_base == 500.0

    def test_has_model(self):
        integ = FatigueQUBOIntegration()
        assert integ.model is not None

    def test_has_predictor(self):
        integ = FatigueQUBOIntegration()
        assert integ.predictor is not None

    def test_empty_cache(self):
        integ = FatigueQUBOIntegration()
        assert len(integ._effectiveness_cache) == 0


# ---------------------------------------------------------------------------
# FatigueQUBOIntegration._calculate_fatigue_penalty
# ---------------------------------------------------------------------------


class TestCalculateFatiguePenalty:
    def setup_method(self):
        self.integ = FatigueQUBOIntegration()

    def test_above_threshold_returns_zero(self):
        # effectiveness >= 77 → no penalty
        assert self.integ._calculate_fatigue_penalty(77.0) == 0.0

    def test_well_above_threshold_returns_zero(self):
        assert self.integ._calculate_fatigue_penalty(95.0) == 0.0

    def test_at_100_returns_zero(self):
        assert self.integ._calculate_fatigue_penalty(100.0) == 0.0

    def test_caution_zone_linear(self):
        # 70 <= eff < 77 → linear: base * gap/10
        # eff=72, gap=5, penalty = 100 * 5/10 = 50
        result = self.integ._calculate_fatigue_penalty(72.0)
        assert abs(result - 50.0) < 0.01

    def test_at_critical_threshold(self):
        # eff=70 → gap=7, linear: 100 * 7/10 = 70
        result = self.integ._calculate_fatigue_penalty(70.0)
        assert abs(result - 70.0) < 0.01

    def test_below_critical_threshold_quadratic(self):
        # eff=67 → gap=10, below critical, quadratic: 100 * (10/10)² = 100
        result = self.integ._calculate_fatigue_penalty(67.0)
        assert abs(result - 100.0) < 0.01

    def test_very_low_effectiveness_high_penalty(self):
        # eff=57 → gap=20, quadratic: 100 * (20/10)² = 400
        result = self.integ._calculate_fatigue_penalty(57.0)
        assert abs(result - 400.0) < 0.01

    def test_just_below_threshold(self):
        # eff=76.9 → gap=0.1, linear: 100 * 0.1/10 = 1.0
        result = self.integ._calculate_fatigue_penalty(76.9)
        assert abs(result - 1.0) < 0.01

    def test_penalty_increases_as_effectiveness_drops(self):
        high = self.integ._calculate_fatigue_penalty(75.0)
        medium = self.integ._calculate_fatigue_penalty(72.0)
        low = self.integ._calculate_fatigue_penalty(60.0)
        assert high < medium < low

    def test_custom_config_thresholds(self):
        cfg = FatigueQUBOConfig(
            fatigue_penalty_base=200.0,
            effectiveness_threshold=80.0,
            critical_threshold=70.0,
        )
        integ = FatigueQUBOIntegration(config=cfg)
        # eff=80 → at threshold → no penalty
        assert integ._calculate_fatigue_penalty(80.0) == 0.0
        # eff=75 → gap=5, linear: 200 * 5/10 = 100
        assert abs(integ._calculate_fatigue_penalty(75.0) - 100.0) < 0.01


# ---------------------------------------------------------------------------
# FatigueQUBOIntegration._calculate_gap_hours
# ---------------------------------------------------------------------------


class TestCalculateGapHours:
    def setup_method(self):
        self.integ = FatigueQUBOIntegration()

    def test_same_day_am_to_pm(self):
        # AM ends 13:00, PM starts 13:00 → gap = 0
        b1 = _block(date(2026, 1, 1), "AM")
        b2 = _block(date(2026, 1, 1), "PM")
        assert self.integ._calculate_gap_hours(b1, b2) == 0.0

    def test_same_day_pm_to_am_negative_clamped(self):
        # PM ends 19:00, AM starts 7:00 on SAME day → negative → clamped to 0
        b1 = _block(date(2026, 1, 1), "PM")
        b2 = _block(date(2026, 1, 1), "AM")
        assert self.integ._calculate_gap_hours(b1, b2) == 0.0

    def test_consecutive_day_am_to_am(self):
        # Day 1 AM ends 13:00, Day 2 AM starts 7:00
        # gap = 24 + (7-13) = 24 - 6 = 18
        b1 = _block(date(2026, 1, 1), "AM")
        b2 = _block(date(2026, 1, 2), "AM")
        assert self.integ._calculate_gap_hours(b1, b2) == 18.0

    def test_consecutive_day_pm_to_am(self):
        # Day 1 PM ends 19:00, Day 2 AM starts 7:00
        # gap = 24 + (7-19) = 24 - 12 = 12
        b1 = _block(date(2026, 1, 1), "PM")
        b2 = _block(date(2026, 1, 2), "AM")
        assert self.integ._calculate_gap_hours(b1, b2) == 12.0

    def test_consecutive_day_am_to_pm(self):
        # Day 1 AM ends 13:00, Day 2 PM starts 13:00
        # gap = 24 + (13-13) = 24
        b1 = _block(date(2026, 1, 1), "AM")
        b2 = _block(date(2026, 1, 2), "PM")
        assert self.integ._calculate_gap_hours(b1, b2) == 24.0

    def test_consecutive_day_pm_to_pm(self):
        # Day 1 PM ends 19:00, Day 2 PM starts 13:00
        # gap = 24 + (13-19) = 24 - 6 = 18
        b1 = _block(date(2026, 1, 1), "PM")
        b2 = _block(date(2026, 1, 2), "PM")
        assert self.integ._calculate_gap_hours(b1, b2) == 18.0

    def test_two_day_gap(self):
        # Day 1 AM ends 13:00, Day 3 AM starts 7:00
        # gap = 48 + (7-13) = 48 - 6 = 42
        b1 = _block(date(2026, 1, 1), "AM")
        b2 = _block(date(2026, 1, 3), "AM")
        assert self.integ._calculate_gap_hours(b1, b2) == 42.0

    def test_returns_float(self):
        b1 = _block(date(2026, 1, 1), "AM")
        b2 = _block(date(2026, 1, 2), "AM")
        result = self.integ._calculate_gap_hours(b1, b2)
        assert isinstance(result, (int, float))

    def test_default_tod_assumed_am(self):
        # Block without time_of_day → defaults to AM
        b1 = SimpleNamespace(id=uuid4(), date=date(2026, 1, 1))
        b2 = SimpleNamespace(id=uuid4(), date=date(2026, 1, 2))
        # AM→AM gap = 18
        assert self.integ._calculate_gap_hours(b1, b2) == 18.0


# ---------------------------------------------------------------------------
# FatigueQUBOIntegration._predict_effectiveness — caching
# ---------------------------------------------------------------------------


class TestPredictEffectiveness:
    def test_returns_float(self):
        integ = FatigueQUBOIntegration()
        pid = uuid4()
        result = integ._predict_effectiveness(pid, date(2026, 1, 1), "AM")
        assert isinstance(result, float)

    def test_value_in_range(self):
        integ = FatigueQUBOIntegration()
        pid = uuid4()
        result = integ._predict_effectiveness(pid, date(2026, 1, 1), "AM")
        assert 0.0 <= result <= 100.0

    def test_cached_on_second_call(self):
        integ = FatigueQUBOIntegration()
        pid = uuid4()
        r1 = integ._predict_effectiveness(pid, date(2026, 1, 1), "AM")
        r2 = integ._predict_effectiveness(pid, date(2026, 1, 1), "AM")
        assert r1 == r2
        assert len(integ._effectiveness_cache) == 1

    def test_different_dates_different_keys(self):
        integ = FatigueQUBOIntegration()
        pid = uuid4()
        integ._predict_effectiveness(pid, date(2026, 1, 1), "AM")
        integ._predict_effectiveness(pid, date(2026, 1, 2), "AM")
        assert len(integ._effectiveness_cache) == 2

    def test_different_tod_different_keys(self):
        integ = FatigueQUBOIntegration()
        pid = uuid4()
        integ._predict_effectiveness(pid, date(2026, 1, 1), "AM")
        integ._predict_effectiveness(pid, date(2026, 1, 1), "PM")
        assert len(integ._effectiveness_cache) == 2


# ---------------------------------------------------------------------------
# create_fatigue_qubo_solver
# ---------------------------------------------------------------------------


class TestCreateFatigueQUBOSolver:
    def test_returns_solver_wrapper(self):
        base = SimpleNamespace(solve=lambda ctx, ea=None: None)
        wrapped = create_fatigue_qubo_solver(base)
        assert wrapped is not None
        assert hasattr(wrapped, "solve")

    def test_with_custom_config(self):
        base = SimpleNamespace(solve=lambda ctx, ea=None: None)
        cfg = FatigueQUBOConfig(fatigue_penalty_base=999.0)
        wrapped = create_fatigue_qubo_solver(base, config=cfg)
        assert wrapped.integration.config.fatigue_penalty_base == 999.0

    def test_wrapper_has_solver_and_integration(self):
        base = SimpleNamespace(solve=lambda ctx, ea=None: None)
        wrapped = create_fatigue_qubo_solver(base)
        assert hasattr(wrapped, "solver")
        assert hasattr(wrapped, "integration")
        assert isinstance(wrapped.integration, FatigueQUBOIntegration)


# ---------------------------------------------------------------------------
# Integration: penalty + gap combined scenarios
# ---------------------------------------------------------------------------


class TestPenaltyGapCombined:
    def setup_method(self):
        self.integ = FatigueQUBOIntegration()

    def test_high_effectiveness_zero_penalty_regardless_of_gap(self):
        # Even with short gap, if effectiveness is high → no penalty
        assert self.integ._calculate_fatigue_penalty(90.0) == 0.0

    def test_short_gap_between_blocks(self):
        # Same day AM→PM → 0 hour gap → recovery concern
        b1 = _block(date(2026, 1, 1), "AM")
        b2 = _block(date(2026, 1, 1), "PM")
        gap = self.integ._calculate_gap_hours(b1, b2)
        assert gap < 10.0  # Below MIN_RECOVERY_HOURS

    def test_adequate_gap_between_blocks(self):
        # Consecutive day PM→AM → 12 hour gap → adequate recovery
        b1 = _block(date(2026, 1, 1), "PM")
        b2 = _block(date(2026, 1, 2), "AM")
        gap = self.integ._calculate_gap_hours(b1, b2)
        assert gap >= 10.0  # Above MIN_RECOVERY_HOURS
