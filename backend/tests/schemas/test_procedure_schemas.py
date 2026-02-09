"""Tests for procedure schemas (field_validators, defaults, CRUD)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.procedure import (
    ProcedureBase,
    ProcedureCreate,
    ProcedureUpdate,
    ProcedureResponse,
    ProcedureListResponse,
    ProcedureSummary,
)


class TestProcedureBase:
    def test_valid_minimal(self):
        r = ProcedureBase(name="Appendectomy")
        assert r.description is None
        assert r.category is None
        assert r.specialty is None
        assert r.supervision_ratio == 1
        assert r.requires_certification is True
        assert r.complexity_level == "standard"
        assert r.min_pgy_level == 1
        assert r.is_active is True

    # --- name field_validator (strip, not empty) ---

    def test_name_empty(self):
        with pytest.raises(ValidationError, match="name cannot be empty"):
            ProcedureBase(name="")

    def test_name_whitespace_only(self):
        with pytest.raises(ValidationError, match="name cannot be empty"):
            ProcedureBase(name="   ")

    def test_name_strips(self):
        r = ProcedureBase(name="  Appendectomy  ")
        assert r.name == "Appendectomy"

    # --- category field_validator ---

    def test_category_valid(self):
        for cat in ("surgical", "office", "obstetric", "clinic"):
            r = ProcedureBase(name="P", category=cat)
            assert r.category == cat

    def test_category_invalid(self):
        with pytest.raises(ValidationError, match="category must be one of"):
            ProcedureBase(name="P", category="invalid")

    # --- complexity_level field_validator ---

    def test_complexity_valid(self):
        for level in ("basic", "standard", "advanced", "complex"):
            r = ProcedureBase(name="P", complexity_level=level)
            assert r.complexity_level == level

    def test_complexity_invalid(self):
        with pytest.raises(ValidationError, match="complexity_level must be one of"):
            ProcedureBase(name="P", complexity_level="extreme")

    # --- min_pgy_level 1-3 ---

    def test_pgy_level_boundaries(self):
        r = ProcedureBase(name="P", min_pgy_level=1)
        assert r.min_pgy_level == 1
        r = ProcedureBase(name="P", min_pgy_level=3)
        assert r.min_pgy_level == 3

    def test_pgy_level_below_min(self):
        with pytest.raises(ValidationError, match="min_pgy_level must be between"):
            ProcedureBase(name="P", min_pgy_level=0)

    def test_pgy_level_above_max(self):
        with pytest.raises(ValidationError, match="min_pgy_level must be between"):
            ProcedureBase(name="P", min_pgy_level=4)

    # --- supervision_ratio >= 1 ---

    def test_supervision_ratio_valid(self):
        r = ProcedureBase(name="P", supervision_ratio=5)
        assert r.supervision_ratio == 5

    def test_supervision_ratio_zero(self):
        with pytest.raises(
            ValidationError, match="supervision_ratio must be at least 1"
        ):
            ProcedureBase(name="P", supervision_ratio=0)


class TestProcedureCreate:
    def test_inherits_base(self):
        r = ProcedureCreate(name="Appendectomy", category="surgical")
        assert r.category == "surgical"


class TestProcedureUpdate:
    def test_all_none(self):
        r = ProcedureUpdate()
        assert r.name is None
        assert r.description is None
        assert r.category is None
        assert r.specialty is None
        assert r.supervision_ratio is None
        assert r.requires_certification is None
        assert r.complexity_level is None
        assert r.min_pgy_level is None
        assert r.is_active is None

    def test_partial(self):
        r = ProcedureUpdate(name="New Name", category="office")
        assert r.name == "New Name"
        assert r.category == "office"

    # --- name field_validator (None-aware) ---

    def test_name_empty_string(self):
        with pytest.raises(ValidationError, match="name cannot be empty"):
            ProcedureUpdate(name="")

    def test_name_whitespace_only(self):
        with pytest.raises(ValidationError, match="name cannot be empty"):
            ProcedureUpdate(name="   ")

    # --- category field_validator (None-aware) ---

    def test_category_invalid(self):
        with pytest.raises(ValidationError, match="category must be one of"):
            ProcedureUpdate(category="invalid")

    # --- complexity_level field_validator (None-aware) ---

    def test_complexity_invalid(self):
        with pytest.raises(ValidationError, match="complexity_level must be one of"):
            ProcedureUpdate(complexity_level="extreme")

    # --- min_pgy_level field_validator (None-aware) ---

    def test_pgy_level_below_min(self):
        with pytest.raises(ValidationError, match="min_pgy_level must be between"):
            ProcedureUpdate(min_pgy_level=0)

    # --- supervision_ratio field_validator (None-aware) ---

    def test_supervision_ratio_zero(self):
        with pytest.raises(
            ValidationError, match="supervision_ratio must be at least 1"
        ):
            ProcedureUpdate(supervision_ratio=0)


class TestProcedureResponse:
    def test_valid(self):
        r = ProcedureResponse(
            id=uuid4(),
            name="Appendectomy",
            category="surgical",
            complexity_level="advanced",
            min_pgy_level=2,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        assert r.name == "Appendectomy"
        assert r.category == "surgical"


class TestProcedureListResponse:
    def test_valid(self):
        r = ProcedureListResponse(items=[], total=0)
        assert r.items == []
        assert r.total == 0


class TestProcedureSummary:
    def test_valid(self):
        r = ProcedureSummary(id=uuid4(), name="Appendectomy")
        assert r.specialty is None
        assert r.category is None

    def test_full(self):
        r = ProcedureSummary(
            id=uuid4(), name="C-Section", specialty="OB/GYN", category="obstetric"
        )
        assert r.specialty == "OB/GYN"
