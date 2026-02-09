"""Tests for schedule draft schemas (Field bounds, field_validators, enums, defaults)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.schedule_draft import (
    ScheduleDraftStatus,
    DraftSourceType,
    DraftAssignmentChangeType,
    DraftFlagType,
    DraftFlagSeverity,
    ScheduleDraftCreate,
    ScheduleDraftCounts,
    ScheduleDraftResponse,
    ScheduleDraftListItem,
    ScheduleDraftList,
    DraftAssignmentResponse,
    DraftAssignmentCreate,
    DraftFlagResponse,
    DraftFlagAcknowledge,
    DraftFlagBulkAcknowledge,
    DraftPreviewResponse,
    PublishRequest,
    PublishResponse,
    RollbackRequest,
    RollbackResponse,
)


# ── Enums ──────────────────────────────────────────────────────────────


class TestScheduleDraftStatus:
    def test_values(self):
        assert ScheduleDraftStatus.DRAFT == "draft"
        assert ScheduleDraftStatus.PUBLISHED == "published"
        assert ScheduleDraftStatus.ROLLED_BACK == "rolled_back"
        assert ScheduleDraftStatus.DISCARDED == "discarded"

    def test_count(self):
        assert len(ScheduleDraftStatus) == 4


class TestDraftSourceType:
    def test_values(self):
        assert DraftSourceType.SOLVER == "solver"
        assert DraftSourceType.MANUAL == "manual"
        assert DraftSourceType.SWAP == "swap"
        assert DraftSourceType.IMPORT == "import"
        assert DraftSourceType.RESILIENCE == "resilience"

    def test_count(self):
        assert len(DraftSourceType) == 5


class TestDraftAssignmentChangeType:
    def test_values(self):
        assert DraftAssignmentChangeType.ADD == "add"
        assert DraftAssignmentChangeType.MODIFY == "modify"
        assert DraftAssignmentChangeType.DELETE == "delete"

    def test_count(self):
        assert len(DraftAssignmentChangeType) == 3


class TestDraftFlagType:
    def test_count(self):
        assert len(DraftFlagType) == 6

    def test_sample(self):
        assert DraftFlagType.CONFLICT == "conflict"
        assert DraftFlagType.CREDENTIAL_MISSING == "credential_missing"


class TestDraftFlagSeverity:
    def test_values(self):
        assert DraftFlagSeverity.ERROR == "error"
        assert DraftFlagSeverity.WARNING == "warning"
        assert DraftFlagSeverity.INFO == "info"

    def test_count(self):
        assert len(DraftFlagSeverity) == 3


# ── ScheduleDraftCreate ────────────────────────────────────────────────


class TestScheduleDraftCreate:
    def test_valid(self):
        r = ScheduleDraftCreate(
            source_type=DraftSourceType.SOLVER,
            target_start_date=date(2026, 1, 1),
            target_end_date=date(2026, 1, 31),
        )
        assert r.target_block is None
        assert r.schedule_run_id is None
        assert r.notes is None

    # --- target_block ge=1, le=26 ---

    def test_target_block_below_min(self):
        with pytest.raises(ValidationError):
            ScheduleDraftCreate(
                source_type=DraftSourceType.SOLVER,
                target_start_date=date(2026, 1, 1),
                target_end_date=date(2026, 1, 31),
                target_block=0,
            )

    def test_target_block_above_max(self):
        with pytest.raises(ValidationError):
            ScheduleDraftCreate(
                source_type=DraftSourceType.SOLVER,
                target_start_date=date(2026, 1, 1),
                target_end_date=date(2026, 1, 31),
                target_block=27,
            )

    # --- notes max_length=2000 ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            ScheduleDraftCreate(
                source_type=DraftSourceType.SOLVER,
                target_start_date=date(2026, 1, 1),
                target_end_date=date(2026, 1, 31),
                notes="x" * 2001,
            )

    # --- target_end_date validator (>= start_date) ---

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="target_end_date must be"):
            ScheduleDraftCreate(
                source_type=DraftSourceType.SOLVER,
                target_start_date=date(2026, 2, 1),
                target_end_date=date(2026, 1, 1),
            )

    def test_same_dates_ok(self):
        r = ScheduleDraftCreate(
            source_type=DraftSourceType.MANUAL,
            target_start_date=date(2026, 1, 1),
            target_end_date=date(2026, 1, 1),
        )
        assert r.target_end_date == date(2026, 1, 1)


# ── ScheduleDraftCounts ────────────────────────────────────────────────


class TestScheduleDraftCounts:
    def test_defaults(self):
        r = ScheduleDraftCounts()
        assert r.assignments_total == 0
        assert r.added == 0
        assert r.modified == 0
        assert r.deleted == 0
        assert r.flags_total == 0
        assert r.flags_acknowledged == 0
        assert r.flags_unacknowledged == 0


# ── ScheduleDraftResponse ──────────────────────────────────────────────


class TestScheduleDraftResponse:
    def test_defaults(self):
        r = ScheduleDraftResponse(
            id=uuid4(),
            created_at=datetime(2026, 1, 15),
            target_start_date=date(2026, 1, 1),
            target_end_date=date(2026, 1, 31),
            status=ScheduleDraftStatus.DRAFT,
            source_type=DraftSourceType.SOLVER,
        )
        assert r.created_by_id is None
        assert r.target_block is None
        assert r.source_schedule_run_id is None
        assert r.published_at is None
        assert r.published_by_id is None
        assert r.approved_at is None
        assert r.approved_by_id is None
        assert r.approval_reason is None
        assert r.lock_date_at_approval is None
        assert r.rollback_available is True
        assert r.rollback_expires_at is None
        assert r.rolled_back_at is None
        assert r.rolled_back_by_id is None
        assert r.notes is None
        assert r.change_summary is None
        assert r.flags_total == 0
        assert r.flags_acknowledged == 0
        assert r.override_comment is None
        assert r.override_by_id is None
        assert r.counts.assignments_total == 0


# ── ScheduleDraftList ──────────────────────────────────────────────────


class TestScheduleDraftList:
    def test_defaults(self):
        r = ScheduleDraftList(items=[], total=0, has_next=False, has_previous=False)
        assert r.page == 1
        assert r.page_size == 50

    # --- page ge=1 ---

    def test_page_below_min(self):
        with pytest.raises(ValidationError):
            ScheduleDraftList(
                items=[], total=0, page=0, has_next=False, has_previous=False
            )

    # --- page_size ge=1, le=100 ---

    def test_page_size_above_max(self):
        with pytest.raises(ValidationError):
            ScheduleDraftList(
                items=[],
                total=0,
                page_size=101,
                has_next=False,
                has_previous=False,
            )


# ── DraftAssignmentCreate ──────────────────────────────────────────────


class TestDraftAssignmentCreate:
    def test_defaults(self):
        r = DraftAssignmentCreate(person_id=uuid4(), assignment_date=date(2026, 1, 15))
        assert r.time_of_day is None
        assert r.activity_code is None
        assert r.rotation_id is None
        assert r.change_type == DraftAssignmentChangeType.ADD
        assert r.existing_assignment_id is None

    # --- time_of_day validator (AM/PM) ---

    def test_time_of_day_am(self):
        r = DraftAssignmentCreate(
            person_id=uuid4(),
            assignment_date=date(2026, 1, 15),
            time_of_day="am",
        )
        assert r.time_of_day == "AM"

    def test_time_of_day_pm(self):
        r = DraftAssignmentCreate(
            person_id=uuid4(),
            assignment_date=date(2026, 1, 15),
            time_of_day="PM",
        )
        assert r.time_of_day == "PM"

    def test_time_of_day_invalid(self):
        with pytest.raises(ValidationError, match="AM.*PM"):
            DraftAssignmentCreate(
                person_id=uuid4(),
                assignment_date=date(2026, 1, 15),
                time_of_day="EVENING",
            )

    def test_time_of_day_none_ok(self):
        r = DraftAssignmentCreate(
            person_id=uuid4(),
            assignment_date=date(2026, 1, 15),
            time_of_day=None,
        )
        assert r.time_of_day is None


# ── DraftFlagAcknowledge ───────────────────────────────────────────────


class TestDraftFlagAcknowledge:
    def test_defaults(self):
        r = DraftFlagAcknowledge()
        assert r.resolution_note is None

    # --- resolution_note max_length=500 ---

    def test_note_too_long(self):
        with pytest.raises(ValidationError):
            DraftFlagAcknowledge(resolution_note="x" * 501)


# ── DraftFlagBulkAcknowledge ───────────────────────────────────────────


class TestDraftFlagBulkAcknowledge:
    def test_valid(self):
        r = DraftFlagBulkAcknowledge(flag_ids=[uuid4()])
        assert r.resolution_note is None

    # --- flag_ids min_length=1, max_length=100 ---

    def test_empty_ids(self):
        with pytest.raises(ValidationError):
            DraftFlagBulkAcknowledge(flag_ids=[])

    def test_too_many_ids(self):
        with pytest.raises(ValidationError):
            DraftFlagBulkAcknowledge(flag_ids=[uuid4() for _ in range(101)])

    # --- resolution_note max_length=500 ---

    def test_note_too_long(self):
        with pytest.raises(ValidationError):
            DraftFlagBulkAcknowledge(flag_ids=[uuid4()], resolution_note="x" * 501)


# ── DraftPreviewResponse ──────────────────────────────────────────────


class TestDraftPreviewResponse:
    def test_defaults(self):
        r = DraftPreviewResponse(draft_id=uuid4())
        assert r.add_count == 0
        assert r.modify_count == 0
        assert r.delete_count == 0
        assert r.flags_total == 0
        assert r.flags_acknowledged == 0
        assert r.acgme_violations == []
        assert r.assignments == []
        assert r.flags == []


# ── PublishRequest ─────────────────────────────────────────────────────


class TestPublishRequest:
    def test_defaults(self):
        r = PublishRequest()
        assert r.override_comment is None
        assert r.break_glass_reason is None
        assert r.validate_acgme is True

    # --- override_comment max_length=500 ---

    def test_override_comment_too_long(self):
        with pytest.raises(ValidationError):
            PublishRequest(override_comment="x" * 501)

    # --- break_glass_reason max_length=500 ---

    def test_break_glass_reason_too_long(self):
        with pytest.raises(ValidationError):
            PublishRequest(break_glass_reason="x" * 501)


# ── PublishResponse ────────────────────────────────────────────────────


class TestPublishResponse:
    def test_defaults(self):
        r = PublishResponse(draft_id=uuid4(), status=ScheduleDraftStatus.PUBLISHED)
        assert r.published_count == 0
        assert r.error_count == 0
        assert r.errors == []
        assert r.acgme_warnings == []
        assert r.rollback_available is True
        assert r.rollback_expires_at is None
        assert r.message == ""


# ── RollbackRequest ────────────────────────────────────────────────────


class TestRollbackRequest:
    def test_defaults(self):
        r = RollbackRequest()
        assert r.reason is None

    # --- reason max_length=500 ---

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            RollbackRequest(reason="x" * 501)


# ── RollbackResponse ──────────────────────────────────────────────────


class TestRollbackResponse:
    def test_defaults(self):
        r = RollbackResponse(
            draft_id=uuid4(),
            status=ScheduleDraftStatus.ROLLED_BACK,
            rolled_back_at=datetime(2026, 1, 15),
        )
        assert r.rolled_back_count == 0
        assert r.failed_count == 0
        assert r.rolled_back_by_id is None
        assert r.errors == []
        assert r.message == ""
