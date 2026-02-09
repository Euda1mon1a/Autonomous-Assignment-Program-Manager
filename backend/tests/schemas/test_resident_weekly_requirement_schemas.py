"""Tests for resident weekly requirement schemas (field_validators, model_validator, bounds)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.resident_weekly_requirement import (
    ResidentWeeklyRequirementBase,
    ResidentWeeklyRequirementCreate,
    ResidentWeeklyRequirementUpdate,
    ResidentWeeklyRequirementResponse,
    ResidentWeeklyRequirementListResponse,
    ResidentWeeklyRequirementWithTemplate,
)


class TestResidentWeeklyRequirementBase:
    def test_defaults(self):
        r = ResidentWeeklyRequirementBase()
        assert r.fm_clinic_min_per_week == 2
        assert r.fm_clinic_max_per_week == 3
        assert r.specialty_min_per_week == 0
        assert r.specialty_max_per_week == 10
        assert r.academics_required is True
        assert r.protected_slots == {}
        assert r.allowed_clinic_days == []
        assert r.specialty_name is None
        assert r.description is None

    # --- fm_clinic_min_per_week ge=0, le=10 ---

    def test_fm_clinic_min_below_min(self):
        with pytest.raises(ValidationError):
            ResidentWeeklyRequirementBase(fm_clinic_min_per_week=-1)

    def test_fm_clinic_min_above_max(self):
        with pytest.raises(ValidationError):
            ResidentWeeklyRequirementBase(fm_clinic_min_per_week=11)

    # --- fm_clinic_max_per_week ge=0, le=10 ---

    def test_fm_clinic_max_below_min(self):
        with pytest.raises(ValidationError):
            ResidentWeeklyRequirementBase(fm_clinic_max_per_week=-1)

    # --- model_validator: min <= max ---

    def test_fm_clinic_min_exceeds_max(self):
        with pytest.raises(
            ValidationError, match="fm_clinic_min_per_week.*cannot exceed"
        ):
            ResidentWeeklyRequirementBase(
                fm_clinic_min_per_week=5, fm_clinic_max_per_week=3
            )

    def test_specialty_min_exceeds_max(self):
        with pytest.raises(
            ValidationError, match="specialty_min_per_week.*cannot exceed"
        ):
            ResidentWeeklyRequirementBase(
                specialty_min_per_week=8, specialty_max_per_week=5
            )

    # --- protected_slots field_validator ---

    def test_valid_protected_slots(self):
        r = ResidentWeeklyRequirementBase(
            protected_slots={"wed_am": "conference", "fri_pm": "didactics"}
        )
        assert len(r.protected_slots) == 2

    def test_invalid_slot_key_format(self):
        with pytest.raises(ValidationError, match="Invalid slot key"):
            ResidentWeeklyRequirementBase(protected_slots={"invalid": "test"})

    def test_invalid_slot_day(self):
        with pytest.raises(ValidationError, match="Invalid day"):
            ResidentWeeklyRequirementBase(protected_slots={"sat_am": "test"})

    def test_invalid_slot_time(self):
        with pytest.raises(ValidationError, match="Invalid time"):
            ResidentWeeklyRequirementBase(protected_slots={"mon_evening": "test"})

    # --- allowed_clinic_days field_validator ---

    def test_valid_clinic_days(self):
        r = ResidentWeeklyRequirementBase(allowed_clinic_days=[0, 1, 4])
        assert r.allowed_clinic_days == [0, 1, 4]

    def test_clinic_days_sorted_and_deduped(self):
        r = ResidentWeeklyRequirementBase(allowed_clinic_days=[4, 1, 1, 0])
        assert r.allowed_clinic_days == [0, 1, 4]

    def test_invalid_clinic_day_negative(self):
        with pytest.raises(ValidationError, match="Invalid day"):
            ResidentWeeklyRequirementBase(allowed_clinic_days=[-1])

    def test_invalid_clinic_day_too_high(self):
        with pytest.raises(ValidationError, match="Invalid day"):
            ResidentWeeklyRequirementBase(allowed_clinic_days=[5])

    # --- specialty_name max_length=255 ---

    def test_specialty_name_too_long(self):
        with pytest.raises(ValidationError):
            ResidentWeeklyRequirementBase(specialty_name="x" * 256)

    # --- description max_length=1024 ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            ResidentWeeklyRequirementBase(description="x" * 1025)


class TestResidentWeeklyRequirementCreate:
    def test_valid(self):
        r = ResidentWeeklyRequirementCreate(rotation_template_id=uuid4())
        assert r.fm_clinic_min_per_week == 2

    def test_with_overrides(self):
        r = ResidentWeeklyRequirementCreate(
            rotation_template_id=uuid4(),
            fm_clinic_min_per_week=1,
            fm_clinic_max_per_week=4,
            academics_required=False,
        )
        assert r.fm_clinic_min_per_week == 1
        assert r.academics_required is False


class TestResidentWeeklyRequirementUpdate:
    def test_all_none(self):
        r = ResidentWeeklyRequirementUpdate()
        assert r.fm_clinic_min_per_week is None
        assert r.fm_clinic_max_per_week is None
        assert r.specialty_min_per_week is None
        assert r.specialty_max_per_week is None
        assert r.academics_required is None
        assert r.protected_slots is None
        assert r.allowed_clinic_days is None
        assert r.specialty_name is None
        assert r.description is None

    def test_partial_update(self):
        r = ResidentWeeklyRequirementUpdate(fm_clinic_min_per_week=3)
        assert r.fm_clinic_min_per_week == 3

    # --- Field bounds still apply ---

    def test_bounds_on_update(self):
        with pytest.raises(ValidationError):
            ResidentWeeklyRequirementUpdate(fm_clinic_min_per_week=11)

    # --- protected_slots None-aware ---

    def test_protected_slots_none(self):
        r = ResidentWeeklyRequirementUpdate(protected_slots=None)
        assert r.protected_slots is None

    def test_protected_slots_invalid(self):
        with pytest.raises(ValidationError, match="Invalid slot key"):
            ResidentWeeklyRequirementUpdate(protected_slots={"bad": "val"})

    # --- allowed_clinic_days None-aware ---

    def test_allowed_days_none(self):
        r = ResidentWeeklyRequirementUpdate(allowed_clinic_days=None)
        assert r.allowed_clinic_days is None

    def test_allowed_days_invalid(self):
        with pytest.raises(ValidationError, match="Invalid day"):
            ResidentWeeklyRequirementUpdate(allowed_clinic_days=[5])


class TestResidentWeeklyRequirementResponse:
    def test_valid(self):
        r = ResidentWeeklyRequirementResponse(
            id=uuid4(),
            rotation_template_id=uuid4(),
            created_at=datetime(2026, 3, 1),
            updated_at=datetime(2026, 3, 1),
            total_min_halfdays=2,
            total_max_halfdays=13,
            is_valid_range=True,
        )
        assert r.total_min_halfdays == 2
        assert r.is_valid_range is True


class TestResidentWeeklyRequirementListResponse:
    def test_valid(self):
        r = ResidentWeeklyRequirementListResponse(items=[], total=0)
        assert r.items == []


class TestResidentWeeklyRequirementWithTemplate:
    def test_valid(self):
        r = ResidentWeeklyRequirementWithTemplate(
            id=uuid4(),
            rotation_template_id=uuid4(),
            created_at=datetime(2026, 3, 1),
            updated_at=datetime(2026, 3, 1),
            total_min_halfdays=2,
            total_max_halfdays=13,
            is_valid_range=True,
            template_name="FM Clinic",
            template_rotation_type="outpatient",
        )
        assert r.template_name == "FM Clinic"
