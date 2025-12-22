"""
Autonomous Scheduling Loop.

This package implements a fully autonomous scheduling control loop where
Python owns the decision-making and the LLM is demoted to an advisory role.

Architecture (8-Point System):
    1. Headless entrypoint - Can run without human interaction
    2. Strict evaluator - Deterministic scoring for constraints
    3. Run state store - Persistence across iterations
    4. Candidate generator - Unified interface to solver stack
    5. Control loop - Core automation owning decisions
    6. Parameter adaptation - Deterministic rules for improvement
    7. LLM advisor - Validated suggestions, can continue without
    8. N-1 test harness - Adversarial scenario generation

Key Principles:
    - Python is authoritative, LLM is advisory
    - Deterministic scoring enables self-improvement
    - Persistence enables learning across runs
    - Loop can run to completion without human intervention

Usage:
    >>> from app.autonomous import AutonomousLoop
    >>> loop = AutonomousLoop.from_config(scenario="baseline")
    >>> result = loop.run(max_iterations=200)
    >>> print(result.best_score)

    Or via CLI:
    $ python -m app.autonomous.cli --scenario baseline --max-iters 200
"""

from app.autonomous.evaluator import (
    ScheduleEvaluator,
    EvaluationResult,
    ViolationDetail,
)
from app.autonomous.state import (
    RunState,
    StateStore,
    IterationRecord,
)
from app.autonomous.generator import (
    CandidateGenerator,
    GeneratorConfig,
    ScheduleCandidate,
)
from app.autonomous.loop import (
    AutonomousLoop,
    LoopConfig,
    LoopResult,
    StopReason,
)
from app.autonomous.adapter import (
    ParameterAdapter,
    AdaptationRule,
)
from app.autonomous.advisor import (
    LLMAdvisor,
    Suggestion,
    SuggestionType,
)
from app.autonomous.harness import (
    ResilienceHarness,
    AdversarialScenario,
    ScenarioResult,
)

__all__ = [
    # Evaluator
    "ScheduleEvaluator",
    "EvaluationResult",
    "ViolationDetail",
    # State
    "RunState",
    "StateStore",
    "IterationRecord",
    # Generator
    "CandidateGenerator",
    "GeneratorConfig",
    "ScheduleCandidate",
    # Loop
    "AutonomousLoop",
    "LoopConfig",
    "LoopResult",
    "StopReason",
    # Adapter
    "ParameterAdapter",
    "AdaptationRule",
    # Advisor
    "LLMAdvisor",
    "Suggestion",
    "SuggestionType",
    # Harness
    "ResilienceHarness",
    "AdversarialScenario",
    "ScenarioResult",
]
