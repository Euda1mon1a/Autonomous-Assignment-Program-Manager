"""Comprehensive tests for ConflictRepository."""
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

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
from app.repositories.conflict_repository import ConflictRepository

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def conflict_repo(db: Session) -> ConflictRepository:
    """Create a ConflictRepository instance."""
    return ConflictRepository(db)


@pytest.fixture
def sample_faculty_for_conflicts(db: Session) -> Person:
    """Create a sample faculty member for conflict tests."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Alice Johnson",
        type="faculty",
        email="alice.johnson@hospital.org",
        performs_procedures=True,
        specialties=["Sports Medicine"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def sample_faculty2(db: Session) -> Person:
    """Create a second sample faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Bob Smith",
        type="faculty",
        email="bob.smith@hospital.org",
        performs_procedures=True,
        specialties=["Primary Care"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def sample_leave(db: Session, sample_faculty_for_conflicts: Person) -> Absence:
    """Create a sample leave/absence record."""
    leave = Absence(
        id=uuid4(),
        person_id=sample_faculty_for_conflicts.id,
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=37),
        absence_type="vacation",
        notes="Annual leave",
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


# ============================================================================
# Tests for CRUD Operations
# ============================================================================


class TestConflictRepositoryCreate:
    """Tests for creating conflict alerts."""

    def test_create_basic_alert(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test creating a basic conflict alert."""
        fmit_week = date.today() + timedelta(days=14)

        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=fmit_week,
            description="Vacation overlaps with FMIT week",
            severity=ConflictSeverity.CRITICAL,
        )

        assert alert.id is not None
        assert isinstance(alert.id, UUID)
        assert alert.faculty_id == sample_faculty_for_conflicts.id
        assert alert.conflict_type == ConflictType.LEAVE_FMIT_OVERLAP
        assert alert.severity == ConflictSeverity.CRITICAL
        assert alert.fmit_week == fmit_week
        assert alert.description == "Vacation overlaps with FMIT week"
        assert alert.status == ConflictAlertStatus.NEW
        assert alert.created_at is not None

    def test_create_with_default_severity(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test creating alert with default WARNING severity."""
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Back-to-back FMIT weeks",
        )

        assert alert.severity == ConflictSeverity.WARNING

    def test_create_with_leave_reference(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_leave: Absence,
    ):
        """Test creating alert with leave reference."""
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=30),
            description="Leave conflicts with FMIT",
            severity=ConflictSeverity.CRITICAL,
            leave_id=sample_leave.id,
        )

        assert alert.leave_id == sample_leave.id

    def test_create_with_swap_reference(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test creating alert with swap reference."""
        swap_id = uuid4()

        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=21),
            description="Swap creates call cascade",
            severity=ConflictSeverity.WARNING,
            swap_id=swap_id,
        )

        assert alert.swap_id == swap_id

    def test_bulk_create_multiple_alerts(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_faculty2: Person,
    ):
        """Test creating multiple alerts (bulk creation pattern)."""
        alerts = []
        base_date = date.today()

        # Create 5 alerts
        for i in range(5):
            faculty = sample_faculty_for_conflicts if i % 2 == 0 else sample_faculty2
            alert = conflict_repo.create(
                faculty_id=faculty.id,
                conflict_type=ConflictType.BACK_TO_BACK,
                fmit_week=base_date + timedelta(days=7 * i),
                description=f"Alert {i + 1}",
                severity=ConflictSeverity.WARNING,
            )
            alerts.append(alert)

        assert len(alerts) == 5
        assert all(a.id is not None for a in alerts)
        assert all(a.status == ConflictAlertStatus.NEW for a in alerts)


class TestConflictRepositoryGet:
    """Tests for retrieving conflict alerts."""

    def test_get_by_id_existing(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test retrieving an existing alert by ID."""
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Test alert",
        )

        retrieved = conflict_repo.get_by_id(alert.id)

        assert retrieved is not None
        assert retrieved.id == alert.id
        assert retrieved.faculty_id == alert.faculty_id
        assert retrieved.description == alert.description

    def test_get_by_id_nonexistent(self, conflict_repo: ConflictRepository):
        """Test retrieving a non-existent alert returns None."""
        fake_id = uuid4()
        result = conflict_repo.get_by_id(fake_id)

        assert result is None


class TestConflictRepositoryUpdate:
    """Tests for updating conflict alerts."""

    def test_update_status(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test updating alert status."""
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Test alert",
        )

        updated = conflict_repo.update(
            alert.id,
            status=ConflictAlertStatus.ACKNOWLEDGED
        )

        assert updated is not None
        assert updated.status == ConflictAlertStatus.ACKNOWLEDGED

    def test_update_multiple_fields(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        admin_user: User,
    ):
        """Test updating multiple fields at once."""
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Original description",
        )

        updated = conflict_repo.update(
            alert.id,
            status=ConflictAlertStatus.RESOLVED,
            resolution_notes="Swapped with colleague",
            resolved_at=datetime.utcnow(),
            resolved_by_id=admin_user.id,
        )

        assert updated is not None
        assert updated.status == ConflictAlertStatus.RESOLVED
        assert updated.resolution_notes == "Swapped with colleague"
        assert updated.resolved_at is not None
        assert updated.resolved_by_id == admin_user.id

    def test_update_nonexistent_alert(self, conflict_repo: ConflictRepository):
        """Test updating non-existent alert returns None."""
        fake_id = uuid4()
        result = conflict_repo.update(
            fake_id,
            status=ConflictAlertStatus.RESOLVED
        )

        assert result is None


class TestConflictRepositoryDelete:
    """Tests for deleting conflict alerts."""

    def test_delete_existing_alert(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test deleting an existing alert."""
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Test alert",
        )

        result = conflict_repo.delete(alert.id)

        assert result is True

        # Verify it's gone
        retrieved = conflict_repo.get_by_id(alert.id)
        assert retrieved is None

    def test_delete_nonexistent_alert(self, conflict_repo: ConflictRepository):
        """Test deleting non-existent alert returns False."""
        fake_id = uuid4()
        result = conflict_repo.delete(fake_id)

        assert result is False

    def test_bulk_delete_multiple_alerts(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test bulk deleting multiple alerts."""
        # Create 5 alerts
        alert_ids = []
        for i in range(5):
            alert = conflict_repo.create(
                faculty_id=sample_faculty_for_conflicts.id,
                conflict_type=ConflictType.BACK_TO_BACK,
                fmit_week=date.today() + timedelta(days=7 * i),
                description=f"Alert {i + 1}",
            )
            alert_ids.append(alert.id)

        # Delete 3 of them
        deleted_ids = alert_ids[:3]
        count = conflict_repo.bulk_delete(deleted_ids)

        assert count == 3

        # Verify deleted alerts are gone
        for alert_id in deleted_ids:
            assert conflict_repo.get_by_id(alert_id) is None

        # Verify remaining alerts still exist
        for alert_id in alert_ids[3:]:
            assert conflict_repo.get_by_id(alert_id) is not None


# ============================================================================
# Tests for Query Methods
# ============================================================================


class TestConflictRepositoryFindByFaculty:
    """Tests for finding alerts by faculty."""

    def test_find_by_faculty_unresolved_only(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_faculty2: Person,
    ):
        """Test finding unresolved alerts for a faculty member."""
        # Create alerts for faculty 1
        alert1 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Alert 1",
        )

        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Alert 2",
        )

        # Create resolved alert for faculty 1
        alert3 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="Alert 3",
        )
        conflict_repo.update(alert3.id, status=ConflictAlertStatus.RESOLVED)

        # Create alert for faculty 2
        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Other faculty alert",
        )

        # Find unresolved alerts for faculty 1
        alerts = conflict_repo.find_by_faculty(sample_faculty_for_conflicts.id)

        assert len(alerts) == 2
        assert all(a.faculty_id == sample_faculty_for_conflicts.id for a in alerts)
        assert all(a.status in [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED] for a in alerts)

    def test_find_by_faculty_include_resolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding all alerts including resolved ones."""
        # Create mix of alerts
        alert1 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Alert 1",
        )

        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Alert 2",
        )
        conflict_repo.update(alert2.id, status=ConflictAlertStatus.RESOLVED)

        # Find all alerts including resolved
        alerts = conflict_repo.find_by_faculty(
            sample_faculty_for_conflicts.id,
            include_resolved=True
        )

        assert len(alerts) == 2
        statuses = [a.status for a in alerts]
        assert ConflictAlertStatus.NEW in statuses
        assert ConflictAlertStatus.RESOLVED in statuses


class TestConflictRepositoryFindByStatus:
    """Tests for finding alerts by status."""

    def test_find_by_status_new(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding NEW alerts."""
        # Create alerts with different statuses
        alert1 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="New alert",
        )

        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Acknowledged alert",
        )
        conflict_repo.update(alert2.id, status=ConflictAlertStatus.ACKNOWLEDGED)

        # Find NEW alerts
        alerts = conflict_repo.find_by_status(ConflictAlertStatus.NEW)

        assert len(alerts) == 1
        assert all(a.status == ConflictAlertStatus.NEW for a in alerts)

    def test_find_by_status_with_faculty_filter(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_faculty2: Person,
    ):
        """Test finding alerts by status for specific faculty."""
        # Create NEW alerts for both faculty
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Faculty 1 alert",
        )

        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Faculty 2 alert",
        )

        # Find NEW alerts for faculty 1 only
        alerts = conflict_repo.find_by_status(
            ConflictAlertStatus.NEW,
            faculty_id=sample_faculty_for_conflicts.id
        )

        assert len(alerts) == 1
        assert alerts[0].faculty_id == sample_faculty_for_conflicts.id


class TestConflictRepositoryFindBySeverity:
    """Tests for finding alerts by severity."""

    def test_find_by_severity_critical_unresolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding unresolved CRITICAL alerts."""
        # Create alerts with different severities
        alert1 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Critical alert",
            severity=ConflictSeverity.CRITICAL,
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Warning alert",
            severity=ConflictSeverity.WARNING,
        )

        # Create resolved critical alert
        alert3 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=21),
            description="Resolved critical",
            severity=ConflictSeverity.CRITICAL,
        )
        conflict_repo.update(alert3.id, status=ConflictAlertStatus.RESOLVED)

        # Find unresolved critical alerts
        alerts = conflict_repo.find_by_severity(ConflictSeverity.CRITICAL)

        assert len(alerts) == 1
        assert all(a.severity == ConflictSeverity.CRITICAL for a in alerts)
        assert all(a.status in [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED] for a in alerts)

    def test_find_by_severity_include_resolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding all alerts of a severity including resolved."""
        # Create critical alerts
        alert1 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Active critical",
            severity=ConflictSeverity.CRITICAL,
        )

        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Resolved critical",
            severity=ConflictSeverity.CRITICAL,
        )
        conflict_repo.update(alert2.id, status=ConflictAlertStatus.RESOLVED)

        # Find all critical alerts
        alerts = conflict_repo.find_by_severity(
            ConflictSeverity.CRITICAL,
            unresolved_only=False
        )

        assert len(alerts) == 2


class TestConflictRepositoryFindByType:
    """Tests for finding alerts by conflict type."""

    def test_find_by_type_unresolved_only(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding unresolved alerts by type."""
        # Create alerts of different types
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Leave overlap 1",
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Leave overlap 2",
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="Back to back",
        )

        # Create resolved leave overlap
        alert4 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=28),
            description="Resolved leave overlap",
        )
        conflict_repo.update(alert4.id, status=ConflictAlertStatus.RESOLVED)

        # Find unresolved leave overlaps
        alerts = conflict_repo.find_by_type(ConflictType.LEAVE_FMIT_OVERLAP)

        assert len(alerts) == 2
        assert all(a.conflict_type == ConflictType.LEAVE_FMIT_OVERLAP for a in alerts)
        assert all(a.status in [ConflictAlertStatus.NEW, ConflictAlertStatus.ACKNOWLEDGED] for a in alerts)

    def test_find_by_type_include_resolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding all alerts of a type including resolved."""
        # Create mix of alerts
        alert1 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Active back-to-back",
        )

        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Resolved back-to-back",
        )
        conflict_repo.update(alert2.id, status=ConflictAlertStatus.RESOLVED)

        # Find all back-to-back alerts
        alerts = conflict_repo.find_by_type(
            ConflictType.BACK_TO_BACK,
            unresolved_only=False
        )

        assert len(alerts) == 2


class TestConflictRepositoryFindByWeek:
    """Tests for finding alerts by FMIT week."""

    def test_find_by_week_all_faculty(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_faculty2: Person,
    ):
        """Test finding all alerts for a specific week."""
        target_week = date.today() + timedelta(days=14)

        # Create alerts for target week
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=target_week,
            description="Faculty 1 alert",
        )

        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
            description="Faculty 2 alert",
        )

        # Create alert for different week
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="Different week",
        )

        # Find alerts for target week
        alerts = conflict_repo.find_by_week(target_week)

        assert len(alerts) == 2
        assert all(a.fmit_week == target_week for a in alerts)

    def test_find_by_week_specific_faculty(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_faculty2: Person,
    ):
        """Test finding alerts for a week and specific faculty."""
        target_week = date.today() + timedelta(days=14)

        # Create alerts for target week
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=target_week,
            description="Faculty 1 alert",
        )

        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
            description="Faculty 2 alert",
        )

        # Find alerts for faculty 1 only
        alerts = conflict_repo.find_by_week(
            target_week,
            faculty_id=sample_faculty_for_conflicts.id
        )

        assert len(alerts) == 1
        assert alerts[0].faculty_id == sample_faculty_for_conflicts.id


class TestConflictRepositoryFindByLeave:
    """Tests for finding alerts by leave reference."""

    def test_find_by_leave(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_leave: Absence,
    ):
        """Test finding alerts related to a leave record."""
        # Create alerts with leave reference
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=30),
            description="Leave overlap 1",
            leave_id=sample_leave.id,
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=35),
            description="Leave overlap 2",
            leave_id=sample_leave.id,
        )

        # Create alert without leave reference
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="No leave reference",
        )

        # Find alerts for the leave
        alerts = conflict_repo.find_by_leave(sample_leave.id)

        assert len(alerts) == 2
        assert all(a.leave_id == sample_leave.id for a in alerts)


class TestConflictRepositoryFindUpcoming:
    """Tests for finding upcoming alerts."""

    def test_find_upcoming_default_days(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding upcoming alerts with default 30 days."""
        today = date.today()

        # Create alerts at different dates
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=today + timedelta(days=7),
            description="Within 30 days",
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=today + timedelta(days=20),
            description="Within 30 days",
        )

        # Create alert beyond 30 days
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=today + timedelta(days=35),
            description="Beyond 30 days",
        )

        # Create past alert
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=today - timedelta(days=7),
            description="Past alert",
        )

        # Find upcoming alerts
        alerts = conflict_repo.find_upcoming()

        assert len(alerts) == 2
        for alert in alerts:
            assert alert.fmit_week >= today
            assert alert.fmit_week <= today + timedelta(days=30)

    def test_find_upcoming_custom_days(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding upcoming alerts with custom days."""
        today = date.today()

        # Create alerts at different dates
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=today + timedelta(days=5),
            description="Within 7 days",
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=today + timedelta(days=10),
            description="Beyond 7 days",
        )

        # Find upcoming alerts within 7 days
        alerts = conflict_repo.find_upcoming(days_ahead=7)

        assert len(alerts) == 1
        assert alerts[0].fmit_week == today + timedelta(days=5)

    def test_find_upcoming_excludes_resolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test that upcoming alerts exclude resolved ones."""
        today = date.today()

        # Create unresolved alert
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=today + timedelta(days=7),
            description="Unresolved",
        )

        # Create resolved alert
        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=today + timedelta(days=14),
            description="Resolved",
        )
        conflict_repo.update(alert2.id, status=ConflictAlertStatus.RESOLVED)

        # Find upcoming alerts
        alerts = conflict_repo.find_upcoming()

        assert len(alerts) == 1
        assert alerts[0].status != ConflictAlertStatus.RESOLVED


class TestConflictRepositoryPagination:
    """Tests for paginated queries and date range filtering."""

    def test_find_with_pagination_basic(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test basic pagination."""
        # Create 25 alerts
        for i in range(25):
            conflict_repo.create(
                faculty_id=sample_faculty_for_conflicts.id,
                conflict_type=ConflictType.BACK_TO_BACK,
                fmit_week=date.today() + timedelta(days=i),
                description=f"Alert {i + 1}",
            )

        # Get first page (default 20 per page)
        alerts, total = conflict_repo.find_with_pagination(page=1, page_size=20)

        assert len(alerts) == 20
        assert total == 25

        # Get second page
        alerts, total = conflict_repo.find_with_pagination(page=2, page_size=20)

        assert len(alerts) == 5
        assert total == 25

    def test_find_with_date_range(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test filtering by date range."""
        base_date = date.today()

        # Create alerts across different dates
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=base_date + timedelta(days=5),
            description="Alert 1",
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=base_date + timedelta(days=15),
            description="Alert 2",
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=base_date + timedelta(days=25),
            description="Alert 3",
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=base_date + timedelta(days=35),
            description="Alert 4",
        )

        # Query date range (day 10 to day 30)
        alerts, total = conflict_repo.find_with_pagination(
            start_date=base_date + timedelta(days=10),
            end_date=base_date + timedelta(days=30),
        )

        assert total == 2
        for alert in alerts:
            assert base_date + timedelta(days=10) <= alert.fmit_week <= base_date + timedelta(days=30)

    def test_find_with_multiple_filters(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_faculty2: Person,
    ):
        """Test pagination with multiple filters."""
        base_date = date.today()

        # Create alerts with various attributes
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=base_date + timedelta(days=7),
            description="Match all filters",
            severity=ConflictSeverity.CRITICAL,
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=base_date + timedelta(days=14),
            description="Wrong type",
            severity=ConflictSeverity.CRITICAL,
        )

        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=base_date + timedelta(days=21),
            description="Wrong faculty",
            severity=ConflictSeverity.CRITICAL,
        )

        # Query with multiple filters
        alerts, total = conflict_repo.find_with_pagination(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=ConflictSeverity.CRITICAL,
        )

        assert total == 1
        assert alerts[0].description == "Match all filters"


# ============================================================================
# Tests for Existence Checks
# ============================================================================


class TestConflictRepositoryExistsSimilar:
    """Tests for checking similar alert existence."""

    def test_exists_similar_found(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test finding similar unresolved alert."""
        target_week = date.today() + timedelta(days=14)

        # Create an alert
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
            description="Original alert",
        )

        # Check for similar alert
        similar = conflict_repo.exists_similar(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
        )

        assert similar is not None
        assert similar.id == alert.id

    def test_exists_similar_not_found_different_week(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test no similar alert for different week."""
        # Create an alert
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Original alert",
        )

        # Check for different week
        similar = conflict_repo.exists_similar(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=21),
        )

        assert similar is None

    def test_exists_similar_excludes_resolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test that resolved alerts are not found as similar."""
        target_week = date.today() + timedelta(days=14)

        # Create and resolve an alert
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
            description="Resolved alert",
        )
        conflict_repo.update(alert.id, status=ConflictAlertStatus.RESOLVED)

        # Check for similar alert
        similar = conflict_repo.exists_similar(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
        )

        assert similar is None


# ============================================================================
# Tests for Statistics
# ============================================================================


class TestConflictRepositoryStatistics:
    """Tests for statistical queries."""

    def test_count_by_status(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test counting alerts by status."""
        # Create alerts with different statuses
        alert1 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Alert 1",
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Alert 2",
        )

        alert3 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=21),
            description="Alert 3",
        )

        # Update statuses
        conflict_repo.update(alert1.id, status=ConflictAlertStatus.ACKNOWLEDGED)
        conflict_repo.update(alert3.id, status=ConflictAlertStatus.RESOLVED)

        # Count by status
        counts = conflict_repo.count_by_status()

        assert counts.get("new") == 1
        assert counts.get("acknowledged") == 1
        assert counts.get("resolved") == 1

    def test_count_by_status_for_faculty(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_faculty2: Person,
    ):
        """Test counting alerts by status for specific faculty."""
        # Create alerts for faculty 1
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Faculty 1 alert",
        )

        # Create alerts for faculty 2
        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Faculty 2 alert 1",
        )

        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=21),
            description="Faculty 2 alert 2",
        )

        # Count for faculty 2 only
        counts = conflict_repo.count_by_status(faculty_id=sample_faculty2.id)

        assert counts.get("new") == 2

    def test_count_by_severity(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test counting alerts by severity."""
        # Create alerts with different severities
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Critical 1",
            severity=ConflictSeverity.CRITICAL,
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Critical 2",
            severity=ConflictSeverity.CRITICAL,
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="Warning",
            severity=ConflictSeverity.WARNING,
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.CALL_CASCADE,
            fmit_week=date.today() + timedelta(days=28),
            description="Info",
            severity=ConflictSeverity.INFO,
        )

        # Count by severity
        counts = conflict_repo.count_by_severity()

        assert counts.get("critical") == 2
        assert counts.get("warning") == 1
        assert counts.get("info") == 1

    def test_count_by_severity_exclude_resolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test counting by severity excludes resolved by default."""
        # Create critical alerts
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Unresolved critical",
            severity=ConflictSeverity.CRITICAL,
        )

        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Resolved critical",
            severity=ConflictSeverity.CRITICAL,
        )
        conflict_repo.update(alert2.id, status=ConflictAlertStatus.RESOLVED)

        # Count unresolved only
        counts = conflict_repo.count_by_severity(unresolved_only=True)

        assert counts.get("critical") == 1

        # Count all
        counts = conflict_repo.count_by_severity(unresolved_only=False)

        assert counts.get("critical") == 2

    def test_count_unresolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test counting unresolved alerts."""
        # Create mix of alerts
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="New alert",
        )

        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Acknowledged alert",
        )
        conflict_repo.update(alert2.id, status=ConflictAlertStatus.ACKNOWLEDGED)

        alert3 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="Resolved alert",
        )
        conflict_repo.update(alert3.id, status=ConflictAlertStatus.RESOLVED)

        # Count unresolved
        count = conflict_repo.count_unresolved()

        assert count == 2  # NEW and ACKNOWLEDGED

    def test_count_unresolved_for_faculty(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_faculty2: Person,
    ):
        """Test counting unresolved alerts for specific faculty."""
        # Create alerts for faculty 1
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=7),
            description="Faculty 1 alert",
        )

        # Create alerts for faculty 2
        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=14),
            description="Faculty 2 alert 1",
        )

        conflict_repo.create(
            faculty_id=sample_faculty2.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=21),
            description="Faculty 2 alert 2",
        )

        # Count for faculty 2 only
        count = conflict_repo.count_unresolved(faculty_id=sample_faculty2.id)

        assert count == 2

    def test_count_critical_unresolved(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test counting critical unresolved alerts."""
        # Create critical alerts
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=7),
            description="Unresolved critical 1",
            severity=ConflictSeverity.CRITICAL,
        )

        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=14),
            description="Unresolved critical 2",
            severity=ConflictSeverity.CRITICAL,
        )

        # Create warning alert (should not be counted)
        conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=date.today() + timedelta(days=21),
            description="Unresolved warning",
            severity=ConflictSeverity.WARNING,
        )

        # Create resolved critical (should not be counted)
        alert4 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=28),
            description="Resolved critical",
            severity=ConflictSeverity.CRITICAL,
        )
        conflict_repo.update(alert4.id, status=ConflictAlertStatus.RESOLVED)

        # Count critical unresolved
        count = conflict_repo.count_critical_unresolved()

        assert count == 2


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


class TestConflictRepositoryEdgeCases:
    """Tests for edge cases and integration scenarios."""

    def test_empty_results(self, conflict_repo: ConflictRepository):
        """Test queries on empty database."""
        # Try various queries
        assert conflict_repo.find_by_status(ConflictAlertStatus.NEW) == []
        assert conflict_repo.find_by_severity(ConflictSeverity.CRITICAL) == []
        assert conflict_repo.find_upcoming() == []
        assert conflict_repo.count_unresolved() == 0
        assert conflict_repo.count_critical_unresolved() == 0

        alerts, total = conflict_repo.find_with_pagination()
        assert alerts == []
        assert total == 0

    def test_create_multiple_alerts_same_faculty_same_week(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test creating multiple different alerts for same faculty and week."""
        target_week = date.today() + timedelta(days=14)

        # Create different types of conflicts for same week
        alert1 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=target_week,
            description="Leave overlap",
        )

        alert2 = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            fmit_week=target_week,
            description="Back to back",
        )

        assert alert1.id != alert2.id
        assert alert1.conflict_type != alert2.conflict_type

        # Both should be findable
        alerts = conflict_repo.find_by_week(target_week, sample_faculty_for_conflicts.id)
        assert len(alerts) == 2

    def test_ordering_consistency(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
    ):
        """Test that results are consistently ordered."""
        # Create alerts
        for i in range(5):
            conflict_repo.create(
                faculty_id=sample_faculty_for_conflicts.id,
                conflict_type=ConflictType.BACK_TO_BACK,
                fmit_week=date.today() + timedelta(days=7 * i),
                description=f"Alert {i}",
            )

        # Query multiple times and check ordering
        result1 = conflict_repo.find_by_faculty(sample_faculty_for_conflicts.id)
        result2 = conflict_repo.find_by_faculty(sample_faculty_for_conflicts.id)

        assert [a.id for a in result1] == [a.id for a in result2]

    def test_full_workflow_scenario(
        self,
        conflict_repo: ConflictRepository,
        sample_faculty_for_conflicts: Person,
        sample_leave: Absence,
        admin_user: User,
    ):
        """Test a complete workflow from creation to resolution."""
        # 1. Create a conflict alert
        alert = conflict_repo.create(
            faculty_id=sample_faculty_for_conflicts.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            fmit_week=date.today() + timedelta(days=30),
            description="Vacation overlaps with FMIT assignment",
            severity=ConflictSeverity.CRITICAL,
            leave_id=sample_leave.id,
        )

        assert alert.status == ConflictAlertStatus.NEW
        assert conflict_repo.count_critical_unresolved() == 1

        # 2. Acknowledge the alert
        conflict_repo.update(
            alert.id,
            status=ConflictAlertStatus.ACKNOWLEDGED,
            acknowledged_at=datetime.utcnow(),
            acknowledged_by_id=admin_user.id,
        )

        # Still counts as unresolved
        assert conflict_repo.count_unresolved() == 1

        # 3. Find it in various ways
        assert len(conflict_repo.find_by_faculty(sample_faculty_for_conflicts.id)) == 1
        assert len(conflict_repo.find_by_severity(ConflictSeverity.CRITICAL)) == 1
        assert len(conflict_repo.find_by_leave(sample_leave.id)) == 1

        # 4. Resolve the alert
        conflict_repo.update(
            alert.id,
            status=ConflictAlertStatus.RESOLVED,
            resolution_notes="Swapped FMIT week with Dr. Jones",
            resolved_at=datetime.utcnow(),
            resolved_by_id=admin_user.id,
        )

        # No longer counts as unresolved
        assert conflict_repo.count_unresolved() == 0
        assert conflict_repo.count_critical_unresolved() == 0

        # 5. Verify it's excluded from unresolved queries
        assert len(conflict_repo.find_by_faculty(sample_faculty_for_conflicts.id)) == 0

        # But included when we request resolved ones
        assert len(conflict_repo.find_by_faculty(
            sample_faculty_for_conflicts.id,
            include_resolved=True
        )) == 1
