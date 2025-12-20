"""
Celery Tasks for Secret Rotation.

Provides automated background tasks for:
- Scheduled secret rotation
- Grace period completion
- Rotation reminders
- Rotation status monitoring
- Emergency rotation triggers

Tasks integrate with SecretRotationService and send notifications for rotation events.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from celery import shared_task
from sqlalchemy.orm import Session

from app.security.secret_rotation import (
    RotationPriority,
    RotationStatus,
    SecretRotationHistory,
    SecretRotationService,
    SecretType,
)

logger = logging.getLogger(__name__)


def get_db_session() -> Session:
    """Get a database session for task execution."""
    from app.core.database import SessionLocal
    return SessionLocal()


@shared_task(
    bind=True,
    name="app.security.rotation_tasks.check_scheduled_rotations",
    max_retries=3,
    default_retry_delay=300,
)
def check_scheduled_rotations(self) -> dict:
    """
    Check for secrets that need rotation and trigger rotation tasks.

    Runs daily at 1 AM (configured in celery_app.py).

    Checks:
    - Secrets past their rotation interval
    - Secrets approaching rotation deadline
    - Failed rotations that need retry

    Returns:
        Dictionary with rotation check results
    """
    logger.info("Checking for scheduled secret rotations")

    db = get_db_session()
    try:
        service = SecretRotationService(db)

        # Check which secrets need rotation
        rotation_status = {}

        # Note: Celery tasks must be synchronous, so we use a sync wrapper
        import asyncio
        due_check = asyncio.run(service.check_rotation_due())

        for secret_type, config in service.DEFAULT_CONFIGS.items():
            try:
                # Check if rotation is due
                status = due_check.get(secret_type, {})

                if status.get("due") and config.auto_rotate:
                    # Trigger rotation
                    logger.info(f"Triggering automatic rotation for {secret_type.value}")
                    rotate_secret.delay(
                        secret_type=secret_type.value,
                        reason="Scheduled automatic rotation",
                    )
                    rotation_status[secret_type.value] = "rotation_triggered"

                elif status.get("days_until_due", 999) <= 7:
                    # Send reminder notification
                    logger.info(
                        f"Sending rotation reminder for {secret_type.value} "
                        f"(due in {status.get('days_until_due')} days)"
                    )
                    send_rotation_reminder.delay(
                        secret_type=secret_type.value,
                        days_until_due=status.get("days_until_due", 0),
                    )
                    rotation_status[secret_type.value] = "reminder_sent"
                else:
                    rotation_status[secret_type.value] = "not_due"

            except Exception as e:
                logger.error(
                    f"Error checking rotation for {secret_type.value}: {e}",
                    exc_info=True,
                )
                rotation_status[secret_type.value] = f"error: {str(e)}"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "rotation_status": rotation_status,
        }

    except Exception as e:
        logger.error(f"Scheduled rotation check failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.security.rotation_tasks.rotate_secret",
    max_retries=3,
    default_retry_delay=600,
)
def rotate_secret(
    self,
    secret_type: str,
    reason: str = "Scheduled rotation",
    initiated_by: str | None = None,
    force: bool = False,
) -> dict:
    """
    Rotate a specific secret.

    Args:
        secret_type: Type of secret to rotate (SecretType enum value)
        reason: Reason for rotation
        initiated_by: User ID who initiated (None for automated)
        force: Force rotation even if not due

    Returns:
        Dictionary with rotation result
    """
    logger.info(f"Starting rotation task for {secret_type}")

    db = get_db_session()
    try:
        service = SecretRotationService(db)

        # Convert string to enum
        secret_type_enum = SecretType(secret_type)

        # Convert initiated_by to UUID if provided
        initiated_by_uuid = UUID(initiated_by) if initiated_by else None

        # Perform rotation (Celery tasks are synchronous, use asyncio.run)
        import asyncio
        result = asyncio.run(service.rotate_secret(
            secret_type=secret_type_enum,
            initiated_by=initiated_by_uuid,
            reason=reason,
            force=force,
        ))

        return {
            "success": result.success,
            "rotation_id": str(result.rotation_id),
            "secret_type": secret_type,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "grace_period_ends": (
                result.grace_period_ends.isoformat()
                if result.grace_period_ends
                else None
            ),
            "error_message": result.error_message,
            "rolled_back": result.rolled_back,
        }

    except Exception as e:
        logger.error(f"Secret rotation failed for {secret_type}: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.security.rotation_tasks.complete_grace_periods",
    max_retries=2,
    default_retry_delay=300,
)
def complete_grace_periods(self) -> dict:
    """
    Complete expired grace periods.

    Runs every hour (configured in celery_app.py).

    Checks for grace periods that have expired and completes them,
    deactivating the old secrets.

    Returns:
        Dictionary with completion results
    """
    logger.info("Checking for expired grace periods")

    db = get_db_session()
    try:
        # Find all grace periods that have expired
        expired_grace_periods = (
            db.query(SecretRotationHistory)
            .filter(
                SecretRotationHistory.status == RotationStatus.GRACE_PERIOD,
                SecretRotationHistory.grace_period_ends <= datetime.utcnow(),
            )
            .all()
        )

        results = {}
        for rotation in expired_grace_periods:
            try:
                logger.info(
                    f"Completing grace period for {rotation.secret_type.value} "
                    f"(rotation_id={rotation.id})"
                )

                service = SecretRotationService(db)
                import asyncio
                success = asyncio.run(service.complete_grace_period(rotation.secret_type))

                results[rotation.secret_type.value] = {
                    "rotation_id": str(rotation.id),
                    "success": success,
                    "completed_at": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(
                    f"Failed to complete grace period for {rotation.secret_type.value}: {e}",
                    exc_info=True,
                )
                results[rotation.secret_type.value] = {
                    "rotation_id": str(rotation.id),
                    "success": False,
                    "error": str(e),
                }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "grace_periods_completed": len([r for r in results.values() if r.get("success")]),
            "failures": len([r for r in results.values() if not r.get("success")]),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Grace period completion failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    name="app.security.rotation_tasks.send_rotation_reminder",
    max_retries=2,
    default_retry_delay=60,
)
def send_rotation_reminder(
    secret_type: str,
    days_until_due: int,
) -> dict:
    """
    Send reminder notification for upcoming rotation.

    Args:
        secret_type: Type of secret approaching rotation
        days_until_due: Number of days until rotation is due

    Returns:
        Dictionary with notification result
    """
    logger.info(
        f"Sending rotation reminder for {secret_type} "
        f"(due in {days_until_due} days)"
    )

    try:
        # In production, this would integrate with notification service
        # For now, just log the reminder

        priority = RotationPriority.HIGH if days_until_due <= 3 else RotationPriority.MEDIUM

        logger.warning(
            f"ROTATION REMINDER: {secret_type} rotation due in {days_until_due} days",
            extra={
                "secret_type": secret_type,
                "days_until_due": days_until_due,
                "priority": priority.value,
            },
        )

        # TODO: Integrate with app.notifications.service.NotificationService
        # to send actual email/webhook notifications

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "secret_type": secret_type,
            "days_until_due": days_until_due,
            "notification_sent": True,
        }

    except Exception as e:
        logger.error(f"Failed to send rotation reminder: {e}", exc_info=True)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "secret_type": secret_type,
            "notification_sent": False,
            "error": str(e),
        }


@shared_task(
    bind=True,
    name="app.security.rotation_tasks.monitor_rotation_health",
    max_retries=2,
    default_retry_delay=300,
)
def monitor_rotation_health(self) -> dict:
    """
    Monitor overall secret rotation health.

    Runs daily at 8 AM (configured in celery_app.py).

    Checks:
    - Failed rotations in last 24 hours
    - Overdue rotations
    - Grace periods approaching expiration
    - Rotation frequency and patterns

    Returns:
        Dictionary with health check results
    """
    logger.info("Running secret rotation health check")

    db = get_db_session()
    try:
        # Check for failed rotations in last 24 hours
        failed_rotations = (
            db.query(SecretRotationHistory)
            .filter(
                SecretRotationHistory.status == RotationStatus.FAILED,
                SecretRotationHistory.started_at >= datetime.utcnow() - timedelta(hours=24),
            )
            .count()
        )

        # Check for active grace periods
        active_grace_periods = (
            db.query(SecretRotationHistory)
            .filter(SecretRotationHistory.status == RotationStatus.GRACE_PERIOD)
            .count()
        )

        # Check for grace periods expiring soon (< 6 hours)
        expiring_soon = (
            db.query(SecretRotationHistory)
            .filter(
                SecretRotationHistory.status == RotationStatus.GRACE_PERIOD,
                SecretRotationHistory.grace_period_ends <= datetime.utcnow() + timedelta(hours=6),
            )
            .count()
        )

        # Check for overdue rotations
        service = SecretRotationService(db)
        import asyncio
        rotation_status = asyncio.run(service.check_rotation_due())
        overdue_rotations = [
            secret_type.value
            for secret_type, status in rotation_status.items()
            if status.get("due") and status.get("days_until_due", 0) < 0
        ]

        # Calculate health status
        health_status = "healthy"
        issues = []

        if failed_rotations > 0:
            health_status = "degraded"
            issues.append(f"{failed_rotations} failed rotations in last 24 hours")

        if len(overdue_rotations) > 0:
            health_status = "degraded"
            issues.append(f"{len(overdue_rotations)} overdue rotations")

        if expiring_soon > 0:
            issues.append(f"{expiring_soon} grace periods expiring within 6 hours")

        # Send alert if unhealthy
        if health_status != "healthy":
            logger.warning(
                f"Secret rotation health check: {health_status}",
                extra={"issues": issues},
            )
            # TODO: Send alert via notification service

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health_status": health_status,
            "failed_rotations_24h": failed_rotations,
            "active_grace_periods": active_grace_periods,
            "grace_periods_expiring_soon": expiring_soon,
            "overdue_rotations": overdue_rotations,
            "issues": issues,
        }

    except Exception as e:
        logger.error(f"Rotation health check failed: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.security.rotation_tasks.emergency_rotate_all",
)
def emergency_rotate_all(
    self,
    reason: str,
    initiated_by: str | None = None,
) -> dict:
    """
    Emergency rotation of all rotatable secrets.

    Used in case of security breach or compromise.
    Should only be triggered manually with proper authorization.

    Args:
        reason: Reason for emergency rotation
        initiated_by: User ID who authorized the rotation

    Returns:
        Dictionary with rotation results for all secrets
    """
    logger.critical(
        f"EMERGENCY ROTATION INITIATED: {reason} "
        f"(authorized by: {initiated_by or 'automated'})"
    )

    db = get_db_session()
    try:
        service = SecretRotationService(db)
        results = {}

        # Rotate all auto-rotatable secrets
        for secret_type, config in service.DEFAULT_CONFIGS.items():
            if not config.auto_rotate:
                # Skip secrets that can't be auto-rotated (e.g., database passwords)
                logger.info(
                    f"Skipping {secret_type.value} (requires manual rotation)"
                )
                results[secret_type.value] = {
                    "skipped": True,
                    "reason": "requires_manual_rotation",
                }
                continue

            try:
                logger.warning(f"Emergency rotating {secret_type.value}")

                initiated_by_uuid = UUID(initiated_by) if initiated_by else None

                import asyncio
                result = asyncio.run(service.rotate_secret(
                    secret_type=secret_type,
                    initiated_by=initiated_by_uuid,
                    reason=f"EMERGENCY: {reason}",
                    force=True,
                ))

                results[secret_type.value] = {
                    "success": result.success,
                    "rotation_id": str(result.rotation_id),
                    "grace_period_ends": (
                        result.grace_period_ends.isoformat()
                        if result.grace_period_ends
                        else None
                    ),
                    "error": result.error_message,
                }

            except Exception as e:
                logger.error(
                    f"Emergency rotation failed for {secret_type.value}: {e}",
                    exc_info=True,
                )
                results[secret_type.value] = {
                    "success": False,
                    "error": str(e),
                }

        # Count successes and failures
        successful = len([r for r in results.values() if r.get("success")])
        failed = len([r for r in results.values() if r.get("success") == False])

        logger.critical(
            f"Emergency rotation completed: {successful} successful, {failed} failed"
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "initiated_by": initiated_by,
            "successful_rotations": successful,
            "failed_rotations": failed,
            "results": results,
        }

    except Exception as e:
        logger.critical(f"Emergency rotation FAILED: {e}", exc_info=True)
        raise
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.security.rotation_tasks.cleanup_old_rotation_history",
    max_retries=2,
)
def cleanup_old_rotation_history(
    self,
    retention_days: int = 730,  # 2 years
) -> dict:
    """
    Clean up old rotation history records.

    Runs monthly on the 1st at 2 AM (configured in celery_app.py).

    Args:
        retention_days: Number of days to retain rotation history

    Returns:
        Dictionary with cleanup results
    """
    logger.info(f"Cleaning up rotation history older than {retention_days} days")

    db = get_db_session()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Delete old rotation records
        deleted_count = (
            db.query(SecretRotationHistory)
            .filter(SecretRotationHistory.started_at < cutoff_date)
            .delete(synchronize_session=False)
        )

        db.commit()

        logger.info(f"Cleaned up {deleted_count} old rotation records")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
            "records_deleted": deleted_count,
        }

    except Exception as e:
        logger.error(f"Rotation history cleanup failed: {e}", exc_info=True)
        db.rollback()
        raise self.retry(exc=e)
    finally:
        db.close()
