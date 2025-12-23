"""Backup service for schedule data."""

import gzip
import json
import logging
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

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
    BackupCreationError,
    BackupNotFoundError,
    BackupPermissionError,
    BackupReadError,
    BackupStorageError,
    BackupValidationError,
    BackupWriteError,
)
from app.models import Absence, Assignment, Block, Person, RotationTemplate, ScheduleRun

logger = logging.getLogger(__name__)


class BackupService:
    """Service for creating and managing schedule data backups."""

    def __init__(self, db: Session, backup_dir: str = "backups"):
        """
        Initialize backup service.

        Args:
            db: Database session
            backup_dir: Directory to store backups (default: "backups")

        Raises:
            BackupPermissionError: If backup directory cannot be created or accessed
        """
        self.db = db
        self.backup_path = Path(backup_dir)

        try:
            self.backup_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initialized BackupService with directory: {self.backup_path}")

            # Validate write permissions
            self._validate_directory_permissions()
        except PermissionError as e:
            logger.error(
                f"Permission denied creating backup directory {backup_dir}: {e}"
            )
            raise BackupPermissionError(
                f"Cannot create or access backup directory '{backup_dir}': {e}"
            ) from e
        except OSError as e:
            logger.error(f"OS error creating backup directory {backup_dir}: {e}")
            raise BackupPermissionError(
                f"Failed to create backup directory '{backup_dir}': {e}"
            ) from e

    def create_backup(
        self, backup_type: str = "full", compress: bool = True
    ) -> dict[str, Any]:
        """
        Create a backup of schedule data.

        Args:
            backup_type: Type of backup ('full' or 'incremental')
            compress: Whether to compress the backup

        Returns:
            Backup metadata dictionary

        Raises:
            BackupValidationError: If backup_type is invalid
            BackupCreationError: If backup creation fails
            BackupStorageError: If insufficient disk space
            SQLAlchemyError: If database query fails
        """
        # Validate backup type
        if backup_type not in ("full", "incremental"):
            logger.error(f"Invalid backup type: {backup_type}")
            raise BackupValidationError(
                f"Invalid backup_type '{backup_type}'. Must be 'full' or 'incremental'."
            )

        backup_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        logger.info(f"Starting {backup_type} backup with ID: {backup_id}")

        try:
            # Check available disk space before proceeding
            self._check_disk_space()

            # Collect all data
            logger.debug("Serializing database tables for backup")
            backup_data = {
                "backup_id": backup_id,
                "backup_type": backup_type,
                "created_at": timestamp.isoformat(),
                "people": self._serialize_people(),
                "rotation_templates": self._serialize_rotation_templates(),
                "blocks": self._serialize_blocks(),
                "assignments": self._serialize_assignments(),
                "absences": self._serialize_absences(),
                "schedule_runs": self._serialize_schedule_runs(),
            }

            # Save backup
            filename = f"backup_{backup_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            if compress:
                filename += ".gz"

            filepath = self.backup_path / filename
            logger.debug(f"Writing backup to file: {filepath}")
            self._write_backup(filepath, backup_data, compress)

            # Create metadata
            metadata = {
                "backup_id": backup_id,
                "filename": filename,
                "timestamp": timestamp.isoformat(),
                "type": backup_type,
                "size_bytes": filepath.stat().st_size,
                "compressed": compress,
                "status": "completed",
                "record_counts": {
                    "people": len(backup_data["people"]),
                    "rotation_templates": len(backup_data["rotation_templates"]),
                    "blocks": len(backup_data["blocks"]),
                    "assignments": len(backup_data["assignments"]),
                    "absences": len(backup_data["absences"]),
                    "schedule_runs": len(backup_data["schedule_runs"]),
                },
            }

            # Save metadata
            self._save_metadata(backup_id, metadata)
            logger.info(
                f"Backup {backup_id} completed successfully. "
                f"Size: {metadata['size_bytes']} bytes, "
                f"Total records: {sum(metadata['record_counts'].values())}"
            )
            return metadata

        except SQLAlchemyError as e:
            logger.error(f"Database error during backup {backup_id}: {e}")
            raise BackupCreationError(
                f"Failed to read database during backup creation: {e}"
            ) from e
        except OSError as e:
            logger.error(f"File I/O error during backup {backup_id}: {e}")
            raise BackupCreationError(
                f"Failed to write backup file '{filename}': {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during backup {backup_id}: {e}")
            raise BackupCreationError(
                f"Unexpected error during backup creation: {e}"
            ) from e

    def create_schedule_snapshot(
        self, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """
        Create a backup of schedule data for a specific date range.

        Args:
            start_date: Start date of the snapshot
            end_date: End date of the snapshot

        Returns:
            Backup metadata dictionary

        Raises:
            BackupValidationError: If date range is invalid
            BackupCreationError: If snapshot creation fails
            SQLAlchemyError: If database query fails
        """
        # Validate date range
        if start_date > end_date:
            logger.error(
                f"Invalid date range: start_date ({start_date}) > end_date ({end_date})"
            )
            raise BackupValidationError(
                f"Invalid date range: start_date ({start_date}) must be <= end_date ({end_date})"
            )

        backup_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        logger.info(
            f"Starting schedule snapshot with ID: {backup_id}, "
            f"date range: {start_date} to {end_date}"
        )

        try:
            # Check available disk space before proceeding
            self._check_disk_space()

            # Get blocks in date range
            logger.debug(f"Querying blocks in date range {start_date} to {end_date}")
            blocks = (
                self.db.query(Block)
                .filter(
                    and_(Block.start_date >= start_date, Block.start_date <= end_date)
                )
                .all()
            )
            block_ids = [b.id for b in blocks]

            # Get assignments for these blocks
            assignments = (
                self.db.query(Assignment)
                .filter(Assignment.block_id.in_(block_ids))
                .all()
                if block_ids
                else []
            )

            # Get people involved in these assignments
            person_ids = list({a.person_id for a in assignments})
            people = (
                self.db.query(Person).filter(Person.id.in_(person_ids)).all()
                if person_ids
                else []
            )

            # Get absences in date range
            absences = (
                self.db.query(Absence)
                .filter(
                    and_(Absence.start_date <= end_date, Absence.end_date >= start_date)
                )
                .all()
            )

            # Get rotation templates used in assignments
            template_ids = list(
                {a.rotation_template_id for a in assignments if a.rotation_template_id}
            )
            templates = (
                self.db.query(RotationTemplate)
                .filter(RotationTemplate.id.in_(template_ids))
                .all()
                if template_ids
                else []
            )

            backup_data = {
                "backup_id": backup_id,
                "backup_type": "snapshot",
                "created_at": timestamp.isoformat(),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "people": [self._model_to_dict(p) for p in people],
                "rotation_templates": [self._model_to_dict(t) for t in templates],
                "blocks": [self._model_to_dict(b) for b in blocks],
                "assignments": [self._model_to_dict(a) for a in assignments],
                "absences": [self._model_to_dict(a) for a in absences],
            }

            filename = f"snapshot_{backup_id}_{start_date}_{end_date}.json.gz"
            filepath = self.backup_path / filename
            logger.debug(f"Writing snapshot to file: {filepath}")
            self._write_backup(filepath, backup_data, compress=True)

            metadata = {
                "backup_id": backup_id,
                "filename": filename,
                "timestamp": timestamp.isoformat(),
                "type": "snapshot",
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "size_bytes": filepath.stat().st_size,
                "compressed": True,
                "status": "completed",
            }

            self._save_metadata(backup_id, metadata)
            logger.info(
                f"Snapshot {backup_id} completed successfully. "
                f"Size: {metadata['size_bytes']} bytes"
            )
            return metadata

        except SQLAlchemyError as e:
            logger.error(f"Database error during snapshot {backup_id}: {e}")
            raise BackupCreationError(
                f"Failed to query database during snapshot creation: {e}"
            ) from e
        except OSError as e:
            logger.error(f"File I/O error during snapshot {backup_id}: {e}")
            raise BackupCreationError(f"Failed to write snapshot file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during snapshot {backup_id}: {e}")
            raise BackupCreationError(
                f"Unexpected error during snapshot creation: {e}"
            ) from e

    def export_to_json(self, backup_id: str) -> Path:
        """
        Export a backup as uncompressed JSON.

        Args:
            backup_id: ID of the backup to export

        Returns:
            Path to exported JSON file

        Raises:
            BackupNotFoundError: If backup doesn't exist
            BackupReadError: If backup file cannot be read
            BackupWriteError: If export file cannot be written
            FileSecurityError: If path validation fails
        """
        logger.info(f"Exporting backup {backup_id} to uncompressed JSON")

        try:
            # Validate backup_id to prevent path traversal
            backup_id = validate_backup_id(backup_id)

            metadata = self._load_metadata(backup_id)
            source_path = self.backup_path / metadata["filename"]

            # Validate source path is within backup directory
            source_path = validate_file_path(source_path, self.backup_path)

            if not source_path.exists():
                logger.error(f"Backup file not found: {source_path}")
                raise BackupNotFoundError(
                    f"Backup file '{metadata['filename']}' not found for backup ID {backup_id}"
                )

            # Read backup data
            logger.debug(f"Reading backup file: {source_path}")
            if metadata["compressed"]:
                with gzip.open(source_path, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                with open(source_path, encoding="utf-8") as f:
                    data = json.load(f)

            # Write uncompressed JSON
            export_filename = f"export_{backup_id}.json"
            export_path = self.backup_path / export_filename

            # Validate export path is within backup directory
            export_path = validate_file_path(export_path, self.backup_path)

            logger.debug(f"Writing export to: {export_path}")
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Successfully exported backup {backup_id} to {export_path}")
            return export_path

        except FileSecurityError:
            raise
        except BackupNotFoundError:
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in backup {backup_id}: {e}")
            raise BackupReadError(f"Backup file contains invalid JSON: {e}") from e
        except OSError as e:
            if "read" in str(e).lower() or not Path(source_path).exists():
                logger.error(f"Error reading backup {backup_id}: {e}")
                raise BackupReadError(f"Failed to read backup file: {e}") from e
            else:
                logger.error(f"Error writing export for backup {backup_id}: {e}")
                raise BackupWriteError(f"Failed to write export file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error exporting backup {backup_id}: {e}")
            raise BackupReadError(f"Unexpected error during export: {e}") from e

    def list_backups(self) -> list[dict[str, Any]]:
        """
        List all available backups with metadata.

        Returns:
            List of backup metadata dictionaries, sorted by timestamp (newest first)

        Raises:
            BackupReadError: If metadata files cannot be read
        """
        logger.debug(f"Listing backups in directory: {self.backup_path}")

        try:
            metadata_files = list(self.backup_path.glob("metadata_*.json"))
            backups = []

            for meta_file in metadata_files:
                try:
                    with open(meta_file, encoding="utf-8") as f:
                        backups.append(json.load(f))
                except (OSError, json.JSONDecodeError) as e:
                    logger.warning(
                        f"Skipping invalid metadata file {meta_file.name}: {e}"
                    )
                    continue

            logger.info(f"Found {len(backups)} backup(s)")
            return sorted(backups, key=lambda x: x.get("timestamp", ""), reverse=True)

        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            raise BackupReadError(f"Failed to list backups: {e}") from e

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup and its metadata.

        Args:
            backup_id: ID of the backup to delete

        Returns:
            True if deletion was successful

        Raises:
            BackupNotFoundError: If backup doesn't exist
            BackupPermissionError: If files cannot be deleted
            FileSecurityError: If path validation fails
        """
        logger.info(f"Deleting backup {backup_id}")

        try:
            # Validate backup_id to prevent path traversal
            backup_id = validate_backup_id(backup_id)

            metadata = self._load_metadata(backup_id)
            backup_file = self.backup_path / metadata["filename"]
            metadata_file = self.backup_path / f"metadata_{backup_id}.json"

            # Validate paths are within backup directory
            backup_file = validate_file_path(backup_file, self.backup_path)
            metadata_file = validate_file_path(metadata_file, self.backup_path)

            # Delete backup file
            if backup_file.exists():
                logger.debug(f"Deleting backup file: {backup_file}")
                backup_file.unlink()
            else:
                logger.warning(f"Backup file not found: {backup_file}")

            # Delete metadata file
            if metadata_file.exists():
                logger.debug(f"Deleting metadata file: {metadata_file}")
                metadata_file.unlink()
            else:
                logger.warning(f"Metadata file not found: {metadata_file}")

            logger.info(f"Successfully deleted backup {backup_id}")
            return True

        except FileSecurityError:
            raise
        except BackupNotFoundError:
            raise
        except PermissionError as e:
            logger.error(f"Permission denied deleting backup {backup_id}: {e}")
            raise BackupPermissionError(
                f"Permission denied when deleting backup {backup_id}: {e}"
            ) from e
        except OSError as e:
            logger.error(f"OS error deleting backup {backup_id}: {e}")
            raise BackupPermissionError(
                f"Failed to delete backup {backup_id}: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error deleting backup {backup_id}: {e}")
            raise BackupPermissionError(f"Unexpected error deleting backup: {e}") from e

    # Private helper methods

    def _serialize_people(self) -> list[dict[str, Any]]:
        """Serialize all people to dictionaries."""
        people = self.db.query(Person).all()
        return [self._model_to_dict(p) for p in people]

    def _serialize_rotation_templates(self) -> list[dict[str, Any]]:
        """Serialize all rotation templates to dictionaries."""
        templates = self.db.query(RotationTemplate).all()
        return [self._model_to_dict(t) for t in templates]

    def _serialize_blocks(self) -> list[dict[str, Any]]:
        """Serialize all blocks to dictionaries."""
        blocks = self.db.query(Block).all()
        return [self._model_to_dict(b) for b in blocks]

    def _serialize_assignments(self) -> list[dict[str, Any]]:
        """Serialize all assignments to dictionaries."""
        assignments = self.db.query(Assignment).all()
        return [self._model_to_dict(a) for a in assignments]

    def _serialize_absences(self) -> list[dict[str, Any]]:
        """Serialize all absences to dictionaries."""
        absences = self.db.query(Absence).all()
        return [self._model_to_dict(a) for a in absences]

    def _serialize_schedule_runs(self) -> list[dict[str, Any]]:
        """Serialize all schedule runs to dictionaries."""
        runs = self.db.query(ScheduleRun).all()
        return [self._model_to_dict(r) for r in runs]

    def _model_to_dict(self, model: Any) -> dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            if isinstance(value, (datetime, date)):
                result[column.name] = value.isoformat()
            elif isinstance(value, UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result

    def _write_backup(self, filepath: Path, data: dict[str, Any], compress: bool):
        """
        Write backup data to file.

        Raises:
            BackupWriteError: If file write fails
            BackupPermissionError: If permission denied
        """
        try:
            if compress:
                with gzip.open(filepath, "wt", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
        except PermissionError as e:
            logger.error(f"Permission denied writing backup file {filepath}: {e}")
            raise BackupPermissionError(
                f"Permission denied writing backup file: {e}"
            ) from e
        except OSError as e:
            logger.error(f"I/O error writing backup file {filepath}: {e}")
            raise BackupWriteError(f"Failed to write backup file: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error writing backup file {filepath}: {e}")
            raise BackupWriteError(f"Unexpected error writing backup file: {e}") from e

    def _save_metadata(self, backup_id: str, metadata: dict[str, Any]):
        """
        Save backup metadata to file.

        Raises:
            BackupWriteError: If metadata write fails
        """
        metadata_file = self.backup_path / f"metadata_{backup_id}.json"

        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except (OSError, PermissionError) as e:
            logger.error(f"Error writing metadata file {metadata_file}: {e}")
            raise BackupWriteError(f"Failed to write metadata file: {e}") from e

    def _load_metadata(self, backup_id: str) -> dict[str, Any]:
        """
        Load backup metadata from file.

        Raises:
            BackupNotFoundError: If metadata file doesn't exist
            BackupReadError: If metadata file cannot be read
            FileSecurityError: If path validation fails
        """
        # Validate backup_id to prevent path traversal
        backup_id = validate_backup_id(backup_id)

        metadata_file = self.backup_path / f"metadata_{backup_id}.json"

        # Validate path is within backup directory
        metadata_file = validate_file_path(metadata_file, self.backup_path)

        if not metadata_file.exists():
            logger.error(f"Metadata file not found for backup {backup_id}")
            raise BackupNotFoundError(
                f"Backup with ID '{backup_id}' not found (metadata file missing)"
            )

        try:
            with open(metadata_file, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in metadata file {metadata_file}: {e}")
            raise BackupReadError(f"Metadata file contains invalid JSON: {e}") from e
        except OSError as e:
            logger.error(f"Error reading metadata file {metadata_file}: {e}")
            raise BackupReadError(f"Failed to read metadata file: {e}") from e

    def _validate_directory_permissions(self):
        """
        Validate that the backup directory has proper read/write permissions.

        Raises:
            BackupPermissionError: If directory is not readable or writable
        """
        if not os.access(self.backup_path, os.R_OK):
            raise BackupPermissionError(
                f"Backup directory '{self.backup_path}' is not readable"
            )

        if not os.access(self.backup_path, os.W_OK):
            raise BackupPermissionError(
                f"Backup directory '{self.backup_path}' is not writable"
            )

    def _check_disk_space(self, min_free_mb: int = 100):
        """
        Check if there is sufficient disk space for backup operations.

        Args:
            min_free_mb: Minimum free space required in megabytes (default: 100MB)

        Raises:
            BackupStorageError: If insufficient disk space
        """
        try:
            stat = os.statvfs(self.backup_path)
            # Available space in bytes
            available_bytes = stat.f_bavail * stat.f_frsize
            available_mb = available_bytes / (1024 * 1024)

            if available_mb < min_free_mb:
                logger.error(
                    f"Insufficient disk space: {available_mb:.2f}MB available, "
                    f"{min_free_mb}MB required"
                )
                raise BackupStorageError(
                    f"Insufficient disk space for backup. Available: {available_mb:.2f}MB, "
                    f"Required: {min_free_mb}MB"
                )

            logger.debug(f"Disk space check passed: {available_mb:.2f}MB available")

        except BackupStorageError:
            raise
        except Exception as e:
            logger.warning(f"Unable to check disk space: {e}")
            # Don't fail the backup if we can't check disk space
            pass
