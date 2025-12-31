"""Dashboard package for real-time analytics data."""

from app.analytics.dashboard.dashboard_data import DashboardData
from app.analytics.dashboard.widget_data import WidgetData
from app.analytics.dashboard.kpi_calculator import KPICalculator
from app.analytics.dashboard.realtime_stats import RealtimeStats
from app.analytics.dashboard.comparison_data import ComparisonData

__all__ = [
    "DashboardData",
    "WidgetData",
    "KPICalculator",
    "RealtimeStats",
    "ComparisonData",
]
