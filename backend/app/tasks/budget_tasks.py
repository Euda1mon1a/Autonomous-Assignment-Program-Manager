"""
Budget-Aware Cron Manager Tasks.

Periodic tasks for monitoring and enforcing AI API budget limits.
Tracks Opus-consuming job costs and enforces daily/monthly budgets.

Configuration:
    Added to celery_app.py beat_schedule for periodic execution.
    Budget status checked hourly, daily report at 11 PM,
    monthly rollup on the 1st at 1 AM.
"""

import json
import logging
from datetime import UTC, datetime, timedelta

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="app.tasks.budget_tasks.check_budget_status",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    queue="maintenance",
)
def check_budget_status(self) -> dict:
    """
    Check current AI API budget status and trigger alerts if needed.

    Runs hourly to monitor spend against daily/monthly limits.
    Logs warnings at threshold levels and critical alerts when
    budget is exhausted.

    Returns:
        Dict with current budget status including spend, limits, and alerts.
    """
    from app.services.budget_cron_manager import BudgetCronManager

    logger.info("Checking AI API budget status")

    manager = BudgetCronManager()
    status = manager.get_budget_status()
    alerts = manager.check_alerts()

    # Log alerts by severity
    for alert in alerts:
        level = alert.get("level", "info")
        message = alert.get("message", "Budget alert triggered")

        if level == "critical":
            logger.critical("BUDGET ALERT [CRITICAL]: %s", message)
        elif level == "warning":
            logger.warning("BUDGET ALERT [WARNING]: %s", message)
        else:
            logger.info("BUDGET ALERT [INFO]: %s", message)

    # Log summary using the nested dict structure from get_budget_status()
    daily = status.get("daily", {})
    monthly = status.get("monthly", {})

    logger.info(
        "Budget status - Daily: $%.2f/$%.2f (%.1f%%) | Monthly: $%.2f/$%.2f (%.1f%%)",
        daily.get("spend_usd", 0),
        daily.get("budget_usd", 0),
        daily.get("utilization_pct", 0),
        monthly.get("spend_usd", 0),
        monthly.get("budget_usd", 0),
        monthly.get("utilization_pct", 0),
    )

    return status


@shared_task(
    name="app.tasks.budget_tasks.record_opus_usage",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="maintenance",
)
def record_opus_usage(
    self,
    task_name: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    job_id: str | None = None,
) -> dict:
    """
    Record AI API usage for budget tracking.

    Called after each Opus-consuming task completes to track
    token usage and estimated cost against budget limits.

    Args:
        task_name: Name of the task that consumed tokens.
        model_id: AI model identifier (e.g., 'claude-opus-4-6').
        input_tokens: Number of input tokens consumed.
        output_tokens: Number of output tokens consumed.
        job_id: Optional job/request identifier for tracing.

    Returns:
        Dict with usage summary including estimated cost.
    """
    from app.services.budget_cron_manager import BudgetCronManager

    logger.info(
        "Recording AI usage: task=%s model=%s input_tokens=%d output_tokens=%d job_id=%s",
        task_name,
        model_id,
        input_tokens,
        output_tokens,
        job_id,
    )

    manager = BudgetCronManager()
    usage_summary = manager.record_usage(
        task_name=task_name,
        model_id=model_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        job_id=job_id,
    )

    logger.info(
        "Usage recorded: cost=$%.4f daily_total=$%.2f",
        usage_summary.get("cost_usd", 0),
        usage_summary.get("daily_total_usd", 0),
    )

    return usage_summary


@shared_task(
    name="app.tasks.budget_tasks.budget_daily_report",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
    queue="maintenance",
)
def budget_daily_report(self) -> dict:
    """
    Generate and log a comprehensive daily budget report.

    Runs at 11 PM daily to summarize the day's AI API spending,
    budget utilization, blocked tasks, and top consumers.

    Returns:
        Dict with daily report including date, total_spend,
        budget_limit, utilization, tasks_blocked, top_consumers.
    """
    from app.services.budget_cron_manager import BudgetCronManager

    logger.info("Generating daily budget report")

    manager = BudgetCronManager()
    status = manager.get_budget_status()

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    daily = status.get("daily", {})
    daily_spend = daily.get("spend_usd", 0)
    daily_limit = daily.get("budget_usd", 0)
    utilization = daily.get("utilization_pct", 0)
    tasks_blocked = 0  # Would require tracking blocked count in Redis
    top_consumers = []

    report = {
        "date": today,
        "total_spend": daily_spend,
        "budget_limit": daily_limit,
        "utilization": round(utilization, 2),
        "tasks_blocked": tasks_blocked,
        "top_consumers": top_consumers,
    }

    # Log the daily report
    logger.info("=" * 60)
    logger.info("DAILY AI BUDGET REPORT - %s", today)
    logger.info("=" * 60)
    logger.info(
        "Total Spend:    $%.2f / $%.2f (%.1f%%)", daily_spend, daily_limit, utilization
    )
    logger.info("Tasks Blocked:  %d", tasks_blocked)

    if top_consumers:
        logger.info("Top Consumers:")
        for i, consumer in enumerate(top_consumers[:5], 1):
            consumer_name = consumer.get("task_name", "unknown")
            consumer_cost = consumer.get("total_cost", 0)
            consumer_calls = consumer.get("call_count", 0)
            logger.info(
                "  %d. %s - $%.2f (%d calls)",
                i,
                consumer_name,
                consumer_cost,
                consumer_calls,
            )

    logger.info("=" * 60)

    if utilization >= 90:
        logger.warning(
            "Daily budget utilization at %.1f%% - approaching limit", utilization
        )

    return report


@shared_task(
    name="app.tasks.budget_tasks.budget_monthly_rollup",
    bind=True,
    max_retries=1,
    default_retry_delay=600,
    queue="maintenance",
)
def budget_monthly_rollup(self) -> dict:
    """
    Generate monthly budget rollup report.

    Runs on the 1st of each month at 1 AM to summarize the previous
    month's AI API spending and produce a monthly summary.

    Returns:
        Dict with monthly report including period, total_spend,
        monthly_limit, utilization, daily_average, peak_day,
        total_tasks, and tasks_blocked.
    """
    from app.services.budget_cron_manager import BudgetCronManager

    logger.info("Generating monthly budget rollup")

    manager = BudgetCronManager()

    now = datetime.now(UTC)
    # Report covers the previous month
    first_of_current = now.replace(day=1)
    last_of_previous = first_of_current - timedelta(days=1)
    report_month = last_of_previous.strftime("%Y-%m")

    # Read previous month's spend directly from Redis (not current month)
    prev_month_key = BudgetCronManager._monthly_key(report_month)
    monthly_spend = float(manager.redis.get(prev_month_key) or 0)
    monthly_limit = manager.monthly_budget
    utilization = (monthly_spend / monthly_limit * 100) if monthly_limit > 0 else 0.0
    daily_average = 0.0  # Would require day-by-day tracking
    peak_day = {}
    total_tasks = 0
    tasks_blocked = 0

    report = {
        "period": report_month,
        "total_spend": monthly_spend,
        "monthly_limit": monthly_limit,
        "utilization": round(utilization, 2),
        "daily_average": daily_average,
        "peak_day": peak_day,
        "total_tasks": total_tasks,
        "tasks_blocked": tasks_blocked,
    }

    # Log the monthly report
    logger.info("=" * 60)
    logger.info("MONTHLY AI BUDGET ROLLUP - %s", report_month)
    logger.info("=" * 60)
    logger.info(
        "Total Spend:    $%.2f / $%.2f (%.1f%%)",
        monthly_spend,
        monthly_limit,
        utilization,
    )
    logger.info("Daily Average:  $%.2f", daily_average)

    if peak_day:
        logger.info(
            "Peak Day:       %s ($%.2f)",
            peak_day.get("date", "N/A"),
            peak_day.get("spend", 0),
        )

    logger.info("Total Tasks:    %d", total_tasks)
    logger.info("Tasks Blocked:  %d", tasks_blocked)
    logger.info("=" * 60)

    if utilization >= 80:
        logger.warning(
            "Monthly budget utilization at %.1f%% - review budget allocation",
            utilization,
        )

    return report


@shared_task(
    name="app.tasks.budget_tasks.cleanup_old_usage_logs",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    queue="maintenance",
)
def cleanup_old_usage_logs(self, retention_days: int = 90) -> dict:
    """
    Clean up old AI budget usage tracking keys from Redis.

    Removes ai_budget:* keys older than the retention period
    to prevent unbounded Redis memory growth.

    Args:
        retention_days: Number of days of usage data to retain.
            Defaults to 90 days.

    Returns:
        Dict with cleanup results including keys_scanned and keys_deleted.
    """
    import redis

    from app.core.config import get_settings

    logger.info("Cleaning up AI budget usage logs older than %d days", retention_days)

    settings = get_settings()
    redis_client = redis.Redis.from_url(
        settings.redis_url_with_password, decode_responses=True
    )

    cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")

    keys_scanned = 0
    keys_deleted = 0
    cursor = 0

    # Use SCAN to iterate over ai_budget:* keys without blocking Redis
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match="ai_budget:*", count=100)
        keys_scanned += len(keys)

        for key in keys:
            # Extract date from key pattern: ai_budget:daily:YYYY-MM-DD:*
            # or ai_budget:usage:YYYY-MM-DD:*
            parts = key.split(":")
            key_date = None
            for part in parts:
                # Look for date-like segments (YYYY-MM-DD)
                if len(part) == 10 and part[4] == "-" and part[7] == "-":
                    key_date = part
                    break

            if key_date and key_date < cutoff_str:
                redis_client.delete(key)
                keys_deleted += 1

        if cursor == 0:
            break

    logger.info(
        "Budget usage cleanup complete: scanned=%d deleted=%d retention=%d days",
        keys_scanned,
        keys_deleted,
        retention_days,
    )

    return {
        "keys_scanned": keys_scanned,
        "keys_deleted": keys_deleted,
        "retention_days": retention_days,
        "cutoff_date": cutoff_str,
    }


# Beat schedule for budget tasks
BUDGET_BEAT_SCHEDULE = {
    # Budget status check every hour
    "budget-status-check": {
        "task": "app.tasks.budget_tasks.check_budget_status",
        "schedule": 3600,  # 1 hour in seconds
        "options": {
            "queue": "maintenance",
            "expires": 1800,
        },
    },
    # Daily budget report at 11 PM
    "budget-daily-report": {
        "task": "app.tasks.budget_tasks.budget_daily_report",
        "schedule": {
            "__type__": "crontab",
            "hour": 23,
            "minute": 0,
        },
        "options": {
            "queue": "maintenance",
            "expires": 3600,
        },
    },
    # Monthly rollup on the 1st at 1 AM
    "budget-monthly-rollup": {
        "task": "app.tasks.budget_tasks.budget_monthly_rollup",
        "schedule": {
            "__type__": "crontab",
            "hour": 1,
            "minute": 0,
            "day_of_month": 1,
        },
        "options": {
            "queue": "maintenance",
            "expires": 3600,
        },
    },
    # Cleanup old usage logs monthly on the 2nd at 3 AM
    "budget-cleanup-usage-logs": {
        "task": "app.tasks.budget_tasks.cleanup_old_usage_logs",
        "schedule": {
            "__type__": "crontab",
            "hour": 3,
            "minute": 0,
            "day_of_month": 2,
        },
        "kwargs": {
            "retention_days": 90,
        },
        "options": {
            "queue": "maintenance",
            "expires": 3600,
        },
    },
}


def get_budget_beat_schedule() -> dict:
    """
    Get beat schedule configuration for budget tasks.

    Returns:
        Dict with beat schedule configuration.

    Usage:
        In celery_app.py:

        from app.tasks.budget_tasks import get_budget_beat_schedule

        celery_app.conf.beat_schedule.update(
            get_budget_beat_schedule()
        )
    """
    return BUDGET_BEAT_SCHEDULE


def configure_celery_for_budget(celery_app_instance) -> None:
    """
    Configure Celery app with budget monitoring tasks.

    Args:
        celery_app_instance: Celery application instance.

    Usage:
        from app.core.celery_app import celery_app
        from app.tasks.budget_tasks import configure_celery_for_budget

        configure_celery_for_budget(celery_app)
    """
    from celery.schedules import crontab

    # Convert schedule dicts to crontab objects for beat schedule
    schedule = {}
    for name, config in BUDGET_BEAT_SCHEDULE.items():
        entry = dict(config)
        sched = entry.get("schedule")
        if isinstance(sched, dict) and sched.get("__type__") == "crontab":
            sched_copy = {k: v for k, v in sched.items() if k != "__type__"}
            entry["schedule"] = crontab(**sched_copy)
        schedule[name] = entry

    # Update beat schedule
    celery_app_instance.conf.beat_schedule.update(schedule)

    # Add task route
    if not hasattr(celery_app_instance.conf, "task_routes"):
        celery_app_instance.conf.task_routes = {}
    celery_app_instance.conf.task_routes.update(
        {
            "app.tasks.budget_tasks.*": {"queue": "maintenance"},
        }
    )
