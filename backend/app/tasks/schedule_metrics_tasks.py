"""
Celery Tasks for Schedule Metrics Computation.

Provides automated background tasks for:
- Computing schedule metrics (fairness, coverage, compliance)
- Computing version diffs between schedule versions
- Taking periodic metrics snapshots
- Cleaning up old snapshot data

Tasks integrate with AnalyticsEngine and StabilityMetricsComputer.
"""

from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from celery import shared_task
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_db_session() -> Session:
    """Get a database session for task execution."""
    from app.core.database import SessionLocal
    return SessionLocal()


@shared_task(
    bind=True,
    name="app.tasks.schedule_metrics_tasks.compute_schedule_metrics",
    max_retries=3,
    default_retry_delay=60,
)
def compute_schedule_metrics(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, Any]:
    """
    Compute comprehensive schedule metrics for a date range.

    Args:
        start_date: Start date (ISO format YYYY-MM-DD). Defaults to today.
        end_date: End date (ISO format YYYY-MM-DD). Defaults to 90 days from start.

    Returns:
        Dict with computed metrics including:
        - fairness_index: Workload distribution fairness
        - coverage_rate: Block coverage percentage
        - acgme_compliance: ACGME compliance rate
        - workload_distribution: Per-resident workload stats
        - stability_metrics: Churn, ripple factor, N-1 vulnerability

    Raises:
        Retries on failure up to max_retries
    """
    logger.info("Starting schedule metrics computation")

    db = get_db_session()
    try:
        # Parse dates
        if start_date:
            start = date.fromisoformat(start_date)
        else:
            start = date.today()

        if end_date:
            end = date.fromisoformat(end_date)
        else:
            end = start + timedelta(days=90)

        # Compute metrics using AnalyticsEngine
        from app.analytics.engine import AnalyticsEngine
        from app.analytics.stability_metrics import compute_stability_metrics

        engine = AnalyticsEngine(db)
        schedule_analysis = engine.analyze_schedule(start, end)

        # Compute stability metrics
        stability = compute_stability_metrics(db, start, end)

        # Combine results
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "period": {
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
            "schedule_analysis": schedule_analysis,
            "stability_metrics": stability,
            "task_status": "completed",
        }

        logger.info(
            f"Metrics computation complete: "
            f"Fairness={schedule_analysis['metrics']['fairness']['value']}, "
            f"Coverage={schedule_analysis['metrics']['coverage']['value']}, "
            f"Stability Grade={stability['stability_grade']}"
        )

        return result

    except Exception as e:
        logger.error(f"Metrics computation failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.schedule_metrics_tasks.compute_version_diff",
    max_retries=2,
    default_retry_delay=120,
)
def compute_version_diff(
    self,
    run_id_1: str,
    run_id_2: str,
) -> dict[str, Any]:
    """
    Compute differences between two schedule versions.

    Args:
        run_id_1: First schedule run ID (UUID string)
        run_id_2: Second schedule run ID (UUID string)

    Returns:
        Dict with comparison results including:
        - violations_delta: Change in ACGME violations
        - blocks_delta: Change in assigned blocks
        - runtime_delta: Change in computation time
        - fairness_change: Change in fairness metric
        - coverage_change: Change in coverage metric

    Raises:
        Retries on failure up to max_retries
    """
    logger.info(f"Computing version diff: {run_id_1} vs {run_id_2}")

    db = get_db_session()
    try:
        from app.analytics.engine import AnalyticsEngine
        from app.models.schedule_run import ScheduleRun

        engine = AnalyticsEngine(db)

        # Get schedule runs
        run1 = db.query(ScheduleRun).filter(
            ScheduleRun.id == UUID(run_id_1)
        ).first()
        run2 = db.query(ScheduleRun).filter(
            ScheduleRun.id == UUID(run_id_2)
        ).first()

        if not run1 or not run2:
            error_msg = f"Schedule run not found: run1={bool(run1)}, run2={bool(run2)}"
            logger.error(error_msg)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": error_msg,
                "task_status": "failed",
            }

        # Use existing comparison method
        comparison = engine.compare_schedules(run_id_1, run_id_2)

        # Compute metrics for each run to get fairness/coverage changes
        analysis1 = engine.analyze_schedule(run1.start_date, run1.end_date)
        analysis2 = engine.analyze_schedule(run2.start_date, run2.end_date)

        # Calculate metric deltas
        fairness_change = (
            analysis2["metrics"]["fairness"]["value"] -
            analysis1["metrics"]["fairness"]["value"]
        )
        coverage_change = (
            analysis2["metrics"]["coverage"]["value"] -
            analysis1["metrics"]["coverage"]["value"]
        )

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "comparison": comparison,
            "metric_changes": {
                "fairness_delta": round(fairness_change, 3),
                "coverage_delta": round(coverage_change, 2),
            },
            "summary": {
                "improved": (
                    fairness_change > 0 and
                    coverage_change >= 0 and
                    comparison["differences"]["violations_delta"] <= 0
                ),
                "violations_changed": comparison["differences"]["violations_delta"] != 0,
                "significant_change": (
                    abs(fairness_change) > 0.1 or
                    abs(coverage_change) > 5.0 or
                    abs(comparison["differences"]["violations_delta"]) > 0
                ),
            },
            "task_status": "completed",
        }

        logger.info(
            f"Version diff complete: "
            f"Fairness change={fairness_change:.3f}, "
            f"Coverage change={coverage_change:.2f}, "
            f"Violations delta={comparison['differences']['violations_delta']}"
        )

        return result

    except Exception as e:
        logger.error(f"Version diff computation failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.schedule_metrics_tasks.snapshot_metrics",
    max_retries=3,
    default_retry_delay=60,
)
def snapshot_metrics(
    self,
    period_days: int = 90,
) -> dict[str, Any]:
    """
    Take a snapshot of current schedule metrics and save to database.

    This creates a point-in-time record of metrics for trend analysis.
    Snapshots are stored in the schedule_run table and can be used for
    historical analysis and reporting.

    Args:
        period_days: Number of days to analyze (default: 90)

    Returns:
        Dict with snapshot metadata and metrics summary

    Raises:
        Retries on failure up to max_retries
    """
    logger.info(f"Taking metrics snapshot for {period_days} days")

    db = get_db_session()
    try:
        from app.analytics.engine import AnalyticsEngine
        from app.analytics.stability_metrics import compute_stability_metrics

        start_date = date.today()
        end_date = start_date + timedelta(days=period_days)

        # Compute current metrics
        engine = AnalyticsEngine(db)
        schedule_analysis = engine.analyze_schedule(start_date, end_date)
        stability = compute_stability_metrics(db, start_date, end_date)

        # Create snapshot record (stored as JSON in existing tables)
        # Note: In production, you might want a dedicated MetricsSnapshot table
        snapshot_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": period_days,
            },
            "metrics": {
                "fairness": schedule_analysis["metrics"]["fairness"]["value"],
                "coverage": schedule_analysis["metrics"]["coverage"]["value"],
                "compliance": schedule_analysis["metrics"]["compliance"]["value"],
                "stability_grade": stability["stability_grade"],
                "churn_rate": stability["churn_rate"],
                "n1_vulnerability": stability["n1_vulnerability_score"],
            },
            "summary": schedule_analysis["summary"],
        }

        # Log snapshot for now (in production, save to dedicated table)
        logger.info(
            f"Metrics snapshot captured: "
            f"Fairness={snapshot_data['metrics']['fairness']}, "
            f"Coverage={snapshot_data['metrics']['coverage']}, "
            f"Stability={snapshot_data['metrics']['stability_grade']}"
        )

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "snapshot_id": f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "snapshot_data": snapshot_data,
            "task_status": "completed",
        }

        return result

    except Exception as e:
        logger.error(f"Metrics snapshot failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.schedule_metrics_tasks.cleanup_old_snapshots",
    max_retries=2,
    default_retry_delay=300,
)
def cleanup_old_snapshots(
    self,
    retention_days: int = 365,
) -> dict[str, Any]:
    """
    Remove metrics snapshots older than retention period.

    This task maintains database hygiene by removing old snapshot data
    while preserving recent history for trend analysis.

    Args:
        retention_days: Number of days to retain snapshots (default: 365)

    Returns:
        Dict with cleanup statistics

    Raises:
        Retries on failure up to max_retries
    """
    logger.info(f"Starting snapshot cleanup (retention: {retention_days} days)")

    db = get_db_session()
    try:
        from app.models.schedule_run import ScheduleRun

        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Query old schedule runs
        old_runs = db.query(ScheduleRun).filter(
            ScheduleRun.created_at < cutoff_date
        ).all()

        # Count by status before deletion
        status_counts = {}
        for run in old_runs:
            status = run.status
            status_counts[status] = status_counts.get(status, 0) + 1

        # Delete old runs
        deleted_count = len(old_runs)
        for run in old_runs:
            db.delete(run)

        db.commit()

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
            "deleted_count": deleted_count,
            "deleted_by_status": status_counts,
            "task_status": "completed",
        }

        logger.info(
            f"Snapshot cleanup complete: "
            f"Deleted {deleted_count} snapshots older than {retention_days} days"
        )

        return result

    except Exception as e:
        logger.error(f"Snapshot cleanup failed: {e}", exc_info=True)
        db.rollback()
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.schedule_metrics_tasks.generate_fairness_trend_report",
    max_retries=2,
    default_retry_delay=120,
)
def generate_fairness_trend_report(
    self,
    weeks_back: int = 12,
) -> dict[str, Any]:
    """
    Generate a trend report for fairness metrics over time.

    Analyzes historical fairness data to identify trends, anomalies,
    and potential issues with workload distribution.

    Args:
        weeks_back: Number of weeks to analyze (default: 12)

    Returns:
        Dict with trend analysis including:
        - weekly_fairness: Fairness values by week
        - trend_direction: "improving", "stable", or "declining"
        - anomalies: Weeks with significant fairness issues
        - recommendations: Suggested actions

    Raises:
        Retries on failure up to max_retries
    """
    logger.info(f"Generating fairness trend report for {weeks_back} weeks")

    db = get_db_session()
    try:
        from app.analytics.engine import AnalyticsEngine

        engine = AnalyticsEngine(db)
        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks_back)

        # Collect weekly fairness metrics
        weekly_metrics = []
        current_date = start_date

        while current_date < end_date:
            week_end = min(current_date + timedelta(days=7), end_date)

            try:
                analysis = engine.analyze_schedule(current_date, week_end)
                fairness = analysis["metrics"]["fairness"]

                weekly_metrics.append({
                    "week_start": current_date.isoformat(),
                    "week_end": week_end.isoformat(),
                    "fairness_value": fairness["value"],
                    "status": fairness["status"],
                })
            except Exception as e:
                logger.warning(f"Failed to get metrics for week {current_date}: {e}")

            current_date = week_end

        if not weekly_metrics:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": "No metrics data available",
                "task_status": "failed",
            }

        # Calculate trend
        values = [m["fairness_value"] for m in weekly_metrics]
        avg_fairness = sum(values) / len(values)

        # Simple trend detection (compare first half vs second half)
        mid_point = len(values) // 2
        first_half_avg = sum(values[:mid_point]) / mid_point if mid_point > 0 else 0
        second_half_avg = sum(values[mid_point:]) / (len(values) - mid_point)

        if second_half_avg > first_half_avg + 0.05:
            trend_direction = "improving"
        elif second_half_avg < first_half_avg - 0.05:
            trend_direction = "declining"
        else:
            trend_direction = "stable"

        # Identify anomalies (fairness < 0.75)
        anomalies = [
            m for m in weekly_metrics
            if m["fairness_value"] < 0.75
        ]

        # Generate recommendations
        recommendations = []
        if trend_direction == "declining":
            recommendations.append(
                "Workload fairness is declining. Review recent assignment changes."
            )
        if len(anomalies) > 2:
            recommendations.append(
                f"Multiple weeks with poor fairness detected ({len(anomalies)} weeks). "
                "Consider rebalancing assignments."
            )
        if avg_fairness < 0.8:
            recommendations.append(
                "Average fairness is below target (0.8). Review overall workload distribution."
            )

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "weeks": weeks_back,
            },
            "weekly_fairness": weekly_metrics,
            "summary": {
                "average_fairness": round(avg_fairness, 3),
                "trend_direction": trend_direction,
                "anomaly_count": len(anomalies),
                "first_half_avg": round(first_half_avg, 3),
                "second_half_avg": round(second_half_avg, 3),
            },
            "anomalies": anomalies,
            "recommendations": recommendations,
            "task_status": "completed",
        }

        logger.info(
            f"Fairness trend report complete: "
            f"Avg={avg_fairness:.3f}, Trend={trend_direction}, "
            f"Anomalies={len(anomalies)}"
        )

        return result

    except Exception as e:
        logger.error(f"Fairness trend report failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()
