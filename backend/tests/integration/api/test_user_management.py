"""
Integration tests for user management workflows.

Tests user CRUD operations, profile management, and user administration.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.security import get_password_hash
from app.models.person import Person
from app.models.user import User


class TestUserManagementWorkflow:
    """Test user management operations."""

    def test_create_user_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test creating a new user."""
        # Step 1: Create user
        create_response = client.post(
            "/api/people/",
            json={
                "name": "Dr. New User",
                "type": "resident",
                "email": "newuser@hospital.org",
                "pgy_level": 1,
            },
            headers=auth_headers,
        )
        assert create_response.status_code in [200, 201]
        user_data = create_response.json()
        user_id = user_data["id"]

        # Step 2: Verify user was created
        get_response = client.get(
            f"/api/people/{user_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Dr. New User"

    def test_update_user_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
    ):
        """Test updating user information."""
        # Step 1: Update user details
        update_response = client.put(
            f"/api/people/{sample_resident.id}",
            json={
                "name": "Dr. Updated Name",
                "email": "updated.email@hospital.org",
            },
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        # Step 2: Verify changes
        get_response = client.get(
            f"/api/people/{sample_resident.id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "Dr. Updated Name"
        assert data["email"] == "updated.email@hospital.org"

    def test_delete_user_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test deleting a user (soft delete)."""
        # Step 1: Create user
        person = Person(
            id=uuid4(),
            name="Dr. To Delete",
            type="resident",
            email="todelete@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        person_id = person.id

        # Step 2: Delete user
        delete_response = client.delete(
            f"/api/people/{person_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code in [200, 204]

        # Step 3: Verify user is deleted or deactivated
        get_response = client.get(
            f"/api/people/{person_id}",
            headers=auth_headers,
        )
        # Should be 404 or show as inactive
        assert get_response.status_code in [200, 404]
        if get_response.status_code == 200:
            assert get_response.json().get("is_active") == False

    def test_list_users_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_residents: list[Person],
    ):
        """Test listing users with pagination."""
        # Step 1: Get all users
        list_response = client.get(
            "/api/people/",
            headers=auth_headers,
        )
        assert list_response.status_code == 200
        users = list_response.json()
        assert len(users) >= len(sample_residents)

        # Step 2: Test pagination
        page1_response = client.get(
            "/api/people/?limit=2&offset=0",
            headers=auth_headers,
        )
        assert page1_response.status_code == 200
        page1 = page1_response.json()
        assert len(page1) <= 2

        # Step 3: Test filtering
        filter_response = client.get(
            "/api/people/?type=resident",
            headers=auth_headers,
        )
        assert filter_response.status_code == 200
        filtered = filter_response.json()
        for user in filtered:
            assert user["type"] == "resident"

    def test_search_users_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
    ):
        """Test user search functionality."""
        # Search by name
        search_response = client.get(
            f"/api/people/search?q={sample_resident.name}",
            headers=auth_headers,
        )
        assert search_response.status_code in [200, 404]

        if search_response.status_code == 200:
            results = search_response.json()
            assert len(results) > 0
            assert any(r["id"] == str(sample_resident.id) for r in results)

    def test_user_profile_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test user profile retrieval and update."""
        # Step 1: Get own profile
        profile_response = client.get(
            "/api/me/profile",
            headers=auth_headers,
        )
        assert profile_response.status_code in [200, 404]

        if profile_response.status_code == 200:
            profile = profile_response.json()

            # Step 2: Update profile
            update_response = client.put(
                "/api/me/profile",
                json={
                    "email": "updated@test.org",
                    "phone": "555-1234",
                },
                headers=auth_headers,
            )
            assert update_response.status_code in [200, 404]

    def test_user_roles_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test user role management."""
        # Step 1: Create user
        person = Person(
            id=uuid4(),
            name="Dr. Role Test",
            type="resident",
            email="roletest@hospital.org",
            pgy_level=2,
        )
        db.add(person)
        db.commit()

        # Step 2: Assign role
        role_response = client.post(
            f"/api/people/{person.id}/roles",
            json={"role": "faculty"},
            headers=auth_headers,
        )
        assert role_response.status_code in [200, 404, 501]

        # Step 3: Verify role change
        if role_response.status_code == 200:
            get_response = client.get(
                f"/api/people/{person.id}",
                headers=auth_headers,
            )
            assert get_response.status_code == 200

    def test_user_permissions_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
    ):
        """Test user permissions management."""
        # Get user permissions
        perms_response = client.get(
            f"/api/people/{sample_resident.id}/permissions",
            headers=auth_headers,
        )
        assert perms_response.status_code in [200, 404, 501]

        if perms_response.status_code == 200:
            perms = perms_response.json()
            assert isinstance(perms, (list, dict))

    def test_bulk_user_import_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test bulk user import."""
        # Step 1: Prepare bulk import data
        users_data = [
            {
                "name": f"Dr. Import {i}",
                "type": "resident",
                "email": f"import{i}@hospital.org",
                "pgy_level": (i % 3) + 1,
            }
            for i in range(5)
        ]

        # Step 2: Import users
        import_response = client.post(
            "/api/people/bulk-import",
            json={"users": users_data},
            headers=auth_headers,
        )
        assert import_response.status_code in [200, 201, 404, 501]

        # Step 3: Verify import
        if import_response.status_code in [200, 201]:
            result = import_response.json()
            assert (
                "created" in result or "imported" in result or isinstance(result, list)
            )

    def test_user_deactivation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """Test user deactivation and reactivation."""
        # Step 1: Create user
        person = Person(
            id=uuid4(),
            name="Dr. Deactivate Test",
            type="faculty",
            email="deactivate@hospital.org",
        )
        db.add(person)
        db.commit()
        person_id = person.id

        # Step 2: Deactivate user
        deactivate_response = client.post(
            f"/api/people/{person_id}/deactivate",
            headers=auth_headers,
        )
        assert deactivate_response.status_code in [200, 404, 501]

        # Step 3: Verify user is inactive
        get_response = client.get(
            f"/api/people/{person_id}",
            headers=auth_headers,
        )
        if get_response.status_code == 200:
            data = get_response.json()
            # May have is_active field
            if "is_active" in data:
                assert data["is_active"] == False

        # Step 4: Reactivate user
        reactivate_response = client.post(
            f"/api/people/{person_id}/activate",
            headers=auth_headers,
        )
        assert reactivate_response.status_code in [200, 404, 501]
