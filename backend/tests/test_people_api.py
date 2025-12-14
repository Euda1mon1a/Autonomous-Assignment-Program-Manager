"""
Tests for the People API endpoints.

Tests CRUD operations for residents and faculty.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.person import Person


class TestListPeople:
    """Tests for GET /api/people endpoint."""

    def test_list_people_empty(self, client: TestClient):
        """Should return empty list when no people exist."""
        response = client.get("/api/people")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_people_with_data(self, client: TestClient, sample_resident: Person, sample_faculty: Person):
        """Should return all people."""
        response = client.get("/api/people")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_people_filter_by_type_resident(self, client: TestClient, sample_resident: Person, sample_faculty: Person):
        """Should filter by type=resident."""
        response = client.get("/api/people?type=resident")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["type"] == "resident"

    def test_list_people_filter_by_type_faculty(self, client: TestClient, sample_resident: Person, sample_faculty: Person):
        """Should filter by type=faculty."""
        response = client.get("/api/people?type=faculty")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["type"] == "faculty"

    def test_list_people_filter_by_pgy_level(self, client: TestClient, sample_residents: list[Person]):
        """Should filter by PGY level."""
        response = client.get("/api/people?pgy_level=1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["pgy_level"] == 1


class TestListResidents:
    """Tests for GET /api/people/residents endpoint."""

    def test_list_residents_empty(self, client: TestClient):
        """Should return empty list when no residents exist."""
        response = client.get("/api/people/residents")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_residents_excludes_faculty(self, client: TestClient, sample_resident: Person, sample_faculty: Person):
        """Should only return residents, not faculty."""
        response = client.get("/api/people/residents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["type"] == "resident"

    def test_list_residents_filter_by_pgy_level(self, client: TestClient, sample_residents: list[Person]):
        """Should filter residents by PGY level."""
        response = client.get("/api/people/residents?pgy_level=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["pgy_level"] == 2


class TestListFaculty:
    """Tests for GET /api/people/faculty endpoint."""

    def test_list_faculty_empty(self, client: TestClient):
        """Should return empty list when no faculty exist."""
        response = client.get("/api/people/faculty")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_faculty_excludes_residents(self, client: TestClient, sample_resident: Person, sample_faculty: Person):
        """Should only return faculty, not residents."""
        response = client.get("/api/people/faculty")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["type"] == "faculty"


class TestGetPerson:
    """Tests for GET /api/people/{person_id} endpoint."""

    def test_get_person_success(self, client: TestClient, sample_resident: Person):
        """Should return person by ID."""
        response = client.get(f"/api/people/{sample_resident.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_resident.id)
        assert data["name"] == sample_resident.name
        assert data["type"] == "resident"
        assert data["pgy_level"] == 2

    def test_get_person_not_found(self, client: TestClient):
        """Should return 404 for non-existent person."""
        fake_id = "00000000-0000-4000-8000-000000000000"
        response = client.get(f"/api/people/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreatePerson:
    """Tests for POST /api/people endpoint."""

    def test_create_resident_success(self, client: TestClient):
        """Should create a new resident."""
        payload = {
            "name": "Dr. New Resident",
            "type": "resident",
            "email": "new.resident@hospital.org",
            "pgy_level": 1,
        }
        response = client.post("/api/people", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["type"] == "resident"
        assert data["pgy_level"] == 1
        assert "id" in data

    def test_create_faculty_success(self, client: TestClient):
        """Should create a new faculty member."""
        payload = {
            "name": "Dr. New Faculty",
            "type": "faculty",
            "email": "new.faculty@hospital.org",
            "performs_procedures": True,
            "specialties": ["Cardiology", "Internal Medicine"],
        }
        response = client.post("/api/people", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["type"] == "faculty"
        assert data["performs_procedures"] is True

    def test_create_resident_missing_pgy_level(self, client: TestClient):
        """Should return 400 when PGY level missing for resident."""
        payload = {
            "name": "Dr. Bad Resident",
            "type": "resident",
            "email": "bad.resident@hospital.org",
            # Missing pgy_level
        }
        response = client.post("/api/people", json=payload)
        assert response.status_code == 400
        assert "pgy" in response.json()["detail"].lower()

    def test_create_person_invalid_type(self, client: TestClient):
        """Should return 422 for invalid person type."""
        payload = {
            "name": "Dr. Invalid",
            "type": "invalid_type",
            "email": "invalid@hospital.org",
        }
        response = client.post("/api/people", json=payload)
        assert response.status_code == 422  # Pydantic validation error

    def test_create_person_invalid_pgy_level(self, client: TestClient):
        """Should return 422 for invalid PGY level."""
        payload = {
            "name": "Dr. Invalid PGY",
            "type": "resident",
            "email": "invalid.pgy@hospital.org",
            "pgy_level": 5,  # Invalid: must be 1-3
        }
        response = client.post("/api/people", json=payload)
        assert response.status_code == 422


class TestUpdatePerson:
    """Tests for PUT /api/people/{person_id} endpoint."""

    def test_update_person_success(self, client: TestClient, sample_resident: Person):
        """Should update person fields."""
        payload = {
            "name": "Dr. Updated Name",
            "email": "updated@hospital.org",
        }
        response = client.put(f"/api/people/{sample_resident.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dr. Updated Name"
        assert data["email"] == "updated@hospital.org"
        # Original fields should remain
        assert data["pgy_level"] == sample_resident.pgy_level

    def test_update_person_partial(self, client: TestClient, sample_resident: Person):
        """Should allow partial updates."""
        original_email = sample_resident.email
        payload = {"name": "Dr. Partial Update"}
        response = client.put(f"/api/people/{sample_resident.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dr. Partial Update"
        # Email should remain unchanged
        assert data["email"] == original_email

    def test_update_person_pgy_level(self, client: TestClient, sample_resident: Person):
        """Should update PGY level for residents."""
        payload = {"pgy_level": 3}
        response = client.put(f"/api/people/{sample_resident.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["pgy_level"] == 3

    def test_update_person_not_found(self, client: TestClient):
        """Should return 404 for non-existent person."""
        fake_id = "00000000-0000-4000-8000-000000000000"
        payload = {"name": "Ghost"}
        response = client.put(f"/api/people/{fake_id}", json=payload)
        assert response.status_code == 404


class TestDeletePerson:
    """Tests for DELETE /api/people/{person_id} endpoint."""

    def test_delete_person_success(self, client: TestClient, sample_resident: Person, db: Session):
        """Should delete person."""
        person_id = str(sample_resident.id)
        response = client.delete(f"/api/people/{person_id}")
        assert response.status_code == 204

        # Verify person is deleted
        person = db.query(Person).filter(Person.id == sample_resident.id).first()
        assert person is None

    def test_delete_person_not_found(self, client: TestClient):
        """Should return 404 for non-existent person."""
        fake_id = "00000000-0000-4000-8000-000000000000"
        response = client.delete(f"/api/people/{fake_id}")
        assert response.status_code == 404

    def test_delete_person_idempotent(self, client: TestClient, sample_resident: Person):
        """Deleting same person twice should return 404 on second attempt."""
        person_id = str(sample_resident.id)

        # First delete
        response1 = client.delete(f"/api/people/{person_id}")
        assert response1.status_code == 204

        # Second delete
        response2 = client.delete(f"/api/people/{person_id}")
        assert response2.status_code == 404
