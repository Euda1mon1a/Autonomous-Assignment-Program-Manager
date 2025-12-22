"""
Tests for the LLM advisor interface with schema validation.
"""

import pytest
from datetime import date, datetime

from app.autonomous.advisor import (
    LLMAdvisor,
    MockLLMAdvisor,
    Suggestion,
    SuggestionType,
    SuggestionSchema,
)
from app.autonomous.evaluator import (
    EvaluationResult,
    ViolationDetail,
    ViolationSeverity,
)
from app.autonomous.state import RunState, GeneratorParams, IterationRecord


class TestSuggestionSchema:
    """Tests for SuggestionSchema validation."""

    def test_valid_algorithm(self):
        """Test validation of valid algorithms."""
        params = {"algorithm": "cp_sat"}
        is_valid, error = SuggestionSchema.validate_params(params)

        assert is_valid is True
        assert error == ""

    def test_invalid_algorithm(self):
        """Test rejection of invalid algorithms."""
        params = {"algorithm": "invalid_solver"}
        is_valid, error = SuggestionSchema.validate_params(params)

        assert is_valid is False
        assert "Invalid algorithm" in error

    def test_timeout_in_range(self):
        """Test validation of timeout in valid range."""
        params = {"timeout_seconds": 120.0}
        is_valid, error = SuggestionSchema.validate_params(params)

        assert is_valid is True

    def test_timeout_too_low(self):
        """Test rejection of timeout below minimum."""
        params = {"timeout_seconds": 5.0}  # Below 10s minimum
        is_valid, error = SuggestionSchema.validate_params(params)

        assert is_valid is False
        assert "Timeout" in error

    def test_timeout_too_high(self):
        """Test rejection of timeout above maximum."""
        params = {"timeout_seconds": 1000.0}  # Above 600s maximum
        is_valid, error = SuggestionSchema.validate_params(params)

        assert is_valid is False
        assert "Timeout" in error

    def test_valid_constraint_weights(self):
        """Test validation of constraint weights."""
        params = {
            "constraint_weights": {
                "coverage_rate": 1.5,
                "resilience": 0.5,
            }
        }
        is_valid, error = SuggestionSchema.validate_params(params)

        assert is_valid is True

    def test_unknown_constraint(self):
        """Test rejection of unknown constraint names."""
        params = {
            "constraint_weights": {
                "unknown_constraint": 1.0,
            }
        }
        is_valid, error = SuggestionSchema.validate_params(params)

        assert is_valid is False
        assert "Unknown constraint" in error

    def test_weight_out_of_range(self):
        """Test rejection of weights outside valid range."""
        params = {
            "constraint_weights": {
                "coverage_rate": 5.0,  # Above 2.0 max
            }
        }
        is_valid, error = SuggestionSchema.validate_params(params)

        assert is_valid is False
        assert "out of range" in error


class TestSuggestion:
    """Tests for Suggestion dataclass."""

    def test_create_suggestion(self):
        """Test creating a suggestion."""
        suggestion = Suggestion(
            type=SuggestionType.ALGORITHM_SWITCH,
            confidence=0.8,
            reasoning="Trying a different solver",
            params=GeneratorParams(algorithm="cp_sat"),
        )

        assert suggestion.type == SuggestionType.ALGORITHM_SWITCH
        assert suggestion.confidence == 0.8
        assert suggestion.params.algorithm == "cp_sat"

    def test_to_dict(self):
        """Test JSON serialization."""
        suggestion = Suggestion(
            type=SuggestionType.PARAMETER_CHANGE,
            confidence=0.7,
            reasoning="Increase timeout",
            params=GeneratorParams(timeout_seconds=120.0),
        )

        data = suggestion.to_dict()

        assert data["type"] == "parameter_change"
        assert data["confidence"] == 0.7
        assert data["params"]["timeout_seconds"] == 120.0


class TestLLMAdvisor:
    """Tests for LLMAdvisor without real LLM."""

    def test_no_client_returns_none(self):
        """Test that advisor returns None without LLM client."""
        advisor = LLMAdvisor(llm_client=None)

        state = RunState(
            run_id="test",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        suggestion = advisor.suggest(state, None, [])

        assert suggestion is None

    def test_validate_suggestion_low_confidence(self):
        """Test that low confidence suggestions are rejected."""
        advisor = LLMAdvisor()

        suggestion = Suggestion(
            type=SuggestionType.PARAMETER_CHANGE,
            confidence=0.2,  # Below 0.3 threshold
            reasoning="Not very sure",
        )

        assert advisor.validate_suggestion(suggestion) is False

    def test_validate_suggestion_no_reasoning(self):
        """Test that suggestions without reasoning are rejected."""
        advisor = LLMAdvisor()

        suggestion = Suggestion(
            type=SuggestionType.PARAMETER_CHANGE,
            confidence=0.8,
            reasoning="",  # Empty reasoning
        )

        assert advisor.validate_suggestion(suggestion) is False

    def test_validate_suggestion_invalid_params(self):
        """Test that suggestions with invalid params are rejected."""
        advisor = LLMAdvisor()

        suggestion = Suggestion(
            type=SuggestionType.PARAMETER_CHANGE,
            confidence=0.8,
            reasoning="Valid reasoning",
            params=GeneratorParams(algorithm="invalid_solver"),
        )

        # The params contain an invalid algorithm
        # But GeneratorParams doesn't validate itself, so we need to
        # check via the schema
        assert advisor.validate_suggestion(suggestion) is False

    def test_validate_suggestion_valid(self):
        """Test that valid suggestions are accepted."""
        advisor = LLMAdvisor()

        suggestion = Suggestion(
            type=SuggestionType.ALGORITHM_SWITCH,
            confidence=0.8,
            reasoning="Switching to CP-SAT for better constraint handling",
            params=GeneratorParams(algorithm="cp_sat"),
        )

        assert advisor.validate_suggestion(suggestion) is True

    def test_fallback_explanation(self):
        """Test fallback explanation without LLM."""
        advisor = LLMAdvisor()

        result = EvaluationResult(
            valid=False,
            score=0.7,
            hard_constraint_pass=False,
            soft_score=0.4,
            coverage_rate=0.85,
            total_violations=2,
            critical_violations=1,
            violations=[
                ViolationDetail(
                    type="80_HOUR_VIOLATION",
                    severity=ViolationSeverity.CRITICAL,
                    message="Exceeded 80 hours",
                )
            ],
        )

        explanation = advisor.explain(result)

        assert "Score: 0.7" in explanation or "70.0%" in explanation
        assert "Invalid" in explanation or "Critical" in explanation


class TestMockLLMAdvisor:
    """Tests for MockLLMAdvisor."""

    def test_suggest_on_critical_violations(self):
        """Test mock advisor suggests algorithm switch on critical violations."""
        advisor = MockLLMAdvisor()

        state = RunState(
            run_id="test",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = EvaluationResult(
            valid=False,
            score=0.5,
            hard_constraint_pass=False,
            soft_score=0.3,
            coverage_rate=0.7,
            total_violations=1,
            critical_violations=1,
            violations=[
                ViolationDetail(
                    type="80_HOUR_VIOLATION",
                    severity=ViolationSeverity.CRITICAL,
                    message="Exceeded 80 hours",
                )
            ],
        )

        suggestion = advisor.suggest(state, result, [])

        assert suggestion is not None
        assert suggestion.type == SuggestionType.ALGORITHM_SWITCH

    def test_suggest_on_stagnation(self):
        """Test mock advisor suggests strategy change on stagnation."""
        advisor = MockLLMAdvisor()

        state = RunState(
            run_id="test",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            iterations_since_improvement=15,
        )

        result = EvaluationResult(
            valid=True,
            score=0.8,
            hard_constraint_pass=True,
            soft_score=0.4,
            coverage_rate=0.9,
            total_violations=0,
            critical_violations=0,
        )

        suggestion = advisor.suggest(state, result, [])

        assert suggestion is not None
        assert suggestion.type == SuggestionType.STRATEGY_CHANGE

    def test_suggest_none_on_good_result(self):
        """Test mock advisor returns None on good non-stagnating result."""
        advisor = MockLLMAdvisor()

        state = RunState(
            run_id="test",
            scenario="baseline",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            iterations_since_improvement=2,
        )

        result = EvaluationResult(
            valid=True,
            score=0.9,  # Good score
            hard_constraint_pass=True,
            soft_score=0.5,
            coverage_rate=0.95,
            total_violations=0,
            critical_violations=0,
        )

        suggestion = advisor.suggest(state, result, [])

        # No suggestion needed for good result
        assert suggestion is None
