"""Restore service for data recovery."""
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import inspect, delete

from app.models import (
    Person,
    Block,
    RotationTemplate,
    Assignment,
    Absence,
    CallAssignment,
    ScheduleRun,
    User,
)
from app.maintenance.backup import BackupService


class RestoreService:
    """Service for restoring database from backups."""

    # Define table order for restore (respecting foreign key dependencies)
    # Reverse of backup order for deletion
    TABLE_ORDER = [
        "users",
        "people",
        "blocks",
        "rotation_templates",
        "absences",
        "assignments",
        "call_assignments",
        "schedule_runs",
    ]

    REVERSE_TABLE_ORDER = [
        "schedule_runs",
        "call_assignments",
        "assignments",
        "absences",
        "rotation_templates",
        "blocks",
        "people",
        "users",
    ]

    MODEL_MAP = {
        "users": User,
        "people": Person,
        "blocks": Block,
        "rotation_templates": RotationTemplate,
        "absences": Absence,
        "assignments": Assignment,
        "call_assignments": CallAssignment,
        "schedule_runs": ScheduleRun,
    }

    def __init__(self, db: Session, backup_dir: str = "/tmp/backups"):
        """
        Initialize restore service.

        Args:
            db: Database session
            backup_dir: Directory where backup files are stored
        """
        self.db = db
        self.backup_service = BackupService(db, backup_dir)

    def validate_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Validate a backup before restore.

        Args:
            backup_id: The backup ID to validate

        Returns:
            Dict with validation results
        """
        # Get backup data
        backup_data = self.backup_service.get_backup(backup_id)
        if not backup_data:
            return {
                "valid": False,
                "error": f"Backup {backup_id} not found",
            }

        metadata = backup_data.get("metadata", {})
        data = backup_data.get("data", {})

        # Check metadata
        if not metadata:
            return {
                "valid": False,
                "error": "Backup missing metadata",
            }

        # Check data structure
        if not data:
            return {
                "valid": False,
                "error": "Backup missing data",
            }

        # Validate tables
        missing_tables = []
        for table_name in metadata.get("tables", []):
            if table_name not in data:
                missing_tables.append(table_name)

        if missing_tables:
            return {
                "valid": False,
                "error": f"Backup missing data for tables: {missing_tables}",
            }

        # Count records
        total_records = sum(len(data[t]) for t in data.keys())

        return {
            "valid": True,
            "backup_id": backup_id,
            "timestamp": metadata.get("timestamp"),
            "total_records": total_records,
            "tables": metadata.get("tables", []),
            "version": metadata.get("version"),
            "description": metadata.get("description"),
        }

    def restore_full(
        self,
        backup_id: str,
        dry_run: bool = False,
        skip_validation: bool = False,
    ) -> Dict[str, Any]:
        """
        Restore full database from backup.

        Args:
            backup_id: The backup ID to restore
            dry_run: If True, validate but don't actually restore
            skip_validation: If True, skip pre-restore validation

        Returns:
            Dict with restore results
        """
        # Validate backup
        if not skip_validation:
            validation = self.validate_backup(backup_id)
            if not validation.get("valid"):
                return {
                    "status": "failed",
                    "error": validation.get("error"),
                }

        # Get backup data
        backup_data = self.backup_service.get_backup(backup_id)
        metadata = backup_data.get("metadata", {})
        data = backup_data.get("data", {})

        if dry_run:
            return {
                "status": "dry_run",
                "backup_id": backup_id,
                "timestamp": metadata.get("timestamp"),
                "total_records": metadata.get("total_records"),
                "tables": metadata.get("tables", []),
                "message": "Dry run completed successfully. No data was modified.",
            }

        # Start restore process
        start_time = datetime.utcnow()
        restored_counts = {}

        try:
            # Create a savepoint for rollback
            savepoint = self.db.begin_nested()

            try:
                # Clear existing data (in reverse order)
                for table_name in self.REVERSE_TABLE_ORDER:
                    if table_name in data:
                        model = self.MODEL_MAP[table_name]
                        self.db.execute(delete(model))

                # Restore data (in forward order)
                for table_name in self.TABLE_ORDER:
                    if table_name in data:
                        count = self._restore_table(table_name, data[table_name])
                        restored_counts[table_name] = count

                # Commit the transaction
                self.db.commit()

            except Exception as e:
                # Rollback on error
                savepoint.rollback()
                raise e

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return {
                "status": "success",
                "backup_id": backup_id,
                "restored_records": sum(restored_counts.values()),
                "tables": restored_counts,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat(),
            }

        except Exception as e:
            # Ensure rollback
            self.db.rollback()
            return {
                "status": "failed",
                "error": str(e),
                "backup_id": backup_id,
            }

    def restore_selective(
        self,
        backup_id: str,
        table_names: List[str],
        dry_run: bool = False,
        clear_existing: bool = True,
    ) -> Dict[str, Any]:
        """
        Restore specific tables from backup.

        Args:
            backup_id: The backup ID to restore
            table_names: List of table names to restore
            dry_run: If True, validate but don't actually restore
            clear_existing: If True, clear existing data before restore

        Returns:
            Dict with restore results
        """
        # Validate table names
        invalid_tables = set(table_names) - set(self.TABLE_ORDER)
        if invalid_tables:
            return {
                "status": "failed",
                "error": f"Invalid table names: {invalid_tables}",
            }

        # Get backup data
        backup_data = self.backup_service.get_backup(backup_id)
        if not backup_data:
            return {
                "status": "failed",
                "error": f"Backup {backup_id} not found",
            }

        metadata = backup_data.get("metadata", {})
        data = backup_data.get("data", {})

        # Check if requested tables are in backup
        missing_tables = set(table_names) - set(data.keys())
        if missing_tables:
            return {
                "status": "failed",
                "error": f"Tables not found in backup: {missing_tables}",
            }

        if dry_run:
            total_records = sum(len(data[t]) for t in table_names)
            return {
                "status": "dry_run",
                "backup_id": backup_id,
                "tables": table_names,
                "total_records": total_records,
                "message": "Dry run completed successfully. No data was modified.",
            }

        # Start restore process
        start_time = datetime.utcnow()
        restored_counts = {}

        try:
            # Create a savepoint for rollback
            savepoint = self.db.begin_nested()

            try:
                # Clear existing data if requested (in reverse order)
                if clear_existing:
                    for table_name in reversed(table_names):
                        if table_name in data:
                            model = self.MODEL_MAP[table_name]
                            self.db.execute(delete(model))

                # Restore data (in forward order)
                ordered_tables = [t for t in self.TABLE_ORDER if t in table_names]
                for table_name in ordered_tables:
                    count = self._restore_table(table_name, data[table_name])
                    restored_counts[table_name] = count

                # Commit the transaction
                self.db.commit()

            except Exception as e:
                # Rollback on error
                savepoint.rollback()
                raise e

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return {
                "status": "success",
                "backup_id": backup_id,
                "restored_records": sum(restored_counts.values()),
                "tables": restored_counts,
                "duration_seconds": duration,
                "timestamp": end_time.isoformat(),
            }

        except Exception as e:
            # Ensure rollback
            self.db.rollback()
            return {
                "status": "failed",
                "error": str(e),
                "backup_id": backup_id,
                "tables": table_names,
            }

    def _restore_table(self, table_name: str, records: List[Dict[str, Any]]) -> int:
        """
        Restore a single table from backup data.

        Args:
            table_name: Name of the table to restore
            records: List of record dictionaries

        Returns:
            Number of records restored
        """
        model = self.MODEL_MAP.get(table_name)
        if not model:
            raise ValueError(f"Unknown table: {table_name}")

        count = 0
        for record_data in records:
            # Convert string UUIDs back to UUID objects
            converted_data = {}
            mapper = inspect(model)

            for column in mapper.columns:
                column_name = column.name
                if column_name in record_data:
                    value = record_data[column_name]

                    # Convert based on column type
                    if value is not None:
                        # Handle UUID columns
                        if hasattr(column.type, 'python_type') and column.type.python_type == UUID:
                            value = UUID(value) if isinstance(value, str) else value
                        # Handle datetime columns
                        elif hasattr(column.type, 'python_type') and column.type.python_type == datetime:
                            if isinstance(value, str):
                                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        # Handle date columns
                        elif str(column.type) in ['DATE', 'Date']:
                            if isinstance(value, str):
                                from datetime import date
                                value = date.fromisoformat(value)

                    converted_data[column_name] = value

            # Create and add the record
            record = model(**converted_data)
            self.db.add(record)
            count += 1

        # Flush to detect any constraint violations early
        self.db.flush()

        return count

    def get_restore_preview(self, backup_id: str) -> Dict[str, Any]:
        """
        Get a preview of what would be restored.

        Args:
            backup_id: The backup ID to preview

        Returns:
            Dict with preview information
        """
        validation = self.validate_backup(backup_id)

        if not validation.get("valid"):
            return validation

        backup_data = self.backup_service.get_backup(backup_id)
        data = backup_data.get("data", {})

        # Gather statistics
        table_stats = {}
        for table_name in validation.get("tables", []):
            if table_name in data:
                records = data[table_name]
                table_stats[table_name] = {
                    "record_count": len(records),
                    "sample_record": records[0] if records else None,
                }

        return {
            "valid": True,
            "backup_id": backup_id,
            "timestamp": validation.get("timestamp"),
            "description": validation.get("description"),
            "total_records": validation.get("total_records"),
            "table_statistics": table_stats,
        }
