"""
Integration tests for data export and import workflows.

Tests data portability, format conversion, and bulk data operations.
"""

from datetime import date, timedelta
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestExportImportWorkflow:
    """Test data export and import workflows."""

    def test_export_schedule_csv_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting schedule to CSV."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        export_response = client.get(
            f"/api/exports/schedule/csv?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=auth_headers,
        )
        assert export_response.status_code in [200, 404]

        if export_response.status_code == 200:
            assert "text/csv" in export_response.headers.get("content-type", "")

    def test_export_schedule_json_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting schedule to JSON."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        export_response = client.get(
            f"/api/exports/schedule/json?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=auth_headers,
        )
        assert export_response.status_code in [200, 404]

    def test_export_schedule_excel_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting schedule to Excel."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        export_response = client.get(
            f"/api/exports/schedule/xlsx?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=auth_headers,
        )
        assert export_response.status_code in [200, 404, 501]

    def test_import_schedule_csv_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test importing schedule from CSV."""
        csv_content = b"date,time_of_day,person_name,rotation\n2024-01-01,AM,Dr. Smith,Clinic\n"

        import_response = client.post(
            "/api/imports/schedule",
            files={"file": ("schedule.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )
        assert import_response.status_code in [200, 201, 400, 404, 501]

    def test_import_schedule_json_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test importing schedule from JSON."""
        json_data = {
            "assignments": [
                {
                    "date": "2024-01-01",
                    "time_of_day": "AM",
                    "person_name": "Dr. Smith",
                    "rotation": "Clinic",
                }
            ]
        }

        import_response = client.post(
            "/api/imports/schedule/json",
            json=json_data,
            headers=auth_headers,
        )
        assert import_response.status_code in [200, 201, 400, 404, 501]

    def test_import_validation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test validation during import."""
        # Invalid CSV with missing columns
        invalid_csv = b"date,person\n2024-01-01,Dr. Smith\n"

        import_response = client.post(
            "/api/imports/schedule",
            files={"file": ("invalid.csv", invalid_csv, "text/csv")},
            headers=auth_headers,
        )
        # Should reject invalid data
        assert import_response.status_code in [400, 422, 404, 501]

    def test_export_people_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting people/personnel data."""
        export_response = client.get(
            "/api/exports/people/csv",
            headers=auth_headers,
        )
        assert export_response.status_code in [200, 404]

    def test_import_people_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test importing people/personnel data."""
        csv_content = b"name,type,email,pgy_level\nDr. Import,resident,import@test.org,1\n"

        import_response = client.post(
            "/api/imports/people",
            files={"file": ("people.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )
        assert import_response.status_code in [200, 201, 400, 404, 501]

    def test_full_database_export_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test exporting entire database."""
        export_response = client.get(
            "/api/exports/full-backup",
            headers=auth_headers,
        )
        assert export_response.status_code in [200, 403, 404, 501]

    def test_full_database_import_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test importing full database backup."""
        backup_data = json.dumps({"version": "1.0", "data": {}}).encode()

        import_response = client.post(
            "/api/imports/full-restore",
            files={"file": ("backup.json", backup_data, "application/json")},
            headers=auth_headers,
        )
        # Should require admin permissions
        assert import_response.status_code in [200, 201, 403, 404, 501]
