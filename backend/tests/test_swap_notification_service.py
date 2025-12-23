"""Tests for SwapNotificationService."""

from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.services.swap_notification_service import (
    SwapNotification,
    SwapNotificationService,
    SwapNotificationType,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def faculty_id():
    """Sample faculty ID."""
    return uuid4()


@pytest.fixture
def requester_id():
    """Sample requester ID."""
    return uuid4()


@pytest.fixture
def swap_id():
    """Sample swap ID."""
    return uuid4()


@pytest.fixture
def sample_week():
    """Sample week date."""
    return date.today() + timedelta(days=14)


@pytest.fixture
def sample_faculty(faculty_id):
    """Sample faculty member."""
    faculty = Mock(spec=Person)
    faculty.id = faculty_id
    faculty.name = "Dr. Jane Smith"
    faculty.email = "jane.smith@hospital.org"
    faculty.type = "faculty"
    return faculty


@pytest.fixture
def sample_requester(requester_id):
    """Sample requester faculty member."""
    requester = Mock(spec=Person)
    requester.id = requester_id
    requester.name = "Dr. John Doe"
    requester.email = "john.doe@hospital.org"
    requester.type = "faculty"
    return requester


@pytest.fixture
def sample_preferences(faculty_id):
    """Sample faculty preferences with all notifications enabled."""
    prefs = Mock(spec=FacultyPreference)
    prefs.faculty_id = faculty_id
    prefs.notify_swap_requests = True
    prefs.notify_schedule_changes = True
    prefs.notify_conflict_alerts = True
    prefs.notify_reminder_days = 7
    return prefs


@pytest.fixture
def service_with_faculty(mock_db, sample_faculty, sample_preferences):
    """Create service with mocked faculty and preferences."""
    # Mock the query chain for faculty
    faculty_query = Mock()
    faculty_query.filter.return_value.first.return_value = sample_faculty

    # Mock the query chain for preferences
    prefs_query = Mock()
    prefs_query.filter.return_value.first.return_value = sample_preferences

    # Set up query to return appropriate mock based on model
    def query_side_effect(model):
        if model == Person:
            return faculty_query
        elif model == FacultyPreference:
            return prefs_query
        return Mock()

    mock_db.query = Mock(side_effect=query_side_effect)

    return SwapNotificationService(db=mock_db)


# ============================================================================
# Test SwapNotification Dataclass
# ============================================================================


class TestSwapNotification:
    """Tests for SwapNotification dataclass."""

    def test_create_notification(self, faculty_id, swap_id, sample_week):
        """Test creating a basic notification."""
        notification = SwapNotification(
            recipient_id=faculty_id,
            recipient_email="test@hospital.org",
            notification_type=SwapNotificationType.SWAP_REQUEST_RECEIVED,
            subject="Test Subject",
            body="Test Body",
            swap_id=swap_id,
            week=sample_week,
        )

        assert notification.recipient_id == faculty_id
        assert notification.recipient_email == "test@hospital.org"
        assert (
            notification.notification_type == SwapNotificationType.SWAP_REQUEST_RECEIVED
        )
        assert notification.subject == "Test Subject"
        assert notification.body == "Test Body"
        assert notification.swap_id == swap_id
        assert notification.week == sample_week
        assert isinstance(notification.created_at, datetime)

    def test_notification_auto_timestamp(self):
        """Test that created_at is automatically set."""
        notification = SwapNotification(
            recipient_id=uuid4(),
            recipient_email="test@hospital.org",
            notification_type=SwapNotificationType.SWAP_EXECUTED,
            subject="Test",
            body="Test",
        )

        assert notification.created_at is not None
        # Should be very recent (within last second)
        assert datetime.utcnow() - notification.created_at < timedelta(seconds=1)

    def test_notification_optional_fields(self):
        """Test notification with optional fields as None."""
        notification = SwapNotification(
            recipient_id=uuid4(),
            recipient_email="test@hospital.org",
            notification_type=SwapNotificationType.SWAP_ROLLED_BACK,
            subject="Test",
            body="Test",
            swap_id=None,
            week=None,
        )

        assert notification.swap_id is None
        assert notification.week is None


# ============================================================================
# Test SwapNotificationType Enum
# ============================================================================


class TestSwapNotificationType:
    """Tests for SwapNotificationType enum."""

    def test_notification_types_exist(self):
        """Test all expected notification types."""
        assert SwapNotificationType.SWAP_REQUEST_RECEIVED == "swap_request_received"
        assert SwapNotificationType.SWAP_REQUEST_ACCEPTED == "swap_request_accepted"
        assert SwapNotificationType.SWAP_REQUEST_REJECTED == "swap_request_rejected"
        assert SwapNotificationType.SWAP_EXECUTED == "swap_executed"
        assert SwapNotificationType.SWAP_ROLLED_BACK == "swap_rolled_back"
        assert SwapNotificationType.SWAP_REMINDER == "swap_reminder"
        assert SwapNotificationType.MARKETPLACE_MATCH == "marketplace_match"


# ============================================================================
# Test notify_swap_request_received
# ============================================================================


class TestNotifySwapRequestReceived:
    """Tests for notify_swap_request_received method."""

    def test_creates_notification_successfully(
        self, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test successful notification creation."""
        notification = service_with_faculty.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. John Doe",
            week_offered=sample_week,
            swap_id=swap_id,
            reason="Conference attendance",
        )

        assert notification is not None
        assert notification.recipient_id == faculty_id
        assert notification.recipient_email == "jane.smith@hospital.org"
        assert (
            notification.notification_type == SwapNotificationType.SWAP_REQUEST_RECEIVED
        )
        assert "Dr. John Doe" in notification.subject
        assert "Dr. John Doe" in notification.body
        assert sample_week.isoformat() in notification.body
        assert "Conference attendance" in notification.body
        assert notification.swap_id == swap_id
        assert notification.week == sample_week

        # Verify it was added to pending notifications
        assert service_with_faculty.get_pending_count() == 1

    def test_notification_without_reason(
        self, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test notification without optional reason."""
        notification = service_with_faculty.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. John Doe",
            week_offered=sample_week,
            swap_id=swap_id,
            reason=None,
        )

        assert notification is not None
        assert "Dr. John Doe" in notification.body
        # Body should still be well-formed without reason
        assert notification.body.strip().endswith("request.")

    def test_respects_notification_preferences_disabled(
        self, mock_db, faculty_id, swap_id, sample_week, sample_faculty
    ):
        """Test notification is not sent when preferences disabled."""
        # Create preferences with swap requests disabled
        prefs = Mock(spec=FacultyPreference)
        prefs.notify_swap_requests = False

        # Set up query mocks
        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = sample_faculty

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = prefs

        def query_side_effect(model):
            if model == Person:
                return faculty_query
            elif model == FacultyPreference:
                return prefs_query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notification = service.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. John Doe",
            week_offered=sample_week,
            swap_id=swap_id,
        )

        assert notification is None
        assert service.get_pending_count() == 0

    def test_faculty_not_found(self, mock_db, swap_id, sample_week):
        """Test notification when faculty not found."""
        # Mock query to return None for faculty
        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = None

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Person:
                return faculty_query
            elif model == FacultyPreference:
                return prefs_query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notification = service.notify_swap_request_received(
            recipient_faculty_id=uuid4(),
            requester_name="Dr. John Doe",
            week_offered=sample_week,
            swap_id=swap_id,
        )

        assert notification is None
        assert service.get_pending_count() == 0

    def test_no_preferences_defaults_to_notify(
        self, mock_db, faculty_id, swap_id, sample_week, sample_faculty
    ):
        """Test that missing preferences defaults to sending notification."""
        # Mock query to return None for preferences
        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = sample_faculty

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Person:
                return faculty_query
            elif model == FacultyPreference:
                return prefs_query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notification = service.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. John Doe",
            week_offered=sample_week,
            swap_id=swap_id,
        )

        assert notification is not None
        assert service.get_pending_count() == 1

    def test_faculty_without_email(
        self, mock_db, faculty_id, swap_id, sample_week, sample_preferences
    ):
        """Test notification for faculty without email (generates default)."""
        # Faculty without email
        faculty = Mock(spec=Person)
        faculty.id = faculty_id
        faculty.name = "Dr. Jane Smith"
        faculty.email = None

        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = faculty

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = sample_preferences

        def query_side_effect(model):
            if model == Person:
                return faculty_query
            elif model == FacultyPreference:
                return prefs_query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notification = service.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. John Doe",
            week_offered=sample_week,
            swap_id=swap_id,
        )

        assert notification is not None
        # Should generate email from name (note: "Dr. Jane Smith" -> "dr..jane.smith")
        assert notification.recipient_email == "dr..jane.smith@example.com"


# ============================================================================
# Test notify_swap_accepted
# ============================================================================


class TestNotifySwapAccepted:
    """Tests for notify_swap_accepted method."""

    def test_creates_notification_successfully(
        self, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test successful acceptance notification."""
        notification = service_with_faculty.notify_swap_accepted(
            recipient_faculty_id=faculty_id,
            accepter_name="Dr. Alice Johnson",
            week=sample_week,
            swap_id=swap_id,
        )

        assert notification is not None
        assert notification.recipient_id == faculty_id
        assert (
            notification.notification_type == SwapNotificationType.SWAP_REQUEST_ACCEPTED
        )
        assert "Dr. Alice Johnson" in notification.subject
        assert "accepted" in notification.subject.lower()
        assert "Dr. Alice Johnson" in notification.body
        assert sample_week.isoformat() in notification.body
        assert notification.swap_id == swap_id
        assert notification.week == sample_week
        assert service_with_faculty.get_pending_count() == 1

    def test_respects_notification_preferences(
        self, mock_db, faculty_id, swap_id, sample_week, sample_faculty
    ):
        """Test notification respects preferences."""
        prefs = Mock(spec=FacultyPreference)
        prefs.notify_swap_requests = False

        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = sample_faculty

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = prefs

        def query_side_effect(model):
            if model == Person:
                return faculty_query
            elif model == FacultyPreference:
                return prefs_query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notification = service.notify_swap_accepted(
            recipient_faculty_id=faculty_id,
            accepter_name="Dr. Alice Johnson",
            week=sample_week,
            swap_id=swap_id,
        )

        assert notification is None
        assert service.get_pending_count() == 0

    def test_faculty_not_found(self, mock_db, swap_id, sample_week):
        """Test when recipient faculty not found."""
        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = None

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Person:
                return faculty_query
            elif model == FacultyPreference:
                return prefs_query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notification = service.notify_swap_accepted(
            recipient_faculty_id=uuid4(),
            accepter_name="Dr. Alice Johnson",
            week=sample_week,
            swap_id=swap_id,
        )

        assert notification is None


# ============================================================================
# Test notify_swap_rejected
# ============================================================================


class TestNotifySwapRejected:
    """Tests for notify_swap_rejected method."""

    def test_creates_notification_with_reason(
        self, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test rejection notification with reason."""
        notification = service_with_faculty.notify_swap_rejected(
            recipient_faculty_id=faculty_id,
            rejecter_name="Dr. Bob Wilson",
            week=sample_week,
            swap_id=swap_id,
            reason="Already committed to another obligation",
        )

        assert notification is not None
        assert (
            notification.notification_type == SwapNotificationType.SWAP_REQUEST_REJECTED
        )
        assert "Dr. Bob Wilson" in notification.subject
        assert "declined" in notification.subject.lower()
        assert "Dr. Bob Wilson" in notification.body
        assert sample_week.isoformat() in notification.body
        assert "Already committed to another obligation" in notification.body
        assert notification.swap_id == swap_id
        assert service_with_faculty.get_pending_count() == 1

    def test_creates_notification_without_reason(
        self, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test rejection notification without reason."""
        notification = service_with_faculty.notify_swap_rejected(
            recipient_faculty_id=faculty_id,
            rejecter_name="Dr. Bob Wilson",
            week=sample_week,
            swap_id=swap_id,
            reason=None,
        )

        assert notification is not None
        assert "Dr. Bob Wilson" in notification.body
        # Should still have helpful content without reason
        assert "marketplace" in notification.body.lower()

    def test_respects_notification_preferences(
        self, mock_db, faculty_id, swap_id, sample_week, sample_faculty
    ):
        """Test notification respects preferences."""
        prefs = Mock(spec=FacultyPreference)
        prefs.notify_swap_requests = False

        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = sample_faculty

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = prefs

        def query_side_effect(model):
            if model == Person:
                return faculty_query
            elif model == FacultyPreference:
                return prefs_query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notification = service.notify_swap_rejected(
            recipient_faculty_id=faculty_id,
            rejecter_name="Dr. Bob Wilson",
            week=sample_week,
            swap_id=swap_id,
        )

        assert notification is None


# ============================================================================
# Test notify_swap_executed
# ============================================================================


class TestNotifySwapExecuted:
    """Tests for notify_swap_executed method."""

    def test_notifies_all_parties(self, mock_db, swap_id, sample_week):
        """Test that all parties receive execution notifications."""
        faculty_ids = [uuid4(), uuid4(), uuid4()]

        # Create faculty mocks
        faculty_list = []
        for fid in faculty_ids:
            faculty = Mock(spec=Person)
            faculty.id = fid
            faculty.name = f"Dr. Faculty {fid}"
            faculty.email = f"faculty{fid}@hospital.org"
            faculty_list.append(faculty)

        # Create preferences - all enabled for schedule changes
        prefs = Mock(spec=FacultyPreference)
        prefs.notify_schedule_changes = True

        call_count = [0]  # Use list to make it mutable in closure

        def query_side_effect(model):
            if model == Person:
                query = Mock()

                # Return faculty in order based on call count
                def filter_func(*args, **kwargs):
                    result = Mock()
                    idx = call_count[0] % len(faculty_list)
                    result.first.return_value = faculty_list[idx]
                    call_count[0] += 1
                    return result

                query.filter = filter_func
                return query
            elif model == FacultyPreference:
                query = Mock()
                query.filter.return_value.first.return_value = prefs
                return query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        details = "Swap completed: Week A exchanged with Week B"
        notifications = service.notify_swap_executed(
            faculty_ids=faculty_ids,
            week=sample_week,
            swap_id=swap_id,
            details=details,
        )

        assert len(notifications) == 3
        for i, notification in enumerate(notifications):
            assert notification.recipient_id == faculty_ids[i]
            assert notification.notification_type == SwapNotificationType.SWAP_EXECUTED
            assert details in notification.body
            assert sample_week.isoformat() in notification.subject
            assert notification.swap_id == swap_id

        assert service.get_pending_count() == 3

    def test_respects_individual_preferences(self, mock_db, swap_id, sample_week):
        """Test that each faculty's preferences are respected."""
        faculty_ids = [uuid4(), uuid4()]

        # First faculty wants notifications
        faculty1 = Mock(spec=Person)
        faculty1.id = faculty_ids[0]
        faculty1.name = "Dr. Notify Me"
        faculty1.email = "notify@hospital.org"

        prefs1 = Mock(spec=FacultyPreference)
        prefs1.notify_schedule_changes = True

        # Second faculty doesn't want notifications
        faculty2 = Mock(spec=Person)
        faculty2.id = faculty_ids[1]
        faculty2.name = "Dr. No Notify"
        faculty2.email = "no-notify@hospital.org"

        prefs2 = Mock(spec=FacultyPreference)
        prefs2.notify_schedule_changes = False

        # Track calls separately for each model
        person_calls = [0]
        prefs_calls = [0]

        def query_side_effect(model):
            if model == Person:
                query = Mock()

                def filter_func(*args, **kwargs):
                    result = Mock()
                    # Return faculty1 for first call, faculty2 for second
                    result.first.return_value = (
                        faculty1 if person_calls[0] == 0 else faculty2
                    )
                    person_calls[0] += 1
                    return result

                query.filter = filter_func
                return query
            elif model == FacultyPreference:
                query = Mock()

                def filter_func(*args, **kwargs):
                    result = Mock()
                    # Return prefs1 for first call, prefs2 for second
                    result.first.return_value = (
                        prefs1 if prefs_calls[0] == 0 else prefs2
                    )
                    prefs_calls[0] += 1
                    return result

                query.filter = filter_func
                return query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notifications = service.notify_swap_executed(
            faculty_ids=faculty_ids,
            week=sample_week,
            swap_id=swap_id,
            details="Swap completed",
        )

        # Only first faculty should receive notification
        assert len(notifications) == 1
        assert notifications[0].recipient_id == faculty_ids[0]
        assert service.get_pending_count() == 1

    def test_handles_faculty_not_found(self, mock_db, swap_id, sample_week):
        """Test graceful handling when faculty not found."""
        faculty_ids = [uuid4(), uuid4()]

        # Only first faculty exists
        faculty1 = Mock(spec=Person)
        faculty1.id = faculty_ids[0]
        faculty1.name = "Dr. Exists"
        faculty1.email = "exists@hospital.org"

        prefs = Mock(spec=FacultyPreference)
        prefs.notify_schedule_changes = True

        call_count = [0]

        def query_side_effect(model):
            if model == Person:
                query = Mock()

                def filter_func(*args, **kwargs):
                    result = Mock()
                    # Return faculty1 for first, None for second
                    result.first.return_value = faculty1 if call_count[0] == 0 else None
                    call_count[0] += 1
                    return result

                query.filter = filter_func
                return query
            elif model == FacultyPreference:
                query = Mock()
                query.filter.return_value.first.return_value = prefs
                return query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notifications = service.notify_swap_executed(
            faculty_ids=faculty_ids,
            week=sample_week,
            swap_id=swap_id,
            details="Swap completed",
        )

        # Only first faculty should get notification
        assert len(notifications) == 1
        assert notifications[0].recipient_id == faculty_ids[0]

    def test_empty_faculty_list(self, mock_db, swap_id, sample_week):
        """Test with empty faculty list."""
        service = SwapNotificationService(db=mock_db)

        notifications = service.notify_swap_executed(
            faculty_ids=[],
            week=sample_week,
            swap_id=swap_id,
            details="Swap completed",
        )

        assert len(notifications) == 0
        assert service.get_pending_count() == 0


# ============================================================================
# Test notify_swap_rolled_back
# ============================================================================


class TestNotifySwapRolledBack:
    """Tests for notify_swap_rolled_back method."""

    def test_notifies_all_parties(self, mock_db, swap_id, sample_week):
        """Test that all parties receive rollback notifications."""
        faculty_ids = [uuid4(), uuid4()]

        faculty_list = []
        for i, fid in enumerate(faculty_ids):
            faculty = Mock(spec=Person)
            faculty.id = fid
            faculty.name = f"Dr. Faculty {i + 1}"
            faculty.email = f"faculty{i + 1}@hospital.org"
            faculty_list.append(faculty)

        call_count = [0]

        def query_side_effect(model):
            if model == Person:
                query = Mock()

                def filter_func(*args, **kwargs):
                    result = Mock()
                    idx = call_count[0] % len(faculty_list)
                    result.first.return_value = faculty_list[idx]
                    call_count[0] += 1
                    return result

                query.filter = filter_func
                return query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        reason = "Conflict detected after execution"
        notifications = service.notify_swap_rolled_back(
            faculty_ids=faculty_ids,
            week=sample_week,
            swap_id=swap_id,
            reason=reason,
        )

        assert len(notifications) == 2
        for i, notification in enumerate(notifications):
            assert notification.recipient_id == faculty_ids[i]
            assert (
                notification.notification_type == SwapNotificationType.SWAP_ROLLED_BACK
            )
            assert reason in notification.body
            assert "rolled back" in notification.body.lower()
            assert sample_week.isoformat() in notification.subject
            assert notification.swap_id == swap_id

        assert service.get_pending_count() == 2

    def test_does_not_check_preferences(self, mock_db, swap_id, sample_week):
        """Test that rollback notifications ignore preferences (critical info)."""
        faculty_id = uuid4()

        faculty = Mock(spec=Person)
        faculty.id = faculty_id
        faculty.name = "Dr. Important"
        faculty.email = "important@hospital.org"

        # Even with all preferences disabled, should still notify
        prefs = Mock(spec=FacultyPreference)
        prefs.notify_schedule_changes = False
        prefs.notify_swap_requests = False

        def query_side_effect(model):
            if model == Person:
                query = Mock()
                query.filter.return_value.first.return_value = faculty
                return query
            elif model == FacultyPreference:
                query = Mock()
                query.filter.return_value.first.return_value = prefs
                return query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notifications = service.notify_swap_rolled_back(
            faculty_ids=[faculty_id],
            week=sample_week,
            swap_id=swap_id,
            reason="System error",
        )

        # Should still notify despite preferences
        assert len(notifications) == 1
        assert notifications[0].recipient_id == faculty_id

    def test_handles_faculty_not_found(self, mock_db, swap_id, sample_week):
        """Test graceful handling when faculty not found."""
        faculty_ids = [uuid4(), uuid4()]

        faculty1 = Mock(spec=Person)
        faculty1.id = faculty_ids[0]
        faculty1.name = "Dr. Exists"
        faculty1.email = "exists@hospital.org"

        call_count = [0]

        def query_side_effect(model):
            if model == Person:
                query = Mock()

                def filter_func(*args, **kwargs):
                    result = Mock()
                    result.first.return_value = faculty1 if call_count[0] == 0 else None
                    call_count[0] += 1
                    return result

                query.filter = filter_func
                return query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notifications = service.notify_swap_rolled_back(
            faculty_ids=faculty_ids,
            week=sample_week,
            swap_id=swap_id,
            reason="Error occurred",
        )

        # Only found faculty should be notified
        assert len(notifications) == 1
        assert notifications[0].recipient_id == faculty_ids[0]


# ============================================================================
# Test notify_marketplace_match
# ============================================================================


class TestNotifyMarketplaceMatch:
    """Tests for notify_marketplace_match method."""

    def test_creates_notification_successfully(
        self, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test successful marketplace match notification."""
        notification = service_with_faculty.notify_marketplace_match(
            recipient_faculty_id=faculty_id,
            poster_name="Dr. Carol Martinez",
            week_available=sample_week,
            request_id=swap_id,
        )

        assert notification is not None
        assert notification.recipient_id == faculty_id
        assert notification.notification_type == SwapNotificationType.MARKETPLACE_MATCH
        assert "Dr. Carol Martinez" in notification.body
        assert sample_week.isoformat() in notification.subject
        assert "marketplace" in notification.body.lower()
        assert notification.swap_id == swap_id
        assert notification.week == sample_week
        assert service_with_faculty.get_pending_count() == 1

    def test_respects_notification_preferences(
        self, mock_db, faculty_id, swap_id, sample_week, sample_faculty
    ):
        """Test notification respects preferences."""
        prefs = Mock(spec=FacultyPreference)
        prefs.notify_swap_requests = False

        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = sample_faculty

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = prefs

        def query_side_effect(model):
            if model == Person:
                return faculty_query
            elif model == FacultyPreference:
                return prefs_query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        notification = service.notify_marketplace_match(
            recipient_faculty_id=faculty_id,
            poster_name="Dr. Carol Martinez",
            week_available=sample_week,
            request_id=swap_id,
        )

        assert notification is None
        assert service.get_pending_count() == 0


# ============================================================================
# Test send_pending_notifications and get_pending_count
# ============================================================================


class TestPendingNotificationManagement:
    """Tests for notification queue management."""

    def test_get_pending_count_empty(self, mock_db):
        """Test pending count starts at zero."""
        service = SwapNotificationService(db=mock_db)
        assert service.get_pending_count() == 0

    def test_get_pending_count_increments(
        self, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test pending count increments as notifications are added."""
        assert service_with_faculty.get_pending_count() == 0

        service_with_faculty.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. Test",
            week_offered=sample_week,
            swap_id=swap_id,
        )
        assert service_with_faculty.get_pending_count() == 1

        service_with_faculty.notify_swap_accepted(
            recipient_faculty_id=faculty_id,
            accepter_name="Dr. Test",
            week=sample_week,
            swap_id=swap_id,
        )
        assert service_with_faculty.get_pending_count() == 2

    @patch("builtins.print")
    def test_send_pending_notifications(
        self, mock_print, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test sending pending notifications."""
        # Add some notifications
        service_with_faculty.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. Test",
            week_offered=sample_week,
            swap_id=swap_id,
        )
        service_with_faculty.notify_swap_accepted(
            recipient_faculty_id=faculty_id,
            accepter_name="Dr. Test",
            week=sample_week,
            swap_id=swap_id,
        )

        assert service_with_faculty.get_pending_count() == 2

        # Send notifications
        count = service_with_faculty.send_pending_notifications()

        assert count == 2
        assert service_with_faculty.get_pending_count() == 0

        # Verify print was called (placeholder implementation)
        assert mock_print.call_count >= 2

    @patch("builtins.print")
    def test_send_pending_clears_queue(
        self, mock_print, service_with_faculty, faculty_id, swap_id, sample_week
    ):
        """Test that sending clears the queue."""
        service_with_faculty.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. Test",
            week_offered=sample_week,
            swap_id=swap_id,
        )

        assert service_with_faculty.get_pending_count() == 1
        service_with_faculty.send_pending_notifications()
        assert service_with_faculty.get_pending_count() == 0

        # Sending again should return 0
        count = service_with_faculty.send_pending_notifications()
        assert count == 0

    def test_send_empty_queue(self, mock_db):
        """Test sending with empty queue."""
        service = SwapNotificationService(db=mock_db)
        count = service.send_pending_notifications()
        assert count == 0


# ============================================================================
# Test Helper Methods
# ============================================================================


class TestHelperMethods:
    """Tests for internal helper methods."""

    def test_should_notify_with_preferences(self, mock_db, faculty_id):
        """Test _should_notify checks preferences correctly."""
        prefs = Mock(spec=FacultyPreference)
        prefs.notify_swap_requests = True
        prefs.notify_schedule_changes = False
        prefs.notify_conflict_alerts = True

        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = prefs

        mock_db.query = Mock(return_value=prefs_query)
        service = SwapNotificationService(db=mock_db)

        assert service._should_notify(faculty_id, "swap_requests") is True
        assert service._should_notify(faculty_id, "schedule_changes") is False
        assert service._should_notify(faculty_id, "conflict_alerts") is True

    def test_should_notify_defaults_true(self, mock_db, faculty_id):
        """Test _should_notify defaults to True when no preferences."""
        prefs_query = Mock()
        prefs_query.filter.return_value.first.return_value = None

        mock_db.query = Mock(return_value=prefs_query)
        service = SwapNotificationService(db=mock_db)

        assert service._should_notify(faculty_id, "swap_requests") is True
        assert service._should_notify(faculty_id, "unknown_key") is True

    def test_get_faculty_info_success(self, mock_db, faculty_id):
        """Test _get_faculty_info retrieves faculty data."""
        faculty = Mock(spec=Person)
        faculty.id = faculty_id
        faculty.name = "Dr. Test Person"
        faculty.email = "test.person@hospital.org"

        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = faculty

        mock_db.query = Mock(return_value=faculty_query)
        service = SwapNotificationService(db=mock_db)

        info = service._get_faculty_info(faculty_id)

        assert info is not None
        assert info["id"] == faculty_id
        assert info["name"] == "Dr. Test Person"
        assert info["email"] == "test.person@hospital.org"

    def test_get_faculty_info_not_found(self, mock_db):
        """Test _get_faculty_info returns None when faculty not found."""
        faculty_query = Mock()
        faculty_query.filter.return_value.first.return_value = None

        mock_db.query = Mock(return_value=faculty_query)
        service = SwapNotificationService(db=mock_db)

        info = service._get_faculty_info(uuid4())
        assert info is None

    def test_build_swap_request_body_with_reason(self, mock_db, sample_week):
        """Test _build_swap_request_body includes reason."""
        service = SwapNotificationService(db=mock_db)

        body = service._build_swap_request_body(
            requester_name="Dr. Requester",
            week=sample_week,
            reason="Conference attendance",
        )

        assert "Dr. Requester" in body
        assert sample_week.isoformat() in body
        assert "Conference attendance" in body
        assert "portal" in body.lower()

    def test_build_swap_request_body_without_reason(self, mock_db, sample_week):
        """Test _build_swap_request_body without reason."""
        service = SwapNotificationService(db=mock_db)

        body = service._build_swap_request_body(
            requester_name="Dr. Requester",
            week=sample_week,
            reason=None,
        )

        assert "Dr. Requester" in body
        assert sample_week.isoformat() in body
        assert "portal" in body.lower()
        # Should not have "Reason:" when no reason provided
        assert "Reason:" not in body or "Reason: None" not in body

    @patch("builtins.print")
    def test_send_notification_placeholder(self, mock_print, mock_db):
        """Test _send_notification placeholder implementation."""
        service = SwapNotificationService(db=mock_db)

        notification = SwapNotification(
            recipient_id=uuid4(),
            recipient_email="test@hospital.org",
            notification_type=SwapNotificationType.SWAP_EXECUTED,
            subject="Test Subject",
            body="Test Body",
        )

        result = service._send_notification(notification)

        assert result is True
        assert mock_print.called
        # Verify email and subject were printed
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("test@hospital.org" in str(call) for call in calls)
        assert any("Test Subject" in str(call) for call in calls)


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegrationScenarios:
    """Integration tests for common workflow scenarios."""

    def test_complete_swap_workflow(self, mock_db, sample_week, swap_id):
        """Test notifications for complete swap lifecycle."""
        requester_id = uuid4()
        target_id = uuid4()

        # Create faculty mocks
        requester = Mock(spec=Person)
        requester.id = requester_id
        requester.name = "Dr. Requester"
        requester.email = "requester@hospital.org"

        target = Mock(spec=Person)
        target.id = target_id
        target.name = "Dr. Target"
        target.email = "target@hospital.org"

        prefs = Mock(spec=FacultyPreference)
        prefs.notify_swap_requests = True
        prefs.notify_schedule_changes = True

        call_count = [0]

        def query_side_effect(model):
            if model == Person:
                query = Mock()

                def filter_func(*args, **kwargs):
                    result = Mock()
                    # Alternate between requester and target
                    result.first.return_value = (
                        target if call_count[0] % 2 == 0 else requester
                    )
                    call_count[0] += 1
                    return result

                query.filter = filter_func
                return query
            elif model == FacultyPreference:
                query = Mock()
                query.filter.return_value.first.return_value = prefs
                return query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        # Step 1: Swap requested
        notif1 = service.notify_swap_request_received(
            recipient_faculty_id=target_id,
            requester_name="Dr. Requester",
            week_offered=sample_week,
            swap_id=swap_id,
        )
        assert notif1 is not None
        assert service.get_pending_count() == 1

        # Step 2: Swap accepted
        notif2 = service.notify_swap_accepted(
            recipient_faculty_id=requester_id,
            accepter_name="Dr. Target",
            week=sample_week,
            swap_id=swap_id,
        )
        assert notif2 is not None
        assert service.get_pending_count() == 2

        # Step 3: Swap executed
        notif3 = service.notify_swap_executed(
            faculty_ids=[requester_id, target_id],
            week=sample_week,
            swap_id=swap_id,
            details="Swap completed successfully",
        )
        assert len(notif3) == 2
        assert service.get_pending_count() == 4

        # Send all notifications
        count = service.send_pending_notifications()
        assert count == 4
        assert service.get_pending_count() == 0

    def test_swap_rejection_workflow(self, mock_db, sample_week, swap_id):
        """Test notifications for rejected swap."""
        requester_id = uuid4()
        target_id = uuid4()

        requester = Mock(spec=Person)
        requester.id = requester_id
        requester.name = "Dr. Requester"
        requester.email = "requester@hospital.org"

        target = Mock(spec=Person)
        target.id = target_id
        target.name = "Dr. Target"
        target.email = "target@hospital.org"

        prefs = Mock(spec=FacultyPreference)
        prefs.notify_swap_requests = True

        call_count = [0]

        def query_side_effect(model):
            if model == Person:
                query = Mock()

                def filter_func(*args, **kwargs):
                    result = Mock()
                    result.first.return_value = (
                        target if call_count[0] == 0 else requester
                    )
                    call_count[0] += 1
                    return result

                query.filter = filter_func
                return query
            elif model == FacultyPreference:
                query = Mock()
                query.filter.return_value.first.return_value = prefs
                return query
            return Mock()

        mock_db.query = Mock(side_effect=query_side_effect)
        service = SwapNotificationService(db=mock_db)

        # Step 1: Request sent
        service.notify_swap_request_received(
            recipient_faculty_id=target_id,
            requester_name="Dr. Requester",
            week_offered=sample_week,
            swap_id=swap_id,
        )

        # Step 2: Request rejected
        service.notify_swap_rejected(
            recipient_faculty_id=requester_id,
            rejecter_name="Dr. Target",
            week=sample_week,
            swap_id=swap_id,
            reason="Already have plans that week",
        )

        assert service.get_pending_count() == 2

        count = service.send_pending_notifications()
        assert count == 2

    @patch("builtins.print")
    def test_multiple_notifications_same_recipient(
        self, mock_print, service_with_faculty, faculty_id, sample_week
    ):
        """Test multiple notifications to same recipient."""
        # Create multiple notifications for the same person
        service_with_faculty.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. Person A",
            week_offered=sample_week,
            swap_id=uuid4(),
        )

        service_with_faculty.notify_swap_request_received(
            recipient_faculty_id=faculty_id,
            requester_name="Dr. Person B",
            week_offered=sample_week + timedelta(days=7),
            swap_id=uuid4(),
        )

        service_with_faculty.notify_marketplace_match(
            recipient_faculty_id=faculty_id,
            poster_name="Dr. Person C",
            week_available=sample_week + timedelta(days=14),
            request_id=uuid4(),
        )

        assert service_with_faculty.get_pending_count() == 3

        count = service_with_faculty.send_pending_notifications()
        assert count == 3
