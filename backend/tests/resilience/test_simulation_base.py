"""Tests for simulation base module (pure logic, no DB)."""

import pytest
from datetime import datetime

from app.resilience.simulation.base import (
    SimulationConfig,
    SimulationResult,
)


# -- SimulationConfig defaults -----------------------------------------------


class TestSimulationConfigDefaults:
    def test_default_values(self):
        cfg = SimulationConfig()
        assert cfg.seed == 42
        assert cfg.duration_days == 365
        assert cfg.time_step_hours == 1.0
        assert cfg.initial_faculty_count == 10
        assert cfg.minimum_viable_count == 3
        assert cfg.zone_count == 6
        assert cfg.sick_call_probability == 0.02
        assert cfg.resignation_base_probability == 0.001
        assert cfg.pcs_probability == 0.0027
        assert cfg.recovery_time_hours == 4.0
        assert cfg.borrowing_enabled is True


# -- SimulationConfig validation ---------------------------------------------


class TestSimulationConfigValidation:
    def test_valid_config(self):
        cfg = SimulationConfig(
            seed=123,
            duration_days=30,
            time_step_hours=0.5,
            initial_faculty_count=20,
            minimum_viable_count=5,
            zone_count=4,
            sick_call_probability=0.05,
            resignation_base_probability=0.002,
            pcs_probability=0.003,
            recovery_time_hours=8.0,
            borrowing_enabled=False,
        )
        assert cfg.duration_days == 30

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError, match="duration_days must be positive"):
            SimulationConfig(duration_days=0)

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError, match="duration_days must be positive"):
            SimulationConfig(duration_days=-1)

    def test_zero_time_step_raises(self):
        with pytest.raises(ValueError, match="time_step_hours must be positive"):
            SimulationConfig(time_step_hours=0)

    def test_negative_time_step_raises(self):
        with pytest.raises(ValueError, match="time_step_hours must be positive"):
            SimulationConfig(time_step_hours=-0.5)

    def test_negative_faculty_count_raises(self):
        with pytest.raises(
            ValueError, match="initial_faculty_count cannot be negative"
        ):
            SimulationConfig(initial_faculty_count=-1)

    def test_zero_faculty_count_ok(self):
        cfg = SimulationConfig(initial_faculty_count=0)
        assert cfg.initial_faculty_count == 0

    def test_negative_minimum_viable_raises(self):
        with pytest.raises(ValueError, match="minimum_viable_count cannot be negative"):
            SimulationConfig(minimum_viable_count=-1)

    def test_zero_zone_count_raises(self):
        with pytest.raises(ValueError, match="zone_count must be at least 1"):
            SimulationConfig(zone_count=0)

    def test_sick_call_prob_out_of_range(self):
        with pytest.raises(ValueError, match="sick_call_probability"):
            SimulationConfig(sick_call_probability=1.5)
        with pytest.raises(ValueError, match="sick_call_probability"):
            SimulationConfig(sick_call_probability=-0.1)

    def test_resignation_prob_out_of_range(self):
        with pytest.raises(ValueError, match="resignation_base_probability"):
            SimulationConfig(resignation_base_probability=1.5)

    def test_pcs_prob_out_of_range(self):
        with pytest.raises(ValueError, match="pcs_probability"):
            SimulationConfig(pcs_probability=-0.01)

    def test_negative_recovery_time_raises(self):
        with pytest.raises(ValueError, match="recovery_time_hours cannot be negative"):
            SimulationConfig(recovery_time_hours=-1.0)

    def test_zero_recovery_time_ok(self):
        cfg = SimulationConfig(recovery_time_hours=0.0)
        assert cfg.recovery_time_hours == 0.0

    def test_boundary_probabilities(self):
        cfg = SimulationConfig(
            sick_call_probability=0.0,
            resignation_base_probability=0.0,
            pcs_probability=0.0,
        )
        assert cfg.sick_call_probability == 0.0

        cfg2 = SimulationConfig(
            sick_call_probability=1.0,
            resignation_base_probability=1.0,
            pcs_probability=1.0,
        )
        assert cfg2.sick_call_probability == 1.0


# -- SimulationResult -------------------------------------------------------


class TestSimulationResult:
    def _make_result(self, **overrides):
        defaults = {
            "config": SimulationConfig(),
            "started_at": datetime(2026, 1, 1, 0, 0, 0),
            "completed_at": datetime(2026, 1, 1, 0, 1, 0),
            "final_faculty_count": 8,
            "coverage_maintained": True,
            "days_until_failure": None,
            "cascade_events": 0,
            "total_sick_calls": 5,
            "total_departures": 2,
        }
        defaults.update(overrides)
        return SimulationResult(**defaults)

    def test_creation(self):
        r = self._make_result()
        assert r.final_faculty_count == 8
        assert r.coverage_maintained is True
        assert r.cascade_events == 0

    def test_duration_seconds(self):
        r = self._make_result(
            started_at=datetime(2026, 1, 1, 0, 0, 0),
            completed_at=datetime(2026, 1, 1, 0, 1, 30),
        )
        assert r.duration_seconds == 90.0

    def test_success_true(self):
        r = self._make_result(coverage_maintained=True, days_until_failure=None)
        assert r.success is True

    def test_success_false_coverage_lost(self):
        r = self._make_result(coverage_maintained=False, days_until_failure=100)
        assert r.success is False

    def test_success_false_days_until_failure_set(self):
        r = self._make_result(coverage_maintained=True, days_until_failure=50)
        assert r.success is False

    def test_metrics_default_empty(self):
        r = self._make_result()
        assert r.metrics == {}

    def test_custom_metrics(self):
        r = self._make_result(metrics={"avg_coverage": 0.85})
        assert r.metrics["avg_coverage"] == 0.85


# -- SimulationResult.to_dict ------------------------------------------------


class TestSimulationResultToDict:
    def _make_result(self, **overrides):
        defaults = {
            "config": SimulationConfig(seed=99, duration_days=30),
            "started_at": datetime(2026, 1, 1, 0, 0, 0),
            "completed_at": datetime(2026, 1, 1, 0, 0, 30),
            "final_faculty_count": 9,
            "coverage_maintained": True,
            "days_until_failure": None,
            "cascade_events": 1,
            "total_sick_calls": 10,
            "total_departures": 3,
            "metrics": {"test": True},
        }
        defaults.update(overrides)
        return SimulationResult(**defaults)

    def test_has_expected_keys(self):
        d = self._make_result().to_dict()
        expected = {
            "config",
            "started_at",
            "completed_at",
            "duration_seconds",
            "final_faculty_count",
            "coverage_maintained",
            "days_until_failure",
            "cascade_events",
            "total_sick_calls",
            "total_departures",
            "success",
            "metrics",
        }
        assert set(d.keys()) == expected

    def test_config_serialized(self):
        d = self._make_result().to_dict()
        assert d["config"]["seed"] == 99
        assert d["config"]["duration_days"] == 30
        assert "borrowing_enabled" in d["config"]

    def test_timestamps_iso_format(self):
        d = self._make_result().to_dict()
        assert "2026-01-01" in d["started_at"]
        assert "2026-01-01" in d["completed_at"]

    def test_success_included(self):
        d = self._make_result().to_dict()
        assert d["success"] is True

    def test_duration_seconds_included(self):
        d = self._make_result().to_dict()
        assert d["duration_seconds"] == 30.0

    def test_metrics_included(self):
        d = self._make_result().to_dict()
        assert d["metrics"]["test"] is True
