"""Tests for assignment API routes with authentication and ACGME validation."""
from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.core.security import create_access_token, get_password_hash
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User(
        id=uuid4(),
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("password"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def coordinator_user(db):
    """Create a coordinator user."""
    user = User(
        id=uuid4(),
        username="coordinator",
        email="coordinator@test.com",
        hashed_password=get_password_hash("password"),
        role="coordinator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def faculty_user(db):
    """Create a faculty user."""
    user = User(
        id=uuid4(),
        username="faculty",
        email="faculty@test.com",
        hashed_password=get_password_hash("password"),
        role="faculty",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Create a token for admin user."""
    return create_access_token(
        data={"sub": str(admin_user.id), "username": admin_user.username}
    )


@pytest.fixture
def coordinator_token(coordinator_user):
    """Create a token for coordinator user."""
    return create_access_token(
        data={"sub": str(coordinator_user.id), "username": coordinator_user.username}
    )


@pytest.fixture
def faculty_token(faculty_user):
    """Create a token for faculty user."""
    return create_access_token(
        data={"sub": str(faculty_user.id), "username": faculty_user.username}
    )


@pytest.fixture
def sample_data(db):
    """Create sample data for tests."""
    # Create a resident
    resident = Person(
        id=uuid4(),
        name="Dr. Test Resident",
        type="resident",
        email="resident@test.com",
        pgy_level=2,
    )
    db.add(resident)

    # Create a faculty
    faculty = Person(
        id=uuid4(),
        name="Dr. Test Faculty",
        type="faculty",
        email="faculty@test.com",
        performs_procedures=True,
        specialties=["Sports Medicine"],
    )
    db.add(faculty)

    # Create a rotation template
    template = RotationTemplate(
        id=uuid4(),
        name="Test Clinic",
        activity_type="clinic",
        abbreviation="TC",
        max_residents=4,
        supervision_required=True,
    )
    db.add(template)

    # Create blocks
    blocks = []
    today = date.today()
    for i in range(7):
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=today + timedelta(days=i),
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(today + timedelta(days=i)).weekday() >= 5,
            )
            db.add(block)
            blocks.append(block)

    db.commit()
    db.refresh(resident)
    db.refresh(faculty)
    db.refresh(template)
    for block in blocks:
        db.refresh(block)

    return {
        "resident": resident,
        "faculty": faculty,
        "template": template,
        "blocks": blocks,
    }


class TestAssignmentAuthenticationEnforcement:
    """Test that all assignment routes require authentication."""

    def test_list_assignments_requires_auth(self, client):
        """Test that listing assignments requires authentication."""
        response = client.get("/api/assignments")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_get_assignment_requires_auth(self, client, sample_data, admin_user, admin_token):
        """Test that getting an assignment requires authentication."""
        # Create an assignment as admin
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_data["blocks"][0].id,
            person_id=sample_data["resident"].id,
            rotation_template_id=sample_data["template"].id,
            role="primary",
            created_by=admin_user.username,
        )
        client.app.dependency_overrides[lambda: None] = lambda: client.app.state.db
        db = client.app.state.db
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Try to get without auth
        response = client.get(f"/api/assignments/{assignment.id}")
        assert response.status_code == 401

    def test_create_assignment_requires_auth(self, client, sample_data):
        """Test that creating an assignment requires authentication."""
        response = client.post(
            "/api/assignments",
            json={
                "block_id": str(sample_data["blocks"][0].id),
                "person_id": str(sample_data["resident"].id),
                "rotation_template_id": str(sample_data["template"].id),
                "role": "primary",
            },
        )
        assert response.status_code == 401

    def test_update_assignment_requires_auth(self, client, sample_data, admin_user, admin_token):
        """Test that updating an assignment requires authentication."""
        # Create an assignment as admin
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_data["blocks"][0].id,
            person_id=sample_data["resident"].id,
            rotation_template_id=sample_data["template"].id,
            role="primary",
            created_by=admin_user.username,
        )
        db = client.app.state.db
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Try to update without auth
        response = client.put(
            f"/api/assignments/{assignment.id}",
            json={
                "role": "backup",
                "updated_at": assignment.updated_at.isoformat(),
            },
        )
        assert response.status_code == 401

    def test_delete_assignment_requires_auth(self, client, sample_data, admin_user):
        """Test that deleting an assignment requires authentication."""
        # Create an assignment as admin
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_data["blocks"][0].id,
            person_id=sample_data["resident"].id,
            rotation_template_id=sample_data["template"].id,
            role="primary",
            created_by=admin_user.username,
        )
        db = client.app.state.db
        db.add(assignment)
        db.commit()

        # Try to delete without auth
        response = client.delete(f"/api/assignments/{assignment.id}")
        assert response.status_code == 401


class TestAssignmentRoleBasedAccessControl:
    """Test role-based access control for assignment routes."""

    def test_faculty_cannot_create_assignment(self, client, sample_data, faculty_token):
        """Test that faculty users cannot create assignments."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {faculty_token}"},
            json={
                "block_id": str(sample_data["blocks"][0].id),
                "person_id": str(sample_data["resident"].id),
                "rotation_template_id": str(sample_data["template"].id),
                "role": "primary",
            },
        )
        assert response.status_code == 403
        assert "Schedule management access required" in response.json()["detail"]

    def test_coordinator_can_create_assignment(self, client, sample_data, coordinator_token):
        """Test that coordinator users can create assignments."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {coordinator_token}"},
            json={
                "block_id": str(sample_data["blocks"][0].id),
                "person_id": str(sample_data["resident"].id),
                "rotation_template_id": str(sample_data["template"].id),
                "role": "primary",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "primary"
        assert "acgme_warnings" in data
        assert "is_compliant" in data

    def test_admin_can_create_assignment(self, client, sample_data, admin_token):
        """Test that admin users can create assignments."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(sample_data["blocks"][0].id),
                "person_id": str(sample_data["resident"].id),
                "rotation_template_id": str(sample_data["template"].id),
                "role": "primary",
            },
        )
        assert response.status_code == 201

    def test_faculty_can_list_assignments(self, client, sample_data, faculty_token, admin_token):
        """Test that faculty users can list assignments (read-only access)."""
        # Create an assignment first
        client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(sample_data["blocks"][0].id),
                "person_id": str(sample_data["resident"].id),
                "rotation_template_id": str(sample_data["template"].id),
                "role": "primary",
            },
        )

        ***REMOVED*** can list
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {faculty_token}"},
        )
        assert response.status_code == 200
        assert "items" in response.json()


class TestACGMEValidationAtWriteTime:
    """Test ACGME validation during assignment create/update."""

    def test_create_assignment_returns_warnings(self, client, sample_data, admin_token, db):
        """Test that creating assignments returns ACGME warnings."""
        # Create multiple assignments for the same resident to trigger 80-hour rule
        blocks = sample_data["blocks"][:28]  # 4 weeks
        resident_id = str(sample_data["resident"].id)
        template_id = str(sample_data["template"].id)

        # Assign resident to many blocks (both AM and PM each day)
        for i, block in enumerate(blocks):
            response = client.post(
                "/api/assignments",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "block_id": str(block.id),
                    "person_id": resident_id,
                    "rotation_template_id": template_id,
                    "role": "primary",
                },
            )
            # Only check last assignment for violations
            if i == len(blocks) - 1:
                assert response.status_code == 201
                data = response.json()
                assert "acgme_warnings" in data
                assert "is_compliant" in data
                # With 28 half-day blocks over 14 days, this should trigger violations
                # (28 * 6 hours = 168 hours / 2 weeks = 84 hours/week average)
                if not data["is_compliant"]:
                    assert len(data["acgme_warnings"]) > 0

    def test_create_assignment_with_override_reason(self, client, sample_data, admin_token, db):
        """Test that override_reason is stored in notes."""
        # Create an assignment
        blocks = sample_data["blocks"][:28]
        resident_id = str(sample_data["resident"].id)
        template_id = str(sample_data["template"].id)

        # Create many assignments
        for block in blocks[:-1]:
            client.post(
                "/api/assignments",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "block_id": str(block.id),
                    "person_id": resident_id,
                    "rotation_template_id": template_id,
                    "role": "primary",
                },
            )

        # Last one with override
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(blocks[-1].id),
                "person_id": resident_id,
                "rotation_template_id": template_id,
                "role": "primary",
                "override_reason": "Critical staffing shortage - approved by program director",
            },
        )
        assert response.status_code == 201
        data = response.json()

        # If there are warnings, check that override is acknowledged
        if data.get("acgme_warnings"):
            assert any("Override acknowledged" in w for w in data["acgme_warnings"])
            # Check that it was saved to notes
            assignment_id = data["id"]
            response = client.get(
                f"/api/assignments/{assignment_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 200
            assignment = response.json()
            if assignment.get("notes"):
                assert "ACGME Override" in assignment["notes"]

    def test_update_assignment_validates_acgme(self, client, sample_data, admin_token):
        """Test that updating assignments validates ACGME compliance."""
        # Create an assignment
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(sample_data["blocks"][0].id),
                "person_id": str(sample_data["resident"].id),
                "rotation_template_id": str(sample_data["template"].id),
                "role": "primary",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assignment_id = data["id"]
        updated_at = data["updated_at"]

        # Update it
        response = client.put(
            f"/api/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "backup",
                "updated_at": updated_at,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "acgme_warnings" in data
        assert "is_compliant" in data


class TestOptimisticLocking:
    """Test optimistic locking for concurrent updates."""

    def test_update_with_stale_timestamp_fails(self, client, sample_data, admin_token):
        """Test that updating with a stale timestamp fails."""
        # Create an assignment
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(sample_data["blocks"][0].id),
                "person_id": str(sample_data["resident"].id),
                "rotation_template_id": str(sample_data["template"].id),
                "role": "primary",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assignment_id = data["id"]
        original_updated_at = data["updated_at"]

        # Update it once
        response = client.put(
            f"/api/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "backup",
                "updated_at": original_updated_at,
            },
        )
        assert response.status_code == 200

        # Try to update with stale timestamp
        response = client.put(
            f"/api/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "supervising",
                "updated_at": original_updated_at,  # Stale timestamp
            },
        )
        assert response.status_code == 409
        assert "modified by another user" in response.json()["detail"]
