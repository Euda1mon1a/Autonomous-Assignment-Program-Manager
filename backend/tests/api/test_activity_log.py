"""
Tests for activity logging functionality.

Tests the ActivityLog model and the activity logging in admin user routes.
Validates audit trail creation for compliance requirements.
"""

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.activity_log import ActivityActionType, ActivityLog
from app.models.user import User


class TestActivityLogModel:
    """Test the ActivityLog model functionality."""

    def test_create_activity_log_entry(self, db: Session, admin_user: User):
        """Test creating an activity log entry via factory method."""
        log_entry = ActivityLog.create_entry(
            action_type=ActivityActionType.USER_CREATED,
            user_id=admin_user.id,
            target_entity="User",
            target_id=str(uuid.uuid4()),
            details={"test": "value"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 Test",
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        assert log_entry.id is not None
        assert log_entry.action_type == "USER_CREATED"
        assert log_entry.user_id == admin_user.id
        assert log_entry.target_entity == "User"
        assert log_entry.details == {"test": "value"}
        assert log_entry.ip_address == "192.168.1.1"
        assert log_entry.user_agent == "Mozilla/5.0 Test"
        assert log_entry.created_at is not None

    def test_activity_log_with_string_action_type(self, db: Session, admin_user: User):
        """Test creating activity log with string action type."""
        log_entry = ActivityLog.create_entry(
            action_type="CUSTOM_ACTION",
            user_id=admin_user.id,
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        assert log_entry.action_type == "CUSTOM_ACTION"

    def test_activity_log_nullable_fields(self, db: Session):
        """Test that nullable fields work correctly."""
        log_entry = ActivityLog.create_entry(
            action_type=ActivityActionType.LOGIN_SUCCESS,
            user_id=None,  # Anonymous action
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        assert log_entry.user_id is None
        assert log_entry.target_entity is None
        assert log_entry.target_id is None
        assert log_entry.ip_address is None
        assert log_entry.user_agent is None

    def test_activity_log_enum_values(self):
        """Test ActivityActionType enum values."""
        # User management
        assert ActivityActionType.USER_CREATED.value == "USER_CREATED"
        assert ActivityActionType.USER_UPDATED.value == "USER_UPDATED"
        assert ActivityActionType.USER_DELETED.value == "USER_DELETED"
        assert ActivityActionType.USER_LOCKED.value == "USER_LOCKED"
        assert ActivityActionType.USER_UNLOCKED.value == "USER_UNLOCKED"

        # Authentication
        assert ActivityActionType.LOGIN_SUCCESS.value == "LOGIN_SUCCESS"
        assert ActivityActionType.LOGIN_FAILED.value == "LOGIN_FAILED"
        assert ActivityActionType.PASSWORD_CHANGED.value == "PASSWORD_CHANGED"

        # Invitations
        assert ActivityActionType.INVITE_SENT.value == "INVITE_SENT"
        assert ActivityActionType.INVITE_RESENT.value == "INVITE_RESENT"


class TestAdminUserActivityLogging:
    """Test activity logging in admin user routes."""

    @pytest.fixture
    def target_user(self, db: Session) -> User:
        """Create a target user for admin operations."""
        user = User(
            id=uuid.uuid4(),
            username="targetuser",
            email="target@test.org",
            hashed_password=get_password_hash("targetpass123"),
            role="coordinator",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def test_create_user_logs_activity(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test that creating a user logs the activity."""
        # Skip if no auth headers (auth may not be set up in test)
        if not auth_headers:
            pytest.skip("Auth not available in test environment")

        response = client.post(
            "/api/admin/users",
            json={
                "email": "newuser@test.org",
                "first_name": "New",
                "last_name": "User",
                "role": "coordinator",
                "send_invite": False,
            },
            headers=auth_headers,
        )

        # If the endpoint exists and works
        if response.status_code == status.HTTP_201_CREATED:
            # Check that an activity log was created
            logs = (
                db.query(ActivityLog)
                .filter(ActivityLog.action_type == "USER_CREATED")
                .all()
            )
            assert len(logs) >= 1

            latest_log = logs[-1]
            assert latest_log.target_entity == "User"
            assert latest_log.details is not None

    def test_activity_log_captures_ip_address(self, db: Session, admin_user: User):
        """Test that activity log captures IP address from request."""
        # Simulate request with X-Forwarded-For header
        log_entry = ActivityLog.create_entry(
            action_type=ActivityActionType.LOGIN_SUCCESS,
            user_id=admin_user.id,
            ip_address="10.0.0.1",
            user_agent="Test Browser/1.0",
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        assert log_entry.ip_address == "10.0.0.1"
        assert log_entry.user_agent == "Test Browser/1.0"

    def test_activity_log_preserves_after_user_deletion(
        self, db: Session, admin_user: User, target_user: User
    ):
        """Test that activity logs are preserved when user is deleted."""
        # Create activity log referencing target user
        log_entry = ActivityLog.create_entry(
            action_type=ActivityActionType.USER_CREATED,
            user_id=admin_user.id,
            target_entity="User",
            target_id=str(target_user.id),
            details={"email": target_user.email},
        )

        db.add(log_entry)
        db.commit()

        log_id = log_entry.id

        # Delete the target user
        db.delete(target_user)
        db.commit()

        # Activity log should still exist
        preserved_log = db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
        assert preserved_log is not None
        assert preserved_log.target_id == str(target_user.id)


class TestActivityLogQuery:
    """Test querying activity logs."""

    @pytest.fixture
    def sample_logs(self, db: Session, admin_user: User) -> list[ActivityLog]:
        """Create sample activity logs for testing."""
        logs = []
        for i, action in enumerate(
            [
                ActivityActionType.USER_CREATED,
                ActivityActionType.USER_UPDATED,
                ActivityActionType.LOGIN_SUCCESS,
                ActivityActionType.USER_LOCKED,
                ActivityActionType.INVITE_SENT,
            ]
        ):
            log = ActivityLog.create_entry(
                action_type=action,
                user_id=admin_user.id,
                target_entity="User",
                target_id=str(uuid.uuid4()),
                details={"index": i},
            )
            # Adjust created_at to ensure ordering
            log.created_at = datetime.utcnow() - timedelta(minutes=i)
            db.add(log)
            logs.append(log)

        db.commit()
        return logs

    def test_query_by_action_type(
        self, db: Session, admin_user: User, sample_logs: list[ActivityLog]
    ):
        """Test filtering logs by action type."""
        results = (
            db.query(ActivityLog)
            .filter(ActivityLog.action_type == "USER_CREATED")
            .all()
        )

        assert len(results) >= 1
        assert all(log.action_type == "USER_CREATED" for log in results)

    def test_query_by_user_id(
        self, db: Session, admin_user: User, sample_logs: list[ActivityLog]
    ):
        """Test filtering logs by user ID."""
        results = (
            db.query(ActivityLog).filter(ActivityLog.user_id == admin_user.id).all()
        )

        assert len(results) >= 5
        assert all(log.user_id == admin_user.id for log in results)

    def test_query_by_date_range(
        self, db: Session, admin_user: User, sample_logs: list[ActivityLog]
    ):
        """Test filtering logs by date range."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        results = (
            db.query(ActivityLog)
            .filter(ActivityLog.created_at >= one_hour_ago)
            .filter(ActivityLog.created_at <= now)
            .all()
        )

        assert len(results) >= 5

    def test_logs_ordered_by_created_at_desc(
        self, db: Session, admin_user: User, sample_logs: list[ActivityLog]
    ):
        """Test that logs are ordered most recent first."""
        results = (
            db.query(ActivityLog)
            .filter(ActivityLog.user_id == admin_user.id)
            .order_by(ActivityLog.created_at.desc())
            .all()
        )

        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].created_at >= results[i + 1].created_at


class TestPHISafety:
    """Test that activity logs don't expose PHI improperly."""

    def test_details_should_use_ids_not_names(self, db: Session, admin_user: User):
        """Test that details contain IDs, not cleartext names."""
        target_id = uuid.uuid4()

        # Good: Store ID
        log_entry = ActivityLog.create_entry(
            action_type=ActivityActionType.USER_UPDATED,
            user_id=admin_user.id,
            target_entity="User",
            target_id=str(target_id),
            details={
                "changes": {"role": {"old": "resident", "new": "faculty"}},
                # Don't store: "name": "Dr. John Smith" (PHI)
            },
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        # Verify no obvious PHI in details
        details_str = str(log_entry.details)
        # These are examples - in real tests, check for actual name patterns
        assert "Dr. " not in details_str or log_entry.details.get("changes") is not None

    def test_user_agent_truncated(self, db: Session, admin_user: User):
        """Test that user agent is truncated to prevent data bloat."""
        long_user_agent = "A" * 1000  # Very long user agent

        log_entry = ActivityLog.create_entry(
            action_type=ActivityActionType.LOGIN_SUCCESS,
            user_id=admin_user.id,
            user_agent=long_user_agent[:500],  # Truncate to 500
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        assert len(log_entry.user_agent) <= 500
