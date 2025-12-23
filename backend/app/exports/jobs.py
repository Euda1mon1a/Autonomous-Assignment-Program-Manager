"""
Celery tasks for scheduled exports.

Background tasks for:
- Running scheduled export jobs
- Cleanup of old export executions
- Export job health checks
"""

import logging
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy import select

from app.db.session import get_async_session_context
from app.exports.scheduler import ExportSchedulerService
from app.models.export_job import ExportJob, ExportJobExecution, ExportJobStatus

logger = logging.getLogger(__name__)


@shared_task(name="app.exports.jobs.run_scheduled_exports", bind=True)
def run_scheduled_exports(self):
    """
    Run all export jobs that are due for execution.

    This task should be scheduled to run periodically (e.g., every 5 minutes).
    """
    import asyncio

    async def _run_scheduled_exports():
        """Async implementation of running scheduled exports."""
        async with get_async_session_context() as db:
            scheduler = ExportSchedulerService(db)

            # Get jobs due for execution
            due_jobs = await scheduler.get_due_jobs()

            if not due_jobs:
                logger.info("No export jobs due for execution")
                return {"executed": 0, "message": "No jobs due"}

            logger.info(f"Found {len(due_jobs)} export jobs due for execution")

            executed_count = 0
            failed_count = 0

            for job in due_jobs:
                try:
                    logger.info(f"Executing export job: {job.name} (ID: {job.id})")
                    execution = await scheduler.execute_job(
                        job_id=str(job.id), triggered_by="scheduled"
                    )

                    if execution.status == ExportJobStatus.COMPLETED:
                        executed_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(
                        f"Failed to execute export job {job.name}: {e}", exc_info=True
                    )
                    failed_count += 1

            logger.info(
                f"Export job execution completed: {executed_count} successful, "
                f"{failed_count} failed"
            )

            return {
                "executed": executed_count,
                "failed": failed_count,
                "total": len(due_jobs),
            }

    # Run async function
    return asyncio.run(_run_scheduled_exports())


@shared_task(name="app.exports.jobs.execute_export_job", bind=True)
def execute_export_job(self, job_id: str, triggered_by: str = "manual"):
    """
    Execute a specific export job.

    Args:
        job_id: Export job ID
        triggered_by: Who/what triggered this execution

    Returns:
        dict: Execution result
    """
    import asyncio

    async def _execute_export_job():
        """Async implementation of executing export job."""
        async with get_async_session_context() as db:
            scheduler = ExportSchedulerService(db)

            try:
                execution = await scheduler.execute_job(
                    job_id=job_id, triggered_by=triggered_by
                )

                return {
                    "success": execution.status == ExportJobStatus.COMPLETED,
                    "execution_id": str(execution.id),
                    "status": execution.status.value,
                    "row_count": execution.row_count,
                    "runtime_seconds": execution.runtime_seconds,
                    "error_message": execution.error_message,
                }

            except Exception as e:
                logger.error(
                    f"Failed to execute export job {job_id}: {e}", exc_info=True
                )
                return {"success": False, "error": str(e)}

    # Run async function
    return asyncio.run(_execute_export_job())


@shared_task(name="app.exports.jobs.cleanup_old_executions", bind=True)
def cleanup_old_executions(self, retention_days: int = 90):
    """
    Cleanup old export job executions.

    Args:
        retention_days: Number of days to retain execution history

    Returns:
        dict: Cleanup result
    """
    import asyncio

    async def _cleanup_old_executions():
        """Async implementation of cleaning up old executions."""
        async with get_async_session_context() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Delete old executions
            result = await db.execute(
                select(ExportJobExecution).where(
                    ExportJobExecution.started_at < cutoff_date
                )
            )
            old_executions = result.scalars().all()

            deleted_count = len(old_executions)

            for execution in old_executions:
                await db.delete(execution)

            await db.commit()

            logger.info(
                f"Cleaned up {deleted_count} old export executions (older than {retention_days} days)"
            )

            return {
                "deleted": deleted_count,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            }

    # Run async function
    return asyncio.run(_cleanup_old_executions())


@shared_task(name="app.exports.jobs.export_health_check", bind=True)
def export_health_check(self):
    """
    Check health of export job system.

    Returns:
        dict: Health check result
    """
    import asyncio

    async def _export_health_check():
        """Async implementation of export health check."""
        async with get_async_session_context() as db:
            # Count total jobs
            total_jobs_result = await db.execute(select(ExportJob))
            total_jobs = len(total_jobs_result.scalars().all())

            # Count enabled jobs
            enabled_jobs_result = await db.execute(
                select(ExportJob).where(ExportJob.enabled == True)
            )
            enabled_jobs = len(enabled_jobs_result.scalars().all())

            # Count scheduled jobs
            scheduled_jobs_result = await db.execute(
                select(ExportJob).where(
                    ExportJob.enabled == True, ExportJob.schedule_enabled == True
                )
            )
            scheduled_jobs = len(scheduled_jobs_result.scalars().all())

            # Count recent executions (last 24 hours)
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_executions_result = await db.execute(
                select(ExportJobExecution).where(
                    ExportJobExecution.started_at >= last_24h
                )
            )
            recent_executions = recent_executions_result.scalars().all()

            successful = len(
                [e for e in recent_executions if e.status == ExportJobStatus.COMPLETED]
            )
            failed = len(
                [e for e in recent_executions if e.status == ExportJobStatus.FAILED]
            )

            # Check for jobs that should have run but didn't
            overdue_jobs_result = await db.execute(
                select(ExportJob).where(
                    ExportJob.enabled == True,
                    ExportJob.schedule_enabled == True,
                    ExportJob.next_run_at < datetime.utcnow() - timedelta(hours=1),
                )
            )
            overdue_jobs = len(overdue_jobs_result.scalars().all())

            health_status = "healthy"
            if overdue_jobs > 0:
                health_status = "degraded"
            if failed > successful and failed > 0:
                health_status = "unhealthy"

            result = {
                "status": health_status,
                "total_jobs": total_jobs,
                "enabled_jobs": enabled_jobs,
                "scheduled_jobs": scheduled_jobs,
                "recent_executions_24h": len(recent_executions),
                "successful_24h": successful,
                "failed_24h": failed,
                "overdue_jobs": overdue_jobs,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Export health check: {result}")
            return result

    # Run async function
    return asyncio.run(_export_health_check())


@shared_task(name="app.exports.jobs.update_next_run_times", bind=True)
def update_next_run_times(self):
    """
    Update next_run_at for all scheduled jobs.

    This is useful after system downtime or clock changes.

    Returns:
        dict: Update result
    """
    import asyncio

    async def _update_next_run_times():
        """Async implementation of updating next run times."""
        async with get_async_session_context() as db:
            scheduler = ExportSchedulerService(db)

            # Get all scheduled jobs
            result = await db.execute(
                select(ExportJob).where(
                    ExportJob.enabled == True, ExportJob.schedule_enabled == True
                )
            )
            scheduled_jobs = result.scalars().all()

            updated_count = 0

            for job in scheduled_jobs:
                if job.schedule_cron:
                    # Recalculate next run time
                    job.next_run_at = scheduler._calculate_next_run_time(
                        job.schedule_cron
                    )
                    updated_count += 1

            await db.commit()

            logger.info(
                f"Updated next_run_at for {updated_count} scheduled export jobs"
            )

            return {
                "updated": updated_count,
                "total_scheduled": len(scheduled_jobs),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # Run async function
    return asyncio.run(_update_next_run_times())
