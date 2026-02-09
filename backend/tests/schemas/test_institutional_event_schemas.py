"""Tests for institutional event schemas (model_validator, Field bounds, enums)."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.institutional_event import (
    InstitutionalEventScope,
    InstitutionalEventType,
)
from app.schemas.institutional_event import (
    InstitutionalEventBase,
    InstitutionalEventCreate,
    InstitutionalEventUpdate,
    InstitutionalEventResponse,
    InstitutionalEventListResponse,
)


class TestInstitutionalEventBase:
    def _valid_kwargs(self):
        return {
            "name": "Training Day",
            "event_type": InstitutionalEventType.TRAINING,
            "start_date": date(2026, 6, 1),
            "end_date": date(2026, 6, 1),
            "activity_id": uuid4(),
        }

    def test_valid_minimal(self):
        r = InstitutionalEventBase(**self._valid_kwargs())
        assert r.time_of_day is None
        assert r.applies_to == InstitutionalEventScope.ALL
        assert r.applies_to_inpatient is False
        assert r.notes is None
        assert r.is_active is True

    def test_full(self):
        kw = self._valid_kwargs()
        kw.update(
            time_of_day="AM",
            applies_to=InstitutionalEventScope.RESIDENT,
            applies_to_inpatient=True,
            notes="Annual training",
            is_active=False,
        )
        r = InstitutionalEventBase(**kw)
        assert r.time_of_day == "AM"
        assert r.applies_to == InstitutionalEventScope.RESIDENT
        assert r.is_active is False

    # --- name min_length=2, max_length=255 ---

    def test_name_too_short(self):
        kw = self._valid_kwargs()
        kw["name"] = "X"
        with pytest.raises(ValidationError):
            InstitutionalEventBase(**kw)

    def test_name_too_long(self):
        kw = self._valid_kwargs()
        kw["name"] = "x" * 256
        with pytest.raises(ValidationError):
            InstitutionalEventBase(**kw)

    def test_name_min_length(self):
        kw = self._valid_kwargs()
        kw["name"] = "OK"
        r = InstitutionalEventBase(**kw)
        assert r.name == "OK"

    # --- notes max_length=2000 ---

    def test_notes_too_long(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 2001
        with pytest.raises(ValidationError):
            InstitutionalEventBase(**kw)

    def test_notes_max_length(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 2000
        r = InstitutionalEventBase(**kw)
        assert len(r.notes) == 2000

    # --- model_validator: end_date >= start_date ---

    def test_end_before_start(self):
        kw = self._valid_kwargs()
        kw["start_date"] = date(2026, 6, 10)
        kw["end_date"] = date(2026, 6, 1)
        with pytest.raises(
            ValidationError, match="end_date must be on or after start_date"
        ):
            InstitutionalEventBase(**kw)

    def test_same_start_end(self):
        kw = self._valid_kwargs()
        kw["start_date"] = date(2026, 6, 1)
        kw["end_date"] = date(2026, 6, 1)
        r = InstitutionalEventBase(**kw)
        assert r.start_date == r.end_date

    # --- event_type enum ---

    def test_all_event_types(self):
        for et in InstitutionalEventType:
            kw = self._valid_kwargs()
            kw["event_type"] = et
            r = InstitutionalEventBase(**kw)
            assert r.event_type == et

    # --- time_of_day Literal["AM", "PM"] ---

    def test_time_of_day_pm(self):
        kw = self._valid_kwargs()
        kw["time_of_day"] = "PM"
        r = InstitutionalEventBase(**kw)
        assert r.time_of_day == "PM"


class TestInstitutionalEventCreate:
    def test_inherits_base(self):
        r = InstitutionalEventCreate(
            name="Holiday",
            event_type=InstitutionalEventType.HOLIDAY,
            start_date=date(2026, 12, 25),
            end_date=date(2026, 12, 25),
            activity_id=uuid4(),
        )
        assert r.name == "Holiday"


class TestInstitutionalEventUpdate:
    def test_all_none(self):
        r = InstitutionalEventUpdate()
        assert r.name is None
        assert r.event_type is None
        assert r.start_date is None
        assert r.end_date is None
        assert r.time_of_day is None
        assert r.applies_to is None
        assert r.applies_to_inpatient is None
        assert r.activity_id is None
        assert r.notes is None
        assert r.is_active is None

    # --- name min_length=2, max_length=255 ---

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            InstitutionalEventUpdate(name="X")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            InstitutionalEventUpdate(name="x" * 256)

    # --- notes max_length=2000 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            InstitutionalEventUpdate(notes="x" * 2001)

    # --- model_validator: end_date >= start_date ---

    def test_end_before_start(self):
        with pytest.raises(
            ValidationError, match="end_date must be on or after start_date"
        ):
            InstitutionalEventUpdate(
                start_date=date(2026, 6, 10),
                end_date=date(2026, 6, 1),
            )

    def test_only_start_date_ok(self):
        r = InstitutionalEventUpdate(start_date=date(2026, 6, 10))
        assert r.start_date == date(2026, 6, 10)

    def test_only_end_date_ok(self):
        r = InstitutionalEventUpdate(end_date=date(2026, 6, 10))
        assert r.end_date == date(2026, 6, 10)


class TestInstitutionalEventResponse:
    def test_valid(self):
        r = InstitutionalEventResponse(
            id=uuid4(),
            name="Conference",
            event_type=InstitutionalEventType.CONFERENCE,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 3),
            activity_id=uuid4(),
        )
        assert r.id is not None


class TestInstitutionalEventListResponse:
    def test_valid(self):
        r = InstitutionalEventListResponse(items=[], total=0, page=1, page_size=10)
        assert r.items == []
        assert r.total == 0
