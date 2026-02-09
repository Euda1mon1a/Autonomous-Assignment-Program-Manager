"""Tests for FMIT assignment schemas (enums, Field bounds, field_validators, defaults)."""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.fmit_assignments import (
    AssignmentStatus,
    FMITAssignmentCreate,
    FMITAssignmentUpdate,
    FMITAssignmentResponse,
    FMITAssignmentDeleteResponse,
    FMITBulkAssignmentItem,
    FMITBulkAssignmentRequest,
    FMITBulkAssignmentResult,
    FMITBulkAssignmentResponse,
    WeekSlot,
    FacultyYearSummary,
    YearGridResponse,
    ConflictType,
    ConflictDetail,
    ConflictCheckResponse,
    FMITOperationResult,
)


class TestAssignmentStatus:
    def test_values(self):
        assert AssignmentStatus.PENDING == "pending"
        assert AssignmentStatus.CONFIRMED == "confirmed"
        assert AssignmentStatus.CANCELLED == "cancelled"

    def test_count(self):
        assert len(AssignmentStatus) == 3


class TestFMITAssignmentCreate:
    def test_defaults(self):
        future = date.today() + timedelta(days=7)
        r = FMITAssignmentCreate(faculty_id=uuid4(), week_date=future)
        assert r.created_by == "system"
        assert r.notes is None

    # --- notes max_length=2000 ---

    def test_notes_too_long(self):
        future = date.today() + timedelta(days=7)
        with pytest.raises(ValidationError):
            FMITAssignmentCreate(faculty_id=uuid4(), week_date=future, notes="x" * 2001)

    # --- created_by max_length=255 ---

    def test_created_by_too_long(self):
        future = date.today() + timedelta(days=7)
        with pytest.raises(ValidationError):
            FMITAssignmentCreate(
                faculty_id=uuid4(), week_date=future, created_by="x" * 256
            )

    # --- week_date field_validator (not more than 30 days in past) ---

    def test_week_date_too_far_past(self):
        past = date.today() - timedelta(days=31)
        with pytest.raises(ValidationError, match="30 days in the past"):
            FMITAssignmentCreate(faculty_id=uuid4(), week_date=past)

    def test_week_date_recent_past_ok(self):
        recent_past = date.today() - timedelta(days=10)
        r = FMITAssignmentCreate(faculty_id=uuid4(), week_date=recent_past)
        assert r.week_date == recent_past


class TestFMITAssignmentUpdate:
    def test_all_none(self):
        r = FMITAssignmentUpdate()
        assert r.faculty_id is None
        assert r.notes is None
        assert r.status is None

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            FMITAssignmentUpdate(notes="x" * 2001)


class TestFMITAssignmentResponse:
    def test_defaults(self):
        r = FMITAssignmentResponse(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            week_start=date(2026, 1, 3),
            week_end=date(2026, 1, 9),
        )
        assert r.assignment_ids == []
        assert r.rotation_template_id is None
        assert r.is_complete is False
        assert r.block_count == 0
        assert r.status == AssignmentStatus.CONFIRMED
        assert r.notes is None
        assert r.created_at is None
        assert r.created_by is None


class TestFMITAssignmentDeleteResponse:
    def test_defaults(self):
        r = FMITAssignmentDeleteResponse(success=True, message="Deleted")
        assert r.deleted_assignment_ids == []
        assert r.deleted_count == 0


class TestFMITBulkAssignmentItem:
    def test_valid(self):
        r = FMITBulkAssignmentItem(faculty_id=uuid4(), week_date=date(2026, 1, 10))
        assert r.notes is None

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            FMITBulkAssignmentItem(
                faculty_id=uuid4(), week_date=date(2026, 1, 10), notes="x" * 501
            )


class TestFMITBulkAssignmentRequest:
    def test_defaults(self):
        item = FMITBulkAssignmentItem(faculty_id=uuid4(), week_date=date(2026, 1, 10))
        r = FMITBulkAssignmentRequest(assignments=[item])
        assert r.created_by == "system"
        assert r.skip_conflicts is False
        assert r.dry_run is False

    # --- assignments min_length=1, max_length=100 ---

    def test_assignments_empty(self):
        with pytest.raises(ValidationError):
            FMITBulkAssignmentRequest(assignments=[])


class TestFMITBulkAssignmentResult:
    def test_defaults(self):
        r = FMITBulkAssignmentResult(
            faculty_id=uuid4(),
            week_date=date(2026, 1, 10),
            success=True,
            message="Created",
        )
        assert r.assignment_ids == []
        assert r.error_code is None


class TestFMITBulkAssignmentResponse:
    def test_defaults(self):
        r = FMITBulkAssignmentResponse(total_requested=5)
        assert r.successful_count == 0
        assert r.failed_count == 0
        assert r.skipped_count == 0
        assert r.results == []
        assert r.dry_run is False
        assert r.warnings == []


class TestWeekSlot:
    def test_defaults(self):
        r = WeekSlot(
            week_number=1,
            week_start=date(2026, 1, 3),
            week_end=date(2026, 1, 9),
        )
        assert r.is_current_week is False
        assert r.is_past is False
        assert r.faculty_id is None
        assert r.faculty_name is None
        assert r.is_complete is False
        assert r.has_conflict is False
        assert r.conflict_reason is None

    # --- week_number ge=1, le=53 ---

    def test_week_number_below_min(self):
        with pytest.raises(ValidationError):
            WeekSlot(
                week_number=0,
                week_start=date(2026, 1, 3),
                week_end=date(2026, 1, 9),
            )

    def test_week_number_above_max(self):
        with pytest.raises(ValidationError):
            WeekSlot(
                week_number=54,
                week_start=date(2026, 1, 3),
                week_end=date(2026, 1, 9),
            )


class TestFacultyYearSummary:
    def test_defaults(self):
        r = FacultyYearSummary(faculty_id=uuid4(), faculty_name="Dr. Smith")
        assert r.total_weeks == 0
        assert r.completed_weeks == 0
        assert r.upcoming_weeks == 0
        assert r.target_weeks == 0.0
        assert r.variance == 0.0
        assert r.is_balanced is True
        assert r.week_dates == []


class TestYearGridResponse:
    def test_defaults(self):
        r = YearGridResponse(
            year=2026,
            academic_year_start=date(2025, 7, 1),
            academic_year_end=date(2026, 6, 30),
            generated_at=datetime(2026, 1, 1),
        )
        assert r.weeks == []
        assert r.faculty_summaries == []
        assert r.total_weeks == 52
        assert r.assigned_weeks == 0
        assert r.unassigned_weeks == 0
        assert r.coverage_percentage == 0.0
        assert r.fairness_index == 0.0


class TestConflictType:
    def test_values(self):
        assert ConflictType.LEAVE_OVERLAP == "leave_overlap"
        assert ConflictType.ALREADY_ASSIGNED == "already_assigned"

    def test_count(self):
        assert len(ConflictType) == 5


class TestConflictDetail:
    def test_defaults(self):
        r = ConflictDetail(
            conflict_type=ConflictType.LEAVE_OVERLAP,
            severity="critical",
            description="Faculty on leave",
        )
        assert r.faculty_id is None
        assert r.faculty_name is None
        assert r.week_date is None
        assert r.blocking_absence_id is None
        assert r.blocking_absence_type is None


class TestConflictCheckResponse:
    def test_defaults(self):
        r = ConflictCheckResponse(can_assign=True)
        assert r.conflicts == []
        assert r.warnings == []
        assert r.suggestions == []


class TestFMITOperationResult:
    def test_defaults(self):
        r = FMITOperationResult(success=True, message="Done")
        assert r.assignment_ids == []
        assert r.error_code is None
        assert r.warnings == []
