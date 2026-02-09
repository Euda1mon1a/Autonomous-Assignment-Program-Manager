"""Tests for half-day assignment schemas (defaults, list response)."""

from datetime import date, datetime
from uuid import uuid4

from app.schemas.half_day_assignment import (
    HalfDayAssignmentRead,
    HalfDayAssignmentListResponse,
)


class TestHalfDayAssignmentRead:
    def _valid_kwargs(self):
        return {
            "id": uuid4(),
            "person_id": uuid4(),
            "date": date(2026, 3, 1),
            "time_of_day": "AM",
            "source": "preload",
            "created_at": datetime(2026, 1, 1),
            "updated_at": datetime(2026, 1, 1),
        }

    def test_valid_minimal(self):
        r = HalfDayAssignmentRead(**self._valid_kwargs())
        assert r.person_name is None
        assert r.person_type is None
        assert r.pgy_level is None
        assert r.activity_id is None
        assert r.activity_code is None
        assert r.activity_name is None
        assert r.display_abbreviation is None
        assert r.is_locked is False
        assert r.is_gap is False

    def test_full(self):
        kw = self._valid_kwargs()
        kw.update(
            person_name="Dr. Smith",
            person_type="resident",
            pgy_level=2,
            activity_id=uuid4(),
            activity_code="fm_clinic",
            activity_name="FM Clinic",
            display_abbreviation="FMC",
            source="solver",
            is_locked=True,
            is_gap=False,
        )
        r = HalfDayAssignmentRead(**kw)
        assert r.person_name == "Dr. Smith"
        assert r.pgy_level == 2
        assert r.is_locked is True

    def test_pm_time_of_day(self):
        kw = self._valid_kwargs()
        kw["time_of_day"] = "PM"
        r = HalfDayAssignmentRead(**kw)
        assert r.time_of_day == "PM"


class TestHalfDayAssignmentListResponse:
    def test_valid(self):
        r = HalfDayAssignmentListResponse(assignments=[], total=0)
        assert r.assignments == []
        assert r.block_number is None
        assert r.academic_year is None
        assert r.start_date is None
        assert r.end_date is None

    def test_with_metadata(self):
        r = HalfDayAssignmentListResponse(
            assignments=[],
            total=0,
            block_number=5,
            academic_year=2026,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 28),
        )
        assert r.block_number == 5
        assert r.academic_year == 2026
