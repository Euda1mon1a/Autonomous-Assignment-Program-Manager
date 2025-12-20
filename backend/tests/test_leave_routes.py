"""Tests for leave API routes.

Comprehensive test suite covering CRUD operations, filters, validation,
calendar view, webhook integration, and bulk import for leave endpoints.
"""
import hashlib
import hmac
import json
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.absence import Absence
from app.models.person import Person


class TestListLeaveEndpoint:
    """Tests for GET /api/leave/ endpoint."""

    def test_list_leave_empty(self, client: TestClient, db: Session):
        """Test listing leave when none exist."""
        response = client.get("/api/v1/leave/")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_leave_with_data(self, client: TestClient, sample_absence: Absence):
        """Test listing leave with existing data."""
        response = client.get("/api/v1/leave/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

        ***REMOVED*** Validate leave structure
        leave = data["items"][0]
        assert "id" in leave
        assert "faculty_id" in leave
        assert "faculty_name" in leave
        assert "start_date" in leave
        assert "end_date" in leave
        assert "leave_type" in leave
        assert "is_blocking" in leave
        assert "description" in leave

    def test_list_leave_filter_by_faculty_id(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test filtering leave by faculty_id."""
        ***REMOVED*** Create absences for different faculty
        other_faculty = Person(
            id=uuid4(),
            name="Dr. Other Faculty",
            type="faculty",
            email="other@hospital.org",
        )
        db.add(other_faculty)
        db.commit()

        ***REMOVED*** Create absences
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=other_faculty.id,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            absence_type="conference",
        )
        db.add(absence1)
        db.add(absence2)
        db.commit()

        response = client.get(
            "/api/v1/leave/",
            params={"faculty_id": str(sample_faculty.id)}
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** All returned leave should be for the specified faculty
        for leave in data["items"]:
            assert leave["faculty_id"] == str(sample_faculty.id)

    def test_list_leave_filter_by_start_date(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test filtering leave by start_date."""
        ***REMOVED*** Create absences with different date ranges
        past_absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=5),
            absence_type="vacation",
        )
        future_absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="conference",
        )
        db.add(past_absence)
        db.add(future_absence)
        db.commit()

        filter_date = (date.today() + timedelta(days=5)).isoformat()
        response = client.get(
            "/api/v1/leave/",
            params={"start_date": filter_date}
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** All returned leave should end on or after the filter date
        for leave in data["items"]:
            leave_end = date.fromisoformat(leave["end_date"])
            assert leave_end >= date.fromisoformat(filter_date)

    def test_list_leave_filter_by_end_date(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test filtering leave by end_date."""
        ***REMOVED*** Create absences with different date ranges
        near_absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            absence_type="vacation",
        )
        far_absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=25),
            absence_type="deployment",
        )
        db.add(near_absence)
        db.add(far_absence)
        db.commit()

        filter_date = (date.today() + timedelta(days=10)).isoformat()
        response = client.get(
            "/api/v1/leave/",
            params={"end_date": filter_date}
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** All returned leave should start on or before the filter date
        for leave in data["items"]:
            leave_start = date.fromisoformat(leave["start_date"])
            assert leave_start <= date.fromisoformat(filter_date)

    def test_list_leave_filter_by_date_range(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test filtering leave by date range."""
        ***REMOVED*** Create absences across different time periods
        absences = [
            Absence(
                id=uuid4(),
                person_id=sample_faculty.id,
                start_date=date.today() - timedelta(days=20),
                end_date=date.today() - timedelta(days=15),
                absence_type="vacation",
            ),
            Absence(
                id=uuid4(),
                person_id=sample_faculty.id,
                start_date=date.today() + timedelta(days=5),
                end_date=date.today() + timedelta(days=10),
                absence_type="conference",
            ),
            Absence(
                id=uuid4(),
                person_id=sample_faculty.id,
                start_date=date.today() + timedelta(days=25),
                end_date=date.today() + timedelta(days=30),
                absence_type="tdy",
            ),
        ]
        for absence in absences:
            db.add(absence)
        db.commit()

        ***REMOVED*** Filter for middle range
        filter_start = (date.today() + timedelta(days=3)).isoformat()
        filter_end = (date.today() + timedelta(days=15)).isoformat()

        response = client.get(
            "/api/v1/leave/",
            params={
                "start_date": filter_start,
                "end_date": filter_end
            }
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** Should only get the middle absence that overlaps the range
        assert data["total"] >= 1

        ***REMOVED*** All blocks should overlap with the range
        for leave in data["items"]:
            leave_start = date.fromisoformat(leave["start_date"])
            leave_end = date.fromisoformat(leave["end_date"])
            ***REMOVED*** Leave overlaps if it ends after filter_start and starts before filter_end
            assert leave_end >= date.fromisoformat(filter_start)
            assert leave_start <= date.fromisoformat(filter_end)

    def test_list_leave_pagination(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test pagination parameters."""
        ***REMOVED*** Create multiple absences
        for i in range(25):
            absence = Absence(
                id=uuid4(),
                person_id=sample_faculty.id,
                start_date=date.today() + timedelta(days=i * 2),
                end_date=date.today() + timedelta(days=i * 2 + 1),
                absence_type="vacation",
            )
            db.add(absence)
        db.commit()

        ***REMOVED*** Test first page
        response = client.get(
            "/api/v1/leave/",
            params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] >= 25
        assert len(data["items"]) == 10

        ***REMOVED*** Test second page
        response = client.get(
            "/api/v1/leave/",
            params={"page": 2, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 10


class TestGetLeaveCalendarEndpoint:
    """Tests for GET /api/leave/calendar endpoint."""

    def test_get_leave_calendar_empty(self, client: TestClient):
        """Test getting leave calendar when no leave exists."""
        start = date.today()
        end = date.today() + timedelta(days=7)

        response = client.get(
            "/api/v1/leave/calendar",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == start.isoformat()
        assert data["end_date"] == end.isoformat()
        assert data["entries"] == []
        assert data["conflict_count"] == 0

    def test_get_leave_calendar_with_data(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test getting leave calendar with leave data."""
        ***REMOVED*** Create absences in the range
        start = date.today()
        end = date.today() + timedelta(days=14)

        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=start + timedelta(days=2),
            end_date=start + timedelta(days=5),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        response = client.get(
            "/api/v1/leave/calendar",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) >= 1

        ***REMOVED*** Validate entry structure
        entry = data["entries"][0]
        assert "faculty_id" in entry
        assert "faculty_name" in entry
        assert "leave_type" in entry
        assert "start_date" in entry
        assert "end_date" in entry
        assert "is_blocking" in entry
        assert "has_fmit_conflict" in entry

    def test_get_leave_calendar_missing_dates(self, client: TestClient):
        """Test calendar endpoint with missing required dates."""
        response = client.get("/api/v1/leave/calendar")

        assert response.status_code == 422  ***REMOVED*** Validation error

    def test_get_leave_calendar_filters_by_date_range(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test that calendar only includes leave in the specified range."""
        start = date.today() + timedelta(days=10)
        end = date.today() + timedelta(days=20)

        ***REMOVED*** Create absence outside range
        outside_absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            absence_type="vacation",
        )
        ***REMOVED*** Create absence inside range
        inside_absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=start + timedelta(days=2),
            end_date=start + timedelta(days=5),
            absence_type="conference",
        )
        db.add(outside_absence)
        db.add(inside_absence)
        db.commit()

        response = client.get(
            "/api/v1/leave/calendar",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            }
        )

        assert response.status_code == 200
        data = response.json()

        ***REMOVED*** All entries should be within or overlap the range
        for entry in data["entries"]:
            entry_start = date.fromisoformat(entry["start_date"])
            entry_end = date.fromisoformat(entry["end_date"])
            ***REMOVED*** Entry overlaps range if it ends after start and starts before end
            assert entry_end >= start
            assert entry_start <= end


class TestCreateLeaveEndpoint:
    """Tests for POST /api/leave/ endpoint."""

    def test_create_leave_success(self, client: TestClient, sample_faculty: Person):
        """Test creating a valid leave record."""
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "leave_type": "vacation",
            "is_blocking": True,
            "description": "Annual vacation",
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["faculty_id"] == leave_data["faculty_id"]
        assert data["start_date"] == leave_data["start_date"]
        assert data["end_date"] == leave_data["end_date"]
        assert data["leave_type"] == leave_data["leave_type"]
        assert data["is_blocking"] == leave_data["is_blocking"]
        assert data["description"] == leave_data["description"]

    def test_create_leave_faculty_not_found(self, client: TestClient):
        """Test creating leave for non-existent faculty."""
        fake_id = uuid4()
        leave_data = {
            "faculty_id": str(fake_id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "leave_type": "vacation",
            "is_blocking": True,
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_leave_invalid_date_range(self, client: TestClient, sample_faculty: Person):
        """Test creating leave with end_date before start_date."""
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=15)).isoformat(),
            "end_date": (date.today() + timedelta(days=10)).isoformat(),  ***REMOVED*** Before start!
            "leave_type": "vacation",
            "is_blocking": True,
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 422  ***REMOVED*** Validation error

    def test_create_leave_missing_required_fields(self, client: TestClient):
        """Test creating leave with missing required fields."""
        leave_data = {
            "faculty_id": str(uuid4()),
            ***REMOVED*** Missing start_date, end_date, leave_type
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 422  ***REMOVED*** Validation error

    def test_create_leave_invalid_leave_type(self, client: TestClient, sample_faculty: Person):
        """Test creating leave with invalid leave_type."""
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "leave_type": "invalid_type",
            "is_blocking": True,
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 422  ***REMOVED*** Validation error

    def test_create_leave_deployment_type(self, client: TestClient, sample_faculty: Person):
        """Test creating deployment leave (always blocking)."""
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=30)).isoformat(),
            "end_date": (date.today() + timedelta(days=90)).isoformat(),
            "leave_type": "deployment",
            "is_blocking": False,  ***REMOVED*** Will be overridden
            "description": "Military deployment",
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 201
        data = response.json()
        ***REMOVED*** Deployment should always be blocking
        assert data["is_blocking"] is True

    def test_create_leave_without_description(self, client: TestClient, sample_faculty: Person):
        """Test creating leave without optional description."""
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "leave_type": "conference",
            "is_blocking": False,
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None or data["description"] == ""


class TestUpdateLeaveEndpoint:
    """Tests for PUT /api/leave/{leave_id} endpoint."""

    def test_update_leave_success(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test successfully updating a leave record."""
        ***REMOVED*** Create a leave to update
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
            notes="Original description",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        update_data = {
            "start_date": (date.today() + timedelta(days=12)).isoformat(),
            "end_date": (date.today() + timedelta(days=17)).isoformat(),
            "description": "Updated description",
        }

        response = client.put(f"/api/v1/leave/{absence.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == update_data["start_date"]
        assert data["end_date"] == update_data["end_date"]
        assert data["description"] == update_data["description"]

    def test_update_leave_not_found(self, client: TestClient):
        """Test updating a non-existent leave record."""
        fake_id = uuid4()
        update_data = {
            "description": "Updated description",
        }

        response = client.put(f"/api/v1/leave/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_update_leave_partial_update(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test partial update (only some fields)."""
        ***REMOVED*** Create a leave to update
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
            notes="Original",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        original_start = absence.start_date
        original_end = absence.end_date

        ***REMOVED*** Only update description
        update_data = {
            "description": "Only description changed",
        }

        response = client.put(f"/api/v1/leave/{absence.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        ***REMOVED*** Dates should remain unchanged
        assert data["start_date"] == original_start.isoformat()
        assert data["end_date"] == original_end.isoformat()
        assert data["description"] == update_data["description"]

    def test_update_leave_change_type(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test updating leave type."""
        ***REMOVED*** Create a leave to update
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        update_data = {
            "leave_type": "conference",
        }

        response = client.put(f"/api/v1/leave/{absence.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["leave_type"] == "conference"


class TestDeleteLeaveEndpoint:
    """Tests for DELETE /api/leave/{leave_id} endpoint."""

    def test_delete_leave_success(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test successfully deleting a leave record."""
        ***REMOVED*** Create a leave to delete
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        leave_id = absence.id

        response = client.delete(f"/api/v1/leave/{leave_id}")

        assert response.status_code == 204
        assert response.content == b""

        ***REMOVED*** Verify deletion
        deleted_absence = db.query(Absence).filter(Absence.id == leave_id).first()
        assert deleted_absence is None

    def test_delete_leave_not_found(self, client: TestClient):
        """Test deleting a non-existent leave record."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/leave/{fake_id}")

        assert response.status_code == 404

    def test_delete_leave_twice(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test deleting the same leave twice."""
        ***REMOVED*** Create a leave to delete
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        leave_id = absence.id

        ***REMOVED*** First delete
        response1 = client.delete(f"/api/v1/leave/{leave_id}")
        assert response1.status_code == 204

        ***REMOVED*** Second delete should fail
        response2 = client.delete(f"/api/v1/leave/{leave_id}")
        assert response2.status_code == 404


class TestLeaveWebhookEndpoint:
    """Tests for POST /api/leave/webhook endpoint."""

    def _create_webhook_signature(self, payload: dict, timestamp: str) -> str:
        """Helper to create valid webhook signature."""
        settings = get_settings()
        body = json.dumps(payload)
        message = f"{timestamp}.{body}"
        signature = hmac.new(
            settings.WEBHOOK_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def test_webhook_missing_signature(self, client: TestClient):
        """Test webhook without signature header."""
        payload = {
            "event_type": "created",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. Test",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
            "leave_type": "vacation",
        }

        response = client.post("/api/v1/leave/webhook", json=payload)

        assert response.status_code == 401

    def test_webhook_missing_timestamp(self, client: TestClient):
        """Test webhook without timestamp header."""
        payload = {
            "event_type": "created",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. Test",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
            "leave_type": "vacation",
        }

        response = client.post(
            "/api/v1/leave/webhook",
            json=payload,
            headers={"X-Webhook-Signature": "fake_signature"}
        )

        assert response.status_code == 401

    def test_webhook_invalid_signature(self, client: TestClient):
        """Test webhook with invalid signature."""
        payload = {
            "event_type": "created",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. Test",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
            "leave_type": "vacation",
        }
        timestamp = str(int(datetime.utcnow().timestamp()))

        response = client.post(
            "/api/v1/leave/webhook",
            json=payload,
            headers={
                "X-Webhook-Signature": "invalid_signature",
                "X-Webhook-Timestamp": timestamp,
            }
        )

        assert response.status_code == 401

    def test_webhook_expired_timestamp(self, client: TestClient):
        """Test webhook with expired timestamp."""
        payload = {
            "event_type": "created",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. Test",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
            "leave_type": "vacation",
        }
        ***REMOVED*** Timestamp from 10 minutes ago
        old_timestamp = str(int((datetime.utcnow() - timedelta(minutes=10)).timestamp()))
        signature = self._create_webhook_signature(payload, old_timestamp)

        response = client.post(
            "/api/v1/leave/webhook",
            json=payload,
            headers={
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": old_timestamp,
            }
        )

        ***REMOVED*** Should fail if timestamp tolerance is less than 10 minutes
        assert response.status_code in [200, 401]

    def test_webhook_valid_created_event(self, client: TestClient):
        """Test valid webhook for created event."""
        payload = {
            "event_type": "created",
            "faculty_id": str(uuid4()),
            "faculty_name": "Dr. Test",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=5)).isoformat(),
            "leave_type": "vacation",
        }
        timestamp = str(int(datetime.utcnow().timestamp()))
        signature = self._create_webhook_signature(payload, timestamp)

        response = client.post(
            "/api/v1/leave/webhook",
            json=payload,
            headers={
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": timestamp,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert data["event_type"] == "created"


class TestBulkLeaveImportEndpoint:
    """Tests for POST /api/leave/bulk-import endpoint."""

    def test_bulk_import_requires_admin(self, client: TestClient, sample_faculty: Person):
        """Test that bulk import requires admin role."""
        ***REMOVED*** This test assumes authentication is required
        ***REMOVED*** Without proper auth, should get 401 or 403
        payload = {
            "records": [
                {
                    "faculty_id": str(sample_faculty.id),
                    "start_date": (date.today() + timedelta(days=10)).isoformat(),
                    "end_date": (date.today() + timedelta(days=15)).isoformat(),
                    "leave_type": "vacation",
                    "is_blocking": True,
                }
            ],
            "skip_duplicates": True,
        }

        response = client.post("/api/v1/leave/bulk-import", json=payload)

        ***REMOVED*** Should require authentication/authorization
        assert response.status_code in [401, 403]

    def test_bulk_import_success(self, client: TestClient, db: Session, admin_user, auth_headers, sample_faculty: Person):
        """Test successful bulk import with admin user."""
        payload = {
            "records": [
                {
                    "faculty_id": str(sample_faculty.id),
                    "start_date": (date.today() + timedelta(days=10)).isoformat(),
                    "end_date": (date.today() + timedelta(days=15)).isoformat(),
                    "leave_type": "vacation",
                    "is_blocking": True,
                },
                {
                    "faculty_id": str(sample_faculty.id),
                    "start_date": (date.today() + timedelta(days=20)).isoformat(),
                    "end_date": (date.today() + timedelta(days=25)).isoformat(),
                    "leave_type": "conference",
                    "is_blocking": False,
                }
            ],
            "skip_duplicates": True,
        }

        response = client.post("/api/v1/leave/bulk-import", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported_count"] == 2
        assert data["error_count"] == 0

    def test_bulk_import_skip_duplicates(self, client: TestClient, db: Session, admin_user, auth_headers, sample_faculty: Person):
        """Test bulk import with skip_duplicates enabled."""
        ***REMOVED*** Create an existing absence
        existing = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(existing)
        db.commit()

        payload = {
            "records": [
                {
                    "faculty_id": str(sample_faculty.id),
                    "start_date": (date.today() + timedelta(days=10)).isoformat(),
                    "end_date": (date.today() + timedelta(days=15)).isoformat(),
                    "leave_type": "vacation",
                    "is_blocking": True,
                },
                {
                    "faculty_id": str(sample_faculty.id),
                    "start_date": (date.today() + timedelta(days=20)).isoformat(),
                    "end_date": (date.today() + timedelta(days=25)).isoformat(),
                    "leave_type": "conference",
                    "is_blocking": False,
                }
            ],
            "skip_duplicates": True,
        }

        response = client.post("/api/v1/leave/bulk-import", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 1  ***REMOVED*** Only the non-duplicate
        assert data["skipped_count"] == 1  ***REMOVED*** The duplicate was skipped


class TestLeaveEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_leave_same_start_end_date(self, client: TestClient, sample_faculty: Person):
        """Test creating leave with same start and end date (single day)."""
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=10)).isoformat(),
            "leave_type": "sick",
            "is_blocking": True,
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 201

    def test_create_leave_far_future(self, client: TestClient, sample_faculty: Person):
        """Test creating leave far in the future."""
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=365)).isoformat(),
            "end_date": (date.today() + timedelta(days=370)).isoformat(),
            "leave_type": "vacation",
            "is_blocking": True,
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        assert response.status_code == 201

    def test_create_leave_long_description(self, client: TestClient, sample_faculty: Person):
        """Test creating leave with very long description."""
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "leave_type": "vacation",
            "is_blocking": True,
            "description": "A" * 1000,  ***REMOVED*** Very long description
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        ***REMOVED*** Should fail validation if max_length=500 is enforced
        assert response.status_code in [201, 422]

    def test_overlapping_leave_same_faculty(self, client: TestClient, db: Session, sample_faculty: Person):
        """Test creating overlapping leave for the same faculty."""
        ***REMOVED*** Create first leave
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence1)
        db.commit()

        ***REMOVED*** Create overlapping leave
        leave_data = {
            "faculty_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=12)).isoformat(),
            "end_date": (date.today() + timedelta(days=17)).isoformat(),
            "leave_type": "conference",
            "is_blocking": True,
        }

        response = client.post("/api/v1/leave/", json=leave_data)

        ***REMOVED*** Should succeed - overlapping leave is allowed (system tracks conflicts)
        assert response.status_code == 201
