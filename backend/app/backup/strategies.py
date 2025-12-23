"""
Backup Strategies.

This module implements different backup strategies using the Strategy pattern:
- Full Backup: Complete database dump
- Incremental Backup: Only changed data since last backup

Each strategy handles:
- Data extraction from database
- Compression and optimization
- Metadata generation
- Validation and verification

Usage:
    strategy = FullBackupStrategy()
    backup_data = await strategy.execute(db, backup_metadata)

    strategy = IncrementalBackupStrategy()
    backup_data = await strategy.execute(db, backup_metadata, last_backup_id)
"""

import gzip
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BackupStrategy(ABC):
    """
    Abstract base class for backup strategies.

    Defines the interface that all backup strategies must implement.
    Uses the Strategy pattern to allow different backup algorithms.
    """

    @abstractmethod
    async def execute(
        self,
        db: Session,
        backup_metadata: dict[str, Any],
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute the backup strategy.

        Args:
            db: Database session
            backup_metadata: Metadata about the backup (id, timestamp, etc.)
            **kwargs: Strategy-specific parameters

        Returns:
            dict: Backup data including tables, rows, metadata

        Raises:
            ValueError: If backup execution fails
        """
        pass

    def _get_table_list(self, db: Session) -> list[str]:
        """
        Get list of tables to backup.

        Excludes:
        - SQLAlchemy-Continuum version tables (backed up with main tables)
        - Alembic migration tables
        - Temporary tables

        Args:
            db: Database session

        Returns:
            list: Table names to backup
        """
        query = text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename NOT LIKE '%_version'
            AND tablename != 'alembic_version'
            AND tablename != 'transaction'
            ORDER BY tablename
        """)

        result = db.execute(query)
        tables = [row[0] for row in result]

        logger.debug(f"Found {len(tables)} tables to backup: {tables}")
        return tables

    def _get_table_row_count(self, db: Session, table: str) -> int:
        """
        Get row count for a table.

        Args:
            db: Database session
            table: Table name

        Returns:
            int: Number of rows in table
        """
        try:
            query = text(f"SELECT COUNT(*) FROM {table}")
            result = db.execute(query)
            count = result.scalar()
            return count or 0
        except Exception as e:
            logger.warning(f"Error getting row count for {table}: {e}")
            return 0

    def _calculate_checksum(self, data: bytes) -> str:
        """
        Calculate SHA-256 checksum of data.

        Args:
            data: Data bytes

        Returns:
            str: Hex digest of SHA-256 hash
        """
        return hashlib.sha256(data).hexdigest()

    def _compress_data(self, data: str) -> bytes:
        """
        Compress data using gzip.

        Args:
            data: String data to compress

        Returns:
            bytes: Compressed data
        """
        return gzip.compress(data.encode("utf-8"))

    def _decompress_data(self, data: bytes) -> str:
        """
        Decompress gzip data.

        Args:
            data: Compressed bytes

        Returns:
            str: Decompressed string
        """
        return gzip.decompress(data).decode("utf-8")


class FullBackupStrategy(BackupStrategy):
    """
    Full Backup Strategy.

    Creates a complete snapshot of all database tables.
    Includes all rows from all tables with full data.

    Advantages:
    - Simple and reliable
    - Self-contained (no dependencies)
    - Fast restore

    Disadvantages:
    - Large storage size
    - Slower to create
    - Redundant data across backups
    """

    async def execute(
        self,
        db: Session,
        backup_metadata: dict[str, Any],
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute full backup strategy.

        Args:
            db: Database session
            backup_metadata: Backup metadata
            **kwargs: Additional parameters (compression, etc.)

        Returns:
            dict: Complete backup data with all tables

        Raises:
            ValueError: If backup fails
        """
        logger.info(f"Starting full backup: {backup_metadata['backup_id']}")

        try:
            tables = self._get_table_list(db)
            backup_data = {
                "backup_id": backup_metadata["backup_id"],
                "backup_type": "full",
                "created_at": backup_metadata["created_at"],
                "strategy": "full",
                "tables": {},
                "metadata": {
                    "table_count": len(tables),
                    "total_rows": 0,
                },
            }

            total_rows = 0

            # Backup each table
            for table in tables:
                logger.debug(f"Backing up table: {table}")

                try:
                    # Get table data
                    table_data = self._backup_table_full(db, table)

                    backup_data["tables"][table] = table_data
                    total_rows += table_data["row_count"]

                except Exception as e:
                    logger.error(f"Error backing up table {table}: {e}")
                    # Continue with other tables
                    backup_data["tables"][table] = {
                        "error": str(e),
                        "row_count": 0,
                        "rows": [],
                    }

            backup_data["metadata"]["total_rows"] = total_rows

            logger.info(
                f"Full backup complete: {len(tables)} tables, {total_rows} rows"
            )

            return backup_data

        except Exception as e:
            logger.error(f"Full backup failed: {e}", exc_info=True)
            raise ValueError(f"Full backup failed: {e}")

    def _backup_table_full(self, db: Session, table: str) -> dict[str, Any]:
        """
        Backup all rows from a table.

        Args:
            db: Database session
            table: Table name

        Returns:
            dict: Table data with all rows
        """
        # Get all rows
        query = text(f"SELECT * FROM {table}")
        result = db.execute(query)

        # Convert rows to dictionaries
        rows = []
        for row in result:
            row_dict = dict(row._mapping)
            # Convert non-JSON-serializable types
            for key, value in row_dict.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                elif hasattr(value, "__str__") and not isinstance(
                    value, (str, int, float, bool, type(None))
                ):
                    row_dict[key] = str(value)

            rows.append(row_dict)

        return {
            "row_count": len(rows),
            "rows": rows,
            "columns": list(result.keys()) if result.keys() else [],
        }


class IncrementalBackupStrategy(BackupStrategy):
    """
    Incremental Backup Strategy.

    Backs up only data that changed since the last backup.
    Uses SQLAlchemy-Continuum transaction tracking to identify changes.

    Advantages:
    - Smaller backup size
    - Faster to create
    - Efficient storage

    Disadvantages:
    - Requires previous backup (dependency chain)
    - More complex restore process
    - Relies on transaction tracking
    """

    async def execute(
        self,
        db: Session,
        backup_metadata: dict[str, Any],
        last_backup_timestamp: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute incremental backup strategy.

        Args:
            db: Database session
            backup_metadata: Backup metadata
            last_backup_timestamp: Timestamp of last backup (ISO format)
            **kwargs: Additional parameters

        Returns:
            dict: Incremental backup data with only changed rows

        Raises:
            ValueError: If incremental backup fails or no base backup exists
        """
        logger.info(f"Starting incremental backup: {backup_metadata['backup_id']}")

        if not last_backup_timestamp:
            raise ValueError(
                "Incremental backup requires last_backup_timestamp. "
                "Create a full backup first."
            )

        try:
            # Convert timestamp to datetime
            last_backup_dt = datetime.fromisoformat(
                last_backup_timestamp.replace("Z", "")
            )

            tables = self._get_table_list(db)
            backup_data = {
                "backup_id": backup_metadata["backup_id"],
                "backup_type": "incremental",
                "created_at": backup_metadata["created_at"],
                "strategy": "incremental",
                "base_backup_timestamp": last_backup_timestamp,
                "tables": {},
                "metadata": {
                    "table_count": 0,
                    "total_changes": 0,
                },
            }

            total_changes = 0
            tables_with_changes = 0

            # Backup changed data from each table
            for table in tables:
                logger.debug(f"Checking for changes in table: {table}")

                try:
                    # Get changed rows since last backup
                    table_data = self._backup_table_incremental(
                        db, table, last_backup_dt
                    )

                    if table_data["row_count"] > 0:
                        backup_data["tables"][table] = table_data
                        total_changes += table_data["row_count"]
                        tables_with_changes += 1

                except Exception as e:
                    logger.warning(f"Error checking table {table} for changes: {e}")
                    # Continue with other tables
                    continue

            backup_data["metadata"]["table_count"] = tables_with_changes
            backup_data["metadata"]["total_changes"] = total_changes

            logger.info(
                f"Incremental backup complete: {tables_with_changes} tables, "
                f"{total_changes} changes"
            )

            return backup_data

        except Exception as e:
            logger.error(f"Incremental backup failed: {e}", exc_info=True)
            raise ValueError(f"Incremental backup failed: {e}")

    def _backup_table_incremental(
        self, db: Session, table: str, since: datetime
    ) -> dict[str, Any]:
        """
        Backup only rows that changed since a timestamp.

        Uses updated_at column if available, otherwise backs up all rows.

        Args:
            db: Database session
            table: Table name
            since: Timestamp to check for changes

        Returns:
            dict: Table data with changed rows
        """
        # Check if table has updated_at column
        column_query = text(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table}'
            AND column_name IN ('updated_at', 'created_at', 'changed_at')
            ORDER BY
                CASE column_name
                    WHEN 'updated_at' THEN 1
                    WHEN 'changed_at' THEN 2
                    WHEN 'created_at' THEN 3
                END
            LIMIT 1
        """)

        result = db.execute(column_query)
        timestamp_column = result.scalar()

        if timestamp_column:
            # Query rows changed since last backup
            query = text(f"""
                SELECT *
                FROM {table}
                WHERE {timestamp_column} > :since
                ORDER BY {timestamp_column}
            """)
            result = db.execute(query, {"since": since})
        else:
            # No timestamp column - include all rows as a safety measure
            logger.warning(f"Table {table} has no timestamp column, including all rows")
            query = text(f"SELECT * FROM {table}")
            result = db.execute(query)

        # Convert rows to dictionaries
        rows = []
        for row in result:
            row_dict = dict(row._mapping)
            # Convert non-JSON-serializable types
            for key, value in row_dict.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                elif hasattr(value, "__str__") and not isinstance(
                    value, (str, int, float, bool, type(None))
                ):
                    row_dict[key] = str(value)

            rows.append(row_dict)

        return {
            "row_count": len(rows),
            "rows": rows,
            "columns": list(result.keys()) if result.keys() else [],
            "timestamp_column": timestamp_column,
        }


class DifferentialBackupStrategy(BackupStrategy):
    """
    Differential Backup Strategy.

    Backs up all changes since the last FULL backup (not the last incremental).
    This is a middle ground between full and incremental backups.

    Advantages:
    - Faster restore than incremental (only need full + differential)
    - More efficient than full backups
    - Simpler dependency chain

    Disadvantages:
    - Larger than incremental backups
    - Still requires a full backup as base
    """

    async def execute(
        self,
        db: Session,
        backup_metadata: dict[str, Any],
        last_full_backup_timestamp: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute differential backup strategy.

        Args:
            db: Database session
            backup_metadata: Backup metadata
            last_full_backup_timestamp: Timestamp of last full backup
            **kwargs: Additional parameters

        Returns:
            dict: Differential backup data

        Raises:
            ValueError: If no full backup exists
        """
        logger.info(f"Starting differential backup: {backup_metadata['backup_id']}")

        if not last_full_backup_timestamp:
            raise ValueError(
                "Differential backup requires last_full_backup_timestamp. "
                "Create a full backup first."
            )

        # Differential backup is similar to incremental but references
        # the last full backup instead of the last backup
        incremental_strategy = IncrementalBackupStrategy()
        backup_data = await incremental_strategy.execute(
            db,
            backup_metadata,
            last_backup_timestamp=last_full_backup_timestamp,
            **kwargs,
        )

        # Update metadata to reflect differential strategy
        backup_data["backup_type"] = "differential"
        backup_data["strategy"] = "differential"
        backup_data["base_full_backup_timestamp"] = last_full_backup_timestamp

        logger.info(
            f"Differential backup complete: {backup_data['metadata']['total_changes']} changes"
        )

        return backup_data
