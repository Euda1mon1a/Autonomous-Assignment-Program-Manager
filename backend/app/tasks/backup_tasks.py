"""
Celery Tasks for Backup Automation.

This module provides background tasks for automated database backups,
including scheduled backups, verification, and cleanup.

Scheduled Tasks:
--------------
- Daily full backup at 1 AM
- Hourly incremental backup (business hours)
- Weekly backup verification on Sunday at 5 AM
- Monthly backup cleanup on 1st at 4 AM

Task Configuration:
-----------------
Tasks are configured in periodic_tasks.py and registered with Celery Beat.
Backup settings can be configured via environment variables.

Usage:
-----
    # Trigger manual full backup
    from app.tasks.backup_tasks import create_full_backup
    task = create_full_backup.delay()

    # Trigger incremental backup
    from app.tasks.backup_tasks import create_incremental_backup
    task = create_incremental_backup.delay()

    # Verify all backups
    from app.tasks.backup_tasks import verify_all_backups
    task = verify_all_backups.delay()

Environment Variables:
--------------------
- BACKUP_ENABLED: Enable/disable automated backups (default: True)
- BACKUP_STORAGE_BACKEND: Storage backend ('local' or 's3')
- BACKUP_RETENTION_DAYS: Days to retain backups (default: 30)
- BACKUP_INCREMENTAL_ENABLED: Enable incremental backups (default: True)
- BACKUP_LOCAL_DIR: Local storage directory
- BACKUP_S3_BUCKET: S3 bucket name
- BACKUP_S3_REGION: S3 region
- BACKUP_S3_ACCESS_KEY: AWS access key
- BACKUP_S3_SECRET_KEY: AWS secret key
"""

import asyncio
import logging
from datetime import datetime
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
    name="app.tasks.backup_tasks.create_full_backup",
    max_retries=3,
    default_retry_delay=600,  # 10 minutes
)
def create_full_backup(
    self,
    compression_enabled: bool = True,
) -> dict[str, Any]:
    """
    Create a full database backup.

    This task creates a complete snapshot of all database tables.
    Suitable for daily backups or as a base for incremental backups.

    Args:
        compression_enabled: Enable gzip compression (default: True)

    Returns:
        dict: Backup operation result with backup_id and statistics

    Raises:
        Exception: If backup fails (will retry up to max_retries)
    """
    from app.backup.service import BackupService
    from app.core.config import get_settings

    settings = get_settings()

    # Check if backups are enabled
    backup_enabled = getattr(settings, "BACKUP_ENABLED", True)
    if not backup_enabled:
        logger.info("Backups are disabled in settings")
        return {
            "status": "skipped",
            "message": "Backups are disabled in settings",
            "completed_at": datetime.utcnow().isoformat(),
        }

    logger.info("Starting scheduled full backup")

    db = get_db_session()

    try:
        # Create backup service
        backup_service = BackupService(
            compression_enabled=compression_enabled,
        )

        # Create full backup (async operation wrapped in sync task)
        loop = asyncio.get_event_loop()
        backup_id = loop.run_until_complete(
            backup_service.create_backup(db, strategy="full")
        )

        # Get backup info
        backup_info = backup_service.get_backup_info(backup_id)

        logger.info(
            f"Full backup created successfully: {backup_id} "
            f"({backup_info.get('size_bytes', 0) / 1024 / 1024:.2f} MB)"
        )

        return {
            "status": "success",
            "backup_id": backup_id,
            "backup_type": "full",
            "size_bytes": backup_info.get("size_bytes", 0),
            "size_mb": backup_info.get("size_bytes", 0) / 1024 / 1024,
            "table_count": backup_info.get("table_count", 0),
            "total_rows": backup_info.get("total_rows", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Full backup failed: {e}", exc_info=True)
        # Retry task
        raise self.retry(exc=e)

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.backup_tasks.create_incremental_backup",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def create_incremental_backup(
    self,
    compression_enabled: bool = True,
) -> dict[str, Any]:
    """
    Create an incremental database backup.

    This task backs up only data that changed since the last backup.
    Requires a previous backup (full or incremental) to exist.

    Args:
        compression_enabled: Enable gzip compression (default: True)

    Returns:
        dict: Backup operation result with backup_id and statistics

    Raises:
        Exception: If backup fails (will retry up to max_retries)
    """
    from app.backup.service import BackupService
    from app.core.config import get_settings

    settings = get_settings()

    # Check if backups are enabled
    backup_enabled = getattr(settings, "BACKUP_ENABLED", True)
    incremental_enabled = getattr(settings, "BACKUP_INCREMENTAL_ENABLED", True)

    if not backup_enabled:
        logger.info("Backups are disabled in settings")
        return {
            "status": "skipped",
            "message": "Backups are disabled in settings",
            "completed_at": datetime.utcnow().isoformat(),
        }

    if not incremental_enabled:
        logger.info("Incremental backups are disabled in settings")
        return {
            "status": "skipped",
            "message": "Incremental backups are disabled in settings",
            "completed_at": datetime.utcnow().isoformat(),
        }

    logger.info("Starting scheduled incremental backup")

    db = get_db_session()

    try:
        # Create backup service
        backup_service = BackupService(
            compression_enabled=compression_enabled,
        )

        # Check if a base backup exists
        backups = backup_service.list_backups(limit=1)
        if not backups:
            logger.warning(
                "No previous backup found for incremental backup. "
                "Creating a full backup instead."
            )
            # Delegate to full backup task
            return create_full_backup.apply().get()

        # Create incremental backup
        loop = asyncio.get_event_loop()
        backup_id = loop.run_until_complete(
            backup_service.create_backup(db, strategy="incremental")
        )

        # Get backup info
        backup_info = backup_service.get_backup_info(backup_id)

        logger.info(
            f"Incremental backup created successfully: {backup_id} "
            f"({backup_info.get('size_bytes', 0) / 1024 / 1024:.2f} MB, "
            f"{backup_info.get('total_rows', 0)} changes)"
        )

        return {
            "status": "success",
            "backup_id": backup_id,
            "backup_type": "incremental",
            "size_bytes": backup_info.get("size_bytes", 0),
            "size_mb": backup_info.get("size_bytes", 0) / 1024 / 1024,
            "table_count": backup_info.get("table_count", 0),
            "total_changes": backup_info.get("total_rows", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }

    except ValueError as e:
        # No base backup - this is expected, create a full backup instead
        if "requires a previous" in str(e).lower():
            logger.warning(
                f"Incremental backup requires base backup: {e}. "
                f"Creating full backup instead."
            )
            return create_full_backup.apply().get()
        else:
            logger.error(f"Incremental backup failed: {e}", exc_info=True)
            raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"Incremental backup failed: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.backup_tasks.cleanup_old_backups",
    max_retries=2,
    default_retry_delay=300,
)
def cleanup_old_backups(
    self,
    retention_days: int | None = None,
    keep_minimum: int = 5,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Clean up backups older than retention period.

    Implements retention policy:
    - Delete backups older than retention_days
    - Always keep at least keep_minimum recent backups
    - Keep at least one full backup per week for older backups

    Args:
        retention_days: Days to retain backups (uses config if None)
        keep_minimum: Minimum number of backups to keep
        dry_run: If True, only report what would be deleted

    Returns:
        dict: Cleanup operation result

    Raises:
        Exception: If cleanup fails (will retry)
    """
    from app.backup.service import BackupService
    from app.core.config import get_settings

    logger.info(
        f"Starting backup cleanup task "
        f"(retention_days={retention_days}, dry_run={dry_run})"
    )

    try:
        # Get retention period from config if not specified
        if retention_days is None:
            settings = get_settings()
            retention_days = getattr(settings, "BACKUP_RETENTION_DAYS", 30)

        # Create backup service
        backup_service = BackupService()

        # Cleanup old backups
        deleted_count = backup_service.cleanup_old_backups(
            retention_days=retention_days,
            keep_minimum=keep_minimum,
            dry_run=dry_run,
        )

        logger.info(
            f"Backup cleanup complete: "
            f"{'Would delete' if dry_run else 'Deleted'} {deleted_count} backups"
        )

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "retention_days": retention_days,
            "keep_minimum": keep_minimum,
            "dry_run": dry_run,
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="app.tasks.backup_tasks.verify_all_backups",
    max_retries=2,
    default_retry_delay=600,
)
def verify_all_backups(
    self,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Verify integrity of all backups.

    Checks checksums and ensures backups are readable.

    Args:
        limit: Maximum number of backups to verify

    Returns:
        dict: Verification results

    Raises:
        Exception: If verification fails (will retry)
    """
    from app.backup.service import BackupService

    logger.info(f"Verifying all backups (limit={limit})")

    try:
        # Create backup service
        backup_service = BackupService()

        # Get all backups
        backups = backup_service.list_backups(limit=limit)

        verified_count = 0
        error_count = 0
        errors = []

        for backup in backups:
            backup_id = backup["backup_id"]
            backup_type = backup.get("backup_type", "full")

            try:
                # Verify backup
                is_valid = backup_service.verify_backup(backup_id)

                if is_valid:
                    verified_count += 1
                    logger.debug(f"Verified backup: {backup_id}")
                else:
                    error_count += 1
                    error_msg = (
                        f"Backup {backup_id} ({backup_type}): Verification failed"
                    )
                    errors.append(error_msg)
                    logger.error(error_msg)

            except Exception as e:
                error_count += 1
                error_msg = f"Backup {backup_id} ({backup_type}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(
            f"Backup verification complete: {verified_count} verified, "
            f"{error_count} errors"
        )

        return {
            "status": "success",
            "total_backups": len(backups),
            "verified_count": verified_count,
            "error_count": error_count,
            "errors": errors[:10],  # Limit to first 10 errors
            "completed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Backup verification failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="app.tasks.backup_tasks.generate_backup_report",
    max_retries=2,
    default_retry_delay=600,
)
def generate_backup_report(self) -> dict[str, Any]:
    """
    Generate comprehensive backup status report.

    Provides statistics about all backups including count, size,
    types, and verification status.

    Returns:
        dict: Backup report data

    Raises:
        Exception: If report generation fails (will retry)
    """
    from app.backup.service import BackupService

    logger.info("Generating backup status report")

    try:
        # Create backup service
        backup_service = BackupService()

        # Get backup statistics
        stats = backup_service.get_backup_statistics()

        # Add task metadata
        stats["task_id"] = self.request.id
        stats["status"] = "success"
        stats["generated_at"] = datetime.utcnow().isoformat()

        logger.info(
            f"Backup report generated: {stats.get('total_count', 0)} backups, "
            f"{stats.get('total_size_mb', 0):.2f} MB total"
        )

        return stats

    except Exception as e:
        logger.error(f"Backup report generation failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="app.tasks.backup_tasks.verify_backup_chain",
    max_retries=2,
    default_retry_delay=300,
)
def verify_backup_chain(
    self,
    backup_id: str,
) -> dict[str, Any]:
    """
    Verify that a backup and its dependencies are intact.

    For incremental backups, verifies the entire chain from base full backup
    through all incrementals.

    Args:
        backup_id: Backup identifier to verify

    Returns:
        dict: Validation results

    Raises:
        Exception: If verification fails (will retry)
    """
    from app.backup.restore import RestoreService

    logger.info(f"Verifying backup chain for: {backup_id}")

    try:
        # Create restore service
        restore_service = RestoreService()

        # Validate backup chain
        result = restore_service.validate_backup_chain(backup_id)

        # Add task metadata
        result["task_id"] = self.request.id
        result["verified_at"] = datetime.utcnow().isoformat()

        logger.info(
            f"Backup chain verification complete: "
            f"{'VALID' if result.get('all_valid') else 'INVALID'}"
        )

        return result

    except Exception as e:
        logger.error(f"Backup chain verification failed: {e}", exc_info=True)
        raise self.retry(exc=e)


# Celery beat schedule for backup tasks
BACKUP_TASKS_BEAT_SCHEDULE = {
    # Daily full backup at 1 AM
    "backup-full-daily": {
        "task": "app.tasks.backup_tasks.create_full_backup",
        "schedule": {"hour": 1, "minute": 0},
        "kwargs": {
            "compression_enabled": True,
        },
        "options": {
            "queue": "backup",
            "expires": 7200,  # 2 hours
        },
    },
    # Hourly incremental backup during business hours (8 AM - 6 PM)
    "backup-incremental-hourly": {
        "task": "app.tasks.backup_tasks.create_incremental_backup",
        "schedule": {"hour": "8-18", "minute": 0, "day_of_week": "1-5"},
        "kwargs": {
            "compression_enabled": True,
        },
        "options": {
            "queue": "backup",
            "expires": 3600,  # 1 hour
        },
    },
    # Weekly backup verification on Sunday at 5 AM
    "backup-verify-weekly": {
        "task": "app.tasks.backup_tasks.verify_all_backups",
        "schedule": {"hour": 5, "minute": 0, "day_of_week": 0},  # Sunday
        "kwargs": {
            "limit": 100,
        },
        "options": {
            "queue": "backup",
        },
    },
    # Monthly backup cleanup on 1st of month at 4 AM
    "backup-cleanup-monthly": {
        "task": "app.tasks.backup_tasks.cleanup_old_backups",
        "schedule": {"hour": 4, "minute": 0, "day_of_month": 1},
        "kwargs": {
            "retention_days": None,  # Uses config
            "keep_minimum": 5,
            "dry_run": False,
        },
        "options": {
            "queue": "backup",
        },
    },
    # Weekly backup report on Monday at 7 AM
    "backup-report-weekly": {
        "task": "app.tasks.backup_tasks.generate_backup_report",
        "schedule": {"hour": 7, "minute": 0, "day_of_week": 1},  # Monday
        "options": {
            "queue": "backup",
        },
    },
}


def get_backup_tasks_beat_schedule() -> dict:
    """
    Get Celery beat schedule for backup tasks.

    Returns:
        dict: Beat schedule configuration

    Usage:
        In celery_app.py:

        from app.tasks.backup_tasks import get_backup_tasks_beat_schedule

        celery_app.conf.beat_schedule.update(
            get_backup_tasks_beat_schedule()
        )
    """
    return BACKUP_TASKS_BEAT_SCHEDULE


# Task routing configuration
BACKUP_TASK_ROUTES = {
    "app.tasks.backup_tasks.*": {"queue": "backup"},
}


# Queue configuration
BACKUP_TASK_QUEUES = {
    "backup": {
        "exchange": "backup",
        "routing_key": "backup",
    },
}
