"""
Celery Application Configuration.

Sets up Celery for background task processing including:
- Periodic health checks
- Automated fallback precomputation
- Contingency analysis
- Alert notifications

Configuration:
- Broker: Redis (default: redis://localhost:6379/0)
- Backend: Redis (for result storage)
- Task serialization: JSON
"""

from celery import Celery
from celery.schedules import crontab
import os

from app.core.config import get_settings

settings = get_settings()

# Redis URL from environment or default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "residency_scheduler",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.resilience.tasks",
        "app.notifications.tasks",
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
    },

    # Task routes
    task_routes={
        "app.resilience.tasks.*": {"queue": "resilience"},
        "app.notifications.tasks.*": {"queue": "notifications"},
    },

    # Task queues
    task_queues={
        "default": {},
        "resilience": {},
        "notifications": {},
    },
)


def get_celery_app() -> Celery:
    """Get the Celery application instance."""
    return celery_app
