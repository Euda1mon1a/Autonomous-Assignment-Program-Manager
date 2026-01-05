"""Tests for batch rotation template endpoints.

Tests cover:
- Batch DELETE /rotation-templates/batch
  - Successful atomic deletion of multiple templates
  - Dry-run mode validation without deletion
  - 400 error when any template not found (atomic)
  - 401 for unauthenticated requests
  - Empty array validation
  - Single template deletion

- Batch PUT /rotation-templates/batch
  - Successful atomic update of multiple templates
  - Dry-run mode validation without updating
  - 400 error when any template not found (atomic)
  - 401 for unauthenticated requests
  - Partial updates (exclude_unset behavior)
"""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rotation_template import RotationTemplate


class TestBatchDeleteRotationTemplates:
    """Tests for DELETE /rotation-templates/batch."""

    @pytest.fixture
    def sample_templates(self, db: Session) -> list[RotationTemplate]:
        """Create sample rotation templates for testing."""
        templates = []
        for i in range(3):
            template = RotationTemplate(
                id=uuid4(),
                name=f"Test Template {i}",
                activity_type="clinic",
                abbreviation=f"T{i}",
                created_at=datetime.utcnow(),
            )
            db.add(template)
            templates.append(template)
        db.commit()
        return templates

    def test_batch_delete_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test successful atomic deletion of multiple templates."""
        template_ids = [str(t.id) for t in sample_templates]

        response = client.request(
            "DELETE",
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"template_ids": template_ids, "dry_run": False},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["operation_type"] == "delete"
        assert data["total"] == 3
        assert data["succeeded"] == 3
        assert data["failed"] == 0
        assert data["dry_run"] is False
        assert len(data["results"]) == 3

        # Verify all results are successful
        for result in data["results"]:
            assert result["success"] is True
            assert result["error"] is None

        # Verify templates are actually deleted
        for template_id in template_ids:
            get_response = client.get(
                f"/api/rotation-templates/{template_id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 404

    def test_batch_delete_dry_run(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test dry-run mode validates without deleting."""
        template_ids = [str(t.id) for t in sample_templates]

        response = client.request(
            "DELETE",
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"template_ids": template_ids, "dry_run": True},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["operation_type"] == "delete"
        assert data["total"] == 3
        assert data["succeeded"] == 3
        assert data["failed"] == 0
        assert data["dry_run"] is True

        # Verify templates are NOT deleted
        for template_id in template_ids:
            get_response = client.get(
                f"/api/rotation-templates/{template_id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 200

    def test_batch_delete_partial_not_found_fails_atomically(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test that if any template not found, entire batch fails."""
        template_ids = [str(t.id) for t in sample_templates]
        fake_id = str(uuid4())
        template_ids.append(fake_id)

        response = client.request(
            "DELETE",
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"template_ids": template_ids, "dry_run": False},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["failed"] == 1

        # Verify original templates are NOT deleted (atomic rollback)
        for template in sample_templates:
            get_response = client.get(
                f"/api/rotation-templates/{template.id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 200

    def test_batch_delete_single_template(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test batch delete with single template."""
        template_id = str(sample_templates[0].id)

        response = client.request(
            "DELETE",
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"template_ids": [template_id], "dry_run": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["succeeded"] == 1

    def test_batch_delete_unauthorized(
        self, client: TestClient, sample_templates: list[RotationTemplate]
    ):
        """Test 401 for unauthenticated request."""
        template_ids = [str(t.id) for t in sample_templates]

        response = client.request(
            "DELETE",
            "/api/rotation-templates/batch",
            json={"template_ids": template_ids},
        )

        assert response.status_code == 401

    def test_batch_delete_empty_array_fails(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that empty template_ids array fails validation."""
        response = client.request(
            "DELETE",
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"template_ids": []},
        )

        # Pydantic validation should fail for min_length=1
        assert response.status_code == 422


class TestBatchUpdateRotationTemplates:
    """Tests for PUT /rotation-templates/batch."""

    @pytest.fixture
    def sample_templates(self, db: Session) -> list[RotationTemplate]:
        """Create sample rotation templates for testing."""
        templates = []
        for i in range(3):
            template = RotationTemplate(
                id=uuid4(),
                name=f"Test Template {i}",
                activity_type="clinic",
                abbreviation=f"T{i}",
                max_residents=i + 1,
                supervision_required=True,
                created_at=datetime.utcnow(),
            )
            db.add(template)
            templates.append(template)
        db.commit()
        return templates

    def test_batch_update_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test successful atomic update of multiple templates."""
        updates = [
            {
                "template_id": str(sample_templates[0].id),
                "updates": {"max_residents": 10},
            },
            {
                "template_id": str(sample_templates[1].id),
                "updates": {"supervision_required": False},
            },
            {
                "template_id": str(sample_templates[2].id),
                "updates": {"activity_type": "inpatient", "max_residents": 5},
            },
        ]

        response = client.put(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": updates, "dry_run": False},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["operation_type"] == "update"
        assert data["total"] == 3
        assert data["succeeded"] == 3
        assert data["failed"] == 0
        assert data["dry_run"] is False

        # Verify updates were applied
        for i, template in enumerate(sample_templates):
            get_response = client.get(
                f"/api/rotation-templates/{template.id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 200
            template_data = get_response.json()

            if i == 0:
                assert template_data["max_residents"] == 10
            elif i == 1:
                assert template_data["supervision_required"] is False
            elif i == 2:
                assert template_data["activity_type"] == "inpatient"
                assert template_data["max_residents"] == 5

    def test_batch_update_dry_run(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test dry-run mode validates without updating."""
        original_max_residents = [t.max_residents for t in sample_templates]

        updates = [
            {
                "template_id": str(sample_templates[0].id),
                "updates": {"max_residents": 100},
            },
            {
                "template_id": str(sample_templates[1].id),
                "updates": {"max_residents": 200},
            },
        ]

        response = client.put(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": updates, "dry_run": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["succeeded"] == 2

        # Verify values are NOT changed
        for i, template in enumerate(sample_templates[:2]):
            get_response = client.get(
                f"/api/rotation-templates/{template.id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 200
            template_data = get_response.json()
            assert template_data["max_residents"] == original_max_residents[i]

    def test_batch_update_partial_not_found_fails_atomically(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test that if any template not found, entire batch fails."""
        original_max_residents = sample_templates[0].max_residents
        fake_id = str(uuid4())

        updates = [
            {
                "template_id": str(sample_templates[0].id),
                "updates": {"max_residents": 999},
            },
            {
                "template_id": fake_id,
                "updates": {"max_residents": 100},
            },
        ]

        response = client.put(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": updates, "dry_run": False},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"]["failed"] == 1

        # Verify first template was NOT updated (atomic rollback)
        get_response = client.get(
            f"/api/rotation-templates/{sample_templates[0].id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        template_data = get_response.json()
        assert template_data["max_residents"] == original_max_residents

    def test_batch_update_same_field_different_values(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test updating same field with different values per template."""
        updates = [
            {
                "template_id": str(sample_templates[0].id),
                "updates": {"max_residents": 1},
            },
            {
                "template_id": str(sample_templates[1].id),
                "updates": {"max_residents": 2},
            },
            {
                "template_id": str(sample_templates[2].id),
                "updates": {"max_residents": 3},
            },
        ]

        response = client.put(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": updates, "dry_run": False},
        )

        assert response.status_code == 200

        # Verify each template has its own value
        for i, template in enumerate(sample_templates):
            get_response = client.get(
                f"/api/rotation-templates/{template.id}",
                headers=auth_headers,
            )
            template_data = get_response.json()
            assert template_data["max_residents"] == i + 1

    def test_batch_update_unauthorized(
        self, client: TestClient, sample_templates: list[RotationTemplate]
    ):
        """Test 401 for unauthenticated request."""
        updates = [
            {
                "template_id": str(sample_templates[0].id),
                "updates": {"max_residents": 10},
            },
        ]

        response = client.put(
            "/api/rotation-templates/batch",
            json={"templates": updates},
        )

        assert response.status_code == 401

    def test_batch_update_empty_array_fails(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that empty templates array fails validation."""
        response = client.put(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": []},
        )

        # Pydantic validation should fail for min_length=1
        assert response.status_code == 422

    def test_batch_update_single_template(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test batch update with single template."""
        updates = [
            {
                "template_id": str(sample_templates[0].id),
                "updates": {"name": "Updated Name"},
            },
        ]

        response = client.put(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": updates, "dry_run": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["succeeded"] == 1

        # Verify update
        get_response = client.get(
            f"/api/rotation-templates/{sample_templates[0].id}",
            headers=auth_headers,
        )
        assert get_response.json()["name"] == "Updated Name"

    def test_batch_update_partial_fields(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_templates: list[RotationTemplate],
    ):
        """Test that partial updates only change specified fields."""
        original_name = sample_templates[0].name
        original_activity = sample_templates[0].activity_type

        updates = [
            {
                "template_id": str(sample_templates[0].id),
                "updates": {"max_residents": 50},  # Only update max_residents
            },
        ]

        response = client.put(
            "/api/rotation-templates/batch",
            headers=auth_headers,
            json={"templates": updates, "dry_run": False},
        )

        assert response.status_code == 200

        # Verify only max_residents changed, other fields preserved
        get_response = client.get(
            f"/api/rotation-templates/{sample_templates[0].id}",
            headers=auth_headers,
        )
        template_data = get_response.json()
        assert template_data["max_residents"] == 50
        assert template_data["name"] == original_name
        assert template_data["activity_type"] == original_activity
