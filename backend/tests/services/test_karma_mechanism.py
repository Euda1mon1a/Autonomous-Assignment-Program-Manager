"""Test suite for karma mechanism service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.services.karma_mechanism import KarmaMechanismService


class TestKarmaMechanismService:
    """Test suite for karma mechanism service."""

    @pytest.fixture
    def karma_service(self, db: Session) -> KarmaMechanismService:
        """Create a karma mechanism service instance."""
        return KarmaMechanismService(db)

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
    def faculty(self, db: Session) -> Person:
        """Create a faculty member."""
        person = Person(
            id=uuid4(),
            name="Dr. Faculty",
            type="faculty",
            email="faculty@hospital.org",
            performs_procedures=True,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    def test_service_initialization(self, db: Session):
        """Test KarmaMechanismService initialization."""
        service = KarmaMechanismService(db)

        assert service.db is db

    def test_get_karma_score(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test getting karma score for person."""
        score = karma_service.get_score(resident.id)

        assert isinstance(score, (float, int, type(None)))

    def test_record_positive_action(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test recording positive action."""
        result = karma_service.record_positive(
            person_id=resident.id,
            action="helped_colleague",
            value=10,
        )

        assert isinstance(result, bool)

    def test_record_negative_action(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test recording negative action."""
        result = karma_service.record_negative(
            person_id=resident.id,
            action="no_show",
            value=-5,
        )

        assert isinstance(result, bool)

    def test_calculate_total_karma(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test calculating total karma."""
        total = karma_service.calculate_total(resident.id)

        assert isinstance(total, (float, int, type(None)))

    def test_get_karma_history(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test getting karma history."""
        history = karma_service.get_history(resident.id)

        assert isinstance(history, list)

    def test_decay_old_karma(
        self,
        karma_service: KarmaMechanismService,
    ):
        """Test decaying old karma scores."""
        result = karma_service.decay_old()

        assert isinstance(result, bool)

    def test_apply_karma_to_scheduling(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test applying karma to scheduling."""
        boost = karma_service.get_scheduling_boost(resident.id)

        assert isinstance(boost, (float, int))

    def test_reward_cooperation(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
        faculty: Person,
    ):
        """Test rewarding cooperation between people."""
        result = karma_service.reward_cooperation(resident.id, faculty.id)

        assert isinstance(result, bool)

    def test_penalize_violation(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test penalizing rule violations."""
        result = karma_service.penalize_violation(
            person_id=resident.id,
            violation="worked_too_many_hours",
        )

        assert isinstance(result, bool)

    def test_get_karma_breakdown(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test getting breakdown of karma."""
        breakdown = karma_service.get_breakdown(resident.id)

        assert isinstance(breakdown, dict)

    def test_compare_karma_scores(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
        faculty: Person,
    ):
        """Test comparing karma scores."""
        comparison = karma_service.compare(resident.id, faculty.id)

        assert isinstance(comparison, dict)

    def test_rank_by_karma(
        self,
        karma_service: KarmaMechanismService,
    ):
        """Test ranking people by karma."""
        ranking = karma_service.get_ranking()

        assert isinstance(ranking, list)

    def test_get_top_contributors(
        self,
        karma_service: KarmaMechanismService,
    ):
        """Test getting top contributors by karma."""
        top = karma_service.get_top_contributors(limit=10)

        assert isinstance(top, list)

    def test_identify_problem_actors(
        self,
        karma_service: KarmaMechanismService,
    ):
        """Test identifying problem actors."""
        problem_actors = karma_service.get_problem_actors()

        assert isinstance(problem_actors, list)

    def test_suggest_improvements(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test suggesting improvements based on karma."""
        suggestions = karma_service.suggest_improvements(resident.id)

        assert isinstance(suggestions, list)

    def test_reset_karma(
        self,
        karma_service: KarmaMechanismService,
        resident: Person,
    ):
        """Test resetting karma score."""
        result = karma_service.reset(resident.id)

        assert isinstance(result, bool)

    def test_export_karma_data(
        self,
        karma_service: KarmaMechanismService,
    ):
        """Test exporting karma data."""
        data = karma_service.export()

        assert isinstance(data, (dict, str))

    def test_apply_scaling_factor(
        self,
        karma_service: KarmaMechanismService,
    ):
        """Test applying scaling factor to karma."""
        result = karma_service.set_scale(scale_factor=1.5)

        assert isinstance(result, bool)

    def test_get_karma_statistics(
        self,
        karma_service: KarmaMechanismService,
    ):
        """Test getting karma statistics."""
        stats = karma_service.get_statistics()

        assert isinstance(stats, dict)

    def test_detect_gaming_the_system(
        self,
        karma_service: KarmaMechanismService,
    ):
        """Test detecting if people are gaming the system."""
        gaming = karma_service.detect_gaming()

        assert isinstance(gaming, list)
