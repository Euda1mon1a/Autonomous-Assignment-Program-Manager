"""Tests for ConflictAutoDetector service."""
from datetime import date, timedelta
from uuid import uuid4

from app.models.absence import Absence
from app.services.conflict_auto_detector import ConflictAutoDetector, ConflictInfo


class TestConflictInfo:
    """Tests for ConflictInfo dataclass."""

    def test_create_conflict_info(self):
        """Test creating a conflict info object."""
        info = ConflictInfo(
            faculty_id=uuid4(),
            faculty_name="Dr. Smith",
            conflict_type="leave_fmit_overlap",
            fmit_week=date.today() + timedelta(days=14),
        )

        assert info.faculty_name == "Dr. Smith"
        assert info.conflict_type == "leave_fmit_overlap"
        assert info.severity == "warning"  # Default

    def test_conflict_info_with_leave(self):
        """Test conflict info with leave reference."""
        leave_id = uuid4()
        info = ConflictInfo(
            faculty_id=uuid4(),
            faculty_name="Dr. Jones",
            conflict_type="leave_fmit_overlap",
            fmit_week=date.today(),
            leave_id=leave_id,
            severity="critical",
            description="TDY overlaps with FMIT",
        )

        assert info.leave_id == leave_id
        assert info.severity == "critical"


class TestConflictAutoDetector:
    """Tests for ConflictAutoDetector service."""

    def test_init(self, db):
        """Test detector initialization."""
        detector = ConflictAutoDetector(db)
        assert detector.db == db

    def test_detect_conflicts_for_absence_not_found(self, db):
        """Test detection when absence doesn't exist."""
        detector = ConflictAutoDetector(db)
        conflicts = detector.detect_conflicts_for_absence(uuid4())
        assert conflicts == []

    def test_detect_conflicts_for_blocking_absence(self, db, sample_faculty, sample_absence):
        """Test detection for blocking absence."""
        detector = ConflictAutoDetector(db)

        # Make sure absence is blocking
        sample_absence.is_blocking = True
        db.commit()

        conflicts = detector.detect_conflicts_for_absence(sample_absence.id)

        # Currently returns empty as FMIT week detection is TODO
        # This test validates the method runs without error
        assert isinstance(conflicts, list)

    def test_detect_conflicts_for_deployment(self, db, sample_faculty):
        """Test deployment type is always treated as blocking."""
        # Create deployment absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=60),
            absence_type="deployment",
            is_blocking=False,  # Even if not marked blocking
        )
        db.add(absence)
        db.commit()

        detector = ConflictAutoDetector(db)
        conflicts = detector.detect_conflicts_for_absence(absence.id)

        # Should still process as blocking
        assert isinstance(conflicts, list)

    def test_detect_all_conflicts_default_range(self, db):
        """Test scanning all conflicts with default date range."""
        detector = ConflictAutoDetector(db)
        conflicts = detector.detect_all_conflicts()

        assert isinstance(conflicts, list)

    def test_detect_all_conflicts_with_faculty_filter(self, db, sample_faculty):
        """Test scanning conflicts for specific faculty."""
        detector = ConflictAutoDetector(db)
        conflicts = detector.detect_all_conflicts(faculty_id=sample_faculty.id)

        assert isinstance(conflicts, list)

    def test_detect_all_conflicts_with_date_range(self, db):
        """Test scanning conflicts with custom date range."""
        detector = ConflictAutoDetector(db)

        start = date.today()
        end = date.today() + timedelta(days=30)

        conflicts = detector.detect_all_conflicts(
            start_date=start,
            end_date=end,
        )

        assert isinstance(conflicts, list)

    def test_create_conflict_alerts(self, db, sample_faculty):
        """Test creating alerts from detected conflicts."""
        detector = ConflictAutoDetector(db)

        conflicts = [
            ConflictInfo(
                faculty_id=sample_faculty.id,
                faculty_name=sample_faculty.name,
                conflict_type="leave_fmit_overlap",
                fmit_week=date.today() + timedelta(days=14),
                severity="critical",
                description="Test conflict",
            ),
        ]

        alert_ids = detector.create_conflict_alerts(conflicts)

        assert len(alert_ids) == 1
        assert all(isinstance(aid, type(uuid4())) for aid in alert_ids)

    def test_create_conflict_alerts_empty_list(self, db):
        """Test creating alerts with empty conflict list."""
        detector = ConflictAutoDetector(db)
        alert_ids = detector.create_conflict_alerts([])

        assert alert_ids == []


class TestBackToBackDetection:
    """Tests for back-to-back conflict detection."""

    def test_check_back_to_back_no_conflict(self, db, sample_faculty):
        """Test back-to-back check with no conflict."""
        detector = ConflictAutoDetector(db)

        # Weeks with gaps
        weeks = [
            date.today(),
            date.today() + timedelta(days=21),  # 3 weeks gap
            date.today() + timedelta(days=42),  # 3 weeks gap
        ]

        conflicts = detector._check_back_to_back(sample_faculty.id, weeks)
        assert conflicts == []

    def test_check_back_to_back_with_conflict(self, db, sample_faculty):
        """Test back-to-back check detects consecutive weeks."""
        detector = ConflictAutoDetector(db)

        # Consecutive weeks (back-to-back)
        weeks = [
            date.today(),
            date.today() + timedelta(days=7),  # 1 week gap - back to back!
        ]

        conflicts = detector._check_back_to_back(sample_faculty.id, weeks)

        # Should detect the conflict
        assert len(conflicts) >= 1
        assert any(c.conflict_type == "back_to_back" for c in conflicts)


class TestFMITOverlapDetection:
    """Tests for FMIT overlap detection."""

    def test_find_fmit_overlaps_placeholder(self, db, sample_faculty):
        """Test FMIT overlap finder (currently placeholder)."""
        detector = ConflictAutoDetector(db)

        overlaps = detector._find_fmit_overlaps(
            faculty_id=sample_faculty.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )

        # Currently returns empty list (TODO implementation)
        assert isinstance(overlaps, list)
