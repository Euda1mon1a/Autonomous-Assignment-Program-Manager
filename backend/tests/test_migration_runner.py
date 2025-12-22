"""
Tests for migration runner service.

Tests cover:
- Migration discovery from filesystem
- Dependency resolution and ordering
- Dry-run mode
- Progress tracking and logging
- Partial migration support
- Pre/post migration hooks
- Migration verification
- Lock management for concurrent migrations
"""
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.migrations.runner import (
    DependencyResolver,
    Migration,
    MigrationDiscovery,
    MigrationDependencyError,
    MigrationExecutionRecord,
    MigrationHooks,
    MigrationLock,
    MigrationLockError,
    MigrationLockManager,
    MigrationLockStatus,
    MigrationResult,
    MigrationRunner,
    MigrationRunRecord,
    MigrationRunStatus,
)


class TestMigration:
    """Tests for Migration dataclass."""

    def test_migration_creation(self):
        """Should create migration with all attributes."""
        migration = Migration(
            name="test_migration",
            version="001",
            description="Test migration",
            dependencies=["000"],
            checksum="abc123"
        )

        assert migration.name == "test_migration"
        assert migration.version == "001"
        assert migration.description == "Test migration"
        assert migration.dependencies == ["000"]
        assert migration.checksum == "abc123"

    def test_migration_equality(self):
        """Should compare migrations by version."""
        migration1 = Migration(name="test1", version="001")
        migration2 = Migration(name="test2", version="001")
        migration3 = Migration(name="test3", version="002")

        assert migration1 == migration2
        assert migration1 != migration3

    def test_migration_hashable(self):
        """Should be hashable for use in sets/dicts."""
        migration1 = Migration(name="test1", version="001")
        migration2 = Migration(name="test2", version="001")

        migration_set = {migration1, migration2}
        assert len(migration_set) == 1  # Same version, so only one in set


class TestMigrationLockManager:
    """Tests for distributed migration locks."""

    def test_acquire_lock(self, db: Session):
        """Should acquire a migration lock."""
        manager = MigrationLockManager(db)
        lock = manager.acquire_lock("test_lock", wait=False)

        assert lock is not None
        assert lock.lock_name == "test_lock"
        assert lock.status == MigrationLockStatus.LOCKED.value
        assert lock.lock_holder == manager.lock_holder_id

    def test_acquire_lock_already_held(self, db: Session):
        """Should raise error when lock is already held."""
        manager1 = MigrationLockManager(db)
        manager2 = MigrationLockManager(db)

        # Manager 1 acquires lock
        lock1 = manager1.acquire_lock("test_lock", wait=False)
        assert lock1 is not None

        # Manager 2 tries to acquire same lock
        with pytest.raises(MigrationLockError):
            manager2.acquire_lock("test_lock", wait=False)

    def test_acquire_lock_wait(self, db: Session):
        """Should wait and acquire lock when it becomes available."""
        manager1 = MigrationLockManager(db, timeout_seconds=2)
        manager2 = MigrationLockManager(db)

        # Manager 1 acquires lock with short timeout
        lock1 = manager1.acquire_lock("test_lock", wait=False)
        assert lock1 is not None

        # Manually expire the lock
        lock1.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

        # Manager 2 should acquire expired lock
        lock2 = manager2.acquire_lock("test_lock", wait=True, wait_timeout=5)
        assert lock2 is not None
        assert lock2.lock_holder == manager2.lock_holder_id

    def test_release_lock(self, db: Session):
        """Should release a lock."""
        manager = MigrationLockManager(db)
        lock = manager.acquire_lock("test_lock", wait=False)

        # Release lock
        manager.release_lock(lock)

        # Verify lock status
        db.refresh(lock)
        assert lock.status == MigrationLockStatus.UNLOCKED.value

    def test_refresh_lock(self, db: Session):
        """Should refresh lock heartbeat."""
        manager = MigrationLockManager(db)
        lock = manager.acquire_lock("test_lock", wait=False)

        original_heartbeat = lock.heartbeat_at

        # Wait a bit and refresh
        time.sleep(0.1)
        manager.refresh_lock(lock)

        db.refresh(lock)
        assert lock.heartbeat_at > original_heartbeat

    def test_cleanup_expired_locks(self, db: Session):
        """Should clean up expired locks."""
        manager = MigrationLockManager(db, timeout_seconds=1)

        # Create lock with short timeout
        lock = manager.acquire_lock("test_lock", wait=False)

        # Manually expire it
        lock.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

        # Clean up expired locks
        cleaned = manager.cleanup_expired_locks()

        assert cleaned == 1
        db.refresh(lock)
        assert lock.status == MigrationLockStatus.EXPIRED.value

    def test_cannot_refresh_unowned_lock(self, db: Session):
        """Should not allow refreshing lock owned by someone else."""
        manager1 = MigrationLockManager(db)
        manager2 = MigrationLockManager(db)

        lock = manager1.acquire_lock("test_lock", wait=False)

        # Manager 2 tries to refresh Manager 1's lock
        with pytest.raises(MigrationLockError):
            manager2.refresh_lock(lock)


class TestDependencyResolver:
    """Tests for migration dependency resolution."""

    def test_resolve_simple_order(self):
        """Should order migrations without dependencies."""
        migrations = [
            Migration(name="m3", version="003", dependencies=[]),
            Migration(name="m1", version="001", dependencies=[]),
            Migration(name="m2", version="002", dependencies=[]),
        ]

        resolver = DependencyResolver()
        # Without dependencies, order should be preserved
        ordered = resolver.resolve_order(migrations)

        assert len(ordered) == 3
        # All migrations should be present
        versions = [m.version for m in ordered]
        assert set(versions) == {"001", "002", "003"}

    def test_resolve_linear_dependencies(self):
        """Should order migrations with linear dependencies."""
        migrations = [
            Migration(name="m3", version="003", dependencies=["002"]),
            Migration(name="m2", version="002", dependencies=["001"]),
            Migration(name="m1", version="001", dependencies=[]),
        ]

        resolver = DependencyResolver()
        ordered = resolver.resolve_order(migrations)

        versions = [m.version for m in ordered]
        assert versions == ["001", "002", "003"]

    def test_resolve_complex_dependencies(self):
        """Should order migrations with complex dependencies."""
        migrations = [
            Migration(name="m4", version="004", dependencies=["002", "003"]),
            Migration(name="m3", version="003", dependencies=["001"]),
            Migration(name="m2", version="002", dependencies=["001"]),
            Migration(name="m1", version="001", dependencies=[]),
        ]

        resolver = DependencyResolver()
        ordered = resolver.resolve_order(migrations)

        versions = [m.version for m in ordered]
        # 001 must come first
        assert versions[0] == "001"
        # 002 and 003 must come before 004
        idx_002 = versions.index("002")
        idx_003 = versions.index("003")
        idx_004 = versions.index("004")
        assert idx_002 < idx_004
        assert idx_003 < idx_004

    def test_detect_circular_dependency(self):
        """Should detect circular dependencies."""
        migrations = [
            Migration(name="m1", version="001", dependencies=["002"]),
            Migration(name="m2", version="002", dependencies=["001"]),
        ]

        resolver = DependencyResolver()
        with pytest.raises(MigrationDependencyError):
            resolver.resolve_order(migrations)

    def test_filter_to_target(self):
        """Should filter migrations to target version."""
        migrations = [
            Migration(name="m1", version="001", dependencies=[]),
            Migration(name="m2", version="002", dependencies=["001"]),
            Migration(name="m3", version="003", dependencies=["002"]),
            Migration(name="m4", version="004", dependencies=["003"]),
        ]

        resolver = DependencyResolver()

        # Filter to version 002
        filtered = resolver.filter_to_target(
            migrations,
            target_version="002",
            current_version=None
        )

        versions = [m.version for m in filtered]
        assert versions == ["001", "002"]

    def test_filter_from_current(self):
        """Should filter migrations starting from current version."""
        migrations = [
            Migration(name="m1", version="001", dependencies=[]),
            Migration(name="m2", version="002", dependencies=["001"]),
            Migration(name="m3", version="003", dependencies=["002"]),
            Migration(name="m4", version="004", dependencies=["003"]),
        ]

        resolver = DependencyResolver()

        # Filter from current version 002
        filtered = resolver.filter_to_target(
            migrations,
            target_version="head",
            current_version="002"
        )

        versions = [m.version for m in filtered]
        assert versions == ["003", "004"]


class TestMigrationDiscovery:
    """Tests for migration discovery from filesystem."""

    def test_discover_no_migrations(self):
        """Should return empty list when no migrations found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = MigrationDiscovery()
            migrations = discovery.discover_migrations(tmpdir)

            assert migrations == []

    def test_discover_migrations(self):
        """Should discover migrations from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create migration files
            self._create_migration_file(
                tmpdir,
                "001_initial.py",
                revision="001",
                dependencies=[]
            )
            self._create_migration_file(
                tmpdir,
                "002_add_table.py",
                revision="002",
                dependencies=["001"]
            )

            discovery = MigrationDiscovery()
            migrations = discovery.discover_migrations(tmpdir)

            assert len(migrations) == 2
            versions = [m.version for m in migrations]
            assert "001" in versions
            assert "002" in versions

    def test_discover_ignores_non_matching_files(self):
        """Should ignore files that don't match pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid migration
            self._create_migration_file(
                tmpdir,
                "001_valid.py",
                revision="001"
            )

            # Create files that should be ignored
            Path(tmpdir, "__init__.py").touch()
            Path(tmpdir, "README.md").touch()
            Path(tmpdir, "helper.py").touch()

            discovery = MigrationDiscovery()
            migrations = discovery.discover_migrations(tmpdir)

            # Should only find the valid migration
            assert len(migrations) == 1
            assert migrations[0].version == "001"

    def test_calculate_file_checksum(self):
        """Should calculate consistent checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir, "test.py")
            file_path.write_text("test content")

            discovery = MigrationDiscovery()
            checksum1 = discovery._calculate_file_checksum(file_path)
            checksum2 = discovery._calculate_file_checksum(file_path)

            assert checksum1 == checksum2
            assert len(checksum1) == 64  # SHA-256 hex digest

    @staticmethod
    def _create_migration_file(
        directory: str,
        filename: str,
        revision: str = "001",
        dependencies: list = None
    ):
        """Helper to create a migration file."""
        dependencies = dependencies or []

        content = f'''"""Test migration."""

revision = "{revision}"
down_revision = {dependencies}

def upgrade():
    """Upgrade database."""
    pass

def downgrade():
    """Downgrade database."""
    pass
'''

        file_path = Path(directory, filename)
        file_path.write_text(content)


class TestMigrationRunner:
    """Tests for migration runner orchestration."""

    def test_create_run_record(self, db: Session):
        """Should create migration run record."""
        runner = MigrationRunner(db)

        run_record = runner._create_run_record(
            run_name="test_run",
            total_migrations=5,
            target_version="head",
            current_version=None,
            dry_run=False,
            created_by="test_user"
        )

        assert run_record.id is not None
        assert run_record.run_name == "test_run"
        assert run_record.total_migrations == 5
        assert run_record.target_version == "head"
        assert run_record.created_by == "test_user"
        assert run_record.status == MigrationRunStatus.PENDING.value

    def test_run_migrations_dry_run(self, db: Session):
        """Should execute migrations in dry run mode."""
        runner = MigrationRunner(db)

        executed_migrations = []

        def mock_upgrade():
            executed_migrations.append(1)

        migrations = [
            Migration(
                name="test1",
                version="001",
                dependencies=[],
                upgrade_func=mock_upgrade
            ),
            Migration(
                name="test2",
                version="002",
                dependencies=["001"],
                upgrade_func=mock_upgrade
            ),
        ]

        result = runner.run_migrations(
            migrations=migrations,
            dry_run=True,
            acquire_lock=False
        )

        assert result.dry_run is True
        # In dry run, changes are rolled back, but functions are still called
        assert len(executed_migrations) == 2

    def test_run_migrations_with_lock(self, db: Session):
        """Should acquire and release lock during execution."""
        runner = MigrationRunner(db)

        migrations = [
            Migration(
                name="test1",
                version="001",
                dependencies=[],
                upgrade_func=lambda: None
            ),
        ]

        result = runner.run_migrations(
            migrations=migrations,
            dry_run=True,
            acquire_lock=True
        )

        assert result.success is True

        # Lock should be released after execution
        locks = db.query(MigrationLock).filter(
            MigrationLock.lock_name == "migrations"
        ).all()

        if locks:
            assert locks[0].status == MigrationLockStatus.UNLOCKED.value

    def test_run_migrations_with_hooks(self, db: Session):
        """Should execute lifecycle hooks."""
        runner = MigrationRunner(db)

        hook_calls = {
            "pre_run": 0,
            "post_run": 0,
            "pre_migration": 0,
            "post_migration": 0,
        }

        def pre_run_hook(db):
            hook_calls["pre_run"] += 1

        def post_run_hook(db, result):
            hook_calls["post_run"] += 1

        def pre_migration_hook(db, migration):
            hook_calls["pre_migration"] += 1

        def post_migration_hook(db, migration, success):
            hook_calls["post_migration"] += 1

        hooks = MigrationHooks(
            pre_run=pre_run_hook,
            post_run=post_run_hook,
            pre_migration=pre_migration_hook,
            post_migration=post_migration_hook
        )

        migrations = [
            Migration(
                name="test1",
                version="001",
                dependencies=[],
                upgrade_func=lambda: None
            ),
            Migration(
                name="test2",
                version="002",
                dependencies=["001"],
                upgrade_func=lambda: None
            ),
        ]

        result = runner.run_migrations(
            migrations=migrations,
            dry_run=True,
            hooks=hooks,
            acquire_lock=False
        )

        assert hook_calls["pre_run"] == 1
        assert hook_calls["post_run"] == 1
        assert hook_calls["pre_migration"] == 2  # Called for each migration
        assert hook_calls["post_migration"] == 2

    def test_run_migrations_error_handling(self, db: Session):
        """Should handle migration errors gracefully."""
        runner = MigrationRunner(db)

        def failing_upgrade():
            raise Exception("Migration failed!")

        migrations = [
            Migration(
                name="test1",
                version="001",
                dependencies=[],
                upgrade_func=failing_upgrade
            ),
        ]

        result = runner.run_migrations(
            migrations=migrations,
            dry_run=True,
            acquire_lock=False
        )

        assert result.success is False
        assert result.failed_migrations == 1
        assert "Migration failed!" in result.error_message

    def test_run_migrations_partial_failure(self, db: Session):
        """Should track partial completions."""
        runner = MigrationRunner(db)

        def working_upgrade():
            pass

        def failing_upgrade():
            raise Exception("Migration 2 failed!")

        migrations = [
            Migration(
                name="test1",
                version="001",
                dependencies=[],
                upgrade_func=working_upgrade
            ),
            Migration(
                name="test2",
                version="002",
                dependencies=["001"],
                upgrade_func=failing_upgrade
            ),
        ]

        result = runner.run_migrations(
            migrations=migrations,
            dry_run=True,
            acquire_lock=False
        )

        # First migration succeeds, second fails
        assert result.completed_migrations == 1
        assert result.failed_migrations == 1
        assert result.success is False

    def test_get_run_progress(self, db: Session):
        """Should retrieve run progress information."""
        runner = MigrationRunner(db)

        migrations = [
            Migration(
                name="test1",
                version="001",
                dependencies=[],
                upgrade_func=lambda: None
            ),
        ]

        result = runner.run_migrations(
            migrations=migrations,
            dry_run=True,
            acquire_lock=False
        )

        # Get progress
        progress = runner.get_run_progress(result.run_id)

        assert progress["run_id"] == str(result.run_id)
        assert progress["status"] == MigrationRunStatus.COMPLETED.value
        assert progress["total_migrations"] == 1
        assert progress["completed_migrations"] == 1
        assert progress["progress_percentage"] == 100.0

    def test_list_runs(self, db: Session):
        """Should list migration runs."""
        runner = MigrationRunner(db)

        # Create multiple runs
        migrations = [
            Migration(
                name="test1",
                version="001",
                dependencies=[],
                upgrade_func=lambda: None
            ),
        ]

        runner.run_migrations(
            migrations=migrations,
            dry_run=True,
            acquire_lock=False,
            run_name="run1"
        )

        runner.run_migrations(
            migrations=migrations,
            dry_run=False,
            acquire_lock=False,
            run_name="run2"
        )

        # List all runs
        runs = runner.list_runs()
        assert len(runs) >= 2

        # Filter by status
        completed_runs = runner.list_runs(
            status=MigrationRunStatus.COMPLETED
        )
        assert len(completed_runs) >= 1


class TestMigrationResult:
    """Tests for migration result dataclass."""

    def test_migration_result_success(self):
        """Should represent successful migration."""
        result = MigrationResult(
            run_id=uuid4(),
            success=True,
            total_migrations=5,
            completed_migrations=5,
            failed_migrations=0,
            dry_run=False,
            execution_time=10.5
        )

        assert result.success is True
        assert result.completed_migrations == result.total_migrations
        assert "SUCCESS" in repr(result)

    def test_migration_result_failure(self):
        """Should represent failed migration."""
        result = MigrationResult(
            run_id=uuid4(),
            success=False,
            total_migrations=5,
            completed_migrations=3,
            failed_migrations=2,
            error_message="Migration 4 failed",
            dry_run=False
        )

        assert result.success is False
        assert result.failed_migrations > 0
        assert "FAILED" in repr(result)

    def test_migration_result_dry_run(self):
        """Should indicate dry run mode."""
        result = MigrationResult(
            run_id=uuid4(),
            success=True,
            total_migrations=3,
            completed_migrations=3,
            dry_run=True
        )

        assert result.dry_run is True
        assert "DRY RUN" in repr(result)


class TestMigrationModels:
    """Tests for migration database models."""

    def test_migration_run_record(self, db: Session):
        """Should create migration run record."""
        record = MigrationRunRecord(
            id=uuid4(),
            run_name="test_run",
            total_migrations=10,
            status=MigrationRunStatus.RUNNING.value
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        assert record.id is not None
        assert record.run_name == "test_run"
        assert record.total_migrations == 10

    def test_migration_execution_record(self, db: Session):
        """Should create migration execution record."""
        run_id = uuid4()
        record = MigrationExecutionRecord(
            id=uuid4(),
            run_id=run_id,
            migration_name="test_migration",
            migration_version="001",
            status=MigrationRunStatus.COMPLETED.value,
            execution_order=1,
            dependencies=["000"]
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        assert record.id is not None
        assert record.run_id == run_id
        assert record.migration_version == "001"

    def test_migration_lock_model(self, db: Session):
        """Should create migration lock."""
        lock = MigrationLock(
            id=uuid4(),
            lock_name="test_lock",
            lock_holder="test_holder",
            status=MigrationLockStatus.LOCKED.value,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        db.add(lock)
        db.commit()
        db.refresh(lock)

        assert lock.id is not None
        assert lock.lock_name == "test_lock"
        assert not lock.is_expired()

    def test_migration_lock_expiration(self, db: Session):
        """Should detect expired locks."""
        lock = MigrationLock(
            id=uuid4(),
            lock_name="test_lock",
            lock_holder="test_holder",
            status=MigrationLockStatus.LOCKED.value,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )

        db.add(lock)
        db.commit()

        assert lock.is_expired()

    def test_migration_lock_refresh_heartbeat(self, db: Session):
        """Should refresh lock heartbeat."""
        lock = MigrationLock(
            id=uuid4(),
            lock_name="test_lock",
            lock_holder="test_holder",
            status=MigrationLockStatus.LOCKED.value,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        db.add(lock)
        db.commit()

        original_heartbeat = lock.heartbeat_at

        time.sleep(0.1)
        lock.refresh_heartbeat()
        db.commit()

        assert lock.heartbeat_at > original_heartbeat
