"""Tests for SwapRepository."""
import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.repositories.swap_repository import SwapRepository
from app.models.swap import SwapRecord, SwapApproval, SwapStatus, SwapType
from app.models.person import Person
from app.models.user import User


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def swap_repo(db: Session) -> SwapRepository:
    """Create a SwapRepository instance."""
    return SwapRepository(db)


@pytest.fixture
def faculty_a(db: Session) -> Person:
    """Create first faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty A",
        type="faculty",
        email="faculty.a@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def faculty_b(db: Session) -> Person:
    """Create second faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty B",
        type="faculty",
        email="faculty.b@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def faculty_c(db: Session) -> Person:
    """Create third faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Faculty C",
        type="faculty",
        email="faculty.c@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user for audit fields."""
    from app.core.security import get_password_hash

    user = User(
        id=uuid4(),
        username="testuser",
        email="testuser@test.org",
        hashed_password=get_password_hash("testpass"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# SwapRecord CRUD Tests
# ============================================================================

class TestSwapRepositoryCreate:
    """Tests for create() method."""

    def test_create_one_to_one_swap(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test creating a one-to-one swap."""
        source_week = date.today() + timedelta(days=14)
        target_week = date.today() + timedelta(days=21)

        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
            target_week=target_week,
            reason="TDY conflict",
            requested_by_id=test_user.id,
        )

        assert swap.id is not None
        assert swap.source_faculty_id == faculty_a.id
        assert swap.target_faculty_id == faculty_b.id
        assert swap.source_week == source_week
        assert swap.target_week == target_week
        assert swap.swap_type == SwapType.ONE_TO_ONE
        assert swap.status == SwapStatus.PENDING
        assert swap.reason == "TDY conflict"
        assert swap.requested_by_id == test_user.id
        assert swap.requested_at is not None

    def test_create_absorb_swap(self, swap_repo, faculty_a, faculty_b):
        """Test creating an absorb swap (no target week)."""
        source_week = date.today() + timedelta(days=14)

        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
            reason="Emergency coverage",
        )

        assert swap.id is not None
        assert swap.source_faculty_id == faculty_a.id
        assert swap.target_faculty_id == faculty_b.id
        assert swap.source_week == source_week
        assert swap.target_week is None
        assert swap.swap_type == SwapType.ABSORB
        assert swap.status == SwapStatus.PENDING

    def test_create_minimal_swap(self, swap_repo, faculty_a, faculty_b):
        """Test creating swap with minimal required fields."""
        source_week = date.today() + timedelta(days=7)

        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=source_week,
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        assert swap.id is not None
        assert swap.status == SwapStatus.PENDING
        assert swap.requested_at is not None
        assert swap.reason is None
        assert swap.requested_by_id is None


class TestSwapRepositoryGetById:
    """Tests for get_by_id() method."""

    def test_get_existing_swap(self, swap_repo, faculty_a, faculty_b):
        """Test retrieving an existing swap by ID."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        retrieved = swap_repo.get_by_id(swap.id)

        assert retrieved is not None
        assert retrieved.id == swap.id
        assert retrieved.source_faculty_id == faculty_a.id

    def test_get_nonexistent_swap(self, swap_repo):
        """Test retrieving a non-existent swap returns None."""
        fake_id = uuid4()
        result = swap_repo.get_by_id(fake_id)

        assert result is None


class TestSwapRepositoryUpdateStatus:
    """Tests for update_status() method."""

    def test_update_to_approved(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test updating swap status to APPROVED."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        updated = swap_repo.update_status(
            swap_id=swap.id,
            status=SwapStatus.APPROVED,
            user_id=test_user.id,
        )

        assert updated is not None
        assert updated.status == SwapStatus.APPROVED
        assert updated.approved_at is not None
        assert updated.approved_by_id == test_user.id

    def test_update_to_executed(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test updating swap status to EXECUTED."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        updated = swap_repo.update_status(
            swap_id=swap.id,
            status=SwapStatus.EXECUTED,
            user_id=test_user.id,
        )

        assert updated is not None
        assert updated.status == SwapStatus.EXECUTED
        assert updated.executed_at is not None
        assert updated.executed_by_id == test_user.id

    def test_update_to_rolled_back(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test updating swap status to ROLLED_BACK."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        # First execute it
        swap_repo.update_status(swap.id, SwapStatus.EXECUTED, test_user.id)

        # Then roll it back
        updated = swap_repo.update_status(
            swap_id=swap.id,
            status=SwapStatus.ROLLED_BACK,
            user_id=test_user.id,
        )

        assert updated is not None
        assert updated.status == SwapStatus.ROLLED_BACK
        assert updated.rolled_back_at is not None
        assert updated.rolled_back_by_id == test_user.id

    def test_update_to_rejected(self, swap_repo, faculty_a, faculty_b):
        """Test updating swap status to REJECTED."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        updated = swap_repo.update_status(
            swap_id=swap.id,
            status=SwapStatus.REJECTED,
        )

        assert updated is not None
        assert updated.status == SwapStatus.REJECTED

    def test_update_nonexistent_swap(self, swap_repo):
        """Test updating a non-existent swap returns None."""
        fake_id = uuid4()
        result = swap_repo.update_status(fake_id, SwapStatus.APPROVED)

        assert result is None


class TestSwapRepositoryDelete:
    """Tests for delete() method."""

    def test_delete_existing_swap(self, swap_repo, faculty_a, faculty_b):
        """Test deleting an existing swap."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        result = swap_repo.delete(swap.id)

        assert result is True
        assert swap_repo.get_by_id(swap.id) is None

    def test_delete_nonexistent_swap(self, swap_repo):
        """Test deleting a non-existent swap returns False."""
        fake_id = uuid4()
        result = swap_repo.delete(fake_id)

        assert result is False


# ============================================================================
# Query Methods Tests
# ============================================================================

class TestSwapRepositoryFindByFaculty:
    """Tests for find_by_faculty() method."""

    def test_find_as_source(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test finding swaps where faculty is the source."""
        # Create swap with faculty_a as source
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        # Create swap with faculty_b as source
        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_c.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        # Find swaps where faculty_a is source
        results = swap_repo.find_by_faculty(faculty_a.id, as_source=True, as_target=False)

        assert len(results) == 1
        assert results[0].id == swap1.id

    def test_find_as_target(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test finding swaps where faculty is the target."""
        # Create swap with faculty_b as target
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        # Create swap with faculty_c as target
        swap2 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_c.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        # Find swaps where faculty_b is target
        results = swap_repo.find_by_faculty(faculty_b.id, as_source=False, as_target=True)

        assert len(results) == 1
        assert results[0].id == swap1.id

    def test_find_as_both(self, swap_repo, faculty_a, faculty_b):
        """Test finding swaps where faculty is either source or target."""
        # Create swaps
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_a.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        # Find all swaps involving faculty_a
        results = swap_repo.find_by_faculty(faculty_a.id, as_source=True, as_target=True)

        assert len(results) == 2
        swap_ids = {s.id for s in results}
        assert swap1.id in swap_ids
        assert swap2.id in swap_ids

    def test_find_with_neither_flag(self, swap_repo, faculty_a, faculty_b):
        """Test finding with both flags False returns empty list."""
        swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_by_faculty(faculty_a.id, as_source=False, as_target=False)

        assert len(results) == 0

    def test_find_ordered_by_requested_at(self, swap_repo, faculty_a, faculty_b):
        """Test results are ordered by requested_at descending."""
        # Create multiple swaps
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        swap2 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_by_faculty(faculty_a.id)

        assert len(results) == 2
        # Most recent should be first
        assert results[0].id == swap2.id
        assert results[1].id == swap1.id


class TestSwapRepositoryFindByStatus:
    """Tests for find_by_status() method."""

    def test_find_pending_swaps(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test finding swaps by PENDING status."""
        # Create swaps with different statuses
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_c.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap2.id, SwapStatus.APPROVED)

        results = swap_repo.find_by_status(SwapStatus.PENDING)

        assert len(results) == 1
        assert results[0].id == swap1.id

    def test_find_executed_swaps(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test finding swaps by EXECUTED status."""
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap1.id, SwapStatus.EXECUTED, test_user.id)

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_a.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_by_status(SwapStatus.EXECUTED)

        assert len(results) == 1
        assert results[0].id == swap1.id

    def test_find_by_status_with_faculty_filter(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test finding swaps by status filtered by faculty."""
        # Create pending swaps
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_c.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        # Find pending swaps involving faculty_a
        results = swap_repo.find_by_status(SwapStatus.PENDING, faculty_id=faculty_a.id)

        assert len(results) == 1
        assert results[0].id == swap1.id

    def test_find_by_status_no_results(self, swap_repo, faculty_a, faculty_b):
        """Test finding swaps when no matches exist."""
        swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_by_status(SwapStatus.REJECTED)

        assert len(results) == 0


class TestSwapRepositoryFindByWeek:
    """Tests for find_by_week() method."""

    def test_find_by_source_week(self, swap_repo, faculty_a, faculty_b):
        """Test finding swaps by source week."""
        week1 = date.today() + timedelta(days=7)
        week2 = date.today() + timedelta(days=14)

        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=week1,
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
            target_week=week2,
        )

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=week2,
            target_faculty_id=faculty_a.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_by_week(week1)

        assert len(results) == 1
        assert results[0].id == swap1.id

    def test_find_by_target_week(self, swap_repo, faculty_a, faculty_b):
        """Test finding swaps by target week."""
        week1 = date.today() + timedelta(days=7)
        week2 = date.today() + timedelta(days=14)

        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=week1,
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
            target_week=week2,
        )

        results = swap_repo.find_by_week(week2)

        assert len(results) == 1
        assert results[0].id == swap.id

    def test_find_by_week_with_faculty_filter(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test finding swaps by week filtered by faculty."""
        week = date.today() + timedelta(days=7)

        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=week,
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=week,
            target_faculty_id=faculty_c.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_by_week(week, faculty_id=faculty_a.id)

        assert len(results) == 1
        assert results[0].id == swap1.id

    def test_find_by_week_no_results(self, swap_repo, faculty_a, faculty_b):
        """Test finding swaps for a week with no swaps."""
        week1 = date.today() + timedelta(days=7)
        week2 = date.today() + timedelta(days=14)

        swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=week1,
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_by_week(week2)

        assert len(results) == 0


class TestSwapRepositoryFindPendingForFaculty:
    """Tests for find_pending_for_faculty() method."""

    def test_find_pending_as_target(self, swap_repo, faculty_a, faculty_b):
        """Test finding pending swaps where faculty is target."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_pending_for_faculty(faculty_b.id)

        assert len(results) == 1
        assert results[0].id == swap.id

    def test_find_pending_excludes_source(self, swap_repo, faculty_a, faculty_b):
        """Test pending swaps where faculty is source are excluded."""
        swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        results = swap_repo.find_pending_for_faculty(faculty_a.id)

        assert len(results) == 0

    def test_find_pending_excludes_non_pending(self, swap_repo, faculty_a, faculty_b):
        """Test non-pending swaps are excluded."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap.id, SwapStatus.APPROVED)

        results = swap_repo.find_pending_for_faculty(faculty_b.id)

        assert len(results) == 0


class TestSwapRepositoryFindRecent:
    """Tests for find_recent() method."""

    def test_find_recent_executed(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test finding recent executed swaps."""
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap1.id, SwapStatus.EXECUTED, test_user.id)

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_a.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        # Leave swap2 as PENDING

        results = swap_repo.find_recent()

        assert len(results) == 1
        assert results[0].id == swap1.id

    def test_find_recent_with_limit(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test finding recent swaps with limit."""
        for i in range(5):
            swap = swap_repo.create(
                source_faculty_id=faculty_a.id,
                source_week=date.today() + timedelta(days=7 + i),
                target_faculty_id=faculty_b.id,
                swap_type=SwapType.ONE_TO_ONE,
            )
            swap_repo.update_status(swap.id, SwapStatus.EXECUTED, test_user.id)

        results = swap_repo.find_recent(limit=3)

        assert len(results) == 3

    def test_find_recent_with_faculty_filter(self, swap_repo, faculty_a, faculty_b, faculty_c, test_user):
        """Test finding recent swaps filtered by faculty."""
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap1.id, SwapStatus.EXECUTED, test_user.id)

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_c.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap2.id, SwapStatus.EXECUTED, test_user.id)

        results = swap_repo.find_recent(faculty_id=faculty_a.id)

        assert len(results) == 1
        assert results[0].id == swap1.id


class TestSwapRepositoryFindWithPagination:
    """Tests for find_with_pagination() method."""

    def test_pagination_basic(self, swap_repo, faculty_a, faculty_b):
        """Test basic pagination."""
        # Create 25 swaps
        for i in range(25):
            swap_repo.create(
                source_faculty_id=faculty_a.id,
                source_week=date.today() + timedelta(days=i),
                target_faculty_id=faculty_b.id,
                swap_type=SwapType.ONE_TO_ONE,
            )

        # Get first page (20 items)
        records, total = swap_repo.find_with_pagination(page=1, page_size=20)

        assert len(records) == 20
        assert total == 25

    def test_pagination_second_page(self, swap_repo, faculty_a, faculty_b):
        """Test getting second page of results."""
        # Create 25 swaps
        for i in range(25):
            swap_repo.create(
                source_faculty_id=faculty_a.id,
                source_week=date.today() + timedelta(days=i),
                target_faculty_id=faculty_b.id,
                swap_type=SwapType.ONE_TO_ONE,
            )

        # Get second page
        records, total = swap_repo.find_with_pagination(page=2, page_size=20)

        assert len(records) == 5
        assert total == 25

    def test_pagination_with_faculty_filter(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test pagination with faculty filter."""
        # Create swaps for faculty_a
        for i in range(10):
            swap_repo.create(
                source_faculty_id=faculty_a.id,
                source_week=date.today() + timedelta(days=i),
                target_faculty_id=faculty_b.id,
                swap_type=SwapType.ONE_TO_ONE,
            )

        # Create swaps for faculty_c
        for i in range(5):
            swap_repo.create(
                source_faculty_id=faculty_c.id,
                source_week=date.today() + timedelta(days=i),
                target_faculty_id=faculty_b.id,
                swap_type=SwapType.ONE_TO_ONE,
            )

        records, total = swap_repo.find_with_pagination(faculty_id=faculty_a.id, page_size=20)

        assert len(records) == 10
        assert total == 10

    def test_pagination_with_status_filter(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test pagination with status filter."""
        # Create swaps with different statuses
        for i in range(5):
            swap = swap_repo.create(
                source_faculty_id=faculty_a.id,
                source_week=date.today() + timedelta(days=i),
                target_faculty_id=faculty_b.id,
                swap_type=SwapType.ONE_TO_ONE,
            )
            if i < 3:
                swap_repo.update_status(swap.id, SwapStatus.EXECUTED, test_user.id)

        records, total = swap_repo.find_with_pagination(status=SwapStatus.EXECUTED)

        assert len(records) == 3
        assert total == 3

    def test_pagination_with_date_filters(self, swap_repo, faculty_a, faculty_b):
        """Test pagination with date range filters."""
        start_date = date.today()

        # Create swaps across different dates
        for i in range(10):
            swap_repo.create(
                source_faculty_id=faculty_a.id,
                source_week=start_date + timedelta(days=i * 7),
                target_faculty_id=faculty_b.id,
                swap_type=SwapType.ONE_TO_ONE,
            )

        # Filter to first 4 weeks
        records, total = swap_repo.find_with_pagination(
            start_date=start_date,
            end_date=start_date + timedelta(days=21),
        )

        assert len(records) == 4
        assert total == 4

    def test_pagination_empty_result(self, swap_repo, faculty_a):
        """Test pagination with no results."""
        records, total = swap_repo.find_with_pagination(faculty_id=faculty_a.id)

        assert len(records) == 0
        assert total == 0


# ============================================================================
# Approval Methods Tests
# ============================================================================

class TestSwapRepositoryApprovals:
    """Tests for approval-related methods."""

    def test_create_approval(self, swap_repo, faculty_a, faculty_b):
        """Test creating an approval record."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
        )

        approval = swap_repo.create_approval(
            swap_id=swap.id,
            faculty_id=faculty_b.id,
            role="target",
        )

        assert approval.id is not None
        assert approval.swap_id == swap.id
        assert approval.faculty_id == faculty_b.id
        assert approval.role == "target"
        assert approval.approved is None

    def test_get_approvals(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test getting all approvals for a swap."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
        )

        approval1 = swap_repo.create_approval(swap.id, faculty_b.id, "target")
        approval2 = swap_repo.create_approval(swap.id, faculty_c.id, "admin")

        approvals = swap_repo.get_approvals(swap.id)

        assert len(approvals) == 2
        approval_ids = {a.id for a in approvals}
        assert approval1.id in approval_ids
        assert approval2.id in approval_ids

    def test_record_approval_response_approved(self, swap_repo, faculty_a, faculty_b):
        """Test recording an approval response."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
        )

        approval = swap_repo.create_approval(swap.id, faculty_b.id, "target")

        updated = swap_repo.record_approval_response(
            approval_id=approval.id,
            approved=True,
            notes="Happy to help!",
        )

        assert updated is not None
        assert updated.approved is True
        assert updated.responded_at is not None
        assert updated.response_notes == "Happy to help!"

    def test_record_approval_response_rejected(self, swap_repo, faculty_a, faculty_b):
        """Test recording a rejection response."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
        )

        approval = swap_repo.create_approval(swap.id, faculty_b.id, "target")

        updated = swap_repo.record_approval_response(
            approval_id=approval.id,
            approved=False,
            notes="Already committed that week",
        )

        assert updated is not None
        assert updated.approved is False
        assert updated.response_notes == "Already committed that week"

    def test_record_approval_response_nonexistent(self, swap_repo):
        """Test recording response for non-existent approval."""
        fake_id = uuid4()
        result = swap_repo.record_approval_response(fake_id, approved=True)

        assert result is None

    def test_is_fully_approved_true(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test checking if all approvals are granted."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
        )

        approval1 = swap_repo.create_approval(swap.id, faculty_b.id, "target")
        approval2 = swap_repo.create_approval(swap.id, faculty_c.id, "admin")

        swap_repo.record_approval_response(approval1.id, approved=True)
        swap_repo.record_approval_response(approval2.id, approved=True)

        assert swap_repo.is_fully_approved(swap.id) is True

    def test_is_fully_approved_false_pending(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test not fully approved when some pending."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
        )

        approval1 = swap_repo.create_approval(swap.id, faculty_b.id, "target")
        approval2 = swap_repo.create_approval(swap.id, faculty_c.id, "admin")

        swap_repo.record_approval_response(approval1.id, approved=True)
        # approval2 left pending

        assert swap_repo.is_fully_approved(swap.id) is False

    def test_is_fully_approved_false_rejected(self, swap_repo, faculty_a, faculty_b):
        """Test not fully approved when one is rejected."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
        )

        approval = swap_repo.create_approval(swap.id, faculty_b.id, "target")
        swap_repo.record_approval_response(approval.id, approved=False)

        assert swap_repo.is_fully_approved(swap.id) is False

    def test_is_fully_approved_no_approvals(self, swap_repo, faculty_a, faculty_b):
        """Test not fully approved when no approvals exist."""
        swap = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ABSORB,
        )

        assert swap_repo.is_fully_approved(swap.id) is False


# ============================================================================
# Statistics Methods Tests
# ============================================================================

class TestSwapRepositoryStatistics:
    """Tests for statistics methods."""

    def test_count_by_status_all(self, swap_repo, faculty_a, faculty_b, test_user):
        """Test counting swaps by status."""
        # Create swaps with different statuses
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        swap2 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap2.id, SwapStatus.APPROVED, test_user.id)

        swap3 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=21),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap3.id, SwapStatus.EXECUTED, test_user.id)

        counts = swap_repo.count_by_status()

        assert counts["pending"] == 1
        assert counts["approved"] == 1
        assert counts["executed"] == 1

    def test_count_by_status_with_faculty_filter(self, swap_repo, faculty_a, faculty_b, faculty_c):
        """Test counting swaps by status filtered by faculty."""
        # Create swaps for faculty_a
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        # Create swap for faculty_c
        swap2 = swap_repo.create(
            source_faculty_id=faculty_c.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )

        counts = swap_repo.count_by_status(faculty_id=faculty_a.id)

        assert counts["pending"] == 1
        assert "rejected" not in counts

    def test_count_executed_for_faculty(self, swap_repo, faculty_a, faculty_b, faculty_c, test_user):
        """Test counting executed swaps for a faculty member."""
        # Create and execute swaps
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap1.id, SwapStatus.EXECUTED, test_user.id)

        swap2 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_a.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap2.id, SwapStatus.EXECUTED, test_user.id)

        # Swap not involving faculty_a
        swap3 = swap_repo.create(
            source_faculty_id=faculty_b.id,
            source_week=date.today() + timedelta(days=21),
            target_faculty_id=faculty_c.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap3.id, SwapStatus.EXECUTED, test_user.id)

        count = swap_repo.count_executed_for_faculty(faculty_a.id)

        assert count == 2

    def test_count_executed_with_date_range(self, swap_repo, faculty_a, faculty_b, test_user, db):
        """Test counting executed swaps with date range filter."""
        # Create swaps and manually set executed_at
        swap1 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=7),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap1.id, SwapStatus.EXECUTED, test_user.id)

        # Manually update executed_at to be in the past
        old_date = datetime.utcnow() - timedelta(days=60)
        swap1.executed_at = old_date
        db.commit()

        swap2 = swap_repo.create(
            source_faculty_id=faculty_a.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=faculty_b.id,
            swap_type=SwapType.ONE_TO_ONE,
        )
        swap_repo.update_status(swap2.id, SwapStatus.EXECUTED, test_user.id)

        # Count only recent (last 30 days)
        start_date = date.today() - timedelta(days=30)
        count = swap_repo.count_executed_for_faculty(
            faculty_a.id,
            start_date=start_date,
        )

        assert count == 1

    def test_count_by_status_empty(self, swap_repo):
        """Test counting when no swaps exist."""
        counts = swap_repo.count_by_status()

        assert counts == {}

    def test_count_executed_zero(self, swap_repo, faculty_a):
        """Test counting executed swaps when none exist."""
        count = swap_repo.count_executed_for_faculty(faculty_a.id)

        assert count == 0
