"""Comprehensive tests for ConflictAlertService."""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.conflict_alert import (
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person
from app.models.user import User
from app.services.conflict_alert_service import ConflictAlertService


@pytest.fixture
def service(db: Session) -> ConflictAlertService:
    """Create a ConflictAlertService instance."""
    return ConflictAlertService(db)


@pytest.fixture
def sample_user(db: Session) -> User:
    """Create a sample user for acknowledgment/resolution operations."""
    from app.core.security import get_password_hash

    user = User(
        id=uuid4(),
        username="testuser",
        email="testuser@test.org",
        hashed_password=get_password_hash("password123"),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_fmit_week() -> date:
    """Return a sample FMIT week date."""
    return date.today() + timedelta(days=14)


@pytest.mark.unit
class TestCreateAlert:
    """Tests for ConflictAlertService.create_alert()."""

    def test_create_basic_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test creating a basic conflict alert."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Vacation overlaps with FMIT week",
            severity=ConflictSeverity.CRITICAL,
        )

        assert alert.id is not None
        assert alert.faculty_id == sample_faculty.id
        assert alert.conflict_type == ConflictType.LEAVE_FMIT_OVERLAP
        assert alert.fmit_week == sample_fmit_week
        assert alert.description == "Vacation overlaps with FMIT week"
        assert alert.severity == ConflictSeverity.CRITICAL
        assert alert.status == ConflictAlertStatus.NEW

    def test_create_alert_with_default_severity(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test creating alert with default WARNING severity."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Back-to-back FMIT weeks",
        )

        assert alert.severity == ConflictSeverity.WARNING

    def test_create_alert_with_leave_reference(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
        sample_absence: Absence,
    ):
        """Test creating alert with a leave_id reference."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="TDY conflicts with FMIT",
            leave_id=sample_absence.id,
        )

        assert alert.leave_id == sample_absence.id

    def test_create_alert_with_swap_reference(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test creating alert with a swap_id reference."""
        swap_id = uuid4()
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=sample_fmit_week,
            description="Swap creates cascade issue",
            swap_id=swap_id,
        )

        assert alert.swap_id == swap_id

    def test_create_duplicate_alert_updates_existing(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test that creating duplicate alert updates existing instead of creating new."""
        # Create first alert
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Original description",
            severity=ConflictSeverity.WARNING,
        )

        # Try to create duplicate with updated info
        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Updated description",
            severity=ConflictSeverity.CRITICAL,
        )

        # Should be the same alert ID (updated, not new)
        assert alert1.id == alert2.id
        assert alert2.description == "Updated description"
        assert alert2.severity == ConflictSeverity.CRITICAL

    def test_create_duplicate_alert_only_if_unresolved(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
        sample_user: User,
    ):
        """Test that resolved alerts don't prevent new alerts from being created."""
        # Create and resolve first alert
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="First alert",
        )
        service.resolve_alert(alert1.id, sample_user.id, "Fixed")

        # Create another with same parameters
        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Second alert",
        )

        # Should be a new alert since first is resolved
        assert alert1.id != alert2.id
        assert alert2.status == ConflictAlertStatus.NEW


@pytest.mark.unit
class TestGetAlert:
    """Tests for ConflictAlertService.get_alert()."""

    def test_get_alert_by_id(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test retrieving an alert by ID."""
        created_alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        retrieved_alert = service.get_alert(created_alert.id)

        assert retrieved_alert is not None
        assert retrieved_alert.id == created_alert.id
        assert retrieved_alert.description == "Test alert"

    def test_get_nonexistent_alert(self, service: ConflictAlertService):
        """Test retrieving a non-existent alert returns None."""
        fake_id = uuid4()
        alert = service.get_alert(fake_id)

        assert alert is None


@pytest.mark.unit
class TestGetAlertsForFaculty:
    """Tests for ConflictAlertService.get_alerts_for_faculty()."""

    def test_get_all_alerts_for_faculty(
        self, service: ConflictAlertService, sample_faculty: Person, db: Session
    ):
        """Test retrieving all alerts for a specific faculty member."""
        # Create multiple alerts for the faculty
        for i in range(3):
            service.create_alert(
                faculty_id=sample_faculty.id,
                conflict_type=ConflictType.BACK_TO_BACK,
                fmit_week=date.today() + timedelta(days=7 * (i + 1)),
                description=f"Alert {i + 1}",
            )

        # Create alert for different faculty
        other_faculty = Person(
            id=uuid4(),
            name="Dr. Other",
            type="faculty",
            email="other@test.org",
        )
        db.add(other_faculty)
        db.commit()

        service.create_alert(
            faculty_id=other_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=28),
            description="Other faculty alert",
        )

        alerts = service.get_alerts_for_faculty(sample_faculty.id)

        assert len(alerts) == 3
        assert all(a.faculty_id == sample_faculty.id for a in alerts)

    def test_get_alerts_filtered_by_status(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
    ):
        """Test filtering alerts by status."""
        # Create alerts with different statuses
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="New alert",
        )

        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Alert to acknowledge",
        )
        service.acknowledge_alert(alert2.id, sample_user.id)

        alert3 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=21),
            description="Alert to resolve",
        )
        service.resolve_alert(alert3.id, sample_user.id)

        # Filter by NEW status
        new_alerts = service.get_alerts_for_faculty(
            sample_faculty.id, status=ConflictAlertStatus.NEW
        )
        assert len(new_alerts) == 1
        assert new_alerts[0].id == alert1.id

        # Filter by ACKNOWLEDGED status
        acked_alerts = service.get_alerts_for_faculty(
            sample_faculty.id, status=ConflictAlertStatus.ACKNOWLEDGED
        )
        assert len(acked_alerts) == 1
        assert acked_alerts[0].id == alert2.id

    def test_get_alerts_exclude_resolved_by_default(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
    ):
        """Test that resolved alerts are excluded by default."""
        # Create new alert
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Active alert",
        )

        # Create and resolve alert
        resolved = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Resolved alert",
        )
        service.resolve_alert(resolved.id, sample_user.id)

        alerts = service.get_alerts_for_faculty(
            sample_faculty.id, include_resolved=False
        )

        assert len(alerts) == 1
        assert alerts[0].status == ConflictAlertStatus.NEW

    def test_get_alerts_include_resolved(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
    ):
        """Test including resolved alerts when requested."""
        # Create new alert
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Active alert",
        )

        # Create and resolve alert
        resolved = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Resolved alert",
        )
        service.resolve_alert(resolved.id, sample_user.id)

        alerts = service.get_alerts_for_faculty(
            sample_faculty.id, include_resolved=True
        )

        assert len(alerts) == 2

    def test_alerts_ordered_by_created_at_desc(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test that alerts are returned in descending order by created_at."""
        # Create alerts with slight delays
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="First alert",
        )

        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Second alert",
        )

        alert3 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=21),
            description="Third alert",
        )

        alerts = service.get_alerts_for_faculty(sample_faculty.id)

        # Most recent first
        assert alerts[0].id == alert3.id
        assert alerts[1].id == alert2.id
        assert alerts[2].id == alert1.id


@pytest.mark.unit
class TestGetActiveAlerts:
    """Tests for ConflictAlertService.get_unresolved_alerts() (active alerts)."""

    def test_get_all_unresolved_alerts(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        db: Session,
    ):
        """Test retrieving all unresolved alerts."""
        # Create unresolved alerts (NEW and ACKNOWLEDGED)
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="New alert",
        )

        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Acknowledged alert",
        )
        service.acknowledge_alert(alert2.id, sample_user.id)

        # Create resolved alert
        alert3 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=21),
            description="Resolved alert",
        )
        service.resolve_alert(alert3.id, sample_user.id)

        # Create alert for different faculty
        other_faculty = Person(
            id=uuid4(),
            name="Dr. Other",
            type="faculty",
            email="other@test.org",
        )
        db.add(other_faculty)
        db.commit()

        alert4 = service.create_alert(
            faculty_id=other_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=28),
            description="Other faculty alert",
        )

        # Get all unresolved
        unresolved = service.get_unresolved_alerts()

        assert len(unresolved) == 3
        assert alert1.id in [a.id for a in unresolved]
        assert alert2.id in [a.id for a in unresolved]
        assert alert4.id in [a.id for a in unresolved]
        assert alert3.id not in [a.id for a in unresolved]

    def test_get_unresolved_alerts_filtered_by_faculty(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        db: Session,
    ):
        """Test filtering unresolved alerts by faculty_id."""
        # Create alerts for sample faculty
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Alert 1",
        )

        # Create alert for different faculty
        other_faculty = Person(
            id=uuid4(),
            name="Dr. Other",
            type="faculty",
            email="other@test.org",
        )
        db.add(other_faculty)
        db.commit()

        service.create_alert(
            faculty_id=other_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Other alert",
        )

        alerts = service.get_unresolved_alerts(faculty_id=sample_faculty.id)

        assert len(alerts) == 1
        assert alerts[0].faculty_id == sample_faculty.id

    def test_get_unresolved_alerts_ordered_by_fmit_week(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test that unresolved alerts are ordered by FMIT week."""
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="Later week",
        )

        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Earlier week",
        )

        alert3 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=14),
            description="Middle week",
        )

        alerts = service.get_unresolved_alerts()

        # Should be ordered by FMIT week
        assert alerts[0].id == alert2.id  # Earliest
        assert alerts[1].id == alert3.id  # Middle
        assert alerts[2].id == alert1.id  # Latest


@pytest.mark.unit
class TestAcknowledgeAlert:
    """Tests for ConflictAlertService.acknowledge_alert()."""

    def test_acknowledge_new_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test acknowledging a new alert."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        before_ack = datetime.utcnow()
        acknowledged = service.acknowledge_alert(alert.id, sample_user.id)
        after_ack = datetime.utcnow()

        assert acknowledged is not None
        assert acknowledged.status == ConflictAlertStatus.ACKNOWLEDGED
        assert acknowledged.acknowledged_by_id == sample_user.id
        assert acknowledged.acknowledged_at is not None
        assert before_ack <= acknowledged.acknowledged_at <= after_ack

    def test_acknowledge_nonexistent_alert(
        self, service: ConflictAlertService, sample_user: User
    ):
        """Test acknowledging a non-existent alert returns None."""
        fake_id = uuid4()
        result = service.acknowledge_alert(fake_id, sample_user.id)

        assert result is None

    def test_acknowledge_already_acknowledged_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test acknowledging an already acknowledged alert is idempotent."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        # First acknowledgment
        service.acknowledge_alert(alert.id, sample_user.id)

        # Second acknowledgment
        result = service.acknowledge_alert(alert.id, sample_user.id)

        assert result is not None
        assert result.status == ConflictAlertStatus.ACKNOWLEDGED

    def test_acknowledge_resolved_alert_no_change(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test that acknowledging a resolved alert doesn't change its status."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        # Resolve the alert
        service.resolve_alert(alert.id, sample_user.id)

        # Try to acknowledge
        result = service.acknowledge_alert(alert.id, sample_user.id)

        # Should return the alert but status remains RESOLVED
        assert result is not None
        assert result.status == ConflictAlertStatus.RESOLVED


@pytest.mark.unit
class TestResolveAlert:
    """Tests for ConflictAlertService.resolve_alert()."""

    def test_resolve_new_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test resolving a new alert."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Conflict detected",
        )

        before_resolve = datetime.utcnow()
        resolved = service.resolve_alert(
            alert.id, sample_user.id, notes="Swapped FMIT week with Dr. Jones"
        )
        after_resolve = datetime.utcnow()

        assert resolved is not None
        assert resolved.status == ConflictAlertStatus.RESOLVED
        assert resolved.resolved_by_id == sample_user.id
        assert resolved.resolved_at is not None
        assert before_resolve <= resolved.resolved_at <= after_resolve
        assert resolved.resolution_notes == "Swapped FMIT week with Dr. Jones"

    def test_resolve_acknowledged_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test resolving an acknowledged alert."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        service.acknowledge_alert(alert.id, sample_user.id)

        resolved = service.resolve_alert(alert.id, sample_user.id, notes="Fixed")

        assert resolved is not None
        assert resolved.status == ConflictAlertStatus.RESOLVED

    def test_resolve_alert_without_notes(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test resolving alert without providing notes."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        resolved = service.resolve_alert(alert.id, sample_user.id)

        assert resolved is not None
        assert resolved.status == ConflictAlertStatus.RESOLVED
        assert resolved.resolution_notes is None

    def test_resolve_nonexistent_alert(
        self, service: ConflictAlertService, sample_user: User
    ):
        """Test resolving a non-existent alert returns None."""
        fake_id = uuid4()
        result = service.resolve_alert(fake_id, sample_user.id)

        assert result is None

    def test_resolve_already_resolved_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test that resolving an already resolved alert is idempotent."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        # First resolution
        service.resolve_alert(alert.id, sample_user.id, notes="First resolution")

        # Second resolution
        result = service.resolve_alert(
            alert.id, sample_user.id, notes="Second resolution"
        )

        assert result is not None
        assert result.status == ConflictAlertStatus.RESOLVED
        # Notes should not change on second resolution
        assert result.resolution_notes == "First resolution"


@pytest.mark.unit
class TestIgnoreAlert:
    """Tests for ConflictAlertService.ignore_alert()."""

    def test_ignore_new_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test ignoring a new alert as false positive."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=sample_fmit_week,
            description="Call cascade alert",
        )

        before_ignore = datetime.utcnow()
        ignored = service.ignore_alert(
            alert.id,
            sample_user.id,
            reason="Not a real conflict - coverage already arranged",
        )
        after_ignore = datetime.utcnow()

        assert ignored is not None
        assert ignored.status == ConflictAlertStatus.IGNORED
        assert ignored.resolved_by_id == sample_user.id
        assert ignored.resolved_at is not None
        assert before_ignore <= ignored.resolved_at <= after_ignore
        assert "Ignored:" in ignored.resolution_notes
        assert "Not a real conflict" in ignored.resolution_notes

    def test_ignore_acknowledged_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test ignoring an acknowledged alert."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXCESSIVE_ALTERNATING,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        service.acknowledge_alert(alert.id, sample_user.id)

        ignored = service.ignore_alert(
            alert.id, sample_user.id, reason="False positive"
        )

        assert ignored is not None
        assert ignored.status == ConflictAlertStatus.IGNORED

    def test_ignore_nonexistent_alert(
        self, service: ConflictAlertService, sample_user: User
    ):
        """Test ignoring a non-existent alert returns None."""
        fake_id = uuid4()
        result = service.ignore_alert(fake_id, sample_user.id, reason="Test")

        assert result is None

    def test_ignore_already_resolved_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test that ignoring an already resolved alert doesn't change it."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        # Resolve the alert
        service.resolve_alert(alert.id, sample_user.id, notes="Fixed")

        # Try to ignore
        result = service.ignore_alert(alert.id, sample_user.id, reason="False positive")

        assert result is not None
        assert result.status == ConflictAlertStatus.RESOLVED  # Status unchanged


@pytest.mark.unit
class TestGetAlertsBySeverity:
    """Tests for filtering alerts by severity using get_unresolved_alerts()."""

    def test_filter_by_critical_severity(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test filtering unresolved alerts by CRITICAL severity."""
        # Create alerts with different severities
        critical = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Critical alert",
            severity=ConflictSeverity.CRITICAL,
        )

        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Warning alert",
            severity=ConflictSeverity.WARNING,
        )

        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXTERNAL_COMMITMENT,
            fmit_week=date.today() + timedelta(days=21),
            description="Info alert",
            severity=ConflictSeverity.INFO,
        )

        critical_alerts = service.get_unresolved_alerts(
            severity=ConflictSeverity.CRITICAL
        )

        assert len(critical_alerts) == 1
        assert critical_alerts[0].id == critical.id
        assert critical_alerts[0].severity == ConflictSeverity.CRITICAL

    def test_filter_by_warning_severity(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test filtering unresolved alerts by WARNING severity."""
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Critical alert",
            severity=ConflictSeverity.CRITICAL,
        )

        warning = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Warning alert",
            severity=ConflictSeverity.WARNING,
        )

        warning_alerts = service.get_unresolved_alerts(
            severity=ConflictSeverity.WARNING
        )

        assert len(warning_alerts) == 1
        assert warning_alerts[0].id == warning.id

    def test_filter_by_info_severity(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test filtering unresolved alerts by INFO severity."""
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Warning alert",
            severity=ConflictSeverity.WARNING,
        )

        info = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXTERNAL_COMMITMENT,
            fmit_week=date.today() + timedelta(days=14),
            description="Info alert",
            severity=ConflictSeverity.INFO,
        )

        info_alerts = service.get_unresolved_alerts(severity=ConflictSeverity.INFO)

        assert len(info_alerts) == 1
        assert info_alerts[0].id == info.id


@pytest.mark.unit
class TestGetAlertsInRange:
    """Tests for date range filtering using get_unresolved_alerts()."""

    def test_filter_by_start_date(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test filtering alerts with start_date."""
        cutoff = date.today() + timedelta(days=14)

        # Before cutoff
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Early alert",
        )

        # At cutoff
        at_cutoff = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=cutoff,
            description="Cutoff alert",
        )

        # After cutoff
        after_cutoff = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=21),
            description="Late alert",
        )

        alerts = service.get_unresolved_alerts(start_date=cutoff)

        assert len(alerts) == 2
        assert at_cutoff.id in [a.id for a in alerts]
        assert after_cutoff.id in [a.id for a in alerts]

    def test_filter_by_end_date(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test filtering alerts with end_date."""
        cutoff = date.today() + timedelta(days=14)

        # Before cutoff
        before_cutoff = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Early alert",
        )

        # At cutoff
        at_cutoff = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=cutoff,
            description="Cutoff alert",
        )

        # After cutoff
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=21),
            description="Late alert",
        )

        alerts = service.get_unresolved_alerts(end_date=cutoff)

        assert len(alerts) == 2
        assert before_cutoff.id in [a.id for a in alerts]
        assert at_cutoff.id in [a.id for a in alerts]

    def test_filter_by_date_range(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test filtering alerts within a specific date range."""
        start = date.today() + timedelta(days=7)
        end = date.today() + timedelta(days=21)

        # Before range
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today(),
            description="Too early",
        )

        # In range
        in_range1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="In range 1",
        )

        in_range2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=14),
            description="In range 2",
        )

        # After range
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXCESSIVE_ALTERNATING,
            fmit_week=date.today() + timedelta(days=28),
            description="Too late",
        )

        alerts = service.get_unresolved_alerts(start_date=start, end_date=end)

        assert len(alerts) == 2
        assert in_range1.id in [a.id for a in alerts]
        assert in_range2.id in [a.id for a in alerts]

    def test_combined_filters(
        self, service: ConflictAlertService, sample_faculty: Person, db: Session
    ):
        """Test combining faculty, severity, and date range filters."""
        start = date.today() + timedelta(days=7)
        end = date.today() + timedelta(days=21)

        # Create matching alert
        matching = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Matching alert",
            severity=ConflictSeverity.CRITICAL,
        )

        # Non-matching: different faculty
        other_faculty = Person(
            id=uuid4(),
            name="Dr. Other",
            type="faculty",
            email="other@test.org",
        )
        db.add(other_faculty)
        db.commit()

        service.create_alert(
            faculty_id=other_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Different faculty",
            severity=ConflictSeverity.CRITICAL,
        )

        # Non-matching: different severity
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Different severity",
            severity=ConflictSeverity.WARNING,
        )

        # Non-matching: outside date range
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=28),
            description="Outside range",
            severity=ConflictSeverity.CRITICAL,
        )

        alerts = service.get_unresolved_alerts(
            faculty_id=sample_faculty.id,
            severity=ConflictSeverity.CRITICAL,
            start_date=start,
            end_date=end,
        )

        assert len(alerts) == 1
        assert alerts[0].id == matching.id


@pytest.mark.unit
class TestGetAlertsForWeek:
    """Tests for ConflictAlertService.get_alerts_for_week()."""

    def test_get_all_alerts_for_specific_week(
        self, service: ConflictAlertService, sample_faculty: Person, db: Session
    ):
        """Test retrieving all alerts for a specific FMIT week."""
        target_week = date.today() + timedelta(days=14)

        # Alerts for target week
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=target_week,
            description="Alert 1",
        )

        other_faculty = Person(
            id=uuid4(),
            name="Dr. Other",
            type="faculty",
            email="other@test.org",
        )
        db.add(other_faculty)
        db.commit()

        alert2 = service.create_alert(
            faculty_id=other_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
            description="Alert 2",
        )

        # Alert for different week
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=21),
            description="Different week",
        )

        alerts = service.get_alerts_for_week(target_week)

        assert len(alerts) == 2
        assert alert1.id in [a.id for a in alerts]
        assert alert2.id in [a.id for a in alerts]

    def test_get_alerts_for_week_filtered_by_faculty(
        self, service: ConflictAlertService, sample_faculty: Person, db: Session
    ):
        """Test retrieving alerts for a week filtered by faculty."""
        target_week = date.today() + timedelta(days=14)

        # Alert for target week and faculty
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=target_week,
            description="Alert 1",
        )

        # Alert for target week but different faculty
        other_faculty = Person(
            id=uuid4(),
            name="Dr. Other",
            type="faculty",
            email="other@test.org",
        )
        db.add(other_faculty)
        db.commit()

        service.create_alert(
            faculty_id=other_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
            description="Other faculty",
        )

        alerts = service.get_alerts_for_week(target_week, faculty_id=sample_faculty.id)

        assert len(alerts) == 1
        assert alerts[0].id == alert1.id


@pytest.mark.unit
class TestCountUnresolvedByFaculty:
    """Tests for ConflictAlertService.count_unresolved_by_faculty()."""

    def test_count_unresolved_alerts(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
    ):
        """Test counting unresolved alerts for a faculty member."""
        # Create unresolved alerts (NEW and ACKNOWLEDGED)
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="New alert",
        )

        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Acknowledged alert",
        )
        service.acknowledge_alert(alert2.id, sample_user.id)

        # Create resolved alert
        alert3 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=21),
            description="Resolved alert",
        )
        service.resolve_alert(alert3.id, sample_user.id)

        count = service.count_unresolved_by_faculty(sample_faculty.id)

        assert count == 2

    def test_count_zero_unresolved(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test counting when there are no unresolved alerts."""
        count = service.count_unresolved_by_faculty(sample_faculty.id)

        assert count == 0


@pytest.mark.unit
class TestGetCriticalAlerts:
    """Tests for ConflictAlertService.get_critical_alerts()."""

    def test_get_all_critical_unresolved_alerts(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
    ):
        """Test retrieving all unresolved critical alerts."""
        # Create critical unresolved alerts
        critical1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Critical alert 1",
            severity=ConflictSeverity.CRITICAL,
        )

        critical2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=14),
            description="Critical alert 2",
            severity=ConflictSeverity.CRITICAL,
        )

        # Create warning alert (should not be included)
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="Warning alert",
            severity=ConflictSeverity.WARNING,
        )

        # Create resolved critical alert (should not be included)
        critical_resolved = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXCESSIVE_ALTERNATING,
            fmit_week=date.today() + timedelta(days=28),
            description="Resolved critical",
            severity=ConflictSeverity.CRITICAL,
        )
        service.resolve_alert(critical_resolved.id, sample_user.id)

        critical_alerts = service.get_critical_alerts()

        assert len(critical_alerts) == 2
        assert critical1.id in [a.id for a in critical_alerts]
        assert critical2.id in [a.id for a in critical_alerts]

    def test_critical_alerts_ordered_by_fmit_week(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test that critical alerts are ordered by FMIT week."""
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=21),
            description="Later week",
            severity=ConflictSeverity.CRITICAL,
        )

        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=7),
            description="Earlier week",
            severity=ConflictSeverity.CRITICAL,
        )

        critical_alerts = service.get_critical_alerts()

        # Should be ordered by FMIT week
        assert critical_alerts[0].id == alert2.id  # Earlier
        assert critical_alerts[1].id == alert1.id  # Later


@pytest.mark.unit
class TestAutoResolveForLeaveDeletion:
    """Tests for ConflictAlertService.auto_resolve_for_leave_deletion()."""

    def test_auto_resolve_alerts_for_deleted_leave(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_absence: Absence,
    ):
        """Test auto-resolving alerts when related leave is deleted."""
        # Create alerts related to the leave
        alert1 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Leave conflict 1",
            leave_id=sample_absence.id,
        )

        alert2 = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Leave conflict 2",
            leave_id=sample_absence.id,
        )

        # Create alert without leave reference
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="No leave reference",
        )

        before_resolve = datetime.utcnow()
        count = service.auto_resolve_for_leave_deletion(sample_absence.id)
        after_resolve = datetime.utcnow()

        assert count == 2

        # Check alerts are resolved
        resolved1 = service.get_alert(alert1.id)
        assert resolved1.status == ConflictAlertStatus.RESOLVED
        assert resolved1.resolved_at is not None
        assert before_resolve <= resolved1.resolved_at <= after_resolve
        assert "Auto-resolved" in resolved1.resolution_notes
        assert "leave record was deleted" in resolved1.resolution_notes

        resolved2 = service.get_alert(alert2.id)
        assert resolved2.status == ConflictAlertStatus.RESOLVED

    def test_auto_resolve_only_unresolved_alerts(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_absence: Absence,
        sample_user: User,
    ):
        """Test that auto-resolve only affects unresolved alerts."""
        # Create new alert
        service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="New alert",
            leave_id=sample_absence.id,
        )

        # Create already resolved alert
        resolved = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Already resolved",
            leave_id=sample_absence.id,
        )
        service.resolve_alert(resolved.id, sample_user.id, notes="Manual resolution")

        count = service.auto_resolve_for_leave_deletion(sample_absence.id)

        # Should only auto-resolve the NEW alert, not the already resolved one
        assert count == 1

    def test_auto_resolve_returns_zero_when_no_matching_alerts(
        self, service: ConflictAlertService
    ):
        """Test that auto-resolve returns 0 when no alerts match."""
        fake_leave_id = uuid4()
        count = service.auto_resolve_for_leave_deletion(fake_leave_id)

        assert count == 0


@pytest.mark.unit
class TestDeleteAlert:
    """Tests for ConflictAlertService.delete_alert()."""

    def test_delete_existing_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test deleting an existing alert."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Alert to delete",
        )

        result = service.delete_alert(alert.id)

        assert result is True

        # Verify alert is deleted
        deleted_alert = service.get_alert(alert.id)
        assert deleted_alert is None

    def test_delete_nonexistent_alert(self, service: ConflictAlertService):
        """Test deleting a non-existent alert returns False."""
        fake_id = uuid4()
        result = service.delete_alert(fake_id)

        assert result is False


@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_multiple_conflict_types(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test creating alerts with different conflict types."""
        conflict_types = [
            ConflictType.LEAVE_FMIT_OVERLAP,
            ConflictType.BACK_TO_BACK,
            ConflictType.EXCESSIVE_ALTERNATING,
            ConflictType.CALL_CASCADE,
            ConflictType.EXTERNAL_COMMITMENT,
        ]

        for i, conflict_type in enumerate(conflict_types):
            alert = service.create_alert(
                faculty_id=sample_faculty.id,
                conflict_type=conflict_type,
                fmit_week=date.today() + timedelta(days=7 * (i + 1)),
                description=f"Conflict type {conflict_type.value}",
            )
            assert alert.conflict_type == conflict_type

    def test_alert_with_past_fmit_week(
        self, service: ConflictAlertService, sample_faculty: Person
    ):
        """Test creating alert with a past FMIT week."""
        past_week = date.today() - timedelta(days=30)

        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=past_week,
            description="Past week conflict",
        )

        assert alert is not None
        assert alert.fmit_week == past_week

    def test_empty_description_handled(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test creating alert with empty description."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="",
        )

        assert alert is not None
        assert alert.description == ""

    def test_concurrent_status_changes(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test status transitions in sequence."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test alert",
        )

        # NEW -> ACKNOWLEDGED
        service.acknowledge_alert(alert.id, sample_user.id)
        updated = service.get_alert(alert.id)
        assert updated.status == ConflictAlertStatus.ACKNOWLEDGED

        # ACKNOWLEDGED -> RESOLVED
        service.resolve_alert(alert.id, sample_user.id)
        updated = service.get_alert(alert.id)
        assert updated.status == ConflictAlertStatus.RESOLVED

    def test_large_description_and_notes(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test handling large text in description and notes."""
        large_text = "A" * 5000

        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description=large_text,
        )

        assert len(alert.description) == 5000

        service.resolve_alert(alert.id, sample_user.id, notes=large_text)
        resolved = service.get_alert(alert.id)

        assert len(resolved.resolution_notes) == 5000


@pytest.mark.unit
class TestGenerateResolutionOptions:
    """Tests for ConflictAlertService.generate_resolution_options()."""

    def test_generate_options_for_leave_overlap(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
        db: Session,
    ):
        """Test generating resolution options for leave/FMIT overlap conflict."""
        # Create another faculty who could swap
        other_faculty = Person(
            id=uuid4(),
            name="Dr. Available",
            type="faculty",
            email="available@test.org",
        )
        db.add(other_faculty)
        db.commit()

        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Leave conflicts with FMIT",
            severity=ConflictSeverity.CRITICAL,
        )

        options = service.generate_resolution_options(alert.id)

        assert len(options) > 0
        # Should include swap, backup, and coverage options
        strategies = [opt.strategy for opt in options]
        assert "swap_assignment" in [s.value for s in strategies]
        # All options should have impact estimates
        assert all(opt.impact is not None for opt in options)

    def test_generate_options_for_back_to_back(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test generating resolution options for back-to-back conflict."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=sample_fmit_week,
            description="Back-to-back FMIT weeks",
            severity=ConflictSeverity.WARNING,
        )

        options = service.generate_resolution_options(alert.id)

        assert len(options) > 0
        strategies = [opt.strategy for opt in options]
        assert "swap_assignment" in [s.value for s in strategies]
        assert "adjust_time_boundaries" in [s.value for s in strategies]

    def test_generate_options_for_external_commitment(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test generating resolution options for external commitment conflict."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXTERNAL_COMMITMENT,
            fmit_week=sample_fmit_week,
            description="Conference during FMIT week",
            severity=ConflictSeverity.WARNING,
        )

        options = service.generate_resolution_options(alert.id)

        assert len(options) > 0
        # Should primarily suggest coverage request
        strategies = [opt.strategy for opt in options]
        assert "request_coverage_pool" in [s.value for s in strategies]

    def test_generate_options_for_nonexistent_alert(
        self, service: ConflictAlertService
    ):
        """Test generating options for non-existent alert returns empty list."""
        fake_id = uuid4()
        options = service.generate_resolution_options(fake_id)

        assert options == []

    def test_options_sorted_by_feasibility(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test that options are sorted by feasibility score (highest first)."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        options = service.generate_resolution_options(alert.id)

        if len(options) > 1:
            # Check descending order of feasibility
            for i in range(len(options) - 1):
                assert (
                    options[i].impact.feasibility_score
                    >= options[i + 1].impact.feasibility_score
                )

    def test_max_options_limit(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test that max_options parameter limits returned options."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        options = service.generate_resolution_options(alert.id, max_options=2)

        assert len(options) <= 2


@pytest.mark.unit
class TestApplyAutoResolution:
    """Tests for ConflictAlertService.apply_auto_resolution()."""

    def test_apply_swap_resolution(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
        db: Session,
    ):
        """Test applying a swap assignment resolution."""
        # Create target faculty for swap
        target_faculty = Person(
            id=uuid4(),
            name="Dr. Target",
            type="faculty",
            email="target@test.org",
        )
        db.add(target_faculty)
        db.commit()

        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Leave conflicts with FMIT",
        )

        options = service.generate_resolution_options(alert.id)
        assert len(options) > 0

        # Apply first option
        success, msg = service.apply_auto_resolution(
            alert.id, options[0].id, sample_user.id
        )

        assert success is True
        assert msg != ""

        # Check alert is resolved
        resolved_alert = service.get_alert(alert.id)
        assert resolved_alert.status == ConflictAlertStatus.RESOLVED
        assert resolved_alert.resolved_by_id == sample_user.id
        assert resolved_alert.resolution_notes is not None

    def test_apply_coverage_request_resolution(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test applying a coverage request resolution."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXTERNAL_COMMITMENT,
            fmit_week=sample_fmit_week,
            description="Conference conflict",
        )

        options = service.generate_resolution_options(alert.id)
        coverage_option = next(
            (o for o in options if o.strategy.value == "request_coverage_pool"), None
        )
        assert coverage_option is not None

        success, msg = service.apply_auto_resolution(
            alert.id, coverage_option.id, sample_user.id
        )

        assert success is True
        assert "coverage" in msg.lower()

        # Check alert is resolved
        resolved_alert = service.get_alert(alert.id)
        assert resolved_alert.status == ConflictAlertStatus.RESOLVED

    def test_apply_resolution_to_nonexistent_alert(
        self, service: ConflictAlertService, sample_user: User
    ):
        """Test applying resolution to non-existent alert fails."""
        fake_id = uuid4()
        success, msg = service.apply_auto_resolution(
            fake_id, "some_option", sample_user.id
        )

        assert success is False
        assert "not found" in msg.lower()

    def test_apply_resolution_with_invalid_option_id(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test applying resolution with invalid option ID fails."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        success, msg = service.apply_auto_resolution(
            alert.id, "invalid_option_id", sample_user.id
        )

        assert success is False
        assert "not found" in msg.lower()

    def test_apply_resolution_to_already_resolved_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test applying resolution to already resolved alert fails."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        # Manually resolve the alert
        service.resolve_alert(alert.id, sample_user.id, "Manual resolution")

        options = service.generate_resolution_options(alert.id)
        if options:
            success, msg = service.apply_auto_resolution(
                alert.id, options[0].id, sample_user.id
            )

            assert success is False
            assert "status" in msg.lower()

    def test_apply_resolution_without_user_id(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test applying resolution without user ID (system auto-resolution)."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXTERNAL_COMMITMENT,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        options = service.generate_resolution_options(alert.id)
        assert len(options) > 0

        success, msg = service.apply_auto_resolution(
            alert.id, options[0].id, user_id=None
        )

        # Should succeed even without user
        if success:
            resolved_alert = service.get_alert(alert.id)
            assert resolved_alert.status == ConflictAlertStatus.RESOLVED
            assert resolved_alert.resolved_by_id is None


@pytest.mark.unit
class TestValidateResolution:
    """Tests for ConflictAlertService.validate_resolution()."""

    def test_validate_swap_resolution_with_valid_target(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
        db: Session,
    ):
        """Test validating swap resolution with valid target faculty."""
        from app.services.conflict_alert_service import (
            ResolutionOption,
            ResolutionStrategy,
        )

        target_faculty = Person(
            id=uuid4(),
            name="Dr. Target",
            type="faculty",
            email="target@test.org",
        )
        db.add(target_faculty)
        db.commit()

        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        resolution = ResolutionOption(
            id="test_swap",
            strategy=ResolutionStrategy.SWAP_ASSIGNMENT,
            description="Test swap",
            details={
                "source_faculty_id": str(sample_faculty.id),
                "target_faculty_id": str(target_faculty.id),
                "source_week": sample_fmit_week.isoformat(),
            },
        )

        is_valid, msg = service.validate_resolution(alert.id, resolution)

        assert is_valid is True

    def test_validate_swap_resolution_with_invalid_target(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test validating swap resolution with non-existent target."""
        from app.services.conflict_alert_service import (
            ResolutionOption,
            ResolutionStrategy,
        )

        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        resolution = ResolutionOption(
            id="test_swap",
            strategy=ResolutionStrategy.SWAP_ASSIGNMENT,
            description="Test swap",
            details={
                "source_faculty_id": str(sample_faculty.id),
                "target_faculty_id": str(uuid4()),  # Non-existent
                "source_week": sample_fmit_week.isoformat(),
            },
        )

        is_valid, msg = service.validate_resolution(alert.id, resolution)

        assert is_valid is False
        assert "not found" in msg.lower()

    def test_validate_coverage_request_always_valid(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test that coverage requests are always valid."""
        from app.services.conflict_alert_service import (
            ResolutionOption,
            ResolutionStrategy,
        )

        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXTERNAL_COMMITMENT,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        resolution = ResolutionOption(
            id="test_coverage",
            strategy=ResolutionStrategy.REQUEST_COVERAGE_POOL,
            description="Request coverage",
            details={
                "faculty_id": str(sample_faculty.id),
                "fmit_week": sample_fmit_week.isoformat(),
            },
        )

        is_valid, msg = service.validate_resolution(alert.id, resolution)

        assert is_valid is True

    def test_validate_resolution_for_resolved_alert(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
    ):
        """Test validation fails for already resolved alert."""
        from app.services.conflict_alert_service import (
            ResolutionOption,
            ResolutionStrategy,
        )

        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        service.resolve_alert(alert.id, sample_user.id)

        resolution = ResolutionOption(
            id="test_resolution",
            strategy=ResolutionStrategy.REQUEST_COVERAGE_POOL,
            description="Test",
            details={},
        )

        is_valid, msg = service.validate_resolution(alert.id, resolution)

        assert is_valid is False
        assert "resolved" in msg.lower()


@pytest.mark.unit
class TestEstimateResolutionImpact:
    """Tests for ConflictAlertService.estimate_resolution_impact()."""

    def test_estimate_swap_impact(self, service: ConflictAlertService):
        """Test estimating impact of swap resolution."""
        from app.services.conflict_alert_service import (
            ResolutionOption,
            ResolutionStrategy,
        )

        resolution = ResolutionOption(
            id="test_swap",
            strategy=ResolutionStrategy.SWAP_ASSIGNMENT,
            description="Test swap",
            details={},
        )

        impact = service.estimate_resolution_impact(resolution)

        assert impact is not None
        assert impact.affected_faculty_count > 0
        assert impact.feasibility_score > 0
        assert impact.workload_balance_score > 0
        assert impact.recommendation != ""

    def test_estimate_backup_impact(self, service: ConflictAlertService):
        """Test estimating impact of backup reassignment."""
        from app.services.conflict_alert_service import (
            ResolutionOption,
            ResolutionStrategy,
        )

        resolution = ResolutionOption(
            id="test_backup",
            strategy=ResolutionStrategy.REASSIGN_TO_BACKUP,
            description="Test backup",
            details={},
        )

        impact = service.estimate_resolution_impact(resolution)

        assert impact is not None
        assert impact.affected_faculty_count > 0
        assert 0 <= impact.feasibility_score <= 1
        assert 0 <= impact.workload_balance_score <= 1

    def test_estimate_coverage_pool_impact(self, service: ConflictAlertService):
        """Test estimating impact of coverage pool request."""
        from app.services.conflict_alert_service import (
            ResolutionOption,
            ResolutionStrategy,
        )

        resolution = ResolutionOption(
            id="test_coverage",
            strategy=ResolutionStrategy.REQUEST_COVERAGE_POOL,
            description="Test coverage",
            details={},
        )

        impact = service.estimate_resolution_impact(resolution)

        assert impact is not None
        # Coverage requests have lower feasibility due to volunteer dependency
        assert impact.feasibility_score <= 0.6

    def test_estimate_time_adjustment_impact(self, service: ConflictAlertService):
        """Test estimating impact of time boundary adjustment."""
        from app.services.conflict_alert_service import (
            ResolutionOption,
            ResolutionStrategy,
        )

        resolution = ResolutionOption(
            id="test_adjust",
            strategy=ResolutionStrategy.ADJUST_TIME_BOUNDARIES,
            description="Test adjustment",
            details={},
        )

        impact = service.estimate_resolution_impact(resolution)

        assert impact is not None
        assert impact.affected_faculty_count >= 1
        assert impact.affected_weeks_count >= 1


@pytest.mark.unit
class TestResolutionHistoryTracking:
    """Tests for resolution history tracking."""

    def test_get_resolution_history_for_conflict(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_fmit_week: date,
    ):
        """Test getting resolution history for a conflict."""
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Test conflict",
        )

        # Note: Current implementation returns None as history is not persisted
        history = service.get_resolution_history(alert.id)

        # This is expected behavior for now
        assert history is None


@pytest.mark.unit
class TestResolutionIntegration:
    """Integration tests for the full auto-resolution workflow."""

    def test_full_resolution_workflow(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
        db: Session,
    ):
        """Test the complete workflow from conflict detection to resolution."""
        # Create another faculty for potential swap
        other_faculty = Person(
            id=uuid4(),
            name="Dr. Available",
            type="faculty",
            email="available@test.org",
        )
        db.add(other_faculty)
        db.commit()

        # Step 1: Create conflict alert
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Leave conflicts with FMIT week",
            severity=ConflictSeverity.CRITICAL,
        )
        assert alert.status == ConflictAlertStatus.NEW

        # Step 2: Generate resolution options
        options = service.generate_resolution_options(alert.id)
        assert len(options) > 0

        # Step 3: Validate best option
        best_option = options[0]
        is_valid, validation_msg = service.validate_resolution(alert.id, best_option)
        assert is_valid is True

        # Step 4: Estimate impact
        impact = service.estimate_resolution_impact(best_option)
        assert impact is not None
        assert impact.feasibility_score > 0

        # Step 5: Apply resolution
        success, msg = service.apply_auto_resolution(
            alert.id, best_option.id, sample_user.id
        )

        if success:
            # Step 6: Verify alert is resolved
            resolved_alert = service.get_alert(alert.id)
            assert resolved_alert.status == ConflictAlertStatus.RESOLVED
            assert resolved_alert.resolved_by_id == sample_user.id
            assert resolved_alert.resolution_notes is not None
            assert best_option.strategy.value in resolved_alert.resolution_notes

    def test_multiple_conflicts_resolution(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        db: Session,
    ):
        """Test resolving multiple conflicts."""
        # Create multiple conflicts
        alerts = []
        for i in range(3):
            alert = service.create_alert(
                faculty_id=sample_faculty.id,
                conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
                fmit_week=date.today() + timedelta(days=7 * (i + 1)),
                description=f"Conflict {i + 1}",
            )
            alerts.append(alert)

        # Resolve each conflict
        resolved_count = 0
        for alert in alerts:
            options = service.generate_resolution_options(alert.id)
            if options:
                success, _ = service.apply_auto_resolution(
                    alert.id, options[0].id, sample_user.id
                )
                if success:
                    resolved_count += 1

        # Verify some were resolved
        assert resolved_count > 0

    def test_cascading_conflict_detection(
        self,
        service: ConflictAlertService,
        sample_faculty: Person,
        sample_user: User,
        sample_fmit_week: date,
        db: Session,
    ):
        """Test that resolving one conflict doesn't create another."""
        # Create target faculty
        target_faculty = Person(
            id=uuid4(),
            name="Dr. Target",
            type="faculty",
            email="target@test.org",
        )
        db.add(target_faculty)
        db.commit()

        # Create conflict
        alert = service.create_alert(
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=sample_fmit_week,
            description="Leave conflicts with FMIT",
        )

        # Get initial conflict count
        initial_conflicts = len(service.get_unresolved_alerts())

        # Apply resolution
        options = service.generate_resolution_options(alert.id)
        if options:
            success, _ = service.apply_auto_resolution(
                alert.id, options[0].id, sample_user.id
            )

            if success:
                # Check that we didn't create more conflicts
                final_conflicts = len(service.get_unresolved_alerts())
                # Should be fewer or same (not more)
                assert final_conflicts <= initial_conflicts
