"""Tests for threshold manager (pure logic, no DB)."""

import pytest

from app.resilience.engine.threshold_manager import (
    Threshold,
    ThresholdManager,
    ThresholdViolation,
)


# ── Threshold dataclass ───────────────────────────────────────────────


class TestThreshold:
    def test_creation(self):
        from datetime import datetime

        t = Threshold(
            name="utilization",
            lower_bound=0.5,
            upper_bound=0.95,
            warning_lower=0.6,
            warning_upper=0.9,
            critical_lower=0.5,
            critical_upper=0.95,
            last_updated=datetime(2026, 1, 15),
            sample_count=50,
            is_adaptive=True,
        )
        assert t.name == "utilization"
        assert t.lower_bound == 0.5
        assert t.upper_bound == 0.95
        assert t.is_adaptive is True
        assert t.sample_count == 50

    def test_none_bounds(self):
        from datetime import datetime

        t = Threshold(
            name="test",
            lower_bound=None,
            upper_bound=None,
            warning_lower=None,
            warning_upper=None,
            critical_lower=None,
            critical_upper=None,
            last_updated=datetime(2026, 1, 15),
            sample_count=0,
            is_adaptive=False,
        )
        assert t.lower_bound is None
        assert t.upper_bound is None


# ── ThresholdViolation dataclass ──────────────────────────────────────


class TestThresholdViolation:
    def test_creation(self):
        from datetime import datetime

        v = ThresholdViolation(
            threshold_name="utilization",
            value=0.98,
            bound_violated="critical_upper",
            severity="critical",
            timestamp=datetime(2026, 1, 15),
            message="utilization=0.98 above critical upper bound 0.95",
        )
        assert v.threshold_name == "utilization"
        assert v.value == 0.98
        assert v.severity == "critical"


# ── ThresholdManager init ────────────────────────────────────────────


class TestThresholdManagerInit:
    def test_empty_init(self):
        mgr = ThresholdManager()
        assert mgr.thresholds == {}
        assert mgr._historical_data == {}


# ── create_static_threshold ──────────────────────────────────────────


class TestCreateStaticThreshold:
    def test_basic_creation(self):
        mgr = ThresholdManager()
        t = mgr.create_static_threshold("util", lower_bound=0.5, upper_bound=0.95)
        assert isinstance(t, Threshold)
        assert t.name == "util"
        assert t.lower_bound == 0.5
        assert t.upper_bound == 0.95
        assert t.is_adaptive is False

    def test_stored_in_manager(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("test")
        assert "test" in mgr.thresholds

    def test_no_bounds(self):
        mgr = ThresholdManager()
        t = mgr.create_static_threshold("open")
        assert t.lower_bound is None
        assert t.upper_bound is None
        assert t.warning_lower is None
        assert t.warning_upper is None
        assert t.critical_lower is None
        assert t.critical_upper is None

    def test_all_bounds(self):
        mgr = ThresholdManager()
        t = mgr.create_static_threshold(
            "full",
            lower_bound=0.0,
            upper_bound=1.0,
            warning_lower=0.2,
            warning_upper=0.8,
            critical_lower=0.1,
            critical_upper=0.9,
        )
        assert t.warning_lower == 0.2
        assert t.critical_upper == 0.9

    def test_sample_count_zero(self):
        mgr = ThresholdManager()
        t = mgr.create_static_threshold("test")
        assert t.sample_count == 0


# ── create_adaptive_threshold ────────────────────────────────────────


class TestCreateAdaptiveThreshold:
    def test_basic_creation(self):
        mgr = ThresholdManager()
        samples = [10.0, 11.0, 12.0, 9.0, 10.0, 11.0]
        t = mgr.create_adaptive_threshold("metric", samples)
        assert isinstance(t, Threshold)
        assert t.is_adaptive is True
        assert t.sample_count == 6

    def test_limits_calculated(self):
        mgr = ThresholdManager()
        samples = [10.0, 10.0, 10.0, 10.0, 10.0]  # Zero std
        t = mgr.create_adaptive_threshold("metric", samples)
        assert t.upper_bound == t.lower_bound  # std=0 → limits at mean

    def test_insufficient_samples_raises(self):
        mgr = ThresholdManager()
        with pytest.raises(ValueError, match="at least 5"):
            mgr.create_adaptive_threshold("metric", [1.0, 2.0])

    def test_stored_in_manager(self):
        mgr = ThresholdManager()
        samples = [10.0, 11.0, 12.0, 9.0, 10.0]
        mgr.create_adaptive_threshold("test", samples)
        assert "test" in mgr.thresholds
        assert "test" in mgr._historical_data

    def test_historical_data_stored(self):
        mgr = ThresholdManager()
        samples = [10.0, 11.0, 12.0, 9.0, 10.0]
        mgr.create_adaptive_threshold("test", samples)
        assert len(mgr._historical_data["test"]) == 5

    def test_custom_sigma_multiplier(self):
        mgr = ThresholdManager()
        samples = [10.0, 12.0, 8.0, 11.0, 9.0, 10.0]
        t_3sigma = mgr.create_adaptive_threshold("t3", samples, sigma_multiplier=3.0)
        mgr2 = ThresholdManager()
        t_2sigma = mgr2.create_adaptive_threshold("t2", samples, sigma_multiplier=2.0)
        # 3-sigma limits should be wider than 2-sigma
        assert t_3sigma.upper_bound > t_2sigma.upper_bound

    def test_upper_above_lower(self):
        mgr = ThresholdManager()
        samples = [10.0, 12.0, 8.0, 11.0, 9.0]
        t = mgr.create_adaptive_threshold("test", samples)
        assert t.upper_bound >= t.lower_bound


# ── update_adaptive_threshold ────────────────────────────────────────


class TestUpdateAdaptiveThreshold:
    def test_basic_update(self):
        mgr = ThresholdManager()
        mgr.create_adaptive_threshold("m", [10.0, 11.0, 12.0, 9.0, 10.0])
        t = mgr.update_adaptive_threshold("m", [13.0, 14.0])
        assert t.sample_count == 7

    def test_not_found_raises(self):
        mgr = ThresholdManager()
        with pytest.raises(ValueError, match="not found"):
            mgr.update_adaptive_threshold("nonexistent", [1.0])

    def test_not_adaptive_raises(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("static", lower_bound=0.0, upper_bound=1.0)
        with pytest.raises(ValueError, match="not adaptive"):
            mgr.update_adaptive_threshold("static", [0.5])

    def test_max_history_enforced(self):
        mgr = ThresholdManager()
        mgr.create_adaptive_threshold("m", [10.0] * 10)
        mgr.update_adaptive_threshold("m", [11.0] * 50, max_history=20)
        assert len(mgr._historical_data["m"]) <= 20

    def test_limits_shift_with_new_data(self):
        mgr = ThresholdManager()
        mgr.create_adaptive_threshold("m", [10.0, 10.0, 10.0, 10.0, 10.0])
        old_upper = mgr.thresholds["m"].upper_bound
        # Add much higher values
        mgr.update_adaptive_threshold("m", [20.0, 20.0, 20.0, 20.0, 20.0])
        new_upper = mgr.thresholds["m"].upper_bound
        assert new_upper > old_upper


# ── check_threshold ──────────────────────────────────────────────────


class TestCheckThreshold:
    def test_in_bounds_returns_none(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", lower_bound=0.0, upper_bound=100.0)
        assert mgr.check_threshold("t", 50.0) is None

    def test_not_found_raises(self):
        mgr = ThresholdManager()
        with pytest.raises(ValueError, match="not found"):
            mgr.check_threshold("nonexistent", 10.0)

    def test_above_critical_upper(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", critical_upper=90.0)
        v = mgr.check_threshold("t", 95.0)
        assert v is not None
        assert v.severity == "critical"
        assert v.bound_violated == "critical_upper"

    def test_below_critical_lower(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", critical_lower=10.0)
        v = mgr.check_threshold("t", 5.0)
        assert v is not None
        assert v.severity == "critical"
        assert v.bound_violated == "critical_lower"

    def test_above_warning_upper(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", warning_upper=80.0)
        v = mgr.check_threshold("t", 85.0)
        assert v is not None
        assert v.severity == "warning"
        assert v.bound_violated == "warning_upper"

    def test_below_warning_lower(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", warning_lower=20.0)
        v = mgr.check_threshold("t", 15.0)
        assert v is not None
        assert v.severity == "warning"
        assert v.bound_violated == "warning_lower"

    def test_above_upper_bound(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", upper_bound=100.0)
        v = mgr.check_threshold("t", 105.0)
        assert v is not None
        assert v.bound_violated == "upper"

    def test_below_lower_bound(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", lower_bound=0.0)
        v = mgr.check_threshold("t", -5.0)
        assert v is not None
        assert v.bound_violated == "lower"

    def test_critical_checked_before_warning(self):
        """Critical bounds are checked before warning bounds."""
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", critical_upper=90.0, warning_upper=80.0)
        v = mgr.check_threshold("t", 95.0)
        assert v.bound_violated == "critical_upper"

    def test_none_bounds_not_checked(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t")  # All bounds None
        assert mgr.check_threshold("t", 1000.0) is None
        assert mgr.check_threshold("t", -1000.0) is None

    def test_violation_has_message(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t", critical_upper=90.0)
        v = mgr.check_threshold("t", 95.0)
        assert "t" in v.message
        assert "95" in v.message

    def test_adaptive_threshold_checked(self):
        mgr = ThresholdManager()
        mgr.create_adaptive_threshold("m", [10.0, 10.0, 10.0, 10.0, 10.0])
        # With std=0, all limits are at mean=10.0
        v = mgr.check_threshold("m", 15.0)
        assert v is not None


# ── get_threshold ────────────────────────────────────────────────────


class TestGetThreshold:
    def test_existing(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t")
        assert mgr.get_threshold("t") is not None
        assert mgr.get_threshold("t").name == "t"

    def test_nonexistent(self):
        mgr = ThresholdManager()
        assert mgr.get_threshold("missing") is None


# ── list_thresholds ──────────────────────────────────────────────────


class TestListThresholds:
    def test_empty(self):
        mgr = ThresholdManager()
        assert mgr.list_thresholds() == []

    def test_multiple(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("a")
        mgr.create_static_threshold("b")
        result = mgr.list_thresholds()
        assert len(result) == 2
        names = {t.name for t in result}
        assert names == {"a", "b"}


# ── delete_threshold ─────────────────────────────────────────────────


class TestDeleteThreshold:
    def test_delete_existing(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t")
        assert mgr.delete_threshold("t") is True
        assert mgr.get_threshold("t") is None

    def test_delete_nonexistent(self):
        mgr = ThresholdManager()
        assert mgr.delete_threshold("missing") is False

    def test_delete_cleans_history(self):
        mgr = ThresholdManager()
        mgr.create_adaptive_threshold("m", [10.0] * 5)
        assert "m" in mgr._historical_data
        mgr.delete_threshold("m")
        assert "m" not in mgr._historical_data

    def test_delete_static_no_history(self):
        mgr = ThresholdManager()
        mgr.create_static_threshold("t")
        assert mgr.delete_threshold("t") is True
