"""Upload API routes.

Provides endpoints for file uploads with validation, processing, and storage.
"""

import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.security import get_current_active_user
from app.core.slowapi_limiter import limiter
from app.models.user import User
from app.schemas.upload import (
    DeleteFileResponse,
    FileUrlResponse,
    UploadProgressResponse,
    UploadResponse,
)
from app.services.upload import UploadService
from app.services.upload.storage import LocalStorageBackend, S3StorageBackend
from app.services.upload.validators import FileValidator, UploadValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


def get_upload_service() -> UploadService:
    """
    Get upload service instance with configured storage backend.

    Returns:
        UploadService: Configured upload service
    """
    settings = get_settings()

    # Determine storage backend from config
    storage_type = getattr(settings, "UPLOAD_STORAGE_BACKEND", "local")

    if storage_type == "s3":
        # S3 storage configuration
        storage = S3StorageBackend(
            bucket_name=getattr(settings, "UPLOAD_S3_BUCKET", "uploads"),
            region=getattr(settings, "UPLOAD_S3_REGION", "us-east-1"),
            access_key=getattr(settings, "UPLOAD_S3_ACCESS_KEY", None),
            secret_key=getattr(settings, "UPLOAD_S3_SECRET_KEY", None),
            endpoint_url=getattr(settings, "UPLOAD_S3_ENDPOINT_URL", None),
        )
    else:
        # Local storage (default)
        default_upload_dir = Path(tempfile.gettempdir()) / "uploads"
        upload_dir = Path(getattr(settings, "UPLOAD_LOCAL_DIR", default_upload_dir))
        storage = LocalStorageBackend(base_path=upload_dir)

    # Configure validator
    max_size_mb = getattr(settings, "UPLOAD_MAX_SIZE_MB", 50)
    enable_virus_scan = getattr(settings, "UPLOAD_ENABLE_VIRUS_SCAN", False)

    validator = FileValidator(
        max_size_mb=max_size_mb,
        enable_virus_scan=enable_virus_scan,
    )

    return UploadService(storage_backend=storage, validator=validator)


def get_upload_service_dependency(request: Request) -> UploadService:
    """Resolve upload service while honoring test overrides and monkeypatching."""
    override = request.app.dependency_overrides.get(get_upload_service)
    if override:
        return override()
    return get_upload_service()


def _normalize_upload_result(
    result: dict[str, Any], *, fallback_filename: str
) -> dict[str, Any]:
    """Normalize legacy and current upload payloads to a stable API contract."""
    file_id = str(result.get("file_id") or "")
    filename = str(result.get("filename") or fallback_filename)
    mime_type = str(result.get("mime_type") or result.get("content_type") or "unknown")

    try:
        size_bytes = int(result.get("size_bytes") or result.get("size") or 0)
    except (TypeError, ValueError):
        size_bytes = 0

    versions = result.get("versions")
    if not isinstance(versions, dict):
        versions = None

    image_data = result.get("image_data")
    if not isinstance(image_data, dict):
        image_data = None

    thumbnails = result.get("thumbnails")
    if not isinstance(thumbnails, dict):
        thumbnails = None

    metadata = result.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    return {
        "upload_id": str(result.get("upload_id") or file_id),
        "file_id": file_id,
        "filename": filename,
        "original_filename": str(result.get("original_filename") or filename),
        "url": str(result.get("url") or f"/api/v1/upload/{file_id}/download"),
        "mime_type": mime_type,
        "size_bytes": size_bytes,
        "checksum": str(result.get("checksum") or ""),
        "category": str(result.get("category") or "document"),
        "uploaded_at": str(result.get("uploaded_at") or datetime.utcnow().isoformat()),
        "storage_backend": str(result.get("storage_backend") or "local"),
        "versions": versions,
        "image_data": image_data,
        "metadata": metadata,
        # Legacy aliases used by existing clients/tests.
        "size": size_bytes,
        "content_type": mime_type,
        "thumbnails": thumbnails,
    }


def _normalize_upload_progress(
    progress: dict[str, Any], *, requested_upload_id: str
) -> dict[str, Any]:
    """Normalize progress payloads from legacy and current service formats."""
    try:
        total_size = int(progress.get("total_size") or progress.get("total_bytes") or 0)
    except (TypeError, ValueError):
        total_size = 0

    try:
        uploaded_size = int(
            progress.get("uploaded_size") or progress.get("bytes_uploaded") or 0
        )
    except (TypeError, ValueError):
        uploaded_size = 0

    raw_progress = progress.get("progress_percent")
    if raw_progress is None:
        raw_progress = progress.get("progress")
    try:
        progress_percent = float(raw_progress or 0.0)
    except (TypeError, ValueError):
        progress_percent = 0.0

    started_at = progress.get("started_at") or datetime.utcnow().isoformat()
    completed_at = progress.get("completed_at")

    return {
        "upload_id": str(progress.get("upload_id") or requested_upload_id),
        "total_size": total_size,
        "uploaded_size": uploaded_size,
        "progress_percent": progress_percent,
        "status": str(progress.get("status") or "in_progress"),
        "started_at": str(started_at),
        "completed_at": str(completed_at) if completed_at else None,
        # Legacy aliases used by existing clients/tests.
        "progress": progress_percent,
        "bytes_uploaded": uploaded_size,
        "total_bytes": total_size,
    }


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("2/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="File to upload"),
    process_images: bool = Form(True, description="Process images (resize, optimize)"),
    generate_thumbnails: bool = Form(True, description="Generate thumbnails"),
    thumbnail_sizes: str = Form(
        "thumbnail,medium", description="Comma-separated thumbnail sizes"
    ),
    description: str | None = Form(None, description="File description"),
    tags: str | None = Form(None, description="Comma-separated tags"),
    category: str | None = Form(None, description="File category"),
    related_entity_id: str | None = Form(None, description="Related entity ID"),
    related_entity_type: str | None = Form(None, description="Related entity type"),
    current_user: User = Depends(get_current_active_user),
    upload_service: UploadService = Depends(get_upload_service_dependency),
) -> UploadResponse:
    """
    Upload a file with validation, processing, and storage.

    Supports:
    - Multiple file types (images, documents, spreadsheets)
    - File validation (size, type, content)
    - Image processing (resize, thumbnails)
    - Virus scanning (if enabled)
    - Local or S3 storage

    Requires authentication.
    """
    try:
        # Read file content
        file_content = await file.read()

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        # Parse thumbnail sizes
        size_list = [s.strip() for s in thumbnail_sizes.split(",") if s.strip()]

        # Build metadata
        metadata_dict: dict[str, Any] = {}
        if description:
            metadata_dict["description"] = description
        if tags:
            metadata_dict["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
        if category:
            metadata_dict["category"] = category
        if related_entity_id:
            metadata_dict["related_entity_id"] = related_entity_id
        if related_entity_type:
            metadata_dict["related_entity_type"] = related_entity_type

        # Upload file
        result = upload_service.upload_file(
            file_content=file_content,
            filename=file.filename,
            user_id=str(current_user.id),
            process_images=process_images,
            generate_thumbnails=generate_thumbnails,
            thumbnail_sizes=size_list,
            metadata=metadata_dict,
        )

        normalized_result = _normalize_upload_result(
            result, fallback_filename=file.filename
        )
        return UploadResponse(**normalized_result)

    except UploadValidationError as e:
        logger.warning(f"Upload validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed. Please try again.",
        ) from e


@router.get("/progress/{upload_id}", response_model=UploadProgressResponse)
async def get_upload_progress(
    upload_id: str,
    current_user: User = Depends(get_current_active_user),
    upload_service: UploadService = Depends(get_upload_service_dependency),
) -> UploadProgressResponse:
    """
    Get upload progress for a specific upload.

    Useful for tracking multipart uploads or long-running uploads.

    Requires authentication.
    """
    progress = upload_service.get_upload_progress(upload_id)

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload not found: {upload_id}",
        )

    normalized_progress = _normalize_upload_progress(
        progress, requested_upload_id=upload_id
    )
    return UploadProgressResponse(**normalized_progress)


@router.get("/{file_id}/url", response_model=FileUrlResponse)
async def get_file_url(
    file_id: str,
    expires_in: int = 3600,
    current_user: User = Depends(get_current_active_user),
    upload_service: UploadService = Depends(get_upload_service_dependency),
) -> FileUrlResponse:
    """
    Get URL to access a file.

    For S3 storage, returns a pre-signed URL with expiration.
    For local storage, returns a path-based URL.

    Args:
        file_id: File identifier
        expires_in: URL expiration time in seconds (default: 3600 = 1 hour)

    Requires authentication.
    """
    try:
        url = upload_service.get_file_url(file_id, expires_in)

        expires_at = None
        if isinstance(upload_service.storage_backend, S3StorageBackend):
            expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

        return FileUrlResponse(file_id=file_id, url=url, expires_at=expires_at)

    except Exception as e:
        logger.error(f"Failed to get file URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}",
        ) from e


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    upload_service: UploadService = Depends(get_upload_service_dependency),
) -> StreamingResponse:
    """
    Download a file by ID.

    Returns the file content as a streaming response with appropriate headers.

    Requires authentication.
    """
    try:
        file_content = upload_service.get_file(file_id)

        # Create streaming response
        return StreamingResponse(
            iter([file_content]),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_id}",
                "Content-Length": str(len(file_content)),
            },
        )

    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}",
        ) from e


@router.delete("/{file_id}", response_model=DeleteFileResponse)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    upload_service: UploadService = Depends(get_upload_service_dependency),
) -> DeleteFileResponse:
    """
    Delete a file by ID.

    Removes the file from storage. This operation cannot be undone.

    Requires authentication.
    """
    try:
        success = upload_service.delete_file(file_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_id}",
            )

        return DeleteFileResponse(
            success=True,
            file_id=file_id,
            message="File deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file",
        ) from e


@router.get("/{file_id}/exists")
async def check_file_exists(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    upload_service: UploadService = Depends(get_upload_service_dependency),
) -> dict[str, Any]:
    """
    Check if a file exists in storage.

    Returns a simple boolean indicating file existence.

    Requires authentication.
    """
    exists = upload_service.storage_backend.exists(file_id)
    return {"exists": exists, "file_id": file_id}
