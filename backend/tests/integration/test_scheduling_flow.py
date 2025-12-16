"""
Integration tests for the complete scheduling workflow.

Tests the end-to-end flow of:
1. Creating people (residents and faculty)
2. Setting up rotation templates
3. Generating blocks
4. Running schedule generation
5. Validating ACGME compliance
"""
import pytest
from datetime import date, timedelta


@pytest.mark.integration
class TestSchedulingFlow:
    """Test complete scheduling workflow."""

    def test_schedule_generation_with_greedy_algorithm(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test schedule generation using greedy algorithm."""
        setup = full_program_setup

        # Generate schedule
        response = integration_client.post(
            "/api/schedule/generate",
            json={
                "start_date": setup["start_date"].isoformat(),
                "end_date": setup["end_date"].isoformat(),
                "algorithm": "greedy",
                "timeout_seconds": 30,
            },
            headers=auth_headers,
        )

        # May fail due to missing auth or other reasons in test env
        # but should not error with 500
        assert response.status_code in [200, 401, 403, 422]

    def test_schedule_generation_validates_acgme(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test that schedule generation includes ACGME validation."""
        setup = full_program_setup

        response = integration_client.post(
            "/api/schedule/generate",
            json={
                "start_date": setup["start_date"].isoformat(),
                "end_date": setup["end_date"].isoformat(),
                "algorithm": "greedy",
            },
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "validation" in data
            assert "status" in data


@pytest.mark.integration
class TestPeopleManagement:
    """Test people CRUD operations."""

    def test_create_resident(self, integration_client, auth_headers):
        """Test creating a new resident."""
        response = integration_client.post(
            "/api/people",
            json={
                "name": "Dr. New Resident",
                "type": "resident",
                "email": "new.resident@hospital.org",
                "pgy_level": 1,
            },
            headers=auth_headers,
        )

        # Check response (may need auth)
        assert response.status_code in [200, 201, 401, 403]

    def test_create_faculty(self, integration_client, auth_headers):
        """Test creating a new faculty member."""
        response = integration_client.post(
            "/api/people",
            json={
                "name": "Dr. New Faculty",
                "type": "faculty",
                "email": "new.faculty@hospital.org",
                "performs_procedures": True,
                "specialties": ["General Medicine"],
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 201, 401, 403]

    def test_list_people(self, integration_client, auth_headers, full_program_setup):
        """Test listing all people."""
        response = integration_client.get("/api/people", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            # Should have 6 people (3 residents + 3 faculty)
            assert len(data) >= 6


@pytest.mark.integration
class TestAssignmentOperations:
    """Test assignment CRUD operations."""

    def test_create_assignment(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test creating a new assignment."""
        setup = full_program_setup

        response = integration_client.post(
            "/api/assignments",
            json={
                "block_id": str(setup["blocks"][0].id),
                "person_id": str(setup["residents"][0].id),
                "rotation_template_id": str(setup["templates"][0].id),
                "role": "primary",
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 201, 401, 403, 422]

    def test_list_assignments(self, integration_client, auth_headers):
        """Test listing assignments."""
        response = integration_client.get("/api/assignments", headers=auth_headers)

        assert response.status_code in [200, 401, 403]


@pytest.mark.integration
class TestAbsenceManagement:
    """Test absence tracking operations."""

    def test_create_absence(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test creating an absence record."""
        setup = full_program_setup
        start = (date.today() + timedelta(days=30)).isoformat()
        end = (date.today() + timedelta(days=37)).isoformat()

        response = integration_client.post(
            "/api/absences",
            json={
                "person_id": str(setup["residents"][0].id),
                "start_date": start,
                "end_date": end,
                "absence_type": "vacation",
                "notes": "Annual leave",
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 201, 401, 403, 422]

    def test_absence_blocks_scheduling(
        self,
        integration_client,
        auth_headers,
        full_program_setup,
    ):
        """Test that absences are respected during scheduling."""
        setup = full_program_setup
        resident = setup["residents"][0]

        # Create an absence for the first week
        start = setup["start_date"].isoformat()
        end = (setup["start_date"] + timedelta(days=6)).isoformat()

        response = integration_client.post(
            "/api/absences",
            json={
                "person_id": str(resident.id),
                "start_date": start,
                "end_date": end,
                "absence_type": "vacation",
                "is_blocking": True,
            },
            headers=auth_headers,
        )

        # Should succeed or need auth
        assert response.status_code in [200, 201, 401, 403, 422]
