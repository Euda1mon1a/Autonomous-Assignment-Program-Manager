"""Data migrator service for batch database operations.

This module provides the core migration functionality including:
- Creating and tracking migrations
- Batch processing with progress tracking
- Dry-run mode for testing
- Transaction management
- Error handling and recovery

Example:
    migrator = DataMigrator(db_session)
    migration_id = migrator.create_migration(
        name="update_person_emails",
        description="Normalize all person email addresses"
    )

    # Execute with dry run first
    result = migrator.execute_migration(
        migration_id,
        transform_func=normalize_emails,
        dry_run=True
    )

    # If dry run succeeds, execute for real
    if result.success:
        migrator.execute_migration(
            migration_id,
            transform_func=normalize_emails,
            dry_run=False
        )
"""

import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.types import GUID

logger = logging.getLogger(__name__)


class MigrationStatus(str, Enum):
    """Status of a data migration."""

    PENDING = "pending"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    DRY_RUN = "dry_run"


class MigrationRecord(Base):
    """Database model for tracking migration history."""

    __tablename__ = "migration_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(
        String(50), nullable=False, default=MigrationStatus.PENDING.value, index=True
    )

    # Execution details
    batch_size = Column(Integer, default=100)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text)
    error_details = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Created by
    created_by = Column(String(255))

    def __repr__(self):
        return f"<MigrationRecord(name='{self.name}', status='{self.status}')>"


class MigrationResult:
    """Result of a migration execution."""

    def __init__(
        self,
        migration_id: UUID,
        success: bool,
        total_records: int = 0,
        processed_records: int = 0,
        failed_records: int = 0,
        error_message: str | None = None,
        dry_run: bool = False,
    ):
        self.migration_id = migration_id
        self.success = success
        self.total_records = total_records
        self.processed_records = processed_records
        self.failed_records = failed_records
        self.error_message = error_message
        self.dry_run = dry_run

    def __repr__(self):
        mode = "DRY RUN" if self.dry_run else "EXECUTION"
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"<MigrationResult({mode} {status}: "
            f"{self.processed_records}/{self.total_records} processed, "
            f"{self.failed_records} failed)>"
        )


class DataMigrator:
    """
    Core service for data migrations.

    Provides batch processing, progress tracking, and transaction management
    for database migrations.
    """

    def __init__(self, db: Session):
        """
        Initialize the data migrator.

        Args:
            db: Database session
        """
        self.db = db

    def create_migration(
        self,
        name: str,
        description: str,
        batch_size: int = 100,
        created_by: str | None = None,
    ) -> UUID:
        """
        Create a new migration record.

        Args:
            name: Name of the migration
            description: Description of what the migration does
            batch_size: Number of records to process per batch
            created_by: User/system creating the migration

        Returns:
            UUID: Migration ID

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            migration = MigrationRecord(
                id=uuid.uuid4(),
                name=name,
                description=description,
                batch_size=batch_size,
                created_by=created_by,
                status=MigrationStatus.PENDING.value,
            )

            self.db.add(migration)
            self.db.commit()

            logger.info(f"Created migration: {migration.id} - {name}")
            return migration.id

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to create migration: {e}")
            raise

    def get_migration(self, migration_id: UUID) -> MigrationRecord | None:
        """
        Get migration record by ID.

        Args:
            migration_id: Migration ID

        Returns:
            MigrationRecord if found, None otherwise
        """
        return (
            self.db.query(MigrationRecord)
            .filter(MigrationRecord.id == migration_id)
            .first()
        )

    def update_status(
        self,
        migration_id: UUID,
        status: MigrationStatus,
        error_message: str | None = None,
    ) -> None:
        """
        Update migration status.

        Args:
            migration_id: Migration ID
            status: New status
            error_message: Error message if status is FAILED
        """
        migration = self.get_migration(migration_id)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")

        migration.status = status.value

        if status == MigrationStatus.RUNNING and not migration.started_at:
            migration.started_at = datetime.utcnow()

        if status in (
            MigrationStatus.COMPLETED,
            MigrationStatus.FAILED,
            MigrationStatus.ROLLED_BACK,
        ):
            migration.completed_at = datetime.utcnow()

        if error_message:
            migration.error_message = error_message

        self.db.commit()
        logger.info(f"Migration {migration_id} status updated to {status.value}")

    def execute_migration(
        self,
        migration_id: UUID,
        query: Any,
        transform_func: Callable[[Any], dict[str, Any]],
        dry_run: bool = False,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> MigrationResult:
        """
        Execute a migration with batch processing.

        Args:
            migration_id: Migration ID
            query: SQLAlchemy query for records to migrate
            transform_func: Function to transform each record
            dry_run: If True, don't commit changes
            progress_callback: Optional callback for progress updates (processed, total)

        Returns:
            MigrationResult with execution details

        Example:
            def transform_person(person):
                return {'email': person.email.lower()}

            query = db.query(Person).filter(Person.type == 'faculty')
            result = migrator.execute_migration(
                migration_id,
                query,
                transform_person,
                dry_run=True
            )
        """
        migration = self.get_migration(migration_id)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")

        # Update status
        status = MigrationStatus.DRY_RUN if dry_run else MigrationStatus.RUNNING
        self.update_status(migration_id, status)

        total_records = 0
        processed_records = 0
        failed_records = 0
        error_message = None

        try:
            # Get total count
            total_records = query.count()
            migration.total_records = total_records
            self.db.commit()

            logger.info(
                f"Starting migration {migration_id} "
                f"({'DRY RUN' if dry_run else 'EXECUTION'}): "
                f"{total_records} records"
            )

            # Process in batches
            batch_size = migration.batch_size
            offset = 0

            while offset < total_records:
                batch = query.limit(batch_size).offset(offset).all()

                if not batch:
                    break

                # Process each record in batch
                for record in batch:
                    try:
                        # Transform record
                        updates = transform_func(record)

                        # Apply updates
                        for key, value in updates.items():
                            setattr(record, key, value)

                        processed_records += 1

                    except Exception as e:
                        failed_records += 1
                        logger.warning(
                            f"Failed to transform record {getattr(record, 'id', 'unknown')}: {e}"
                        )

                        # Store first error
                        if not error_message:
                            error_message = str(e)

                # Commit batch if not dry run
                if not dry_run:
                    self.db.commit()
                else:
                    self.db.rollback()

                # Update progress
                migration.processed_records = processed_records
                migration.failed_records = failed_records
                self.db.commit()

                # Progress callback
                if progress_callback:
                    progress_callback(processed_records, total_records)

                offset += batch_size

            # Mark as completed if no failures
            success = failed_records == 0
            final_status = (
                MigrationStatus.COMPLETED if success else MigrationStatus.FAILED
            )

            if not dry_run:
                self.update_status(migration_id, final_status, error_message)

            logger.info(
                f"Migration {migration_id} completed: "
                f"{processed_records}/{total_records} processed, "
                f"{failed_records} failed"
            )

            return MigrationResult(
                migration_id=migration_id,
                success=success,
                total_records=total_records,
                processed_records=processed_records,
                failed_records=failed_records,
                error_message=error_message,
                dry_run=dry_run,
            )

        except Exception as e:
            logger.error(f"Migration {migration_id} failed: {e}", exc_info=True)
            self.db.rollback()

            if not dry_run:
                self.update_status(migration_id, MigrationStatus.FAILED, str(e))

            return MigrationResult(
                migration_id=migration_id,
                success=False,
                total_records=total_records,
                processed_records=processed_records,
                failed_records=failed_records,
                error_message=str(e),
                dry_run=dry_run,
            )

    def execute_custom_migration(
        self,
        migration_id: UUID,
        migration_func: Callable[[Session], None],
        dry_run: bool = False,
    ) -> MigrationResult:
        """
        Execute a custom migration function.

        Useful for complex migrations that don't fit the standard pattern.

        Args:
            migration_id: Migration ID
            migration_func: Custom migration function that takes a DB session
            dry_run: If True, rollback changes

        Returns:
            MigrationResult

        Example:
            def custom_migration(db):
                # Complex multi-table operation
                db.execute(text("UPDATE ..."))
                db.execute(text("INSERT INTO ..."))

            result = migrator.execute_custom_migration(
                migration_id,
                custom_migration,
                dry_run=True
            )
        """
        migration = self.get_migration(migration_id)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")

        status = MigrationStatus.DRY_RUN if dry_run else MigrationStatus.RUNNING
        self.update_status(migration_id, status)

        try:
            logger.info(
                f"Executing custom migration {migration_id} "
                f"({'DRY RUN' if dry_run else 'EXECUTION'})"
            )

            # Execute custom function
            migration_func(self.db)

            # Commit or rollback
            if not dry_run:
                self.db.commit()
                self.update_status(migration_id, MigrationStatus.COMPLETED)
            else:
                self.db.rollback()

            logger.info(f"Custom migration {migration_id} completed successfully")

            return MigrationResult(
                migration_id=migration_id, success=True, dry_run=dry_run
            )

        except Exception as e:
            logger.error(f"Custom migration {migration_id} failed: {e}", exc_info=True)
            self.db.rollback()

            if not dry_run:
                self.update_status(migration_id, MigrationStatus.FAILED, str(e))

            return MigrationResult(
                migration_id=migration_id,
                success=False,
                error_message=str(e),
                dry_run=dry_run,
            )

    def list_migrations(
        self, status: MigrationStatus | None = None, limit: int = 50
    ) -> list[MigrationRecord]:
        """
        List migrations with optional filtering.

        Args:
            status: Filter by status
            limit: Maximum number of records to return

        Returns:
            List of MigrationRecord objects
        """
        query = self.db.query(MigrationRecord)

        if status:
            query = query.filter(MigrationRecord.status == status.value)

        return query.order_by(MigrationRecord.created_at.desc()).limit(limit).all()

    def get_migration_progress(self, migration_id: UUID) -> dict[str, Any]:
        """
        Get detailed progress information for a migration.

        Args:
            migration_id: Migration ID

        Returns:
            Dictionary with progress details
        """
        migration = self.get_migration(migration_id)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")

        progress_pct = 0.0
        if migration.total_records > 0:
            progress_pct = (migration.processed_records / migration.total_records) * 100

        return {
            "migration_id": str(migration.id),
            "name": migration.name,
            "status": migration.status,
            "total_records": migration.total_records,
            "processed_records": migration.processed_records,
            "failed_records": migration.failed_records,
            "progress_percentage": round(progress_pct, 2),
            "created_at": (
                migration.created_at.isoformat() if migration.created_at else None
            ),
            "started_at": (
                migration.started_at.isoformat() if migration.started_at else None
            ),
            "completed_at": (
                migration.completed_at.isoformat() if migration.completed_at else None
            ),
            "error_message": migration.error_message,
        }
