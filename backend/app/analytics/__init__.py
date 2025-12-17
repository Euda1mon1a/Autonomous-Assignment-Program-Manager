"""Analytics module for schedule analysis and reporting."""
from sqlalchemy.orm import Session

from app.analytics.engine import AnalyticsEngine
from app.analytics.metrics import (
    calculate_acgme_compliance_rate,
    calculate_consecutive_duty_stats,
    calculate_coverage_rate,
    calculate_fairness_index,
    calculate_preference_satisfaction,
)
from app.analytics.reports import ReportGenerator


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
    "ReportGenerator",
    # Factory functions
    "get_analytics_engine",
    "get_report_generator",
    # Metric functions
    "calculate_fairness_index",
    "calculate_coverage_rate",
    "calculate_acgme_compliance_rate",
    "calculate_preference_satisfaction",
    "calculate_consecutive_duty_stats",
]
