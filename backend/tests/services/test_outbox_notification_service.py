"""Tests for OutboxNotificationService.

Covers:
- Assignment notifications (created, updated, deleted)
- Swap notifications (requested, approved, rejected, executed)
- Conflict notifications (detected, resolved, escalated)
- Edge cases: missing emails, invalid person IDs, no coordinators
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.outbox_notification_service import OutboxNotificationService


@pytest.fixture
def mock_db():
    """Create a mocked DB session."""
    return MagicMock()


@pytest.fixture
def mock_email_service():
    """Patch EmailService to avoid real email sending."""
    with patch(
        "app.services.outbox_notification_service.EmailService"
    ) as MockEmailService:
        instance = MockEmailService.return_value
        instance.send_email = MagicMock(return_value=True)
        yield instance


@pytest.fixture
def service(mock_db, mock_email_service):
    """Create an OutboxNotificationService with mocked dependencies."""
    svc = OutboxNotificationService(mock_db)
    svc.email_service = mock_email_service
    return svc


# =========================================================================
# _get_person_email
# =========================================================================


class TestGetPersonEmail:
    """Tests for _get_person_email helper."""

    def test_returns_email_when_person_found(self, service, mock_db):
        """Returns email address when person exists."""
        person = MagicMock()
        person.email = "user@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        email = service._get_person_email(str(uuid4()))
        assert email == "user@example.com"

    def test_returns_none_when_person_not_found(self, service, mock_db):
        """Returns None when person does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        email = service._get_person_email(str(uuid4()))
        assert email is None

    def test_returns_none_for_invalid_uuid(self, service):
        """Returns None for a malformed UUID string."""
        email = service._get_person_email("not-a-uuid")
        assert email is None

    def test_accepts_uuid_object(self, service, mock_db):
        """Accepts UUID objects directly, not just strings."""
        person = MagicMock()
        person.email = "uuid@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        email = service._get_person_email(uuid4())
        assert email == "uuid@example.com"


# =========================================================================
# _get_coordinator_emails
# =========================================================================


class TestGetCoordinatorEmails:
    """Tests for _get_coordinator_emails helper."""

    def test_returns_coordinator_emails(self, service, mock_db):
        """Returns emails for active admin/coordinator users."""
        user1 = MagicMock()
        user1.email = "admin@example.com"
        user2 = MagicMock()
        user2.email = "coord@example.com"
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            user1,
            user2,
        ]

        emails = service._get_coordinator_emails()
        assert emails == ["admin@example.com", "coord@example.com"]

    def test_returns_empty_list_when_no_coordinators(self, service, mock_db):
        """Returns empty list when no coordinators exist."""
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        emails = service._get_coordinator_emails()
        assert emails == []

    def test_skips_users_without_email(self, service, mock_db):
        """Skips coordinator users that have no email set."""
        user1 = MagicMock()
        user1.email = "has@example.com"
        user2 = MagicMock()
        user2.email = None
        user3 = MagicMock()
        user3.email = ""
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            user1,
            user2,
            user3,
        ]

        emails = service._get_coordinator_emails()
        assert emails == ["has@example.com"]


# =========================================================================
# Assignment Notifications
# =========================================================================


class TestAssignmentNotifications:
    """Tests for assignment notification methods."""

    def test_notify_assignment_created_success(
        self, service, mock_db, mock_email_service
    ):
        """Successfully sends email for new assignment."""
        person = MagicMock()
        person.email = "resident@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_assignment_created(
            person_id=str(uuid4()),
            block_id=str(uuid4()),
            rotation_id=str(uuid4()),
            payload={"rotation_name": "Sports Medicine", "block_date": "2025-01-06"},
        )

        assert result is True
        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args
        assert "Sports Medicine" in call_args[0][1]  # subject

    def test_notify_assignment_created_no_email(self, service, mock_db):
        """Returns False when person has no email."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.notify_assignment_created(
            person_id=str(uuid4()),
            block_id=str(uuid4()),
            rotation_id=None,
            payload={},
        )

        assert result is False

    def test_notify_assignment_updated_success(
        self, service, mock_db, mock_email_service
    ):
        """Successfully sends email for assignment update."""
        person = MagicMock()
        person.email = "resident@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_assignment_updated(
            person_id=str(uuid4()),
            assignment_id=str(uuid4()),
            old_rotation="SM",
            new_rotation="FMC",
            payload={"old_rotation_name": "Sports Med", "new_rotation_name": "FMC"},
        )

        assert result is True
        mock_email_service.send_email.assert_called_once()

    def test_notify_assignment_deleted_success(
        self, service, mock_db, mock_email_service
    ):
        """Successfully sends email for deleted assignment."""
        person = MagicMock()
        person.email = "resident@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_assignment_deleted(
            person_id=str(uuid4()),
            assignment_id=str(uuid4()),
            payload={"rotation_name": "Night Float", "block_date": "2025-01-06"},
        )

        assert result is True

    def test_notify_assignment_updated_no_email(self, service, mock_db):
        """Returns False when person has no email for update."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.notify_assignment_updated(
            person_id=str(uuid4()),
            assignment_id=str(uuid4()),
            old_rotation=None,
            new_rotation=None,
            payload={},
        )
        assert result is False


# =========================================================================
# Swap Notifications
# =========================================================================


class TestSwapNotifications:
    """Tests for swap notification methods."""

    def test_notify_swap_requested_success(self, service, mock_db, mock_email_service):
        """Successfully sends swap request notification."""
        person = MagicMock()
        person.email = "target@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_swap_requested(
            target_id=str(uuid4()),
            requester_id=str(uuid4()),
            swap_id=str(uuid4()),
            payload={"requester_name": "Dr. Smith", "swap_type": "schedule"},
        )

        assert result is True
        call_args = mock_email_service.send_email.call_args
        assert "Dr. Smith" in call_args[0][1]

    def test_notify_swap_approved_success(self, service, mock_db, mock_email_service):
        """Successfully sends swap approved notification."""
        person = MagicMock()
        person.email = "requester@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_swap_approved(
            requester_id=str(uuid4()),
            swap_id=str(uuid4()),
            payload={"approver_name": "Coordinator"},
        )
        assert result is True

    def test_notify_swap_rejected_with_reason(
        self, service, mock_db, mock_email_service
    ):
        """Includes rejection reason in notification."""
        person = MagicMock()
        person.email = "requester@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_swap_rejected(
            requester_id=str(uuid4()),
            swap_id=str(uuid4()),
            reason="ACGME compliance violation",
            payload={},
        )
        assert result is True
        call_args = mock_email_service.send_email.call_args
        assert "ACGME compliance violation" in call_args[0][2]  # body_html

    def test_notify_swap_rejected_no_reason(self, service, mock_db, mock_email_service):
        """Uses default reason text when no reason provided."""
        person = MagicMock()
        person.email = "requester@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_swap_rejected(
            requester_id=str(uuid4()),
            swap_id=str(uuid4()),
            reason=None,
            payload={},
        )
        assert result is True
        call_args = mock_email_service.send_email.call_args
        assert "No reason provided" in call_args[0][2]

    def test_notify_swap_executed_both_parties(
        self, service, mock_db, mock_email_service
    ):
        """Notifies both requester and target when swap executed."""
        person = MagicMock()
        person.email = "party@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_swap_executed(
            requester_id=str(uuid4()),
            target_id=str(uuid4()),
            swap_id=str(uuid4()),
            payload={"swap_type": "call"},
        )

        assert result is True
        assert mock_email_service.send_email.call_count == 2

    def test_notify_swap_executed_no_target(self, service, mock_db, mock_email_service):
        """Notifies only requester when no target (absorb swap)."""
        person = MagicMock()
        person.email = "requester@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_swap_executed(
            requester_id=str(uuid4()),
            target_id=None,
            swap_id=str(uuid4()),
            payload={"swap_type": "absorb"},
        )

        assert result is True
        assert mock_email_service.send_email.call_count == 1

    def test_notify_swap_executed_all_emails_fail(
        self, service, mock_db, mock_email_service
    ):
        """Returns False when no emails could be sent."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.notify_swap_executed(
            requester_id=str(uuid4()),
            target_id=str(uuid4()),
            swap_id=str(uuid4()),
            payload={},
        )

        assert result is False


# =========================================================================
# Conflict Notifications
# =========================================================================


class TestConflictNotifications:
    """Tests for conflict notification methods."""

    def test_notify_conflict_detected_high_severity(
        self, service, mock_db, mock_email_service
    ):
        """High severity conflicts notify coordinators and affected persons."""
        # Mock coordinator emails
        coordinator = MagicMock()
        coordinator.email = "coord@example.com"
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            coordinator
        ]

        # Mock person email lookup
        person = MagicMock()
        person.email = "resident@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_conflict_detected(
            conflict_id=str(uuid4()),
            conflict_type="leave_overlap",
            severity="high",
            affected_persons=[str(uuid4())],
            payload={},
        )

        assert result is True
        # Coordinator + affected person
        assert mock_email_service.send_email.call_count >= 2

    def test_notify_conflict_detected_low_severity(
        self, service, mock_db, mock_email_service
    ):
        """Low severity conflicts only notify affected persons, not coordinators."""
        person = MagicMock()
        person.email = "resident@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_conflict_detected(
            conflict_id=None,
            conflict_type="scheduling_conflict",
            severity="low",
            affected_persons=[str(uuid4())],
            payload={},
        )

        assert result is True

    def test_notify_conflict_resolved(self, service, mock_db, mock_email_service):
        """Notifies affected persons when conflict is resolved."""
        person = MagicMock()
        person.email = "resident@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = person

        result = service.notify_conflict_resolved(
            conflict_id=str(uuid4()),
            resolution="Automatic reassignment",
            affected_persons=[str(uuid4()), str(uuid4())],
            payload={},
        )

        assert result is True
        assert mock_email_service.send_email.call_count == 2

    def test_notify_conflict_resolved_no_persons(
        self, service, mock_db, mock_email_service
    ):
        """Returns False when no affected persons."""
        result = service.notify_conflict_resolved(
            conflict_id=None,
            resolution="N/A",
            affected_persons=[],
            payload={},
        )

        assert result is False

    def test_notify_conflict_escalated(self, service, mock_db, mock_email_service):
        """Notifies coordinators when conflict is escalated."""
        coordinator = MagicMock()
        coordinator.email = "coord@example.com"
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            coordinator
        ]

        result = service.notify_conflict_escalated(
            conflict_id=str(uuid4()),
            conflict_type="critical_overlap",
            escalation_level=2,
            payload={},
        )

        assert result is True
        call_args = mock_email_service.send_email.call_args
        assert "Level 2" in call_args[0][2]  # body_html

    def test_notify_conflict_escalated_no_coordinators(
        self, service, mock_db, mock_email_service
    ):
        """Returns False when no coordinator emails available."""
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.notify_conflict_escalated(
            conflict_id=None,
            conflict_type="overlap",
            escalation_level=1,
            payload={},
        )

        assert result is False
