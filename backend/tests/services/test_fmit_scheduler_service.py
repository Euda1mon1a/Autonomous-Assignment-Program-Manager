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

    def test_validate_schedule_detects_coverage_gaps(self, db, fmit_rotation_template):
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

    def test_get_faculty_load(self, db, sample_faculty_list, fmit_rotation_template):
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


# =============================================================================
# Week Boundary Tests (Friday-Thursday FMIT weeks)
# =============================================================================


class TestFMITWeekBoundaries:
    """Test that FMIT service uses Friday-Thursday week boundaries.

    FMIT weeks run from Friday to Thursday, not Monday to Sunday.
    This aligns with the constraint logic in app.scheduling.constraints.fmit.

    Note: These tests use a mock session to avoid SQLite/JSONB compatibility
    issues in the test infrastructure. The _get_week_start method doesn't
    actually use the database session.
    """

    @pytest.fixture
    def mock_db(self):
        """Mock database session (not actually used by _get_week_start)."""
        from unittest.mock import MagicMock

        return MagicMock()

    def test_get_week_start_returns_friday(self, mock_db):
        """Test _get_week_start returns Friday for any date in the week."""
        service = FMITSchedulerService(mock_db)

        # Wednesday Jan 8, 2025 should return Friday Jan 3, 2025
        wednesday = date(2025, 1, 8)
        week_start = service._get_week_start(wednesday)
        assert week_start == date(2025, 1, 3)  # Friday
        assert week_start.weekday() == 4  # Friday = weekday 4

    def test_get_week_start_friday_returns_same(self, mock_db):
        """Test _get_week_start returns same Friday if given a Friday."""
        service = FMITSchedulerService(mock_db)

        friday = date(2025, 1, 3)  # Friday
        week_start = service._get_week_start(friday)
        assert week_start == friday
        assert week_start.weekday() == 4

    def test_get_week_start_thursday_returns_previous_friday(self, mock_db):
        """Test Thursday (end of FMIT week) returns previous Friday."""
        service = FMITSchedulerService(mock_db)

        thursday = date(2025, 1, 9)  # Thursday (end of FMIT week)
        week_start = service._get_week_start(thursday)
        assert week_start == date(2025, 1, 3)  # Friday (start of same FMIT week)
        assert week_start.weekday() == 4

    def test_get_week_start_saturday_returns_previous_friday(self, mock_db):
        """Test Saturday returns the Friday of the current FMIT week."""
        service = FMITSchedulerService(mock_db)

        saturday = date(2025, 1, 4)  # Saturday
        week_start = service._get_week_start(saturday)
        assert week_start == date(2025, 1, 3)  # Previous Friday
        assert week_start.weekday() == 4

    def test_get_week_start_sunday_returns_previous_friday(self, mock_db):
        """Test Sunday returns the Friday of the current FMIT week."""
        service = FMITSchedulerService(mock_db)

        sunday = date(2025, 1, 5)  # Sunday
        week_start = service._get_week_start(sunday)
        assert week_start == date(2025, 1, 3)  # Previous Friday
        assert week_start.weekday() == 4

    def test_get_week_start_monday_returns_previous_friday(self, mock_db):
        """Test Monday returns the Friday of the current FMIT week.

        This is the key behavioral change from the bug fix.
        Previously, Monday Jan 6 would return Monday Jan 6.
        Now it should return Friday Jan 3 (same FMIT week).
        """
        service = FMITSchedulerService(mock_db)

        monday = date(2025, 1, 6)  # Monday
        week_start = service._get_week_start(monday)
        # Monday Jan 6 is part of the Fri Jan 3 - Thu Jan 9 FMIT week
        assert week_start == date(2025, 1, 3)  # Friday
        assert week_start.weekday() == 4

    def test_week_boundary_alignment_with_constraints(self, mock_db):
        """Test that service week boundaries align with constraint module.

        The service should use the same Friday-Thursday boundaries as
        get_fmit_week_dates() from app.scheduling.constraints.fmit.
        """
        from app.scheduling.constraints.fmit import get_fmit_week_dates

        service = FMITSchedulerService(mock_db)

        # Test several dates
        test_dates = [
            date(2025, 1, 3),  # Friday
            date(2025, 1, 6),  # Monday
            date(2025, 1, 9),  # Thursday
            date(2025, 2, 15),  # Saturday
            date(2025, 3, 20),  # Thursday
        ]

        for test_date in test_dates:
            service_week_start = service._get_week_start(test_date)
            constraint_friday, _ = get_fmit_week_dates(test_date)
            assert service_week_start == constraint_friday, (
                f"For {test_date}: service returned {service_week_start}, "
                f"constraint returned {constraint_friday}"
            )

    def test_year_boundary_fmit_week(self, mock_db):
        """Test FMIT week spanning year boundary."""
        service = FMITSchedulerService(mock_db)

        # Dec 31, 2024 is a Tuesday, part of Fri Dec 27 - Thu Jan 2 week
        dec_31 = date(2024, 12, 31)
        week_start = service._get_week_start(dec_31)
        assert week_start == date(2024, 12, 27)  # Friday Dec 27, 2024
        assert week_start.weekday() == 4

    def test_consecutive_weeks_non_overlapping(self, mock_db):
        """Test consecutive FMIT weeks don't overlap."""
        service = FMITSchedulerService(mock_db)

        # Week 1: Fri Jan 3 - Thu Jan 9
        date_in_week1 = date(2025, 1, 5)  # Sunday
        week1_start = service._get_week_start(date_in_week1)

        # Week 2: Fri Jan 10 - Thu Jan 16
        date_in_week2 = date(2025, 1, 12)  # Sunday
        week2_start = service._get_week_start(date_in_week2)

        # Week 1 end (Thursday) should be day before week 2 start (Friday)
        week1_end = week1_start + timedelta(days=6)
        assert week1_end + timedelta(days=1) == week2_start
