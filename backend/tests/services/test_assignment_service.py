"""Tests for AssignmentService."""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch

from app.services.assignment_service import AssignmentService
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestAssignmentService:
    """Test suite for AssignmentService."""

    # ========================================================================
    # Get Assignment Tests
    # ========================================================================

    def test_get_assignment_success(self, db, sample_resident, sample_block):
        """Test getting an assignment by ID successfully."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        service = AssignmentService(db)
        result = service.get_assignment(assignment.id)

        assert result is not None
        assert result.id == assignment.id
        assert result.block_id == sample_block.id
        assert result.person_id == sample_resident.id

    def test_get_assignment_not_found(self, db):
        """Test getting a non-existent assignment returns None."""
        service = AssignmentService(db)
        result = service.get_assignment(uuid4())

        assert result is None

    # ========================================================================
    # List Assignments Tests
    # ========================================================================

    def test_list_assignments_no_filters(self, db, sample_residents, sample_blocks):
        """Test listing all assignments without filters."""
        # Create multiple assignments
        assignments = []
        for i, resident in enumerate(sample_residents[:2]):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=resident.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)
        db.commit()

        service = AssignmentService(db)
        result = service.list_assignments()

        assert result["total"] == 2
        assert len(result["items"]) == 2

    def test_list_assignments_filter_by_person_id(self, db, sample_residents, sample_blocks):
        """Test filtering assignments by person_id."""
        person1, person2, person3 = sample_residents

        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=person1.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=person2.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        service = AssignmentService(db)
        result = service.list_assignments(person_id=person1.id)

        assert result["total"] == 1
        assert result["items"][0].person_id == person1.id

    def test_list_assignments_filter_by_role(self, db, sample_resident, sample_blocks):
        """Test filtering assignments by role."""
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=sample_resident.id,
            role="backup",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        service = AssignmentService(db)
        result = service.list_assignments(role="primary")

        assert result["total"] == 1
        assert result["items"][0].role == "primary"

    def test_list_assignments_filter_by_activity_type(self, db, sample_resident, sample_blocks):
        """Test filtering assignments by activity_type."""
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            role="primary",
            activity_type="clinic",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=sample_resident.id,
            role="primary",
            activity_type="inpatient",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        service = AssignmentService(db)
        result = service.list_assignments(activity_type="clinic")

        assert result["total"] == 1
        assert result["items"][0].activity_type == "clinic"

    def test_list_assignments_filter_by_date_range(self, db, sample_resident):
        """Test filtering assignments by date range."""
        # Create blocks with specific dates
        block1 = Block(
            id=uuid4(),
            date=date(2025, 1, 15),
            time_of_day="AM",
            block_number=1,
        )
        block2 = Block(
            id=uuid4(),
            date=date(2025, 2, 15),
            time_of_day="AM",
            block_number=2,
        )
        block3 = Block(
            id=uuid4(),
            date=date(2025, 3, 15),
            time_of_day="AM",
            block_number=3,
        )
        db.add_all([block1, block2, block3])
        db.commit()

        assignment1 = Assignment(
            id=uuid4(),
            block_id=block1.id,
            person_id=sample_resident.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=block2.id,
            person_id=sample_resident.id,
            role="primary",
        )
        assignment3 = Assignment(
            id=uuid4(),
            block_id=block3.id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2, assignment3])
        db.commit()

        service = AssignmentService(db)
        result = service.list_assignments(
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
        )

        assert result["total"] == 1

    def test_list_assignments_empty_result(self, db):
        """Test listing assignments when none exist."""
        service = AssignmentService(db)
        result = service.list_assignments()

        assert result["total"] == 0
        assert len(result["items"]) == 0

    # ========================================================================
    # Create Assignment Tests
    # ========================================================================

    @patch('app.services.assignment_service.ACGMEValidator')
    def test_create_assignment_success(self, mock_validator, db, sample_resident, sample_block):
        """Test creating an assignment successfully."""
        # Mock ACGME validation to return no violations
        mock_validator_instance = Mock()
        mock_validator_instance.validate_all.return_value = Mock(violations=[])
        mock_validator.return_value = mock_validator_instance

        service = AssignmentService(db)
        result = service.create_assignment(
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
            created_by="test_user",
        )

        assert result["error"] is None
        assert result["assignment"] is not None
        assert result["assignment"].block_id == sample_block.id
        assert result["assignment"].person_id == sample_resident.id
        assert result["assignment"].role == "primary"
        assert result["is_compliant"] is True
        assert len(result["acgme_warnings"]) == 0

    @patch('app.services.assignment_service.ACGMEValidator')
    def test_create_assignment_with_all_optional_fields(
        self, mock_validator, db, sample_resident, sample_block, sample_rotation_template
    ):
        """Test creating an assignment with all optional fields."""
        mock_validator_instance = Mock()
        mock_validator_instance.validate_all.return_value = Mock(violations=[])
        mock_validator.return_value = mock_validator_instance

        service = AssignmentService(db)
        result = service.create_assignment(
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
            created_by="test_user",
            rotation_template_id=sample_rotation_template.id,
            activity_type="clinic",
            notes="Test assignment",
        )

        assignment = result["assignment"]
        assert assignment.rotation_template_id == sample_rotation_template.id
        assert assignment.activity_type == "clinic"
        assert assignment.notes == "Test assignment"

    @patch('app.services.assignment_service.ACGMEValidator')
    def test_create_assignment_duplicate_error(self, mock_validator, db, sample_resident, sample_block):
        """Test creating a duplicate assignment returns error."""
        mock_validator_instance = Mock()
        mock_validator_instance.validate_all.return_value = Mock(violations=[])
        mock_validator.return_value = mock_validator_instance

        # Create first assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Try to create duplicate
        service = AssignmentService(db)
        result = service.create_assignment(
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="backup",
            created_by="test_user",
        )

        assert result["error"] == "Person already assigned to this block"
        assert result["assignment"] is None

    @patch('app.services.assignment_service.ACGMEValidator')
    def test_create_assignment_with_acgme_violations(self, mock_validator, db, sample_resident, sample_block):
        """Test creating an assignment with ACGME violations."""
        # Mock ACGME validation to return violations
        mock_violation = Mock()
        mock_violation.person_id = sample_resident.id
        mock_violation.severity = "WARNING"
        mock_violation.message = "Exceeds maximum consecutive days"

        mock_validator_instance = Mock()
        mock_validator_instance.validate_all.return_value = Mock(
            violations=[mock_violation]
        )
        mock_validator.return_value = mock_validator_instance

        service = AssignmentService(db)
        result = service.create_assignment(
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
            created_by="test_user",
        )

        assert result["assignment"] is not None
        assert result["is_compliant"] is False
        assert len(result["acgme_warnings"]) == 1
        assert "WARNING: Exceeds maximum consecutive days" in result["acgme_warnings"]

    @patch('app.services.assignment_service.ACGMEValidator')
    def test_create_assignment_with_override_reason(self, mock_validator, db, sample_resident, sample_block):
        """Test creating an assignment with override reason adds note."""
        # Mock ACGME validation to return violations
        mock_violation = Mock()
        mock_violation.person_id = sample_resident.id
        mock_violation.severity = "WARNING"
        mock_violation.message = "Exceeds maximum consecutive days"

        mock_validator_instance = Mock()
        mock_validator_instance.validate_all.return_value = Mock(
            violations=[mock_violation]
        )
        mock_validator.return_value = mock_validator_instance

        service = AssignmentService(db)
        result = service.create_assignment(
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
            created_by="test_user",
            override_reason="Emergency coverage needed",
        )

        assignment = result["assignment"]
        assert "ACGME Override: Emergency coverage needed" in assignment.notes
        assert "Override acknowledged: Emergency coverage needed" in result["acgme_warnings"]

    # ========================================================================
    # Update Assignment Tests
    # ========================================================================

    @patch('app.services.assignment_service.ACGMEValidator')
    def test_update_assignment_success(self, mock_validator, db, sample_resident, sample_block):
        """Test updating an assignment successfully."""
        mock_validator_instance = Mock()
        mock_validator_instance.validate_all.return_value = Mock(violations=[])
        mock_validator.return_value = mock_validator_instance

        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        service = AssignmentService(db)
        result = service.update_assignment(
            assignment.id,
            {"role": "backup", "notes": "Updated notes"},
            assignment.updated_at,
        )

        assert result["error"] is None
        assert result["assignment"].role == "backup"
        assert result["assignment"].notes == "Updated notes"

    def test_update_assignment_not_found(self, db):
        """Test updating a non-existent assignment returns error."""
        service = AssignmentService(db)
        result = service.update_assignment(
            uuid4(),
            {"role": "backup"},
            None,
        )

        assert result["error"] == "Assignment not found"
        assert result["assignment"] is None

    @patch('app.services.assignment_service.ACGMEValidator')
    def test_update_assignment_optimistic_locking_conflict(
        self, mock_validator, db, sample_resident, sample_block
    ):
        """Test optimistic locking prevents concurrent updates."""
        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        old_updated_at = assignment.updated_at

        # Simulate another user updating the assignment
        assignment.role = "backup"
        db.commit()
        db.refresh(assignment)

        # Try to update with old timestamp
        service = AssignmentService(db)
        result = service.update_assignment(
            assignment.id,
            {"notes": "My update"},
            old_updated_at,
        )

        assert "Assignment has been modified by another user" in result["error"]
        assert result["assignment"] is None

    @patch('app.services.assignment_service.ACGMEValidator')
    def test_update_assignment_with_acgme_validation(
        self, mock_validator, db, sample_resident, sample_block
    ):
        """Test that updating an assignment triggers ACGME validation."""
        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # Mock ACGME validation
        mock_violation = Mock()
        mock_violation.person_id = sample_resident.id
        mock_violation.severity = "ERROR"
        mock_violation.message = "Maximum hours exceeded"

        mock_validator_instance = Mock()
        mock_validator_instance.validate_all.return_value = Mock(
            violations=[mock_violation]
        )
        mock_validator.return_value = mock_validator_instance

        service = AssignmentService(db)
        result = service.update_assignment(
            assignment.id,
            {"role": "backup"},
            assignment.updated_at,
        )

        assert result["is_compliant"] is False
        assert len(result["acgme_warnings"]) == 1

    # ========================================================================
    # Delete Assignment Tests
    # ========================================================================

    def test_delete_assignment_success(self, db, sample_resident, sample_block):
        """Test deleting an assignment successfully."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        assignment_id = assignment.id

        service = AssignmentService(db)
        result = service.delete_assignment(assignment_id)

        assert result["success"] is True
        assert result["error"] is None

        # Verify deletion
        db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        assert db_assignment is None

    def test_delete_assignment_not_found(self, db):
        """Test deleting a non-existent assignment returns error."""
        service = AssignmentService(db)
        result = service.delete_assignment(uuid4())

        assert result["success"] is False
        assert result["error"] == "Assignment not found"

    # ========================================================================
    # Delete Assignments Bulk Tests
    # ========================================================================

    def test_delete_assignments_bulk_success(self, db, sample_resident):
        """Test bulk deleting assignments in a date range."""
        # Create blocks for different dates
        blocks = []
        for i in range(10):
            block = Block(
                id=uuid4(),
                date=date(2025, 1, 1) + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Create assignments for these blocks
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Delete assignments in a date range (first 5 days)
        service = AssignmentService(db)
        result = service.delete_assignments_bulk(
            date(2025, 1, 1),
            date(2025, 1, 5),
        )

        assert result["deleted"] == 5

        # Verify remaining assignments
        remaining = db.query(Assignment).count()
        assert remaining == 5

    def test_delete_assignments_bulk_no_matches(self, db):
        """Test bulk delete with no matching assignments."""
        service = AssignmentService(db)
        result = service.delete_assignments_bulk(
            date(2025, 1, 1),
            date(2025, 1, 31),
        )

        assert result["deleted"] == 0

    def test_delete_assignments_bulk_partial_range(self, db, sample_resident):
        """Test bulk delete only affects assignments in specified range."""
        # Create blocks before, during, and after the range
        block_before = Block(
            id=uuid4(),
            date=date(2024, 12, 15),
            time_of_day="AM",
            block_number=1,
        )
        block_during = Block(
            id=uuid4(),
            date=date(2025, 1, 15),
            time_of_day="AM",
            block_number=1,
        )
        block_after = Block(
            id=uuid4(),
            date=date(2025, 2, 15),
            time_of_day="AM",
            block_number=2,
        )
        db.add_all([block_before, block_during, block_after])
        db.commit()

        # Create assignments
        for block in [block_before, block_during, block_after]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Delete only January assignments
        service = AssignmentService(db)
        result = service.delete_assignments_bulk(
            date(2025, 1, 1),
            date(2025, 1, 31),
        )

        assert result["deleted"] == 1

        # Verify correct assignments remain
        remaining = db.query(Assignment).all()
        assert len(remaining) == 2
        remaining_block_ids = {a.block_id for a in remaining}
        assert block_before.id in remaining_block_ids
        assert block_after.id in remaining_block_ids
        assert block_during.id not in remaining_block_ids
