"""Tests for simulation metrics (pure logic, no DB)."""

import pytest

from app.resilience.simulation.metrics import (
    MetricsCollector,
    MetricsSummary,
    SimulationMetrics,
    TimeSeriesPoint,
)


# -- TimeSeriesPoint dataclass -----------------------------------------------


class TestTimeSeriesPoint:
    def test_creation(self):
        p = TimeSeriesPoint(time=1.0, value=42.0)
        assert p.time == 1.0
        assert p.value == 42.0
        assert p.label is None

    def test_with_label(self):
        p = TimeSeriesPoint(time=2.0, value=10.0, label="test")
        assert p.label == "test"


# -- MetricsSummary dataclass ------------------------------------------------


class TestMetricsSummary:
    def test_creation(self):
        s = MetricsSummary(
            name="test",
            count=10,
            mean=5.0,
            std=1.0,
            min_val=1.0,
            max_val=10.0,
            p25=3.0,
            p50=5.0,
            p75=7.0,
            p95=9.0,
            p99=10.0,
        )
        assert s.name == "test"
        assert s.count == 10
        assert s.mean == 5.0
        assert s.p50 == 5.0


# -- MetricsCollector init ---------------------------------------------------


class TestMetricsCollectorInit:
    def test_empty_init(self):
        mc = MetricsCollector()
        assert mc._time_series == {}
        assert mc._counters == {}
        assert mc._events == []
        assert mc._gauges == {}


# -- record_value / get_time_series ------------------------------------------


class TestRecordValue:
    def test_record_single_value(self):
        mc = MetricsCollector()
        mc.record_value("cpu", 1.0, 75.0)
        series = mc.get_time_series("cpu")
        assert len(series) == 1
        assert series[0].time == 1.0
        assert series[0].value == 75.0

    def test_record_multiple_values(self):
        mc = MetricsCollector()
        mc.record_value("cpu", 1.0, 75.0)
        mc.record_value("cpu", 2.0, 80.0)
        mc.record_value("cpu", 3.0, 70.0)
        assert len(mc.get_time_series("cpu")) == 3

    def test_record_with_label(self):
        mc = MetricsCollector()
        mc.record_value("load", 1.0, 50.0, label="zone_a")
        series = mc.get_time_series("load")
        assert series[0].label == "zone_a"

    def test_get_nonexistent_metric(self):
        mc = MetricsCollector()
        assert mc.get_time_series("missing") == []

    def test_multiple_metrics(self):
        mc = MetricsCollector()
        mc.record_value("cpu", 1.0, 75.0)
        mc.record_value("mem", 1.0, 60.0)
        assert len(mc.get_time_series("cpu")) == 1
        assert len(mc.get_time_series("mem")) == 1


# -- increment / decrement / get_counter ------------------------------------


class TestCounters:
    def test_increment_new(self):
        mc = MetricsCollector()
        mc.increment("errors")
        assert mc.get_counter("errors") == 1

    def test_increment_multiple(self):
        mc = MetricsCollector()
        mc.increment("errors")
        mc.increment("errors")
        mc.increment("errors")
        assert mc.get_counter("errors") == 3

    def test_increment_by_amount(self):
        mc = MetricsCollector()
        mc.increment("errors", amount=5)
        assert mc.get_counter("errors") == 5

    def test_decrement(self):
        mc = MetricsCollector()
        mc.increment("active", amount=10)
        mc.decrement("active", amount=3)
        assert mc.get_counter("active") == 7

    def test_decrement_new_counter(self):
        mc = MetricsCollector()
        mc.decrement("active")
        assert mc.get_counter("active") == -1

    def test_get_nonexistent_counter(self):
        mc = MetricsCollector()
        assert mc.get_counter("missing") == 0


# -- set_gauge / get_gauge ---------------------------------------------------


class TestGauges:
    def test_set_and_get(self):
        mc = MetricsCollector()
        mc.set_gauge("temperature", 98.6)
        assert mc.get_gauge("temperature") == 98.6

    def test_overwrite_gauge(self):
        mc = MetricsCollector()
        mc.set_gauge("temperature", 98.6)
        mc.set_gauge("temperature", 100.0)
        assert mc.get_gauge("temperature") == 100.0

    def test_get_nonexistent_gauge(self):
        mc = MetricsCollector()
        assert mc.get_gauge("missing") is None


# -- record_event / get_events -----------------------------------------------


class TestEvents:
    def test_record_event(self):
        mc = MetricsCollector()
        mc.record_event("alert", 5.0, {"level": "high"})
        events = mc.get_events()
        assert len(events) == 1
        assert events[0]["type"] == "alert"
        assert events[0]["time"] == 5.0
        assert events[0]["level"] == "high"

    def test_filter_by_type(self):
        mc = MetricsCollector()
        mc.record_event("alert", 1.0, {"level": "high"})
        mc.record_event("info", 2.0, {"msg": "ok"})
        mc.record_event("alert", 3.0, {"level": "low"})
        alerts = mc.get_events("alert")
        assert len(alerts) == 2
        infos = mc.get_events("info")
        assert len(infos) == 1

    def test_no_filter_returns_all(self):
        mc = MetricsCollector()
        mc.record_event("a", 1.0, {})
        mc.record_event("b", 2.0, {})
        assert len(mc.get_events()) == 2

    def test_filter_nonexistent_type(self):
        mc = MetricsCollector()
        mc.record_event("a", 1.0, {})
        assert mc.get_events("missing") == []

    def test_events_returns_copy(self):
        mc = MetricsCollector()
        mc.record_event("a", 1.0, {})
        events = mc.get_events()
        events.clear()
        assert len(mc.get_events()) == 1


# -- get_summary -------------------------------------------------------------


class TestGetSummary:
    def test_nonexistent_metric_returns_none(self):
        mc = MetricsCollector()
        assert mc.get_summary("missing") is None

    def test_single_value_summary(self):
        mc = MetricsCollector()
        mc.record_value("x", 1.0, 42.0)
        s = mc.get_summary("x")
        assert s is not None
        assert s.count == 1
        assert s.mean == 42.0
        assert s.std == 0.0
        assert s.min_val == 42.0
        assert s.max_val == 42.0

    def test_multi_value_summary(self):
        mc = MetricsCollector()
        for i in range(10):
            mc.record_value("x", float(i), float(i + 1))
        s = mc.get_summary("x")
        assert s is not None
        assert s.count == 10
        assert s.min_val == 1.0
        assert s.max_val == 10.0
        assert s.mean == pytest.approx(5.5)

    def test_percentiles_ordered(self):
        mc = MetricsCollector()
        for i in range(20):
            mc.record_value("x", float(i), float(i))
        s = mc.get_summary("x")
        assert s.p25 <= s.p50 <= s.p75 <= s.p95

    def test_summary_name(self):
        mc = MetricsCollector()
        mc.record_value("my_metric", 1.0, 5.0)
        s = mc.get_summary("my_metric")
        assert s.name == "my_metric"


# -- get_all_summaries -------------------------------------------------------


class TestGetAllSummaries:
    def test_empty(self):
        mc = MetricsCollector()
        assert mc.get_all_summaries() == {}

    def test_multiple_metrics(self):
        mc = MetricsCollector()
        mc.record_value("a", 1.0, 10.0)
        mc.record_value("b", 1.0, 20.0)
        summaries = mc.get_all_summaries()
        assert "a" in summaries
        assert "b" in summaries
        assert summaries["a"].mean == 10.0
        assert summaries["b"].mean == 20.0


# -- to_dict -----------------------------------------------------------------


class TestToDict:
    def test_empty_collector(self):
        mc = MetricsCollector()
        d = mc.to_dict()
        assert d == {
            "time_series": {},
            "counters": {},
            "gauges": {},
            "events": [],
        }

    def test_populated_collector(self):
        mc = MetricsCollector()
        mc.record_value("cpu", 1.0, 75.0, label="zone_a")
        mc.increment("errors")
        mc.set_gauge("temp", 98.6)
        mc.record_event("alert", 2.0, {"level": "high"})
        d = mc.to_dict()
        assert len(d["time_series"]["cpu"]) == 1
        assert d["counters"]["errors"] == 1
        assert d["gauges"]["temp"] == 98.6
        assert len(d["events"]) == 1

    def test_time_series_format(self):
        mc = MetricsCollector()
        mc.record_value("x", 1.0, 42.0, label="lbl")
        d = mc.to_dict()
        point = d["time_series"]["x"][0]
        assert point["time"] == 1.0
        assert point["value"] == 42.0
        assert point["label"] == "lbl"


# -- reset -------------------------------------------------------------------


class TestReset:
    def test_reset_clears_all(self):
        mc = MetricsCollector()
        mc.record_value("x", 1.0, 10.0)
        mc.increment("errors")
        mc.set_gauge("temp", 98.6)
        mc.record_event("alert", 1.0, {})
        mc.reset()
        assert mc.get_time_series("x") == []
        assert mc.get_counter("errors") == 0
        assert mc.get_gauge("temp") is None
        assert mc.get_events() == []


# -- SimulationMetrics -------------------------------------------------------


class TestSimulationMetricsInit:
    def test_init(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        assert sm.collector is mc


class TestRecordFacultyCount:
    def test_records_to_collector(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        sm.record_faculty_count(1.0, 25)
        series = mc.get_time_series("faculty_count")
        assert len(series) == 1
        assert series[0].value == 25.0


class TestRecordCoverageRate:
    def test_records_to_collector(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        sm.record_coverage_rate(1.0, 0.85)
        series = mc.get_time_series("coverage_rate")
        assert len(series) == 1
        assert series[0].value == 0.85


class TestRecordZoneStatus:
    def test_records_event(self):
        from uuid import uuid4

        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        zone_id = uuid4()
        sm.record_zone_status(1.0, zone_id, "degraded")
        events = mc.get_events("zone_status_change")
        assert len(events) == 1
        assert events[0]["status"] == "degraded"
        assert events[0]["zone_id"] == str(zone_id)


class TestRecordCascadeEvent:
    def test_increments_counter_and_records_event(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        sm.record_cascade_event(5.0, zones_affected=3)
        assert mc.get_counter("cascade_events") == 1
        events = mc.get_events("cascade")
        assert len(events) == 1
        assert events[0]["zones_affected"] == 3


class TestRecordBorrowingAttempt:
    def test_approved_increments_both(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        sm.record_borrowing_attempt(1.0, approved=True)
        assert mc.get_counter("borrowing_attempts") == 1
        assert mc.get_counter("borrowing_approved") == 1

    def test_denied_increments_attempts_only(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        sm.record_borrowing_attempt(1.0, approved=False)
        assert mc.get_counter("borrowing_attempts") == 1
        assert mc.get_counter("borrowing_approved") == 0


class TestCoverageAndFacultySummary:
    def test_coverage_summary(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        for i in range(5):
            sm.record_coverage_rate(float(i), 0.8 + i * 0.01)
        summary = sm.get_coverage_summary()
        assert summary is not None
        assert summary.count == 5

    def test_faculty_summary(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        for i in range(5):
            sm.record_faculty_count(float(i), 20 + i)
        summary = sm.get_faculty_summary()
        assert summary is not None
        assert summary.count == 5

    def test_no_data_returns_none(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        assert sm.get_coverage_summary() is None
        assert sm.get_faculty_summary() is None


class TestCascadeCount:
    def test_zero_initially(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        assert sm.cascade_count() == 0

    def test_counts_cascades(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        sm.record_cascade_event(1.0, 2)
        sm.record_cascade_event(2.0, 3)
        assert sm.cascade_count() == 2


class TestBorrowingSuccessRate:
    def test_no_attempts(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        assert sm.borrowing_success_rate() == 0.0

    def test_all_approved(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        sm.record_borrowing_attempt(1.0, True)
        sm.record_borrowing_attempt(2.0, True)
        assert sm.borrowing_success_rate() == 1.0

    def test_mixed(self):
        mc = MetricsCollector()
        sm = SimulationMetrics(mc)
        sm.record_borrowing_attempt(1.0, True)
        sm.record_borrowing_attempt(2.0, False)
        sm.record_borrowing_attempt(3.0, True)
        sm.record_borrowing_attempt(4.0, False)
        assert sm.borrowing_success_rate() == pytest.approx(0.5)
