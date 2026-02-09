"""Tests for leave schemas (enums, field_validators, date validation, defaults)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.leave import (
    LeaveType,
    LeaveStatus,
    LeaveWebhookPayload,
    LeaveCreateRequest,
    LeaveUpdateRequest,
    LeaveResponse,
    LeaveRequestResponse,
    LeaveApprovalRequest,
    LeaveApprovalResponse,
    LeaveListResponse,
    LeaveCalendarEntry,
    LeaveCalendarResponse,
    BulkLeaveImportRequest,
    BulkLeaveImportResponse,
)


class TestLeaveType:
    def test_values(self):
        assert LeaveType.VACATION.value == "vacation"
        assert LeaveType.TDY.value == "tdy"
        assert LeaveType.DEPLOYMENT.value == "deployment"
        assert LeaveType.CONFERENCE.value == "conference"
        assert LeaveType.MEDICAL.value == "medical"
        assert LeaveType.FAMILY_EMERGENCY.value == "family_emergency"
        assert LeaveType.BEREAVEMENT.value == "bereavement"
        assert LeaveType.EMERGENCY_LEAVE.value == "emergency_leave"
        assert LeaveType.SICK.value == "sick"
        assert LeaveType.CONVALESCENT.value == "convalescent"
        assert LeaveType.MATERNITY_PATERNITY.value == "maternity_paternity"

    def test_count(self):
        assert len(LeaveType) == 11

    def test_is_str(self):
        assert isinstance(LeaveType.VACATION, str)


class TestLeaveStatus:
    def test_values(self):
        assert LeaveStatus.PENDING.value == "pending"
        assert LeaveStatus.APPROVED.value == "approved"
        assert LeaveStatus.REJECTED.value == "rejected"
        assert LeaveStatus.CANCELLED.value == "cancelled"

    def test_count(self):
        assert len(LeaveStatus) == 4


class TestLeaveWebhookPayload:
    def test_valid(self):
        r = LeaveWebhookPayload(
            event_type="created",
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            start_date=date(2026, 3, 2),
            end_date=date(2026, 3, 6),
            leave_type=LeaveType.VACATION,
        )
        assert r.is_blocking is True
        assert r.description is None
        assert r.leave_id is None

    def test_event_type_pattern(self):
        for event in ("created", "updated", "deleted"):
            r = LeaveWebhookPayload(
                event_type=event,
                faculty_id=uuid4(),
                faculty_name="Dr. Smith",
                start_date=date(2026, 3, 2),
                end_date=date(2026, 3, 6),
                leave_type=LeaveType.TDY,
            )
            assert r.event_type == event

    def test_invalid_event_type(self):
        with pytest.raises(ValidationError):
            LeaveWebhookPayload(
                event_type="invalid",
                faculty_id=uuid4(),
                faculty_name="Dr. Smith",
                start_date=date(2026, 3, 2),
                end_date=date(2026, 3, 6),
                leave_type=LeaveType.VACATION,
            )

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="end_date must be after start_date"):
            LeaveWebhookPayload(
                event_type="created",
                faculty_id=uuid4(),
                faculty_name="Dr. Smith",
                start_date=date(2026, 3, 6),
                end_date=date(2026, 3, 2),
                leave_type=LeaveType.VACATION,
            )


class TestLeaveCreateRequest:
    def test_valid_minimal(self):
        r = LeaveCreateRequest(
            faculty_id=uuid4(),
            start_date=date(2026, 3, 2),
            end_date=date(2026, 3, 6),
            leave_type=LeaveType.CONFERENCE,
        )
        assert r.is_blocking is True
        assert r.description is None

    def test_with_description(self):
        r = LeaveCreateRequest(
            faculty_id=uuid4(),
            start_date=date(2026, 3, 2),
            end_date=date(2026, 3, 6),
            leave_type=LeaveType.TDY,
            is_blocking=True,
            description="TDY to Fort Bragg",
        )
        assert r.description == "TDY to Fort Bragg"

    # --- description max_length=500 ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            LeaveCreateRequest(
                faculty_id=uuid4(),
                start_date=date(2026, 3, 2),
                end_date=date(2026, 3, 6),
                leave_type=LeaveType.VACATION,
                description="x" * 501,
            )

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="end_date must be after start_date"):
            LeaveCreateRequest(
                faculty_id=uuid4(),
                start_date=date(2026, 3, 6),
                end_date=date(2026, 3, 2),
                leave_type=LeaveType.VACATION,
            )


class TestLeaveUpdateRequest:
    def test_all_none(self):
        r = LeaveUpdateRequest()
        assert r.start_date is None
        assert r.end_date is None
        assert r.leave_type is None
        assert r.is_blocking is None
        assert r.description is None

    def test_partial(self):
        r = LeaveUpdateRequest(leave_type=LeaveType.MEDICAL, is_blocking=True)
        assert r.leave_type == LeaveType.MEDICAL

    # --- description max_length=500 ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            LeaveUpdateRequest(description="x" * 501)


class TestLeaveResponse:
    def _make_response(self, **overrides):
        defaults = {
            "id": uuid4(),
            "faculty_id": uuid4(),
            "faculty_name": "Dr. Smith",
            "start_date": date(2026, 3, 2),
            "end_date": date(2026, 3, 6),
            "leave_type": LeaveType.VACATION,
            "is_blocking": False,
            "description": None,
            "status": LeaveStatus.APPROVED,
            "created_at": datetime(2026, 3, 1),
            "updated_at": None,
        }
        defaults.update(overrides)
        return LeaveResponse(**defaults)

    def test_valid_minimal(self):
        r = self._make_response()
        assert r.reviewed_at is None
        assert r.reviewed_by_id is None
        assert r.review_notes is None

    def test_with_review(self):
        r = self._make_response(
            reviewed_at=datetime(2026, 3, 2),
            reviewed_by_id=uuid4(),
            review_notes="Approved per policy",
        )
        assert r.review_notes == "Approved per policy"


class TestLeaveRequestResponse:
    def test_valid(self):
        r = LeaveRequestResponse(
            success=True,
            leave_id=uuid4(),
            status=LeaveStatus.PENDING,
            message="Leave request created",
        )
        assert r.success is True

    def test_no_leave_id(self):
        r = LeaveRequestResponse(
            success=False,
            status=LeaveStatus.REJECTED,
            message="Conflict detected",
        )
        assert r.leave_id is None


class TestLeaveApprovalRequest:
    def test_approve(self):
        r = LeaveApprovalRequest(approved=True)
        assert r.notes is None

    def test_reject_with_notes(self):
        r = LeaveApprovalRequest(approved=False, notes="Coverage not available")
        assert r.notes == "Coverage not available"

    # --- notes max_length=500 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            LeaveApprovalRequest(approved=False, notes="x" * 501)


class TestLeaveApprovalResponse:
    def test_valid(self):
        r = LeaveApprovalResponse(
            success=True,
            status=LeaveStatus.APPROVED,
            message="Leave approved",
        )
        assert r.success is True


class TestLeaveListResponse:
    def test_valid(self):
        r = LeaveListResponse(items=[], total=0, page=1, page_size=20)
        assert r.items == []


class TestLeaveCalendarEntry:
    def test_valid(self):
        r = LeaveCalendarEntry(
            faculty_id=uuid4(),
            faculty_name="Dr. Jones",
            leave_type=LeaveType.DEPLOYMENT,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
            is_blocking=True,
        )
        assert r.has_fmit_conflict is False

    def test_with_conflict(self):
        r = LeaveCalendarEntry(
            faculty_id=uuid4(),
            faculty_name="Dr. Jones",
            leave_type=LeaveType.VACATION,
            start_date=date(2026, 3, 2),
            end_date=date(2026, 3, 6),
            is_blocking=False,
            has_fmit_conflict=True,
        )
        assert r.has_fmit_conflict is True


class TestLeaveCalendarResponse:
    def test_valid(self):
        r = LeaveCalendarResponse(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            entries=[],
        )
        assert r.conflict_count == 0

    def test_with_conflicts(self):
        r = LeaveCalendarResponse(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            entries=[],
            conflict_count=3,
        )
        assert r.conflict_count == 3


class TestBulkLeaveImportRequest:
    def test_valid(self):
        record = LeaveCreateRequest(
            faculty_id=uuid4(),
            start_date=date(2026, 3, 2),
            end_date=date(2026, 3, 6),
            leave_type=LeaveType.VACATION,
        )
        r = BulkLeaveImportRequest(records=[record])
        assert r.skip_duplicates is True

    def test_no_skip(self):
        record = LeaveCreateRequest(
            faculty_id=uuid4(),
            start_date=date(2026, 3, 2),
            end_date=date(2026, 3, 6),
            leave_type=LeaveType.TDY,
        )
        r = BulkLeaveImportRequest(records=[record], skip_duplicates=False)
        assert r.skip_duplicates is False


class TestBulkLeaveImportResponse:
    def test_valid(self):
        r = BulkLeaveImportResponse(
            success=True, imported_count=5, skipped_count=1, error_count=0
        )
        assert r.errors == []

    def test_with_errors(self):
        r = BulkLeaveImportResponse(
            success=False,
            imported_count=3,
            skipped_count=0,
            error_count=2,
            errors=["Row 4: invalid date", "Row 7: duplicate"],
        )
        assert len(r.errors) == 2
