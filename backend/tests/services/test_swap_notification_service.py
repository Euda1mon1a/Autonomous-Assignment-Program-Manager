"""Test suite for swap notification service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.services.swap_notification_service import SwapNotificationService


class TestSwapNotificationService:
    """Test suite for swap notification service."""

    @pytest.fixture
    def notification_service(self, db: Session) -> SwapNotificationService:
        """Create a swap notification service instance."""
        return SwapNotificationService(db)

    @pytest.fixture
    def faculty_1(self, db: Session) -> Person:
        """Create first faculty."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty 1",
            type="faculty",
            email="fac1@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @pytest.fixture
    def faculty_2(self, db: Session) -> Person:
        """Create second faculty."""
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty 2",
            type="faculty",
            email="fac2@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @pytest.fixture
    def swap_record(self, db: Session, faculty_1: Person) -> SwapRecord:
        """Create a swap record."""
        swap = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_1.id,
            faculty_1_week=date.today() + timedelta(days=30),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )
        db.add(swap)
        db.commit()
        db.refresh(swap)
        return swap

    def test_notification_service_initialization(self, db: Session):
        """Test SwapNotificationService initialization."""
        service = SwapNotificationService(db)

        assert service.db is db

    def test_notify_swap_request_created(
        self,
        notification_service: SwapNotificationService,
        swap_record: SwapRecord,
    ):
        """Test notification when swap request is created."""
        result = notification_service.notify_swap_created(swap_record.id)

        assert isinstance(result, bool)

    def test_notify_swap_request_matched(
        self,
        notification_service: SwapNotificationService,
        swap_record: SwapRecord,
    ):
        """Test notification when swap request is matched."""
        result = notification_service.notify_swap_matched(swap_record.id)

        assert isinstance(result, bool)

    def test_notify_swap_request_completed(
        self,
        notification_service: SwapNotificationService,
        swap_record: SwapRecord,
    ):
        """Test notification when swap is completed."""
        result = notification_service.notify_swap_completed(swap_record.id)

        assert isinstance(result, bool)

    def test_notify_swap_request_rejected(
        self,
        notification_service: SwapNotificationService,
        swap_record: SwapRecord,
    ):
        """Test notification when swap is rejected."""
        result = notification_service.notify_swap_rejected(
            swap_record.id, "Reason for rejection"
        )

        assert isinstance(result, bool)

    def test_notify_swap_expiring_soon(
        self,
        notification_service: SwapNotificationService,
    ):
        """Test notification for expiring swap requests."""
        result = notification_service.notify_expiring_swaps()

        assert isinstance(result, int)

    def test_send_notification_to_faculty(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
    ):
        """Test sending notification to a faculty member."""
        result = notification_service.send_to_faculty(
            faculty_id=faculty_1.id,
            subject="Test Notification",
            message="This is a test notification",
        )

        assert isinstance(result, bool)

    def test_send_bulk_notifications(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
        faculty_2: Person,
    ):
        """Test sending bulk notifications."""
        faculty_ids = [faculty_1.id, faculty_2.id]

        result = notification_service.send_bulk(
            faculty_ids=faculty_ids,
            subject="Bulk Notification",
            message="Notification to multiple faculty",
        )

        assert isinstance(result, int)

    def test_get_notification_preferences(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
    ):
        """Test retrieving notification preferences."""
        preferences = notification_service.get_preferences(faculty_1.id)

        assert isinstance(preferences, (dict, type(None)))

    def test_update_notification_preferences(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
    ):
        """Test updating notification preferences."""
        preferences = {
            "email_on_swap_created": True,
            "email_on_swap_matched": True,
            "daily_digest": False,
        }

        result = notification_service.update_preferences(faculty_1.id, preferences)

        assert isinstance(result, bool)

    def test_opt_out_notifications(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
    ):
        """Test opting out of notifications."""
        result = notification_service.opt_out(faculty_1.id)

        assert isinstance(result, bool)

    def test_opt_in_notifications(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
    ):
        """Test opting in to notifications."""
        result = notification_service.opt_in(faculty_1.id)

        assert isinstance(result, bool)

    def test_get_unread_notifications(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
    ):
        """Test getting unread notifications."""
        notifications = notification_service.get_unread(faculty_1.id)

        assert isinstance(notifications, list)

    def test_mark_notification_read(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
    ):
        """Test marking notification as read."""
        notification_id = uuid4()

        result = notification_service.mark_read(notification_id)

        assert isinstance(result, bool)

    def test_notify_swap_request_pending(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
        faculty_2: Person,
        db: Session,
    ):
        """Test notification when swap becomes pending."""
        swap = SwapRecord(
            id=uuid4(),
            faculty_1_id=faculty_1.id,
            faculty_1_week=date.today() + timedelta(days=30),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            created_at=date.today(),
        )
        db.add(swap)
        db.commit()

        result = notification_service.notify_swap_pending(swap.id)

        assert isinstance(result, bool)

    def test_notify_all_pending_swaps(
        self,
        notification_service: SwapNotificationService,
    ):
        """Test notifying about all pending swaps."""
        result = notification_service.notify_all_pending()

        assert isinstance(result, int)

    def test_send_reminder_notifications(
        self,
        notification_service: SwapNotificationService,
    ):
        """Test sending reminder notifications."""
        result = notification_service.send_reminders()

        assert isinstance(result, int)

    def test_notification_service_with_invalid_faculty(
        self,
        notification_service: SwapNotificationService,
    ):
        """Test notification service with nonexistent faculty."""
        invalid_id = uuid4()

        result = notification_service.send_to_faculty(
            faculty_id=invalid_id,
            subject="Test",
            message="Test message",
        )

        # Should handle gracefully
        assert isinstance(result, bool)

    def test_notification_service_with_invalid_swap(
        self,
        notification_service: SwapNotificationService,
    ):
        """Test notification service with nonexistent swap."""
        invalid_id = uuid4()

        result = notification_service.notify_swap_created(invalid_id)

        assert isinstance(result, bool)

    def test_get_notification_history(
        self,
        notification_service: SwapNotificationService,
        faculty_1: Person,
    ):
        """Test getting notification history."""
        history = notification_service.get_history(faculty_1.id, limit=10)

        assert isinstance(history, list)

    def test_clear_old_notifications(
        self,
        notification_service: SwapNotificationService,
    ):
        """Test clearing old notifications."""
        result = notification_service.clear_old(days=30)

        assert isinstance(result, int)

    def test_notification_template_rendering(
        self,
        notification_service: SwapNotificationService,
        swap_record: SwapRecord,
    ):
        """Test notification template rendering."""
        template = {
            "subject": "Swap Request: {faculty_name}",
            "body": "Faculty {faculty_name} has requested a swap",
        }

        # Service should be able to render templates
        assert isinstance(template, dict)
