"""Tests for resilience Prometheus metrics (pure logic, no DB)."""

import pytest

from app.resilience.metrics import (
    PROMETHEUS_AVAILABLE,
    ResilienceMetrics,
    get_metrics,
    setup_metrics,
)


# -- Module-level flag -------------------------------------------------------


class TestPrometheusAvailable:
    def test_flag_is_bool(self):
        assert isinstance(PROMETHEUS_AVAILABLE, bool)


# -- ResilienceMetrics disabled mode -----------------------------------------


class TestResilienceMetricsDisabled:
    """Test that all methods are safe when prometheus is unavailable."""

    def _make_disabled(self):
        """Create a metrics instance with _enabled=False."""
        m = ResilienceMetrics.__new__(ResilienceMetrics)
        m._enabled = False
        return m

    def test_update_utilization_noop(self):
        m = self._make_disabled()
        m.update_utilization(0.5, "yellow")  # Should not raise

    def test_update_defense_level_noop(self):
        m = self._make_disabled()
        m.update_defense_level(3)

    def test_update_load_shedding_noop(self):
        m = self._make_disabled()
        m.update_load_shedding(2, suspended_count=5)

    def test_update_contingency_status_noop(self):
        m = self._make_disabled()
        m.update_contingency_status(True, False)

    def test_update_faculty_counts_noop(self):
        m = self._make_disabled()
        m.update_faculty_counts(total=20, on_duty=15, on_leave=5)

    def test_update_coverage_noop(self):
        m = self._make_disabled()
        m.update_coverage(0.95)

    def test_update_redundancy_noop(self):
        m = self._make_disabled()
        m.update_redundancy("surgery", 2)

    def test_update_active_fallbacks_noop(self):
        m = self._make_disabled()
        m.update_active_fallbacks(3)

    def test_record_crisis_activation_noop(self):
        m = self._make_disabled()
        m.record_crisis_activation("severe", "test")

    def test_record_fallback_activation_noop(self):
        m = self._make_disabled()
        m.record_fallback_activation("pcs_surge")

    def test_record_load_shedding_change_noop(self):
        m = self._make_disabled()
        m.record_load_shedding_change(0, 2)

    def test_record_defense_activation_noop(self):
        m = self._make_disabled()
        m.record_defense_activation(3, "activate_fallback")

    def test_record_health_check_failure_noop(self):
        m = self._make_disabled()
        m.record_health_check_failure("timeout")

    def test_time_health_check_returns_context_manager(self):
        m = self._make_disabled()
        ctx = m.time_health_check()
        with ctx:
            pass  # Should work as a no-op context manager

    def test_time_contingency_analysis_returns_context_manager(self):
        m = self._make_disabled()
        ctx = m.time_contingency_analysis()
        with ctx:
            pass


# -- ResilienceMetrics enabled mode (with prometheus_client) -----------------


@pytest.mark.skipif(
    not PROMETHEUS_AVAILABLE,
    reason="prometheus_client not installed",
)
class TestResilienceMetricsEnabled:
    def _make_metrics(self):
        """Create metrics with isolated registry."""
        from prometheus_client import CollectorRegistry

        registry = CollectorRegistry()
        return ResilienceMetrics(registry=registry)

    def test_enabled(self):
        m = self._make_metrics()
        assert m._enabled is True

    def test_update_utilization(self):
        m = self._make_metrics()
        m.update_utilization(0.75, "yellow", buffer=0.1, component="overall")
        val = m.utilization_rate.labels(component="overall")._value.get()
        assert val == pytest.approx(0.75)

    def test_update_utilization_level_map(self):
        m = self._make_metrics()
        m.update_utilization(0.5, "orange")
        val = m.utilization_level._value.get()
        assert val == 2  # orange=2

    def test_update_defense_level(self):
        m = self._make_metrics()
        m.update_defense_level(4)
        val = m.defense_level._value.get()
        assert val == 4

    def test_update_load_shedding(self):
        m = self._make_metrics()
        m.update_load_shedding(3, suspended_count=7)
        assert m.load_shedding_level._value.get() == 3
        assert m.suspended_activities._value.get() == 7

    def test_update_contingency_status_both_pass(self):
        m = self._make_metrics()
        m.update_contingency_status(True, True)
        assert m.n1_compliant._value.get() == 1
        assert m.n2_compliant._value.get() == 1

    def test_update_contingency_status_both_fail(self):
        m = self._make_metrics()
        m.update_contingency_status(False, False)
        assert m.n1_compliant._value.get() == 0
        assert m.n2_compliant._value.get() == 0

    def test_update_faculty_counts(self):
        m = self._make_metrics()
        m.update_faculty_counts(total=25, on_duty=18, on_leave=7)
        assert m.faculty_available.labels(type="total")._value.get() == 25
        assert m.faculty_available.labels(type="on_duty")._value.get() == 18
        assert m.faculty_available.labels(type="on_leave")._value.get() == 7

    def test_update_coverage(self):
        m = self._make_metrics()
        m.update_coverage(0.92)
        assert m.coverage_rate._value.get() == pytest.approx(0.92)

    def test_update_redundancy(self):
        m = self._make_metrics()
        m.update_redundancy("icu", 2)
        assert m.redundancy_level.labels(service="icu")._value.get() == 2

    def test_update_active_fallbacks(self):
        m = self._make_metrics()
        m.update_active_fallbacks(5)
        assert m.active_fallbacks._value.get() == 5

    def test_record_crisis_activation(self):
        m = self._make_metrics()
        m.record_crisis_activation("critical")
        val = m.crisis_activations.labels(severity="critical")._value.get()
        assert val == 1.0

    def test_record_fallback_activation(self):
        m = self._make_metrics()
        m.record_fallback_activation("mass_casualty")
        val = m.fallback_activations.labels(scenario="mass_casualty")._value.get()
        assert val == 1.0

    def test_record_load_shedding_change(self):
        m = self._make_metrics()
        m.record_load_shedding_change(0, 3)
        val = m.load_shedding_events.labels(from_level="0", to_level="3")._value.get()
        assert val == 1.0

    def test_record_defense_activation(self):
        m = self._make_metrics()
        m.record_defense_activation(2, "suspend_optional")
        val = m.defense_activations.labels(
            level="2", action="suspend_optional"
        )._value.get()
        assert val == 1.0

    def test_record_health_check_failure(self):
        m = self._make_metrics()
        m.record_health_check_failure("db_unreachable")
        val = m.health_check_failures.labels(reason="db_unreachable")._value.get()
        assert val == 1.0

    def test_time_health_check_context_manager(self):
        m = self._make_metrics()
        with m.time_health_check():
            pass  # Just verify it works as a context manager

    def test_time_contingency_analysis_context_manager(self):
        m = self._make_metrics()
        with m.time_contingency_analysis():
            pass

    def test_buffer_remaining(self):
        m = self._make_metrics()
        m.update_utilization(0.8, "red", buffer=0.05)
        assert m.buffer_remaining._value.get() == pytest.approx(0.05)

    def test_info_set(self):
        m = self._make_metrics()
        # Info metric should be set during init
        assert m.info is not None


# -- Global functions --------------------------------------------------------


class TestGlobalFunctions:
    def test_get_metrics_returns_instance(self):
        m = get_metrics()
        assert isinstance(m, ResilienceMetrics)

    def test_setup_metrics_returns_instance(self):
        m = setup_metrics()
        assert isinstance(m, ResilienceMetrics)

    @pytest.mark.skipif(
        not PROMETHEUS_AVAILABLE,
        reason="prometheus_client not installed",
    )
    def test_setup_metrics_with_registry(self):
        from prometheus_client import CollectorRegistry

        registry = CollectorRegistry()
        m = setup_metrics(registry=registry)
        assert m._enabled is True
