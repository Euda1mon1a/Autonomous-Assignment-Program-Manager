"""
Schedule Metrics Tasks Module.

This module provides Celery background tasks for computing and tracking
schedule metrics over time. Tasks are designed to run periodically via
Celery Beat for automated monitoring and reporting.

Main Tasks:
-----------
- compute_schedule_metrics: Compute comprehensive schedule metrics
- compute_version_diff: Compare two schedule versions
- snapshot_metrics: Take periodic metrics snapshots
- cleanup_old_snapshots: Remove old snapshot data
- generate_fairness_trend_report: Generate fairness trend analysis

Periodic Schedule:
-----------------
Schedules are defined in periodic_tasks.py and should be registered
in the main celery_app.py configuration.

Default schedule:
- Hourly snapshots during business hours (8 AM - 6 PM, Mon-Fri)
- Daily cleanup at 3 AM
- Weekly fairness report on Monday at 7 AM
- Daily full metrics computation at 6 AM

Usage:
------
Tasks can be called directly or queued via Celery:

    # Direct call (synchronous)
    result = compute_schedule_metrics(
        start_date="2025-01-01",
        end_date="2025-03-31"
    )

    # Async call via Celery (recommended)
    from app.tasks import compute_schedule_metrics
    task = compute_schedule_metrics.delay(
        start_date="2025-01-01",
        end_date="2025-03-31"
    )
    result = task.get(timeout=600)

Configuration:
-------------
To enable these tasks, add to celery_app.py:

    from app.tasks.periodic_tasks import configure_celery_for_schedule_metrics
    configure_celery_for_schedule_metrics(celery_app)

Or manually update the includes:

    celery_app = Celery(
        "residency_scheduler",
        include=[
            "app.resilience.tasks",
            "app.notifications.tasks",
            "app.tasks.schedule_metrics_tasks",  # Add this
        ],
    )
"""

# Import all tasks for easy access
# Import configuration helpers
from app.tasks.periodic_tasks import (
    SCHEDULE_METRICS_BEAT_SCHEDULE,
    SCHEDULE_METRICS_TASK_CONFIG,
    SCHEDULE_METRICS_TASK_QUEUES,
    SCHEDULE_METRICS_TASK_ROUTES,
    configure_celery_for_schedule_metrics,
    get_beat_schedule_for_environment,
    get_schedule_metrics_beat_schedule,
)
from app.tasks.schedule_metrics_tasks import (
    cleanup_old_snapshots,
    compute_schedule_metrics,
    compute_version_diff,
    generate_fairness_trend_report,
    snapshot_metrics,
)

__all__ = [
    # Tasks
    "compute_schedule_metrics",
    "compute_version_diff",
    "snapshot_metrics",
    "cleanup_old_snapshots",
    "generate_fairness_trend_report",
    # Configuration
    "get_schedule_metrics_beat_schedule",
    "get_beat_schedule_for_environment",
    "configure_celery_for_schedule_metrics",
    "SCHEDULE_METRICS_BEAT_SCHEDULE",
    "SCHEDULE_METRICS_TASK_ROUTES",
    "SCHEDULE_METRICS_TASK_QUEUES",
    "SCHEDULE_METRICS_TASK_CONFIG",
]
