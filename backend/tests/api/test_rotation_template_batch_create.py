"""Tests for batch create rotation template endpoint.

Tests cover:
- Batch POST /rotation-templates/batch
  - Successful atomic creation of multiple templates
  - Dry-run mode validation without creation
  - 400 error when duplicate names in batch
  - 400 error when name collision with existing template
  - 401 for unauthenticated requests
  - Empty array validation
  - Single template creation
  - Validation of all fields
"""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rotation_template import RotationTemplate


class TestBatchCreateRotationTemplates:
    """Tests for POST /rotation-templates/batch."""

    def test_batch_create_success(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test successful atomic creation of multiple templates."""
        templates = [
            {"name": "Test Clinic A", "activity_type": "clinic"},
            {"name": "Test Inpatient B", "activity_type": "inpatient"},
            {"name": "Test Procedure C", "activity_type": "procedure"},
        ]

        response = client.post(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": templates, "dry_run": False},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["operation_type"] == "create"
        assert data["total"] == 3
        assert data["succeeded"] == 3
        assert data["failed"] == 0
        assert data["dry_run"] is False
        assert len(data["results"]) == 3
        assert data["created_ids"] is not None
        assert len(data["created_ids"]) == 3

        # Verify all results are successful
        for result in data["results"]:
            assert result["success"] is True
            assert result["error"] is None

        # Verify templates are actually created
        for created_id in data["created_ids"]:
            get_response = client.get(
                f"/api/rotation-templates/{created_id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 200

    def test_batch_create_dry_run(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test dry-run mode validates without creating."""
        templates = [
            {"name": "Dry Run Clinic", "activity_type": "clinic"},
            {"name": "Dry Run Inpatient", "activity_type": "inpatient"},
        ]

        response = client.post(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": templates, "dry_run": True},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["operation_type"] == "create"
        assert data["total"] == 2
        assert data["succeeded"] == 2
        assert data["failed"] == 0
        assert data["dry_run"] is True
        # No IDs created in dry run
        assert data["created_ids"] is None or len(data["created_ids"]) == 0

        # Verify templates are NOT created
        all_templates = client.get(
            "/api/rotation-templates",
            headers=auth_headers,
        )
        template_names = [t["name"] for t in all_templates.json()["items"]]
        assert "Dry Run Clinic" not in template_names
        assert "Dry Run Inpatient" not in template_names

    def test_batch_create_duplicate_names_in_batch_fails(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that duplicate names within batch fail atomically."""
        templates = [
            {"name": "Duplicate Test", "activity_type": "clinic"},
            {"name": "Duplicate Test", "activity_type": "inpatient"},
        ]

        response = client.post(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": templates, "dry_run": False},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["failed"] >= 1

    def test_batch_create_name_collision_with_existing(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test that name collision with existing template fails."""
        # Create existing template
        existing = RotationTemplate(
            id=uuid4(),
            name="Existing Template",
            activity_type="clinic",
            created_at=datetime.utcnow(),
        )
        db.add(existing)
        db.commit()

        templates = [
            {"name": "Existing Template", "activity_type": "inpatient"},
            {"name": "New Template", "activity_type": "clinic"},
        ]

        response = client.post(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": templates, "dry_run": False},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["failed"] >= 1

    def test_batch_create_single_template(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch create with single template."""
        templates = [
            {"name": "Single Batch Create", "activity_type": "clinic"},
        ]

        response = client.post(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": templates, "dry_run": False},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 1
        assert data["succeeded"] == 1
        assert len(data["created_ids"]) == 1

    def test_batch_create_unauthorized(
        self, client: TestClient
    ):
        """Test 401 for unauthenticated request."""
        templates = [
            {"name": "Unauthorized", "activity_type": "clinic"},
        ]

        response = client.post(
            "/api/rotation-templates/batch",
            json={"templates": templates},
        )

        assert response.status_code == 401

    def test_batch_create_empty_array_fails(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that empty templates array fails validation."""
        response = client.post(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": []},
        )

        # Pydantic validation should fail for min_length=1
        assert response.status_code == 422

    def test_batch_create_with_all_fields(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test batch create with all optional fields specified."""
        templates = [
            {
                "name": "Full Template",
                "activity_type": "clinic",
                "abbreviation": "FT",
                "display_abbreviation": "FULL",
                "font_color": "text-blue-400",
                "background_color": "bg-blue-500/20",
                "clinic_location": "Main Clinic",
                "max_residents": 5,
                "requires_specialty": "Internal Medicine",
                "requires_procedure_credential": True,
                "supervision_required": True,
                "max_supervision_ratio": 4,
            },
        ]

        response = client.post(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": templates, "dry_run": False},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["succeeded"] == 1

        # Verify fields are saved correctly
        created_id = data["created_ids"][0]
        get_response = client.get(
            f"/api/rotation-templates/{created_id}",
            headers=auth_headers,
        )
        template = get_response.json()
        assert template["name"] == "Full Template"
        assert template["abbreviation"] == "FT"
        assert template["max_residents"] == 5
        assert template["supervision_required"] is True

    def test_batch_create_invalid_activity_type_fails(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that invalid activity_type fails validation."""
        templates = [
            {"name": "Invalid Type", "activity_type": "invalid_type"},
        ]

        response = client.post(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": templates, "dry_run": False},
        )

        # Pydantic validation should fail
        assert response.status_code == 422
