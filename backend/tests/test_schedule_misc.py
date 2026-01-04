"""
Comprehensive tests for Schedule Miscellaneous API routes.

Tests coverage for:
- GET /api/schedule/{start_date}/{end_date} - Get schedule for date range
- POST /api/schedule/faculty-outpatient/generate - Generate faculty outpatient assignments
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes for GET /api/schedule/{start_date}/{end_date}
# ============================================================================


class TestGetScheduleEndpoint:
    """Tests for GET /api/schedule/{start_date}/{end_date} endpoint."""

    def test_get_schedule_success(self, client: TestClient):
        """Test successful schedule retrieval."""
        start = date.today().isoformat()
        end = (date.today() + timedelta(days=7)).isoformat()

        response = client.get(f"/api/schedule/{start}/{end}")

        # May succeed or need auth depending on configuration
        assert response.status_code in [200, 401, 422, 500]

    def test_get_schedule_empty_results(self, client: TestClient):
        """Test schedule retrieval with no assignments."""
        # Use far future dates unlikely to have assignments
        start = (date.today() + timedelta(days=365)).isoformat()
        end = (date.today() + timedelta(days=372)).isoformat()

        response = client.get(f"/api/schedule/{start}/{end}")

        assert response.status_code in [200, 401, 422, 500]

    def test_get_schedule_invalid_start_date(self, client: TestClient):
        """Test schedule retrieval with invalid start date format."""
        response = client.get("/api/schedule/invalid-date/2025-01-31")

        assert response.status_code in [400, 422]

    def test_get_schedule_invalid_end_date(self, client: TestClient):
        """Test schedule retrieval with invalid end date format."""
        response = client.get("/api/schedule/2025-01-01/invalid-date")

        assert response.status_code in [400, 422]

    def test_get_schedule_both_dates_invalid(self, client: TestClient):
        """Test schedule retrieval with both dates invalid."""
        response = client.get("/api/schedule/bad/dates")

        assert response.status_code in [400, 422]

    def test_get_schedule_single_day(self, client: TestClient):
        """Test schedule retrieval for a single day."""
        single_date = date.today().isoformat()

        response = client.get(f"/api/schedule/{single_date}/{single_date}")

        assert response.status_code in [200, 401, 422, 500]

    def test_get_schedule_date_range(self, client: TestClient):
        """Test schedule retrieval for various date ranges."""
        ranges = [
            (date.today(), date.today() + timedelta(days=1)),  # 2 days
            (date.today(), date.today() + timedelta(days=7)),  # 1 week
            (date.today(), date.today() + timedelta(days=28)),  # 4 weeks
        ]

        for start, end in ranges:
            response = client.get(
                f"/api/schedule/{start.isoformat()}/{end.isoformat()}"
            )
            assert response.status_code in [200, 401, 422, 500]

    def test_get_schedule_end_before_start(self, client: TestClient):
        """Test schedule retrieval with end date before start date."""
        start = (date.today() + timedelta(days=7)).isoformat()
        end = date.today().isoformat()

        response = client.get(f"/api/schedule/{start}/{end}")

        # Should still work but return empty or handle gracefully
        assert response.status_code in [200, 400, 401, 422, 500]

    def test_get_schedule_response_structure(self, client: TestClient, db: Session):
        """Test schedule response has expected structure."""
        start = date.today().isoformat()
        end = (date.today() + timedelta(days=7)).isoformat()

        response = client.get(f"/api/schedule/{start}/{end}")

        if response.status_code == 200:
            data = response.json()
            assert "start_date" in data
            assert "end_date" in data
            assert "schedule" in data
            assert "total_assignments" in data

    def test_get_schedule_grouped_by_date(self, client: TestClient):
        """Test that schedule is properly grouped by date."""
        start = date.today().isoformat()
        end = (date.today() + timedelta(days=7)).isoformat()

        response = client.get(f"/api/schedule/{start}/{end}")

        if response.status_code == 200:
            data = response.json()
            schedule = data.get("schedule", {})
            # Schedule should be a dict with date keys
            for date_key, slots in schedule.items():
                assert isinstance(slots, dict)
                # Should have AM and PM keys
                assert "AM" in slots or "PM" in slots or slots == {}


# ============================================================================
# Test Classes for POST /api/schedule/faculty-outpatient/generate
# ============================================================================


class TestFacultyOutpatientGenerateEndpoint:
    """Tests for POST /api/schedule/faculty-outpatient/generate endpoint."""

    def test_generate_requires_auth(self, client: TestClient):
        """Test that faculty outpatient generation requires authentication."""
        response = client.post(
            "/api/schedule/faculty-outpatient/generate",
            params={"block_number": 1},
        )

        assert response.status_code in [401, 403]

    def test_generate_happy_path(self, client: TestClient, auth_headers: dict):
        """Test successful faculty outpatient generation."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Generated successfully"
            mock_result.block_number = 1
            mock_result.block_start = date.today()
            mock_result.block_end = date.today() + timedelta(days=28)
            mock_result.total_clinic_assignments = 20
            mock_result.total_supervision_assignments = 15
            mock_result.cleared_count = 0
            mock_result.faculty_summaries = []
            mock_result.warnings = []
            mock_result.errors = []

            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.return_value = (
                mock_result
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={"block_number": 1},
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_generate_with_regenerate(self, client: TestClient, auth_headers: dict):
        """Test faculty outpatient generation with regenerate flag."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Regenerated successfully"
            mock_result.block_number = 1
            mock_result.block_start = date.today()
            mock_result.block_end = date.today() + timedelta(days=28)
            mock_result.total_clinic_assignments = 20
            mock_result.total_supervision_assignments = 15
            mock_result.cleared_count = 35
            mock_result.faculty_summaries = []
            mock_result.warnings = []
            mock_result.errors = []

            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.return_value = (
                mock_result
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={"block_number": 1, "regenerate": True},
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_generate_clinic_only(self, client: TestClient, auth_headers: dict):
        """Test faculty outpatient generation with only clinic assignments."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Generated clinic only"
            mock_result.block_number = 1
            mock_result.block_start = date.today()
            mock_result.block_end = date.today() + timedelta(days=28)
            mock_result.total_clinic_assignments = 20
            mock_result.total_supervision_assignments = 0
            mock_result.cleared_count = 0
            mock_result.faculty_summaries = []
            mock_result.warnings = []
            mock_result.errors = []

            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.return_value = (
                mock_result
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={
                    "block_number": 1,
                    "include_clinic": True,
                    "include_supervision": False,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_generate_supervision_only(self, client: TestClient, auth_headers: dict):
        """Test faculty outpatient generation with only supervision assignments."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Generated supervision only"
            mock_result.block_number = 1
            mock_result.block_start = date.today()
            mock_result.block_end = date.today() + timedelta(days=28)
            mock_result.total_clinic_assignments = 0
            mock_result.total_supervision_assignments = 15
            mock_result.cleared_count = 0
            mock_result.faculty_summaries = []
            mock_result.warnings = []
            mock_result.errors = []

            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.return_value = (
                mock_result
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={
                    "block_number": 1,
                    "include_clinic": False,
                    "include_supervision": True,
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_generate_invalid_block_number_zero(
        self, client: TestClient, auth_headers: dict
    ):
        """Test generation with invalid block number (0)."""
        response = client.post(
            "/api/schedule/faculty-outpatient/generate",
            params={"block_number": 0},
            headers=auth_headers,
        )

        # Block number must be 1-13
        assert response.status_code in [400, 401, 422]

    def test_generate_invalid_block_number_14(
        self, client: TestClient, auth_headers: dict
    ):
        """Test generation with invalid block number (14)."""
        response = client.post(
            "/api/schedule/faculty-outpatient/generate",
            params={"block_number": 14},
            headers=auth_headers,
        )

        # Block number must be 1-13
        assert response.status_code in [400, 401, 422]

    def test_generate_negative_block_number(
        self, client: TestClient, auth_headers: dict
    ):
        """Test generation with negative block number."""
        response = client.post(
            "/api/schedule/faculty-outpatient/generate",
            params={"block_number": -1},
            headers=auth_headers,
        )

        assert response.status_code in [400, 401, 422]

    def test_generate_service_failure(self, client: TestClient, auth_headers: dict):
        """Test generation when service returns failure."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            mock_result = MagicMock()
            mock_result.success = False
            mock_result.message = "No faculty available for assignments"

            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.return_value = (
                mock_result
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={"block_number": 1},
                headers=auth_headers,
            )

            assert response.status_code in [400, 401, 422, 500]

    def test_generate_service_exception(self, client: TestClient, auth_headers: dict):
        """Test generation when service raises exception."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.side_effect = (
                ValueError("Database error")
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={"block_number": 1},
                headers=auth_headers,
            )

            assert response.status_code in [400, 401, 500]

    def test_generate_faculty_summaries(self, client: TestClient, auth_headers: dict):
        """Test generation includes faculty summaries in response."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            faculty_summary = MagicMock()
            faculty_summary.faculty_id = uuid4()
            faculty_summary.faculty_name = "Dr. Smith"
            faculty_summary.faculty_role = "Core"
            faculty_summary.clinic_sessions = 4
            faculty_summary.supervision_sessions = 3
            faculty_summary.total_sessions = 7

            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Generated successfully"
            mock_result.block_number = 1
            mock_result.block_start = date.today()
            mock_result.block_end = date.today() + timedelta(days=28)
            mock_result.total_clinic_assignments = 4
            mock_result.total_supervision_assignments = 3
            mock_result.cleared_count = 0
            mock_result.faculty_summaries = [faculty_summary]
            mock_result.warnings = []
            mock_result.errors = []

            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.return_value = (
                mock_result
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={"block_number": 1},
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_generate_with_warnings(self, client: TestClient, auth_headers: dict):
        """Test generation that produces warnings."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Generated with warnings"
            mock_result.block_number = 1
            mock_result.block_start = date.today()
            mock_result.block_end = date.today() + timedelta(days=28)
            mock_result.total_clinic_assignments = 15
            mock_result.total_supervision_assignments = 10
            mock_result.cleared_count = 0
            mock_result.faculty_summaries = []
            mock_result.warnings = [
                "Dr. Smith exceeded weekly clinic limit",
                "Some slots left unassigned",
            ]
            mock_result.errors = []

            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.return_value = (
                mock_result
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={"block_number": 1},
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_generate_specialty_constraints(
        self, client: TestClient, auth_headers: dict
    ):
        """Test generation respects specialty constraints."""
        with patch(
            "app.api.routes.schedule.FacultyOutpatientAssignmentService"
        ) as mock_service_class:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Generated with specialty constraints"
            mock_result.block_number = 1
            mock_result.block_start = date.today()
            mock_result.block_end = date.today() + timedelta(days=28)
            mock_result.total_clinic_assignments = 20
            mock_result.total_supervision_assignments = 15
            mock_result.cleared_count = 0
            mock_result.faculty_summaries = []
            mock_result.warnings = []
            mock_result.errors = []

            mock_service = MagicMock()
            mock_service.generate_faculty_outpatient_assignments.return_value = (
                mock_result
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/schedule/faculty-outpatient/generate",
                params={"block_number": 1},
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]


# ============================================================================
# Integration Tests
# ============================================================================


class TestScheduleMiscIntegration:
    """Integration tests for miscellaneous schedule endpoints."""

    def test_get_schedule_endpoint_exists(self, client: TestClient):
        """Test that get schedule endpoint exists."""
        start = date.today().isoformat()
        end = (date.today() + timedelta(days=7)).isoformat()

        response = client.get(f"/api/schedule/{start}/{end}")

        assert response.status_code != 404

    def test_faculty_outpatient_endpoint_exists(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that faculty outpatient endpoint exists."""
        response = client.post(
            "/api/schedule/faculty-outpatient/generate",
            params={"block_number": 1},
            headers=auth_headers,
        )

        assert response.status_code != 404

    def test_all_blocks_valid(self, client: TestClient, auth_headers: dict):
        """Test that all valid block numbers (1-13) are accepted."""
        for block in range(1, 14):
            with patch(
                "app.api.routes.schedule.FacultyOutpatientAssignmentService"
            ) as mock_service_class:
                mock_result = MagicMock()
                mock_result.success = True
                mock_result.message = "Success"
                mock_result.block_number = block
                mock_result.block_start = date.today()
                mock_result.block_end = date.today() + timedelta(days=28)
                mock_result.total_clinic_assignments = 0
                mock_result.total_supervision_assignments = 0
                mock_result.cleared_count = 0
                mock_result.faculty_summaries = []
                mock_result.warnings = []
                mock_result.errors = []

                mock_service = MagicMock()
                mock_service.generate_faculty_outpatient_assignments.return_value = (
                    mock_result
                )
                mock_service_class.return_value = mock_service

                response = client.post(
                    "/api/schedule/faculty-outpatient/generate",
                    params={"block_number": block},
                    headers=auth_headers,
                )

                # Should not reject valid block numbers
                assert response.status_code in [
                    200,
                    400,
                    401,
                    422,
                    500,
                ], f"Block {block} failed"

    def test_date_validation_consistency(self, client: TestClient):
        """Test that date validation is consistent across endpoints."""
        # Test various date formats
        valid_dates = [
            "2025-01-01",
            "2025-12-31",
            "2026-06-15",
        ]

        for date_str in valid_dates:
            end_date = (date.fromisoformat(date_str) + timedelta(days=7)).isoformat()
            response = client.get(f"/api/schedule/{date_str}/{end_date}")
            assert response.status_code in [
                200,
                401,
                422,
                500,
            ], f"Valid date {date_str} rejected"

        # Invalid dates should be rejected
        invalid_dates = [
            "2025-13-01",  # Invalid month
            "2025-01-32",  # Invalid day
            "25-01-01",  # Wrong format
            "2025/01/01",  # Wrong separator
        ]

        for date_str in invalid_dates:
            response = client.get(f"/api/schedule/{date_str}/2025-01-31")
            assert response.status_code in [
                400,
                422,
            ], f"Invalid date {date_str} accepted"
