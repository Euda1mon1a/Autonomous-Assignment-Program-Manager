"""Tests for EmergencyDeploymentService."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.schemas.emergency_deployment import (
    EmergencyDeploymentRequest,
    EmergencyStrategy,
)
from app.services.emergency_deployment_service import EmergencyDeploymentService


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
async def faculty_person(async_db: AsyncSession) -> Person:
    """Create a faculty member for testing."""
    person = Person(
        id=uuid4(),
        name="Test Faculty",
        email="test.faculty@example.com",
        type="faculty",
    )
    async_db.add(person)
    await async_db.commit()
    await async_db.refresh(person)
    return person


@pytest.fixture
async def resident_person(async_db: AsyncSession) -> Person:
    """Create a resident for testing."""
    person = Person(
        id=uuid4(),
        name="Test Resident",
        email="test.resident@example.com",
        type="resident",
        pgy_level=2,
    )
    async_db.add(person)
    await async_db.commit()
    await async_db.refresh(person)
    return person


class TestEmergencyDeploymentService:
    """Tests for EmergencyDeploymentService."""

    @pytest.mark.asyncio
    async def test_dry_run_assessment_only(
        self,
        async_db: AsyncSession,
        faculty_person: Person,
    ):
        """Dry run should return assessment without making changes."""
        service = EmergencyDeploymentService(async_db)
        request = EmergencyDeploymentRequest(
            person_id=faculty_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            reason="test_deployment",
            dry_run=True,
        )

        response = await service.handle_deployment(request)

        assert response.dry_run is True
        assert response.assessment is not None
        assert response.assessment.affected_slots == 0
        assert response.repair_outcome is None
        assert response.health_check is None
        assert response.overall_success is True
        assert len(response.recommendations) > 0

    @pytest.mark.asyncio
    async def test_rejects_non_faculty(
        self,
        async_db: AsyncSession,
        resident_person: Person,
    ):
        """Should reject non-faculty persons."""
        service = EmergencyDeploymentService(async_db)
        request = EmergencyDeploymentRequest(
            person_id=resident_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            reason="test_deployment",
            dry_run=True,
        )

        response = await service.handle_deployment(request)

        assert response.overall_success is False
        assert "faculty only" in response.errors[0].lower()

    @pytest.mark.asyncio
    async def test_rejects_unknown_person(
        self,
        async_db: AsyncSession,
    ):
        """Should handle unknown person gracefully."""
        service = EmergencyDeploymentService(async_db)
        request = EmergencyDeploymentRequest(
            person_id=uuid4(),  # Non-existent
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            reason="test_deployment",
            dry_run=True,
        )

        response = await service.handle_deployment(request)

        assert response.overall_success is False
        assert "not found" in response.errors[0].lower()

    @pytest.mark.asyncio
    async def test_fragility_assessment_with_assignments(
        self,
        async_db: AsyncSession,
        faculty_person: Person,
    ):
        """Fragility should increase with more assignments."""
        # Add some half-day assignments
        for i in range(5):
            assignment = HalfDayAssignment(
                id=uuid4(),
                person_id=faculty_person.id,
                date=date.today() + timedelta(days=i),
                time_of_day="AM",
                source="manual",
            )
            async_db.add(assignment)
        await async_db.commit()

        service = EmergencyDeploymentService(async_db)
        request = EmergencyDeploymentRequest(
            person_id=faculty_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            reason="test_deployment",
            dry_run=True,
        )

        response = await service.handle_deployment(request)

        assert response.assessment.affected_slots == 5
        assert response.assessment.fragility_score > 0
        # With 5 slots, should recommend cascade (fragility 0.35)
        assert response.assessment.recommended_strategy in [
            EmergencyStrategy.CASCADE,
            EmergencyStrategy.INCREMENTAL,
        ]

    @pytest.mark.asyncio
    async def test_force_strategy_override(
        self,
        async_db: AsyncSession,
        faculty_person: Person,
    ):
        """Force strategy should override automatic selection."""
        service = EmergencyDeploymentService(async_db)
        request = EmergencyDeploymentRequest(
            person_id=faculty_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            reason="test_deployment",
            dry_run=True,
            force_strategy=EmergencyStrategy.FALLBACK,
        )

        response = await service.handle_deployment(request)

        assert response.assessment.recommended_strategy == EmergencyStrategy.FALLBACK

    @pytest.mark.asyncio
    async def test_call_assignments_increase_fragility(
        self,
        async_db: AsyncSession,
        faculty_person: Person,
    ):
        """Call assignments should increase fragility more than half-day."""
        # Add call assignments
        for i in range(3):
            call = CallAssignment(
                id=uuid4(),
                person_id=faculty_person.id,
                date=date.today() + timedelta(days=i),
                call_type="weekday",
            )
            async_db.add(call)
        await async_db.commit()

        service = EmergencyDeploymentService(async_db)
        request = EmergencyDeploymentRequest(
            person_id=faculty_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            reason="test_deployment",
            dry_run=True,
        )

        response = await service.handle_deployment(request)

        # 3 call assignments should boost fragility
        assert response.assessment.affected_slots == 3
        # Fragility boosted by +0.1 for >= 3 call assignments
        assert response.assessment.fragility_score >= 0.25

    @pytest.mark.asyncio
    async def test_execute_with_no_assignments(
        self,
        async_db: AsyncSession,
        faculty_person: Person,
    ):
        """Execute with no assignments should succeed trivially."""
        service = EmergencyDeploymentService(async_db)
        request = EmergencyDeploymentRequest(
            person_id=faculty_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            reason="test_deployment",
            dry_run=False,  # Actually execute
        )

        response = await service.handle_deployment(request)

        assert response.dry_run is False
        assert response.assessment.affected_slots == 0
        assert response.repair_outcome is not None
        assert response.health_check is not None
        assert response.health_check.coverage_rate == 1.0
        assert response.health_check.is_healthy is True
        assert response.overall_success is True

    @pytest.mark.asyncio
    async def test_high_fragility_triggers_fallback_strategy(
        self,
        async_db: AsyncSession,
        faculty_person: Person,
    ):
        """Many assignments should trigger fallback strategy recommendation."""
        # Add many assignments to push fragility above 0.6
        for i in range(15):
            assignment = HalfDayAssignment(
                id=uuid4(),
                person_id=faculty_person.id,
                date=date.today() + timedelta(days=i),
                time_of_day="AM" if i % 2 == 0 else "PM",
                source="manual",
            )
            async_db.add(assignment)
        for i in range(4):
            call = CallAssignment(
                id=uuid4(),
                person_id=faculty_person.id,
                date=date.today() + timedelta(days=i * 5),
                call_type="weekday",
            )
            async_db.add(call)
        await async_db.commit()

        service = EmergencyDeploymentService(async_db)
        request = EmergencyDeploymentRequest(
            person_id=faculty_person.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=20),
            reason="test_deployment",
            dry_run=True,
        )

        response = await service.handle_deployment(request)

        # 19 slots (15 half-day + 4 call) should push fragility high
        assert response.assessment.affected_slots == 19
        assert response.assessment.fragility_score >= 0.6
        assert response.assessment.recommended_strategy == EmergencyStrategy.FALLBACK
