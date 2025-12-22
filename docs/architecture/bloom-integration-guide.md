# Bloom Integration Guide: Scheduler & Resilience Modules

> Practical implementation guide for integrating Bloom prisoner's dilemma concepts into the residency scheduler
>
> *Date: 2025-12-22*

---

## Overview

This guide details **concrete integration points** for adding Bloom-style behavioral evaluation to the existing scheduler and resilience infrastructure.

### What We're Adding

| Capability | Integration Point | Benefit |
|-----------|-------------------|---------|
| AI Agent Evaluation | `GameTheoryService` | Test AI scheduling assistants before deployment |
| Behavioral Signals | `SwapAutoMatcher` | Detect cooperation/defection patterns in swap behavior |
| Resilience Metrics | `ResilienceService` | Use PD cooperation rates as health indicators |
| Configuration Testing | Tournament system | Prove configs are cooperation-stable |

---

## 1. Extend GameTheoryService for AI Evaluation

### Current State

The existing `GameTheoryService` tests **deterministic configuration strategies** (e.g., "80% utilization + cross-zone borrowing"). It doesn't evaluate AI models.

### Integration: Add BloomAIPlayer

**File:** `backend/app/services/game_theory.py`

```python
# Add after ResilienceConfigPlayer class (line ~142)

class BloomAIPlayer(axl.Player):
    """
    Axelrod player that wraps evaluated AI model behavior.

    Instead of deterministic strategy, uses actual AI model cooperation
    tendency measured by Bloom evaluation.

    This allows testing AI scheduling assistants in tournaments
    against configuration strategies.
    """

    name = "Bloom AI Player"
    classifier = {
        "memory_depth": float("inf"),  # AI has context
        "stochastic": True,  # AI responses vary
        "long_run_time": True,  # API calls
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def __init__(
        self,
        model_id: str,
        cooperation_rate: float,
        strategy_detected: str,
        defection_threshold: float = 0.3,
        bloom_evaluation_id: str | None = None,
        **kwargs
    ):
        """
        Initialize from Bloom evaluation results.

        Args:
            model_id: The AI model identifier (e.g., "claude-3-5-sonnet")
            cooperation_rate: Measured cooperation rate (0-1) from Bloom
            strategy_detected: Strategy type detected (tit_for_tat, etc.)
            defection_threshold: Opponent defection rate that triggers retaliation
            bloom_evaluation_id: Reference to full Bloom evaluation
        """
        super().__init__()
        self.model_id = model_id
        self.cooperation_rate = cooperation_rate
        self.strategy_detected = strategy_detected
        self.defection_threshold = defection_threshold
        self.bloom_evaluation_id = bloom_evaluation_id

        # Cache for simulating model behavior
        self._defection_count = 0

    def strategy(self, opponent: axl.Player) -> axl.Action:
        """
        Decide action based on measured AI behavior.

        Simulates the AI's strategy based on Bloom evaluation results.
        """
        import random

        # First move: based on detected strategy
        if len(self.history) == 0:
            # Most AI models cooperate first (from research)
            if self.strategy_detected in ["always_defect", "suspicious_tft"]:
                return axl.Action.D
            return axl.Action.C

        # Track opponent defections
        if len(opponent.history) > 0 and opponent.history[-1] == axl.Action.D:
            self._defection_count += 1

        opponent_defection_rate = self._defection_count / len(opponent.history)

        # Simulate based on detected strategy
        if self.strategy_detected == "always_cooperate":
            return axl.Action.C

        elif self.strategy_detected == "always_defect":
            return axl.Action.D

        elif self.strategy_detected == "tit_for_tat":
            return opponent.history[-1]

        elif self.strategy_detected == "forgiving_tft":
            # Research shows LLMs shift to forgiving at ~30% defection
            if opponent_defection_rate < self.defection_threshold:
                return axl.Action.C
            return opponent.history[-1]

        else:
            # Use measured cooperation rate as probability
            return axl.Action.C if random.random() < self.cooperation_rate else axl.Action.D

    def reset(self):
        """Reset for new match."""
        super().reset()
        self._defection_count = 0


# Add to GameTheoryService class

def create_ai_strategy_from_bloom(
    self,
    model_id: str,
    bloom_results: dict,
    name: str | None = None,
    created_by: str | None = None,
) -> ConfigStrategy:
    """
    Create a ConfigStrategy from Bloom evaluation results.

    This allows AI models to participate in tournaments alongside
    configuration strategies.

    Args:
        model_id: AI model identifier
        bloom_results: Results from Bloom evaluation containing:
            - cooperation_rate: float (0-1)
            - strategy_detected: str
            - avg_cooperation_score: float (0-10)
        name: Optional custom name
        created_by: User who initiated evaluation

    Returns:
        ConfigStrategy representing the AI model's behavior
    """
    strategy_name = name or f"AI: {model_id}"

    # Map Bloom results to strategy parameters
    coop_rate = bloom_results.get("cooperation_rate", 0.5)
    detected_strategy = bloom_results.get("strategy_detected", "mixed")

    # Determine strategy type from detected behavior
    if coop_rate > 0.9:
        strategy_type = "cooperative"
    elif coop_rate < 0.2:
        strategy_type = "aggressive"
    elif detected_strategy == "tit_for_tat":
        strategy_type = "tit_for_tat"
    elif detected_strategy == "forgiving_tft":
        strategy_type = "forgiving_tft"
    else:
        strategy_type = "tit_for_tat"  # Default to TFT for mixed

    # Create strategy record
    strategy = ConfigStrategy(
        name=strategy_name,
        description=f"AI model {model_id} evaluated via Bloom. "
                    f"Cooperation rate: {coop_rate:.1%}, "
                    f"Detected strategy: {detected_strategy}",
        strategy_type=strategy_type,
        created_by=created_by,
        # Map cooperation rate to utilization target
        # Higher cooperation = more willing to share (lower utilization)
        utilization_target=0.95 - (coop_rate * 0.25),  # 0.70-0.95
        cross_zone_borrowing=coop_rate > 0.5,
        sacrifice_willingness="high" if coop_rate > 0.7 else "medium" if coop_rate > 0.4 else "low",
        is_ai_model=True,
        ai_model_id=model_id,
        bloom_evaluation_id=bloom_results.get("evaluation_id"),
        cooperation_rate=coop_rate,
    )

    self.db.add(strategy)
    self.db.commit()
    self.db.refresh(strategy)

    return strategy


def run_human_ai_tournament(
    self,
    ai_strategy_ids: list[UUID],
    config_strategy_ids: list[UUID],
    turns: int = 100,
    repetitions: int = 10,
    name: str | None = None,
) -> GameTheoryTournament:
    """
    Run tournament mixing AI model strategies with config strategies.

    Tests how AI scheduling assistants behave alongside human-designed
    configuration strategies.

    Args:
        ai_strategy_ids: Strategies created from Bloom evaluations
        config_strategy_ids: Traditional configuration strategies
        turns: Interactions per matchup
        repetitions: Statistical repetitions
        name: Tournament name

    Returns:
        Tournament results including AI vs config comparisons
    """
    # Load all strategies
    ai_strategies = [self.get_strategy(sid) for sid in ai_strategy_ids]
    config_strategies = [self.get_strategy(sid) for sid in config_strategy_ids]

    all_strategies = ai_strategies + config_strategies

    # Create players
    players = []
    for strategy in all_strategies:
        if strategy.is_ai_model:
            # Use BloomAIPlayer for AI models
            player = BloomAIPlayer(
                model_id=strategy.ai_model_id,
                cooperation_rate=strategy.cooperation_rate or 0.5,
                strategy_detected=strategy.strategy_type,
            )
        else:
            # Use ResilienceConfigPlayer for configs
            player = ResilienceConfigPlayer(
                strategy_type=strategy.strategy_type,
                utilization_target=strategy.utilization_target,
            )
        player.name = strategy.name
        players.append(player)

    # Run tournament
    tournament = axl.Tournament(
        players,
        turns=turns,
        repetitions=repetitions,
        seed=42,
    )
    results = tournament.play()

    # Store results with AI vs Config breakdown
    # ... (similar to existing run_tournament but with additional analysis)

    return self._store_tournament_results(
        results,
        all_strategies,
        name or "Human-AI Tournament",
        extra_analysis=self._analyze_ai_vs_config(results, ai_strategies, config_strategies)
    )


def _analyze_ai_vs_config(
    self,
    results: axl.ResultSet,
    ai_strategies: list[ConfigStrategy],
    config_strategies: list[ConfigStrategy],
) -> dict:
    """Analyze how AI models performed against config strategies."""
    ai_names = {s.name for s in ai_strategies}
    config_names = {s.name for s in config_strategies}

    ai_vs_config_scores = []
    ai_vs_ai_scores = []
    config_vs_config_scores = []

    # Extract matchup scores
    for i, name_i in enumerate(results.ranked_names):
        for j, name_j in enumerate(results.ranked_names):
            if i >= j:
                continue
            score = results.payoff_matrix[i][j]

            if name_i in ai_names and name_j in config_names:
                ai_vs_config_scores.append(score)
            elif name_i in ai_names and name_j in ai_names:
                ai_vs_ai_scores.append(score)
            elif name_i in config_names and name_j in config_names:
                config_vs_config_scores.append(score)

    return {
        "ai_vs_config_avg": sum(ai_vs_config_scores) / len(ai_vs_config_scores) if ai_vs_config_scores else 0,
        "ai_vs_ai_avg": sum(ai_vs_ai_scores) / len(ai_vs_ai_scores) if ai_vs_ai_scores else 0,
        "config_vs_config_avg": sum(config_vs_config_scores) / len(config_vs_config_scores) if config_vs_config_scores else 0,
        "ai_dominates_config": results.ranked_names[0] in ai_names,
    }
```

---

## 2. Add Behavioral Signals to SwapAutoMatcher

### Current State

`SwapAutoMatcher` uses preference history, workload balance, and availability to score swap matches. It doesn't consider cooperation patterns.

### Integration: Add PD-Based Scoring

**File:** `backend/app/services/swap_auto_matcher.py`

```python
# Add to MatchingCriteria dataclass

@dataclass
class MatchingCriteria:
    # ... existing fields ...

    # NEW: Prisoner's Dilemma behavioral weights
    pd_cooperation_weight: float = 0.15  # Weight for cooperation history
    pd_reciprocity_weight: float = 0.10  # Weight for reciprocal behavior
    pd_exploitation_penalty: float = 0.20  # Penalty for exploitative patterns


# Add to SwapAutoMatcher class

def _calculate_pd_behavioral_score(
    self,
    faculty_a_id: UUID,
    faculty_b_id: UUID,
) -> tuple[float, str]:
    """
    Calculate behavioral compatibility using Prisoner's Dilemma patterns.

    Analyzes past swap interactions to detect:
    - Mutual cooperation (both honor swaps)
    - Exploitation (one always benefits)
    - Reciprocity (balanced give-and-take)

    Returns:
        (score, explanation) where score is 0-1
    """
    # Get swap history between these two faculty
    shared_history = self._get_shared_swap_history(faculty_a_id, faculty_b_id)

    if not shared_history:
        return (0.5, "No shared history; neutral score")

    # Analyze as iterated PD
    a_cooperations = 0  # A honored commitments to B
    a_defections = 0    # A benefited at B's expense
    b_cooperations = 0
    b_defections = 0

    for swap in shared_history:
        if swap.source_faculty_id == faculty_a_id:
            # A initiated swap with B
            if swap.status == "completed":
                a_cooperations += 1
            elif swap.status == "cancelled_by_source":
                a_defections += 1  # A backed out
        else:
            # B initiated swap with A
            if swap.status == "completed":
                b_cooperations += 1
            elif swap.status == "cancelled_by_source":
                b_defections += 1

    total_interactions = a_cooperations + a_defections + b_cooperations + b_defections
    if total_interactions == 0:
        return (0.5, "No meaningful interactions")

    # Calculate cooperation rates
    a_coop_rate = a_cooperations / (a_cooperations + a_defections) if (a_cooperations + a_defections) > 0 else 0.5
    b_coop_rate = b_cooperations / (b_cooperations + b_defections) if (b_cooperations + b_defections) > 0 else 0.5

    # Mutual cooperation score
    mutual_coop = (a_coop_rate + b_coop_rate) / 2

    # Reciprocity score (balanced relationship)
    reciprocity = 1.0 - abs(a_coop_rate - b_coop_rate)

    # Exploitation penalty (one-sided benefit)
    exploitation = 0.0
    if a_coop_rate > 0.8 and b_coop_rate < 0.3:
        exploitation = 0.5  # B exploits A
    elif b_coop_rate > 0.8 and a_coop_rate < 0.3:
        exploitation = 0.5  # A exploits B

    # Combined score
    score = (
        mutual_coop * 0.5 +
        reciprocity * 0.3 -
        exploitation * 0.2
    )

    # Generate explanation
    if score > 0.7:
        explanation = f"Strong cooperation history ({mutual_coop:.0%} mutual, {reciprocity:.0%} reciprocity)"
    elif exploitation > 0:
        explanation = f"Warning: Exploitation pattern detected"
    else:
        explanation = f"Moderate cooperation ({mutual_coop:.0%})"

    return (max(0, min(1, score)), explanation)


def _detect_strategy_type(
    self,
    faculty_id: UUID,
    lookback_days: int = 180,
) -> str:
    """
    Detect faculty member's swap strategy using PD classifications.

    Returns one of:
    - "cooperator": Always honors swaps
    - "defector": Frequently backs out
    - "tit_for_tat": Reciprocates partner behavior
    - "grudger": Cooperates until betrayed
    - "random": Unpredictable
    """
    swap_history = self._get_faculty_swap_history(faculty_id, lookback_days)

    if len(swap_history) < 5:
        return "unknown"

    completions = sum(1 for s in swap_history if s.status == "completed")
    cancellations = sum(1 for s in swap_history if s.status == "cancelled_by_source")

    completion_rate = completions / len(swap_history)

    # Simple classification
    if completion_rate > 0.9:
        return "cooperator"
    elif completion_rate < 0.3:
        return "defector"
    else:
        # Check for TFT pattern (mirrors partner behavior)
        if self._shows_tft_pattern(faculty_id, swap_history):
            return "tit_for_tat"
        return "mixed"


def suggest_optimal_matches_with_pd_analysis(
    self,
    request_id: UUID,
    top_k: int = 5,
    include_pd_analysis: bool = True,
) -> list[RankedMatch]:
    """
    Suggest matches with Prisoner's Dilemma behavioral analysis.

    Enhanced version of suggest_optimal_matches that includes
    cooperation/defection pattern analysis.
    """
    # Get base matches
    matches = self.suggest_optimal_matches(request_id, top_k * 2)  # Get more to filter

    if not include_pd_analysis:
        return matches[:top_k]

    request = self.db.query(SwapRecord).get(request_id)

    # Enhance with PD scoring
    for match in matches:
        pd_score, pd_explanation = self._calculate_pd_behavioral_score(
            request.source_faculty_id,
            match.match.faculty_b_id,
        )

        # Detect partner's strategy
        partner_strategy = self._detect_strategy_type(match.match.faculty_b_id)

        # Adjust compatibility score
        pd_weight = self.criteria.pd_cooperation_weight
        match.compatibility_score = (
            match.compatibility_score * (1 - pd_weight) +
            pd_score * pd_weight
        )

        # Add to explanation
        match.explanation += f"; PD: {pd_explanation}"

        if partner_strategy == "defector":
            match.compatibility_score *= (1 - self.criteria.pd_exploitation_penalty)
            match.explanation += " (Warning: Partner has defection pattern)"
        elif partner_strategy == "cooperator":
            match.compatibility_score *= 1.1  # Bonus for reliable partners
            match.explanation += " (Reliable partner)"

    # Re-sort by updated scores
    matches.sort(key=lambda m: m.compatibility_score, reverse=True)

    return matches[:top_k]
```

---

## 3. Add PD Metrics to Resilience Health Checks

### Current State

`ResilienceService.check_health()` monitors utilization, redundancy, defense levels, etc. It doesn't include cooperation metrics.

### Integration: Add Cooperation Health Indicators

**File:** `backend/app/resilience/service.py`

```python
# Add to SystemHealthReport dataclass

@dataclass
class SystemHealthReport:
    # ... existing fields ...

    # NEW: Prisoner's Dilemma cooperation metrics
    pd_system_cooperation_rate: float | None = None
    pd_exploitation_alerts: list[str] | None = None
    pd_network_health: str | None = None  # "healthy", "degraded", "toxic"


# Add to ResilienceService class

def check_pd_network_health(self) -> dict:
    """
    Evaluate system health using Prisoner's Dilemma cooperation metrics.

    Analyzes swap network for:
    - Overall cooperation rate (target: >70%)
    - Exploitation patterns (should be <10% of interactions)
    - Reciprocity balance (should be >60%)

    Returns:
        Health report with cooperation metrics and alerts
    """
    # Get recent swap data
    lookback_days = 90
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)

    swaps = self.db.query(SwapRecord).filter(
        SwapRecord.created_at >= cutoff
    ).all()

    if len(swaps) < 10:
        return {
            "status": "insufficient_data",
            "cooperation_rate": None,
            "message": "Not enough swap data for PD analysis"
        }

    # Calculate system-wide cooperation rate
    completed = sum(1 for s in swaps if s.status == "completed")
    cooperation_rate = completed / len(swaps)

    # Detect exploitation patterns
    exploitation_alerts = self._detect_exploitation_patterns(swaps)

    # Check reciprocity balance
    reciprocity_score = self._calculate_network_reciprocity(swaps)

    # Determine overall health
    if cooperation_rate > 0.7 and len(exploitation_alerts) == 0 and reciprocity_score > 0.6:
        network_health = "healthy"
    elif cooperation_rate > 0.5 and len(exploitation_alerts) <= 2:
        network_health = "degraded"
    else:
        network_health = "toxic"

    return {
        "status": network_health,
        "cooperation_rate": cooperation_rate,
        "reciprocity_score": reciprocity_score,
        "exploitation_alerts": exploitation_alerts,
        "recommendations": self._generate_pd_recommendations(
            cooperation_rate, exploitation_alerts, reciprocity_score
        ),
    }


def _detect_exploitation_patterns(self, swaps: list[SwapRecord]) -> list[str]:
    """Detect faculty members who exploit others."""
    alerts = []

    # Group by faculty
    faculty_stats = {}
    for swap in swaps:
        source_id = str(swap.source_faculty_id)
        target_id = str(swap.target_faculty_id) if swap.target_faculty_id else None

        if source_id not in faculty_stats:
            faculty_stats[source_id] = {"initiated": 0, "completed": 0, "received": 0}
        faculty_stats[source_id]["initiated"] += 1
        if swap.status == "completed":
            faculty_stats[source_id]["completed"] += 1

        if target_id:
            if target_id not in faculty_stats:
                faculty_stats[target_id] = {"initiated": 0, "completed": 0, "received": 0}
            faculty_stats[target_id]["received"] += 1

    # Detect exploiters (high receive, low give)
    for fid, stats in faculty_stats.items():
        if stats["initiated"] > 0:
            give_take_ratio = stats["received"] / stats["initiated"]
            if give_take_ratio > 3 and stats["received"] > 5:
                alerts.append(f"Faculty {fid[:8]}... receiving 3x more than giving")

        # Detect defectors (low completion rate)
        if stats["initiated"] > 5:
            completion_rate = stats["completed"] / stats["initiated"]
            if completion_rate < 0.5:
                alerts.append(f"Faculty {fid[:8]}... has <50% completion rate")

    return alerts


def _generate_pd_recommendations(
    self,
    cooperation_rate: float,
    alerts: list[str],
    reciprocity: float,
) -> list[str]:
    """Generate recommendations based on PD health metrics."""
    recommendations = []

    if cooperation_rate < 0.5:
        recommendations.append(
            "CRITICAL: System cooperation rate below 50%. Consider reviewing "
            "swap policies and addressing chronic defectors."
        )
    elif cooperation_rate < 0.7:
        recommendations.append(
            "WARNING: Cooperation rate degraded. Monitor for emerging "
            "exploitation patterns."
        )

    if len(alerts) > 3:
        recommendations.append(
            "Multiple exploitation patterns detected. Consider implementing "
            "reciprocity requirements for swap eligibility."
        )

    if reciprocity < 0.4:
        recommendations.append(
            "Low reciprocity indicates imbalanced swap relationships. "
            "Consider swap matching that enforces balance."
        )

    return recommendations


# Integrate into main health check

def check_health(self, schedule_id: UUID | None = None) -> SystemHealthReport:
    """
    Comprehensive health check including PD metrics.
    """
    # ... existing health checks ...

    # Add PD network health
    pd_health = self.check_pd_network_health()

    report = SystemHealthReport(
        # ... existing fields ...
        pd_system_cooperation_rate=pd_health.get("cooperation_rate"),
        pd_exploitation_alerts=pd_health.get("exploitation_alerts"),
        pd_network_health=pd_health.get("status"),
    )

    return report
```

---

## 4. Add AI Agent Testing Endpoint

### New API Route

**File:** `backend/app/api/routes/game_theory.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/game-theory", tags=["Game Theory"])


class BloomEvaluationInput(BaseModel):
    """Input from Bloom evaluation of an AI model."""
    model_id: str
    cooperation_rate: float
    strategy_detected: str
    avg_cooperation_score: float
    scenarios_evaluated: int
    evaluation_id: str | None = None


class AITournamentRequest(BaseModel):
    """Request to run AI vs Config tournament."""
    ai_model_evaluations: list[BloomEvaluationInput]
    config_strategy_ids: list[str]
    turns: int = 100
    repetitions: int = 10
    name: str | None = None


@router.post("/ai-strategies/from-bloom")
async def create_strategy_from_bloom(
    evaluation: BloomEvaluationInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a ConfigStrategy from Bloom evaluation results.

    This allows AI models to participate in tournaments alongside
    traditional configuration strategies.
    """
    service = GameTheoryService(db)

    strategy = service.create_ai_strategy_from_bloom(
        model_id=evaluation.model_id,
        bloom_results={
            "cooperation_rate": evaluation.cooperation_rate,
            "strategy_detected": evaluation.strategy_detected,
            "avg_cooperation_score": evaluation.avg_cooperation_score,
            "scenarios_evaluated": evaluation.scenarios_evaluated,
            "evaluation_id": evaluation.evaluation_id,
        },
        created_by=str(current_user.id),
    )

    return {
        "strategy_id": str(strategy.id),
        "name": strategy.name,
        "strategy_type": strategy.strategy_type,
        "message": f"Created AI strategy from Bloom evaluation of {evaluation.model_id}",
    }


@router.post("/tournaments/human-ai")
async def run_human_ai_tournament(
    request: AITournamentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run tournament mixing AI models with configuration strategies.

    Tests how AI scheduling assistants behave alongside human-designed
    configuration strategies.
    """
    service = GameTheoryService(db)

    # Create AI strategies from evaluations
    ai_strategy_ids = []
    for eval_input in request.ai_model_evaluations:
        strategy = service.create_ai_strategy_from_bloom(
            model_id=eval_input.model_id,
            bloom_results={
                "cooperation_rate": eval_input.cooperation_rate,
                "strategy_detected": eval_input.strategy_detected,
            },
            created_by=str(current_user.id),
        )
        ai_strategy_ids.append(strategy.id)

    # Run tournament
    config_ids = [UUID(sid) for sid in request.config_strategy_ids]

    tournament = service.run_human_ai_tournament(
        ai_strategy_ids=ai_strategy_ids,
        config_strategy_ids=config_ids,
        turns=request.turns,
        repetitions=request.repetitions,
        name=request.name,
    )

    return {
        "tournament_id": str(tournament.id),
        "status": tournament.status,
        "ai_vs_config_analysis": tournament.extra_analysis,
    }


@router.get("/health/pd-network")
async def get_pd_network_health(
    db: Session = Depends(get_db),
):
    """
    Get Prisoner's Dilemma cooperation health metrics for the swap network.

    Returns:
    - System cooperation rate
    - Exploitation alerts
    - Network health status
    - Recommendations
    """
    from app.resilience.service import ResilienceService

    service = ResilienceService(db)
    health = service.check_pd_network_health()

    return health
```

---

## 5. Database Model Updates

**File:** `backend/app/models/game_theory.py`

```python
# Add to ConfigStrategy model

class ConfigStrategy(Base):
    __tablename__ = "config_strategies"

    # ... existing columns ...

    # NEW: AI model fields
    is_ai_model = Column(Boolean, default=False)
    ai_model_id = Column(String, nullable=True)  # e.g., "claude-3-5-sonnet"
    bloom_evaluation_id = Column(String, nullable=True)  # Reference to Bloom run
    cooperation_rate = Column(Float, nullable=True)  # Measured from Bloom
    scenarios_evaluated = Column(Integer, nullable=True)
```

**Migration:** `backend/alembic/versions/xxx_add_ai_model_fields.py`

```python
def upgrade():
    op.add_column('config_strategies', sa.Column('is_ai_model', sa.Boolean(), default=False))
    op.add_column('config_strategies', sa.Column('ai_model_id', sa.String(), nullable=True))
    op.add_column('config_strategies', sa.Column('bloom_evaluation_id', sa.String(), nullable=True))
    op.add_column('config_strategies', sa.Column('cooperation_rate', sa.Float(), nullable=True))
    op.add_column('config_strategies', sa.Column('scenarios_evaluated', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('config_strategies', 'scenarios_evaluated')
    op.drop_column('config_strategies', 'cooperation_rate')
    op.drop_column('config_strategies', 'bloom_evaluation_id')
    op.drop_column('config_strategies', 'ai_model_id')
    op.drop_column('config_strategies', 'is_ai_model')
```

---

## 6. Usage Flow

### Step 1: Run Bloom Evaluation

```bash
# In Bloom repository
python bloom.py --seed seeds/scheduling_cooperation.yaml --target claude-3-5-sonnet
```

### Step 2: Import Results to Scheduler

```python
# POST /api/game-theory/ai-strategies/from-bloom
{
    "model_id": "claude-3-5-sonnet-20241022",
    "cooperation_rate": 0.78,
    "strategy_detected": "forgiving_tft",
    "avg_cooperation_score": 7.2,
    "scenarios_evaluated": 100,
    "evaluation_id": "bloom-run-abc123"
}
```

### Step 3: Run Human-AI Tournament

```python
# POST /api/game-theory/tournaments/human-ai
{
    "ai_model_evaluations": [
        {"model_id": "claude-3-5-sonnet", "cooperation_rate": 0.78, ...},
        {"model_id": "gpt-4-turbo", "cooperation_rate": 0.65, ...}
    ],
    "config_strategy_ids": ["uuid-conservative", "uuid-moderate", "uuid-aggressive"],
    "turns": 200,
    "repetitions": 50
}
```

### Step 4: Monitor PD Network Health

```python
# GET /api/game-theory/health/pd-network
# Returns:
{
    "status": "healthy",
    "cooperation_rate": 0.73,
    "reciprocity_score": 0.65,
    "exploitation_alerts": [],
    "recommendations": []
}
```

---

## Summary

| Integration | File | Purpose |
|-------------|------|---------|
| `BloomAIPlayer` | `game_theory.py` | AI models in tournaments |
| `create_ai_strategy_from_bloom` | `game_theory.py` | Import Bloom results |
| `_calculate_pd_behavioral_score` | `swap_auto_matcher.py` | PD scoring for swaps |
| `check_pd_network_health` | `resilience/service.py` | Cooperation health metrics |
| `/ai-strategies/from-bloom` | `routes/game_theory.py` | API for Bloom import |
| `/health/pd-network` | `routes/game_theory.py` | PD health endpoint |

This integration allows:
1. Testing AI scheduling assistants before deployment
2. Detecting cooperation/defection patterns in faculty behavior
3. Monitoring system health using game theory metrics
4. Comparing AI models against proven configuration strategies
