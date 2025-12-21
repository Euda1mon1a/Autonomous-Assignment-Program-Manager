# Game Theory Framework Architecture

This document describes the architecture of the game theory analysis framework for testing resilience configurations.

---

## Overview

The game theory framework applies Robert Axelrod's Prisoner's Dilemma tournament approach to empirically test scheduling and resilience configurations. By treating configurations as competing strategies, we can identify optimal, evolutionarily stable configurations that perform well under various conditions.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Game Theory Framework                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│   │   Frontend   │     │   Backend    │     │   Axelrod    │            │
│   │  Dashboard   │────▶│   Service    │────▶│   Library    │            │
│   └──────────────┘     └──────────────┘     └──────────────┘            │
│          │                    │                    │                     │
│          │                    │                    │                     │
│          ▼                    ▼                    ▼                     │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│   │   React      │     │  PostgreSQL  │     │  Tournament  │            │
│   │   Hooks      │     │   Database   │     │   Engine     │            │
│   └──────────────┘     └──────────────┘     └──────────────┘            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### Prisoner's Dilemma Mapping

The system maps resilience configuration behaviors to game theory primitives:

| Game Theory | Resilience Equivalent |
|-------------|----------------------|
| **Cooperate (C)** | Follow protocol, share resources, maintain 80% utilization |
| **Defect (D)** | Hoard resources, ignore constraints, push to 95%+ utilization |
| **Payoff Matrix** | Coverage rates, stability metrics, cascade resistance |
| **Tournament** | Round-robin testing of all config pairings |
| **Moran Process** | Evolutionary selection pressure on configs |

### Strategy Types

The framework supports six built-in strategy types:

| Type | Behavior | Scheduling Analog |
|------|----------|-------------------|
| `cooperative` | Always cooperates | Conservative config (70% target) |
| `aggressive` | Always defects | Aggressive config (95% target) |
| `tit_for_tat` | Mirrors opponent | Adaptive config (80% target) |
| `grudger` | Cooperates until betrayed | Defensive config |
| `random` | Random actions | Chaos monkey testing |
| `custom` | User-defined logic | Custom configurations |

---

## Component Architecture

### Backend Components

```
backend/app/
├── models/
│   └── game_theory.py          # SQLAlchemy models
├── schemas/
│   └── game_theory.py          # Pydantic schemas
├── services/
│   └── game_theory.py          # Business logic + Axelrod integration
└── api/routes/
    └── game_theory.py          # REST API endpoints
```

#### Database Models

```python
# ConfigStrategy - Represents a configuration as a game strategy
class ConfigStrategy(Base):
    id: UUID
    name: str
    strategy_type: StrategyType  # cooperative, aggressive, tit_for_tat, etc.
    utilization_target: float
    cross_zone_borrowing: bool
    sacrifice_willingness: str  # low, medium, high
    response_timeout_ms: int
    custom_logic: Optional[str]  # JSON for custom behavior
    is_active: bool

# GameTheoryTournament - Round-robin tournament execution
class GameTheoryTournament(Base):
    id: UUID
    name: str
    status: SimulationStatus
    turns_per_match: int
    repetitions: int
    noise: float
    results: Optional[dict]  # JSON results

# EvolutionSimulation - Moran process evolutionary simulation
class EvolutionSimulation(Base):
    id: UUID
    name: str
    status: SimulationStatus
    population_size: int
    max_generations: int
    mutation_rate: float
    results: Optional[dict]  # JSON results
```

#### GameTheoryService

The core service integrates with the Axelrod library:

```python
class GameTheoryService:
    """
    Service for game-theoretic analysis of resilience configurations.
    """

    async def create_strategy(self, db, data) -> ConfigStrategy:
        """Create a new configuration strategy."""

    async def run_tournament(self, db, data) -> GameTheoryTournament:
        """Run round-robin tournament with specified strategies."""

    async def run_evolution(self, db, data) -> EvolutionSimulation:
        """Run Moran process evolutionary simulation."""

    async def validate_strategy(self, db, data) -> ValidationResult:
        """Validate strategy against TFT benchmark."""

    async def analyze_current_config(self, db) -> AnalysisResult:
        """Analyze current system configuration."""
```

#### ResilienceConfigPlayer

Custom Axelrod player that translates configuration behavior:

```python
class ResilienceConfigPlayer(axl.Player):
    """
    Custom Axelrod player representing a resilience configuration.

    Maps configuration parameters to cooperation/defection decisions.
    """

    def __init__(self, config: ConfigStrategy):
        self.config = config
        self.utilization_target = config.utilization_target
        self.sacrifice_willingness = config.sacrifice_willingness

    def strategy(self, opponent: axl.Player) -> axl.Action:
        # First move: always cooperate (nice property)
        if len(self.history) == 0:
            return axl.Action.C

        # Map strategy_type to behavior
        if self.config.strategy_type == StrategyType.COOPERATIVE:
            return axl.Action.C
        elif self.config.strategy_type == StrategyType.AGGRESSIVE:
            return axl.Action.D
        elif self.config.strategy_type == StrategyType.TIT_FOR_TAT:
            return opponent.history[-1]
        # ... etc
```

### Frontend Components

```
frontend/src/
├── app/admin/game-theory/
│   └── page.tsx                    # Main dashboard page
├── components/game-theory/
│   ├── PayoffMatrix.tsx            # Heatmap visualization
│   ├── EvolutionChart.tsx          # Population dynamics chart
│   ├── StrategyCard.tsx            # Strategy display
│   ├── TournamentCard.tsx          # Tournament results
│   └── index.ts                    # Barrel export
├── hooks/
│   └── useGameTheory.ts            # TanStack Query hooks
└── types/
    └── game-theory.ts              # TypeScript types
```

#### React Hooks

TanStack Query hooks for data fetching with automatic polling for running simulations:

```typescript
// Queries
export function useStrategies() { ... }
export function useTournaments() { ... }
export function useEvolutions() { ... }
export function useGameTheorySummary() { ... }

// Mutations
export function useCreateStrategy() { ... }
export function useCreateTournament() { ... }
export function useCreateEvolution() { ... }
export function useValidateStrategy() { ... }
export function useAnalyzeConfig() { ... }
```

---

## Data Flow

### Tournament Execution Flow

```
1. User creates tournament via frontend
     │
     ▼
2. API receives request, validates strategies exist
     │
     ▼
3. GameTheoryService.run_tournament() called
     │
     ▼
4. Tournament record created with status="pending"
     │
     ▼
5. Background task starts (FastAPI BackgroundTasks)
     │
     ▼
6. ResilienceConfigPlayer instances created for each strategy
     │
     ▼
7. axl.Tournament() runs round-robin matches
     │
     ▼
8. Results computed: rankings, payoff matrix, cooperation rates
     │
     ▼
9. Database updated with results, status="completed"
     │
     ▼
10. Frontend polls and displays results
```

### Evolution Simulation Flow

```
1. User creates evolution simulation
     │
     ▼
2. Initial population created from strategy mix
     │
     ▼
3. axl.MoranProcess() initialized
     │
     ▼
4. Population evolves through selection pressure
     │
     ▼
5. Each generation: interactions → fitness → selection → reproduction
     │
     ▼
6. Process continues until fixation or max generations
     │
     ▼
7. Results: winner, generations to fixation, population history
     │
     ▼
8. Frontend visualizes population dynamics
```

---

## Integration with Resilience Framework

### Mapping to Existing Concepts

| Resilience Concept | Game Theory Translation |
|-------------------|------------------------|
| 80% Utilization Rule | Cooperation threshold (leave buffer for others) |
| N-1/N-2 Contingency | Robustness to opponent defection |
| Blast Radius Isolation | Limiting defection impact to zones |
| Defense in Depth | Multiple cooperation mechanisms |
| Sacrifice Hierarchy | Graduated defection responses |
| Homeostasis | Return to cooperation after perturbation |

### Using Game Theory for Resilience Validation

1. **Configuration Robustness**: Run tournaments to find configs that perform well across diverse opponents
2. **Evolutionary Stability**: Use Moran process to prove configs cannot be invaded by edge cases
3. **TFT Benchmark**: Validate that configs can coexist with cooperative neighbors
4. **Cascade Resistance**: Test configs against adversarial defection cascades

---

## Performance Considerations

### Tournament Complexity

- Time complexity: O(n² × turns × repetitions) where n = number of strategies
- Typical tournament: 6 strategies × 200 turns × 50 reps ≈ 2-5 seconds

### Evolution Complexity

- Time complexity: O(generations × population × turns)
- Typical evolution: 500 generations × 100 population × 100 turns ≈ 10-30 seconds

### Recommendations

1. **Use background tasks** for tournaments with >10 strategies
2. **Limit population size** for evolution simulations (100-200 is sufficient)
3. **Enable polling** in frontend for running simulations
4. **Consider Celery** for production-scale simulations

---

## Security Considerations

1. **Custom Logic Validation**: Custom strategy logic is stored as JSON, not executed code
2. **Rate Limiting**: Apply rate limits to tournament/evolution creation endpoints
3. **Resource Limits**: Cap maximum turns, repetitions, and population size
4. **Authentication**: All endpoints require authentication (except summary stats if desired)

---

## Future Enhancements

### Planned Features

1. **Multi-player Games**: Extend beyond 2-player PD to N-player scenarios
2. **Spatial Games**: Add network topology to model zone-based interactions
3. **Continuous Actions**: Move beyond binary C/D to continuous cooperation levels
4. **Real-time Integration**: Connect to live resilience metrics for dynamic adaptation

### Research Directions

1. **Mechanism Design**: Use VCG auctions for resource allocation
2. **Coalition Formation**: Model zone cooperation as coalitional games
3. **Stochastic Games**: Handle uncertainty in opponent behavior
4. **Reinforcement Learning**: Train optimal strategies through RL

---

## References

- Axelrod, R. (1984). *The Evolution of Cooperation*
- [Axelrod Python Library](https://axelrod.readthedocs.io/)
- Nowak, M. A. (2006). *Evolutionary Dynamics*
- See also: `docs/explorations/game-theory-resilience-study.md`
