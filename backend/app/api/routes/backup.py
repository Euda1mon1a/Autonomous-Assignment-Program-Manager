"""Database backup API routes.

Provides lightweight snapshot endpoints for admin bulk operations.
Creates point-in-time table snapshots before bulk operations for rollback.
"""

import logging
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.permissions.decorators import require_role
from app.core.config import settings
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# Allowed tables for snapshot (whitelist for security)
# Accepts both snake_case (backend convention) and camelCase (frontend convention)
# to handle axios interceptor only converting keys, not string values.
# See: Session 086 - "impedance mismatch" research
ALLOWED_SNAPSHOT_TABLES = {
    # snake_case (backend/DB convention)
    "rotation_templates",
    "weekly_patterns",
    "rotation_halfday_requirements",
    "rotation_preferences",
    "people",
    "absences",
    "assignments",
    # camelCase (frontend convention)
    "rotationTemplates",
    "weeklyPatterns",
    "rotationHalfdayRequirements",
    "rotationPreferences",
    # Note: "people", "absences", "assignments" are same in both conventions
}

# Snapshot storage directory
SNAPSHOT_DIR = Path("backups/snapshots")


# ============================================================================
# Schemas
# ============================================================================


class SnapshotRequest(BaseModel):
    """Request to create a table snapshot."""

    table: str = Field(..., description="Table name to snapshot")
    reason: str = Field(..., description="Reason for snapshot (audit trail)")


class SnapshotResponse(BaseModel):
    """Response after creating a snapshot."""

    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    table: str = Field(..., description="Table that was snapshotted")
    row_count: int = Field(..., description="Number of rows captured")
    file_path: str = Field(..., description="Path to snapshot file")
    created_at: datetime = Field(..., description="Snapshot creation time")
    created_by: str = Field(..., description="User who created snapshot")
    reason: str = Field(..., description="Reason for snapshot")


class SnapshotListResponse(BaseModel):
    """List of available snapshots."""

    snapshots: list[SnapshotResponse]
    total: int


class RestoreRequest(BaseModel):
    """Request to restore from a snapshot."""

    snapshot_id: str = Field(..., description="Snapshot ID to restore")
    dry_run: bool = Field(True, description="Preview restore without applying")


class RestoreResponse(BaseModel):
    """Response after restoring from snapshot."""

    snapshot_id: str
    table: str
    rows_restored: int
    dry_run: bool
    message: str


# ============================================================================
# Helper Functions
# ============================================================================


def get_snapshot_dir() -> Path:
    """Get or create snapshot directory."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR


def generate_snapshot_id(table: str) -> str:
    """Generate unique snapshot ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{table}_{timestamp}"


# ============================================================================
# Routes
# ============================================================================


@router.post(
    "/backup/snapshot",
    response_model=SnapshotResponse,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def create_snapshot(
    request: SnapshotRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SnapshotResponse:
    """
    Create a lightweight snapshot of a specific table.

    Used before bulk operations to enable rollback if needed.

    Requires ADMIN role.

    Args:
        request: Snapshot request with table name and reason

    Returns:
        Snapshot information with ID for potential restore
    """
    # Validate table name against whitelist
    if request.table not in ALLOWED_SNAPSHOT_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Table '{request.table}' not allowed for snapshot. "
            f"Allowed tables: {', '.join(sorted(ALLOWED_SNAPSHOT_TABLES))}",
        )

    try:
        # Get row count
        count_result = db.execute(
            text(f"SELECT COUNT(*) FROM {request.table}")  # noqa: S608 - whitelist validated
        ).scalar()

        # Generate snapshot ID
        snapshot_id = generate_snapshot_id(request.table)
        snapshot_dir = get_snapshot_dir()
        file_path = snapshot_dir / f"{snapshot_id}.sql"

        # Create snapshot using pg_dump for single table
        # This is more reliable than COPY for preserving data integrity
        database_url = str(settings.DATABASE_URL)

        # Parse connection info from DATABASE_URL
        # Format: postgresql://user:pass@host:port/dbname
        if database_url.startswith("postgresql://"):
            # Extract parts using simple parsing
            db_part = database_url.replace("postgresql://", "")
            user_pass, host_db = db_part.split("@", 1)
            if ":" in user_pass:
                db_user, db_pass = user_pass.split(":", 1)
            else:
                db_user = user_pass
                db_pass = ""
            host_port, db_name = host_db.split("/", 1)
            if ":" in host_port:
                db_host, db_port = host_port.split(":", 1)
            else:
                db_host = host_port
                db_port = "5432"

            # Create snapshot with pg_dump
            env = {"PGPASSWORD": db_pass}
            cmd = [
                "pg_dump",
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "-d",
                db_name,
                "-t",
                request.table,
                "--data-only",
                "--inserts",
                "-f",
                str(file_path),
            ]

            result = subprocess.run(
                cmd,
                env={**subprocess.os.environ, **env},
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create snapshot: {result.stderr[:200]}",
                )
        else:
            raise HTTPException(
                status_code=500,
                detail="Unsupported database URL format",
            )

        created_at = datetime.utcnow()

        # Log the snapshot for audit
        logger.info(
            f"Snapshot created: {snapshot_id} for table {request.table} "
            f"({count_result} rows) by {current_user.username}. Reason: {request.reason}"
        )

        return SnapshotResponse(
            snapshot_id=snapshot_id,
            table=request.table,
            row_count=count_result,
            file_path=str(file_path),
            created_at=created_at,
            created_by=current_user.username,
            reason=request.reason,
        )

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Snapshot operation timed out",
        )
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred creating the snapshot",
        )


@router.get(
    "/backup/snapshots",
    response_model=SnapshotListResponse,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def list_snapshots(
    table: str | None = Query(None, description="Filter by table name"),
    limit: int = Query(20, ge=1, le=100, description="Max snapshots to return"),
    current_user: User = Depends(get_current_active_user),
) -> SnapshotListResponse:
    """
    List available snapshots.

    Requires ADMIN role.

    Args:
        table: Optional filter by table name
        limit: Maximum number of snapshots to return

    Returns:
        List of available snapshots
    """
    try:
        snapshot_dir = get_snapshot_dir()
        snapshots = []

        # List snapshot files
        pattern = f"{table}_*.sql" if table else "*.sql"
        files = sorted(snapshot_dir.glob(pattern), reverse=True)[:limit]

        for file_path in files:
            # Parse snapshot ID from filename
            snapshot_id = file_path.stem
            parts = snapshot_id.rsplit("_", 2)

            if len(parts) >= 3:
                table_name = "_".join(parts[:-2])
                # Parse date/time from filename
                try:
                    date_str = parts[-2]
                    time_str = parts[-1]
                    created_at = datetime.strptime(
                        f"{date_str}_{time_str}", "%Y%m%d_%H%M%S"
                    )
                except ValueError:
                    created_at = datetime.fromtimestamp(file_path.stat().st_mtime)
            else:
                table_name = parts[0]
                created_at = datetime.fromtimestamp(file_path.stat().st_mtime)

            # Get file size as proxy for row count (rough estimate)
            file_size = file_path.stat().st_size

            snapshots.append(
                SnapshotResponse(
                    snapshot_id=snapshot_id,
                    table=table_name,
                    row_count=-1,  # Would need to parse file to get actual count
                    file_path=str(file_path),
                    created_at=created_at,
                    created_by="unknown",  # Would need metadata file
                    reason="",  # Would need metadata file
                )
            )

        return SnapshotListResponse(
            snapshots=snapshots,
            total=len(snapshots),
        )

    except Exception as e:
        logger.error(f"Error listing snapshots: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred listing snapshots",
        )


@router.post(
    "/backup/restore",
    response_model=RestoreResponse,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def restore_snapshot(
    request: RestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RestoreResponse:
    """
    Restore a table from a snapshot.

    WARNING: This will replace all data in the table with snapshot data.

    Requires ADMIN role.

    Args:
        request: Restore request with snapshot ID and dry_run flag

    Returns:
        Restore result
    """
    try:
        snapshot_dir = get_snapshot_dir()
        file_path = snapshot_dir / f"{request.snapshot_id}.sql"

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot '{request.snapshot_id}' not found",
            )

        # Parse table name from snapshot ID
        parts = request.snapshot_id.rsplit("_", 2)
        if len(parts) >= 3:
            table_name = "_".join(parts[:-2])
        else:
            table_name = parts[0]

        # Validate table is in whitelist
        if table_name not in ALLOWED_SNAPSHOT_TABLES:
            raise HTTPException(
                status_code=400,
                detail=f"Table '{table_name}' not allowed for restore",
            )

        if request.dry_run:
            # Count lines in file as estimate
            with open(file_path) as f:
                line_count = sum(1 for line in f if line.startswith("INSERT"))

            return RestoreResponse(
                snapshot_id=request.snapshot_id,
                table=table_name,
                rows_restored=line_count,
                dry_run=True,
                message=f"DRY RUN: Would restore ~{line_count} rows to {table_name}",
            )

        # Actually restore - use psql to run the SQL file
        database_url = str(settings.DATABASE_URL)

        if database_url.startswith("postgresql://"):
            db_part = database_url.replace("postgresql://", "")
            user_pass, host_db = db_part.split("@", 1)
            if ":" in user_pass:
                db_user, db_pass = user_pass.split(":", 1)
            else:
                db_user = user_pass
                db_pass = ""
            host_port, db_name = host_db.split("/", 1)
            if ":" in host_port:
                db_host, db_port = host_port.split(":", 1)
            else:
                db_host = host_port
                db_port = "5432"

            # First truncate the table
            db.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))  # noqa: S608
            db.commit()

            # Then restore from snapshot
            env = {"PGPASSWORD": db_pass}
            cmd = [
                "psql",
                "-h",
                db_host,
                "-p",
                db_port,
                "-U",
                db_user,
                "-d",
                db_name,
                "-f",
                str(file_path),
            ]

            result = subprocess.run(
                cmd,
                env={**subprocess.os.environ, **env},
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                logger.error(f"psql restore failed: {result.stderr}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to restore snapshot: {result.stderr[:200]}",
                )

            # Count restored rows
            row_count = db.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
            ).scalar()

            logger.warning(
                f"Snapshot restored: {request.snapshot_id} to {table_name} "
                f"({row_count} rows) by {current_user.username}"
            )

            return RestoreResponse(
                snapshot_id=request.snapshot_id,
                table=table_name,
                rows_restored=row_count,
                dry_run=False,
                message=f"Successfully restored {row_count} rows to {table_name}",
            )

        else:
            raise HTTPException(
                status_code=500,
                detail="Unsupported database URL format",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring snapshot: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred restoring the snapshot",
        )


# ============================================================================
# Full Database Backup Schemas
# ============================================================================


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


class CreateBackupRequest(BaseModel):
    """Request to create a full database backup."""

    strategy: BackupStrategy = Field(
        BackupStrategy.FULL, description="Backup strategy to use"
    )
    description: str = Field("", description="Optional description for audit trail")


class BackupResult(BaseModel):
    """Result of a backup operation."""

    backup_id: str = Field(..., description="Unique backup identifier")
    created_at: datetime = Field(..., description="Backup creation timestamp")
    size_mb: float = Field(..., description="Backup file size in MB")
    strategy: str = Field(..., description="Backup strategy used")
    status: str = Field(..., description="Backup status")
    file_path: str = Field(..., description="Path to backup file")
    schema_version: str | None = Field(None, description="Alembic schema version")


class BackupListResult(BaseModel):
    """List of available backups."""

    backups: list[BackupResult]
    total_count: int
    storage_used_mb: float


class BackupVerifyResult(BaseModel):
    """Result of backup verification."""

    backup_id: str
    valid: bool
    checksum: str | None
    file_exists: bool
    size_mb: float
    error: str | None = None


class BackupStatusResponse(BaseModel):
    """Backup system health status."""

    healthy: bool
    latest_backup_age_hours: float | None
    latest_backup_id: str | None
    total_backups: int
    storage_used_mb: float
    backup_directory: str
    warnings: list[str]


class RestoreBackupRequest(BaseModel):
    """Request to restore from a backup."""

    dry_run: bool = Field(True, description="Preview restore without applying")


# ============================================================================
# Full Database Backup Helper Functions
# ============================================================================

BACKUP_DIR = Path("backups/postgres")


def get_backup_dir() -> Path:
    """Get or create backup directory."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def parse_backup_metadata(backup_file: Path) -> dict:
    """Parse backup metadata from companion .metadata file."""
    metadata_file = backup_file.with_suffix(".metadata")
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                import json

                return json.load(f)
        except Exception:
            pass
    return {}


# ============================================================================
# Full Database Backup Routes
# ============================================================================


@router.post(
    "/backup/create",
    response_model=BackupResult,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def create_backup(
    request: CreateBackupRequest,
    current_user: User = Depends(get_current_active_user),
) -> BackupResult:
    """
    Create a full database backup.

    Triggers the backup script to create a compressed PostgreSQL backup.
    Requires ADMIN role.

    Args:
        request: Backup request with strategy and description

    Returns:
        Backup result with backup_id, size, and status
    """
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_id = f"residency_scheduler_{timestamp}"

        # Run backup script
        script_path = Path("scripts/backup-db.sh")
        if not script_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Backup script not found",
            )

        cmd = ["bash", str(script_path), "--docker"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=Path(".").absolute(),
        )

        if result.returncode != 0:
            logger.error(f"Backup script failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Backup failed: {result.stderr[:200]}",
            )

        # Find the created backup file
        backup_dir = get_backup_dir()
        backup_files = sorted(backup_dir.glob("*.sql.gz"), reverse=True)

        if not backup_files:
            raise HTTPException(
                status_code=500,
                detail="Backup file not created",
            )

        latest_backup = backup_files[0]
        size_bytes = latest_backup.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        # Get schema version from metadata
        metadata = parse_backup_metadata(latest_backup)
        schema_version = metadata.get("alembic_version")

        # Log the backup for audit
        logger.info(
            f"Full backup created: {latest_backup.stem} "
            f"({size_mb:.2f}MB) by {current_user.username}. "
            f"Strategy: {request.strategy.value}. Description: {request.description}"
        )

        return BackupResult(
            backup_id=latest_backup.stem.replace(".sql", ""),
            created_at=datetime.utcnow(),
            size_mb=round(size_mb, 2),
            strategy=request.strategy.value,
            status=BackupStatus.SUCCESS.value,
            file_path=str(latest_backup),
            schema_version=schema_version,
        )

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Backup operation timed out",
        )
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred creating the backup",
        )


@router.get(
    "/backup/list",
    response_model=BackupListResult,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def list_backups(
    limit: int = Query(50, ge=1, le=100, description="Max backups to return"),
    strategy: str | None = Query(None, description="Filter by strategy"),
    current_user: User = Depends(get_current_active_user),
) -> BackupListResult:
    """
    List available database backups.

    Requires ADMIN role.

    Args:
        limit: Maximum number of backups to return
        strategy: Optional filter by strategy type

    Returns:
        List of backups with metadata and storage stats
    """
    try:
        backup_dir = get_backup_dir()
        backup_files = sorted(backup_dir.glob("*.sql.gz"), reverse=True)[:limit]

        backups = []
        total_size = 0.0

        for backup_file in backup_files:
            size_bytes = backup_file.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            total_size += size_mb

            # Parse timestamp from filename
            # Format: residency_scheduler_YYYYMMDD_HHMMSS.sql.gz
            filename = backup_file.stem.replace(".sql", "")
            parts = filename.split("_")
            if len(parts) >= 4:
                try:
                    date_str = parts[-2]
                    time_str = parts[-1]
                    created_at = datetime.strptime(
                        f"{date_str}_{time_str}", "%Y%m%d_%H%M%S"
                    )
                except ValueError:
                    created_at = datetime.fromtimestamp(backup_file.stat().st_mtime)
            else:
                created_at = datetime.fromtimestamp(backup_file.stat().st_mtime)

            metadata = parse_backup_metadata(backup_file)

            # Filter by strategy if specified
            backup_strategy = metadata.get("strategy", "full")
            if strategy and backup_strategy != strategy:
                continue

            backups.append(
                BackupResult(
                    backup_id=filename,
                    created_at=created_at,
                    size_mb=round(size_mb, 2),
                    strategy=backup_strategy,
                    status=BackupStatus.SUCCESS.value,
                    file_path=str(backup_file),
                    schema_version=metadata.get("alembic_version"),
                )
            )

        return BackupListResult(
            backups=backups,
            total_count=len(backups),
            storage_used_mb=round(total_size, 2),
        )

    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred listing backups",
        )


@router.post(
    "/backup/restore/{backup_id}",
    response_model=RestoreResponse,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def restore_from_backup(
    backup_id: str,
    request: RestoreBackupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RestoreResponse:
    """
    Restore database from a full backup.

    WARNING: This will replace all data in the database.

    Requires ADMIN role.

    Args:
        backup_id: ID of backup to restore
        request: Restore request with dry_run flag

    Returns:
        Restore result
    """
    try:
        backup_dir = get_backup_dir()
        backup_file = backup_dir / f"{backup_id}.sql.gz"

        if not backup_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Backup '{backup_id}' not found",
            )

        if request.dry_run:
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            return RestoreResponse(
                snapshot_id=backup_id,
                table="full_database",
                rows_restored=-1,
                dry_run=True,
                message=f"DRY RUN: Would restore full database from {backup_id} ({size_mb:.2f}MB)",
            )

        # Parse database connection
        database_url = str(settings.DATABASE_URL)

        if database_url.startswith("postgresql://"):
            db_part = database_url.replace("postgresql://", "")
            user_pass, host_db = db_part.split("@", 1)
            if ":" in user_pass:
                db_user, db_pass = user_pass.split(":", 1)
            else:
                db_user = user_pass
                db_pass = ""
            host_port, db_name = host_db.split("/", 1)
            if ":" in host_port:
                db_host, db_port = host_port.split(":", 1)
            else:
                db_host = host_port
                db_port = "5432"

            # Decompress and restore
            env = {"PGPASSWORD": db_pass}

            # Use gunzip piped to psql
            cmd = f"gunzip -c {backup_file} | psql -h {db_host} -p {db_port} -U {db_user} -d {db_name}"

            result = subprocess.run(
                cmd,
                shell=True,  # noqa: S602 - required for pipe  # nosec B602
                env={**subprocess.os.environ, **env},
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to restore backup: {result.stderr[:200]}",
                )

            logger.warning(
                f"Full restore completed: {backup_id} by {current_user.username}"
            )

            return RestoreResponse(
                snapshot_id=backup_id,
                table="full_database",
                rows_restored=-1,  # Unknown for full restore
                dry_run=False,
                message=f"Successfully restored database from {backup_id}",
            )

        else:
            raise HTTPException(
                status_code=500,
                detail="Unsupported database URL format",
            )

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Restore operation timed out",
        )
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred restoring the backup",
        )


@router.get(
    "/backup/verify/{backup_id}",
    response_model=BackupVerifyResult,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def verify_backup(
    backup_id: str,
    current_user: User = Depends(get_current_active_user),
) -> BackupVerifyResult:
    """
    Verify backup integrity.

    Checks file existence and calculates checksum.

    Requires ADMIN role.

    Args:
        backup_id: ID of backup to verify

    Returns:
        Verification result with checksum and validity
    """
    try:
        import hashlib

        backup_dir = get_backup_dir()
        backup_file = backup_dir / f"{backup_id}.sql.gz"

        if not backup_file.exists():
            return BackupVerifyResult(
                backup_id=backup_id,
                valid=False,
                checksum=None,
                file_exists=False,
                size_mb=0.0,
                error="Backup file not found",
            )

        # Calculate MD5 checksum (not for security, just integrity verification)
        hash_md5 = hashlib.md5(usedforsecurity=False)  # noqa: S324
        with open(backup_file, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)

        checksum = hash_md5.hexdigest()
        size_mb = backup_file.stat().st_size / (1024 * 1024)

        # Basic validation - file should be at least 1KB
        valid = size_mb > 0.001

        logger.info(
            f"Backup verified: {backup_id} - valid={valid}, checksum={checksum}"
        )

        return BackupVerifyResult(
            backup_id=backup_id,
            valid=valid,
            checksum=checksum,
            file_exists=True,
            size_mb=round(size_mb, 2),
            error=None,
        )

    except Exception as e:
        logger.error(f"Error verifying backup: {e}")
        return BackupVerifyResult(
            backup_id=backup_id,
            valid=False,
            checksum=None,
            file_exists=False,
            size_mb=0.0,
            error=str(e),
        )


@router.get(
    "/backup/status",
    response_model=BackupStatusResponse,
    dependencies=[Depends(require_role("ADMIN"))],
)
async def get_backup_status(
    current_user: User = Depends(get_current_active_user),
) -> BackupStatusResponse:
    """
    Get backup system health status.

    Returns latest backup age, total count, and warnings.

    Requires ADMIN role.

    Returns:
        Backup system status with health indicators
    """
    try:
        backup_dir = get_backup_dir()
        backup_files = sorted(backup_dir.glob("*.sql.gz"), reverse=True)

        warnings = []
        latest_backup_age_hours = None
        latest_backup_id = None
        total_size = 0.0

        for backup_file in backup_files:
            total_size += backup_file.stat().st_size / (1024 * 1024)

        if backup_files:
            latest_backup = backup_files[0]
            latest_backup_id = latest_backup.stem.replace(".sql", "")
            mtime = datetime.fromtimestamp(latest_backup.stat().st_mtime)
            age = datetime.utcnow() - mtime
            latest_backup_age_hours = age.total_seconds() / 3600

            # Warn if backup is older than 24 hours
            if latest_backup_age_hours > 24:
                warnings.append(
                    f"Latest backup is {latest_backup_age_hours:.1f} hours old"
                )

            # Warn if backup is older than 7 days
            if latest_backup_age_hours > 168:
                warnings.append("CRITICAL: No backup in over 7 days")
        else:
            warnings.append("No backups found")

        healthy = len(warnings) == 0 or (
            len(warnings) == 1 and "24 hours" in warnings[0]
        )

        return BackupStatusResponse(
            healthy=healthy,
            latest_backup_age_hours=round(latest_backup_age_hours, 2)
            if latest_backup_age_hours
            else None,
            latest_backup_id=latest_backup_id,
            total_backups=len(backup_files),
            storage_used_mb=round(total_size, 2),
            backup_directory=str(backup_dir.absolute()),
            warnings=warnings,
        )

    except Exception as e:
        logger.error(f"Error getting backup status: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred getting backup status",
        )
