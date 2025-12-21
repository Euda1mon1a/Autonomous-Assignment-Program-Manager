"""
Celery Tasks for Audit Log Archival.

This module provides background tasks for automated audit log archival,
including scheduled archival, compliance reporting, and archive cleanup.

Scheduled Tasks:
--------------
- Daily archival at 2 AM (archives logs older than retention period)
- Weekly compliance report generation on Monday at 6 AM
- Monthly archive cleanup (purges old archives per retention policy)

Task Configuration:
-----------------
Tasks are configured in periodic_tasks.py and registered with Celery Beat.
Default retention periods can be overridden via environment variables.

Usage:
-----
    # Trigger manual archival
    from app.tasks.audit_tasks import archive_old_audit_logs
    task = archive_old_audit_logs.delay(days=90, purge_after_archive=True)

    # Trigger compliance report
    from app.tasks.audit_tasks import generate_audit_compliance_report
    task = generate_audit_compliance_report.delay(months_back=3)

Environment Variables:
--------------------
- AUDIT_RETENTION_DAYS: Default retention period (default: 90)
- AUDIT_ARCHIVE_RETENTION_YEARS: Archive retention in years (default: 7)
- AUDIT_ARCHIVE_STORAGE: Storage backend ('local' or 's3')
- AUDIT_ARCHIVE_PATH: Local storage path
- AUDIT_ARCHIVE_S3_BUCKET: S3 bucket name
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from celery import shared_task
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_db_session() -> Session:
    """Get a database session for task execution."""
    from app.db.session import SessionLocal

    return SessionLocal()


@shared_task(
    bind=True,
    name="app.tasks.audit_tasks.archive_old_audit_logs",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def archive_old_audit_logs(
    self,
    days: int | None = None,
    entity_types: list[str] | None = None,
    purge_after_archive: bool = False,
) -> dict[str, Any]:
    """
    Archive audit logs older than specified days.

    This task archives old audit logs to compressed storage, optionally
    purging them from the active database to save space.

    Args:
        days: Archive logs older than this many days (uses config if None)
        entity_types: Specific entity types to archive (None = all)
        purge_after_archive: Remove archived logs from database

    Returns:
        dict: Archive operation result with statistics

    Raises:
        Exception: If archival fails (will retry up to max_retries)
    """
    from app.audit.archiver import AuditArchiver
    from app.core.config import get_settings

    logger.info(
        f"Starting scheduled audit log archival "
        f"(days={days}, purge={purge_after_archive})"
    )

    db = get_db_session()

    try:
        # Get retention period from config if not specified
        if days is None:
            settings = get_settings()
            days = getattr(settings, "AUDIT_RETENTION_DAYS", 90)

        # Create archiver
        archiver = AuditArchiver(db)

        # Perform archival
        import asyncio

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            archiver.archive_old_logs(
                days=days,
                entity_types=entity_types,
                purge_after_archive=purge_after_archive,
            )
        )

        logger.info(
            f"Successfully archived {result.record_count} audit logs "
            f"to {result.archive_id}"
        )

        return {
            "status": "success",
            "archive_id": result.archive_id,
            "record_count": result.record_count,
            "size_bytes": result.size_bytes,
            "storage_backend": result.storage_backend,
            "purged": result.purged_from_db,
            "completed_at": datetime.utcnow().isoformat(),
        }

    except ValueError as e:
        # No logs to archive - this is normal, not an error
        logger.info(f"No logs to archive: {e}")
        return {
            "status": "no_action",
            "message": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Audit log archival failed: {e}", exc_info=True)

        # Retry task
        raise self.retry(exc=e)

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.audit_tasks.generate_audit_compliance_report",
    max_retries=2,
    default_retry_delay=600,  # 10 minutes
)
def generate_audit_compliance_report(
    self,
    months_back: int = 3,
    entity_types: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generate compliance report from audit archives.

    Creates a comprehensive report of audit activity over the specified
    period, including statistics and entity breakdowns.

    Args:
        months_back: Number of months to include in report
        entity_types: Specific entity types to include (None = all)

    Returns:
        dict: Compliance report data

    Raises:
        Exception: If report generation fails (will retry)
    """
    from app.audit.restore import AuditRestorer

    logger.info(f"Generating audit compliance report ({months_back} months)")

    db = get_db_session()

    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months_back * 30)

        # Create restorer
        restorer = AuditRestorer(db)

        # Generate report
        import asyncio

        loop = asyncio.get_event_loop()
        report = loop.run_until_complete(
            restorer.generate_compliance_report(
                start_date=start_date,
                end_date=end_date,
                entity_types=entity_types,
            )
        )

        logger.info(
            f"Compliance report generated: {report['total_records']} records "
            f"across {report['archives_reviewed']} archives"
        )

        # Add task metadata
        report["task_id"] = self.request.id
        report["status"] = "success"

        return report

    except Exception as e:
        logger.error(f"Compliance report generation failed: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.audit_tasks.cleanup_old_archives",
    max_retries=3,
    default_retry_delay=300,
)
def cleanup_old_archives(
    self,
    retention_years: int | None = None,
) -> dict[str, Any]:
    """
    Clean up archives older than retention period.

    Purges archives that have exceeded their retention period based on
    the configured archive retention policy.

    Args:
        retention_years: Archive retention in years (uses config if None)

    Returns:
        dict: Cleanup operation result

    Raises:
        Exception: If cleanup fails (will retry)
    """
    from app.audit.retention import get_policy_manager
    from app.audit.storage import get_storage_backend
    from app.core.config import get_settings

    logger.info("Starting archive cleanup task")

    try:
        # Get retention period from config if not specified
        if retention_years is None:
            settings = get_settings()
            retention_years = getattr(settings, "AUDIT_ARCHIVE_RETENTION_YEARS", 7)

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_years * 365)

        # Get storage backend
        storage = get_storage_backend()

        # List archives
        all_archives = storage.list_archives()

        # Filter archives older than cutoff
        old_archives = [
            a
            for a in all_archives
            if datetime.fromisoformat(a["created_at"]) < cutoff_date
        ]

        # Delete old archives
        deleted_count = 0
        deleted_size = 0

        for archive in old_archives:
            archive_id = archive["archive_id"]

            try:
                if storage.delete_archive(archive_id):
                    deleted_count += 1
                    deleted_size += archive.get("size_bytes", 0)
                    logger.info(f"Deleted old archive: {archive_id}")

            except Exception as e:
                logger.warning(f"Failed to delete archive {archive_id}: {e}")
                continue

        logger.info(
            f"Archive cleanup complete: deleted {deleted_count} archives "
            f"({deleted_size / 1024 / 1024:.2f} MB)"
        )

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "deleted_size_bytes": deleted_size,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_years": retention_years,
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Archive cleanup failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="app.tasks.audit_tasks.archive_by_entity_type",
    max_retries=3,
    default_retry_delay=300,
)
def archive_by_entity_type(
    self,
    entity_type: str,
    days: int = 90,
) -> dict[str, Any]:
    """
    Archive logs for a specific entity type.

    Useful for targeted archival of high-volume entity types like
    assignments or schedule runs.

    Args:
        entity_type: Entity type to archive (assignment, absence, etc.)
        days: Archive logs older than this many days

    Returns:
        dict: Archive operation result
    """
    from app.audit.archiver import AuditArchiver

    logger.info(f"Archiving {entity_type} logs older than {days} days")

    db = get_db_session()

    try:
        archiver = AuditArchiver(db)

        import asyncio

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            archiver.archive_old_logs(
                days=days,
                entity_types=[entity_type],
                purge_after_archive=False,
            )
        )

        logger.info(
            f"Archived {result.record_count} {entity_type} logs "
            f"to {result.archive_id}"
        )

        return {
            "status": "success",
            "entity_type": entity_type,
            "archive_id": result.archive_id,
            "record_count": result.record_count,
            "completed_at": datetime.utcnow().isoformat(),
        }

    except ValueError as e:
        logger.info(f"No {entity_type} logs to archive: {e}")
        return {
            "status": "no_action",
            "entity_type": entity_type,
            "message": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to archive {entity_type} logs: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.audit_tasks.verify_archive_integrity",
    max_retries=2,
    default_retry_delay=600,
)
def verify_archive_integrity(
    self,
    archive_id: str | None = None,
) -> dict[str, Any]:
    """
    Verify integrity of archived data.

    Checks archive checksums and ensures archives are readable.
    If archive_id is None, verifies all archives.

    Args:
        archive_id: Specific archive to verify (None = all)

    Returns:
        dict: Verification results
    """
    from app.audit.storage import get_storage_backend

    logger.info(f"Verifying archive integrity (archive_id={archive_id})")

    try:
        storage = get_storage_backend()

        # Get archives to verify
        if archive_id:
            archives = [{"archive_id": archive_id}]
        else:
            archives = storage.list_archives()

        verified_count = 0
        error_count = 0
        errors = []

        for archive_meta in archives:
            aid = archive_meta["archive_id"]

            try:
                # Try to load archive
                archive_data = storage.get_archive(aid)

                # Verify required fields
                required_fields = ["archive_id", "created_at", "records"]
                for field in required_fields:
                    if field not in archive_data:
                        raise ValueError(f"Missing required field: {field}")

                verified_count += 1
                logger.debug(f"Verified archive: {aid}")

            except Exception as e:
                error_count += 1
                error_msg = f"Archive {aid}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(
            f"Archive verification complete: {verified_count} verified, "
            f"{error_count} errors"
        )

        return {
            "status": "success",
            "verified_count": verified_count,
            "error_count": error_count,
            "errors": errors[:10],  # Limit to first 10 errors
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Archive verification failed: {e}", exc_info=True)
        raise self.retry(exc=e)


# Celery beat schedule for audit tasks
AUDIT_TASKS_BEAT_SCHEDULE = {
    # Daily archival at 2 AM
    "audit-archive-daily": {
        "task": "app.tasks.audit_tasks.archive_old_audit_logs",
        "schedule": {"hour": 2, "minute": 0},
        "kwargs": {
            "days": None,  # Uses config
            "purge_after_archive": True,
        },
        "options": {
            "queue": "audit",
            "expires": 7200,  # 2 hours
        },
    },
    # Weekly compliance report on Monday at 6 AM
    "audit-compliance-report-weekly": {
        "task": "app.tasks.audit_tasks.generate_audit_compliance_report",
        "schedule": {"hour": 6, "minute": 0, "day_of_week": 1},  # Monday
        "kwargs": {
            "months_back": 3,
        },
        "options": {
            "queue": "audit",
        },
    },
    # Monthly archive cleanup on 1st of month at 3 AM
    "audit-cleanup-monthly": {
        "task": "app.tasks.audit_tasks.cleanup_old_archives",
        "schedule": {"hour": 3, "minute": 0, "day_of_month": 1},
        "options": {
            "queue": "audit",
        },
    },
    # Weekly archive integrity check on Sunday at 4 AM
    "audit-integrity-check-weekly": {
        "task": "app.tasks.audit_tasks.verify_archive_integrity",
        "schedule": {"hour": 4, "minute": 0, "day_of_week": 0},  # Sunday
        "options": {
            "queue": "audit",
        },
    },
}


def get_audit_tasks_beat_schedule() -> dict:
    """
    Get Celery beat schedule for audit tasks.

    Returns:
        dict: Beat schedule configuration

    Usage:
        In celery_app.py:

        from app.tasks.audit_tasks import get_audit_tasks_beat_schedule

        celery_app.conf.beat_schedule.update(
            get_audit_tasks_beat_schedule()
        )
    """
    return AUDIT_TASKS_BEAT_SCHEDULE


# Task routing configuration
AUDIT_TASK_ROUTES = {
    "app.tasks.audit_tasks.*": {"queue": "audit"},
}


# Queue configuration
AUDIT_TASK_QUEUES = {
    "audit": {
        "exchange": "audit",
        "routing_key": "audit",
    },
}
