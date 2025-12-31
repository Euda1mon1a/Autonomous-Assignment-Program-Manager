"""Test suite for game theory service."""

import pytest
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.services.game_theory import GameTheoryService


class TestGameTheoryService:
    """Test suite for game theory service."""

    @pytest.fixture
    def gt_service(self, db: Session) -> GameTheoryService:
        """Create a game theory service instance."""
        return GameTheoryService(db)

    @pytest.fixture
    def faculty_1(self, db: Session) -> Person:
        """Create first faculty."""
        person = Person(
            id=uuid4(),
            name="Dr. Faculty 1",
            type="faculty",
            email="fac1@hospital.org",
            performs_procedures=True,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def faculty_2(self, db: Session) -> Person:
        """Create second faculty."""
        person = Person(
            id=uuid4(),
            name="Dr. Faculty 2",
            type="faculty",
            email="fac2@hospital.org",
            performs_procedures=True,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    def test_service_initialization(self, db: Session):
        """Test GameTheoryService initialization."""
        service = GameTheoryService(db)

        assert service.db is db

    def test_calculate_nash_equilibrium(
        self,
        gt_service: GameTheoryService,
    ):
        """Test calculating Nash equilibrium."""
        equilibrium = gt_service.calculate_nash_equilibrium()

        assert isinstance(equilibrium, (dict, list, type(None)))

    def test_analyze_cooperation_incentives(
        self,
        gt_service: GameTheoryService,
    ):
        """Test analyzing cooperation incentives."""
        incentives = gt_service.analyze_cooperation()

        assert isinstance(incentives, dict)

    def test_detect_prisoner_dilemma(
        self,
        gt_service: GameTheoryService,
    ):
        """Test detecting prisoner's dilemma scenarios."""
        dilemmas = gt_service.detect_dilemmas()

        assert isinstance(dilemmas, list)

    def test_calculate_payoff_matrix(
        self,
        gt_service: GameTheoryService,
    ):
        """Test calculating payoff matrix."""
        payoffs = gt_service.calculate_payoff_matrix()

        assert isinstance(payoffs, (dict, list))

    def test_analyze_coalition_formation(
        self,
        gt_service: GameTheoryService,
    ):
        """Test analyzing coalition formation."""
        coalitions = gt_service.analyze_coalitions()

        assert isinstance(coalitions, list)

    def test_calculate_shapley_value(
        self,
        gt_service: GameTheoryService,
        faculty_1: Person,
    ):
        """Test calculating Shapley value."""
        value = gt_service.calculate_shapley_value(faculty_1.id)

        assert isinstance(value, (float, int, type(None)))

    def test_calculate_core_allocation(
        self,
        gt_service: GameTheoryService,
    ):
        """Test calculating core allocation."""
        allocation = gt_service.calculate_core()

        assert isinstance(allocation, (dict, list))

    def test_analyze_fairness(
        self,
        gt_service: GameTheoryService,
    ):
        """Test analyzing fairness."""
        fairness = gt_service.analyze_fairness()

        assert isinstance(fairness, dict)

    def test_detect_blocking_coalitions(
        self,
        gt_service: GameTheoryService,
    ):
        """Test detecting blocking coalitions."""
        blocking = gt_service.detect_blocking_coalitions()

        assert isinstance(blocking, list)

    def test_calculate_bargaining_power(
        self,
        gt_service: GameTheoryService,
        faculty_1: Person,
    ):
        """Test calculating bargaining power."""
        power = gt_service.calculate_bargaining_power(faculty_1.id)

        assert isinstance(power, (float, int, type(None)))

    def test_analyze_strategic_interactions(
        self,
        gt_service: GameTheoryService,
    ):
        """Test analyzing strategic interactions."""
        interactions = gt_service.analyze_interactions()

        assert isinstance(interactions, dict)

    def test_detect_dominant_strategy(
        self,
        gt_service: GameTheoryService,
    ):
        """Test detecting dominant strategy."""
        strategy = gt_service.detect_dominant_strategy()

        assert isinstance(strategy, (dict, type(None)))

    def test_calculate_stability_index(
        self,
        gt_service: GameTheoryService,
    ):
        """Test calculating stability index."""
        stability = gt_service.calculate_stability()

        assert isinstance(stability, (float, int))

    def test_analyze_incentive_compatibility(
        self,
        gt_service: GameTheoryService,
    ):
        """Test analyzing incentive compatibility."""
        compatible = gt_service.analyze_ic()

        assert isinstance(compatible, bool)

    def test_calculate_social_welfare(
        self,
        gt_service: GameTheoryService,
    ):
        """Test calculating social welfare."""
        welfare = gt_service.calculate_social_welfare()

        assert isinstance(welfare, (float, int, type(None)))

    def test_detect_pareto_improvements(
        self,
        gt_service: GameTheoryService,
    ):
        """Test detecting Pareto improvements."""
        improvements = gt_service.detect_pareto_improvements()

        assert isinstance(improvements, list)

    def test_analyze_voting_power(
        self,
        gt_service: GameTheoryService,
    ):
        """Test analyzing voting power."""
        voting_power = gt_service.analyze_voting()

        assert isinstance(voting_power, dict)

    def test_model_information_asymmetry(
        self,
        gt_service: GameTheoryService,
    ):
        """Test modeling information asymmetry."""
        asymmetry = gt_service.model_asymmetry()

        assert isinstance(asymmetry, dict)

    def test_detect_adverse_selection(
        self,
        gt_service: GameTheoryService,
    ):
        """Test detecting adverse selection."""
        selection = gt_service.detect_adverse_selection()

        assert isinstance(selection, bool)
