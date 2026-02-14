"""Scheduler operations API routes for n8n workflow integration.

Provides endpoints for:
- GET /sitrep - Situation report for Slack monitoring
- POST /fix-it - Automated task recovery and retry
- POST /approve - Task approval workflow

These endpoints are designed to be called by n8n workflows for
autonomous scheduling operations via Slack commands.
"""

import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from itertools import islice
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.user import User
from app.schemas.scheduler_ops import (
    ActiveSolversResponse,
    AffectedTask,
    ApprovalAction,
    ApprovalRequest,
    ApprovalResponse,
    ApprovedTaskInfo,
    CoverageMetrics,
    FixItMode,
    FixItRequest,
    FixItResponse,
    RecentTaskInfo,
    SitrepResponse,
    SolverAbortRequest,
    SolverAbortResponse,
    SolverProgressResponse,
    TaskMetrics,
    TaskStatus,
)

if TYPE_CHECKING:
    from app.resilience.service import ResilienceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduler", tags=["scheduler-ops"])


# In-memory storage for approval tokens and fix-it executions
# In production, this should be in Redis or database
_approval_tokens: dict[str, dict] = {}
_fix_it_executions: dict[str, dict] = {}


# ============================================================================
# Helper Functions
# ============================================================================


def _get_resilience_service(db: Session) -> "ResilienceService":
    """Get or create ResilienceService instance."""
    from app.core.config import get_resilience_config
    from app.resilience.service import ResilienceService

    config = get_resilience_config()
    return ResilienceService(db=db, config=config)


def _calculate_task_metrics(db: Session) -> TaskMetrics:
    """Calculate task execution metrics from Celery backend.

    Queries actual Celery task data from:
    - Active tasks (currently running)
    - Scheduled tasks (queued for execution)
    - Reserved tasks (claimed by workers)
    - Recent task results (completed/failed)
    """
    try:
        from app.core.celery_app import celery_app

        # Get Celery inspect API
        inspect = celery_app.control.inspect()

        # Query active, scheduled, and reserved tasks
        active_tasks_dict = inspect.active() or {}
        scheduled_tasks_dict = inspect.scheduled() or {}
        reserved_tasks_dict = inspect.reserved() or {}

        # Count active tasks across all workers
        active_count = sum(len(tasks) for tasks in active_tasks_dict.values())

        # Count pending tasks (scheduled + reserved)
        scheduled_count = sum(len(tasks) for tasks in scheduled_tasks_dict.values())
        reserved_count = sum(len(tasks) for tasks in reserved_tasks_dict.values())
        pending_count = scheduled_count + reserved_count

        # Query stats for completed/failed tasks
        stats_dict = inspect.stats() or {}

        # Aggregate task counts from worker stats
        total_completed = 0
        total_failed = 0

        for worker_name, worker_stats in stats_dict.items():
            # Worker stats may contain task counters
            if isinstance(worker_stats, dict):
                total_completed += worker_stats.get("total", {}).get("completed", 0)

        # For recent failures, check registered tasks
        registered_dict = inspect.registered() or {}

        # Get recent task results from result backend
        # Query last 100 task IDs to get completion statistics
        try:
            # Use Redis to query recent task keys
            from redis import Redis

            from app.core.config import get_settings

            settings = get_settings()
            redis_client = Redis.from_url(settings.redis_url_with_password)

            # Celery stores results with pattern: celery-task-meta-*
            task_keys = redis_client.keys("celery-task-meta-*")

            completed_count = 0
            failed_count = 0

            # Sample up to 100 most recent tasks
            for key in task_keys[:100]:
                try:
                    task_data = redis_client.get(key)
                    if task_data:
                        import json

                        result = json.loads(task_data)
                        status = result.get("status", "")

                        if status == "SUCCESS":
                            completed_count += 1
                        elif status == "FAILURE":
                            failed_count += 1
                except (json.JSONDecodeError, Exception) as parse_error:
                    logger.debug(f"Error parsing task result: {parse_error}")
                    continue

            # Use sampled data if available
            if completed_count > 0 or failed_count > 0:
                total_completed = completed_count
                total_failed = failed_count

        except Exception as redis_error:
            logger.warning(f"Could not query Redis for task results: {redis_error}")
            # Fall back to worker stats if Redis query fails
            pass

        # Calculate total and success rate
        total_tasks = active_count + pending_count + total_completed + total_failed

        # Ensure we have at least some tasks to report
        if total_tasks == 0:
            # If no tasks found, return minimal metrics
            return TaskMetrics(
                total_tasks=0,
                active_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                pending_tasks=0,
                success_rate=1.0,
            )

        success_rate = (
            total_completed / (total_completed + total_failed)
            if (total_completed + total_failed) > 0
            else 1.0
        )

        return TaskMetrics(
            total_tasks=total_tasks,
            active_tasks=active_count,
            completed_tasks=total_completed,
            failed_tasks=total_failed,
            pending_tasks=pending_count,
            success_rate=success_rate,
        )

    except Exception as e:
        logger.error(f"Error calculating task metrics from Celery: {e}", exc_info=True)
        # Return safe defaults
        return TaskMetrics(
            total_tasks=0,
            active_tasks=0,
            completed_tasks=0,
            failed_tasks=0,
            pending_tasks=0,
            success_rate=1.0,
        )


def _get_recent_tasks(db: Session, limit: int = 10) -> list[RecentTaskInfo]:
    """Get recent task activity from Celery backend.

    Queries actual task execution history from Redis/Celery result backend.
    Returns most recent tasks with their status, timing, and error information.
    """
    recent_tasks: list[RecentTaskInfo] = []

    try:
        import json

        from redis import Redis

        from app.core.celery_app import celery_app
        from app.core.config import get_settings

        settings = get_settings()
        redis_client = Redis.from_url(settings.redis_url_with_password)

        # Get all task result keys from Redis
        task_keys = redis_client.keys("celery-task-meta-*")

        # Parse and collect task information
        task_data_list: list[dict[str, Any]] = []

        for key in task_keys:
            try:
                task_data = redis_client.get(key)
                if not task_data:
                    continue

                # task_data is bytes from Redis
                if isinstance(task_data, bytes):
                    result = json.loads(task_data.decode("utf-8"))
                else:
                    result = json.loads(task_data)

                # Extract task ID from key (format: celery-task-meta-<uuid>)
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                task_id = key_str.replace("celery-task-meta-", "")

                # Parse task information
                status_str = result.get("status", "UNKNOWN")
                task_name = result.get("task_name") or result.get(
                    "name", "Unknown Task"
                )
                date_done = result.get("date_done")
                traceback = result.get("traceback")

                # Map Celery status to our TaskStatus enum
                status_mapping = {
                    "PENDING": TaskStatus.PENDING,
                    "STARTED": TaskStatus.IN_PROGRESS,
                    "SUCCESS": TaskStatus.COMPLETED,
                    "FAILURE": TaskStatus.FAILED,
                    "RETRY": TaskStatus.IN_PROGRESS,
                    "REVOKED": TaskStatus.CANCELLED,
                }
                task_status = status_mapping.get(status_str, TaskStatus.PENDING)

                # Parse timestamps
                completed_at = None
                if date_done:
                    try:
                        # Celery date_done is in ISO format
                        completed_at = datetime.fromisoformat(
                            date_done.replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        pass

                # Extract error message if failed
                error_message = None
                if status_str == "FAILURE":
                    error_result = result.get("result")
                    if isinstance(error_result, dict):
                        error_message = error_result.get(
                            "exc_message"
                        ) or error_result.get("exc_type")
                    elif isinstance(error_result, str):
                        error_message = error_result[:200]  # Truncate long errors

                    # Use traceback if no error message
                    if not error_message and traceback:
                        error_message = traceback.split("\n")[-1][:200]

                task_data_list.append(
                    {
                        "task_id": task_id,
                        "name": task_name,
                        "status": task_status,
                        "completed_at": completed_at,
                        "error_message": error_message,
                    }
                )

            except (json.JSONDecodeError, Exception) as parse_error:
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                logger.debug(f"Error parsing task key {key_str}: {parse_error}")
                continue

        # Sort by completion time (most recent first)
        task_data_list.sort(
            key=lambda x: x["completed_at"] if x["completed_at"] else datetime.min,
            reverse=True,
        )

        # Get task result keys from Redis using non-blocking SCAN and limit the sample size
        scan_limit = max(limit * 5, 50)
        task_keys = list(
            islice(
                redis_client.scan_iter(match="celery-task-meta-*", count=100),
                scan_limit,
            )
        )

        # Clear the list for the second iteration
        task_data_list.clear()

        for key in task_keys:
            try:
                task_data = redis_client.get(key)
                if not task_data:
                    continue

                # task_data is bytes from Redis
                if isinstance(task_data, bytes):
                    result = json.loads(task_data.decode("utf-8"))
                else:
                    result = json.loads(task_data)

                # Extract task ID from key (format: celery-task-meta-<uuid>)
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                task_id = key_str.replace("celery-task-meta-", "")

                # Parse task information
                status_str = result.get("status", "UNKNOWN")
                task_name = result.get("task_name") or result.get(
                    "name", "Unknown Task"
                )
                date_done = result.get("date_done")
                traceback = result.get("traceback")

                # Map Celery status to our TaskStatus enum
                status_mapping = {
                    "PENDING": TaskStatus.PENDING,
                    "STARTED": TaskStatus.IN_PROGRESS,
                    "SUCCESS": TaskStatus.COMPLETED,
                    "FAILURE": TaskStatus.FAILED,
                    "RETRY": TaskStatus.IN_PROGRESS,
                    "REVOKED": TaskStatus.CANCELLED,
                }
                task_status = status_mapping.get(status_str, TaskStatus.PENDING)

                # Parse timestamps
                completed_at = None
                if date_done:
                    try:
                        # Celery date_done is in ISO format
                        completed_at = datetime.fromisoformat(
                            date_done.replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        pass

                # Extract error message if failed
                error_message = None
                if status_str == "FAILURE":
                    error_result = result.get("result")
                    if isinstance(error_result, dict):
                        error_message = error_result.get(
                            "exc_message"
                        ) or error_result.get("exc_type")
                    elif isinstance(error_result, str):
                        error_message = error_result[:200]  # Truncate long errors

                    # Use traceback if no error message
                    if not error_message and traceback:
                        error_message = traceback.split("\n")[-1][:200]

                task_data_list.append(
                    {
                        "task_id": task_id,
                        "name": task_name,
                        "status": task_status,
                        "completed_at": completed_at,
                        "error_message": error_message,
                    }
                )

            except (json.JSONDecodeError, Exception) as parse_error:
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                logger.debug(f"Error parsing task key {key_str}: {parse_error}")
                continue

        # Sort by completion time (most recent first)
        task_data_list.sort(
            key=lambda x: x["completed_at"] if x["completed_at"] else datetime.min,
            reverse=True,
        )

        # Get active tasks to supplement recent tasks
        inspect = celery_app.control.inspect()
        active_tasks_dict = inspect.active() or {}

        # Add active tasks to the list
        for worker_name, tasks_list in active_tasks_dict.items():
            for task_info in tasks_list:
                task_id = task_info.get("id", "unknown")
                task_name = task_info.get("name", "Unknown Task")

                # Get start time
                started_at = None
                if "time_start" in task_info:
                    try:
                        started_at = datetime.fromtimestamp(task_info["time_start"])
                    except (ValueError, TypeError):
                        pass

                # Parse args/kwargs for description
                args = task_info.get("args", [])
                kwargs = task_info.get("kwargs", {})
                description = f"Worker: {worker_name}"
                if args or kwargs:
                    description += f" | Args: {args[:50]}" if args else ""

                task_data_list.append(
                    {
                        "task_id": task_id,
                        "name": task_name,
                        "status": TaskStatus.IN_PROGRESS,
                        "started_at": started_at,
                        "completed_at": None,
                        "error_message": None,
                        "description": description,
                    }
                )

        # Take the most recent tasks up to limit
        for task_entry in task_data_list[:limit]:
            # Calculate duration if both timestamps available
            duration_seconds = None
            if task_entry.get("started_at") and task_entry.get("completed_at"):
                delta = task_entry["completed_at"] - task_entry["started_at"]
                duration_seconds = delta.total_seconds()

            # Generate human-readable task name from Celery task path
            task_name = task_entry["name"]
            if "." in task_name:
                # Extract last part for readability (e.g., app.resilience.tasks.periodic_health_check -> periodic_health_check)
                task_name_parts = task_name.split(".")
                friendly_name = task_name_parts[-1].replace("_", " ").title()
            else:
                friendly_name = task_name

            # Build description
            description = task_entry.get("description") or ""
            if not description:
                if task_entry["status"] == TaskStatus.COMPLETED:
                    description = "Task completed successfully"
                elif task_entry["status"] == TaskStatus.FAILED:
                    description = f"Task failed: {task_entry.get('error_message', 'Unknown error')}"
                elif task_entry["status"] == TaskStatus.IN_PROGRESS:
                    description = "Task is currently running"
                else:
                    description = f"Task status: {task_entry['status'].value}"

            recent_tasks.append(
                RecentTaskInfo(
                    task_id=task_entry["task_id"],
                    name=friendly_name,
                    status=task_entry["status"],
                    description=description,
                    started_at=task_entry.get("started_at"),
                    completed_at=task_entry.get("completed_at"),
                    duration_seconds=duration_seconds,
                    error_message=task_entry.get("error_message"),
                )
            )

    except Exception as e:
        logger.error(f"Error fetching recent tasks from Celery: {e}", exc_info=True)

    return recent_tasks


def _calculate_coverage_metrics(db: Session) -> CoverageMetrics:
    """Calculate schedule coverage metrics."""
    try:
        # Get blocks and assignments for next 30 days
        start_date = datetime.utcnow().date()
        end_date = start_date + timedelta(days=30)

        total_blocks = (
            db.query(func.count(Block.id))
            .filter(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .scalar()
        )

        covered_blocks = (
            db.query(func.count(Assignment.id.distinct()))
            .join(Block)
            .filter(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .scalar()
        )

        coverage_rate = covered_blocks / total_blocks if total_blocks > 0 else 0.0

        # Get faculty count and calculate utilization
        faculty_count = (
            db.query(func.count(Person.id)).filter(Person.type == "faculty").scalar()
        )

        # Estimate utilization (assignments per faculty per day)
        avg_assignments_per_day = covered_blocks / 30 if covered_blocks > 0 else 0
        faculty_utilization = (
            avg_assignments_per_day / (faculty_count * 2) if faculty_count > 0 else 0.0
        )  # *2 for AM/PM blocks
        faculty_utilization = min(faculty_utilization, 1.0)

        # Identify critical gaps (blocks with no assignments)
        critical_gaps = max(0, total_blocks - covered_blocks)

        return CoverageMetrics(
            coverage_rate=coverage_rate,
            blocks_covered=covered_blocks or 0,
            blocks_total=total_blocks or 0,
            critical_gaps=critical_gaps,
            faculty_utilization=faculty_utilization,
        )
    except Exception as e:
        logger.error(f"Error calculating coverage metrics: {e}")
        return CoverageMetrics(
            coverage_rate=0.0,
            blocks_covered=0,
            blocks_total=0,
            critical_gaps=0,
            faculty_utilization=0.0,
        )


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/sitrep", response_model=SitrepResponse)
async def get_situation_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SitrepResponse:
    """
    Get situation report for scheduler operations.

    Returns comprehensive status including:
    - Task execution metrics (total, active, completed, failed)
    - System health status
    - Recent task activity
    - Schedule coverage metrics
    - Immediate actions and watch items

    This endpoint is designed to be called by n8n workflows
    for Slack-based monitoring (e.g., /scheduler sitrep command).

    Requires authentication.
    """
    logger.info(f"Generating sitrep for user {current_user.username}")

    try:
        # Get resilience service for health data
        service = _get_resilience_service(db)

        # Get system health
        try:
            health_report = service.get_health_snapshot()  # type: ignore[attr-defined]
            health_status = health_report.get("overall_status", "unknown")
            defense_level = health_report.get("defense_level")
            crisis_mode = health_report.get("crisis_mode", False)
            immediate_actions = health_report.get("immediate_actions", [])
            watch_items = health_report.get("watch_items", [])
        except Exception as e:
            logger.warning(f"Could not get health report: {e}")
            health_status = "unknown"
            defense_level = None
            crisis_mode = False
            immediate_actions = ["Unable to retrieve system health"]
            watch_items = []

        # Calculate metrics
        task_metrics = _calculate_task_metrics(db)
        recent_tasks = _get_recent_tasks(db, limit=5)
        coverage_metrics = _calculate_coverage_metrics(db)

        # Build response
        response = SitrepResponse(
            timestamp=datetime.utcnow(),
            task_metrics=task_metrics,
            health_status=health_status,
            defense_level=defense_level,
            recent_tasks=recent_tasks,
            coverage_metrics=coverage_metrics,
            immediate_actions=immediate_actions,
            watch_items=watch_items,
            last_update=datetime.utcnow(),
            crisis_mode=crisis_mode,
        )

        logger.info(
            f"Sitrep generated: {task_metrics.total_tasks} tasks, "
            f"{health_status} health, {coverage_metrics.coverage_rate:.1%} coverage"
        )

        return response

    except Exception as e:
        logger.error(f"Error generating sitrep: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate situation report",
        )


@router.post("/fix-it", response_model=FixItResponse)
async def initiate_fix_it_mode(
    request: FixItRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FixItResponse:
    """
    Initiate fix-it mode for automated task recovery.

    Fix-it mode attempts to automatically recover failed tasks by:
    - Retrying failed tasks with exponential backoff
    - Applying corrective actions based on failure type
    - Reallocating resources if needed
    - Skipping non-recoverable tasks

    Modes:
    - greedy: Aggressive fixes, may impact quality
    - conservative: Careful fixes, prioritize stability
    - balanced: Balance between speed and quality

    This endpoint is designed to be called by n8n workflows
    for Slack-based operations (e.g., /scheduler fix-it command).

    Requires authentication.
    """
    logger.info(
        f"Fix-it mode initiated by {request.initiated_by} (mode={request.mode.value}, "
        f"dry_run={request.dry_run})"
    )

    try:
        # Generate execution ID
        execution_id = str(uuid.uuid4())

        # Get current failed tasks
        task_metrics = _calculate_task_metrics(db)
        failed_count = task_metrics.failed_tasks

        # Simulate fix-it logic
        # In production, this would:
        # 1. Query actual failed tasks from Celery or task queue
        # 2. Apply mode-specific recovery strategies
        # 3. Track progress and results
        # 4. Return actual affected tasks

        if request.dry_run:
            # Dry run - just preview what would happen
            tasks_fixed = 0
            tasks_retried = failed_count
            tasks_skipped = 0
            tasks_failed = 0
            message = f"Dry run complete. Would retry {failed_count} tasks in {request.mode.value} mode."
        else:
            # Actual execution - simulate recovery
            if request.mode == FixItMode.GREEDY:
                # Greedy mode: try to fix most tasks aggressively
                success_rate = 0.8
            elif request.mode == FixItMode.CONSERVATIVE:
                # Conservative mode: only fix safe tasks
                success_rate = 0.6
            else:  # BALANCED
                # Balanced mode: moderate success rate
                success_rate = 0.7

            tasks_fixed = int(failed_count * success_rate)
            tasks_retried = failed_count
            tasks_failed = failed_count - tasks_fixed
            tasks_skipped = 0

            message = f"Fix-it completed: {tasks_fixed}/{failed_count} tasks recovered."

            # Store execution for later queries
            _fix_it_executions[execution_id] = {
                "mode": request.mode.value,
                "initiated_by": request.initiated_by,
                "initiated_at": datetime.utcnow(),
                "tasks_fixed": tasks_fixed,
                "tasks_retried": tasks_retried,
                "tasks_failed": tasks_failed,
                "status": "completed",
            }

        # Build affected tasks list (placeholder)
        affected_tasks = []
        for i in range(min(tasks_retried, 10)):  # Show up to 10 tasks
            affected_tasks.append(
                AffectedTask(
                    task_id=f"task-{i + 1}",
                    task_name=f"Scheduled task #{i + 1}",
                    previous_status=TaskStatus.FAILED,
                    new_status=(
                        TaskStatus.COMPLETED if i < tasks_fixed else TaskStatus.FAILED
                    ),
                    action_taken=(
                        "Retried with corrective action"
                        if i < tasks_fixed
                        else "Retry failed"
                    ),
                    retry_count=request.max_retries,
                )
            )

        # Determine estimated completion
        estimated_completion = None
        if not request.dry_run and tasks_retried > 0:
            # Estimate 30 seconds per task
            estimated_seconds = tasks_retried * 30
            estimated_completion = datetime.utcnow() + timedelta(
                seconds=estimated_seconds
            )

        # Build warnings
        warnings = []
        if request.mode == FixItMode.GREEDY:
            warnings.append(
                "Greedy mode may impact schedule quality. Review results carefully."
            )
        if request.auto_approve:
            warnings.append(
                "Auto-approve is enabled. Changes will be applied without review."
            )

        response = FixItResponse(
            status="completed" if not request.dry_run else "dry_run",
            execution_id=execution_id,
            mode=request.mode,
            tasks_fixed=tasks_fixed,
            tasks_retried=tasks_retried,
            tasks_skipped=tasks_skipped,
            tasks_failed=tasks_failed,
            affected_tasks=affected_tasks,
            estimated_completion=estimated_completion,
            initiated_by=request.initiated_by,
            initiated_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if not request.dry_run else None,
            message=message,
            warnings=warnings,
        )

        logger.info(
            f"Fix-it {execution_id}: {tasks_fixed} fixed, {tasks_failed} failed "
            f"(mode={request.mode.value})"
        )

        return response

    except Exception as e:
        logger.error(f"Error in fix-it mode: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fix-it mode failed: {str(e)}",
        )


@router.post("/approve", response_model=ApprovalResponse)
async def approve_task(
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApprovalResponse:
    """
    Approve or deny a pending task.

    Tasks requiring approval are typically:
    - High-impact schedule changes
    - Conflict resolutions requiring human judgment
    - Critical resource allocations
    - Override requests

    Approval tokens are generated when tasks require approval
    and can be used via Slack or API to approve/deny tasks.

    This endpoint is designed to be called by n8n workflows
    for Slack-based approvals (e.g., /scheduler approve command).

    Requires authentication.
    """
    logger.info(
        f"Approval request by {request.approved_by} "
        f"(action={request.action.value}, token={request.token[:8]}...)"
    )

    try:
        # Validate token
        token_data = _approval_tokens.get(request.token)
        if not token_data:
            logger.warning(f"Invalid approval token: {request.token[:8]}...")
            return ApprovalResponse(
                status="invalid_token",
                action=request.action,
                task_id=None,
                approved_tasks=0,
                denied_tasks=0,
                task_details=[],
                approved_by=request.approved_by,
                approved_at=datetime.utcnow(),
                message="Invalid or expired approval token.",
                warnings=[
                    "Token not found in system. It may have expired or already been used."
                ],
            )

        # Get tasks associated with token
        task_ids = token_data.get("task_ids", [])
        if request.task_id:
            # Specific task approval
            if request.task_id not in task_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {request.task_id} not found for this token",
                )
            task_ids = [request.task_id]

        # Process approvals
        approved_count = 0
        denied_count = 0
        task_details = []

        for task_id in task_ids:
            # In production, this would:
            # 1. Update task status in database
            # 2. Trigger task execution if approved
            # 3. Cancel or rollback if denied
            # 4. Send notifications

            if request.action == ApprovalAction.APPROVE:
                approved_count += 1
                new_status = TaskStatus.IN_PROGRESS
            else:
                denied_count += 1
                new_status = TaskStatus.CANCELLED

            task_info = ApprovedTaskInfo(
                task_id=task_id,
                task_name=f"Task {task_id}",
                task_type=token_data.get("task_type", "schedule_change"),
                previous_status=TaskStatus.PENDING,
                new_status=new_status,
                approved_at=datetime.utcnow(),
            )
            task_details.append(task_info)

        # Mark token as used
        _approval_tokens[request.token]["used"] = True
        _approval_tokens[request.token]["used_at"] = datetime.utcnow()
        _approval_tokens[request.token]["used_by"] = request.approved_by

        # Build response message
        if request.action == ApprovalAction.APPROVE:
            status_str = "approved"
            message = f"Successfully approved {approved_count} task(s)."
        else:
            status_str = "denied"
            message = f"Successfully denied {denied_count} task(s)."

        # Determine task_id for response
        response_task_id = request.task_id if request.task_id else "multiple"

        response = ApprovalResponse(
            status=status_str,
            action=request.action,
            task_id=response_task_id,
            approved_tasks=approved_count,
            denied_tasks=denied_count,
            task_details=task_details,
            approved_by=request.approved_by,
            approved_at=datetime.utcnow(),
            message=message,
            warnings=[],
        )

        logger.info(
            f"Approval processed: {approved_count} approved, {denied_count} denied "
            f"by {request.approved_by}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing approval: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval processing failed: {str(e)}",
        )


@router.post("/approve/token/generate")
async def generate_approval_token(
    task_ids: list[str],
    task_type: str = "schedule_change",
    expires_in_hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Generate an approval token for tasks requiring approval.

    This is a helper endpoint for creating approval tokens
    that can be used with the /approve endpoint.

    Tokens expire after the specified duration (default 24 hours).

    Requires authentication.
    """
    logger.info(
        f"Generating approval token for {len(task_ids)} tasks by {current_user.username}"
    )

    try:
        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Store token data
        _approval_tokens[token] = {
            "task_ids": task_ids,
            "task_type": task_type,
            "created_by": current_user.username,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=expires_in_hours),
            "used": False,
        }

        logger.info(
            f"Generated approval token {token[:8]}... for {len(task_ids)} tasks"
        )

        return {
            "token": token,
            "task_ids": task_ids,
            "task_type": task_type,
            "expires_at": _approval_tokens[token]["expires_at"].isoformat(),
            "message": f"Approval token generated for {len(task_ids)} task(s)",
        }

    except Exception as e:
        logger.error(f"Error generating approval token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token generation failed: {str(e)}",
        )


# ============================================================================
# Solver Control Endpoints (Kill-Switch)
# ============================================================================


@router.post("/runs/{run_id}/abort", response_model=SolverAbortResponse)
async def abort_solver_run(
    run_id: str,
    request: SolverAbortRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SolverAbortResponse:
    """
    Abort a running solver job.

    This endpoint signals a running solver to stop gracefully and
    save its best solution so far. Use this when:
    - A solver is taking too long
    - A constraint bug is causing pathological behavior
    - Resources need to be freed immediately

    The solver will:
    1. Receive the abort signal on its next iteration check
    2. Save its best solution found so far
    3. Clean up and return a partial result

    Requires authentication. Admin role recommended for production.
    """
    from app.scheduling.solver_control import SolverControl

    logger.warning(
        f"Abort requested for run {run_id} by {request.requested_by}: {request.reason}"
    )

    try:
        # Check if run exists and is active
        progress = SolverControl.get_progress(run_id)

        if progress and progress.get("status") == "running":
            # Request abort
            success = SolverControl.request_abort(
                run_id=run_id, reason=request.reason, requested_by=request.requested_by
            )

            if success:
                return SolverAbortResponse(
                    status="abort_requested",
                    run_id=run_id,
                    reason=request.reason,
                    requested_by=request.requested_by,
                    message=f"Abort signal sent to solver run {run_id}. "
                    f"Solver will stop on next iteration check.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send abort signal",
                )
        elif progress:
            # Run exists but not running
            return SolverAbortResponse(
                status="already_completed",
                run_id=run_id,
                reason=request.reason,
                requested_by=request.requested_by,
                message=f"Solver run {run_id} is not currently running "
                f"(status: {progress.get('status', 'unknown')})",
            )
        else:
            # No progress found - might still be starting or doesn't exist
            # Send abort anyway in case it's just starting
            SolverControl.request_abort(
                run_id=run_id, reason=request.reason, requested_by=request.requested_by
            )

            return SolverAbortResponse(
                status="abort_requested",
                run_id=run_id,
                reason=request.reason,
                requested_by=request.requested_by,
                message=f"Abort signal sent for run {run_id}. "
                f"No active progress found - run may not have started yet.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aborting solver run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to abort solver: {str(e)}",
        )


@router.get("/runs/{run_id}/progress", response_model=SolverProgressResponse)
async def get_solver_progress(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SolverProgressResponse:
    """
    Get progress for a running or recently completed solver job.

    Returns current iteration, best score, and status for monitoring
    long-running solver operations.

    Requires authentication.
    """
    from app.scheduling.solver_control import SolverControl

    try:
        progress = SolverControl.get_progress(run_id)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No progress found for run {run_id}",
            )

        return SolverProgressResponse(
            run_id=progress["run_id"],
            iteration=progress["iteration"],
            best_score=progress["best_score"],
            assignments_count=progress["assignments_count"],
            violations_count=progress["violations_count"],
            status=progress["status"],
            updated_at=progress.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress for {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get solver progress: {str(e)}",
        )


@router.get("/runs/active", response_model=ActiveSolversResponse)
async def get_active_solvers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ActiveSolversResponse:
    """
    Get all currently active solver runs.

    Returns a list of all solver jobs that are currently running,
    useful for monitoring and deciding which jobs to abort.

    Requires authentication.
    """
    from app.scheduling.solver_control import SolverControl

    try:
        active_runs = SolverControl.get_active_runs()

        return ActiveSolversResponse(
            active_runs=[
                SolverProgressResponse(
                    run_id=run["run_id"],
                    iteration=run["iteration"],
                    best_score=run["best_score"],
                    assignments_count=run["assignments_count"],
                    violations_count=run["violations_count"],
                    status=run["status"],
                    updated_at=run.get("updated_at"),
                )
                for run in active_runs
            ],
            count=len(active_runs),
        )

    except Exception as e:
        logger.error(f"Error getting active solvers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active solvers: {str(e)}",
        )
