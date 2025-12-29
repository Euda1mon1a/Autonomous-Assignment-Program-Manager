"""Analytics module for schedule analysis and reporting."""

from sqlalchemy.orm import Session

from app.analytics.api import (
    APIAnalyticsService,
    get_api_analytics_service,
)
from app.analytics.arima_forecast import (
    ARIMAConfig,
    ARIMAForecaster,
    WorkloadSeries,
    auto_select_arima_order,
    check_stationarity,
    forecast_workload,
)
from app.analytics.engine import AnalyticsEngine
from app.analytics.metrics import (
    calculate_acgme_compliance_rate,
    calculate_consecutive_duty_stats,
    calculate_coverage_rate,
    calculate_fairness_index,
    calculate_preference_satisfaction,
)
from app.analytics.persistent_homology import (
    CoverageVoid,
    CyclicPattern,
    PersistenceDiagram,
    PersistentScheduleAnalyzer,
    TopologicalFeature,
)
from app.analytics.reports import ReportGenerator
from app.analytics.stability_metrics import (
    StabilityMetrics,
    StabilityMetricsComputer,
    compute_stability_metrics,
)
from app.analytics.tda_visualization import (
    BarcodeVisualization,
    create_tda_summary_report,
    visualize_point_cloud,
)


def get_analytics_engine(db: Session) -> AnalyticsEngine:
    """
    Factory function to create an AnalyticsEngine instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        Configured AnalyticsEngine instance
    """
    return AnalyticsEngine(db)


def get_report_generator(db: Session) -> ReportGenerator:
    """
    Factory function to create a ReportGenerator instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        Configured ReportGenerator instance
    """
    return ReportGenerator(db)


__all__ = [
    # Classes
    "AnalyticsEngine",
    "APIAnalyticsService",
    "ARIMAConfig",
    "ARIMAForecaster",
    "BarcodeVisualization",
    "CoverageVoid",
    "CyclicPattern",
    "PersistenceDiagram",
    "PersistentScheduleAnalyzer",
    "ReportGenerator",
    "StabilityMetrics",
    "StabilityMetricsComputer",
    "TopologicalFeature",
    "WorkloadSeries",
    # Factory functions
    "get_analytics_engine",
    "get_api_analytics_service",
    "get_report_generator",
    # Metric functions
    "calculate_acgme_compliance_rate",
    "calculate_consecutive_duty_stats",
    "calculate_coverage_rate",
    "calculate_fairness_index",
    "calculate_preference_satisfaction",
    "compute_stability_metrics",
    # ARIMA forecasting functions
    "auto_select_arima_order",
    "check_stationarity",
    "forecast_workload",
    # TDA functions
    "create_tda_summary_report",
    "visualize_point_cloud",
]
