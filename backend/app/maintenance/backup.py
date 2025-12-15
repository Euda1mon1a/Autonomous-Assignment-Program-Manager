"""Backup service for schedule data."""
import json
import gzip
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Person, Assignment, Absence, RotationTemplate, ScheduleRun, Block


class BackupService:
    """Service for creating and managing schedule data backups."""

    def __init__(self, db: Session, backup_dir: str = "backups"):
        """
        Initialize backup service.

        Args:
            db: Database session
            backup_dir: Directory to store backups (default: "backups")
        """
        self.db = db
        self.backup_path = Path(backup_dir)
        self.backup_path.mkdir(parents=True, exist_ok=True)

    def create_backup(self, backup_type: str = 'full', compress: bool = True) -> Dict[str, Any]:
        """
        Create a backup of schedule data.

        Args:
            backup_type: Type of backup ('full' or 'incremental')
            compress: Whether to compress the backup

        Returns:
            Backup metadata dictionary
        """
        backup_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # Collect all data
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
            }
        }

        # Save metadata
        self._save_metadata(backup_id, metadata)
        return metadata

    def create_schedule_snapshot(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Create a backup of schedule data for a specific date range.

        Args:
            start_date: Start date of the snapshot
            end_date: End date of the snapshot

        Returns:
            Backup metadata dictionary
        """
        backup_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        # Get blocks in date range
        blocks = self.db.query(Block).filter(
            and_(Block.start_date >= start_date, Block.start_date <= end_date)
        ).all()
        block_ids = [b.id for b in blocks]

        # Get assignments for these blocks
        assignments = self.db.query(Assignment).filter(
            Assignment.block_id.in_(block_ids)
        ).all() if block_ids else []

        # Get people involved in these assignments
        person_ids = list(set([a.person_id for a in assignments]))
        people = self.db.query(Person).filter(Person.id.in_(person_ids)).all() if person_ids else []

        # Get absences in date range
        absences = self.db.query(Absence).filter(
            and_(Absence.start_date <= end_date, Absence.end_date >= start_date)
        ).all()

        # Get rotation templates used in assignments
        template_ids = list(set([a.rotation_template_id for a in assignments if a.rotation_template_id]))
        templates = self.db.query(RotationTemplate).filter(
            RotationTemplate.id.in_(template_ids)
        ).all() if template_ids else []

        backup_data = {
            "backup_id": backup_id,
            "backup_type": "snapshot",
            "created_at": timestamp.isoformat(),
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "people": [self._model_to_dict(p) for p in people],
            "rotation_templates": [self._model_to_dict(t) for t in templates],
            "blocks": [self._model_to_dict(b) for b in blocks],
            "assignments": [self._model_to_dict(a) for a in assignments],
            "absences": [self._model_to_dict(a) for a in absences],
        }

        filename = f"snapshot_{backup_id}_{start_date}_{end_date}.json.gz"
        filepath = self.backup_path / filename
        self._write_backup(filepath, backup_data, compress=True)

        metadata = {
            "backup_id": backup_id,
            "filename": filename,
            "timestamp": timestamp.isoformat(),
            "type": "snapshot",
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "size_bytes": filepath.stat().st_size,
            "compressed": True,
            "status": "completed",
        }

        self._save_metadata(backup_id, metadata)
        return metadata

    def export_to_json(self, backup_id: str) -> Path:
        """
        Export a backup as uncompressed JSON.

        Args:
            backup_id: ID of the backup to export

        Returns:
            Path to exported JSON file
        """
        metadata = self._load_metadata(backup_id)
        source_path = self.backup_path / metadata["filename"]

        # Read backup data
        if metadata["compressed"]:
            with gzip.open(source_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

        # Write uncompressed JSON
        export_filename = f"export_{backup_id}.json"
        export_path = self.backup_path / export_filename
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return export_path

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata."""
        metadata_files = list(self.backup_path.glob("metadata_*.json"))
        backups = []
        for meta_file in metadata_files:
            with open(meta_file, 'r') as f:
                backups.append(json.load(f))
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup and its metadata.

        Args:
            backup_id: ID of the backup to delete

        Returns:
            True if deletion was successful
        """
        try:
            metadata = self._load_metadata(backup_id)
            backup_file = self.backup_path / metadata["filename"]
            metadata_file = self.backup_path / f"metadata_{backup_id}.json"

            if backup_file.exists():
                backup_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            return True
        except Exception:
            return False

    # Private helper methods

    def _serialize_people(self) -> List[Dict[str, Any]]:
        """Serialize all people to dictionaries."""
        people = self.db.query(Person).all()
        return [self._model_to_dict(p) for p in people]

    def _serialize_rotation_templates(self) -> List[Dict[str, Any]]:
        """Serialize all rotation templates to dictionaries."""
        templates = self.db.query(RotationTemplate).all()
        return [self._model_to_dict(t) for t in templates]

    def _serialize_blocks(self) -> List[Dict[str, Any]]:
        """Serialize all blocks to dictionaries."""
        blocks = self.db.query(Block).all()
        return [self._model_to_dict(b) for b in blocks]

    def _serialize_assignments(self) -> List[Dict[str, Any]]:
        """Serialize all assignments to dictionaries."""
        assignments = self.db.query(Assignment).all()
        return [self._model_to_dict(a) for a in assignments]

    def _serialize_absences(self) -> List[Dict[str, Any]]:
        """Serialize all absences to dictionaries."""
        absences = self.db.query(Absence).all()
        return [self._model_to_dict(a) for a in absences]

    def _serialize_schedule_runs(self) -> List[Dict[str, Any]]:
        """Serialize all schedule runs to dictionaries."""
        runs = self.db.query(ScheduleRun).all()
        return [self._model_to_dict(r) for r in runs]

    def _model_to_dict(self, model: Any) -> Dict[str, Any]:
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

    def _write_backup(self, filepath: Path, data: Dict[str, Any], compress: bool):
        """Write backup data to file."""
        if compress:
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

    def _save_metadata(self, backup_id: str, metadata: Dict[str, Any]):
        """Save backup metadata to file."""
        metadata_file = self.backup_path / f"metadata_{backup_id}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self, backup_id: str) -> Dict[str, Any]:
        """Load backup metadata from file."""
        metadata_file = self.backup_path / f"metadata_{backup_id}.json"
        with open(metadata_file, 'r') as f:
            return json.load(f)
