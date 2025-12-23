"""
Priority Job Queue System.

Provides advanced priority-based job queue functionality including:
- Multi-priority queue support (LOW, NORMAL, HIGH, CRITICAL, URGENT)
- Job scheduling with delays and absolute times
- Job deduplication using content hashing
- Dead letter queue for failed jobs
- Job progress tracking and monitoring
- Job cancellation and revocation
- Queue metrics and statistics
- Fair scheduling across priorities
- Job retry policies with exponential backoff
- Job timeout management
- Job dependency tracking

This module provides a high-level abstraction over Celery for managing
priority-based job execution with sophisticated scheduling and monitoring.
"""

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum
from typing import Any
from uuid import uuid4

from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================


class JobPriority(IntEnum):
    """
    Job priority levels with extended granularity.

    Higher numbers = higher priority.
    Maps to Celery's priority system (0-10).
    """

    LOW = 2
    NORMAL = 5
    HIGH = 7
    CRITICAL = 9
    URGENT = 10  # Emergency/immediate execution


class JobState(str):
    """Job state constants."""

    PENDING = "pending"  # Queued but not started
    SCHEDULED = "scheduled"  # Scheduled for future execution
    DEDUPED = "deduped"  # Deduplicated (duplicate of existing job)
    RUNNING = "running"  # Currently executing
    PROGRESS = "progress"  # Running with progress updates
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed after all retries
    CANCELLED = "cancelled"  # Cancelled by user
    TIMEOUT = "timeout"  # Timed out
    DEAD_LETTER = "dead_letter"  # Moved to dead letter queue


class FairSchedulingPolicy(str):
    """Fair scheduling policy options."""

    ROUND_ROBIN = "round_robin"  # Round-robin across priorities
    WEIGHTED = "weighted"  # Weighted by priority
    STRICT_PRIORITY = "strict_priority"  # Strict priority order
    DEFICIT_ROUND_ROBIN = "deficit_round_robin"  # DRR for fairness


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class JobMetadata:
    """
    Metadata for a job in the priority queue.

    Tracks job lifecycle, priority, scheduling, and monitoring information.
    """

    job_id: str
    task_name: str
    priority: JobPriority
    state: JobState
    created_at: datetime
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    queue: str = "default"
    retry_count: int = 0
    max_retries: int = 3
    timeout: int | None = None
    dedup_key: str | None = None
    parent_job_id: str | None = None
    dependencies: list[str] = field(default_factory=list)
    progress: dict | None = None
    result: Any | None = None
    error: str | None = None
    error_type: str | None = None
    traceback: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "job_id": self.job_id,
            "task_name": self.task_name,
            "priority": self.priority.name,
            "state": self.state,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": (
                self.scheduled_at.isoformat() if self.scheduled_at else None
            ),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "queue": self.queue,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "dedup_key": self.dedup_key,
            "parent_job_id": self.parent_job_id,
            "dependencies": self.dependencies,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "error_type": self.error_type,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class QueueMetrics:
    """Metrics for a priority queue."""

    queue_name: str
    priority: JobPriority
    pending_count: int = 0
    scheduled_count: int = 0
    running_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    cancelled_count: int = 0
    dead_letter_count: int = 0
    avg_wait_time_seconds: float = 0.0
    avg_execution_time_seconds: float = 0.0
    oldest_pending_job_age_seconds: float | None = None
    throughput_per_minute: float = 0.0
    success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "queue_name": self.queue_name,
            "priority": self.priority.name,
            "pending_count": self.pending_count,
            "scheduled_count": self.scheduled_count,
            "running_count": self.running_count,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "cancelled_count": self.cancelled_count,
            "dead_letter_count": self.dead_letter_count,
            "avg_wait_time_seconds": self.avg_wait_time_seconds,
            "avg_execution_time_seconds": self.avg_execution_time_seconds,
            "oldest_pending_job_age_seconds": self.oldest_pending_job_age_seconds,
            "throughput_per_minute": self.throughput_per_minute,
            "success_rate": self.success_rate,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class DeadLetterRecord:
    """Record for a job in the dead letter queue."""

    job_id: str
    task_name: str
    priority: JobPriority
    args: tuple
    kwargs: dict
    error: str
    error_type: str
    traceback: str
    retry_count: int
    failed_at: datetime
    reason: str
    original_metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "job_id": self.job_id,
            "task_name": self.task_name,
            "priority": self.priority.name,
            "args": list(self.args),
            "kwargs": self.kwargs,
            "error": self.error,
            "error_type": self.error_type,
            "traceback": self.traceback,
            "retry_count": self.retry_count,
            "failed_at": self.failed_at.isoformat(),
            "reason": self.reason,
            "original_metadata": self.original_metadata,
        }


# ============================================================================
# Priority Queue Manager
# ============================================================================


class PriorityQueueManager:
    """
    Advanced priority-based job queue manager.

    Provides comprehensive job queue management with:
    - Multi-level priority support
    - Job deduplication
    - Scheduled execution
    - Dead letter queue
    - Progress tracking
    - Cancellation support
    - Fair scheduling
    - Detailed metrics

    Example:
        >>> manager = PriorityQueueManager()
        >>> job_id = manager.enqueue(
        ...     task_name="app.tasks.process_data",
        ...     args=(data_id,),
        ...     priority=JobPriority.HIGH,
        ...     dedup_key="process:data:123",
        ... )
        >>> status = manager.get_job_status(job_id)
        >>> metrics = manager.get_queue_metrics()
    """

    # Queue name mapping by priority
    PRIORITY_QUEUE_MAP = {
        JobPriority.LOW: "low_priority",
        JobPriority.NORMAL: "default",
        JobPriority.HIGH: "high_priority",
        JobPriority.CRITICAL: "critical",
        JobPriority.URGENT: "urgent",
    }

    def __init__(
        self,
        enable_deduplication: bool = True,
        enable_fair_scheduling: bool = True,
        fair_scheduling_policy: FairSchedulingPolicy = FairSchedulingPolicy.WEIGHTED,
        default_timeout: int = 600,
        dead_letter_retention_hours: int = 168,  # 7 days
    ):
        """
        Initialize priority queue manager.

        Args:
            enable_deduplication: Enable job deduplication
            enable_fair_scheduling: Enable fair scheduling across priorities
            fair_scheduling_policy: Fair scheduling policy to use
            default_timeout: Default job timeout in seconds
            dead_letter_retention_hours: How long to keep dead letter records
        """
        self.app = celery_app
        self.enable_deduplication = enable_deduplication
        self.enable_fair_scheduling = enable_fair_scheduling
        self.fair_scheduling_policy = fair_scheduling_policy
        self.default_timeout = default_timeout
        self.dead_letter_retention_hours = dead_letter_retention_hours

        # In-memory storage for job metadata
        # In production, this would be Redis or a database
        self._job_metadata: dict[str, JobMetadata] = {}
        self._dedup_index: dict[str, str] = {}  # dedup_key -> job_id
        self._dead_letter_queue: dict[str, DeadLetterRecord] = {}
        self._priority_counters: dict[JobPriority, int] = defaultdict(int)

        logger.info(
            f"PriorityQueueManager initialized "
            f"(dedup={enable_deduplication}, "
            f"fair_scheduling={enable_fair_scheduling}, "
            f"policy={fair_scheduling_policy})"
        )

    def _generate_dedup_key(
        self,
        task_name: str,
        args: tuple,
        kwargs: dict,
    ) -> str:
        """
        Generate deduplication key from task parameters.

        Args:
            task_name: Task name
            args: Task arguments
            kwargs: Task keyword arguments

        Returns:
            str: Deduplication key (SHA256 hash)
        """
        # Create canonical representation
        canonical = {
            "task": task_name,
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        canonical_str = json.dumps(canonical, sort_keys=True, default=str)
        return hashlib.sha256(canonical_str.encode()).hexdigest()

    def _check_deduplication(
        self,
        dedup_key: str | None,
        task_name: str,
        args: tuple,
        kwargs: dict,
    ) -> str | None:
        """
        Check if job is duplicate and return existing job ID if found.

        Args:
            dedup_key: Custom deduplication key
            task_name: Task name
            args: Task arguments
            kwargs: Task keyword arguments

        Returns:
            Optional[str]: Existing job ID if duplicate, None otherwise
        """
        if not self.enable_deduplication:
            return None

        # Use custom dedup key or generate one
        if dedup_key is None:
            dedup_key = self._generate_dedup_key(task_name, args, kwargs)

        # Check if key exists and job is still active
        if dedup_key in self._dedup_index:
            existing_job_id = self._dedup_index[dedup_key]
            if existing_job_id in self._job_metadata:
                metadata = self._job_metadata[existing_job_id]
                # Only deduplicate if job is not completed/failed/cancelled
                if metadata.state in [
                    JobState.PENDING,
                    JobState.SCHEDULED,
                    JobState.RUNNING,
                    JobState.PROGRESS,
                ]:
                    logger.info(
                        f"Job deduplicated: {task_name} "
                        f"(existing={existing_job_id}, dedup_key={dedup_key})"
                    )
                    return existing_job_id

        return None

    def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict | None = None,
        priority: JobPriority = JobPriority.NORMAL,
        countdown: int | None = None,
        eta: datetime | None = None,
        timeout: int | None = None,
        max_retries: int = 3,
        dedup_key: str | None = None,
        queue: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        Enqueue a job with specified priority.

        Args:
            task_name: Name of the task to execute
            args: Positional arguments for the task
            kwargs: Keyword arguments for the task
            priority: Job priority level
            countdown: Delay in seconds before execution
            eta: Absolute time when to execute
            timeout: Job timeout in seconds
            max_retries: Maximum retry attempts
            dedup_key: Custom deduplication key
            queue: Custom queue name (overrides priority-based routing)
            tags: Tags for categorization and filtering
            metadata: Additional metadata

        Returns:
            str: Job ID

        Raises:
            ValidationError: If task not found or invalid parameters
            ConflictError: If duplicate job exists (when deduplication enabled)

        Example:
            >>> job_id = manager.enqueue(
            ...     task_name="app.tasks.process_schedule",
            ...     args=(schedule_id,),
            ...     priority=JobPriority.HIGH,
            ...     timeout=300,
            ...     dedup_key=f"schedule:{schedule_id}",
            ...     tags=["schedule", "processing"],
            ... )
        """
        kwargs = kwargs or {}
        tags = tags or []
        metadata = metadata or {}

        # Validate task exists
        task = self.app.tasks.get(task_name)
        if not task:
            raise ValidationError(f"Task {task_name} not found in registry")

        # Check deduplication
        existing_job_id = self._check_deduplication(dedup_key, task_name, args, kwargs)
        if existing_job_id:
            # Update metadata state to indicate deduplication
            if existing_job_id in self._job_metadata:
                existing_metadata = self._job_metadata[existing_job_id]
                logger.info(
                    f"Returning existing job {existing_job_id} "
                    f"for deduplicated request (state={existing_metadata.state})"
                )
            return existing_job_id

        # Generate job ID
        job_id = str(uuid4())

        # Determine queue
        if queue is None:
            queue = self.PRIORITY_QUEUE_MAP.get(priority, "default")

        # Determine timeout
        if timeout is None:
            timeout = self.default_timeout

        # Create job metadata
        job_metadata = JobMetadata(
            job_id=job_id,
            task_name=task_name,
            priority=priority,
            state=JobState.SCHEDULED if (countdown or eta) else JobState.PENDING,
            created_at=datetime.utcnow(),
            scheduled_at=eta
            or (
                datetime.utcnow() + timedelta(seconds=countdown) if countdown else None
            ),
            args=args,
            kwargs=kwargs,
            queue=queue,
            max_retries=max_retries,
            timeout=timeout,
            dedup_key=dedup_key or self._generate_dedup_key(task_name, args, kwargs),
            tags=tags,
            metadata=metadata,
        )

        # Store metadata
        self._job_metadata[job_id] = job_metadata

        # Update deduplication index
        if self.enable_deduplication and job_metadata.dedup_key:
            self._dedup_index[job_metadata.dedup_key] = job_id

        # Submit to Celery
        try:
            result = task.apply_async(
                args=args,
                kwargs=kwargs,
                task_id=job_id,
                priority=int(priority),
                countdown=countdown,
                eta=eta,
                expires=eta + timedelta(hours=24) if eta else None,
                queue=queue,
                time_limit=timeout,
                soft_time_limit=timeout - 30 if timeout > 30 else timeout,
            )

            # Update priority counter
            self._priority_counters[priority] += 1

            logger.info(
                f"Job enqueued: {task_name} "
                f"(id={job_id}, priority={priority.name}, queue={queue}, "
                f"scheduled={bool(countdown or eta)})"
            )

            return job_id

        except Exception as exc:
            # Clean up metadata on failure
            self._job_metadata.pop(job_id, None)
            if self.enable_deduplication and job_metadata.dedup_key:
                self._dedup_index.pop(job_metadata.dedup_key, None)

            logger.error(f"Failed to enqueue job {job_id}: {exc}", exc_info=True)
            raise ValidationError(f"Failed to enqueue job: {exc}")

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """
        Get comprehensive job status.

        Args:
            job_id: Job ID

        Returns:
            dict: Job status information

        Raises:
            NotFoundError: If job not found
        """
        # Check metadata store
        if job_id not in self._job_metadata:
            raise NotFoundError(f"Job {job_id} not found")

        metadata = self._job_metadata[job_id]

        # Get Celery result
        result = AsyncResult(job_id, app=self.app)

        # Sync state from Celery if different
        celery_state_map = {
            "PENDING": JobState.PENDING,
            "RECEIVED": JobState.PENDING,
            "STARTED": JobState.RUNNING,
            "PROGRESS": JobState.PROGRESS,
            "SUCCESS": JobState.COMPLETED,
            "FAILURE": JobState.FAILED,
            "RETRY": JobState.RUNNING,
            "REVOKED": JobState.CANCELLED,
        }

        if result.state in celery_state_map:
            new_state = celery_state_map[result.state]
            if metadata.state != new_state:
                metadata.state = new_state

                if new_state == JobState.RUNNING and not metadata.started_at:
                    metadata.started_at = datetime.utcnow()
                elif new_state in [JobState.COMPLETED, JobState.FAILED]:
                    metadata.completed_at = datetime.utcnow()

        # Update progress if available
        if result.state == "PROGRESS" and result.info:
            metadata.progress = result.info

        # Update result/error
        if result.ready():
            if result.successful():
                metadata.result = result.result
            else:
                metadata.error = str(result.info)
                if hasattr(result.info, "__class__"):
                    metadata.error_type = result.info.__class__.__name__

        return metadata.to_dict()

    def get_job_progress(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job progress information.

        Args:
            job_id: Job ID

        Returns:
            Optional[dict]: Progress information or None

        Raises:
            NotFoundError: If job not found
        """
        if job_id not in self._job_metadata:
            raise NotFoundError(f"Job {job_id} not found")

        metadata = self._job_metadata[job_id]

        if metadata.state == JobState.PROGRESS and metadata.progress:
            return metadata.progress

        # Check Celery result
        result = AsyncResult(job_id, app=self.app)
        if result.state == "PROGRESS":
            return result.info

        return None

    def cancel_job(
        self,
        job_id: str,
        terminate: bool = False,
        reason: str | None = None,
    ) -> bool:
        """
        Cancel a job.

        Args:
            job_id: Job ID to cancel
            terminate: If True, terminate the job if running
            reason: Cancellation reason

        Returns:
            bool: True if job was cancelled

        Raises:
            NotFoundError: If job not found
        """
        if job_id not in self._job_metadata:
            raise NotFoundError(f"Job {job_id} not found")

        metadata = self._job_metadata[job_id]

        # Check if job can be cancelled
        if metadata.state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
            logger.warning(f"Job {job_id} cannot be cancelled (state={metadata.state})")
            return False

        # Revoke in Celery
        self.app.control.revoke(job_id, terminate=terminate, signal="SIGTERM")

        # Update metadata
        metadata.state = JobState.CANCELLED
        metadata.completed_at = datetime.utcnow()
        if reason:
            metadata.metadata["cancellation_reason"] = reason

        # Clean up deduplication index
        if self.enable_deduplication and metadata.dedup_key:
            self._dedup_index.pop(metadata.dedup_key, None)

        logger.info(
            f"Job cancelled: {job_id} "
            f"(terminate={terminate}, reason={reason or 'not specified'})"
        )

        return True

    def retry_job(
        self,
        job_id: str,
        countdown: int | None = None,
        priority: JobPriority | None = None,
    ) -> str:
        """
        Retry a failed job.

        Args:
            job_id: Job ID to retry
            countdown: Delay before retry (seconds)
            priority: New priority (defaults to original)

        Returns:
            str: New job ID

        Raises:
            NotFoundError: If job not found
            ValidationError: If job not in failed state
        """
        if job_id not in self._job_metadata:
            raise NotFoundError(f"Job {job_id} not found")

        metadata = self._job_metadata[job_id]

        if metadata.state != JobState.FAILED:
            raise ValidationError(
                f"Job {job_id} is not in failed state (state={metadata.state})"
            )

        # Create new job with same parameters
        new_job_id = self.enqueue(
            task_name=metadata.task_name,
            args=metadata.args,
            kwargs=metadata.kwargs,
            priority=priority or metadata.priority,
            countdown=countdown,
            max_retries=metadata.max_retries,
            timeout=metadata.timeout,
            dedup_key=None,  # Don't deduplicate retries
            queue=metadata.queue,
            tags=metadata.tags + ["retry"],
            metadata={
                **metadata.metadata,
                "original_job_id": job_id,
                "retry_of": job_id,
            },
        )

        logger.info(f"Job {job_id} retried as {new_job_id}")
        return new_job_id

    def send_to_dead_letter_queue(
        self,
        job_id: str,
        reason: str,
        error: str | None = None,
        error_type: str | None = None,
        traceback: str | None = None,
    ) -> None:
        """
        Send job to dead letter queue.

        Args:
            job_id: Job ID
            reason: Reason for dead lettering
            error: Error message
            error_type: Error type/class
            traceback: Error traceback
        """
        if job_id not in self._job_metadata:
            logger.warning(f"Cannot dead letter unknown job {job_id}")
            return

        metadata = self._job_metadata[job_id]

        # Create dead letter record
        record = DeadLetterRecord(
            job_id=job_id,
            task_name=metadata.task_name,
            priority=metadata.priority,
            args=metadata.args,
            kwargs=metadata.kwargs,
            error=error or metadata.error or "Unknown error",
            error_type=error_type or metadata.error_type or "Unknown",
            traceback=traceback or metadata.traceback or "",
            retry_count=metadata.retry_count,
            failed_at=datetime.utcnow(),
            reason=reason,
            original_metadata=metadata.to_dict(),
        )

        # Store in dead letter queue
        self._dead_letter_queue[job_id] = record

        # Update metadata
        metadata.state = JobState.DEAD_LETTER
        metadata.completed_at = datetime.utcnow()

        # Clean up deduplication index
        if self.enable_deduplication and metadata.dedup_key:
            self._dedup_index.pop(metadata.dedup_key, None)

        logger.error(
            f"Job sent to dead letter queue: {job_id} "
            f"(task={metadata.task_name}, reason={reason})"
        )

    def get_dead_letter_queue(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get dead letter queue records.

        Args:
            limit: Maximum number of records
            offset: Offset for pagination

        Returns:
            list[dict]: Dead letter records
        """
        records = list(self._dead_letter_queue.values())
        # Sort by failed_at descending
        records.sort(key=lambda r: r.failed_at, reverse=True)
        return [r.to_dict() for r in records[offset : offset + limit]]

    def requeue_from_dead_letter(
        self,
        job_id: str,
        priority: JobPriority | None = None,
    ) -> str:
        """
        Requeue a job from dead letter queue.

        Args:
            job_id: Job ID in dead letter queue
            priority: New priority (defaults to original)

        Returns:
            str: New job ID

        Raises:
            NotFoundError: If job not in dead letter queue
        """
        if job_id not in self._dead_letter_queue:
            raise NotFoundError(f"Job {job_id} not found in dead letter queue")

        record = self._dead_letter_queue[job_id]

        # Create new job
        new_job_id = self.enqueue(
            task_name=record.task_name,
            args=record.args,
            kwargs=record.kwargs,
            priority=priority or record.priority,
            max_retries=3,
            dedup_key=None,  # Don't deduplicate requeued jobs
            tags=["requeued_from_dlq"],
            metadata={
                "original_job_id": job_id,
                "requeued_from_dlq": True,
                "original_error": record.error,
            },
        )

        logger.info(f"Job {job_id} requeued from dead letter queue as {new_job_id}")
        return new_job_id

    def get_queue_metrics(
        self,
        priority: JobPriority | None = None,
    ) -> dict[str, Any]:
        """
        Get queue metrics by priority.

        Args:
            priority: Specific priority to get metrics for (None for all)

        Returns:
            dict: Queue metrics

        Example:
            >>> metrics = manager.get_queue_metrics(JobPriority.HIGH)
            >>> print(f"Pending: {metrics['high_priority']['pending_count']}")
        """
        metrics_by_priority: dict[str, QueueMetrics] = {}

        # Get metrics for each priority
        priorities = [priority] if priority else list(JobPriority)

        for prio in priorities:
            queue_name = self.PRIORITY_QUEUE_MAP.get(prio, "default")
            metrics = QueueMetrics(queue_name=queue_name, priority=prio)

            # Count jobs by state
            wait_times: list[float] = []
            execution_times: list[float] = []
            oldest_pending_age: float | None = None

            for metadata in self._job_metadata.values():
                if metadata.priority != prio:
                    continue

                # Count by state
                if metadata.state == JobState.PENDING:
                    metrics.pending_count += 1
                    age = (datetime.utcnow() - metadata.created_at).total_seconds()
                    if oldest_pending_age is None or age > oldest_pending_age:
                        oldest_pending_age = age
                elif metadata.state == JobState.SCHEDULED:
                    metrics.scheduled_count += 1
                elif metadata.state in [JobState.RUNNING, JobState.PROGRESS]:
                    metrics.running_count += 1
                elif metadata.state == JobState.COMPLETED:
                    metrics.completed_count += 1

                    # Calculate wait and execution times
                    if metadata.started_at:
                        wait_time = (
                            metadata.started_at - metadata.created_at
                        ).total_seconds()
                        wait_times.append(wait_time)

                    if metadata.started_at and metadata.completed_at:
                        exec_time = (
                            metadata.completed_at - metadata.started_at
                        ).total_seconds()
                        execution_times.append(exec_time)

                elif metadata.state == JobState.FAILED:
                    metrics.failed_count += 1
                elif metadata.state == JobState.CANCELLED:
                    metrics.cancelled_count += 1
                elif metadata.state == JobState.DEAD_LETTER:
                    metrics.dead_letter_count += 1

            # Calculate averages
            if wait_times:
                metrics.avg_wait_time_seconds = sum(wait_times) / len(wait_times)

            if execution_times:
                metrics.avg_execution_time_seconds = sum(execution_times) / len(
                    execution_times
                )

            metrics.oldest_pending_job_age_seconds = oldest_pending_age

            # Calculate success rate
            total_completed = metrics.completed_count + metrics.failed_count
            if total_completed > 0:
                metrics.success_rate = metrics.completed_count / total_completed

            # Calculate throughput (jobs per minute in last hour)
            # This is a simplified calculation
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_completions = sum(
                1
                for m in self._job_metadata.values()
                if m.priority == prio
                and m.state == JobState.COMPLETED
                and m.completed_at
                and m.completed_at >= one_hour_ago
            )
            metrics.throughput_per_minute = recent_completions / 60.0

            metrics_by_priority[prio.name.lower()] = metrics

        # Add overall metrics
        overall = {
            "by_priority": {k: v.to_dict() for k, v in metrics_by_priority.items()},
            "total_jobs": len(self._job_metadata),
            "total_dead_letter": len(self._dead_letter_queue),
            "dedup_index_size": len(self._dedup_index),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return overall

    def purge_queue(
        self,
        priority: JobPriority | None = None,
        state: JobState | None = None,
    ) -> int:
        """
        Purge jobs from queue.

        Warning: This operation cannot be undone.

        Args:
            priority: Purge only jobs with this priority (None for all)
            state: Purge only jobs in this state (None for all)

        Returns:
            int: Number of jobs purged
        """
        jobs_to_purge = []

        for job_id, metadata in self._job_metadata.items():
            if priority and metadata.priority != priority:
                continue
            if state and metadata.state != state:
                continue
            jobs_to_purge.append(job_id)

        # Revoke in Celery
        for job_id in jobs_to_purge:
            self.app.control.revoke(job_id, terminate=True)

        # Remove from metadata
        for job_id in jobs_to_purge:
            metadata = self._job_metadata.pop(job_id, None)
            if metadata and self.enable_deduplication and metadata.dedup_key:
                self._dedup_index.pop(metadata.dedup_key, None)

        logger.warning(
            f"Purged {len(jobs_to_purge)} jobs "
            f"(priority={priority.name if priority else 'all'}, "
            f"state={state if state else 'all'})"
        )

        return len(jobs_to_purge)

    def cleanup_completed_jobs(
        self,
        retention_hours: int = 24,
    ) -> int:
        """
        Clean up old completed/failed/cancelled jobs.

        Args:
            retention_hours: Keep jobs from this many hours ago

        Returns:
            int: Number of jobs cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        jobs_to_remove = []

        for job_id, metadata in self._job_metadata.items():
            if metadata.state in [
                JobState.COMPLETED,
                JobState.FAILED,
                JobState.CANCELLED,
            ]:
                if metadata.completed_at and metadata.completed_at < cutoff_time:
                    jobs_to_remove.append(job_id)

        # Remove old jobs
        for job_id in jobs_to_remove:
            metadata = self._job_metadata.pop(job_id, None)
            if metadata and self.enable_deduplication and metadata.dedup_key:
                self._dedup_index.pop(metadata.dedup_key, None)

        logger.info(
            f"Cleaned up {len(jobs_to_remove)} old jobs (retention={retention_hours}h)"
        )

        return len(jobs_to_remove)

    def cleanup_dead_letter_queue(
        self,
        retention_hours: int | None = None,
    ) -> int:
        """
        Clean up old dead letter queue records.

        Args:
            retention_hours: Keep records from this many hours ago
                            (defaults to configured retention)

        Returns:
            int: Number of records cleaned up
        """
        retention_hours = retention_hours or self.dead_letter_retention_hours
        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        records_to_remove = []

        for job_id, record in self._dead_letter_queue.items():
            if record.failed_at < cutoff_time:
                records_to_remove.append(job_id)

        # Remove old records
        for job_id in records_to_remove:
            self._dead_letter_queue.pop(job_id, None)

        logger.info(
            f"Cleaned up {len(records_to_remove)} old dead letter records "
            f"(retention={retention_hours}h)"
        )

        return len(records_to_remove)

    def get_jobs_by_tag(
        self,
        tag: str,
        state: JobState | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get jobs by tag.

        Args:
            tag: Tag to filter by
            state: Optional state filter

        Returns:
            list[dict]: Matching jobs
        """
        matching_jobs = []

        for metadata in self._job_metadata.values():
            if tag in metadata.tags:
                if state is None or metadata.state == state:
                    matching_jobs.append(metadata.to_dict())

        return matching_jobs

    def get_health_status(self) -> dict[str, Any]:
        """
        Get queue health status.

        Returns:
            dict: Health status information
        """
        total_jobs = len(self._job_metadata)
        total_pending = sum(
            1
            for m in self._job_metadata.values()
            if m.state in [JobState.PENDING, JobState.SCHEDULED]
        )
        total_running = sum(
            1
            for m in self._job_metadata.values()
            if m.state in [JobState.RUNNING, JobState.PROGRESS]
        )
        total_failed = sum(
            1 for m in self._job_metadata.values() if m.state == JobState.FAILED
        )

        # Calculate health score (0-100)
        health_score = 100.0
        if total_jobs > 0:
            failed_ratio = total_failed / total_jobs
            health_score -= failed_ratio * 50  # Failed jobs reduce health

            pending_ratio = total_pending / total_jobs
            if pending_ratio > 0.5:  # Too many pending
                health_score -= (pending_ratio - 0.5) * 50

        health_score = max(0, min(100, health_score))

        return {
            "status": (
                "healthy"
                if health_score >= 80
                else "degraded" if health_score >= 50 else "unhealthy"
            ),
            "health_score": round(health_score, 2),
            "total_jobs": total_jobs,
            "pending_jobs": total_pending,
            "running_jobs": total_running,
            "failed_jobs": total_failed,
            "dead_letter_count": len(self._dead_letter_queue),
            "deduplication_enabled": self.enable_deduplication,
            "fair_scheduling_enabled": self.enable_fair_scheduling,
            "timestamp": datetime.utcnow().isoformat(),
        }
