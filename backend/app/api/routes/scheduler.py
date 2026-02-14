"""
Background Job Scheduler API Routes.

Provides endpoints for managing scheduled jobs:
- Create, update, delete jobs
- List jobs and execution history
- Pause/resume jobs
- Get job statistics
- Sync scheduler with database
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.scheduled_job import JobExecution
from app.models.user import User
from app.scheduler import get_scheduler
from app.scheduler.persistence import JobPersistence
from app.schemas.scheduler import (
    JobActionResponseSchema,
    JobCreateSchema,
    JobExecutionListSchema,
    JobExecutionSchema,
    JobListResponseSchema,
    JobResponseSchema,
    JobStatisticsSchema,
    JobUpdateSchema,
    SyncResultSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Job Management
# ============================================================================


@router.post("/jobs", response_model=JobResponseSchema, status_code=201)
async def create_job(
    job_data: JobCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobResponseSchema:
    """
    Create a new scheduled job.

    Requires authentication and admin/coordinator role.

    Example:
        >>> POST /api/v1/scheduler/jobs
        >>> {
        >>>     "name": "daily_cleanup",
        >>>     "job_func": "app.scheduler.jobs.cleanup_old_executions",
        >>>     "trigger_type": "cron",
        >>>     "trigger_config": {"hour": 3, "minute": 0},
        >>>     "kwargs": {"retention_days": 90},
        >>>     "description": "Clean up old job execution records"
        >>> }
    """
    # Check permissions
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to create scheduled jobs"
        )

    try:
        scheduler = get_scheduler()

        # Add job to scheduler
        job_id = scheduler.add_job(
            name=job_data.name,
            job_func=job_data.job_func,
            trigger_type=job_data.trigger_type,
            trigger_config=job_data.trigger_config,
            args=job_data.args,
            kwargs=job_data.kwargs,
            max_instances=job_data.max_instances,
            misfire_grace_time=job_data.misfire_grace_time,
            coalesce=job_data.coalesce,
            description=job_data.description,
            created_by=current_user.username,
        )

        # Get the created job
        persistence = JobPersistence(db)
        job = persistence.get_job_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=500, detail="Failed to retrieve created job"
            )

        return JobResponseSchema.model_validate(job)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.get("/jobs", response_model=JobListResponseSchema)
async def list_jobs(
    enabled_only: bool = Query(False, description="Only return enabled jobs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobListResponseSchema:
    """
    List all scheduled jobs.

    Requires authentication.

    Example:
        >>> GET /api/v1/scheduler/jobs?enabled_only=true
        {
            "total": 5,
            "jobs": [...]
        }
    """
    try:
        persistence = JobPersistence(db)
        jobs = persistence.get_all_jobs(enabled_only=enabled_only)

        return JobListResponseSchema(
            total=len(jobs),
            jobs=[JobResponseSchema.model_validate(job) for job in jobs],
        )

    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list jobs")


@router.get("/jobs/{job_id}", response_model=JobResponseSchema)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobResponseSchema:
    """
    Get a specific scheduled job.

    Requires authentication.

    Example:
        >>> GET /api/v1/scheduler/jobs/{job_id}
    """
    try:
        persistence = JobPersistence(db)
        job = persistence.get_job_by_id(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobResponseSchema.model_validate(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job")


@router.patch("/jobs/{job_id}", response_model=JobResponseSchema)
async def update_job(
    job_id: UUID,
    job_data: JobUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobResponseSchema:
    """
    Update a scheduled job.

    Requires authentication and admin/coordinator role.

    Example:
        >>> PATCH /api/v1/scheduler/jobs/{job_id}
        >>> {
        >>>     "enabled": false,
        >>>     "description": "Updated description"
        >>> }
    """
    # Check permissions
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to update scheduled jobs"
        )

    try:
        persistence = JobPersistence(db)

        # Get current job
        job = persistence.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Update fields
        update_data = job_data.model_dump(exclude_unset=True)

        # Update in database
        updated_job = persistence.update_job(job_id, **update_data)

        if not updated_job:
            raise HTTPException(status_code=404, detail="Job not found")

        # If job was enabled/disabled, sync with scheduler
        if "enabled" in update_data:
            scheduler = get_scheduler()
            if update_data["enabled"]:
                scheduler.resume_job(job_id)
            else:
                scheduler.pause_job(job_id)

        return JobResponseSchema.model_validate(updated_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update job")


@router.delete("/jobs/{job_id}", response_model=JobActionResponseSchema)
async def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobActionResponseSchema:
    """
    Delete a scheduled job.

    Requires authentication and admin/coordinator role.

    Example:
        >>> DELETE /api/v1/scheduler/jobs/{job_id}
    """
    # Check permissions
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to delete scheduled jobs"
        )

    try:
        scheduler = get_scheduler()
        success = scheduler.remove_job(job_id)

        if not success:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobActionResponseSchema(
            success=True,
            message="Job deleted successfully",
            job_id=job_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete job")


# ============================================================================
# Job Control
# ============================================================================


@router.post("/jobs/{job_id}/pause", response_model=JobActionResponseSchema)
async def pause_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
) -> JobActionResponseSchema:
    """
    Pause a scheduled job.

    Requires authentication and admin/coordinator role.

    Example:
        >>> POST /api/v1/scheduler/jobs/{job_id}/pause
    """
    # Check permissions
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to pause scheduled jobs"
        )

    try:
        scheduler = get_scheduler()
        success = scheduler.pause_job(job_id)

        if not success:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobActionResponseSchema(
            success=True,
            message="Job paused successfully",
            job_id=job_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to pause job")


@router.post("/jobs/{job_id}/resume", response_model=JobActionResponseSchema)
async def resume_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
) -> JobActionResponseSchema:
    """
    Resume a paused job.

    Requires authentication and admin/coordinator role.

    Example:
        >>> POST /api/v1/scheduler/jobs/{job_id}/resume
    """
    # Check permissions
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to resume scheduled jobs"
        )

    try:
        scheduler = get_scheduler()
        success = scheduler.resume_job(job_id)

        if not success:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobActionResponseSchema(
            success=True,
            message="Job resumed successfully",
            job_id=job_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resume job")


# ============================================================================
# Job Execution History
# ============================================================================


@router.get("/jobs/{job_id}/executions", response_model=JobExecutionListSchema)
async def get_job_executions(
    job_id: UUID,
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobExecutionListSchema:
    """
    Get execution history for a job.

    Requires authentication.

    Example:
        >>> GET /api/v1/scheduler/jobs/{job_id}/executions?limit=50
    """
    try:
        persistence = JobPersistence(db)

        # Verify job exists
        job = persistence.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get executions
        executions = persistence.get_job_executions(
            job_id=job_id,
            limit=limit,
            offset=offset,
        )

        # Count total executions
        total = (
            db.query(func.count(JobExecution.id))
            .filter(JobExecution.job_id == job_id)
            .scalar()
            or 0
        )

        return JobExecutionListSchema(
            total=total,
            limit=limit,
            offset=offset,
            executions=[JobExecutionSchema.model_validate(e) for e in executions],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job executions")


@router.get("/executions", response_model=JobExecutionListSchema)
async def get_all_executions(
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobExecutionListSchema:
    """
    Get execution history for all jobs.

    Requires authentication.

    Example:
        >>> GET /api/v1/scheduler/executions?limit=50
    """
    try:
        persistence = JobPersistence(db)

        executions = persistence.get_job_executions(
            job_id=None,
            limit=limit,
            offset=offset,
        )

        # Count total executions
        total = db.query(func.count(JobExecution.id)).scalar() or 0

        return JobExecutionListSchema(
            total=total,
            limit=limit,
            offset=offset,
            executions=[JobExecutionSchema.model_validate(e) for e in executions],
        )

    except Exception as e:
        logger.error(f"Error getting executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get executions")


# ============================================================================
# Job Statistics
# ============================================================================


@router.get("/jobs/{job_id}/statistics", response_model=JobStatisticsSchema)
async def get_job_statistics(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JobStatisticsSchema:
    """
    Get statistics for a job.

    Requires authentication.

    Example:
        >>> GET /api/v1/scheduler/jobs/{job_id}/statistics
    """
    try:
        persistence = JobPersistence(db)

        # Verify job exists
        job = persistence.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        stats = persistence.get_job_statistics(job_id)

        return JobStatisticsSchema(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job statistics")


# ============================================================================
# Scheduler Management
# ============================================================================


@router.post("/sync", response_model=SyncResultSchema)
async def sync_scheduler(
    current_user: User = Depends(get_current_active_user),
) -> SyncResultSchema:
    """
    Sync scheduler with database.

    Loads any new jobs from the database and removes deleted jobs.
    Requires authentication and admin/coordinator role.

    Example:
        >>> POST /api/v1/scheduler/sync
    """
    # Check permissions
    if not current_user.can_manage_schedules:
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to sync scheduler"
        )

    try:
        scheduler = get_scheduler()
        result = scheduler.sync_with_database()

        return SyncResultSchema(**result)

    except Exception as e:
        logger.error(f"Error syncing scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sync scheduler")


@router.get("/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get scheduler status.

    Requires authentication.

    Example:
        >>> GET /api/v1/scheduler/status
    """
    try:
        scheduler = get_scheduler()

        jobs = scheduler.list_jobs()

        return {
            "running": scheduler._started,
            "total_jobs": len(jobs),
            "jobs": jobs,
        }

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get scheduler status")
