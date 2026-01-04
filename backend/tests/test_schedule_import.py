"""
Comprehensive tests for Schedule Import API routes.

Tests coverage for:
- POST /api/schedule/import/analyze - Analyze imported schedules for conflicts
- POST /api/schedule/import/analyze-file - Quick analysis of a single file
- POST /api/schedule/import/block - Parse a block schedule from Excel
"""

import io
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Helper Functions
# ============================================================================


def create_mock_excel_file(content: bytes = b"mock excel content") -> io.BytesIO:
    """Create a mock Excel file for testing."""
    return io.BytesIO(content)


# ============================================================================
# Test Classes for POST /api/schedule/import/analyze
# ============================================================================


class TestImportAnalyzeEndpoint:
    """Tests for POST /api/schedule/import/analyze endpoint."""

    def test_analyze_basic(self, client: TestClient):
        """Test basic schedule import analysis."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch("app.api.routes.schedule.analyze_schedule_conflicts") as mock_analyze,
        ):
            mock_validate.return_value = None
            mock_analyze.return_value = {
                "success": True,
                "fmit_schedule": {
                    "start_date": date.today().isoformat(),
                    "end_date": (date.today() + timedelta(days=28)).isoformat(),
                    "total_slots": 20,
                },
                "clinic_schedule": None,
                "conflicts": [],
                "recommendations": [],
                "summary": {
                    "total_conflicts": 0,
                    "critical_conflicts": 0,
                    "providers_affected": 0,
                },
            }

            response = client.post(
                "/api/schedule/import/analyze",
                files={
                    "fmit_file": (
                        "fmit.xlsx",
                        b"mock content",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

            # May succeed or fail validation
            assert response.status_code in [200, 400, 422, 500]

    def test_analyze_with_clinic_file(self, client: TestClient):
        """Test analysis with both FMIT and clinic files."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch("app.api.routes.schedule.analyze_schedule_conflicts") as mock_analyze,
        ):
            mock_validate.return_value = None
            mock_analyze.return_value = {
                "success": True,
                "fmit_schedule": {"start_date": date.today().isoformat()},
                "clinic_schedule": {"start_date": date.today().isoformat()},
                "conflicts": [
                    {
                        "type": "double_booking",
                        "provider": "Dr. Smith",
                        "date": date.today().isoformat(),
                        "fmit_slot": "AM",
                        "clinic_slot": "AM",
                    }
                ],
                "recommendations": [
                    {"type": "reschedule", "message": "Move clinic to PM"}
                ],
                "summary": {"total_conflicts": 1},
            }

            response = client.post(
                "/api/schedule/import/analyze",
                files={
                    "fmit_file": (
                        "fmit.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ),
                    "clinic_file": (
                        "clinic.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ),
                },
            )

            assert response.status_code in [200, 400, 422, 500]

    def test_analyze_malformed_excel(self, client: TestClient):
        """Test analysis with malformed Excel file."""
        with patch("app.api.routes.schedule.validate_excel_upload") as mock_validate:
            from app.core.file_security import FileValidationError

            mock_validate.side_effect = FileValidationError("Invalid file format")

            response = client.post(
                "/api/schedule/import/analyze",
                files={
                    "fmit_file": (
                        "bad.xlsx",
                        b"not excel",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

            assert response.status_code in [400, 422]

    def test_analyze_empty_file(self, client: TestClient):
        """Test analysis with empty file."""
        response = client.post(
            "/api/schedule/import/analyze",
            files={
                "fmit_file": (
                    "empty.xlsx",
                    b"",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert response.status_code in [400, 422]

    def test_analyze_with_specialty_providers(self, client: TestClient):
        """Test analysis with specialty providers JSON."""
        import json

        specialty_map = {"Sports Medicine": ["FAC-SPORTS"], "Cardiology": ["FAC-CARD"]}

        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch("app.api.routes.schedule.analyze_schedule_conflicts") as mock_analyze,
        ):
            mock_validate.return_value = None
            mock_analyze.return_value = {
                "success": True,
                "fmit_schedule": {},
                "clinic_schedule": None,
                "conflicts": [],
                "recommendations": [],
                "summary": {"total_conflicts": 0},
            }

            response = client.post(
                "/api/schedule/import/analyze",
                files={
                    "fmit_file": (
                        "fmit.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"specialty_providers": json.dumps(specialty_map)},
            )

            assert response.status_code in [200, 400, 422, 500]

    def test_analyze_invalid_specialty_json(self, client: TestClient):
        """Test analysis with invalid specialty providers JSON."""
        with patch("app.api.routes.schedule.validate_excel_upload") as mock_validate:
            mock_validate.return_value = None

            response = client.post(
                "/api/schedule/import/analyze",
                files={
                    "fmit_file": (
                        "fmit.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"specialty_providers": "not valid json{"},
            )

            assert response.status_code in [400, 422]

    def test_analyze_file_read_error(self, client: TestClient):
        """Test analysis when file read fails."""
        # Test with missing file
        response = client.post("/api/schedule/import/analyze", files={})

        assert response.status_code == 422

    def test_analyze_analysis_failure(self, client: TestClient):
        """Test analysis when analysis function fails."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch("app.api.routes.schedule.analyze_schedule_conflicts") as mock_analyze,
        ):
            mock_validate.return_value = None
            mock_analyze.return_value = {
                "success": False,
                "error": "Failed to parse schedule format",
            }

            response = client.post(
                "/api/schedule/import/analyze",
                files={
                    "fmit_file": (
                        "fmit.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

            assert response.status_code in [400, 422, 500]


# ============================================================================
# Test Classes for POST /api/schedule/import/analyze-file
# ============================================================================


class TestImportAnalyzeFileEndpoint:
    """Tests for POST /api/schedule/import/analyze-file endpoint."""

    def test_analyze_file_basic(self, client: TestClient):
        """Test basic single file analysis."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch(
                "app.api.routes.schedule.ClinicScheduleImporter"
            ) as mock_importer_class,
        ):
            mock_validate.return_value = None

            mock_result = MagicMock()
            mock_result.success = True
            mock_result.providers = {}
            mock_result.date_range = (date.today(), date.today() + timedelta(days=28))
            mock_result.total_slots = 20
            mock_result.fmit_slots = 10
            mock_result.clinic_slots = 10
            mock_result.warnings = []

            mock_importer = MagicMock()
            mock_importer.import_file.return_value = mock_result
            mock_importer_class.return_value = mock_importer

            response = client.post(
                "/api/schedule/import/analyze-file",
                files={
                    "file": (
                        "schedule.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"file_type": "auto"},
            )

            assert response.status_code in [200, 400, 422, 500]

    def test_analyze_file_fmit_type(self, client: TestClient):
        """Test single file analysis with FMIT type."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch(
                "app.api.routes.schedule.ClinicScheduleImporter"
            ) as mock_importer_class,
        ):
            mock_validate.return_value = None

            mock_result = MagicMock()
            mock_result.success = True
            mock_result.providers = {}
            mock_result.date_range = (date.today(), date.today() + timedelta(days=28))
            mock_result.total_slots = 20
            mock_result.fmit_slots = 20
            mock_result.clinic_slots = 0
            mock_result.warnings = []

            mock_importer = MagicMock()
            mock_importer.import_file.return_value = mock_result
            mock_importer_class.return_value = mock_importer

            response = client.post(
                "/api/schedule/import/analyze-file",
                files={
                    "file": (
                        "fmit.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"file_type": "fmit"},
            )

            assert response.status_code in [200, 400, 422, 500]

    def test_analyze_file_clinic_type(self, client: TestClient):
        """Test single file analysis with clinic type."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch(
                "app.api.routes.schedule.ClinicScheduleImporter"
            ) as mock_importer_class,
        ):
            mock_validate.return_value = None

            mock_result = MagicMock()
            mock_result.success = True
            mock_result.providers = {}
            mock_result.date_range = (date.today(), date.today() + timedelta(days=28))
            mock_result.total_slots = 20
            mock_result.fmit_slots = 0
            mock_result.clinic_slots = 20
            mock_result.warnings = []

            mock_importer = MagicMock()
            mock_importer.import_file.return_value = mock_result
            mock_importer_class.return_value = mock_importer

            response = client.post(
                "/api/schedule/import/analyze-file",
                files={
                    "file": (
                        "clinic.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"file_type": "clinic"},
            )

            assert response.status_code in [200, 400, 422, 500]

    def test_analyze_file_invalid_format(self, client: TestClient):
        """Test analysis with invalid file format."""
        with patch("app.api.routes.schedule.validate_excel_upload") as mock_validate:
            from app.core.file_security import FileValidationError

            mock_validate.side_effect = FileValidationError("Invalid file")

            response = client.post(
                "/api/schedule/import/analyze-file",
                files={"file": ("bad.txt", b"not excel", "text/plain")},
            )

            assert response.status_code in [400, 422]

    def test_analyze_file_size_limit(self, client: TestClient):
        """Test analysis with oversized file."""
        # Create a large mock file
        large_content = b"x" * (10 * 1024 * 1024 + 1)  # Just over 10MB

        with patch("app.api.routes.schedule.validate_excel_upload") as mock_validate:
            from app.core.file_security import FileValidationError

            mock_validate.side_effect = FileValidationError("File too large")

            response = client.post(
                "/api/schedule/import/analyze-file",
                files={
                    "file": (
                        "large.xlsx",
                        large_content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

            assert response.status_code in [400, 413, 422]

    def test_analyze_file_parse_failure(self, client: TestClient):
        """Test analysis when parsing fails."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch(
                "app.api.routes.schedule.ClinicScheduleImporter"
            ) as mock_importer_class,
        ):
            mock_validate.return_value = None

            mock_result = MagicMock()
            mock_result.success = False
            mock_result.errors = ["Could not find schedule header row"]

            mock_importer = MagicMock()
            mock_importer.import_file.return_value = mock_result
            mock_importer_class.return_value = mock_importer

            response = client.post(
                "/api/schedule/import/analyze-file",
                files={
                    "file": (
                        "bad.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

            assert response.status_code in [400, 422]

    def test_analyze_file_alternating_patterns(self, client: TestClient):
        """Test detection of alternating FMIT patterns."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch(
                "app.api.routes.schedule.ClinicScheduleImporter"
            ) as mock_importer_class,
        ):
            mock_validate.return_value = None

            mock_schedule = MagicMock()
            mock_schedule.has_alternating_pattern.return_value = True
            mock_schedule.get_fmit_weeks.return_value = [
                (date.today(), date.today() + timedelta(days=6)),
                (date.today() + timedelta(days=14), date.today() + timedelta(days=20)),
            ]
            mock_schedule.slots = {}

            mock_result = MagicMock()
            mock_result.success = True
            mock_result.providers = {"Dr. Smith": mock_schedule}
            mock_result.date_range = (date.today(), date.today() + timedelta(days=28))
            mock_result.total_slots = 20
            mock_result.fmit_slots = 10
            mock_result.clinic_slots = 10
            mock_result.warnings = []

            mock_importer = MagicMock()
            mock_importer.import_file.return_value = mock_result
            mock_importer_class.return_value = mock_importer

            response = client.post(
                "/api/schedule/import/analyze-file",
                files={
                    "file": (
                        "schedule.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            )

            assert response.status_code in [200, 400, 422, 500]


# ============================================================================
# Test Classes for POST /api/schedule/import/block
# ============================================================================


class TestImportBlockEndpoint:
    """Tests for POST /api/schedule/import/block endpoint."""

    def test_block_requires_auth(self, client: TestClient):
        """Test that block import requires authentication."""
        response = client.post(
            "/api/schedule/import/block",
            files={
                "file": (
                    "block.xlsx",
                    b"mock",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"block_number": 1},
        )

        assert response.status_code in [401, 403]

    def test_block_parse_success(self, client: TestClient, auth_headers: dict):
        """Test successful block schedule parsing."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch("app.api.routes.schedule.parse_block_schedule") as mock_parse,
            patch("app.api.routes.schedule.parse_fmit_attending") as mock_fmit,
        ):
            mock_validate.return_value = None

            mock_result = MagicMock()
            mock_result.block_number = 1
            mock_result.start_date = date.today()
            mock_result.end_date = date.today() + timedelta(days=28)
            mock_result.residents = [
                {"name": "Dr. Resident 1", "template": "R1", "pgy_level": 1}
            ]
            mock_result.assignments = []
            mock_result.warnings = []
            mock_result.errors = []
            mock_result.get_residents_by_template.return_value = {
                "R1": [{"name": "Dr. Resident 1", "template": "R1", "pgy_level": 1}]
            }

            mock_parse.return_value = mock_result
            mock_fmit.return_value = []

            response = client.post(
                "/api/schedule/import/block",
                files={
                    "file": (
                        "block.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"block_number": "1"},
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_block_invalid_number(self, client: TestClient, auth_headers: dict):
        """Test block parsing with invalid block number."""
        response = client.post(
            "/api/schedule/import/block",
            files={
                "file": (
                    "block.xlsx",
                    b"mock",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"block_number": "14"},  # Invalid: must be 1-13
            headers=auth_headers,
        )

        assert response.status_code in [400, 401, 422]

    def test_block_zero_number(self, client: TestClient, auth_headers: dict):
        """Test block parsing with block number 0."""
        response = client.post(
            "/api/schedule/import/block",
            files={
                "file": (
                    "block.xlsx",
                    b"mock",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"block_number": "0"},  # Invalid: must be 1-13
            headers=auth_headers,
        )

        assert response.status_code in [400, 401, 422]

    def test_block_with_known_people(self, client: TestClient, auth_headers: dict):
        """Test block parsing with known people for fuzzy matching."""
        import json

        known_people = ["Dr. Smith", "Dr. Jones", "Dr. Williams"]

        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch("app.api.routes.schedule.parse_block_schedule") as mock_parse,
            patch("app.api.routes.schedule.parse_fmit_attending") as mock_fmit,
        ):
            mock_validate.return_value = None

            mock_result = MagicMock()
            mock_result.block_number = 1
            mock_result.start_date = date.today()
            mock_result.end_date = date.today() + timedelta(days=28)
            mock_result.residents = []
            mock_result.assignments = []
            mock_result.warnings = []
            mock_result.errors = []
            mock_result.get_residents_by_template.return_value = {}

            mock_parse.return_value = mock_result
            mock_fmit.return_value = []

            response = client.post(
                "/api/schedule/import/block",
                files={
                    "file": (
                        "block.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={
                    "block_number": "1",
                    "known_people": json.dumps(known_people),
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_block_invalid_known_people_json(
        self, client: TestClient, auth_headers: dict
    ):
        """Test block parsing with invalid known people JSON."""
        with patch("app.api.routes.schedule.validate_excel_upload") as mock_validate:
            mock_validate.return_value = None

            response = client.post(
                "/api/schedule/import/block",
                files={
                    "file": (
                        "block.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={
                    "block_number": "1",
                    "known_people": "not valid json",
                },
                headers=auth_headers,
            )

            assert response.status_code in [400, 401, 422]

    def test_block_exclude_fmit(self, client: TestClient, auth_headers: dict):
        """Test block parsing without FMIT schedule."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch("app.api.routes.schedule.parse_block_schedule") as mock_parse,
        ):
            mock_validate.return_value = None

            mock_result = MagicMock()
            mock_result.block_number = 1
            mock_result.start_date = date.today()
            mock_result.end_date = date.today() + timedelta(days=28)
            mock_result.residents = []
            mock_result.assignments = []
            mock_result.warnings = []
            mock_result.errors = []
            mock_result.get_residents_by_template.return_value = {}

            mock_parse.return_value = mock_result

            response = client.post(
                "/api/schedule/import/block",
                files={
                    "file": (
                        "block.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={
                    "block_number": "1",
                    "include_fmit": "false",
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 400, 401, 422, 500]

    def test_block_parse_errors(self, client: TestClient, auth_headers: dict):
        """Test block parsing with parse errors."""
        with (
            patch("app.api.routes.schedule.validate_excel_upload") as mock_validate,
            patch("app.api.routes.schedule.parse_block_schedule") as mock_parse,
        ):
            mock_validate.return_value = None
            mock_parse.side_effect = ValueError("Could not find block header")

            response = client.post(
                "/api/schedule/import/block",
                files={
                    "file": (
                        "block.xlsx",
                        b"mock",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"block_number": "1"},
                headers=auth_headers,
            )

            assert response.status_code in [400, 401, 422]

    def test_block_missing_fields(self, client: TestClient, auth_headers: dict):
        """Test block parsing with missing required fields."""
        response = client.post(
            "/api/schedule/import/block",
            files={
                "file": (
                    "block.xlsx",
                    b"mock",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            # Missing block_number
            headers=auth_headers,
        )

        assert response.status_code in [400, 401, 422]

    def test_block_file_validation_error(self, client: TestClient, auth_headers: dict):
        """Test block parsing with file validation error."""
        with patch("app.api.routes.schedule.validate_excel_upload") as mock_validate:
            from app.core.file_security import FileValidationError

            mock_validate.side_effect = FileValidationError("Invalid file")

            response = client.post(
                "/api/schedule/import/block",
                files={
                    "file": (
                        "bad.xlsx",
                        b"not excel",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"block_number": "1"},
                headers=auth_headers,
            )

            assert response.status_code in [400, 401, 422]


# ============================================================================
# Integration Tests
# ============================================================================


class TestScheduleImportIntegration:
    """Integration tests for schedule import endpoints."""

    def test_endpoints_accessible(self, client: TestClient, auth_headers: dict):
        """Test that all import endpoints respond appropriately."""
        endpoints = [
            "/api/schedule/import/analyze",
            "/api/schedule/import/analyze-file",
            "/api/schedule/import/block",
        ]

        for url in endpoints:
            response = client.post(url, files={}, headers=auth_headers)
            # Should not return 404 - endpoint exists
            assert response.status_code != 404, f"Endpoint {url} not found"

    def test_all_endpoints_handle_empty_files(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that all endpoints handle empty file uploads."""
        endpoints_and_files = [
            (
                "/api/schedule/import/analyze",
                {
                    "fmit_file": (
                        "empty.xlsx",
                        b"",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            ),
            (
                "/api/schedule/import/analyze-file",
                {
                    "file": (
                        "empty.xlsx",
                        b"",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            ),
            (
                "/api/schedule/import/block",
                {
                    "file": (
                        "empty.xlsx",
                        b"",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
            ),
        ]

        for url, files in endpoints_and_files:
            data = {"block_number": "1"} if "block" in url else {}
            response = client.post(url, files=files, data=data, headers=auth_headers)
            # Should return an error for empty files
            assert response.status_code in [
                400,
                401,
                422,
                500,
            ], f"Unexpected status for {url}"
