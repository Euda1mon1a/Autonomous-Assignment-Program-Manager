"""Tests for cascade override schemas (Field bounds, defaults, Literal types)."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.cascade_override import (
    CascadeOverrideRequest,
    CascadeOverrideStep,
    CascadeOverridePlanResponse,
)


class TestCascadeOverrideRequest:
    def _valid_kwargs(self):
        return {
            "person_id": uuid4(),
            "start_date": date(2026, 3, 1),
            "end_date": date(2026, 3, 14),
        }

    def test_defaults(self):
        r = CascadeOverrideRequest(**self._valid_kwargs())
        assert r.reason is None
        assert r.notes is None
        assert r.apply is False
        assert r.max_depth == 2

    # --- max_depth ge=1, le=2 ---

    def test_max_depth_boundaries(self):
        kw = self._valid_kwargs()
        r = CascadeOverrideRequest(**kw, max_depth=1)
        assert r.max_depth == 1
        r = CascadeOverrideRequest(**kw, max_depth=2)
        assert r.max_depth == 2

    def test_max_depth_below_min(self):
        kw = self._valid_kwargs()
        with pytest.raises(ValidationError):
            CascadeOverrideRequest(**kw, max_depth=0)

    def test_max_depth_above_max(self):
        kw = self._valid_kwargs()
        with pytest.raises(ValidationError):
            CascadeOverrideRequest(**kw, max_depth=3)

    def test_with_optional_fields(self):
        kw = self._valid_kwargs()
        r = CascadeOverrideRequest(
            **kw, reason="deployment", notes="Emergency coverage", apply=True
        )
        assert r.reason == "deployment"
        assert r.apply is True


class TestCascadeOverrideStep:
    def test_valid_coverage(self):
        r = CascadeOverrideStep(
            target_type="half_day",
            assignment_id=uuid4(),
            override_type="coverage",
        )
        assert r.replacement_person_id is None
        assert r.reason is None
        assert r.notes is None
        assert r.score is None
        assert r.warnings == []
        assert r.created_override_id is None

    def test_valid_cancellation(self):
        r = CascadeOverrideStep(
            target_type="call",
            assignment_id=uuid4(),
            override_type="cancellation",
            replacement_person_id=uuid4(),
            score=0.85,
            warnings=["Coverage gap possible"],
        )
        assert r.override_type == "cancellation"
        assert r.score == 0.85
        assert len(r.warnings) == 1

    def test_valid_gap(self):
        r = CascadeOverrideStep(
            target_type="half_day",
            assignment_id=uuid4(),
            override_type="gap",
        )
        assert r.override_type == "gap"


class TestCascadeOverridePlanResponse:
    def test_valid(self):
        r = CascadeOverridePlanResponse(
            person_id=uuid4(),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
            applied=False,
            steps=[],
        )
        assert r.applied is False
        assert r.steps == []
        assert r.warnings == []
        assert r.errors == []

    def test_with_steps_and_warnings(self):
        step = CascadeOverrideStep(
            target_type="call",
            assignment_id=uuid4(),
            override_type="coverage",
            replacement_person_id=uuid4(),
        )
        r = CascadeOverridePlanResponse(
            person_id=uuid4(),
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 14),
            applied=True,
            steps=[step],
            warnings=["Short notice"],
            errors=[],
        )
        assert len(r.steps) == 1
        assert r.applied is True
