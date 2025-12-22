"""Upload service for managing file uploads.

Coordinates file validation, processing, and storage.
"""

import logging
from datetime import datetime
from typing import Any, BinaryIO
from uuid import UUID, uuid4

from app.services.upload.processors import FileProcessorFactory, ImageProcessor
from app.services.upload.storage import LocalStorageBackend, S3StorageBackend, StorageBackend
from app.services.upload.validators import FileValidator, UploadValidationError

logger = logging.getLogger(__name__)


class UploadProgress:
    """Track upload progress for multipart uploads."""

    def __init__(self, upload_id: str, total_size: int):
        """
        Initialize upload progress tracker.

        Args:
            upload_id: Unique upload identifier
            total_size: Total size in bytes
        """
        self.upload_id = upload_id
        self.total_size = total_size
        self.uploaded_size = 0
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.status = "in_progress"  # in_progress, completed, failed

    @property
    def progress_percent(self) -> float:
        """Calculate upload progress percentage."""
        if self.total_size == 0:
            return 0.0
        return (self.uploaded_size / self.total_size) * 100

    def update(self, bytes_uploaded: int) -> None:
        """Update progress with newly uploaded bytes."""
        self.uploaded_size += bytes_uploaded

    def complete(self) -> None:
        """Mark upload as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()

    def fail(self) -> None:
        """Mark upload as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "upload_id": self.upload_id,
            "total_size": self.total_size,
            "uploaded_size": self.uploaded_size,
            "progress_percent": self.progress_percent,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class UploadService:
    """
    Main upload service coordinating validation, processing, and storage.

    Features:
    - File validation (type, size, content)
    - Virus scanning integration
    - Image processing (resize, thumbnails)
    - Multiple storage backends (local, S3)
    - Upload progress tracking
    - Metadata management
    """

    def __init__(
        self,
        storage_backend: StorageBackend | None = None,
        validator: FileValidator | None = None,
    ):
        """
        Initialize upload service.

        Args:
            storage_backend: Storage backend to use (defaults to local storage)
            validator: File validator instance
        """
        self.storage_backend = storage_backend or LocalStorageBackend()
        self.validator = validator or FileValidator()
        self.upload_progress: dict[str, UploadProgress] = {}

    def upload_file(
        self,
        file_content: bytes | BinaryIO,
        filename: str,
        user_id: str | UUID | None = None,
        process_images: bool = True,
        generate_thumbnails: bool = True,
        thumbnail_sizes: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Upload file with validation, processing, and storage.

        Args:
            file_content: File content as bytes or file-like object
            filename: Original filename
            user_id: ID of user uploading the file
            process_images: Whether to process images (resize, optimize)
            generate_thumbnails: Whether to generate thumbnails
            thumbnail_sizes: List of thumbnail sizes to generate
            metadata: Additional metadata to store with file

        Returns:
            dict: Upload result with file_id, url, metadata, etc.

        Raises:
            UploadValidationError: If validation fails
        """
        upload_id = str(uuid4())

        try:
            # Convert file-like object to bytes if needed
            if not isinstance(file_content, bytes):
                if hasattr(file_content, "read"):
                    file_content = file_content.read()
                else:
                    raise UploadValidationError("Invalid file content type")

            # Initialize progress tracking
            progress = UploadProgress(upload_id, len(file_content))
            self.upload_progress[upload_id] = progress

            # Validate file
            logger.info(f"Validating file: {filename} ({len(file_content)} bytes)")
            validation_result = self.validator.validate_file(file_content, filename)

            if not validation_result["valid"]:
                progress.fail()
                raise UploadValidationError(
                    f"Validation failed: {', '.join(validation_result['errors'])}"
                )

            progress.update(len(file_content) // 4)  # 25% - validation complete

            # Prepare upload metadata
            upload_metadata = {
                "original_filename": filename,
                "sanitized_filename": validation_result["sanitized_filename"],
                "mime_type": validation_result["mime_type"],
                "size_bytes": validation_result["size_bytes"],
                "checksum": validation_result["checksum"],
                "uploaded_by": str(user_id) if user_id else None,
                "uploaded_at": datetime.utcnow().isoformat(),
                "category": FileValidator.get_file_category(
                    validation_result["mime_type"]
                ),
            }

            # Merge user metadata
            if metadata:
                upload_metadata.update(metadata)

            # Process images if enabled
            processed_versions = None
            if process_images and validation_result["mime_type"].startswith("image/"):
                logger.info(f"Processing image: {filename}")
                processed_versions = self._process_image(
                    file_content,
                    validation_result["mime_type"],
                    generate_thumbnails,
                    thumbnail_sizes,
                )
                progress.update(len(file_content) // 4)  # 50% - processing complete

            # Store original file
            logger.info(f"Storing file: {filename}")
            storage_result = self.storage_backend.save(
                file_content,
                validation_result["sanitized_filename"],
                validation_result["mime_type"],
                upload_metadata,
            )

            progress.update(len(file_content) // 4)  # 75% - storage complete

            # Store processed versions (if any)
            version_results = {}
            if processed_versions:
                for version_name, version_data in processed_versions["versions"].items():
                    if version_name != "original":  # Original is already stored
                        version_filename = (
                            f"{Path(validation_result['sanitized_filename']).stem}"
                            f"_{version_name}{Path(validation_result['sanitized_filename']).suffix}"
                        )
                        version_result = self.storage_backend.save(
                            version_data["bytes"],
                            version_filename,
                            validation_result["mime_type"],
                            {**upload_metadata, "version": version_name},
                        )
                        version_results[version_name] = {
                            "file_id": version_result["file_id"],
                            "url": self.storage_backend.get_url(
                                version_result["file_id"]
                            ),
                            "size_bytes": version_data["size"],
                            "width": version_data["width"],
                            "height": version_data["height"],
                        }

            progress.update(len(file_content) // 4)  # 100% - complete
            progress.complete()

            # Build response
            result = {
                "upload_id": upload_id,
                "file_id": storage_result["file_id"],
                "filename": validation_result["sanitized_filename"],
                "original_filename": filename,
                "url": self.storage_backend.get_url(storage_result["file_id"]),
                "mime_type": validation_result["mime_type"],
                "size_bytes": validation_result["size_bytes"],
                "checksum": validation_result["checksum"],
                "category": upload_metadata["category"],
                "uploaded_at": storage_result["created_at"],
                "metadata": upload_metadata,
                "storage_backend": storage_result["backend"],
            }

            # Add processed versions
            if version_results:
                result["versions"] = version_results

            # Add image-specific data
            if processed_versions:
                result["image_data"] = {
                    "width": processed_versions["original"]["width"],
                    "height": processed_versions["original"]["height"],
                    "format": processed_versions["original"]["format"],
                    "exif": processed_versions.get("exif", {}),
                }

            logger.info(f"Upload completed: {result['file_id']}")
            return result

        except Exception as e:
            if upload_id in self.upload_progress:
                self.upload_progress[upload_id].fail()
            logger.error(f"Upload failed: {e}")
            raise

    def get_upload_progress(self, upload_id: str) -> dict[str, Any] | None:
        """
        Get upload progress for a specific upload.

        Args:
            upload_id: Upload identifier

        Returns:
            dict: Progress information or None if not found
        """
        progress = self.upload_progress.get(upload_id)
        return progress.to_dict() if progress else None

    def delete_file(self, file_id: str) -> bool:
        """
        Delete uploaded file from storage.

        Args:
            file_id: File identifier

        Returns:
            bool: True if deleted successfully
        """
        logger.info(f"Deleting file: {file_id}")
        return self.storage_backend.delete(file_id)

    def get_file(self, file_id: str) -> bytes:
        """
        Retrieve file content from storage.

        Args:
            file_id: File identifier

        Returns:
            bytes: File content
        """
        return self.storage_backend.get(file_id)

    def get_file_url(self, file_id: str, expires_in: int = 3600) -> str:
        """
        Get URL to access file.

        Args:
            file_id: File identifier
            expires_in: URL expiration time in seconds

        Returns:
            str: File URL
        """
        return self.storage_backend.get_url(file_id, expires_in)

    def _process_image(
        self,
        file_content: bytes,
        mime_type: str,
        generate_thumbnails: bool,
        thumbnail_sizes: list[str] | None,
    ) -> dict[str, Any] | None:
        """
        Process image with resizing and optimization.

        Args:
            file_content: Image bytes
            mime_type: Image MIME type
            generate_thumbnails: Whether to generate thumbnails
            thumbnail_sizes: List of sizes to generate

        Returns:
            dict: Processing result or None
        """
        processor = FileProcessorFactory.get_processor(mime_type)
        if not processor or not isinstance(processor, ImageProcessor):
            return None

        sizes_to_generate = thumbnail_sizes or ["thumbnail", "medium"]
        if generate_thumbnails:
            return processor.process_image(file_content, sizes=sizes_to_generate)
        else:
            return processor.process_image(file_content, sizes=None)


# Import Path for filename operations
from pathlib import Path
