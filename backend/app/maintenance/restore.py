"""Restore service for schedule data."""

import gzip
import json
import logging
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.file_security import (
    FileSecurityError,
    validate_backup_id,
    validate_file_path,
)

# Import custom exceptions
from app.maintenance import (
    BackupNotFoundError,
    BackupReadError,
    RestoreDataError,
    RestoreError,
    RestorePermissionError,
    RestoreRollbackError,
    RestoreValidationError,
)
from app.models import Absence, Assignment, Block, Person, RotationTemplate, ScheduleRun

logger = logging.getLogger(__name__)


class RestoreService:
    """Service for restoring schedule data from backups."""

    def __init__(self, db: Session, backup_dir: str = "backups") -> None:
        """
        Initialize restore service.

        Args:
            db: Database session
            backup_dir: Directory containing backups (default: "backups")

        Raises:
            RestorePermissionError: If backup directory cannot be accessed
        """
        self.db = db
        self.backup_path = Path(backup_dir)
        self.restore_history: list[dict[str, Any]] = []

        if not self.backup_path.exists():
            logger.error(f"Backup directory does not exist: {backup_dir}")
            raise RestorePermissionError(
                f"Backup directory '{backup_dir}' does not exist"
            )

        if not self.backup_path.is_dir():
            logger.error(f"Backup path is not a directory: {backup_dir}")
            raise RestorePermissionError(
                f"Backup path '{backup_dir}' is not a directory"
            )

        logger.info(f"Initialized RestoreService with directory: {self.backup_path}")

    def restore_from_backup(
        self, backup_id: str, options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Restore data from a backup.

        Args:
            backup_id: ID of the backup to restore
            options: Restore options (mode: 'replace' or 'merge', dry_run: bool)

        Returns:
            Restore result summary

        Raises:
            RestoreValidationError: If validation fails or invalid mode
            RestoreError: If restore operation fails
            BackupNotFoundError: If backup doesn't exist
        """
        options = options or {}
        mode = options.get("mode", "replace")
        dry_run = options.get("dry_run", False)

        # Validate mode
        if mode not in ("replace", "merge"):
            logger.error(f"Invalid restore mode: {mode}")
            raise RestoreValidationError(
                f"Invalid restore mode '{mode}'. Must be 'replace' or 'merge'."
            )

        logger.info(
            f"Starting restore from backup {backup_id}, mode: {mode}, dry_run: {dry_run}"
        )

        try:
            # Load backup data
            backup_data = self._load_backup(backup_id)

            # Validate before restoring
            logger.debug(f"Validating backup {backup_id}")
            validation = self.validate_backup(backup_id)
            if not validation["valid"]:
                error_msg = validation.get("error", "Unknown validation error")
                logger.error(f"Backup validation failed: {error_msg}")
                raise RestoreValidationError(f"Backup validation failed: {error_msg}")

            restore_id = str(uuid.uuid4())
            restore_timestamp = datetime.utcnow()

            if dry_run:
                logger.info(f"Dry run completed for backup {backup_id}")
                return self._preview_restore_result(backup_data, mode)

                # Create restore point for rollback
            logger.debug("Creating restore point for rollback")
            rollback_data = self._create_restore_point(restore_id)

            # Perform restore
            if mode == "replace":
                logger.info(f"Performing replace restore from backup {backup_id}")
                result = self._replace_restore(backup_data)
            else:
                logger.info(f"Performing merge restore from backup {backup_id}")
                result = self._merge_restore(backup_data)

                # Commit transaction
            self.db.commit()
            logger.debug("Database transaction committed")

            # Save restore metadata
            restore_metadata = {
                "restore_id": restore_id,
                "backup_id": backup_id,
                "timestamp": restore_timestamp.isoformat(),
                "mode": mode,
                "status": "completed",
                "records_restored": result,
            }
            self.restore_history.append(restore_metadata)
            self._save_restore_metadata(restore_id, restore_metadata, rollback_data)

            logger.info(
                f"Restore {restore_id} completed successfully. "
                f"Total records restored: {sum(result.values())}"
            )

            return {
                "success": True,
                "restore_id": restore_id,
                "records_restored": result,
                "mode": mode,
            }

        except (RestoreValidationError, BackupNotFoundError, RestoreError):
            self.db.rollback()
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during restore: {e}")
            raise RestoreError(f"Database error during restore: {e}") from e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error during restore: {e}")
            raise RestoreError(f"Unexpected error during restore: {e}") from e

    def restore_schedule_range(
        self, backup_id: str, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """
        Restore schedule data for a specific date range.

        Args:
            backup_id: ID of the backup
            start_date: Start date to restore
            end_date: End date to restore

        Returns:
            Restore result summary

        Raises:
            RestoreValidationError: If date range is invalid
            RestoreError: If restore operation fails
            BackupNotFoundError: If backup doesn't exist
        """
        # Validate date range
        if start_date > end_date:
            logger.error(
                f"Invalid date range: start_date ({start_date}) > end_date ({end_date})"
            )
            raise RestoreValidationError(
                f"Invalid date range: start_date ({start_date}) must be <= end_date ({end_date})"
            )

        logger.info(
            f"Restoring schedule range from backup {backup_id}, "
            f"date range: {start_date} to {end_date}"
        )

        try:
            backup_data = self._load_backup(backup_id)

            # Filter data by date range
            logger.debug(
                f"Filtering backup data for date range {start_date} to {end_date}"
            )
            filtered_blocks = [
                b
                for b in backup_data.get("blocks", [])
                if self._date_in_range(b.get("start_date"), start_date, end_date)
            ]
            block_ids = [b["id"] for b in filtered_blocks]

            filtered_assignments = [
                a
                for a in backup_data.get("assignments", [])
                if a.get("block_id") in block_ids
            ]

            filtered_absences = [
                a
                for a in backup_data.get("absences", [])
                if self._date_range_overlaps(
                    a.get("start_date"),
                    a.get("end_date"),
                    start_date.isoformat(),
                    end_date.isoformat(),
                )
            ]

            # Create filtered backup data
            filtered_data = {
                **backup_data,
                "blocks": filtered_blocks,
                "assignments": filtered_assignments,
                "absences": filtered_absences,
            }

            restore_id = str(uuid.uuid4())

            # Delete existing data in range
            logger.debug("Deleting existing blocks in date range")
            self.db.query(Block).filter(
                and_(Block.start_date >= start_date, Block.start_date <= end_date)
            ).delete(synchronize_session=False)

            # Restore filtered data
            logger.debug("Restoring filtered data")
            result = self._restore_data(filtered_data)
            self.db.commit()

            logger.info(
                f"Schedule range restore {restore_id} completed successfully. "
                f"Total records restored: {sum(result.values())}"
            )

            return {
                "success": True,
                "restore_id": restore_id,
                "records_restored": result,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }

        except (RestoreValidationError, BackupNotFoundError):
            self.db.rollback()
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during schedule range restore: {e}")
            raise RestoreError(
                f"Database error during schedule range restore: {e}"
            ) from e
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error during schedule range restore: {e}")
            raise RestoreError(
                f"Unexpected error during schedule range restore: {e}"
            ) from e

    def preview_restore(self, backup_id: str) -> dict[str, Any]:
        """
        Preview what would be restored without making changes.

        Args:
            backup_id: ID of the backup to preview

        Returns:
            Preview summary

        Raises:
            BackupNotFoundError: If backup doesn't exist
            BackupReadError: If backup cannot be read
        """
        logger.info(f"Previewing restore from backup {backup_id}")

        try:
            backup_data = self._load_backup(backup_id)
            preview = self._preview_restore_result(backup_data, mode="replace")
            logger.debug(f"Preview completed for backup {backup_id}")
            return preview
        except (BackupNotFoundError, BackupReadError):
            raise
        except Exception as e:
            logger.error(f"Error previewing restore from backup {backup_id}: {e}")
            raise BackupReadError(f"Failed to preview restore: {e}") from e

    def validate_backup(self, backup_id: str) -> dict[str, Any]:
        """
        Validate backup integrity.

        Args:
            backup_id: ID of the backup to validate

        Returns:
            Validation result dictionary with 'valid' field and details
        """
        logger.debug(f"Validating backup {backup_id}")

        try:
            backup_data = self._load_backup(backup_id)

            # Check required fields
            required_keys = ["backup_id", "backup_type", "created_at"]
            missing_keys = [k for k in required_keys if k not in backup_data]

            if missing_keys:
                logger.warning(
                    f"Backup {backup_id} validation failed: missing keys {missing_keys}"
                )
                return {
                    "valid": False,
                    "error": f"Missing required keys: {missing_keys}",
                }

                # Validate backup_id matches
            if backup_data.get("backup_id") != backup_id:
                logger.warning(
                    f"Backup {backup_id} validation failed: "
                    f"ID mismatch (file contains {backup_data.get('backup_id')})"
                )
                return {
                    "valid": False,
                    "error": f"Backup ID mismatch: expected {backup_id}, "
                    f"found {backup_data.get('backup_id')}",
                }

                # Validate data structure
            validation_results = {
                "valid": True,
                "backup_id": backup_id,
                "backup_type": backup_data.get("backup_type"),
                "created_at": backup_data.get("created_at"),
                "record_counts": {
                    "people": len(backup_data.get("people", [])),
                    "rotation_templates": len(
                        backup_data.get("rotation_templates", [])
                    ),
                    "blocks": len(backup_data.get("blocks", [])),
                    "assignments": len(backup_data.get("assignments", [])),
                    "absences": len(backup_data.get("absences", [])),
                    "schedule_runs": len(backup_data.get("schedule_runs", [])),
                },
            }

            logger.debug(f"Backup {backup_id} validation successful")
            return validation_results

        except (BackupNotFoundError, BackupReadError) as e:
            logger.error(f"Backup {backup_id} validation failed: {e}")
            return {"valid": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error validating backup {backup_id}: {e}")
            return {"valid": False, "error": f"Validation error: {e}"}

    def rollback_restore(self, restore_id: str) -> dict[str, Any]:
        """
        Rollback a previous restore operation.

        Args:
            restore_id: ID of the restore to rollback

        Returns:
            Rollback result

        Raises:
            RestoreRollbackError: If rollback operation fails
            BackupNotFoundError: If restore metadata not found
            FileSecurityError: If path validation fails
        """
        logger.info(f"Starting rollback of restore {restore_id}")

        try:
            # Validate restore_id to prevent path traversal
            restore_id = validate_backup_id(restore_id)

            # Load restore metadata and rollback data
            restore_file = self.backup_path / f"restore_{restore_id}.json"

            # Validate path is within backup directory
            restore_file = validate_file_path(restore_file, self.backup_path)

            if not restore_file.exists():
                logger.error(f"Restore metadata not found for restore {restore_id}")
                raise BackupNotFoundError(
                    f"No restore metadata found for restore ID '{restore_id}'"
                )

            with open(restore_file, encoding="utf-8") as f:
                restore_data = json.load(f)

            rollback_data = restore_data.get("rollback_data")
            if not rollback_data:
                logger.error(f"No rollback data available for restore {restore_id}")
                raise RestoreRollbackError(
                    f"No rollback data available for restore '{restore_id}'"
                )

                # Restore the rollback data
            logger.debug("Restoring rollback data")
            self._restore_data(rollback_data)
            self.db.commit()

            logger.info(f"Rollback of restore {restore_id} completed successfully")
            return {
                "success": True,
                "restore_id": restore_id,
                "message": "Rollback completed successfully",
            }

        except (FileSecurityError, BackupNotFoundError, RestoreRollbackError):
            self.db.rollback()
            raise
        except json.JSONDecodeError as e:
            self.db.rollback()
            logger.error(f"Invalid JSON in restore metadata {restore_id}: {e}")
            raise RestoreRollbackError(
                f"Restore metadata contains invalid JSON: {e}"
            ) from e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during rollback of restore {restore_id}: {e}")
            raise RestoreRollbackError(f"Database error during rollback: {e}") from e
        except OSError as e:
            self.db.rollback()
            logger.error(f"File I/O error during rollback of restore {restore_id}: {e}")
            raise RestoreRollbackError(f"Failed to read restore metadata: {e}") from e
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Unexpected error during rollback of restore {restore_id}: {e}"
            )
            raise RestoreRollbackError(f"Unexpected error during rollback: {e}") from e

            # Private helper methods

    def _load_backup(self, backup_id: str) -> dict[str, Any]:
        """
        Load backup data from file.

        Raises:
            BackupNotFoundError: If backup files don't exist
            BackupReadError: If backup files cannot be read
            FileSecurityError: If path validation fails
        """
        # Validate backup_id to prevent path traversal
        backup_id = validate_backup_id(backup_id)

        metadata_file = self.backup_path / f"metadata_{backup_id}.json"

        # Validate metadata path is within backup directory
        metadata_file = validate_file_path(metadata_file, self.backup_path)

        if not metadata_file.exists():
            logger.error(f"Metadata file not found for backup {backup_id}")
            raise BackupNotFoundError(
                f"Backup with ID '{backup_id}' not found (metadata file missing)"
            )

        try:
            with open(metadata_file, encoding="utf-8") as f:
                metadata = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in metadata file for backup {backup_id}: {e}")
            raise BackupReadError(f"Metadata file contains invalid JSON: {e}") from e
        except OSError as e:
            logger.error(f"Error reading metadata file for backup {backup_id}: {e}")
            raise BackupReadError(f"Failed to read metadata file: {e}") from e

        backup_file = self.backup_path / metadata["filename"]

        # Validate backup file path is within backup directory
        backup_file = validate_file_path(backup_file, self.backup_path)

        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            raise BackupNotFoundError(
                f"Backup file '{metadata['filename']}' not found for backup ID {backup_id}"
            )

        try:
            if metadata.get("compressed", False):
                with gzip.open(backup_file, "rt", encoding="utf-8") as f:
                    return json.load(f)
            else:
                with open(backup_file, encoding="utf-8") as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in backup file {backup_file}: {e}")
            raise BackupReadError(f"Backup file contains invalid JSON: {e}") from e
        except OSError as e:
            logger.error(f"Error reading backup file {backup_file}: {e}")
            raise BackupReadError(f"Failed to read backup file: {e}") from e

    def _replace_restore(self, backup_data: dict[str, Any]) -> dict[str, int]:
        """
        Perform a replace restore (delete all, then restore).

        Raises:
            RestoreDataError: If data restore fails
            SQLAlchemyError: If database operations fail
        """
        try:
            # Delete all existing data (in correct order due to FK constraints)
            logger.debug("Deleting existing data for replace restore")
            self.db.query(Assignment).delete()
            self.db.query(Absence).delete()
            self.db.query(ScheduleRun).delete()
            self.db.query(Block).delete()
            self.db.query(RotationTemplate).delete()
            self.db.query(Person).delete()

            # Restore all data
            logger.debug("Restoring data from backup")
            return self._restore_data(backup_data)

        except SQLAlchemyError as e:
            logger.error(f"Database error during replace restore: {e}")
            raise RestoreDataError(
                f"Failed to delete existing data during replace restore: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Error during replace restore: {e}")
            raise RestoreDataError(f"Failed during replace restore: {e}") from e

    def _merge_restore(self, backup_data: dict[str, Any]) -> dict[str, int]:
        """
        Perform a merge restore (update existing, add new).

        Raises:
            RestoreDataError: If data restore fails
        """
        # For merge, we restore data without deleting
        logger.debug("Performing merge restore")
        return self._restore_data(backup_data)

    def _restore_data(self, backup_data: dict[str, Any]) -> dict[str, int]:
        """
        Restore data from backup dictionary.

        Raises:
            RestoreDataError: If data restore fails
            SQLAlchemyError: If database operations fail
        """
        try:
            counts = {}

            # Restore in correct order (due to FK constraints)
            logger.debug("Restoring people")
            counts["people"] = self._restore_people(backup_data.get("people", []))

            logger.debug("Restoring rotation templates")
            counts["rotation_templates"] = self._restore_rotation_templates(
                backup_data.get("rotation_templates", [])
            )

            logger.debug("Restoring blocks")
            counts["blocks"] = self._restore_blocks(backup_data.get("blocks", []))

            logger.debug("Restoring assignments")
            counts["assignments"] = self._restore_assignments(
                backup_data.get("assignments", [])
            )

            logger.debug("Restoring absences")
            counts["absences"] = self._restore_absences(backup_data.get("absences", []))

            logger.debug("Restoring schedule runs")
            counts["schedule_runs"] = self._restore_schedule_runs(
                backup_data.get("schedule_runs", [])
            )

            logger.debug(f"Restored {sum(counts.values())} total records")
            return counts

        except SQLAlchemyError as e:
            logger.error(f"Database error restoring data: {e}")
            raise RestoreDataError(f"Database error during data restore: {e}") from e
        except Exception as e:
            logger.error(f"Error restoring data: {e}")
            raise RestoreDataError(f"Failed to restore data: {e}") from e

    def _restore_people(self, people_data: list[dict[str, Any]]) -> int:
        """Restore people records."""
        for data in people_data:
            person = Person(**self._prepare_model_data(data))
            self.db.merge(person)
        return len(people_data)

    def _restore_rotation_templates(self, templates_data: list[dict[str, Any]]) -> int:
        """Restore rotation template records."""
        for data in templates_data:
            template = RotationTemplate(**self._prepare_model_data(data))
            self.db.merge(template)
        return len(templates_data)

    def _restore_blocks(self, blocks_data: list[dict[str, Any]]) -> int:
        """Restore block records."""
        for data in blocks_data:
            block = Block(**self._prepare_model_data(data))
            self.db.merge(block)
        return len(blocks_data)

    def _restore_assignments(self, assignments_data: list[dict[str, Any]]) -> int:
        """Restore assignment records."""
        for data in assignments_data:
            assignment = Assignment(**self._prepare_model_data(data))
            self.db.merge(assignment)
        return len(assignments_data)

    def _restore_absences(self, absences_data: list[dict[str, Any]]) -> int:
        """Restore absence records."""
        for data in absences_data:
            absence = Absence(**self._prepare_model_data(data))
            self.db.merge(absence)
        return len(absences_data)

    def _restore_schedule_runs(self, runs_data: list[dict[str, Any]]) -> int:
        """Restore schedule run records."""
        for data in runs_data:
            run = ScheduleRun(**self._prepare_model_data(data))
            self.db.merge(run)
        return len(runs_data)

    def _prepare_model_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Prepare data dictionary for model creation."""
        prepared = {}
        for key, value in data.items():
            if value is None:
                prepared[key] = None
            elif isinstance(value, str) and "date" in key.lower():
                # Convert ISO date strings back to date/datetime objects
                if "T" in value:
                    prepared[key] = datetime.fromisoformat(value)
                else:
                    prepared[key] = date.fromisoformat(value)
            else:
                prepared[key] = value
        return prepared

    def _create_restore_point(self, restore_id: str) -> dict[str, Any]:
        """Create a restore point for potential rollback."""
        # Create a snapshot of current data
        return {
            "people": [self._model_to_dict(p) for p in self.db.query(Person).all()],
            "rotation_templates": [
                self._model_to_dict(t) for t in self.db.query(RotationTemplate).all()
            ],
            "blocks": [self._model_to_dict(b) for b in self.db.query(Block).all()],
            "assignments": [
                self._model_to_dict(a) for a in self.db.query(Assignment).all()
            ],
            "absences": [self._model_to_dict(a) for a in self.db.query(Absence).all()],
            "schedule_runs": [
                self._model_to_dict(r) for r in self.db.query(ScheduleRun).all()
            ],
        }

    def _model_to_dict(self, model: Any) -> dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            if isinstance(value, (datetime, date)):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

    def _preview_restore_result(
        self, backup_data: dict[str, Any], mode: str
    ) -> dict[str, Any]:
        """Generate a preview of restore operation."""
        return {
            "dry_run": True,
            "mode": mode,
            "would_restore": {
                "people": len(backup_data.get("people", [])),
                "rotation_templates": len(backup_data.get("rotation_templates", [])),
                "blocks": len(backup_data.get("blocks", [])),
                "assignments": len(backup_data.get("assignments", [])),
                "absences": len(backup_data.get("absences", [])),
                "schedule_runs": len(backup_data.get("schedule_runs", [])),
            },
            "current_counts": {
                "people": self.db.query(Person).count(),
                "rotation_templates": self.db.query(RotationTemplate).count(),
                "blocks": self.db.query(Block).count(),
                "assignments": self.db.query(Assignment).count(),
                "absences": self.db.query(Absence).count(),
                "schedule_runs": self.db.query(ScheduleRun).count(),
            },
        }

    def _save_restore_metadata(
        self, restore_id: str, metadata: dict[str, Any], rollback_data: dict[str, Any]
    ) -> None:
        """
        Save restore metadata and rollback data.

        Raises:
            RestoreError: If metadata save fails
        """
        try:
            # Validate restore_id to prevent path traversal
            restore_id = validate_backup_id(restore_id)

            restore_file = self.backup_path / f"restore_{restore_id}.json"

            # Validate path is within backup directory
            restore_file = validate_file_path(restore_file, self.backup_path)

            with open(restore_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"metadata": metadata, "rollback_data": rollback_data}, f, indent=2
                )

            logger.debug(f"Saved restore metadata to {restore_file}")

        except (OSError, PermissionError) as e:
            logger.error(f"Error writing restore metadata file: {e}")
            # Don't fail the restore if we can't save metadata
            logger.warning("Continuing without saving restore metadata")

    def _date_in_range(self, date_str: str, start_date: date, end_date: date) -> bool:
        """Check if a date string is within a date range."""
        if not date_str:
            return False
        check_date = date.fromisoformat(date_str.split("T")[0])
        return start_date <= check_date <= end_date

    def _date_range_overlaps(
        self, start1: str, end1: str, start2: str, end2: str
    ) -> bool:
        """Check if two date ranges overlap."""
        if not all([start1, end1, start2, end2]):
            return False
        s1 = date.fromisoformat(start1.split("T")[0])
        e1 = date.fromisoformat(end1.split("T")[0])
        s2 = date.fromisoformat(start2.split("T")[0])
        e2 = date.fromisoformat(end2.split("T")[0])
        return s1 <= e2 and s2 <= e1
