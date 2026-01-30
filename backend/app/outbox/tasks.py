"""Celery Background Tasks for Transactional Outbox.

This module defines the Celery tasks that power the transactional outbox pattern:

Tasks Overview
--------------
1. **relay_outbox_messages** (every 1 minute)
   Core task that reads pending messages from the outbox table and publishes
   them to Celery. This is the "pump" that moves messages from database to broker.

2. **handle_outbox_event** (on-demand)
   Generic event handler that receives all outbox events. Routes to specific
   handlers based on event_type (assignment.*, swap.*, conflict.*).

3. **archive_published_messages** (every 6 hours)
   Moves successfully published messages to the archive table to keep the
   main outbox table small for performance.

4. **cleanup_old_archive** (daily at 3 AM)
   Deletes archived messages older than retention period (default: 30 days).

5. **cleanup_failed_messages** (daily at 4 AM)
   Deletes dead letter messages (exceeded max retries) after investigation
   period (default: 7 days).

6. **collect_outbox_metrics** (every 5 minutes)
   Gathers statistics for monitoring: pending count, latency, failures.

Task Scheduling
---------------
These tasks are designed to run via Celery Beat. Add to celery_app.py::

    from celery.schedules import crontab

    beat_schedule = {
        "outbox-relay": {
            "task": "app.outbox.tasks.relay_outbox_messages",
            "schedule": crontab(minute="*/1"),  # Every minute
            "options": {"queue": "outbox"},
        },
        "outbox-archive": {
            "task": "app.outbox.tasks.archive_published_messages",
            "schedule": crontab(hour="*/6"),  # Every 6 hours
            "options": {"queue": "outbox"},
        },
        "outbox-cleanup-archive": {
            "task": "app.outbox.tasks.cleanup_old_archive",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
            "options": {"queue": "outbox"},
        },
        "outbox-cleanup-failed": {
            "task": "app.outbox.tasks.cleanup_failed_messages",
            "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM
            "options": {"queue": "outbox"},
        },
        "outbox-metrics": {
            "task": "app.outbox.tasks.collect_outbox_metrics",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
            "options": {"queue": "outbox"},
        },
    }

Queue Configuration
-------------------
All outbox tasks use the "outbox" queue. This allows:
- Dedicated workers for outbox processing
- Priority isolation from other Celery tasks
- Independent scaling of outbox processing

To start an outbox-only worker::

    celery -A app.core.celery_app worker -Q outbox --concurrency=2

Error Handling
--------------
All tasks inherit from OutboxTask base class which provides:
- Structured logging on failure/retry
- Automatic retry with exponential backoff (relay task)
- Exception context for debugging

Event Routing
-------------
The handle_outbox_event task routes events by prefix:
- assignment.* -> _handle_assignment_event
- swap.* -> _handle_swap_event
- conflict.* -> _handle_conflict_event

Add new handlers as your domain events grow.
"""

import logging
from typing import Any

from celery import Task

from app.core.celery_app import celery_app
from app.db.session import task_session_scope
from app.outbox.metrics import OutboxMetricsCollector
from app.outbox.outbox import OutboxCleaner, OutboxRelay
from app.services.outbox_notification_service import OutboxNotificationService

logger = logging.getLogger(__name__)


class OutboxTask(Task):
    """Base Celery task class for all outbox-related tasks.

    This class provides common error handling, logging, and monitoring
    for outbox tasks. All outbox tasks should use this as their base class.

    Features:
        - Structured logging with task context on failure
        - Warning logs on retry with retry count
        - Consistent error message format for alerting

    Usage:
        ::

            @celery_app.task(base=OutboxTask)
            def my_outbox_task():
                # Task implementation
                pass

    Note:
        Override on_failure and on_retry in subclasses if you need
        custom error handling (e.g., sending to external monitoring).
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo) -> None:
        """Log structured error when task fails after all retries exhausted.

        Args:
            exc: The exception that caused the failure
            task_id: Celery task ID
            args: Positional arguments passed to task
            kwargs: Keyword arguments passed to task
            einfo: Exception info object with traceback
        """
        logger.error(
            f"Outbox task {self.name} failed: {exc}",
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
            },
            exc_info=True,
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo) -> None:
        """Log warning when task is being retried.

        Args:
            exc: The exception that triggered the retry
            task_id: Celery task ID
            args: Positional arguments passed to task
            kwargs: Keyword arguments passed to task
            einfo: Exception info object with traceback
        """
        logger.warning(
            f"Outbox task {self.name} retrying: {exc}",
            extra={
                "task_id": task_id,
                "retry_count": self.request.retries,
            },
        )


@celery_app.task(
    base=OutboxTask,
    name="app.outbox.tasks.relay_outbox_messages",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def relay_outbox_messages(
    self,
    batch_size: int = 100,
) -> dict[str, Any]:
    """
    Relay pending outbox messages to the message broker.

    This task:
    1. Fetches pending messages from the outbox
    2. Publishes them to Redis/Celery
    3. Marks them as published or failed

    This should run frequently (e.g., every minute) to ensure
    timely message delivery.

    Args:
        batch_size: Maximum number of messages to process per run

    Returns:
        dict: Statistics about the relay operation
    """
    logger.info(f"Starting outbox relay (batch_size={batch_size})")

    try:
        with task_session_scope() as db:
            relay = OutboxRelay(db)
            published_count = relay.publish_pending_messages(
                batch_size=batch_size,
                timeout_stuck_processing=True,
            )

        logger.info(f"Outbox relay completed: published {published_count} messages")

        return {
            "status": "success",
            "published_count": published_count,
            "batch_size": batch_size,
        }

    except Exception as exc:
        logger.error(f"Outbox relay failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@celery_app.task(
    base=OutboxTask,
    name="app.outbox.tasks.handle_outbox_event",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def handle_outbox_event(
    self,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    headers: dict[str, Any],
    message_id: str,
    sequence: int,
) -> dict[str, Any]:
    """Generic handler for all outbox events.

    This is the default consumer task that receives events published by the
    OutboxRelay. It routes events to domain-specific handlers based on the
    event_type prefix.

    Event Routing
    -------------
    Events are routed by prefix:
    - ``assignment.*`` -> _handle_assignment_event
    - ``swap.*`` -> _handle_swap_event
    - ``conflict.*`` -> _handle_conflict_event
    - Other events -> logged as unhandled

    Idempotency
    -----------
    Use the ``message_id`` parameter to implement idempotent processing.
    Store processed message IDs and skip duplicates::

        if is_already_processed(message_id):
            return {"status": "duplicate", "message_id": message_id}
        process_event(...)
        mark_as_processed(message_id)

    Ordering
    --------
    The ``sequence`` parameter indicates ordering within an aggregate.
    If strict ordering is required, verify sequence is monotonically
    increasing for each aggregate.

    Args:
        event_type: Domain event type (e.g., "assignment.created", "swap.executed")
        aggregate_type: Type of business entity (e.g., "assignment", "swap")
        aggregate_id: UUID of the specific entity instance (as string)
        payload: Event data as dict (structure depends on event_type)
        headers: Optional message headers (correlation_id, trace_id, etc.)
        message_id: Unique message UUID for idempotency checking
        sequence: Sequence number for ordering within aggregate (0, 1, 2, ...)

    Returns:
        dict: Processing result with at least {"status": "success"|"unhandled"}

    Raises:
        Exception: Re-raised after logging to trigger Celery retry
    """
    logger.info(
        f"Handling outbox event: {event_type} for {aggregate_type}:{aggregate_id}",
        extra={
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "message_id": message_id,
            "sequence": sequence,
        },
    )

    try:
        # Route to specific handlers based on event type
        if event_type.startswith("assignment."):
            return _handle_assignment_event(event_type, payload, headers)
        elif event_type.startswith("swap."):
            return _handle_swap_event(event_type, payload, headers)
        elif event_type.startswith("conflict."):
            return _handle_conflict_event(event_type, payload, headers)
        else:
            logger.warning(f"No specific handler for event type: {event_type}")
            return {"status": "unhandled", "event_type": event_type}

    except Exception as exc:
        logger.error(
            f"Failed to handle outbox event {event_type}: {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc)


def _handle_assignment_event(
    event_type: str,
    payload: dict[str, Any],
    headers: dict[str, Any],
) -> dict[str, Any]:
    """
    Handle assignment-related events.

    Args:
        event_type: Specific event type
        payload: Event payload
        headers: Message headers

    Returns:
        dict: Processing result
    """
    from app.services.outbox_notification_service import OutboxNotificationService

    logger.info(f"Processing assignment event: {event_type}")

    # Extract common fields from payload
    assignment_id = payload.get("assignment_id")
    person_id = payload.get("person_id")
    block_id = payload.get("block_id")
    rotation_id = payload.get("rotation_id")

    notification_sent = False

    # Send notifications for assignment changes
    with task_session_scope() as db:
        notification_service = OutboxNotificationService(db)

        if event_type == "assignment.created":
            logger.info(
                f"Assignment created: person={person_id}, block={block_id}, "
                f"rotation={rotation_id}"
            )
            if person_id:
                notification_sent = notification_service.notify_assignment_created(
                    person_id=person_id,
                    block_id=block_id,
                    rotation_id=rotation_id,
                    payload=payload,
                )

        elif event_type == "assignment.updated":
            old_rotation = payload.get("old_rotation_id")
            new_rotation = payload.get("new_rotation_id")
            logger.info(
                f"Assignment updated: assignment={assignment_id}, "
                f"rotation changed from {old_rotation} to {new_rotation}"
            )
            if person_id:
                notification_sent = notification_service.notify_assignment_updated(
                    person_id=person_id,
                    assignment_id=assignment_id,
                    old_rotation=old_rotation,
                    new_rotation=new_rotation,
                    payload=payload,
                )

        elif event_type == "assignment.deleted":
            logger.info(
                f"Assignment deleted: assignment={assignment_id}, person={person_id}"
            )
            if person_id:
                notification_sent = notification_service.notify_assignment_deleted(
                    person_id=person_id,
                    assignment_id=assignment_id,
                    payload=payload,
                )

    return {
        "status": "success",
        "event_type": event_type,
        "assignment_id": assignment_id,
        "notification_sent": notification_sent,
    }


def _handle_swap_event(
    event_type: str,
    payload: dict[str, Any],
    headers: dict[str, Any],
) -> dict[str, Any]:
    """
    Handle swap-related events.

    Args:
        event_type: Specific event type
        payload: Event payload
        headers: Message headers

    Returns:
        dict: Processing result
    """
    from app.services.outbox_notification_service import OutboxNotificationService

    logger.info(f"Processing swap event: {event_type}")

    # Extract common fields from payload
    swap_id = payload.get("swap_id")
    requester_id = payload.get("requester_id")
    target_id = payload.get("target_id")
    swap_type = payload.get("swap_type")

    notification_sent = False

    # Send notifications for swap events
    with task_session_scope() as db:
        notification_service = OutboxNotificationService(db)

        if event_type == "swap.executed":
            logger.info(
                f"Swap executed: swap_id={swap_id}, type={swap_type}, "
                f"requester={requester_id}, target={target_id}"
            )
            if requester_id:
                notification_sent = notification_service.notify_swap_executed(
                    requester_id=requester_id,
                    target_id=target_id,
                    swap_id=swap_id,
                    payload=payload,
                )

        elif event_type == "swap.requested":
            logger.info(
                f"Swap requested: swap_id={swap_id}, type={swap_type}, "
                f"from={requester_id}, to={target_id}"
            )
            if target_id and requester_id:
                notification_sent = notification_service.notify_swap_requested(
                    target_id=target_id,
                    requester_id=requester_id,
                    swap_id=swap_id,
                    payload=payload,
                )

        elif event_type == "swap.approved":
            logger.info(f"Swap approved: swap_id={swap_id}, requester={requester_id}")
            if requester_id:
                notification_sent = notification_service.notify_swap_approved(
                    requester_id=requester_id,
                    swap_id=swap_id,
                    payload=payload,
                )

        elif event_type == "swap.rejected":
            reason = payload.get("rejection_reason")
            logger.info(f"Swap rejected: swap_id={swap_id}, reason={reason}")
            if requester_id:
                notification_sent = notification_service.notify_swap_rejected(
                    requester_id=requester_id,
                    swap_id=swap_id,
                    reason=reason,
                    payload=payload,
                )

    return {
        "status": "success",
        "event_type": event_type,
        "swap_id": swap_id,
        "notification_sent": notification_sent,
    }


def _handle_conflict_event(
    event_type: str,
    payload: dict[str, Any],
    headers: dict[str, Any],
) -> dict[str, Any]:
    """
    Handle conflict-related events.

    Args:
        event_type: Specific event type
        payload: Event payload
        headers: Message headers

    Returns:
        dict: Processing result
    """
    from app.services.outbox_notification_service import OutboxNotificationService

    logger.info(f"Processing conflict event: {event_type}")

    # Extract common fields from payload
    conflict_id = payload.get("conflict_id")
    conflict_type = payload.get("conflict_type")
    affected_persons = payload.get("affected_persons", [])
    severity = payload.get("severity", "medium")

    notification_sent = False

    # Send alerts for conflicts
    with task_session_scope() as db:
        notification_service = OutboxNotificationService(db)

        if event_type == "conflict.detected":
            logger.warning(
                f"Conflict detected: id={conflict_id}, type={conflict_type}, "
                f"severity={severity}, affected_persons={affected_persons}"
            )
            notification_sent = notification_service.notify_conflict_detected(
                conflict_id=conflict_id,
                conflict_type=conflict_type,
                severity=severity,
                affected_persons=affected_persons,
                payload=payload,
            )

        elif event_type == "conflict.resolved":
            resolution = payload.get("resolution", "Unknown resolution")
            logger.info(
                f"Conflict resolved: id={conflict_id}, resolution={resolution}, "
                f"affected_persons={affected_persons}"
            )
            notification_sent = notification_service.notify_conflict_resolved(
                conflict_id=conflict_id,
                resolution=resolution,
                affected_persons=affected_persons,
                payload=payload,
            )

        elif event_type == "conflict.escalated":
            escalation_level = payload.get("escalation_level", 1)
            logger.warning(
                f"Conflict escalated: id={conflict_id}, level={escalation_level}, "
                f"type={conflict_type}"
            )
            notification_sent = notification_service.notify_conflict_escalated(
                conflict_id=conflict_id,
                conflict_type=conflict_type,
                escalation_level=escalation_level,
                payload=payload,
            )

    return {
        "status": "success",
        "event_type": event_type,
        "conflict_id": conflict_id,
        "severity": severity,
        "notification_sent": notification_sent,
    }


@celery_app.task(
    base=OutboxTask,
    name="app.outbox.tasks.archive_published_messages",
    bind=True,
)
def archive_published_messages(
    self,
    batch_size: int = 1000,
    archive_after_hours: int = 24,
) -> dict[str, Any]:
    """
    Archive successfully published messages.

    Moves published messages to the archive table to keep
    the main outbox table small and performant.

    Args:
        batch_size: Maximum messages to archive per run
        archive_after_hours: Hours after publishing to archive

    Returns:
        dict: Archival statistics
    """
    logger.info(
        f"Starting outbox archival (batch_size={batch_size}, "
        f"archive_after_hours={archive_after_hours})"
    )

    try:
        with task_session_scope() as db:
            cleaner = OutboxCleaner(
                db,
                archive_after_hours=archive_after_hours,
            )
            archived_count = cleaner.archive_published_messages(batch_size)

        logger.info(f"Archived {archived_count} outbox messages")

        return {
            "status": "success",
            "archived_count": archived_count,
        }

    except Exception as exc:
        logger.error(f"Outbox archival failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    base=OutboxTask,
    name="app.outbox.tasks.cleanup_old_archive",
    bind=True,
)
def cleanup_old_archive(
    self,
    batch_size: int = 1000,
    retention_days: int = 30,
) -> dict[str, Any]:
    """
    Delete old archived messages based on retention policy.

    Args:
        batch_size: Maximum messages to delete per run
        retention_days: Days to keep archived messages

    Returns:
        dict: Cleanup statistics
    """
    logger.info(
        f"Starting archive cleanup (batch_size={batch_size}, "
        f"retention_days={retention_days})"
    )

    try:
        with task_session_scope() as db:
            cleaner = OutboxCleaner(
                db,
                retention_days=retention_days,
            )
            deleted_count = cleaner.delete_old_archive(batch_size)

        logger.info(f"Deleted {deleted_count} archived outbox messages")

        return {
            "status": "success",
            "deleted_count": deleted_count,
        }

    except Exception as exc:
        logger.error(f"Archive cleanup failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    base=OutboxTask,
    name="app.outbox.tasks.cleanup_failed_messages",
    bind=True,
)
def cleanup_failed_messages(
    self,
    batch_size: int = 1000,
    max_age_days: int = 7,
) -> dict[str, Any]:
    """
    Delete old failed messages (dead letters).

    Args:
        batch_size: Maximum messages to delete per run
        max_age_days: Days to keep failed messages

    Returns:
        dict: Cleanup statistics
    """
    logger.info(
        f"Starting failed message cleanup (batch_size={batch_size}, "
        f"max_age_days={max_age_days})"
    )

    try:
        with task_session_scope() as db:
            cleaner = OutboxCleaner(db)
            deleted_count = cleaner.cleanup_failed_messages(
                max_age_days=max_age_days,
                batch_size=batch_size,
            )

        logger.info(f"Deleted {deleted_count} failed outbox messages")

        return {
            "status": "success",
            "deleted_count": deleted_count,
        }

    except Exception as exc:
        logger.error(f"Failed message cleanup failed: {exc}", exc_info=True)
        raise


@celery_app.task(
    base=OutboxTask,
    name="app.outbox.tasks.collect_outbox_metrics",
    bind=True,
)
def collect_outbox_metrics(self) -> dict[str, Any]:
    """
    Collect and report outbox metrics.

    This task gathers statistics about the outbox:
    - Message counts by status
    - Average processing time
    - Failed message counts
    - Retry statistics

    Returns:
        dict: Collected metrics
    """
    logger.debug("Collecting outbox metrics")

    try:
        with task_session_scope() as db:
            collector = OutboxMetricsCollector(db)
            metrics = collector.collect_metrics()

        logger.info(
            f"Outbox metrics: pending={metrics['pending_count']}, "
            f"failed={metrics['failed_count']}, "
            f"avg_age_seconds={metrics['avg_pending_age_seconds']:.2f}"
        )

        return metrics

    except Exception as exc:
        logger.error(f"Metrics collection failed: {exc}", exc_info=True)
        raise
