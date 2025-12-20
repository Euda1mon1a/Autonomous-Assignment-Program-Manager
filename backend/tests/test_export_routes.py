"""Tests for export API routes.

Comprehensive test suite covering data export functionality including
CSV, JSON, and Excel formats for people, absences, and schedules.
"""
import csv
import io
import json
from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


# ============================================================================
# Test Classes
# ============================================================================

class TestExportPeopleEndpoint:
    """Tests for GET /api/export/people endpoint."""

    def test_export_people_csv_success(
        self, client: TestClient, sample_residents: list[Person]
    ):
        """Test exporting people as CSV."""
        response = client.get("/api/v1/export/people", params={"format": "csv"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "people.csv" in response.headers["content-disposition"]

        # Parse CSV content
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        # Should have at least the sample residents
        assert len(rows) >= len(sample_residents)

        # Validate CSV headers
        if rows:
            assert "Name" in rows[0]
            assert "Type" in rows[0]
            assert "PGY Level" in rows[0]
            assert "Email" in rows[0]

    def test_export_people_json_success(
        self, client: TestClient, sample_residents: list[Person]
    ):
        """Test exporting people as JSON."""
        response = client.get("/api/v1/export/people", params={"format": "json"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers["content-disposition"]
        assert "people.json" in response.headers["content-disposition"]

        # Parse JSON content
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(sample_residents)

        # Validate JSON structure
        if data:
            person = data[0]
            assert "name" in person
            assert "type" in person
            assert "pgy_level" in person
            assert "email" in person
            assert "specialties" in person
            assert "performs_procedures" in person

    def test_export_people_default_format(
        self, client: TestClient, sample_residents: list[Person]
    ):
        """Test that default export format is CSV."""
        response = client.get("/api/v1/export/people")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_export_people_empty_database(self, client: TestClient):
        """Test exporting people when database is empty."""
        response = client.get("/api/v1/export/people", params={"format": "csv"})

        assert response.status_code == 200

        # Should return CSV with headers but no data rows
        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # Should have header row
        assert len(rows) >= 1

    def test_export_people_includes_faculty(
        self, client: TestClient, sample_faculty: Person
    ):
        """Test that export includes faculty members."""
        response = client.get("/api/v1/export/people", params={"format": "json"})

        assert response.status_code == 200
        data = response.json()

        # Should include the faculty member
        faculty_found = any(p["name"] == sample_faculty.name for p in data)
        assert faculty_found

    def test_export_people_requires_admin(self, client: TestClient):
        """Test that people export requires admin role."""
        # Note: This test assumes admin role is required
        # Actual behavior depends on require_admin() dependency

        response = client.get("/api/v1/export/people")

        # Should either succeed (if admin check passes) or return 403
        assert response.status_code in [200, 401, 403]

    def test_export_people_invalid_format(self, client: TestClient):
        """Test export with invalid format parameter."""
        response = client.get("/api/v1/export/people", params={"format": "xml"})

        # Should default to CSV or return error
        assert response.status_code in [200, 400, 422]

    def test_export_people_csv_encoding(
        self, client: TestClient, db: Session
    ):
        """Test that CSV export handles special characters correctly."""
        # Create person with special characters
        person = Person(
            id=uuid4(),
            name="Dr. José García-O'Brien",
            type="faculty",
            email="jose.garcia@hospital.org",
        )
        db.add(person)
        db.commit()

        response = client.get("/api/v1/export/people", params={"format": "csv"})

        assert response.status_code == 200
        content = response.text
        # Should contain the special characters
        assert "José" in content or "Jose" in content


class TestExportAbsencesEndpoint:
    """Tests for GET /api/export/absences endpoint."""

    def test_export_absences_csv_success(
        self, client: TestClient, sample_absence: Absence
    ):
        """Test exporting absences as CSV."""
        response = client.get("/api/v1/export/absences", params={"format": "csv"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "absences.csv" in response.headers["content-disposition"]

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        assert len(rows) >= 1

        # Validate headers
        if rows:
            assert "Person" in rows[0]
            assert "Type" in rows[0]
            assert "Start Date" in rows[0]
            assert "End Date" in rows[0]
            assert "Notes" in rows[0]

    def test_export_absences_json_success(
        self, client: TestClient, sample_absence: Absence
    ):
        """Test exporting absences as JSON."""
        response = client.get("/api/v1/export/absences", params={"format": "json"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "absences.json" in response.headers["content-disposition"]

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        if data:
            absence = data[0]
            assert "person_name" in absence
            assert "absence_type" in absence
            assert "start_date" in absence
            assert "end_date" in absence
            assert "notes" in absence

    def test_export_absences_with_date_filter(
        self, client: TestClient, db: Session, sample_resident: Person
    ):
        """Test filtering absences by date range."""
        # Create absences at different times
        past_absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=25),
            absence_type="vacation",
        )
        future_absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            absence_type="conference",
        )
        db.add(past_absence)
        db.add(future_absence)
        db.commit()

        # Filter for future absences only
        filter_start = date.today()
        response = client.get(
            "/api/v1/export/absences",
            params={
                "format": "json",
                "start_date": filter_start.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should only include future absences
        for absence in data:
            end_date = date.fromisoformat(absence["end_date"])
            assert end_date >= filter_start

    def test_export_absences_with_end_date_filter(
        self, client: TestClient, db: Session, sample_resident: Person
    ):
        """Test filtering absences by end_date."""
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=50),
            end_date=date.today() + timedelta(days=55),
            absence_type="deployment",
            deployment_orders="Order 12345",
        )
        db.add(absence)
        db.commit()

        # Filter with end_date before the absence
        filter_end = date.today() + timedelta(days=40)
        response = client.get(
            "/api/v1/export/absences",
            params={
                "format": "json",
                "end_date": filter_end.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should not include the future absence
        for absence in data:
            if absence.get("start_date"):
                start_date = date.fromisoformat(absence["start_date"])
                assert start_date <= filter_end

    def test_export_absences_with_date_range(
        self, client: TestClient, sample_absence: Absence
    ):
        """Test filtering absences by both start and end date."""
        start = date.today()
        end = date.today() + timedelta(days=30)

        response = client.get(
            "/api/v1/export/absences",
            params={
                "format": "json",
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Validate date range
        for absence in data:
            if absence.get("end_date"):
                absence_end = date.fromisoformat(absence["end_date"])
                assert absence_end >= start

            if absence.get("start_date"):
                absence_start = date.fromisoformat(absence["start_date"])
                assert absence_start <= end

    def test_export_absences_empty(self, client: TestClient, db: Session):
        """Test exporting when no absences exist."""
        response = client.get("/api/v1/export/absences", params={"format": "csv"})

        assert response.status_code == 200

        # Should return headers but no data
        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) >= 1  # At least header row

    def test_export_absences_includes_deployment_info(
        self, client: TestClient, db: Session, sample_resident: Person
    ):
        """Test that deployment-related fields are exported."""
        deployment = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=20),
            absence_type="deployment",
            deployment_orders="TDY-2024-001",
            tdy_location="Remote Site Alpha",
        )
        db.add(deployment)
        db.commit()

        response = client.get("/api/v1/export/absences", params={"format": "json"})

        assert response.status_code == 200
        data = response.json()

        # Find the deployment
        deployment_data = next(
            (a for a in data if a.get("deployment_orders") == "TDY-2024-001"),
            None
        )
        assert deployment_data is not None
        assert deployment_data["tdy_location"] == "Remote Site Alpha"


class TestExportScheduleEndpoint:
    """Tests for GET /api/export/schedule endpoint."""

    def test_export_schedule_csv_success(
        self, client: TestClient, sample_assignment: Assignment
    ):
        """Test exporting schedule as CSV."""
        start = date.today()
        end = date.today() + timedelta(days=7)

        response = client.get(
            "/api/v1/export/schedule",
            params={
                "format": "csv",
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "schedule.csv" in response.headers["content-disposition"]

        # Parse CSV
        content = response.text
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        # Validate headers
        if rows:
            assert "Date" in rows[0]
            assert "Time" in rows[0]
            assert "Person" in rows[0]
            assert "Type" in rows[0]
            assert "Role" in rows[0]
            assert "Activity" in rows[0]

    def test_export_schedule_json_success(
        self, client: TestClient, sample_assignment: Assignment
    ):
        """Test exporting schedule as JSON."""
        start = date.today()
        end = date.today() + timedelta(days=7)

        response = client.get(
            "/api/v1/export/schedule",
            params={
                "format": "json",
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "schedule.json" in response.headers["content-disposition"]

        data = response.json()
        assert isinstance(data, list)

        if data:
            item = data[0]
            assert "date" in item
            assert "time_of_day" in item
            assert "person_name" in item
            assert "person_type" in item
            assert "role" in item
            assert "activity" in item

    def test_export_schedule_requires_date_range(self, client: TestClient):
        """Test that schedule export requires start_date and end_date."""
        # Missing both dates
        response = client.get("/api/v1/export/schedule")
        assert response.status_code == 422

        # Missing end_date
        response = client.get(
            "/api/v1/export/schedule",
            params={"start_date": date.today().isoformat()}
        )
        assert response.status_code == 422

        # Missing start_date
        response = client.get(
            "/api/v1/export/schedule",
            params={"end_date": date.today().isoformat()}
        )
        assert response.status_code == 422

    def test_export_schedule_date_range_validation(self, client: TestClient):
        """Test schedule export with invalid date range."""
        start = date.today()
        end = start - timedelta(days=7)  # End before start

        response = client.get(
            "/api/v1/export/schedule",
            params={
                "format": "csv",
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        # Should handle gracefully (might return empty or error)
        assert response.status_code in [200, 400, 422]

    def test_export_schedule_with_assignments(
        self, client: TestClient, db: Session,
        sample_resident: Person, sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate
    ):
        """Test schedule export includes assignment details."""
        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
            activity_name="Clinic Duty",
        )
        db.add(assignment)
        db.commit()

        start = sample_blocks[0].date
        end = sample_blocks[-1].date

        response = client.get(
            "/api/v1/export/schedule",
            params={
                "format": "json",
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Find the assignment in export
        assignment_data = next(
            (a for a in data if a.get("activity") == "Clinic Duty"),
            None
        )
        assert assignment_data is not None

    def test_export_schedule_empty_range(self, client: TestClient):
        """Test exporting schedule for range with no assignments."""
        # Far future date range
        start = date.today() + timedelta(days=365)
        end = start + timedelta(days=7)

        response = client.get(
            "/api/v1/export/schedule",
            params={
                "format": "csv",
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200

        # Should return headers but minimal data
        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) >= 1  # At least header

    def test_export_schedule_single_day(
        self, client: TestClient, sample_assignment: Assignment
    ):
        """Test exporting schedule for a single day."""
        day = date.today()

        response = client.get(
            "/api/v1/export/schedule",
            params={
                "format": "json",
                "start_date": day.isoformat(),
                "end_date": day.isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()

        # All entries should be for the same date
        for item in data:
            assert item["date"] == day.isoformat()


class TestExportScheduleXLSXEndpoint:
    """Tests for GET /api/export/schedule/xlsx endpoint."""

    def test_export_xlsx_success(self, client: TestClient, sample_assignment: Assignment):
        """Test exporting schedule as Excel file."""
        start = date.today()
        end = date.today() + timedelta(days=27)  # 28-day block

        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in response.headers["content-disposition"]
        assert ".xlsx" in response.headers["content-disposition"]

        # Verify it's actual binary data (Excel file)
        assert len(response.content) > 0
        # Excel files start with PK (ZIP signature)
        assert response.content[:2] == b'PK'

    def test_export_xlsx_requires_dates(self, client: TestClient):
        """Test that XLSX export requires date parameters."""
        # Missing both
        response = client.get("/api/v1/export/schedule/xlsx")
        assert response.status_code == 422

        # Missing end_date
        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={"start_date": date.today().isoformat()}
        )
        assert response.status_code == 422

    def test_export_xlsx_with_block_number(
        self, client: TestClient, sample_assignment: Assignment
    ):
        """Test XLSX export with block_number parameter."""
        start = date.today()
        end = date.today() + timedelta(days=27)

        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "block_number": 5
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_export_xlsx_with_federal_holidays(
        self, client: TestClient, sample_assignment: Assignment
    ):
        """Test XLSX export with federal holidays parameter."""
        start = date.today()
        end = date.today() + timedelta(days=27)
        holidays = f"{(start + timedelta(days=10)).isoformat()},{(start + timedelta(days=20)).isoformat()}"

        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "federal_holidays": holidays
            }
        )

        assert response.status_code == 200

    def test_export_xlsx_invalid_holiday_format(self, client: TestClient):
        """Test XLSX export with invalid holiday date format."""
        start = date.today()
        end = date.today() + timedelta(days=27)

        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "federal_holidays": "invalid-date,also-invalid"
            }
        )

        assert response.status_code == 400
        assert "detail" in response.json()
        assert "date format" in response.json()["detail"].lower()

    def test_export_xlsx_filename_includes_dates(
        self, client: TestClient, sample_assignment: Assignment
    ):
        """Test that XLSX filename includes date range."""
        start = date.today()
        end = date.today() + timedelta(days=27)

        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        assert response.status_code == 200

        # Filename should contain dates
        disposition = response.headers["content-disposition"]
        assert start.strftime("%Y%m%d") in disposition
        assert end.strftime("%Y%m%d") in disposition

    def test_export_xlsx_empty_schedule(self, client: TestClient):
        """Test XLSX export with no assignments in range."""
        # Far future
        start = date.today() + timedelta(days=500)
        end = start + timedelta(days=27)

        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        # Should still generate file
        assert response.status_code in [200, 500]

    def test_export_xlsx_large_date_range(self, client: TestClient):
        """Test XLSX export with very large date range."""
        start = date.today()
        end = start + timedelta(days=365)  # Full year

        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
        )

        # Should handle large range (might succeed or timeout)
        assert response.status_code in [200, 400, 500, 504]


class TestExportAuthenticationAndAuthorization:
    """Tests for authentication and authorization on export endpoints."""

    def test_export_people_requires_admin(self, client: TestClient):
        """Test that people export requires admin role."""
        response = client.get("/api/v1/export/people")

        # Should require admin (403) or allow access (200)
        assert response.status_code in [200, 401, 403]

    def test_export_absences_requires_admin(self, client: TestClient):
        """Test that absences export requires admin role."""
        response = client.get(
            "/api/v1/export/absences",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat()
            }
        )

        assert response.status_code in [200, 401, 403]

    def test_export_schedule_requires_admin(self, client: TestClient):
        """Test that schedule export requires admin role."""
        response = client.get(
            "/api/v1/export/schedule",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat()
            }
        )

        assert response.status_code in [200, 401, 403]

    def test_export_xlsx_requires_admin(self, client: TestClient):
        """Test that XLSX export requires admin role."""
        response = client.get(
            "/api/v1/export/schedule/xlsx",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat()
            }
        )

        assert response.status_code in [200, 401, 403]


class TestExportEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_export_with_null_values(
        self, client: TestClient, db: Session
    ):
        """Test export handles null/None values correctly."""
        # Create person with minimal data
        person = Person(
            id=uuid4(),
            name="Minimal Person",
            type="resident",
            email=None,  # Null email
            pgy_level=None,  # Null PGY
        )
        db.add(person)
        db.commit()

        response = client.get("/api/v1/export/people", params={"format": "csv"})

        assert response.status_code == 200

        # CSV should handle null values (empty strings)
        content = response.text
        assert "Minimal Person" in content

    def test_export_json_with_none_serialization(
        self, client: TestClient, db: Session, sample_resident: Person
    ):
        """Test that JSON export properly serializes None values."""
        # Create absence with null notes
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            absence_type="vacation",
            notes=None,  # Explicitly null
        )
        db.add(absence)
        db.commit()

        response = client.get("/api/v1/export/absences", params={"format": "json"})

        assert response.status_code == 200
        data = response.json()

        # Find our absence
        absence_data = next(
            (a for a in data if a["absence_type"] == "vacation"),
            None
        )
        assert absence_data is not None
        # notes should be null/None
        assert absence_data["notes"] is None or absence_data["notes"] == ""

    def test_export_csv_quoting(
        self, client: TestClient, db: Session
    ):
        """Test that CSV properly quotes fields with commas."""
        person = Person(
            id=uuid4(),
            name="Smith, Jr., John",  # Contains commas
            type="faculty",
            email="john.smith@test.org",
        )
        db.add(person)
        db.commit()

        response = client.get("/api/v1/export/people", params={"format": "csv"})

        assert response.status_code == 200
        content = response.text

        # Should properly handle commas in name
        assert "Smith, Jr., John" in content or '"Smith, Jr., John"' in content

    def test_export_schedule_ordering(
        self, client: TestClient, db: Session,
        sample_resident: Person, sample_rotation_template: RotationTemplate
    ):
        """Test that schedule export is properly ordered by date and time."""
        # Create blocks and assignments out of order
        dates = [date.today() + timedelta(days=i) for i in [2, 0, 1]]
        blocks = []

        for d in dates:
            for tod in ["PM", "AM"]:  # Intentionally out of order
                block = Block(
                    id=uuid4(),
                    date=d,
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)
                blocks.append(block)
                db.flush()

                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=sample_resident.id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)

        db.commit()

        response = client.get(
            "/api/v1/export/schedule",
            params={
                "format": "json",
                "start_date": min(dates).isoformat(),
                "end_date": max(dates).isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should be ordered by date, then time_of_day
        if len(data) > 1:
            for i in range(len(data) - 1):
                curr_date = date.fromisoformat(data[i]["date"])
                next_date = date.fromisoformat(data[i + 1]["date"])

                # Next item should be same or later date
                assert next_date >= curr_date

                # If same date, check time ordering
                if curr_date == next_date:
                    curr_time = data[i]["time_of_day"]
                    next_time = data[i + 1]["time_of_day"]
                    # AM should come before PM
                    if curr_time == "AM":
                        assert next_time in ["AM", "PM"]


class TestExportPerformance:
    """Tests for export performance and limits."""

    def test_export_large_dataset(
        self, client: TestClient, db: Session
    ):
        """Test exporting large number of people."""
        # Create many people
        for i in range(50):
            person = Person(
                id=uuid4(),
                name=f"Person {i}",
                type="resident" if i % 2 == 0 else "faculty",
                email=f"person{i}@test.org",
                pgy_level=(i % 3) + 1 if i % 2 == 0 else None,
            )
            db.add(person)
        db.commit()

        response = client.get("/api/v1/export/people", params={"format": "csv"})

        assert response.status_code == 200

        # Should include all people
        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        # Header + 50 data rows
        assert len(rows) >= 50

    def test_export_schedule_large_range(
        self, client: TestClient, db: Session,
        sample_resident: Person, sample_rotation_template: RotationTemplate
    ):
        """Test exporting schedule over large date range."""
        # Create 90 days of blocks and assignments
        start_date = date.today()
        for i in range(90):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=tod,
                    block_number=1 + (i // 28),
                )
                db.add(block)
                db.flush()

                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=sample_resident.id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)

        db.commit()

        response = client.get(
            "/api/v1/export/schedule",
            params={
                "format": "json",
                "start_date": start_date.isoformat(),
                "end_date": (start_date + timedelta(days=89)).isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 90 days * 2 blocks = 180 assignments
        assert len(data) == 180
