"""Tests for call override schemas (Literal types, defaults, list response)."""

from datetime import date, datetime
from uuid import uuid4

from app.schemas.call_override import (
    CallOverrideCreate,
    CallOverrideResponse,
    CallOverrideListResponse,
)


class TestCallOverrideCreate:
    def test_valid_minimal(self):
        r = CallOverrideCreate(
            call_assignment_id=uuid4(),
            replacement_person_id=uuid4(),
        )
        assert r.override_type == "coverage"
        assert r.reason is None
        assert r.notes is None
        assert r.supersedes_override_id is None

    def test_with_optional_fields(self):
        r = CallOverrideCreate(
            call_assignment_id=uuid4(),
            replacement_person_id=uuid4(),
            reason="deployment",
            notes="Emergency coverage needed",
            supersedes_override_id=uuid4(),
        )
        assert r.reason == "deployment"
        assert r.notes is not None
        assert r.supersedes_override_id is not None


class TestCallOverrideResponse:
    def _valid_kwargs(self):
        return {
            "id": uuid4(),
            "call_assignment_id": uuid4(),
            "replacement_person_id": uuid4(),
            "override_type": "coverage",
            "effective_date": date(2026, 3, 1),
            "call_type": "night_float",
            "is_active": True,
            "created_at": datetime(2026, 1, 1),
        }

    def test_valid_minimal(self):
        r = CallOverrideResponse(**self._valid_kwargs())
        assert r.original_person_id is None
        assert r.reason is None
        assert r.notes is None
        assert r.created_by_id is None
        assert r.deactivated_at is None
        assert r.deactivated_by_id is None
        assert r.supersedes_override_id is None

    def test_full(self):
        kw = self._valid_kwargs()
        kw.update(
            original_person_id=uuid4(),
            reason="sick",
            notes="Short notice",
            created_by_id=uuid4(),
        )
        r = CallOverrideResponse(**kw)
        assert r.reason == "sick"


class TestCallOverrideListResponse:
    def test_valid(self):
        r = CallOverrideListResponse(overrides=[], total=0)
        assert r.overrides == []
        assert r.block_number is None
        assert r.academic_year is None
        assert r.start_date is None
        assert r.end_date is None

    def test_with_metadata(self):
        r = CallOverrideListResponse(
            overrides=[],
            total=0,
            block_number=5,
            academic_year=2026,
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 28),
        )
        assert r.block_number == 5
