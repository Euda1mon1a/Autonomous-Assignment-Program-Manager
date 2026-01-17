"""
Database backup management tools for the Scheduler MCP server.

Provides MCP tools for creating, listing, restoring, and verifying
database backups via the FastAPI backend.
"""

import logging
from enum import Enum

from pydantic import BaseModel, Field

from .api_client import get_api_client

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class BackupStrategy(str, Enum):
    """Backup strategy types."""

    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(str, Enum):
    """Backup operation status."""

    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


# =============================================================================
# Response Models
# =============================================================================


class BackupInfo(BaseModel):
    """Information about a single backup."""

    backup_id: str = Field(..., description="Unique backup identifier")
    created_at: str = Field(..., description="Backup creation timestamp (ISO format)")
    size_mb: float = Field(..., description="Backup file size in MB")
    strategy: str = Field(..., description="Backup strategy used")
    status: str = Field(..., description="Backup status")
    file_path: str = Field(..., description="Path to backup file")
    schema_version: str | None = Field(None, description="Alembic schema version")


class CreateBackupResult(BaseModel):
    """Result of creating a backup."""

    success: bool = Field(..., description="Whether backup was created successfully")
    backup: BackupInfo | None = Field(None, description="Backup details if successful")
    error: str | None = Field(None, description="Error message if failed")


class ListBackupsResult(BaseModel):
    """Result of listing backups."""

    backups: list[BackupInfo] = Field(..., description="List of available backups")
    total_count: int = Field(..., description="Total number of backups")
    storage_used_mb: float = Field(..., description="Total storage used in MB")


class RestoreBackupResult(BaseModel):
    """Result of restoring from a backup."""

    success: bool = Field(..., description="Whether restore was successful")
    backup_id: str = Field(..., description="ID of backup restored")
    dry_run: bool = Field(..., description="Whether this was a dry run")
    message: str = Field(..., description="Status message")
    error: str | None = Field(None, description="Error message if failed")


class VerifyBackupResult(BaseModel):
    """Result of verifying a backup."""

    backup_id: str = Field(..., description="ID of backup verified")
    valid: bool = Field(..., description="Whether backup is valid")
    checksum: str | None = Field(None, description="MD5 checksum of backup file")
    file_exists: bool = Field(..., description="Whether backup file exists")
    size_mb: float = Field(..., description="Backup file size in MB")
    error: str | None = Field(None, description="Error message if verification failed")


class BackupStatusResult(BaseModel):
    """Backup system health status."""

    healthy: bool = Field(..., description="Whether backup system is healthy")
    latest_backup_age_hours: float | None = Field(
        None, description="Age of most recent backup in hours"
    )
    latest_backup_id: str | None = Field(
        None, description="ID of most recent backup"
    )
    total_backups: int = Field(..., description="Total number of backups available")
    storage_used_mb: float = Field(..., description="Total storage used in MB")
    backup_directory: str = Field(..., description="Path to backup directory")
    warnings: list[str] = Field(
        default_factory=list, description="List of warnings"
    )


# =============================================================================
# Tool Functions
# =============================================================================


async def create_backup(
    strategy: str = "full",
    description: str = "",
) -> CreateBackupResult:
    """
    Create a database backup.

    Triggers backup creation via the backend API, which runs the backup
    script and creates a compressed PostgreSQL dump.

    Args:
        strategy: Backup strategy - "full", "incremental", or "differential"
        description: Optional description for audit trail

    Returns:
        CreateBackupResult with backup details or error

    Raises:
        ValueError: If strategy is invalid
    """
    # Validate strategy
    valid_strategies = [s.value for s in BackupStrategy]
    if strategy not in valid_strategies:
        raise ValueError(
            f"Invalid strategy: {strategy}. Must be one of: {valid_strategies}"
        )

    try:
        client = await get_api_client()
        result = await client.create_backup(
            strategy=strategy,
            description=description,
        )

        # Parse response into model
        backup_info = BackupInfo(
            backup_id=result["backup_id"],
            created_at=result["created_at"],
            size_mb=result["size_mb"],
            strategy=result["strategy"],
            status=result["status"],
            file_path=result["file_path"],
            schema_version=result.get("schema_version"),
        )

        logger.info(f"Backup created: {backup_info.backup_id} ({backup_info.size_mb}MB)")

        return CreateBackupResult(
            success=True,
            backup=backup_info,
            error=None,
        )

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return CreateBackupResult(
            success=False,
            backup=None,
            error=str(e),
        )


async def list_backups(
    limit: int = 50,
    strategy: str | None = None,
) -> ListBackupsResult:
    """
    List available database backups.

    Retrieves list of backups from the backend API with metadata
    and storage statistics.

    Args:
        limit: Maximum backups to return (default 50, max 100)
        strategy: Filter by strategy type (optional)

    Returns:
        ListBackupsResult with backups and storage stats
    """
    try:
        client = await get_api_client()
        result = await client.list_backups(
            limit=min(limit, 100),
            strategy=strategy,
        )

        # Parse backups
        backups = []
        for b in result.get("backups", []):
            backups.append(
                BackupInfo(
                    backup_id=b["backup_id"],
                    created_at=b["created_at"],
                    size_mb=b["size_mb"],
                    strategy=b["strategy"],
                    status=b["status"],
                    file_path=b["file_path"],
                    schema_version=b.get("schema_version"),
                )
            )

        return ListBackupsResult(
            backups=backups,
            total_count=result.get("total_count", len(backups)),
            storage_used_mb=result.get("storage_used_mb", 0.0),
        )

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        return ListBackupsResult(
            backups=[],
            total_count=0,
            storage_used_mb=0.0,
        )


async def restore_backup(
    backup_id: str,
    dry_run: bool = True,
) -> RestoreBackupResult:
    """
    Restore database from a backup.

    WARNING: Non-dry-run will replace ALL data in the database.
    Always run with dry_run=True first to preview the restore.

    Args:
        backup_id: ID of backup to restore
        dry_run: If True, preview restore without applying (default True)

    Returns:
        RestoreBackupResult with status and message
    """
    try:
        client = await get_api_client()
        result = await client.restore_backup(
            backup_id=backup_id,
            dry_run=dry_run,
        )

        if dry_run:
            logger.info(f"DRY RUN restore from backup: {backup_id}")
        else:
            logger.warning(f"RESTORED database from backup: {backup_id}")

        return RestoreBackupResult(
            success=True,
            backup_id=backup_id,
            dry_run=dry_run,
            message=result.get("message", "Restore completed"),
            error=None,
        )

    except Exception as e:
        logger.error(f"Failed to restore backup {backup_id}: {e}")
        return RestoreBackupResult(
            success=False,
            backup_id=backup_id,
            dry_run=dry_run,
            message=f"Restore failed: {e}",
            error=str(e),
        )


async def verify_backup(
    backup_id: str,
) -> VerifyBackupResult:
    """
    Verify backup integrity.

    Checks that the backup file exists and calculates its checksum
    for integrity verification.

    Args:
        backup_id: ID of backup to verify

    Returns:
        VerifyBackupResult with checksum and validity status
    """
    try:
        client = await get_api_client()
        result = await client.verify_backup(backup_id=backup_id)

        return VerifyBackupResult(
            backup_id=backup_id,
            valid=result.get("valid", False),
            checksum=result.get("checksum"),
            file_exists=result.get("file_exists", False),
            size_mb=result.get("size_mb", 0.0),
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Failed to verify backup {backup_id}: {e}")
        return VerifyBackupResult(
            backup_id=backup_id,
            valid=False,
            checksum=None,
            file_exists=False,
            size_mb=0.0,
            error=str(e),
        )


async def get_backup_status() -> BackupStatusResult:
    """
    Get backup system health status.

    Returns the age of the latest backup, total backup count,
    storage usage, and any warnings about backup health.

    Returns:
        BackupStatusResult with health indicators and warnings
    """
    try:
        client = await get_api_client()
        result = await client.get_backup_status()

        return BackupStatusResult(
            healthy=result.get("healthy", False),
            latest_backup_age_hours=result.get("latest_backup_age_hours"),
            latest_backup_id=result.get("latest_backup_id"),
            total_backups=result.get("total_backups", 0),
            storage_used_mb=result.get("storage_used_mb", 0.0),
            backup_directory=result.get("backup_directory", ""),
            warnings=result.get("warnings", []),
        )

    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        return BackupStatusResult(
            healthy=False,
            latest_backup_age_hours=None,
            latest_backup_id=None,
            total_backups=0,
            storage_used_mb=0.0,
            backup_directory="",
            warnings=[f"Failed to get status: {e}"],
        )
