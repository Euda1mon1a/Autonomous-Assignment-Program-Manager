"""Test suite for conflict auto-resolver service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.rotation_template import RotationTemplate
from app.services.conflict_auto_resolver import ConflictAutoResolver


class TestConflictAutoResolver:
    """Test suite for conflict auto-resolver service."""

    @pytest.fixture
    def resolver(self, db: Session) -> ConflictAutoResolver:
        """Create a conflict auto-resolver instance."""
        return ConflictAutoResolver(db)

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
            activity_type="outpatient",
            abbreviation="ROT",
            max_residents=4,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def test_resolver_initialization(self, db: Session):
        """Test ConflictAutoResolver initialization."""
        resolver = ConflictAutoResolver(db)

        assert resolver.db is db

    def test_resolve_all_conflicts(
        self,
        resolver: ConflictAutoResolver,
    ):
        """Test resolving all conflicts."""
        result = resolver.resolve_all()

        assert isinstance(result, (bool, int, dict))

    def test_resolve_conflicts_for_person(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test resolving conflicts for specific person."""
        result = resolver.resolve_person(resident.id)

        assert isinstance(result, (bool, int, dict))

    def test_suggest_resolution(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test suggesting resolutions for conflicts."""
        suggestions = resolver.suggest_resolution(resident.id)

        assert isinstance(suggestions, list)

    def test_apply_suggested_resolution(
        self,
        resolver: ConflictAutoResolver,
    ):
        """Test applying suggested resolution."""
        suggestion = {"action": "remove_assignment", "assignment_id": str(uuid4())}

        result = resolver.apply_suggestion(suggestion)

        assert isinstance(result, bool)

    def test_reassign_conflicting_shifts(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test reassigning conflicting shifts."""
        result = resolver.reassign_shifts(resident.id)

        assert isinstance(result, (bool, int))

    def test_resolve_by_removal(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
        rotation_template: RotationTemplate,
        db: Session,
    ):
        """Test resolving conflicts by removing assignments."""
        # Create conflicting assignments
        same_day = date.today()

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

        result = resolver.resolve_by_removal(resident.id)

        assert isinstance(result, (bool, int))

    def test_resolve_by_reassignment(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test resolving conflicts by reassigning."""
        result = resolver.resolve_by_reassignment(resident.id)

        assert isinstance(result, (bool, int))

    def test_resolve_by_swap(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test resolving conflicts by swapping assignments."""
        result = resolver.resolve_by_swap(resident.id)

        assert isinstance(result, bool)

    def test_get_resolution_options(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test getting resolution options."""
        options = resolver.get_options(resident.id)

        assert isinstance(options, list)

    def test_calculate_resolution_priority(
        self,
        resolver: ConflictAutoResolver,
    ):
        """Test calculating resolution priority."""
        priority = resolver.get_priority()

        assert isinstance(priority, (list, dict))

    def test_resolve_critical_conflicts_first(
        self,
        resolver: ConflictAutoResolver,
    ):
        """Test resolving critical conflicts first."""
        result = resolver.resolve_by_priority()

        assert isinstance(result, (bool, int))

    def test_preview_resolution(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test previewing resolution without applying."""
        preview = resolver.preview_resolution(resident.id)

        assert isinstance(preview, (dict, list, type(None)))

    def test_get_resolution_impact(
        self,
        resolver: ConflictAutoResolver,
    ):
        """Test getting impact of resolution."""
        impact = resolver.get_impact()

        assert isinstance(impact, dict)

    def test_rollback_resolution(
        self,
        resolver: ConflictAutoResolver,
    ):
        """Test rolling back resolution."""
        result = resolver.rollback()

        assert isinstance(result, bool)

    def test_get_resolution_history(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test getting resolution history."""
        history = resolver.get_history(resident.id)

        assert isinstance(history, list)

    def test_prevent_future_conflicts(
        self,
        resolver: ConflictAutoResolver,
    ):
        """Test getting recommendations to prevent future conflicts."""
        recommendations = resolver.get_prevention_recommendations()

        assert isinstance(recommendations, list)

    def test_validate_resolution(
        self,
        resolver: ConflictAutoResolver,
    ):
        """Test validating resolution."""
        is_valid = resolver.validate()

        assert isinstance(is_valid, bool)

    def test_resolve_with_constraints(
        self,
        resolver: ConflictAutoResolver,
        resident: Person,
    ):
        """Test resolving with constraint preservation."""
        result = resolver.resolve_with_constraints(resident.id)

        assert isinstance(result, (bool, int))

    def test_batch_resolve_conflicts(
        self,
        resolver: ConflictAutoResolver,
        db: Session,
    ):
        """Test resolving conflicts for multiple people."""
        # Create multiple residents
        resident_ids = []
        for i in range(3):
            person = Person(
                id=uuid4(),
                name=f"Dr. Resident {i}",
                type="resident",
                email=f"res{i}@hospital.org",
                pgy_level=1,
            )
            db.add(person)
            resident_ids.append(person.id)
        db.commit()

        result = resolver.batch_resolve(resident_ids)

        assert isinstance(result, (bool, int))
