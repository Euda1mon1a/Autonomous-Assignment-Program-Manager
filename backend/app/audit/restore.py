"""
Audit Log Archive Restoration Service.

This module provides functionality to restore archived audit logs back
into the active database or query them directly from archives without restoration.

Restoration Modes:
----------------
1. Query-only: Search archives without restoring to database
2. Temporary restore: Load archive into memory for analysis
3. Full restore: Restore archive back to version tables
4. Selective restore: Restore specific records based on filters

Use Cases:
---------
- Compliance audits requiring historical data access
- Legal discovery requests
- Security incident investigation
- Data recovery after accidental purge

Usage:
-----
    from app.audit.restore import AuditRestorer
    from app.db.session import get_db

    db = next(get_db())
    restorer = AuditRestorer(db)

    # Query archive without restoration
    logs = await restorer.query_archive(
        archive_id="archive-2024-01-15",
        filters={"entity_type": "assignment"}
    )

    # Restore specific records
    result = await restorer.restore_from_archive(
        archive_id="archive-2024-01-15",
        restore_mode="selective",
        filters={"user_id": "user-123"}
    )
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.audit.storage import ArchiveStorageBackend, get_storage_backend

logger = logging.getLogger(__name__)


class RestoreResult(BaseModel):
    """Result of an archive restoration operation."""

    archive_id: str = Field(description="Archive that was restored")
    records_found: int = Field(description="Total records in archive")
    records_restored: int = Field(description="Number of records restored to database")
    restore_mode: str = Field(description="Restoration mode used")
    restored_at: str = Field(description="Restoration timestamp")
    filters_applied: dict[str, Any] | None = Field(
        default=None, description="Filters used for selective restore"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AuditRestorer:
    """
    Service for restoring archived audit logs.

    Provides flexible restoration options from query-only access
    to full database restoration.
    """

    def __init__(
        self,
        db: Session,
        storage_backend: ArchiveStorageBackend | None = None,
    ) -> None:
        """
        Initialize audit restorer.

        Args:
            db: Database session
            storage_backend: Storage backend (defaults to configured backend)
        """
        self.db = db
        self.storage_backend = storage_backend or self._get_default_storage()

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
            backend_config["access_key"] = getattr(
                settings, "UPLOAD_S3_ACCESS_KEY", None
            )
            backend_config["secret_key"] = getattr(
                settings, "UPLOAD_S3_SECRET_KEY", None
            )
            backend_config["endpoint_url"] = getattr(
                settings, "UPLOAD_S3_ENDPOINT_URL", None
            )

        return get_storage_backend(backend_type, **backend_config)

    async def query_archive(
        self,
        archive_id: str,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query archive without restoring to database.

        Args:
            archive_id: Archive identifier
            filters: Query filters (entity_type, user_id, etc.)
            limit: Maximum records to return

        Returns:
            list: Matching audit log records from archive

        Raises:
            ValueError: If archive not found
        """
        logger.info(f"Querying archive {archive_id} with filters {filters}")

        # Retrieve archive
        archive_data = self.storage_backend.get_archive(archive_id)

        # Extract records
        records = archive_data.get("records", [])

        # Apply filters
        if filters:
            records = self._apply_filters(records, filters)

            # Apply limit
        if limit:
            records = records[:limit]

        logger.info(f"Found {len(records)} matching records in archive {archive_id}")

        return records

    async def restore_from_archive(
        self,
        archive_id: str,
        restore_mode: str = "selective",
        filters: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> RestoreResult:
        """
        Restore records from archive to active database.

        Args:
            archive_id: Archive identifier
            restore_mode: 'full' or 'selective'
            filters: Filters for selective restore
            dry_run: If True, don't actually restore (test mode)

        Returns:
            RestoreResult: Restoration result

        Raises:
            ValueError: If archive not found or restore_mode invalid
        """
        if restore_mode not in ("full", "selective"):
            raise ValueError(f"Invalid restore_mode: {restore_mode}")

        logger.info(
            f"Restoring from archive {archive_id} "
            f"(mode={restore_mode}, dry_run={dry_run})"
        )

        # Retrieve archive
        archive_data = self.storage_backend.get_archive(archive_id)

        # Extract records
        all_records = archive_data.get("records", [])

        # Apply filters for selective restore
        records_to_restore = all_records
        if restore_mode == "selective" and filters:
            records_to_restore = self._apply_filters(all_records, filters)

            # Restore records
        restored_count = 0
        if not dry_run:
            restored_count = await self._restore_records_to_db(records_to_restore)

        result = RestoreResult(
            archive_id=archive_id,
            records_found=len(all_records),
            records_restored=restored_count if not dry_run else 0,
            restore_mode=restore_mode,
            restored_at=datetime.utcnow().isoformat(),
            filters_applied=filters,
            metadata={
                "dry_run": dry_run,
                "archive_created_at": archive_data.get("created_at"),
                "archive_date_range": archive_data.get("date_range"),
            },
        )

        logger.info(
            f"Restored {result.records_restored} records from {archive_id} "
            f"(dry_run={dry_run})"
        )

        return result

    async def list_available_archives(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        List all available archives.

        Args:
            start_date: Filter archives created after this date
            end_date: Filter archives created before this date

        Returns:
            list: Archive metadata
        """
        archives = self.storage_backend.list_archives(
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(f"Found {len(archives)} available archives")
        return archives

    async def get_archive_metadata(self, archive_id: str) -> dict[str, Any]:
        """
        Get metadata for a specific archive without loading all records.

        Args:
            archive_id: Archive identifier

        Returns:
            dict: Archive metadata

        Raises:
            ValueError: If archive not found
        """
        archive_data = self.storage_backend.get_archive(archive_id)

        # Return metadata without full record list
        metadata = {
            "archive_id": archive_data.get("archive_id"),
            "created_at": archive_data.get("created_at"),
            "record_count": archive_data.get("record_count"),
            "date_range": archive_data.get("date_range"),
            "entity_type_counts": archive_data.get("entity_type_counts"),
            "operation_counts": archive_data.get("operation_counts"),
            "retention_policy": archive_data.get("retention_policy"),
        }

        return metadata

    async def search_across_archives(
        self,
        filters: dict[str, Any],
        archive_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Search across multiple archives.

        Args:
            filters: Search filters
            archive_ids: Specific archives to search (None = all)
            limit: Maximum results to return

        Returns:
            list: Matching records from all searched archives
        """
        logger.info(f"Searching archives with filters {filters}")

        # Get archives to search
        if archive_ids:
            archives = [
                {"archive_id": aid}
                for aid in archive_ids
                if self.storage_backend.exists(aid)
            ]
        else:
            archives = await self.list_available_archives()

        all_results = []
        for archive_meta in archives:
            archive_id = archive_meta["archive_id"]

            try:
                records = await self.query_archive(
                    archive_id=archive_id,
                    filters=filters,
                )

                # Add archive source to each record
                for record in records:
                    record["archive_source"] = archive_id

                all_results.extend(records)

                # Stop if we hit the limit
                if len(all_results) >= limit:
                    break

            except Exception as e:
                logger.warning(f"Error searching archive {archive_id}: {e}")
                continue

                # Apply final limit
        all_results = all_results[:limit]

        logger.info(
            f"Found {len(all_results)} matching records across {len(archives)} archives"
        )

        return all_results

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate compliance report from archives.

        Args:
            start_date: Report start date
            end_date: Report end date
            entity_types: Entity types to include

        Returns:
            dict: Compliance report data
        """
        logger.info(
            f"Generating compliance report from {start_date.date()} "
            f"to {end_date.date()}"
        )

        # Get relevant archives
        archives = await self.list_available_archives(
            start_date=start_date,
            end_date=end_date,
        )

        # Collect statistics
        total_records = 0
        entity_type_counts = {}
        operation_counts = {}
        user_activity = {}

        for archive_meta in archives:
            archive_id = archive_meta["archive_id"]

            try:
                metadata = await self.get_archive_metadata(archive_id)

                total_records += metadata.get("record_count", 0)

                # Aggregate entity type counts
                for entity_type, count in metadata.get(
                    "entity_type_counts", {}
                ).items():
                    if entity_types and entity_type not in entity_types:
                        continue
                    entity_type_counts[entity_type] = (
                        entity_type_counts.get(entity_type, 0) + count
                    )

                    # Aggregate operation counts
                for operation, count in metadata.get("operation_counts", {}).items():
                    operation_counts[operation] = (
                        operation_counts.get(operation, 0) + count
                    )

            except Exception as e:
                logger.warning(f"Error processing archive {archive_id}: {e}")
                continue

        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_records": total_records,
            "archives_reviewed": len(archives),
            "entity_type_counts": entity_type_counts,
            "operation_counts": operation_counts,
            "generated_at": datetime.utcnow().isoformat(),
            "entity_type_filter": entity_types,
        }

        logger.info(
            f"Compliance report generated: {total_records} records "
            f"across {len(archives)} archives"
        )

        return report

    def _apply_filters(
        self,
        records: list[dict[str, Any]],
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Apply filters to records.

        Args:
            records: List of audit log records
            filters: Filter criteria

        Returns:
            list: Filtered records
        """
        filtered = records

        if "entity_type" in filters:
            entity_type = filters["entity_type"]
            filtered = [r for r in filtered if r.get("entity_type") == entity_type]

        if "entity_id" in filters:
            entity_id = filters["entity_id"]
            filtered = [r for r in filtered if r.get("entity_id") == entity_id]

        if "user_id" in filters:
            user_id = filters["user_id"]
            filtered = [r for r in filtered if r.get("user_id") == user_id]

        if "operation_type" in filters:
            operation_type = filters["operation_type"]
            filtered = [
                r for r in filtered if r.get("operation_type") == operation_type
            ]

        if "start_date" in filters:
            start_date = filters["start_date"]
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", ""))
            filtered = [
                r
                for r in filtered
                if r.get("issued_at")
                and datetime.fromisoformat(r["issued_at"]) >= start_date
            ]

        if "end_date" in filters:
            end_date = filters["end_date"]
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", ""))
            filtered = [
                r
                for r in filtered
                if r.get("issued_at")
                and datetime.fromisoformat(r["issued_at"]) <= end_date
            ]

        return filtered

    async def _restore_records_to_db(
        self,
        records: list[dict[str, Any]],
    ) -> int:
        """
        Restore records to version tables.

        Args:
            records: Records to restore

        Returns:
            int: Number of records restored
        """
        if not records:
            return 0

        try:
            # Group by entity type
            records_by_type: dict[str, list[dict[str, Any]]] = {}
            for record in records:
                entity_type = record["entity_type"]
                if entity_type not in records_by_type:
                    records_by_type[entity_type] = []
                records_by_type[entity_type].append(record)

            restored_count = 0

            # Restore to each version table
            for entity_type, entity_records in records_by_type.items():
                table_name = f"{entity_type}_version"

                for record in entity_records:
                    # Build insert query
                    insert_query = text(
                        f"""
                        INSERT INTO {table_name}
                        (id, transaction_id, operation_type)
                        VALUES (:entity_id, :transaction_id, :operation_type)
                        ON CONFLICT (id, transaction_id) DO NOTHING
                    """
                    )

                    self.db.execute(
                        insert_query,
                        {
                            "entity_id": record["entity_id"],
                            "transaction_id": record["transaction_id"],
                            "operation_type": record["operation_type"],
                        },
                    )

                    restored_count += 1

            self.db.commit()
            logger.info(f"Restored {restored_count} records to database")
            return restored_count

        except Exception as e:
            logger.error(f"Failed to restore records to database: {e}")
            self.db.rollback()
            raise
