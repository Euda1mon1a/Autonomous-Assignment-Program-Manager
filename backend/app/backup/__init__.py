"""
Backup Automation Package.

This package provides comprehensive backup and restore functionality for the
Residency Scheduler application, including:

- Scheduled backups (daily, weekly, monthly)
- Incremental backups (only changed data)
- Full backups (complete database dump)
- Multiple storage backends (local filesystem, S3)
- Backup verification and integrity checks
- Point-in-time recovery
- Backup retention policies
- Automated cleanup of old backups

Architecture:
    - BackupService: Main service orchestrating backup operations
    - BackupStrategy: Strategy pattern for full/incremental backups
    - BackupStorage: Storage abstraction for local/S3 backends
    - RestoreService: Point-in-time recovery and restore operations
    - Celery Tasks: Automated scheduled backups

Usage:
    # Schedule a backup via Celery
    from app.tasks.backup_tasks import create_full_backup
    task = create_full_backup.delay()

    # Manual backup
    from app.backup.service import BackupService
    service = BackupService()
    backup_id = await service.create_backup(strategy="full")

    # Restore from backup
    from app.backup.restore import RestoreService
    restore = RestoreService()
    await restore.restore_from_backup(backup_id)

Configuration:
    Environment variables:
    - BACKUP_ENABLED: Enable/disable automated backups (default: True)
    - BACKUP_STORAGE_BACKEND: Storage backend (local, s3)
    - BACKUP_LOCAL_DIR: Local storage directory
    - BACKUP_S3_BUCKET: S3 bucket name
    - BACKUP_S3_REGION: S3 region
    - BACKUP_S3_ACCESS_KEY: AWS access key
    - BACKUP_S3_SECRET_KEY: AWS secret key
    - BACKUP_RETENTION_DAYS: Days to retain backups (default: 30)
    - BACKUP_INCREMENTAL_ENABLED: Enable incremental backups (default: True)
    - BACKUP_COMPRESSION_ENABLED: Enable compression (default: True)
    - BACKUP_ENCRYPTION_ENABLED: Enable encryption (default: False)
"""

from app.backup.restore import RestoreService
from app.backup.service import BackupService
from app.backup.storage import BackupStorage, LocalStorage, S3Storage
from app.backup.strategies import (
    BackupStrategy,
    FullBackupStrategy,
    IncrementalBackupStrategy,
)

__all__ = [
    "BackupService",
    "BackupStrategy",
    "FullBackupStrategy",
    "IncrementalBackupStrategy",
    "BackupStorage",
    "LocalStorage",
    "S3Storage",
    "RestoreService",
]
