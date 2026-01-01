"""Tests for FMIT Scheduler Service.

This module tests the FMIT (Faculty Member in Training) scheduling service,
which handles fair schedule generation, validation, and assignment.

Tests cover:
- Schedule retrieval by date range
- Fair schedule generation
- Schedule validation
- Week assignment operations
- Faculty load calculations
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.fmit_scheduler_service import FMITSchedulerService


class TestFMITSchedulerService:
    """Test suite for FMIT scheduling service."""

    @pytest.fixture
    def fmit_rotation_template(self, db):
        """Create FMIT rotation template.

        Note: The service looks for a template named "FMIT" specifically.
        """
        template = RotationTemplate(
            id=uuid4(),
            name="FMIT",  # Must match FMITSchedulerService.FMIT_ROTATION_NAME
            activity_type="clinic",
            abbreviation="FMIT",
            clinic_location="Main Campus",
            max_residents=2,
            supervision_required=True,
            max_supervision_ratio=2,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @pytest.fixture
    def sample_faculty_list(self, db):
        """Create multiple faculty members for FMIT testing."""
        faculty = []
        for i in range(3):
            fac = Person(
                id=uuid4(),
                name=f"Dr. Faculty {i + 1}",
                type="faculty",
                email=f"faculty{i + 1}@test.org",
                performs_procedures=True,
                specialties=["General"],
            )
            db.add(fac)
            faculty.append(fac)
        db.commit()
        for f in faculty:
            db.refresh(f)
        return faculty

    @pytest.fixture
    def week_blocks(self, db):
        """Create blocks for one week (14 blocks: AM/PM for 7 days)."""
        blocks = []
        # Use a fixed Monday for reproducibility
        start_date = date(2025, 1, 6)  # Monday

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

    # =========================================================================
    # Schedule Retrieval Tests
    # =========================================================================

    def test_get_fmit_schedule_success(
        self, db, sample_faculty_list, week_blocks, fmit_rotation_template
    ):
        """Test retrieving FMIT schedule for a date range."""
        # Create an assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=week_blocks[0].id,
            person_id=sample_faculty_list[0].id,
            rotation_template_id=fmit_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        service = FMITSchedulerService(db)
        result = service.get_fmit_schedule(
            start_date=date(2025, 1, 6),
            end_date=date(2025, 1, 12),
        )

        assert result is not None
        assert hasattr(result, "assignments")
        assert result.start_date == date(2025, 1, 6)
        assert result.end_date == date(2025, 1, 12)

    def test_get_fmit_schedule_empty_range(self, db, fmit_rotation_template):
        """Test retrieving FMIT schedule with no assignments."""
        service = FMITSchedulerService(db)
        result = service.get_fmit_schedule(
            start_date=date(2099, 1, 1),
            end_date=date(2099, 1, 31),
        )

        assert result is not None
        assert result.assignments == []
        assert result.total_weeks == 0

    def test_get_fmit_schedule_no_template(self, db):
        """Test retrieving FMIT schedule when no FMIT template exists."""
        service = FMITSchedulerService(db)
        result = service.get_fmit_schedule(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )

        assert result is not None
        assert result.assignments == []
        assert result.total_weeks == 0

    # =========================================================================
    # Fair Schedule Generation Tests
    # =========================================================================

    def test_generate_fair_schedule_success(
        self, db, sample_faculty_list, fmit_rotation_template
    ):
        """Test fair schedule generation distributes weeks fairly."""
        service = FMITSchedulerService(db)
        result = service.generate_fair_schedule(
            year=2025,
            created_by="test",
        )

        assert result is not None
        assert result.success
        assert result.total_weeks == 52
        assert result.assignments_created > 0
        # Each faculty should have some assignments
        for faculty in sample_faculty_list:
            assert faculty.id in result.faculty_loads

    def test_generate_fair_schedule_no_faculty(self, db, fmit_rotation_template):
        """Test fair schedule generation with no available faculty."""
        service = FMITSchedulerService(db)
        result = service.generate_fair_schedule(
            year=2025,
            created_by="test",
        )

        assert result is not None
        assert not result.success
        assert result.error_code == "NO_FACULTY"

    def test_generate_fair_schedule_no_template(self, db, sample_faculty_list):
        """Test fair schedule generation without FMIT template."""
        service = FMITSchedulerService(db)
        result = service.generate_fair_schedule(
            year=2025,
            created_by="test",
        )

        # Should still succeed but with warnings about missing template
        # The service will create empty schedule
        assert result is not None

    # =========================================================================
    # Schedule Validation Tests
    # =========================================================================

    def test_validate_schedule_detects_coverage_gaps(
        self, db, fmit_rotation_template
    ):
        """Test validation detects weeks without coverage."""
        service = FMITSchedulerService(db)
        result = service.validate_schedule(
            start_date=date(2025, 1, 6),
            end_date=date(2025, 1, 19),  # 2 weeks
        )

        assert result is not None
        assert not result.valid  # No assignments = coverage gaps
        assert len(result.coverage_gaps) > 0
        assert len(result.errors) > 0

    def test_validate_schedule_clean(
        self, db, sample_faculty_list, week_blocks, fmit_rotation_template
    ):
        """Test validation passes for schedule with full coverage."""
        # Create assignments for all blocks in the week
        for block in week_blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_faculty_list[0].id,
                rotation_template_id=fmit_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        service = FMITSchedulerService(db)
        result = service.validate_schedule(
            start_date=date(2025, 1, 6),
            end_date=date(2025, 1, 12),
        )

        assert result is not None
        # Week should have coverage
        assert len(result.coverage_gaps) == 0

    # =========================================================================
    # Week Assignment Tests
    # =========================================================================

    def test_assign_faculty_to_week_success(
        self, db, sample_faculty_list, fmit_rotation_template
    ):
        """Test successful FMIT week assignment."""
        service = FMITSchedulerService(db)
        result = service.assign_faculty_to_week(
            faculty_id=sample_faculty_list[0].id,
            week_date=date(2025, 1, 6),
            created_by="test",
        )

        assert result.success
        assert len(result.assignment_ids) == 14  # 7 days × 2 blocks
        assert "Assigned" in result.message

    def test_assign_faculty_to_week_not_found(self, db, fmit_rotation_template):
        """Test assignment fails for non-existent faculty."""
        service = FMITSchedulerService(db)
        result = service.assign_faculty_to_week(
            faculty_id=uuid4(),  # Non-existent
            week_date=date(2025, 1, 6),
            created_by="test",
        )

        assert not result.success
        assert result.error_code == "FACULTY_NOT_FOUND"

    def test_assign_faculty_to_week_already_assigned(
        self, db, sample_faculty_list, fmit_rotation_template
    ):
        """Test assigning to already-assigned week fails."""
        service = FMITSchedulerService(db)

        # First assignment should succeed
        result1 = service.assign_faculty_to_week(
            faculty_id=sample_faculty_list[0].id,
            week_date=date(2025, 1, 6),
            created_by="test",
        )
        assert result1.success

        # Second assignment for same faculty/week should fail
        result2 = service.assign_faculty_to_week(
            faculty_id=sample_faculty_list[0].id,
            week_date=date(2025, 1, 6),
            created_by="test",
        )
        assert not result2.success
        assert result2.error_code == "ALREADY_ASSIGNED"

    def test_assign_faculty_to_week_no_template(self, db, sample_faculty_list):
        """Test assignment fails when FMIT template doesn't exist."""
        service = FMITSchedulerService(db)
        result = service.assign_faculty_to_week(
            faculty_id=sample_faculty_list[0].id,
            week_date=date(2025, 1, 6),
            created_by="test",
        )

        assert not result.success
        assert result.error_code == "TEMPLATE_NOT_FOUND"

    # =========================================================================
    # Remove Faculty From Week Tests
    # =========================================================================

    def test_remove_faculty_from_week_success(
        self, db, sample_faculty_list, fmit_rotation_template
    ):
        """Test removing faculty from an assigned week."""
        service = FMITSchedulerService(db)

        # First assign
        assign_result = service.assign_faculty_to_week(
            faculty_id=sample_faculty_list[0].id,
            week_date=date(2025, 1, 6),
            created_by="test",
        )
        assert assign_result.success

        # Then remove
        remove_result = service.remove_faculty_from_week(
            faculty_id=sample_faculty_list[0].id,
            week_date=date(2025, 1, 6),
        )

        assert remove_result.success
        assert len(remove_result.assignment_ids) == 14
        assert "Removed" in remove_result.message

    def test_remove_faculty_from_week_not_found(
        self, db, sample_faculty_list, fmit_rotation_template
    ):
        """Test removing from unassigned week fails gracefully."""
        service = FMITSchedulerService(db)
        result = service.remove_faculty_from_week(
            faculty_id=sample_faculty_list[0].id,
            week_date=date(2025, 1, 6),  # Not assigned
        )

        assert not result.success
        assert result.error_code == "NOT_FOUND"

    # =========================================================================
    # Faculty Load Tests
    # =========================================================================

    def test_get_faculty_load(
        self, db, sample_faculty_list, fmit_rotation_template
    ):
        """Test calculating faculty workload."""
        service = FMITSchedulerService(db)

        # Assign a week
        service.assign_faculty_to_week(
            faculty_id=sample_faculty_list[0].id,
            week_date=date(2025, 1, 6),
            created_by="test",
        )

        result = service.get_faculty_load(
            faculty_id=sample_faculty_list[0].id,
            year=2025,
        )

        assert result.faculty_id == sample_faculty_list[0].id
        assert result.total_weeks == 1
        assert len(result.week_dates) == 1
        assert result.year == 2025

    def test_get_faculty_load_unknown_faculty(self, db, fmit_rotation_template):
        """Test faculty load for unknown faculty."""
        service = FMITSchedulerService(db)
        result = service.get_faculty_load(
            faculty_id=uuid4(),
            year=2025,
        )

        assert result.faculty_name == "Unknown"
        assert result.total_weeks == 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestFMITSchedulerIntegration:
    """Integration tests for FMIT scheduler with database."""

    @pytest.fixture
    def fmit_rotation_template(self, db):
        """Create FMIT rotation template."""
        template = RotationTemplate(
            id=uuid4(),
            name="FMIT",
            activity_type="clinic",
            abbreviation="FMIT",
            clinic_location="Main Campus",
            max_residents=2,
            supervision_required=True,
            max_supervision_ratio=2,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @pytest.fixture
    def sample_faculty_list(self, db):
        """Create faculty for integration testing."""
        faculty = []
        for i in range(3):
            fac = Person(
                id=uuid4(),
                name=f"Dr. Integration Faculty {i + 1}",
                type="faculty",
                email=f"int_faculty{i + 1}@test.org",
                performs_procedures=True,
                specialties=["General"],
            )
            db.add(fac)
            faculty.append(fac)
        db.commit()
        for f in faculty:
            db.refresh(f)
        return faculty

    def test_full_schedule_generation_workflow(
        self, db, sample_faculty_list, fmit_rotation_template
    ):
        """Test complete workflow: generate, validate, verify."""
        service = FMITSchedulerService(db)

        # 1. Generate fair schedule for a month
        gen_result = service.generate_fair_schedule(
            year=2025,
            created_by="integration_test",
        )
        assert gen_result.success
        assert gen_result.assignments_created > 0

        # 2. Get schedule to verify
        schedule = service.get_fmit_schedule(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        assert schedule.total_weeks > 0

        # 3. Validate schedule
        validation = service.validate_schedule(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
        )
        # Should have mostly valid coverage after generation
        assert validation is not None

    def test_assign_and_remove_workflow(
        self, db, sample_faculty_list, fmit_rotation_template
    ):
        """Test assign and remove operations work correctly together."""
        service = FMITSchedulerService(db)
        faculty_id = sample_faculty_list[0].id
        week_date = date(2025, 2, 3)

        # 1. Assign
        assign_result = service.assign_faculty_to_week(
            faculty_id=faculty_id,
            week_date=week_date,
            created_by="test",
        )
        assert assign_result.success

        # 2. Verify assignment exists
        schedule = service.get_week_assignments(week_date)
        assert len(schedule) == 1
        assert schedule[0].faculty_id == faculty_id

        # 3. Remove
        remove_result = service.remove_faculty_from_week(
            faculty_id=faculty_id,
            week_date=week_date,
        )
        assert remove_result.success

        # 4. Verify assignment is gone
        schedule_after = service.get_week_assignments(week_date)
        assert len(schedule_after) == 0
