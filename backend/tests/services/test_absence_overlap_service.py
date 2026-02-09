"""Tests for absence_overlap_service.py — pure classification logic.

Tests the private methods that don't require DB access:
- _classify_overlap: date range overlap classification
- _assess_severity: overlap severity assessment
- _get_resolution_options: resolution suggestions
- _get_primary_overlap_type: priority ranking
- _can_auto_merge: auto-merge eligibility
- _suggest_action: action recommendation

No async/DB fixtures needed — we instantiate the service with db=None
since none of these methods touch the database.
"""

from datetime import date
from uuid import uuid4

import pytest

from app.models.import_staging import OverlapType
from app.services.absence_overlap_service import (
    AbsenceOverlapService,
    OverlapDetail,
    OverlapSeverity,
)


@pytest.fixture
def service():
    """Create service with no DB (only testing pure methods)."""
    return AbsenceOverlapService(db=None)  # type: ignore[arg-type]


# ============================================================================
# _classify_overlap
# ============================================================================


class TestClassifyOverlap:
    """Test date range overlap classification."""

    def test_exact_match(self, service):
        result = service._classify_overlap(
            date(2026, 1, 1),
            date(2026, 1, 10),
            date(2026, 1, 1),
            date(2026, 1, 10),
        )
        assert result == OverlapType.EXACT

    def test_no_overlap_before(self, service):
        result = service._classify_overlap(
            date(2026, 1, 1),
            date(2026, 1, 5),
            date(2026, 1, 10),
            date(2026, 1, 15),
        )
        assert result == OverlapType.NONE

    def test_no_overlap_after(self, service):
        result = service._classify_overlap(
            date(2026, 1, 10),
            date(2026, 1, 15),
            date(2026, 1, 1),
            date(2026, 1, 5),
        )
        assert result == OverlapType.NONE

    def test_new_contained_in_existing(self, service):
        result = service._classify_overlap(
            date(2026, 1, 3),
            date(2026, 1, 7),
            date(2026, 1, 1),
            date(2026, 1, 10),
        )
        assert result == OverlapType.CONTAINED

    def test_new_contains_existing(self, service):
        result = service._classify_overlap(
            date(2026, 1, 1),
            date(2026, 1, 10),
            date(2026, 1, 3),
            date(2026, 1, 7),
        )
        assert result == OverlapType.CONTAINS

    def test_partial_overlap_right(self, service):
        """New starts before existing ends."""
        result = service._classify_overlap(
            date(2026, 1, 5),
            date(2026, 1, 15),
            date(2026, 1, 1),
            date(2026, 1, 10),
        )
        assert result == OverlapType.PARTIAL

    def test_partial_overlap_left(self, service):
        """New ends after existing starts."""
        result = service._classify_overlap(
            date(2026, 1, 1),
            date(2026, 1, 10),
            date(2026, 1, 5),
            date(2026, 1, 15),
        )
        assert result == OverlapType.PARTIAL

    def test_adjacent_dates_overlap(self, service):
        """Same boundary date counts as partial overlap."""
        result = service._classify_overlap(
            date(2026, 1, 1),
            date(2026, 1, 5),
            date(2026, 1, 5),
            date(2026, 1, 10),
        )
        assert result == OverlapType.PARTIAL

    def test_single_day_exact(self, service):
        result = service._classify_overlap(
            date(2026, 1, 5),
            date(2026, 1, 5),
            date(2026, 1, 5),
            date(2026, 1, 5),
        )
        assert result == OverlapType.EXACT

    def test_single_day_contained(self, service):
        result = service._classify_overlap(
            date(2026, 1, 5),
            date(2026, 1, 5),
            date(2026, 1, 1),
            date(2026, 1, 10),
        )
        assert result == OverlapType.CONTAINED

    def test_new_equals_existing_start(self, service):
        """Same start, new ends earlier -> contained."""
        result = service._classify_overlap(
            date(2026, 1, 1),
            date(2026, 1, 5),
            date(2026, 1, 1),
            date(2026, 1, 10),
        )
        assert result == OverlapType.CONTAINED

    def test_new_equals_existing_end(self, service):
        """Same end, new starts later -> contained."""
        result = service._classify_overlap(
            date(2026, 1, 5),
            date(2026, 1, 10),
            date(2026, 1, 1),
            date(2026, 1, 10),
        )
        assert result == OverlapType.CONTAINED


# ============================================================================
# _assess_severity
# ============================================================================


class TestAssessSeverity:
    """Test overlap severity classification."""

    def test_exact_always_critical(self, service):
        result = service._assess_severity(OverlapType.EXACT, "leave", "leave")
        assert result == OverlapSeverity.CRITICAL

    def test_exact_different_types_critical(self, service):
        result = service._assess_severity(OverlapType.EXACT, "tdy", "leave")
        assert result == OverlapSeverity.CRITICAL

    def test_contained_same_type_critical(self, service):
        result = service._assess_severity(OverlapType.CONTAINED, "tdy", "tdy")
        assert result == OverlapSeverity.CRITICAL

    def test_contains_same_type_critical(self, service):
        result = service._assess_severity(OverlapType.CONTAINS, "tdy", "tdy")
        assert result == OverlapSeverity.CRITICAL

    def test_partial_different_types_warning(self, service):
        result = service._assess_severity(OverlapType.PARTIAL, "tdy", "leave")
        assert result == OverlapSeverity.WARNING

    def test_contains_different_types_warning(self, service):
        result = service._assess_severity(OverlapType.CONTAINS, "tdy", "leave")
        assert result == OverlapSeverity.WARNING

    def test_contained_different_types_info(self, service):
        """Contained with different types is just info."""
        result = service._assess_severity(OverlapType.CONTAINED, "tdy", "leave")
        assert result == OverlapSeverity.INFO

    def test_partial_same_type_warning(self, service):
        result = service._assess_severity(OverlapType.PARTIAL, "leave", "leave")
        assert result == OverlapSeverity.WARNING


# ============================================================================
# _get_resolution_options
# ============================================================================


class TestGetResolutionOptions:
    """Test resolution option generation."""

    def test_exact_options(self, service):
        options = service._get_resolution_options(OverlapType.EXACT, "leave", "leave")
        assert "skip" in options
        assert "replace" in options

    def test_contained_options(self, service):
        options = service._get_resolution_options(
            OverlapType.CONTAINED, "leave", "leave"
        )
        assert options == ["skip"]

    def test_contains_same_type(self, service):
        options = service._get_resolution_options(OverlapType.CONTAINS, "tdy", "tdy")
        assert "replace" in options
        assert "extend_existing" in options

    def test_contains_different_type(self, service):
        options = service._get_resolution_options(OverlapType.CONTAINS, "tdy", "leave")
        assert "create_separate" in options

    def test_partial_same_type(self, service):
        options = service._get_resolution_options(OverlapType.PARTIAL, "leave", "leave")
        assert "merge" in options

    def test_partial_different_type(self, service):
        options = service._get_resolution_options(OverlapType.PARTIAL, "tdy", "leave")
        assert "create_separate" in options
        assert "merge" not in options

    def test_none_no_options(self, service):
        options = service._get_resolution_options(OverlapType.NONE, "leave", "leave")
        assert options == []


# ============================================================================
# _get_primary_overlap_type
# ============================================================================


class TestGetPrimaryOverlapType:
    """Test priority ranking of overlap types."""

    def _detail(self, overlap_type):
        """Create a minimal OverlapDetail for testing."""
        return OverlapDetail(
            existing_absence_id=uuid4(),
            overlap_type=overlap_type,
            severity=OverlapSeverity.INFO,
            existing_start_date=date(2026, 1, 1),
            existing_end_date=date(2026, 1, 10),
            existing_absence_type="leave",
            overlap_start_date=date(2026, 1, 1),
            overlap_end_date=date(2026, 1, 5),
            overlap_days=5,
            description="test",
        )

    def test_empty_returns_none(self, service):
        result = service._get_primary_overlap_type([])
        assert result == OverlapType.NONE

    def test_single_exact(self, service):
        result = service._get_primary_overlap_type([self._detail(OverlapType.EXACT)])
        assert result == OverlapType.EXACT

    def test_exact_beats_partial(self, service):
        details = [
            self._detail(OverlapType.PARTIAL),
            self._detail(OverlapType.EXACT),
        ]
        result = service._get_primary_overlap_type(details)
        assert result == OverlapType.EXACT

    def test_contained_beats_partial(self, service):
        details = [
            self._detail(OverlapType.PARTIAL),
            self._detail(OverlapType.CONTAINED),
        ]
        result = service._get_primary_overlap_type(details)
        assert result == OverlapType.CONTAINED

    def test_contained_beats_contains(self, service):
        details = [
            self._detail(OverlapType.CONTAINS),
            self._detail(OverlapType.CONTAINED),
        ]
        result = service._get_primary_overlap_type(details)
        assert result == OverlapType.CONTAINED


# ============================================================================
# _can_auto_merge
# ============================================================================


class TestCanAutoMerge:
    """Test auto-merge eligibility."""

    def _detail(self, overlap_type, absence_type="leave"):
        return OverlapDetail(
            existing_absence_id=uuid4(),
            overlap_type=overlap_type,
            severity=OverlapSeverity.INFO,
            existing_start_date=date(2026, 1, 1),
            existing_end_date=date(2026, 1, 10),
            existing_absence_type=absence_type,
            overlap_start_date=date(2026, 1, 1),
            overlap_end_date=date(2026, 1, 5),
            overlap_days=5,
            description="test",
        )

    def test_empty_details(self, service):
        assert service._can_auto_merge([], "leave") is False

    def test_single_partial_same_type(self, service):
        details = [self._detail(OverlapType.PARTIAL, "leave")]
        assert service._can_auto_merge(details, "leave") is True

    def test_single_contains_same_type(self, service):
        details = [self._detail(OverlapType.CONTAINS, "leave")]
        assert service._can_auto_merge(details, "leave") is True

    def test_different_types_no_merge(self, service):
        details = [self._detail(OverlapType.PARTIAL, "tdy")]
        assert service._can_auto_merge(details, "leave") is False

    def test_exact_no_merge(self, service):
        details = [self._detail(OverlapType.EXACT, "leave")]
        assert service._can_auto_merge(details, "leave") is False

    def test_multiple_overlaps_no_merge(self, service):
        details = [
            self._detail(OverlapType.PARTIAL, "leave"),
            self._detail(OverlapType.PARTIAL, "leave"),
        ]
        assert service._can_auto_merge(details, "leave") is False


# ============================================================================
# _suggest_action
# ============================================================================


class TestSuggestAction:
    """Test action suggestion logic."""

    def _detail(self, overlap_type, absence_type="leave"):
        return OverlapDetail(
            existing_absence_id=uuid4(),
            overlap_type=overlap_type,
            severity=OverlapSeverity.INFO,
            existing_start_date=date(2026, 1, 1),
            existing_end_date=date(2026, 1, 10),
            existing_absence_type=absence_type,
            overlap_start_date=date(2026, 1, 1),
            overlap_end_date=date(2026, 1, 5),
            overlap_days=5,
            description="test",
        )

    def test_none_suggests_create(self, service):
        result = service._suggest_action(OverlapType.NONE, [], "leave")
        assert result == "create"

    def test_exact_suggests_skip(self, service):
        details = [self._detail(OverlapType.EXACT)]
        result = service._suggest_action(OverlapType.EXACT, details, "leave")
        assert result == "skip"

    def test_contained_suggests_skip(self, service):
        details = [self._detail(OverlapType.CONTAINED)]
        result = service._suggest_action(OverlapType.CONTAINED, details, "leave")
        assert result == "skip"

    def test_contains_same_type_suggests_extend(self, service):
        details = [self._detail(OverlapType.CONTAINS, "leave")]
        result = service._suggest_action(OverlapType.CONTAINS, details, "leave")
        assert result == "extend"

    def test_partial_same_type_suggests_merge(self, service):
        details = [self._detail(OverlapType.PARTIAL, "leave")]
        result = service._suggest_action(OverlapType.PARTIAL, details, "leave")
        assert result == "merge"

    def test_partial_different_type_suggests_create(self, service):
        details = [self._detail(OverlapType.PARTIAL, "tdy")]
        result = service._suggest_action(OverlapType.PARTIAL, details, "leave")
        assert result == "create"

    def test_multiple_overlaps_suggests_create(self, service):
        details = [
            self._detail(OverlapType.PARTIAL, "leave"),
            self._detail(OverlapType.PARTIAL, "leave"),
        ]
        result = service._suggest_action(OverlapType.PARTIAL, details, "leave")
        assert result == "create"
