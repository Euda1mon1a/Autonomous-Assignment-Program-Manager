"""Data migration utilities for database operations.

This package provides tools for:
- Batch data migration
- Data transformation pipelines
- Validation before/after migration
- Rollback capabilities
- Progress tracking
- Dry-run mode
- Migration history

Usage:
    from app.migrations.migrator import DataMigrator
    from app.migrations.validators import MigrationValidator
    from app.migrations.transformers import DataTransformer
    from app.migrations.rollback import RollbackManager

Example:
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
"""

from app.migrations.migrator import DataMigrator, MigrationStatus
from app.migrations.validators import MigrationValidator, ValidationResult
from app.migrations.transformers import DataTransformer, TransformationPipeline
from app.migrations.rollback import RollbackManager, RollbackStrategy

__all__ = [
    "DataMigrator",
    "MigrationStatus",
    "MigrationValidator",
    "ValidationResult",
    "DataTransformer",
    "TransformationPipeline",
    "RollbackManager",
    "RollbackStrategy",
]
