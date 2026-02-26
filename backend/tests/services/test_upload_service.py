"""Tests for upload service and storage backends.

Tests the UploadService orchestration layer, UploadProgress tracking,
LocalStorageBackend file I/O, and FileProcessorFactory routing.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.upload.processors import (
    DocumentProcessor,
    FileProcessorFactory,
    ImageProcessor,
    ProcessorError,
)
from app.services.upload.service import UploadProgress, UploadService
from app.services.upload.storage import LocalStorageBackend, StorageError
from app.services.upload.validators import UploadValidationError


class TestUploadProgress:
    """Test UploadProgress tracking."""

    def test_initial_state(self):
        p = UploadProgress("upload-1", total_size=1000)
        assert p.upload_id == "upload-1"
        assert p.total_size == 1000
        assert p.uploaded_size == 0
        assert p.status == "in_progress"
        assert p.completed_at is None

    def test_progress_percent_zero_total(self):
        p = UploadProgress("upload-1", total_size=0)
        assert p.progress_percent == 0.0

    def test_progress_percent_partial(self):
        p = UploadProgress("upload-1", total_size=1000)
        p.update(500)
        assert p.progress_percent == 50.0

    def test_progress_percent_full(self):
        p = UploadProgress("upload-1", total_size=1000)
        p.update(1000)
        assert p.progress_percent == 100.0

    def test_update_accumulates(self):
        p = UploadProgress("upload-1", total_size=1000)
        p.update(250)
        p.update(250)
        assert p.uploaded_size == 500

    def test_complete_sets_status(self):
        p = UploadProgress("upload-1", total_size=1000)
        p.complete()
        assert p.status == "completed"
        assert p.completed_at is not None

    def test_fail_sets_status(self):
        p = UploadProgress("upload-1", total_size=1000)
        p.fail()
        assert p.status == "failed"
        assert p.completed_at is not None

    def test_to_dict(self):
        p = UploadProgress("upload-1", total_size=1000)
        p.update(500)
        d = p.to_dict()
        assert d["upload_id"] == "upload-1"
        assert d["total_size"] == 1000
        assert d["uploaded_size"] == 500
        assert d["progress_percent"] == 50.0
        assert d["status"] == "in_progress"
        assert d["started_at"] is not None
        assert d["completed_at"] is None

    def test_to_dict_completed(self):
        p = UploadProgress("upload-1", total_size=1000)
        p.complete()
        d = p.to_dict()
        assert d["status"] == "completed"
        assert d["completed_at"] is not None


class TestLocalStorageBackend:
    """Test local filesystem storage backend."""

    def test_save_and_get(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        result = storage.save(b"test content", "test.txt", "text/plain")
        assert result["file_id"] is not None
        assert result["backend"] == "local"
        assert result["size_bytes"] == 12

        # Retrieve the file
        content = storage.get(result["file_id"])
        assert content == b"test content"

    def test_save_creates_date_directory(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        storage.save(b"data", "file.txt", "text/plain")
        # Should create YYYY/MM/DD directory structure
        subdirs = list(tmp_path.rglob("*"))
        assert any(p.is_dir() for p in subdirs)

    def test_exists_true(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        result = storage.save(b"data", "file.txt", "text/plain")
        assert storage.exists(result["file_id"]) is True

    def test_exists_false(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        assert storage.exists("nonexistent-id") is False

    def test_delete_removes_file(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        result = storage.save(b"data", "file.txt", "text/plain")
        file_id = result["file_id"]
        assert storage.exists(file_id) is True
        assert storage.delete(file_id) is True
        assert storage.exists(file_id) is False

    def test_delete_nonexistent_returns_false(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        assert storage.delete("nonexistent-id") is False

    def test_get_nonexistent_raises(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        with pytest.raises(StorageError, match="File not found"):
            storage.get("nonexistent-id")

    def test_get_url(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        result = storage.save(b"data", "file.txt", "text/plain")
        url = storage.get_url(result["file_id"])
        assert url.startswith("/api/v1/uploads/")
        assert result["file_id"] in url

    def test_get_url_nonexistent_raises(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        with pytest.raises(StorageError, match="File not found"):
            storage.get_url("nonexistent-id")

    def test_save_with_metadata(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        metadata = {"uploaded_by": "user-1", "category": "document"}
        result = storage.save(b"data", "file.txt", "text/plain", metadata=metadata)
        assert result["metadata"] == metadata

    def test_default_base_path_uses_tempdir(self):
        storage = LocalStorageBackend()
        expected = Path(tempfile.gettempdir()) / "uploads"
        assert storage.base_path == expected


class TestFileProcessorFactory:
    """Test processor factory routing."""

    def test_image_type_returns_image_processor(self):
        result = FileProcessorFactory.get_processor("image/jpeg")
        assert isinstance(result, ImageProcessor)

    def test_image_png_returns_image_processor(self):
        result = FileProcessorFactory.get_processor("image/png")
        assert isinstance(result, ImageProcessor)

    def test_pdf_returns_document_processor(self):
        result = FileProcessorFactory.get_processor("application/pdf")
        assert isinstance(result, DocumentProcessor)

    def test_unknown_type_returns_none(self):
        result = FileProcessorFactory.get_processor("text/plain")
        assert result is None

    def test_video_type_returns_none(self):
        result = FileProcessorFactory.get_processor("video/mp4")
        assert result is None


class TestUploadService:
    """Test UploadService orchestration."""

    def test_upload_simple_file(self, tmp_path):
        """Test uploading a valid JPEG file."""
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        # Valid JPEG content
        content = b"\xff\xd8\xff" + b"\x00" * 100

        result = service.upload_file(
            content,
            "photo.jpg",
            user_id="user-1",
            process_images=False,
        )

        assert result["upload_id"] is not None
        assert result["file_id"] is not None
        assert result["filename"] == "photo.jpg"
        assert result["original_filename"] == "photo.jpg"
        assert result["mime_type"] == "image/jpeg"
        assert result["size_bytes"] == 103
        assert result["category"] == "image"

    def test_upload_pdf(self, tmp_path):
        """Test uploading a valid PDF file."""
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        content = b"%PDF" + b"\x00" * 100

        result = service.upload_file(
            content,
            "document.pdf",
            process_images=False,
        )

        assert result["mime_type"] == "application/pdf"
        assert result["category"] == "document"

    def test_upload_invalid_type_raises(self, tmp_path):
        """Test that uploading a disallowed type raises."""
        from app.services.upload.validators import FileValidator

        storage = LocalStorageBackend(base_path=tmp_path)
        validator = FileValidator(allowed_mime_types={"image/png"})
        service = UploadService(storage_backend=storage, validator=validator)

        content = b"\xff\xd8\xff" + b"\x00" * 100  # JPEG

        with pytest.raises(UploadValidationError):
            service.upload_file(content, "photo.jpg")

    def test_upload_tracks_progress(self, tmp_path):
        """Test that upload progress is tracked."""
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        content = b"\xff\xd8\xff" + b"\x00" * 100

        result = service.upload_file(content, "photo.jpg", process_images=False)

        # Check progress was tracked
        progress = service.get_upload_progress(result["upload_id"])
        assert progress is not None
        assert progress["status"] == "completed"

    def test_get_progress_nonexistent(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)
        assert service.get_upload_progress("nonexistent") is None

    def test_delete_file(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        content = b"\xff\xd8\xff" + b"\x00" * 100
        result = service.upload_file(content, "photo.jpg", process_images=False)

        assert service.delete_file(result["file_id"]) is True

    def test_get_file(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        content = b"\xff\xd8\xff" + b"\x00" * 100
        result = service.upload_file(content, "photo.jpg", process_images=False)

        retrieved = service.get_file(result["file_id"])
        assert retrieved == content

    def test_get_file_url(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        content = b"\xff\xd8\xff" + b"\x00" * 100
        result = service.upload_file(content, "photo.jpg", process_images=False)

        url = service.get_file_url(result["file_id"])
        assert result["file_id"] in url

    def test_upload_empty_file_raises(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        with pytest.raises(UploadValidationError, match="empty"):
            service.upload_file(b"", "empty.jpg")

    def test_upload_file_like_object(self, tmp_path):
        """Test uploading from a file-like object (BinaryIO)."""
        import io

        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        content = b"\xff\xd8\xff" + b"\x00" * 100
        file_obj = io.BytesIO(content)

        result = service.upload_file(
            file_obj,
            "photo.jpg",
            process_images=False,
        )

        assert result["mime_type"] == "image/jpeg"
        assert result["size_bytes"] == 103

    def test_upload_with_metadata(self, tmp_path):
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        content = b"\xff\xd8\xff" + b"\x00" * 100
        custom_meta = {"department": "radiology", "study_id": "12345"}

        result = service.upload_file(
            content,
            "photo.jpg",
            process_images=False,
            metadata=custom_meta,
        )

        assert result["metadata"]["department"] == "radiology"
        assert result["metadata"]["study_id"] == "12345"

    def test_failed_upload_marks_progress_failed(self, tmp_path):
        """Verify that failed uploads mark progress as 'failed'."""
        storage = LocalStorageBackend(base_path=tmp_path)
        service = UploadService(storage_backend=storage)

        # File too large
        service.validator = service.validator.__class__(max_size_mb=0)

        with pytest.raises(UploadValidationError):
            service.upload_file(b"\xff\xd8\xff", "photo.jpg")
