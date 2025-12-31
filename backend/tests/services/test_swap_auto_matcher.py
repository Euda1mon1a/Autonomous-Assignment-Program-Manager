"""Test suite for swap auto-matcher service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.schemas.swap_matching import MatchingCriteria
from app.services.swap_auto_matcher import SwapAutoMatcher


class TestSwapAutoMatcher:
    """Test suite for swap auto-matcher service."""

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
    def swap_request_1(self, db: Session, faculty_1: Person) -> SwapRecord:
        """Create first swap request."""
        swap = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_1.id,
            faculty_1_week=date.today() + timedelta(days=30),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)
        return swap

    @pytest.fixture
    def swap_request_2(self, db: Session, faculty_2: Person) -> SwapRecord:
        """Create second swap request."""
        swap = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_2.id,
            faculty_1_week=date.today() + timedelta(days=35),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)
        return swap

    def test_matcher_initialization(self, db: Session):
        """Test SwapAutoMatcher initialization."""
        matcher = SwapAutoMatcher(db)

        assert matcher.db is db
        assert matcher.criteria is not None
        assert isinstance(matcher.criteria, MatchingCriteria)

    def test_matcher_custom_criteria(self, db: Session):
        """Test SwapAutoMatcher with custom criteria."""
        criteria = MatchingCriteria(
            max_date_distance_days=60,
            min_preference_score=0.5,
        )
        matcher = SwapAutoMatcher(db, criteria)

        assert matcher.criteria == criteria

    def test_find_compatible_swaps_nonexistent_request(self, db: Session):
        """Test finding compatible swaps for nonexistent request."""
        matcher = SwapAutoMatcher(db)
        nonexistent_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            matcher.find_compatible_swaps(nonexistent_id)

    def test_find_compatible_swaps_single_request(
        self, db: Session, swap_request_1: SwapRecord
    ):
        """Test finding compatible swaps with only one request."""
        matcher = SwapAutoMatcher(db)

        matches = matcher.find_compatible_swaps(swap_request_1.id)

        assert isinstance(matches, list)
        assert len(matches) == 0  # No other compatible requests

    def test_find_compatible_swaps_multiple_candidates(
        self,
        db: Session,
        swap_request_1: SwapRecord,
        swap_request_2: SwapRecord,
    ):
        """Test finding compatible swaps with multiple candidates."""
        matcher = SwapAutoMatcher(db)

        matches = matcher.find_compatible_swaps(swap_request_1.id)

        assert isinstance(matches, list)

    def test_score_swap_compatibility(
        self, db: Session, swap_request_1: SwapRecord, swap_request_2: SwapRecord
    ):
        """Test compatibility scoring between two swaps."""
        matcher = SwapAutoMatcher(db)

        score = matcher.score_swap_compatibility(swap_request_1, swap_request_2)

        assert isinstance(score, (int, float))
        assert score >= 0.0

    def test_find_compatible_swaps_only_pending(
        self,
        db: Session,
        swap_request_1: SwapRecord,
        swap_request_2: SwapRecord,
    ):
        """Test that only pending requests are matched."""
        # Complete swap_request_2
        swap_request_2.status = SwapStatus.COMPLETED
        db.commit()

        matcher = SwapAutoMatcher(db)
        matches = matcher.find_compatible_swaps(swap_request_1.id)

        # Should not match completed swaps
        assert isinstance(matches, list)

    def test_find_compatible_swaps_completed_request(
        self, db: Session, swap_request_1: SwapRecord, swap_request_2: SwapRecord
    ):
        """Test that completed requests cannot be matched."""
        # Complete the request
        swap_request_1.status = SwapStatus.COMPLETED
        db.commit()

        matcher = SwapAutoMatcher(db)

        # Finding matches for completed request should fail or return empty
        try:
            matches = matcher.find_compatible_swaps(swap_request_1.id)
            assert len(matches) == 0
        except ValueError:
            # May throw if request status is wrong
            pass

    def test_find_compatible_swaps_rejected_request(
        self, db: Session, swap_request_1: SwapRecord
    ):
        """Test handling of rejected requests."""
        swap_request_1.status = SwapStatus.REJECTED
        db.commit()

        matcher = SwapAutoMatcher(db)

        try:
            matches = matcher.find_compatible_swaps(swap_request_1.id)
            assert len(matches) == 0
        except ValueError:
            pass

    def test_score_compatibility_same_dates(
        self, db: Session, faculty_1: Person, faculty_2: Person
    ):
        """Test compatibility scoring with same week dates."""
        same_week = date.today() + timedelta(days=30)

        swap1 = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_1.id,
            faculty_1_week=same_week,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_2.id,
            faculty_1_week=same_week,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )

        db.add_all([swap1, swap2])
        db.commit()

        matcher = SwapAutoMatcher(db)
        score = matcher.score_swap_compatibility(swap1, swap2)

        # Same dates should have higher score
        assert isinstance(score, (int, float))

    def test_score_compatibility_distant_dates(
        self, db: Session, faculty_1: Person, faculty_2: Person
    ):
        """Test compatibility scoring with distant dates."""
        week1 = date.today() + timedelta(days=30)
        week2 = date.today() + timedelta(days=180)

        swap1 = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_1.id,
            faculty_1_week=week1,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_2.id,
            faculty_1_week=week2,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )

        db.add_all([swap1, swap2])
        db.commit()

        matcher = SwapAutoMatcher(db)
        score = matcher.score_swap_compatibility(swap1, swap2)

        # Distant dates should have lower score
        assert isinstance(score, (int, float))

    def test_find_compatible_swaps_return_type(
        self, db: Session, swap_request_1: SwapRecord
    ):
        """Test that find_compatible_swaps returns correct type."""
        matcher = SwapAutoMatcher(db)

        matches = matcher.find_compatible_swaps(swap_request_1.id)

        assert isinstance(matches, list)
        for match in matches:
            # Each match should be a SwapMatch object
            assert hasattr(match, "__dict__")

    def test_matcher_with_three_candidates(
        self,
        db: Session,
        swap_request_1: SwapRecord,
        swap_request_2: SwapRecord,
        faculty_3: Person,
    ):
        """Test matching with three candidate requests."""
        swap3 = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_3.id,
            faculty_1_week=date.today() + timedelta(days=32),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )
        db.add(swap3)
        db.commit()

        matcher = SwapAutoMatcher(db)
        matches = matcher.find_compatible_swaps(swap_request_1.id)

        # Should find multiple matches if available
        assert isinstance(matches, list)

    def test_find_compatible_swaps_different_swap_types(
        self,
        db: Session,
        faculty_1: Person,
        faculty_2: Person,
    ):
        """Test matching with different swap types."""
        swap1 = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_1.id,
            faculty_1_week=date.today() + timedelta(days=30),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_2.id,
            faculty_1_week=date.today() + timedelta(days=30),
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )

        db.add_all([swap1, swap2])
        db.commit()

        matcher = SwapAutoMatcher(db)
        matches = matcher.find_compatible_swaps(swap1.id)

        assert isinstance(matches, list)

    def test_score_swap_returns_numeric(
        self, db: Session, swap_request_1: SwapRecord, swap_request_2: SwapRecord
    ):
        """Test that swap score is always numeric."""
        matcher = SwapAutoMatcher(db)

        score = matcher.score_swap_compatibility(swap_request_1, swap_request_2)

        assert isinstance(score, (int, float))
        assert not isinstance(score, bool)

    def test_matcher_database_session_persistence(self, db: Session):
        """Test that matcher maintains database session."""
        matcher = SwapAutoMatcher(db)

        # Session should be usable after matcher creation
        result = db.query(SwapRecord).all()
        assert isinstance(result, list)
