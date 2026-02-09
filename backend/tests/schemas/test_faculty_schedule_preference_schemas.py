"""Tests for faculty schedule preference schemas (Field bounds, model_validator, enums)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.faculty_schedule_preference import (
    FacultyPreferenceDirection,
    FacultyPreferenceType,
)
from app.schemas.faculty_schedule_preference import (
    FacultySchedulePreferenceBase,
    FacultySchedulePreferenceCreate,
    FacultySchedulePreferenceUpdate,
    FacultySchedulePreferenceResponse,
    FacultySchedulePreferenceListResponse,
)


class TestFacultySchedulePreferenceBase:
    def _valid_kwargs(self):
        return {
            "person_id": uuid4(),
            "preference_type": FacultyPreferenceType.CLINIC,
            "direction": FacultyPreferenceDirection.PREFER,
            "rank": 1,
            "day_of_week": 1,
            "time_of_day": "AM",
        }

    def test_valid_minimal(self):
        r = FacultySchedulePreferenceBase(**self._valid_kwargs())
        assert r.weight == 6
        assert r.is_active is True
        assert r.notes is None

    def test_full(self):
        kw = self._valid_kwargs()
        kw.update(weight=50, is_active=False, notes="Prefers Monday AM")
        r = FacultySchedulePreferenceBase(**kw)
        assert r.weight == 50
        assert r.is_active is False
        assert r.notes == "Prefers Monday AM"

    # --- rank ge=1, le=2 ---

    def test_rank_boundaries(self):
        kw = self._valid_kwargs()
        kw["rank"] = 1
        r = FacultySchedulePreferenceBase(**kw)
        assert r.rank == 1
        kw["rank"] = 2
        r = FacultySchedulePreferenceBase(**kw)
        assert r.rank == 2

    def test_rank_below_min(self):
        kw = self._valid_kwargs()
        kw["rank"] = 0
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceBase(**kw)

    def test_rank_above_max(self):
        kw = self._valid_kwargs()
        kw["rank"] = 3
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceBase(**kw)

    # --- day_of_week ge=0, le=6 ---

    def test_day_of_week_boundaries(self):
        kw = self._valid_kwargs()
        kw["day_of_week"] = 0
        r = FacultySchedulePreferenceBase(**kw)
        assert r.day_of_week == 0
        kw["day_of_week"] = 6
        r = FacultySchedulePreferenceBase(**kw)
        assert r.day_of_week == 6

    def test_day_of_week_negative(self):
        kw = self._valid_kwargs()
        kw["day_of_week"] = -1
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceBase(**kw)

    def test_day_of_week_above_max(self):
        kw = self._valid_kwargs()
        kw["day_of_week"] = 7
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceBase(**kw)

    # --- weight ge=1, le=100 ---

    def test_weight_boundaries(self):
        kw = self._valid_kwargs()
        kw["weight"] = 1
        r = FacultySchedulePreferenceBase(**kw)
        assert r.weight == 1
        kw["weight"] = 100
        r = FacultySchedulePreferenceBase(**kw)
        assert r.weight == 100

    def test_weight_below_min(self):
        kw = self._valid_kwargs()
        kw["weight"] = 0
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceBase(**kw)

    def test_weight_above_max(self):
        kw = self._valid_kwargs()
        kw["weight"] = 101
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceBase(**kw)

    # --- notes max_length=500 ---

    def test_notes_too_long(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 501
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceBase(**kw)

    def test_notes_max_length(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 500
        r = FacultySchedulePreferenceBase(**kw)
        assert len(r.notes) == 500

    # --- model_validator: clinic requires time_of_day ---

    def test_clinic_without_time_of_day(self):
        kw = self._valid_kwargs()
        kw["preference_type"] = FacultyPreferenceType.CLINIC
        kw["time_of_day"] = None
        with pytest.raises(
            ValidationError, match="Clinic preferences require time_of_day"
        ):
            FacultySchedulePreferenceBase(**kw)

    # --- model_validator: call must not include time_of_day ---

    def test_call_with_time_of_day(self):
        kw = self._valid_kwargs()
        kw["preference_type"] = FacultyPreferenceType.CALL
        kw["time_of_day"] = "AM"
        with pytest.raises(
            ValidationError, match="Call preferences must not include time_of_day"
        ):
            FacultySchedulePreferenceBase(**kw)

    def test_call_without_time_of_day(self):
        kw = self._valid_kwargs()
        kw["preference_type"] = FacultyPreferenceType.CALL
        kw["time_of_day"] = None
        r = FacultySchedulePreferenceBase(**kw)
        assert r.preference_type == FacultyPreferenceType.CALL
        assert r.time_of_day is None

    # --- direction enum ---

    def test_all_directions(self):
        for d in FacultyPreferenceDirection:
            kw = self._valid_kwargs()
            kw["direction"] = d
            r = FacultySchedulePreferenceBase(**kw)
            assert r.direction == d


class TestFacultySchedulePreferenceCreate:
    def test_inherits_base(self):
        r = FacultySchedulePreferenceCreate(
            person_id=uuid4(),
            preference_type=FacultyPreferenceType.CLINIC,
            direction=FacultyPreferenceDirection.PREFER,
            rank=1,
            day_of_week=3,
            time_of_day="PM",
        )
        assert r.day_of_week == 3


class TestFacultySchedulePreferenceUpdate:
    def test_all_none(self):
        r = FacultySchedulePreferenceUpdate()
        assert r.preference_type is None
        assert r.direction is None
        assert r.rank is None
        assert r.day_of_week is None
        assert r.time_of_day is None
        assert r.weight is None
        assert r.is_active is None
        assert r.notes is None

    # --- rank ge=1, le=2 ---

    def test_rank_below_min(self):
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceUpdate(rank=0)

    def test_rank_above_max(self):
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceUpdate(rank=3)

    # --- day_of_week ge=0, le=6 ---

    def test_day_of_week_negative(self):
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceUpdate(day_of_week=-1)

    def test_day_of_week_above_max(self):
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceUpdate(day_of_week=7)

    # --- weight ge=1, le=100 ---

    def test_weight_below_min(self):
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceUpdate(weight=0)

    def test_weight_above_max(self):
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceUpdate(weight=101)

    # --- notes max_length=500 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            FacultySchedulePreferenceUpdate(notes="x" * 501)

    # --- model_validator: clinic requires time_of_day ---

    def test_clinic_without_time_of_day(self):
        with pytest.raises(
            ValidationError, match="Clinic preferences require time_of_day"
        ):
            FacultySchedulePreferenceUpdate(
                preference_type=FacultyPreferenceType.CLINIC, time_of_day=None
            )

    # --- model_validator: call must not include time_of_day ---

    def test_call_with_time_of_day(self):
        with pytest.raises(
            ValidationError, match="Call preferences must not include time_of_day"
        ):
            FacultySchedulePreferenceUpdate(
                preference_type=FacultyPreferenceType.CALL, time_of_day="PM"
            )


class TestFacultySchedulePreferenceResponse:
    def test_valid(self):
        r = FacultySchedulePreferenceResponse(
            id=uuid4(),
            person_id=uuid4(),
            preference_type=FacultyPreferenceType.CLINIC,
            direction=FacultyPreferenceDirection.AVOID,
            rank=2,
            day_of_week=4,
            time_of_day="PM",
        )
        assert r.id is not None
        assert r.direction == FacultyPreferenceDirection.AVOID


class TestFacultySchedulePreferenceListResponse:
    def test_valid(self):
        r = FacultySchedulePreferenceListResponse(
            items=[], total=0, page=1, page_size=10
        )
        assert r.items == []
        assert r.total == 0
