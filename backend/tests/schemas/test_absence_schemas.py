"""Tests for absence schemas (Pydantic validation, field_validator, model_validator)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.validators.common import ValidationError as AppValidationError

from app.schemas.absence import (
    AbsenceType,
    VALID_ABSENCE_TYPES,
    AbsenceBase,
    AbsenceCreate,
    AbsenceUpdate,
    AbsenceListResponse,
    AbsenceBulkCreate,
    AbsenceValidationError as AbsenceValError,
    AbsenceBulkPreview,
    AbsenceBulkApply,
    ThresholdStatus,
    AwayAbsenceDetail,
    AwayFromProgramSummary,
    AwayFromProgramCheck,
    AllResidentsAwayStatus,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestAbsenceType:
    def test_values(self):
        assert AbsenceType.VACATION.value == "vacation"
        assert AbsenceType.DEPLOYMENT.value == "deployment"
        assert AbsenceType.TDY.value == "tdy"
        assert AbsenceType.MEDICAL.value == "medical"
        assert AbsenceType.FAMILY_EMERGENCY.value == "family_emergency"
        assert AbsenceType.CONFERENCE.value == "conference"
        assert AbsenceType.BEREAVEMENT.value == "bereavement"
        assert AbsenceType.EMERGENCY_LEAVE.value == "emergency_leave"
        assert AbsenceType.SICK.value == "sick"
        assert AbsenceType.CONVALESCENT.value == "convalescent"
        assert AbsenceType.MATERNITY_PATERNITY.value == "maternity_paternity"
        assert AbsenceType.TRAINING.value == "training"
        assert AbsenceType.MILITARY_DUTY.value == "military_duty"

    def test_count(self):
        assert len(AbsenceType) == 13

    def test_valid_absence_types_tuple(self):
        assert len(VALID_ABSENCE_TYPES) == 13
        assert "vacation" in VALID_ABSENCE_TYPES
        assert "deployment" in VALID_ABSENCE_TYPES


class TestThresholdStatus:
    def test_values(self):
        assert ThresholdStatus.OK.value == "ok"
        assert ThresholdStatus.WARNING.value == "warning"
        assert ThresholdStatus.CRITICAL.value == "critical"
        assert ThresholdStatus.EXCEEDED.value == "exceeded"

    def test_count(self):
        assert len(ThresholdStatus) == 4


# ===========================================================================
# AbsenceBase Tests
# ===========================================================================


class TestAbsenceBase:
    def _valid_kwargs(self):
        return {
            "person_id": uuid4(),
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=5),
            "absence_type": "vacation",
        }

    def test_valid_minimal(self):
        r = AbsenceBase(**self._valid_kwargs())
        assert r.deployment_orders is False
        assert r.tdy_location is None
        assert r.replacement_activity is None
        assert r.notes is None

    def test_with_optional_fields(self):
        kw = self._valid_kwargs()
        kw["absence_type"] = "tdy"
        kw["deployment_orders"] = True
        kw["tdy_location"] = "Fort Liberty"
        kw["replacement_activity"] = "Training exercise"
        kw["notes"] = "Annual training"
        r = AbsenceBase(**kw)
        assert r.tdy_location == "Fort Liberty"

    # --- absence_type field_validator ---

    def test_all_valid_absence_types(self):
        for at in VALID_ABSENCE_TYPES:
            kw = self._valid_kwargs()
            kw["absence_type"] = at
            r = AbsenceBase(**kw)
            assert r.absence_type == at

    def test_invalid_absence_type(self):
        kw = self._valid_kwargs()
        kw["absence_type"] = "sabbatical"
        with pytest.raises(ValidationError):
            AbsenceBase(**kw)

    # --- model_validator: end_date >= start_date ---

    def test_end_date_equals_start_date(self):
        kw = self._valid_kwargs()
        kw["end_date"] = kw["start_date"]
        r = AbsenceBase(**kw)
        assert r.start_date == r.end_date

    def test_end_date_before_start_date(self):
        kw = self._valid_kwargs()
        kw["end_date"] = kw["start_date"] - timedelta(days=1)
        with pytest.raises(ValidationError):
            AbsenceBase(**kw)

    # --- tdy_location max_length=200 ---

    def test_tdy_location_too_long(self):
        kw = self._valid_kwargs()
        kw["tdy_location"] = "x" * 201
        with pytest.raises(ValidationError):
            AbsenceBase(**kw)

    # --- replacement_activity max_length=200 ---

    def test_replacement_activity_too_long(self):
        kw = self._valid_kwargs()
        kw["replacement_activity"] = "x" * 201
        with pytest.raises(ValidationError):
            AbsenceBase(**kw)

    # --- notes max_length=1000 (Field) ---

    def test_notes_field_max_length(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 1001
        with pytest.raises(ValidationError):
            AbsenceBase(**kw)

    # --- notes field_validator (>2000 chars) ---

    def test_notes_validator_too_long(self):
        """The field_validator checks >2000 chars, Field checks >1000."""
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 1000
        r = AbsenceBase(**kw)
        assert len(r.notes) == 1000

    # --- date field_validator: validate_academic_year_date (5-year range) ---

    def test_start_date_far_past(self):
        kw = self._valid_kwargs()
        kw["start_date"] = date.today() - timedelta(days=365 * 6)
        kw["end_date"] = date.today() - timedelta(days=365 * 6 - 5)
        with pytest.raises((ValidationError, AppValidationError)):
            AbsenceBase(**kw)

    def test_start_date_far_future(self):
        kw = self._valid_kwargs()
        kw["start_date"] = date.today() + timedelta(days=365 * 6)
        kw["end_date"] = date.today() + timedelta(days=365 * 6 + 5)
        with pytest.raises((ValidationError, AppValidationError)):
            AbsenceBase(**kw)


# ===========================================================================
# AbsenceCreate Tests
# ===========================================================================


class TestAbsenceCreate:
    def _valid_kwargs(self):
        return {
            "person_id": uuid4(),
            "start_date": date.today(),
            "end_date": date.today() + timedelta(days=3),
            "absence_type": "vacation",
        }

    def test_defaults(self):
        r = AbsenceCreate(**self._valid_kwargs())
        assert r.is_blocking is None
        assert r.return_date_tentative is False
        assert r.created_by_id is None
        assert r.is_away_from_program is True

    def test_with_optional_fields(self):
        kw = self._valid_kwargs()
        kw["is_blocking"] = True
        kw["return_date_tentative"] = True
        kw["created_by_id"] = uuid4()
        kw["is_away_from_program"] = False
        r = AbsenceCreate(**kw)
        assert r.is_blocking is True
        assert r.is_away_from_program is False


# ===========================================================================
# AbsenceUpdate Tests
# ===========================================================================


class TestAbsenceUpdate:
    def test_all_none(self):
        r = AbsenceUpdate()
        assert r.start_date is None
        assert r.end_date is None
        assert r.absence_type is None
        assert r.is_blocking is None
        assert r.return_date_tentative is None
        assert r.is_away_from_program is None
        assert r.deployment_orders is None
        assert r.tdy_location is None
        assert r.replacement_activity is None
        assert r.notes is None

    def test_absence_type_valid(self):
        r = AbsenceUpdate(absence_type="deployment")
        assert r.absence_type == "deployment"

    def test_absence_type_none_allowed(self):
        r = AbsenceUpdate(absence_type=None)
        assert r.absence_type is None

    def test_absence_type_invalid(self):
        with pytest.raises(ValidationError):
            AbsenceUpdate(absence_type="sabbatical")

    # --- tdy_location max_length=200 ---

    def test_tdy_location_too_long(self):
        with pytest.raises(ValidationError):
            AbsenceUpdate(tdy_location="x" * 201)

    # --- replacement_activity max_length=200 ---

    def test_replacement_activity_too_long(self):
        with pytest.raises(ValidationError):
            AbsenceUpdate(replacement_activity="x" * 201)

    # --- notes max_length=1000 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            AbsenceUpdate(notes="x" * 1001)


# ===========================================================================
# AbsenceListResponse Tests
# ===========================================================================


class TestAbsenceListResponse:
    def test_valid(self):
        r = AbsenceListResponse(items=[], total=0)
        assert r.page is None
        assert r.page_size is None


# ===========================================================================
# AbsenceBulkCreate Tests
# ===========================================================================


class TestAbsenceBulkCreate:
    def _make_absence(self):
        return AbsenceCreate(
            person_id=uuid4(),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=3),
            absence_type="vacation",
        )

    def test_valid(self):
        r = AbsenceBulkCreate(absences=[self._make_absence()])
        assert len(r.absences) == 1

    # --- absences min_length=1 ---

    def test_empty_list(self):
        with pytest.raises(ValidationError):
            AbsenceBulkCreate(absences=[])


# ===========================================================================
# AbsenceValidationError Tests
# ===========================================================================


class TestAbsenceValidationError:
    def test_valid(self):
        r = AbsenceValError(index=0, message="Invalid date")
        assert r.field is None
        assert r.absence_data is None

    def test_with_optional_fields(self):
        r = AbsenceValError(
            index=2,
            field="start_date",
            message="Date out of range",
            absence_data={"start_date": "2026-03-01"},
        )
        assert r.field == "start_date"


# ===========================================================================
# AbsenceBulkPreview Tests
# ===========================================================================


class TestAbsenceBulkPreview:
    def test_defaults(self):
        r = AbsenceBulkPreview()
        assert r.valid == []
        assert r.errors == []
        assert r.summary == {}


# ===========================================================================
# AbsenceBulkApply Tests
# ===========================================================================


class TestAbsenceBulkApply:
    def test_defaults(self):
        r = AbsenceBulkApply()
        assert r.created == 0
        assert r.skipped == 0
        assert r.errors == []


# ===========================================================================
# AwayAbsenceDetail Tests
# ===========================================================================


class TestAwayAbsenceDetail:
    def test_valid(self):
        r = AwayAbsenceDetail(
            id="abs-1",
            start_date="2026-03-01",
            end_date="2026-03-05",
            absence_type="vacation",
            days=5,
        )
        assert r.days == 5


# ===========================================================================
# AwayFromProgramSummary Tests
# ===========================================================================


class TestAwayFromProgramSummary:
    def test_valid(self):
        r = AwayFromProgramSummary(
            person_id="R001",
            academic_year="2025-2026",
            days_used=14,
            days_remaining=14,
            threshold_status=ThresholdStatus.OK,
        )
        assert r.max_days == 28
        assert r.warning_days == 21
        assert r.absences == []


# ===========================================================================
# AwayFromProgramCheck Tests
# ===========================================================================


class TestAwayFromProgramCheck:
    def test_valid(self):
        r = AwayFromProgramCheck(
            current_days=10,
            projected_days=15,
            threshold_status=ThresholdStatus.WARNING,
            days_remaining=13,
        )
        assert r.max_days == 28
        assert r.warning_days == 21


# ===========================================================================
# AllResidentsAwayStatus Tests
# ===========================================================================


class TestAllResidentsAwayStatus:
    def test_valid(self):
        r = AllResidentsAwayStatus(
            academic_year="2025-2026",
            residents=[],
        )
        assert r.summary == {}
