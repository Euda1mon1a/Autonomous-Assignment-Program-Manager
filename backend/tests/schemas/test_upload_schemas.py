"""Tests for upload schemas (defaults, nested models, required fields)."""

from app.schemas.upload import (
    UploadMetadata,
    UploadConfigRequest,
    ImageVersionInfo,
    ImageData,
    UploadResponse,
    UploadProgressResponse,
    FileUrlResponse,
    DeleteFileResponse,
    UploadErrorResponse,
)


class TestUploadMetadata:
    def test_defaults(self):
        r = UploadMetadata()
        assert r.description is None
        assert r.tags == []
        assert r.category is None
        assert r.related_entity_id is None
        assert r.related_entity_type is None
        assert r.custom_metadata == {}

    def test_full(self):
        r = UploadMetadata(
            description="Profile photo",
            tags=["photo", "profile"],
            category="images",
            related_entity_id="person-1",
            related_entity_type="person",
            custom_metadata={"source": "upload"},
        )
        assert r.description == "Profile photo"
        assert len(r.tags) == 2
        assert r.custom_metadata["source"] == "upload"


class TestUploadConfigRequest:
    def test_defaults(self):
        r = UploadConfigRequest()
        assert r.process_images is True
        assert r.generate_thumbnails is True
        assert r.thumbnail_sizes == ["thumbnail", "medium"]
        assert r.metadata is None

    def test_with_metadata(self):
        meta = UploadMetadata(description="Test")
        r = UploadConfigRequest(
            process_images=False,
            generate_thumbnails=False,
            thumbnail_sizes=["large"],
            metadata=meta,
        )
        assert r.process_images is False
        assert r.metadata.description == "Test"


class TestImageVersionInfo:
    def test_valid(self):
        r = ImageVersionInfo(
            file_id="file-1",
            url="/uploads/file-1",
            size_bytes=15000,
            width=150,
            height=150,
        )
        assert r.file_id == "file-1"
        assert r.size_bytes == 15000


class TestImageData:
    def test_valid(self):
        r = ImageData(width=2048, height=1536, format="JPEG")
        assert r.exif == {}

    def test_with_exif(self):
        r = ImageData(
            width=1920,
            height=1080,
            format="PNG",
            exif={"camera": "Canon"},
        )
        assert r.exif["camera"] == "Canon"


class TestUploadResponse:
    def _make_response(self, **overrides):
        defaults = {
            "upload_id": "up-1",
            "file_id": "file-1",
            "filename": "photo.jpg",
            "original_filename": "my photo.jpg",
            "url": "/uploads/file-1",
            "mime_type": "image/jpeg",
            "size_bytes": 1024000,
            "checksum": "abc123",
            "category": "image",
            "uploaded_at": "2026-03-01T10:30:00Z",
            "storage_backend": "local",
        }
        defaults.update(overrides)
        return UploadResponse(**defaults)

    def test_valid_minimal(self):
        r = self._make_response()
        assert r.versions is None
        assert r.image_data is None
        assert r.metadata == {}

    def test_with_versions(self):
        thumb = ImageVersionInfo(
            file_id="file-2",
            url="/uploads/file-2",
            size_bytes=5000,
            width=150,
            height=150,
        )
        r = self._make_response(versions={"thumbnail": thumb})
        assert r.versions["thumbnail"].width == 150

    def test_with_image_data(self):
        img = ImageData(width=2048, height=1536, format="JPEG")
        r = self._make_response(image_data=img)
        assert r.image_data.format == "JPEG"


class TestUploadProgressResponse:
    def test_valid(self):
        r = UploadProgressResponse(
            upload_id="up-1",
            total_size=1024000,
            uploaded_size=512000,
            progress_percent=50.0,
            status="in_progress",
            started_at="2026-03-01T10:30:00Z",
        )
        assert r.completed_at is None
        assert r.progress_percent == 50.0

    def test_completed(self):
        r = UploadProgressResponse(
            upload_id="up-1",
            total_size=1024000,
            uploaded_size=1024000,
            progress_percent=100.0,
            status="completed",
            started_at="2026-03-01T10:30:00Z",
            completed_at="2026-03-01T10:31:00Z",
        )
        assert r.completed_at is not None


class TestFileUrlResponse:
    def test_valid(self):
        r = FileUrlResponse(file_id="file-1", url="https://example.com/file")
        assert r.expires_at is None

    def test_with_expiration(self):
        r = FileUrlResponse(
            file_id="file-1",
            url="https://example.com/file",
            expires_at="2026-03-01T11:30:00Z",
        )
        assert r.expires_at is not None


class TestDeleteFileResponse:
    def test_valid(self):
        r = DeleteFileResponse(
            success=True, file_id="file-1", message="File deleted successfully"
        )
        assert r.success is True


class TestUploadErrorResponse:
    def test_valid_minimal(self):
        r = UploadErrorResponse(error="ValidationError", message="File too large")
        assert r.details is None

    def test_with_details(self):
        r = UploadErrorResponse(
            error="ValidationError",
            message="File too large",
            details={"max_size_mb": 50, "actual_size_mb": 60.0},
        )
        assert r.details["max_size_mb"] == 50
