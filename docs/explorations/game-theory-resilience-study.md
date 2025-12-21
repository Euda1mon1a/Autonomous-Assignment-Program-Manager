# Game Theory for Empirical Resilience Testing

> Using Axelrod's Prisoner's Dilemma tournaments to empirically study scheduling and resilience configurations
>
> *Date: 2025-12-21*

---

## The Insight

Robert Axelrod's famous computer tournaments (1980-1984) revealed something profound: in an environment where agents repeatedly interact, the simple **Tit for Tat** strategy consistently beats far more sophisticated algorithms.

**Tit for Tat (TFT)** wins because it is:
- **Nice**: Never defects first
- **Retaliatory**: Punishes defection immediately
- **Forgiving**: Returns to cooperation if opponent does
- **Clear**: Easy to predict, builds trust

This isn't just game theory trivia. It's a framework for **empirically testing system configurations** by treating them as competing strategies in an environment.

---

## Why This Matters for Scheduling

The existing game theory research in this codebase focuses on:
- **Mechanism Design**: VCG, Shapley values, Nash equilibrium
- **Fair Allocation**: Strategyproof preference elicitation
- **Workload Distribution**: Cooperative game theory

This is different. Axelrod's approach lets us:
- **Test configurations empirically** rather than theoretically
- **Discover emergent properties** through simulation
- **Find evolutionarily stable configurations** that can't be invaded by edge cases
- **Prove robustness** through competition

---

## The Core Framework

### Step 1: Gamify the Environment

To use Axelrod's framework, we must translate scheduling concepts into game theory primitives.

#### The Payoff Matrix

In the Prisoner's Dilemma, two players choose to **Cooperate (C)** or **Defect (D)**:

```
                   Player B
                 C         D
          ┌─────────┬─────────┐
Player A  │  (3,3)  │  (0,5)  │   C
          ├─────────┼─────────┤
          │  (5,0)  │  (1,1)  │   D
          └─────────┴─────────┘
```

- Both cooperate → Both get 3 (mutual benefit)
- One defects, one cooperates → Defector gets 5, cooperator gets 0
- Both defect → Both get 1 (mutual harm)

#### Translation to Scheduling

| Game Theory | Scheduling Analog |
|-------------|-------------------|
| **Cooperate** | Follow protocol, release unused resources, share coverage, respond quickly |
| **Defect** | Hoard resources, throttle requests, delay responses, ignore constraints |
| **Mutual Cooperation** | System stable, high throughput, good coverage (+3) |
| **Mutual Defection** | System deadlock, cascades, poor coverage (+1) |
| **Exploiter wins** | Aggressive config gets resources, others starve (+5 vs 0) |

#### Payoff Matrix for Resilience Configurations

```
                        Config B
                   Cooperative    Aggressive
              ┌─────────────────┬─────────────────┐
Config A      │  Both stable    │  A starved      │  Cooperative
Cooperative   │  Coverage: 95%  │  A: 70%, B: 99% │
              │  (+3, +3)       │  (0, +5)        │
              ├─────────────────┼─────────────────┤
Aggressive    │  B starved      │  Both degraded  │
              │  A: 99%, B: 70% │  Coverage: 80%  │
              │  (+5, 0)        │  (+1, +1)       │
              └─────────────────┴─────────────────┘
```

### Step 2: Define What "Winning" Means

**Utility function** for a scheduling configuration:

```python
def calculate_utility(config_result: ConfigResult) -> float:
    """
    Calculate utility (payoff) for a configuration's performance.

    Components:
    - Coverage achieved (0-100%)
    - ACGME compliance (binary or percentage)
    - Resource utilization (target: 80%)
    - Response latency (lower = better)
    - Cascade failures avoided (binary)
    """
    return (
        0.40 * config_result.coverage_rate +
        0.25 * config_result.acgme_compliance +
        0.15 * (1.0 - abs(config_result.utilization - 0.80)) +
        0.10 * (1.0 - config_result.normalized_latency) +
        0.10 * (1.0 if not config_result.cascade_occurred else 0.0)
    )
```

---

## Scenario A: Single Deployment (Tournament Approach)

In a single deployment, we test which configuration handles a shared environment best.

### How It Works

1. **Define Configurations as Strategies**

   Each configuration becomes a "player" with defined behavior:

   ```python
   class CooperativeConfig:
       """Conservative configuration that shares resources."""
       utilization_target = 0.70  # Leave 30% buffer
       cross_zone_borrowing = True
       sacrifice_willingness = "high"
       response_timeout = 5000  # ms, generous

   class AggressiveConfig:
       """Aggressive configuration that maximizes own performance."""
       utilization_target = 0.95  # Push limits
       cross_zone_borrowing = False  # Hoard resources
       sacrifice_willingness = "low"
       response_timeout = 500  # ms, impatient

   class TitForTatConfig:
       """Adaptive configuration that mirrors environment behavior."""
       def __init__(self):
           self.last_opponent_action = "cooperate"

       @property
       def utilization_target(self):
           if self.last_opponent_action == "cooperate":
               return 0.70  # Cooperative
           else:
               return 0.90  # Retaliatory
   ```

2. **Run Round-Robin Tournament**

   Every configuration pairs against every other (including itself):

   ```python
   import axelrod as axl

   # Define custom strategies (our configs)
   players = [
       CooperativeStrategy(),    # Always cooperative
       AggressiveStrategy(),     # Always defect
       TitForTatStrategy(),      # Mirror opponent
       RandomStrategy(),         # Chaos monkey
       GrudgerStrategy(),        # Cooperate until betrayed, then always defect
       PavlovStrategy(),         # Win-stay, lose-shift
   ]

   # Run tournament
   tournament = axl.Tournament(players, turns=100, repetitions=10)
   results = tournament.play()

   print(results.ranked_names)
   # ['Tit For Tat', 'Pavlov', 'Cooperative', 'Grudger', 'Random', 'Aggressive']
   ```

3. **Use TFT as Benchmark Validator**

   A key insight: if a configuration cannot survive against Tit for Tat, it's too aggressive for a shared production environment.

   ```python
   def validate_config_against_tft(config: Config) -> ValidationResult:
       """
       Test if configuration can coexist with TFT validator.

       If config tries to "defect" (hog resources), TFT will
       retaliate (throttle the config). Only cooperative configs
       can achieve high scores against TFT.
       """
       tft_validator = TitForTatValidator()

       scores = []
       for round in range(100):
           config_action = config.decide_action(tft_validator.history)
           tft_action = tft_validator.decide_action(config.history)

           config_score, tft_score = calculate_payoffs(config_action, tft_action)
           scores.append(config_score)

           config.history.append(config_action)
           tft_validator.history.append(tft_action)

       avg_score = sum(scores) / len(scores)

       return ValidationResult(
           passed=avg_score >= 2.5,  # Mutual cooperation threshold
           avg_score=avg_score,
           recommendation="cooperative" if avg_score >= 2.5 else "too_aggressive"
       )
   ```

### Tournament Metrics

| Metric | What It Measures |
|--------|------------------|
| **Average Score** | Overall performance across all opponents |
| **Win Rate** | Fraction of matchups with higher score |
| **Cooperation Rate** | How often config cooperated |
| **Exploitation Resistance** | Score against aggressive opponents |
| **Stability** | Variance in scores across matchups |

---

## Scenario B: Multiple Deployments (Evolutionary Approach)

This is where Axelrod's framework truly shines. Instead of fixed tournaments, we simulate **evolution** of configurations over generations.

### The Moran Process

A population of configurations "reproduces" based on fitness. Over time, successful strategies spread while unsuccessful ones go extinct.

```python
import axelrod as axl

# Define starting population
players = [
    axl.TitForTat(),
    axl.TitForTat(),
    axl.Defector(),
    axl.Defector(),
    axl.Cooperator(),
    axl.Random(),
]

# Run Moran process
mp = axl.MoranProcess(players, turns=100)
populations = mp.play()

print(f"Winner: {mp.winning_strategy_name}")
# Typically: "Tit For Tat"
```

### Why TFT Wins Evolutionarily

1. **Aggressive configs (Defectors)** initially dominate cooperative configs
2. **But** when Defectors encounter other Defectors, both score poorly (mutual defection)
3. **Meanwhile**, TFT configs cooperate with each other, maintaining steady high scores
4. **Over generations**, TFT population grows while Defector population shrinks
5. **Eventually**, TFT achieves dominance (evolutionarily stable)

### Applying to Resilience Configurations

```python
class EvolutionaryConfigTester:
    """
    Test configurations using evolutionary dynamics.

    Proves which config is "evolutionarily stable" - meaning it cannot
    be invaded by mutant configurations (edge cases, anomalies).
    """

    def __init__(self, population_size: int = 100):
        self.population_size = population_size

    def run_evolution(
        self,
        configs: list[ConfigStrategy],
        generations: int = 1000,
        interaction_per_gen: int = 10
    ) -> EvolutionResult:
        """
        Run evolutionary simulation.

        Args:
            configs: Initial configuration strategies
            generations: Number of evolution cycles
            interaction_per_gen: Random interactions per generation

        Returns:
            EvolutionResult with winning strategy and population history
        """
        # Initialize population
        population = self._initialize_population(configs)
        history = []

        for gen in range(generations):
            # Random interactions
            for _ in range(interaction_per_gen):
                # Select two random individuals
                i, j = random.sample(range(len(population)), 2)

                # They interact (play prisoner's dilemma)
                payoff_i, payoff_j = self._interact(population[i], population[j])

                # Update fitness
                population[i].fitness += payoff_i
                population[j].fitness += payoff_j

            # Selection: weakest 10% die, strongest 10% reproduce
            population = self._selection(population)

            # Record population state
            history.append(self._count_strategies(population))

        return EvolutionResult(
            winner=self._dominant_strategy(population),
            history=history,
            final_population=population
        )

    def _interact(self, config_a: ConfigStrategy, config_b: ConfigStrategy) -> tuple[float, float]:
        """
        Simulate interaction between two configurations.

        Translates to resilience: How do they perform when sharing resources?
        """
        action_a = config_a.decide(config_b.history)
        action_b = config_b.decide(config_a.history)

        # Update histories
        config_a.history.append(action_a)
        config_b.history.append(action_b)

        # Calculate payoffs
        return self._payoff_matrix(action_a, action_b)

    def _selection(self, population: list[ConfigStrategy]) -> list[ConfigStrategy]:
        """
        Natural selection: weak die, strong reproduce.
        """
        # Sort by fitness
        sorted_pop = sorted(population, key=lambda c: c.fitness)

        # Kill bottom 10%
        survivors = sorted_pop[len(sorted_pop) // 10:]

        # Clone top 10%
        top_performers = sorted_pop[-len(sorted_pop) // 10:]
        clones = [copy.deepcopy(c) for c in top_performers]

        # New population
        new_population = survivors + clones

        # Reset fitness for next generation
        for config in new_population:
            config.fitness = 0.0

        return new_population
```

### Visualizing Evolution

The Axelrod library can generate **stackplots** showing strategy population over time:

```python
import axelrod as axl
import matplotlib.pyplot as plt

players = [
    axl.TitForTat(), axl.TitForTat(),
    axl.Defector(), axl.Defector(),
    axl.Cooperator(), axl.Cooperator(),
    axl.Random(), axl.Random(),
]

mp = axl.MoranProcess(players, turns=100)
populations = mp.play()

# Plot population dynamics
ax = mp.populations_plot()
plt.title("Configuration Evolution Over Generations")
plt.xlabel("Generation")
plt.ylabel("Population Fraction")
plt.savefig("evolution_plot.png")
```

---

## Integration with Existing Resilience Framework

### Mapping Resilience Concepts to Game Theory

| Resilience Concept | Game Theory Translation |
|-------------------|------------------------|
| **80% Utilization Rule** | Cooperation threshold (leave buffer for others) |
| **N-1/N-2 Contingency** | Robustness to opponent defection |
| **Blast Radius Isolation** | Limiting defection impact |
| **Defense in Depth** | Multiple cooperation mechanisms |
| **Sacrifice Hierarchy** | Graduated defection responses |
| **Homeostasis** | Return to cooperation after perturbation |
| **Static Stability** | Pre-computed TFT responses |

### Connecting to Existing Simulation Infrastructure

The codebase already has simulation infrastructure in `backend/app/resilience/simulation/`:

```python
# Extend existing SimulationEnvironment with game theory
from app.resilience.simulation.base import SimulationEnvironment, SimulationConfig

class GameTheoreticSimulation(SimulationEnvironment):
    """
    Extends resilience simulation with game-theoretic analysis.
    """

    def __init__(self, config: SimulationConfig, strategies: list[ConfigStrategy]):
        super().__init__(config)
        self.strategies = strategies
        self.tournament_results = None
        self.evolution_results = None

    def run_tournament(self) -> TournamentResults:
        """Run Axelrod-style round-robin tournament."""
        import axelrod as axl

        # Convert our strategies to axelrod format
        axl_players = [self._to_axelrod_player(s) for s in self.strategies]

        tournament = axl.Tournament(
            axl_players,
            turns=self.config.duration_days,
            repetitions=10
        )

        self.tournament_results = tournament.play()
        return self._convert_results(self.tournament_results)

    def run_evolution(self, generations: int = 100) -> EvolutionResults:
        """Run Moran process evolutionary simulation."""
        import axelrod as axl

        axl_players = [self._to_axelrod_player(s) for s in self.strategies]

        mp = axl.MoranProcess(axl_players, turns=self.config.duration_days)
        self.evolution_results = mp.play()

        return EvolutionResults(
            winner=mp.winning_strategy_name,
            generations=len(self.evolution_results),
            is_evolutionarily_stable=self._check_ess(mp)
        )

    def _to_axelrod_player(self, strategy: ConfigStrategy) -> axl.Player:
        """Convert our config strategy to axelrod Player."""

        class CustomPlayer(axl.Player):
            name = strategy.name
            classifier = {"stochastic": strategy.is_stochastic}

            def strategy(self, opponent):
                # Map our config decisions to C/D
                action = strategy.decide(opponent.history)
                return axl.Action.C if action == "cooperate" else axl.Action.D

        return CustomPlayer()
```

### Specific Experiments to Run

#### Experiment 1: Configuration Robustness Tournament

Test which resilience configuration performs best across diverse opponents:

```python
def experiment_config_tournament():
    """
    Test resilience configurations in round-robin tournament.

    Question: Which configuration strategy is most robust?
    """
    configs = [
        ConservativeConfig(utilization_target=0.70, buffer=0.30),
        ModerateConfig(utilization_target=0.80, buffer=0.20),
        AggressiveConfig(utilization_target=0.90, buffer=0.10),
        AdaptiveConfig(strategy="tit_for_tat"),
        GrudgerConfig(strategy="cooperate_until_betrayed"),
        RandomConfig(strategy="chaos_monkey"),
    ]

    sim = GameTheoreticSimulation(
        config=SimulationConfig(duration_days=365),
        strategies=configs
    )

    results = sim.run_tournament()

    print("Configuration Rankings:")
    for i, (name, score) in enumerate(results.rankings):
        print(f"  {i+1}. {name}: {score:.2f}")

    # Expected: Adaptive (TFT-based) ranks highest
    return results
```

#### Experiment 2: Evolutionary Stability of 80% Rule

Test if the 80% utilization threshold is evolutionarily stable:

```python
def experiment_utilization_evolution():
    """
    Test if 80% utilization rule is evolutionarily stable.

    Question: Can aggressive configs (95%+) invade a population
              following the 80% rule?
    """
    # Population following 80% rule
    population = [
        UtilizationConfig(target=0.80) for _ in range(80)
    ] + [
        # Invaders trying higher utilization
        UtilizationConfig(target=0.95) for _ in range(20)
    ]

    sim = GameTheoreticSimulation(
        config=SimulationConfig(duration_days=365),
        strategies=population
    )

    results = sim.run_evolution(generations=500)

    print(f"Winner: {results.winner}")
    print(f"80% Rule Stable: {results.winner.target == 0.80}")

    # If 80% wins, the threshold is evolutionarily stable
    # If 95% wins, the threshold may be too conservative
    return results
```

#### Experiment 3: Defense Strategy Evolution

Test which defense-in-depth strategy survives evolutionary pressure:

```python
def experiment_defense_evolution():
    """
    Test defense strategies under evolutionary selection.

    Question: Which defense-in-depth level is optimal?
    """
    population = []

    # Mix of defense strategies
    for level in [1, 2, 3, 4, 5]:  # Defense levels
        for _ in range(20):
            population.append(DefenseConfig(
                activation_threshold=level,
                escalation_speed="immediate" if level <= 2 else "gradual"
            ))

    sim = GameTheoreticSimulation(
        config=SimulationConfig(duration_days=365),
        strategies=population
    )

    results = sim.run_evolution(generations=500)

    # Analyze which defense level dominates
    final_levels = [c.activation_threshold for c in results.final_population]
    avg_level = sum(final_levels) / len(final_levels)

    print(f"Average Defense Level: {avg_level:.1f}")
    print(f"Level Distribution: {Counter(final_levels)}")

    return results
```

#### Experiment 4: Cascade Resistance

Test which configurations resist cascade failures best:

```python
def experiment_cascade_resistance():
    """
    Test cascade resistance using TFT-based validation.

    Question: Can configurations survive a "defection cascade"?
    """
    configs = [
        IsolatedZonesConfig(cross_borrowing=False),
        SharedResourcesConfig(cross_borrowing=True),
        AdaptiveBorrowingConfig(strategy="tit_for_tat"),
    ]

    # Create adversarial environment with cascading defectors
    adversaries = [
        CascadeDefector() for _ in range(10)  # Defect and spread
    ]

    for config in configs:
        # Test each config against cascade adversaries
        results = test_against_adversaries(config, adversaries, rounds=100)

        print(f"{config.name}:")
        print(f"  Survival Rate: {results.survival_rate:.1%}")
        print(f"  Cascade Blocked: {results.cascades_blocked}")
        print(f"  Final Coverage: {results.final_coverage:.1%}")

    # Isolated zones should resist cascades best
    # Adaptive should balance resistance with cooperation benefits
```

---

## Implementation with Axelrod Library

### Installation

```bash
pip install axelrod
```

### Custom Strategy Template

```python
import axelrod as axl

class ResilienceConfigStrategy(axl.Player):
    """
    Base class for resilience configuration strategies.

    Translates scheduling/resilience behavior to Prisoner's Dilemma actions.
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
        utilization_target: float = 0.80,
        cross_zone_borrowing: bool = True,
        sacrifice_willingness: str = "medium"
    ):
        super().__init__()
        self.utilization_target = utilization_target
        self.cross_zone_borrowing = cross_zone_borrowing
        self.sacrifice_willingness = sacrifice_willingness

    def strategy(self, opponent: axl.Player) -> axl.Action:
        """
        Decide to cooperate or defect based on configuration behavior.

        Cooperation = following protocols, sharing resources
        Defection = hoarding resources, ignoring constraints
        """
        # First move: always cooperate (nice)
        if len(self.history) == 0:
            return axl.Action.C

        # Check opponent's last move
        opponent_defected = opponent.history[-1] == axl.Action.D

        # Tit for Tat base behavior
        if opponent_defected:
            # Retaliatory behavior based on config
            if self.sacrifice_willingness == "high":
                # Forgiving: still try to cooperate
                return axl.Action.C
            elif self.sacrifice_willingness == "low":
                # Grudging: defect back
                return axl.Action.D
            else:
                # Medium: TFT
                return axl.Action.D
        else:
            # Opponent cooperated, reciprocate
            return axl.Action.C


class AggressiveConfig(ResilienceConfigStrategy):
    """Configuration that prioritizes own performance over cooperation."""

    name = "Aggressive Config"

    def __init__(self):
        super().__init__(
            utilization_target=0.95,
            cross_zone_borrowing=False,
            sacrifice_willingness="low"
        )

    def strategy(self, opponent: axl.Player) -> axl.Action:
        # Always defect (maximize own resources)
        return axl.Action.D


class ConservativeConfig(ResilienceConfigStrategy):
    """Configuration that always cooperates (leaves buffer for others)."""

    name = "Conservative Config"

    def __init__(self):
        super().__init__(
            utilization_target=0.70,
            cross_zone_borrowing=True,
            sacrifice_willingness="high"
        )

    def strategy(self, opponent: axl.Player) -> axl.Action:
        # Always cooperate
        return axl.Action.C


class TitForTatConfig(ResilienceConfigStrategy):
    """Configuration that mirrors opponent behavior."""

    name = "TFT Config"

    def __init__(self):
        super().__init__(
            utilization_target=0.80,
            cross_zone_borrowing=True,
            sacrifice_willingness="medium"
        )

    def strategy(self, opponent: axl.Player) -> axl.Action:
        # First move: cooperate
        if len(opponent.history) == 0:
            return axl.Action.C
        # Mirror opponent's last move
        return opponent.history[-1]


class GrudgerConfig(ResilienceConfigStrategy):
    """Configuration that cooperates until betrayed, then always defects."""

    name = "Grudger Config"

    def __init__(self):
        super().__init__(
            utilization_target=0.80,
            cross_zone_borrowing=True,
            sacrifice_willingness="medium"
        )
        self._betrayed = False

    def strategy(self, opponent: axl.Player) -> axl.Action:
        if axl.Action.D in opponent.history:
            self._betrayed = True

        if self._betrayed:
            return axl.Action.D
        return axl.Action.C
```

### Running a Full Tournament

```python
import axelrod as axl
import matplotlib.pyplot as plt

def run_resilience_tournament():
    """
    Full tournament testing resilience configurations.
    """
    # Create players
    players = [
        ConservativeConfig(),
        AggressiveConfig(),
        TitForTatConfig(),
        GrudgerConfig(),
        axl.Random(),  # Chaos monkey baseline
        axl.TitForTwoTats(),  # More forgiving TFT
        axl.SuspiciousTitForTat(),  # Defects first, then TFT
    ]

    # Run tournament
    tournament = axl.Tournament(
        players,
        turns=200,  # 200 interactions per matchup
        repetitions=50,  # 50 repetitions for statistical significance
        seed=42  # Reproducibility
    )

    results = tournament.play()

    # Print rankings
    print("=== Tournament Rankings ===")
    for i, name in enumerate(results.ranked_names):
        score = results.scores[results.ranking.index(i)]
        print(f"{i+1}. {name}: {sum(score)/len(score):.2f}")

    # Plot results
    plot = axl.Plot(results)

    # Payoff matrix heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    plot.payoff(ax=ax)
    plt.title("Configuration Payoff Matrix")
    plt.tight_layout()
    plt.savefig("payoff_matrix.png")

    # Win distribution
    fig, ax = plt.subplots(figsize=(10, 6))
    plot.boxplot(ax=ax)
    plt.title("Configuration Score Distribution")
    plt.tight_layout()
    plt.savefig("score_distribution.png")

    return results


def run_resilience_evolution():
    """
    Evolutionary simulation of resilience configurations.
    """
    # Initial population
    players = [
        ConservativeConfig(),
        ConservativeConfig(),
        AggressiveConfig(),
        AggressiveConfig(),
        TitForTatConfig(),
        TitForTatConfig(),
        GrudgerConfig(),
        GrudgerConfig(),
    ]

    # Run Moran process
    mp = axl.MoranProcess(
        players,
        turns=100,
        noise=0.01  # Small chance of random action (mutation)
    )

    populations = mp.play()

    print(f"=== Evolution Results ===")
    print(f"Winner: {mp.winning_strategy_name}")
    print(f"Generations: {len(populations)}")

    # Plot population dynamics
    fig, ax = plt.subplots(figsize=(12, 6))
    mp.populations_plot(ax=ax)
    plt.title("Configuration Population Over Generations")
    plt.xlabel("Generation")
    plt.ylabel("Population Count")
    plt.tight_layout()
    plt.savefig("evolution_dynamics.png")

    return mp


if __name__ == "__main__":
    print("Running Tournament...")
    tournament_results = run_resilience_tournament()

    print("\nRunning Evolution...")
    evolution_results = run_resilience_evolution()
```

---

## Key Insights for Resilience Design

### 1. TFT Properties Map to Resilience Principles

| TFT Property | Resilience Principle | Implementation |
|--------------|---------------------|----------------|
| **Nice** | Start with cooperation | Default to 80% utilization, enable borrowing |
| **Retaliatory** | Respond to defection | Activate defense levels when stressed |
| **Forgiving** | Return to normal | Homeostasis feedback loops |
| **Clear** | Predictable behavior | Explicit thresholds, documented responses |

### 2. Aggressive Configs Are Self-Defeating

When aggressive configurations encounter each other:
- Both try to hoard resources → deadlock
- Both ignore constraints → cascade failures
- Mutual defection → everyone loses

This explains why the 80% utilization rule works: it leaves room for cooperation.

### 3. Evolutionarily Stable = Production Ready

A configuration that wins evolutionary simulation is:
- Robust to edge cases (mutant invaders)
- Stable under repeated stress
- Cannot be exploited by gaming

If your config survives a Moran process, it can survive production anomalies.

### 4. Tournament Rankings Reveal Trade-offs

Tournament results show:
- **High average score** = good general performance
- **Low variance** = consistent, predictable
- **High cooperation rate** = good neighbor in shared environment

Choose configs that balance these trade-offs for your use case.

---

## Conclusion

Axelrod's Prisoner's Dilemma framework provides a rigorous, empirical method for testing scheduling and resilience configurations:

1. **Gamify** the environment by defining cooperation/defection in scheduling terms
2. **Tournament** testing reveals which configs are most robust across opponents
3. **Evolutionary** simulation proves which configs are stable against anomalies
4. **TFT validation** provides a benchmark for "good citizen" behavior

The system already implements many TFT-like properties:
- **Nice**: 80% utilization leaves buffer (cooperation)
- **Retaliatory**: Defense-in-depth activates under stress
- **Forgiving**: Homeostasis returns to normal after perturbation
- **Clear**: Explicit thresholds and documented responses

By formalizing these as game-theoretic strategies and running Axelrod-style tournaments, we can **prove** configuration robustness rather than just **assume** it.

---

## References

- Axelrod, R. (1984). *The Evolution of Cooperation*. Basic Books.
- Axelrod, R. (1980). "Effective Choice in the Prisoner's Dilemma." *Journal of Conflict Resolution*, 24(1), 3-25.
- Nowak, M. A. (2006). *Evolutionary Dynamics: Exploring the Equations of Life*. Harvard University Press.
- [Axelrod Python Library Documentation](https://axelrod.readthedocs.io/)
- [Vincent Knight - "Tit for Tat and the Axelrod Library"](https://www.youtube.com/watch?v=mUxt--mMjwA) (Talk by library maintainer)

---

## Appendix: Full Integration Example

```python
"""
Full integration of game-theoretic testing with resilience framework.
"""
from app.resilience.service import ResilienceService
from app.resilience.simulation.base import SimulationConfig
import axelrod as axl


class ResilienceGameTheoryAnalyzer:
    """
    Integrates Axelrod tournament analysis with resilience framework.
    """

    def __init__(self, resilience_service: ResilienceService):
        self.resilience_service = resilience_service

    def analyze_current_config(self) -> dict:
        """
        Analyze current resilience configuration using game theory.
        """
        # Get current config parameters
        current_config = self.resilience_service.get_current_config()

        # Create strategy representation
        current_strategy = self._config_to_strategy(current_config)

        # Standard opponents to test against
        opponents = [
            axl.Cooperator(),
            axl.Defector(),
            axl.TitForTat(),
            axl.Random(),
            axl.Grudger(),
        ]

        # Run matches
        results = {}
        for opponent in opponents:
            match = axl.Match([current_strategy, opponent], turns=100)
            match.play()

            results[opponent.name] = {
                "score": match.final_score()[0],
                "cooperation_rate": match.cooperation()[0],
                "outcome": "win" if match.winner() == current_strategy else "loss"
            }

        # Overall assessment
        avg_score = sum(r["score"] for r in results.values()) / len(results)
        avg_coop = sum(r["cooperation_rate"] for r in results.values()) / len(results)

        return {
            "config_name": current_config.name,
            "matchup_results": results,
            "average_score": avg_score,
            "cooperation_rate": avg_coop,
            "recommendation": self._generate_recommendation(avg_score, avg_coop)
        }

    def find_optimal_config(
        self,
        candidates: list[dict],
        generations: int = 100
    ) -> dict:
        """
        Find optimal configuration through evolutionary simulation.
        """
        # Convert configs to strategies
        strategies = [self._config_to_strategy(c) for c in candidates]

        # Run Moran process
        mp = axl.MoranProcess(strategies, turns=100)
        mp.play()

        winner_name = mp.winning_strategy_name
        winner_config = next(
            c for c in candidates
            if c["name"] == winner_name
        )

        return {
            "optimal_config": winner_config,
            "generations_to_win": len(mp.population_distribution()),
            "is_evolutionarily_stable": True
        }

    def _config_to_strategy(self, config: dict) -> axl.Player:
        """Convert resilience config to Axelrod player."""

        class ConfigStrategy(axl.Player):
            name = config.get("name", "Config")

            def strategy(self, opponent):
                # Map utilization target to cooperation tendency
                util_target = config.get("utilization_target", 0.80)

                if util_target <= 0.70:
                    # Conservative: always cooperate
                    return axl.Action.C
                elif util_target >= 0.90:
                    # Aggressive: always defect
                    return axl.Action.D
                else:
                    # Moderate: TFT
                    if len(opponent.history) == 0:
                        return axl.Action.C
                    return opponent.history[-1]

        return ConfigStrategy()

    def _generate_recommendation(self, score: float, coop_rate: float) -> str:
        """Generate recommendation based on game theory analysis."""
        if score >= 2.5 and coop_rate >= 0.6:
            return "Config is cooperative and performs well. Suitable for production."
        elif score >= 2.0 and coop_rate < 0.4:
            return "Config is too aggressive. May cause issues in shared environment."
        elif score < 2.0:
            return "Config underperforms. Consider more adaptive strategy."
        else:
            return "Config is balanced but could improve cooperation."
```

---

*End of exploration.*
