"""Restore service for schedule data."""
import gzip
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Absence, Assignment, Block, Person, RotationTemplate, ScheduleRun


class RestoreService:
    """Service for restoring schedule data from backups."""

    def __init__(self, db: Session, backup_dir: str = "backups"):
        """
        Initialize restore service.

        Args:
            db: Database session
            backup_dir: Directory containing backups (default: "backups")
        """
        self.db = db
        self.backup_path = Path(backup_dir)
        self.restore_history: list[dict[str, Any]] = []

    def restore_from_backup(
        self,
        backup_id: str,
        options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Restore data from a backup.

        Args:
            backup_id: ID of the backup to restore
            options: Restore options (mode: 'replace' or 'merge', dry_run: bool)

        Returns:
            Restore result summary
        """
        options = options or {}
        mode = options.get('mode', 'replace')
        dry_run = options.get('dry_run', False)

        # Load backup data
        backup_data = self._load_backup(backup_id)

        # Validate before restoring
        validation = self.validate_backup(backup_id)
        if not validation['valid']:
            return {
                "success": False,
                "error": "Backup validation failed",
                "details": validation
            }

        restore_id = str(uuid.uuid4())
        restore_timestamp = datetime.utcnow()

        if dry_run:
            return self._preview_restore_result(backup_data, mode)

        # Create restore point for rollback
        rollback_data = self._create_restore_point(restore_id)

        try:
            if mode == 'replace':
                result = self._replace_restore(backup_data)
            else:
                result = self._merge_restore(backup_data)

            # Commit transaction
            self.db.commit()

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

            return {
                "success": True,
                "restore_id": restore_id,
                "records_restored": result,
                "mode": mode,
            }

        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "restore_id": restore_id,
            }

    def restore_schedule_range(
        self,
        backup_id: str,
        start_date: date,
        end_date: date
    ) -> dict[str, Any]:
        """
        Restore schedule data for a specific date range.

        Args:
            backup_id: ID of the backup
            start_date: Start date to restore
            end_date: End date to restore

        Returns:
            Restore result summary
        """
        backup_data = self._load_backup(backup_id)

        # Filter data by date range
        filtered_blocks = [
            b for b in backup_data.get("blocks", [])
            if self._date_in_range(b.get("start_date"), start_date, end_date)
        ]
        block_ids = [b["id"] for b in filtered_blocks]

        filtered_assignments = [
            a for a in backup_data.get("assignments", [])
            if a.get("block_id") in block_ids
        ]

        filtered_absences = [
            a for a in backup_data.get("absences", [])
            if self._date_range_overlaps(
                a.get("start_date"), a.get("end_date"),
                start_date.isoformat(), end_date.isoformat()
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

        try:
            # Delete existing data in range
            self.db.query(Block).filter(
                and_(Block.start_date >= start_date, Block.start_date <= end_date)
            ).delete(synchronize_session=False)

            # Restore filtered data
            result = self._restore_data(filtered_data)
            self.db.commit()

            return {
                "success": True,
                "restore_id": restore_id,
                "records_restored": result,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }

        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "restore_id": restore_id,
            }

    def preview_restore(self, backup_id: str) -> dict[str, Any]:
        """
        Preview what would be restored without making changes.

        Args:
            backup_id: ID of the backup to preview

        Returns:
            Preview summary
        """
        backup_data = self._load_backup(backup_id)
        return self._preview_restore_result(backup_data, mode='replace')

    def validate_backup(self, backup_id: str) -> dict[str, Any]:
        """
        Validate backup integrity.

        Args:
            backup_id: ID of the backup to validate

        Returns:
            Validation result
        """
        try:
            backup_data = self._load_backup(backup_id)

            # Check required fields
            required_keys = ["backup_id", "backup_type", "created_at"]
            missing_keys = [k for k in required_keys if k not in backup_data]

            if missing_keys:
                return {
                    "valid": False,
                    "error": f"Missing required keys: {missing_keys}"
                }

            # Validate data structure
            validation_results = {
                "valid": True,
                "backup_id": backup_id,
                "backup_type": backup_data.get("backup_type"),
                "created_at": backup_data.get("created_at"),
                "record_counts": {
                    "people": len(backup_data.get("people", [])),
                    "rotation_templates": len(backup_data.get("rotation_templates", [])),
                    "blocks": len(backup_data.get("blocks", [])),
                    "assignments": len(backup_data.get("assignments", [])),
                    "absences": len(backup_data.get("absences", [])),
                    "schedule_runs": len(backup_data.get("schedule_runs", [])),
                }
            }

            return validation_results

        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

    def rollback_restore(self, restore_id: str) -> dict[str, Any]:
        """
        Rollback a previous restore operation.

        Args:
            restore_id: ID of the restore to rollback

        Returns:
            Rollback result
        """
        try:
            # Load restore metadata and rollback data
            restore_file = self.backup_path / f"restore_{restore_id}.json"
            with open(restore_file) as f:
                restore_data = json.load(f)

            rollback_data = restore_data.get("rollback_data")
            if not rollback_data:
                return {
                    "success": False,
                    "error": "No rollback data available"
                }

            # Restore the rollback data
            self._restore_data(rollback_data)
            self.db.commit()

            return {
                "success": True,
                "restore_id": restore_id,
                "message": "Rollback completed successfully"
            }

        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    # Private helper methods

    def _load_backup(self, backup_id: str) -> dict[str, Any]:
        """Load backup data from file."""
        metadata_file = self.backup_path / f"metadata_{backup_id}.json"
        with open(metadata_file) as f:
            metadata = json.load(f)

        backup_file = self.backup_path / metadata["filename"]

        if metadata.get("compressed", False):
            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(backup_file, encoding='utf-8') as f:
                return json.load(f)

    def _replace_restore(self, backup_data: dict[str, Any]) -> dict[str, int]:
        """Perform a replace restore (delete all, then restore)."""
        # Delete all existing data (in correct order due to FK constraints)
        self.db.query(Assignment).delete()
        self.db.query(Absence).delete()
        self.db.query(ScheduleRun).delete()
        self.db.query(Block).delete()
        self.db.query(RotationTemplate).delete()
        self.db.query(Person).delete()

        # Restore all data
        return self._restore_data(backup_data)

    def _merge_restore(self, backup_data: dict[str, Any]) -> dict[str, int]:
        """Perform a merge restore (update existing, add new)."""
        # For merge, we restore data without deleting
        return self._restore_data(backup_data)

    def _restore_data(self, backup_data: dict[str, Any]) -> dict[str, int]:
        """Restore data from backup dictionary."""
        counts = {}

        # Restore in correct order (due to FK constraints)
        counts['people'] = self._restore_people(backup_data.get("people", []))
        counts['rotation_templates'] = self._restore_rotation_templates(
            backup_data.get("rotation_templates", [])
        )
        counts['blocks'] = self._restore_blocks(backup_data.get("blocks", []))
        counts['assignments'] = self._restore_assignments(backup_data.get("assignments", []))
        counts['absences'] = self._restore_absences(backup_data.get("absences", []))
        counts['schedule_runs'] = self._restore_schedule_runs(
            backup_data.get("schedule_runs", [])
        )

        return counts

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
            elif isinstance(value, str) and 'date' in key.lower():
                # Convert ISO date strings back to date/datetime objects
                if 'T' in value:
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
            "rotation_templates": [self._model_to_dict(t) for t in self.db.query(RotationTemplate).all()],
            "blocks": [self._model_to_dict(b) for b in self.db.query(Block).all()],
            "assignments": [self._model_to_dict(a) for a in self.db.query(Assignment).all()],
            "absences": [self._model_to_dict(a) for a in self.db.query(Absence).all()],
            "schedule_runs": [self._model_to_dict(r) for r in self.db.query(ScheduleRun).all()],
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

    def _preview_restore_result(self, backup_data: dict[str, Any], mode: str) -> dict[str, Any]:
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
            }
        }

    def _save_restore_metadata(
        self,
        restore_id: str,
        metadata: dict[str, Any],
        rollback_data: dict[str, Any]
    ):
        """Save restore metadata and rollback data."""
        restore_file = self.backup_path / f"restore_{restore_id}.json"
        with open(restore_file, 'w') as f:
            json.dump({
                "metadata": metadata,
                "rollback_data": rollback_data
            }, f, indent=2)

    def _date_in_range(self, date_str: str, start_date: date, end_date: date) -> bool:
        """Check if a date string is within a date range."""
        if not date_str:
            return False
        check_date = date.fromisoformat(date_str.split('T')[0])
        return start_date <= check_date <= end_date

    def _date_range_overlaps(
        self,
        start1: str,
        end1: str,
        start2: str,
        end2: str
    ) -> bool:
        """Check if two date ranges overlap."""
        if not all([start1, end1, start2, end2]):
            return False
        s1 = date.fromisoformat(start1.split('T')[0])
        e1 = date.fromisoformat(end1.split('T')[0])
        s2 = date.fromisoformat(start2.split('T')[0])
        e2 = date.fromisoformat(end2.split('T')[0])
        return s1 <= e2 and s2 <= e1
