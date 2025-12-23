"""
Backup Service.

Main service for orchestrating backup operations including:
- Creating backups (full, incremental, differential)
- Managing backup lifecycle
- Scheduling automated backups
- Retention policy enforcement
- Backup verification

Usage:
    service = BackupService()

    # Create a full backup
    backup_id = await service.create_backup(strategy="full")

    # Create an incremental backup
    backup_id = await service.create_backup(strategy="incremental")

    # List backups
    backups = service.list_backups()

    # Delete old backups
    deleted_count = service.cleanup_old_backups(retention_days=30)
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.backup.storage import BackupStorage, get_storage_backend
from app.backup.strategies import (
    BackupStrategy,
    DifferentialBackupStrategy,
    FullBackupStrategy,
    IncrementalBackupStrategy,
)

logger = logging.getLogger(__name__)


class BackupService:
    """
    Backup service for creating and managing database backups.

    Orchestrates backup strategies and storage backends to provide
    comprehensive backup functionality.
    """

    def __init__(
        self,
        storage: BackupStorage | None = None,
        compression_enabled: bool = True,
        encryption_enabled: bool = False,
    ):
        """
        Initialize backup service.

        Args:
            storage: Storage backend (uses settings if None)
            compression_enabled: Enable gzip compression
            encryption_enabled: Enable encryption (future feature)
        """
        self.storage = storage or get_storage_backend()
        self.compression_enabled = compression_enabled
        self.encryption_enabled = encryption_enabled

        logger.info(
            f"Initialized BackupService with storage: {type(self.storage).__name__}"
        )

    async def create_backup(
        self,
        db: Session,
        strategy: str = "full",
        **kwargs,
    ) -> str:
        """
        Create a database backup.

        Args:
            db: Database session
            strategy: Backup strategy (full, incremental, differential)
            **kwargs: Strategy-specific parameters

        Returns:
            str: Backup ID

        Raises:
            ValueError: If backup creation fails
        """
        backup_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"

        logger.info(f"Creating {strategy} backup: {backup_id}")

        try:
            # Get appropriate strategy
            backup_strategy = self._get_strategy(strategy)

            # Prepare metadata
            backup_metadata = {
                "backup_id": backup_id,
                "created_at": created_at,
                "strategy": strategy,
                "compression_enabled": self.compression_enabled,
                "encryption_enabled": self.encryption_enabled,
            }

            # For incremental/differential, find last backup timestamp
            if strategy in ["incremental", "differential"]:
                last_backup = self._get_last_backup(
                    backup_type="full" if strategy == "differential" else None
                )

                if not last_backup:
                    raise ValueError(
                        f"{strategy.capitalize()} backup requires a previous "
                        f"{'full' if strategy == 'differential' else ''} backup. "
                        f"Create a full backup first."
                    )

                kwargs["last_backup_timestamp"] = last_backup["created_at"]

                if strategy == "differential":
                    kwargs["last_full_backup_timestamp"] = last_backup["created_at"]

            # Execute backup strategy
            backup_data = await backup_strategy.execute(
                db,
                backup_metadata,
                **kwargs,
            )

            # Save to storage
            self.storage.save_backup(backup_id, backup_data)

            # Verify backup
            if not self.storage.verify_backup(backup_id):
                raise ValueError("Backup verification failed")

            logger.info(
                f"Backup {backup_id} created successfully "
                f"(strategy: {strategy}, "
                f"size: {self.storage.get_backup_size(backup_id) / 1024 / 1024:.2f} MB)"
            )

            return backup_id

        except Exception as e:
            logger.error(f"Backup creation failed: {e}", exc_info=True)
            raise ValueError(f"Backup creation failed: {e}")

    def _get_strategy(self, strategy: str) -> BackupStrategy:
        """
        Get backup strategy instance.

        Args:
            strategy: Strategy name (full, incremental, differential)

        Returns:
            BackupStrategy: Strategy instance

        Raises:
            ValueError: If strategy is invalid
        """
        strategies = {
            "full": FullBackupStrategy,
            "incremental": IncrementalBackupStrategy,
            "differential": DifferentialBackupStrategy,
        }

        strategy_class = strategies.get(strategy.lower())

        if not strategy_class:
            raise ValueError(
                f"Invalid backup strategy: {strategy}. "
                f"Must be one of: {', '.join(strategies.keys())}"
            )

        return strategy_class()

    def _get_last_backup(self, backup_type: str | None = None) -> dict[str, Any] | None:
        """
        Get the most recent backup.

        Args:
            backup_type: Filter by backup type (full, incremental, differential)

        Returns:
            dict: Backup metadata or None if no backups exist
        """
        backups = self.storage.list_backups(backup_type=backup_type, limit=1)

        if not backups:
            return None

        return backups[0]

    def list_backups(
        self,
        backup_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List available backups.

        Args:
            backup_type: Filter by backup type
            limit: Maximum number of backups to return

        Returns:
            list: List of backup metadata dictionaries
        """
        return self.storage.list_backups(backup_type=backup_type, limit=limit)

    def get_backup_info(self, backup_id: str) -> dict[str, Any]:
        """
        Get information about a specific backup.

        Args:
            backup_id: Backup identifier

        Returns:
            dict: Backup information including size, type, timestamp

        Raises:
            ValueError: If backup not found
        """
        try:
            # Find backup in list
            all_backups = self.storage.list_backups(limit=1000)

            for backup in all_backups:
                if backup["backup_id"] == backup_id:
                    # Add verification status
                    backup["verified"] = self.storage.verify_backup(backup_id)
                    return backup

            raise ValueError(f"Backup {backup_id} not found")

        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            raise ValueError(f"Error getting backup info: {e}")

    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity.

        Args:
            backup_id: Backup identifier

        Returns:
            bool: True if backup is valid

        Raises:
            ValueError: If verification fails
        """
        return self.storage.verify_backup(backup_id)

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a specific backup.

        Args:
            backup_id: Backup identifier

        Returns:
            bool: True if successful

        Raises:
            ValueError: If deletion fails
        """
        logger.info(f"Deleting backup: {backup_id}")

        try:
            result = self.storage.delete_backup(backup_id)

            logger.info(f"Backup {backup_id} deleted successfully")
            return result

        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            raise ValueError(f"Failed to delete backup: {e}")

    def cleanup_old_backups(
        self,
        retention_days: int = 30,
        keep_minimum: int = 5,
        dry_run: bool = False,
    ) -> int:
        """
        Delete backups older than retention period.

        Implements retention policy:
        - Delete backups older than retention_days
        - Always keep at least keep_minimum recent backups
        - Keep at least one full backup per week for older backups

        Args:
            retention_days: Days to retain backups
            keep_minimum: Minimum number of backups to keep
            dry_run: If True, only report what would be deleted

        Returns:
            int: Number of backups deleted

        Raises:
            ValueError: If cleanup fails
        """
        logger.info(
            f"Starting backup cleanup (retention: {retention_days} days, "
            f"keep minimum: {keep_minimum}, dry_run: {dry_run})"
        )

        try:
            # Get all backups
            all_backups = self.storage.list_backups(limit=1000)

            # Sort by created_at descending (newest first)
            all_backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            deleted_count = 0
            kept_full_backups = set()

            for i, backup in enumerate(all_backups):
                backup_id = backup["backup_id"]
                backup_type = backup.get("backup_type", "full")
                created_at = datetime.fromisoformat(
                    backup["created_at"].replace("Z", "")
                )

                # Always keep minimum number of recent backups
                if i < keep_minimum:
                    logger.debug(
                        f"Keeping recent backup {backup_id} "
                        f"(within minimum {keep_minimum})"
                    )
                    continue

                # Keep backups within retention period
                if created_at >= cutoff_date:
                    logger.debug(
                        f"Keeping backup {backup_id} (within retention period)"
                    )
                    continue

                # For old backups, keep one full backup per week
                if backup_type == "full":
                    week_key = created_at.strftime("%Y-W%W")

                    if week_key not in kept_full_backups:
                        kept_full_backups.add(week_key)
                        logger.debug(
                            f"Keeping full backup {backup_id} "
                            f"(weekly retention: {week_key})"
                        )
                        continue

                # Delete this backup
                logger.info(
                    f"{'[DRY RUN] Would delete' if dry_run else 'Deleting'} "
                    f"backup {backup_id} (created: {created_at.isoformat()})"
                )

                if not dry_run:
                    self.storage.delete_backup(backup_id)

                deleted_count += 1

            logger.info(
                f"Backup cleanup complete: "
                f"{'Would delete' if dry_run else 'Deleted'} {deleted_count} backups"
            )

            return deleted_count

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}", exc_info=True)
            raise ValueError(f"Backup cleanup failed: {e}")

    def get_backup_statistics(self) -> dict[str, Any]:
        """
        Get statistics about all backups.

        Returns:
            dict: Statistics including count, size, oldest, newest
        """
        try:
            all_backups = self.storage.list_backups(limit=1000)

            if not all_backups:
                return {
                    "total_count": 0,
                    "total_size_bytes": 0,
                    "total_size_mb": 0.0,
                    "by_type": {},
                    "oldest_backup": None,
                    "newest_backup": None,
                }

            # Calculate statistics
            total_size = sum(b.get("size_bytes", 0) for b in all_backups)
            by_type = {}

            for backup in all_backups:
                backup_type = backup.get("backup_type", "full")
                if backup_type not in by_type:
                    by_type[backup_type] = {"count": 0, "size_bytes": 0}

                by_type[backup_type]["count"] += 1
                by_type[backup_type]["size_bytes"] += backup.get("size_bytes", 0)

            # Sort by created_at
            sorted_backups = sorted(all_backups, key=lambda x: x.get("created_at", ""))

            return {
                "total_count": len(all_backups),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / 1024 / 1024,
                "by_type": by_type,
                "oldest_backup": sorted_backups[0]["created_at"],
                "newest_backup": sorted_backups[-1]["created_at"],
            }

        except Exception as e:
            logger.error(f"Error calculating backup statistics: {e}")
            return {
                "error": str(e),
                "total_count": 0,
                "total_size_bytes": 0,
            }
