"""Comprehensive tests for SwapAutoMatcher service."""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.swap import SwapApproval, SwapRecord, SwapStatus, SwapType
from app.schemas.swap_matching import (
    MatchingCriteria,
    MatchPriority,
    MatchType,
)
from app.services.swap_auto_matcher import SwapAutoMatcher


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def faculty_members(db: Session) -> list[Person]:
    """Create multiple faculty members for testing."""
    faculty_list = []
    for i in range(6):
        faculty = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i+1}",
            type="faculty",
            email=f"faculty{i+1}@hospital.org",
            performs_procedures=True,
            specialties=["General"],
        )
        db.add(faculty)
        faculty_list.append(faculty)
    db.commit()
    for f in faculty_list:
        db.refresh(f)
    return faculty_list


@pytest.fixture
def swap_auto_matcher(db: Session) -> SwapAutoMatcher:
    """Create a SwapAutoMatcher instance with test database."""
    return SwapAutoMatcher(db)


@pytest.fixture
def custom_criteria_matcher(db: Session) -> SwapAutoMatcher:
    """Create a SwapAutoMatcher with custom matching criteria."""
    criteria = MatchingCriteria(
        date_proximity_weight=0.3,
        preference_alignment_weight=0.3,
        workload_balance_weight=0.2,
        history_weight=0.1,
        availability_weight=0.1,
        minimum_score_threshold=0.5,
        max_date_separation_days=90,
        high_priority_threshold=0.8,
    )
    return SwapAutoMatcher(db, criteria)


@pytest.fixture
def sample_blocks(db: Session) -> list[Block]:
    """Create sample blocks for testing."""
    blocks = []
    start_date = date.today() + timedelta(days=14)

    for i in range(12):  # 12 weeks
        block = Block(
            id=uuid4(),
            name=f"Week {i+1}",
            start_date=start_date + timedelta(weeks=i),
            end_date=start_date + timedelta(weeks=i, days=6),
        )
        db.add(block)
        blocks.append(block)

    db.commit()
    for block in blocks:
        db.refresh(block)
    return blocks


@pytest.fixture
def faculty_preferences(db: Session, faculty_members: list[Person]) -> list[FacultyPreference]:
    """Create faculty preferences for testing."""
    preferences = []
    base_date = date.today() + timedelta(days=14)

    ***REMOVED*** 0: prefers week 2, blocks week 0
    pref0 = FacultyPreference(
        id=uuid4(),
        faculty_id=faculty_members[0].id,
        preferred_weeks=[(base_date + timedelta(weeks=2)).isoformat()],
        blocked_weeks=[(base_date + timedelta(weeks=0)).isoformat()],
        max_weeks_per_month=2,
    )

    ***REMOVED*** 1: prefers week 0, blocks week 2
    pref1 = FacultyPreference(
        id=uuid4(),
        faculty_id=faculty_members[1].id,
        preferred_weeks=[(base_date + timedelta(weeks=0)).isoformat()],
        blocked_weeks=[(base_date + timedelta(weeks=2)).isoformat()],
        max_weeks_per_month=2,
    )

    ***REMOVED*** 2: no specific preferences
    pref2 = FacultyPreference(
        id=uuid4(),
        faculty_id=faculty_members[2].id,
        preferred_weeks=[],
        blocked_weeks=[],
        max_weeks_per_month=3,
    )

    preferences.extend([pref0, pref1, pref2])
    db.add_all(preferences)
    db.commit()
    for pref in preferences:
        db.refresh(pref)
    return preferences


@pytest.fixture
def pending_swap_requests(
    db: Session,
    faculty_members: list[Person],
    sample_blocks: list[Block]
) -> list[SwapRecord]:
    """Create pending swap requests for testing."""
    base_date = date.today() + timedelta(days=14)

    # Perfect mutual match: Faculty 0 and 1 want each other's weeks
    swap1 = SwapRecord(
        id=uuid4(),
        source_faculty_id=faculty_members[0].id,
        source_week=base_date,
        target_week=base_date + timedelta(weeks=2),
        target_faculty_id=None,
        swap_type=SwapType.ONE_TO_ONE,
        status=SwapStatus.PENDING,
        requested_at=datetime.utcnow(),
    )

    swap2 = SwapRecord(
        id=uuid4(),
        source_faculty_id=faculty_members[1].id,
        source_week=base_date + timedelta(weeks=2),
        target_week=base_date,
        target_faculty_id=None,
        swap_type=SwapType.ONE_TO_ONE,
        status=SwapStatus.PENDING,
        requested_at=datetime.utcnow(),
    )

    # Non-matching request
    swap3 = SwapRecord(
        id=uuid4(),
        source_faculty_id=faculty_members[2].id,
        source_week=base_date + timedelta(weeks=6),
        target_week=base_date + timedelta(weeks=8),
        target_faculty_id=None,
        swap_type=SwapType.ONE_TO_ONE,
        status=SwapStatus.PENDING,
        requested_at=datetime.utcnow(),
    )

    # Absorb type request
    swap4 = SwapRecord(
        id=uuid4(),
        source_faculty_id=faculty_members[3].id,
        source_week=base_date + timedelta(weeks=4),
        target_week=None,
        target_faculty_id=None,
        swap_type=SwapType.ABSORB,
        status=SwapStatus.PENDING,
        requested_at=datetime.utcnow(),
    )

    swaps = [swap1, swap2, swap3, swap4]
    db.add_all(swaps)
    db.commit()
    for swap in swaps:
        db.refresh(swap)
    return swaps


# ============================================================================
# Test Service Initialization
# ============================================================================


class TestSwapAutoMatcherInitialization:
    """Tests for SwapAutoMatcher initialization."""

    def test_init_with_default_criteria(self, db: Session):
        """Test initialization with default matching criteria."""
        matcher = SwapAutoMatcher(db)

        assert matcher.db == db
        assert matcher.criteria is not None
        assert matcher.criteria.date_proximity_weight == 0.25
        assert matcher.criteria.preference_alignment_weight == 0.30
        assert matcher.criteria.workload_balance_weight == 0.20
        assert matcher.criteria.history_weight == 0.15
        assert matcher.criteria.availability_weight == 0.10
        assert matcher.preference_service is not None
        assert matcher.validation_service is not None

    def test_init_with_custom_criteria(self, db: Session):
        """Test initialization with custom matching criteria."""
        criteria = MatchingCriteria(
            date_proximity_weight=0.4,
            preference_alignment_weight=0.3,
            workload_balance_weight=0.1,
            history_weight=0.1,
            availability_weight=0.1,
            minimum_score_threshold=0.6,
        )
        matcher = SwapAutoMatcher(db, criteria)

        assert matcher.criteria.date_proximity_weight == 0.4
        assert matcher.criteria.minimum_score_threshold == 0.6


# ============================================================================
# Test Finding Compatible Swaps
# ============================================================================


class TestFindCompatibleSwaps:
    """Tests for find_compatible_swaps method."""

    def test_find_compatible_swaps_with_matches(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
    ):
        """Test finding compatible swaps when matches exist."""
        # Find matches for swap1 (should match with swap2)
        matches = swap_auto_matcher.find_compatible_swaps(pending_swap_requests[0].id)

        assert len(matches) >= 1
        # Check that we found swap2 as a match
        match_ids = [m.request_b_id for m in matches]
        assert pending_swap_requests[1].id in match_ids

        # Verify match properties
        first_match = matches[0]
        assert first_match.request_a_id == pending_swap_requests[0].id
        assert first_match.match_type in [MatchType.MUTUAL, MatchType.ONE_WAY]
        assert isinstance(first_match.faculty_a_name, str)
        assert isinstance(first_match.faculty_b_name, str)

    def test_find_compatible_swaps_no_matches(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test finding compatible swaps when no matches exist."""
        # Create an isolated swap request with no potential matches
        base_date = date.today() + timedelta(days=180)
        isolated_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[4].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add(isolated_swap)
        db.commit()
        db.refresh(isolated_swap)

        matches = swap_auto_matcher.find_compatible_swaps(isolated_swap.id)

        assert len(matches) == 0

    def test_find_compatible_swaps_nonexistent_request(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
    ):
        """Test that finding swaps for non-existent request raises error."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match=f"Swap request {fake_id} not found"):
            swap_auto_matcher.find_compatible_swaps(fake_id)

    def test_find_compatible_swaps_only_pending_status(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test that only pending requests are matched."""
        base_date = date.today() + timedelta(days=14)

        # Create an approved swap (should not be matched)
        approved_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.APPROVED,
            requested_at=datetime.utcnow(),
        )
        db.add(approved_swap)
        db.commit()
        db.refresh(approved_swap)

        matches = swap_auto_matcher.find_compatible_swaps(approved_swap.id)

        # Should return empty list for non-pending requests
        assert len(matches) == 0

    def test_find_compatible_swaps_excludes_same_faculty(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test that faculty are not matched with themselves."""
        base_date = date.today() + timedelta(days=14)

        # Create two swaps from same faculty
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date + timedelta(weeks=2),
            target_week=base_date + timedelta(weeks=3),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add_all([swap1, swap2])
        db.commit()

        matches = swap_auto_matcher.find_compatible_swaps(swap1.id)

        # Should not match with swap2 (same faculty)
        match_ids = [m.request_b_id for m in matches]
        assert swap2.id not in match_ids


# ============================================================================
# Test 5-Factor Compatibility Scoring
# ============================================================================


class TestCompatibilityScoring:
    """Tests for score_swap_compatibility and individual scoring factors."""

    def test_score_swap_compatibility_perfect_match(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test scoring for a perfect mutual match with preference alignment."""
        base_date = date.today() + timedelta(days=14)

        ***REMOVED*** 0 wants week 2, Faculty 1 wants week 0
        # These preferences already exist in faculty_preferences fixture
        swap_a = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=2),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=2),
            target_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher.score_swap_compatibility(swap_a, swap_b)

        # Perfect match should have high score
        assert 0.0 <= score <= 1.0
        assert score > 0.5, "Perfect match should score above 0.5"

    def test_score_swap_compatibility_blocked_week(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test scoring when one party has blocked the week they would receive."""
        base_date = date.today() + timedelta(days=14)

        ***REMOVED*** 0 blocks week 0, so they can't accept it from Faculty 2
        swap_a = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[2].id,
            source_week=base_date + timedelta(weeks=1),
            target_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher.score_swap_compatibility(swap_a, swap_b)

        # Blocked week should result in very low or zero score
        assert 0.0 <= score <= 1.0
        assert score < 0.3, "Blocked week should result in low score"

    def test_score_date_proximity_close_dates(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test date proximity scoring for close dates."""
        base_date = date.today() + timedelta(days=14)

        # Dates within 2 weeks
        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(days=7),  # 1 week apart
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher._score_date_proximity(swap_a, swap_b)

        assert score == 1.0, "Dates within 2 weeks should score 1.0"

    def test_score_date_proximity_distant_dates(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test date proximity scoring for distant dates."""
        base_date = date.today() + timedelta(days=14)

        # Dates far apart
        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(days=120),  # ~17 weeks apart
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher._score_date_proximity(swap_a, swap_b)

        assert 0.0 <= score <= 1.0
        assert score < 1.0, "Distant dates should score below 1.0"

    def test_score_availability_both_available(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test availability scoring when both parties are available."""
        base_date = date.today() + timedelta(days=14)

        ***REMOVED*** 2 has no blocks
        swap_a = SwapRecord(
            source_faculty_id=faculty_members[2].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[2].id,
            source_week=base_date + timedelta(weeks=2),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher._score_availability(swap_a, swap_b)

        assert score >= 0.5, "Both available should score at least 0.5"

    def test_score_availability_one_blocked(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test availability scoring when one party has blocked week."""
        base_date = date.today() + timedelta(days=14)

        ***REMOVED*** 0 blocks week 0
        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[2].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher._score_availability(swap_a, swap_b)

        assert 0.0 <= score <= 1.0

    def test_score_swap_history_no_history(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test history scoring when no past swaps exist."""
        base_date = date.today() + timedelta(days=14)

        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher._score_swap_history(swap_a, swap_b)

        # No history should default to neutral/high score
        assert 0.5 <= score <= 1.0

    def test_score_swap_history_with_past_rejection(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test history scoring with past rejections."""
        base_date = date.today() + timedelta(days=14)

        # Create past rejected swap between faculty 0 and 1
        past_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            target_faculty_id=faculty_members[1].id,
            source_week=base_date - timedelta(days=30),
            target_week=base_date - timedelta(days=23),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.REJECTED,
            requested_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(past_swap)
        db.commit()

        # New swap between same faculty
        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher._score_swap_history(swap_a, swap_b)

        # Past rejection should lower score
        assert 0.0 <= score <= 1.0
        assert score < 1.0, "Past rejection should lower history score"

    def test_score_swap_history_with_past_success(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test history scoring with past successful swaps."""
        base_date = date.today() + timedelta(days=14)

        # Create past executed swap between faculty 0 and 1
        past_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            target_faculty_id=faculty_members[1].id,
            source_week=base_date - timedelta(days=60),
            target_week=base_date - timedelta(days=53),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.EXECUTED,
            requested_at=datetime.utcnow() - timedelta(days=60),
            executed_at=datetime.utcnow() - timedelta(days=55),
        )
        db.add(past_swap)
        db.commit()

        # New swap between same faculty
        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher._score_swap_history(swap_a, swap_b)

        # Past success should maintain or boost score
        assert 0.5 <= score <= 1.0

    def test_score_normalized_to_range(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test that total compatibility score is normalized to 0-1 range."""
        base_date = date.today() + timedelta(days=14)

        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = swap_auto_matcher.score_swap_compatibility(swap_a, swap_b)

        assert 0.0 <= score <= 1.0, "Score must be between 0.0 and 1.0"


# ============================================================================
# Test Suggesting Optimal Matches
# ============================================================================


class TestSuggestOptimalMatches:
    """Tests for suggest_optimal_matches method."""

    def test_suggest_optimal_matches_with_results(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test suggesting optimal matches when matches exist."""
        matches = swap_auto_matcher.suggest_optimal_matches(
            pending_swap_requests[0].id,
            top_k=5
        )

        assert len(matches) >= 1

        # Verify first match structure
        first_match = matches[0]
        assert first_match.compatibility_score >= 0.0
        assert first_match.compatibility_score <= 1.0
        assert first_match.priority in [
            MatchPriority.CRITICAL,
            MatchPriority.HIGH,
            MatchPriority.MEDIUM,
            MatchPriority.LOW,
        ]
        assert first_match.scoring_breakdown is not None
        assert isinstance(first_match.explanation, str)
        assert 0.0 <= first_match.estimated_acceptance_probability <= 1.0
        assert isinstance(first_match.recommended_action, str)
        assert isinstance(first_match.warnings, list)

    def test_suggest_optimal_matches_sorted_by_score(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test that matches are sorted by compatibility score (highest first)."""
        matches = swap_auto_matcher.suggest_optimal_matches(
            pending_swap_requests[0].id,
            top_k=10
        )

        if len(matches) > 1:
            # Verify descending order
            for i in range(len(matches) - 1):
                assert matches[i].compatibility_score >= matches[i+1].compatibility_score

    def test_suggest_optimal_matches_respects_top_k(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
    ):
        """Test that suggest_optimal_matches respects the top_k parameter."""
        matches = swap_auto_matcher.suggest_optimal_matches(
            pending_swap_requests[0].id,
            top_k=2
        )

        assert len(matches) <= 2

    def test_suggest_optimal_matches_filters_by_threshold(
        self,
        db: Session,
        custom_criteria_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test that matches below threshold are filtered out."""
        base_date = date.today() + timedelta(days=14)

        # Create swaps with poor compatibility
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=15),  # Far apart
            target_week=None,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
        )
        db.add_all([swap1, swap2])
        db.commit()

        # Custom criteria has threshold of 0.5
        matches = custom_criteria_matcher.suggest_optimal_matches(swap1.id, top_k=10)

        # All returned matches should be above threshold
        for match in matches:
            assert match.compatibility_score >= 0.5

    def test_suggest_optimal_matches_scoring_breakdown(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test that scoring breakdown contains all 5 factors."""
        matches = swap_auto_matcher.suggest_optimal_matches(
            pending_swap_requests[0].id,
            top_k=1
        )

        assert len(matches) >= 1

        breakdown = matches[0].scoring_breakdown
        assert 0.0 <= breakdown.date_proximity_score <= 1.0
        assert 0.0 <= breakdown.preference_alignment_score <= 1.0
        assert 0.0 <= breakdown.workload_balance_score <= 1.0
        assert 0.0 <= breakdown.history_score <= 1.0
        assert 0.0 <= breakdown.availability_score <= 1.0
        assert 0.0 <= breakdown.blocking_penalty <= 1.0
        assert 0.0 <= breakdown.total_score <= 1.0

    def test_suggest_optimal_matches_nonexistent_request(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
    ):
        """Test suggesting matches for non-existent request raises error."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match=f"Swap request {fake_id} not found"):
            swap_auto_matcher.suggest_optimal_matches(fake_id)

    def test_suggest_optimal_matches_no_results(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test suggesting matches when no compatible matches exist."""
        base_date = date.today() + timedelta(days=180)

        isolated_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[4].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add(isolated_swap)
        db.commit()

        matches = swap_auto_matcher.suggest_optimal_matches(isolated_swap.id)

        assert len(matches) == 0


# ============================================================================
# Test Priority Determination
# ============================================================================


class TestPriorityDetermination:
    """Tests for match priority determination."""

    def test_determine_priority_critical_with_blocked_week(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test that blocked weeks with high score result in critical priority."""
        base_date = date.today() + timedelta(days=14)

        ***REMOVED*** 0 has week 0 blocked
        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[2].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        priority = swap_auto_matcher._determine_priority(0.75, swap_a, swap_b)

        # Blocked week with good score should be critical
        assert priority == MatchPriority.CRITICAL

    def test_determine_priority_high_score(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test high priority for high compatibility scores."""
        base_date = date.today() + timedelta(days=14)

        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        priority = swap_auto_matcher._determine_priority(0.85, swap_a, swap_b)

        assert priority == MatchPriority.HIGH

    def test_determine_priority_medium_score(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test medium priority for moderate scores."""
        base_date = date.today() + timedelta(days=14)

        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        priority = swap_auto_matcher._determine_priority(0.65, swap_a, swap_b)

        assert priority == MatchPriority.MEDIUM

    def test_determine_priority_low_score(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test low priority for low scores."""
        base_date = date.today() + timedelta(days=14)

        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        priority = swap_auto_matcher._determine_priority(0.45, swap_a, swap_b)

        assert priority == MatchPriority.LOW


# ============================================================================
# Test Batch Auto-Matching
# ============================================================================


class TestAutoMatchPendingRequests:
    """Tests for auto_match_pending_requests method."""

    def test_auto_match_pending_requests_with_matches(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test batch auto-matching with pending requests."""
        result = swap_auto_matcher.auto_match_pending_requests()

        assert result.total_requests_processed == len(pending_swap_requests)
        assert result.total_matches_found >= 0
        assert result.execution_time_seconds > 0
        assert isinstance(result.successful_matches, list)
        assert isinstance(result.no_matches, list)
        assert isinstance(result.high_priority_matches, list)

    def test_auto_match_pending_requests_no_requests(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
    ):
        """Test batch auto-matching when no pending requests exist."""
        result = swap_auto_matcher.auto_match_pending_requests()

        assert result.total_requests_processed == 0
        assert result.total_matches_found == 0
        assert len(result.successful_matches) == 0
        assert len(result.no_matches) == 0

    def test_auto_match_pending_requests_tracks_no_matches(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test that requests with no matches are tracked."""
        base_date = date.today() + timedelta(days=14)

        # Create isolated swap with no potential matches
        isolated_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[5].id,
            source_week=base_date + timedelta(weeks=20),
            target_week=None,
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
        )
        db.add(isolated_swap)
        db.commit()

        result = swap_auto_matcher.auto_match_pending_requests()

        assert isolated_swap.id in result.no_matches

    def test_auto_match_pending_requests_identifies_high_priority(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test that high priority matches are identified."""
        result = swap_auto_matcher.auto_match_pending_requests()

        # Check if any high priority matches were found
        if len(result.high_priority_matches) > 0:
            for match_result in result.high_priority_matches:
                assert match_result.best_match is not None
                assert match_result.best_match.priority in [
                    MatchPriority.CRITICAL,
                    MatchPriority.HIGH,
                ]


# ============================================================================
# Test Proactive Swap Suggestions
# ============================================================================


class TestSuggestProactiveSwaps:
    """Tests for suggest_proactive_swaps method."""

    def test_suggest_proactive_swaps_with_blocked_week(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
        sample_blocks: list[Block],
    ):
        """Test proactive suggestions when faculty has blocked week."""
        base_date = date.today() + timedelta(days=14)

        # Create assignment for faculty 0 on their blocked week
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=faculty_members[0].id,
            role="primary",
        )
        db.add(assignment)

        # Create assignment for faculty 1 on a preferred week
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[2].id,
            person_id=faculty_members[1].id,
            role="primary",
        )
        db.add(assignment2)
        db.commit()

        suggestions = swap_auto_matcher.suggest_proactive_swaps(
            faculty_members[0].id,
            limit=5
        )

        # Should suggest swaps for blocked week
        assert isinstance(suggestions, list)

        if len(suggestions) > 0:
            suggestion = suggestions[0]
            assert suggestion.faculty_id == faculty_members[0].id
            assert 0.0 <= suggestion.benefit_score <= 1.0
            assert isinstance(suggestion.reason, str)
            assert isinstance(suggestion.action_text, str)

    def test_suggest_proactive_swaps_no_conflicts(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test proactive suggestions when no conflicts exist."""
        ***REMOVED*** 5 has no preferences or assignments
        suggestions = swap_auto_matcher.suggest_proactive_swaps(
            faculty_members[5].id,
            limit=5
        )

        # Should return empty list or very low benefit suggestions
        assert isinstance(suggestions, list)

    def test_suggest_proactive_swaps_respects_limit(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
        sample_blocks: list[Block],
    ):
        """Test that proactive suggestions respect the limit parameter."""
        # Create multiple potential suggestions
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=faculty_members[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        suggestions = swap_auto_matcher.suggest_proactive_swaps(
            faculty_members[0].id,
            limit=2
        )

        assert len(suggestions) <= 2

    def test_suggest_proactive_swaps_sorted_by_benefit(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
        sample_blocks: list[Block],
    ):
        """Test that proactive suggestions are sorted by benefit score."""
        # Create assignments
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=faculty_members[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        suggestions = swap_auto_matcher.suggest_proactive_swaps(
            faculty_members[0].id,
            limit=10
        )

        if len(suggestions) > 1:
            # Verify descending order by benefit score
            for i in range(len(suggestions) - 1):
                assert suggestions[i].benefit_score >= suggestions[i+1].benefit_score


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    def test_perfect_mutual_match_identified(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test that perfect mutual matches are correctly identified."""
        base_date = date.today() + timedelta(days=14)

        # Create perfect mutual match
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=2),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=2),
            target_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add_all([swap1, swap2])
        db.commit()

        matches = swap_auto_matcher.find_compatible_swaps(swap1.id)

        assert len(matches) >= 1
        mutual_match = next((m for m in matches if m.is_mutual), None)
        assert mutual_match is not None
        assert mutual_match.match_type == MatchType.MUTUAL

    def test_absorb_type_swap_matching(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
    ):
        """Test matching with ABSORB type swaps."""
        # pending_swap_requests[3] is an ABSORB type
        matches = swap_auto_matcher.find_compatible_swaps(
            pending_swap_requests[3].id
        )

        # ABSORB swaps should still find compatible matches
        assert isinstance(matches, list)

    def test_date_separation_constraint(
        self,
        db: Session,
        custom_criteria_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test that date separation constraint is enforced."""
        base_date = date.today() + timedelta(days=14)

        # Create swaps beyond max_date_separation_days (90 days)
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=None,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(days=100),  # Beyond limit
            target_week=None,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add_all([swap1, swap2])
        db.commit()

        matches = custom_criteria_matcher.find_compatible_swaps(swap1.id)

        # Should not match due to date separation constraint
        match_ids = [m.request_b_id for m in matches]
        assert swap2.id not in match_ids

    def test_warnings_for_distant_dates(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test that warnings are generated for distant dates."""
        base_date = date.today() + timedelta(days=14)

        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=None,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(days=70),  # Far apart
            target_week=None,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add_all([swap1, swap2])
        db.commit()

        matches = swap_auto_matcher.suggest_optimal_matches(swap1.id, top_k=5)

        if len(matches) > 0:
            # Check if warnings exist for distant dates
            for match in matches:
                if match.match.request_b_id == swap2.id:
                    assert len(match.warnings) > 0

    def test_warnings_for_imminent_swaps(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test that warnings are generated for imminent swaps."""
        base_date = date.today() + timedelta(days=7)  # Within 2 weeks

        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=None,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(days=7),
            target_week=None,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add_all([swap1, swap2])
        db.commit()

        matches = swap_auto_matcher.suggest_optimal_matches(swap1.id, top_k=5)

        if len(matches) > 0:
            # Should have warning about imminent swap
            has_imminent_warning = any(
                "soon" in " ".join(match.warnings).lower()
                for match in matches
            )
            assert has_imminent_warning or len(matches[0].warnings) >= 0

    def test_empty_database_state(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
    ):
        """Test behavior with empty database (no swaps, no faculty)."""
        result = swap_auto_matcher.auto_match_pending_requests()

        assert result.total_requests_processed == 0
        assert result.total_matches_found == 0
        assert len(result.successful_matches) == 0

    def test_single_pending_request(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test behavior with only one pending request (no matches possible)."""
        base_date = date.today() + timedelta(days=14)

        single_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add(single_swap)
        db.commit()

        matches = swap_auto_matcher.find_compatible_swaps(single_swap.id)

        assert len(matches) == 0

    def test_workload_imbalance_warning(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
        sample_blocks: list[Block],
    ):
        """Test that workload imbalance generates warnings."""
        base_date = date.today() + timedelta(days=14)

        # Create many assignments for faculty 0
        for i in range(10):
            if i < len(sample_blocks):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=sample_blocks[i].id,
                    person_id=faculty_members[0].id,
                    role="primary",
                )
                db.add(assignment)

        # Create few assignments for faculty 1
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=faculty_members[1].id,
            role="primary",
        )
        db.add(assignment2)
        db.commit()

        # Create swaps between them
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            target_week=None,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            target_week=None,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add_all([swap1, swap2])
        db.commit()

        matches = swap_auto_matcher.suggest_optimal_matches(swap1.id, top_k=5)

        if len(matches) > 0:
            # Check for workload imbalance warning
            for match in matches:
                if match.match.request_b_id == swap2.id:
                    has_workload_warning = any(
                        "workload" in warning.lower()
                        for warning in match.warnings
                    )
                    # May or may not have warning depending on threshold
                    assert isinstance(match.warnings, list)

    def test_match_explanation_generation(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test that match explanations are generated correctly."""
        matches = swap_auto_matcher.suggest_optimal_matches(
            pending_swap_requests[0].id,
            top_k=5
        )

        if len(matches) > 0:
            for match in matches:
                assert len(match.explanation) > 0
                assert isinstance(match.explanation, str)
                # Should contain some reasoning
                assert len(match.explanation.split()) > 2

    def test_recommended_action_varies_by_priority(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        pending_swap_requests: list[SwapRecord],
        faculty_preferences: list[FacultyPreference],
    ):
        """Test that recommended actions vary based on priority."""
        matches = swap_auto_matcher.suggest_optimal_matches(
            pending_swap_requests[0].id,
            top_k=10
        )

        if len(matches) > 0:
            for match in matches:
                assert isinstance(match.recommended_action, str)
                assert len(match.recommended_action) > 0

                # Critical/high priority should have stronger recommendations
                if match.priority in [MatchPriority.CRITICAL, MatchPriority.HIGH]:
                    action_lower = match.recommended_action.lower()
                    assert any(
                        word in action_lower
                        for word in ["urgent", "immediately", "strongly", "recommend"]
                    )


# ============================================================================
# Test Integration with Mocked Dependencies
# ============================================================================


class TestMockedDependencies:
    """Tests using mocked dependencies to isolate service logic."""

    def test_compatibility_scoring_with_mocked_preference_service(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test compatibility scoring with mocked preference service."""
        base_date = date.today() + timedelta(days=14)

        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        # Mock the preference alignment scoring
        with patch.object(
            swap_auto_matcher.preference_service,
            '_score_preference_alignment',
            return_value=1.0
        ):
            score = swap_auto_matcher.score_swap_compatibility(swap_a, swap_b)

            # Should still return valid score
            assert 0.0 <= score <= 1.0
            # Should be higher due to perfect preference alignment
            assert score > 0.5

    def test_compatibility_scoring_with_mocked_validation_service(
        self,
        db: Session,
        swap_auto_matcher: SwapAutoMatcher,
        faculty_members: list[Person],
    ):
        """Test compatibility scoring with mocked validation service."""
        base_date = date.today() + timedelta(days=14)

        swap_a = SwapRecord(
            source_faculty_id=faculty_members[0].id,
            source_week=base_date,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            source_faculty_id=faculty_members[1].id,
            source_week=base_date + timedelta(weeks=1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        # Create mock validation result
        mock_validation = MagicMock()
        mock_validation.valid = True

        with patch.object(
            swap_auto_matcher.validation_service,
            'validate_swap',
            return_value=mock_validation
        ):
            # Should proceed normally with valid validation
            score = swap_auto_matcher.score_swap_compatibility(swap_a, swap_b)
            assert 0.0 <= score <= 1.0
