"""Tests for ScheduleDraftService dataclasses and constants.

Tests the result dataclasses (CreateDraftResult, DraftPreviewResult,
PublishResult, RollbackResult) and module-level constants without DB access.
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.models.schedule_draft import ScheduleDraftStatus
from app.services.schedule_draft_service import (
    ROLLBACK_WINDOW_HOURS,
    STALE_DRAFT_HOURS,
    CreateDraftResult,
    DraftPreviewResult,
    PublishResult,
    RollbackResult,
)


# ============================================================================
# Constants
# ============================================================================


class TestConstants:
    """Tests for module-level constants."""

    def test_rollback_window_is_24_hours(self):
        assert ROLLBACK_WINDOW_HOURS == 24

    def test_stale_draft_threshold_is_24_hours(self):
        assert STALE_DRAFT_HOURS == 24

    def test_rollback_window_positive(self):
        assert ROLLBACK_WINDOW_HOURS > 0

    def test_stale_draft_positive(self):
        assert STALE_DRAFT_HOURS > 0


# ============================================================================
# CreateDraftResult
# ============================================================================


class TestCreateDraftResult:
    """Tests for CreateDraftResult dataclass."""

    def test_success_result(self):
        draft_id = uuid4()
        result = CreateDraftResult(
            success=True,
            draft_id=draft_id,
            message="Created draft for Block 10",
        )
        assert result.success is True
        assert result.draft_id == draft_id
        assert "Block 10" in result.message
        assert result.error_code is None

    def test_failure_result(self):
        result = CreateDraftResult(
            success=False,
            message="Failed to create draft",
            error_code="CREATE_FAILED",
        )
        assert result.success is False
        assert result.draft_id is None
        assert result.error_code == "CREATE_FAILED"

    def test_defaults(self):
        result = CreateDraftResult(success=True)
        assert result.draft_id is None
        assert result.message == ""
        assert result.error_code is None


# ============================================================================
# DraftPreviewResult
# ============================================================================


class TestDraftPreviewResult:
    """Tests for DraftPreviewResult dataclass."""

    def test_basic_preview(self):
        draft_id = uuid4()
        result = DraftPreviewResult(
            draft_id=draft_id,
            add_count=5,
            modify_count=3,
            delete_count=1,
            flags_total=2,
            flags_acknowledged=1,
        )
        assert result.draft_id == draft_id
        assert result.add_count == 5
        assert result.modify_count == 3
        assert result.delete_count == 1
        assert result.flags_total == 2
        assert result.flags_acknowledged == 1

    def test_defaults(self):
        draft_id = uuid4()
        result = DraftPreviewResult(draft_id=draft_id)
        assert result.add_count == 0
        assert result.modify_count == 0
        assert result.delete_count == 0
        assert result.flags_total == 0
        assert result.flags_acknowledged == 0
        assert result.assignments is None
        assert result.flags is None
        assert result.acgme_violations is None

    def test_with_assignments_and_flags(self):
        draft_id = uuid4()
        result = DraftPreviewResult(
            draft_id=draft_id,
            assignments=[{"id": "1", "activity_code": "C"}],
            flags=[{"type": "LOCK_WINDOW", "severity": "error"}],
            acgme_violations=["80-hour rule exceeded"],
        )
        assert len(result.assignments) == 1
        assert len(result.flags) == 1
        assert len(result.acgme_violations) == 1


# ============================================================================
# PublishResult
# ============================================================================


class TestPublishResult:
    """Tests for PublishResult dataclass."""

    def test_successful_publish(self):
        draft_id = uuid4()
        now = datetime.utcnow()
        result = PublishResult(
            success=True,
            draft_id=draft_id,
            status=ScheduleDraftStatus.PUBLISHED,
            published_count=25,
            rollback_available=True,
            rollback_expires_at=now,
        )
        assert result.success is True
        assert result.status == ScheduleDraftStatus.PUBLISHED
        assert result.published_count == 25
        assert result.rollback_available is True
        assert result.rollback_expires_at == now

    def test_failed_publish(self):
        draft_id = uuid4()
        result = PublishResult(
            success=False,
            draft_id=draft_id,
            status=ScheduleDraftStatus.DRAFT,
            error_count=5,
            errors=[{"error": "Assignment conflict"}],
            message="Publish failed",
            error_code="PUBLISH_FAILED",
        )
        assert result.success is False
        assert result.error_count == 5
        assert result.error_code == "PUBLISH_FAILED"

    def test_defaults(self):
        draft_id = uuid4()
        result = PublishResult(
            success=True,
            draft_id=draft_id,
            status=ScheduleDraftStatus.PUBLISHED,
        )
        assert result.published_count == 0
        assert result.error_count == 0
        assert result.errors is None
        assert result.acgme_warnings is None
        assert result.rollback_available is True
        assert result.rollback_expires_at is None
        assert result.message == ""
        assert result.error_code is None

    def test_with_acgme_warnings(self):
        draft_id = uuid4()
        result = PublishResult(
            success=True,
            draft_id=draft_id,
            status=ScheduleDraftStatus.PUBLISHED,
            acgme_warnings=[
                "Resident X near 80-hour limit",
                "Missing supervision ratio",
            ],
        )
        assert len(result.acgme_warnings) == 2


# ============================================================================
# RollbackResult
# ============================================================================


class TestRollbackResult:
    """Tests for RollbackResult dataclass."""

    def test_successful_rollback(self):
        draft_id = uuid4()
        result = RollbackResult(
            success=True,
            draft_id=draft_id,
            status=ScheduleDraftStatus.ROLLED_BACK,
            rolled_back_count=25,
        )
        assert result.success is True
        assert result.status == ScheduleDraftStatus.ROLLED_BACK
        assert result.rolled_back_count == 25

    def test_failed_rollback(self):
        draft_id = uuid4()
        result = RollbackResult(
            success=False,
            draft_id=draft_id,
            status=ScheduleDraftStatus.PUBLISHED,
            failed_count=3,
            errors=["Lock expired", "Conflict detected"],
            message="Rollback failed",
            error_code="ROLLBACK_EXPIRED",
        )
        assert result.success is False
        assert result.failed_count == 3
        assert len(result.errors) == 2
        assert result.error_code == "ROLLBACK_EXPIRED"

    def test_defaults(self):
        draft_id = uuid4()
        result = RollbackResult(
            success=True,
            draft_id=draft_id,
            status=ScheduleDraftStatus.ROLLED_BACK,
        )
        assert result.rolled_back_count == 0
        assert result.failed_count == 0
        assert result.errors is None
        assert result.message == ""
        assert result.error_code is None
