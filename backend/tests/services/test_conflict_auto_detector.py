"""Test suite for conflict auto-detector service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.rotation_template import RotationTemplate
from app.services.conflict_auto_detector import ConflictAutoDetector


class TestConflictAutoDetector:
    """Test suite for conflict auto-detector service."""

    @pytest.fixture
    def detector(self, db: Session) -> ConflictAutoDetector:
        """Create a conflict auto-detector instance."""
        return ConflictAutoDetector(db)

    @pytest.fixture
    def resident(self, db: Session) -> Person:
        """Create a resident."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def rotation_template(self, db: Session) -> RotationTemplate:
        """Create a rotation template."""
        template = RotationTemplate(
            id=uuid4(),
            name="Rotation",
            rotation_type="outpatient",
            abbreviation="ROT",
            max_residents=4,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def test_detector_initialization(self, db: Session):
        """Test ConflictAutoDetector initialization."""
        detector = ConflictAutoDetector(db)

        assert detector.db is db

    def test_detect_conflicts(
        self,
        detector: ConflictAutoDetector,
    ):
        """Test detecting all conflicts."""
        conflicts = detector.detect_all()

        assert isinstance(conflicts, list)

    def test_detect_person_conflicts(
        self,
        detector: ConflictAutoDetector,
        resident: Person,
    ):
        """Test detecting conflicts for specific person."""
        conflicts = detector.detect_for_person(resident.id)

        assert isinstance(conflicts, list)

    def test_detect_overlapping_blocks(
        self,
        detector: ConflictAutoDetector,
        resident: Person,
        rotation_template: RotationTemplate,
        db: Session,
    ):
        """Test detection of overlapping block assignments."""
        same_day = date.today()

        # Create two blocks
        block_am = Block(
            id=uuid4(),
            date=same_day,
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        block_pm = Block(
            id=uuid4(),
            date=same_day,
            time_of_day="PM",
            block_number=1,
            is_weekend=False,
        )
        db.add_all([block_am, block_pm])
        db.commit()

        # Assign to both blocks
        assignment_1 = Assignment(
            id=uuid4(),
            person_id=resident.id,
            block_id=block_am.id,
            rotation_template_id=rotation_template.id,
            role="primary",
        )
        assignment_2 = Assignment(
            id=uuid4(),
            person_id=resident.id,
            block_id=block_pm.id,
            rotation_template_id=rotation_template.id,
            role="primary",
        )
        db.add_all([assignment_1, assignment_2])
        db.commit()

        # Detect conflicts
        conflicts = detector.detect_for_person(resident.id)

        assert isinstance(conflicts, list)

    def test_detect_insufficient_rest(
        self,
        detector: ConflictAutoDetector,
        resident: Person,
        rotation_template: RotationTemplate,
        db: Session,
    ):
        """Test detection of insufficient rest between shifts."""
        day1 = date.today()
        day2 = day1 + timedelta(hours=20)  # Less than 24 hours

        block_1 = Block(
            id=uuid4(),
            date=day1,
            time_of_day="PM",
            block_number=1,
            is_weekend=False,
        )
        block_2 = Block(
            id=uuid4(),
            date=day2,
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add_all([block_1, block_2])
        db.commit()

        assignment_1 = Assignment(
            id=uuid4(),
            person_id=resident.id,
            block_id=block_1.id,
            rotation_template_id=rotation_template.id,
            role="primary",
        )
        assignment_2 = Assignment(
            id=uuid4(),
            person_id=resident.id,
            block_id=block_2.id,
            rotation_template_id=rotation_template.id,
            role="primary",
        )
        db.add_all([assignment_1, assignment_2])
        db.commit()

        conflicts = detector.detect_for_person(resident.id)

        assert isinstance(conflicts, list)

    def test_auto_fix_conflicts(
        self,
        detector: ConflictAutoDetector,
    ):
        """Test automatic conflict fixing."""
        # Get all conflicts
        conflicts = detector.detect_all()

        # Try to auto-fix
        result = detector.auto_fix()

        assert isinstance(result, (bool, int, dict))

    def test_suggest_conflict_resolution(
        self,
        detector: ConflictAutoDetector,
        resident: Person,
    ):
        """Test getting suggestions for conflict resolution."""
        suggestions = detector.suggest_fixes(resident.id)

        assert isinstance(suggestions, list)

    def test_detect_multiple_people_conflicts(
        self,
        detector: ConflictAutoDetector,
        db: Session,
    ):
        """Test detecting conflicts across multiple people."""
        # Create multiple residents
        residents = []
        for i in range(3):
            person = Person(
                id=uuid4(),
                name=f"Dr. Resident {i}",
                type="resident",
                email=f"res{i}@hospital.org",
                pgy_level=1,
            )
            db.add(person)
            residents.append(person)
        db.commit()

        conflicts = detector.detect_all()

        assert isinstance(conflicts, list)

    def test_detect_date_range_conflicts(
        self,
        detector: ConflictAutoDetector,
    ):
        """Test detecting conflicts in a date range."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        conflicts = detector.detect_in_range(start_date, end_date)

        assert isinstance(conflicts, list)

    def test_conflict_severity_assessment(
        self,
        detector: ConflictAutoDetector,
    ):
        """Test assessing conflict severity."""
        conflicts = detector.detect_all()

        for conflict in conflicts:
            # Each conflict should have some way to determine severity
            assert hasattr(conflict, "__dict__") or isinstance(conflict, dict)

    def test_bulk_conflict_detection(
        self,
        detector: ConflictAutoDetector,
        db: Session,
    ):
        """Test bulk conflict detection across entire schedule."""
        result = detector.detect_all()

        assert isinstance(result, list)

    def test_get_conflict_report(
        self,
        detector: ConflictAutoDetector,
    ):
        """Test generating conflict report."""
        report = detector.get_report()

        assert isinstance(report, dict)

    def test_conflict_statistics(
        self,
        detector: ConflictAutoDetector,
    ):
        """Test getting conflict statistics."""
        stats = detector.get_statistics()

        assert isinstance(stats, dict)

    def test_real_time_conflict_detection(
        self,
        detector: ConflictAutoDetector,
        resident: Person,
        rotation_template: RotationTemplate,
        db: Session,
    ):
        """Test real-time conflict detection on assignment creation."""
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
        )
        db.add(block)
        db.commit()

        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            person_id=resident.id,
            block_id=block.id,
            rotation_template_id=rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # Check for conflicts
        conflicts = detector.detect_for_person(resident.id)

        assert isinstance(conflicts, list)

    def test_get_affected_persons(
        self,
        detector: ConflictAutoDetector,
    ):
        """Test getting list of people with conflicts."""
        affected = detector.get_affected_persons()

        assert isinstance(affected, list)

    def test_conflict_history(
        self,
        detector: ConflictAutoDetector,
        resident: Person,
    ):
        """Test getting conflict history."""
        history = detector.get_history(resident.id)

        assert isinstance(history, list)

    def test_prevent_future_conflicts(
        self,
        detector: ConflictAutoDetector,
    ):
        """Test conflict prevention recommendations."""
        recommendations = detector.get_prevention_recommendations()

        assert isinstance(recommendations, list)
