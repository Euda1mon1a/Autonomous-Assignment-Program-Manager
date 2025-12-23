"""Tests for upload API routes.

Tests the file upload functionality including:
- File upload with validation
- Upload progress tracking
- File URL generation
- File download
- File deletion
"""

from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestUploadRoutes:
    """Test suite for upload API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_upload_requires_auth(self, client: TestClient):
        """Test that upload endpoint requires authentication."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"test content", "text/plain")},
        )
        assert response.status_code == 401

    def test_get_progress_requires_auth(self, client: TestClient):
        """Test that progress endpoint requires authentication."""
        response = client.get(f"/api/upload/progress/{uuid4()}")
        assert response.status_code == 401

    def test_get_file_url_requires_auth(self, client: TestClient):
        """Test that file URL endpoint requires authentication."""
        response = client.get(f"/api/upload/{uuid4()}/url")
        assert response.status_code == 401

    def test_download_requires_auth(self, client: TestClient):
        """Test that download endpoint requires authentication."""
        response = client.get(f"/api/upload/{uuid4()}/download")
        assert response.status_code == 401

    def test_delete_requires_auth(self, client: TestClient):
        """Test that delete endpoint requires authentication."""
        response = client.delete(f"/api/upload/{uuid4()}")
        assert response.status_code == 401

    def test_check_exists_requires_auth(self, client: TestClient):
        """Test that exists check requires authentication."""
        response = client.get(f"/api/upload/{uuid4()}/exists")
        assert response.status_code == 401

    # ========================================================================
    # Upload Tests
    # ========================================================================

    @patch("app.api.routes.upload.get_upload_service")
    def test_upload_file_success(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test successful file upload."""
        mock_service = MagicMock()
        mock_service.upload_file.return_value = {
            "file_id": str(uuid4()),
            "filename": "test.txt",
            "size": 12,
            "content_type": "text/plain",
            "uploaded_by": str(admin_user.id),
            "uploaded_at": "2025-01-15T10:00:00",
        }
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/upload",
            headers=auth_headers,
            files={"file": ("test.txt", b"test content", "text/plain")},
            data={
                "process_images": "true",
                "generate_thumbnails": "true",
                "thumbnail_sizes": "thumbnail,medium",
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test.txt"

    @patch("app.api.routes.upload.get_upload_service")
    def test_upload_file_with_metadata(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test file upload with metadata."""
        mock_service = MagicMock()
        mock_service.upload_file.return_value = {
            "file_id": str(uuid4()),
            "filename": "document.pdf",
            "size": 1024,
            "content_type": "application/pdf",
            "uploaded_by": str(admin_user.id),
            "uploaded_at": "2025-01-15T10:00:00",
        }
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/upload",
            headers=auth_headers,
            files={"file": ("document.pdf", b"pdf content", "application/pdf")},
            data={
                "description": "Test document",
                "tags": "test,document",
                "category": "documents",
                "related_entity_id": str(uuid4()),
                "related_entity_type": "person",
            },
        )
        assert response.status_code == 201

    @patch("app.api.routes.upload.get_upload_service")
    def test_upload_validation_error(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test upload validation failure."""
        from app.services.upload.validators import UploadValidationError

        mock_service = MagicMock()
        mock_service.upload_file.side_effect = UploadValidationError("File too large")
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/upload",
            headers=auth_headers,
            files={"file": ("large.bin", b"x" * 1000, "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    # ========================================================================
    # Progress Tests
    # ========================================================================

    @patch("app.api.routes.upload.get_upload_service")
    def test_get_upload_progress_success(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting upload progress."""
        upload_id = str(uuid4())

        mock_service = MagicMock()
        mock_service.get_upload_progress.return_value = {
            "upload_id": upload_id,
            "status": "processing",
            "progress": 75,
            "bytes_uploaded": 750000,
            "total_bytes": 1000000,
        }
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/upload/progress/{upload_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["progress"] == 75

    @patch("app.api.routes.upload.get_upload_service")
    def test_get_upload_progress_not_found(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test progress for non-existent upload."""
        mock_service = MagicMock()
        mock_service.get_upload_progress.return_value = None
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/upload/progress/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ========================================================================
    # File URL Tests
    # ========================================================================

    @patch("app.api.routes.upload.get_upload_service")
    def test_get_file_url_success(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting file URL."""
        file_id = str(uuid4())

        mock_service = MagicMock()
        mock_service.get_file_url.return_value = f"http://storage.local/{file_id}"
        mock_service.storage_backend = MagicMock()
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/upload/{file_id}/url",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "url" in data
        assert data["file_id"] == file_id

    @patch("app.api.routes.upload.get_upload_service")
    def test_get_file_url_not_found(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test URL for non-existent file."""
        mock_service = MagicMock()
        mock_service.get_file_url.side_effect = Exception("File not found")
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/upload/{uuid4()}/url",
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ========================================================================
    # Download Tests
    # ========================================================================

    @patch("app.api.routes.upload.get_upload_service")
    def test_download_file_success(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test file download."""
        file_id = str(uuid4())
        file_content = b"test file content"

        mock_service = MagicMock()
        mock_service.get_file.return_value = file_content
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/upload/{file_id}/download",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.content == file_content

    @patch("app.api.routes.upload.get_upload_service")
    def test_download_file_not_found(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test download of non-existent file."""
        mock_service = MagicMock()
        mock_service.get_file.side_effect = Exception("File not found")
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/upload/{uuid4()}/download",
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ========================================================================
    # Delete Tests
    # ========================================================================

    @patch("app.api.routes.upload.get_upload_service")
    def test_delete_file_success(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test file deletion."""
        file_id = str(uuid4())

        mock_service = MagicMock()
        mock_service.delete_file.return_value = True
        mock_get_service.return_value = mock_service

        response = client.delete(
            f"/api/upload/{file_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["file_id"] == file_id

    @patch("app.api.routes.upload.get_upload_service")
    def test_delete_file_not_found(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test deletion of non-existent file."""
        mock_service = MagicMock()
        mock_service.delete_file.return_value = False
        mock_get_service.return_value = mock_service

        response = client.delete(
            f"/api/upload/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ========================================================================
    # Exists Check Tests
    # ========================================================================

    @patch("app.api.routes.upload.get_upload_service")
    def test_check_file_exists_true(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test check file exists returns true."""
        file_id = str(uuid4())

        mock_service = MagicMock()
        mock_service.storage_backend.exists.return_value = True
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/upload/{file_id}/exists",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["exists"] is True
        assert data["file_id"] == file_id

    @patch("app.api.routes.upload.get_upload_service")
    def test_check_file_exists_false(
        self,
        mock_get_service: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test check file exists returns false."""
        file_id = str(uuid4())

        mock_service = MagicMock()
        mock_service.storage_backend.exists.return_value = False
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/upload/{file_id}/exists",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["exists"] is False
