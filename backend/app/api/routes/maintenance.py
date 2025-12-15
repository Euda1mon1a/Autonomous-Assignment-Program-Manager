"""Maintenance API routes for backup and restore operations."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_active_user
from app.maintenance.backup import BackupService
from app.maintenance.restore import RestoreService


router = APIRouter()


# Request/Response Schemas
class BackupRequest(BaseModel):
    """Request schema for creating a backup."""
    description: Optional[str] = Field(None, description="Optional description of the backup")
    compress: bool = Field(True, description="Whether to compress the backup file")
    tables: Optional[List[str]] = Field(None, description="Specific tables to backup (if None, backs up all)")


class BackupResponse(BaseModel):
    """Response schema for backup operation."""
    backup_id: str
    timestamp: str
    file_path: str
    total_records: int
    checksum: str
    compressed: bool
    size_bytes: int
    tables: Optional[List[str]] = None


class BackupListItem(BaseModel):
    """Schema for backup list item."""
    backup_id: str
    timestamp: str
    file_path: str
    size_bytes: int
    compressed: bool
    total_records: Optional[int] = None
    description: Optional[str] = None
    tables: Optional[List[str]] = None


class RestoreRequest(BaseModel):
    """Request schema for restore operation."""
    backup_id: str = Field(..., description="ID of the backup to restore")
    dry_run: bool = Field(False, description="If true, validate but don't actually restore")
    tables: Optional[List[str]] = Field(None, description="Specific tables to restore (if None, restores all)")
    clear_existing: bool = Field(True, description="Whether to clear existing data before restore")


class RestoreResponse(BaseModel):
    """Response schema for restore operation."""
    status: str
    backup_id: str
    restored_records: Optional[int] = None
    tables: Optional[dict] = None
    duration_seconds: Optional[float] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None


class ValidationResponse(BaseModel):
    """Response schema for backup validation."""
    valid: bool
    backup_id: Optional[str] = None
    timestamp: Optional[str] = None
    total_records: Optional[int] = None
    tables: Optional[List[str]] = None
    version: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None


class PreviewResponse(BaseModel):
    """Response schema for restore preview."""
    valid: bool
    backup_id: Optional[str] = None
    timestamp: Optional[str] = None
    description: Optional[str] = None
    total_records: Optional[int] = None
    table_statistics: Optional[dict] = None
    error: Optional[str] = None


# API Endpoints
@router.post("/backup", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a database backup. Requires authentication.

    Creates either a full backup or selective table backup.
    Backups are compressed by default and include metadata with checksums.

    - **description**: Optional description for the backup
    - **compress**: Whether to compress the backup (default: true)
    - **tables**: List of specific tables to backup (if None, backs up all tables)

    Returns backup metadata including backup_id, timestamp, and file location.
    """
    try:
        backup_service = BackupService(db)

        if request.tables:
            # Selective backup
            result = backup_service.create_selective_backup(
                table_names=request.tables,
                description=request.description,
                compress=request.compress,
            )
            result["tables"] = request.tables
        else:
            # Full backup
            result = backup_service.create_full_backup(
                description=request.description,
                compress=request.compress,
            )

        return BackupResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/backups", response_model=List[BackupListItem])
async def list_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all available backups. Requires authentication.

    Returns a list of all backup files with their metadata including:
    - backup_id: Unique identifier for the backup
    - timestamp: When the backup was created
    - size_bytes: File size
    - total_records: Number of records in the backup
    - tables: List of tables included in the backup
    """
    try:
        backup_service = BackupService(db)
        backups = backup_service.list_backups()
        return [BackupListItem(**backup) for backup in backups]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.get("/backups/{backup_id}", response_model=BackupListItem)
async def get_backup_info(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed information about a specific backup. Requires authentication.

    - **backup_id**: The unique identifier of the backup

    Returns detailed metadata about the backup.
    """
    try:
        backup_service = BackupService(db)
        backup_data = backup_service.get_backup(backup_id)

        if not backup_data:
            raise HTTPException(status_code=404, detail=f"Backup {backup_id} not found")

        metadata = backup_data.get("metadata", {})

        # Find the file to get size
        backups = backup_service.list_backups()
        backup_info = next((b for b in backups if b["backup_id"] == backup_id), None)

        if not backup_info:
            raise HTTPException(status_code=404, detail=f"Backup {backup_id} not found")

        return BackupListItem(**backup_info)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backup info: {str(e)}")


@router.get("/backups/{backup_id}/validate", response_model=ValidationResponse)
async def validate_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Validate a backup file. Requires authentication.

    Checks the integrity and validity of a backup file before restore.
    Validates:
    - File exists and is readable
    - Metadata is present and valid
    - All declared tables have data
    - Record counts match

    - **backup_id**: The unique identifier of the backup to validate

    Returns validation results.
    """
    try:
        restore_service = RestoreService(db)
        validation = restore_service.validate_backup(backup_id)
        return ValidationResponse(**validation)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/backups/{backup_id}/preview", response_model=PreviewResponse)
async def preview_restore(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Preview what would be restored from a backup. Requires authentication.

    Shows detailed statistics about the backup including:
    - Table names and record counts
    - Sample records from each table
    - Total records to be restored

    This is useful for verifying backup contents before performing a restore.

    - **backup_id**: The unique identifier of the backup to preview

    Returns preview information.
    """
    try:
        restore_service = RestoreService(db)
        preview = restore_service.get_restore_preview(backup_id)
        return PreviewResponse(**preview)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.post("/restore", response_model=RestoreResponse)
async def restore_backup(
    request: RestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Restore database from a backup. Requires authentication.

    **WARNING**: This operation will replace existing data!

    Supports:
    - Full restore: Restores all tables from backup
    - Selective restore: Restores only specified tables
    - Dry run: Validates without making changes
    - Automatic rollback on failure

    - **backup_id**: ID of the backup to restore
    - **dry_run**: If true, validates but doesn't actually restore
    - **tables**: Specific tables to restore (if None, restores all)
    - **clear_existing**: Whether to clear existing data before restore

    Returns restore results including status, records restored, and duration.
    """
    try:
        restore_service = RestoreService(db)

        if request.tables:
            # Selective restore
            result = restore_service.restore_selective(
                backup_id=request.backup_id,
                table_names=request.tables,
                dry_run=request.dry_run,
                clear_existing=request.clear_existing,
            )
        else:
            # Full restore
            result = restore_service.restore_full(
                backup_id=request.backup_id,
                dry_run=request.dry_run,
            )

        if result.get("status") == "failed":
            raise HTTPException(status_code=400, detail=result.get("error", "Restore failed"))

        return RestoreResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete("/backups/{backup_id}")
async def delete_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a backup file. Requires authentication.

    Permanently deletes a backup file from the system.
    This operation cannot be undone.

    - **backup_id**: The unique identifier of the backup to delete

    Returns success message if deleted.
    """
    try:
        backup_service = BackupService(db)
        deleted = backup_service.delete_backup(backup_id)

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Backup {backup_id} not found")

        return {
            "status": "success",
            "message": f"Backup {backup_id} deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")
