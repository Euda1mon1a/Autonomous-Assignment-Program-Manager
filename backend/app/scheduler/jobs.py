"""
Job definitions and utilities for the scheduler.

Provides decorators and utilities for defining scheduled jobs.
"""

import functools
import logging
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


class JobChain:
    """
    Represents a chain of jobs to be executed in sequence.

    Allows defining dependencies between jobs where one job's
    output becomes the next job's input.

    Example:
        >>> chain = JobChain()
        >>> chain.add_job("fetch_data", fetch_data_func, args=[url])
        >>> chain.add_job("process_data", process_data_func)
        >>> chain.add_job("save_results", save_results_func)
        >>> chain.execute()
    """

    def __init__(self):
        """Initialize an empty job chain."""
        self.jobs: list[dict[str, Any]] = []

    def add_job(
        self,
        name: str,
        func: Callable,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> "JobChain":
        """
        Add a job to the chain.

        Args:
            name: Name of the job
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Self for method chaining
        """
        self.jobs.append({
            "name": name,
            "func": func,
            "args": args or [],
            "kwargs": kwargs or {},
        })
        return self

    def execute(self) -> Any:
        """
        Execute all jobs in the chain sequentially.

        The output of each job is passed as the first argument to the next job.

        Returns:
            The result of the last job in the chain

        Raises:
            Exception: If any job in the chain fails
        """
        result = None

        for job in self.jobs:
            try:
                logger.info(f"Executing job '{job['name']}' in chain")

                # Pass previous result as first argument
                if result is not None:
                    args = [result] + list(job["args"])
                else:
                    args = job["args"]

                result = job["func"](*args, **job["kwargs"])

                logger.info(f"Job '{job['name']}' completed successfully")

            except Exception as e:
                logger.error(f"Job '{job['name']}' failed: {e}", exc_info=True)
                raise

        return result


def scheduled_job(
    name: str | None = None,
    description: str | None = None,
    max_instances: int = 1,
) -> Callable:
    """
    Decorator to mark a function as a scheduled job.

    Adds metadata to the function for easier registration with the scheduler.

    Args:
        name: Optional name for the job (defaults to function name)
        description: Optional description of what the job does
        max_instances: Maximum number of concurrent instances (default: 1)

    Returns:
        Decorated function with scheduling metadata

    Example:
        >>> @scheduled_job(name="daily_cleanup", max_instances=1)
        >>> def cleanup_old_records():
        >>>     # Implementation here
        >>>     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Add scheduling metadata
        wrapper._scheduled_job = True
        wrapper._job_name = name or func.__name__
        wrapper._job_description = description or func.__doc__
        wrapper._max_instances = max_instances

        return wrapper

    return decorator


def get_job_function(func_path: str) -> Callable:
    """
    Dynamically import and return a function from a string path.

    Args:
        func_path: Fully qualified function path (e.g., "app.tasks.cleanup.cleanup_task")

    Returns:
        The imported function

    Raises:
        ImportError: If the module or function cannot be imported
        AttributeError: If the function doesn't exist in the module
    """
    try:
        module_path, func_name = func_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[func_name])
        return getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import job function '{func_path}': {e}")
        raise


# Example job functions that can be scheduled

@scheduled_job(name="heartbeat", description="Scheduler heartbeat check")
def heartbeat_job() -> dict[str, Any]:
    """
    Heartbeat job to verify scheduler is running.

    Returns:
        dict: Status information
    """
    logger.info("Scheduler heartbeat")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@scheduled_job(name="cleanup_executions", description="Clean up old job execution records")
def cleanup_old_executions(retention_days: int = 90) -> dict[str, Any]:
    """
    Clean up old job execution records.

    Args:
        retention_days: Number of days to retain execution records

    Returns:
        dict: Cleanup results
    """
    from datetime import timedelta

    from app.db.session import SessionLocal
    from app.models.scheduled_job import JobExecution

    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    deleted_count = 0

    db = SessionLocal()
    try:
        # Delete old execution records
        result = db.query(JobExecution).filter(
            JobExecution.started_at < cutoff_date
        ).delete()
        db.commit()
        deleted_count = result

        logger.info(f"Deleted {deleted_count} old job execution records")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clean up old executions: {e}", exc_info=True)
        raise
    finally:
        db.close()


@scheduled_job(name="sync_schedules", description="Sync scheduler state with database")
def sync_scheduler_state() -> dict[str, Any]:
    """
    Sync scheduler state with database.

    Ensures scheduler has all enabled jobs from the database loaded.

    Returns:
        dict: Sync results
    """
    from app.scheduler import get_scheduler

    scheduler = get_scheduler()
    result = scheduler.sync_with_database()

    logger.info(
        f"Scheduler sync complete: {result['added']} added, "
        f"{result['removed']} removed, {result['updated']} updated"
    )

    return result
