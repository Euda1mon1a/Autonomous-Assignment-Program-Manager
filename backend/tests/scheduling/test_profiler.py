"""Tests for SchedulingProfiler and PhaseMetrics (pure logic, no DB required)."""

import time
from unittest.mock import patch

import pytest

from app.scheduling.profiler import PhaseMetrics, SchedulingProfiler


# ==================== PhaseMetrics Tests ====================


class TestPhaseMetrics:
    """Test PhaseMetrics dataclass."""

    def test_basic_construction(self):
        pm = PhaseMetrics(name="solving", start_time=100.0)
        assert pm.name == "solving"
        assert pm.start_time == 100.0
        assert pm.end_time is None
        assert pm.duration is None

    def test_defaults(self):
        pm = PhaseMetrics(name="test", start_time=0.0)
        assert pm.metrics == {}
        assert pm.memory_start is None
        assert pm.memory_end is None

    def test_finalize_computes_duration(self):
        pm = PhaseMetrics(name="phase1", start_time=10.0, end_time=15.5)
        pm.finalize()
        assert pm.duration == pytest.approx(5.5)

    def test_finalize_no_end_time(self):
        pm = PhaseMetrics(name="incomplete", start_time=10.0)
        pm.finalize()
        assert pm.duration is None

    def test_finalize_computes_memory_delta(self):
        pm = PhaseMetrics(
            name="mem_test",
            start_time=0.0,
            end_time=1.0,
            memory_start=100 * 1024 * 1024,  # 100 MB
            memory_end=150 * 1024 * 1024,  # 150 MB
        )
        pm.finalize()
        assert pm.metrics["memory_delta_mb"] == 50.0

    def test_finalize_no_memory_tracking(self):
        pm = PhaseMetrics(name="no_mem", start_time=0.0, end_time=1.0)
        pm.finalize()
        assert "memory_delta_mb" not in pm.metrics

    def test_finalize_memory_delta_rounded(self):
        pm = PhaseMetrics(
            name="round_test",
            start_time=0.0,
            end_time=1.0,
            memory_start=100 * 1024 * 1024,  # 100 MB
            memory_end=101.5 * 1024 * 1024,  # 101.5 MB
        )
        pm.finalize()
        assert pm.metrics["memory_delta_mb"] == 1.5

    def test_finalize_zero_memory_start_skips_delta(self):
        """When memory_start=0 (falsy), finalize skips memory delta."""
        pm = PhaseMetrics(
            name="zero_start",
            start_time=0.0,
            end_time=1.0,
            memory_start=0,
            memory_end=1024 * 1024,
        )
        pm.finalize()
        assert "memory_delta_mb" not in pm.metrics


# ==================== SchedulingProfiler Construction Tests ====================


class TestSchedulingProfilerInit:
    """Test SchedulingProfiler initialization."""

    def test_default_track_memory(self):
        p = SchedulingProfiler(track_memory=False)
        assert p.track_memory is False

    def test_initial_phases_empty(self):
        p = SchedulingProfiler(track_memory=False)
        assert p._phases == {}
        assert p._phase_stack == []
        assert p._metrics == {}

    def test_psutil_import_failure_disables_memory(self):
        with patch.dict("sys.modules", {"psutil": None}):
            p = SchedulingProfiler(track_memory=True)
            # psutil import fails -> memory tracking disabled
            assert p.track_memory is False


# ==================== Phase Timing Tests ====================


class TestPhaseTiming:
    """Test start_phase, end_phase, and context manager."""

    def test_start_phase_creates_entry(self):
        p = SchedulingProfiler(track_memory=False)
        p.start_phase("solving")
        assert "solving" in p._phases
        assert p._phases["solving"].name == "solving"
        assert p._phases["solving"].start_time > 0
        assert "solving" in p._phase_stack

    def test_end_phase_finalizes(self):
        p = SchedulingProfiler(track_memory=False)
        p.start_phase("solving")
        time.sleep(0.01)
        p.end_phase("solving")
        phase = p._phases["solving"]
        assert phase.end_time is not None
        assert phase.duration is not None
        assert phase.duration > 0
        assert "solving" not in p._phase_stack

    def test_end_unknown_phase_noop(self):
        p = SchedulingProfiler(track_memory=False)
        p.end_phase("nonexistent")  # Should not raise
        assert "nonexistent" not in p._phases

    def test_context_manager_auto_timing(self):
        p = SchedulingProfiler(track_memory=False)
        with p.phase("context_building"):
            time.sleep(0.01)
        phase = p._phases["context_building"]
        assert phase.duration is not None
        assert phase.duration > 0

    def test_context_manager_on_exception(self):
        p = SchedulingProfiler(track_memory=False)
        with pytest.raises(ValueError):
            with p.phase("failing_phase"):
                raise ValueError("test error")
        # Phase should still be finalized
        phase = p._phases["failing_phase"]
        assert phase.end_time is not None
        assert phase.duration is not None

    def test_multiple_phases(self):
        p = SchedulingProfiler(track_memory=False)
        with p.phase("phase_a"):
            time.sleep(0.01)
        with p.phase("phase_b"):
            time.sleep(0.01)
        assert "phase_a" in p._phases
        assert "phase_b" in p._phases
        assert p._phases["phase_a"].duration > 0
        assert p._phases["phase_b"].duration > 0

    def test_restart_phase_resets(self):
        p = SchedulingProfiler(track_memory=False)
        p.start_phase("redo")
        first_start = p._phases["redo"].start_time
        time.sleep(0.01)
        p.start_phase("redo")  # Reset
        second_start = p._phases["redo"].start_time
        assert second_start > first_start


# ==================== Custom Metrics Tests ====================


class TestCustomMetrics:
    """Test record_metric."""

    def test_record_numeric_metric(self):
        p = SchedulingProfiler(track_memory=False)
        p.record_metric("iterations", 500)
        assert p._metrics["iterations"] == 500

    def test_record_string_metric(self):
        p = SchedulingProfiler(track_memory=False)
        p.record_metric("algorithm", "cpsat")
        assert p._metrics["algorithm"] == "cpsat"

    def test_record_dict_metric(self):
        p = SchedulingProfiler(track_memory=False)
        p.record_metric("scores", {"best": 0.95, "worst": 0.10})
        assert p._metrics["scores"]["best"] == 0.95

    def test_overwrite_metric(self):
        p = SchedulingProfiler(track_memory=False)
        p.record_metric("count", 1)
        p.record_metric("count", 2)
        assert p._metrics["count"] == 2


# ==================== Report Tests ====================


class TestGetReport:
    """Test get_report output structure."""

    def test_report_has_required_keys(self):
        p = SchedulingProfiler(track_memory=False)
        report = p.get_report()
        assert "total_time" in report
        assert "phases" in report
        assert "metrics" in report
        assert "memory" in report
        assert "timestamp" in report

    def test_report_total_time_positive(self):
        p = SchedulingProfiler(track_memory=False)
        time.sleep(0.01)
        report = p.get_report()
        assert report["total_time"] > 0

    def test_report_phases_included(self):
        p = SchedulingProfiler(track_memory=False)
        with p.phase("solving"):
            time.sleep(0.01)
        report = p.get_report()
        assert "solving" in report["phases"]
        assert report["phases"]["solving"]["duration"] > 0
        assert "start" in report["phases"]["solving"]

    def test_report_metrics_included(self):
        p = SchedulingProfiler(track_memory=False)
        p.record_metric("test_val", 42)
        report = p.get_report()
        assert report["metrics"]["test_val"] == 42

    def test_report_memory_none_when_disabled(self):
        p = SchedulingProfiler(track_memory=False)
        report = p.get_report()
        assert report["memory"] is None

    def test_report_timestamp_is_iso(self):
        p = SchedulingProfiler(track_memory=False)
        report = p.get_report()
        # Should be parseable as ISO timestamp
        assert "T" in report["timestamp"]

    def test_report_phase_start_relative_to_profiler(self):
        p = SchedulingProfiler(track_memory=False)
        time.sleep(0.02)
        with p.phase("delayed"):
            pass
        report = p.get_report()
        assert report["phases"]["delayed"]["start"] >= 0.01


# ==================== Reset Tests ====================


class TestReset:
    """Test profiler reset."""

    def test_reset_clears_phases(self):
        p = SchedulingProfiler(track_memory=False)
        with p.phase("old"):
            pass
        p.reset()
        assert p._phases == {}

    def test_reset_clears_stack(self):
        p = SchedulingProfiler(track_memory=False)
        p.start_phase("active")
        p.reset()
        assert p._phase_stack == []

    def test_reset_clears_metrics(self):
        p = SchedulingProfiler(track_memory=False)
        p.record_metric("old_metric", 999)
        p.reset()
        assert p._metrics == {}

    def test_reset_resets_start_time(self):
        p = SchedulingProfiler(track_memory=False)
        old_start = p._start_time
        time.sleep(0.01)
        p.reset()
        assert p._start_time > old_start


# ==================== Print Report Tests ====================


class TestPrintReport:
    """Test print_report output (smoke test)."""

    def test_print_report_runs_without_error(self, capsys):
        p = SchedulingProfiler(track_memory=False)
        with p.phase("test_phase"):
            time.sleep(0.01)
        p.record_metric("test_metric", 42)
        p.print_report()
        captured = capsys.readouterr()
        assert "SCHEDULING PERFORMANCE REPORT" in captured.out
        assert "test_phase" in captured.out
        assert "test_metric" in captured.out

    def test_print_report_empty_profiler(self, capsys):
        p = SchedulingProfiler(track_memory=False)
        p.print_report()
        captured = capsys.readouterr()
        assert "Total Time:" in captured.out


# ==================== Memory Tracking Tests ====================


class TestMemoryTracking:
    """Test _get_memory_usage when psutil not available."""

    def test_no_psutil_returns_zero(self):
        p = SchedulingProfiler(track_memory=False)
        p._psutil = None
        assert p._get_memory_usage() == 0.0
