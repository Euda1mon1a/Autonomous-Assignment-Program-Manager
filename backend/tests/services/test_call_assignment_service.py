"""Tests for Call Assignment Service.

This module tests the call assignment service which handles
on-call scheduling with async SQLAlchemy 2.0 patterns.

Tests cover:
- CRUD operations for call assignments
- Date range queries
- Coverage and equity reports
- Bulk operations
"""

import pytest
import pytest_asyncio
from datetime import date, timedelta
from uuid import uuid4

from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.schemas.call_assignment import CallAssignmentCreate, CallAssignmentUpdate
from app.services.call_assignment_service import CallAssignmentService


class TestCallAssignmentService:
    """Test suite for call assignment service."""

    @pytest_asyncio.fixture
    async def sample_faculty(self, async_db):
        """Create sample faculty for testing."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Call Faculty",
            type="faculty",
            email="call.faculty@hospital.org",
            performs_procedures=True,
            specialties=["General"],
        )
        async_db.add(faculty)
        await async_db.commit()
        await async_db.refresh(faculty)
        return faculty

    @pytest_asyncio.fixture
    async def sample_faculty_list(self, async_db):
        """Create multiple faculty members for testing."""
        faculty = []
        for i in range(3):
            fac = Person(
                id=uuid4(),
                name=f"Dr. Faculty {i + 1}",
                type="faculty",
                email=f"faculty{i + 1}@hospital.org",
                performs_procedures=True,
                specialties=["General"],
            )
            async_db.add(fac)
            faculty.append(fac)
        await async_db.commit()
        for f in faculty:
            await async_db.refresh(f)
        return faculty

    @pytest_asyncio.fixture
    async def sample_call_assignment(self, async_db, sample_faculty):
        """Create a sample call assignment."""
        call_assignment = CallAssignment(
            id=uuid4(),
            date=date.today(),
            person_id=sample_faculty.id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
        )
        async_db.add(call_assignment)
        await async_db.commit()
        await async_db.refresh(call_assignment)
        return call_assignment

    # =========================================================================
    # Retrieval Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_call_assignment_success(
        self, async_db, sample_call_assignment
    ):
        """Test retrieving a call assignment by ID."""
        service = CallAssignmentService(async_db)
        assignment = await service.get_call_assignment(sample_call_assignment.id)

        assert assignment is not None
        assert assignment.id == sample_call_assignment.id
        assert assignment.call_type == "overnight"

    @pytest.mark.asyncio
    async def test_get_call_assignment_not_found(self, async_db):
        """Test retrieving non-existent call assignment returns None."""
        service = CallAssignmentService(async_db)
        assignment = await service.get_call_assignment(uuid4())

        assert assignment is None

    @pytest.mark.asyncio
    async def test_get_call_assignment_with_eager_loading(
        self, async_db, sample_call_assignment, sample_faculty
    ):
        """Test N+1 optimization via selectinload."""
        service = CallAssignmentService(async_db)
        assignment = await service.get_call_assignment(sample_call_assignment.id)

        assert assignment is not None
        # Person should be eagerly loaded - no second query
        assert assignment.person is not None
        assert assignment.person.id == sample_faculty.id

    @pytest.mark.asyncio
    async def test_get_call_assignments_by_date_range(
        self, async_db, sample_call_assignment
    ):
        """Test retrieving call assignments by date range."""
        service = CallAssignmentService(async_db)
        result = await service.get_call_assignments(
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=1),
        )

        assert isinstance(result, dict)
        assert "items" in result
        assert "total" in result
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_call_assignments_empty_result(self, async_db):
        """Test retrieving call assignments with no matches."""
        service = CallAssignmentService(async_db)
        result = await service.get_call_assignments(
            start_date=date(2099, 1, 1),
            end_date=date(2099, 12, 31),
        )

        assert isinstance(result, dict)
        assert result["items"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_get_call_assignments_pagination(
        self, async_db, sample_faculty_list
    ):
        """Test pagination of call assignments."""
        # Create multiple assignments
        for i, faculty in enumerate(sample_faculty_list):
            call = CallAssignment(
                id=uuid4(),
                date=date.today() + timedelta(days=i),
                person_id=faculty.id,
                call_type="overnight",
                is_weekend=False,
                is_holiday=False,
            )
            async_db.add(call)
        await async_db.commit()

        service = CallAssignmentService(async_db)
        page1 = await service.get_call_assignments(limit=2, skip=0)
        page2 = await service.get_call_assignments(limit=2, skip=2)

        assert len(page1["items"]) == 2
        assert page1["total"] >= 3

    # =========================================================================
    # Creation Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_call_assignment_success(self, async_db, sample_faculty):
        """Test creating a new call assignment."""
        service = CallAssignmentService(async_db)
        assignment_data = CallAssignmentCreate(
            call_date=date.today() + timedelta(days=10),
            person_id=sample_faculty.id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
        )

        result = await service.create_call_assignment(assignment_data)

        assert result["error"] is None
        assert result["call_assignment"] is not None
        assert result["call_assignment"].person_id == sample_faculty.id

    @pytest.mark.asyncio
    async def test_create_call_assignment_duplicate(
        self, async_db, sample_faculty, sample_call_assignment
    ):
        """Test creating duplicate call assignment fails."""
        service = CallAssignmentService(async_db)
        assignment_data = CallAssignmentCreate(
            call_date=sample_call_assignment.date,
            person_id=sample_faculty.id,
            call_type="overnight",  # Same type, same date, same person
            is_weekend=False,
            is_holiday=False,
        )

        result = await service.create_call_assignment(assignment_data)

        assert result["error"] is not None
        assert "already exists" in result["error"]
        assert result["call_assignment"] is None

    @pytest.mark.asyncio
    async def test_create_call_assignment_person_not_found(self, async_db):
        """Test creating call assignment with non-existent person."""
        service = CallAssignmentService(async_db)
        assignment_data = CallAssignmentCreate(
            call_date=date.today(),
            person_id=uuid4(),  # Non-existent
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
        )

        result = await service.create_call_assignment(assignment_data)

        assert result["error"] is not None
        assert "not found" in result["error"]

    # =========================================================================
    # Update Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_update_call_assignment_success(
        self, async_db, sample_call_assignment
    ):
        """Test updating a call assignment."""
        service = CallAssignmentService(async_db)
        update_data = CallAssignmentUpdate(
            call_type="weekend",
            is_weekend=True,
        )

        result = await service.update_call_assignment(
            sample_call_assignment.id, update_data
        )

        assert result["error"] is None
        assert result["call_assignment"].call_type == "weekend"
        assert result["call_assignment"].is_weekend is True

    @pytest.mark.asyncio
    async def test_update_call_assignment_not_found(self, async_db):
        """Test updating non-existent call assignment."""
        service = CallAssignmentService(async_db)
        update_data = CallAssignmentUpdate(call_type="weekend")

        result = await service.update_call_assignment(uuid4(), update_data)

        assert result["error"] is not None
        assert "not found" in result["error"]

    # =========================================================================
    # Deletion Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_delete_call_assignment_success(
        self, async_db, sample_call_assignment
    ):
        """Test deleting a call assignment."""
        service = CallAssignmentService(async_db)

        result = await service.delete_call_assignment(sample_call_assignment.id)

        assert result["success"] is True
        assert result["error"] is None

        # Verify deleted
        deleted = await service.get_call_assignment(sample_call_assignment.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_call_assignment_not_found(self, async_db):
        """Test deleting non-existent call assignment."""
        service = CallAssignmentService(async_db)

        result = await service.delete_call_assignment(uuid4())

        assert result["success"] is False
        assert result["error"] is not None

    # =========================================================================
    # Coverage Report Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_coverage_report(
        self, async_db, sample_faculty_list
    ):
        """Test coverage report generation."""
        # Create some overnight call assignments
        start_date = date(2025, 1, 6)  # Monday
        for i in range(5):  # Mon-Fri
            call = CallAssignment(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                person_id=sample_faculty_list[i % len(sample_faculty_list)].id,
                call_type="overnight",
                is_weekend=False,
                is_holiday=False,
            )
            async_db.add(call)
        await async_db.commit()

        service = CallAssignmentService(async_db)
        report = await service.get_coverage_report(
            start_date=start_date,
            end_date=start_date + timedelta(days=6),
        )

        assert report is not None
        assert report.start_date == start_date
        assert hasattr(report, "coverage_percentage")
        assert hasattr(report, "gaps")

    @pytest.mark.asyncio
    async def test_get_coverage_report_empty(self, async_db):
        """Test coverage report with no assignments."""
        service = CallAssignmentService(async_db)
        report = await service.get_coverage_report(
            start_date=date(2099, 1, 1),
            end_date=date(2099, 1, 31),
        )

        assert report is not None
        assert len(report.gaps) > 0  # Should have coverage gaps

    # =========================================================================
    # Equity Report Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_equity_report(
        self, async_db, sample_faculty_list
    ):
        """Test equity report generation."""
        # Create varied call assignments
        start_date = date(2025, 1, 1)
        for i in range(10):
            call = CallAssignment(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                person_id=sample_faculty_list[i % len(sample_faculty_list)].id,
                call_type="overnight",
                is_weekend=False,
                is_holiday=False,
            )
            async_db.add(call)
        await async_db.commit()

        service = CallAssignmentService(async_db)
        report = await service.get_equity_report(
            start_date=start_date,
            end_date=start_date + timedelta(days=30),
        )

        assert report is not None
        assert report.faculty_count >= 1
        assert hasattr(report, "distribution")
        assert hasattr(report, "sunday_call_stats")

    # =========================================================================
    # Bulk Operations Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_bulk_create_call_assignments(
        self, async_db, sample_faculty_list
    ):
        """Test bulk creation of call assignments."""
        assignments = []
        for i, faculty in enumerate(sample_faculty_list):
            assignments.append(
                CallAssignmentCreate(
                    call_date=date.today() + timedelta(days=50 + i),
                    person_id=faculty.id,
                    call_type="overnight",
                    is_weekend=False,
                    is_holiday=False,
                )
            )

        service = CallAssignmentService(async_db)
        result = await service.bulk_create_call_assignments(assignments)

        assert result["count"] == len(sample_faculty_list)
        assert len(result["created"]) == len(sample_faculty_list)
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_clear_call_assignments_in_range(
        self, async_db, sample_faculty
    ):
        """Test clearing call assignments in date range."""
        # Create assignments
        start_date = date(2025, 6, 1)
        for i in range(5):
            call = CallAssignment(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                person_id=sample_faculty.id,
                call_type="overnight",
                is_weekend=False,
                is_holiday=False,
            )
            async_db.add(call)
        await async_db.commit()

        service = CallAssignmentService(async_db)
        result = await service.clear_call_assignments_in_range(
            start_date=start_date,
            end_date=start_date + timedelta(days=10),
        )

        assert result["deleted"] == 5
        assert result["error"] is None


class TestCallAssignmentConcurrency:
    """Test concurrent access patterns for call assignments."""

    @pytest_asyncio.fixture
    async def sample_faculty(self, async_db):
        """Create sample faculty for testing."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Concurrent Faculty",
            type="faculty",
            email="concurrent.faculty@hospital.org",
            performs_procedures=True,
        )
        async_db.add(faculty)
        await async_db.commit()
        await async_db.refresh(faculty)
        return faculty

    @pytest.mark.asyncio
    async def test_create_different_call_types_same_day(
        self, async_db, sample_faculty
    ):
        """Test creating different call types for same person/date."""
        service = CallAssignmentService(async_db)

        # Create overnight call
        overnight = CallAssignmentCreate(
            call_date=date.today() + timedelta(days=100),
            person_id=sample_faculty.id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
        )
        result1 = await service.create_call_assignment(overnight)
        assert result1["error"] is None

        # Create backup call for same day - different type should work
        backup = CallAssignmentCreate(
            call_date=date.today() + timedelta(days=100),
            person_id=sample_faculty.id,
            call_type="backup",
            is_weekend=False,
            is_holiday=False,
        )
        result2 = await service.create_call_assignment(backup)
        assert result2["error"] is None


class TestCallAssignmentIntegration:
    """Integration tests for call assignment service."""

    @pytest_asyncio.fixture
    async def sample_faculty(self, async_db):
        """Create sample faculty for integration tests."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Integration Faculty",
            type="faculty",
            email="integration.faculty@hospital.org",
            performs_procedures=True,
        )
        async_db.add(faculty)
        await async_db.commit()
        await async_db.refresh(faculty)
        return faculty

    @pytest.mark.asyncio
    async def test_full_call_schedule_workflow(
        self, async_db, sample_faculty
    ):
        """Test complete workflow: create, read, update, delete."""
        service = CallAssignmentService(async_db)
        test_date = date.today() + timedelta(days=200)

        # 1. Create
        create_data = CallAssignmentCreate(
            call_date=test_date,
            person_id=sample_faculty.id,
            call_type="overnight",
            is_weekend=False,
            is_holiday=False,
        )
        create_result = await service.create_call_assignment(create_data)
        assert create_result["error"] is None
        assignment_id = create_result["call_assignment"].id

        # 2. Read
        read_result = await service.get_call_assignment(assignment_id)
        assert read_result is not None
        assert read_result.call_type == "overnight"

        # 3. Update
        update_data = CallAssignmentUpdate(call_type="weekend")
        update_result = await service.update_call_assignment(
            assignment_id, update_data
        )
        assert update_result["error"] is None
        assert update_result["call_assignment"].call_type == "weekend"

        # 4. Delete
        delete_result = await service.delete_call_assignment(assignment_id)
        assert delete_result["success"] is True

        # 5. Verify deleted
        final_read = await service.get_call_assignment(assignment_id)
        assert final_read is None
