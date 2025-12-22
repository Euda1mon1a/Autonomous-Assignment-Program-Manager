"""
Tests for the automated parameter adaptation.
"""

import pytest
from datetime import datetime

from app.autonomous.adapter import (
    ParameterAdapter,
    AdaptationRule,
    AdaptationAction,
)
from app.autonomous.evaluator import (
    EvaluationResult,
    ViolationDetail,
    ViolationSeverity,
)
from app.autonomous.state import GeneratorParams, IterationRecord


def make_result(
    score: float = 0.5,
    valid: bool = False,
    violations: list[ViolationDetail] | None = None,
) -> EvaluationResult:
    """Helper to create evaluation results for testing."""
    return EvaluationResult(
        valid=valid,
        score=score,
        hard_constraint_pass=valid,
        soft_score=score * 0.6,
        coverage_rate=0.8,
        total_violations=len(violations) if violations else 0,
        critical_violations=sum(
            1 for v in (violations or [])
            if v.severity == ViolationSeverity.CRITICAL
        ),
        violations=violations or [],
    )


def make_history(
    scores: list[float],
    valid: bool = True,
    algorithm: str = "greedy",
) -> list[IterationRecord]:
    """Helper to create iteration history for testing."""
    return [
        IterationRecord(
            iteration=i,
            timestamp=datetime.now(),
            params=GeneratorParams(algorithm=algorithm),
            score=score,
            valid=valid,
            critical_violations=0,
            total_violations=0,
            violation_types=[],
            duration_seconds=30.0,
        )
        for i, score in enumerate(scores)
    ]


class TestParameterAdapter:
    """Tests for ParameterAdapter."""

    def test_no_change_on_empty_history(self):
        """Test that adapter makes no change with empty history."""
        adapter = ParameterAdapter()
        params = GeneratorParams(algorithm="greedy")
        result = make_result(score=0.5)
        history = []

        new_params = adapter.adapt(params, result, history)

        # Should return unchanged or with algorithm switch for ACGME
        assert new_params.algorithm in ["greedy", "cp_sat"]

    def test_switch_algorithm_on_acgme_violation(self):
        """Test algorithm switch when ACGME violation occurs."""
        adapter = ParameterAdapter()
        params = GeneratorParams(algorithm="greedy")
        result = make_result(
            score=0.4,
            violations=[
                ViolationDetail(
                    type="80_HOUR_VIOLATION",
                    severity=ViolationSeverity.CRITICAL,
                    message="Exceeded 80 hours",
                )
            ],
        )
        history = []

        new_params = adapter.adapt(params, result, history)

        assert new_params.algorithm == "cp_sat"  # Switched from greedy

    def test_algorithm_rotation(self):
        """Test that algorithm switches rotate through all options."""
        adapter = ParameterAdapter()

        # Start with greedy
        assert adapter._next_algorithm("greedy") == "cp_sat"
        assert adapter._next_algorithm("cp_sat") == "pulp"
        assert adapter._next_algorithm("pulp") == "hybrid"
        assert adapter._next_algorithm("hybrid") == "greedy"  # Wraps around

    def test_diversification_on_stagnation(self):
        """Test that diversification increases on stagnation."""
        adapter = ParameterAdapter()
        params = GeneratorParams(
            algorithm="greedy",
            diversification_factor=0.0,
        )
        result = make_result(score=0.7)
        # 5 iterations with similar scores = stagnation
        history = make_history([0.70, 0.70, 0.70, 0.70, 0.70])

        new_params = adapter.adapt(params, result, history)

        assert new_params.diversification_factor > 0.0

    def test_timeout_increase_on_slow_run(self):
        """Test that timeout increases when solver times out."""
        adapter = ParameterAdapter()
        params = GeneratorParams(
            algorithm="cp_sat",
            timeout_seconds=60.0,
        )
        result = make_result(score=0.3)
        # History with long duration and low score
        history = [
            IterationRecord(
                iteration=0,
                timestamp=datetime.now(),
                params=params,
                score=0.3,
                valid=False,
                critical_violations=0,
                total_violations=0,
                violation_types=[],
                duration_seconds=58.0,  # Close to timeout
            )
        ]

        new_params = adapter.adapt(params, result, history)

        assert new_params.timeout_seconds > 60.0

    def test_n1_weight_increase(self):
        """Test that resilience weight increases on N-1 vulnerability."""
        adapter = ParameterAdapter()
        params = GeneratorParams(algorithm="greedy")
        result = make_result(
            score=0.7,
            violations=[
                ViolationDetail(
                    type="N1_VULNERABILITY",
                    severity=ViolationSeverity.HIGH,
                    message="N-1 vulnerable",
                )
            ],
        )
        history = []

        new_params = adapter.adapt(params, result, history)

        assert "resilience" in new_params.constraint_weights
        assert new_params.constraint_weights["resilience"] > 1.0

    def test_narrow_search_near_feasible(self):
        """Test that search narrows when close to feasible."""
        adapter = ParameterAdapter()
        params = GeneratorParams(
            algorithm="greedy",
            neighborhood_size=10,
            diversification_factor=0.5,
        )
        result = make_result(score=0.85, valid=False)  # Close but not valid
        history = []

        new_params = adapter.adapt(params, result, history)

        assert new_params.neighborhood_size < 10
        assert new_params.diversification_factor < 0.5


class TestAdaptationRule:
    """Tests for individual adaptation rules."""

    def test_custom_rule(self):
        """Test adding custom rules."""
        # Custom rule that always triggers
        custom_rule = AdaptationRule(
            name="always_switch",
            condition=lambda e, h: True,
            action=AdaptationAction.SWITCH_ALGORITHM,
            priority=1000,  # High priority
        )

        adapter = ParameterAdapter(custom_rules=[custom_rule])
        params = GeneratorParams(algorithm="greedy")
        result = make_result(score=0.9, valid=True)  # Good result
        history = []

        new_params = adapter.adapt(params, result, history)

        # Custom rule should trigger despite good result
        assert new_params.algorithm == "cp_sat"

    def test_rule_priority_ordering(self):
        """Test that higher priority rules are checked first."""
        # Low priority rule that switches algorithm
        low_priority = AdaptationRule(
            name="low_priority",
            condition=lambda e, h: True,
            action=AdaptationAction.SWITCH_ALGORITHM,
            priority=1,
        )

        # High priority rule that increases timeout
        high_priority = AdaptationRule(
            name="high_priority",
            condition=lambda e, h: True,
            action=AdaptationAction.INCREASE_TIMEOUT,
            params={"factor": 2.0},
            priority=100,
        )

        adapter = ParameterAdapter(custom_rules=[low_priority, high_priority])
        params = GeneratorParams(algorithm="greedy", timeout_seconds=60.0)
        result = make_result()
        history = []

        new_params = adapter.adapt(params, result, history)

        # High priority should win - timeout should increase
        assert new_params.timeout_seconds == 120.0
        assert new_params.algorithm == "greedy"  # Unchanged


class TestConditionFunctions:
    """Tests for built-in condition functions."""

    def test_is_stagnating_false_short_history(self):
        """Test stagnation detection with short history."""
        adapter = ParameterAdapter()

        result = make_result(score=0.7)
        history = make_history([0.7, 0.7, 0.7])  # Only 3 iterations

        assert adapter._is_stagnating(result, history) is False

    def test_is_stagnating_true(self):
        """Test stagnation detection with flat scores."""
        adapter = ParameterAdapter()

        result = make_result(score=0.7)
        history = make_history([0.70, 0.70, 0.70, 0.70, 0.70])

        assert adapter._is_stagnating(result, history) is True

    def test_is_stagnating_false_improving(self):
        """Test stagnation detection with improving scores."""
        adapter = ParameterAdapter()

        result = make_result(score=0.75)
        history = make_history([0.70, 0.71, 0.72, 0.73, 0.74])

        assert adapter._is_stagnating(result, history) is False

    def test_is_near_feasible(self):
        """Test near-feasible detection."""
        adapter = ParameterAdapter()

        # High score but not valid = near feasible
        result = make_result(score=0.85, valid=False)
        history = []

        assert adapter._is_near_feasible(result, history) is True

        # Low score = not near feasible
        result = make_result(score=0.5, valid=False)
        assert adapter._is_near_feasible(result, history) is False

        # Valid = not "near" feasible (already there)
        result = make_result(score=0.85, valid=True)
        assert adapter._is_near_feasible(result, history) is False
