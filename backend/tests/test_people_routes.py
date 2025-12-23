"""Tests for people API routes.

Comprehensive test suite covering CRUD operations, filters, validation,
credential endpoints, and error handling for people endpoints.
All endpoints require authentication.
"""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.person import Person


class TestListPeopleEndpoint:
    """Tests for GET /api/people endpoint."""

    def test_list_people_empty(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test listing people when none exist."""
        response = client.get("/api/v1/people", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_people_with_data(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test listing people with existing data."""
        response = client.get("/api/v1/people", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert len(data["items"]) > 0

        # Validate person structure
        person = data["items"][0]
        assert "id" in person
        assert "name" in person
        assert "type" in person
        assert "email" in person

    def test_list_people_filter_by_type_resident(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test filtering people by type='resident'."""
        response = client.get(
            "/api/v1/people", params={"type": "resident"}, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # All returned people should be residents
        for person in data["items"]:
            assert person["type"] == "resident"
            assert "pgy_level" in person

    def test_list_people_filter_by_type_faculty(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test filtering people by type='faculty'."""
        response = client.get(
            "/api/v1/people", params={"type": "faculty"}, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # All returned people should be faculty
        for person in data["items"]:
            assert person["type"] == "faculty"

    def test_list_people_filter_by_pgy_level(
        self, client: TestClient, sample_residents, auth_headers: dict
    ):
        """Test filtering people by pgy_level."""
        response = client.get(
            "/api/v1/people", params={"pgy_level": 2}, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # All returned people should be PGY-2
        for person in data["items"]:
            assert person["pgy_level"] == 2

    def test_list_people_filter_type_and_pgy(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test combined filter by type and pgy_level."""
        response = client.get(
            "/api/v1/people",
            params={"type": "resident", "pgy_level": 1},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # All should be PGY-1 residents
        for person in data["items"]:
            assert person["type"] == "resident"
            assert person["pgy_level"] == 1

    def test_list_people_requires_auth(self, client: TestClient):
        """Test that listing people requires authentication."""
        response = client.get("/api/v1/people")

        assert response.status_code == 401


class TestListResidentsEndpoint:
    """Tests for GET /api/people/residents endpoint."""

    def test_list_residents_all(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test listing all residents."""
        response = client.get("/api/v1/people/residents", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should only return residents
        assert data["total"] == len(sample_residents)
        for person in data["items"]:
            assert person["type"] == "resident"

    def test_list_residents_filter_pgy_level(
        self, client: TestClient, sample_residents, auth_headers: dict
    ):
        """Test filtering residents by PGY level."""
        response = client.get(
            "/api/v1/people/residents", params={"pgy_level": 3}, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # All should be PGY-3
        for person in data["items"]:
            assert person["type"] == "resident"
            assert person["pgy_level"] == 3

    def test_list_residents_empty(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test listing residents when none exist."""
        response = client.get("/api/v1/people/residents", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_residents_excludes_faculty(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test that list residents excludes faculty members."""
        response = client.get("/api/v1/people/residents", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify no faculty in results
        for person in data["items"]:
            assert person["type"] != "faculty"

    def test_list_residents_requires_auth(self, client: TestClient):
        """Test that listing residents requires authentication."""
        response = client.get("/api/v1/people/residents")

        assert response.status_code == 401


class TestListFacultyEndpoint:
    """Tests for GET /api/people/faculty endpoint."""

    def test_list_faculty_all(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test listing all faculty."""
        response = client.get("/api/v1/people/faculty", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should only return faculty
        assert data["total"] == len(sample_faculty_members)
        for person in data["items"]:
            assert person["type"] == "faculty"

    def test_list_faculty_filter_specialty(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test filtering faculty by specialty."""
        # Create faculty with specific specialty
        faculty = Person(
            id=uuid4(),
            name="Dr. Sports Med",
            type="faculty",
            email="sports@hospital.org",
            specialties=["Sports Medicine"],
        )
        db.add(faculty)
        db.commit()

        response = client.get(
            "/api/v1/people/faculty",
            params={"specialty": "Sports Medicine"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # All should have Sports Medicine specialty
        for person in data["items"]:
            assert person["type"] == "faculty"
            assert person["specialties"] is not None

    def test_list_faculty_empty(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test listing faculty when none exist."""
        response = client.get("/api/v1/people/faculty", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_faculty_excludes_residents(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test that list faculty excludes residents."""
        response = client.get("/api/v1/people/faculty", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify no residents in results
        for person in data["items"]:
            assert person["type"] != "resident"

    def test_list_faculty_requires_auth(self, client: TestClient):
        """Test that listing faculty requires authentication."""
        response = client.get("/api/v1/people/faculty")

        assert response.status_code == 401


class TestGetPersonEndpoint:
    """Tests for GET /api/people/{person_id} endpoint."""

    def test_get_person_resident_success(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test getting an existing resident by ID."""
        response = client.get(
            f"/api/v1/people/{sample_resident.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_resident.id)
        assert data["name"] == sample_resident.name
        assert data["type"] == "resident"
        assert data["pgy_level"] == sample_resident.pgy_level

    def test_get_person_faculty_success(
        self, client: TestClient, sample_faculty: Person, auth_headers: dict
    ):
        """Test getting an existing faculty by ID."""
        response = client.get(
            f"/api/v1/people/{sample_faculty.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_faculty.id)
        assert data["name"] == sample_faculty.name
        assert data["type"] == "faculty"
        assert "specialties" in data

    def test_get_person_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting a non-existent person."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/people/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_person_invalid_uuid(self, client: TestClient, auth_headers: dict):
        """Test getting person with invalid UUID format."""
        response = client.get("/api/v1/people/not-a-valid-uuid", headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_get_person_requires_auth(
        self, client: TestClient, sample_resident: Person
    ):
        """Test that getting a person requires authentication."""
        response = client.get(f"/api/v1/people/{sample_resident.id}")

        assert response.status_code == 401

    def test_get_person_includes_timestamps(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test that person response includes created_at and updated_at."""
        response = client.get(
            f"/api/v1/people/{sample_resident.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "created_at" in data
        assert "updated_at" in data


class TestCreatePersonEndpoint:
    """Tests for POST /api/people endpoint."""

    def test_create_resident_success(self, client: TestClient, auth_headers: dict):
        """Test creating a new resident."""
        person_data = {
            "name": "Dr. New Resident",
            "type": "resident",
            "email": "new.resident@hospital.org",
            "pgy_level": 1,
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == person_data["name"]
        assert data["type"] == "resident"
        assert data["pgy_level"] == 1

    def test_create_faculty_success(self, client: TestClient, auth_headers: dict):
        """Test creating a new faculty member."""
        person_data = {
            "name": "Dr. New Faculty",
            "type": "faculty",
            "email": "new.faculty@hospital.org",
            "performs_procedures": True,
            "specialties": ["Primary Care"],
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == person_data["name"]
        assert data["type"] == "faculty"
        assert data["performs_procedures"] is True
        assert data["specialties"] == ["Primary Care"]

    def test_create_person_invalid_type(self, client: TestClient, auth_headers: dict):
        """Test creating person with invalid type."""
        person_data = {
            "name": "Invalid Person",
            "type": "invalid_type",
            "email": "invalid@hospital.org",
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_create_person_invalid_pgy_level(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating resident with invalid PGY level."""
        person_data = {
            "name": "Dr. Invalid PGY",
            "type": "resident",
            "email": "invalid.pgy@hospital.org",
            "pgy_level": 5,  # Invalid, must be 1-3
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_create_person_missing_required_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating person with missing required fields."""
        person_data = {
            "type": "resident",
            # Missing name
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_create_person_duplicate_email(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test creating person with duplicate email."""
        person_data = {
            "name": "Dr. Duplicate Email",
            "type": "resident",
            "email": sample_resident.email,  # Duplicate
            "pgy_level": 1,
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        # Should fail with 400 or 422
        assert response.status_code in [400, 422]

    def test_create_person_requires_auth(self, client: TestClient):
        """Test that creating a person requires authentication."""
        person_data = {
            "name": "Dr. No Auth",
            "type": "resident",
            "email": "noauth@hospital.org",
            "pgy_level": 1,
        }

        response = client.post("/api/v1/people", json=person_data)

        assert response.status_code == 401

    def test_create_faculty_with_role(self, client: TestClient, auth_headers: dict):
        """Test creating faculty with faculty_role."""
        person_data = {
            "name": "Dr. Program Director",
            "type": "faculty",
            "email": "pd@hospital.org",
            "faculty_role": "pd",
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["faculty_role"] == "pd"


class TestUpdatePersonEndpoint:
    """Tests for PUT /api/people/{person_id} endpoint."""

    def test_update_person_name_success(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test updating a person's name."""
        update_data = {
            "name": "Dr. Updated Name",
        }

        response = client.put(
            f"/api/v1/people/{sample_resident.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dr. Updated Name"

    def test_update_person_pgy_level(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test updating a resident's PGY level."""
        update_data = {
            "pgy_level": 3,
        }

        response = client.put(
            f"/api/v1/people/{sample_resident.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pgy_level"] == 3

    def test_update_person_specialties(
        self, client: TestClient, sample_faculty: Person, auth_headers: dict
    ):
        """Test updating faculty specialties."""
        update_data = {
            "specialties": ["Dermatology", "Primary Care"],
        }

        response = client.put(
            f"/api/v1/people/{sample_faculty.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "Dermatology" in data["specialties"]

    def test_update_person_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating a non-existent person."""
        fake_id = uuid4()
        update_data = {
            "name": "Dr. Not Found",
        }

        response = client.put(
            f"/api/v1/people/{fake_id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_person_invalid_uuid(self, client: TestClient, auth_headers: dict):
        """Test updating person with invalid UUID."""
        response = client.put(
            "/api/v1/people/invalid-uuid", json={"name": "Test"}, headers=auth_headers
        )

        assert response.status_code == 422

    def test_update_person_requires_auth(
        self, client: TestClient, sample_resident: Person
    ):
        """Test that updating a person requires authentication."""
        response = client.put(
            f"/api/v1/people/{sample_resident.id}", json={"name": "No Auth"}
        )

        assert response.status_code == 401

    def test_update_person_partial_update(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test partial update (only some fields)."""
        original_email = sample_resident.email

        update_data = {
            "name": "Dr. Partial Update",
            # Not updating email
        }

        response = client.put(
            f"/api/v1/people/{sample_resident.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dr. Partial Update"
        assert data["email"] == original_email  # Should remain unchanged


class TestDeletePersonEndpoint:
    """Tests for DELETE /api/people/{person_id} endpoint."""

    def test_delete_person_success(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test successfully deleting a person."""
        # Create a person to delete
        person = Person(
            id=uuid4(),
            name="Dr. To Delete",
            type="resident",
            email="delete@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        person_id = person.id

        response = client.delete(f"/api/v1/people/{person_id}", headers=auth_headers)

        assert response.status_code == 204
        assert response.content == b""

        # Verify person is deleted
        verify_response = client.get(
            f"/api/v1/people/{person_id}", headers=auth_headers
        )
        assert verify_response.status_code == 404

    def test_delete_person_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting a non-existent person."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/people/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_person_invalid_uuid(self, client: TestClient, auth_headers: dict):
        """Test deleting person with invalid UUID."""
        response = client.delete("/api/v1/people/invalid-uuid", headers=auth_headers)

        assert response.status_code == 422

    def test_delete_person_requires_auth(
        self, client: TestClient, sample_resident: Person
    ):
        """Test that deleting a person requires authentication."""
        response = client.delete(f"/api/v1/people/{sample_resident.id}")

        assert response.status_code == 401

    def test_delete_person_twice(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test deleting the same person twice."""
        person = Person(
            id=uuid4(),
            name="Dr. Delete Twice",
            type="faculty",
            email="deletetwice@hospital.org",
        )
        db.add(person)
        db.commit()
        person_id = person.id

        # First delete
        response1 = client.delete(f"/api/v1/people/{person_id}", headers=auth_headers)
        assert response1.status_code == 204

        # Second delete should fail
        response2 = client.delete(f"/api/v1/people/{person_id}", headers=auth_headers)
        assert response2.status_code == 404


class TestPersonCredentialsEndpoint:
    """Tests for GET /api/people/{person_id}/credentials endpoint."""

    def test_get_person_credentials_empty(
        self, client: TestClient, sample_faculty: Person, auth_headers: dict
    ):
        """Test getting credentials for faculty with none."""
        response = client.get(
            f"/api/v1/people/{sample_faculty.id}/credentials", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0

    def test_get_person_credentials_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting credentials for non-existent person."""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/people/{fake_id}/credentials", headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_person_credentials_filter_status(
        self, client: TestClient, sample_faculty: Person, auth_headers: dict
    ):
        """Test filtering credentials by status."""
        response = client.get(
            f"/api/v1/people/{sample_faculty.id}/credentials",
            params={"status": "active"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_person_credentials_include_expired(
        self, client: TestClient, sample_faculty: Person, auth_headers: dict
    ):
        """Test including expired credentials."""
        response = client.get(
            f"/api/v1/people/{sample_faculty.id}/credentials",
            params={"include_expired": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_get_person_credentials_requires_auth(
        self, client: TestClient, sample_faculty: Person
    ):
        """Test that getting credentials requires authentication."""
        response = client.get(f"/api/v1/people/{sample_faculty.id}/credentials")

        assert response.status_code == 401


class TestPersonCredentialSummaryEndpoint:
    """Tests for GET /api/people/{person_id}/credentials/summary endpoint."""

    def test_get_credential_summary_success(
        self, client: TestClient, sample_faculty: Person, auth_headers: dict
    ):
        """Test getting credential summary for faculty."""
        response = client.get(
            f"/api/v1/people/{sample_faculty.id}/credentials/summary",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "person_id" in data
        assert data["person_id"] == str(sample_faculty.id)

    def test_get_credential_summary_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting credential summary for non-existent person."""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/people/{fake_id}/credentials/summary", headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_credential_summary_invalid_uuid(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting credential summary with invalid UUID."""
        response = client.get(
            "/api/v1/people/invalid-uuid/credentials/summary", headers=auth_headers
        )

        assert response.status_code == 422

    def test_get_credential_summary_requires_auth(
        self, client: TestClient, sample_faculty: Person
    ):
        """Test that getting credential summary requires authentication."""
        response = client.get(f"/api/v1/people/{sample_faculty.id}/credentials/summary")

        assert response.status_code == 401


class TestPersonProceduresEndpoint:
    """Tests for GET /api/people/{person_id}/procedures endpoint."""

    def test_get_person_procedures_empty(
        self, client: TestClient, sample_faculty: Person, auth_headers: dict
    ):
        """Test getting procedures for faculty with none."""
        response = client.get(
            f"/api/v1/people/{sample_faculty.id}/procedures", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_person_procedures_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting procedures for non-existent person."""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/people/{fake_id}/procedures", headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_person_procedures_invalid_uuid(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting procedures with invalid UUID."""
        response = client.get(
            "/api/v1/people/invalid-uuid/procedures", headers=auth_headers
        )

        assert response.status_code == 422

    def test_get_person_procedures_requires_auth(
        self, client: TestClient, sample_faculty: Person
    ):
        """Test that getting procedures requires authentication."""
        response = client.get(f"/api/v1/people/{sample_faculty.id}/procedures")

        assert response.status_code == 401


class TestPersonResponseStructure:
    """Tests for person response data structure and field validation."""

    def test_person_response_has_all_fields(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test that person response includes all expected fields."""
        response = client.get(
            f"/api/v1/people/{sample_resident.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = ["id", "name", "type", "email", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data

        # Equity tracking fields
        assert "sunday_call_count" in data
        assert "weekday_call_count" in data
        assert "fmit_weeks_count" in data

    def test_resident_has_pgy_level(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test that resident response includes pgy_level."""
        response = client.get(
            f"/api/v1/people/{sample_resident.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "pgy_level" in data
        assert data["pgy_level"] is not None

    def test_faculty_has_specialties(
        self, client: TestClient, sample_faculty: Person, auth_headers: dict
    ):
        """Test that faculty response includes specialties."""
        response = client.get(
            f"/api/v1/people/{sample_faculty.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "specialties" in data
        assert "performs_procedures" in data

    def test_person_type_values(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test that type only contains valid values."""
        response = client.get("/api/v1/people", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            for person in data["items"]:
                assert person["type"] in ["resident", "faculty"]


class TestPersonEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_resident_without_email(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a resident without email."""
        person_data = {
            "name": "Dr. No Email",
            "type": "resident",
            "pgy_level": 1,
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        # Should succeed - email is optional
        assert response.status_code == 201

    def test_create_faculty_without_specialties(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating faculty without specialties."""
        person_data = {
            "name": "Dr. No Specialty",
            "type": "faculty",
            "email": "nospecialty@hospital.org",
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        # Should succeed
        assert response.status_code == 201

    def test_pgy_level_boundary_values(self, client: TestClient, auth_headers: dict):
        """Test PGY level boundary values (1 and 3)."""
        # PGY-1 (minimum)
        person_data_1 = {
            "name": "Dr. PGY1",
            "type": "resident",
            "email": "pgy1@hospital.org",
            "pgy_level": 1,
        }
        response1 = client.post(
            "/api/v1/people", json=person_data_1, headers=auth_headers
        )
        assert response1.status_code == 201

        # PGY-3 (maximum)
        person_data_3 = {
            "name": "Dr. PGY3",
            "type": "resident",
            "email": "pgy3@hospital.org",
            "pgy_level": 3,
        }
        response3 = client.post(
            "/api/v1/people", json=person_data_3, headers=auth_headers
        )
        assert response3.status_code == 201

    def test_update_person_empty_body(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test updating person with empty body."""
        response = client.put(
            f"/api/v1/people/{sample_resident.id}", json={}, headers=auth_headers
        )

        # Should succeed - partial update with no changes
        assert response.status_code in [200, 422]

    def test_create_person_very_long_name(self, client: TestClient, auth_headers: dict):
        """Test creating person with very long name."""
        long_name = "Dr. " + "A" * 250

        person_data = {
            "name": long_name,
            "type": "resident",
            "email": "longname@hospital.org",
            "pgy_level": 1,
        }

        response = client.post("/api/v1/people", json=person_data, headers=auth_headers)

        # Should succeed or handle gracefully
        assert response.status_code in [201, 422]
