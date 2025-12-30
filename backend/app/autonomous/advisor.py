"""
LLM Advisor Interface with Schema Validation.

Only then add the LLM as an advisor, not a driver. Where it helps:
    - Suggest which failure mode is most important
    - Suggest plausible parameter deltas
    - Suggest new neighborhood moves or repair operators
    - Explain reports for humans

The Python loop must be able to:
    - Validate LLM suggestions against a schema
    - Reject them if unsafe or nonsensical
    - Continue without them
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.autonomous.evaluator import EvaluationResult
from app.autonomous.state import GeneratorParams, IterationRecord, RunState
from app.prompts.scheduling_assistant import (
    SCHEDULING_ASSISTANT_SYSTEM_PROMPT,
    PromptManager,
)
from app.schemas.llm import LLMRequest
from app.services.llm_router import LLMRouter

logger = logging.getLogger(__name__)


class SuggestionType(str, Enum):
    """Types of suggestions the LLM can make."""

    PARAMETER_CHANGE = "parameter_change"
    ALGORITHM_SWITCH = "algorithm_switch"
    CONSTRAINT_WEIGHT = "constraint_weight"
    FAILURE_ANALYSIS = "failure_analysis"
    STRATEGY_CHANGE = "strategy_change"
    EXPLANATION = "explanation"


@dataclass
class Suggestion:
    """
    A validated suggestion from the LLM advisor.

    Attributes:
        type: Type of suggestion
        confidence: LLM's confidence in suggestion (0.0-1.0)
        reasoning: Explanation of why this suggestion was made
        params: Optional updated parameters if type is PARAMETER_CHANGE
        analysis: Optional analysis if type is FAILURE_ANALYSIS
        raw_response: Original LLM response for debugging
    """

    type: SuggestionType
    confidence: float
    reasoning: str
    params: GeneratorParams | None = None
    analysis: dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "params": self.params.to_dict() if self.params else None,
            "analysis": self.analysis,
        }


class SuggestionSchema:
    """
    Schema for validating LLM suggestions.

    The schema defines what the LLM can and cannot suggest.
    Suggestions that don't match the schema are rejected.
    """

    # Valid algorithms the LLM can suggest
    VALID_ALGORITHMS = {"greedy", "cp_sat", "pulp", "hybrid"}

    # Valid parameter ranges
    TIMEOUT_RANGE = (10.0, 600.0)  # 10 seconds to 10 minutes
    WEIGHT_RANGE = (0.0, 2.0)  # Constraint weights
    DIVERSIFICATION_RANGE = (0.0, 1.0)

    # Valid constraint names for weight adjustments
    VALID_CONSTRAINTS = {
        "acgme_compliance",
        "coverage_rate",
        "resilience",
        "load_balance",
        "preference_alignment",
    }

    @classmethod
    def validate_params(cls, params: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate parameter suggestions.

        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []

        # Validate algorithm
        if "algorithm" in params:
            if params["algorithm"] not in cls.VALID_ALGORITHMS:
                errors.append(f"Invalid algorithm: {params['algorithm']}")

        # Validate timeout
        if "timeout_seconds" in params:
            timeout = params["timeout_seconds"]
            if not cls.TIMEOUT_RANGE[0] <= timeout <= cls.TIMEOUT_RANGE[1]:
                errors.append(f"Timeout {timeout} out of range {cls.TIMEOUT_RANGE}")

        # Validate diversification
        if "diversification_factor" in params:
            div = params["diversification_factor"]
            if not cls.DIVERSIFICATION_RANGE[0] <= div <= cls.DIVERSIFICATION_RANGE[1]:
                errors.append(
                    f"Diversification {div} out of range {cls.DIVERSIFICATION_RANGE}"
                )

        # Validate constraint weights
        if "constraint_weights" in params:
            for name, weight in params["constraint_weights"].items():
                if name not in cls.VALID_CONSTRAINTS:
                    errors.append(f"Unknown constraint: {name}")
                if not cls.WEIGHT_RANGE[0] <= weight <= cls.WEIGHT_RANGE[1]:
                    errors.append(
                        f"Weight {weight} for {name} out of range {cls.WEIGHT_RANGE}"
                    )

        if errors:
            return False, "; ".join(errors)
        return True, ""


class LLMAdvisor:
    """
    Advisory LLM interface for the autonomous loop.

    This class provides an interface to query an LLM for suggestions
    while ensuring:
    1. Suggestions are validated against a schema
    2. Invalid suggestions are rejected
    3. The loop can continue without LLM input

    The LLM is advisory only - it cannot make decisions that bypass
    the Python control loop.

    Example:
        >>> router = LLMRouter(default_provider="ollama", airgap_mode=True)
        >>> advisor = LLMAdvisor(llm_router=router)
        >>> suggestion = await advisor.suggest(
        ...     state=state,
        ...     last_evaluation=evaluation,
        ...     history=history,
        ... )
        >>> if suggestion and advisor.validate_suggestion(suggestion):
        ...     # Apply suggestion
        ...     state.current_params = suggestion.params
    """

    def __init__(
        self,
        llm_router: Optional[LLMRouter] = None,
        model: str = "llama3.2",
        max_tokens: int = 1024,
        temperature: float = 0.3,
        airgap_mode: bool = True,
    ):
        """
        Initialize the LLM advisor.

        Args:
            llm_router: LLMRouter instance (if None, creates local Ollama router)
            model: Model to use for suggestions (default: llama3.2 for Ollama)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (lower = more deterministic)
            airgap_mode: If True, only use local Ollama (no cloud providers)
        """
        self.llm_router = llm_router or LLMRouter(
            default_provider="ollama",
            enable_fallback=True,
            airgap_mode=airgap_mode,
        )
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.schema = SuggestionSchema()
        self.prompt_manager = PromptManager()

        logger.info(
            f"LLMAdvisor initialized (model={model}, airgap={airgap_mode})"
        )

    async def suggest(
        self,
        state: RunState,
        last_evaluation: EvaluationResult | None,
        history: list[IterationRecord],
    ) -> Suggestion | None:
        """
        Get a suggestion from the LLM.

        Args:
            state: Current run state
            last_evaluation: Most recent evaluation result
            history: Recent iteration history

        Returns:
            Validated Suggestion or None if LLM unavailable/failed
        """
        if self.llm_router is None:
            return None

        try:
            # Build prompt
            prompt = self._build_prompt(state, last_evaluation, history)

            # Query LLM
            response = await self._query_llm(prompt)

            # Parse response
            suggestion = self._parse_response(response)

            return suggestion

        except Exception as e:
            # Log but don't crash - the loop can continue without LLM
            logger.warning(f"LLM advisor error: {e}", exc_info=True)
            return None

    def validate_suggestion(self, suggestion: Suggestion) -> bool:
        """
        Validate a suggestion against the schema.

        Args:
            suggestion: Suggestion to validate

        Returns:
            True if valid, False if should be rejected
        """
        # Basic validation
        if suggestion.confidence < 0.3:
            logger.debug("Suggestion rejected: confidence too low")
            return False  # Low confidence suggestions are ignored

        if not suggestion.reasoning:
            logger.debug("Suggestion rejected: no reasoning provided")
            return False  # Require reasoning

        # Validate parameters if present
        if suggestion.params:
            is_valid, error = self.schema.validate_params(suggestion.params.to_dict())
            if not is_valid:
                logger.warning(f"Suggestion rejected: {error}")
                return False

        return True

    async def explain(
        self,
        evaluation: EvaluationResult,
    ) -> str:
        """
        Get a human-readable explanation of an evaluation.

        This is a read-only operation - it doesn't affect the loop,
        just helps humans understand the results.

        Args:
            evaluation: Evaluation to explain

        Returns:
            Human-readable explanation string
        """
        if self.llm_router is None:
            return self._fallback_explanation(evaluation)

        try:
            prompt = self._build_explanation_prompt(evaluation)
            response = await self._query_llm(prompt)
            return response

        except Exception as e:
            logger.warning(f"LLM explanation error: {e}")
            return self._fallback_explanation(evaluation)

    def _build_prompt(
        self,
        state: RunState,
        last_evaluation: EvaluationResult | None,
        history: list[IterationRecord],
    ) -> str:
        """Build prompt for suggestion request."""
        prompt_parts = [
            "You are an expert scheduling advisor. Analyze the following scheduling optimization state and suggest improvements.",
            "",
            "CURRENT STATE:",
            f"- Scenario: {state.scenario}",
            f"- Iteration: {state.current_iteration}/{state.max_iterations}",
            f"- Best score: {state.best_score:.4f}",
            f"- Target score: {state.target_score}",
            f"- Iterations since improvement: {state.iterations_since_improvement}",
            f"- Current algorithm: {state.current_params.algorithm}",
            f"- Current timeout: {state.current_params.timeout_seconds}s",
        ]

        if last_evaluation:
            prompt_parts.extend(
                [
                    "",
                    "LAST EVALUATION:",
                    f"- Score: {last_evaluation.score:.4f}",
                    f"- Valid: {last_evaluation.valid}",
                    f"- Critical violations: {last_evaluation.critical_violations}",
                    f"- Total violations: {last_evaluation.total_violations}",
                ]
            )

            if last_evaluation.violations:
                prompt_parts.append("- Violation types:")
                for v in last_evaluation.violations[:5]:  # Limit to 5
                    prompt_parts.append(f"  - {v.type}: {v.message}")

        if history:
            prompt_parts.extend(
                [
                    "",
                    "RECENT HISTORY (last 5 iterations):",
                ]
            )
            for record in history[-5:]:
                prompt_parts.append(
                    f"- Iter {record.iteration}: score={record.score:.4f}, "
                    f"valid={record.valid}, algorithm={record.params.algorithm}"
                )

        prompt_parts.extend(
            [
                "",
                "Based on this data, suggest ONE improvement. Respond in JSON format:",
                "{",
                '  "type": "parameter_change" | "algorithm_switch" | "constraint_weight" | "failure_analysis",',
                '  "confidence": 0.0-1.0,',
                '  "reasoning": "explanation of why this change should help",',
                '  "params": {',
                '    "algorithm": "greedy" | "cp_sat" | "pulp" | "hybrid",',
                '    "timeout_seconds": 10-600,',
                '    "diversification_factor": 0.0-1.0,',
                '    "constraint_weights": {"constraint_name": 0.0-2.0}',
                "  }",
                "}",
                "",
                "Only include params fields you want to change. Keep suggestions conservative.",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_explanation_prompt(self, evaluation: EvaluationResult) -> str:
        """Build prompt for explanation request."""
        prompt_parts = [
            "Explain this schedule evaluation result in plain language for a scheduler administrator:",
            "",
            f"Score: {evaluation.score:.4f}/1.0",
            f"Valid: {evaluation.valid}",
            f"Coverage: {evaluation.coverage_rate:.1%}",
            "",
            "Score Components:",
        ]

        for c in evaluation.components:
            prompt_parts.append(
                f"- {c.name}: {c.raw_value:.3f} (weight: {c.weight}) - {c.details}"
            )

        if evaluation.violations:
            prompt_parts.extend(
                [
                    "",
                    "Violations:",
                ]
            )
            for v in evaluation.violations:
                prompt_parts.append(f"- {v.severity.value.upper()}: {v.message}")

        prompt_parts.extend(
            [
                "",
                "Provide a 2-3 sentence summary explaining:",
                "1. The overall quality of this schedule",
                "2. The most important issue to address (if any)",
                "3. One specific actionable recommendation",
            ]
        )

        return "\n".join(prompt_parts)

    async def _query_llm(self, prompt: str) -> str:
        """Query the LLM and return response text."""
        if self.llm_router is None:
            raise ValueError("No LLM router configured")

        # Build LLM request
        request = LLMRequest(
            prompt=prompt,
            system=SCHEDULING_ASSISTANT_SYSTEM_PROMPT,
            model=self.model,
            provider="ollama",  # Use local Ollama for airgap compatibility
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        # Generate response
        response = await self.llm_router.generate(request)

        return response.content

    def _parse_response(self, response: str) -> Suggestion:
        """Parse LLM response into a Suggestion."""
        # Extract JSON from response
        json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")

        data = json.loads(json_match.group())

        # Parse type
        suggestion_type = SuggestionType(data.get("type", "parameter_change"))

        # Parse params if present
        params = None
        if "params" in data and data["params"]:
            params = GeneratorParams(
                algorithm=data["params"].get("algorithm", "greedy"),
                timeout_seconds=data["params"].get("timeout_seconds", 60.0),
                diversification_factor=data["params"].get(
                    "diversification_factor", 0.0
                ),
                constraint_weights=data["params"].get("constraint_weights", {}),
            )

        return Suggestion(
            type=suggestion_type,
            confidence=data.get("confidence", 0.5),
            reasoning=data.get("reasoning", ""),
            params=params,
            analysis=data.get("analysis", {}),
            raw_response=response,
        )

    def _fallback_explanation(self, evaluation: EvaluationResult) -> str:
        """Generate explanation without LLM."""
        lines = [
            f"Schedule Score: {evaluation.score:.1%}",
            f"Status: {'Valid' if evaluation.valid else 'Invalid'}",
            f"Coverage: {evaluation.coverage_rate:.1%}",
        ]

        if evaluation.critical_violations > 0:
            lines.append(
                f"Critical Issues: {evaluation.critical_violations} ACGME violations require immediate attention."
            )

        if not evaluation.valid:
            top_violation = evaluation.violations[0] if evaluation.violations else None
            if top_violation:
                lines.append(f"Top Priority: {top_violation.message}")

        return " ".join(lines)

    async def close(self):
        """Close LLM router connections."""
        if self.llm_router:
            await self.llm_router.close()


class MockLLMAdvisor(LLMAdvisor):
    """
    Mock LLM advisor for testing.

    Returns predetermined suggestions based on evaluation state.
    Useful for testing the advisor integration without LLM costs.
    """

    def __init__(self):
        """Initialize mock advisor without LLM router."""
        # Don't call super().__init__ to avoid creating router
        self.llm_router = None
        self.model = "mock"
        self.max_tokens = 1024
        self.temperature = 0.3
        self.schema = SuggestionSchema()
        self.prompt_manager = PromptManager()

    async def suggest(
        self,
        state: RunState,
        last_evaluation: EvaluationResult | None,
        history: list[IterationRecord],
    ) -> Suggestion | None:
        """Return mock suggestion based on state."""
        if last_evaluation is None:
            return None

        # Simple heuristic-based suggestions
        if last_evaluation.critical_violations > 0:
            return Suggestion(
                type=SuggestionType.ALGORITHM_SWITCH,
                confidence=0.7,
                reasoning="Critical violations detected, trying a different solver",
                params=GeneratorParams(algorithm="cp_sat"),
            )

        if state.iterations_since_improvement > 10:
            return Suggestion(
                type=SuggestionType.STRATEGY_CHANGE,
                confidence=0.6,
                reasoning="Stagnation detected, increasing diversification",
                params=GeneratorParams(diversification_factor=0.5),
            )

        if last_evaluation.score < 0.5:
            return Suggestion(
                type=SuggestionType.PARAMETER_CHANGE,
                confidence=0.5,
                reasoning="Low score, trying longer timeout",
                params=GeneratorParams(timeout_seconds=120.0),
            )

        return None

    async def close(self):
        """No-op for mock advisor."""
        pass
