"""Tests for Call Assignment Service.

This module tests the call assignment service which handles
on-call scheduling with async SQLAlchemy 2.0 patterns.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.services.call_assignment_service import CallAssignmentService


# ============================================================================
# Async Database Fixture
# ============================================================================


@pytest.fixture
async def async_db():
    """Create in-memory async test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def sample_resident_async(async_db: AsyncSession) -> Person:
    """Create a sample resident for async tests."""
    resident = Person(
        id=uuid4(),
        name="Dr. Test Resident",
        type="resident",
        email="test.resident@hospital.org",
        pgy_level=2,
    )
    async_db.add(resident)
    await async_db.commit()
    await async_db.refresh(resident)
    return resident


@pytest.fixture
async def sample_faculty_async(async_db: AsyncSession) -> Person:
    """Create a sample faculty member for async tests."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Test Faculty",
        type="faculty",
        email="test.faculty@hospital.org",
        performs_procedures=True,
    )
    async_db.add(faculty)
    await async_db.commit()
    await async_db.refresh(faculty)
    return faculty


class TestCallAssignmentService:
    """Test suite for call assignment service."""

    # =========================================================================
    # Retrieval Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_call_assignment_not_found(self, async_db):
        """Test retrieving a non-existent call assignment returns None."""
        service = CallAssignmentService(async_db)
        assignment = await service.get_call_assignment(uuid4())
        assert assignment is None

    @pytest.mark.asyncio
    async def test_get_call_assignment_success(
        self, async_db, sample_resident_async, sample_faculty_async
    ):
        """Test retrieving a call assignment by ID."""
        service = CallAssignmentService(async_db)

        # Create a call assignment
        from app.schemas.call_assignment import CallAssignmentCreate

        create_data = CallAssignmentCreate(
            person_id=sample_resident_async.id,
            date=date.today() + timedelta(days=1),
            call_type="overnight",
            supervisor_id=sample_faculty_async.id,
        )

        created = await service.create_call_assignment(create_data)
        assert created is not None
        assert created.id is not None

        # Retrieve it
        retrieved = await service.get_call_assignment(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.person_id == sample_resident_async.id
        # Person should be eagerly loaded
        assert retrieved.person is not None
        assert retrieved.person.name == sample_resident_async.name

    @pytest.mark.asyncio
    async def test_get_call_assignments_empty(self, async_db):
        """Test retrieving call assignments when none exist."""
        service = CallAssignmentService(async_db)
        result = await service.get_call_assignments()

        assert isinstance(result, dict)
        assert "items" in result
        assert "total" in result
        assert result["total"] == 0
        assert len(result["items"]) == 0

    @pytest.mark.asyncio
    async def test_get_call_assignments_by_date_range(
        self, async_db, sample_resident_async, sample_faculty_async
    ):
        """Test retrieving call assignments by date range."""
        service = CallAssignmentService(async_db)

        # Create assignments on different dates
        from app.schemas.call_assignment import CallAssignmentCreate

        date1 = date.today() + timedelta(days=1)
        date2 = date.today() + timedelta(days=5)
        date3 = date.today() + timedelta(days=10)

        await service.create_call_assignment(
            CallAssignmentCreate(
                person_id=sample_resident_async.id,
                date=date1,
                call_type="overnight",
                supervisor_id=sample_faculty_async.id,
            )
        )
        await service.create_call_assignment(
            CallAssignmentCreate(
                person_id=sample_resident_async.id,
                date=date2,
                call_type="weekend",
                supervisor_id=sample_faculty_async.id,
            )
        )
        await service.create_call_assignment(
            CallAssignmentCreate(
                person_id=sample_resident_async.id,
                date=date3,
                call_type="backup",
                supervisor_id=sample_faculty_async.id,
            )
        )

        # Query for middle date range
        result = await service.get_call_assignments(
            start_date=date.today() + timedelta(days=3),
            end_date=date.today() + timedelta(days=7),
        )

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].date == date2

    @pytest.mark.asyncio
    async def test_get_call_assignments_pagination(
        self, async_db, sample_resident_async, sample_faculty_async
    ):
        """Test pagination of call assignments."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import CallAssignmentCreate

        # Create 5 assignments
        for i in range(5):
            await service.create_call_assignment(
                CallAssignmentCreate(
                    person_id=sample_resident_async.id,
                    date=date.today() + timedelta(days=i),
                    call_type="overnight",
                    supervisor_id=sample_faculty_async.id,
                )
            )

        # Get first page
        page1 = await service.get_call_assignments(limit=2, skip=0)
        assert page1["total"] == 5
        assert len(page1["items"]) == 2

        # Get second page
        page2 = await service.get_call_assignments(limit=2, skip=2)
        assert page2["total"] == 5
        assert len(page2["items"]) == 2

        # Items should be different
        page1_ids = {item.id for item in page1["items"]}
        page2_ids = {item.id for item in page2["items"]}
        assert len(page1_ids & page2_ids) == 0  # No overlap

    # =========================================================================
    # Creation Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_call_assignment_success(
        self, async_db, sample_resident_async, sample_faculty_async
    ):
        """Test creating a new call assignment."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import CallAssignmentCreate

        create_data = CallAssignmentCreate(
            person_id=sample_resident_async.id,
            date=date.today() + timedelta(days=1),
            call_type="overnight",
            supervisor_id=sample_faculty_async.id,
            notes="Test call assignment",
        )

        result = await service.create_call_assignment(create_data)

        assert result is not None
        assert result.id is not None
        assert result.person_id == sample_resident_async.id
        assert result.call_type == "overnight"
        assert result.supervisor_id == sample_faculty_async.id
        assert result.notes == "Test call assignment"

    # =========================================================================
    # Deletion Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_delete_call_assignment_success(
        self, async_db, sample_resident_async, sample_faculty_async
    ):
        """Test deleting a call assignment."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import CallAssignmentCreate

        # Create assignment
        create_data = CallAssignmentCreate(
            person_id=sample_resident_async.id,
            date=date.today() + timedelta(days=1),
            call_type="overnight",
            supervisor_id=sample_faculty_async.id,
        )

        created = await service.create_call_assignment(create_data)
        assignment_id = created.id

        # Delete it
        result = await service.delete_call_assignment(assignment_id)
        assert result is True

        # Verify it's gone
        retrieved = await service.get_call_assignment(assignment_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_call_assignment_not_found(self, async_db):
        """Test deleting non-existent call assignment."""
        service = CallAssignmentService(async_db)

        # Try to delete non-existent ID
        result = await service.delete_call_assignment(uuid4())
        assert result is False


class TestCallAssignmentConcurrency:
    """Test concurrent access patterns for call assignments."""

    # NOTE: These tests are kept as placeholders for future implementation
    # when concurrency testing infrastructure is fully set up.
    pass


class TestCallAssignmentIntegration:
    """Integration tests for call assignment service."""

    # NOTE: These tests are kept as placeholders for future implementation
    # when full ACGME validation integration is available.
    pass
