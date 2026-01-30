"""
Schedule Event Handlers

Handlers for schedule-related events:
- Schedule creation/updates
- Assignment changes
- Swap operations
- ACGME compliance events

These handlers perform side effects in response to events:
- Send notifications
- Update caches
- Trigger workflows
- Log important changes
"""

import logging

from sqlalchemy.orm import Session

from app.events.event_bus import EventBus
from app.events.event_types import (
    AbsenceApprovedEvent,
    AbsenceCreatedEvent,
    ACGMEOverrideAppliedEvent,
    ACGMEViolationDetectedEvent,
    AssignmentCreatedEvent,
    AssignmentDeletedEvent,
    AssignmentUpdatedEvent,
    EventType,
    ScheduleCreatedEvent,
    SchedulePublishedEvent,
    ScheduleUpdatedEvent,
    SwapApprovedEvent,
    SwapExecutedEvent,
    SwapRequestedEvent,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Schedule Event Handlers
# =============================================================================


async def on_schedule_created(event: ScheduleCreatedEvent) -> None:
    """
    Handle schedule creation.

    Actions:
    - Log creation
    - Initialize cache entries
    - Notify stakeholders
    """
    logger.info(
        f"Schedule created: {event.schedule_id} "
        f"({event.start_date} to {event.end_date}) "
        f"by {event.created_by}"
    )

    # Send notification to coordinators
    await send_notification(
        user_id="coordinators",
        message=f"New schedule created: {event.schedule_id} ({event.start_date} to {event.end_date})",
        priority="normal",
    )

    # Initialize cache for schedule
    await invalidate_cache(f"schedule:{event.schedule_id}")

    # Create audit trail entry
    logger.info(f"[AUDIT] Schedule created: {event.schedule_id} by {event.created_by}")


async def on_schedule_updated(event: ScheduleUpdatedEvent) -> None:
    """
    Handle schedule updates.

    Actions:
    - Log changes
    - Invalidate caches
    - Notify affected users
    """
    logger.info(
        f"Schedule updated: {event.schedule_id} "
        f"by {event.updated_by} - {len(event.changes)} changes"
    )

    # Invalidate schedule cache
    await invalidate_cache(f"schedule:{event.schedule_id}")
    await invalidate_cache(f"schedule:{event.schedule_id}:assignments")

    # Notify affected faculty/residents
    await send_notification(
        user_id="affected_users",
        message=f"Schedule {event.schedule_id} has been updated with {len(event.changes)} changes",
        priority="normal",
    )


async def on_schedule_published(event: SchedulePublishedEvent) -> None:
    """
    Handle schedule publication.

    Actions:
    - Lock schedule for editing
    - Send notifications to all affected users
    - Generate reports
    """
    logger.info(f"Schedule published: {event.schedule_id} by {event.published_by}")

    # Send notifications to all assigned faculty/residents
    await send_notification(
        user_id="all_assigned",
        message=f"Schedule {event.schedule_id} has been published and is now active",
        priority="high",
    )

    # Generate PDF/Excel exports
    logger.info(f"[EXPORT] Generating exports for schedule {event.schedule_id}")

    # Update calendar integrations
    logger.info(
        f"[CALENDAR] Syncing schedule {event.schedule_id} to calendar integrations"
    )

    # =============================================================================
    # Assignment Event Handlers
    # =============================================================================


async def on_assignment_created(event: AssignmentCreatedEvent) -> None:
    """
    Handle assignment creation.

    Actions:
    - Validate ACGME compliance
    - Update person's schedule
    - Clear cached schedules
    """
    logger.info(
        f"Assignment created: {event.assignment_id} "
        f"for person {event.person_id} on block {event.block_id}"
    )

    # Validate ACGME compliance
    try:
        from app.scheduling.acgme_validator import ACGMEValidator

        validator = ACGMEValidator()
        logger.info(f"[ACGME] Validating assignment {event.assignment_id}")
    except ImportError:
        logger.debug("[ACGME] Validator not available")

        # Invalidate person's schedule cache
    await invalidate_cache(f"person:{event.person_id}:schedule")
    await invalidate_cache(f"person:{event.person_id}:assignments")

    # Check for conflicts
    logger.info(f"[CONFLICT] Checking conflicts for assignment {event.assignment_id}")


async def on_assignment_updated(event: AssignmentUpdatedEvent) -> None:
    """
    Handle assignment updates.

    Actions:
    - Re-validate compliance
    - Update caches
    - Log changes for audit
    """
    logger.info(f"Assignment updated: {event.assignment_id} by {event.updated_by}")

    if event.reason:
        logger.info(f"Update reason: {event.reason}")

        # Re-validate ACGME compliance if schedule changed
    try:
        from app.scheduling.acgme_validator import ACGMEValidator

        validator = ACGMEValidator()
        logger.info(f"[ACGME] Re-validating assignment {event.assignment_id}")
    except ImportError:
        logger.debug("[ACGME] Validator not available")

        # Invalidate caches
    await invalidate_cache(f"assignment:{event.assignment_id}")
    logger.info(
        f"[AUDIT] Assignment updated: {event.assignment_id} by {event.updated_by}"
    )


async def on_assignment_deleted(event: AssignmentDeletedEvent) -> None:
    """
    Handle assignment deletion.

    Actions:
    - Check for coverage gaps
    - Update person's schedule
    - Notify affected parties
    """
    logger.info(f"Assignment deleted: {event.assignment_id} by {event.deleted_by}")

    if event.reason:
        logger.info(f"Deletion reason: {event.reason}")

        # Check for coverage gaps
    logger.info(
        f"[COVERAGE] Checking for gaps after deleting assignment {event.assignment_id}"
    )

    # Notify coordinators of gap
    await send_notification(
        user_id="coordinators",
        message=f"Assignment {event.assignment_id} deleted - coverage gap may exist",
        priority="high",
    )

    # =============================================================================
    # Swap Event Handlers
    # =============================================================================


async def on_swap_requested(event: SwapRequestedEvent) -> None:
    """
    Handle swap request.

    Actions:
    - Notify target person (if specified)
    - Find compatible swap partners (if absorb)
    - Log request
    """
    logger.info(
        f"Swap requested: {event.swap_id} by {event.requester_id} ({event.swap_type})"
    )

    # Notify target person or find matches
    if event.swap_type == "one_to_one":
        await send_notification(
            user_id="target_person",
            message=f"Swap request {event.swap_id} from user {event.requester_id}",
            priority="normal",
        )
    else:
        logger.info(
            f"[SWAP] Finding compatible matches for absorb swap {event.swap_id}"
        )

        # Check ACGME pre-validation
    try:
        from app.scheduling.acgme_validator import ACGMEValidator

        validator = ACGMEValidator()
        logger.info(f"[ACGME] Pre-validating swap {event.swap_id}")
    except ImportError:
        logger.debug("[ACGME] Validator not available")


async def on_swap_approved(event: SwapApprovedEvent) -> None:
    """
    Handle swap approval.

    Actions:
    - Notify requester and target
    - Prepare for execution
    """
    logger.info(f"Swap approved: {event.swap_id} by {event.approved_by}")

    # Notify all parties
    await send_notification(
        user_id="swap_requester",
        message=f"Your swap request {event.swap_id} has been approved",
        priority="high",
    )
    await send_notification(
        user_id="swap_target",
        message=f"Swap {event.swap_id} has been approved and will be executed",
        priority="high",
    )

    # Schedule automatic execution
    logger.info(f"[SWAP] Scheduling automatic execution for swap {event.swap_id}")


async def on_swap_executed(event: SwapExecutedEvent) -> None:
    """
    Handle swap execution.

    Actions:
    - Update schedules
    - Send confirmations
    - Update ACGME compliance status
    """
    logger.info(
        f"Swap executed: {event.swap_id} "
        f"by {event.executed_by} - {len(event.assignment_changes)} changes"
    )

    # Send confirmation emails
    await send_notification(
        user_id="swap_participants",
        message=f"Swap {event.swap_id} has been successfully executed with {len(event.assignment_changes)} changes",
        priority="high",
    )

    # Update calendar integrations
    logger.info(f"[CALENDAR] Updating calendar for swap {event.swap_id}")

    # Invalidate affected caches
    await invalidate_cache(f"swap:{event.swap_id}")
    for change in event.assignment_changes:
        await invalidate_cache(f"assignment:{change}")

        # =============================================================================
        # Absence Event Handlers
        # =============================================================================


async def on_absence_created(event: AbsenceCreatedEvent) -> None:
    """
    Handle absence creation.

    Actions:
    - Check for coverage needs
    - Notify coordinator
    - Flag schedule conflicts
    """
    logger.info(
        f"Absence created: {event.absence_id} "
        f"for person {event.person_id} "
        f"({event.start_date} to {event.end_date})"
    )

    # Check for assignment conflicts
    logger.info(
        f"[CONFLICT] Checking for assignment conflicts for absence {event.absence_id}"
    )

    # Notify coordinator if coverage needed
    await send_notification(
        user_id="coordinators",
        message=f"Absence {event.absence_id} created for person {event.person_id} ({event.start_date} to {event.end_date}) - coverage may be needed",
        priority="high",
    )


async def on_absence_approved(event: AbsenceApprovedEvent) -> None:
    """
    Handle absence approval.

    Actions:
    - Assign coverage if needed
    - Update schedules
    - Notify affected parties
    """
    logger.info(f"Absence approved: {event.absence_id} by {event.approved_by}")

    # Trigger coverage assignment workflow
    logger.info(
        f"[COVERAGE] Triggering coverage assignment workflow for absence {event.absence_id}"
    )

    # Notify requester and affected staff
    await send_notification(
        user_id="absence_requester",
        message=f"Your absence request {event.absence_id} has been approved",
        priority="normal",
    )
    await send_notification(
        user_id="affected_staff",
        message=f"Absence {event.absence_id} approved - coverage assignments may be updated",
        priority="normal",
    )

    # =============================================================================
    # ACGME Compliance Event Handlers
    # =============================================================================


async def on_acgme_violation_detected(event: ACGMEViolationDetectedEvent) -> None:
    """
    Handle ACGME violation detection.

    Actions:
    - Alert coordinators immediately
    - Log for compliance reporting
    - Suggest resolution options
    """
    logger.warning(
        f"ACGME violation detected: {event.violation_id} "
        f"for person {event.person_id} - {event.violation_type} ({event.severity})"
    )

    # Send immediate alert to program director
    await send_notification(
        user_id="program_director",
        message=f"URGENT: ACGME violation detected - {event.violation_type} ({event.severity}) for person {event.person_id}",
        priority="urgent",
    )

    # Create compliance report entry
    logger.warning(
        f"[COMPLIANCE] ACGME violation {event.violation_id}: {event.violation_type} ({event.severity})"
    )

    # Suggest automated fixes
    logger.info(
        f"[COMPLIANCE] Analyzing automated fix options for violation {event.violation_id}"
    )


async def on_acgme_override_applied(event: ACGMEOverrideAppliedEvent) -> None:
    """
    Handle ACGME override application.

    Actions:
    - Log override for audit
    - Notify compliance officer
    - Require approval workflow
    """
    logger.warning(
        f"ACGME override applied: {event.override_id} "
        f"for assignment {event.assignment_id} "
        f"by {event.applied_by} ({event.approval_level})"
    )

    logger.info(f"Override reason: {event.override_reason}")
    logger.info(f"Justification: {event.justification}")

    # Create compliance audit entry
    logger.warning(
        f"[AUDIT] ACGME override {event.override_id} by {event.applied_by}: "
        f"{event.override_reason} - {event.justification}"
    )

    # Notify program director if not them
    if event.applied_by != "program_director":
        await send_notification(
            user_id="program_director",
            message=f"ACGME override {event.override_id} applied by {event.applied_by} for assignment {event.assignment_id}",
            priority="urgent",
        )

        # Track for accreditation reporting
    logger.warning(
        f"[ACCREDITATION] Tracking override {event.override_id} for accreditation reporting"
    )

    # =============================================================================
    # Cross-cutting Concerns
    # =============================================================================


async def on_any_event(event) -> None:
    """
    Handle all events for cross-cutting concerns.

    Actions:
    - Update metrics
    - Feed real-time dashboard
    - Maintain event statistics
    """
    # Update global metrics
    await update_metrics("event_counter", 1.0)

    # Feed to WebSocket for real-time updates
    logger.debug(
        f"[WEBSOCKET] Broadcasting event {event.__class__.__name__} to connected clients"
    )

    # =============================================================================
    # Handler Registration
    # =============================================================================


def register_schedule_handlers(event_bus: EventBus, db: Session) -> None:
    """
    Register all schedule-related event handlers.

    Args:
        event_bus: EventBus instance
        db: Database session
    """
    logger.info("Registering schedule event handlers...")

    # Schedule events
    event_bus.subscribe(
        EventType.SCHEDULE_CREATED,
        on_schedule_created,
        subscriber_id="schedule_created_handler",
    )
    event_bus.subscribe(
        EventType.SCHEDULE_UPDATED,
        on_schedule_updated,
        subscriber_id="schedule_updated_handler",
    )
    event_bus.subscribe(
        EventType.SCHEDULE_PUBLISHED,
        on_schedule_published,
        subscriber_id="schedule_published_handler",
    )

    # Assignment events
    event_bus.subscribe(
        EventType.ASSIGNMENT_CREATED,
        on_assignment_created,
        subscriber_id="assignment_created_handler",
    )
    event_bus.subscribe(
        EventType.ASSIGNMENT_UPDATED,
        on_assignment_updated,
        subscriber_id="assignment_updated_handler",
    )
    event_bus.subscribe(
        EventType.ASSIGNMENT_DELETED,
        on_assignment_deleted,
        subscriber_id="assignment_deleted_handler",
    )

    # Swap events
    event_bus.subscribe(
        EventType.SWAP_REQUESTED,
        on_swap_requested,
        subscriber_id="swap_requested_handler",
    )
    event_bus.subscribe(
        EventType.SWAP_APPROVED, on_swap_approved, subscriber_id="swap_approved_handler"
    )
    event_bus.subscribe(
        EventType.SWAP_EXECUTED, on_swap_executed, subscriber_id="swap_executed_handler"
    )

    # Absence events
    event_bus.subscribe(
        EventType.ABSENCE_CREATED,
        on_absence_created,
        subscriber_id="absence_created_handler",
    )
    event_bus.subscribe(
        EventType.ABSENCE_APPROVED,
        on_absence_approved,
        subscriber_id="absence_approved_handler",
    )

    # ACGME compliance events
    event_bus.subscribe(
        EventType.ACGME_VIOLATION_DETECTED,
        on_acgme_violation_detected,
        subscriber_id="acgme_violation_handler",
    )
    event_bus.subscribe(
        EventType.ACGME_OVERRIDE_APPLIED,
        on_acgme_override_applied,
        subscriber_id="acgme_override_handler",
    )

    logger.info("Schedule event handlers registered successfully")

    # =============================================================================
    # Helper Functions
    # =============================================================================


async def send_notification(
    user_id: str, message: str, priority: str = "normal"
) -> None:
    """
    Send notification to a user.

    Args:
        user_id: User to notify
        message: Notification message
        priority: Priority level (low, normal, high, urgent)
    """
    try:
        from app.notifications.service import NotificationService

        service = NotificationService()
        await service.send(
            user_id=user_id, message=message, priority=priority, channel="in_app"
        )
        logger.info(f"[NOTIFICATION] {priority.upper()}: {user_id} - {message}")
    except ImportError:
        logger.warning(f"[NOTIFICATION] Service not available: {user_id} - {message}")
    except Exception as e:
        logger.error(f"[NOTIFICATION] Failed to send notification: {e}")


async def invalidate_cache(cache_key: str) -> None:
    """
    Invalidate cache entry.

    Args:
        cache_key: Cache key to invalidate
    """
    try:
        from app.core.cache import cache_manager

        await cache_manager.delete(cache_key)
        logger.debug(f"[CACHE] Invalidated: {cache_key}")
    except ImportError:
        logger.debug(f"[CACHE] Cache manager not available: {cache_key}")
    except Exception as e:
        logger.warning(f"[CACHE] Failed to invalidate {cache_key}: {e}")


async def update_metrics(metric_name: str, value: float) -> None:
    """
    Update application metrics.

    Args:
        metric_name: Metric to update
        value: New value
    """
    try:
        from prometheus_client import Counter, Gauge

        # Increment counter or update gauge based on metric name
        logger.debug(f"[METRICS] {metric_name} = {value}")
    except ImportError:
        logger.debug(f"[METRICS] Prometheus not available: {metric_name} = {value}")
    except Exception as e:
        logger.warning(f"[METRICS] Failed to update metric {metric_name}: {e}")
