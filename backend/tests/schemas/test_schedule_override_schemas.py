"""Tests for schedule override schemas (model_validator, Literal types, defaults)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.schedule_override import (
    ScheduleOverrideCreate,
    ScheduleOverrideResponse,
    ScheduleOverrideListResponse,
)


class TestScheduleOverrideCreate:
    def test_valid_coverage(self):
        r = ScheduleOverrideCreate(
            half_day_assignment_id=uuid4(),
            override_type="coverage",
            replacement_person_id=uuid4(),
        )
        assert r.override_type == "coverage"
        assert r.reason is None
        assert r.notes is None
        assert r.supersedes_override_id is None

    def test_valid_cancellation(self):
        r = ScheduleOverrideCreate(
            half_day_assignment_id=uuid4(),
            override_type="cancellation",
        )
        assert r.override_type == "cancellation"
        assert r.replacement_person_id is None

    def test_valid_gap(self):
        r = ScheduleOverrideCreate(
            half_day_assignment_id=uuid4(),
            override_type="gap",
        )
        assert r.override_type == "gap"

    def test_default_override_type(self):
        r = ScheduleOverrideCreate(
            half_day_assignment_id=uuid4(),
            replacement_person_id=uuid4(),
        )
        assert r.override_type == "coverage"

    # --- model_validator: coverage requires replacement ---

    def test_coverage_without_replacement(self):
        with pytest.raises(
            ValidationError,
            match="replacement_person_id is required for coverage overrides",
        ):
            ScheduleOverrideCreate(
                half_day_assignment_id=uuid4(),
                override_type="coverage",
                replacement_person_id=None,
            )

    # --- model_validator: cancellation/gap must not have replacement ---

    def test_cancellation_with_replacement(self):
        with pytest.raises(
            ValidationError,
            match="replacement_person_id must be null for cancellation/gap overrides",
        ):
            ScheduleOverrideCreate(
                half_day_assignment_id=uuid4(),
                override_type="cancellation",
                replacement_person_id=uuid4(),
            )

    def test_gap_with_replacement(self):
        with pytest.raises(
            ValidationError,
            match="replacement_person_id must be null for cancellation/gap overrides",
        ):
            ScheduleOverrideCreate(
                half_day_assignment_id=uuid4(),
                override_type="gap",
                replacement_person_id=uuid4(),
            )

    def test_with_optional_fields(self):
        r = ScheduleOverrideCreate(
            half_day_assignment_id=uuid4(),
            override_type="coverage",
            replacement_person_id=uuid4(),
            reason="deployment",
            notes="Emergency coverage",
            supersedes_override_id=uuid4(),
        )
        assert r.reason == "deployment"
        assert r.notes is not None
        assert r.supersedes_override_id is not None


class TestScheduleOverrideResponse:
    def _valid_kwargs(self):
        return {
            "id": uuid4(),
            "half_day_assignment_id": uuid4(),
            "override_type": "coverage",
            "effective_date": date(2026, 3, 1),
            "time_of_day": "AM",
            "is_active": True,
            "created_at": datetime(2026, 1, 1),
        }

    def test_valid_minimal(self):
        r = ScheduleOverrideResponse(**self._valid_kwargs())
        assert r.original_person_id is None
        assert r.replacement_person_id is None
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
            replacement_person_id=uuid4(),
            reason="sick",
            notes="Short notice",
            created_by_id=uuid4(),
        )
        r = ScheduleOverrideResponse(**kw)
        assert r.reason == "sick"


class TestScheduleOverrideListResponse:
    def test_valid(self):
        r = ScheduleOverrideListResponse(overrides=[], total=0)
        assert r.overrides == []
        assert r.block_number is None
        assert r.academic_year is None
        assert r.start_date is None
        assert r.end_date is None
