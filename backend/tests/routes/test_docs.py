"""Tests for documentation API routes.

Tests the documentation generation and export functionality including:
- Enhanced OpenAPI schema
- Markdown documentation
- Code examples
- Error documentation
- Changelog and version info
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestDocsRoutes:
    """Test suite for documentation API endpoints."""

    # ========================================================================
    # Documentation Index Tests
    # ========================================================================

    def test_docs_index(self, client: TestClient):
        """Test documentation index endpoint."""
        response = client.get("/api/docs/")
        assert response.status_code == 200

        data = response.json()
        assert "title" in data
        assert "endpoints" in data
        assert "/openapi-enhanced.json" in data["endpoints"]
        assert "/markdown" in data["endpoints"]
        assert "/endpoint" in data["endpoints"]
        assert "/examples" in data["endpoints"]
        assert "/errors" in data["endpoints"]
        assert "/changelog" in data["endpoints"]
        assert "/version" in data["endpoints"]
        assert "/stats" in data["endpoints"]

    # ========================================================================
    # Enhanced OpenAPI Tests
    # ========================================================================

    def test_get_enhanced_openapi(self, client: TestClient):
        """Test enhanced OpenAPI schema endpoint."""
        response = client.get("/api/docs/openapi-enhanced.json")
        assert response.status_code == 200

        data = response.json()
        # OpenAPI schema should have basic structure
        assert "openapi" in data or "info" in data or "paths" in data

    def test_get_enhanced_openapi_is_json(self, client: TestClient):
        """Test that enhanced OpenAPI returns valid JSON."""
        response = client.get("/api/docs/openapi-enhanced.json")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    # ========================================================================
    # Markdown Documentation Tests
    # ========================================================================

    def test_get_markdown_docs(self, client: TestClient):
        """Test Markdown documentation endpoint."""
        response = client.get("/api/docs/markdown")
        assert response.status_code == 200

        # Should return plain text
        assert "text/plain" in response.headers["content-type"]

        # Content should be non-empty
        assert len(response.text) > 0

    def test_get_markdown_docs_contains_headings(self, client: TestClient):
        """Test that Markdown docs contain expected headings."""
        response = client.get("/api/docs/markdown")
        assert response.status_code == 200

        # Markdown should have some structure
        content = response.text
        # Should contain markdown headings
        assert "#" in content or "API" in content

    # ========================================================================
    # Endpoint Documentation Tests
    # ========================================================================

    def test_get_endpoint_documentation_markdown(self, client: TestClient):
        """Test endpoint documentation in Markdown format."""
        response = client.get(
            "/api/docs/endpoint",
            params={"path": "/api/people", "method": "GET", "format": "markdown"},
        )
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_get_endpoint_documentation_json(self, client: TestClient):
        """Test endpoint documentation in JSON format."""
        response = client.get(
            "/api/docs/endpoint",
            params={"path": "/api/people", "method": "GET", "format": "json"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

        data = response.json()
        assert "documentation" in data

    def test_get_endpoint_documentation_requires_path(self, client: TestClient):
        """Test that path parameter is required."""
        response = client.get(
            "/api/docs/endpoint",
            params={"method": "GET"},
        )
        assert response.status_code == 422  # Validation error

    def test_get_endpoint_documentation_requires_method(self, client: TestClient):
        """Test that method parameter is required."""
        response = client.get(
            "/api/docs/endpoint",
            params={"path": "/api/people"},
        )
        assert response.status_code == 422  # Validation error

    # ========================================================================
    # Code Examples Tests
    # ========================================================================

    def test_get_code_examples(self, client: TestClient):
        """Test code examples endpoint."""
        response = client.get(
            "/api/docs/examples",
            params={"path": "/api/people", "method": "GET"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_get_code_examples_with_language(self, client: TestClient):
        """Test code examples with specific language filter."""
        response = client.get(
            "/api/docs/examples",
            params={"path": "/api/people", "method": "GET", "language": "python"},
        )
        assert response.status_code == 200

    def test_get_code_examples_requires_path(self, client: TestClient):
        """Test that path parameter is required for examples."""
        response = client.get(
            "/api/docs/examples",
            params={"method": "GET"},
        )
        assert response.status_code == 422

    # ========================================================================
    # Error Documentation Tests
    # ========================================================================

    def test_get_error_documentation(self, client: TestClient):
        """Test error documentation endpoint."""
        response = client.get("/api/docs/errors")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_error_documentation_structure(self, client: TestClient):
        """Test error documentation response structure."""
        response = client.get("/api/docs/errors")
        assert response.status_code == 200

        # Should return dict or list of error codes
        data = response.json()
        assert isinstance(data, (dict, list))

    # ========================================================================
    # Changelog Tests
    # ========================================================================

    def test_get_changelog(self, client: TestClient):
        """Test changelog endpoint."""
        response = client.get("/api/docs/changelog")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    # ========================================================================
    # Version Info Tests
    # ========================================================================

    def test_get_version_info(self, client: TestClient):
        """Test version info endpoint."""
        response = client.get("/api/docs/version")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

        data = response.json()
        # Should have version-related fields
        assert isinstance(data, dict)

    # ========================================================================
    # Stats Tests
    # ========================================================================

    def test_get_documentation_stats(self, client: TestClient):
        """Test documentation stats endpoint."""
        response = client.get("/api/docs/stats")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

        data = response.json()
        assert isinstance(data, dict)

    # ========================================================================
    # Export Tests
    # ========================================================================

    @patch("app.api.routes.docs._get_doc_generator")
    def test_export_openapi_schema(
        self,
        mock_get_generator: MagicMock,
        client: TestClient,
    ):
        """Test OpenAPI schema export endpoint."""
        mock_generator = MagicMock()
        mock_generator.export_openapi_json.return_value = None
        mock_get_generator.return_value = mock_generator

        response = client.get(
            "/api/docs/export/openapi",
            params={"filepath": "/tmp/test-openapi.json"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "filepath" in data

    @patch("app.api.routes.docs._get_doc_generator")
    def test_export_markdown_documentation(
        self,
        mock_get_generator: MagicMock,
        client: TestClient,
    ):
        """Test Markdown export endpoint."""
        mock_generator = MagicMock()
        mock_generator.export_markdown_docs.return_value = None
        mock_get_generator.return_value = mock_generator

        response = client.get(
            "/api/docs/export/markdown",
            params={"filepath": "/tmp/test-docs.md"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "filepath" in data

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @patch("app.api.routes.docs._get_doc_generator")
    def test_enhanced_openapi_error_handling(
        self,
        mock_get_generator: MagicMock,
        client: TestClient,
    ):
        """Test error handling in enhanced OpenAPI endpoint."""
        mock_generator = MagicMock()
        mock_generator.get_enhanced_openapi_schema.side_effect = Exception("Test error")
        mock_get_generator.return_value = mock_generator

        response = client.get("/api/docs/openapi-enhanced.json")
        assert response.status_code == 500
        assert "Failed to generate" in response.json()["detail"]

    @patch("app.api.routes.docs._get_doc_generator")
    def test_markdown_docs_error_handling(
        self,
        mock_get_generator: MagicMock,
        client: TestClient,
    ):
        """Test error handling in Markdown docs endpoint."""
        mock_generator = MagicMock()
        mock_generator.get_markdown_documentation.side_effect = Exception("Test error")
        mock_get_generator.return_value = mock_generator

        response = client.get("/api/docs/markdown")
        assert response.status_code == 500

    @patch("app.api.routes.docs._get_doc_generator")
    def test_export_error_handling(
        self,
        mock_get_generator: MagicMock,
        client: TestClient,
    ):
        """Test error handling in export endpoint."""
        mock_generator = MagicMock()
        mock_generator.export_openapi_json.side_effect = Exception("Export failed")
        mock_get_generator.return_value = mock_generator

        response = client.get(
            "/api/docs/export/openapi",
            params={"filepath": "/invalid/path.json"},
        )
        assert response.status_code == 500
