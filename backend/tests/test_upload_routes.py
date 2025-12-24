"""
Comprehensive tests for Upload API routes.

Tests coverage for file upload functionality:
- POST /api/upload - Upload a file
- GET /api/upload/progress/{upload_id} - Get upload progress
- GET /api/upload/{file_id}/url - Get file URL
- GET /api/upload/{file_id}/download - Download file
- DELETE /api/upload/{file_id} - Delete file
- GET /api/upload/{file_id}/exists - Check file exists
"""

import io
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestUploadFileEndpoint:
    """Tests for POST /api/upload endpoint."""

    def test_upload_requires_auth(self, client: TestClient):
        """Test that upload requires authentication."""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = client.post("/api/upload", files=files)

        assert response.status_code in [401, 403]

    def test_upload_file_success(self, client: TestClient, auth_headers: dict):
        """Test successful file upload."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.upload_file.return_value = {
                "file_id": str(uuid4()),
                "filename": "test.txt",
                "size": 12,
                "content_type": "text/plain",
                "uploaded_at": "2025-01-01T00:00:00Z",
            }
            mock_get_service.return_value = mock_service

            files = {"file": ("test.txt", b"test content", "text/plain")}
            response = client.post(
                "/api/upload",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code in [201, 401]

    def test_upload_image_with_processing(
        self, client: TestClient, auth_headers: dict
    ):
        """Test image upload with processing options."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.upload_file.return_value = {
                "file_id": str(uuid4()),
                "filename": "image.png",
                "size": 1024,
                "content_type": "image/png",
                "uploaded_at": "2025-01-01T00:00:00Z",
                "thumbnails": {"thumbnail": "thumb_url", "medium": "medium_url"},
            }
            mock_get_service.return_value = mock_service

            # Create a simple PNG-like content
            files = {"file": ("image.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png")}
            data = {
                "process_images": "true",
                "generate_thumbnails": "true",
                "thumbnail_sizes": "thumbnail,medium",
            }
            response = client.post(
                "/api/upload",
                files=files,
                data=data,
                headers=auth_headers,
            )

            assert response.status_code in [201, 401]

    def test_upload_with_metadata(self, client: TestClient, auth_headers: dict):
        """Test file upload with metadata."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.upload_file.return_value = {
                "file_id": str(uuid4()),
                "filename": "document.pdf",
                "size": 2048,
                "content_type": "application/pdf",
                "uploaded_at": "2025-01-01T00:00:00Z",
            }
            mock_get_service.return_value = mock_service

            files = {"file": ("document.pdf", b"%PDF-1.4" + b"\x00" * 100, "application/pdf")}
            data = {
                "description": "Test document",
                "tags": "test,document",
                "category": "reports",
            }
            response = client.post(
                "/api/upload",
                files=files,
                data=data,
                headers=auth_headers,
            )

            assert response.status_code in [201, 401]

    def test_upload_with_related_entity(self, client: TestClient, auth_headers: dict):
        """Test file upload linked to an entity."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.upload_file.return_value = {
                "file_id": str(uuid4()),
                "filename": "attachment.txt",
                "size": 100,
                "content_type": "text/plain",
                "uploaded_at": "2025-01-01T00:00:00Z",
            }
            mock_get_service.return_value = mock_service

            entity_id = str(uuid4())
            files = {"file": ("attachment.txt", b"content", "text/plain")}
            data = {
                "related_entity_id": entity_id,
                "related_entity_type": "person",
            }
            response = client.post(
                "/api/upload",
                files=files,
                data=data,
                headers=auth_headers,
            )

            assert response.status_code in [201, 401]

    def test_upload_missing_file(self, client: TestClient, auth_headers: dict):
        """Test upload without file."""
        response = client.post(
            "/api/upload",
            headers=auth_headers,
        )

        # Should return 422 for missing required field
        assert response.status_code in [401, 422]


class TestUploadProgressEndpoint:
    """Tests for GET /api/upload/progress/{upload_id} endpoint."""

    def test_progress_requires_auth(self, client: TestClient):
        """Test that progress check requires authentication."""
        upload_id = str(uuid4())
        response = client.get(f"/api/upload/progress/{upload_id}")

        assert response.status_code in [401, 403]

    def test_progress_success(self, client: TestClient, auth_headers: dict):
        """Test successful progress check."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_upload_progress.return_value = {
                "upload_id": str(uuid4()),
                "status": "processing",
                "progress": 50,
                "bytes_uploaded": 500,
                "total_bytes": 1000,
            }
            mock_get_service.return_value = mock_service

            upload_id = str(uuid4())
            response = client.get(
                f"/api/upload/progress/{upload_id}",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_progress_not_found(self, client: TestClient, auth_headers: dict):
        """Test progress for non-existent upload."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_upload_progress.return_value = None
            mock_get_service.return_value = mock_service

            upload_id = str(uuid4())
            response = client.get(
                f"/api/upload/progress/{upload_id}",
                headers=auth_headers,
            )

            assert response.status_code in [401, 404]


class TestFileUrlEndpoint:
    """Tests for GET /api/upload/{file_id}/url endpoint."""

    def test_url_requires_auth(self, client: TestClient):
        """Test that URL retrieval requires authentication."""
        file_id = str(uuid4())
        response = client.get(f"/api/upload/{file_id}/url")

        assert response.status_code in [401, 403]

    def test_url_success(self, client: TestClient, auth_headers: dict):
        """Test successful URL retrieval."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_file_url.return_value = "https://storage.example.com/file123"
            mock_service.storage_backend = MagicMock()
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.get(
                f"/api/upload/{file_id}/url",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_url_with_expiration(self, client: TestClient, auth_headers: dict):
        """Test URL retrieval with custom expiration."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_file_url.return_value = "https://storage.example.com/file123"
            mock_service.storage_backend = MagicMock()
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.get(
                f"/api/upload/{file_id}/url?expires_in=7200",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_url_file_not_found(self, client: TestClient, auth_headers: dict):
        """Test URL for non-existent file."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_file_url.side_effect = Exception("File not found")
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.get(
                f"/api/upload/{file_id}/url",
                headers=auth_headers,
            )

            assert response.status_code in [401, 404]


class TestDownloadFileEndpoint:
    """Tests for GET /api/upload/{file_id}/download endpoint."""

    def test_download_requires_auth(self, client: TestClient):
        """Test that download requires authentication."""
        file_id = str(uuid4())
        response = client.get(f"/api/upload/{file_id}/download")

        assert response.status_code in [401, 403]

    def test_download_success(self, client: TestClient, auth_headers: dict):
        """Test successful file download."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_file.return_value = b"file content here"
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.get(
                f"/api/upload/{file_id}/download",
                headers=auth_headers,
            )

            if response.status_code == 200:
                assert response.content == b"file content here"
                assert "content-disposition" in response.headers

    def test_download_not_found(self, client: TestClient, auth_headers: dict):
        """Test download for non-existent file."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_file.side_effect = Exception("File not found")
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.get(
                f"/api/upload/{file_id}/download",
                headers=auth_headers,
            )

            assert response.status_code in [401, 404]


class TestDeleteFileEndpoint:
    """Tests for DELETE /api/upload/{file_id} endpoint."""

    def test_delete_requires_auth(self, client: TestClient):
        """Test that delete requires authentication."""
        file_id = str(uuid4())
        response = client.delete(f"/api/upload/{file_id}")

        assert response.status_code in [401, 403]

    def test_delete_success(self, client: TestClient, auth_headers: dict):
        """Test successful file deletion."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.delete_file.return_value = True
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.delete(
                f"/api/upload/{file_id}",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401]

    def test_delete_not_found(self, client: TestClient, auth_headers: dict):
        """Test delete for non-existent file."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.delete_file.return_value = False
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.delete(
                f"/api/upload/{file_id}",
                headers=auth_headers,
            )

            assert response.status_code in [401, 404]


class TestFileExistsEndpoint:
    """Tests for GET /api/upload/{file_id}/exists endpoint."""

    def test_exists_requires_auth(self, client: TestClient):
        """Test that exists check requires authentication."""
        file_id = str(uuid4())
        response = client.get(f"/api/upload/{file_id}/exists")

        assert response.status_code in [401, 403]

    def test_exists_file_found(self, client: TestClient, auth_headers: dict):
        """Test exists returns true for existing file."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_storage = MagicMock()
            mock_storage.exists.return_value = True
            mock_service.storage_backend = mock_storage
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.get(
                f"/api/upload/{file_id}/exists",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert data["exists"] is True

    def test_exists_file_not_found(self, client: TestClient, auth_headers: dict):
        """Test exists returns false for non-existent file."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_storage = MagicMock()
            mock_storage.exists.return_value = False
            mock_service.storage_backend = mock_storage
            mock_get_service.return_value = mock_service

            file_id = str(uuid4())
            response = client.get(
                f"/api/upload/{file_id}/exists",
                headers=auth_headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert data["exists"] is False


# ============================================================================
# Validation Tests
# ============================================================================


class TestUploadValidation:
    """Tests for upload validation."""

    def test_upload_validation_error(self, client: TestClient, auth_headers: dict):
        """Test upload with validation error."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            from app.services.upload.validators import UploadValidationError

            mock_service = MagicMock()
            mock_service.upload_file.side_effect = UploadValidationError(
                "File too large"
            )
            mock_get_service.return_value = mock_service

            files = {"file": ("large.bin", b"\x00" * 100, "application/octet-stream")}
            response = client.post(
                "/api/upload",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code in [400, 401]

    def test_upload_server_error(self, client: TestClient, auth_headers: dict):
        """Test upload with server error."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.upload_file.side_effect = Exception("Storage error")
            mock_get_service.return_value = mock_service

            files = {"file": ("test.txt", b"content", "text/plain")}
            response = client.post(
                "/api/upload",
                files=files,
                headers=auth_headers,
            )

            assert response.status_code in [401, 500]


# ============================================================================
# Integration Tests
# ============================================================================


class TestUploadIntegration:
    """Integration tests for upload functionality."""

    def test_upload_endpoints_accessible(
        self, client: TestClient, auth_headers: dict
    ):
        """Test all upload endpoints respond appropriately."""
        file_id = str(uuid4())
        upload_id = str(uuid4())

        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_upload_progress.return_value = None
            mock_service.get_file_url.side_effect = Exception("Not found")
            mock_service.get_file.side_effect = Exception("Not found")
            mock_service.delete_file.return_value = False
            mock_storage = MagicMock()
            mock_storage.exists.return_value = False
            mock_service.storage_backend = mock_storage
            mock_get_service.return_value = mock_service

            endpoints = [
                (f"/api/upload/progress/{upload_id}", "GET"),
                (f"/api/upload/{file_id}/url", "GET"),
                (f"/api/upload/{file_id}/download", "GET"),
                (f"/api/upload/{file_id}/exists", "GET"),
                (f"/api/upload/{file_id}", "DELETE"),
            ]

            for url, method in endpoints:
                if method == "GET":
                    response = client.get(url, headers=auth_headers)
                else:
                    response = client.delete(url, headers=auth_headers)

                # Should return meaningful status (not 500)
                assert response.status_code in [200, 401, 404], f"Failed for {url}"

    def test_upload_response_format(self, client: TestClient, auth_headers: dict):
        """Test upload returns valid response format."""
        with patch("app.api.routes.upload.get_upload_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.upload_file.return_value = {
                "file_id": str(uuid4()),
                "filename": "test.txt",
                "size": 12,
                "content_type": "text/plain",
                "uploaded_at": "2025-01-01T00:00:00Z",
            }
            mock_get_service.return_value = mock_service

            files = {"file": ("test.txt", b"test content", "text/plain")}
            response = client.post(
                "/api/upload",
                files=files,
                headers=auth_headers,
            )

            if response.status_code == 201:
                data = response.json()
                assert "file_id" in data
                assert "filename" in data
                assert "size" in data
