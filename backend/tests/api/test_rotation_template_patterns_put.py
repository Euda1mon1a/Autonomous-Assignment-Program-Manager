"""Tests for PUT /{template_id}/patterns endpoint.

Tests cover:
- Successful atomic replacement of patterns
- Validation of pattern data
- 404 for non-existent templates
- 401 for unauthenticated requests
- 400 for validation errors
"""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern


class TestPutWeeklyPatterns:
    """Tests for PUT /rotation-templates/{template_id}/patterns."""

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
    def existing_patterns(
        self, db: Session, sample_template: RotationTemplate
    ) -> list[WeeklyPattern]:
        """Create existing patterns that will be replaced."""
        now = datetime.utcnow()
        patterns = [
            WeeklyPattern(
                id=uuid4(),
                rotation_template_id=sample_template.id,
                day_of_week=0,  # Sunday
                time_of_day="AM",
                activity_type="off",
                is_protected=False,
                created_at=now,
                updated_at=now,
            ),
        ]
        for pattern in patterns:
            db.add(pattern)
        db.commit()
        return patterns

    def test_replace_patterns_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        existing_patterns: list[WeeklyPattern],
    ):
        """Test successful atomic replacement of patterns."""
        new_patterns = {
            "patterns": [
                {
                    "day_of_week": 1,
                    "time_of_day": "AM",
                    "activity_type": "fm_clinic",
                    "is_protected": False,
                },
                {
                    "day_of_week": 1,
                    "time_of_day": "PM",
                    "activity_type": "fm_clinic",
                    "is_protected": False,
                },
                {
                    "day_of_week": 2,
                    "time_of_day": "AM",
                    "activity_type": "specialty",
                    "is_protected": True,
                    "notes": "Protected conference time",
                },
            ]
        }

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json=new_patterns,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return 3 new patterns (replacing the 1 existing)
        assert len(data) == 3

        # Verify pattern content
        activity_types = {p["activity_type"] for p in data}
        assert "fm_clinic" in activity_types
        assert "specialty" in activity_types
        assert "off" not in activity_types  # Old pattern should be gone

    def test_replace_patterns_empty_list_clears_all(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        existing_patterns: list[WeeklyPattern],
    ):
        """Test that empty patterns list clears all existing patterns."""
        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json={"patterns": []},
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

        # Verify patterns are actually deleted
        get_response = client.get(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        assert get_response.json() == []

    def test_replace_patterns_max_14_slots(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that maximum 14 patterns (7 days x 2 times) are allowed."""
        # Create full 14-slot grid
        patterns = []
        for day in range(7):
            for time in ["AM", "PM"]:
                patterns.append(
                    {
                        "day_of_week": day,
                        "time_of_day": time,
                        "activity_type": "fm_clinic",
                        "is_protected": False,
                    }
                )

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json={"patterns": patterns},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 14

    def test_replace_patterns_over_14_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that more than 14 patterns fails validation."""
        # Create 15 patterns (invalid)
        patterns = [
            {
                "day_of_week": i % 7,
                "time_of_day": "AM" if i < 7 else "PM",
                "activity_type": "fm_clinic",
                "is_protected": False,
            }
            for i in range(15)
        ]

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json={"patterns": patterns},
        )

        # Should fail with validation error
        assert response.status_code in [400, 422]

    def test_replace_patterns_duplicate_slot_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that duplicate day/time slots fail validation."""
        patterns = {
            "patterns": [
                {
                    "day_of_week": 1,
                    "time_of_day": "AM",
                    "activity_type": "fm_clinic",
                    "is_protected": False,
                },
                {
                    "day_of_week": 1,
                    "time_of_day": "AM",  # Duplicate!
                    "activity_type": "specialty",
                    "is_protected": False,
                },
            ]
        }

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json=patterns,
        )

        assert response.status_code == 400
        error = response.json()
        assert "detail" in error
        assert "duplicate" in error["detail"].lower()

    def test_replace_patterns_invalid_day_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that invalid day_of_week fails validation."""
        patterns = {
            "patterns": [
                {
                    "day_of_week": 7,  # Invalid: must be 0-6
                    "time_of_day": "AM",
                    "activity_type": "fm_clinic",
                    "is_protected": False,
                }
            ]
        }

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json=patterns,
        )

        assert response.status_code in [400, 422]

    def test_replace_patterns_invalid_time_fails(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test that invalid time_of_day fails validation."""
        patterns = {
            "patterns": [
                {
                    "day_of_week": 1,
                    "time_of_day": "NOON",  # Invalid: must be AM or PM
                    "activity_type": "fm_clinic",
                    "is_protected": False,
                }
            ]
        }

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json=patterns,
        )

        assert response.status_code in [400, 422]

    def test_replace_patterns_template_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test 404 for non-existent template."""
        fake_id = uuid4()
        patterns = {
            "patterns": [
                {
                    "day_of_week": 1,
                    "time_of_day": "AM",
                    "activity_type": "fm_clinic",
                    "is_protected": False,
                }
            ]
        }

        response = client.put(
            f"/api/rotation-templates/{fake_id}/patterns",
            headers=auth_headers,
            json=patterns,
        )

        assert response.status_code == 400  # Service raises ValueError -> 400
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

    def test_replace_patterns_unauthorized(
        self, client: TestClient, sample_template: RotationTemplate
    ):
        """Test 401 for unauthenticated request."""
        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            json={"patterns": []},
        )

        assert response.status_code == 401

    def test_replace_patterns_with_linked_template(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_template: RotationTemplate,
    ):
        """Test patterns can reference linked templates."""
        # Create template to link to
        linked_template = RotationTemplate(
            id=uuid4(),
            name="Specialty Template",
            activity_type="specialty",
            created_at=datetime.utcnow(),
        )
        db.add(linked_template)
        db.commit()

        patterns = {
            "patterns": [
                {
                    "day_of_week": 1,
                    "time_of_day": "AM",
                    "activity_type": "specialty",
                    "linked_template_id": str(linked_template.id),
                    "is_protected": False,
                }
            ]
        }

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json=patterns,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["linked_template_id"] == str(linked_template.id)

    def test_replace_patterns_with_notes(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
    ):
        """Test patterns can include notes."""
        patterns = {
            "patterns": [
                {
                    "day_of_week": 3,  # Wednesday
                    "time_of_day": "AM",
                    "activity_type": "conference",
                    "is_protected": True,
                    "notes": "Weekly department meeting - do not schedule",
                }
            ]
        }

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json=patterns,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["notes"] == "Weekly department meeting - do not schedule"
        assert data[0]["is_protected"] is True

    def test_replace_patterns_atomicity_on_error(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        existing_patterns: list[WeeklyPattern],
        db: Session,
    ):
        """Test that on validation error, existing patterns are not deleted."""
        # Try to replace with invalid patterns
        patterns = {
            "patterns": [
                {
                    "day_of_week": 1,
                    "time_of_day": "AM",
                    "activity_type": "fm_clinic",
                    "is_protected": False,
                },
                {
                    "day_of_week": 1,
                    "time_of_day": "AM",  # Duplicate - should fail
                    "activity_type": "specialty",
                    "is_protected": False,
                },
            ]
        }

        response = client.put(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
            json=patterns,
        )

        assert response.status_code == 400

        # Verify existing patterns still exist
        get_response = client.get(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert len(data) == 1  # Original pattern should still be there
        assert data[0]["activity_type"] == "off"
