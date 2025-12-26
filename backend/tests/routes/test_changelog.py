"""Tests for changelog API routes.

Tests the API changelog functionality including:
- Version management (list, save, delete)
- Changelog generation between versions
- API diff detection
- Migration guide generation
- Semantic version suggestions
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestChangelogRoutes:
    """Test suite for changelog API endpoints."""

    # ========================================================================
    # Version Management Tests
    # ========================================================================

    @patch("app.api.routes.changelog.changelog_generator")
    def test_list_versions_success(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test listing all stored API versions."""
        mock_generator.list_versions.return_value = [
            {
                "version": "1.2.0",
                "saved_at": "2024-01-15T10:30:00",
                "metadata": {"author": "API Team"},
            },
            {
                "version": "1.1.0",
                "saved_at": "2024-01-10T09:00:00",
                "metadata": {},
            },
        ]

        response = client.get("/api/changelog/versions")
        assert response.status_code == 200

        data = response.json()
        assert "versions" in data
        assert data["count"] == 2
        assert data["versions"][0]["version"] == "1.2.0"

    @patch("app.api.routes.changelog.changelog_generator")
    def test_list_versions_empty(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test listing versions when none exist."""
        mock_generator.list_versions.return_value = []

        response = client.get("/api/changelog/versions")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 0
        assert data["versions"] == []

    @patch("app.api.routes.changelog.changelog_generator")
    def test_save_version_success(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test saving a version snapshot."""
        mock_generator.save_current_version.return_value = "1.2.0"

        response = client.post(
            "/api/changelog/versions",
            json={
                "version": "1.2.0",
                "schema": {
                    "openapi": "3.0.0",
                    "info": {"version": "1.2.0"},
                    "paths": {},
                },
                "metadata": {"author": "API Team"},
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["version"] == "1.2.0"
        assert "saved_at" in data

    @patch("app.api.routes.changelog.changelog_generator")
    def test_save_version_error(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test save version handles errors."""
        mock_generator.save_current_version.side_effect = Exception("Storage error")

        response = client.post(
            "/api/changelog/versions",
            json={
                "schema": {"openapi": "3.0.0", "paths": {}},
            },
        )
        assert response.status_code == 500

    @patch("app.api.routes.changelog.changelog_generator")
    def test_delete_version_success(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test deleting a version snapshot."""
        mock_generator.version_history.delete_version.return_value = True

        response = client.delete("/api/changelog/versions/1.0.0")
        assert response.status_code == 200

        data = response.json()
        assert "1.0.0" in data["message"]

    @patch("app.api.routes.changelog.changelog_generator")
    def test_delete_version_not_found(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test deleting non-existent version."""
        mock_generator.version_history.delete_version.return_value = False

        response = client.delete("/api/changelog/versions/9.9.9")
        assert response.status_code == 404

    # ========================================================================
    # Changelog Generation Tests
    # ========================================================================

    @patch("app.api.routes.changelog.changelog_generator")
    def test_generate_changelog_success(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test generating changelog from stored versions."""
        mock_generator.generate_from_versions.return_value = (
            "# API Changelog\n\n## Changes"
        )

        response = client.post(
            "/api/changelog/generate",
            json={
                "old_version": "1.0.0",
                "new_version": "1.1.0",
                "output_format": "markdown",
                "include_migration_guide": True,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "changelog" in data
        assert data["old_version"] == "1.0.0"
        assert data["new_version"] == "1.1.0"

    @patch("app.api.routes.changelog.changelog_generator")
    def test_generate_changelog_invalid_format(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test generating changelog with invalid format."""
        response = client.post(
            "/api/changelog/generate",
            json={
                "old_version": "1.0.0",
                "new_version": "1.1.0",
                "output_format": "invalid_format",
            },
        )
        assert response.status_code == 400
        assert "Invalid output format" in response.json()["detail"]

    @patch("app.api.routes.changelog.changelog_generator")
    def test_generate_changelog_version_not_found(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test generating changelog when version not found."""
        mock_generator.generate_from_versions.return_value = None

        response = client.post(
            "/api/changelog/generate",
            json={
                "old_version": "1.0.0",
                "new_version": "2.0.0",
                "output_format": "markdown",
            },
        )
        assert response.status_code == 404

    @patch("app.api.routes.changelog.changelog_generator")
    def test_generate_changelog_from_schemas(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test generating changelog from raw schemas."""
        mock_generator.generate_changelog.return_value = "# Changelog"

        response = client.post(
            "/api/changelog/generate/schemas",
            json={
                "old_schema": {
                    "openapi": "3.0.0",
                    "info": {"version": "1.0.0"},
                    "paths": {},
                },
                "new_schema": {
                    "openapi": "3.0.0",
                    "info": {"version": "1.1.0"},
                    "paths": {"/users": {"get": {}}},
                },
                "output_format": "markdown",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "changelog" in data

    # ========================================================================
    # API Diff Tests
    # ========================================================================

    @patch("app.api.routes.changelog.changelog_generator")
    def test_get_api_diff_success(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test getting structured diff between versions."""
        # Mock version history loading
        mock_generator.version_history.load_version.side_effect = [
            {"schema": {"openapi": "3.0.0", "paths": {}}},
            {"schema": {"openapi": "3.0.0", "paths": {"/new": {}}}},
        ]

        # Mock diff result
        mock_diff = MagicMock()
        mock_diff.changes = []
        mock_diff.breaking_changes = []
        mock_diff.non_breaking_changes = []
        mock_diff.has_breaking_changes = False
        mock_diff.old_version = "1.0.0"
        mock_diff.new_version = "1.1.0"
        mock_diff.suggest_version_bump.return_value = "1.1.0"
        mock_generator.get_diff.return_value = mock_diff

        response = client.post(
            "/api/changelog/diff",
            json={
                "old_version": "1.0.0",
                "new_version": "1.1.0",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "changes" in data

    @patch("app.api.routes.changelog.changelog_generator")
    def test_get_api_diff_old_version_not_found(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test diff when old version not found."""
        mock_generator.version_history.load_version.return_value = None

        response = client.post(
            "/api/changelog/diff",
            json={
                "old_version": "0.0.1",
                "new_version": "1.0.0",
            },
        )
        assert response.status_code == 404
        assert "Old version not found" in response.json()["detail"]

    # ========================================================================
    # Migration Guide Tests
    # ========================================================================

    @patch("app.api.routes.changelog.changelog_generator")
    def test_generate_migration_guide_success(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test generating migration guide."""
        # Mock version loading
        mock_generator.version_history.load_version.side_effect = [
            {"schema": {"openapi": "3.0.0", "paths": {}}},
            {"schema": {"openapi": "3.0.0", "paths": {}}},
        ]

        mock_generator.generate_migration_guide.return_value = "# Migration Guide"

        mock_diff = MagicMock()
        mock_diff.breaking_changes = [MagicMock(), MagicMock()]
        mock_generator.get_diff.return_value = mock_diff

        response = client.post(
            "/api/changelog/migration-guide",
            json={
                "old_version": "1.0.0",
                "new_version": "2.0.0",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "migration_guide" in data
        assert data["breaking_changes_count"] == 2

    # ========================================================================
    # Version Suggestion Tests
    # ========================================================================

    @patch("app.api.routes.changelog.changelog_generator")
    def test_suggest_version_success(
        self,
        mock_generator: MagicMock,
        client: TestClient,
    ):
        """Test semantic version suggestion."""
        # Mock version loading
        mock_generator.version_history.load_version.side_effect = [
            {"schema": {"openapi": "3.0.0", "paths": {}}},
            {"schema": {"openapi": "3.0.0", "paths": {}}},
        ]

        mock_generator.suggest_version.return_value = "2.0.0"

        mock_diff = MagicMock()
        mock_change = MagicMock()
        mock_change.change_type = MagicMock()
        mock_change.change_type.value = "endpoint_removed"
        mock_diff.changes = [mock_change]
        mock_diff.breaking_changes = [mock_change]
        mock_generator.get_diff.return_value = mock_diff

        response = client.post(
            "/api/changelog/suggest-version",
            json={
                "old_version": "1.0.0",
                "new_version": "current",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "suggested_version" in data
        assert data["breaking_changes"] >= 0

    # ========================================================================
    # Current Schema Tests
    # ========================================================================

    def test_get_current_schema(
        self,
        client: TestClient,
    ):
        """Test getting current OpenAPI schema."""
        response = client.get("/api/changelog/current")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data or "swagger" in data
