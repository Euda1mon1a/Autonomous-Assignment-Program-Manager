"""Game Theory Service for Axelrod-style tournament simulations.

Implements Robert Axelrod's Prisoner's Dilemma framework for
empirically testing scheduling and resilience configurations.

Key features:
- Round-robin tournaments between configuration strategies
- Moran process evolutionary simulations
- TFT validation for production-readiness
- Integration with resilience framework
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

# Optional dependency - game theory features require axelrod
try:
    import axelrod as axl
    AXELROD_AVAILABLE = True
except ImportError:
    AXELROD_AVAILABLE = False
    if not TYPE_CHECKING:
        # Create dummy module for runtime
        class DummyAxelrod:
            Player = Any
            Action = Any
            Game = Any
            Tournament = Any
            MoranProcess = Any
            TitForTat = Any
            Cooperator = Any
            Defector = Any
            Random = Any
            Grudger = Any
            Match = Any
        axl = DummyAxelrod()  # type: ignore

from app.models.game_theory import (
    ConfigStrategy,
    EvolutionSimulation,
    GameTheoryTournament,
    SimulationStatus,
    StrategyType,
    TournamentMatch,
    ValidationResult,
)

logger = logging.getLogger(__name__)


# Only define ResilienceConfigPlayer if axelrod is available
if AXELROD_AVAILABLE:
    class ResilienceConfigPlayer(axl.Player):  # type: ignore
        """
        Custom Axelrod player that maps resilience configuration to PD strategy.

        Translates scheduling/resilience behavior to cooperation/defection:
        - Cooperate: Follow protocol, share resources, respond quickly
        - Defect: Hoard resources, ignore constraints, slow response
        """

        name = "Resilience Config"
        classifier = {
            "memory_depth": 1,
            "stochastic": False,
            "long_run_time": False,
            "inspects_source": False,
            "manipulates_source": False,
            "manipulates_state": False,
        }

        def __init__(
            self,
            strategy_type: str = "tit_for_tat",
            utilization_target: float = 0.80,
            initial_action: str = "cooperate",
            forgiveness_probability: float = 0.0,
            retaliation_memory: int = 1,
            **kwargs,
        ):
            super().__init__()
            self.strategy_type = strategy_type
            self.utilization_target = utilization_target
            self.initial_action = initial_action
            self.forgiveness_probability = forgiveness_probability
            self.retaliation_memory = retaliation_memory
            self._betrayed = False

        def strategy(self, opponent: axl.Player) -> axl.Action:
            """Decide to cooperate or defect based on configuration behavior."""
            import random

            # First move
            if len(self.history) == 0:
                if self.initial_action == "defect":
                    return axl.Action.D
                return axl.Action.C

            # Strategy-specific behavior
            if self.strategy_type == "cooperative":
                return axl.Action.C

            elif self.strategy_type == "aggressive":
                return axl.Action.D

            elif self.strategy_type == "tit_for_tat":
                # Mirror opponent's last move
                if (
                    self.forgiveness_probability > 0
                    and opponent.history[-1] == axl.Action.D
                ):
                    if random.random() < self.forgiveness_probability:
                        return axl.Action.C
                return opponent.history[-1]

            elif self.strategy_type == "grudger":
                if axl.Action.D in opponent.history:
                    self._betrayed = True
                return axl.Action.D if self._betrayed else axl.Action.C

            elif self.strategy_type == "pavlov":
                # Win-stay, lose-shift
                if len(self.history) == 0:
                    return axl.Action.C
                last_payoff = self._calculate_last_payoff(opponent)
                if last_payoff >= 3:  # Good outcome (CC or DC)
                    return self.history[-1]
                else:
                    return (
                        axl.Action.C if self.history[-1] == axl.Action.D else axl.Action.D
                    )

            elif self.strategy_type == "random":
                return axl.Action.C if random.random() > 0.5 else axl.Action.D

            elif self.strategy_type == "suspicious_tft":
                # Defect first, then TFT
                if len(self.history) == 0:
                    return axl.Action.D
                return opponent.history[-1]

            elif self.strategy_type == "forgiving_tft":
                # TFT but only retaliate if opponent defected multiple times
                recent = opponent.history[-self.retaliation_memory :]
                defection_count = recent.count(axl.Action.D)
                if defection_count >= self.retaliation_memory:
                    return axl.Action.D
                return axl.Action.C

            # Default: TFT
            return opponent.history[-1] if len(opponent.history) > 0 else axl.Action.C

        def _calculate_last_payoff(self, opponent: axl.Player) -> float:
            """Calculate payoff from last round."""
            if len(self.history) == 0:
                return 0
            my_last = self.history[-1]
            their_last = opponent.history[-1]
            if my_last == axl.Action.C and their_last == axl.Action.C:
                return 3
            elif my_last == axl.Action.D and their_last == axl.Action.C:
                return 5
            elif my_last == axl.Action.C and their_last == axl.Action.D:
                return 0
            else:
                return 1
else:
    # Create a stub class when axelrod is not available
    ResilienceConfigPlayer = None  # type: ignore


class GameTheoryService:
    """Service for running game theory simulations."""

    def __init__(self, db: Session):
        if not AXELROD_AVAILABLE:
            logger.warning(
                "Axelrod library not available. Game theory features disabled. "
                "Install with: pip install axelrod"
            )
        self.db = db

    # =========================================================================
    # Strategy Management
    # =========================================================================

    def create_strategy(
        self,
        name: str,
        strategy_type: str,
        description: str | None = None,
        created_by: str | None = None,
        **config_params,
    ) -> ConfigStrategy:
        """Create a new configuration strategy."""
        strategy = ConfigStrategy(
            name=name,
            description=description,
            strategy_type=strategy_type,
            created_by=created_by,
            utilization_target=config_params.get("utilization_target", 0.80),
            cross_zone_borrowing=config_params.get("cross_zone_borrowing", True),
            sacrifice_willingness=config_params.get("sacrifice_willingness", "medium"),
            defense_activation_threshold=config_params.get(
                "defense_activation_threshold", 3
            ),
            response_timeout_ms=config_params.get("response_timeout_ms", 5000),
            initial_action=config_params.get("initial_action", "cooperate"),
            forgiveness_probability=config_params.get("forgiveness_probability", 0.0),
            retaliation_memory=config_params.get("retaliation_memory", 1),
            is_stochastic=config_params.get("is_stochastic", False),
            custom_logic=config_params.get("custom_logic"),
        )
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def get_strategy(self, strategy_id: UUID) -> ConfigStrategy | None:
        """Get a strategy by ID."""
        return (
            self.db.query(ConfigStrategy)
            .filter(ConfigStrategy.id == strategy_id)
            .first()
        )

    def list_strategies(self, active_only: bool = True) -> list[ConfigStrategy]:
        """List all strategies."""
        query = self.db.query(ConfigStrategy)
        if active_only:
            query = query.filter(ConfigStrategy.is_active == True)
        return query.order_by(ConfigStrategy.created_at.desc()).all()

    def update_strategy(self, strategy_id: UUID, **updates) -> ConfigStrategy | None:
        """Update a strategy."""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return None
        for key, value in updates.items():
            if hasattr(strategy, key) and value is not None:
                setattr(strategy, key, value)
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def _strategy_to_player(self, strategy: ConfigStrategy) -> axl.Player:
        """Convert a ConfigStrategy to an Axelrod player."""
        player = ResilienceConfigPlayer(
            strategy_type=strategy.strategy_type,
            utilization_target=strategy.utilization_target,
            initial_action=strategy.initial_action,
            forgiveness_probability=strategy.forgiveness_probability,
            retaliation_memory=strategy.retaliation_memory,
        )
        player.name = strategy.name
        return player

    def create_default_strategies(self) -> list[ConfigStrategy]:
        """Create default set of strategies for testing."""
        defaults = [
            {
                "name": "Conservative (80% Utilization)",
                "strategy_type": StrategyType.TIT_FOR_TAT.value,
                "description": "Standard TFT strategy with 80% utilization target. Follows the resilience framework defaults.",
                "utilization_target": 0.80,
                "cross_zone_borrowing": True,
                "sacrifice_willingness": "medium",
            },
            {
                "name": "Aggressive (95% Utilization)",
                "strategy_type": StrategyType.AGGRESSIVE.value,
                "description": "Always defects - pushes utilization to 95%, hoards resources.",
                "utilization_target": 0.95,
                "cross_zone_borrowing": False,
                "sacrifice_willingness": "low",
            },
            {
                "name": "Ultra-Conservative (70% Utilization)",
                "strategy_type": StrategyType.COOPERATIVE.value,
                "description": "Always cooperates - leaves 30% buffer, shares everything.",
                "utilization_target": 0.70,
                "cross_zone_borrowing": True,
                "sacrifice_willingness": "high",
            },
            {
                "name": "Grudger (One Strike)",
                "strategy_type": StrategyType.GRUDGER.value,
                "description": "Cooperates until betrayed, then always defects. Zero tolerance.",
                "utilization_target": 0.80,
                "initial_action": "cooperate",
            },
            {
                "name": "Forgiving TFT",
                "strategy_type": StrategyType.FORGIVING_TFT.value,
                "description": "Like TFT but forgives occasional defection. More resilient to noise.",
                "utilization_target": 0.80,
                "forgiveness_probability": 0.1,
                "retaliation_memory": 2,
            },
            {
                "name": "Chaos Monkey",
                "strategy_type": StrategyType.RANDOM.value,
                "description": "Random behavior - baseline for testing robustness.",
                "is_stochastic": True,
            },
        ]

        created = []
        for config in defaults:
            existing = (
                self.db.query(ConfigStrategy)
                .filter(ConfigStrategy.name == config["name"])
                .first()
            )
            if not existing:
                strategy = self.create_strategy(**config, created_by="system")
                created.append(strategy)

        return created

    # =========================================================================
    # Tournament Management
    # =========================================================================

    def create_tournament(
        self,
        name: str,
        strategy_ids: list[UUID],
        description: str | None = None,
        created_by: str | None = None,
        turns_per_match: int = 200,
        repetitions: int = 10,
        noise: float = 0.0,
        payoff_cc: float = 3.0,
        payoff_cd: float = 0.0,
        payoff_dc: float = 5.0,
        payoff_dd: float = 1.0,
    ) -> GameTheoryTournament:
        """Create a new tournament."""
        tournament = GameTheoryTournament(
            name=name,
            description=description,
            created_by=created_by,
            strategy_ids=[str(sid) for sid in strategy_ids],
            turns_per_match=turns_per_match,
            repetitions=repetitions,
            noise=noise,
            payoff_cc=payoff_cc,
            payoff_cd=payoff_cd,
            payoff_dc=payoff_dc,
            payoff_dd=payoff_dd,
            status=SimulationStatus.PENDING.value,
        )
        self.db.add(tournament)
        self.db.commit()
        self.db.refresh(tournament)
        return tournament

    def get_tournament(self, tournament_id: UUID) -> GameTheoryTournament | None:
        """Get a tournament by ID."""
        return (
            self.db.query(GameTheoryTournament)
            .filter(GameTheoryTournament.id == tournament_id)
            .first()
        )

    def list_tournaments(self, limit: int = 50) -> list[GameTheoryTournament]:
        """List recent tournaments."""
        return (
            self.db.query(GameTheoryTournament)
            .order_by(GameTheoryTournament.created_at.desc())
            .limit(limit)
            .all()
        )

    def run_tournament(self, tournament_id: UUID) -> dict:
        """
        Run a tournament synchronously.

        For async execution, use the Celery task instead.
        """
        tournament = self.get_tournament(tournament_id)
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")

        if tournament.status != SimulationStatus.PENDING.value:
            raise ValueError(f"Tournament already {tournament.status}")

        # Update status
        tournament.status = SimulationStatus.RUNNING.value
        tournament.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # Load strategies
            strategies = []
            for sid in tournament.strategy_ids:
                strategy = self.get_strategy(UUID(sid))
                if strategy:
                    strategies.append(strategy)

            if len(strategies) < 2:
                raise ValueError("Need at least 2 strategies for tournament")

            # Convert to Axelrod players
            players = [self._strategy_to_player(s) for s in strategies]

            # Create custom game with specified payoffs
            game = axl.Game(
                r=tournament.payoff_cc,  # Reward for mutual cooperation
                s=tournament.payoff_cd,  # Sucker's payoff
                t=tournament.payoff_dc,  # Temptation to defect
                p=tournament.payoff_dd,  # Punishment for mutual defection
            )

            # Run tournament
            axl_tournament = axl.Tournament(
                players,
                game=game,
                turns=tournament.turns_per_match,
                repetitions=tournament.repetitions,
                noise=tournament.noise,
            )

            results = axl_tournament.play()

            # Process results
            rankings = []
            for rank, player_index in enumerate(results.ranking):
                name = results.ranked_names[rank]
                strategy = (
                    strategies[player_index]
                    if player_index < len(strategies)
                    else next((s for s in strategies if s.name == name), None)
                )
                scores = results.scores[player_index]
                avg_score = sum(scores) / len(scores) if scores else 0

                rankings.append(
                    {
                        "rank": rank + 1,
                        "strategy_id": str(strategy.id) if strategy else None,
                        "strategy_name": name,
                        "total_score": sum(scores),
                        "average_score": avg_score,
                    }
                )

                # Update strategy stats
                if strategy:
                    strategy.tournaments_participated += 1
                    strategy.average_score = avg_score
                    if rank == 0:
                        strategy.total_wins += 1

            # Build payoff matrix
            payoff_matrix = {}
            for i, p1 in enumerate(players):
                payoff_matrix[p1.name] = {}
                for j, p2 in enumerate(players):
                    if i < len(results.payoff_matrix) and j < len(
                        results.payoff_matrix[i]
                    ):
                        payoff_matrix[p1.name][p2.name] = results.payoff_matrix[i][j]

            # Store matches
            for interaction in results.interactions:
                # Simplified - store summary matches
                pass

            # Update tournament
            tournament.status = SimulationStatus.COMPLETED.value
            tournament.completed_at = datetime.utcnow()
            tournament.total_matches = (
                len(results.interactions)
                if hasattr(results, "interactions")
                else len(players) * (len(players) - 1) // 2
            )
            tournament.winner_strategy_name = (
                rankings[0]["strategy_name"] if rankings else None
            )
            tournament.winner_strategy_id = (
                UUID(rankings[0]["strategy_id"])
                if rankings and rankings[0]["strategy_id"]
                else None
            )
            tournament.rankings = rankings
            tournament.payoff_matrix = payoff_matrix

            self.db.commit()

            return {
                "tournament_id": str(tournament.id),
                "status": "completed",
                "winner": tournament.winner_strategy_name,
                "rankings": rankings,
            }

        except Exception as e:
            logger.exception(f"Tournament {tournament_id} failed")
            tournament.status = SimulationStatus.FAILED.value
            tournament.error_message = str(e)
            self.db.commit()
            raise

    # =========================================================================
    # Evolution Simulation
    # =========================================================================

    def create_evolution(
        self,
        name: str,
        initial_composition: dict[str, int],
        description: str | None = None,
        created_by: str | None = None,
        turns_per_interaction: int = 100,
        max_generations: int = 1000,
        mutation_rate: float = 0.01,
    ) -> EvolutionSimulation:
        """Create a new evolutionary simulation."""
        total_pop = sum(initial_composition.values())

        evolution = EvolutionSimulation(
            name=name,
            description=description,
            created_by=created_by,
            initial_population_size=total_pop,
            initial_composition=initial_composition,
            turns_per_interaction=turns_per_interaction,
            max_generations=max_generations,
            mutation_rate=mutation_rate,
            status=SimulationStatus.PENDING.value,
        )
        self.db.add(evolution)
        self.db.commit()
        self.db.refresh(evolution)
        return evolution

    def get_evolution(self, evolution_id: UUID) -> EvolutionSimulation | None:
        """Get an evolution simulation by ID."""
        return (
            self.db.query(EvolutionSimulation)
            .filter(EvolutionSimulation.id == evolution_id)
            .first()
        )

    def list_evolutions(self, limit: int = 50) -> list[EvolutionSimulation]:
        """List recent evolution simulations."""
        return (
            self.db.query(EvolutionSimulation)
            .order_by(EvolutionSimulation.created_at.desc())
            .limit(limit)
            .all()
        )

    def run_evolution(self, evolution_id: UUID) -> dict:
        """
        Run an evolutionary simulation synchronously.

        Uses Moran process to evolve population over generations.
        """
        evolution = self.get_evolution(evolution_id)
        if not evolution:
            raise ValueError(f"Evolution {evolution_id} not found")

        if evolution.status != SimulationStatus.PENDING.value:
            raise ValueError(f"Evolution already {evolution.status}")

        # Update status
        evolution.status = SimulationStatus.RUNNING.value
        evolution.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # Build initial population
            players = []
            for sid_str, count in evolution.initial_composition.items():
                strategy = self.get_strategy(UUID(sid_str))
                if strategy:
                    for _ in range(count):
                        players.append(self._strategy_to_player(strategy))

            if len(players) < 2:
                raise ValueError("Need at least 2 players for evolution")

            # Run Moran process
            mp = axl.MoranProcess(
                players,
                turns=evolution.turns_per_interaction,
                noise=evolution.mutation_rate,
            )

            # Track population history
            population_history = []
            sample_interval = max(1, evolution.max_generations // 100)

            try:
                generations = 0
                for gen, pop in enumerate(mp):
                    generations = gen
                    if gen % sample_interval == 0:
                        # Count strategies
                        counts = {}
                        for player in pop:
                            name = player.name
                            counts[name] = counts.get(name, 0) + 1
                        population_history.append(
                            {"generation": gen, "populations": counts}
                        )

                    if gen >= evolution.max_generations:
                        break

                    # Check if fixation occurred
                    if mp.fixated:
                        break

            except StopIteration:
                pass

            # Get final state
            final_counts = {}
            for player in mp.population:
                name = player.name
                final_counts[name] = final_counts.get(name, 0) + 1

            # Determine winner
            winner_name = (
                mp.winning_strategy_name
                if hasattr(mp, "winning_strategy_name")
                else None
            )
            if not winner_name and final_counts:
                winner_name = max(final_counts.keys(), key=lambda k: final_counts[k])

            # Update evolution record
            evolution.status = SimulationStatus.COMPLETED.value
            evolution.completed_at = datetime.utcnow()
            evolution.generations_completed = generations
            evolution.winner_strategy_name = winner_name
            evolution.is_evolutionarily_stable = (
                mp.fixated if hasattr(mp, "fixated") else False
            )
            evolution.population_history = population_history
            evolution.final_population = final_counts

            # Find winner strategy ID
            if winner_name:
                winner = (
                    self.db.query(ConfigStrategy)
                    .filter(ConfigStrategy.name == winner_name)
                    .first()
                )
                if winner:
                    evolution.winner_strategy_id = winner.id

            self.db.commit()

            return {
                "evolution_id": str(evolution.id),
                "status": "completed",
                "generations": generations,
                "winner": winner_name,
                "is_stable": evolution.is_evolutionarily_stable,
                "final_population": final_counts,
            }

        except Exception as e:
            logger.exception(f"Evolution {evolution_id} failed")
            evolution.status = SimulationStatus.FAILED.value
            evolution.error_message = str(e)
            self.db.commit()
            raise

    # =========================================================================
    # Validation
    # =========================================================================

    def validate_strategy(
        self,
        strategy_id: UUID,
        turns: int = 100,
        repetitions: int = 10,
        pass_threshold: float = 2.5,
    ) -> ValidationResult:
        """
        Validate a strategy against Tit for Tat.

        A strategy that cannot coexist with TFT is too aggressive
        for a production environment.
        """
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")

        # Create players
        config_player = self._strategy_to_player(strategy)
        tft_player = axl.TitForTat()

        # Run matches
        total_score = 0
        total_cooperations = 0
        total_moves = 0

        for _ in range(repetitions):
            match = axl.Match([config_player, tft_player], turns=turns)
            match.play()

            total_score += match.final_score()[0]
            total_cooperations += match.cooperation()[0]
            total_moves += turns

            # Reset players for next match
            config_player.reset()
            tft_player.reset()

        avg_score = total_score / repetitions
        coop_rate = total_cooperations / total_moves

        # Determine assessment
        passed = avg_score >= pass_threshold
        if passed and coop_rate >= 0.6:
            assessment = "cooperative"
            recommendation = (
                "Strategy is cooperative and performs well. Suitable for production."
            )
        elif passed and coop_rate < 0.4:
            assessment = "exploitative"
            recommendation = "Strategy passes but is not cooperative. May cause issues in shared environment."
        elif not passed and coop_rate < 0.3:
            assessment = "too_aggressive"
            recommendation = (
                "Strategy is too aggressive. Will trigger retaliation and underperform."
            )
        else:
            assessment = "exploitable"
            recommendation = "Strategy underperforms. Consider more adaptive approach."

        # Create record
        validation = ValidationResult(
            strategy_id=strategy_id,
            strategy_name=strategy.name,
            turns=turns,
            repetitions=repetitions,
            passed=passed,
            average_score=avg_score,
            cooperation_rate=coop_rate,
            pass_threshold=pass_threshold,
            assessment=assessment,
            recommendation=recommendation,
        )
        self.db.add(validation)
        self.db.commit()
        self.db.refresh(validation)

        return validation

    # =========================================================================
    # Analysis
    # =========================================================================

    def analyze_current_config(
        self,
        utilization_target: float = 0.80,
        cross_zone_borrowing: bool = True,
        sacrifice_willingness: str = "medium",
        defense_activation_threshold: int = 3,
    ) -> dict:
        """
        Analyze current resilience configuration using game theory.

        Tests the config against standard opponent strategies.
        """
        # Determine strategy type based on config
        if utilization_target >= 0.90:
            strategy_type = "aggressive"
        elif utilization_target <= 0.70:
            strategy_type = "cooperative"
        elif sacrifice_willingness == "high":
            strategy_type = "forgiving_tft"
        else:
            strategy_type = "tit_for_tat"

        # Create player
        config_player = ResilienceConfigPlayer(
            strategy_type=strategy_type,
            utilization_target=utilization_target,
        )
        config_player.name = f"Config ({utilization_target:.0%})"

        # Standard opponents
        opponents = [
            axl.Cooperator(),
            axl.Defector(),
            axl.TitForTat(),
            axl.Random(),
            axl.Grudger(),
        ]

        # Run matches
        results = {}
        total_score = 0
        total_coop = 0

        for opponent in opponents:
            match = axl.Match([config_player, opponent], turns=100)
            match.play()

            results[opponent.name] = {
                "score": match.final_score()[0],
                "cooperation_rate": match.cooperation()[0],
                "outcome": (
                    "win"
                    if match.winner() == config_player
                    else "loss"
                    if match.winner()
                    else "tie"
                ),
            }

            total_score += match.final_score()[0]
            total_coop += match.cooperation()[0]

            config_player.reset()

        avg_score = total_score / len(opponents)
        avg_coop = total_coop / len(opponents)

        # Generate recommendation
        if avg_score >= 2.5 and avg_coop >= 0.6:
            recommendation = (
                "Config is cooperative and performs well. Suitable for production."
            )
        elif avg_score >= 2.0 and avg_coop < 0.4:
            recommendation = (
                "Config is too aggressive. May cause issues in shared environment."
            )
        elif avg_score < 2.0:
            recommendation = "Config underperforms. Consider more adaptive strategy."
        else:
            recommendation = "Config is balanced but could improve cooperation."

        return {
            "config_name": config_player.name,
            "matchup_results": results,
            "average_score": avg_score,
            "cooperation_rate": avg_coop,
            "recommendation": recommendation,
            "strategy_classification": strategy_type,
        }


def get_game_theory_service(db: Session) -> GameTheoryService:
    """Dependency injection for GameTheoryService."""
    return GameTheoryService(db)
