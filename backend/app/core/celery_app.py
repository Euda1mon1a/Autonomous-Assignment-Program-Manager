"""
Celery Application Configuration.

Sets up Celery for background task processing including:
- Periodic health checks
- Automated fallback precomputation
- Contingency analysis
- Alert notifications
- Schedule metrics computation and snapshots

Configuration:
- Broker: Redis (default: redis://localhost:6379/0)
- Backend: Redis (for result storage)
- Task serialization: JSON
"""

import os

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

# Redis URL from environment or build from settings with password
# Priority: Use environment variable if set (for Docker), otherwise use settings with password
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    # Fallback to settings with password support for local development
    REDIS_URL = settings.redis_url_with_password

# Create Celery app
celery_app = Celery(
    "residency_scheduler",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.resilience.tasks",
        "app.notifications.tasks",
        "app.tasks.schedule_metrics_tasks",
        "app.exports.jobs",
        "app.security.rotation_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task settings
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit at 9 minutes
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    # Beat schedule for periodic tasks
    beat_schedule={
        # Health check every 15 minutes
        "resilience-health-check": {
            "task": "app.resilience.tasks.periodic_health_check",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "resilience"},
        },
        # Contingency analysis daily at 2 AM
        "resilience-contingency-analysis": {
            "task": "app.resilience.tasks.run_contingency_analysis",
            "schedule": crontab(hour=2, minute=0),
            "options": {"queue": "resilience"},
        },
        # Fallback precomputation weekly on Sunday at 3 AM
        "resilience-precompute-fallbacks": {
            "task": "app.resilience.tasks.precompute_fallback_schedules",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),
            "options": {"queue": "resilience"},
        },
        # Utilization forecast daily at 6 AM
        "resilience-utilization-forecast": {
            "task": "app.resilience.tasks.generate_utilization_forecast",
            "schedule": crontab(hour=6, minute=0),
            "options": {"queue": "resilience"},
        },
        # Schedule Metrics - Hourly snapshots during business hours
        "schedule-metrics-hourly-snapshot": {
            "task": "app.tasks.schedule_metrics_tasks.snapshot_metrics",
            "schedule": crontab(hour="8-18", minute=0, day_of_week="1-5"),
            "kwargs": {"period_days": 90},
            "options": {"queue": "metrics"},
        },
        # Schedule Metrics - Daily cleanup at 3 AM
        "schedule-metrics-daily-cleanup": {
            "task": "app.tasks.schedule_metrics_tasks.cleanup_old_snapshots",
            "schedule": crontab(hour=3, minute=30),
            "kwargs": {"retention_days": 365},
            "options": {"queue": "metrics"},
        },
        # Schedule Metrics - Weekly fairness report on Monday at 7 AM
        "schedule-metrics-weekly-fairness-report": {
            "task": "app.tasks.schedule_metrics_tasks.generate_fairness_trend_report",
            "schedule": crontab(hour=7, minute=0, day_of_week=1),
            "kwargs": {"weeks_back": 12},
            "options": {"queue": "metrics"},
        },
        # Schedule Metrics - Daily full computation at 5 AM
        "schedule-metrics-daily-computation": {
            "task": "app.tasks.schedule_metrics_tasks.compute_schedule_metrics",
            "schedule": crontab(hour=5, minute=0),
            "options": {"queue": "metrics"},
        },
        # Export Jobs - Run scheduled exports every 5 minutes
        "export-run-scheduled": {
            "task": "app.exports.jobs.run_scheduled_exports",
            "schedule": crontab(minute="*/5"),
            "options": {"queue": "exports"},
        },
        # Export Jobs - Daily cleanup at 4 AM
        "export-cleanup-old-executions": {
            "task": "app.exports.jobs.cleanup_old_executions",
            "schedule": crontab(hour=4, minute=0),
            "kwargs": {"retention_days": 90},
            "options": {"queue": "exports"},
        },
        # Export Jobs - Health check every hour
        "export-health-check": {
            "task": "app.exports.jobs.export_health_check",
            "schedule": crontab(minute=0),
            "options": {"queue": "exports"},
        },
        # Secret Rotation - Check scheduled rotations daily at 1 AM
        "security-check-scheduled-rotations": {
            "task": "app.security.rotation_tasks.check_scheduled_rotations",
            "schedule": crontab(hour=1, minute=0),
            "options": {"queue": "security"},
        },
        # Secret Rotation - Complete grace periods every hour
        "security-complete-grace-periods": {
            "task": "app.security.rotation_tasks.complete_grace_periods",
            "schedule": crontab(minute=30),
            "options": {"queue": "security"},
        },
        # Secret Rotation - Health monitoring daily at 8 AM
        "security-monitor-rotation-health": {
            "task": "app.security.rotation_tasks.monitor_rotation_health",
            "schedule": crontab(hour=8, minute=0),
            "options": {"queue": "security"},
        },
        # Secret Rotation - Cleanup old history monthly on the 1st at 2 AM
        "security-cleanup-rotation-history": {
            "task": "app.security.rotation_tasks.cleanup_old_rotation_history",
            "schedule": crontab(hour=2, minute=0, day_of_month=1),
            "kwargs": {"retention_days": 730},
            "options": {"queue": "security"},
        },
    },
    # Task routes
    task_routes={
        "app.resilience.tasks.*": {"queue": "resilience"},
        "app.notifications.tasks.*": {"queue": "notifications"},
        "app.tasks.schedule_metrics_tasks.*": {"queue": "metrics"},
        "app.exports.jobs.*": {"queue": "exports"},
        "app.security.rotation_tasks.*": {"queue": "security"},
    },
    # Task queues
    task_queues={
        "default": {},
        "resilience": {},
        "notifications": {},
        "metrics": {},
        "exports": {},
        "security": {},
    },
)


def get_celery_app() -> Celery:
    """Get the Celery application instance."""
    return celery_app
