"""Upload schemas for request and response validation."""

from typing import Any

from pydantic import BaseModel, Field


class UploadMetadata(BaseModel):
    """Metadata for file upload."""

    description: str | None = Field(None, description="File description")
    tags: list[str] = Field(default_factory=list, description="File tags")
    category: str | None = Field(None, description="File category")
    related_entity_id: str | None = Field(
        None, description="ID of related entity (person, procedure, etc.)"
    )
    related_entity_type: str | None = Field(None, description="Type of related entity")
    custom_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional custom metadata"
    )


class UploadConfigRequest(BaseModel):
    """Configuration for file upload."""

    process_images: bool = Field(
        True, description="Whether to process images (resize, optimize)"
    )
    generate_thumbnails: bool = Field(
        True, description="Whether to generate thumbnails for images"
    )
    thumbnail_sizes: list[str] = Field(
        default_factory=lambda: ["thumbnail", "medium"],
        description="Thumbnail sizes to generate",
    )
    metadata: UploadMetadata | None = Field(None, description="Upload metadata")


class ImageVersionInfo(BaseModel):
    """Information about a processed image version."""

    file_id: str = Field(..., description="Unique file identifier for this version")
    url: str = Field(..., description="URL to access this version")
    size_bytes: int = Field(..., description="File size in bytes")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")


class ImageData(BaseModel):
    """Image-specific data."""

    width: int = Field(..., description="Original image width")
    height: int = Field(..., description="Original image height")
    format: str = Field(..., description="Image format")
    exif: dict[str, Any] = Field(default_factory=dict, description="EXIF metadata")


class UploadResponse(BaseModel):
    """Response for successful file upload."""

    upload_id: str = Field(..., description="Unique upload identifier")
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Sanitized filename")
    original_filename: str = Field(..., description="Original filename from upload")
    url: str = Field(..., description="URL to access the file")
    mime_type: str = Field(..., description="File MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    checksum: str = Field(..., description="SHA-256 checksum")
    category: str = Field(..., description="File category (image, document, etc.)")
    uploaded_at: str = Field(..., description="Upload timestamp (ISO format)")
    storage_backend: str = Field(..., description="Storage backend used")
    versions: dict[str, ImageVersionInfo] | None = Field(
        None, description="Processed image versions (for images only)"
    )
    image_data: ImageData | None = Field(
        None, description="Image-specific data (for images only)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Upload metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_id": "660e8400-e29b-41d4-a716-446655440001",
                "filename": "profile_picture.jpg",
                "original_filename": "profile picture.jpg",
                "url": "/api/v1/uploads/660e8400-e29b-41d4-a716-446655440001",
                "mime_type": "image/jpeg",
                "size_bytes": 1024000,
                "checksum": "abc123...",
                "category": "image",
                "uploaded_at": "2025-12-20T10:30:00Z",
                "storage_backend": "local",
                "versions": {
                    "thumbnail": {
                        "file_id": "660e8400-e29b-41d4-a716-446655440002",
                        "url": "/api/v1/uploads/660e8400-e29b-41d4-a716-446655440002",
                        "size_bytes": 15000,
                        "width": 150,
                        "height": 150,
                    }
                },
                "image_data": {
                    "width": 2048,
                    "height": 1536,
                    "format": "JPEG",
                    "exif": {},
                },
                "metadata": {},
            }
        }


class UploadProgressResponse(BaseModel):
    """Response for upload progress query."""

    upload_id: str = Field(..., description="Upload identifier")
    total_size: int = Field(..., description="Total file size in bytes")
    uploaded_size: int = Field(..., description="Bytes uploaded so far")
    progress_percent: float = Field(..., description="Upload progress percentage")
    status: str = Field(
        ..., description="Upload status (in_progress, completed, failed)"
    )
    started_at: str = Field(..., description="Upload start timestamp")
    completed_at: str | None = Field(None, description="Upload completion timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_size": 1024000,
                "uploaded_size": 512000,
                "progress_percent": 50.0,
                "status": "in_progress",
                "started_at": "2025-12-20T10:30:00Z",
                "completed_at": None,
            }
        }


class FileUrlResponse(BaseModel):
    """Response for file URL request."""

    file_id: str = Field(..., description="File identifier")
    url: str = Field(..., description="URL to access the file")
    expires_at: str | None = Field(
        None, description="URL expiration timestamp (for pre-signed URLs)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "660e8400-e29b-41d4-a716-446655440001",
                "url": "https://s3.amazonaws.com/bucket/file?signature=...",
                "expires_at": "2025-12-20T11:30:00Z",
            }
        }


class DeleteFileResponse(BaseModel):
    """Response for file deletion."""

    success: bool = Field(..., description="Whether deletion was successful")
    file_id: str = Field(..., description="File identifier")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "file_id": "660e8400-e29b-41d4-a716-446655440001",
                "message": "File deleted successfully",
            }
        }


class UploadErrorResponse(BaseModel):
    """Error response for upload failures."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "File too large: 60.00MB (max: 50MB)",
                "details": {"max_size_mb": 50, "actual_size_mb": 60.0},
            }
        }
