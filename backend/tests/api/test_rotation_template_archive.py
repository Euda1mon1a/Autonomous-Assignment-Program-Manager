"""Tests for rotation template archive/restore functionality.

This module tests Phase 3 features:
- Single template archive/restore
- Batch archive/restore operations
- Query filtering with include_archived parameter
- Archive fields and audit trail
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestRotationTemplateArchive:
    """Test archive and restore operations for rotation templates."""

    def test_archive_single_template(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test archiving a single rotation template."""
        # Create a template
        template_data = {
            "name": "Test Clinic",
            "rotation_type": "clinic",
            "supervision_required": True,
        }
        response = client.post(
            "/api/v1/rotation-templates",
            json=template_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        template_id = response.json()["id"]

        # Archive the template
        response = client.put(
            f"/api/v1/rotation-templates/{template_id}/archive",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is True
        assert data["archived_at"] is not None
        assert data["archived_by"] is not None

    def test_archive_already_archived_template_fails(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that archiving an already archived template fails."""
        # Create and archive a template
        template_data = {
            "name": "Test Clinic",
            "rotation_type": "clinic",
        }
        response = client.post(
            "/api/v1/rotation-templates",
            json=template_data,
            headers=auth_headers,
        )
        template_id = response.json()["id"]

        # Archive once
        client.put(
            f"/api/v1/rotation-templates/{template_id}/archive",
            headers=auth_headers,
        )

        # Try to archive again
        response = client.put(
            f"/api/v1/rotation-templates/{template_id}/archive",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already archived" in response.json()["detail"]

    def test_restore_archived_template(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test restoring an archived rotation template."""
        # Create and archive a template
        template_data = {
            "name": "Test Clinic",
            "rotation_type": "clinic",
        }
        response = client.post(
            "/api/v1/rotation-templates",
            json=template_data,
            headers=auth_headers,
        )
        template_id = response.json()["id"]

        client.put(
            f"/api/v1/rotation-templates/{template_id}/archive",
            headers=auth_headers,
        )

        # Restore the template
        response = client.put(
            f"/api/v1/rotation-templates/{template_id}/restore",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is False
        assert data["archived_at"] is None
        assert data["archived_by"] is None

    def test_restore_non_archived_template_fails(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that restoring a non-archived template fails."""
        # Create a template (not archived)
        template_data = {
            "name": "Test Clinic",
            "rotation_type": "clinic",
        }
        response = client.post(
            "/api/v1/rotation-templates",
            json=template_data,
            headers=auth_headers,
        )
        template_id = response.json()["id"]

        # Try to restore
        response = client.put(
            f"/api/v1/rotation-templates/{template_id}/restore",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "not archived" in response.json()["detail"]

    def test_list_excludes_archived_by_default(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that list endpoint excludes archived templates by default."""
        # Create two templates
        for i in range(2):
            client.post(
                "/api/v1/rotation-templates",
                json={"name": f"Template {i}", "rotation_type": "clinic"},
                headers=auth_headers,
            )

        # Get list (should show 2)
        response = client.get(
            "/api/v1/rotation-templates",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        initial_count = data["total"]
        assert initial_count >= 2

        # Archive one template
        template_id = data["items"][0]["id"]
        client.put(
            f"/api/v1/rotation-templates/{template_id}/archive",
            headers=auth_headers,
        )

        # Get list again (should show 1 less)
        response = client.get(
            "/api/v1/rotation-templates",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == initial_count - 1

    def test_list_with_include_archived(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that list endpoint includes archived templates when requested."""
        # Create and archive a template
        response = client.post(
            "/api/v1/rotation-templates",
            json={"name": "Test Clinic", "rotation_type": "clinic"},
            headers=auth_headers,
        )
        template_id = response.json()["id"]

        client.put(
            f"/api/v1/rotation-templates/{template_id}/archive",
            headers=auth_headers,
        )

        # Get list with include_archived=true
        response = client.get(
            "/api/v1/rotation-templates?include_archived=true",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Find the archived template
        archived_templates = [t for t in data["items"] if t["is_archived"]]
        assert len(archived_templates) >= 1


class TestRotationTemplateBatchArchive:
    """Test batch archive and restore operations."""

    def test_batch_archive_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test batch archiving multiple templates."""
        # Create 3 templates
        template_ids = []
        for i in range(3):
            response = client.post(
                "/api/v1/rotation-templates",
                json={"name": f"Template {i}", "rotation_type": "clinic"},
                headers=auth_headers,
            )
            template_ids.append(response.json()["id"])

        # Batch archive
        response = client.put(
            "/api/v1/rotation-templates/batch/archive",
            json={"template_ids": template_ids, "dry_run": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["operation_type"] == "archive"
        assert data["succeeded"] == 3
        assert data["failed"] == 0

    def test_batch_archive_dry_run(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test batch archive dry run mode."""
        # Create a template
        response = client.post(
            "/api/v1/rotation-templates",
            json={"name": "Test Clinic", "rotation_type": "clinic"},
            headers=auth_headers,
        )
        template_id = response.json()["id"]

        # Dry run archive
        response = client.put(
            "/api/v1/rotation-templates/batch/archive",
            json={"template_ids": [template_id], "dry_run": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["succeeded"] == 1

        # Verify template is NOT actually archived
        response = client.get(
            f"/api/v1/rotation-templates/{template_id}",
            headers=auth_headers,
        )
        assert response.json()["is_archived"] is False

    def test_batch_archive_partial_failure(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test batch archive with some invalid template IDs."""
        # Create one valid template
        response = client.post(
            "/api/v1/rotation-templates",
            json={"name": "Valid Template", "rotation_type": "clinic"},
            headers=auth_headers,
        )
        valid_id = response.json()["id"]
        invalid_id = str(uuid4())

        # Try to archive valid and invalid
        response = client.put(
            "/api/v1/rotation-templates/batch/archive",
            json={"template_ids": [valid_id, invalid_id], "dry_run": False},
            headers=auth_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert "failed" in data["detail"]

    def test_batch_restore_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test batch restoring multiple templates."""
        # Create and archive 2 templates
        template_ids = []
        for i in range(2):
            response = client.post(
                "/api/v1/rotation-templates",
                json={"name": f"Template {i}", "rotation_type": "clinic"},
                headers=auth_headers,
            )
            template_id = response.json()["id"]
            template_ids.append(template_id)

            # Archive it
            client.put(
                f"/api/v1/rotation-templates/{template_id}/archive",
                headers=auth_headers,
            )

        # Batch restore
        response = client.put(
            "/api/v1/rotation-templates/batch/restore",
            json={"template_ids": template_ids, "dry_run": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["operation_type"] == "restore"
        assert data["succeeded"] == 2
        assert data["failed"] == 0


class TestRotationTemplateBatchPatterns:
    """Test batch pattern application."""

    def test_batch_apply_patterns_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test applying the same pattern to multiple templates."""
        # Create 2 templates
        template_ids = []
        for i in range(2):
            response = client.post(
                "/api/v1/rotation-templates",
                json={"name": f"Clinic {i}", "rotation_type": "clinic"},
                headers=auth_headers,
            )
            template_ids.append(response.json()["id"])

        # Define a standard clinic pattern
        patterns = [
            {
                "day_of_week": 0,  # Monday
                "time_of_day": "AM",
                "rotation_type": "clinic",
                "is_protected": False,
            },
            {
                "day_of_week": 0,  # Monday
                "time_of_day": "PM",
                "rotation_type": "clinic",
                "is_protected": False,
            },
        ]

        # Apply to both templates
        response = client.put(
            "/api/v1/rotation-templates/batch/patterns",
            json={
                "template_ids": template_ids,
                "patterns": patterns,
                "dry_run": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["operation_type"] == "batch_apply_patterns"
        assert data["succeeded"] == 2
        assert data["failed"] == 0

        # Verify patterns were applied
        for template_id in template_ids:
            response = client.get(
                f"/api/v1/rotation-templates/{template_id}/patterns",
                headers=auth_headers,
            )
            assert len(response.json()) == 2


class TestRotationTemplateBatchPreferences:
    """Test batch preference application."""

    def test_batch_apply_preferences_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test applying the same preferences to multiple templates."""
        # Create 2 templates
        template_ids = []
        for i in range(2):
            response = client.post(
                "/api/v1/rotation-templates",
                json={"name": f"Template {i}", "rotation_type": "clinic"},
                headers=auth_headers,
            )
            template_ids.append(response.json()["id"])

        # Define standard preferences
        preferences = [
            {
                "preference_type": "full_day_grouping",
                "weight": "high",
                "is_active": True,
            },
            {
                "preference_type": "avoid_friday_pm",
                "weight": "medium",
                "is_active": True,
            },
        ]

        # Apply to both templates
        response = client.put(
            "/api/v1/rotation-templates/batch/preferences",
            json={
                "template_ids": template_ids,
                "preferences": preferences,
                "dry_run": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["operation_type"] == "batch_apply_preferences"
        assert data["succeeded"] == 2
        assert data["failed"] == 0

        # Verify preferences were applied
        for template_id in template_ids:
            response = client.get(
                f"/api/v1/rotation-templates/{template_id}/preferences",
                headers=auth_headers,
            )
            assert len(response.json()) == 2


class TestRotationTemplateHistory:
    """Test version history endpoint."""

    def test_get_template_history(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test retrieving version history for a template."""
        # Create a template
        response = client.post(
            "/api/v1/rotation-templates",
            json={"name": "Test Clinic", "rotation_type": "clinic"},
            headers=auth_headers,
        )
        template_id = response.json()["id"]

        # Update it to create history
        client.put(
            f"/api/v1/rotation-templates/{template_id}",
            json={"name": "Updated Clinic"},
            headers=auth_headers,
        )

        # Get history
        response = client.get(
            f"/api/v1/rotation-templates/{template_id}/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == template_id
        assert data["template_name"] == "Updated Clinic"
        assert "versions" in data
        assert "version_count" in data

    def test_get_history_nonexistent_template(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that getting history for nonexistent template returns 404."""
        response = client.get(
            f"/api/v1/rotation-templates/{uuid4()}/history",
            headers=auth_headers,
        )
        assert response.status_code == 404
