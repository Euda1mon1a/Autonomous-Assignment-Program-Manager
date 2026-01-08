"""Database backup API routes.

Provides lightweight snapshot endpoints for admin bulk operations.
Creates point-in-time table snapshots before bulk operations for rollback.
"""

import logging
import subprocess
from datetime import datetime
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
ALLOWED_SNAPSHOT_TABLES = {
    "rotation_templates",
    "weekly_patterns",
    "rotation_halfday_requirements",
    "rotation_preferences",
    "people",
    "absences",
    "assignments",
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
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-d", db_name,
                "-t", request.table,
                "--data-only",
                "--inserts",
                "-f", str(file_path),
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
                "-h", db_host,
                "-p", db_port,
                "-U", db_user,
                "-d", db_name,
                "-f", str(file_path),
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
