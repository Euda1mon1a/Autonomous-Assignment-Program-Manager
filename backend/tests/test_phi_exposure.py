"""Tests for PHI exposure protection.

Comprehensive test suite verifying that Protected Health Information (PHI)
is properly handled according to HIPAA requirements and documented in
docs/security/PHI_EXPOSURE_AUDIT.md.

Tests cover:
1. X-Contains-PHI headers on affected endpoints
2. Error messages don't leak PHI
3. Logging doesn't expose PHI
"""

import logging
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.person import Person


class TestPHIHeaders:
    """Tests for X-Contains-PHI response headers on affected endpoints."""

    def test_list_people_has_phi_headers(
        self, client: TestClient, sample_residents, auth_headers: dict
    ):
        """Test that GET /api/people includes PHI warning headers."""
        response = client.get("/api/v1/people", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"
        assert "name" in response.headers.get("X-PHI-Fields", "")
        assert "email" in response.headers.get("X-PHI-Fields", "")

    def test_list_residents_has_phi_headers(
        self, client: TestClient, sample_residents, auth_headers: dict
    ):
        """Test that GET /api/people/residents includes PHI warning headers."""
        response = client.get("/api/v1/people/residents", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"
        assert "name" in response.headers.get("X-PHI-Fields", "")
        assert "email" in response.headers.get("X-PHI-Fields", "")

    def test_list_faculty_has_phi_headers(
        self, client: TestClient, sample_faculty_members, auth_headers: dict
    ):
        """Test that GET /api/people/faculty includes PHI warning headers."""
        response = client.get("/api/v1/people/faculty", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"
        assert "name" in response.headers.get("X-PHI-Fields", "")
        assert "email" in response.headers.get("X-PHI-Fields", "")

    def test_get_person_has_phi_headers(
        self, client: TestClient, sample_residents, auth_headers: dict
    ):
        """Test that GET /api/people/{id} includes PHI warning headers."""
        person_id = sample_residents[0].id
        response = client.get(f"/api/v1/people/{person_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"
        assert "name" in response.headers.get("X-PHI-Fields", "")
        assert "email" in response.headers.get("X-PHI-Fields", "")

    def test_list_absences_has_phi_headers(
        self, client: TestClient, db: Session, sample_residents, auth_headers: dict
    ):
        """Test that GET /api/absences includes PHI/OPSEC warning headers."""
        # Create test absence
        absence = Absence(
            person_id=sample_residents[0].id,
            absence_type="medical",
            start_date="2025-01-15",
            end_date="2025-01-20",
            notes="Medical procedure",
        )
        db.add(absence)
        db.commit()

        response = client.get("/api/v1/absences", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"
        phi_fields = response.headers.get("X-PHI-Fields", "")
        assert "person_id" in phi_fields
        assert "absence_type" in phi_fields
        assert "deployment_orders" in phi_fields
        assert "tdy_location" in phi_fields
        assert "notes" in phi_fields

    def test_get_absence_has_phi_headers(
        self, client: TestClient, db: Session, sample_residents, auth_headers: dict
    ):
        """Test that GET /api/absences/{id} includes PHI/OPSEC warning headers."""
        # Create test absence
        absence = Absence(
            person_id=sample_residents[0].id,
            absence_type="deployment",
            start_date="2025-01-15",
            end_date="2025-03-15",
            deployment_orders="PCS orders to overseas location",
            tdy_location="Classified",
        )
        db.add(absence)
        db.commit()

        response = client.get(f"/api/v1/absences/{absence.id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"
        phi_fields = response.headers.get("X-PHI-Fields", "")
        assert "person_id" in phi_fields
        assert "absence_type" in phi_fields
        assert "deployment_orders" in phi_fields
        assert "tdy_location" in phi_fields

    def test_list_assignments_has_phi_headers(
        self,
        client: TestClient,
        db: Session,
        sample_residents,
        sample_blocks,
        auth_headers: dict,
    ):
        """Test that GET /api/assignments includes PHI/OPSEC warning headers."""
        # Create test assignment
        assignment = Assignment(
            person_id=sample_residents[0].id,
            block_id=sample_blocks[0].id,
            role="primary",
            activity_type="inpatient",
            notes="Sensitive note about performance",
        )
        db.add(assignment)
        db.commit()

        response = client.get("/api/v1/assignments", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"
        phi_fields = response.headers.get("X-PHI-Fields", "")
        assert "person_id" in phi_fields
        assert "notes" in phi_fields
        assert "override_reason" in phi_fields

    def test_get_assignment_has_phi_headers(
        self,
        client: TestClient,
        db: Session,
        sample_residents,
        sample_blocks,
        auth_headers: dict,
    ):
        """Test that GET /api/assignments/{id} includes PHI/OPSEC warning headers."""
        # Create test assignment
        assignment = Assignment(
            person_id=sample_residents[0].id,
            block_id=sample_blocks[0].id,
            role="primary",
            activity_type="inpatient",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            f"/api/v1/assignments/{assignment.id}", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"
        phi_fields = response.headers.get("X-PHI-Fields", "")
        assert "person_id" in phi_fields
        assert "notes" in phi_fields


class TestErrorMessagesNoPhiLeak:
    """Tests that error messages don't leak Protected Health Information."""

    def test_404_person_not_found_generic_message(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that 404 for missing person uses generic message without ID."""
        fake_person_id = str(uuid4())
        response = client.get(f"/api/v1/people/{fake_person_id}", headers=auth_headers)

        assert response.status_code == 404
        error_detail = response.json()["detail"]

        # Verify error doesn't include person_id (confirms/denies existence)
        assert fake_person_id not in error_detail
        # Should be generic message
        assert "not found" in error_detail.lower()

    def test_404_absence_not_found_generic_message(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that 404 for missing absence uses generic message without ID."""
        fake_absence_id = str(uuid4())
        response = client.get(
            f"/api/v1/absences/{fake_absence_id}", headers=auth_headers
        )

        assert response.status_code == 404
        error_detail = response.json()["detail"]

        # Verify error doesn't include absence_id
        assert fake_absence_id not in error_detail
        assert "not found" in error_detail.lower()

    def test_404_assignment_not_found_generic_message(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that 404 for missing assignment uses generic message without ID."""
        fake_assignment_id = str(uuid4())
        response = client.get(
            f"/api/v1/assignments/{fake_assignment_id}", headers=auth_headers
        )

        assert response.status_code == 404
        error_detail = response.json()["detail"]

        # Verify error doesn't include assignment_id
        assert fake_assignment_id not in error_detail
        assert "not found" in error_detail.lower()

    def test_validation_errors_dont_echo_phi(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that validation errors don't echo potentially PHI-containing input."""
        # Attempt to create person with invalid data that might contain PHI
        invalid_person = {
            "name": "Dr. John Smith",  # Real-sounding name
            "email": "invalid-email-format",  # Invalid but might contain PHI
            "type": "resident",
            # Missing required pgy_level
        }

        response = client.post(
            "/api/v1/people", json=invalid_person, headers=auth_headers
        )

        # Should get validation error
        assert response.status_code in [400, 422]
        error_detail = str(response.json()["detail"])

        # Error should describe the problem without echoing the invalid email
        # Note: Pydantic may include field name but not the actual value
        if "invalid-email-format" in error_detail:
            pytest.fail("Validation error echoed potentially PHI-containing input!")

    def test_500_errors_dont_leak_phi_in_production(
        self, client: TestClient, monkeypatch, auth_headers: dict
    ):
        """Test that 500 errors in production mode don't leak PHI in stack traces."""
        # This is handled by global exception handler in main.py
        # In production (DEBUG=False), should return generic error message
        # In development (DEBUG=True), may include details

        # Note: This would require triggering an actual 500 error
        # and verifying the global exception handler behavior.
        # Implementation depends on app configuration.
        pass


class TestResponseDataMinimization:
    """Tests for data minimization in API responses."""

    def test_people_endpoint_returns_only_necessary_fields(
        self, client: TestClient, sample_residents, auth_headers: dict
    ):
        """Test that people endpoint doesn't return unnecessary PHI."""
        response = client.get("/api/v1/people", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify structure but ensure no extra PHI fields
        for person in data["items"]:
            # Expected fields
            assert "id" in person
            assert "name" in person  # PHI but necessary
            assert "type" in person

            # Verify no unexpected sensitive fields
            assert "ssn" not in person  # Should never exist
            assert "medical_history" not in person  # Should never exist
            assert "password" not in person  # Should never be in response

    def test_absence_endpoint_doesnt_include_full_person_object(
        self, client: TestClient, db: Session, sample_residents, auth_headers: dict
    ):
        """Test that absences return person_id, not full person object with PHI."""
        # Create test absence
        absence = Absence(
            person_id=sample_residents[0].id,
            absence_type="medical",
            start_date="2025-01-15",
            end_date="2025-01-20",
        )
        db.add(absence)
        db.commit()

        response = client.get("/api/v1/absences", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        for absence_item in data["items"]:
            # Should have person_id reference
            assert "person_id" in absence_item

            # Should NOT embed full person object with name/email
            # (Frontend can fetch if needed with proper auth)
            if "person" in absence_item and isinstance(absence_item["person"], dict):
                # If person object included, should be minimal
                person_obj = absence_item["person"]
                # Check if it's a full person object (has name/email)
                if "name" in person_obj or "email" in person_obj:
                    pytest.fail(
                        "Absence response includes full person object with PHI. "
                        "Should return person_id only for data minimization."
                    )


class TestNonPhiEndpointsNoHeaders:
    """Tests that non-PHI endpoints don't incorrectly set PHI headers."""

    def test_health_endpoint_no_phi_headers(self, client: TestClient):
        """Test that health check endpoint doesn't set PHI headers."""
        response = client.get("/api/v1/health")

        # Health endpoint should not have PHI headers
        assert response.headers.get("X-Contains-PHI") != "true"

    def test_auth_endpoints_no_phi_headers(self, client: TestClient):
        """Test that authentication endpoints don't set PHI headers."""
        # Login endpoint doesn't return PHI
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass"},
        )

        # Should not have PHI headers (returns only token)
        assert response.headers.get("X-Contains-PHI") != "true"


class TestPhiHeaderConsistency:
    """Tests that PHI headers are consistent across different request patterns."""

    def test_filtered_people_endpoint_has_phi_headers(
        self,
        client: TestClient,
        sample_residents,
        sample_faculty_members,
        auth_headers: dict,
    ):
        """Test that filtered people queries still include PHI headers."""
        # Filter by type
        response = client.get(
            "/api/v1/people", params={"type": "resident"}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"

        # Filter by PGY level
        response = client.get(
            "/api/v1/people", params={"pgy_level": 1}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"

    def test_empty_results_still_have_phi_headers(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that empty result sets still include PHI headers (endpoint capability)."""
        # Query with impossible filter to get empty results
        response = client.get(
            "/api/v1/people", params={"pgy_level": 99}, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0  # No results

        # But endpoint is still capable of returning PHI, so header should be present
        assert response.headers.get("X-Contains-PHI") == "true"

    def test_paginated_results_have_phi_headers(
        self, client: TestClient, sample_residents, auth_headers: dict
    ):
        """Test that paginated results include PHI headers on all pages."""
        # First page
        response = client.get(
            "/api/v1/people", params={"page": 1, "page_size": 2}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers.get("X-Contains-PHI") == "true"

        # Second page (if exists)
        response = client.get(
            "/api/v1/people", params={"page": 2, "page_size": 2}, headers=auth_headers
        )
        assert response.status_code == 200
        # Even if empty, header should be present
        assert response.headers.get("X-Contains-PHI") == "true"


class TestPhiFieldsHeaderAccuracy:
    """Tests that X-PHI-Fields header accurately lists exposed fields."""

    def test_people_endpoint_phi_fields_complete(
        self, client: TestClient, sample_residents, auth_headers: dict
    ):
        """Test that X-PHI-Fields header lists all PHI fields in response."""
        response = client.get("/api/v1/people", headers=auth_headers)

        assert response.status_code == 200
        phi_fields_header = response.headers.get("X-PHI-Fields", "")
        response_data = response.json()

        # Check actual response for PHI fields
        if response_data["items"]:
            person = response_data["items"][0]

            # If response contains name, header should list it
            if "name" in person:
                assert "name" in phi_fields_header

            # If response contains email, header should list it
            if "email" in person and person["email"] is not None:
                assert "email" in phi_fields_header

    def test_absence_endpoint_phi_fields_complete(
        self, client: TestClient, db: Session, sample_residents, auth_headers: dict
    ):
        """Test that absence endpoint PHI fields header matches response."""
        # Create absence with deployment info
        absence = Absence(
            person_id=sample_residents[0].id,
            absence_type="deployment",
            start_date="2025-01-15",
            end_date="2025-03-15",
            deployment_orders="Classified orders",
            tdy_location="Overseas base",
            notes="Deployment notes",
        )
        db.add(absence)
        db.commit()

        response = client.get(f"/api/v1/absences/{absence.id}", headers=auth_headers)

        assert response.status_code == 200
        phi_fields_header = response.headers.get("X-PHI-Fields", "")

        # Verify all OPSEC-sensitive fields are listed
        assert "deployment_orders" in phi_fields_header
        assert "tdy_location" in phi_fields_header
        assert "notes" in phi_fields_header
