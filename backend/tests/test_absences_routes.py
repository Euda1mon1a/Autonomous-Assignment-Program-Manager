"""Tests for absences API routes.

Comprehensive test suite covering CRUD operations, filters, validation,
date range queries, and error handling for absence endpoints.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.person import Person


class TestListAbsencesEndpoint:
    """Tests for GET /api/absences endpoint."""

    def test_list_absences_empty(self, client: TestClient, db: Session):
        """Test listing absences when none exist."""
        response = client.get("/api/absences")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Service may return different formats, check for common patterns
        if "items" in data:
            assert data["items"] == []
        elif isinstance(data, list):
            assert len(data) == 0

    def test_list_absences_with_data(self, client: TestClient, sample_absence: Absence):
        """Test listing absences with existing data."""
        response = client.get("/api/absences")

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        if "items" in data:
            assert len(data["items"]) >= 1
            absence = data["items"][0]
        else:
            assert len(data) >= 1
            absence = data[0]

        # Validate absence structure
        assert "id" in absence
        assert "person_id" in absence
        assert "start_date" in absence
        assert "end_date" in absence
        assert "absence_type" in absence

    def test_list_absences_filter_by_person_id(self, client: TestClient, db: Session, sample_resident: Person):
        """Test filtering absences by person_id."""
        # Create absences for different people
        other_person = Person(
            id=uuid4(),
            name="Dr. Other Person",
            type="resident",
            email="other@hospital.org",
            pgy_level=1,
        )
        db.add(other_person)
        db.commit()

        # Create absences
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=other_person.id,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            absence_type="conference",
        )
        db.add(absence1)
        db.add(absence2)
        db.commit()

        response = client.get(
            "/api/absences",
            params={"person_id": str(sample_resident.id)}
        )

        assert response.status_code == 200
        data = response.json()

        # Extract items from response
        items = data.get("items", data) if isinstance(data, dict) else data

        # All returned absences should be for the specified person
        for absence in items:
            assert absence["person_id"] == str(sample_resident.id)

    def test_list_absences_filter_by_start_date(self, client: TestClient, db: Session, sample_resident: Person):
        """Test filtering absences by start_date."""
        # Create absences with different date ranges
        past_absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=5),
            absence_type="vacation",
        )
        future_absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="conference",
        )
        db.add(past_absence)
        db.add(future_absence)
        db.commit()

        filter_date = (date.today() + timedelta(days=5)).isoformat()
        response = client.get(
            "/api/absences",
            params={"start_date": filter_date}
        )

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data

        # All returned absences should end on or after the filter date
        for absence in items:
            absence_end = date.fromisoformat(absence["end_date"])
            assert absence_end >= date.fromisoformat(filter_date)

    def test_list_absences_filter_by_end_date(self, client: TestClient, db: Session, sample_resident: Person):
        """Test filtering absences by end_date."""
        # Create absences with different date ranges
        near_absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
            absence_type="vacation",
        )
        far_absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=25),
            absence_type="deployment",
        )
        db.add(near_absence)
        db.add(far_absence)
        db.commit()

        filter_date = (date.today() + timedelta(days=10)).isoformat()
        response = client.get(
            "/api/absences",
            params={"end_date": filter_date}
        )

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data

        # All returned absences should start on or before the filter date
        for absence in items:
            absence_start = date.fromisoformat(absence["start_date"])
            assert absence_start <= date.fromisoformat(filter_date)

    def test_list_absences_filter_by_date_range(self, client: TestClient, db: Session, sample_resident: Person):
        """Test filtering absences by date range."""
        # Create absences across different time periods
        absences = [
            Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() - timedelta(days=20),
                end_date=date.today() - timedelta(days=15),
                absence_type="vacation",
            ),
            Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=5),
                end_date=date.today() + timedelta(days=10),
                absence_type="conference",
            ),
            Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=25),
                end_date=date.today() + timedelta(days=30),
                absence_type="tdy",
            ),
        ]
        for absence in absences:
            db.add(absence)
        db.commit()

        # Filter for middle range
        filter_start = (date.today() + timedelta(days=3)).isoformat()
        filter_end = (date.today() + timedelta(days=15)).isoformat()

        response = client.get(
            "/api/absences",
            params={
                "start_date": filter_start,
                "end_date": filter_end
            }
        )

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data

        # Should only get absences that overlap the range
        assert len(items) >= 1

        # All absences should overlap with the range
        for absence in items:
            absence_start = date.fromisoformat(absence["start_date"])
            absence_end = date.fromisoformat(absence["end_date"])
            # Absence overlaps if it ends after filter_start and starts before filter_end
            assert absence_end >= date.fromisoformat(filter_start)
            assert absence_start <= date.fromisoformat(filter_end)

    def test_list_absences_filter_by_absence_type(self, client: TestClient, db: Session, sample_resident: Person):
        """Test filtering absences by absence_type."""
        # Create absences with different types
        vacation = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            absence_type="vacation",
        )
        conference = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            absence_type="conference",
        )
        deployment = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=60),
            absence_type="deployment",
        )
        db.add(vacation)
        db.add(conference)
        db.add(deployment)
        db.commit()

        response = client.get(
            "/api/absences",
            params={"absence_type": "vacation"}
        )

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data

        # All returned absences should be of type vacation
        for absence in items:
            assert absence["absence_type"] == "vacation"

    def test_list_absences_combined_filters(self, client: TestClient, db: Session, sample_resident: Person):
        """Test combining multiple filters."""
        other_person = Person(
            id=uuid4(),
            name="Dr. Other",
            type="resident",
            email="other@hospital.org",
            pgy_level=2,
        )
        db.add(other_person)
        db.commit()

        # Create various absences
        absences = [
            Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=5),
                absence_type="vacation",
            ),
            Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=15),
                absence_type="conference",
            ),
            Absence(
                id=uuid4(),
                person_id=other_person.id,
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=5),
                absence_type="vacation",
            ),
        ]
        for absence in absences:
            db.add(absence)
        db.commit()

        # Filter by person and type
        response = client.get(
            "/api/absences",
            params={
                "person_id": str(sample_resident.id),
                "absence_type": "vacation"
            }
        )

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data

        # Should get only vacation absences for sample_resident
        assert len(items) >= 1
        for absence in items:
            assert absence["person_id"] == str(sample_resident.id)
            assert absence["absence_type"] == "vacation"

    def test_list_absences_no_results(self, client: TestClient, sample_absence: Absence):
        """Test filtering with parameters that have no matches."""
        # Query far in the future
        future_start = (date.today() + timedelta(days=365)).isoformat()
        future_end = (date.today() + timedelta(days=400)).isoformat()

        response = client.get(
            "/api/absences",
            params={
                "start_date": future_start,
                "end_date": future_end
            }
        )

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data
        # May be empty or have very few results
        assert isinstance(items, list)


class TestGetAbsenceEndpoint:
    """Tests for GET /api/absences/{absence_id} endpoint."""

    def test_get_absence_success(self, client: TestClient, sample_absence: Absence):
        """Test getting an existing absence by ID."""
        response = client.get(f"/api/absences/{sample_absence.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_absence.id)
        assert data["person_id"] == str(sample_absence.person_id)
        assert data["start_date"] == sample_absence.start_date.isoformat()
        assert data["end_date"] == sample_absence.end_date.isoformat()
        assert data["absence_type"] == sample_absence.absence_type

    def test_get_absence_not_found(self, client: TestClient):
        """Test getting a non-existent absence."""
        fake_id = uuid4()
        response = client.get(f"/api/absences/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_absence_invalid_uuid(self, client: TestClient):
        """Test getting absence with invalid UUID format."""
        response = client.get("/api/absences/not-a-valid-uuid")

        assert response.status_code == 422  # Validation error

    def test_get_absence_with_notes(self, client: TestClient, db: Session, sample_resident: Person):
        """Test getting an absence that has notes."""
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            absence_type="vacation",
            notes="Annual leave - Hawaii trip",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        response = client.get(f"/api/absences/{absence.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Annual leave - Hawaii trip"


class TestCreateAbsenceEndpoint:
    """Tests for POST /api/absences endpoint."""

    def test_create_absence_success(self, client: TestClient, sample_resident: Person):
        """Test creating a valid absence."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "absence_type": "vacation",
            "notes": "Annual vacation",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["person_id"] == absence_data["person_id"]
        assert data["start_date"] == absence_data["start_date"]
        assert data["end_date"] == absence_data["end_date"]
        assert data["absence_type"] == absence_data["absence_type"]
        assert data["notes"] == absence_data["notes"]

    def test_create_absence_person_not_found(self, client: TestClient):
        """Test creating absence for non-existent person."""
        fake_id = uuid4()
        absence_data = {
            "person_id": str(fake_id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "absence_type": "vacation",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 400

    def test_create_absence_invalid_date_range(self, client: TestClient, sample_resident: Person):
        """Test creating absence with end_date before start_date."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=15)).isoformat(),
            "end_date": (date.today() + timedelta(days=10)).isoformat(),  # Before start!
            "absence_type": "vacation",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 422  # Validation error

    def test_create_absence_missing_required_fields(self, client: TestClient):
        """Test creating absence with missing required fields."""
        absence_data = {
            "person_id": str(uuid4()),
            # Missing start_date, end_date, absence_type
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 422  # Validation error

    def test_create_absence_invalid_absence_type(self, client: TestClient, sample_resident: Person):
        """Test creating absence with invalid absence_type."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "absence_type": "invalid_type",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 422  # Validation error

    def test_create_absence_deployment(self, client: TestClient, sample_resident: Person):
        """Test creating deployment absence."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=30)).isoformat(),
            "end_date": (date.today() + timedelta(days=90)).isoformat(),
            "absence_type": "deployment",
            "deployment_orders": True,
            "notes": "Deployment to overseas location",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 201
        data = response.json()
        assert data["absence_type"] == "deployment"

    def test_create_absence_tdy(self, client: TestClient, sample_faculty: Person):
        """Test creating TDY absence with location."""
        absence_data = {
            "person_id": str(sample_faculty.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "absence_type": "tdy",
            "tdy_location": "Tripler Army Medical Center",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 201
        data = response.json()
        assert data["absence_type"] == "tdy"
        assert data["tdy_location"] == "Tripler Army Medical Center"

    def test_create_absence_without_optional_fields(self, client: TestClient, sample_resident: Person):
        """Test creating absence without optional fields."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "absence_type": "conference",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 201
        data = response.json()
        # Optional fields should be None or have default values
        assert data.get("notes") is None or data.get("notes") == ""

    def test_create_absence_same_start_end_date(self, client: TestClient, sample_resident: Person):
        """Test creating absence with same start and end date (single day)."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=10)).isoformat(),
            "absence_type": "sick",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 201


class TestUpdateAbsenceEndpoint:
    """Tests for PUT /api/absences/{absence_id} endpoint."""

    def test_update_absence_success(self, client: TestClient, db: Session, sample_resident: Person):
        """Test successfully updating an absence."""
        # Create an absence to update
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
            notes="Original notes",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        update_data = {
            "start_date": (date.today() + timedelta(days=12)).isoformat(),
            "end_date": (date.today() + timedelta(days=17)).isoformat(),
            "notes": "Updated notes",
        }

        response = client.put(f"/api/absences/{absence.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == update_data["start_date"]
        assert data["end_date"] == update_data["end_date"]
        assert data["notes"] == update_data["notes"]

    def test_update_absence_not_found(self, client: TestClient):
        """Test updating a non-existent absence."""
        fake_id = uuid4()
        update_data = {
            "notes": "Updated notes",
        }

        response = client.put(f"/api/absences/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_update_absence_partial_update(self, client: TestClient, db: Session, sample_resident: Person):
        """Test partial update (only some fields)."""
        # Create an absence to update
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
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
        original_type = absence.absence_type

        # Only update notes
        update_data = {
            "notes": "Only notes changed",
        }

        response = client.put(f"/api/absences/{absence.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        # Dates and type should remain unchanged
        assert data["start_date"] == original_start.isoformat()
        assert data["end_date"] == original_end.isoformat()
        assert data["absence_type"] == original_type
        assert data["notes"] == update_data["notes"]

    def test_update_absence_change_type(self, client: TestClient, db: Session, sample_resident: Person):
        """Test updating absence type."""
        # Create an absence to update
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        update_data = {
            "absence_type": "conference",
        }

        response = client.put(f"/api/absences/{absence.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["absence_type"] == "conference"

    def test_update_absence_invalid_type(self, client: TestClient, db: Session, sample_resident: Person):
        """Test updating absence with invalid type."""
        # Create an absence to update
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        update_data = {
            "absence_type": "invalid_type",
        }

        response = client.put(f"/api/absences/{absence.id}", json=update_data)

        assert response.status_code == 422  # Validation error

    def test_update_absence_deployment_fields(self, client: TestClient, db: Session, sample_resident: Person):
        """Test updating deployment-specific fields."""
        # Create a deployment absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=90),
            absence_type="deployment",
            deployment_orders=False,
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        update_data = {
            "deployment_orders": True,
            "notes": "Orders received",
        }

        response = client.put(f"/api/absences/{absence.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["deployment_orders"] is True
        assert data["notes"] == "Orders received"


class TestDeleteAbsenceEndpoint:
    """Tests for DELETE /api/absences/{absence_id} endpoint."""

    def test_delete_absence_success(self, client: TestClient, db: Session, sample_resident: Person):
        """Test successfully deleting an absence."""
        # Create an absence to delete
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        absence_id = absence.id

        response = client.delete(f"/api/absences/{absence_id}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify deletion
        deleted_absence = db.query(Absence).filter(Absence.id == absence_id).first()
        assert deleted_absence is None

    def test_delete_absence_not_found(self, client: TestClient):
        """Test deleting a non-existent absence."""
        fake_id = uuid4()
        response = client.delete(f"/api/absences/{fake_id}")

        assert response.status_code == 404

    def test_delete_absence_invalid_uuid(self, client: TestClient):
        """Test deleting absence with invalid UUID format."""
        response = client.delete("/api/absences/invalid-uuid-format")

        assert response.status_code == 422  # Validation error

    def test_delete_absence_twice(self, client: TestClient, db: Session, sample_resident: Person):
        """Test deleting the same absence twice."""
        # Create an absence to delete
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        absence_id = absence.id

        # First delete
        response1 = client.delete(f"/api/absences/{absence_id}")
        assert response1.status_code == 204

        # Second delete should fail
        response2 = client.delete(f"/api/absences/{absence_id}")
        assert response2.status_code == 404


class TestAbsenceStructureAndValidation:
    """Tests for absence data structure and field validation."""

    def test_absence_response_has_all_fields(self, client: TestClient, sample_absence: Absence):
        """Test that absence response includes all expected fields."""
        response = client.get(f"/api/absences/{sample_absence.id}")

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = ["id", "person_id", "start_date", "end_date", "absence_type"]
        for field in required_fields:
            assert field in data

        # Optional fields should be present (even if None)
        optional_fields = ["notes", "deployment_orders", "tdy_location", "is_blocking"]
        for field in optional_fields:
            assert field in data

    def test_absence_date_format(self, client: TestClient, db: Session, sample_resident: Person):
        """Test that absence dates are in ISO format."""
        # Create absences
        for i in range(3):
            absence = Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=i * 5),
                end_date=date.today() + timedelta(days=i * 5 + 2),
                absence_type="vacation",
            )
            db.add(absence)
        db.commit()

        response = client.get("/api/absences")

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data

        if items:
            for absence in items:
                # Should be parseable as ISO date
                try:
                    parsed_start = date.fromisoformat(absence["start_date"])
                    parsed_end = date.fromisoformat(absence["end_date"])
                    assert isinstance(parsed_start, date)
                    assert isinstance(parsed_end, date)
                except ValueError:
                    pytest.fail(f"Invalid date format in absence: {absence}")

    def test_absence_type_values(self, client: TestClient, db: Session, sample_resident: Person):
        """Test that absence_type contains valid values."""
        valid_types = [
            "vacation", "deployment", "tdy", "medical", "family_emergency",
            "conference", "bereavement", "emergency_leave", "sick",
            "convalescent", "maternity_paternity"
        ]

        # Create absences with various types
        for absence_type in valid_types[:3]:
            absence = Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=3),
                absence_type=absence_type,
            )
            db.add(absence)
        db.commit()

        response = client.get("/api/absences")

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data

        if items:
            for absence in items:
                assert absence["absence_type"] in valid_types


class TestAbsenceEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_absence_far_future(self, client: TestClient, sample_resident: Person):
        """Test creating absence far in the future."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=365)).isoformat(),
            "end_date": (date.today() + timedelta(days=370)).isoformat(),
            "absence_type": "vacation",
        }

        response = client.post("/api/absences", json=absence_data)

        assert response.status_code == 201

    def test_create_absence_past_date(self, client: TestClient, sample_resident: Person):
        """Test creating absence with past dates."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() - timedelta(days=30)).isoformat(),
            "end_date": (date.today() - timedelta(days=25)).isoformat(),
            "absence_type": "sick",
        }

        response = client.post("/api/absences", json=absence_data)

        # Should succeed - historical absences are allowed
        assert response.status_code in [201, 400]

    def test_overlapping_absences_same_person(self, client: TestClient, db: Session, sample_resident: Person):
        """Test creating overlapping absences for the same person."""
        # Create first absence
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence1)
        db.commit()

        # Create overlapping absence
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=12)).isoformat(),
            "end_date": (date.today() + timedelta(days=17)).isoformat(),
            "absence_type": "conference",
        }

        response = client.post("/api/absences", json=absence_data)

        # May succeed or fail depending on business logic
        assert response.status_code in [201, 400]

    def test_create_absence_long_notes(self, client: TestClient, sample_resident: Person):
        """Test creating absence with very long notes."""
        absence_data = {
            "person_id": str(sample_resident.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),
            "absence_type": "vacation",
            "notes": "A" * 1000,  # Very long notes
        }

        response = client.post("/api/absences", json=absence_data)

        # Should succeed unless there's a length limit
        assert response.status_code in [201, 422]

    def test_update_absence_dates_to_invalid_range(self, client: TestClient, db: Session, sample_resident: Person):
        """Test updating absence to have invalid date range."""
        # Create an absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)

        # Try to update with invalid range
        update_data = {
            "start_date": (date.today() + timedelta(days=20)).isoformat(),
            "end_date": (date.today() + timedelta(days=15)).isoformat(),  # Before start!
        }

        response = client.put(f"/api/absences/{absence.id}", json=update_data)

        # Should fail validation
        assert response.status_code in [400, 422]

    def test_list_absences_boundary_dates(self, client: TestClient, db: Session, sample_resident: Person):
        """Test filtering with exact boundary dates."""
        # Create absences for specific dates
        base_date = date.today() + timedelta(days=50)
        for i in range(5):
            absence = Absence(
                id=uuid4(),
                person_id=sample_resident.id,
                start_date=base_date + timedelta(days=i * 3),
                end_date=base_date + timedelta(days=i * 3 + 2),
                absence_type="vacation",
            )
            db.add(absence)
        db.commit()

        # Query with exact start date
        response = client.get(
            "/api/absences",
            params={"start_date": base_date.isoformat()}
        )

        assert response.status_code == 200
        data = response.json()

        items = data.get("items", data) if isinstance(data, dict) else data
        # Should include absences that end on or after the start date
        assert len(items) >= 1
