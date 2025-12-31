"""Tests for dashboard components."""

import pytest
from datetime import date
from unittest.mock import AsyncMock

from app.analytics.dashboard.dashboard_data import DashboardData
from app.analytics.dashboard.widget_data import WidgetData
from app.analytics.dashboard.kpi_calculator import KPICalculator
from app.analytics.dashboard.realtime_stats import RealtimeStats
from app.analytics.dashboard.comparison_data import ComparisonData


@pytest.mark.asyncio
class TestDashboardData:
    """Test dashboard data provider."""

    async def test_get_dashboard_data(self, async_db_session):
        """Test dashboard data retrieval."""
        dashboard = DashboardData(async_db_session)

        # Mock dependencies
        dashboard.analytics_engine.get_dashboard_summary = AsyncMock(
            return_value={
                "kpis": {},
                "trends": {},
            }
        )
        dashboard.kpi_calculator.calculate_kpis = AsyncMock(return_value={})
        dashboard.realtime_stats.get_stats = AsyncMock(return_value={})

        data = await dashboard.get_dashboard_data(30)

        assert isinstance(data, dict)
        assert "summary" in data
        assert "kpis" in data
        assert "realtime" in data


@pytest.mark.asyncio
class TestWidgetData:
    """Test widget data provider."""

    async def test_get_coverage_widget(self, async_db_session):
        """Test coverage widget data."""
        widget = WidgetData(async_db_session)

        data = await widget.get_coverage_widget()

        assert isinstance(data, dict)
        assert "title" in data
        assert "value" in data

    async def test_get_violations_widget(self, async_db_session):
        """Test violations widget data."""
        widget = WidgetData(async_db_session)

        data = await widget.get_violations_widget()

        assert isinstance(data, dict)
        assert "title" in data
        assert "value" in data


@pytest.mark.asyncio
class TestKPICalculator:
    """Test KPI calculator."""

    async def test_calculate_kpis(self, async_db_session):
        """Test KPI calculation."""
        calculator = KPICalculator(async_db_session)

        kpis = await calculator.calculate_kpis(30)

        assert isinstance(kpis, dict)
        assert "coverage" in kpis
        assert "workload" in kpis
        assert "utilization" in kpis


@pytest.mark.asyncio
class TestRealtimeStats:
    """Test realtime stats provider."""

    async def test_get_stats(self, async_db_session):
        """Test realtime stats retrieval."""
        stats = RealtimeStats(async_db_session)

        data = await stats.get_stats()

        assert isinstance(data, dict)
        assert "today" in data
        assert "active" in data
        assert "timestamp" in data


@pytest.mark.asyncio
class TestComparisonData:
    """Test comparison data provider."""

    async def test_get_week_over_week(self, async_db_session):
        """Test week-over-week comparison."""
        comparison = ComparisonData(async_db_session)

        # Mock comparator
        comparison.comparator.compare = AsyncMock(
            return_value={
                "period1": {},
                "period2": {},
                "comparison": {},
            }
        )

        data = await comparison.get_week_over_week()

        assert isinstance(data, dict)
        assert data["type"] == "week_over_week"
        assert "comparison" in data
