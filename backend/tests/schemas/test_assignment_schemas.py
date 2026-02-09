"""Tests for assignment schemas (enums, field_validators, defaults, CRUD)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.assignment import (
    AssignmentRole,
    AssignmentBase,
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentWithWarnings,
    AssignmentListResponse,
    AssignmentWithExplanation,
)


class TestAssignmentRole:
    def test_values(self):
        assert AssignmentRole.PRIMARY.value == "primary"
        assert AssignmentRole.SUPERVISING.value == "supervising"
        assert AssignmentRole.BACKUP.value == "backup"

    def test_count(self):
        assert len(AssignmentRole) == 3

    def test_is_str(self):
        assert isinstance(AssignmentRole.PRIMARY, str)


class TestAssignmentBase:
    def _valid_kwargs(self):
        return {
            "block_id": uuid4(),
            "person_id": uuid4(),
            "role": AssignmentRole.PRIMARY,
        }

    def test_valid_minimal(self):
        r = AssignmentBase(**self._valid_kwargs())
        assert r.rotation_template_id is None
        assert r.activity_override is None
        assert r.notes is None
        assert r.override_reason is None

    def test_full(self):
        kw = self._valid_kwargs()
        kw["rotation_template_id"] = uuid4()
        kw["activity_override"] = "ICU Coverage"
        kw["notes"] = "Special assignment"
        kw["override_reason"] = "Approved by PD"
        r = AssignmentBase(**kw)
        assert r.activity_override == "ICU Coverage"

    # --- activity_override max_length=200 ---

    def test_activity_override_too_long(self):
        kw = self._valid_kwargs()
        kw["activity_override"] = "x" * 201
        with pytest.raises(ValidationError):
            AssignmentBase(**kw)

    # --- notes max_length=1000 ---

    def test_notes_too_long(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 1001
        with pytest.raises(ValidationError):
            AssignmentBase(**kw)

    # --- override_reason max_length=500 ---

    def test_override_reason_too_long(self):
        kw = self._valid_kwargs()
        kw["override_reason"] = "x" * 501
        with pytest.raises(ValidationError):
            AssignmentBase(**kw)


class TestAssignmentCreate:
    def test_valid(self):
        r = AssignmentCreate(
            block_id=uuid4(),
            person_id=uuid4(),
            role=AssignmentRole.PRIMARY,
        )
        assert r.created_by is None

    def test_with_created_by(self):
        r = AssignmentCreate(
            block_id=uuid4(),
            person_id=uuid4(),
            role=AssignmentRole.SUPERVISING,
            created_by="admin",
        )
        assert r.created_by == "admin"

    # --- created_by max_length=100 ---

    def test_created_by_too_long(self):
        with pytest.raises(ValidationError):
            AssignmentCreate(
                block_id=uuid4(),
                person_id=uuid4(),
                role=AssignmentRole.PRIMARY,
                created_by="x" * 101,
            )


class TestAssignmentUpdate:
    def test_valid_minimal(self):
        r = AssignmentUpdate(updated_at=datetime(2026, 3, 1))
        assert r.rotation_template_id is None
        assert r.role is None
        assert r.acknowledge_override is None

    def test_partial(self):
        r = AssignmentUpdate(
            role=AssignmentRole.BACKUP,
            notes="Updated notes",
            updated_at=datetime(2026, 3, 1),
        )
        assert r.role == AssignmentRole.BACKUP

    # --- notes field_validator ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            AssignmentUpdate(
                notes="x" * 1001,
                updated_at=datetime(2026, 3, 1),
            )


class TestAssignmentResponse:
    def _make_response(self, **overrides):
        defaults = {
            "id": uuid4(),
            "block_id": uuid4(),
            "person_id": uuid4(),
            "role": AssignmentRole.PRIMARY,
            "created_at": datetime(2026, 3, 1),
            "updated_at": datetime(2026, 3, 1),
        }
        defaults.update(overrides)
        return AssignmentResponse(**defaults)

    def test_valid(self):
        r = self._make_response()
        assert r.created_by is None
        assert r.override_acknowledged_at is None
        assert r.confidence is None
        assert r.score is None

    def test_with_scores(self):
        r = self._make_response(confidence=0.85, score=950.0)
        assert r.confidence == 0.85
        assert r.score == 950.0


class TestAssignmentWithWarnings:
    def test_defaults(self):
        r = AssignmentWithWarnings(
            id=uuid4(),
            block_id=uuid4(),
            person_id=uuid4(),
            role=AssignmentRole.PRIMARY,
            created_at=datetime(2026, 3, 1),
            updated_at=datetime(2026, 3, 1),
        )
        assert r.acgme_warnings == []
        assert r.is_compliant is True

    def test_with_warnings(self):
        r = AssignmentWithWarnings(
            id=uuid4(),
            block_id=uuid4(),
            person_id=uuid4(),
            role=AssignmentRole.PRIMARY,
            created_at=datetime(2026, 3, 1),
            updated_at=datetime(2026, 3, 1),
            acgme_warnings=["80-hour approaching"],
            is_compliant=False,
        )
        assert len(r.acgme_warnings) == 1
        assert r.is_compliant is False


class TestAssignmentListResponse:
    def test_valid(self):
        r = AssignmentListResponse(items=[], total=0)
        assert r.page is None
        assert r.page_size is None


class TestAssignmentWithExplanation:
    def test_valid_minimal(self):
        r = AssignmentWithExplanation(
            id=uuid4(),
            block_id=uuid4(),
            person_id=uuid4(),
            role=AssignmentRole.PRIMARY,
            created_at=datetime(2026, 3, 1),
            updated_at=datetime(2026, 3, 1),
        )
        assert r.explain_json is None
        assert r.alternatives_json is None
        assert r.audit_hash is None
        assert r.confidence_level is None
        assert r.trade_off_summary is None
