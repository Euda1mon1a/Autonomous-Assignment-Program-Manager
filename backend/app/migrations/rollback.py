"""Rollback utilities for data migrations.

This module provides functionality to rollback migrations by:
- Creating snapshots before migration
- Restoring from snapshots
- Point-in-time recovery
- Partial rollbacks

Example:
    # Create snapshot before migration
    rollback_mgr = RollbackManager(db_session)
    snapshot_id = rollback_mgr.create_snapshot(
        migration_id,
        query=db.query(Person).filter(Person.type == 'faculty')
    )

    # Execute migration
    migrator.execute_migration(...)

    # Rollback if needed
    rollback_mgr.rollback_to_snapshot(snapshot_id)
"""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.types import GUID

logger = logging.getLogger(__name__)


class RollbackStrategy(str, Enum):
    """Strategy for rolling back migrations."""

    SNAPSHOT = "snapshot"  # Restore from full snapshot
    INCREMENTAL = "incremental"  # Undo changes incrementally
    CUSTOM = "custom"  # Custom rollback function


class RollbackStatus(str, Enum):
    """Status of a rollback operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SnapshotRecord(Base):
    """Database model for storing data snapshots."""

    __tablename__ = "migration_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    migration_id = Column(GUID(), nullable=False, index=True)
    table_name = Column(String(255), nullable=False)

    # Snapshot data
    record_count = Column(Integer, default=0)
    snapshot_data = Column(Text)  # JSON serialized data

    # Metadata
    strategy = Column(String(50), default=RollbackStrategy.SNAPSHOT.value)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SnapshotRecord(migration={self.migration_id}, table={self.table_name})>"


class RollbackRecord(Base):
    """Database model for tracking rollback operations."""

    __tablename__ = "rollback_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    migration_id = Column(GUID(), nullable=False, index=True)
    snapshot_id = Column(GUID(), index=True)

    status = Column(String(50), default=RollbackStatus.PENDING.value)
    strategy = Column(String(50), default=RollbackStrategy.SNAPSHOT.value)

    # Execution details
    records_restored = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<RollbackRecord(migration={self.migration_id}, status={self.status})>"


class RollbackResult:
    """Result of a rollback operation."""

    def __init__(
        self,
        rollback_id: UUID,
        success: bool,
        records_restored: int = 0,
        records_failed: int = 0,
        error_message: Optional[str] = None
    ):
        self.rollback_id = rollback_id
        self.success = success
        self.records_restored = records_restored
        self.records_failed = records_failed
        self.error_message = error_message

    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"<RollbackResult({status}: "
            f"{self.records_restored} restored, {self.records_failed} failed)>"
        )


class RollbackManager:
    """
    Service for managing migration rollbacks.

    Provides snapshot creation, restoration, and rollback tracking.
    """

    def __init__(self, db: Session):
        """
        Initialize the rollback manager.

        Args:
            db: Database session
        """
        self.db = db

    def create_snapshot(
        self,
        migration_id: UUID,
        query: Any,
        table_name: str,
        strategy: RollbackStrategy = RollbackStrategy.SNAPSHOT
    ) -> UUID:
        """
        Create a snapshot of data before migration.

        Args:
            migration_id: Migration ID
            query: SQLAlchemy query for records to snapshot
            table_name: Name of table being snapshotted
            strategy: Rollback strategy

        Returns:
            UUID: Snapshot ID

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            logger.info(f"Creating snapshot for migration {migration_id}, table {table_name}")

            # Get all records
            records = query.all()
            record_count = len(records)

            # Serialize records to JSON
            snapshot_data = []
            for record in records:
                # Get record as dict (excluding relationships)
                record_dict = {}
                for column in record.__table__.columns:
                    value = getattr(record, column.name)

                    # Handle special types
                    if isinstance(value, (datetime, UUID)):
                        value = str(value)

                    record_dict[column.name] = value

                snapshot_data.append(record_dict)

            # Create snapshot record
            snapshot = SnapshotRecord(
                id=uuid.uuid4(),
                migration_id=migration_id,
                table_name=table_name,
                record_count=record_count,
                snapshot_data=json.dumps(snapshot_data),
                strategy=strategy.value
            )

            self.db.add(snapshot)
            self.db.commit()

            logger.info(
                f"Created snapshot {snapshot.id}: {record_count} records from {table_name}"
            )

            return snapshot.id

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to create snapshot: {e}")
            raise

    def get_snapshot(self, snapshot_id: UUID) -> Optional[SnapshotRecord]:
        """
        Get snapshot record by ID.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            SnapshotRecord if found, None otherwise
        """
        return self.db.query(SnapshotRecord).filter(
            SnapshotRecord.id == snapshot_id
        ).first()

    def list_snapshots(self, migration_id: UUID) -> list[SnapshotRecord]:
        """
        List all snapshots for a migration.

        Args:
            migration_id: Migration ID

        Returns:
            List of SnapshotRecord objects
        """
        return self.db.query(SnapshotRecord).filter(
            SnapshotRecord.migration_id == migration_id
        ).order_by(SnapshotRecord.created_at.desc()).all()

    def rollback_to_snapshot(
        self,
        snapshot_id: UUID,
        model_class: Any
    ) -> RollbackResult:
        """
        Rollback to a snapshot by restoring data.

        Args:
            snapshot_id: Snapshot ID to restore from
            model_class: SQLAlchemy model class for the table

        Returns:
            RollbackResult with restoration details

        Example:
            from app.models.person import Person
            result = rollback_mgr.rollback_to_snapshot(snapshot_id, Person)
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        # Create rollback record
        rollback_record = RollbackRecord(
            id=uuid.uuid4(),
            migration_id=snapshot.migration_id,
            snapshot_id=snapshot_id,
            status=RollbackStatus.IN_PROGRESS.value,
            strategy=snapshot.strategy,
            started_at=datetime.utcnow()
        )
        self.db.add(rollback_record)
        self.db.commit()

        records_restored = 0
        records_failed = 0
        error_message = None

        try:
            logger.info(
                f"Rolling back to snapshot {snapshot_id}: "
                f"{snapshot.record_count} records for {snapshot.table_name}"
            )

            # Parse snapshot data
            snapshot_data = json.loads(snapshot.snapshot_data)

            # Restore each record
            for record_data in snapshot_data:
                try:
                    # Get record ID
                    record_id = record_data.get('id')
                    if not record_id:
                        logger.warning("Snapshot record missing ID, skipping")
                        records_failed += 1
                        continue

                    # Convert UUID strings back to UUID
                    if isinstance(record_id, str):
                        record_id = UUID(record_id)

                    # Find existing record
                    existing = self.db.query(model_class).filter(
                        model_class.id == record_id
                    ).first()

                    if existing:
                        # Update existing record
                        for key, value in record_data.items():
                            # Skip relationships
                            if key in existing.__table__.columns.keys():
                                # Convert UUID strings back
                                if isinstance(value, str):
                                    try:
                                        value = UUID(value)
                                    except (ValueError, TypeError):
                                        pass

                                setattr(existing, key, value)

                        records_restored += 1

                    else:
                        # Record was deleted during migration, recreate it
                        new_record = model_class(**record_data)
                        self.db.add(new_record)
                        records_restored += 1

                except Exception as e:
                    logger.warning(f"Failed to restore record: {e}")
                    records_failed += 1

                    if not error_message:
                        error_message = str(e)

            # Commit restoration
            self.db.commit()

            # Update rollback record
            success = records_failed == 0
            rollback_record.status = (
                RollbackStatus.COMPLETED.value if success else RollbackStatus.FAILED.value
            )
            rollback_record.records_restored = records_restored
            rollback_record.records_failed = records_failed
            rollback_record.error_message = error_message
            rollback_record.completed_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                f"Rollback completed: {records_restored} restored, {records_failed} failed"
            )

            return RollbackResult(
                rollback_id=rollback_record.id,
                success=success,
                records_restored=records_restored,
                records_failed=records_failed,
                error_message=error_message
            )

        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            self.db.rollback()

            # Update rollback record
            rollback_record.status = RollbackStatus.FAILED.value
            rollback_record.error_message = str(e)
            rollback_record.completed_at = datetime.utcnow()
            self.db.commit()

            return RollbackResult(
                rollback_id=rollback_record.id,
                success=False,
                records_restored=records_restored,
                records_failed=records_failed,
                error_message=str(e)
            )

    def rollback_migration(
        self,
        migration_id: UUID,
        model_class: Any
    ) -> RollbackResult:
        """
        Rollback a migration using its most recent snapshot.

        Args:
            migration_id: Migration ID to rollback
            model_class: SQLAlchemy model class for the table

        Returns:
            RollbackResult

        Raises:
            ValueError: If no snapshot found for migration
        """
        # Find most recent snapshot
        snapshots = self.list_snapshots(migration_id)
        if not snapshots:
            raise ValueError(f"No snapshot found for migration {migration_id}")

        snapshot = snapshots[0]  # Most recent
        logger.info(f"Rolling back migration {migration_id} using snapshot {snapshot.id}")

        return self.rollback_to_snapshot(snapshot.id, model_class)

    def delete_snapshot(self, snapshot_id: UUID) -> None:
        """
        Delete a snapshot.

        Args:
            snapshot_id: Snapshot ID to delete
        """
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot:
            self.db.delete(snapshot)
            self.db.commit()
            logger.info(f"Deleted snapshot {snapshot_id}")

    def cleanup_old_snapshots(self, days: int = 30) -> int:
        """
        Delete snapshots older than specified days.

        Args:
            days: Delete snapshots older than this many days

        Returns:
            Number of snapshots deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            deleted = self.db.query(SnapshotRecord).filter(
                SnapshotRecord.created_at < cutoff_date
            ).delete()

            self.db.commit()
            logger.info(f"Cleaned up {deleted} snapshots older than {days} days")

            return deleted

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup snapshots: {e}")
            raise

    def get_rollback_history(
        self,
        migration_id: Optional[UUID] = None,
        limit: int = 50
    ) -> list[RollbackRecord]:
        """
        Get rollback history with optional filtering.

        Args:
            migration_id: Filter by migration ID
            limit: Maximum number of records to return

        Returns:
            List of RollbackRecord objects
        """
        query = self.db.query(RollbackRecord)

        if migration_id:
            query = query.filter(RollbackRecord.migration_id == migration_id)

        return query.order_by(RollbackRecord.created_at.desc()).limit(limit).all()

    def estimate_rollback_time(self, snapshot_id: UUID) -> dict[str, Any]:
        """
        Estimate time required for rollback based on snapshot size.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Dictionary with time estimates
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        # Rough estimates (adjust based on your system)
        RECORDS_PER_SECOND = 100

        estimated_seconds = snapshot.record_count / RECORDS_PER_SECOND

        return {
            'snapshot_id': str(snapshot_id),
            'record_count': snapshot.record_count,
            'estimated_seconds': round(estimated_seconds, 2),
            'estimated_minutes': round(estimated_seconds / 60, 2)
        }
