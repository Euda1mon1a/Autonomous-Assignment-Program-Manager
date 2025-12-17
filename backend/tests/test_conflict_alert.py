"""Tests for ConflictAlert model."""
from datetime import date, datetime, timedelta
from uuid import uuid4

from app.models.absence import Absence
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person


class TestConflictAlertStatus:
    """Tests for ConflictAlertStatus enum."""

    def test_status_values(self):
        """Test all status values exist."""
        assert ConflictAlertStatus.NEW == "new"
        assert ConflictAlertStatus.ACKNOWLEDGED == "acknowledged"
        assert ConflictAlertStatus.RESOLVED == "resolved"
        assert ConflictAlertStatus.IGNORED == "ignored"

    def test_status_count(self):
        """Test we have expected number of statuses."""
        assert len(ConflictAlertStatus) == 4


class TestConflictSeverity:
    """Tests for ConflictSeverity enum."""

    def test_severity_values(self):
        """Test all severity values."""
        assert ConflictSeverity.CRITICAL == "critical"
        assert ConflictSeverity.WARNING == "warning"
        assert ConflictSeverity.INFO == "info"

    def test_severity_count(self):
        """Test expected number of severities."""
        assert len(ConflictSeverity) == 3


class TestConflictType:
    """Tests for ConflictType enum."""

    def test_type_values(self):
        """Test all conflict type values."""
        assert ConflictType.LEAVE_FMIT_OVERLAP == "leave_fmit_overlap"
        assert ConflictType.BACK_TO_BACK == "back_to_back"
        assert ConflictType.EXCESSIVE_ALTERNATING == "excessive_alternating"
        assert ConflictType.CALL_CASCADE == "call_cascade"
        assert ConflictType.EXTERNAL_COMMITMENT == "external_commitment"


class TestConflictAlertModel:
    """Tests for ConflictAlert model."""

    def test_create_alert(self, db, sample_faculty):
        """Test creating a basic conflict alert."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=ConflictSeverity.CRITICAL,
            fmit_week=date.today() + timedelta(days=14),
            description="Vacation overlaps with FMIT week",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        assert alert.id is not None
        assert alert.faculty_id == sample_faculty.id
        assert alert.conflict_type == ConflictType.LEAVE_FMIT_OVERLAP
        assert alert.severity == ConflictSeverity.CRITICAL
        assert alert.status == ConflictAlertStatus.NEW  # Default

    def test_alert_with_leave_reference(self, db, sample_faculty, sample_absence):
        """Test alert referencing an absence record."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=ConflictSeverity.CRITICAL,
            fmit_week=date.today() + timedelta(days=14),
            leave_id=sample_absence.id,
            description="TDY conflicts with FMIT",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        assert alert.leave_id == sample_absence.id
        # Verify the foreign key reference is valid
        leave = db.query(Absence).filter(Absence.id == alert.leave_id).first()
        assert leave is not None
        assert leave.id == sample_absence.id

    def test_acknowledge_alert(self, db, sample_faculty, admin_user):
        """Test acknowledging an alert."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            severity=ConflictSeverity.WARNING,
            fmit_week=date.today() + timedelta(days=14),
            description="Back-to-back FMIT weeks detected",
        )
        db.add(alert)
        db.commit()

        # Acknowledge
        alert.acknowledge(admin_user.id)
        db.commit()
        db.refresh(alert)

        assert alert.status == ConflictAlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_at is not None
        assert alert.acknowledged_by_id == admin_user.id

    def test_resolve_alert(self, db, sample_faculty, admin_user):
        """Test resolving an alert."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=ConflictSeverity.CRITICAL,
            fmit_week=date.today() + timedelta(days=14),
            description="Conflict detected",
        )
        db.add(alert)
        db.commit()

        # Resolve
        alert.resolve(admin_user.id, notes="Swapped FMIT week with Dr. Jones")
        db.commit()
        db.refresh(alert)

        assert alert.status == ConflictAlertStatus.RESOLVED
        assert alert.resolved_at is not None
        assert alert.resolved_by_id == admin_user.id
        assert alert.resolution_notes == "Swapped FMIT week with Dr. Jones"

    def test_ignore_alert(self, db, sample_faculty, admin_user):
        """Test ignoring an alert (false positive)."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.CALL_CASCADE,
            severity=ConflictSeverity.INFO,
            fmit_week=date.today() + timedelta(days=14),
            description="Call cascade alert",
        )
        db.add(alert)
        db.commit()

        # Ignore
        alert.ignore(admin_user.id, "Not a real conflict - coverage already arranged")
        db.commit()
        db.refresh(alert)

        assert alert.status == ConflictAlertStatus.IGNORED
        assert "Ignored:" in alert.resolution_notes

    def test_alert_faculty_relationship(self, db, sample_faculty):
        """Test alert relationship to faculty."""
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            severity=ConflictSeverity.WARNING,
            fmit_week=date.today() + timedelta(days=14),
            description="Test alert",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Verify the foreign key is set correctly
        assert alert.faculty_id == sample_faculty.id
        # Query to verify the faculty exists
        faculty = db.query(Person).filter(Person.id == alert.faculty_id).first()
        assert faculty is not None
        assert faculty.name == sample_faculty.name

    def test_alert_timestamps(self, db, sample_faculty):
        """Test alert created_at timestamp."""
        before = datetime.utcnow()

        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.BACK_TO_BACK,
            severity=ConflictSeverity.WARNING,
            fmit_week=date.today() + timedelta(days=14),
            description="Test alert",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        after = datetime.utcnow()

        assert before <= alert.created_at <= after
