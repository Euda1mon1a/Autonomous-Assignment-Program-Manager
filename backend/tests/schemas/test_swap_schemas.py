"""Tests for swap schemas (enums, field_validators, Field bounds)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.swap import (
    SwapStatusSchema,
    SwapTypeSchema,
    SwapExecuteRequest,
    SwapApprovalRequest,
    SwapRollbackRequest,
    SwapHistoryFilter,
    SwapValidationResult,
    SwapRecordResponse,
    SwapExecuteResponse,
    SwapRequestCreateResponse,
    SwapApprovalResponse,
    SwapExecuteByIdResponse,
    SwapHistoryResponse,
)


class TestSwapStatusSchema:
    def test_values(self):
        assert SwapStatusSchema.PENDING.value == "pending"
        assert SwapStatusSchema.APPROVED.value == "approved"
        assert SwapStatusSchema.EXECUTED.value == "executed"
        assert SwapStatusSchema.REJECTED.value == "rejected"
        assert SwapStatusSchema.CANCELLED.value == "cancelled"
        assert SwapStatusSchema.ROLLED_BACK.value == "rolled_back"

    def test_count(self):
        assert len(SwapStatusSchema) == 6

    def test_is_str(self):
        assert isinstance(SwapStatusSchema.PENDING, str)


class TestSwapTypeSchema:
    def test_values(self):
        assert SwapTypeSchema.ONE_TO_ONE.value == "one_to_one"
        assert SwapTypeSchema.ABSORB.value == "absorb"

    def test_count(self):
        assert len(SwapTypeSchema) == 2


class TestSwapApprovalRequest:
    def test_valid(self):
        r = SwapApprovalRequest(approved=True)
        assert r.notes is None

    def test_with_notes(self):
        r = SwapApprovalRequest(approved=False, notes="Conflict with leave")
        assert r.notes == "Conflict with leave"

    # --- notes max_length=500 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            SwapApprovalRequest(approved=True, notes="x" * 501)

    # --- notes field_validator (strip, not empty) ---

    def test_notes_empty_string(self):
        with pytest.raises(ValidationError, match="notes cannot be empty"):
            SwapApprovalRequest(approved=True, notes="   ")

    def test_notes_strips(self):
        r = SwapApprovalRequest(approved=True, notes="  Some notes  ")
        assert r.notes == "Some notes"


class TestSwapRollbackRequest:
    def test_valid(self):
        r = SwapRollbackRequest(reason="Data entry error by coordinator")
        assert r.reason == "Data entry error by coordinator"

    # --- reason min_length=10, max_length=500 ---

    def test_reason_too_short(self):
        with pytest.raises(ValidationError):
            SwapRollbackRequest(reason="short")

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            SwapRollbackRequest(reason="x" * 501)

    # --- reason field_validator (strip, not empty) ---

    def test_reason_whitespace_only(self):
        with pytest.raises(ValidationError, match="reason cannot be empty"):
            SwapRollbackRequest(reason="          ")  # 10+ chars of whitespace


class TestSwapHistoryFilter:
    def test_defaults(self):
        r = SwapHistoryFilter()
        assert r.faculty_id is None
        assert r.status is None
        assert r.start_date is None
        assert r.end_date is None
        assert r.page == 1
        assert r.page_size == 20

    # --- page ge=1 ---

    def test_page_zero(self):
        with pytest.raises(ValidationError):
            SwapHistoryFilter(page=0)

    # --- page_size ge=1, le=100 ---

    def test_page_size_zero(self):
        with pytest.raises(ValidationError):
            SwapHistoryFilter(page_size=0)

    def test_page_size_above_max(self):
        with pytest.raises(ValidationError):
            SwapHistoryFilter(page_size=101)

    def test_page_size_boundaries(self):
        r = SwapHistoryFilter(page_size=1)
        assert r.page_size == 1
        r = SwapHistoryFilter(page_size=100)
        assert r.page_size == 100

    # --- page field_validator (max 1000) ---

    def test_page_too_large(self):
        with pytest.raises(ValidationError, match="page number too large"):
            SwapHistoryFilter(page=1001)

    def test_with_filter(self):
        r = SwapHistoryFilter(
            status=SwapStatusSchema.PENDING,
            page=2,
            page_size=50,
        )
        assert r.status == SwapStatusSchema.PENDING
        assert r.page == 2


class TestSwapValidationResult:
    def test_valid_defaults(self):
        r = SwapValidationResult(valid=True)
        assert r.errors == []
        assert r.warnings == []
        assert r.back_to_back_conflict is False
        assert r.external_conflict is None

    def test_invalid(self):
        r = SwapValidationResult(
            valid=False,
            errors=["Coverage gap created"],
            warnings=["Back-to-back shift"],
            back_to_back_conflict=True,
            external_conflict="Conflicts with TDY schedule",
        )
        assert len(r.errors) == 1
        assert r.back_to_back_conflict is True


class TestSwapRecordResponse:
    def test_valid(self):
        r = SwapRecordResponse(
            id=uuid4(),
            source_faculty_id=uuid4(),
            source_faculty_name="Dr. Smith",
            source_week=date(2026, 3, 2),
            target_faculty_id=uuid4(),
            target_faculty_name="Dr. Jones",
            target_week=date(2026, 3, 9),
            swap_type=SwapTypeSchema.ONE_TO_ONE,
            status=SwapStatusSchema.EXECUTED,
            reason="Vacation conflict",
            requested_at=datetime(2026, 3, 1),
            executed_at=datetime(2026, 3, 1, 12, 0),
        )
        assert r.swap_type == SwapTypeSchema.ONE_TO_ONE

    def test_absorb_no_target_week(self):
        r = SwapRecordResponse(
            id=uuid4(),
            source_faculty_id=uuid4(),
            source_faculty_name="Dr. Smith",
            source_week=date(2026, 3, 2),
            target_faculty_id=uuid4(),
            target_faculty_name="Dr. Jones",
            target_week=None,
            swap_type=SwapTypeSchema.ABSORB,
            status=SwapStatusSchema.PENDING,
            reason=None,
            requested_at=datetime(2026, 3, 1),
            executed_at=None,
        )
        assert r.target_week is None
        assert r.executed_at is None


class TestSwapExecuteResponse:
    def test_valid(self):
        validation = SwapValidationResult(valid=True)
        r = SwapExecuteResponse(
            success=True,
            swap_id=uuid4(),
            message="Swap executed",
            validation=validation,
        )
        assert r.success is True


class TestSwapRequestCreateResponse:
    def test_valid(self):
        r = SwapRequestCreateResponse(
            success=True,
            swap_id=uuid4(),
            status=SwapStatusSchema.PENDING,
            message="Request created",
        )
        assert r.status == SwapStatusSchema.PENDING


class TestSwapApprovalResponse:
    def test_valid(self):
        r = SwapApprovalResponse(
            success=True,
            status=SwapStatusSchema.APPROVED,
            message="Swap approved",
        )
        assert r.status == SwapStatusSchema.APPROVED


class TestSwapExecuteByIdResponse:
    def test_valid(self):
        r = SwapExecuteByIdResponse(
            success=True,
            status=SwapStatusSchema.EXECUTED,
            message="Executed",
        )
        assert r.status == SwapStatusSchema.EXECUTED


class TestSwapHistoryResponse:
    def test_valid(self):
        r = SwapHistoryResponse(items=[], total=0, page=1, page_size=20, pages=0)
        assert r.items == []
        assert r.pages == 0
