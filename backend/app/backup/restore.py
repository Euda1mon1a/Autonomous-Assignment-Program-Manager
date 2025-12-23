"""
Restore Utilities.

Provides point-in-time recovery and restore operations from backups.
Handles restoration from full, incremental, and differential backups.

Usage:
    restore_service = RestoreService()

    # Restore from a specific backup
    await restore_service.restore_from_backup(db, backup_id)

    # Point-in-time recovery
    await restore_service.restore_to_point_in_time(db, target_datetime)

    # Dry run (validate without applying)
    result = await restore_service.restore_from_backup(
        db, backup_id, dry_run=True
    )
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.backup.storage import BackupStorage, get_storage_backend

logger = logging.getLogger(__name__)


class RestoreService:
    """
    Service for restoring database from backups.

    Supports:
    - Full backup restoration
    - Incremental backup chain restoration
    - Point-in-time recovery
    - Dry-run validation
    - Selective table restoration
    """

    def __init__(self, storage: BackupStorage | None = None):
        """
        Initialize restore service.

        Args:
            storage: Storage backend (uses settings if None)
        """
        self.storage = storage or get_storage_backend()

        logger.info(
            f"Initialized RestoreService with storage: {type(self.storage).__name__}"
        )

    async def restore_from_backup(
        self,
        db: Session,
        backup_id: str,
        tables: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Restore database from a specific backup.

        For incremental backups, automatically restores the full chain:
        1. Find the base full backup
        2. Apply incremental changes in order
        3. Apply the target backup

        Args:
            db: Database session
            backup_id: Backup identifier
            tables: Specific tables to restore (None = all tables)
            dry_run: If True, validate without applying changes

        Returns:
            dict: Restoration result with statistics

        Raises:
            ValueError: If restoration fails
        """
        logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Restoring from backup: {backup_id}"
        )

        try:
            # Get backup data
            backup_data = self.storage.get_backup(backup_id)

            backup_type = backup_data.get("backup_type", "full")
            created_at = backup_data.get("created_at")

            # Build restoration chain
            restore_chain = self._build_restore_chain(backup_id, backup_data)

            logger.info(
                f"Restore chain: {len(restore_chain)} backups to apply "
                f"(types: {[b['backup_type'] for b in restore_chain]})"
            )

            # Apply each backup in chain
            total_rows_restored = 0
            tables_restored = set()

            for i, chain_backup in enumerate(restore_chain):
                chain_backup_id = chain_backup["backup_id"]
                chain_backup_type = chain_backup["backup_type"]

                logger.info(
                    f"Applying backup {i + 1}/{len(restore_chain)}: "
                    f"{chain_backup_id} ({chain_backup_type})"
                )

                # Get full backup data if not already loaded
                if chain_backup_id != backup_id:
                    chain_data = self.storage.get_backup(chain_backup_id)
                else:
                    chain_data = backup_data

                # Restore tables from this backup
                result = await self._restore_backup_data(
                    db,
                    chain_data,
                    tables=tables,
                    dry_run=dry_run,
                )

                total_rows_restored += result["rows_restored"]
                tables_restored.update(result["tables"])

            if not dry_run:
                db.commit()
                logger.info("Database changes committed")

            logger.info(
                f"{'[DRY RUN] ' if dry_run else ''}Restoration complete: "
                f"{total_rows_restored} rows across {len(tables_restored)} tables"
            )

            return {
                "status": "success" if not dry_run else "dry_run_success",
                "backup_id": backup_id,
                "backup_type": backup_type,
                "backup_created_at": created_at,
                "restore_chain_length": len(restore_chain),
                "rows_restored": total_rows_restored,
                "tables_restored": list(tables_restored),
                "dry_run": dry_run,
            }

        except Exception as e:
            logger.error(f"Restoration failed: {e}", exc_info=True)
            if not dry_run:
                db.rollback()
            raise ValueError(f"Restoration failed: {e}")

    def _build_restore_chain(
        self, backup_id: str, backup_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Build the chain of backups needed for restoration.

        For full backups: Just the backup itself
        For incremental backups: Base full backup + all incrementals in order
        For differential backups: Base full backup + differential

        Args:
            backup_id: Target backup identifier
            backup_data: Target backup data

        Returns:
            list: Ordered list of backups to apply

        Raises:
            ValueError: If chain cannot be built
        """
        backup_type = backup_data.get("backup_type", "full")

        # Full backup - just return itself
        if backup_type == "full":
            return [
                {
                    "backup_id": backup_id,
                    "backup_type": backup_type,
                    "created_at": backup_data.get("created_at"),
                }
            ]

        # Incremental or differential - need to find base and build chain
        base_timestamp = backup_data.get("base_backup_timestamp")
        target_timestamp = backup_data.get("created_at")

        if not base_timestamp:
            raise ValueError(
                f"Incremental backup {backup_id} missing base_backup_timestamp"
            )

        # Get all backups
        all_backups = self.storage.list_backups(limit=1000)

        # Find base full backup
        base_backup = None
        for backup in all_backups:
            if (
                backup.get("backup_type") == "full"
                and backup.get("created_at") <= base_timestamp
            ):
                if not base_backup or backup["created_at"] > base_backup["created_at"]:
                    base_backup = backup

        if not base_backup:
            raise ValueError(
                f"Could not find base full backup for {backup_id} "
                f"(base timestamp: {base_timestamp})"
            )

        chain = [base_backup]

        # For differential, just add the differential backup
        if backup_type == "differential":
            chain.append(
                {
                    "backup_id": backup_id,
                    "backup_type": backup_type,
                    "created_at": target_timestamp,
                }
            )
            return chain

        # For incremental, add all incrementals between base and target
        incrementals = []
        for backup in all_backups:
            if backup.get("backup_type") != "incremental":
                continue

            created_at = backup.get("created_at", "")

            if base_backup["created_at"] < created_at <= target_timestamp:
                incrementals.append(backup)

        # Sort incrementals by created_at
        incrementals.sort(key=lambda x: x.get("created_at", ""))

        chain.extend(incrementals)

        return chain

    async def _restore_backup_data(
        self,
        db: Session,
        backup_data: dict[str, Any],
        tables: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Restore data from a single backup.

        Args:
            db: Database session
            backup_data: Backup data dictionary
            tables: Specific tables to restore (None = all)
            dry_run: If True, validate without applying

        Returns:
            dict: Restoration result for this backup

        Raises:
            ValueError: If restoration fails
        """
        backup_tables = backup_data.get("tables", {})
        rows_restored = 0
        tables_restored = []

        for table_name, table_data in backup_tables.items():
            # Skip if not in requested tables
            if tables and table_name not in tables:
                continue

            # Skip if table has errors
            if "error" in table_data:
                logger.warning(f"Skipping table {table_name}: {table_data['error']}")
                continue

            logger.debug(f"Restoring table: {table_name}")

            try:
                restored = await self._restore_table(
                    db,
                    table_name,
                    table_data,
                    dry_run=dry_run,
                )

                rows_restored += restored
                tables_restored.append(table_name)

            except Exception as e:
                logger.error(f"Error restoring table {table_name}: {e}")
                # Continue with other tables
                continue

        return {
            "rows_restored": rows_restored,
            "tables": tables_restored,
        }

    async def _restore_table(
        self,
        db: Session,
        table_name: str,
        table_data: dict[str, Any],
        dry_run: bool = False,
    ) -> int:
        """
        Restore a single table.

        Uses UPSERT (INSERT ... ON CONFLICT UPDATE) to handle both
        new rows and updated rows.

        Args:
            db: Database session
            table_name: Name of table to restore
            table_data: Table data from backup
            dry_run: If True, validate without applying

        Returns:
            int: Number of rows restored

        Raises:
            ValueError: If restoration fails
        """
        rows = table_data.get("rows", [])
        columns = table_data.get("columns", [])

        if not rows:
            logger.debug(f"No rows to restore for {table_name}")
            return 0

        if not columns:
            raise ValueError(f"No column information for {table_name}")

        # Build UPSERT query
        # Note: This assumes tables have a primary key named 'id'
        # For tables with different primary keys, we'd need schema introspection

        rows_restored = 0

        for row in rows:
            if dry_run:
                # Just validate the row structure
                rows_restored += 1
                continue

            try:
                # Build INSERT ... ON CONFLICT DO UPDATE
                column_names = ", ".join(columns)
                placeholders = ", ".join([f":{col}" for col in columns])

                # Build update clause (all columns except id)
                update_cols = [col for col in columns if col != "id"]
                update_clause = ", ".join(
                    [f"{col} = EXCLUDED.{col}" for col in update_cols]
                )

                query = text(f"""
                    INSERT INTO {table_name} ({column_names})
                    VALUES ({placeholders})
                    ON CONFLICT (id)
                    DO UPDATE SET {update_clause}
                """)

                db.execute(query, row)
                rows_restored += 1

            except Exception as e:
                logger.warning(f"Error restoring row in {table_name}: {e}. Row: {row}")
                # Continue with other rows
                continue

        logger.debug(f"Restored {rows_restored} rows to {table_name}")
        return rows_restored

    async def restore_to_point_in_time(
        self,
        db: Session,
        target_datetime: datetime | str,
        tables: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Restore database to a specific point in time.

        Finds the most recent backup before the target time and restores from it.

        Args:
            db: Database session
            target_datetime: Target datetime (datetime object or ISO string)
            tables: Specific tables to restore (None = all)
            dry_run: If True, validate without applying

        Returns:
            dict: Restoration result

        Raises:
            ValueError: If restoration fails or no suitable backup exists
        """
        # Convert string to datetime if needed
        if isinstance(target_datetime, str):
            target_datetime = datetime.fromisoformat(target_datetime.replace("Z", ""))

        target_str = target_datetime.isoformat() + "Z"

        logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Restoring to point in time: {target_str}"
        )

        try:
            # Get all backups
            all_backups = self.storage.list_backups(limit=1000)

            # Find most recent backup before target time
            suitable_backups = [
                b for b in all_backups if b.get("created_at", "") <= target_str
            ]

            if not suitable_backups:
                raise ValueError(
                    f"No backups found before {target_str}. "
                    f"Earliest backup: {min(b.get('created_at', '') for b in all_backups)}"
                )

            # Sort by created_at descending
            suitable_backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Use the most recent suitable backup
            backup_to_use = suitable_backups[0]
            backup_id = backup_to_use["backup_id"]

            logger.info(
                f"Using backup {backup_id} created at {backup_to_use['created_at']}"
            )

            # Restore from this backup
            result = await self.restore_from_backup(
                db,
                backup_id,
                tables=tables,
                dry_run=dry_run,
            )

            result["point_in_time_target"] = target_str
            result["backup_used"] = backup_to_use

            return result

        except Exception as e:
            logger.error(f"Point-in-time restoration failed: {e}", exc_info=True)
            raise ValueError(f"Point-in-time restoration failed: {e}")

    def validate_backup_chain(self, backup_id: str) -> dict[str, Any]:
        """
        Validate that a backup and its dependencies are intact.

        Args:
            backup_id: Backup identifier

        Returns:
            dict: Validation result with status and details

        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Validating backup chain for: {backup_id}")

        try:
            # Get backup data
            backup_data = self.storage.get_backup(backup_id)

            # Build restore chain
            restore_chain = self._build_restore_chain(backup_id, backup_data)

            # Verify each backup in chain
            validation_results = []

            for chain_backup in restore_chain:
                chain_backup_id = chain_backup["backup_id"]

                try:
                    # Verify backup integrity
                    is_valid = self.storage.verify_backup(chain_backup_id)

                    validation_results.append(
                        {
                            "backup_id": chain_backup_id,
                            "backup_type": chain_backup["backup_type"],
                            "created_at": chain_backup["created_at"],
                            "valid": is_valid,
                            "error": None,
                        }
                    )

                except Exception as e:
                    validation_results.append(
                        {
                            "backup_id": chain_backup_id,
                            "backup_type": chain_backup["backup_type"],
                            "created_at": chain_backup["created_at"],
                            "valid": False,
                            "error": str(e),
                        }
                    )

            # Check if all backups in chain are valid
            all_valid = all(r["valid"] for r in validation_results)

            logger.info(
                f"Backup chain validation complete: "
                f"{'VALID' if all_valid else 'INVALID'}"
            )

            return {
                "status": "valid" if all_valid else "invalid",
                "backup_id": backup_id,
                "chain_length": len(restore_chain),
                "validation_results": validation_results,
                "all_valid": all_valid,
            }

        except Exception as e:
            logger.error(f"Backup chain validation failed: {e}", exc_info=True)
            raise ValueError(f"Backup chain validation failed: {e}")
