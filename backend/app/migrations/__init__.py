"""Data migration utilities for database operations.

This package provides tools for:
- Batch data migration
- Data transformation pipelines
- Validation before/after migration
- Rollback capabilities
- Progress tracking
- Dry-run mode
- Migration history
- Migration orchestration and execution
- Dependency resolution
- Distributed locking

Usage:
    from app.migrations.migrator import DataMigrator
    from app.migrations.validators import MigrationValidator
    from app.migrations.transformers import DataTransformer
    from app.migrations.rollback import RollbackManager
    from app.migrations.runner import MigrationRunner

Example (Data Migration):
    # Create a migration
    migrator = DataMigrator(db_session)
    migration_id = migrator.create_migration(
        name="update_faculty_roles",
        description="Update faculty roles to new schema"
    )

    # Validate before migration
    validator = MigrationValidator(db_session)
    is_valid = validator.validate_pre_migration(migration_id)

    # Execute migration
    if is_valid:
        migrator.execute_migration(migration_id, dry_run=False)

    # Rollback if needed
    rollback_mgr = RollbackManager(db_session)
    rollback_mgr.rollback_migration(migration_id)

Example (Migration Runner):
    # Discover and run migrations
    runner = MigrationRunner(db_session)
    migrations = runner.discover_migrations("alembic/versions")

    # Dry run first
    result = runner.run_migrations(
        migrations=migrations,
        dry_run=True,
        target_version="head"
    )

    # Execute if successful
    if result.success:
        runner.run_migrations(
            migrations=migrations,
            dry_run=False,
            target_version="head"
        )
"""

from app.migrations.migrator import DataMigrator, MigrationStatus
from app.migrations.rollback import RollbackManager, RollbackStrategy
from app.migrations.runner import (
    DependencyResolver,
    Migration,
    MigrationDependencyError,
    MigrationDiscovery,
    MigrationError,
    MigrationHooks,
    MigrationLockError,
    MigrationLockManager,
    MigrationResult,
    MigrationRunner,
    MigrationRunStatus,
    MigrationVerificationError,
)
from app.migrations.transformers import DataTransformer, TransformationPipeline
from app.migrations.validators import MigrationValidator, ValidationResult

__all__ = [
    # Data Migration
    "DataMigrator",
    "MigrationStatus",
    "MigrationValidator",
    "ValidationResult",
    "DataTransformer",
    "TransformationPipeline",
    "RollbackManager",
    "RollbackStrategy",
    # Migration Runner
    "MigrationRunner",
    "MigrationRunStatus",
    "MigrationLockManager",
    "MigrationDiscovery",
    "DependencyResolver",
    "Migration",
    "MigrationResult",
    "MigrationHooks",
    "MigrationError",
    "MigrationLockError",
    "MigrationDependencyError",
    "MigrationVerificationError",
]
