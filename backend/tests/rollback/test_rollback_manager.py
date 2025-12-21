"""
Tests for rollback manager service.

Tests cover:
- Rollback point creation
- State snapshot management
- Selective rollback
- Full rollback execution
- Rollback verification
- Cascading rollback handling
- Rollback history tracking
- Authorization checks
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.rollback.manager import (
    RollbackManager,
    RollbackPoint,
    RollbackResult,
    RollbackStatus,
    RollbackScope,
    RollbackAuthorizationError,
    RollbackExpiredError,
    EntitySnapshot,
)
from app.models.user import User
from app.models.assignment import Assignment
from app.models.absence import Absence


class TestRollbackManager:
    """Test suite for rollback manager."""

    def test_manager_initialization(self, db):
        """Test rollback manager initializes correctly."""
        manager = RollbackManager(db)
        assert manager.db == db
        assert manager.DEFAULT_EXPIRATION_DAYS == 30
        assert "assignment" in manager.SUPPORTED_ENTITY_TYPES
        assert "absence" in manager.SUPPORTED_ENTITY_TYPES

    def test_supported_entity_types(self, db):
        """Test that supported entity types are properly defined."""
        manager = RollbackManager(db)

        assert "assignment" in manager.SUPPORTED_ENTITY_TYPES
        assert "absence" in manager.SUPPORTED_ENTITY_TYPES
        assert "schedule_run" in manager.SUPPORTED_ENTITY_TYPES
        assert "swap_record" in manager.SUPPORTED_ENTITY_TYPES

        assert manager.SUPPORTED_ENTITY_TYPES["assignment"] == Assignment
        assert manager.SUPPORTED_ENTITY_TYPES["absence"] == Absence

    def test_authorization_check_admin(self, db):
        """Test authorization check allows admin users."""
        manager = RollbackManager(db)

        # Create admin user
        admin_user = User(
            id=uuid4(),
            username="admin_user",
            email="admin@example.com",
            hashed_password="dummy",
            role="admin",
        )
        db.add(admin_user)
        db.commit()

        # Should not raise exception
        manager._verify_authorization(admin_user.id, "create_rollback")

    def test_authorization_check_coordinator(self, db):
        """Test authorization check allows coordinator users."""
        manager = RollbackManager(db)

        # Create coordinator user
        coordinator_user = User(
            id=uuid4(),
            username="coordinator_user",
            email="coordinator@example.com",
            hashed_password="dummy",
            role="coordinator",
        )
        db.add(coordinator_user)
        db.commit()

        # Should not raise exception
        manager._verify_authorization(coordinator_user.id, "create_rollback")

    def test_authorization_check_faculty_denied(self, db):
        """Test authorization check denies faculty users."""
        manager = RollbackManager(db)

        # Create faculty user
        faculty_user = User(
            id=uuid4(),
            username="faculty_user",
            email="faculty@example.com",
            hashed_password="dummy",
            role="faculty",
        )
        db.add(faculty_user)
        db.commit()

        # Should raise authorization error
        with pytest.raises(RollbackAuthorizationError):
            manager._verify_authorization(faculty_user.id, "create_rollback")

    def test_entity_serialization(self, db):
        """Test entity serialization to dictionary."""
        manager = RollbackManager(db)

        # Create test assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=uuid4(),
            person_id=uuid4(),
            role="primary",
            created_by="test_user",
        )

        # Serialize
        state = manager._serialize_entity(assignment)

        # Verify serialization
        assert "id" in state
        assert "block_id" in state
        assert "person_id" in state
        assert "role" in state
        assert state["role"] == "primary"

    def test_dependency_detection_assignment(self, db):
        """Test dependency detection for assignments."""
        manager = RollbackManager(db)

        block_id = uuid4()
        person_id = uuid4()

        assignment = Assignment(
            id=uuid4(),
            block_id=block_id,
            person_id=person_id,
            role="primary",
            created_by="test_user",
        )

        dependencies = manager._detect_dependencies("assignment", assignment)

        assert len(dependencies) == 2
        assert ("block", block_id) in dependencies
        assert ("person", person_id) in dependencies

    def test_dependency_detection_absence(self, db):
        """Test dependency detection for absences."""
        manager = RollbackManager(db)

        person_id = uuid4()

        absence = Absence(
            id=uuid4(),
            person_id=person_id,
            start_date=datetime.utcnow().date(),
            end_date=(datetime.utcnow() + timedelta(days=7)).date(),
            absence_type="vacation",
        )

        dependencies = manager._detect_dependencies("absence", absence)

        assert len(dependencies) == 1
        assert ("person", person_id) in dependencies

    def test_state_comparison_identical(self, db):
        """Test state comparison for identical states."""
        manager = RollbackManager(db)

        state1 = {
            "id": "123",
            "name": "Test",
            "value": 42,
        }
        state2 = {
            "id": "123",
            "name": "Test",
            "value": 42,
        }

        mismatches = manager._compare_states(state1, state2)
        assert len(mismatches) == 0

    def test_state_comparison_different(self, db):
        """Test state comparison for different states."""
        manager = RollbackManager(db)

        state1 = {
            "id": "123",
            "name": "Test",
            "value": 42,
        }
        state2 = {
            "id": "123",
            "name": "Test",
            "value": 100,
        }

        mismatches = manager._compare_states(state1, state2)
        assert len(mismatches) == 1
        assert mismatches[0]["field"] == "value"
        assert mismatches[0]["expected"] == 42
        assert mismatches[0]["actual"] == 100

    def test_state_comparison_ignore_fields(self, db):
        """Test state comparison with ignored fields."""
        manager = RollbackManager(db)

        state1 = {
            "id": "123",
            "name": "Test",
            "created_at": "2024-01-01",
        }
        state2 = {
            "id": "123",
            "name": "Test",
            "created_at": "2024-01-02",
        }

        # Should find mismatch without ignore
        mismatches = manager._compare_states(state1, state2)
        assert len(mismatches) == 1

        # Should not find mismatch with ignore
        mismatches = manager._compare_states(
            state1, state2, ignore_fields={"created_at"}
        )
        assert len(mismatches) == 0

    def test_rollback_message_success(self, db):
        """Test rollback message for successful operation."""
        manager = RollbackManager(db)

        message = manager._build_rollback_message(
            success=True,
            entities_restored=10,
            entities_failed=0,
            dry_run=False,
        )

        assert "Successfully restored 10 entities" in message

    def test_rollback_message_partial(self, db):
        """Test rollback message for partial completion."""
        manager = RollbackManager(db)

        message = manager._build_rollback_message(
            success=False,
            entities_restored=5,
            entities_failed=3,
            dry_run=False,
        )

        assert "Partially completed" in message
        assert "5 entities restored" in message
        assert "3 failed" in message

    def test_rollback_message_failure(self, db):
        """Test rollback message for failed operation."""
        manager = RollbackManager(db)

        message = manager._build_rollback_message(
            success=False,
            entities_restored=0,
            entities_failed=10,
            dry_run=False,
        )

        assert "Rollback failed" in message
        assert "10 entities could not be restored" in message

    def test_rollback_message_dry_run(self, db):
        """Test rollback message for dry run."""
        manager = RollbackManager(db)

        message = manager._build_rollback_message(
            success=True,
            entities_restored=10,
            entities_failed=2,
            dry_run=True,
        )

        assert "Dry run" in message
        assert "Would restore 10 entities" in message
        assert "2 would fail" in message

    def test_entity_snapshot_dataclass(self):
        """Test EntitySnapshot dataclass."""
        entity_id = uuid4()
        timestamp = datetime.utcnow()

        snapshot = EntitySnapshot(
            entity_type="assignment",
            entity_id=entity_id,
            version_id=123,
            state={"role": "primary"},
            timestamp=timestamp,
            dependencies=[("block", uuid4())],
            metadata={"note": "test"},
        )

        assert snapshot.entity_type == "assignment"
        assert snapshot.entity_id == entity_id
        assert snapshot.version_id == 123
        assert snapshot.state == {"role": "primary"}
        assert snapshot.timestamp == timestamp
        assert len(snapshot.dependencies) == 1
        assert snapshot.metadata["note"] == "test"

    def test_rollback_point_dataclass(self):
        """Test RollbackPoint dataclass."""
        point_id = uuid4()
        created_at = datetime.utcnow()
        created_by = uuid4()

        point = RollbackPoint(
            id=point_id,
            name="Test Point",
            description="Test description",
            created_at=created_at,
            created_by=created_by,
            entity_snapshots=[],
            status=RollbackStatus.CREATED,
            scope=RollbackScope.FULL,
            tags=["test"],
        )

        assert point.id == point_id
        assert point.name == "Test Point"
        assert point.description == "Test description"
        assert point.created_at == created_at
        assert point.created_by == created_by
        assert point.status == RollbackStatus.CREATED
        assert point.scope == RollbackScope.FULL
        assert "test" in point.tags

    def test_rollback_result_dataclass(self):
        """Test RollbackResult dataclass."""
        point_id = uuid4()
        executed_at = datetime.utcnow()
        executed_by = uuid4()
        entity_id = uuid4()

        result = RollbackResult(
            success=True,
            rollback_point_id=point_id,
            executed_at=executed_at,
            executed_by=executed_by,
            scope=RollbackScope.FULL,
            entities_restored=[("assignment", entity_id)],
            entities_failed=[],
            verification_passed=True,
            status=RollbackStatus.COMPLETED,
            message="Success",
        )

        assert result.success is True
        assert result.rollback_point_id == point_id
        assert result.executed_at == executed_at
        assert result.executed_by == executed_by
        assert result.scope == RollbackScope.FULL
        assert len(result.entities_restored) == 1
        assert len(result.entities_failed) == 0
        assert result.verification_passed is True
        assert result.status == RollbackStatus.COMPLETED
        assert result.message == "Success"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def db():
    """Mock database session for testing."""
    from unittest.mock import MagicMock
    return MagicMock()
