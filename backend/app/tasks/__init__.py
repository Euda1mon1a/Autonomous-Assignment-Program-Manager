"""
Tasks Module - Celery Background Tasks.

This module provides Celery background tasks for automated operations
including schedule metrics, RAG embeddings, and other async workflows.
Tasks are designed to run periodically via Celery Beat for automated
monitoring and reporting.

Main Task Categories:
--------------------

Schedule Metrics Tasks:
- compute_schedule_metrics: Compute comprehensive schedule metrics
- compute_version_diff: Compare two schedule versions
- snapshot_metrics: Take periodic metrics snapshots
- cleanup_old_snapshots: Remove old snapshot data
- generate_fairness_trend_report: Generate fairness trend analysis

RAG Embedding Tasks:
- initialize_embeddings: Embed all knowledge base documents
- refresh_single_document: Update embeddings for one document
- check_rag_health: Verify RAG system status
- periodic_refresh: Scheduled weekly refresh
- clear_all_embeddings: Reset all RAG embeddings

Periodic Schedule:
-----------------
Schedules are defined in periodic_tasks.py and should be registered
in the main celery_app.py configuration.

Default schedule:
- Hourly snapshots during business hours (8 AM - 6 PM, Mon-Fri)
- Daily cleanup at 3 AM
- Weekly fairness report on Monday at 7 AM
- Daily full metrics computation at 6 AM
- Weekly RAG refresh on Monday at 2 AM

Usage:
------
Tasks can be called directly or queued via Celery:

    # Direct call (synchronous)
    result = compute_schedule_metrics(
        start_date="2025-01-01",
        end_date="2025-03-31"
    )

    # Async call via Celery (recommended)
    from app.tasks import compute_schedule_metrics, initialize_embeddings

    task = compute_schedule_metrics.delay(
        start_date="2025-01-01",
        end_date="2025-03-31"
    )
    result = task.get(timeout=600)

    # RAG embeddings initialization
    rag_task = initialize_embeddings.delay()
    rag_result = rag_task.get(timeout=300)

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
            "app.tasks.schedule_metrics_tasks",
            "app.tasks.rag_tasks",  # Add for RAG embeddings
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
from app.tasks.rag_tasks import (
    check_rag_health,
    clear_all_embeddings,
    initialize_embeddings,
    periodic_refresh,
    refresh_single_document,
)

__all__ = [
    # Schedule Metrics Tasks
    "compute_schedule_metrics",
    "compute_version_diff",
    "snapshot_metrics",
    "cleanup_old_snapshots",
    "generate_fairness_trend_report",
    # RAG Tasks
    "initialize_embeddings",
    "refresh_single_document",
    "check_rag_health",
    "periodic_refresh",
    "clear_all_embeddings",
    # Configuration
    "get_schedule_metrics_beat_schedule",
    "get_beat_schedule_for_environment",
    "configure_celery_for_schedule_metrics",
    "SCHEDULE_METRICS_BEAT_SCHEDULE",
    "SCHEDULE_METRICS_TASK_ROUTES",
    "SCHEDULE_METRICS_TASK_QUEUES",
    "SCHEDULE_METRICS_TASK_CONFIG",
]
