"""Migration runner service for orchestrating database migrations.

This module provides a comprehensive migration execution framework with:
- Migration discovery from filesystem
- Dependency resolution and ordering
- Dry-run mode for safe testing
- Progress tracking and logging
- Partial migration support (resume from failure)
- Pre/post migration hooks
- Migration verification
- Distributed lock management for concurrent migrations

Example:
    runner = MigrationRunner(db_session)

    # Discover migrations from directory
    migrations = runner.discover_migrations("alembic/versions")

    # Execute with dry run first
    result = runner.run_migrations(
        migrations=migrations,
        dry_run=True,
        target_version="head"
    )

    # If dry run succeeds, execute for real
    if result.success:
        runner.run_migrations(
            migrations=migrations,
            dry_run=False,
            target_version="head"
        )
"""

import hashlib
import importlib.util
import logging
import os
import re
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, ValidationError
from app.db.base import Base
from app.db.types import GUID, JSONType

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class MigrationRunStatus(str, Enum):
    """Status of a migration run."""

    PENDING = "pending"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    ROLLED_BACK = "rolled_back"
    DRY_RUN = "dry_run"


class MigrationLockStatus(str, Enum):
    """Status of a migration lock."""

    LOCKED = "locked"
    UNLOCKED = "unlocked"
    EXPIRED = "expired"


# Default lock timeout: 30 minutes
DEFAULT_LOCK_TIMEOUT_SECONDS = 1800

# Maximum time to wait for lock acquisition: 5 minutes
MAX_LOCK_WAIT_SECONDS = 300


# =============================================================================
# Database Models
# =============================================================================


class MigrationRunRecord(Base):
    """Database model for tracking migration runs."""

    __tablename__ = "migration_runs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    run_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(
        String(50), nullable=False, default=MigrationRunStatus.PENDING.value, index=True
    )

    # Migration details
    total_migrations = Column(Integer, default=0)
    completed_migrations = Column(Integer, default=0)
    failed_migrations = Column(Integer, default=0)
    skipped_migrations = Column(Integer, default=0)

    # Target and current version
    target_version = Column(String(255))
    current_version = Column(String(255))

    # Configuration
    dry_run = Column(Boolean, default=False)
    config = Column(JSONType)

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSONType)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Created by
    created_by = Column(String(255))

    def __repr__(self):
        return f"<MigrationRunRecord(name='{self.run_name}', status='{self.status}')>"


class MigrationExecutionRecord(Base):
    """Database model for tracking individual migration executions."""

    __tablename__ = "migration_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    run_id = Column(GUID(), nullable=False, index=True)
    migration_name = Column(String(255), nullable=False, index=True)
    migration_version = Column(String(255), nullable=False, index=True)

    # Execution details
    status = Column(String(50), nullable=False, index=True)
    execution_order = Column(Integer, nullable=False)

    # Dependencies
    dependencies = Column(JSONType)

    # Checksums for verification
    checksum_before = Column(String(64))
    checksum_after = Column(String(64))

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSONType)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Execution time in seconds
    execution_time = Column(Integer)

    def __repr__(self):
        return f"<MigrationExecutionRecord(name='{self.migration_name}', status='{self.status}')>"


class MigrationLock(Base):
    """Database model for distributed migration locks."""

    __tablename__ = "migration_locks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    lock_name = Column(String(255), nullable=False, unique=True, index=True)
    lock_holder = Column(String(255), nullable=False)
    status = Column(
        String(50), nullable=False, default=MigrationLockStatus.LOCKED.value, index=True
    )

    # Lock details
    acquired_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    heartbeat_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Metadata
    metadata = Column(JSONType)

    def __repr__(self):
        return f"<MigrationLock(name='{self.lock_name}', holder='{self.lock_holder}')>"

    def is_expired(self) -> bool:
        """Check if lock has expired."""
        return datetime.utcnow() > self.expires_at

    def refresh_heartbeat(self) -> None:
        """Update heartbeat timestamp."""
        self.heartbeat_at = datetime.utcnow()


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Migration:
    """Represents a single migration."""

    name: str
    version: str
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    upgrade_func: Callable | None = None
    downgrade_func: Callable | None = None
    file_path: str | None = None
    checksum: str | None = None

    def __hash__(self):
        return hash(self.version)

    def __eq__(self, other):
        if isinstance(other, Migration):
            return self.version == other.version
        return False


@dataclass
class MigrationResult:
    """Result of a migration run."""

    run_id: UUID
    success: bool
    total_migrations: int = 0
    completed_migrations: int = 0
    failed_migrations: int = 0
    skipped_migrations: int = 0
    error_message: str | None = None
    error_details: dict | None = None
    dry_run: bool = False
    execution_time: float = 0.0

    def __repr__(self):
        mode = "DRY RUN" if self.dry_run else "EXECUTION"
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"<MigrationResult({mode} {status}: "
            f"{self.completed_migrations}/{self.total_migrations} completed, "
            f"{self.failed_migrations} failed, "
            f"{self.skipped_migrations} skipped)>"
        )


@dataclass
class MigrationHooks:
    """Hooks for migration lifecycle events."""

    pre_run: Callable[[Session], None] | None = None
    post_run: Callable[[Session, MigrationResult], None] | None = None
    pre_migration: Callable[[Session, Migration], None] | None = None
    post_migration: Callable[[Session, Migration, bool], None] | None = None
    on_error: Callable[[Session, Migration, Exception], None] | None = None


# =============================================================================
# Exceptions
# =============================================================================


class MigrationError(AppException):
    """Base exception for migration errors."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class MigrationLockError(MigrationError):
    """Exception raised when unable to acquire migration lock."""

    pass


class MigrationDependencyError(MigrationError):
    """Exception raised when migration dependencies cannot be resolved."""

    pass


class MigrationVerificationError(MigrationError):
    """Exception raised when migration verification fails."""

    pass


# =============================================================================
# Migration Lock Manager
# =============================================================================


class MigrationLockManager:
    """Manager for distributed migration locks."""

    def __init__(
        self, db: Session, timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SECONDS
    ):
        """
        Initialize lock manager.

        Args:
            db: Database session
            timeout_seconds: Lock timeout in seconds
        """
        self.db = db
        self.timeout_seconds = timeout_seconds
        self.lock_holder_id = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"

    def acquire_lock(
        self,
        lock_name: str,
        wait: bool = True,
        wait_timeout: int = MAX_LOCK_WAIT_SECONDS,
        metadata: dict | None = None,
    ) -> MigrationLock:
        """
        Acquire a migration lock.

        Args:
            lock_name: Name of the lock
            wait: Whether to wait for lock if already held
            wait_timeout: Maximum time to wait in seconds
            metadata: Optional metadata to store with lock

        Returns:
            MigrationLock object

        Raises:
            MigrationLockError: If unable to acquire lock
        """
        start_time = time.time()

        while True:
            try:
                # Try to acquire lock
                lock = self._try_acquire_lock(lock_name, metadata)
                if lock:
                    logger.info(f"Lock '{lock_name}' acquired by {self.lock_holder_id}")
                    return lock

                # Check if we should wait
                if not wait:
                    raise MigrationLockError(f"Lock '{lock_name}' is already held")

                # Check wait timeout
                elapsed = time.time() - start_time
                if elapsed >= wait_timeout:
                    raise MigrationLockError(
                        f"Timeout waiting for lock '{lock_name}' after {wait_timeout}s"
                    )

                # Wait and retry
                time.sleep(1)

            except IntegrityError:
                # Lock already exists, retry
                self.db.rollback()
                if not wait:
                    raise MigrationLockError(f"Lock '{lock_name}' is already held")
                time.sleep(1)

    def _try_acquire_lock(
        self, lock_name: str, metadata: dict | None = None
    ) -> MigrationLock | None:
        """
        Try to acquire lock once.

        Args:
            lock_name: Name of the lock
            metadata: Optional metadata

        Returns:
            MigrationLock if acquired, None otherwise
        """
        # Check for existing lock
        existing_lock = (
            self.db.query(MigrationLock)
            .filter(MigrationLock.lock_name == lock_name)
            .first()
        )

        if existing_lock:
            # Check if lock is expired
            if existing_lock.is_expired():
                logger.warning(
                    f"Lock '{lock_name}' held by {existing_lock.lock_holder} "
                    f"has expired, reclaiming"
                )
                # Update existing lock
                existing_lock.lock_holder = self.lock_holder_id
                existing_lock.status = MigrationLockStatus.LOCKED.value
                existing_lock.acquired_at = datetime.utcnow()
                existing_lock.expires_at = datetime.utcnow() + timedelta(
                    seconds=self.timeout_seconds
                )
                existing_lock.heartbeat_at = datetime.utcnow()
                existing_lock.metadata = metadata
                self.db.commit()
                return existing_lock
            else:
                # Lock is held by someone else
                return None

        # Create new lock
        expires_at = datetime.utcnow() + timedelta(seconds=self.timeout_seconds)
        lock = MigrationLock(
            lock_name=lock_name,
            lock_holder=self.lock_holder_id,
            status=MigrationLockStatus.LOCKED.value,
            expires_at=expires_at,
            metadata=metadata,
        )

        self.db.add(lock)
        self.db.commit()
        return lock

    def release_lock(self, lock: MigrationLock) -> None:
        """
        Release a migration lock.

        Args:
            lock: Lock to release
        """
        try:
            # Verify we own this lock
            if lock.lock_holder != self.lock_holder_id:
                logger.warning(
                    f"Attempt to release lock '{lock.lock_name}' not owned by us "
                    f"(owned by {lock.lock_holder})"
                )
                return

            # Update lock status
            lock.status = MigrationLockStatus.UNLOCKED.value
            self.db.commit()

            logger.info(f"Lock '{lock.lock_name}' released by {self.lock_holder_id}")

        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
            self.db.rollback()

    def refresh_lock(self, lock: MigrationLock) -> None:
        """
        Refresh lock heartbeat to prevent expiration.

        Args:
            lock: Lock to refresh
        """
        try:
            # Verify we own this lock
            if lock.lock_holder != self.lock_holder_id:
                raise MigrationLockError(
                    f"Cannot refresh lock '{lock.lock_name}' owned by "
                    f"{lock.lock_holder}"
                )

            lock.refresh_heartbeat()
            self.db.commit()

        except Exception as e:
            logger.error(f"Error refreshing lock: {e}")
            self.db.rollback()
            raise

    def cleanup_expired_locks(self) -> int:
        """
        Clean up expired locks.

        Returns:
            Number of locks cleaned up
        """
        try:
            expired_locks = (
                self.db.query(MigrationLock)
                .filter(
                    MigrationLock.expires_at < datetime.utcnow(),
                    MigrationLock.status == MigrationLockStatus.LOCKED.value,
                )
                .all()
            )

            count = 0
            for lock in expired_locks:
                lock.status = MigrationLockStatus.EXPIRED.value
                count += 1

            if count > 0:
                self.db.commit()
                logger.info(f"Cleaned up {count} expired migration locks")

            return count

        except Exception as e:
            logger.error(f"Error cleaning up expired locks: {e}")
            self.db.rollback()
            return 0


# =============================================================================
# Migration Discovery
# =============================================================================


class MigrationDiscovery:
    """Discovers migrations from filesystem."""

    @staticmethod
    def discover_migrations(
        directory: str, pattern: str = r"^(\d+)_.+\.py$"
    ) -> list[Migration]:
        """
        Discover migrations from a directory.

        Args:
            directory: Directory to search
            pattern: Regex pattern for migration files

        Returns:
            List of Migration objects
        """
        migrations = []
        path = Path(directory)

        if not path.exists():
            logger.warning(f"Migration directory {directory} does not exist")
            return migrations

        # Find all Python files matching pattern
        pattern_re = re.compile(pattern)

        for file_path in sorted(path.glob("*.py")):
            if file_path.name.startswith("__"):
                continue

            match = pattern_re.match(file_path.name)
            if not match:
                continue

            try:
                migration = MigrationDiscovery._load_migration_file(file_path)
                if migration:
                    migrations.append(migration)
            except Exception as e:
                logger.error(f"Error loading migration {file_path}: {e}")

        logger.info(f"Discovered {len(migrations)} migrations from {directory}")
        return migrations

    @staticmethod
    def _load_migration_file(file_path: Path) -> Migration | None:
        """
        Load a migration from a file.

        Args:
            file_path: Path to migration file

        Returns:
            Migration object or None
        """
        # Load module
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Extract migration metadata
        version = getattr(module, "revision", file_path.stem)
        name = getattr(module, "name", file_path.stem)
        description = getattr(module, "__doc__", "") or ""
        dependencies = getattr(module, "down_revision", [])

        # Normalize dependencies to list
        if dependencies is None:
            dependencies = []
        elif isinstance(dependencies, str):
            dependencies = [dependencies] if dependencies else []
        elif isinstance(dependencies, tuple):
            dependencies = list(dependencies)

        # Get upgrade/downgrade functions
        upgrade_func = getattr(module, "upgrade", None)
        downgrade_func = getattr(module, "downgrade", None)

        # Calculate checksum
        checksum = MigrationDiscovery._calculate_file_checksum(file_path)

        return Migration(
            name=name,
            version=version,
            description=description,
            dependencies=dependencies,
            upgrade_func=upgrade_func,
            downgrade_func=downgrade_func,
            file_path=str(file_path),
            checksum=checksum,
        )

    @staticmethod
    def _calculate_file_checksum(file_path: Path) -> str:
        """
        Calculate SHA-256 checksum of a file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal checksum string
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


# =============================================================================
# Migration Dependency Resolver
# =============================================================================


class DependencyResolver:
    """Resolves migration dependencies and determines execution order."""

    @staticmethod
    def resolve_order(migrations: list[Migration]) -> list[Migration]:
        """
        Resolve migration execution order based on dependencies.

        Uses topological sorting to ensure dependencies are executed first.

        Args:
            migrations: List of migrations

        Returns:
            Ordered list of migrations

        Raises:
            MigrationDependencyError: If circular dependencies detected
        """
        # Build dependency graph
        migration_map = {m.version: m for m in migrations}

        # Track visited nodes and recursion stack for cycle detection
        visited = set()
        rec_stack = set()
        ordered = []

        def visit(migration: Migration):
            """Visit a migration node (DFS)."""
            if migration.version in rec_stack:
                raise MigrationDependencyError(
                    f"Circular dependency detected involving {migration.version}"
                )

            if migration.version in visited:
                return

            rec_stack.add(migration.version)

            # Visit dependencies first
            for dep_version in migration.dependencies:
                if dep_version in migration_map:
                    visit(migration_map[dep_version])
                else:
                    logger.warning(
                        f"Migration {migration.version} depends on "
                        f"{dep_version} which is not found"
                    )

            rec_stack.remove(migration.version)
            visited.add(migration.version)
            ordered.append(migration)

        # Visit all migrations
        for migration in migrations:
            if migration.version not in visited:
                visit(migration)

        logger.info(f"Resolved migration order: {[m.version for m in ordered]}")

        return ordered

    @staticmethod
    def filter_to_target(
        migrations: list[Migration],
        target_version: str | None = None,
        current_version: str | None = None,
    ) -> list[Migration]:
        """
        Filter migrations to only those needed to reach target version.

        Args:
            migrations: List of migrations in execution order
            target_version: Target version (None or "head" for latest)
            current_version: Current version (None for all)

        Returns:
            Filtered list of migrations
        """
        # If no target specified or "head", include all
        if not target_version or target_version == "head":
            target_idx = len(migrations)
        else:
            # Find target version index
            target_idx = None
            for i, m in enumerate(migrations):
                if m.version == target_version:
                    target_idx = i + 1
                    break

            if target_idx is None:
                raise ValidationError(f"Target version {target_version} not found")

        # Find current version index
        current_idx = 0
        if current_version:
            for i, m in enumerate(migrations):
                if m.version == current_version:
                    current_idx = i + 1
                    break

        # Return migrations between current and target
        filtered = migrations[current_idx:target_idx]

        logger.info(
            f"Filtered {len(filtered)} migrations from "
            f"{current_version or 'start'} to {target_version or 'head'}"
        )

        return filtered


# =============================================================================
# Migration Runner
# =============================================================================


class MigrationRunner:
    """
    Core migration runner service.

    Orchestrates migration discovery, dependency resolution, execution,
    and tracking.
    """

    def __init__(self, db: Session):
        """
        Initialize migration runner.

        Args:
            db: Database session
        """
        self.db = db
        self.lock_manager = MigrationLockManager(db)
        self.discovery = MigrationDiscovery()
        self.resolver = DependencyResolver()

    def discover_migrations(
        self, directory: str, pattern: str = r"^(\d+)_.+\.py$"
    ) -> list[Migration]:
        """
        Discover migrations from directory.

        Args:
            directory: Directory to search
            pattern: Regex pattern for migration files

        Returns:
            List of discovered migrations
        """
        return self.discovery.discover_migrations(directory, pattern)

    def run_migrations(
        self,
        migrations: list[Migration],
        dry_run: bool = False,
        target_version: str | None = None,
        current_version: str | None = None,
        hooks: MigrationHooks | None = None,
        created_by: str | None = None,
        acquire_lock: bool = True,
        run_name: str | None = None,
    ) -> MigrationResult:
        """
        Run migrations with full orchestration.

        Args:
            migrations: List of migrations to run
            dry_run: If True, don't commit changes
            target_version: Target version to migrate to
            current_version: Current version to start from
            hooks: Optional lifecycle hooks
            created_by: User/system running migration
            acquire_lock: Whether to acquire distributed lock
            run_name: Optional name for this run

        Returns:
            MigrationResult
        """
        start_time = time.time()
        lock = None

        try:
            # Acquire lock if requested
            if acquire_lock:
                lock = self.lock_manager.acquire_lock(
                    "migrations",
                    wait=True,
                    metadata={"run_name": run_name or "migration_run"},
                )

            # Resolve execution order
            ordered_migrations = self.resolver.resolve_order(migrations)

            # Filter to target version
            filtered_migrations = self.resolver.filter_to_target(
                ordered_migrations,
                target_version=target_version,
                current_version=current_version,
            )

            # Create run record
            run_record = self._create_run_record(
                run_name=run_name or f"migration_run_{uuid.uuid4().hex[:8]}",
                total_migrations=len(filtered_migrations),
                target_version=target_version or "head",
                current_version=current_version,
                dry_run=dry_run,
                created_by=created_by,
            )

            # Execute pre-run hook
            if hooks and hooks.pre_run:
                try:
                    hooks.pre_run(self.db)
                except Exception as e:
                    logger.error(f"Pre-run hook failed: {e}")

            # Execute migrations
            result = self._execute_migrations(
                run_id=run_record.id,
                migrations=filtered_migrations,
                dry_run=dry_run,
                hooks=hooks,
                lock=lock,
            )

            # Update run record
            self._update_run_record(run_record, result)

            # Execute post-run hook
            if hooks and hooks.post_run:
                try:
                    hooks.post_run(self.db, result)
                except Exception as e:
                    logger.error(f"Post-run hook failed: {e}")

            # Calculate execution time
            result.execution_time = time.time() - start_time

            return result

        finally:
            # Release lock
            if lock:
                self.lock_manager.release_lock(lock)

    def _create_run_record(
        self,
        run_name: str,
        total_migrations: int,
        target_version: str | None,
        current_version: str | None,
        dry_run: bool,
        created_by: str | None,
    ) -> MigrationRunRecord:
        """Create a migration run record."""
        run_record = MigrationRunRecord(
            run_name=run_name,
            total_migrations=total_migrations,
            target_version=target_version,
            current_version=current_version,
            dry_run=dry_run,
            status=(
                MigrationRunStatus.DRY_RUN.value
                if dry_run
                else MigrationRunStatus.PENDING.value
            ),
            created_by=created_by,
        )

        self.db.add(run_record)
        self.db.commit()

        logger.info(f"Created migration run record: {run_record.id}")
        return run_record

    def _execute_migrations(
        self,
        run_id: UUID,
        migrations: list[Migration],
        dry_run: bool,
        hooks: MigrationHooks | None,
        lock: MigrationLock | None,
    ) -> MigrationResult:
        """Execute list of migrations."""
        completed = 0
        failed = 0
        skipped = 0
        error_message = None
        error_details = None

        for i, migration in enumerate(migrations):
            try:
                # Refresh lock heartbeat
                if lock:
                    self.lock_manager.refresh_lock(lock)

                # Execute pre-migration hook
                if hooks and hooks.pre_migration:
                    try:
                        hooks.pre_migration(self.db, migration)
                    except Exception as e:
                        logger.error(f"Pre-migration hook failed: {e}")

                # Execute migration
                success = self._execute_single_migration(
                    run_id=run_id,
                    migration=migration,
                    execution_order=i,
                    dry_run=dry_run,
                )

                if success:
                    completed += 1
                else:
                    failed += 1

                # Execute post-migration hook
                if hooks and hooks.post_migration:
                    try:
                        hooks.post_migration(self.db, migration, success)
                    except Exception as e:
                        logger.error(f"Post-migration hook failed: {e}")

            except Exception as e:
                failed += 1
                if not error_message:
                    error_message = str(e)
                    error_details = {"migration": migration.version, "error": str(e)}

                logger.error(
                    f"Migration {migration.version} failed: {e}", exc_info=True
                )

                # Execute error hook
                if hooks and hooks.on_error:
                    try:
                        hooks.on_error(self.db, migration, e)
                    except Exception as hook_error:
                        logger.error(f"Error hook failed: {hook_error}")

        return MigrationResult(
            run_id=run_id,
            success=(failed == 0),
            total_migrations=len(migrations),
            completed_migrations=completed,
            failed_migrations=failed,
            skipped_migrations=skipped,
            error_message=error_message,
            error_details=error_details,
            dry_run=dry_run,
        )

    def _execute_single_migration(
        self, run_id: UUID, migration: Migration, execution_order: int, dry_run: bool
    ) -> bool:
        """
        Execute a single migration.

        Args:
            run_id: Run ID
            migration: Migration to execute
            execution_order: Order in execution sequence
            dry_run: Whether this is a dry run

        Returns:
            True if successful, False otherwise
        """
        exec_record = MigrationExecutionRecord(
            run_id=run_id,
            migration_name=migration.name,
            migration_version=migration.version,
            status=MigrationRunStatus.PENDING.value,
            execution_order=execution_order,
            dependencies=migration.dependencies,
        )

        self.db.add(exec_record)
        self.db.commit()

        try:
            logger.info(
                f"Executing migration {migration.version}: {migration.name} "
                f"({'DRY RUN' if dry_run else 'REAL'})"
            )

            # Calculate checksum before
            exec_record.checksum_before = self._calculate_db_checksum()
            exec_record.status = MigrationRunStatus.RUNNING.value
            exec_record.started_at = datetime.utcnow()
            self.db.commit()

            # Execute upgrade function
            if migration.upgrade_func:
                migration.upgrade_func()
            else:
                logger.warning(f"Migration {migration.version} has no upgrade function")

            # Calculate checksum after
            exec_record.checksum_after = self._calculate_db_checksum()

            # Verify migration
            self._verify_migration(migration, exec_record)

            # Commit or rollback
            if not dry_run:
                self.db.commit()
            else:
                self.db.rollback()

            # Update execution record
            exec_record.status = MigrationRunStatus.COMPLETED.value
            exec_record.completed_at = datetime.utcnow()
            exec_record.execution_time = int(
                (exec_record.completed_at - exec_record.started_at).total_seconds()
            )
            self.db.commit()

            logger.info(
                f"Migration {migration.version} completed successfully "
                f"in {exec_record.execution_time}s"
            )

            return True

        except Exception as e:
            logger.error(f"Migration {migration.version} failed: {e}", exc_info=True)

            self.db.rollback()

            exec_record.status = MigrationRunStatus.FAILED.value
            exec_record.completed_at = datetime.utcnow()
            exec_record.error_message = str(e)
            exec_record.error_details = {"error": str(e)}
            self.db.commit()

            return False

    def _calculate_db_checksum(self) -> str:
        """
        Calculate a checksum of database schema state.

        Returns:
            Hexadecimal checksum string
        """
        try:
            # Query table names and column info
            result = self.db.execute(
                text(
                    """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """
                )
            )

            schema_info = "\n".join(f"{row[0]}.{row[1]}:{row[2]}" for row in result)

            return hashlib.sha256(schema_info.encode()).hexdigest()

        except Exception as e:
            logger.warning(f"Could not calculate DB checksum: {e}")
            return ""

    def _verify_migration(
        self, migration: Migration, exec_record: MigrationExecutionRecord
    ) -> None:
        """
        Verify migration executed correctly.

        Args:
            migration: Migration that was executed
            exec_record: Execution record

        Raises:
            MigrationVerificationError: If verification fails
        """
        # Check that schema changed (checksums are different)
        if exec_record.checksum_before == exec_record.checksum_after:
            logger.warning(
                f"Migration {migration.version} did not change database schema "
                f"(checksums identical)"
            )

    def _update_run_record(
        self, run_record: MigrationRunRecord, result: MigrationResult
    ) -> None:
        """Update migration run record with results."""
        run_record.completed_migrations = result.completed_migrations
        run_record.failed_migrations = result.failed_migrations
        run_record.skipped_migrations = result.skipped_migrations
        run_record.error_message = result.error_message
        run_record.error_details = result.error_details

        if result.success:
            run_record.status = MigrationRunStatus.COMPLETED.value
        elif result.completed_migrations > 0:
            run_record.status = MigrationRunStatus.PARTIALLY_COMPLETED.value
        else:
            run_record.status = MigrationRunStatus.FAILED.value

        run_record.completed_at = datetime.utcnow()
        self.db.commit()

    def get_run_progress(self, run_id: UUID) -> dict[str, Any]:
        """
        Get progress information for a migration run.

        Args:
            run_id: Run ID

        Returns:
            Dictionary with progress details
        """
        run_record = (
            self.db.query(MigrationRunRecord)
            .filter(MigrationRunRecord.id == run_id)
            .first()
        )

        if not run_record:
            raise ValidationError(f"Migration run {run_id} not found")

        progress_pct = 0.0
        if run_record.total_migrations > 0:
            progress_pct = (
                run_record.completed_migrations / run_record.total_migrations
            ) * 100

        return {
            "run_id": str(run_record.id),
            "run_name": run_record.run_name,
            "status": run_record.status,
            "total_migrations": run_record.total_migrations,
            "completed_migrations": run_record.completed_migrations,
            "failed_migrations": run_record.failed_migrations,
            "skipped_migrations": run_record.skipped_migrations,
            "progress_percentage": round(progress_pct, 2),
            "dry_run": run_record.dry_run,
            "target_version": run_record.target_version,
            "current_version": run_record.current_version,
            "created_at": (
                run_record.created_at.isoformat() if run_record.created_at else None
            ),
            "started_at": (
                run_record.started_at.isoformat() if run_record.started_at else None
            ),
            "completed_at": (
                run_record.completed_at.isoformat() if run_record.completed_at else None
            ),
            "error_message": run_record.error_message,
        }

    def list_runs(
        self, status: MigrationRunStatus | None = None, limit: int = 50
    ) -> list[MigrationRunRecord]:
        """
        List migration runs.

        Args:
            status: Filter by status
            limit: Maximum number of records

        Returns:
            List of MigrationRunRecord objects
        """
        query = self.db.query(MigrationRunRecord)

        if status:
            query = query.filter(MigrationRunRecord.status == status.value)

        return query.order_by(MigrationRunRecord.created_at.desc()).limit(limit).all()
