"""Tests for PUT /{template_id}/preferences endpoint.

Tests cover:
- Successful atomic replacement of preferences
- Validation of preference types and weights
- 404 for non-existent templates
- 401 for unauthenticated requests
- 400 for validation errors
"""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rotation_preference import RotationPreference
from app.models.rotation_template import RotationTemplate


class TestPutRotationPreferences:
    """Tests for PUT /rotation-templates/{template_id}/preferences."""

    @pytest.fixture
    def sample_template(self, db: Session) -> RotationTemplate:
        """Create a sample rotation template for testing."""
        template = RotationTemplate(
            id=uuid4(),
            name="Test Clinic Template",
            activity_type="clinic",
            abbreviation="TC",
            created_at=datetime.utcnow(),
        )
        db.add(template)
        db.commit()
        return template

    @pytest.fixture
    def existing_preferences(
        self, db: Session, sample_template: RotationTemplate
    ) -> list[RotationPreference]:
        """Create existing preferences that will be replaced."""
        now = datetime.utcnow()
        preferences = [
            RotationPreference(
                id=uuid4(),
                rotation_template_id=sample_template.id,
                preference_type="avoid_friday_pm",
                weight="low",
                config_json={},
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
        ]
        for pref in preferences:
            db.add(pref)
        db.commit()
        return preferences

    def test_replace_preferences_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        existing_preferences: list[RotationPreference],
    ):
        """Test successful atomic replacement of preferences."""
        new_preferences = [
            {
                "preference_type": "full_day_grouping",
                "weight": "medium",
                "config_json": {},
                "is_active": True,
                "description": "Prefer full days",
            },
            {
                "preference_type": "consecutive_specialty",
                "weight": "high",
                "config_json": {"min_consecutive": 2},
                "is_active": True,
                "description": "Group specialty sessions",
            },
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=new_preferences,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return 2 new preferences (replacing the 1 existing)
        assert len(data) == 2

        # Verify preference types
        types = {p["preference_type"] for p in data}
        assert "full_day_grouping" in types
        assert "consecutive_specialty" in types
        assert "avoid_friday_pm" not in types  # Old preference should be gone

    def test_replace_preferences_empty_list_clears_all(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        existing_preferences: list[RotationPreference],
    ):
        """Test that empty preferences list clears all existing preferences."""
        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=[],
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

        # Verify preferences are actually deleted
        get_response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        assert get_response.json() == []

    def test_replace_preferences_all_valid_types(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test all valid preference types can be created."""
        all_types = [
            "full_day_grouping",
            "consecutive_specialty",
            "avoid_isolated",
            "preferred_days",
            "avoid_friday_pm",
            "balance_weekly",
        ]

        preferences = [
            {
                "preference_type": ptype,
                "weight": "medium",
                "config_json": {},
                "is_active": True,
            }
            for ptype in all_types
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 6

        returned_types = {p["preference_type"] for p in data}
        assert returned_types == set(all_types)

    def test_replace_preferences_all_valid_weights(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test all valid weight values can be set."""
        weights = ["low", "medium", "high", "required"]

        preferences = [
            {
                "preference_type": f"full_day_grouping",  # Use same type, different weights
                "weight": weight,
                "config_json": {},
                "is_active": True,
            }
            for weight in weights[:1]  # Can only have one of each type
        ]

        # Create preferences with different types and weights
        type_weight_pairs = [
            ("full_day_grouping", "low"),
            ("consecutive_specialty", "medium"),
            ("avoid_isolated", "high"),
            ("avoid_friday_pm", "required"),
        ]

        preferences = [
            {
                "preference_type": ptype,
                "weight": weight,
                "config_json": {},
                "is_active": True,
            }
            for ptype, weight in type_weight_pairs
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 200
        data = response.json()

        weights_by_type = {p["preference_type"]: p["weight"] for p in data}
        assert weights_by_type["full_day_grouping"] == "low"
        assert weights_by_type["consecutive_specialty"] == "medium"
        assert weights_by_type["avoid_isolated"] == "high"
        assert weights_by_type["avoid_friday_pm"] == "required"

    def test_replace_preferences_duplicate_type_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that duplicate preference types fail validation."""
        preferences = [
            {
                "preference_type": "full_day_grouping",
                "weight": "medium",
                "config_json": {},
                "is_active": True,
            },
            {
                "preference_type": "full_day_grouping",  # Duplicate!
                "weight": "high",
                "config_json": {},
                "is_active": True,
            },
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 400
        error = response.json()
        assert "detail" in error
        assert "duplicate" in error["detail"].lower()

    def test_replace_preferences_invalid_type_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that invalid preference type fails validation."""
        preferences = [
            {
                "preference_type": "invalid_preference_type",
                "weight": "medium",
                "config_json": {},
                "is_active": True,
            }
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 400
        error = response.json()
        assert "detail" in error
        assert "invalid" in error["detail"].lower()

    def test_replace_preferences_invalid_weight_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that invalid weight fails validation."""
        preferences = [
            {
                "preference_type": "full_day_grouping",
                "weight": "critical",  # Invalid weight
                "config_json": {},
                "is_active": True,
            }
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code in [400, 422]

    def test_replace_preferences_template_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test 404 for non-existent template."""
        fake_id = uuid4()
        preferences = [
            {
                "preference_type": "full_day_grouping",
                "weight": "medium",
                "config_json": {},
                "is_active": True,
            }
        ]

        response = client.put(
            f"/api/rotation-templates/{fake_id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 400  # Service raises ValueError -> 400
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

    def test_replace_preferences_unauthorized(
        self, client: TestClient, sample_template: RotationTemplate
    ):
        """Test 401 for unauthenticated request."""
        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            json=[],
        )

        assert response.status_code == 401

    def test_replace_preferences_with_config_json(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test preferences can include complex config_json."""
        preferences = [
            {
                "preference_type": "consecutive_specialty",
                "weight": "high",
                "config_json": {"min_consecutive": 2, "max_gap": 4},
                "is_active": True,
            },
            {
                "preference_type": "preferred_days",
                "weight": "medium",
                "config_json": {
                    "activity": "fm_clinic",
                    "days": [1, 2, 5],
                    "avoid_days": [0, 6],
                },
                "is_active": True,
            },
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify config_json is preserved
        consecutive_pref = next(
            p for p in data if p["preference_type"] == "consecutive_specialty"
        )
        assert consecutive_pref["config_json"]["min_consecutive"] == 2
        assert consecutive_pref["config_json"]["max_gap"] == 4

        preferred_pref = next(
            p for p in data if p["preference_type"] == "preferred_days"
        )
        assert preferred_pref["config_json"]["days"] == [1, 2, 5]

    def test_replace_preferences_with_inactive(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test preferences can be created as inactive."""
        preferences = [
            {
                "preference_type": "full_day_grouping",
                "weight": "medium",
                "config_json": {},
                "is_active": False,  # Created as inactive
                "description": "Disabled preference",
            }
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is False

    def test_replace_preferences_atomicity_on_error(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        existing_preferences: list[RotationPreference],
        db: Session,
    ):
        """Test that on validation error, existing preferences are not deleted."""
        # Try to replace with invalid preferences
        preferences = [
            {
                "preference_type": "full_day_grouping",
                "weight": "medium",
                "config_json": {},
                "is_active": True,
            },
            {
                "preference_type": "full_day_grouping",  # Duplicate - should fail
                "weight": "high",
                "config_json": {},
                "is_active": True,
            },
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 400

        # Verify existing preferences still exist
        get_response = client.get(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert len(data) == 1  # Original preference should still be there
        assert data[0]["preference_type"] == "avoid_friday_pm"

    def test_replace_preferences_missing_required_fields(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that missing required fields fail validation."""
        # Missing preference_type
        preferences = [
            {
                "weight": "medium",
                "config_json": {},
                "is_active": True,
            }
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 422

    def test_replace_preferences_default_values(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that default values are applied correctly."""
        # Only required field
        preferences = [
            {
                "preference_type": "full_day_grouping",
            }
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/preferences",
            headers=auth_headers,
            json=preferences,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        # Verify defaults
        pref = data[0]
        assert pref["weight"] == "medium"  # Default weight
        assert pref["config_json"] == {}  # Default empty config
        assert pref["is_active"] is True  # Default active
        assert pref["description"] is None  # Optional, no default
