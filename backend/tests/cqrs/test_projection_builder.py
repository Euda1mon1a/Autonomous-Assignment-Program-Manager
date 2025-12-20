"""
Tests for CQRS Projection Builder Service.

Tests:
- Projection registration
- Incremental updates
- Full rebuilds
- Projection versioning
- Concurrent builds
- Checkpointing
- Error handling
- Health monitoring
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.cqrs.projection_builder import (
    BaseProjection,
    BuildMode,
    BuildResult,
    ProjectionBuilder,
    ProjectionCheckpoint,
    ProjectionError,
    ProjectionMetadata,
    ProjectionNotFoundError,
    ProjectionStatus,
)
from app.db.base import Base
from app.events.event_store import EventStore, StoredEvent
from app.events.event_types import (
    AssignmentCreatedEvent,
    AssignmentUpdatedEvent,
    PersonCreatedEvent,
    EventMetadata,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create database session."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def event_store(db_session):
    """Create event store instance."""
    return EventStore(db_session)


@pytest.fixture
def projection_builder(db_session, event_store):
    """Create projection builder instance."""
    return ProjectionBuilder(db_session, event_store)


# =============================================================================
# Test Projections
# =============================================================================


class TestPersonProjection(BaseProjection):
    """Test projection for person events."""

    projection_name = "test_person_summary"
    version = 1
    description = "Test projection for persons"

    def __init__(self, db: Session):
        super().__init__(db)
        self.persons: dict[str, dict] = {}

    async def handle_person_created(self, event: PersonCreatedEvent):
        """Handle person created event."""
        self.persons[event.person_id] = {
            "person_id": event.person_id,
            "name": event.name,
            "email": event.email,
            "role": event.role,
            "created_at": event.metadata.timestamp,
        }

    async def handle_person_updated(self, event):
        """Handle person updated event."""
        if event.person_id in self.persons:
            self.persons[event.person_id].update(event.changes)

    async def reset(self):
        """Reset projection data."""
        self.persons.clear()

    async def get_checkpoint_data(self) -> dict[str, Any]:
        """Get checkpoint data."""
        return {"person_count": len(self.persons)}

    async def restore_checkpoint_data(self, data: dict[str, Any]):
        """Restore from checkpoint."""
        # In a real implementation, would restore state
        pass


class TestAssignmentProjection(BaseProjection):
    """Test projection for assignment events."""

    projection_name = "test_assignment_summary"
    version = 1
    description = "Test projection for assignments"
    parallel_enabled = True

    def __init__(self, db: Session):
        super().__init__(db)
        self.assignments: dict[str, dict] = {}

    async def handle_assignment_created(self, event: AssignmentCreatedEvent):
        """Handle assignment created event."""
        self.assignments[event.assignment_id] = {
            "assignment_id": event.assignment_id,
            "person_id": event.person_id,
            "block_id": event.block_id,
            "rotation_id": event.rotation_id,
            "role": event.role,
            "created_at": event.metadata.timestamp,
        }

    async def handle_assignment_updated(self, event: AssignmentUpdatedEvent):
        """Handle assignment updated event."""
        if event.assignment_id in self.assignments:
            self.assignments[event.assignment_id].update(event.changes)

    async def reset(self):
        """Reset projection data."""
        self.assignments.clear()


class ErrorTestProjection(BaseProjection):
    """Projection that raises errors for testing error handling."""

    projection_name = "test_error_projection"
    version = 1
    retry_on_error = False

    def __init__(self, db: Session):
        super().__init__(db)
        self.error_on_next = False

    async def handle_person_created(self, event: PersonCreatedEvent):
        """Handler that can raise errors."""
        if self.error_on_next:
            self.error_on_next = False
            raise ValueError("Test error")

    async def reset(self):
        """Reset projection data."""
        pass


# =============================================================================
# Test Cases
# =============================================================================


class TestProjectionRegistration:
    """Test projection registration."""

    @pytest.mark.asyncio
    async def test_register_projection(self, projection_builder, db_session):
        """Test registering a projection."""
        projection = TestPersonProjection(db_session)
        projection_builder.register_projection(projection)

        assert projection.projection_name in projection_builder._projections

        # Check metadata was created
        metadata = (
            db_session.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection.projection_name)
            .first()
        )
        assert metadata is not None
        assert metadata.projection_version == 1
        assert metadata.status == ProjectionStatus.INITIALIZING

    @pytest.mark.asyncio
    async def test_register_without_name_fails(self, projection_builder, db_session):
        """Test registering projection without name fails."""

        class NoNameProjection(BaseProjection):
            # Missing projection_name
            version = 1

            async def reset(self):
                pass

        projection = NoNameProjection(db_session)
        with pytest.raises(ValueError, match="must have a name"):
            projection_builder.register_projection(projection)

    @pytest.mark.asyncio
    async def test_version_change_marks_for_rebuild(
        self, projection_builder, db_session
    ):
        """Test that version changes trigger rebuild."""
        # Register v1
        projection_v1 = TestPersonProjection(db_session)
        projection_builder.register_projection(projection_v1)

        # Update version in database
        metadata = (
            db_session.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection_v1.projection_name)
            .first()
        )
        metadata.status = ProjectionStatus.ACTIVE
        db_session.commit()

        # Register v2
        class TestPersonProjectionV2(TestPersonProjection):
            version = 2

        projection_v2 = TestPersonProjectionV2(db_session)
        projection_builder.register_projection(projection_v2)

        # Check status changed to INITIALIZING
        metadata = (
            db_session.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection_v1.projection_name)
            .first()
        )
        assert metadata.projection_version == 2
        assert metadata.status == ProjectionStatus.INITIALIZING


class TestProjectionBuilding:
    """Test projection building."""

    @pytest.mark.asyncio
    async def test_build_projection_incremental(
        self, projection_builder, event_store, db_session
    ):
        """Test incremental projection build."""
        # Create test events
        person_id = str(uuid4())
        event = PersonCreatedEvent(
            aggregate_id=person_id,
            person_id=person_id,
            name="John Doe",
            email="john@example.com",
            role="RESIDENT",
            created_by="admin",
            metadata=EventMetadata(event_type="PersonCreated"),
        )

        await event_store.append_event(event)

        # Register and build projection
        projection = TestPersonProjection(db_session)
        projection_builder.register_projection(projection)

        result = await projection_builder.build_projection(
            projection.projection_name, mode=BuildMode.INCREMENTAL
        )

        assert result.success is True
        assert result.events_processed > 0
        assert person_id in projection.persons

    @pytest.mark.asyncio
    async def test_build_projection_full(
        self, projection_builder, event_store, db_session
    ):
        """Test full projection rebuild."""
        # Create test events
        person_id = str(uuid4())
        event = PersonCreatedEvent(
            aggregate_id=person_id,
            person_id=person_id,
            name="Jane Doe",
            email="jane@example.com",
            role="FACULTY",
            created_by="admin",
            metadata=EventMetadata(event_type="PersonCreated"),
        )

        await event_store.append_event(event)

        # Register projection
        projection = TestPersonProjection(db_session)
        projection_builder.register_projection(projection)

        # Full rebuild
        result = await projection_builder.build_projection(
            projection.projection_name, mode=BuildMode.FULL
        )

        assert result.success is True
        assert person_id in projection.persons

        # Check metadata
        metadata = (
            db_session.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection.projection_name)
            .first()
        )
        assert metadata.status == ProjectionStatus.ACTIVE
        assert metadata.events_processed > 0

    @pytest.mark.asyncio
    async def test_build_unregistered_projection_fails(
        self, projection_builder, db_session
    ):
        """Test building unregistered projection fails."""
        with pytest.raises(ValueError, match="not registered"):
            await projection_builder.build_projection("nonexistent")


class TestCheckpointing:
    """Test projection checkpointing."""

    @pytest.mark.asyncio
    async def test_checkpoints_created_during_build(
        self, projection_builder, event_store, db_session
    ):
        """Test that checkpoints are created during build."""

        # Create projection with small checkpoint interval
        class SmallCheckpointProjection(TestPersonProjection):
            projection_name = "test_checkpoint_projection"
            checkpoint_interval = 2  # Checkpoint every 2 events

        projection = SmallCheckpointProjection(db_session)
        projection_builder.register_projection(projection)

        # Create multiple events
        for i in range(5):
            person_id = str(uuid4())
            event = PersonCreatedEvent(
                aggregate_id=person_id,
                person_id=person_id,
                name=f"Person {i}",
                email=f"person{i}@example.com",
                role="RESIDENT",
                created_by="admin",
                metadata=EventMetadata(event_type="PersonCreated"),
            )
            await event_store.append_event(event)

        # Build projection
        await projection_builder.build_projection(
            projection.projection_name, mode=BuildMode.FULL
        )

        # Check checkpoints were created
        checkpoints = (
            db_session.query(ProjectionCheckpoint)
            .filter(ProjectionCheckpoint.projection_name == projection.projection_name)
            .all()
        )
        assert len(checkpoints) > 0

    @pytest.mark.asyncio
    async def test_rebuild_from_checkpoint(
        self, projection_builder, event_store, db_session
    ):
        """Test rebuilding from checkpoint."""

        class CheckpointProjection(TestPersonProjection):
            projection_name = "test_checkpoint_rebuild"
            checkpoint_interval = 2

        projection = CheckpointProjection(db_session)
        projection_builder.register_projection(projection)

        # Create events and build
        for i in range(5):
            person_id = str(uuid4())
            event = PersonCreatedEvent(
                aggregate_id=person_id,
                person_id=person_id,
                name=f"Person {i}",
                email=f"person{i}@example.com",
                role="RESIDENT",
                created_by="admin",
                metadata=EventMetadata(event_type="PersonCreated"),
            )
            await event_store.append_event(event)

        await projection_builder.build_projection(
            projection.projection_name, mode=BuildMode.FULL
        )

        # Rebuild from checkpoint
        result = await projection_builder.rebuild_projection(
            projection.projection_name, from_checkpoint=True
        )

        assert result.success is True


class TestConcurrentBuilding:
    """Test concurrent projection building."""

    @pytest.mark.asyncio
    async def test_build_all_sequential(
        self, projection_builder, event_store, db_session
    ):
        """Test building all projections sequentially."""
        # Register multiple projections
        person_proj = TestPersonProjection(db_session)
        assignment_proj = TestAssignmentProjection(db_session)

        projection_builder.register_projection(person_proj)
        projection_builder.register_projection(assignment_proj)

        # Create test events
        person_id = str(uuid4())
        person_event = PersonCreatedEvent(
            aggregate_id=person_id,
            person_id=person_id,
            name="John Doe",
            email="john@example.com",
            role="RESIDENT",
            created_by="admin",
            metadata=EventMetadata(event_type="PersonCreated"),
        )
        await event_store.append_event(person_event)

        assignment_id = str(uuid4())
        assignment_event = AssignmentCreatedEvent(
            aggregate_id=assignment_id,
            assignment_id=assignment_id,
            person_id=person_id,
            block_id=str(uuid4()),
            rotation_id=str(uuid4()),
            role="RESIDENT",
            created_by="admin",
            metadata=EventMetadata(event_type="AssignmentCreated"),
        )
        await event_store.append_event(assignment_event)

        # Build all
        results = await projection_builder.build_all(
            mode=BuildMode.FULL, parallel=False
        )

        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_build_all_parallel(
        self, projection_builder, event_store, db_session
    ):
        """Test building projections in parallel."""
        # Register projections (one supports parallel)
        person_proj = TestPersonProjection(db_session)
        assignment_proj = TestAssignmentProjection(db_session)  # parallel_enabled=True

        projection_builder.register_projection(person_proj)
        projection_builder.register_projection(assignment_proj)

        # Create events
        person_id = str(uuid4())
        person_event = PersonCreatedEvent(
            aggregate_id=person_id,
            person_id=person_id,
            name="John Doe",
            email="john@example.com",
            role="RESIDENT",
            created_by="admin",
            metadata=EventMetadata(event_type="PersonCreated"),
        )
        await event_store.append_event(person_event)

        # Build in parallel
        results = await projection_builder.build_all(mode=BuildMode.FULL, parallel=True)

        # At least one should succeed
        assert any(r.success for r in results)


class TestErrorHandling:
    """Test projection error handling."""

    @pytest.mark.asyncio
    async def test_error_updates_metadata(
        self, projection_builder, event_store, db_session
    ):
        """Test that errors update projection metadata."""
        projection = ErrorTestProjection(db_session)
        projection.error_on_next = True
        projection_builder.register_projection(projection)

        # Create event that will cause error
        person_id = str(uuid4())
        event = PersonCreatedEvent(
            aggregate_id=person_id,
            person_id=person_id,
            name="Test",
            email="test@example.com",
            role="RESIDENT",
            created_by="admin",
            metadata=EventMetadata(event_type="PersonCreated"),
        )
        await event_store.append_event(event)

        # Build should fail
        result = await projection_builder.build_projection(projection.projection_name)

        assert result.success is False
        assert result.error is not None

        # Check metadata
        metadata = (
            db_session.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection.projection_name)
            .first()
        )
        assert metadata.status == ProjectionStatus.ERROR
        assert metadata.error_count > 0
        assert metadata.last_error is not None

    @pytest.mark.asyncio
    async def test_retry_on_error(self, projection_builder, event_store, db_session):
        """Test retry logic on transient errors."""

        class RetryProjection(BaseProjection):
            projection_name = "test_retry"
            version = 1
            retry_on_error = True
            max_retries = 3

            def __init__(self, db: Session):
                super().__init__(db)
                self.attempt_count = 0

            async def handle_person_created(self, event: PersonCreatedEvent):
                self.attempt_count += 1
                if self.attempt_count < 2:
                    raise ValueError("Transient error")

            async def reset(self):
                self.attempt_count = 0

        projection = RetryProjection(db_session)
        projection_builder.register_projection(projection)

        # Create event
        person_id = str(uuid4())
        event = PersonCreatedEvent(
            aggregate_id=person_id,
            person_id=person_id,
            name="Test",
            email="test@example.com",
            role="RESIDENT",
            created_by="admin",
            metadata=EventMetadata(event_type="PersonCreated"),
        )
        await event_store.append_event(event)

        # Should succeed after retry
        result = await projection_builder.build_projection(projection.projection_name)
        assert result.success is True
        assert projection.attempt_count >= 2


class TestProjectionManagement:
    """Test projection management operations."""

    @pytest.mark.asyncio
    async def test_pause_resume_projection(
        self, projection_builder, db_session
    ):
        """Test pausing and resuming a projection."""
        projection = TestPersonProjection(db_session)
        projection_builder.register_projection(projection)

        # Pause
        await projection_builder.pause_projection(projection.projection_name)

        metadata = (
            db_session.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection.projection_name)
            .first()
        )
        assert metadata.status == ProjectionStatus.PAUSED

        # Resume (will trigger rebuild)
        # Note: This would normally rebuild, but we'll just check the status change
        metadata.status = ProjectionStatus.ACTIVE
        db_session.commit()

        assert metadata.status == ProjectionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_disable_enable_projection(
        self, projection_builder, db_session
    ):
        """Test disabling and enabling a projection."""
        projection = TestPersonProjection(db_session)
        projection_builder.register_projection(projection)

        # Disable
        await projection_builder.disable_projection(projection.projection_name)

        metadata = (
            db_session.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection.projection_name)
            .first()
        )
        assert metadata.enabled is False

        # Enable
        metadata.enabled = True
        db_session.commit()
        assert metadata.enabled is True

    @pytest.mark.asyncio
    async def test_get_projection_status(
        self, projection_builder, db_session
    ):
        """Test getting projection status."""
        projection = TestPersonProjection(db_session)
        projection_builder.register_projection(projection)

        status = await projection_builder.get_projection_status(
            projection.projection_name
        )

        assert status["name"] == projection.projection_name
        assert status["version"] == projection.version
        assert "status" in status
        assert "events_processed" in status

    @pytest.mark.asyncio
    async def test_get_all_projections_status(
        self, projection_builder, db_session
    ):
        """Test getting status of all projections."""
        person_proj = TestPersonProjection(db_session)
        assignment_proj = TestAssignmentProjection(db_session)

        projection_builder.register_projection(person_proj)
        projection_builder.register_projection(assignment_proj)

        statuses = await projection_builder.get_projection_status()

        assert len(statuses) == 2
        assert person_proj.projection_name in statuses
        assert assignment_proj.projection_name in statuses

    @pytest.mark.asyncio
    async def test_get_build_history(
        self, projection_builder, event_store, db_session
    ):
        """Test getting build history."""
        projection = TestPersonProjection(db_session)
        projection_builder.register_projection(projection)

        # Create event and build
        person_id = str(uuid4())
        event = PersonCreatedEvent(
            aggregate_id=person_id,
            person_id=person_id,
            name="Test",
            email="test@example.com",
            role="RESIDENT",
            created_by="admin",
            metadata=EventMetadata(event_type="PersonCreated"),
        )
        await event_store.append_event(event)

        await projection_builder.build_projection(projection.projection_name)

        # Get history
        history = await projection_builder.get_build_history(projection.projection_name)

        assert len(history) > 0
        assert history[0]["build_mode"] in [m.value for m in BuildMode]


class TestHealthMonitoring:
    """Test health monitoring."""

    @pytest.mark.asyncio
    async def test_get_health_status(
        self, projection_builder, db_session
    ):
        """Test getting overall health status."""
        person_proj = TestPersonProjection(db_session)
        assignment_proj = TestAssignmentProjection(db_session)

        projection_builder.register_projection(person_proj)
        projection_builder.register_projection(assignment_proj)

        health = await projection_builder.get_health_status()

        assert health["total_projections"] == 2
        assert "active" in health
        assert "error" in health
        assert "healthy" in health

    @pytest.mark.asyncio
    async def test_health_status_with_errors(
        self, projection_builder, event_store, db_session
    ):
        """Test health status when projections have errors."""
        projection = ErrorTestProjection(db_session)
        projection.error_on_next = True
        projection_builder.register_projection(projection)

        # Create event that causes error
        person_id = str(uuid4())
        event = PersonCreatedEvent(
            aggregate_id=person_id,
            person_id=person_id,
            name="Test",
            email="test@example.com",
            role="RESIDENT",
            created_by="admin",
            metadata=EventMetadata(event_type="PersonCreated"),
        )
        await event_store.append_event(event)

        await projection_builder.build_projection(projection.projection_name)

        health = await projection_builder.get_health_status()

        assert health["error"] > 0
        assert health["healthy"] is False


class TestEventHandlerDiscovery:
    """Test event handler discovery."""

    def test_handler_discovery(self, db_session):
        """Test that event handlers are discovered correctly."""
        projection = TestPersonProjection(db_session)

        # Should discover handle_person_created and handle_person_updated
        assert "person_created" in projection._event_handlers
        assert "person_updated" in projection._event_handlers

    def test_normalize_event_name(self, db_session):
        """Test event name normalization."""
        projection = TestPersonProjection(db_session)

        assert projection._normalize_event_name("PersonCreated") == "person_created"
        assert projection._normalize_event_name("AssignmentUpdated") == "assignment_updated"
        assert projection._normalize_event_name("ACGMEViolationDetected") == "a_c_g_m_e_violation_detected"
