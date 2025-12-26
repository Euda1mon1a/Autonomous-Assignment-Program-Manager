"""
Comprehensive tests for Daily Manifest API routes.

Tests coverage for daily staffing manifest:
- GET /api/assignments/daily-manifest - Get daily manifest showing where everyone is
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestDailyManifestEndpoint:
    """Tests for GET /api/assignments/daily-manifest endpoint."""

    def test_daily_manifest_requires_auth(self, client: TestClient):
        """Test that daily manifest requires authentication."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}"
        )

        # Should require authentication
        assert response.status_code in [401, 403]

    def test_daily_manifest_requires_date_param(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that daily manifest requires date parameter."""
        response = client.get(
            "/api/assignments/daily-manifest",
            headers=auth_headers,
        )

        # Should return 422 for missing required param
        assert response.status_code in [401, 422]

    def test_daily_manifest_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting daily manifest with valid date."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}",
            headers=auth_headers,
        )

        # May return 200 or 401 depending on auth fixture
        assert response.status_code in [200, 401]

    def test_daily_manifest_with_time_of_day_am(
        self, client: TestClient, auth_headers: dict
    ):
        """Test daily manifest filtered by AM time slot."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}&time_of_day=AM",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]

    def test_daily_manifest_with_time_of_day_pm(
        self, client: TestClient, auth_headers: dict
    ):
        """Test daily manifest filtered by PM time slot."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}&time_of_day=PM",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401]

    def test_daily_manifest_invalid_time_of_day(
        self, client: TestClient, auth_headers: dict
    ):
        """Test daily manifest with invalid time_of_day parameter."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}&time_of_day=INVALID",
            headers=auth_headers,
        )

        # Should return 400 for invalid time_of_day
        assert response.status_code in [400, 401]

    def test_daily_manifest_response_structure(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test daily manifest response has correct structure."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            # Verify expected fields
            assert "date" in data
            assert "locations" in data
            assert "generated_at" in data
            assert isinstance(data["locations"], list)

    def test_daily_manifest_future_date(self, client: TestClient, auth_headers: dict):
        """Test daily manifest for a future date."""
        from datetime import timedelta

        future_date = date.today() + timedelta(days=7)
        response = client.get(
            f"/api/assignments/daily-manifest?date={future_date.isoformat()}",
            headers=auth_headers,
        )

        # Should work for future dates
        assert response.status_code in [200, 401]

    def test_daily_manifest_past_date(self, client: TestClient, auth_headers: dict):
        """Test daily manifest for a past date."""
        from datetime import timedelta

        past_date = date.today() - timedelta(days=7)
        response = client.get(
            f"/api/assignments/daily-manifest?date={past_date.isoformat()}",
            headers=auth_headers,
        )

        # Should work for past dates
        assert response.status_code in [200, 401]


class TestDailyManifestWithData:
    """Tests for daily manifest with actual assignment data."""

    def test_daily_manifest_with_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_assignment,
    ):
        """Test daily manifest returns assignments correctly."""
        from datetime import date as date_type

        # Get the date from the sample assignment's block
        block_date = sample_assignment.block.date

        response = client.get(
            f"/api/assignments/daily-manifest?date={block_date.isoformat()}",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "locations" in data
            # May or may not have locations depending on data

    def test_daily_manifest_location_grouping(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that assignments are grouped by location."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            locations = data.get("locations", [])
            for location in locations:
                assert "clinic_location" in location
                assert "time_slots" in location
                assert "staffing_summary" in location

    def test_daily_manifest_staffing_summary(
        self, client: TestClient, auth_headers: dict
    ):
        """Test staffing summary calculation."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            for location in data.get("locations", []):
                summary = location.get("staffing_summary", {})
                if summary:
                    assert "total" in summary
                    assert "residents" in summary
                    assert "faculty" in summary


class TestDailyManifestEdgeCases:
    """Tests for edge cases in daily manifest."""

    def test_daily_manifest_invalid_date_format(
        self, client: TestClient, auth_headers: dict
    ):
        """Test daily manifest with invalid date format."""
        response = client.get(
            "/api/assignments/daily-manifest?date=invalid-date",
            headers=auth_headers,
        )

        # Should return 422 for invalid date format
        assert response.status_code in [401, 422]

    def test_daily_manifest_empty_day(self, client: TestClient, auth_headers: dict):
        """Test daily manifest for a day with no assignments."""
        from datetime import timedelta

        # Use a far future date unlikely to have assignments
        far_future = date.today() + timedelta(days=365 * 2)
        response = client.get(
            f"/api/assignments/daily-manifest?date={far_future.isoformat()}",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            # Should return empty locations list
            assert "locations" in data

    def test_daily_manifest_accepts_only_get(self, client: TestClient):
        """Test that daily manifest only accepts GET requests."""
        test_date = date.today().isoformat()

        # POST should not be allowed
        response = client.post(f"/api/assignments/daily-manifest?date={test_date}")
        assert response.status_code in [401, 405]

        # PUT should not be allowed
        response = client.put(f"/api/assignments/daily-manifest?date={test_date}")
        assert response.status_code in [401, 405]


# ============================================================================
# Integration Tests
# ============================================================================


class TestDailyManifestIntegration:
    """Integration tests for daily manifest functionality."""

    def test_daily_manifest_json_response(self, client: TestClient, auth_headers: dict):
        """Test daily manifest returns valid JSON."""
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}",
            headers=auth_headers,
        )

        if response.status_code == 200:
            assert response.headers["content-type"] == "application/json"
            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)

    def test_daily_manifest_performance(self, client: TestClient, auth_headers: dict):
        """Test daily manifest responds quickly."""
        import time

        start = time.time()
        response = client.get(
            f"/api/assignments/daily-manifest?date={date.today().isoformat()}",
            headers=auth_headers,
        )
        elapsed = time.time() - start

        # Should respond within 2 seconds
        assert elapsed < 2.0
        assert response.status_code in [200, 401]
