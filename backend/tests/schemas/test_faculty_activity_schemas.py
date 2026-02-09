"""Tests for faculty activity schemas (Literal types, Field bounds, defaults, nested)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.faculty_activity import (
    FacultyTemplateSlotBase,
    FacultyTemplateSlotCreate,
    FacultyTemplateUpdateRequest,
    FacultyTemplateResponse,
    FacultyOverrideBase,
    FacultyOverrideCreate,
    FacultyOverridesListResponse,
    EffectiveSlot,
    EffectiveWeekResponse,
    PermittedActivitiesResponse,
    FacultyWeekSlots,
    FacultyMatrixRow,
    FacultyMatrixResponse,
    FacultyMissingWeeklyTemplateItem,
    FacultyWeeklyTemplateCoverageResponse,
)


class TestFacultyTemplateSlotBase:
    def test_valid_minimal(self):
        r = FacultyTemplateSlotBase(day_of_week=0, time_of_day="AM")
        assert r.week_number is None
        assert r.activity_id is None
        assert r.is_locked is False
        assert r.priority == 50
        assert r.notes is None

    def test_full(self):
        r = FacultyTemplateSlotBase(
            day_of_week=5,
            time_of_day="PM",
            week_number=3,
            activity_id=uuid4(),
            is_locked=True,
            priority=90,
            notes="Special coverage",
        )
        assert r.day_of_week == 5
        assert r.time_of_day == "PM"
        assert r.week_number == 3
        assert r.is_locked is True

    # --- day_of_week ge=0, le=6 ---

    def test_day_of_week_below_min(self):
        with pytest.raises(ValidationError):
            FacultyTemplateSlotBase(day_of_week=-1, time_of_day="AM")

    def test_day_of_week_above_max(self):
        with pytest.raises(ValidationError):
            FacultyTemplateSlotBase(day_of_week=7, time_of_day="AM")

    # --- time_of_day Literal["AM", "PM"] ---

    def test_invalid_time_of_day(self):
        with pytest.raises(ValidationError):
            FacultyTemplateSlotBase(day_of_week=0, time_of_day="EVENING")

    # --- week_number ge=1, le=4 ---

    def test_week_number_below_min(self):
        with pytest.raises(ValidationError):
            FacultyTemplateSlotBase(day_of_week=0, time_of_day="AM", week_number=0)

    def test_week_number_above_max(self):
        with pytest.raises(ValidationError):
            FacultyTemplateSlotBase(day_of_week=0, time_of_day="AM", week_number=5)

    # --- priority ge=0, le=100 ---

    def test_priority_below_min(self):
        with pytest.raises(ValidationError):
            FacultyTemplateSlotBase(day_of_week=0, time_of_day="AM", priority=-1)

    def test_priority_above_max(self):
        with pytest.raises(ValidationError):
            FacultyTemplateSlotBase(day_of_week=0, time_of_day="AM", priority=101)

    def test_priority_boundaries(self):
        r = FacultyTemplateSlotBase(day_of_week=0, time_of_day="AM", priority=0)
        assert r.priority == 0
        r = FacultyTemplateSlotBase(day_of_week=0, time_of_day="AM", priority=100)
        assert r.priority == 100


class TestFacultyTemplateSlotCreate:
    def test_inherits_base(self):
        r = FacultyTemplateSlotCreate(day_of_week=1, time_of_day="PM")
        assert r.is_locked is False


class TestFacultyTemplateUpdateRequest:
    def test_valid(self):
        slot = FacultyTemplateSlotCreate(day_of_week=0, time_of_day="AM")
        r = FacultyTemplateUpdateRequest(slots=[slot])
        assert r.clear_existing is False

    def test_clear_existing(self):
        slot = FacultyTemplateSlotCreate(day_of_week=0, time_of_day="AM")
        r = FacultyTemplateUpdateRequest(slots=[slot], clear_existing=True)
        assert r.clear_existing is True


class TestFacultyTemplateResponse:
    def test_valid(self):
        r = FacultyTemplateResponse(
            person_id=uuid4(),
            person_name="Dr. Smith",
            faculty_role="core",
            slots=[],
            total_slots=0,
        )
        assert r.total_slots == 0


class TestFacultyOverrideBase:
    def test_valid_minimal(self):
        r = FacultyOverrideBase(
            effective_date=date(2026, 3, 2),
            day_of_week=1,
            time_of_day="AM",
        )
        assert r.activity_id is None
        assert r.is_locked is False
        assert r.override_reason is None

    # --- day_of_week ge=0, le=6 ---

    def test_day_of_week_below_min(self):
        with pytest.raises(ValidationError):
            FacultyOverrideBase(
                effective_date=date(2026, 3, 2),
                day_of_week=-1,
                time_of_day="AM",
            )


class TestFacultyOverrideCreate:
    def test_inherits_base(self):
        r = FacultyOverrideCreate(
            effective_date=date(2026, 3, 2),
            day_of_week=3,
            time_of_day="PM",
            override_reason="Coverage swap",
        )
        assert r.override_reason == "Coverage swap"


class TestFacultyOverridesListResponse:
    def test_valid(self):
        r = FacultyOverridesListResponse(
            person_id=uuid4(),
            week_start=date(2026, 3, 2),
            overrides=[],
            total=0,
        )
        assert r.total == 0


class TestEffectiveSlot:
    def test_defaults(self):
        r = EffectiveSlot(day_of_week=0, time_of_day="AM")
        assert r.activity_id is None
        assert r.activity is None
        assert r.is_locked is False
        assert r.priority == 50
        assert r.source is None
        assert r.notes is None

    def test_source_values(self):
        r = EffectiveSlot(day_of_week=0, time_of_day="AM", source="template")
        assert r.source == "template"
        r = EffectiveSlot(day_of_week=0, time_of_day="AM", source="override")
        assert r.source == "override"

    def test_invalid_source(self):
        with pytest.raises(ValidationError):
            EffectiveSlot(day_of_week=0, time_of_day="AM", source="unknown")


class TestEffectiveWeekResponse:
    def test_valid(self):
        r = EffectiveWeekResponse(
            person_id=uuid4(),
            person_name="Dr. Smith",
            faculty_role="pd",
            week_start=date(2026, 3, 2),
            week_number=1,
            slots=[],
        )
        assert r.week_number == 1


class TestPermittedActivitiesResponse:
    def test_valid(self):
        r = PermittedActivitiesResponse(
            faculty_role="core",
            activities=[],
            default_activities=[],
        )
        assert r.faculty_role == "core"


class TestFacultyWeekSlots:
    def test_valid(self):
        r = FacultyWeekSlots(week_start=date(2026, 3, 2), slots=[])
        assert r.slots == []


class TestFacultyMatrixRow:
    def test_valid(self):
        r = FacultyMatrixRow(
            person_id=uuid4(),
            name="Dr. Smith",
            faculty_role="core",
            weeks=[],
        )
        assert r.weeks == []


class TestFacultyMatrixResponse:
    def test_valid(self):
        r = FacultyMatrixResponse(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            faculty=[],
            total_faculty=0,
        )
        assert r.total_faculty == 0


class TestFacultyMissingWeeklyTemplateItem:
    def test_valid(self):
        r = FacultyMissingWeeklyTemplateItem(
            person_id=uuid4(), name="Dr. Jones", faculty_role=None
        )
        assert r.faculty_role is None


class TestFacultyWeeklyTemplateCoverageResponse:
    def test_valid(self):
        r = FacultyWeeklyTemplateCoverageResponse(
            total_faculty=20, total_missing=3, missing=[]
        )
        assert r.total_missing == 3
