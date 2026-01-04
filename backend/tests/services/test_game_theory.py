"""Test suite for game theory service.

Tests the GameTheoryService which implements Axelrod-style tournament
simulations for testing scheduling and resilience configurations.
"""

import pytest
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.services.game_theory import GameTheoryService, AXELROD_AVAILABLE


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

    # =========================================================================
    # Strategy Management Tests
    # =========================================================================

    def test_create_strategy(self, gt_service: GameTheoryService):
        """Test creating a configuration strategy."""
        strategy = gt_service.create_strategy(
            name="Test Strategy",
            strategy_type="tit_for_tat",
            description="A test strategy",
            created_by="test_user",
            utilization_target=0.80,
        )
        assert strategy is not None
        assert strategy.name == "Test Strategy"
        assert strategy.strategy_type == "tit_for_tat"

    def test_get_strategy(self, gt_service: GameTheoryService):
        """Test retrieving a strategy by ID."""
        # First create a strategy
        created = gt_service.create_strategy(
            name="Retrievable Strategy",
            strategy_type="cooperative",
        )
        # Then retrieve it
        retrieved = gt_service.get_strategy(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Retrievable Strategy"

    def test_get_nonexistent_strategy(self, gt_service: GameTheoryService):
        """Test retrieving a non-existent strategy returns None."""
        result = gt_service.get_strategy(uuid4())
        assert result is None

    def test_list_strategies(self, gt_service: GameTheoryService):
        """Test listing all active strategies."""
        # Create some strategies
        gt_service.create_strategy(name="Strategy A", strategy_type="cooperative")
        gt_service.create_strategy(name="Strategy B", strategy_type="aggressive")

        strategies = gt_service.list_strategies(active_only=True)
        assert isinstance(strategies, list)
        assert len(strategies) >= 2

    def test_update_strategy(self, gt_service: GameTheoryService):
        """Test updating a strategy."""
        strategy = gt_service.create_strategy(
            name="Original Name",
            strategy_type="tit_for_tat",
        )
        updated = gt_service.update_strategy(
            strategy.id, name="Updated Name", description="New description"
        )
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "New description"

    def test_create_default_strategies(self, gt_service: GameTheoryService):
        """Test creating default set of strategies."""
        created = gt_service.create_default_strategies()
        assert isinstance(created, list)
        # Should create some default strategies if they don't exist

    # =========================================================================
    # Tournament Management Tests
    # =========================================================================

    def test_create_tournament(self, gt_service: GameTheoryService):
        """Test creating a tournament."""
        # First create strategies to use
        strategy1 = gt_service.create_strategy(
            name="Tourney Strategy 1", strategy_type="cooperative"
        )
        strategy2 = gt_service.create_strategy(
            name="Tourney Strategy 2", strategy_type="aggressive"
        )

        tournament = gt_service.create_tournament(
            name="Test Tournament",
            strategy_ids=[str(strategy1.id), str(strategy2.id)],
            description="A test tournament",
            turns_per_match=100,
            repetitions=5,
        )
        assert tournament is not None
        assert tournament.name == "Test Tournament"
        assert len(tournament.strategy_ids) == 2

    def test_get_tournament(self, gt_service: GameTheoryService):
        """Test retrieving a tournament by ID."""
        strategy = gt_service.create_strategy(
            name="Minimal Strategy", strategy_type="cooperative"
        )
        created = gt_service.create_tournament(
            name="Retrievable Tournament", strategy_ids=[str(strategy.id)]
        )
        retrieved = gt_service.get_tournament(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_tournaments(self, gt_service: GameTheoryService):
        """Test listing recent tournaments."""
        strategy = gt_service.create_strategy(
            name="List Strategy", strategy_type="tit_for_tat"
        )
        gt_service.create_tournament(name="Tournament 1", strategy_ids=[str(strategy.id)])
        gt_service.create_tournament(name="Tournament 2", strategy_ids=[str(strategy.id)])

        tournaments = gt_service.list_tournaments(limit=10)
        assert isinstance(tournaments, list)
        assert len(tournaments) >= 2

    @pytest.mark.skipif(not AXELROD_AVAILABLE, reason="Axelrod library not installed")
    def test_run_tournament(self, gt_service: GameTheoryService):
        """Test running a tournament (requires axelrod)."""
        strategy1 = gt_service.create_strategy(
            name="Run Strategy 1", strategy_type="cooperative"
        )
        strategy2 = gt_service.create_strategy(
            name="Run Strategy 2", strategy_type="tit_for_tat"
        )

        tournament = gt_service.create_tournament(
            name="Runnable Tournament",
            strategy_ids=[str(strategy1.id), str(strategy2.id)],
            turns_per_match=50,
            repetitions=3,
        )

        result = gt_service.run_tournament(tournament.id)
        assert result is not None
        assert "tournament_id" in result
        assert result["status"] == "completed"

    # =========================================================================
    # Evolution Simulation Tests
    # =========================================================================

    def test_create_evolution(self, gt_service: GameTheoryService):
        """Test creating an evolutionary simulation."""
        strategy = gt_service.create_strategy(
            name="Evolve Strategy", strategy_type="tit_for_tat"
        )

        evolution = gt_service.create_evolution(
            name="Test Evolution",
            initial_composition={str(strategy.id): 10},
            description="A test evolution",
            turns_per_interaction=50,
            max_generations=100,
        )
        assert evolution is not None
        assert evolution.name == "Test Evolution"

    def test_get_evolution(self, gt_service: GameTheoryService):
        """Test retrieving an evolution simulation by ID."""
        strategy = gt_service.create_strategy(
            name="Get Evolution Strategy", strategy_type="cooperative"
        )
        created = gt_service.create_evolution(
            name="Retrievable Evolution",
            initial_composition={str(strategy.id): 5},
        )
        retrieved = gt_service.get_evolution(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_evolutions(self, gt_service: GameTheoryService):
        """Test listing recent evolution simulations."""
        strategy = gt_service.create_strategy(
            name="List Evolution Strategy", strategy_type="aggressive"
        )
        gt_service.create_evolution(
            name="Evolution 1", initial_composition={str(strategy.id): 5}
        )
        gt_service.create_evolution(
            name="Evolution 2", initial_composition={str(strategy.id): 5}
        )

        evolutions = gt_service.list_evolutions(limit=10)
        assert isinstance(evolutions, list)
        assert len(evolutions) >= 2

    # =========================================================================
    # Validation Tests
    # =========================================================================

    @pytest.mark.skipif(not AXELROD_AVAILABLE, reason="Axelrod library not installed")
    def test_validate_strategy(self, gt_service: GameTheoryService):
        """Test validating a strategy against TFT (requires axelrod)."""
        strategy = gt_service.create_strategy(
            name="Validate Strategy", strategy_type="tit_for_tat"
        )

        result = gt_service.validate_strategy(
            strategy.id, turns=50, repetitions=3, pass_threshold=2.0
        )
        assert result is not None
        assert hasattr(result, "passed")
        assert hasattr(result, "average_score")
        assert hasattr(result, "cooperation_rate")

    # =========================================================================
    # Analysis Tests
    # =========================================================================

    @pytest.mark.skipif(not AXELROD_AVAILABLE, reason="Axelrod library not installed")
    def test_analyze_current_config(self, gt_service: GameTheoryService):
        """Test analyzing current resilience configuration (requires axelrod)."""
        result = gt_service.analyze_current_config(
            utilization_target=0.80,
            cross_zone_borrowing=True,
            sacrifice_willingness="medium",
            defense_activation_threshold=3,
        )
        assert result is not None
        assert "config_name" in result
        assert "matchup_results" in result
        assert "average_score" in result
        assert "cooperation_rate" in result
        assert "recommendation" in result
        assert "strategy_classification" in result

    @pytest.mark.skipif(not AXELROD_AVAILABLE, reason="Axelrod library not installed")
    def test_analyze_config_aggressive(self, gt_service: GameTheoryService):
        """Test analyzing an aggressive configuration (requires axelrod)."""
        result = gt_service.analyze_current_config(
            utilization_target=0.95,  # Aggressive
            cross_zone_borrowing=False,
            sacrifice_willingness="low",
        )
        assert result is not None
        assert result["strategy_classification"] == "aggressive"

    @pytest.mark.skipif(not AXELROD_AVAILABLE, reason="Axelrod library not installed")
    def test_analyze_config_cooperative(self, gt_service: GameTheoryService):
        """Test analyzing a cooperative configuration (requires axelrod)."""
        result = gt_service.analyze_current_config(
            utilization_target=0.70,  # Conservative
            cross_zone_borrowing=True,
            sacrifice_willingness="high",
        )
        assert result is not None
        assert result["strategy_classification"] == "cooperative"


class TestGameTheoryServiceEdgeCases:
    """Edge case tests for GameTheoryService."""

    @pytest.fixture
    def gt_service(self, db: Session) -> GameTheoryService:
        """Create a game theory service instance."""
        return GameTheoryService(db)

    def test_update_nonexistent_strategy(self, gt_service: GameTheoryService):
        """Test updating a strategy that doesn't exist."""
        result = gt_service.update_strategy(uuid4(), name="New Name")
        assert result is None

    def test_get_nonexistent_tournament(self, gt_service: GameTheoryService):
        """Test getting a tournament that doesn't exist."""
        result = gt_service.get_tournament(uuid4())
        assert result is None

    def test_get_nonexistent_evolution(self, gt_service: GameTheoryService):
        """Test getting an evolution that doesn't exist."""
        result = gt_service.get_evolution(uuid4())
        assert result is None

    @pytest.mark.skipif(not AXELROD_AVAILABLE, reason="Axelrod library not installed")
    def test_run_tournament_not_found(self, gt_service: GameTheoryService):
        """Test running a tournament that doesn't exist (requires axelrod)."""
        with pytest.raises(ValueError, match="not found"):
            gt_service.run_tournament(uuid4())

    @pytest.mark.skipif(not AXELROD_AVAILABLE, reason="Axelrod library not installed")
    def test_validate_strategy_not_found(self, gt_service: GameTheoryService):
        """Test validating a strategy that doesn't exist (requires axelrod)."""
        with pytest.raises(ValueError, match="not found"):
            gt_service.validate_strategy(uuid4())

    def test_create_strategy_all_params(self, gt_service: GameTheoryService):
        """Test creating a strategy with all parameters."""
        strategy = gt_service.create_strategy(
            name="Full Params Strategy",
            strategy_type="forgiving_tft",
            description="Strategy with all parameters",
            created_by="test_user",
            utilization_target=0.75,
            cross_zone_borrowing=True,
            sacrifice_willingness="high",
            defense_activation_threshold=2,
            response_timeout_ms=3000,
            initial_action="cooperate",
            forgiveness_probability=0.1,
            retaliation_memory=2,
            is_stochastic=False,
        )
        assert strategy is not None
        assert strategy.forgiveness_probability == 0.1
        assert strategy.retaliation_memory == 2

    def test_create_tournament_custom_payoffs(self, gt_service: GameTheoryService):
        """Test creating a tournament with custom payoffs."""
        strategy = gt_service.create_strategy(
            name="Payoff Strategy", strategy_type="cooperative"
        )

        tournament = gt_service.create_tournament(
            name="Custom Payoff Tournament",
            strategy_ids=[str(strategy.id)],
            payoff_cc=5.0,  # Custom payoff values
            payoff_cd=1.0,
            payoff_dc=7.0,
            payoff_dd=2.0,
            noise=0.05,
        )
        assert tournament is not None
        assert tournament.payoff_cc == 5.0
        assert tournament.noise == 0.05

    def test_create_evolution_with_mutation(self, gt_service: GameTheoryService):
        """Test creating an evolution with mutation rate."""
        strategy = gt_service.create_strategy(
            name="Mutation Strategy", strategy_type="tit_for_tat"
        )

        evolution = gt_service.create_evolution(
            name="Mutating Evolution",
            initial_composition={str(strategy.id): 10},
            mutation_rate=0.05,
            max_generations=500,
        )
        assert evolution is not None
        assert evolution.mutation_rate == 0.05
        assert evolution.max_generations == 500

    def test_list_strategies_inactive(self, gt_service: GameTheoryService):
        """Test listing strategies including inactive ones."""
        # Create strategy and mark inactive
        strategy = gt_service.create_strategy(
            name="Inactive Strategy", strategy_type="random"
        )
        gt_service.update_strategy(strategy.id, is_active=False)

        # Should not include inactive when active_only=True
        active_strategies = gt_service.list_strategies(active_only=True)
        inactive_ids = [s.id for s in active_strategies if not s.is_active]
        assert strategy.id not in inactive_ids or not active_strategies


class TestGameTheoryWithoutAxelrod:
    """Tests that work even without axelrod library."""

    @pytest.fixture
    def gt_service(self, db: Session) -> GameTheoryService:
        """Create a game theory service instance."""
        return GameTheoryService(db)

    def test_service_works_without_axelrod(self, db: Session):
        """Test that service initializes even without axelrod."""
        service = GameTheoryService(db)
        assert service.db is db

    def test_strategy_crud_without_axelrod(self, gt_service: GameTheoryService):
        """Test strategy CRUD operations don't require axelrod."""
        # Create
        strategy = gt_service.create_strategy(
            name="No Axelrod Strategy", strategy_type="tit_for_tat"
        )
        assert strategy is not None

        # Read
        retrieved = gt_service.get_strategy(strategy.id)
        assert retrieved is not None

        # Update
        updated = gt_service.update_strategy(strategy.id, description="Updated")
        assert updated.description == "Updated"

        # List
        strategies = gt_service.list_strategies()
        assert len(strategies) >= 1

    def test_tournament_creation_without_axelrod(self, gt_service: GameTheoryService):
        """Test tournament creation doesn't require axelrod."""
        strategy = gt_service.create_strategy(
            name="Tournament Creation Strategy", strategy_type="cooperative"
        )
        tournament = gt_service.create_tournament(
            name="Created Tournament", strategy_ids=[str(strategy.id)]
        )
        assert tournament is not None

    def test_evolution_creation_without_axelrod(self, gt_service: GameTheoryService):
        """Test evolution creation doesn't require axelrod."""
        strategy = gt_service.create_strategy(
            name="Evolution Creation Strategy", strategy_type="aggressive"
        )
        evolution = gt_service.create_evolution(
            name="Created Evolution", initial_composition={str(strategy.id): 5}
        )
        assert evolution is not None
