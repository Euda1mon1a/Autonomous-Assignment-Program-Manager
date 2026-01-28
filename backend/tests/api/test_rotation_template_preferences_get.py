"""Tests for GET /{template_id}/preferences endpoint.

Tests cover:
- Successful retrieval of preferences
- Empty preference list for templates without preferences
- 404 for non-existent templates
- 401 for unauthenticated requests
- Preference structure validation
"""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rotation_preference import RotationPreference
from app.models.rotation_template import RotationTemplate


class TestGetRotationPreferences:
    """Tests for GET /rotation-templates/{template_id}/preferences."""

    @pytest.fixture
    def sample_template(self, db: Session) -> RotationTemplate:
        """Create a sample rotation template for testing."""
        template = RotationTemplate(
            id=uuid4(),
            name="Test Clinic Template",
            rotation_type="clinic",
            abbreviation="TC",
            created_at=datetime.utcnow(),
        )
        db.add(template)
        db.commit()
        return template

    @pytest.fixture
    def sample_preferences(
        self, db: Session, sample_template: RotationTemplate
    ) -> list[RotationPreference]:
        """Create sample preferences for testing."""
        now = datetime.utcnow()
        preferences = [
            RotationPreference(
                id=uuid4(),
                rotation_template_id=sample_template.id,
                preference_type="full_day_grouping",
                weight="medium",
                config_json={},
                is_active=True,
                description="Prefer full days when possible",
                created_at=now,
                updated_at=now,
            ),
            RotationPreference(
                id=uuid4(),
                rotation_template_id=sample_template.id,
                preference_type="avoid_friday_pm",
                weight="low",
                config_json={},
                is_active=True,
                description="Keep Friday PM open",
                created_at=now,
                updated_at=now,
            ),
            RotationPreference(
                id=uuid4(),
                rotation_template_id=sample_template.id,
                preference_type="consecutive_specialty",
                weight="high",
                config_json={"min_consecutive": 2},
                is_active=False,
                description="Group specialty sessions",
                created_at=now,
                updated_at=now,
            ),
        ]
        for pref in preferences:
            db.add(pref)
        db.commit()
        return preferences

    def test_get_preferences_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        sample_preferences: list[RotationPreference],
    ):
        """Test successful retrieval of preferences."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return 3 preferences
        assert len(data) == 3

        # Verify preference structure
        first_pref = data[0]
        assert "id" in first_pref
        assert "rotation_template_id" in first_pref
        assert "preference_type" in first_pref
        assert "weight" in first_pref
        assert "config_json" in first_pref
        assert "is_active" in first_pref
        assert "description" in first_pref
        assert "created_at" in first_pref
        assert "updated_at" in first_pref

    def test_get_preferences_ordered_by_type(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        sample_preferences: list[RotationPreference],
    ):
        """Test preferences are returned ordered by preference_type."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify alphabetical ordering by preference_type
        types = [p["preference_type"] for p in data]
        assert types == sorted(types)

    def test_get_preferences_empty_list(
        self, client: TestClient, auth_headers: dict, sample_template: RotationTemplate
    ):
        """Test returns empty list for template with no preferences."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_preferences_template_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test 404 for non-existent template."""
        fake_id = uuid4()
        response = client.get(
            f"/api/rotation-templates/{fake_id}/preferences",
            headers=auth_headers,
        )

        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

    def test_get_preferences_unauthorized(
        self, client: TestClient, sample_template: RotationTemplate
    ):
        """Test 401 for unauthenticated request."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences"
        )

        assert response.status_code == 401

    def test_get_preferences_invalid_uuid(self, client: TestClient, auth_headers: dict):
        """Test 422 for invalid UUID format."""
        response = client.get(
            "/api/rotation-templates/not-a-uuid/preferences",
            headers=auth_headers,
        )

        # FastAPI returns 422 for path parameter validation errors
        assert response.status_code in [400, 422]

    def test_get_preferences_includes_config_json(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        sample_preferences: list[RotationPreference],
    ):
        """Test preferences include config_json correctly."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Find the consecutive_specialty preference with config
        config_pref = next(
            p for p in data if p["preference_type"] == "consecutive_specialty"
        )
        assert config_pref["config_json"] == {"min_consecutive": 2}

    def test_get_preferences_includes_active_status(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        sample_preferences: list[RotationPreference],
    ):
        """Test preferences include is_active correctly."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check active/inactive status
        active_prefs = [p for p in data if p["is_active"]]
        inactive_prefs = [p for p in data if not p["is_active"]]

        assert len(active_prefs) == 2
        assert len(inactive_prefs) == 1
        assert inactive_prefs[0]["preference_type"] == "consecutive_specialty"

    def test_get_preferences_weight_values(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        sample_preferences: list[RotationPreference],
    ):
        """Test preferences have valid weight values."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        valid_weights = {"low", "medium", "high", "required"}
        for pref in data:
            assert pref["weight"] in valid_weights

        # Verify specific weights
        weights_by_type = {p["preference_type"]: p["weight"] for p in data}
        assert weights_by_type["full_day_grouping"] == "medium"
        assert weights_by_type["avoid_friday_pm"] == "low"
        assert weights_by_type["consecutive_specialty"] == "high"

    def test_get_preferences_description_optional(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_template: RotationTemplate,
    ):
        """Test preferences can have null description."""
        now = datetime.utcnow()
        pref = RotationPreference(
            id=uuid4(),
            rotation_template_id=sample_template.id,
            preference_type="balance_weekly",
            weight="medium",
            config_json={},
            is_active=True,
            description=None,  # No description
            created_at=now,
            updated_at=now,
        )
        db.add(pref)
        db.commit()

        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] is None
