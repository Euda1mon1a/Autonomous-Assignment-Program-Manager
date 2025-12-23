"""Backup and restore system for schedule data.

This module provides comprehensive backup, restore, and scheduling capabilities
for the Autonomous Assignment Program Manager.

Features:
- Full and incremental backups
- Date range snapshots
- Restore with preview and validation
- Rollback capability
- Automated scheduling (daily/weekly)
- Retention policies
- JSON format with optional compression

Example usage:
    from app.maintenance import quick_backup, quick_restore
    from app.db.session import SessionLocal

    # Create a quick backup
    db = SessionLocal()
    backup_id = quick_backup(db)

    # Restore from backup
    result = quick_restore(db, backup_id)
"""

from datetime import date
from typing import Any

from sqlalchemy.orm import Session


# Custom Exceptions
class MaintenanceError(Exception):
    """Base exception for all maintenance module errors."""

    pass


class BackupError(MaintenanceError):
    """Base exception for backup-related errors."""

    pass


class BackupCreationError(BackupError):
    """Raised when backup creation fails."""

    pass


class BackupReadError(BackupError):
    """Raised when reading a backup file fails."""

    pass


class BackupWriteError(BackupError):
    """Raised when writing a backup file fails."""

    pass


class BackupNotFoundError(BackupError):
    """Raised when a requested backup cannot be found."""

    pass


class BackupValidationError(BackupError):
    """Raised when backup validation fails."""

    pass


class BackupPermissionError(BackupError):
    """Raised when backup operation lacks necessary permissions."""

    pass


class BackupStorageError(BackupError):
    """Raised when there are storage issues (e.g., disk space)."""

    pass


class RestoreError(MaintenanceError):
    """Base exception for restore-related errors."""

    pass


class RestoreValidationError(RestoreError):
    """Raised when restore validation fails."""

    pass


class RestoreDataError(RestoreError):
    """Raised when restore data is corrupted or invalid."""

    pass


class RestorePermissionError(RestoreError):
    """Raised when restore operation lacks necessary permissions."""

    pass


class RestoreRollbackError(RestoreError):
    """Raised when restore rollback operation fails."""

    pass


class SchedulerError(MaintenanceError):
    """Base exception for scheduler-related errors."""

    pass


class ScheduleConfigurationError(SchedulerError):
    """Raised when schedule configuration is invalid."""

    pass


class ScheduleExecutionError(SchedulerError):
    """Raised when scheduled backup execution fails."""

    pass


from app.maintenance.backup import BackupService
from app.maintenance.restore import RestoreService
from app.maintenance.scheduler import BackupScheduler

__all__ = [
    "BackupService",
    "RestoreService",
    "BackupScheduler",
    "quick_backup",
    "quick_restore",
    # Exceptions
    "MaintenanceError",
    "BackupError",
    "BackupCreationError",
    "BackupReadError",
    "BackupWriteError",
    "BackupNotFoundError",
    "BackupValidationError",
    "BackupPermissionError",
    "BackupStorageError",
    "RestoreError",
    "RestoreValidationError",
    "RestoreDataError",
    "RestorePermissionError",
    "RestoreRollbackError",
    "SchedulerError",
    "ScheduleConfigurationError",
    "ScheduleExecutionError",
]


def quick_backup(
    db: Session,
    backup_type: str = "full",
    compress: bool = True,
    backup_dir: str = "backups",
) -> str:
    """
    Convenience function to quickly create a backup.

    Args:
        db: Database session
        backup_type: Type of backup ('full' or 'incremental')
        compress: Whether to compress the backup
        backup_dir: Directory to store backups

    Returns:
        Backup ID (UUID string)

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> backup_id = quick_backup(db)
        >>> print(f"Backup created: {backup_id}")
    """
    service = BackupService(db, backup_dir)
    metadata = service.create_backup(backup_type=backup_type, compress=compress)
    return metadata["backup_id"]


def quick_restore(
    db: Session,
    backup_id: str,
    mode: str = "replace",
    dry_run: bool = False,
    backup_dir: str = "backups",
) -> dict[str, Any]:
    """
    Convenience function to quickly restore from a backup.

    Args:
        db: Database session
        backup_id: ID of the backup to restore
        mode: Restore mode ('replace' or 'merge')
        dry_run: If True, preview without making changes
        backup_dir: Directory containing backups

    Returns:
        Restore result dictionary

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> # Preview restore
        >>> preview = quick_restore(db, backup_id, dry_run=True)
        >>> # Actually restore
        >>> result = quick_restore(db, backup_id)
        >>> if result['success']:
        ...     print("Restore completed successfully")
    """
    service = RestoreService(db, backup_dir)
    options = {"mode": mode, "dry_run": dry_run}
    return service.restore_from_backup(backup_id, options)


def create_schedule_snapshot(
    db: Session, start_date: date, end_date: date, backup_dir: str = "backups"
) -> str:
    """
    Convenience function to create a snapshot of a specific date range.

    Args:
        db: Database session
        start_date: Start date of the snapshot
        end_date: End date of the snapshot
        backup_dir: Directory to store backups

    Returns:
        Backup ID (UUID string)

    Example:
        >>> from datetime import date
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> backup_id = create_schedule_snapshot(
        ...     db,
        ...     date(2024, 1, 1),
        ...     date(2024, 3, 31)
        ... )
    """
    service = BackupService(db, backup_dir)
    metadata = service.create_schedule_snapshot(start_date, end_date)
    return metadata["backup_id"]


def list_all_backups(db: Session, backup_dir: str = "backups") -> list:
    """
    Convenience function to list all available backups.

    Args:
        db: Database session
        backup_dir: Directory containing backups

    Returns:
        List of backup metadata dictionaries

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> backups = list_all_backups(db)
        >>> for backup in backups:
        ...     print(f"{backup['backup_id']}: {backup['timestamp']}")
    """
    service = BackupService(db, backup_dir)
    return service.list_backups()


def setup_daily_backup(
    db: Session, hour: int = 2, minute: int = 0, backup_dir: str = "backups"
) -> dict[str, Any]:
    """
    Convenience function to set up daily automated backups.

    Args:
        db: Database session
        hour: Hour of day (0-23) to run backup (default: 2 AM)
        minute: Minute of hour (0-59) to run backup (default: 0)
        backup_dir: Directory to store backups

    Returns:
        Schedule configuration dictionary

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> # Schedule daily backup at 3 AM
        >>> config = setup_daily_backup(db, hour=3, minute=0)
    """
    from datetime import time

    scheduler = BackupScheduler(db, backup_dir)
    backup_time = time(hour=hour, minute=minute)
    return scheduler.schedule_daily_backup(backup_time)


def setup_weekly_backup(
    db: Session,
    day: int = 6,
    hour: int = 2,
    minute: int = 0,
    backup_dir: str = "backups",
) -> dict[str, Any]:
    """
    Convenience function to set up weekly automated backups.

    Args:
        db: Database session
        day: Day of week (0=Monday, 6=Sunday) to run backup
        hour: Hour of day (0-23) to run backup (default: 2 AM)
        minute: Minute of hour (0-59) to run backup (default: 0)
        backup_dir: Directory to store backups

    Returns:
        Schedule configuration dictionary

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> # Schedule weekly backup on Sunday at 2 AM
        >>> config = setup_weekly_backup(db, day=6, hour=2)
    """
    from datetime import time

    scheduler = BackupScheduler(db, backup_dir)
    backup_time = time(hour=hour, minute=minute)
    return scheduler.schedule_weekly_backup(day, backup_time)
