"""Tests for ImportStagingService dataclasses, constants, and pure functions.

Tests the result dataclasses (StageResult, PreviewResult, ApplyResult,
RollbackResult), module-level constants, and fuzzy matching logic
without DB access.
"""

from uuid import UUID, uuid4

import pytest

from app.models.import_staging import ImportBatchStatus
from app.services.import_staging_service import (
    FUZZY_MATCH_THRESHOLD,
    ROLLBACK_WINDOW_HOURS,
    ApplyResult,
    ImportStagingService,
    PreviewResult,
    RollbackResult,
    StageResult,
)


# ============================================================================
# Constants
# ============================================================================


class TestConstants:
    """Tests for module-level constants."""

    def test_rollback_window_is_24_hours(self):
        assert ROLLBACK_WINDOW_HOURS == 24

    def test_rollback_window_positive(self):
        assert ROLLBACK_WINDOW_HOURS > 0

    def test_fuzzy_match_threshold_is_70(self):
        assert FUZZY_MATCH_THRESHOLD == 70

    def test_fuzzy_match_threshold_in_range(self):
        assert 0 <= FUZZY_MATCH_THRESHOLD <= 100


# ============================================================================
# StageResult
# ============================================================================


class TestStageResult:
    """Tests for StageResult dataclass."""

    def test_success_result(self):
        batch_id = uuid4()
        result = StageResult(
            success=True,
            batch_id=batch_id,
            message="Successfully staged 10 rows",
            row_count=10,
        )
        assert result.success is True
        assert result.batch_id == batch_id
        assert result.row_count == 10
        assert result.error_code is None

    def test_failure_result(self):
        result = StageResult(
            success=False,
            message="Parse error",
            error_code="PARSE_ERROR",
            error_count=3,
        )
        assert result.success is False
        assert result.batch_id is None
        assert result.error_code == "PARSE_ERROR"
        assert result.error_count == 3

    def test_defaults(self):
        result = StageResult(success=True)
        assert result.batch_id is None
        assert result.message == ""
        assert result.error_code is None
        assert result.row_count == 0
        assert result.error_count == 0
        assert result.warning_count == 0


# ============================================================================
# PreviewResult
# ============================================================================


class TestPreviewResult:
    """Tests for PreviewResult dataclass."""

    def test_basic_preview(self):
        batch_id = uuid4()
        result = PreviewResult(
            batch_id=batch_id,
            new_count=5,
            update_count=3,
            conflict_count=1,
            skip_count=2,
            total_staged=11,
        )
        assert result.batch_id == batch_id
        assert result.new_count == 5
        assert result.update_count == 3
        assert result.conflict_count == 1
        assert result.skip_count == 2
        assert result.total_staged == 11

    def test_defaults(self):
        batch_id = uuid4()
        result = PreviewResult(batch_id=batch_id)
        assert result.new_count == 0
        assert result.update_count == 0
        assert result.conflict_count == 0
        assert result.skip_count == 0
        assert result.staged_assignments is None
        assert result.conflicts is None
        assert result.acgme_violations is None
        assert result.total_staged == 0

    def test_with_data(self):
        batch_id = uuid4()
        result = PreviewResult(
            batch_id=batch_id,
            staged_assignments=[{"id": "1"}],
            conflicts=[{"type": "overlap"}],
            acgme_violations=["80-hour rule"],
        )
        assert len(result.staged_assignments) == 1
        assert len(result.conflicts) == 1
        assert len(result.acgme_violations) == 1


# ============================================================================
# ApplyResult
# ============================================================================


class TestApplyResult:
    """Tests for ApplyResult dataclass."""

    def test_success_result(self):
        batch_id = uuid4()
        result = ApplyResult(
            success=True,
            batch_id=batch_id,
            status=ImportBatchStatus.APPROVED,
            applied_count=25,
        )
        assert result.success is True
        assert result.status == ImportBatchStatus.APPROVED
        assert result.applied_count == 25
        assert result.rollback_available is True

    def test_failure_result(self):
        batch_id = uuid4()
        result = ApplyResult(
            success=False,
            batch_id=batch_id,
            status=ImportBatchStatus.STAGED,
            error_count=5,
            errors=[{"error": "conflict"}],
            error_code="APPLY_FAILED",
        )
        assert result.success is False
        assert result.error_count == 5
        assert result.error_code == "APPLY_FAILED"

    def test_defaults(self):
        batch_id = uuid4()
        result = ApplyResult(
            success=True,
            batch_id=batch_id,
            status=ImportBatchStatus.APPROVED,
        )
        assert result.applied_count == 0
        assert result.skipped_count == 0
        assert result.error_count == 0
        assert result.errors is None
        assert result.acgme_warnings is None
        assert result.rollback_available is True
        assert result.rollback_expires_at is None
        assert result.message == ""
        assert result.error_code is None


# ============================================================================
# RollbackResult
# ============================================================================


class TestRollbackResult:
    """Tests for RollbackResult dataclass."""

    def test_success_result(self):
        batch_id = uuid4()
        result = RollbackResult(
            success=True,
            batch_id=batch_id,
            status=ImportBatchStatus.ROLLED_BACK,
            rolled_back_count=25,
        )
        assert result.success is True
        assert result.status == ImportBatchStatus.ROLLED_BACK
        assert result.rolled_back_count == 25

    def test_failure_result(self):
        batch_id = uuid4()
        result = RollbackResult(
            success=False,
            batch_id=batch_id,
            status=ImportBatchStatus.APPROVED,
            failed_count=3,
            errors=["Expired", "Conflict"],
            error_code="ROLLBACK_EXPIRED",
        )
        assert result.success is False
        assert result.failed_count == 3
        assert len(result.errors) == 2
        assert result.error_code == "ROLLBACK_EXPIRED"

    def test_defaults(self):
        batch_id = uuid4()
        result = RollbackResult(
            success=True,
            batch_id=batch_id,
            status=ImportBatchStatus.ROLLED_BACK,
        )
        assert result.rolled_back_count == 0
        assert result.failed_count == 0
        assert result.errors is None
        assert result.message == ""
        assert result.error_code is None


# ============================================================================
# Fuzzy matching — _fuzzy_match_person
# ============================================================================


class TestFuzzyMatchPerson:
    """Tests for _fuzzy_match_person with pre-loaded cache."""

    @pytest.fixture
    def service(self):
        svc = ImportStagingService.__new__(ImportStagingService)
        svc.db = None
        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()
        svc._person_cache = {
            "smith, john": (id1, 100),
            "jones, mary": (id2, 100),
            "williams, robert": (id3, 100),
        }
        svc._ids = {"smith": id1, "jones": id2, "williams": id3}
        return svc

    def test_exact_match(self, service):
        person_id, confidence = service._fuzzy_match_person("Smith, John")
        assert person_id == service._ids["smith"]
        assert confidence == 100

    def test_exact_match_case_insensitive(self, service):
        person_id, confidence = service._fuzzy_match_person("SMITH, JOHN")
        assert person_id == service._ids["smith"]
        assert confidence == 100

    def test_exact_match_strips_whitespace(self, service):
        person_id, confidence = service._fuzzy_match_person("  Smith, John  ")
        assert person_id == service._ids["smith"]
        assert confidence == 100

    def test_fuzzy_match_close_name(self, service):
        """A close misspelling should still match above threshold."""
        person_id, confidence = service._fuzzy_match_person("Smith, Johnn")
        assert person_id == service._ids["smith"]
        assert confidence >= FUZZY_MATCH_THRESHOLD

    def test_no_match_very_different_name(self, service):
        """A completely different name should not match."""
        person_id, confidence = service._fuzzy_match_person("Zzzzzzz, Xxxxxx")
        assert person_id is None
        assert confidence == 0

    def test_fuzzy_match_picks_best(self, service):
        """When multiple matches possible, picks highest scoring."""
        person_id, _ = service._fuzzy_match_person("Jones, Mar")
        assert person_id == service._ids["jones"]


# ============================================================================
# Fuzzy matching — _fuzzy_match_rotation
# ============================================================================


class TestFuzzyMatchRotation:
    """Tests for _fuzzy_match_rotation with pre-loaded cache."""

    @pytest.fixture
    def service(self):
        svc = ImportStagingService.__new__(ImportStagingService)
        svc.db = None
        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()
        svc._rotation_cache = {
            "family medicine": (id1, 100),
            "internal medicine": (id2, 100),
            "pediatrics": (id3, 100),
        }
        svc._ids = {"family": id1, "internal": id2, "peds": id3}
        return svc

    def test_exact_match(self, service):
        rotation_id, confidence = service._fuzzy_match_rotation("Family Medicine")
        assert rotation_id == service._ids["family"]
        assert confidence == 100

    def test_exact_match_case_insensitive(self, service):
        rotation_id, confidence = service._fuzzy_match_rotation("FAMILY MEDICINE")
        assert rotation_id == service._ids["family"]
        assert confidence == 100

    def test_exact_match_strips_whitespace(self, service):
        rotation_id, confidence = service._fuzzy_match_rotation("  Family Medicine  ")
        assert rotation_id == service._ids["family"]
        assert confidence == 100

    def test_fuzzy_match_close_name(self, service):
        rotation_id, confidence = service._fuzzy_match_rotation("Family Medicin")
        assert rotation_id == service._ids["family"]
        assert confidence >= FUZZY_MATCH_THRESHOLD

    def test_no_match_very_different(self, service):
        rotation_id, confidence = service._fuzzy_match_rotation("Zzzzzzz")
        assert rotation_id is None
        assert confidence == 0

    def test_internal_medicine_match(self, service):
        rotation_id, confidence = service._fuzzy_match_rotation("Internal Medicine")
        assert rotation_id == service._ids["internal"]
        assert confidence == 100

    def test_pediatrics_match(self, service):
        rotation_id, confidence = service._fuzzy_match_rotation("Pediatrics")
        assert rotation_id == service._ids["peds"]
        assert confidence == 100
