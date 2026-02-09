"""Tests for call assignment schemas (Field bounds, field_validators, defaults, aliases)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.call_assignment import (
    CallType,
    CallAssignmentBase,
    CallAssignmentCreate,
    CallAssignmentUpdate,
    PersonBrief,
    CallAssignmentResponse,
    CallAssignmentListResponse,
    BulkCallAssignmentCreate,
    BulkCallAssignmentResponse,
    CallCoverageReport,
    CallEquityReport,
    BulkCallAssignmentUpdateInput,
    BulkCallAssignmentUpdateRequest,
    BulkCallAssignmentUpdateResponse,
    PCATGenerationRequest,
    PCATAssignmentResult,
    PCATGenerationResponse,
    SimulatedChange,
    EquityPreviewRequest,
    FacultyEquityDetail,
    EquityPreviewResponse,
)


# ── CallType enum ──────────────────────────────────────────────────────


class TestCallType:
    def test_values(self):
        assert CallType.SUNDAY == "sunday"
        assert CallType.WEEKDAY == "weekday"
        assert CallType.HOLIDAY == "holiday"
        assert CallType.BACKUP == "backup"

    def test_count(self):
        assert len(CallType) == 4


# ── CallAssignmentBase ─────────────────────────────────────────────────


class TestCallAssignmentBase:
    def test_defaults(self):
        uid = uuid4()
        r = CallAssignmentBase(call_date=date(2026, 1, 15), person_id=uid)
        assert r.call_type == "weekday"
        assert r.is_weekend is False
        assert r.is_holiday is False

    # --- call_type field_validator ---

    def test_call_type_valid_all(self):
        uid = uuid4()
        for ct in ("sunday", "weekday", "holiday", "backup"):
            r = CallAssignmentBase(
                call_date=date(2026, 1, 15), person_id=uid, call_type=ct
            )
            assert r.call_type == ct

    def test_call_type_invalid(self):
        with pytest.raises(ValidationError, match="call_type must be one of"):
            CallAssignmentBase(
                call_date=date(2026, 1, 15),
                person_id=uuid4(),
                call_type="overnight",
            )


# ── CallAssignmentCreate ───────────────────────────────────────────────


class TestCallAssignmentCreate:
    def test_inherits_base(self):
        r = CallAssignmentCreate(
            call_date=date(2026, 1, 15), person_id=uuid4(), call_type="sunday"
        )
        assert r.call_type == "sunday"


# ── CallAssignmentUpdate ───────────────────────────────────────────────


class TestCallAssignmentUpdate:
    def test_all_none(self):
        r = CallAssignmentUpdate()
        assert r.call_date is None
        assert r.person_id is None
        assert r.call_type is None
        assert r.is_weekend is None
        assert r.is_holiday is None
        assert r.auto_generate_post_call is None

    # --- call_type validator (handles None) ---

    def test_call_type_none_ok(self):
        r = CallAssignmentUpdate(call_type=None)
        assert r.call_type is None

    def test_call_type_valid(self):
        r = CallAssignmentUpdate(call_type="holiday")
        assert r.call_type == "holiday"

    def test_call_type_invalid(self):
        with pytest.raises(ValidationError, match="call_type must be one of"):
            CallAssignmentUpdate(call_type="night")

    # --- call_date validator (not more than 2 years future) ---

    def test_call_date_within_range(self):
        r = CallAssignmentUpdate(call_date=date.today() + timedelta(days=365))
        assert r.call_date is not None

    def test_call_date_too_far_future(self):
        with pytest.raises(ValidationError, match="2 years"):
            CallAssignmentUpdate(call_date=date.today() + timedelta(days=731))

    def test_call_date_none_ok(self):
        r = CallAssignmentUpdate(call_date=None)
        assert r.call_date is None


# ── PersonBrief ────────────────────────────────────────────────────────


class TestPersonBrief:
    def test_valid(self):
        uid = uuid4()
        r = PersonBrief(id=uid, name="Dr. Smith")
        assert r.faculty_role is None

    def test_with_role(self):
        r = PersonBrief(id=uuid4(), name="Dr. Jones", faculty_role="Attending")
        assert r.faculty_role == "Attending"


# ── CallAssignmentResponse ─────────────────────────────────────────────


class TestCallAssignmentResponse:
    def test_by_alias(self):
        r = CallAssignmentResponse(
            id=uuid4(),
            date=date(2026, 1, 15),
            person_id=uuid4(),
            call_type="weekday",
            is_weekend=False,
            is_holiday=False,
        )
        assert r.call_date == date(2026, 1, 15)

    def test_by_field_name(self):
        r = CallAssignmentResponse(
            id=uuid4(),
            call_date=date(2026, 1, 15),
            person_id=uuid4(),
            call_type="weekday",
            is_weekend=False,
            is_holiday=False,
        )
        assert r.call_date == date(2026, 1, 15)

    def test_person_default_none(self):
        r = CallAssignmentResponse(
            id=uuid4(),
            date=date(2026, 1, 15),
            person_id=uuid4(),
            call_type="weekday",
            is_weekend=False,
            is_holiday=False,
        )
        assert r.person is None


# ── CallAssignmentListResponse ─────────────────────────────────────────


class TestCallAssignmentListResponse:
    def test_defaults(self):
        r = CallAssignmentListResponse(items=[], total=0)
        assert r.skip == 0
        assert r.limit == 100


# ── BulkCallAssignmentCreate ───────────────────────────────────────────


class TestBulkCallAssignmentCreate:
    def test_defaults(self):
        a = CallAssignmentCreate(
            call_date=date(2026, 1, 15), person_id=uuid4(), call_type="weekday"
        )
        r = BulkCallAssignmentCreate(assignments=[a])
        assert r.replace_existing is False

    def test_empty_assignments(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            BulkCallAssignmentCreate(assignments=[])


# ── BulkCallAssignmentResponse ─────────────────────────────────────────


class TestBulkCallAssignmentResponse:
    def test_defaults(self):
        r = BulkCallAssignmentResponse(created=5)
        assert r.errors == []


# ── CallCoverageReport ─────────────────────────────────────────────────


class TestCallCoverageReport:
    def test_defaults(self):
        r = CallCoverageReport(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            total_expected_nights=22,
            covered_nights=20,
            coverage_percentage=90.9,
        )
        assert r.gaps == []


# ── BulkCallAssignmentUpdateRequest ────────────────────────────────────


class TestBulkCallAssignmentUpdateRequest:
    def test_valid(self):
        uid = uuid4()
        inp = BulkCallAssignmentUpdateInput(person_id=uid)
        r = BulkCallAssignmentUpdateRequest(assignment_ids=[uuid4()], updates=inp)
        assert r.auto_generate_post_call is False

    def test_empty_ids(self):
        inp = BulkCallAssignmentUpdateInput()
        with pytest.raises(ValidationError, match="cannot be empty"):
            BulkCallAssignmentUpdateRequest(assignment_ids=[], updates=inp)


# ── BulkCallAssignmentUpdateResponse ───────────────────────────────────


class TestBulkCallAssignmentUpdateResponse:
    def test_defaults(self):
        r = BulkCallAssignmentUpdateResponse(updated=3)
        assert r.errors == []
        assert r.assignments == []


# ── PCATGenerationRequest ──────────────────────────────────────────────


class TestPCATGenerationRequest:
    def test_valid(self):
        r = PCATGenerationRequest(assignment_ids=[uuid4()])
        assert len(r.assignment_ids) == 1

    def test_empty_ids(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            PCATGenerationRequest(assignment_ids=[])


# ── PCATAssignmentResult ───────────────────────────────────────────────


class TestPCATAssignmentResult:
    def test_defaults(self):
        r = PCATAssignmentResult(
            call_assignment_id=uuid4(),
            call_date=date(2026, 1, 15),
            person_id=uuid4(),
        )
        assert r.pcat_created is False
        assert r.do_created is False
        assert r.person_name is None
        assert r.pcat_assignment_id is None
        assert r.do_assignment_id is None
        assert r.error is None


# ── PCATGenerationResponse ─────────────────────────────────────────────


class TestPCATGenerationResponse:
    def test_defaults(self):
        r = PCATGenerationResponse(processed=5, pcat_created=3, do_created=2)
        assert r.errors == []
        assert r.results == []


# ── SimulatedChange ────────────────────────────────────────────────────


class TestSimulatedChange:
    def test_defaults(self):
        r = SimulatedChange(new_person_id=uuid4())
        assert r.assignment_id is None
        assert r.call_date is None
        assert r.old_person_id is None
        assert r.call_type == "overnight"


# ── EquityPreviewRequest ──────────────────────────────────────────────


class TestEquityPreviewRequest:
    def test_defaults(self):
        r = EquityPreviewRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31)
        )
        assert r.simulated_changes == []


# ── FacultyEquityDetail ───────────────────────────────────────────────


class TestFacultyEquityDetail:
    def test_valid(self):
        r = FacultyEquityDetail(
            person_id=uuid4(),
            name="Dr. Smith",
            current_sunday_calls=3,
            current_weekday_calls=10,
            current_total_calls=13,
            projected_sunday_calls=4,
            projected_weekday_calls=10,
            projected_total_calls=14,
            delta=1,
        )
        assert r.delta == 1


# ── EquityPreviewResponse ─────────────────────────────────────────────


class TestEquityPreviewResponse:
    def test_defaults(self):
        equity = CallEquityReport(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            faculty_count=10,
            total_overnight_calls=100,
            sunday_call_stats={"min": 1, "max": 5},
            weekday_call_stats={"min": 5, "max": 15},
            distribution=[],
        )
        r = EquityPreviewResponse(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            current_equity=equity,
            projected_equity=equity,
            improvement_score=0.5,
        )
        assert r.faculty_details == []
        assert r.improvement_score == 0.5
