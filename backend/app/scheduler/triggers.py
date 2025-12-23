"""
Trigger types for job scheduling.

Provides different trigger types for scheduling jobs:
- CronTrigger: Schedule jobs using cron expressions
- IntervalTrigger: Schedule jobs at fixed intervals
- DateTrigger: Schedule one-time jobs for a specific date/time
"""

from datetime import datetime
from typing import Any

from apscheduler.triggers.cron import CronTrigger as APCronTrigger
from apscheduler.triggers.date import DateTrigger as APDateTrigger
from apscheduler.triggers.interval import IntervalTrigger as APIntervalTrigger
from pydantic import BaseModel


class CronTriggerConfig(BaseModel):
    """
    Configuration for cron-based scheduling.

    Attributes:
        year: 4-digit year
        month: Month (1-12)
        day: Day of month (1-31)
        week: ISO week (1-53)
        day_of_week: Number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
        hour: Hour (0-23)
        minute: Minute (0-59)
        second: Second (0-59)
        start_date: Earliest possible date/time to trigger on
        end_date: Latest possible date/time to trigger on
        timezone: Time zone to use for the date/time calculations

    Example:
        >>> # Run every day at 3:00 AM
        >>> CronTriggerConfig(hour=3, minute=0)
        >>> # Run every Monday at 9:30 AM
        >>> CronTriggerConfig(day_of_week='mon', hour=9, minute=30)
        >>> # Run every 15 minutes during business hours
        >>> CronTriggerConfig(hour='9-17', minute='*/15')
    """

    year: str | int | None = None
    month: str | int | None = None
    day: str | int | None = None
    week: str | int | None = None
    day_of_week: str | int | None = None
    hour: str | int | None = None
    minute: str | int | None = None
    second: str | int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    timezone: str = "UTC"

    def to_apscheduler_trigger(self) -> APCronTrigger:
        """
        Convert to APScheduler CronTrigger.

        Returns:
            APCronTrigger: APScheduler trigger instance
        """
        return APCronTrigger(
            year=self.year,
            month=self.month,
            day=self.day,
            week=self.week,
            day_of_week=self.day_of_week,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            start_date=self.start_date,
            end_date=self.end_date,
            timezone=self.timezone,
        )


class IntervalTriggerConfig(BaseModel):
    """
    Configuration for interval-based scheduling.

    Attributes:
        weeks: Number of weeks to wait
        days: Number of days to wait
        hours: Number of hours to wait
        minutes: Number of minutes to wait
        seconds: Number of seconds to wait
        start_date: Starting point for the interval calculation
        end_date: Latest possible date/time to trigger on
        timezone: Time zone to use for the date/time calculations

    Example:
        >>> # Run every 30 minutes
        >>> IntervalTriggerConfig(minutes=30)
        >>> # Run every 2 hours starting at noon
        >>> IntervalTriggerConfig(hours=2, start_date=datetime(2024, 1, 1, 12, 0))
        >>> # Run every day at the same time
        >>> IntervalTriggerConfig(days=1)
    """

    weeks: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    start_date: datetime | None = None
    end_date: datetime | None = None
    timezone: str = "UTC"

    def to_apscheduler_trigger(self) -> APIntervalTrigger:
        """
        Convert to APScheduler IntervalTrigger.

        Returns:
            APIntervalTrigger: APScheduler trigger instance
        """
        return APIntervalTrigger(
            weeks=self.weeks,
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            start_date=self.start_date,
            end_date=self.end_date,
            timezone=self.timezone,
        )


class DateTriggerConfig(BaseModel):
    """
    Configuration for one-time date-based scheduling.

    Attributes:
        run_date: The date/time to run the job on
        timezone: Time zone to use for the date/time

    Example:
        >>> # Run once on January 1, 2025 at 10:00 AM UTC
        >>> DateTriggerConfig(run_date=datetime(2025, 1, 1, 10, 0))
    """

    run_date: datetime
    timezone: str = "UTC"

    def to_apscheduler_trigger(self) -> APDateTrigger:
        """
        Convert to APScheduler DateTrigger.

        Returns:
            APDateTrigger: APScheduler trigger instance
        """
        return APDateTrigger(
            run_date=self.run_date,
            timezone=self.timezone,
        )


def create_trigger(trigger_type: str, config: dict[str, Any]) -> Any:
    """
    Create a trigger from type and configuration.

    Args:
        trigger_type: Type of trigger (cron, interval, date)
        config: Trigger configuration dictionary

    Returns:
        APScheduler trigger instance

    Raises:
        ValueError: If trigger_type is invalid
    """
    if trigger_type == "cron":
        trigger_config = CronTriggerConfig(**config)
        return trigger_config.to_apscheduler_trigger()
    elif trigger_type == "interval":
        trigger_config = IntervalTriggerConfig(**config)
        return trigger_config.to_apscheduler_trigger()
    elif trigger_type == "date":
        trigger_config = DateTriggerConfig(**config)
        return trigger_config.to_apscheduler_trigger()
    else:
        raise ValueError(f"Invalid trigger type: {trigger_type}")
