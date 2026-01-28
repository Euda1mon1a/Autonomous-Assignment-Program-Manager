"""Tests for GET /{template_id}/patterns endpoint.

Tests cover:
- Successful retrieval of patterns
- Empty pattern list for templates without patterns
- 404 for non-existent templates
- 401 for unauthenticated requests
- Pattern ordering by day and time
"""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern


class TestGetWeeklyPatterns:
    """Tests for GET /rotation-templates/{template_id}/patterns."""

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
    def sample_patterns(
        self, db: Session, sample_template: RotationTemplate
    ) -> list[WeeklyPattern]:
        """Create sample weekly patterns for testing."""
        now = datetime.utcnow()
        patterns = [
            WeeklyPattern(
                id=uuid4(),
                rotation_template_id=sample_template.id,
                day_of_week=1,  # Monday
                time_of_day="AM",
                activity_type="fm_clinic",
                is_protected=False,
                created_at=now,
                updated_at=now,
            ),
            WeeklyPattern(
                id=uuid4(),
                rotation_template_id=sample_template.id,
                day_of_week=1,  # Monday
                time_of_day="PM",
                activity_type="fm_clinic",
                is_protected=False,
                created_at=now,
                updated_at=now,
            ),
            WeeklyPattern(
                id=uuid4(),
                rotation_template_id=sample_template.id,
                day_of_week=2,  # Tuesday
                time_of_day="AM",
                activity_type="specialty",
                is_protected=True,
                created_at=now,
                updated_at=now,
            ),
        ]
        for pattern in patterns:
            db.add(pattern)
        db.commit()
        return patterns

    def test_get_patterns_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        sample_patterns: list[WeeklyPattern],
    ):
        """Test successful retrieval of weekly patterns."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return 3 patterns
        assert len(data) == 3

        # Verify pattern structure
        first_pattern = data[0]
        assert "id" in first_pattern
        assert "rotation_template_id" in first_pattern
        assert "day_of_week" in first_pattern
        assert "time_of_day" in first_pattern
        assert "activity_type" in first_pattern
        assert "is_protected" in first_pattern
        assert "created_at" in first_pattern
        assert "updated_at" in first_pattern

    def test_get_patterns_ordered_by_day_and_time(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        sample_patterns: list[WeeklyPattern],
    ):
        """Test patterns are returned ordered by day_of_week and time_of_day."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify ordering
        for i in range(len(data) - 1):
            current = data[i]
            next_item = data[i + 1]

            if current["day_of_week"] == next_item["day_of_week"]:
                # Same day: AM should come before PM
                assert current["time_of_day"] <= next_item["time_of_day"]
            else:
                # Different days: lower day number should come first
                assert current["day_of_week"] <= next_item["day_of_week"]

    def test_get_patterns_empty_list(
        self, client: TestClient, auth_headers: dict, sample_template: RotationTemplate
    ):
        """Test returns empty list for template with no patterns."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_patterns_template_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test 404 for non-existent template."""
        fake_id = uuid4()
        response = client.get(
            f"/api/rotation-templates/{fake_id}/patterns",
            headers=auth_headers,
        )

        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

    def test_get_patterns_unauthorized(
        self, client: TestClient, sample_template: RotationTemplate
    ):
        """Test 401 for unauthenticated request."""
        response = client.get(f"/api/rotation-templates/{sample_template.id}/patterns")

        assert response.status_code == 401

    def test_get_patterns_invalid_uuid(self, client: TestClient, auth_headers: dict):
        """Test 422 for invalid UUID format."""
        response = client.get(
            "/api/rotation-templates/not-a-uuid/patterns",
            headers=auth_headers,
        )

        # FastAPI returns 422 for path parameter validation errors
        assert response.status_code in [400, 422]

    def test_get_patterns_includes_protected_flag(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_template: RotationTemplate,
        sample_patterns: list[WeeklyPattern],
    ):
        """Test patterns include is_protected flag correctly."""
        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Find the protected pattern (Tuesday AM)
        protected_patterns = [p for p in data if p["is_protected"]]
        assert len(protected_patterns) == 1
        assert protected_patterns[0]["day_of_week"] == 2
        assert protected_patterns[0]["time_of_day"] == "AM"

    def test_get_patterns_includes_linked_template_id(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_template: RotationTemplate,
    ):
        """Test patterns can include linked_template_id."""
        # Create another template to link to
        linked_template = RotationTemplate(
            id=uuid4(),
            name="Specialty Template",
            activity_type="specialty",
            created_at=datetime.utcnow(),
        )
        db.add(linked_template)

        # Create pattern with linked template
        now = datetime.utcnow()
        pattern = WeeklyPattern(
            id=uuid4(),
            rotation_template_id=sample_template.id,
            day_of_week=3,
            time_of_day="AM",
            activity_type="specialty",
            linked_template_id=linked_template.id,
            is_protected=False,
            created_at=now,
            updated_at=now,
        )
        db.add(pattern)
        db.commit()

        response = client.get(
            f"/api/rotation-templates/{sample_template.id}/patterns",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["linked_template_id"] == str(linked_template.id)
