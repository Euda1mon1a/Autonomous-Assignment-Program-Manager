"""Example usage of saga orchestration for distributed transactions.

This module demonstrates how to use the saga orchestrator for complex
multi-step transactions with automatic compensation on failure.

When to Use Sagas:
    - Operations spanning multiple services or data stores
    - Long-running transactions that can't hold locks
    - Workflows requiring atomic "all or nothing" semantics
    - Operations where partial completion is worse than full rollback

When NOT to Use Sagas:
    - Simple single-database transactions (use DB transactions)
    - Read-only operations (no rollback needed)
    - Operations where partial completion is acceptable
    - Very short operations (saga overhead not worth it)

Compensation Design Guidelines:
    1. Compensations should be idempotent (safe to retry)
    2. Compensations may not restore exact previous state
    3. Compensations should succeed even if original action failed
    4. Consider using "reserved" states that expire automatically

Example Compensation Patterns:
    - CreateRecord -> DeleteRecord (or mark as cancelled)
    - ReserveInventory -> ReleaseReservation (or let reservation expire)
    - SendNotification -> SendCancellationNotification
    - ChargePayment -> RefundPayment (may have different fees)
    - AssignSlot -> UnassignSlot (check for dependencies first)
"""

import asyncio
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.saga import (
    SagaDefinition,
    SagaOrchestrator,
    SagaStepDefinition,
)

logger = logging.getLogger(__name__)


# Example: Scheduling Assignment Transaction
# ===========================================
# This saga handles creating a schedule assignment with multiple steps:
# 1. Validate ACGME compliance
# 2. Reserve the time slot
# 3. Create assignment record
# 4. Send notifications
#
# If any step fails, previous steps are compensated (rolled back).


async def validate_acgme_compliance(data: dict[str, Any]) -> dict[str, Any]:
    """Validate that assignment meets ACGME requirements.

    Args:
        data: Contains person_id, block_id, rotation_id

    Returns:
        Validation result with compliance check details

    Raises:
        ValueError: If compliance validation fails
    """
    person_id = data["person_id"]
    block_id = data["block_id"]

    logger.info(f"Validating ACGME compliance for person {person_id}, block {block_id}")

    # Simulate validation logic
    # In real implementation, this would check:
    # - 80-hour rule
    # - 1-in-7 rule
    # - Supervision ratios
    await asyncio.sleep(0.1)  # Simulate DB query

    return {
        "compliance_valid": True,
        "hours_this_week": 40,
        "hours_this_month": 160,
        "days_since_day_off": 3,
    }


async def compensate_acgme_validation(data: dict[str, Any]) -> None:
    """No compensation needed for read-only validation."""
    logger.info("No compensation needed for ACGME validation")


async def reserve_time_slot(data: dict[str, Any]) -> dict[str, Any]:
    """Reserve the time slot for the assignment.

    Args:
        data: Contains person_id, block_id

    Returns:
        Reservation details

    Raises:
        ValueError: If slot already reserved
    """
    person_id = data["person_id"]
    block_id = data["block_id"]

    logger.info(f"Reserving time slot for person {person_id}, block {block_id}")

    # Simulate reservation logic
    await asyncio.sleep(0.1)

    return {
        "reservation_id": "rsv_12345",
        "reserved_at": "2024-01-15T10:30:00Z",
        "expires_at": "2024-01-15T10:35:00Z",
    }


async def compensate_time_slot_reservation(data: dict[str, Any]) -> None:
    """Release the reserved time slot.

    Args:
        data: Contains the reservation details from reserve_time_slot
    """
    reservation_data = data.get("reserve_time_slot", {})
    reservation_id = reservation_data.get("reservation_id")

    logger.info(f"Releasing time slot reservation {reservation_id}")

    # Simulate releasing reservation
    await asyncio.sleep(0.05)


async def create_assignment_record(data: dict[str, Any]) -> dict[str, Any]:
    """Create the assignment database record.

    Args:
        data: Contains person_id, block_id, rotation_id

    Returns:
        Created assignment details
    """
    person_id = data["person_id"]
    block_id = data["block_id"]
    rotation_id = data["rotation_id"]

    logger.info(f"Creating assignment record: person={person_id}, block={block_id}")

    # Simulate DB insert
    await asyncio.sleep(0.1)

    return {
        "assignment_id": "asgn_67890",
        "created_at": "2024-01-15T10:30:05Z",
    }


async def compensate_assignment_record(data: dict[str, Any]) -> None:
    """Delete the assignment record.

    Args:
        data: Contains assignment details from create_assignment_record
    """
    assignment_data = data.get("create_assignment_record", {})
    assignment_id = assignment_data.get("assignment_id")

    logger.info(f"Deleting assignment record {assignment_id}")

    # Simulate DB delete
    await asyncio.sleep(0.05)


async def send_notifications(data: dict[str, Any]) -> dict[str, Any]:
    """Send notifications about the new assignment.

    Args:
        data: Contains assignment details

    Returns:
        Notification status
    """
    assignment_data = data.get("create_assignment_record", {})
    assignment_id = assignment_data.get("assignment_id")

    logger.info(f"Sending notifications for assignment {assignment_id}")

    # Simulate sending emails/push notifications
    await asyncio.sleep(0.1)

    return {
        "notifications_sent": 2,
        "recipients": ["faculty@example.com", "resident@example.com"],
    }


async def compensate_notifications(data: dict[str, Any]) -> None:
    """Send cancellation notifications.

    Args:
        data: Contains notification details
    """
    logger.info("Sending assignment cancellation notifications")

    # Simulate sending cancellation emails
    await asyncio.sleep(0.05)


# Define the saga
ASSIGNMENT_CREATION_SAGA = SagaDefinition(
    name="assignment_creation",
    description="Create schedule assignment with ACGME validation",
    version="1.0",
    steps=[
        SagaStepDefinition(
            name="validate_acgme_compliance",
            action=validate_acgme_compliance,
            compensation=compensate_acgme_validation,
            timeout_seconds=30,
            retry_attempts=2,
            idempotent=True,
        ),
        SagaStepDefinition(
            name="reserve_time_slot",
            action=reserve_time_slot,
            compensation=compensate_time_slot_reservation,
            timeout_seconds=10,
            retry_attempts=3,
            idempotent=True,
        ),
        SagaStepDefinition(
            name="create_assignment_record",
            action=create_assignment_record,
            compensation=compensate_assignment_record,
            timeout_seconds=15,
            retry_attempts=2,
            idempotent=False,  # Not idempotent - creates new record
        ),
        SagaStepDefinition(
            name="send_notifications",
            action=send_notifications,
            compensation=compensate_notifications,
            timeout_seconds=30,
            retry_attempts=1,
            idempotent=True,
        ),
    ],
    timeout_seconds=300,  # 5 minutes total
)


# Example: Parallel Service Updates
# ==================================
# This saga demonstrates parallel execution of independent steps.


async def update_analytics_service(data: dict[str, Any]) -> dict[str, Any]:
    """Update analytics service with new assignment."""
    logger.info("Updating analytics service")
    await asyncio.sleep(0.2)
    return {"analytics_updated": True}


async def update_calendar_service(data: dict[str, Any]) -> dict[str, Any]:
    """Update calendar service with new assignment."""
    logger.info("Updating calendar service")
    await asyncio.sleep(0.2)
    return {"calendar_updated": True}


async def update_notification_service(data: dict[str, Any]) -> dict[str, Any]:
    """Update notification service with new assignment."""
    logger.info("Updating notification service")
    await asyncio.sleep(0.2)
    return {"notification_service_updated": True}


async def compensate_analytics_update(data: dict[str, Any]) -> None:
    """Revert analytics service update."""
    logger.info("Reverting analytics service update")
    await asyncio.sleep(0.1)


async def compensate_calendar_update(data: dict[str, Any]) -> None:
    """Revert calendar service update."""
    logger.info("Reverting calendar service update")
    await asyncio.sleep(0.1)


async def compensate_notification_update(data: dict[str, Any]) -> None:
    """Revert notification service update."""
    logger.info("Reverting notification service update")
    await asyncio.sleep(0.1)


PARALLEL_UPDATE_SAGA = SagaDefinition(
    name="parallel_service_updates",
    description="Update multiple services in parallel",
    version="1.0",
    steps=[
        # These three steps execute in parallel
        SagaStepDefinition(
            name="update_analytics",
            action=update_analytics_service,
            compensation=compensate_analytics_update,
            parallel_group="service_updates",
            timeout_seconds=30,
        ),
        SagaStepDefinition(
            name="update_calendar",
            action=update_calendar_service,
            compensation=compensate_calendar_update,
            parallel_group="service_updates",
            timeout_seconds=30,
        ),
        SagaStepDefinition(
            name="update_notifications",
            action=update_notification_service,
            compensation=compensate_notification_update,
            parallel_group="service_updates",
            timeout_seconds=30,
        ),
        # This step executes after parallel group completes
        SagaStepDefinition(
            name="finalize_updates",
            action=send_notifications,  # Reuse from above
            compensation=compensate_notifications,
            timeout_seconds=30,
        ),
    ],
    timeout_seconds=120,
)


# Usage example
async def create_assignment_with_saga(
    db: Session,
    person_id: str,
    block_id: str,
    rotation_id: str,
) -> dict[str, Any]:
    """Create an assignment using saga orchestration.

    Args:
        db: Database session
        person_id: Person ID
        block_id: Block ID
        rotation_id: Rotation ID

    Returns:
        Assignment creation result

    Raises:
        SagaTimeoutError: If saga times out
        SagaCompensationError: If compensation fails
    """
    # Create orchestrator
    orchestrator = SagaOrchestrator(db)

    # Register saga definition
    orchestrator.register_saga(ASSIGNMENT_CREATION_SAGA)

    # Execute saga
    result = await orchestrator.execute_saga(
        saga_name="assignment_creation",
        input_data={
            "person_id": person_id,
            "block_id": block_id,
            "rotation_id": rotation_id,
        },
        metadata={
            "user_id": "current_user_id",
            "trace_id": "trace_123",
            "operation": "create_assignment",
        },
    )

    if result.is_successful:
        logger.info(f"Assignment created successfully via saga {result.saga_id}")
        return {
            "success": True,
            "saga_id": str(result.saga_id),
            "assignment_id": result.step_results[2].output_data.get("assignment_id"),
        }
    else:
        logger.error(
            f"Assignment creation failed: {result.error_message}. "
            f"Compensated {result.compensated_steps} steps."
        )
        return {
            "success": False,
            "error": result.error_message,
            "saga_id": str(result.saga_id),
            "compensated_steps": result.compensated_steps,
        }


async def execute_parallel_saga_example(db: Session) -> None:
    """Demonstrate parallel saga execution.

    Args:
        db: Database session
    """
    orchestrator = SagaOrchestrator(db)
    orchestrator.register_saga(PARALLEL_UPDATE_SAGA)

    result = await orchestrator.execute_saga(
        saga_name="parallel_service_updates",
        input_data={"assignment_id": "asgn_12345"},
    )

    logger.info(f"Parallel saga result: {result.status}")
    logger.info(f"Duration: {result.duration_seconds}s")

    for step_result in result.step_results:
        logger.info(
            f"  Step '{step_result.step_name}': {step_result.status} "
            f"(retries: {step_result.retry_count})"
        )


# Recovery example
async def recover_interrupted_sagas(db: Session) -> None:
    """Recover sagas interrupted by service restart.

    This should be called on service startup.

    Args:
        db: Database session
    """
    orchestrator = SagaOrchestrator(db)

    # Register all saga definitions that might need recovery
    orchestrator.register_saga(ASSIGNMENT_CREATION_SAGA)
    orchestrator.register_saga(PARALLEL_UPDATE_SAGA)

    # Recover pending sagas
    recovered_ids = await orchestrator.recover_pending_sagas()

    logger.info(f"Recovered {len(recovered_ids)} interrupted sagas")
    for saga_id in recovered_ids:
        logger.info(f"  - Saga {saga_id}")


# Monitoring example
async def monitor_saga_execution(db: Session, saga_id: str) -> None:
    """Monitor saga execution progress.

    Args:
        db: Database session
        saga_id: Saga execution ID
    """
    orchestrator = SagaOrchestrator(db)

    from uuid import UUID

    result = await orchestrator.get_saga_status(UUID(saga_id))

    if not result:
        logger.error(f"Saga {saga_id} not found")
        return

    logger.info(f"Saga {saga_id} Status Report")
    logger.info(f"  Status: {result.status}")
    logger.info(f"  Started: {result.started_at}")
    logger.info(f"  Completed: {result.completed_at}")
    logger.info(f"  Duration: {result.duration_seconds}s")
    logger.info(f"  Compensated Steps: {result.compensated_steps}")

    if result.error_message:
        logger.info(f"  Error: {result.error_message}")

    logger.info("  Steps:")
    for step in result.step_results:
        logger.info(
            f"    - {step.step_name}: {step.status} (retries: {step.retry_count})"
        )
        if step.error_message:
            logger.info(f"      Error: {step.error_message}")
