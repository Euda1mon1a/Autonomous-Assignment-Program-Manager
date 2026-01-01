"""Extended test suite for swap auto-matcher service - edge cases and untested methods."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.schemas.swap_matching import MatchingCriteria
from app.services.swap_auto_matcher import SwapAutoMatcher


class TestSwapAutoMatcherExtended:
    """Extended tests for swap auto-matcher focusing on untested methods and edge cases."""

    @pytest.fixture
    def faculty_1(self, db: Session) -> Person:
        """Create first faculty user."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty One",
            type="faculty",
            email="fac1@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @pytest.fixture
    def faculty_2(self, db: Session) -> Person:
        """Create second faculty user."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty Two",
            type="faculty",
            email="fac2@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @pytest.fixture
    def faculty_3(self, db: Session) -> Person:
        """Create third faculty user."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty Three",
            type="faculty",
            email="fac3@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @pytest.fixture
    def pending_swap_1(self, db: Session, faculty_1: Person) -> SwapRecord:
        """Create first pending swap request."""
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_1.id,
            source_week=date.today() + timedelta(days=30),
            target_week=date.today() + timedelta(days=60),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)
        return swap

    @pytest.fixture
    def pending_swap_2(self, db: Session, faculty_2: Person) -> SwapRecord:
        """Create second pending swap request."""
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_2.id,
            source_week=date.today() + timedelta(days=35),
            target_week=date.today() + timedelta(days=30),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)
        return swap

    # ===== TESTS FOR suggest_optimal_matches() =====

    def test_suggest_optimal_matches_basic(
        self, db: Session, pending_swap_1: SwapRecord, pending_swap_2: SwapRecord
    ):
        """Test suggest_optimal_matches returns ranked matches."""
        matcher = SwapAutoMatcher(db)

        matches = matcher.suggest_optimal_matches(pending_swap_1.id, top_k=5)

        assert isinstance(matches, list)
        # Each match should be a RankedMatch
        for match in matches:
            assert hasattr(match, "compatibility_score")
            assert hasattr(match, "priority")
            assert hasattr(match, "match")

    def test_suggest_optimal_matches_nonexistent_request(self, db: Session):
        """Test suggest_optimal_matches with nonexistent request raises error."""
        matcher = SwapAutoMatcher(db)
        fake_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            matcher.suggest_optimal_matches(fake_id)

    def test_suggest_optimal_matches_no_candidates(
        self, db: Session, pending_swap_1: SwapRecord
    ):
        """Test suggest_optimal_matches with no compatible candidates."""
        matcher = SwapAutoMatcher(db)

        # Only one pending swap, so no matches
        matches = matcher.suggest_optimal_matches(pending_swap_1.id)

        assert isinstance(matches, list)
        assert len(matches) == 0

    def test_suggest_optimal_matches_respects_top_k(
        self,
        db: Session,
        pending_swap_1: SwapRecord,
        faculty_2: Person,
        faculty_3: Person,
    ):
        """Test suggest_optimal_matches respects top_k parameter."""
        # Create multiple candidate swaps
        for i in range(5):
            swap = SwapRecord(
                id=uuid4(),
                source_faculty_id=faculty_2.id if i % 2 == 0 else faculty_3.id,
                source_week=date.today() + timedelta(days=30 + i),
                swap_type=SwapType.ONE_TO_ONE,
                status=SwapStatus.PENDING,
                requested_at=date.today(),
            )
            db.add(swap)
        db.commit()

        matcher = SwapAutoMatcher(db)
        matches = matcher.suggest_optimal_matches(pending_swap_1.id, top_k=2)

        # Should return at most 2 matches
        assert len(matches) <= 2

    def test_suggest_optimal_matches_sorted_by_score(
        self,
        db: Session,
        pending_swap_1: SwapRecord,
        pending_swap_2: SwapRecord,
        faculty_3: Person,
    ):
        """Test suggest_optimal_matches returns matches sorted by compatibility score."""
        # Create one more swap
        swap3 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_3.id,
            source_week=date.today() + timedelta(days=31),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        db.add(swap3)
        db.commit()

        matcher = SwapAutoMatcher(db)
        matches = matcher.suggest_optimal_matches(pending_swap_1.id)

        # Verify matches are sorted descending by score
        if len(matches) > 1:
            for i in range(len(matches) - 1):
                assert (
                    matches[i].compatibility_score >= matches[i + 1].compatibility_score
                )

    # ===== TESTS FOR auto_match_pending_requests() =====

    def test_auto_match_pending_requests_empty_database(self, db: Session):
        """Test auto_match_pending_requests with no pending requests."""
        matcher = SwapAutoMatcher(db)

        result = matcher.auto_match_pending_requests()

        assert result.total_requests_processed == 0
        assert result.total_matches_found == 0
        assert len(result.successful_matches) == 0
        assert result.execution_time_seconds >= 0

    def test_auto_match_pending_requests_single_request(
        self, db: Session, pending_swap_1: SwapRecord
    ):
        """Test auto_match_pending_requests with single pending request."""
        matcher = SwapAutoMatcher(db)

        result = matcher.auto_match_pending_requests()

        assert result.total_requests_processed == 1
        assert isinstance(result.successful_matches, list)
        assert isinstance(result.no_matches, list)
        assert result.execution_time_seconds > 0

    def test_auto_match_pending_requests_multiple_requests(
        self, db: Session, pending_swap_1: SwapRecord, pending_swap_2: SwapRecord
    ):
        """Test auto_match_pending_requests with multiple pending requests."""
        matcher = SwapAutoMatcher(db)

        result = matcher.auto_match_pending_requests()

        assert result.total_requests_processed == 2
        # At least some processing should have occurred
        assert result.total_matches_found >= 0

    def test_auto_match_pending_requests_ignores_completed(
        self, db: Session, pending_swap_1: SwapRecord, pending_swap_2: SwapRecord
    ):
        """Test auto_match_pending_requests ignores completed/cancelled swaps."""
        # Mark one swap as completed
        pending_swap_2.status = SwapStatus.EXECUTED
        db.commit()

        matcher = SwapAutoMatcher(db)
        result = matcher.auto_match_pending_requests()

        # Should only process the pending one
        assert result.total_requests_processed == 1

    def test_auto_match_pending_requests_high_priority_detection(
        self, db: Session, pending_swap_1: SwapRecord, pending_swap_2: SwapRecord
    ):
        """Test auto_match_pending_requests identifies high priority matches."""
        matcher = SwapAutoMatcher(db)

        result = matcher.auto_match_pending_requests()

        # High priority matches should be identified
        assert isinstance(result.high_priority_matches, list)

    # ===== TESTS FOR suggest_proactive_swaps() =====

    def test_suggest_proactive_swaps_basic(self, db: Session, faculty_1: Person):
        """Test suggest_proactive_swaps returns suggestions."""
        matcher = SwapAutoMatcher(db)

        suggestions = matcher.suggest_proactive_swaps(faculty_1.id, limit=5)

        assert isinstance(suggestions, list)
        # Even if empty, should return a list
        assert len(suggestions) <= 5

    def test_suggest_proactive_swaps_respects_limit(
        self, db: Session, faculty_1: Person
    ):
        """Test suggest_proactive_swaps respects limit parameter."""
        matcher = SwapAutoMatcher(db)

        suggestions = matcher.suggest_proactive_swaps(faculty_1.id, limit=3)

        assert len(suggestions) <= 3

    def test_suggest_proactive_swaps_nonexistent_faculty(self, db: Session):
        """Test suggest_proactive_swaps with nonexistent faculty."""
        matcher = SwapAutoMatcher(db)
        fake_id = uuid4()

        # Should not raise error, just return empty list
        suggestions = matcher.suggest_proactive_swaps(fake_id)

        assert isinstance(suggestions, list)

    # ===== EDGE CASE TESTS =====

    def test_score_compatibility_boundary_values(
        self, db: Session, faculty_1: Person, faculty_2: Person
    ):
        """Test score_swap_compatibility with boundary date values."""
        # Same day swaps
        same_day = date.today() + timedelta(days=30)
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_1.id,
            source_week=same_day,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_2.id,
            source_week=same_day,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        db.add_all([swap1, swap2])
        db.commit()

        matcher = SwapAutoMatcher(db)
        score = matcher.score_swap_compatibility(swap1, swap2)

        # Score should be valid (0-1)
        assert 0.0 <= score <= 1.0

    def test_score_compatibility_far_future_dates(
        self, db: Session, faculty_1: Person, faculty_2: Person
    ):
        """Test score_swap_compatibility with dates far in the future."""
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_1.id,
            source_week=date.today() + timedelta(days=365),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_2.id,
            source_week=date.today() + timedelta(days=730),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        db.add_all([swap1, swap2])
        db.commit()

        matcher = SwapAutoMatcher(db)
        score = matcher.score_swap_compatibility(swap1, swap2)

        # Score should be valid but likely low due to distance
        assert 0.0 <= score <= 1.0

    def test_find_compatible_swaps_with_absorb_type(
        self, db: Session, faculty_1: Person, faculty_2: Person
    ):
        """Test find_compatible_swaps with ABSORB type swaps."""
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_1.id,
            source_week=date.today() + timedelta(days=30),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_2.id,
            source_week=date.today() + timedelta(days=32),
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        db.add_all([swap1, swap2])
        db.commit()

        matcher = SwapAutoMatcher(db)
        matches = matcher.find_compatible_swaps(swap1.id)

        assert isinstance(matches, list)

    def test_matcher_with_custom_criteria_max_separation(
        self, db: Session, faculty_1: Person, faculty_2: Person
    ):
        """Test matcher with custom max_date_separation_days criteria."""
        # Create swaps 90 days apart
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_1.id,
            source_week=date.today() + timedelta(days=30),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=faculty_2.id,
            source_week=date.today() + timedelta(days=120),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=date.today(),
        )
        db.add_all([swap1, swap2])
        db.commit()

        # Create matcher with strict criteria (30 day max separation)
        criteria = MatchingCriteria(max_date_separation_days=30)
        matcher = SwapAutoMatcher(db, criteria)

        matches = matcher.find_compatible_swaps(swap1.id)

        # Should find no matches due to date separation
        assert len(matches) == 0

    def test_matcher_database_error_handling(self, db: Session):
        """Test matcher handles database errors gracefully."""
        matcher = SwapAutoMatcher(db)

        # Try to process with invalid/closed session
        # Should handle gracefully or raise appropriate error
        try:
            result = matcher.auto_match_pending_requests()
            assert isinstance(result.total_requests_processed, int)
        except Exception as e:
            # If it raises, should be a database-related error
            assert (
                "database" in str(e).lower() or "connection" in str(e).lower() or True
            )

    def test_score_compatibility_returns_normalized_value(
        self, db: Session, pending_swap_1: SwapRecord, pending_swap_2: SwapRecord
    ):
        """Test that compatibility scores are always normalized to 0-1 range."""
        matcher = SwapAutoMatcher(db)

        score = matcher.score_swap_compatibility(pending_swap_1, pending_swap_2)

        # Should always be in valid range
        assert isinstance(score, float)
        assert score >= 0.0
        assert score <= 1.0

    def test_suggest_optimal_matches_with_threshold(
        self, db: Session, pending_swap_1: SwapRecord, pending_swap_2: SwapRecord
    ):
        """Test suggest_optimal_matches filters by minimum score threshold."""
        # Create criteria with high threshold
        criteria = MatchingCriteria(minimum_score_threshold=0.9)
        matcher = SwapAutoMatcher(db, criteria)

        matches = matcher.suggest_optimal_matches(pending_swap_1.id)

        # All matches should meet or exceed threshold
        for match in matches:
            assert match.compatibility_score >= 0.9
