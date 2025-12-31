"""
Tests for enhanced swap engine.

Tests the core swap orchestration engine including request creation,
validation, execution, and rollback.
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4

from app.services.swap.swap_engine import SwapEngine, SwapEngineResult
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.person import Person


pytestmark = pytest.mark.asyncio


class TestSwapEngine:
    """Test suite for SwapEngine."""

    async def test_create_swap_request_success(self, async_db, test_faculty):
        """Test successful swap request creation."""
        engine = SwapEngine(async_db)

        source_faculty = test_faculty[0]
        target_faculty = test_faculty[1]

        result = await engine.create_swap_request(
            source_faculty_id=source_faculty.id,
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=target_faculty.id,
            target_week=date.today() + timedelta(days=21),
            swap_type=SwapType.ONE_TO_ONE,
            reason="Need to attend conference",
        )

        assert result.success
        assert result.swap_id is not None
        assert "created successfully" in result.message.lower()

    async def test_create_swap_request_faculty_not_found(self, async_db):
        """Test swap request creation with non-existent faculty."""
        engine = SwapEngine(async_db)

        result = await engine.create_swap_request(
            source_faculty_id=uuid4(),  # Non-existent
            source_week=date.today() + timedelta(days=14),
            target_faculty_id=uuid4(),  # Non-existent
            target_week=None,
            swap_type=SwapType.ABSORB,
        )

        assert not result.success
        assert result.error_code == "FACULTY_NOT_FOUND"

    async def test_validate_swap(self, async_db, test_swap_request):
        """Test swap validation."""
        engine = SwapEngine(async_db)

        # Register a simple validator
        class MockValidator:
            async def validate(self, swap):
                return {
                    "valid": True,
                    "message": "Mock validation passed",
                }

        engine.register_validator(MockValidator())

        result = await engine.validate_swap(test_swap_request.id)

        assert result.success
        assert result.metadata["total_validators"] == 1
        assert result.metadata["passed"] == 1

    async def test_execute_swap_success(self, async_db, test_swap_request):
        """Test successful swap execution."""
        engine = SwapEngine(async_db)

        # Register mock validator that passes
        class PassValidator:
            async def validate(self, swap):
                return {"valid": True}

        engine.register_validator(PassValidator())

        result = await engine.execute_swap(
            swap_id=test_swap_request.id,
            executed_by_id=uuid4(),
            dry_run=False,
        )

        assert result.success
        assert "executed successfully" in result.message.lower()

    async def test_execute_swap_dry_run(self, async_db, test_swap_request):
        """Test dry run execution."""
        engine = SwapEngine(async_db)

        class PassValidator:
            async def validate(self, swap):
                return {"valid": True}

        engine.register_validator(PassValidator())

        result = await engine.execute_swap(
            swap_id=test_swap_request.id,
            dry_run=True,
        )

        assert result.success
        assert result.metadata["dry_run"] is True

    async def test_execute_swap_validation_failure(self, async_db, test_swap_request):
        """Test execution fails on validation error."""
        engine = SwapEngine(async_db)

        class FailValidator:
            async def validate(self, swap):
                return {"valid": False, "error": "Test validation failure"}

        engine.register_validator(FailValidator())

        result = await engine.execute_swap(test_swap_request.id)

        assert not result.success
        assert result.error_code == "VALIDATION_FAILED"

    async def test_rollback_swap_success(self, async_db, test_executed_swap):
        """Test successful swap rollback."""
        engine = SwapEngine(async_db)

        result = await engine.rollback_swap(
            swap_id=test_executed_swap.id,
            reason="Testing rollback",
            rolled_back_by_id=uuid4(),
        )

        assert result.success
        assert "rolled back successfully" in result.message.lower()

    async def test_rollback_swap_not_found(self, async_db):
        """Test rollback with non-existent swap."""
        engine = SwapEngine(async_db)

        result = await engine.rollback_swap(
            swap_id=uuid4(),
            reason="Test",
        )

        assert not result.success
        assert result.error_code == "SWAP_NOT_FOUND"

    async def test_rollback_swap_invalid_status(self, async_db, test_swap_request):
        """Test rollback fails for non-executed swap."""
        engine = SwapEngine(async_db)

        result = await engine.rollback_swap(
            swap_id=test_swap_request.id,
            reason="Test",
        )

        assert not result.success
        assert result.error_code == "INVALID_STATUS"

    async def test_create_execution_plan(self, async_db, test_swap_request):
        """Test execution plan creation."""
        engine = SwapEngine(async_db)

        plan = await engine.create_execution_plan(test_swap_request.id)

        assert plan is not None
        assert plan.swap_id == test_swap_request.id
        assert len(plan.execution_steps) > 0
        assert len(plan.rollback_plan) > 0


# ===== Fixtures =====


@pytest.fixture
async def test_faculty(async_db):
    """Create test faculty members."""
    faculty = []

    for i in range(3):
        person = Person(
            id=uuid4(),
            name=f"Test Faculty {i}",
            type="faculty",
        )
        async_db.add(person)
        faculty.append(person)

    await async_db.commit()

    return faculty


@pytest.fixture
async def test_swap_request(async_db, test_faculty):
    """Create a test swap request."""
    swap = SwapRecord(
        id=uuid4(),
        source_faculty_id=test_faculty[0].id,
        target_faculty_id=test_faculty[1].id,
        source_week=date.today() + timedelta(days=14),
        target_week=date.today() + timedelta(days=21),
        swap_type=SwapType.ONE_TO_ONE,
        status=SwapStatus.PENDING,
        requested_at=datetime.utcnow(),
    )

    async_db.add(swap)
    await async_db.commit()

    return swap


@pytest.fixture
async def test_executed_swap(async_db, test_faculty):
    """Create an executed swap for testing rollback."""
    swap = SwapRecord(
        id=uuid4(),
        source_faculty_id=test_faculty[0].id,
        target_faculty_id=test_faculty[1].id,
        source_week=date.today() + timedelta(days=14),
        target_week=date.today() + timedelta(days=21),
        swap_type=SwapType.ONE_TO_ONE,
        status=SwapStatus.EXECUTED,
        requested_at=datetime.utcnow(),
        executed_at=datetime.utcnow(),
    )

    async_db.add(swap)
    await async_db.commit()

    return swap
