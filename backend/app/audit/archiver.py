"""
Audit Log Archiver Service.

This module provides the core archival functionality for audit logs,
moving old logs from the active database to compressed archive storage.

Archival Process:
---------------
1. Identify logs eligible for archival based on retention policy
2. Extract logs from version tables (SQLAlchemy-Continuum)
3. Compress and package logs into archive format
4. Store archive in configured backend (local/S3)
5. Optionally purge archived logs from active database
6. Record archive metadata for future restoration

Archive Structure:
----------------
Each archive contains:
- Archive metadata (ID, creation date, record count, date range)
- Retention policy information
- Array of audit log records with full history
- Checksum for integrity verification

Usage:
-----
    from app.audit.archiver import AuditArchiver
    from app.db.session import get_db

    db = next(get_db())
    archiver = AuditArchiver(db)

    # Archive logs older than 90 days
    result = await archiver.archive_old_logs(days=90)
    print(f"Archived {result.record_count} records")

    # Archive with custom retention policy
    from app.audit.retention import COMPLIANCE_POLICY
    result = await archiver.archive_old_logs(
        days=365,
        policy=COMPLIANCE_POLICY,
        purge_after_archive=False,
    )
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.audit.retention import RetentionPolicy, get_policy_manager
from app.audit.storage import ArchiveStorageBackend, get_storage_backend

logger = logging.getLogger(__name__)


class ArchiveResult(BaseModel):
    """Result of an archival operation."""

    archive_id: str = Field(description="Unique archive identifier")
    record_count: int = Field(description="Number of records archived")
    size_bytes: int = Field(description="Archive size in bytes")
    date_range: dict[str, str] = Field(description="Date range of archived logs")
    entity_types: list[str] = Field(description="Entity types included in archive")
    storage_backend: str = Field(description="Storage backend used")
    storage_path: str = Field(description="Storage path or key")
    checksum: str = Field(description="Archive checksum")
    created_at: str = Field(description="Archive creation timestamp")
    purged_from_db: bool = Field(
        default=False, description="Whether records were purged from database"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AuditArchiver:
    """
    Service for archiving audit logs to compressed storage.

    Manages the full archival lifecycle including:
    - Log extraction from version tables
    - Compression and packaging
    - Storage backend interaction
    - Metadata tracking
    - Optional database purging
    """

    def __init__(
        self,
        db: Session,
        storage_backend: ArchiveStorageBackend | None = None,
    ):
        """
        Initialize audit archiver.

        Args:
            db: Database session
            storage_backend: Storage backend (defaults to configured backend)
        """
        self.db = db
        self.storage_backend = storage_backend or self._get_default_storage()
        self.policy_manager = get_policy_manager()

    def _get_default_storage(self) -> ArchiveStorageBackend:
        """
        Get default storage backend from configuration.

        Returns:
            ArchiveStorageBackend: Configured storage backend
        """
        from app.core.config import get_settings

        settings = get_settings()

        backend_type = getattr(settings, "AUDIT_ARCHIVE_STORAGE", "local")
        backend_config = {}

        if backend_type == "local":
            backend_config["base_path"] = getattr(
                settings, "AUDIT_ARCHIVE_PATH", "/var/audit/archives"
            )
        elif backend_type == "s3":
            backend_config["bucket_name"] = getattr(
                settings, "AUDIT_ARCHIVE_S3_BUCKET", "audit-archives"
            )
            backend_config["region"] = getattr(
                settings, "AUDIT_ARCHIVE_S3_REGION", "us-east-1"
            )
            backend_config["access_key"] = getattr(settings, "UPLOAD_S3_ACCESS_KEY", None)
            backend_config["secret_key"] = getattr(settings, "UPLOAD_S3_SECRET_KEY", None)
            backend_config["endpoint_url"] = getattr(
                settings, "UPLOAD_S3_ENDPOINT_URL", None
            )

        return get_storage_backend(backend_type, **backend_config)

    async def archive_old_logs(
        self,
        days: int | None = None,
        entity_types: list[str] | None = None,
        policy: RetentionPolicy | None = None,
        purge_after_archive: bool = False,
        batch_size: int = 10000,
    ) -> ArchiveResult:
        """
        Archive audit logs older than specified days.

        Args:
            days: Archive logs older than this many days (uses policy if None)
            entity_types: Specific entity types to archive (None = all)
            policy: Retention policy to use (uses default if None)
            purge_after_archive: Remove archived logs from active database
            batch_size: Maximum records per archive

        Returns:
            ArchiveResult: Archive operation result

        Raises:
            ValueError: If no logs found to archive
        """
        # Determine retention policy
        if policy is None:
            policy = self.policy_manager.get_policy()

        # Calculate cutoff date
        if days is not None:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
        else:
            cutoff_date = policy.get_archive_cutoff_date()

        logger.info(
            f"Starting archival of logs older than {cutoff_date.date()} "
            f"(entity_types={entity_types})"
        )

        # Extract logs to archive
        logs_to_archive = await self._extract_logs_for_archive(
            cutoff_date=cutoff_date,
            entity_types=entity_types,
            batch_size=batch_size,
        )

        if not logs_to_archive:
            logger.warning("No logs found to archive")
            raise ValueError("No logs found to archive")

        # Create archive
        archive_id = self._generate_archive_id(cutoff_date)
        archive_data = self._build_archive_data(
            archive_id=archive_id,
            logs=logs_to_archive,
            cutoff_date=cutoff_date,
            policy=policy,
        )

        # Save to storage
        storage_result = self.storage_backend.save_archive(
            archive_id=archive_id,
            archive_data=archive_data,
            compress=policy.compress_archives,
        )

        # Optionally purge from database
        purged = False
        if purge_after_archive:
            purged = await self._purge_archived_logs(logs_to_archive)

        # Build result
        result = ArchiveResult(
            archive_id=archive_id,
            record_count=len(logs_to_archive),
            size_bytes=storage_result["size_bytes"],
            date_range={
                "start": archive_data["date_range"]["start"],
                "end": archive_data["date_range"]["end"],
            },
            entity_types=list(archive_data["entity_type_counts"].keys()),
            storage_backend=storage_result["backend"],
            storage_path=storage_result["storage_path"],
            checksum=storage_result["checksum"],
            created_at=storage_result["created_at"],
            purged_from_db=purged,
            metadata={
                "policy_level": policy.level,
                "total_size_kb": storage_result["size_bytes"] / 1024,
            },
        )

        logger.info(
            f"Successfully archived {result.record_count} records to {archive_id} "
            f"({result.size_bytes} bytes, purged={purged})"
        )

        return result

    async def archive_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_types: list[str] | None = None,
        policy: RetentionPolicy | None = None,
    ) -> ArchiveResult:
        """
        Archive audit logs within a specific date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            entity_types: Specific entity types to archive
            policy: Retention policy to use

        Returns:
            ArchiveResult: Archive operation result
        """
        if policy is None:
            policy = self.policy_manager.get_policy()

        logger.info(
            f"Archiving logs from {start_date.date()} to {end_date.date()} "
            f"(entity_types={entity_types})"
        )

        # Extract logs in date range
        logs_to_archive = await self._extract_logs_by_date_range(
            start_date=start_date,
            end_date=end_date,
            entity_types=entity_types,
        )

        if not logs_to_archive:
            raise ValueError("No logs found in date range")

        # Create archive
        archive_id = self._generate_archive_id(start_date, end_date)
        archive_data = self._build_archive_data(
            archive_id=archive_id,
            logs=logs_to_archive,
            cutoff_date=end_date,
            policy=policy,
        )

        # Save to storage
        storage_result = self.storage_backend.save_archive(
            archive_id=archive_id,
            archive_data=archive_data,
            compress=policy.compress_archives,
        )

        result = ArchiveResult(
            archive_id=archive_id,
            record_count=len(logs_to_archive),
            size_bytes=storage_result["size_bytes"],
            date_range={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            entity_types=list(archive_data["entity_type_counts"].keys()),
            storage_backend=storage_result["backend"],
            storage_path=storage_result["storage_path"],
            checksum=storage_result["checksum"],
            created_at=storage_result["created_at"],
            purged_from_db=False,
            metadata={"policy_level": policy.level},
        )

        logger.info(
            f"Successfully archived {result.record_count} records to {archive_id}"
        )

        return result

    async def _extract_logs_for_archive(
        self,
        cutoff_date: datetime,
        entity_types: list[str] | None = None,
        batch_size: int = 10000,
    ) -> list[dict[str, Any]]:
        """
        Extract audit logs from version tables for archival.

        Args:
            cutoff_date: Archive logs older than this date
            entity_types: Entity types to include (None = all)
            batch_size: Maximum records to extract

        Returns:
            list: Audit log records
        """
        # Version tables to query
        version_tables = [
            "assignment_version",
            "absence_version",
            "schedule_run_version",
            "swap_record_version",
        ]

        # Filter by entity types if specified
        if entity_types:
            entity_table_map = {
                "assignment": "assignment_version",
                "absence": "absence_version",
                "schedule_run": "schedule_run_version",
                "swap_record": "swap_record_version",
            }
            version_tables = [
                entity_table_map[et] for et in entity_types if et in entity_table_map
            ]

        all_logs = []

        for table_name in version_tables:
            try:
                # Query version table with transaction join
                query = text(f"""
                    SELECT
                        v.id as entity_id,
                        v.transaction_id,
                        v.operation_type,
                        t.issued_at,
                        t.user_id,
                        t.remote_addr
                    FROM {table_name} v
                    LEFT JOIN transaction t ON v.transaction_id = t.id
                    WHERE t.issued_at < :cutoff_date
                    ORDER BY t.issued_at ASC
                    LIMIT :batch_size
                """)

                result = self.db.execute(
                    query, {"cutoff_date": cutoff_date, "batch_size": batch_size}
                )

                for row in result:
                    # Extract entity type from table name
                    entity_type = table_name.replace("_version", "")

                    all_logs.append(
                        {
                            "entity_type": entity_type,
                            "entity_id": str(row[0]),
                            "transaction_id": row[1],
                            "operation_type": row[2],
                            "issued_at": row[3].isoformat() if row[3] else None,
                            "user_id": str(row[4]) if row[4] else None,
                            "remote_addr": row[5],
                        }
                    )

            except Exception as e:
                logger.warning(f"Error extracting from {table_name}: {e}")
                continue

        logger.info(f"Extracted {len(all_logs)} logs for archival")
        return all_logs

    async def _extract_logs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Extract audit logs within a date range.

        Args:
            start_date: Start of range
            end_date: End of range
            entity_types: Entity types to include

        Returns:
            list: Audit log records
        """
        version_tables = [
            "assignment_version",
            "absence_version",
            "schedule_run_version",
            "swap_record_version",
        ]

        if entity_types:
            entity_table_map = {
                "assignment": "assignment_version",
                "absence": "absence_version",
                "schedule_run": "schedule_run_version",
                "swap_record": "swap_record_version",
            }
            version_tables = [
                entity_table_map[et] for et in entity_types if et in entity_table_map
            ]

        all_logs = []

        for table_name in version_tables:
            try:
                query = text(f"""
                    SELECT
                        v.id as entity_id,
                        v.transaction_id,
                        v.operation_type,
                        t.issued_at,
                        t.user_id,
                        t.remote_addr
                    FROM {table_name} v
                    LEFT JOIN transaction t ON v.transaction_id = t.id
                    WHERE t.issued_at >= :start_date
                      AND t.issued_at <= :end_date
                    ORDER BY t.issued_at ASC
                """)

                result = self.db.execute(
                    query, {"start_date": start_date, "end_date": end_date}
                )

                for row in result:
                    entity_type = table_name.replace("_version", "")

                    all_logs.append(
                        {
                            "entity_type": entity_type,
                            "entity_id": str(row[0]),
                            "transaction_id": row[1],
                            "operation_type": row[2],
                            "issued_at": row[3].isoformat() if row[3] else None,
                            "user_id": str(row[4]) if row[4] else None,
                            "remote_addr": row[5],
                        }
                    )

            except Exception as e:
                logger.warning(f"Error extracting from {table_name}: {e}")
                continue

        return all_logs

    def _build_archive_data(
        self,
        archive_id: str,
        logs: list[dict[str, Any]],
        cutoff_date: datetime,
        policy: RetentionPolicy,
    ) -> dict[str, Any]:
        """
        Build archive data structure.

        Args:
            archive_id: Archive identifier
            logs: Audit log records
            cutoff_date: Cutoff date for archival
            policy: Retention policy

        Returns:
            dict: Archive data structure
        """
        # Calculate date range
        dates = [
            datetime.fromisoformat(log["issued_at"])
            for log in logs
            if log["issued_at"]
        ]
        date_range = {
            "start": min(dates).isoformat() if dates else cutoff_date.isoformat(),
            "end": max(dates).isoformat() if dates else cutoff_date.isoformat(),
        }

        # Count by entity type
        entity_type_counts = {}
        for log in logs:
            entity_type = log["entity_type"]
            entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1

        # Count by operation type
        operation_counts = {}
        operation_map = {0: "create", 1: "update", 2: "delete"}
        for log in logs:
            op = operation_map.get(log["operation_type"], "unknown")
            operation_counts[op] = operation_counts.get(op, 0) + 1

        return {
            "archive_id": archive_id,
            "created_at": datetime.utcnow().isoformat(),
            "record_count": len(logs),
            "date_range": date_range,
            "entity_type_counts": entity_type_counts,
            "operation_counts": operation_counts,
            "retention_policy": {
                "level": policy.level,
                "active_retention_days": policy.active_retention_days,
                "archive_retention_years": policy.archive_retention_years,
            },
            "cutoff_date": cutoff_date.isoformat(),
            "records": logs,
        }

    async def _purge_archived_logs(self, logs: list[dict[str, Any]]) -> bool:
        """
        Purge archived logs from active database.

        Args:
            logs: List of logs that were archived

        Returns:
            bool: True if purged successfully
        """
        try:
            # Group by entity type
            logs_by_type: dict[str, list[int]] = {}
            for log in logs:
                entity_type = log["entity_type"]
                transaction_id = log["transaction_id"]

                if entity_type not in logs_by_type:
                    logs_by_type[entity_type] = []
                logs_by_type[entity_type].append(transaction_id)

            # Delete from each version table
            for entity_type, transaction_ids in logs_by_type.items():
                table_name = f"{entity_type}_version"

                # Build delete query
                placeholders = ",".join([f":tid_{i}" for i in range(len(transaction_ids))])
                delete_query = text(
                    f"DELETE FROM {table_name} WHERE transaction_id IN ({placeholders})"
                )

                # Create params dict
                params = {f"tid_{i}": tid for i, tid in enumerate(transaction_ids)}

                self.db.execute(delete_query, params)

            self.db.commit()
            logger.info(f"Purged {len(logs)} archived logs from database")
            return True

        except Exception as e:
            logger.error(f"Failed to purge archived logs: {e}")
            self.db.rollback()
            return False

    def _generate_archive_id(
        self, cutoff_date: datetime, end_date: datetime | None = None
    ) -> str:
        """
        Generate unique archive identifier.

        Args:
            cutoff_date: Archive cutoff date
            end_date: End date (for range archives)

        Returns:
            str: Archive ID
        """
        if end_date:
            # Range-based archive
            return (
                f"archive-{cutoff_date.strftime('%Y-%m-%d')}-"
                f"to-{end_date.strftime('%Y-%m-%d')}"
            )
        else:
            # Date-based archive
            return f"archive-{cutoff_date.strftime('%Y-%m-%d')}-{uuid4().hex[:8]}"
