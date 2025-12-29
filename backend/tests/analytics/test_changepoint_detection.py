"""Tests for change point detection in signal processing module.

Tests the CUSUM and PELT algorithms for detecting regime shifts,
policy changes, and structural breaks in schedule patterns.
"""

from datetime import date, timedelta

import numpy as np
import pytest

from app.analytics.signal_processing import (
    WorkloadSignalProcessor,
    WorkloadTimeSeries,
    detect_schedule_changepoints,
)


class TestCUSUMDetection:
    """Tests for CUSUM change point detection."""

    def test_detects_upward_mean_shift(self):
        """CUSUM should detect upward mean shifts."""
        # Create series with clear mean shift at index 50
        series = np.concatenate([
            np.random.normal(8.0, 0.5, 50),  # Low mean
            np.random.normal(12.0, 0.5, 50),  # High mean
        ])

        processor = WorkloadSignalProcessor()
        change_points = processor.detect_change_points_cusum(series, threshold=4.0)

        # Should detect at least one change point near index 50
        assert len(change_points) >= 1
        detected_indices = [cp["index"] for cp in change_points]
        assert any(45 <= idx <= 55 for idx in detected_indices)

        # Should be upward shift
        assert any("upward" in cp["change_type"] for cp in change_points)

    def test_detects_downward_mean_shift(self):
        """CUSUM should detect downward mean shifts."""
        series = np.concatenate([
            np.random.normal(12.0, 0.5, 50),  # High mean
            np.random.normal(8.0, 0.5, 50),   # Low mean
        ])

        processor = WorkloadSignalProcessor()
        change_points = processor.detect_change_points_cusum(series, threshold=4.0)

        assert len(change_points) >= 1
        assert any("downward" in cp["change_type"] for cp in change_points)

    def test_no_change_points_in_stable_series(self):
        """CUSUM should find no change points in stable data."""
        series = np.random.normal(10.0, 0.5, 100)  # Stable series

        processor = WorkloadSignalProcessor()
        change_points = processor.detect_change_points_cusum(series, threshold=5.0)

        # Stable series should have few or no change points
        assert len(change_points) <= 1

    def test_handles_short_series(self):
        """CUSUM should handle short series gracefully."""
        series = np.array([1.0, 2.0, 3.0])  # Too short

        processor = WorkloadSignalProcessor()
        change_points = processor.detect_change_points_cusum(series)

        assert change_points == []


class TestPELTDetection:
    """Tests for PELT change point detection."""

    def test_detects_multiple_segments(self):
        """PELT should detect multiple change points."""
        # Create series with 3 distinct segments
        series = np.concatenate([
            np.random.normal(5.0, 0.3, 30),   # Segment 1
            np.random.normal(10.0, 0.3, 30),  # Segment 2
            np.random.normal(7.0, 0.3, 30),   # Segment 3
        ])

        processor = WorkloadSignalProcessor()
        change_points = processor.detect_change_points_pelt(
            series, penalty=0.5, min_segment_length=5
        )

        # Should detect at least 1-2 change points
        assert len(change_points) >= 1

    def test_respects_minimum_segment_length(self):
        """PELT should respect minimum segment length."""
        series = np.random.normal(10.0, 1.0, 50)

        processor = WorkloadSignalProcessor()
        change_points = processor.detect_change_points_pelt(
            series, min_segment_length=10
        )

        # All change points should be at least 10 apart
        if len(change_points) >= 2:
            indices = sorted(cp["index"] for cp in change_points)
            for i in range(1, len(indices)):
                assert indices[i] - indices[i-1] >= 10

    def test_handles_short_series(self):
        """PELT should handle short series gracefully."""
        series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])  # Too short for min_segment=5

        processor = WorkloadSignalProcessor()
        change_points = processor.detect_change_points_pelt(
            series, min_segment_length=5
        )

        assert change_points == []


class TestScheduleChangepoints:
    """Tests for comprehensive change point analysis."""

    def test_analyze_schedule_changepoints_runs_both_methods(self):
        """Should run both CUSUM and PELT by default."""
        values = list(np.random.normal(10.0, 1.0, 60))
        dates = [date(2025, 1, 1) + timedelta(days=i) for i in range(60)]

        ts = WorkloadTimeSeries(
            values=np.array(values),
            dates=dates,
        )

        processor = WorkloadSignalProcessor()
        results = processor.analyze_schedule_changepoints(ts)

        assert "cusum" in results
        assert "pelt" in results
        assert results["cusum"]["method"] == "cusum"
        assert results["pelt"]["method"] == "pelt"

    def test_fills_timestamps(self):
        """Should fill timestamps for detected change points."""
        # Create series with clear change point
        values = [8.0] * 30 + [12.0] * 30
        dates = [date(2025, 1, 1) + timedelta(days=i) for i in range(60)]

        ts = WorkloadTimeSeries(
            values=np.array(values, dtype=np.float64),
            dates=dates,
        )

        processor = WorkloadSignalProcessor()
        results = processor.analyze_schedule_changepoints(ts)

        # Check that timestamps are filled
        for method, method_result in results.items():
            for cp in method_result.get("change_points", []):
                if cp["index"] < len(dates):
                    assert cp["timestamp"] != ""
                    assert "2025" in cp["timestamp"]


class TestConvenienceFunction:
    """Tests for detect_schedule_changepoints convenience function."""

    def test_convenience_function_works(self):
        """Convenience function should return valid results."""
        daily_hours = [8.0] * 20 + [12.0] * 20
        dates = [date(2025, 1, 1) + timedelta(days=i) for i in range(40)]

        results = detect_schedule_changepoints(daily_hours, dates)

        assert "cusum" in results
        assert "pelt" in results
        assert all("num_changepoints" in r for r in results.values())

    def test_custom_methods(self):
        """Should respect custom method selection."""
        daily_hours = [8.0] * 20 + [12.0] * 20
        dates = [date(2025, 1, 1) + timedelta(days=i) for i in range(40)]

        results = detect_schedule_changepoints(daily_hours, dates, methods=["cusum"])

        assert "cusum" in results
        assert "pelt" not in results


class TestIntegrationWithAnalysisPipeline:
    """Tests for integration with main analysis pipeline."""

    def test_changepoint_in_analyze_workload_patterns(self):
        """Change point detection should integrate with main pipeline."""
        values = [8.0] * 30 + [12.0] * 30
        dates = [date(2025, 1, 1) + timedelta(days=i) for i in range(60)]

        ts = WorkloadTimeSeries(
            values=np.array(values, dtype=np.float64),
            dates=dates,
        )

        processor = WorkloadSignalProcessor()
        result = processor.analyze_workload_patterns(ts, analysis_types=["changepoint"])

        assert "changepoint_analysis" in result
        assert result["changepoint_analysis"] is not None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_constant_series(self):
        """Should handle constant series without errors."""
        series = np.ones(50) * 10.0

        processor = WorkloadSignalProcessor()
        cusum_cps = processor.detect_change_points_cusum(series)
        pelt_cps = processor.detect_change_points_pelt(series)

        # Constant series should have no change points
        assert len(cusum_cps) == 0
        assert len(pelt_cps) == 0

    def test_single_value(self):
        """Should handle single value gracefully."""
        series = np.array([10.0])

        processor = WorkloadSignalProcessor()
        cusum_cps = processor.detect_change_points_cusum(series)
        pelt_cps = processor.detect_change_points_pelt(series)

        assert cusum_cps == []
        assert pelt_cps == []

    def test_high_variance_series(self):
        """Should handle high variance series."""
        series = np.random.normal(10.0, 5.0, 100)  # High variance

        processor = WorkloadSignalProcessor()
        # Should not crash
        cusum_cps = processor.detect_change_points_cusum(series, threshold=5.0)
        pelt_cps = processor.detect_change_points_pelt(series)

        assert isinstance(cusum_cps, list)
        assert isinstance(pelt_cps, list)
