"""Tests for half-day import schemas (enums, defaults, Field default_factory)."""

from uuid import uuid4

from app.schemas.half_day_import import (
    HalfDayDiffType,
    HalfDayDiffEntry,
    HalfDayDiffMetrics,
    HalfDayImportStageResponse,
    HalfDayImportPreviewResponse,
    HalfDayImportDraftRequest,
    HalfDayImportDraftResponse,
)

from datetime import date, datetime

import pytest
from pydantic import ValidationError


class TestHalfDayDiffType:
    def test_values(self):
        assert HalfDayDiffType.ADDED.value == "added"
        assert HalfDayDiffType.REMOVED.value == "removed"
        assert HalfDayDiffType.MODIFIED.value == "modified"

    def test_count(self):
        assert len(HalfDayDiffType) == 3

    def test_is_str(self):
        assert isinstance(HalfDayDiffType.ADDED, str)


class TestHalfDayDiffEntry:
    def test_valid_minimal(self):
        r = HalfDayDiffEntry(
            person_name="Dr. Smith",
            assignment_date=date(2026, 3, 1),
            time_of_day="AM",
            diff_type=HalfDayDiffType.ADDED,
        )
        assert r.staged_id is None
        assert r.person_id is None
        assert r.excel_value is None
        assert r.current_value is None
        assert r.warnings == []
        assert r.errors == []

    def test_full(self):
        r = HalfDayDiffEntry(
            staged_id=uuid4(),
            person_id=uuid4(),
            person_name="Dr. Jones",
            assignment_date=date(2026, 3, 1),
            time_of_day="PM",
            diff_type=HalfDayDiffType.MODIFIED,
            excel_value="FM Clinic",
            current_value="ICU",
            warnings=["Conflict detected"],
            errors=["Missing activity"],
        )
        assert r.diff_type == HalfDayDiffType.MODIFIED
        assert len(r.warnings) == 1
        assert len(r.errors) == 1


class TestHalfDayDiffMetrics:
    def test_defaults(self):
        r = HalfDayDiffMetrics()
        assert r.total_slots == 0
        assert r.changed_slots == 0
        assert r.added == 0
        assert r.removed == 0
        assert r.modified == 0
        assert r.percent_changed == 0.0
        assert r.manual_half_days == 0
        assert r.manual_hours == 0.0
        assert r.by_activity == {}

    def test_full(self):
        r = HalfDayDiffMetrics(
            total_slots=100,
            changed_slots=10,
            added=5,
            removed=2,
            modified=3,
            percent_changed=10.0,
            manual_half_days=8,
            manual_hours=32.0,
            by_activity={"FM Clinic": 5, "ICU": 3},
        )
        assert r.total_slots == 100
        assert r.by_activity["FM Clinic"] == 5


class TestHalfDayImportStageResponse:
    def test_valid_minimal(self):
        r = HalfDayImportStageResponse(success=True, message="Staged successfully")
        assert r.batch_id is None
        assert r.created_at is None
        assert r.warnings == []
        assert r.diff_metrics is None

    def test_with_metrics(self):
        metrics = HalfDayDiffMetrics(total_slots=50, changed_slots=5)
        r = HalfDayImportStageResponse(
            success=True,
            batch_id=uuid4(),
            created_at=datetime(2026, 1, 1),
            message="Staged",
            diff_metrics=metrics,
        )
        assert r.diff_metrics.total_slots == 50


class TestHalfDayImportPreviewResponse:
    def test_valid(self):
        r = HalfDayImportPreviewResponse(
            batch_id=uuid4(),
            metrics=HalfDayDiffMetrics(),
        )
        assert r.diffs == []
        assert r.total_diffs == 0
        assert r.page == 1
        assert r.page_size == 50


class TestHalfDayImportDraftRequest:
    def test_defaults(self):
        r = HalfDayImportDraftRequest()
        assert r.staged_ids is None
        assert r.notes is None

    def test_with_ids(self):
        r = HalfDayImportDraftRequest(staged_ids=[uuid4(), uuid4()])
        assert len(r.staged_ids) == 2

    # --- notes max_length=2000 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            HalfDayImportDraftRequest(notes="x" * 2001)

    def test_notes_max_length(self):
        r = HalfDayImportDraftRequest(notes="x" * 2000)
        assert len(r.notes) == 2000


class TestHalfDayImportDraftResponse:
    def test_valid_minimal(self):
        r = HalfDayImportDraftResponse(
            success=True,
            batch_id=uuid4(),
            message="Draft created",
        )
        assert r.draft_id is None
        assert r.total_selected == 0
        assert r.added == 0
        assert r.modified == 0
        assert r.removed == 0
        assert r.skipped == 0
        assert r.failed == 0
        assert r.failed_ids == []

    def test_full(self):
        r = HalfDayImportDraftResponse(
            success=True,
            batch_id=uuid4(),
            draft_id=uuid4(),
            message="Applied",
            total_selected=10,
            added=5,
            modified=3,
            removed=1,
            skipped=0,
            failed=1,
            failed_ids=[uuid4()],
        )
        assert r.total_selected == 10
        assert len(r.failed_ids) == 1
