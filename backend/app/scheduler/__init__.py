"""
Background job scheduler package.

Provides flexible job scheduling capabilities beyond Celery's periodic tasks:
- Cron-based scheduling
- Interval-based scheduling
- One-time jobs
- Job persistence to database
- Missed job handling
- Job chaining support

The scheduler uses APScheduler as the underlying engine and stores
job configurations in the database for persistence across restarts.
"""

from app.scheduler.scheduler import JobScheduler, get_scheduler

__all__ = [
    "JobScheduler",
    "get_scheduler",
]
