"""
Periodic Task Configuration for Schedule Metrics.

Defines Celery Beat schedules for automated metrics computation:
- Hourly metrics snapshots during business hours (8 AM - 6 PM)
- Daily cleanup of old snapshots at 3 AM
- Weekly fairness trend report on Monday at 7 AM

These schedules should be registered in celery_app.py beat_schedule.
"""

from celery.schedules import crontab

***REMOVED*** Celery beat schedule for schedule metrics tasks
SCHEDULE_METRICS_BEAT_SCHEDULE = {
    ***REMOVED*** Hourly metrics snapshot during business hours (8 AM - 6 PM, Mon-Fri)
    "schedule-metrics-hourly-snapshot": {
        "task": "app.tasks.schedule_metrics_tasks.snapshot_metrics",
        "schedule": crontab(
            hour="8-18",  ***REMOVED*** 8 AM to 6 PM
            minute=0,  ***REMOVED*** On the hour
            day_of_week="1-5",  ***REMOVED*** Monday through Friday
        ),
        "kwargs": {
            "period_days": 90,  ***REMOVED*** 90-day snapshot
        },
        "options": {
            "queue": "metrics",
            "expires": 3600,  ***REMOVED*** Task expires after 1 hour
        },
    },
    ***REMOVED*** Daily snapshot cleanup at 3 AM
    "schedule-metrics-daily-cleanup": {
        "task": "app.tasks.schedule_metrics_tasks.cleanup_old_snapshots",
        "schedule": crontab(
            hour=3,
            minute=0,
        ),
        "kwargs": {
            "retention_days": 365,  ***REMOVED*** Keep 1 year of history
        },
        "options": {
            "queue": "metrics",
        },
    },
    ***REMOVED*** Weekly fairness trend report on Monday at 7 AM
    "schedule-metrics-weekly-fairness-report": {
        "task": "app.tasks.schedule_metrics_tasks.generate_fairness_trend_report",
        "schedule": crontab(
            hour=7,
            minute=0,
            day_of_week=1,  ***REMOVED*** Monday
        ),
        "kwargs": {
            "weeks_back": 12,  ***REMOVED*** 12-week trend analysis
        },
        "options": {
            "queue": "metrics",
        },
    },
    ***REMOVED*** Daily full metrics computation at 6 AM
    "schedule-metrics-daily-computation": {
        "task": "app.tasks.schedule_metrics_tasks.compute_schedule_metrics",
        "schedule": crontab(
            hour=6,
            minute=0,
        ),
        "kwargs": {
            ***REMOVED*** Uses default: today + 90 days
        },
        "options": {
            "queue": "metrics",
            "expires": 7200,  ***REMOVED*** Task expires after 2 hours
        },
    },
}


def get_schedule_metrics_beat_schedule() -> dict:
    """
    Get the beat schedule configuration for schedule metrics tasks.

    Returns:
        Dict with beat schedule configuration

    Usage:
        In celery_app.py:

        from app.tasks.periodic_tasks import get_schedule_metrics_beat_schedule

        celery_app.conf.beat_schedule.update(
            get_schedule_metrics_beat_schedule()
        )
    """
    return SCHEDULE_METRICS_BEAT_SCHEDULE


***REMOVED*** Alternative schedules for different deployment scenarios

***REMOVED*** Development schedule (less frequent, for testing)
SCHEDULE_METRICS_BEAT_SCHEDULE_DEV = {
    ***REMOVED*** Every 4 hours during the day
    "schedule-metrics-dev-snapshot": {
        "task": "app.tasks.schedule_metrics_tasks.snapshot_metrics",
        "schedule": crontab(
            hour="8-20/4",  ***REMOVED*** Every 4 hours from 8 AM to 8 PM
            minute=0,
        ),
        "kwargs": {
            "period_days": 30,  ***REMOVED*** Shorter period for dev
        },
        "options": {
            "queue": "metrics",
        },
    },
    ***REMOVED*** Weekly cleanup
    "schedule-metrics-dev-cleanup": {
        "task": "app.tasks.schedule_metrics_tasks.cleanup_old_snapshots",
        "schedule": crontab(
            hour=3,
            minute=0,
            day_of_week=0,  ***REMOVED*** Sunday
        ),
        "kwargs": {
            "retention_days": 90,  ***REMOVED*** Shorter retention for dev
        },
        "options": {
            "queue": "metrics",
        },
    },
}


***REMOVED*** High-frequency schedule (for critical deployments)
SCHEDULE_METRICS_BEAT_SCHEDULE_HIGH_FREQ = {
    ***REMOVED*** Every 30 minutes during business hours
    "schedule-metrics-highfreq-snapshot": {
        "task": "app.tasks.schedule_metrics_tasks.snapshot_metrics",
        "schedule": crontab(
            hour="6-22",  ***REMOVED*** 6 AM to 10 PM
            minute="*/30",  ***REMOVED*** Every 30 minutes
            day_of_week="1-5",  ***REMOVED*** Monday through Friday
        ),
        "kwargs": {
            "period_days": 90,
        },
        "options": {
            "queue": "metrics",
        },
    },
    ***REMOVED*** Hourly on weekends
    "schedule-metrics-highfreq-weekend-snapshot": {
        "task": "app.tasks.schedule_metrics_tasks.snapshot_metrics",
        "schedule": crontab(
            hour="*/2",  ***REMOVED*** Every 2 hours
            minute=0,
            day_of_week="0,6",  ***REMOVED*** Saturday and Sunday
        ),
        "kwargs": {
            "period_days": 90,
        },
        "options": {
            "queue": "metrics",
        },
    },
    ***REMOVED*** Daily cleanup
    "schedule-metrics-highfreq-cleanup": {
        "task": "app.tasks.schedule_metrics_tasks.cleanup_old_snapshots",
        "schedule": crontab(
            hour=3,
            minute=0,
        ),
        "kwargs": {
            "retention_days": 730,  ***REMOVED*** 2 years for high-freq
        },
        "options": {
            "queue": "metrics",
        },
    },
    ***REMOVED*** Twice-weekly fairness report (Monday and Thursday)
    "schedule-metrics-highfreq-fairness-report": {
        "task": "app.tasks.schedule_metrics_tasks.generate_fairness_trend_report",
        "schedule": crontab(
            hour=7,
            minute=0,
            day_of_week="1,4",  ***REMOVED*** Monday and Thursday
        ),
        "kwargs": {
            "weeks_back": 12,
        },
        "options": {
            "queue": "metrics",
        },
    },
}


def get_beat_schedule_for_environment(env: str = "production") -> dict:
    """
    Get beat schedule configuration for specific environment.

    Args:
        env: Environment name ("production", "development", "high_freq")

    Returns:
        Dict with beat schedule configuration
    """
    schedules = {
        "production": SCHEDULE_METRICS_BEAT_SCHEDULE,
        "development": SCHEDULE_METRICS_BEAT_SCHEDULE_DEV,
        "high_freq": SCHEDULE_METRICS_BEAT_SCHEDULE_HIGH_FREQ,
    }

    return schedules.get(env, SCHEDULE_METRICS_BEAT_SCHEDULE)


***REMOVED*** Task routing configuration
SCHEDULE_METRICS_TASK_ROUTES = {
    "app.tasks.schedule_metrics_tasks.*": {"queue": "metrics"},
}


***REMOVED*** Queue configuration for metrics tasks
SCHEDULE_METRICS_TASK_QUEUES = {
    "metrics": {
        "exchange": "metrics",
        "routing_key": "metrics",
    },
}


***REMOVED*** Additional configuration for metrics tasks
SCHEDULE_METRICS_TASK_CONFIG = {
    ***REMOVED*** Task time limits
    "task_time_limit": 600,  ***REMOVED*** 10 minutes max per task
    "task_soft_time_limit": 540,  ***REMOVED*** Soft limit at 9 minutes

    ***REMOVED*** Task result settings
    "result_expires": 86400,  ***REMOVED*** Results expire after 24 hours (longer than default)

    ***REMOVED*** Task acknowledgment
    "task_acks_late": True,  ***REMOVED*** Acknowledge after completion (not before)
    "task_reject_on_worker_lost": True,  ***REMOVED*** Reject if worker crashes

    ***REMOVED*** Task serialization
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],

    ***REMOVED*** Task compression
    "task_compression": "gzip",  ***REMOVED*** Compress large result payloads
    "result_compression": "gzip",
}


def configure_celery_for_schedule_metrics(celery_app):
    """
    Configure Celery app with schedule metrics tasks.

    This is a convenience function to apply all schedule metrics
    configuration to a Celery app instance.

    Args:
        celery_app: Celery application instance

    Usage:
        from app.core.celery_app import celery_app
        from app.tasks.periodic_tasks import configure_celery_for_schedule_metrics

        configure_celery_for_schedule_metrics(celery_app)
    """
    ***REMOVED*** Update beat schedule
    celery_app.conf.beat_schedule.update(
        get_schedule_metrics_beat_schedule()
    )

    ***REMOVED*** Update task routes
    if not hasattr(celery_app.conf, 'task_routes'):
        celery_app.conf.task_routes = {}
    celery_app.conf.task_routes.update(SCHEDULE_METRICS_TASK_ROUTES)

    ***REMOVED*** Update task queues
    if not hasattr(celery_app.conf, 'task_queues'):
        celery_app.conf.task_queues = {}
    celery_app.conf.task_queues.update(SCHEDULE_METRICS_TASK_QUEUES)

    ***REMOVED*** Apply additional configuration
    celery_app.conf.update(SCHEDULE_METRICS_TASK_CONFIG)
