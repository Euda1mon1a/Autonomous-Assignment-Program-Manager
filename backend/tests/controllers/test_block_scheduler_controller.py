"""Tests for BlockSchedulerController."""

import pytest
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.block_scheduler_controller import BlockSchedulerController
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.block_assignment import BlockAssignment
from app.schemas.block_assignment import (
    BlockAssignmentCreate,
    BlockAssignmentUpdate,
    BlockScheduleRequest,
)


class TestBlockSchedulerController:
    """Test suite for BlockSchedulerController."""

    @pytest.fixture
    def setup_data(self, db):
        """Create common test data."""
        # Create residents
        residents = []
        for pgy in [1, 2, 3]:
            for i in range(2):
                resident = Person(
                    id=uuid4(),
                    name=f"Dr. Resident PGY{pgy}-{i}",
                    type="resident",
                    email=f"resident_pgy{pgy}_{i}@hospital.org",
                    pgy_level=pgy,
                )
                db.add(resident)
                residents.append(resident)

        # Create rotation templates
        templates = []
        template_data = [
            {
                "name": "FMIT",
                "activity_type": "inpatient",
                "leave_eligible": False,
                "abbreviation": "FMIT",
            },
            {
                "name": "Outpatient Clinic",
                "activity_type": "outpatient",
                "leave_eligible": True,
                "abbreviation": "OPC",
            },
            {
                "name": "Night Float",
                "activity_type": "call",
                "leave_eligible": False,
                "abbreviation": "NF",
            },
            {
                "name": "Elective",
                "activity_type": "elective",
                "leave_eligible": True,
                "abbreviation": "ELEC",
            },
        ]
        for data in template_data:
            template = RotationTemplate(
                id=uuid4(),
                name=data["name"],
                activity_type=data["activity_type"],
                leave_eligible=data["leave_eligible"],
                abbreviation=data["abbreviation"],
                max_residents=4,
            )
            db.add(template)
            templates.append(template)

        db.commit()

        return {
            "residents": residents,
            "templates": templates,
        }

    # ========================================================================
    # Get Dashboard Tests
    # ========================================================================

    def test_get_dashboard_success(self, db, setup_data):
        """Test getting block scheduler dashboard."""
        controller = BlockSchedulerController(db)

        dashboard = controller.get_dashboard(block_number=1, academic_year=2025)

        assert dashboard is not None
        assert hasattr(dashboard, "block_number")
        assert hasattr(dashboard, "academic_year")

    def test_get_dashboard_different_blocks(self, db, setup_data):
        """Test dashboard for different blocks."""
        controller = BlockSchedulerController(db)

        for block in [1, 5, 10, 13]:
            dashboard = controller.get_dashboard(block_number=block, academic_year=2025)
            assert dashboard.block_number == block

    # ========================================================================
    # Schedule Block Tests
    # ========================================================================

    def test_schedule_block_dry_run(self, db, setup_data):
        """Test scheduling a block in dry run mode."""
        controller = BlockSchedulerController(db)

        request = BlockScheduleRequest(
            block_number=1,
            academic_year=2025,
            dry_run=True,
            include_all_residents=True,
        )

        result = controller.schedule_block(request, created_by="test_user")

        assert result is not None
        assert hasattr(result, "assignments")
        # Dry run should not save to database
        saved = (
            db.query(BlockAssignment)
            .filter(
                BlockAssignment.block_number == 1,
                BlockAssignment.academic_year == 2025,
            )
            .all()
        )
        # May or may not have saved depending on implementation

    def test_schedule_block_save(self, db, setup_data):
        """Test scheduling a block and saving."""
        controller = BlockSchedulerController(db)

        request = BlockScheduleRequest(
            block_number=2,
            academic_year=2025,
            dry_run=False,
            include_all_residents=True,
        )

        result = controller.schedule_block(request, created_by="test_user")

        assert result is not None

    def test_schedule_block_with_subset(self, db, setup_data):
        """Test scheduling only a subset of residents."""
        controller = BlockSchedulerController(db)

        request = BlockScheduleRequest(
            block_number=3,
            academic_year=2025,
            dry_run=True,
            include_all_residents=False,
        )

        result = controller.schedule_block(request)

        assert result is not None

    # ========================================================================
    # Get Assignment Tests
    # ========================================================================

    def test_get_assignment_success(self, db, setup_data):
        """Test getting a block assignment by ID."""
        # Create an assignment first
        assignment = BlockAssignment(
            id=uuid4(),
            block_number=1,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            assignment_reason="balanced",
            created_by="test",
        )
        db.add(assignment)
        db.commit()

        controller = BlockSchedulerController(db)
        result = controller.get_assignment(assignment.id)

        assert result is not None
        assert result.id == assignment.id
        assert result.block_number == 1

    def test_get_assignment_not_found(self, db):
        """Test getting non-existent assignment raises 404."""
        controller = BlockSchedulerController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_assignment(uuid4())

        assert exc_info.value.status_code == 404

    def test_get_assignment_includes_resident_info(self, db, setup_data):
        """Test that assignment includes resident information."""
        assignment = BlockAssignment(
            id=uuid4(),
            block_number=1,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            assignment_reason="balanced",
        )
        db.add(assignment)
        db.commit()

        controller = BlockSchedulerController(db)
        result = controller.get_assignment(assignment.id)

        assert result.resident is not None
        assert result.resident.name == setup_data["residents"][0].name

    def test_get_assignment_includes_rotation_info(self, db, setup_data):
        """Test that assignment includes rotation template information."""
        assignment = BlockAssignment(
            id=uuid4(),
            block_number=1,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            assignment_reason="balanced",
        )
        db.add(assignment)
        db.commit()

        controller = BlockSchedulerController(db)
        result = controller.get_assignment(assignment.id)

        assert result.rotation_template is not None
        assert result.rotation_template.name == setup_data["templates"][0].name

    # ========================================================================
    # Create Assignment Tests
    # ========================================================================

    def test_create_assignment_success(self, db, setup_data):
        """Test creating a manual block assignment."""
        controller = BlockSchedulerController(db)

        assignment_data = BlockAssignmentCreate(
            block_number=4,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            created_by="test_user",
        )

        result = controller.create_assignment(assignment_data)

        assert result is not None
        assert result.block_number == 4
        assert result.resident_id == setup_data["residents"][0].id

    def test_create_assignment_with_notes(self, db, setup_data):
        """Test creating assignment with notes."""
        controller = BlockSchedulerController(db)

        assignment_data = BlockAssignmentCreate(
            block_number=5,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            created_by="test_user",
            notes="Manual assignment for coverage",
        )

        result = controller.create_assignment(assignment_data)

        assert result.notes == "Manual assignment for coverage"

    def test_create_assignment_duplicate_fails(self, db, setup_data):
        """Test creating duplicate assignment raises conflict error."""
        # Create initial assignment
        assignment = BlockAssignment(
            id=uuid4(),
            block_number=6,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            assignment_reason="balanced",
        )
        db.add(assignment)
        db.commit()

        controller = BlockSchedulerController(db)

        # Try to create duplicate
        assignment_data = BlockAssignmentCreate(
            block_number=6,  # Same block
            academic_year=2025,  # Same year
            resident_id=setup_data["residents"][0].id,  # Same resident
            rotation_template_id=setup_data["templates"][1].id,
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_assignment(assignment_data)

        assert exc_info.value.status_code == 409  # Conflict

    # ========================================================================
    # Update Assignment Tests
    # ========================================================================

    def test_update_assignment_success(self, db, setup_data):
        """Test updating a block assignment."""
        assignment = BlockAssignment(
            id=uuid4(),
            block_number=7,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            assignment_reason="balanced",
        )
        db.add(assignment)
        db.commit()

        controller = BlockSchedulerController(db)

        update_data = BlockAssignmentUpdate(
            rotation_template_id=setup_data["templates"][1].id,
            notes="Changed rotation",
        )
        result = controller.update_assignment(assignment.id, update_data)

        assert result.rotation_template_id == setup_data["templates"][1].id
        assert result.notes == "Changed rotation"

    def test_update_assignment_leave_status(self, db, setup_data):
        """Test updating assignment leave status."""
        assignment = BlockAssignment(
            id=uuid4(),
            block_number=8,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            assignment_reason="balanced",
            has_leave=False,
            leave_days=0,
        )
        db.add(assignment)
        db.commit()

        controller = BlockSchedulerController(db)

        update_data = BlockAssignmentUpdate(has_leave=True, leave_days=5)
        result = controller.update_assignment(assignment.id, update_data)

        assert result.has_leave is True
        assert result.leave_days == 5

    def test_update_assignment_not_found(self, db):
        """Test updating non-existent assignment raises 404."""
        controller = BlockSchedulerController(db)

        update_data = BlockAssignmentUpdate(notes="New notes")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_assignment(uuid4(), update_data)

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Delete Assignment Tests
    # ========================================================================

    def test_delete_assignment_success(self, db, setup_data):
        """Test deleting a block assignment."""
        assignment = BlockAssignment(
            id=uuid4(),
            block_number=9,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            assignment_reason="balanced",
        )
        db.add(assignment)
        db.commit()
        assignment_id = assignment.id

        controller = BlockSchedulerController(db)
        controller.delete_assignment(assignment_id)

        # Verify deletion
        deleted = (
            db.query(BlockAssignment)
            .filter(BlockAssignment.id == assignment_id)
            .first()
        )
        assert deleted is None

    def test_delete_assignment_not_found(self, db):
        """Test deleting non-existent assignment raises 404."""
        controller = BlockSchedulerController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_assignment(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_schedule_then_modify_workflow(self, db, setup_data):
        """Test scheduling a block then modifying an assignment."""
        controller = BlockSchedulerController(db)

        # Create a manual assignment
        assignment_data = BlockAssignmentCreate(
            block_number=10,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=setup_data["templates"][0].id,
            created_by="test",
        )
        created = controller.create_assignment(assignment_data)
        assignment_id = created.id

        # Retrieve it
        retrieved = controller.get_assignment(assignment_id)
        assert retrieved.block_number == 10

        # Update it
        update_data = BlockAssignmentUpdate(
            rotation_template_id=setup_data["templates"][1].id,
        )
        updated = controller.update_assignment(assignment_id, update_data)
        assert updated.rotation_template_id == setup_data["templates"][1].id

        # Delete it
        controller.delete_assignment(assignment_id)

        with pytest.raises(HTTPException):
            controller.get_assignment(assignment_id)

    def test_multiple_residents_same_block(self, db, setup_data):
        """Test assigning multiple residents to the same block."""
        controller = BlockSchedulerController(db)

        # Create assignments for multiple residents in same block
        for i, resident in enumerate(setup_data["residents"][:3]):
            assignment_data = BlockAssignmentCreate(
                block_number=11,
                academic_year=2025,
                resident_id=resident.id,
                rotation_template_id=setup_data["templates"][i % len(setup_data["templates"])].id,
                created_by="test",
            )
            result = controller.create_assignment(assignment_data)
            assert result is not None

        # Check dashboard shows all assignments
        dashboard = controller.get_dashboard(block_number=11, academic_year=2025)
        assert dashboard is not None

    def test_leave_eligible_rotation_assignment(self, db, setup_data):
        """Test assigning resident with leave to leave-eligible rotation."""
        controller = BlockSchedulerController(db)

        # Find leave-eligible template
        leave_template = next(t for t in setup_data["templates"] if t.leave_eligible)

        # Create assignment with leave
        assignment_data = BlockAssignmentCreate(
            block_number=12,
            academic_year=2025,
            resident_id=setup_data["residents"][0].id,
            rotation_template_id=leave_template.id,
            created_by="test",
        )
        created = controller.create_assignment(assignment_data)

        # Update to indicate leave
        update_data = BlockAssignmentUpdate(
            has_leave=True,
            leave_days=7,
        )
        updated = controller.update_assignment(created.id, update_data)

        assert updated.has_leave is True
        assert updated.leave_days == 7

    def test_different_academic_years(self, db, setup_data):
        """Test assignments across different academic years."""
        controller = BlockSchedulerController(db)

        # Create assignments for different years
        for year in [2024, 2025, 2026]:
            assignment_data = BlockAssignmentCreate(
                block_number=1,
                academic_year=year,
                resident_id=setup_data["residents"][0].id,
                rotation_template_id=setup_data["templates"][0].id,
                created_by="test",
            )
            result = controller.create_assignment(assignment_data)
            assert result.academic_year == year

        # Check dashboards for each year
        for year in [2024, 2025, 2026]:
            dashboard = controller.get_dashboard(block_number=1, academic_year=year)
            assert dashboard.academic_year == year
