"""
Export scheduler API routes.

Provides endpoints for managing scheduled data exports including:
- Export job CRUD operations
- Manual job execution
- Execution history
- Export templates
- Statistics
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_async_db, get_db
from app.exports.jobs import execute_export_job
from app.exports.scheduler import ExportSchedulerService
from app.models.export_job import (
    ExportFormat,
    ExportJob,
    ExportJobExecution,
    ExportJobStatus,
    ExportTemplate,
)
from app.models.user import User
from app.schemas.export import (
    ExportJobCreate,
    ExportJobExecutionListResponse,
    ExportJobExecutionResponse,
    ExportJobListResponse,
    ExportJobResponse,
    ExportJobRunRequest,
    ExportJobRunResponse,
    ExportJobStatsResponse,
    ExportJobUpdate,
    ExportTemplateInfo,
    ExportTemplateListResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Export Job CRUD
# ============================================================================


@router.post("", response_model=ExportJobResponse, status_code=201)
async def create_export_job(
    job_data: ExportJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new export job.

    Requires authentication. The job will be created with the current user as creator.
    """
    scheduler = ExportSchedulerService(db)

    try:
        job = await scheduler.create_job(
            job_data=job_data.model_dump(exclude_unset=True),
            created_by=current_user.username,
        )
        return job
    except Exception as e:
        logger.error(f"Failed to create export job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create export job")


@router.get("", response_model=ExportJobListResponse)
async def list_export_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    enabled_only: bool = Query(False, description="Only return enabled jobs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List export jobs with pagination.

    Requires authentication.
    """
    scheduler = ExportSchedulerService(db)

    try:
        jobs, total = await scheduler.list_jobs(
            page=page, page_size=page_size, enabled_only=enabled_only
        )

        total_pages = (total + page_size - 1) // page_size

        return ExportJobListResponse(
            jobs=jobs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error(f"Failed to list export jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list export jobs")


@router.get("/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific export job by ID.

    Requires authentication.
    """
    scheduler = ExportSchedulerService(db)

    job = await scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    return job


@router.patch("/{job_id}", response_model=ExportJobResponse)
async def update_export_job(
    job_id: str,
    update_data: ExportJobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update an export job.

    Requires authentication. Only provided fields will be updated.
    """
    scheduler = ExportSchedulerService(db)

    try:
        job = await scheduler.update_job(
            job_id=job_id, update_data=update_data.model_dump(exclude_unset=True)
        )

        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update export job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update export job")


@router.delete("/{job_id}", status_code=204)
async def delete_export_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete an export job.

    Requires authentication. This will also stop any scheduled executions.
    """
    scheduler = ExportSchedulerService(db)

    success = await scheduler.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Export job not found")

    return None


# ============================================================================
# Job Execution
# ============================================================================


@router.post("/{job_id}/run", response_model=ExportJobRunResponse)
async def run_export_job(
    job_id: str,
    request: ExportJobRunRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Manually trigger execution of an export job.

    Requires authentication. The job will be executed asynchronously via Celery.
    Returns immediately with execution ID for tracking.
    """
    # Verify job exists
    scheduler = ExportSchedulerService(db)
    job = await scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    try:
        # Queue job execution via Celery
        task = execute_export_job.delay(
            job_id=job_id, triggered_by=f"manual:{current_user.username}"
        )

        logger.info(
            f"Queued export job {job.name} (ID: {job_id}) for execution via Celery task {task.id}"
        )

        return ExportJobRunResponse(
            execution_id=task.id,
            job_id=job_id,
            job_name=job.name,
            status="queued",
            message="Export job queued for execution",
        )

    except Exception as e:
        logger.error(f"Failed to queue export job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to queue export job")


# ============================================================================
# Execution History
# ============================================================================


@router.get("/{job_id}/executions", response_model=ExportJobExecutionListResponse)
async def list_job_executions(
    job_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: ExportJobStatus | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List execution history for a specific export job.

    Requires authentication.
    """
    # Verify job exists
    scheduler = ExportSchedulerService(db)
    job = await scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    try:
        # Build query
        query = select(ExportJobExecution).where(ExportJobExecution.job_id == job_id)
        if status:
            query = query.where(ExportJobExecution.status == status.value)

        # Get total count
        count_query = (
            select(func.count())
            .select_from(ExportJobExecution)
            .where(ExportJobExecution.job_id == job_id)
        )
        if status:
            count_query = count_query.where(ExportJobExecution.status == status.value)
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(ExportJobExecution.started_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        executions = list(result.scalars().all())

        total_pages = (total + page_size - 1) // page_size

        return ExportJobExecutionListResponse(
            executions=executions,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(f"Failed to list job executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list job executions")


@router.get("/executions/{execution_id}", response_model=ExportJobExecutionResponse)
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get details of a specific execution.

    Requires authentication.
    """
    result = await db.execute(
        select(ExportJobExecution).where(ExportJobExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution


# ============================================================================
# Templates
# ============================================================================


@router.get("/templates/list", response_model=ExportTemplateListResponse)
async def list_export_templates(
    current_user: User = Depends(get_current_active_user),
):
    """
    List available export templates.

    Requires authentication.
    """
    templates = [
        ExportTemplateInfo(
            template=ExportTemplate.FULL_SCHEDULE,
            name="Full Schedule",
            description="Complete schedule with all assignments",
            supported_formats=[ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX],
            default_filters={"start_date": None, "end_date": None},
            available_columns=[
                "date",
                "time_of_day",
                "person_name",
                "person_type",
                "role",
                "activity",
            ],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.PERSONNEL,
            name="Personnel",
            description="All personnel records",
            supported_formats=[ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX],
            default_filters={"type": None, "pgy_level": None},
            available_columns=[
                "id",
                "name",
                "type",
                "pgy_level",
                "email",
                "specialties",
                "performs_procedures",
            ],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.ABSENCES,
            name="Absences",
            description="Absence and leave records",
            supported_formats=[ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX],
            default_filters={
                "start_date": None,
                "end_date": None,
                "absence_type": None,
            },
            available_columns=[
                "person_name",
                "absence_type",
                "start_date",
                "end_date",
                "notes",
            ],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.CERTIFICATIONS,
            name="Certifications",
            description="Personnel certifications and credentials",
            supported_formats=[ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX],
            default_filters={},
            available_columns=[
                "person_name",
                "certification_name",
                "expiration_date",
                "status",
            ],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.ACGME_COMPLIANCE,
            name="ACGME Compliance",
            description="ACGME compliance reports",
            supported_formats=[ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX],
            default_filters={"start_date": None, "end_date": None},
            available_columns=[
                "person_name",
                "hours_worked",
                "violations",
                "compliance_status",
            ],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.SWAP_HISTORY,
            name="Swap History",
            description="Schedule swap request history",
            supported_formats=[ExportFormat.CSV, ExportFormat.JSON, ExportFormat.XLSX],
            default_filters={},
            available_columns=[
                "swap_type",
                "status",
                "requested_date",
                "created_at",
                "executed_at",
            ],
        ),
    ]

    return ExportTemplateListResponse(templates=templates)


# ============================================================================
# Statistics
# ============================================================================


@router.get("/stats/overview", response_model=ExportJobStatsResponse)
async def get_export_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get export job statistics.

    Requires authentication.
    """
    try:
        # Count total jobs
        total_jobs_result = await db.execute(
            select(func.count()).select_from(ExportJob)
        )
        total_jobs = total_jobs_result.scalar()

        # Count active jobs
        active_jobs_result = await db.execute(
            select(func.count())
            .select_from(ExportJob)
            .where(ExportJob.enabled.is_(True))
        )
        active_jobs = active_jobs_result.scalar()

        # Count scheduled jobs
        scheduled_jobs_result = await db.execute(
            select(func.count())
            .select_from(ExportJob)
            .where(ExportJob.enabled.is_(True), ExportJob.schedule_enabled.is_(True))
        )
        scheduled_jobs = scheduled_jobs_result.scalar()

        # Count executions
        total_executions_result = await db.execute(
            select(func.count()).select_from(ExportJobExecution)
        )
        total_executions = total_executions_result.scalar()

        # Count successful executions
        successful_result = await db.execute(
            select(func.count())
            .select_from(ExportJobExecution)
            .where(ExportJobExecution.status == ExportJobStatus.COMPLETED.value)
        )
        successful_executions = successful_result.scalar()

        # Count failed executions
        failed_result = await db.execute(
            select(func.count())
            .select_from(ExportJobExecution)
            .where(ExportJobExecution.status == ExportJobStatus.FAILED.value)
        )
        failed_executions = failed_result.scalar()

        # Calculate average runtime
        avg_runtime_result = await db.execute(
            select(func.avg(ExportJobExecution.runtime_seconds)).where(
                ExportJobExecution.status == ExportJobStatus.COMPLETED.value
            )
        )
        avg_runtime = avg_runtime_result.scalar()

        # Calculate total rows and bytes
        total_rows_result = await db.execute(
            select(func.sum(ExportJobExecution.row_count)).where(
                ExportJobExecution.status == ExportJobStatus.COMPLETED.value
            )
        )
        total_rows = total_rows_result.scalar() or 0

        total_bytes_result = await db.execute(
            select(func.sum(ExportJobExecution.file_size_bytes)).where(
                ExportJobExecution.status == ExportJobStatus.COMPLETED.value
            )
        )
        total_bytes = total_bytes_result.scalar() or 0

        return ExportJobStatsResponse(
            totalJobs=total_jobs,
            activeJobs=active_jobs,
            scheduledJobs=scheduled_jobs,
            totalExecutions=total_executions,
            successfulExecutions=successful_executions,
            failedExecutions=failed_executions,
            averageRuntimeSeconds=float(avg_runtime) if avg_runtime else None,
            totalRowsExported=int(total_rows),
            totalBytesExported=int(total_bytes),
        )

    except Exception as e:
        logger.error(f"Failed to get export stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get export statistics")
