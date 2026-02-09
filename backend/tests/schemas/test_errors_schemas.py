"""Tests for error response schemas (Field bounds, defaults, inheritance)."""

import pytest
from pydantic import ValidationError

from app.core.error_codes import ErrorCode
from app.schemas.errors import (
    ErrorDetail,
    ErrorResponse,
    ValidationErrorResponse,
    ACGMEViolationDetail,
    ACGMEComplianceErrorResponse,
    ScheduleConflictDetail,
    ScheduleConflictErrorResponse,
    RateLimitErrorResponse,
    ErrorResponseWithSuggestions,
    MultiErrorResponse,
    SimpleErrorResponse,
)


# ── Helper ─────────────────────────────────────────────────────────────

_BASE_KWARGS = {
    "type": "https://example.com/errors/test",
    "title": "Test Error",
    "status": 422,
    "detail": "Something went wrong",
    "instance": "/api/v1/test",
    "error_code": ErrorCode.VALIDATION_ERROR,
    "error_id": "abc-123",
    "timestamp": "2026-01-15T10:00:00Z",
}


# ── ErrorDetail ────────────────────────────────────────────────────────


class TestErrorDetail:
    def test_defaults(self):
        r = ErrorDetail(field="email", message="Invalid")
        assert r.type is None
        assert r.location is None

    def test_all_fields(self):
        r = ErrorDetail(
            field="email",
            message="Invalid",
            type="value_error.email",
            location="body",
        )
        assert r.location == "body"


# ── ErrorResponse ──────────────────────────────────────────────────────


class TestErrorResponse:
    def test_valid(self):
        r = ErrorResponse(**_BASE_KWARGS)
        assert r.status == 422
        assert r.error_code == ErrorCode.VALIDATION_ERROR

    # --- status ge=100, le=599 ---

    def test_status_below_min(self):
        with pytest.raises(ValidationError):
            ErrorResponse(**{**_BASE_KWARGS, "status": 99})

    def test_status_above_max(self):
        with pytest.raises(ValidationError):
            ErrorResponse(**{**_BASE_KWARGS, "status": 600})


# ── ValidationErrorResponse ────────────────────────────────────────────


class TestValidationErrorResponse:
    def test_valid(self):
        detail = ErrorDetail(field="name", message="Required")
        r = ValidationErrorResponse(**_BASE_KWARGS, errors=[detail])
        assert len(r.errors) == 1
        assert r.errors[0].field == "name"

    def test_inherits_status_bounds(self):
        with pytest.raises(ValidationError):
            ValidationErrorResponse(**{**_BASE_KWARGS, "status": 99}, errors=[])


# ── ACGMEViolationDetail ───────────────────────────────────────────────


class TestACGMEViolationDetail:
    def test_defaults(self):
        r = ACGMEViolationDetail()
        assert r.resident_id is None
        assert r.violation_date is None
        assert r.period_start is None
        assert r.period_end is None
        assert r.actual_hours is None
        assert r.limit_hours is None
        assert r.rule_violated is None


# ── ACGMEComplianceErrorResponse ───────────────────────────────────────


class TestACGMEComplianceErrorResponse:
    def test_valid(self):
        violation = ACGMEViolationDetail(
            actual_hours=84.5, limit_hours=80.0, rule_violated="80-hour"
        )
        r = ACGMEComplianceErrorResponse(**_BASE_KWARGS, violation=violation)
        assert r.violation.actual_hours == 84.5


# ── ScheduleConflictDetail ─────────────────────────────────────────────


class TestScheduleConflictDetail:
    def test_defaults(self):
        r = ScheduleConflictDetail()
        assert r.conflicting_assignment_id is None
        assert r.requested_date is None
        assert r.person_id is None
        assert r.conflict_type is None


# ── ScheduleConflictErrorResponse ──────────────────────────────────────


class TestScheduleConflictErrorResponse:
    def test_valid(self):
        conflict = ScheduleConflictDetail(conflict_type="time")
        r = ScheduleConflictErrorResponse(**_BASE_KWARGS, conflict=conflict)
        assert r.conflict.conflict_type == "time"


# ── RateLimitErrorResponse ─────────────────────────────────────────────


class TestRateLimitErrorResponse:
    def test_valid(self):
        r = RateLimitErrorResponse(
            **_BASE_KWARGS, limit=100, window_seconds=60, retry_after=45
        )
        assert r.limit == 100
        assert r.window_seconds == 60
        assert r.retry_after == 45


# ── ErrorResponseWithSuggestions ───────────────────────────────────────


class TestErrorResponseWithSuggestions:
    def test_valid(self):
        r = ErrorResponseWithSuggestions(
            **_BASE_KWARGS, suggestions=["Check fields", "Retry later"]
        )
        assert len(r.suggestions) == 2


# ── MultiErrorResponse ─────────────────────────────────────────────────


class TestMultiErrorResponse:
    def test_valid(self):
        err = ErrorResponse(**_BASE_KWARGS)
        r = MultiErrorResponse(
            errors=[err], total_errors=1, timestamp="2026-01-15T10:00:00Z"
        )
        assert r.total_errors == 1
        assert len(r.errors) == 1


# ── SimpleErrorResponse ────────────────────────────────────────────────


class TestSimpleErrorResponse:
    def test_defaults(self):
        r = SimpleErrorResponse(detail="Not found", status_code=404)
        assert r.error_code is None

    def test_with_error_code(self):
        r = SimpleErrorResponse(
            detail="Not found", status_code=404, error_code="NOT_FOUND"
        )
        assert r.error_code == "NOT_FOUND"
