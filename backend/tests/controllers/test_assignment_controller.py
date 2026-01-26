"""Tests for AssignmentController."""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.assignment_controller import AssignmentController
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.core.security import get_password_hash


class TestAssignmentController:
    """Test suite for AssignmentController."""

    @pytest.fixture
    def setup_data(self, db):
        """Create common test data."""
        # Create a resident
        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=2,
        )
        db.add(resident)

        # Create a faculty
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            type="faculty",
            email="faculty@hospital.org",
        )
        db.add(faculty)

        # Create a block
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=30),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)

        # Create a rotation template
        template = RotationTemplate(
            id=uuid4(),
            name="Test Rotation",
            rotation_type="outpatient",
            abbreviation="TR",
            max_residents=4,
            supervision_required=True,
        )
        db.add(template)

        # Create a user for auth
        user = User(
            id=uuid4(),
            username="testuser",
            email="testuser@test.org",
            hashed_password=get_password_hash("Password123!"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)

        db.commit()

        return {
            "resident": resident,
            "faculty": faculty,
            "block": block,
            "template": template,
            "user": user,
        }

    # ========================================================================
    # List Assignments Tests
    # ========================================================================

    def test_list_assignments_no_filters(self, db, setup_data):
        """Test listing all assignments without filters."""
        # Create some assignments
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=date.today() + timedelta(days=i + 40),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=setup_data["resident"].id,
                rotation_template_id=setup_data["template"].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        controller = AssignmentController(db)
        result = controller.list_assignments()

        assert result["total"] >= 3
        assert len(result["items"]) >= 3

    def test_list_assignments_with_date_filter(self, db, setup_data):
        """Test listing assignments with date range filter."""
        start_date = date.today() + timedelta(days=50)

        # Create blocks and assignments
        for i in range(5):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=setup_data["resident"].id,
                rotation_template_id=setup_data["template"].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        controller = AssignmentController(db)
        result = controller.list_assignments(
            start_date=start_date,
            end_date=start_date + timedelta(days=2),
        )

        assert result["total"] >= 3

    def test_list_assignments_with_person_filter(self, db, setup_data):
        """Test listing assignments for specific person."""
        # Create another resident with assignments
        other_resident = Person(
            id=uuid4(),
            name="Other Resident",
            type="resident",
            email="other@hospital.org",
            pgy_level=1,
        )
        db.add(other_resident)
        db.commit()

        # Create assignments for different residents
        block1 = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=60),
            time_of_day="AM",
            block_number=1,
        )
        block2 = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=61),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([block1, block2])
        db.commit()

        assignment1 = Assignment(
            id=uuid4(),
            block_id=block1.id,
            person_id=setup_data["resident"].id,
            rotation_template_id=setup_data["template"].id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=block2.id,
            person_id=other_resident.id,
            rotation_template_id=setup_data["template"].id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        controller = AssignmentController(db)
        result = controller.list_assignments(person_id=setup_data["resident"].id)

        # Should include the original resident's assignments
        assert all(
            item.person_id == setup_data["resident"].id
            for item in result["items"]
            if hasattr(item, "person_id")
        )

    def test_list_assignments_pagination(self, db, setup_data):
        """Test assignment list pagination."""
        # Create 10 assignments
        for i in range(10):
            block = Block(
                id=uuid4(),
                date=date.today() + timedelta(days=70 + i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=setup_data["resident"].id,
                rotation_template_id=setup_data["template"].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        controller = AssignmentController(db)

        # Get first page
        page1 = controller.list_assignments(page=1, page_size=5)
        assert len(page1["items"]) <= 5
        assert page1["page"] == 1
        assert page1["page_size"] == 5

    # ========================================================================
    # Get Assignment Tests
    # ========================================================================

    def test_get_assignment_success(self, db, setup_data):
        """Test getting a single assignment by ID."""
        assignment = Assignment(
            id=uuid4(),
            block_id=setup_data["block"].id,
            person_id=setup_data["resident"].id,
            rotation_template_id=setup_data["template"].id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        controller = AssignmentController(db)
        result = controller.get_assignment(assignment.id)

        assert result is not None
        assert result.id == assignment.id

    def test_get_assignment_not_found(self, db):
        """Test getting a non-existent assignment raises 404."""
        controller = AssignmentController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_assignment(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    # ========================================================================
    # Create Assignment Tests
    # ========================================================================

    def test_create_assignment_success(self, db, setup_data):
        """Test creating an assignment."""
        controller = AssignmentController(db)

        assignment_data = AssignmentCreate(
            block_id=setup_data["block"].id,
            person_id=setup_data["resident"].id,
            role="primary",
            rotation_template_id=setup_data["template"].id,
        )

        result = controller.create_assignment(assignment_data, setup_data["user"])

        assert result is not None
        assert result.role == "primary"

    def test_create_assignment_with_notes(self, db, setup_data):
        """Test creating an assignment with notes."""
        # Create a new block to avoid conflicts
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=90),
            time_of_day="PM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        controller = AssignmentController(db)

        assignment_data = AssignmentCreate(
            block_id=block.id,
            person_id=setup_data["resident"].id,
            role="primary",
            rotation_template_id=setup_data["template"].id,
            notes="Test notes",
        )

        result = controller.create_assignment(assignment_data, setup_data["user"])

        assert result is not None

    def test_create_assignment_invalid_block(self, db, setup_data):
        """Test creating assignment with non-existent block fails."""
        controller = AssignmentController(db)

        assignment_data = AssignmentCreate(
            block_id=uuid4(),  # Non-existent block
            person_id=setup_data["resident"].id,
            role="primary",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_assignment(assignment_data, setup_data["user"])

        assert exc_info.value.status_code == 400

    def test_create_assignment_invalid_person(self, db, setup_data):
        """Test creating assignment with non-existent person fails."""
        controller = AssignmentController(db)

        assignment_data = AssignmentCreate(
            block_id=setup_data["block"].id,
            person_id=uuid4(),  # Non-existent person
            role="primary",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_assignment(assignment_data, setup_data["user"])

        assert exc_info.value.status_code == 400

    # ========================================================================
    # Update Assignment Tests
    # ========================================================================

    def test_update_assignment_success(self, db, setup_data):
        """Test updating an assignment."""
        # Create another block for update
        new_block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=100),
            time_of_day="PM",
            block_number=2,
        )
        db.add(new_block)

        assignment = Assignment(
            id=uuid4(),
            block_id=setup_data["block"].id,
            person_id=setup_data["resident"].id,
            rotation_template_id=setup_data["template"].id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        controller = AssignmentController(db)

        update_data = AssignmentUpdate(
            role="backup",
            updated_at=assignment.updated_at,
        )
        result = controller.update_assignment(assignment.id, update_data)

        assert result.role == "backup"

    def test_update_assignment_not_found(self, db, setup_data):
        """Test updating non-existent assignment raises 404."""
        controller = AssignmentController(db)

        update_data = AssignmentUpdate(role="backup")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_assignment(uuid4(), update_data)

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Delete Assignment Tests
    # ========================================================================

    def test_delete_assignment_success(self, db, setup_data):
        """Test deleting an assignment."""
        assignment = Assignment(
            id=uuid4(),
            block_id=setup_data["block"].id,
            person_id=setup_data["resident"].id,
            rotation_template_id=setup_data["template"].id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        assignment_id = assignment.id

        controller = AssignmentController(db)
        controller.delete_assignment(assignment_id)

        # Verify deletion
        deleted = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        assert deleted is None

    def test_delete_assignment_not_found(self, db):
        """Test deleting non-existent assignment raises 404."""
        controller = AssignmentController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_assignment(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Bulk Delete Tests
    # ========================================================================

    def test_delete_assignments_bulk(self, db, setup_data):
        """Test bulk deleting assignments in date range."""
        start = date.today() + timedelta(days=110)

        # Create assignments for 5 days
        for i in range(5):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=setup_data["resident"].id,
                rotation_template_id=setup_data["template"].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        controller = AssignmentController(db)
        result = controller.delete_assignments_bulk(
            start_date=start,
            end_date=start + timedelta(days=2),
        )

        assert result["deleted_count"] >= 3

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_create_get_update_delete_workflow(self, db, setup_data):
        """Test complete CRUD workflow for assignment."""
        controller = AssignmentController(db)

        # Create new block for this workflow
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=120),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        # Create
        assignment_data = AssignmentCreate(
            block_id=block.id,
            person_id=setup_data["resident"].id,
            role="primary",
            rotation_template_id=setup_data["template"].id,
        )
        created = controller.create_assignment(assignment_data, setup_data["user"])
        assignment_id = created.id

        # Get
        retrieved = controller.get_assignment(assignment_id)
        assert retrieved.id == assignment_id

        # Update
        update_data = AssignmentUpdate(
            role="backup",
            updated_at=retrieved.updated_at,
        )
        updated = controller.update_assignment(assignment_id, update_data)
        assert updated.role == "backup"

        # Delete
        controller.delete_assignment(assignment_id)

        # Verify deletion
        with pytest.raises(HTTPException):
            controller.get_assignment(assignment_id)
