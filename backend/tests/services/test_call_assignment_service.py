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
            call_date=date.today() + timedelta(days=1),
            call_type="overnight",
        )

        result = await service.create_call_assignment(create_data)
        assert result["call_assignment"] is not None
        assert result["error"] is None
        created = result["call_assignment"]

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
                call_date=date1,
                call_type="overnight",
            )
        )
        await service.create_call_assignment(
            CallAssignmentCreate(
                person_id=sample_resident_async.id,
                call_date=date2,
                call_type="weekend",
            )
        )
        await service.create_call_assignment(
            CallAssignmentCreate(
                person_id=sample_resident_async.id,
                call_date=date3,
                call_type="backup",
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
                    call_date=date.today() + timedelta(days=i),
                    call_type="overnight",
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
            call_date=date.today() + timedelta(days=1),
            call_type="overnight",
        )

        result = await service.create_call_assignment(create_data)

        assert result is not None
        assert result["call_assignment"] is not None
        assert result["error"] is None
        created = result["call_assignment"]
        assert created.id is not None
        assert created.person_id == sample_resident_async.id
        assert created.call_type == "overnight"

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
            call_date=date.today() + timedelta(days=1),
            call_type="overnight",
        )

        result = await service.create_call_assignment(create_data)
        assignment_id = result["call_assignment"].id

        # Delete it
        delete_result = await service.delete_call_assignment(assignment_id)
        assert delete_result["success"] is True
        assert delete_result["error"] is None

        # Verify it's gone
        retrieved = await service.get_call_assignment(assignment_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_call_assignment_not_found(self, async_db):
        """Test deleting non-existent call assignment."""
        service = CallAssignmentService(async_db)

        # Try to delete non-existent ID
        result = await service.delete_call_assignment(uuid4())
        assert result["success"] is False
        assert result["error"] == "Call assignment not found"


class TestBulkUpdateCallAssignments:
    """Test suite for bulk update call assignments functionality."""

    @pytest.mark.asyncio
    async def test_bulk_update_success(self, async_db, sample_resident_async, sample_faculty_async):
        """Test bulk updating multiple call assignments to new person."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import CallAssignmentCreate, BulkCallAssignmentUpdateInput

        # Create call assignments
        call_ids = []
        for i in range(3):
            create_data = CallAssignmentCreate(
                person_id=sample_resident_async.id,
                call_date=date.today() + timedelta(days=i + 10),
                call_type="overnight",
            )
            result = await service.create_call_assignment(create_data)
            if result.get("call_assignment"):
                call_ids.append(result["call_assignment"].id)

        assert len(call_ids) == 3

        # Bulk update to faculty
        updates = BulkCallAssignmentUpdateInput(person_id=sample_faculty_async.id)
        result = await service.bulk_update_call_assignments(call_ids, updates)

        assert result["updated"] == 3
        assert len(result["errors"]) == 0
        assert len(result["assignments"]) == 3

        # Verify all assignments now have faculty_id
        for assignment in result["assignments"]:
            assert assignment.person_id == sample_faculty_async.id

    @pytest.mark.asyncio
    async def test_bulk_update_invalid_person(self, async_db, sample_resident_async):
        """Test bulk update with invalid person_id returns error."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import CallAssignmentCreate, BulkCallAssignmentUpdateInput

        # Create a call assignment
        create_data = CallAssignmentCreate(
            person_id=sample_resident_async.id,
            call_date=date.today() + timedelta(days=20),
            call_type="overnight",
        )
        result = await service.create_call_assignment(create_data)
        call_id = result["call_assignment"].id

        # Try to update to non-existent person
        updates = BulkCallAssignmentUpdateInput(person_id=uuid4())
        result = await service.bulk_update_call_assignments([call_id], updates)

        assert result["updated"] == 0
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0].lower()

    @pytest.mark.asyncio
    async def test_bulk_update_nonexistent_assignment(self, async_db, sample_faculty_async):
        """Test bulk update with non-existent assignment ID."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import BulkCallAssignmentUpdateInput

        # Try to update non-existent assignment
        updates = BulkCallAssignmentUpdateInput(person_id=sample_faculty_async.id)
        result = await service.bulk_update_call_assignments([uuid4()], updates)

        assert result["updated"] == 0
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0].lower()


class TestEquityReportAndPreview:
    """Test suite for equity report and preview functionality."""

    @pytest.fixture
    async def setup_equity_data(self, async_db):
        """Create test data for equity testing."""
        # Create two faculty members
        faculty1 = Person(
            id=uuid4(),
            name="Dr. Faculty One",
            type="faculty",
            email="faculty1@hospital.org",
        )
        faculty2 = Person(
            id=uuid4(),
            name="Dr. Faculty Two",
            type="faculty",
            email="faculty2@hospital.org",
        )
        async_db.add(faculty1)
        async_db.add(faculty2)
        await async_db.commit()
        await async_db.refresh(faculty1)
        await async_db.refresh(faculty2)

        return {"faculty1": faculty1, "faculty2": faculty2}

    @pytest.mark.asyncio
    async def test_equity_report_empty(self, async_db):
        """Test equity report with no call assignments."""
        service = CallAssignmentService(async_db)

        report = await service.get_equity_report(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

        assert report.faculty_count == 0
        assert report.total_overnight_calls == 0
        assert len(report.distribution) == 0

    @pytest.mark.asyncio
    async def test_equity_report_with_assignments(self, async_db, setup_equity_data):
        """Test equity report with call assignments."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import CallAssignmentCreate

        faculty1 = setup_equity_data["faculty1"]
        faculty2 = setup_equity_data["faculty2"]

        # Create unequal distribution: faculty1 gets 3, faculty2 gets 1
        for i in range(3):
            await service.create_call_assignment(
                CallAssignmentCreate(
                    person_id=faculty1.id,
                    call_date=date.today() + timedelta(days=i),
                    call_type="overnight",
                )
            )

        await service.create_call_assignment(
            CallAssignmentCreate(
                person_id=faculty2.id,
                call_date=date.today() + timedelta(days=5),
                call_type="overnight",
            )
        )

        report = await service.get_equity_report(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

        assert report.faculty_count == 2
        assert report.total_overnight_calls == 4

    @pytest.mark.asyncio
    async def test_equity_preview_with_simulated_changes(self, async_db, setup_equity_data):
        """Test equity preview with simulated reassignment."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import CallAssignmentCreate, SimulatedChange

        faculty1 = setup_equity_data["faculty1"]
        faculty2 = setup_equity_data["faculty2"]

        # Create initial assignment
        result = await service.create_call_assignment(
            CallAssignmentCreate(
                person_id=faculty1.id,
                call_date=date.today() + timedelta(days=1),
                call_type="overnight",
            )
        )
        assignment_id = result["call_assignment"].id

        # Get preview simulating reassignment to faculty2
        simulated_changes = [
            SimulatedChange(
                assignment_id=assignment_id,
                call_date=date.today() + timedelta(days=1),
                old_person_id=faculty1.id,
                new_person_id=faculty2.id,
            )
        ]

        preview = await service.get_equity_preview(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            simulated_changes=simulated_changes,
        )

        assert preview is not None
        assert preview.current_equity is not None
        assert preview.projected_equity is not None


class TestCoverageReport:
    """Test suite for coverage report functionality."""

    @pytest.mark.asyncio
    async def test_coverage_report_empty(self, async_db):
        """Test coverage report with no assignments."""
        service = CallAssignmentService(async_db)

        report = await service.get_coverage_report(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert report.covered_nights == 0
        # Should have gaps for any Sun-Thu nights

    @pytest.mark.asyncio
    async def test_coverage_report_partial_coverage(self, async_db, sample_resident_async):
        """Test coverage report with partial coverage."""
        service = CallAssignmentService(async_db)
        from app.schemas.call_assignment import CallAssignmentCreate

        # Create one overnight call
        await service.create_call_assignment(
            CallAssignmentCreate(
                person_id=sample_resident_async.id,
                call_date=date.today() + timedelta(days=1),
                call_type="overnight",
            )
        )

        report = await service.get_coverage_report(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        # Should have partial coverage
        assert report.coverage_percentage < 100 or report.total_expected_nights <= 1


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
