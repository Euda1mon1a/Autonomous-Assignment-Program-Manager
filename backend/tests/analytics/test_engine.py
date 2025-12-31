"""Tests for analytics engine."""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, Mock

from app.analytics.engine.analytics_engine import AnalyticsEngine
from app.analytics.engine.metric_calculator import MetricCalculator
from app.analytics.engine.aggregator import DataAggregator
from app.analytics.engine.time_series import TimeSeriesAnalyzer
from app.analytics.engine.trend_detector import TrendDetector
from app.analytics.engine.anomaly_finder import AnomalyFinder
from app.analytics.engine.forecast_engine import ForecastEngine
from app.analytics.engine.comparison import PeriodComparison


@pytest.mark.asyncio
class TestAnalyticsEngine:
    """Test analytics engine."""

    async def test_calculate_all_metrics(self, async_db_session):
        """Test calculating all metrics."""
        engine = AnalyticsEngine(async_db_session)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        # Mock the metric calculator methods
        engine.metric_calculator.calculate_schedule_metrics = AsyncMock(return_value={
            "coverage_rate": 95.0,
            "total_assignments": 100,
        })
        engine.metric_calculator.calculate_compliance_metrics = AsyncMock(return_value={
            "compliance_score": 98.0,
        })
        engine.metric_calculator.calculate_resilience_metrics = AsyncMock(return_value={
            "avg_utilization": 0.75,
        })
        engine.time_series.get_time_series = AsyncMock(return_value={})
        engine.trend_detector.detect_trends = Mock(return_value={})
        engine.anomaly_finder.find_anomalies = Mock(return_value=[])
        engine.forecast_engine.forecast = Mock(return_value={})

        metrics = await engine.calculate_all_metrics(start_date, end_date)

        assert "schedule_metrics" in metrics
        assert "compliance_metrics" in metrics
        assert "resilience_metrics" in metrics
        assert metrics["period"]["start_date"] == start_date.isoformat()

    async def test_get_dashboard_summary(self, async_db_session):
        """Test dashboard summary generation."""
        engine = AnalyticsEngine(async_db_session)

        # Mock calculate_all_metrics
        engine.calculate_all_metrics = AsyncMock(return_value={
            "schedule_metrics": {"coverage_rate": 95.0, "avg_workload_hours": 60.0},
            "compliance_metrics": {"compliance_score": 98.0, "total_violations": 2},
            "resilience_metrics": {"avg_utilization": 0.75, "high_utilization_count": 3},
            "trends": {},
            "anomalies": [],
            "forecasts": {},
            "period": {"start_date": "2024-01-01", "end_date": "2024-01-31", "days": 31},
        })

        summary = await engine.get_dashboard_summary(30)

        assert "kpis" in summary
        assert "trends" in summary
        assert "alerts" in summary
        assert summary["kpis"]["coverage_rate"] == 95.0


@pytest.mark.asyncio
class TestMetricCalculator:
    """Test metric calculator."""

    async def test_calculate_schedule_metrics(self, async_db_session):
        """Test schedule metrics calculation."""
        calculator = MetricCalculator(async_db_session)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        # Would need fixtures for actual data
        # For now, test that method runs
        metrics = await calculator.calculate_schedule_metrics(start_date, end_date)

        assert isinstance(metrics, dict)
        assert "coverage_rate" in metrics
        assert "total_assignments" in metrics


class TestTrendDetector:
    """Test trend detector."""

    def test_detect_trends_empty_data(self):
        """Test trend detection with empty data."""
        detector = TrendDetector()

        trends = detector.detect_trends({})

        assert isinstance(trends, dict)
        assert len(trends) == 0

    def test_detect_trends_insufficient_data(self):
        """Test with insufficient observations."""
        import pandas as pd

        detector = TrendDetector()
        series = pd.Series([1, 2])

        trends = detector.detect_trends({"metric1": series}, min_observations=4)

        assert trends["metric1"]["direction"] == "insufficient_data"


class TestAnomalyFinder:
    """Test anomaly finder."""

    def test_find_anomalies_empty_data(self):
        """Test anomaly detection with empty data."""
        finder = AnomalyFinder()

        anomalies = finder.find_anomalies({})

        assert isinstance(anomalies, list)
        assert len(anomalies) == 0

    def test_prioritize_anomalies(self):
        """Test anomaly prioritization."""
        finder = AnomalyFinder()

        anomalies = [
            {"severity": "low", "type": "statistical", "z_score": 1.5},
            {"severity": "critical", "type": "acgme_violation", "z_score": 4.0},
            {"severity": "medium", "type": "sudden_change", "z_score": 2.5},
        ]

        prioritized = finder.prioritize_anomalies(anomalies, max_results=2)

        assert len(prioritized) == 2
        assert prioritized[0]["severity"] == "critical"


class TestForecastEngine:
    """Test forecast engine."""

    def test_forecast_empty_data(self):
        """Test forecasting with empty data."""
        engine = ForecastEngine()

        forecasts = engine.forecast({}, periods=4)

        assert isinstance(forecasts, dict)
        assert len(forecasts) == 0

    def test_forecast_with_data(self):
        """Test forecasting with valid data."""
        import pandas as pd
        import numpy as np

        engine = ForecastEngine()

        # Create sample time series
        series = pd.Series(np.random.randn(10).cumsum())

        forecasts = engine.forecast({"metric1": series}, periods=4)

        assert "metric1" in forecasts
        assert "predicted_values" in forecasts["metric1"]
        assert len(forecasts["metric1"]["predicted_values"]) == 4


@pytest.mark.asyncio
class TestPeriodComparison:
    """Test period comparison."""

    async def test_compare_periods(self, async_db_session):
        """Test period comparison."""
        comparator = PeriodComparison(async_db_session)

        # Mock metric calculator
        comparator.metric_calculator.calculate_schedule_metrics = AsyncMock(
            return_value={"coverage_rate": 95.0}
        )
        comparator.metric_calculator.calculate_compliance_metrics = AsyncMock(
            return_value={"compliance_score": 98.0}
        )
        comparator.metric_calculator.calculate_resilience_metrics = AsyncMock(
            return_value={"avg_utilization": 0.75}
        )

        period1_start = date(2024, 1, 1)
        period1_end = date(2024, 1, 31)
        period2_start = date(2024, 2, 1)
        period2_end = date(2024, 2, 29)

        comparison = await comparator.compare(
            period1_start, period1_end,
            period2_start, period2_end,
        )

        assert "period1" in comparison
        assert "period2" in comparison
        assert "comparison" in comparison
        assert "summary" in comparison
