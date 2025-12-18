"""
Celery Tasks for Database Cleanup Operations.

Provides automated background tasks for:
- Cleaning up expired idempotency requests
- Cleaning up expired token blacklist entries
- Timing out stale pending idempotency requests

These tasks prevent unbounded table growth and ensure
orphaned records don't block system operations.
"""

import logging
from datetime import datetime
from typing import Any

from celery import shared_task
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_db_session() -> Session:
    """Get a database session for task execution."""
    from app.core.database import SessionLocal
    return SessionLocal()


@shared_task(
    bind=True,
    name="app.tasks.cleanup_tasks.cleanup_idempotency_requests",
    max_retries=3,
    default_retry_delay=60,
)
def cleanup_idempotency_requests(
    self,
    batch_size: int = 1000,
) -> dict[str, Any]:
    """
    Clean up expired idempotency request records.

    Removes records past their expires_at timestamp to prevent
    unbounded table growth. Default expiration is 24 hours.

    Args:
        batch_size: Maximum records to delete per execution

    Returns:
        Dict with cleanup results including count deleted
    """
    logger.info("Starting idempotency request cleanup")

    db = get_db_session()
    try:
        from app.services.idempotency_service import IdempotencyService

        service = IdempotencyService(db)
        deleted = service.cleanup_expired(batch_size=batch_size)

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "task": "cleanup_idempotency_requests",
            "deleted_count": deleted,
            "batch_size": batch_size,
            "status": "completed",
        }

        logger.info(f"Idempotency cleanup complete: {deleted} records deleted")
        return result

    except Exception as exc:
        logger.exception("Idempotency cleanup failed")
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.cleanup_tasks.cleanup_token_blacklist",
    max_retries=3,
    default_retry_delay=60,
)
def cleanup_token_blacklist(self) -> dict[str, Any]:
    """
    Clean up expired token blacklist entries.

    Removes tokens past their expires_at timestamp. Tokens only
    need to remain blacklisted until their natural expiration.

    Returns:
        Dict with cleanup results including count deleted
    """
    logger.info("Starting token blacklist cleanup")

    db = get_db_session()
    try:
        from app.models.token_blacklist import TokenBlacklist

        deleted = TokenBlacklist.cleanup_expired(db)

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "task": "cleanup_token_blacklist",
            "deleted_count": deleted,
            "status": "completed",
        }

        logger.info(f"Token blacklist cleanup complete: {deleted} records deleted")
        return result

    except Exception as exc:
        logger.exception("Token blacklist cleanup failed")
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.cleanup_tasks.timeout_stale_pending_requests",
    max_retries=3,
    default_retry_delay=60,
)
def timeout_stale_pending_requests(
    self,
    timeout_minutes: int = 10,
    batch_size: int = 100,
) -> dict[str, Any]:
    """
    Mark stale pending idempotency requests as failed.

    Requests stuck in PENDING state beyond timeout_minutes are
    likely orphaned (worker crash, network timeout). Marking them
    failed allows new requests with the same idempotency key.

    Args:
        timeout_minutes: Minutes after which pending requests are stale
        batch_size: Maximum records to update per execution

    Returns:
        Dict with timeout results including count timed out
    """
    logger.info(f"Starting stale pending request timeout (threshold: {timeout_minutes}m)")

    db = get_db_session()
    try:
        from app.services.idempotency_service import IdempotencyService

        service = IdempotencyService(db)
        timed_out = service.timeout_stale_pending(
            timeout_minutes=timeout_minutes,
            batch_size=batch_size
        )

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "task": "timeout_stale_pending_requests",
            "timed_out_count": timed_out,
            "timeout_minutes": timeout_minutes,
            "batch_size": batch_size,
            "status": "completed",
        }

        if timed_out > 0:
            logger.warning(f"Timed out {timed_out} stale pending requests")
        else:
            logger.info("No stale pending requests found")

        return result

    except Exception as exc:
        logger.exception("Stale pending timeout failed")
        raise self.retry(exc=exc)
    finally:
        db.close()
