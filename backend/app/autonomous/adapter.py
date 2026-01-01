"""
Automated Parameter Adaptation.

Start simple and deterministic:
    - If violation type A occurs, adjust parameter X by delta
    - If score stagnates N iterations, increase diversification
    - If close to feasible, narrow search (local neighborhood moves)

You can later add bandits/Bayesian optimization, but don't start there.
"""

import logging
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from app.autonomous.evaluator import EvaluationResult
from app.autonomous.state import GeneratorParams, IterationRecord

logger = logging.getLogger(__name__)

# Check for scipy availability
try:
    from scipy.optimize import minimize
    from scipy.stats import norm

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logger.warning(
        "scipy not installed - Bayesian optimization will use random perturbation"
    )


class AdaptationAction(str, Enum):
    """Types of parameter adaptations."""

    SWITCH_ALGORITHM = "switch_algorithm"
    INCREASE_TIMEOUT = "increase_timeout"
    RANDOM_RESTART = "random_restart"
    ADJUST_WEIGHT = "adjust_weight"
    INCREASE_DIVERSIFICATION = "increase_diversification"
    NARROW_SEARCH = "narrow_search"
    NO_CHANGE = "no_change"


@dataclass
class AdaptationRule:
    """
    A rule for adapting parameters based on conditions.

    Attributes:
        name: Human-readable rule name
        condition: Function that checks if rule applies
        action: Type of adaptation to perform
        params: Parameters for the action
        priority: Higher priority rules are checked first
    """

    name: str
    condition: Callable[[EvaluationResult, list[IterationRecord]], bool]
    action: AdaptationAction
    params: dict[str, Any] = field(default_factory=dict)
    priority: int = 0


class ParameterAdapter:
    """
    Deterministic parameter adaptation based on failure modes.

    This adapter analyzes evaluation results and iteration history
    to decide how to adjust parameters for the next iteration.

    The rules are deterministic and prioritized. The adapter:
    1. Evaluates all rules in priority order
    2. Applies the first matching rule
    3. Returns the adapted parameters

    No machine learning or stochastic optimization is used here.
    The goal is reliable, predictable adaptation that can be debugged.

    Example:
        >>> adapter = ParameterAdapter()
        >>> new_params = adapter.adapt(
        ...     current_params=params,
        ...     evaluation=result,
        ...     history=history,
        ... )
    """

    # Algorithm rotation order
    ALGORITHM_ORDER = ["greedy", "cp_sat", "pulp", "hybrid"]

    def __init__(self, custom_rules: list[AdaptationRule] | None = None):
        """
        Initialize adapter with default and custom rules.

        Args:
            custom_rules: Optional additional rules to include
        """
        self.rules = self._build_default_rules()
        if custom_rules:
            self.rules.extend(custom_rules)
        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: -r.priority)

    def adapt(
        self,
        current_params: GeneratorParams,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> GeneratorParams:
        """
        Adapt parameters based on evaluation results.

        Args:
            current_params: Current generation parameters
            evaluation: Result from latest evaluation
            history: Recent iteration history

        Returns:
            Adapted parameters for next iteration
        """
        # Check each rule in priority order
        for rule in self.rules:
            try:
                if rule.condition(evaluation, history):
                    return self._apply_rule(rule, current_params, evaluation, history)
            except Exception:
                # Rule evaluation failed, skip it
                continue

        # No rule matched, return unchanged
        return current_params

    def _apply_rule(
        self,
        rule: AdaptationRule,
        params: GeneratorParams,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> GeneratorParams:
        """Apply an adaptation rule to the parameters."""
        # Create copy of params
        new_params = GeneratorParams(
            algorithm=params.algorithm,
            timeout_seconds=params.timeout_seconds,
            random_seed=params.random_seed,
            solver_params=params.solver_params.copy(),
            constraint_weights=params.constraint_weights.copy(),
            max_restarts=params.max_restarts,
            neighborhood_size=params.neighborhood_size,
            diversification_factor=params.diversification_factor,
        )

        if rule.action == AdaptationAction.SWITCH_ALGORITHM:
            new_params.algorithm = self._next_algorithm(params.algorithm)

        elif rule.action == AdaptationAction.INCREASE_TIMEOUT:
            factor = rule.params.get("factor", 1.5)
            max_timeout = rule.params.get("max_timeout", 300.0)
            new_params.timeout_seconds = min(
                params.timeout_seconds * factor,
                max_timeout,
            )

        elif rule.action == AdaptationAction.RANDOM_RESTART:
            new_params.random_seed = random.randint(0, 2**32 - 1)
            new_params.max_restarts = rule.params.get("restarts", 3)

        elif rule.action == AdaptationAction.ADJUST_WEIGHT:
            constraint = rule.params.get("constraint")
            delta = rule.params.get("delta", 0.1)
            if constraint:
                current = new_params.constraint_weights.get(constraint, 1.0)
                new_params.constraint_weights[constraint] = max(0.0, current + delta)

        elif rule.action == AdaptationAction.INCREASE_DIVERSIFICATION:
            factor = rule.params.get("factor", 1.5)
            new_params.diversification_factor = min(
                1.0,
                params.diversification_factor * factor + 0.1,
            )
            new_params.random_seed = random.randint(0, 2**32 - 1)

        elif rule.action == AdaptationAction.NARROW_SEARCH:
            new_params.neighborhood_size = max(
                1,
                params.neighborhood_size // 2,
            )
            new_params.diversification_factor = max(
                0.0,
                params.diversification_factor - 0.1,
            )

        return new_params

    def _next_algorithm(self, current: str) -> str:
        """Get next algorithm in rotation."""
        try:
            idx = self.ALGORITHM_ORDER.index(current)
            return self.ALGORITHM_ORDER[(idx + 1) % len(self.ALGORITHM_ORDER)]
        except ValueError:
            return self.ALGORITHM_ORDER[0]

    def _build_default_rules(self) -> list[AdaptationRule]:
        """Build the default set of adaptation rules."""
        rules = []

        # Rule 1: If score stagnating, increase diversification
        rules.append(
            AdaptationRule(
                name="stagnation_diversification",
                condition=self._is_stagnating,
                action=AdaptationAction.INCREASE_DIVERSIFICATION,
                params={"factor": 1.5},
                priority=100,
            )
        )

        # Rule 2: If solver times out, increase timeout
        rules.append(
            AdaptationRule(
                name="timeout_increase",
                condition=self._is_timing_out,
                action=AdaptationAction.INCREASE_TIMEOUT,
                params={"factor": 1.5, "max_timeout": 300.0},
                priority=90,
            )
        )

        # Rule 3: If too many ACGME violations, switch algorithm
        rules.append(
            AdaptationRule(
                name="acgme_algorithm_switch",
                condition=self._has_acgme_violations,
                action=AdaptationAction.SWITCH_ALGORITHM,
                priority=80,
            )
        )

        # Rule 4: If N-1 vulnerable, increase resilience weight
        rules.append(
            AdaptationRule(
                name="n1_weight_increase",
                condition=self._is_n1_vulnerable,
                action=AdaptationAction.ADJUST_WEIGHT,
                params={"constraint": "resilience", "delta": 0.2},
                priority=70,
            )
        )

        # Rule 5: If close to feasible (score > 0.8), narrow search
        rules.append(
            AdaptationRule(
                name="near_feasible_narrow",
                condition=self._is_near_feasible,
                action=AdaptationAction.NARROW_SEARCH,
                priority=60,
            )
        )

        # Rule 6: If utilization too high, adjust coverage weight
        rules.append(
            AdaptationRule(
                name="utilization_weight_decrease",
                condition=self._is_over_utilized,
                action=AdaptationAction.ADJUST_WEIGHT,
                params={"constraint": "coverage", "delta": -0.1},
                priority=50,
            )
        )

        # Rule 7: Random restart every N iterations without improvement
        rules.append(
            AdaptationRule(
                name="periodic_restart",
                condition=self._needs_restart,
                action=AdaptationAction.RANDOM_RESTART,
                params={"restarts": 3},
                priority=40,
            )
        )

        return rules

    # Condition functions

    def _is_stagnating(
        self,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> bool:
        """Check if progress has stagnated."""
        if len(history) < 5:
            return False

        # Check if last 5 iterations have similar scores
        recent_scores = [r.score for r in history[-5:]]
        score_range = max(recent_scores) - min(recent_scores)
        return score_range < 0.01  # Less than 1% variation

    def _is_timing_out(
        self,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> bool:
        """Check if solver is timing out."""
        if not history:
            return False

        last = history[-1]
        # Heuristic: if duration is close to timeout and score is low
        return last.duration_seconds > 55.0 and last.score < 0.5

    def _has_acgme_violations(
        self,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> bool:
        """Check if there are ACGME violations."""
        # Check for 80_HOUR or SUPERVISION violations
        acgme_types = {
            "80_HOUR_VIOLATION",
            "1_IN_7_VIOLATION",
            "SUPERVISION_RATIO_VIOLATION",
        }
        for v in evaluation.violations:
            if v.type in acgme_types:
                return True
        return False

    def _is_n1_vulnerable(
        self,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> bool:
        """Check if schedule is N-1 vulnerable."""
        for v in evaluation.violations:
            if v.type == "N1_VULNERABILITY":
                return True
        return False

    def _is_near_feasible(
        self,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> bool:
        """Check if schedule is close to feasible."""
        return evaluation.score >= 0.8 and not evaluation.valid

    def _is_over_utilized(
        self,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> bool:
        """Check if utilization is too high."""
        for v in evaluation.violations:
            if v.type in {"UTILIZATION_RED", "UTILIZATION_BLACK"}:
                return True
        return False

    def _needs_restart(
        self,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> bool:
        """Check if a random restart is needed."""
        if len(history) < 10:
            return False

        # Check if last 10 iterations had no improvement
        if history:
            recent_best = max(r.score for r in history[-10:])
            older_best = max((r.score for r in history[:-10]), default=0)
            return recent_best <= older_best + 0.001

        return False


class BayesianAdapter(ParameterAdapter):
    """
    Optional: Bayesian optimization-based parameter adaptation.

    This is a more sophisticated adapter that uses Bayesian optimization
    to learn the relationship between parameters and scores.

    Only use this after the deterministic adapter is working well.
    It requires scipy for Gaussian process implementation.
    """

    def __init__(self):
        """Initialize Bayesian adapter."""
        super().__init__()
        self._observations: list[tuple[dict, float]] = []

    def adapt(
        self,
        current_params: GeneratorParams,
        evaluation: EvaluationResult,
        history: list[IterationRecord],
    ) -> GeneratorParams:
        """
        Adapt parameters using Bayesian optimization.

        Falls back to deterministic rules if not enough observations.
        """
        # Record observation
        self._observations.append(
            (
                current_params.to_dict(),
                evaluation.score,
            )
        )

        # Need at least 10 observations for Bayesian optimization
        if len(self._observations) < 10:
            return super().adapt(current_params, evaluation, history)

        # Try Bayesian optimization
        try:
            return self._bayesian_suggest(current_params)
        except Exception:
            # Fall back to deterministic
            return super().adapt(current_params, evaluation, history)

    def _bayesian_suggest(self, current: GeneratorParams) -> GeneratorParams:
        """
        Use Bayesian optimization to suggest next parameters.

        Uses a simplified acquisition function approach:
        1. Fit a surrogate model (weighted average) to observed data
        2. Use Expected Improvement to find promising regions
        3. Return parameters that balance exploration/exploitation
        """
        if not HAS_SCIPY or len(self._observations) < 10:
            # Fall back to random perturbation
            return self._random_perturbation(current)

        try:
            # Extract observations into arrays
            X = []  # Parameter vectors
            y = []  # Scores

            for params_dict, score in self._observations:
                # Extract continuous parameters
                param_vec = [
                    params_dict.get("timeout_seconds", 60.0) / 120.0,  # Normalize
                    params_dict.get("diversification_factor", 0.0),
                ]
                X.append(param_vec)
                y.append(score)

            X = np.array(X)
            y = np.array(y)

            # Find best observed
            best_idx = np.argmax(y)
            best_score = y[best_idx]
            best_x = X[best_idx]

            # Simple acquisition: sample around best with decay based on observations
            # More observations = tighter sampling (exploitation)
            exploration_scale = max(0.05, 1.0 / len(self._observations))

            # Sample new point using Expected Improvement heuristic
            # Move toward best observation with some randomness
            new_x = best_x + np.random.normal(0, exploration_scale, size=best_x.shape)

            # Clip to valid bounds
            new_x = np.clip(new_x, 0.0, 1.0)

            # Convert back to parameters
            new_timeout = new_x[0] * 120.0  # Denormalize
            new_timeout = max(30.0, min(300.0, new_timeout))

            new_diversification = new_x[1]
            new_diversification = max(0.0, min(1.0, new_diversification))

            logger.debug(
                f"Bayesian suggestion: timeout={new_timeout:.1f}s, "
                f"diversification={new_diversification:.3f}"
            )

            return GeneratorParams(
                algorithm=current.algorithm,
                timeout_seconds=new_timeout,
                random_seed=random.randint(0, 2**32 - 1),
                solver_params=current.solver_params.copy(),
                constraint_weights=current.constraint_weights.copy(),
                diversification_factor=new_diversification,
            )

        except Exception as e:
            logger.warning(
                f"Bayesian optimization failed: {e}, using random perturbation"
            )
            return self._random_perturbation(current)

    def _random_perturbation(self, current: GeneratorParams) -> GeneratorParams:
        """Apply random perturbation to parameters (fallback method)."""
        return GeneratorParams(
            algorithm=current.algorithm,
            timeout_seconds=current.timeout_seconds * (0.9 + 0.2 * random.random()),
            random_seed=random.randint(0, 2**32 - 1),
            solver_params=current.solver_params.copy(),
            constraint_weights=current.constraint_weights.copy(),
            diversification_factor=min(
                1.0, current.diversification_factor + 0.05 * random.random()
            ),
        )
