"""Celery tasks for transactional outbox pattern.

This module defines background tasks for:
1. Relaying outbox messages to the message broker
2. Handling outbox events (generic event handler)
3. Archiving published messages
4. Cleaning up old messages
5. Monitoring and metrics collection

Periodic Schedule:
-----------------
- relay_outbox_messages: Every 1 minute (ensures fast message delivery)
- archive_published_messages: Every 6 hours
- cleanup_old_archive: Daily at 3 AM
- cleanup_failed_messages: Daily at 4 AM
- collect_outbox_metrics: Every 5 minutes

Configuration:
-------------
Add to celery_app.py beat_schedule:

    "outbox-relay": {
        "task": "app.outbox.tasks.relay_outbox_messages",
        "schedule": crontab(minute="*/1"),  # Every minute
        "options": {"queue": "outbox"},
    },
"""

import logging
from typing import Any

from celery import Task

from app.core.celery_app import celery_app
from app.db.session import task_session_scope
from app.outbox.metrics import OutboxMetricsCollector
from app.outbox.outbox import OutboxCleaner, OutboxRelay

logger = logging.getLogger(__name__)


class OutboxTask(Task):
    """
    Base task class for outbox tasks.

    Provides common error handling and logging for outbox-related tasks.
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
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

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
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
    """
    Generic handler for outbox events.

    This is the default task that receives all outbox events.
    It can route to specific handlers based on event_type or
    perform common processing for all events.

    Args:
        event_type: Type of event (e.g., "assignment.created")
        aggregate_type: Type of aggregate (e.g., "assignment")
        aggregate_id: ID of the aggregate
        payload: Event payload data
        headers: Message headers
        message_id: Unique message ID (for idempotency)
        sequence: Sequence number for ordering

    Returns:
        dict: Processing result
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
    logger.info(f"Processing assignment event: {event_type}")

    # Extract common fields from payload
    assignment_id = payload.get("assignment_id")
    person_id = payload.get("person_id")
    block_id = payload.get("block_id")
    rotation_id = payload.get("rotation_id")

    # Send notifications for assignment changes
    if event_type == "assignment.created":
        # Trigger notification to affected person
        logger.info(
            f"Assignment created: person={person_id}, block={block_id}, "
            f"rotation={rotation_id}"
        )
        # TODO: Integrate with notification service when available
        # Example: send_notification(person_id, "New assignment created", payload)

    elif event_type == "assignment.updated":
        # Trigger change notification
        old_rotation = payload.get("old_rotation_id")
        new_rotation = payload.get("new_rotation_id")
        logger.info(
            f"Assignment updated: assignment={assignment_id}, "
            f"rotation changed from {old_rotation} to {new_rotation}"
        )
        # TODO: Integrate with notification service
        # Example: send_notification(person_id, "Assignment updated", payload)

    elif event_type == "assignment.deleted":
        # Trigger deletion notification
        logger.info(
            f"Assignment deleted: assignment={assignment_id}, person={person_id}"
        )
        # TODO: Integrate with notification service
        # Example: send_notification(person_id, "Assignment removed", payload)

    return {
        "status": "success",
        "event_type": event_type,
        "assignment_id": assignment_id,
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
    logger.info(f"Processing swap event: {event_type}")

    # Extract common fields from payload
    swap_id = payload.get("swap_id")
    requester_id = payload.get("requester_id")
    target_id = payload.get("target_id")
    swap_type = payload.get("swap_type")

    # Send notifications for swap events
    if event_type == "swap.executed":
        # Trigger notifications to both parties
        logger.info(
            f"Swap executed: swap_id={swap_id}, type={swap_type}, "
            f"requester={requester_id}, target={target_id}"
        )
        # TODO: Integrate with notification service
        # Example: send_notification(requester_id, "Swap completed", payload)
        # Example: send_notification(target_id, "Swap completed", payload)

    elif event_type == "swap.requested":
        # Trigger request notification to target
        logger.info(
            f"Swap requested: swap_id={swap_id}, type={swap_type}, "
            f"from={requester_id}, to={target_id}"
        )
        # TODO: Integrate with notification service
        # Example: send_notification(target_id, "New swap request", payload)

    elif event_type == "swap.approved":
        # Notify requester of approval
        logger.info(f"Swap approved: swap_id={swap_id}, requester={requester_id}")
        # TODO: send_notification(requester_id, "Swap request approved", payload)

    elif event_type == "swap.rejected":
        # Notify requester of rejection
        reason = payload.get("rejection_reason", "No reason provided")
        logger.info(f"Swap rejected: swap_id={swap_id}, reason={reason}")
        # TODO: send_notification(requester_id, f"Swap rejected: {reason}", payload)

    return {"status": "success", "event_type": event_type, "swap_id": swap_id}


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
    logger.info(f"Processing conflict event: {event_type}")

    # Extract common fields from payload
    conflict_id = payload.get("conflict_id")
    conflict_type = payload.get("conflict_type")
    affected_persons = payload.get("affected_persons", [])
    severity = payload.get("severity", "medium")
    details = payload.get("details", {})

    # Send alerts for conflicts
    if event_type == "conflict.detected":
        # Trigger alert notification to affected persons and coordinators
        logger.warning(
            f"Conflict detected: id={conflict_id}, type={conflict_type}, "
            f"severity={severity}, affected_persons={affected_persons}"
        )
        # TODO: Integrate with notification service
        # Example: For high-severity conflicts, notify coordinators immediately
        # if severity == "high":
        #     send_notification("coordinator", "High-severity conflict detected", payload)
        #
        # Example: Notify affected persons
        # for person_id in affected_persons:
        #     send_notification(person_id, f"Schedule conflict: {conflict_type}", payload)

    elif event_type == "conflict.resolved":
        # Notify affected persons that conflict has been resolved
        resolution = payload.get("resolution", "Unknown resolution")
        logger.info(
            f"Conflict resolved: id={conflict_id}, resolution={resolution}, "
            f"affected_persons={affected_persons}"
        )
        # TODO: send notifications about resolution
        # for person_id in affected_persons:
        #     send_notification(person_id, "Conflict resolved", payload)

    elif event_type == "conflict.escalated":
        # Escalate to higher authority (e.g., program director)
        escalation_level = payload.get("escalation_level", 1)
        logger.warning(
            f"Conflict escalated: id={conflict_id}, level={escalation_level}, "
            f"type={conflict_type}"
        )
        # TODO: Send escalation notifications
        # send_notification("program_director", "Conflict requires attention", payload)

    return {
        "status": "success",
        "event_type": event_type,
        "conflict_id": conflict_id,
        "severity": severity,
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
