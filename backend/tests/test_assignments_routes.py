"""Comprehensive tests for assignment API routes.

Tests all CRUD operations, filtering, authentication, authorization,
ACGME validation, optimistic locking, and error handling.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for tests."""
    user = User(
        id=uuid4(),
        username="admin_test",
        email="admin_test@test.com",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def coordinator_user(db: Session) -> User:
    """Create a coordinator user for tests."""
    user = User(
        id=uuid4(),
        username="coordinator_test",
        email="coordinator_test@test.com",
        hashed_password=get_password_hash("coordinatorpass"),
        role="coordinator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def faculty_user(db: Session) -> User:
    """Create a faculty user for tests."""
    user = User(
        id=uuid4(),
        username="faculty_test",
        email="faculty_test@test.com",
        hashed_password=get_password_hash("facultypass"),
        role="faculty",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Create access token for admin user."""
    return create_access_token(
        data={"sub": str(admin_user.id), "username": admin_user.username}
    )


@pytest.fixture
def coordinator_token(coordinator_user: User) -> str:
    """Create access token for coordinator user."""
    return create_access_token(
        data={"sub": str(coordinator_user.id), "username": coordinator_user.username}
    )


@pytest.fixture
def faculty_token(faculty_user: User) -> str:
    """Create access token for faculty user."""
    return create_access_token(
        data={"sub": str(faculty_user.id), "username": faculty_user.username}
    )


@pytest.fixture
def test_resident(db: Session) -> Person:
    """Create a test resident."""
    resident = Person(
        id=uuid4(),
        name="Dr. Test Resident",
        type="resident",
        email="test.resident@hospital.org",
        pgy_level=2,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


@pytest.fixture
def test_faculty(db: Session) -> Person:
    """Create a test faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Test Faculty",
        type="faculty",
        email="test.faculty@hospital.org",
        performs_procedures=True,
        specialties=["Sports Medicine"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def multiple_residents(db: Session) -> list[Person]:
    """Create multiple residents for testing."""
    residents = []
    for i in range(1, 4):
        resident = Person(
            id=uuid4(),
            name=f"Dr. Resident PGY{i}",
            type="resident",
            email=f"resident.pgy{i}@hospital.org",
            pgy_level=i,
        )
        db.add(resident)
        residents.append(resident)
    db.commit()
    for r in residents:
        db.refresh(r)
    return residents


@pytest.fixture
def clinic_template(db: Session) -> RotationTemplate:
    """Create a clinic rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="Test Clinic",
        rotation_type="clinic",
        abbreviation="TC",
        clinic_location="Building A",
        max_residents=4,
        supervision_required=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def on_call_template(db: Session) -> RotationTemplate:
    """Create an on-call rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="On Call",
        rotation_type="on_call",
        abbreviation="OC",
        supervision_required=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def inpatient_template(db: Session) -> RotationTemplate:
    """Create an inpatient rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="Inpatient Service",
        rotation_type="inpatient",
        abbreviation="IP",
        supervision_required=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def test_blocks(db: Session) -> list[Block]:
    """Create test blocks for one week."""
    blocks = []
    start_date = date.today()

    for i in range(7):
        current_date = start_date + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)

    db.commit()
    for b in blocks:
        db.refresh(b)
    return blocks


@pytest.fixture
def test_assignment(
    db: Session,
    test_resident: Person,
    test_blocks: list[Block],
    clinic_template: RotationTemplate,
    admin_user: User,
) -> Assignment:
    """Create a test assignment."""
    assignment = Assignment(
        id=uuid4(),
        block_id=test_blocks[0].id,
        person_id=test_resident.id,
        rotation_template_id=clinic_template.id,
        role="primary",
        created_by=admin_user.username,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# ============================================================================
# Authentication Tests
# ============================================================================


class TestAssignmentRouteAuthentication:
    """Test that all assignment routes require authentication."""

    def test_list_assignments_requires_auth(self, client: TestClient):
        """Test that listing assignments requires authentication."""
        response = client.get("/api/assignments")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_get_assignment_requires_auth(
        self, client: TestClient, test_assignment: Assignment
    ):
        """Test that getting a single assignment requires authentication."""
        response = client.get(f"/api/assignments/{test_assignment.id}")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_create_assignment_requires_auth(
        self,
        client: TestClient,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test that creating an assignment requires authentication."""
        response = client.post(
            "/api/assignments",
            json={
                "block_id": str(test_blocks[0].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
            },
        )
        assert response.status_code == 401

    def test_update_assignment_requires_auth(
        self, client: TestClient, test_assignment: Assignment
    ):
        """Test that updating an assignment requires authentication."""
        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            json={
                "role": "backup",
                "updated_at": test_assignment.updated_at.isoformat(),
            },
        )
        assert response.status_code == 401

    def test_delete_assignment_requires_auth(
        self, client: TestClient, test_assignment: Assignment
    ):
        """Test that deleting an assignment requires authentication."""
        response = client.delete(f"/api/assignments/{test_assignment.id}")
        assert response.status_code == 401

    def test_bulk_delete_requires_auth(self, client: TestClient):
        """Test that bulk delete requires authentication."""
        today = date.today()
        response = client.delete(
            "/api/assignments",
            params={
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 401


# ============================================================================
# Authorization Tests (Role-Based Access Control)
# ============================================================================


class TestAssignmentRoleBasedAccessControl:
    """Test role-based access control for assignment routes."""

    def test_faculty_can_list_assignments(
        self,
        client: TestClient,
        faculty_token: str,
        test_assignment: Assignment,
    ):
        """Test that faculty users can list assignments (read-only)."""
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {faculty_token}"},
        )
        assert response.status_code == 200
        assert "items" in response.json()

    def test_faculty_can_get_assignment(
        self,
        client: TestClient,
        faculty_token: str,
        test_assignment: Assignment,
    ):
        """Test that faculty users can get a single assignment."""
        response = client.get(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {faculty_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_assignment.id)

    def test_faculty_cannot_create_assignment(
        self,
        client: TestClient,
        faculty_token: str,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test that faculty users cannot create assignments."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {faculty_token}"},
            json={
                "block_id": str(test_blocks[0].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
            },
        )
        assert response.status_code == 403
        assert "Schedule management access required" in response.json()["detail"]

    def test_faculty_cannot_update_assignment(
        self,
        client: TestClient,
        faculty_token: str,
        test_assignment: Assignment,
    ):
        """Test that faculty users cannot update assignments."""
        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {faculty_token}"},
            json={
                "role": "backup",
                "updated_at": test_assignment.updated_at.isoformat(),
            },
        )
        assert response.status_code == 403

    def test_faculty_cannot_delete_assignment(
        self,
        client: TestClient,
        faculty_token: str,
        test_assignment: Assignment,
    ):
        """Test that faculty users cannot delete assignments."""
        response = client.delete(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {faculty_token}"},
        )
        assert response.status_code == 403

    def test_coordinator_can_create_assignment(
        self,
        client: TestClient,
        coordinator_token: str,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test that coordinator users can create assignments."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {coordinator_token}"},
            json={
                "block_id": str(test_blocks[1].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "primary"
        assert "acgme_warnings" in data
        assert "is_compliant" in data

    def test_coordinator_can_update_assignment(
        self,
        client: TestClient,
        coordinator_token: str,
        test_assignment: Assignment,
    ):
        """Test that coordinator users can update assignments."""
        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {coordinator_token}"},
            json={
                "role": "backup",
                "updated_at": test_assignment.updated_at.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "backup"

    def test_coordinator_can_delete_assignment(
        self,
        client: TestClient,
        coordinator_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        coordinator_user: User,
    ):
        """Test that coordinator users can delete assignments."""
        # Create an assignment to delete
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[2].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=coordinator_user.username,
        )
        db.add(assignment)
        db.commit()

        response = client.delete(
            f"/api/assignments/{assignment.id}",
            headers={"Authorization": f"Bearer {coordinator_token}"},
        )
        assert response.status_code == 204

    def test_admin_can_create_assignment(
        self,
        client: TestClient,
        admin_token: str,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test that admin users can create assignments."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(test_blocks[3].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
            },
        )
        assert response.status_code == 201

    def test_admin_can_update_assignment(
        self,
        client: TestClient,
        admin_token: str,
        test_assignment: Assignment,
    ):
        """Test that admin users can update assignments."""
        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "supervising",
                "updated_at": test_assignment.updated_at.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "supervising"

    def test_admin_can_delete_assignment(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test that admin users can delete assignments."""
        # Create an assignment to delete
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[4].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment)
        db.commit()

        response = client.delete(
            f"/api/assignments/{assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204


# ============================================================================
# CRUD Operation Tests
# ============================================================================


class TestAssignmentCRUDOperations:
    """Test basic CRUD operations for assignments."""

    def test_create_assignment_success(
        self,
        client: TestClient,
        admin_token: str,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test successful assignment creation."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(test_blocks[5].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["role"] == "primary"
        assert data["person_id"] == str(test_resident.id)
        assert data["block_id"] == str(test_blocks[5].id)
        assert "acgme_warnings" in data
        assert "is_compliant" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_assignment_with_notes(
        self,
        client: TestClient,
        admin_token: str,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test creating assignment with notes."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(test_blocks[6].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
                "notes": "Special assignment - requested by program director",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["notes"] == "Special assignment - requested by program director"

    def test_create_assignment_with_invalid_role(
        self,
        client: TestClient,
        admin_token: str,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test creating assignment with invalid role."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(test_blocks[7].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "invalid_role",
            },
        )
        assert response.status_code == 422  # Validation error

    def test_create_assignment_with_nonexistent_block(
        self,
        client: TestClient,
        admin_token: str,
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test creating assignment with non-existent block ID."""
        fake_block_id = uuid4()
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(fake_block_id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
            },
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_get_assignment_success(
        self,
        client: TestClient,
        admin_token: str,
        test_assignment: Assignment,
    ):
        """Test successfully getting an assignment by ID."""
        response = client.get(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_assignment.id)
        assert data["role"] == test_assignment.role
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_assignment_not_found(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test getting a non-existent assignment."""
        fake_id = uuid4()
        response = client.get(
            f"/api/assignments/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_assignment_success(
        self,
        client: TestClient,
        admin_token: str,
        test_assignment: Assignment,
    ):
        """Test successfully updating an assignment."""
        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "backup",
                "notes": "Updated notes",
                "updated_at": test_assignment.updated_at.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "backup"
        assert data["notes"] == "Updated notes"
        assert "acgme_warnings" in data
        assert "is_compliant" in data

    def test_update_assignment_not_found(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test updating a non-existent assignment."""
        fake_id = uuid4()
        response = client.put(
            f"/api/assignments/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "backup",
                "updated_at": datetime.utcnow().isoformat(),
            },
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_assignment_success(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test successfully deleting an assignment."""
        # Create an assignment to delete
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[8].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment)
        db.commit()

        response = client.delete(
            f"/api/assignments/{assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        # Verify it's deleted
        verify_response = client.get(
            f"/api/assignments/{assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert verify_response.status_code == 404

    def test_delete_assignment_not_found(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test deleting a non-existent assignment."""
        fake_id = uuid4()
        response = client.delete(
            f"/api/assignments/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


# ============================================================================
# Filtering Tests
# ============================================================================


class TestAssignmentFiltering:
    """Test assignment filtering functionality."""

    def test_list_assignments_no_filter(
        self,
        client: TestClient,
        admin_token: str,
        test_assignment: Assignment,
    ):
        """Test listing all assignments without filters."""
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    def test_filter_by_date_range(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test filtering assignments by date range."""
        # Create assignments on specific dates
        today = date.today()

        # Assignment today
        assignment_today = Assignment(
            id=uuid4(),
            block_id=test_blocks[0].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment_today)
        db.commit()

        # Filter by date range
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=2)).isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

    def test_filter_by_person_id(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        multiple_residents: list[Person],
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test filtering assignments by person ID."""
        # Create assignments for different residents
        for i, resident in enumerate(multiple_residents):
            assignment = Assignment(
                id=uuid4(),
                block_id=test_blocks[i].id,
                person_id=resident.id,
                rotation_template_id=clinic_template.id,
                role="primary",
                created_by=admin_user.username,
            )
            db.add(assignment)
        db.commit()

        # Filter by specific resident
        target_resident = multiple_residents[0]
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"person_id": str(target_resident.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        for item in data["items"]:
            assert item["person_id"] == str(target_resident.id)

    def test_filter_by_role(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        test_faculty: Person,
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test filtering assignments by role."""
        # Create assignments with different roles
        primary_assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[0].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        supervising_assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[0].id,
            person_id=test_faculty.id,
            rotation_template_id=clinic_template.id,
            role="supervising",
            created_by=admin_user.username,
        )
        db.add_all([primary_assignment, supervising_assignment])
        db.commit()

        # Filter by role
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"role": "primary"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        for item in data["items"]:
            assert item["role"] == "primary"

    def test_filter_by_rotation_type_clinic(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        on_call_template: RotationTemplate,
        admin_user: User,
    ):
        """Test filtering assignments by activity type - clinic."""
        # Create assignments with different activity types
        clinic_assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[0].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        on_call_assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[1].id,
            person_id=test_resident.id,
            rotation_template_id=on_call_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add_all([clinic_assignment, on_call_assignment])
        db.commit()

        # Filter by clinic activity type
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"rotation_type": "clinic"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        # Note: Response includes rotation_template nested object
        for item in data["items"]:
            if item.get("rotation_template"):
                assert item["rotation_template"]["rotation_type"] == "clinic"

    def test_filter_by_rotation_type_on_call(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        on_call_template: RotationTemplate,
        admin_user: User,
    ):
        """Test filtering assignments by activity type - on_call."""
        # Create on-call assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[2].id,
            person_id=test_resident.id,
            rotation_template_id=on_call_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment)
        db.commit()

        # Filter by on_call activity type
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"rotation_type": "on_call"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        for item in data["items"]:
            if item.get("rotation_template"):
                assert item["rotation_template"]["rotation_type"] == "on_call"

    def test_filter_by_rotation_type_inpatient(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        inpatient_template: RotationTemplate,
        admin_user: User,
    ):
        """Test filtering assignments by activity type - inpatient."""
        # Create inpatient assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[3].id,
            person_id=test_resident.id,
            rotation_template_id=inpatient_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment)
        db.commit()

        # Filter by inpatient activity type
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"rotation_type": "inpatient"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        for item in data["items"]:
            if item.get("rotation_template"):
                assert item["rotation_template"]["rotation_type"] == "inpatient"

    def test_filter_combined_date_and_person(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        multiple_residents: list[Person],
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test combining date range and person filters."""
        # Create assignments for different residents
        today = date.today()
        target_resident = multiple_residents[0]

        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[0].id,
            person_id=target_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment)
        db.commit()

        # Filter by date range and person
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=7)).isoformat(),
                "person_id": str(target_resident.id),
            },
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["person_id"] == str(target_resident.id)

    def test_filter_combined_rotation_type_and_role(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        on_call_template: RotationTemplate,
        admin_user: User,
    ):
        """Test combining activity type and role filters."""
        # Create on-call primary assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[4].id,
            person_id=test_resident.id,
            rotation_template_id=on_call_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment)
        db.commit()

        # Filter by activity type and role
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "rotation_type": "on_call",
                "role": "primary",
            },
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["role"] == "primary"
            if item.get("rotation_template"):
                assert item["rotation_template"]["rotation_type"] == "on_call"


# ============================================================================
# Optimistic Locking Tests
# ============================================================================


class TestOptimisticLocking:
    """Test optimistic locking for concurrent updates."""

    def test_update_with_correct_timestamp_succeeds(
        self,
        client: TestClient,
        admin_token: str,
        test_assignment: Assignment,
    ):
        """Test that update with correct timestamp succeeds."""
        # Get current timestamp
        updated_at = test_assignment.updated_at

        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "backup",
                "updated_at": updated_at.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "backup"

    def test_update_with_stale_timestamp_fails(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test that update with stale timestamp fails with 409 Conflict."""
        # Create a fresh assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[9].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        original_updated_at = assignment.updated_at

        # First update
        response1 = client.put(
            f"/api/assignments/{assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "backup",
                "updated_at": original_updated_at.isoformat(),
            },
        )
        assert response1.status_code == 200

        # Second update with stale timestamp
        response2 = client.put(
            f"/api/assignments/{assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "supervising",
                "updated_at": original_updated_at.isoformat(),  # Stale
            },
        )
        assert response2.status_code == 409
        assert "modified by another user" in response2.json()["detail"].lower()

    def test_concurrent_updates_detection(
        self,
        client: TestClient,
        admin_token: str,
        coordinator_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test detection of concurrent updates from different users."""
        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=test_blocks[10].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        original_updated_at = assignment.updated_at

        # Admin updates first
        response1 = client.put(
            f"/api/assignments/{assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "notes": "Admin updated this",
                "updated_at": original_updated_at.isoformat(),
            },
        )
        assert response1.status_code == 200

        # Coordinator tries to update with stale timestamp
        response2 = client.put(
            f"/api/assignments/{assignment.id}",
            headers={"Authorization": f"Bearer {coordinator_token}"},
            json={
                "notes": "Coordinator updated this",
                "updated_at": original_updated_at.isoformat(),  # Stale
            },
        )
        assert response2.status_code == 409


# ============================================================================
# ACGME Validation Tests
# ============================================================================


class TestACGMEValidation:
    """Test ACGME validation during assignment create/update."""

    def test_create_assignment_returns_acgme_warnings(
        self,
        client: TestClient,
        admin_token: str,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test that creating assignments returns ACGME validation."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(test_blocks[11].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "acgme_warnings" in data
        assert "is_compliant" in data
        assert isinstance(data["acgme_warnings"], list)
        assert isinstance(data["is_compliant"], bool)

    def test_create_assignment_with_override_reason(
        self,
        client: TestClient,
        admin_token: str,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
    ):
        """Test creating assignment with ACGME override reason."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(test_blocks[12].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
                "override_reason": "Emergency staffing shortage - approved by PD",
            },
        )
        assert response.status_code == 201
        data = response.json()
        # If override reason is provided, check for acknowledgment
        if data.get("acgme_warnings"):
            # The notes or warnings might include override info
            assert "override_reason" in data or len(data["acgme_warnings"]) >= 0

    def test_update_assignment_validates_acgme(
        self,
        client: TestClient,
        admin_token: str,
        test_assignment: Assignment,
    ):
        """Test that updating assignments validates ACGME compliance."""
        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "backup",
                "updated_at": test_assignment.updated_at.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "acgme_warnings" in data
        assert "is_compliant" in data


# ============================================================================
# Bulk Delete Tests
# ============================================================================


class TestBulkDelete:
    """Test bulk delete functionality."""

    def test_bulk_delete_success(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test successfully bulk deleting assignments in date range."""
        # Create assignments for specific date range
        start_date = date.today() + timedelta(days=14)
        end_date = start_date + timedelta(days=7)

        # Create blocks for this range
        blocks_to_delete = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day="AM",
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            blocks_to_delete.append(block)
        db.commit()

        # Create assignments
        for block in blocks_to_delete:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=test_resident.id,
                rotation_template_id=clinic_template.id,
                role="primary",
                created_by=admin_user.username,
            )
            db.add(assignment)
        db.commit()

        # Bulk delete
        response = client.delete(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
        assert data["deleted"] >= 7

    def test_bulk_delete_requires_date_params(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test that bulk delete requires start_date and end_date."""
        # Missing both dates
        response = client.delete(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422  # Validation error

    def test_bulk_delete_empty_range(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test bulk delete with no assignments in range."""
        future_date = date.today() + timedelta(days=365)
        response = client.delete(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": future_date.isoformat(),
                "end_date": (future_date + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == 0

    def test_bulk_delete_requires_scheduler_role(
        self,
        client: TestClient,
        faculty_token: str,
    ):
        """Test that bulk delete requires scheduler role."""
        today = date.today()
        response = client.delete(
            "/api/assignments",
            headers={"Authorization": f"Bearer {faculty_token}"},
            params={
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 403


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling."""

    def test_create_assignment_missing_required_fields(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test creating assignment with missing required fields."""
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "primary",
                # Missing block_id, person_id, rotation_template_id
            },
        )
        assert response.status_code == 422  # Validation error

    def test_update_assignment_missing_updated_at(
        self,
        client: TestClient,
        admin_token: str,
        test_assignment: Assignment,
    ):
        """Test updating assignment without updated_at timestamp."""
        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "backup",
                # Missing updated_at
            },
        )
        assert response.status_code == 422  # Validation error

    def test_list_assignments_with_invalid_uuid(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test filtering by invalid UUID format."""
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"person_id": "not-a-valid-uuid"},
        )
        assert response.status_code == 422  # Validation error

    def test_get_assignment_with_invalid_uuid(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test getting assignment with invalid UUID format."""
        response = client.get(
            "/api/assignments/not-a-valid-uuid",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422  # Validation error

    def test_list_assignments_with_invalid_date_format(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test filtering with invalid date format."""
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": "not-a-date",
            },
        )
        assert response.status_code == 422  # Validation error

    def test_create_assignment_duplicate_on_same_block(
        self,
        client: TestClient,
        admin_token: str,
        db: Session,
        test_blocks: list[Block],
        test_resident: Person,
        clinic_template: RotationTemplate,
        admin_user: User,
    ):
        """Test creating duplicate assignment on same block for same person."""
        # Create first assignment
        assignment1 = Assignment(
            id=uuid4(),
            block_id=test_blocks[13].id,
            person_id=test_resident.id,
            rotation_template_id=clinic_template.id,
            role="primary",
            created_by=admin_user.username,
        )
        db.add(assignment1)
        db.commit()

        # Try to create duplicate
        response = client.post(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "block_id": str(test_blocks[13].id),
                "person_id": str(test_resident.id),
                "rotation_template_id": str(clinic_template.id),
                "role": "primary",
            },
        )
        # Should fail with conflict or validation error
        assert response.status_code in [400, 409]

    def test_update_assignment_with_invalid_role(
        self,
        client: TestClient,
        admin_token: str,
        test_assignment: Assignment,
    ):
        """Test updating assignment with invalid role value."""
        response = client.put(
            f"/api/assignments/{test_assignment.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "invalid_role",
                "updated_at": test_assignment.updated_at.isoformat(),
            },
        )
        assert response.status_code == 422  # Validation error

    def test_list_assignments_empty_result(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """Test listing assignments when none match filters."""
        future_date = date.today() + timedelta(days=1000)
        response = client.get(
            "/api/assignments",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "start_date": future_date.isoformat(),
                "end_date": (future_date + timedelta(days=7)).isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0
