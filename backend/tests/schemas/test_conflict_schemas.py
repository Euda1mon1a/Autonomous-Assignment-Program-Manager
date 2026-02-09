"""Tests for conflict detection schemas (Pydantic validation and Field coverage)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.conflict import (
    ConflictSeverityEnum,
    ConflictTypeEnum,
    ConflictStatusEnum,
    ConflictBase,
    ConflictInfo,
    ConflictAlertCreate,
    ConflictAlertUpdate,
    ConflictAlertResponse,
    ConflictGroup,
    ConflictDetectionRequest,
    ConflictDetectionResponse,
    ACGMEComplianceCheck,
    SupervisionRatioCheck,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestConflictSeverityEnum:
    def test_values(self):
        assert ConflictSeverityEnum.CRITICAL.value == "critical"
        assert ConflictSeverityEnum.HIGH.value == "high"
        assert ConflictSeverityEnum.MEDIUM.value == "medium"
        assert ConflictSeverityEnum.LOW.value == "low"

    def test_count(self):
        assert len(ConflictSeverityEnum) == 4

    def test_is_str(self):
        assert isinstance(ConflictSeverityEnum.CRITICAL, str)


class TestConflictTypeEnum:
    def test_values(self):
        assert ConflictTypeEnum.LEAVE_FMIT_OVERLAP.value == "leave_fmit_overlap"
        assert (
            ConflictTypeEnum.RESIDENCY_FMIT_DOUBLE_BOOKING.value
            == "residency_fmit_double_booking"
        )
        assert ConflictTypeEnum.BACK_TO_BACK.value == "back_to_back"
        assert ConflictTypeEnum.EXCESSIVE_ALTERNATING.value == "excessive_alternating"
        assert ConflictTypeEnum.WORK_HOUR_VIOLATION.value == "work_hour_violation"
        assert ConflictTypeEnum.REST_DAY_VIOLATION.value == "rest_day_violation"
        assert (
            ConflictTypeEnum.SUPERVISION_RATIO_VIOLATION.value
            == "supervision_ratio_violation"
        )
        assert ConflictTypeEnum.MISSING_SUPERVISION.value == "missing_supervision"
        assert ConflictTypeEnum.CALL_CASCADE.value == "call_cascade"
        assert ConflictTypeEnum.EXTERNAL_COMMITMENT.value == "external_commitment"

    def test_count(self):
        assert len(ConflictTypeEnum) == 10


class TestConflictStatusEnum:
    def test_values(self):
        assert ConflictStatusEnum.NEW.value == "new"
        assert ConflictStatusEnum.ACKNOWLEDGED.value == "acknowledged"
        assert ConflictStatusEnum.RESOLVED.value == "resolved"
        assert ConflictStatusEnum.IGNORED.value == "ignored"

    def test_count(self):
        assert len(ConflictStatusEnum) == 4


# ===========================================================================
# ConflictBase Tests
# ===========================================================================


class TestConflictBase:
    def _valid_kwargs(self):
        return {
            "faculty_id": uuid4(),
            "faculty_name": "Dr. Smith",
            "conflict_type": ConflictTypeEnum.BACK_TO_BACK,
            "severity": ConflictSeverityEnum.MEDIUM,
            "description": "Back to back scheduling conflict",
        }

    def test_valid_minimal(self):
        r = ConflictBase(**self._valid_kwargs())
        assert r.fmit_week is None
        assert r.leave_id is None
        assert r.assignment_id is None
        assert r.residency_block_id is None

    def test_with_optional_fields(self):
        kw = self._valid_kwargs()
        kw["fmit_week"] = date(2026, 3, 1)
        kw["leave_id"] = uuid4()
        kw["assignment_id"] = uuid4()
        kw["residency_block_id"] = uuid4()
        r = ConflictBase(**kw)
        assert r.fmit_week == date(2026, 3, 1)

    # --- faculty_name min_length=1, max_length=200 ---

    def test_faculty_name_empty(self):
        kw = self._valid_kwargs()
        kw["faculty_name"] = ""
        with pytest.raises(ValidationError):
            ConflictBase(**kw)

    def test_faculty_name_too_long(self):
        kw = self._valid_kwargs()
        kw["faculty_name"] = "x" * 201
        with pytest.raises(ValidationError):
            ConflictBase(**kw)

    # --- description min_length=1, max_length=1000 ---

    def test_description_empty(self):
        kw = self._valid_kwargs()
        kw["description"] = ""
        with pytest.raises(ValidationError):
            ConflictBase(**kw)

    def test_description_too_long(self):
        kw = self._valid_kwargs()
        kw["description"] = "x" * 1001
        with pytest.raises(ValidationError):
            ConflictBase(**kw)

    def test_description_max_length(self):
        kw = self._valid_kwargs()
        kw["description"] = "x" * 1000
        r = ConflictBase(**kw)
        assert len(r.description) == 1000


# ===========================================================================
# ConflictInfo Tests
# ===========================================================================


class TestConflictInfo:
    def _valid_kwargs(self):
        return {
            "faculty_id": uuid4(),
            "faculty_name": "Dr. Smith",
            "conflict_type": ConflictTypeEnum.WORK_HOUR_VIOLATION,
            "severity": ConflictSeverityEnum.CRITICAL,
            "description": "80-hour work week violation",
        }

    def test_valid_minimal(self):
        r = ConflictInfo(**self._valid_kwargs())
        assert r.start_date is None
        assert r.end_date is None
        assert r.affected_blocks == []
        assert r.related_people == []
        assert r.hours_worked is None
        assert r.consecutive_days is None
        assert r.supervision_ratio is None
        assert r.suggested_resolution is None

    def test_with_acgme_data(self):
        kw = self._valid_kwargs()
        kw["hours_worked"] = 82.5
        kw["consecutive_days"] = 8
        kw["supervision_ratio"] = 3.0
        r = ConflictInfo(**kw)
        assert r.hours_worked == 82.5
        assert r.consecutive_days == 8

    # --- hours_worked ge=0 ---

    def test_hours_worked_zero(self):
        kw = self._valid_kwargs()
        kw["hours_worked"] = 0
        r = ConflictInfo(**kw)
        assert r.hours_worked == 0

    def test_hours_worked_negative(self):
        kw = self._valid_kwargs()
        kw["hours_worked"] = -1.0
        with pytest.raises(ValidationError):
            ConflictInfo(**kw)

    # --- consecutive_days ge=0 ---

    def test_consecutive_days_zero(self):
        kw = self._valid_kwargs()
        kw["consecutive_days"] = 0
        r = ConflictInfo(**kw)
        assert r.consecutive_days == 0

    def test_consecutive_days_negative(self):
        kw = self._valid_kwargs()
        kw["consecutive_days"] = -1
        with pytest.raises(ValidationError):
            ConflictInfo(**kw)

    # --- supervision_ratio ge=0 ---

    def test_supervision_ratio_zero(self):
        kw = self._valid_kwargs()
        kw["supervision_ratio"] = 0.0
        r = ConflictInfo(**kw)
        assert r.supervision_ratio == 0.0

    def test_supervision_ratio_negative(self):
        kw = self._valid_kwargs()
        kw["supervision_ratio"] = -0.1
        with pytest.raises(ValidationError):
            ConflictInfo(**kw)

    # --- suggested_resolution max_length=500 ---

    def test_suggested_resolution_too_long(self):
        kw = self._valid_kwargs()
        kw["suggested_resolution"] = "x" * 501
        with pytest.raises(ValidationError):
            ConflictInfo(**kw)

    def test_suggested_resolution_max_length(self):
        kw = self._valid_kwargs()
        kw["suggested_resolution"] = "x" * 500
        r = ConflictInfo(**kw)
        assert len(r.suggested_resolution) == 500


# ===========================================================================
# ConflictAlertCreate Tests
# ===========================================================================


class TestConflictAlertCreate:
    def _valid_kwargs(self):
        return {
            "faculty_id": uuid4(),
            "conflict_type": ConflictTypeEnum.LEAVE_FMIT_OVERLAP,
            "severity": ConflictSeverityEnum.HIGH,
            "fmit_week": date(2026, 3, 1),
            "description": "Leave overlaps with FMIT week",
        }

    def test_valid(self):
        r = ConflictAlertCreate(**self._valid_kwargs())
        assert r.leave_id is None
        assert r.swap_id is None

    # --- description min_length=1, max_length=1000 ---

    def test_description_empty(self):
        kw = self._valid_kwargs()
        kw["description"] = ""
        with pytest.raises(ValidationError):
            ConflictAlertCreate(**kw)

    def test_description_too_long(self):
        kw = self._valid_kwargs()
        kw["description"] = "x" * 1001
        with pytest.raises(ValidationError):
            ConflictAlertCreate(**kw)


# ===========================================================================
# ConflictAlertUpdate Tests
# ===========================================================================


class TestConflictAlertUpdate:
    def test_all_none(self):
        r = ConflictAlertUpdate()
        assert r.status is None
        assert r.resolution_notes is None

    # --- resolution_notes max_length=1000 ---

    def test_resolution_notes_too_long(self):
        with pytest.raises(ValidationError):
            ConflictAlertUpdate(resolution_notes="x" * 1001)

    def test_resolution_notes_max_length(self):
        r = ConflictAlertUpdate(resolution_notes="x" * 1000)
        assert len(r.resolution_notes) == 1000


# ===========================================================================
# ConflictAlertResponse Tests
# ===========================================================================


class TestConflictAlertResponse:
    def test_valid(self):
        r = ConflictAlertResponse(
            id=uuid4(),
            faculty_id=uuid4(),
            conflict_type=ConflictTypeEnum.CALL_CASCADE,
            severity=ConflictSeverityEnum.LOW,
            fmit_week=date(2026, 3, 1),
            description="Call cascade issue",
            status=ConflictStatusEnum.NEW,
            created_at=datetime.now(),
        )
        assert r.leave_id is None
        assert r.swap_id is None
        assert r.acknowledged_at is None
        assert r.acknowledged_by_id is None
        assert r.resolved_at is None
        assert r.resolved_by_id is None
        assert r.resolution_notes is None


# ===========================================================================
# ConflictGroup Tests
# ===========================================================================


class TestConflictGroup:
    def test_valid(self):
        r = ConflictGroup(
            group_by="type",
            group_key="back_to_back",
            conflict_count=3,
            conflicts=[],
        )
        assert r.severity_breakdown == {}
        assert r.earliest_date is None
        assert r.latest_date is None


# ===========================================================================
# ConflictDetectionRequest Tests
# ===========================================================================


class TestConflictDetectionRequest:
    def test_defaults(self):
        r = ConflictDetectionRequest()
        assert r.faculty_id is None
        assert r.start_date is None
        assert r.end_date is None
        assert r.include_resolved is False
        assert r.group_by is None


# ===========================================================================
# ConflictDetectionResponse Tests
# ===========================================================================


class TestConflictDetectionResponse:
    def test_valid(self):
        r = ConflictDetectionResponse(total_conflicts=0, conflicts=[])
        assert r.groups is None
        assert r.by_severity == {}
        assert r.by_type == {}
        assert r.affected_faculty_count == 0


# ===========================================================================
# ACGMEComplianceCheck Tests
# ===========================================================================


class TestACGMEComplianceCheck:
    def _valid_kwargs(self):
        return {
            "person_id": uuid4(),
            "person_name": "Dr. Johnson",
            "check_period_start": date(2026, 3, 1),
            "check_period_end": date(2026, 3, 31),
        }

    def test_valid(self):
        r = ACGMEComplianceCheck(**self._valid_kwargs())
        assert r.weekly_hours == {}
        assert r.hours_violations == []
        assert r.consecutive_work_days == []
        assert r.rest_day_violations == []
        assert r.is_compliant is True
        assert r.violation_count == 0

    # --- person_name min_length=1, max_length=200 ---

    def test_person_name_empty(self):
        kw = self._valid_kwargs()
        kw["person_name"] = ""
        with pytest.raises(ValidationError):
            ACGMEComplianceCheck(**kw)

    def test_person_name_too_long(self):
        kw = self._valid_kwargs()
        kw["person_name"] = "x" * 201
        with pytest.raises(ValidationError):
            ACGMEComplianceCheck(**kw)

    # --- violation_count ge=0 ---

    def test_violation_count_zero(self):
        kw = self._valid_kwargs()
        kw["violation_count"] = 0
        r = ACGMEComplianceCheck(**kw)
        assert r.violation_count == 0

    def test_violation_count_negative(self):
        kw = self._valid_kwargs()
        kw["violation_count"] = -1
        with pytest.raises(ValidationError):
            ACGMEComplianceCheck(**kw)


# ===========================================================================
# SupervisionRatioCheck Tests
# ===========================================================================


class TestSupervisionRatioCheck:
    def _valid_kwargs(self):
        return {
            "block_id": uuid4(),
            "block_date": date(2026, 3, 1),
            "block_time": "AM",
            "rotation_name": "Family Medicine",
            "resident_count": 4,
            "pgy1_count": 2,
            "pgy2_3_count": 2,
            "faculty_count": 1,
        }

    def test_valid(self):
        r = SupervisionRatioCheck(**self._valid_kwargs())
        assert r.pgy1_ratio_actual is None
        assert r.pgy1_ratio_required == 2.0
        assert r.pgy2_3_ratio_actual is None
        assert r.pgy2_3_ratio_required == 4.0
        assert r.is_compliant is True
        assert r.violations == []

    # --- block_time max_length=20 ---

    def test_block_time_too_long(self):
        kw = self._valid_kwargs()
        kw["block_time"] = "x" * 21
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    # --- rotation_name min_length=1, max_length=200 ---

    def test_rotation_name_empty(self):
        kw = self._valid_kwargs()
        kw["rotation_name"] = ""
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    def test_rotation_name_too_long(self):
        kw = self._valid_kwargs()
        kw["rotation_name"] = "x" * 201
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    # --- count fields ge=0 ---

    def test_resident_count_negative(self):
        kw = self._valid_kwargs()
        kw["resident_count"] = -1
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    def test_pgy1_count_negative(self):
        kw = self._valid_kwargs()
        kw["pgy1_count"] = -1
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    def test_pgy2_3_count_negative(self):
        kw = self._valid_kwargs()
        kw["pgy2_3_count"] = -1
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    def test_faculty_count_negative(self):
        kw = self._valid_kwargs()
        kw["faculty_count"] = -1
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    # --- ratio fields ge=0 ---

    def test_pgy1_ratio_actual_negative(self):
        kw = self._valid_kwargs()
        kw["pgy1_ratio_actual"] = -0.1
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    def test_pgy1_ratio_required_negative(self):
        kw = self._valid_kwargs()
        kw["pgy1_ratio_required"] = -0.1
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    def test_pgy2_3_ratio_actual_negative(self):
        kw = self._valid_kwargs()
        kw["pgy2_3_ratio_actual"] = -0.1
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)

    def test_pgy2_3_ratio_required_negative(self):
        kw = self._valid_kwargs()
        kw["pgy2_3_ratio_required"] = -0.1
        with pytest.raises(ValidationError):
            SupervisionRatioCheck(**kw)
