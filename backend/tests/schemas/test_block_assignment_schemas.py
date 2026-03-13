"""Tests for block assignment schemas (Pydantic validation, field_validator, Field bounds)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.block_assignment import (
    AssignmentReasonEnum,
    BlockAssignmentBase,
    BlockAssignmentCreate,
    BlockAssignmentUpdate,
    RotationTemplateInfo,
    ResidentInfo,
    BlockAssignmentResponse,
    BlockAssignmentListResponse,
    ResidentLeaveInfo,
    RotationCapacity,
    BlockScheduleRequest,
    AssignmentPreview,
    CoverageGap,
    LeaveConflict,
    BlockScheduleResponse,
    BlockSchedulerDashboard,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestAssignmentReasonEnum:
    def test_values(self):
        assert AssignmentReasonEnum.LEAVE_ELIGIBLE_MATCH.value == "leave_eligible_match"
        assert AssignmentReasonEnum.COVERAGE_PRIORITY.value == "coverage_priority"
        assert AssignmentReasonEnum.BALANCED.value == "balanced"
        assert AssignmentReasonEnum.MANUAL.value == "manual"
        assert AssignmentReasonEnum.SPECIALTY_MATCH.value == "specialty_match"

    def test_count(self):
        assert len(AssignmentReasonEnum) == 5

    def test_is_str(self):
        assert isinstance(AssignmentReasonEnum.BALANCED, str)


# ===========================================================================
# BlockAssignmentBase Tests
# ===========================================================================


class TestBlockAssignmentBase:
    def _valid_kwargs(self):
        return {
            "block_number": 5,
            "academic_year": 2026,
            "resident_id": uuid4(),
            "block_half": 1,
        }

    def test_valid_minimal(self):
        r = BlockAssignmentBase(**self._valid_kwargs())
        assert r.rotation_template_id is None
        assert r.has_leave is False
        assert r.leave_days == 0
        assert r.assignment_reason == "balanced"
        assert r.notes is None

    # --- block_number ge=0, le=13 ---

    def test_block_number_boundaries(self):
        kw = self._valid_kwargs()
        kw["block_number"] = 0
        r = BlockAssignmentBase(**kw)
        assert r.block_number == 0

        kw["block_number"] = 13
        r = BlockAssignmentBase(**kw)
        assert r.block_number == 13

    def test_block_number_negative(self):
        kw = self._valid_kwargs()
        kw["block_number"] = -1
        with pytest.raises(ValidationError):
            BlockAssignmentBase(**kw)

    def test_block_number_above_max(self):
        kw = self._valid_kwargs()
        kw["block_number"] = 14
        with pytest.raises(ValidationError):
            BlockAssignmentBase(**kw)

    # --- academic_year ge=2020, le=2100 ---

    def test_academic_year_boundaries(self):
        kw = self._valid_kwargs()
        kw["academic_year"] = 2020
        r = BlockAssignmentBase(**kw)
        assert r.academic_year == 2020

        kw["academic_year"] = 2100
        r = BlockAssignmentBase(**kw)
        assert r.academic_year == 2100

    def test_academic_year_below_min(self):
        kw = self._valid_kwargs()
        kw["academic_year"] = 2019
        with pytest.raises(ValidationError):
            BlockAssignmentBase(**kw)

    def test_academic_year_above_max(self):
        kw = self._valid_kwargs()
        kw["academic_year"] = 2101
        with pytest.raises(ValidationError):
            BlockAssignmentBase(**kw)

    # --- leave_days ge=0 ---

    def test_leave_days_zero(self):
        kw = self._valid_kwargs()
        kw["leave_days"] = 0
        r = BlockAssignmentBase(**kw)
        assert r.leave_days == 0

    def test_leave_days_negative(self):
        kw = self._valid_kwargs()
        kw["leave_days"] = -1
        with pytest.raises(ValidationError):
            BlockAssignmentBase(**kw)

    # --- assignment_reason field_validator ---

    def test_all_valid_reasons(self):
        for reason in [r.value for r in AssignmentReasonEnum]:
            kw = self._valid_kwargs()
            kw["assignment_reason"] = reason
            r = BlockAssignmentBase(**kw)
            assert r.assignment_reason == reason

    def test_invalid_reason(self):
        kw = self._valid_kwargs()
        kw["assignment_reason"] = "arbitrary"
        with pytest.raises(ValidationError):
            BlockAssignmentBase(**kw)

    # --- notes field_validator (>1000 chars) ---

    def test_notes_too_long(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 1001
        with pytest.raises(ValidationError):
            BlockAssignmentBase(**kw)

    def test_notes_max_length(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 1000
        r = BlockAssignmentBase(**kw)
        assert len(r.notes) == 1000


# ===========================================================================
# BlockAssignmentCreate Tests
# ===========================================================================


class TestBlockAssignmentCreate:
    def test_valid(self):
        r = BlockAssignmentCreate(
            block_number=1,
            academic_year=2026,
            resident_id=uuid4(),
            block_half=1,
        )
        assert r.created_by is None

    def test_with_created_by(self):
        r = BlockAssignmentCreate(
            block_number=1,
            academic_year=2026,
            resident_id=uuid4(),
            block_half=1,
            created_by="admin",
        )
        assert r.created_by == "admin"


# ===========================================================================
# BlockAssignmentUpdate Tests
# ===========================================================================


class TestBlockAssignmentUpdate:
    def test_all_none(self):
        r = BlockAssignmentUpdate()
        assert r.rotation_template_id is None
        assert r.has_leave is None
        assert r.leave_days is None
        assert r.assignment_reason is None
        assert r.notes is None

    # --- leave_days ge=0 ---

    def test_leave_days_negative(self):
        with pytest.raises(ValidationError):
            BlockAssignmentUpdate(leave_days=-1)

    # --- assignment_reason field_validator ---

    def test_reason_valid(self):
        r = BlockAssignmentUpdate(assignment_reason="manual")
        assert r.assignment_reason == "manual"

    def test_reason_none_allowed(self):
        r = BlockAssignmentUpdate(assignment_reason=None)
        assert r.assignment_reason is None

    def test_reason_invalid(self):
        with pytest.raises(ValidationError):
            BlockAssignmentUpdate(assignment_reason="arbitrary")

    # --- notes field_validator (>1000 chars) ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            BlockAssignmentUpdate(notes="x" * 1001)


# ===========================================================================
# RotationTemplateInfo Tests
# ===========================================================================


class TestRotationTemplateInfo:
    def test_valid(self):
        r = RotationTemplateInfo(
            id=uuid4(),
            name="Family Medicine",
            rotation_type="outpatient",
            leave_eligible=True,
        )
        assert r.leave_eligible is True


# ===========================================================================
# ResidentInfo Tests
# ===========================================================================


class TestResidentInfo:
    def test_valid(self):
        r = ResidentInfo(id=uuid4(), name="Dr. Smith", pgy_level=2)
        assert r.pgy_level == 2

    def test_pgy_none(self):
        r = ResidentInfo(id=uuid4(), name="Dr. Smith", pgy_level=None)
        assert r.pgy_level is None


# ===========================================================================
# BlockAssignmentListResponse Tests
# ===========================================================================


class TestBlockAssignmentListResponse:
    def test_valid(self):
        r = BlockAssignmentListResponse(items=[], total=0)
        assert r.block_number is None
        assert r.academic_year is None


# ===========================================================================
# BlockScheduleRequest Tests
# ===========================================================================


class TestBlockScheduleRequest:
    def test_defaults(self):
        r = BlockScheduleRequest(block_number=5, academic_year=2026)
        assert r.dry_run is True
        assert r.include_all_residents is True

    # --- block_number ge=0, le=13 ---

    def test_block_number_negative(self):
        with pytest.raises(ValidationError):
            BlockScheduleRequest(block_number=-1, academic_year=2026)

    def test_block_number_above_max(self):
        with pytest.raises(ValidationError):
            BlockScheduleRequest(block_number=14, academic_year=2026)

    # --- academic_year ge=2020, le=2100 ---

    def test_academic_year_below_min(self):
        with pytest.raises(ValidationError):
            BlockScheduleRequest(block_number=1, academic_year=2019)

    def test_academic_year_above_max(self):
        with pytest.raises(ValidationError):
            BlockScheduleRequest(block_number=1, academic_year=2101)


# ===========================================================================
# Simple Response Model Tests
# ===========================================================================


class TestResidentLeaveInfo:
    def test_valid(self):
        r = ResidentLeaveInfo(
            resident_id=uuid4(),
            resident_name="Dr. Smith",
            pgy_level=2,
            leave_days=5,
            leave_types=["vacation"],
        )
        assert r.leave_days == 5


class TestRotationCapacity:
    def test_valid(self):
        r = RotationCapacity(
            rotation_template_id=uuid4(),
            rotation_name="ICU",
            leave_eligible=False,
            max_residents=None,
            current_assigned=3,
            available_slots=None,
        )
        assert r.max_residents is None


class TestAssignmentPreview:
    def test_valid(self):
        r = AssignmentPreview(
            resident_id=uuid4(),
            resident_name="Dr. Jones",
            pgy_level=1,
            rotation_template_id=uuid4(),
            rotation_name="FM Clinic",
            has_leave=True,
            leave_days=3,
            assignment_reason="leave_eligible_match",
            is_leave_eligible_rotation=True,
        )
        assert r.is_leave_eligible_rotation is True


class TestCoverageGap:
    def test_valid(self):
        r = CoverageGap(
            rotation_template_id=uuid4(),
            rotation_name="Emergency",
            required_coverage=4,
            assigned_coverage=2,
            gap=2,
            severity="critical",
        )
        assert r.gap == 2


class TestLeaveConflict:
    def test_valid(self):
        r = LeaveConflict(
            resident_id=uuid4(),
            resident_name="Dr. Brown",
            rotation_name="ICU",
            leave_days=5,
            conflict_reason="non_leave_eligible_rotation",
        )
        assert r.conflict_reason == "non_leave_eligible_rotation"


class TestBlockScheduleResponse:
    def test_valid(self):
        r = BlockScheduleResponse(
            block_number=5,
            academic_year=2026,
            dry_run=True,
            success=True,
            message="Preview generated",
            assignments=[],
            total_residents=20,
            residents_with_leave=5,
            coverage_gaps=[],
            leave_conflicts=[],
            rotation_capacities=[],
        )
        assert r.total_residents == 20


class TestBlockSchedulerDashboard:
    def test_valid(self):
        r = BlockSchedulerDashboard(
            block_number=5,
            academic_year=2026,
            block_start_date=None,
            block_end_date=None,
            total_residents=20,
            residents_with_leave=[],
            rotation_capacities=[],
            leave_eligible_rotations=5,
            non_leave_eligible_rotations=10,
            current_assignments=[],
            unassigned_residents=3,
        )
        assert r.unassigned_residents == 3
