"""
Example: Using LLM Advisor with Local Ollama.

This script demonstrates how the LLM Advisor integrates with the autonomous
scheduling loop using local Ollama models (airgap compatible).

Run this after starting Ollama:
    docker-compose up -d ollama
    python -m app.autonomous.examples.advisor_example
"""

import asyncio
import logging
from datetime import date

from app.autonomous.advisor import LLMAdvisor, MockLLMAdvisor
from app.autonomous.evaluator import (
    EvaluationResult,
    ScoreComponent,
    Violation,
    ViolationSeverity,
)
from app.autonomous.state import GeneratorParams, IterationRecord, RunState
from app.services.llm_router import LLMRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def example_with_real_llm() -> None:
    """Example using real Ollama LLM (requires Ollama running)."""
    logger.info("=== Example 1: Real LLM Advisor with Ollama ===")

    # Create LLM advisor with Ollama
    advisor = LLMAdvisor(
        llm_router=None,  # Will create default Ollama router
        model="llama3.2",
        airgap_mode=True,  # Local only
    )

    # Create mock run state
    state = RunState(
        run_id="example-001",
        scenario="baseline",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        max_iterations=200,
        target_score=0.95,
        current_iteration=15,
        best_score=0.65,
        iterations_since_improvement=5,
        current_params=GeneratorParams(
            algorithm="greedy",
            timeout_seconds=60.0,
            diversification_factor=0.0,
        ),
    )

    # Create mock evaluation with some violations
    evaluation = EvaluationResult(
        score=0.65,
        valid=False,
        critical_violations=2,
        total_violations=5,
        coverage_rate=0.85,
        components=[
            ScoreComponent(
                name="acgme_compliance",
                raw_value=0.5,
                weight=0.4,
                details="2 critical violations",
            ),
            ScoreComponent(
                name="coverage_rate",
                raw_value=0.85,
                weight=0.3,
                details="Good coverage",
            ),
            ScoreComponent(
                name="load_balance",
                raw_value=0.7,
                weight=0.3,
                details="Moderate balance",
            ),
        ],
        violations=[
            Violation(
                type="acgme_80_hour",
                message="Resident exceeded 80 hours in week 2",
                severity=ViolationSeverity.CRITICAL,
                person_id="RES-001",
            ),
            Violation(
                type="acgme_1_in_7",
                message="Resident did not get 1 day off in 7",
                severity=ViolationSeverity.CRITICAL,
                person_id="RES-002",
            ),
        ],
    )

    # Create some iteration history
    history = [
        IterationRecord(
            iteration=i,
            params=GeneratorParams(algorithm="greedy"),
            score=0.5 + (i * 0.02),
            valid=False,
            critical_violations=2 if i < 10 else 1,
            total_violations=5,
            violation_types=["acgme_80_hour", "acgme_1_in_7"],
            duration_seconds=3.5,
        )
        for i in range(10, 15)
    ]

    try:
        # Get LLM suggestion
        logger.info("Requesting suggestion from LLM advisor...")
        suggestion = await advisor.suggest(
            state=state,
            last_evaluation=evaluation,
            history=history,
        )

        if suggestion:
            logger.info("✓ LLM Suggestion Received:")
            logger.info(f"  Type: {suggestion.type.value}")
            logger.info(f"  Confidence: {suggestion.confidence:.2f}")
            logger.info(f"  Reasoning: {suggestion.reasoning}")

            # Validate suggestion
            is_valid = advisor.validate_suggestion(suggestion)
            logger.info(f"  Valid: {is_valid}")

            if suggestion.params:
                logger.info("  Suggested Parameters:")
                logger.info(f"    Algorithm: {suggestion.params.algorithm}")
                logger.info(f"    Timeout: {suggestion.params.timeout_seconds}s")
                logger.info(
                    f"    Diversification: {suggestion.params.diversification_factor}"
                )

        else:
            logger.warning("No suggestion received from LLM")

            # Get explanation
        logger.info("\nRequesting explanation from LLM advisor...")
        explanation = await advisor.explain(evaluation)
        logger.info(f"Explanation: {explanation}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await advisor.close()


def example_with_mock_advisor() -> None:
    """Example using mock advisor (no LLM required)."""
    logger.info("\n=== Example 2: Mock Advisor (No LLM Required) ===")

    # Create mock advisor
    advisor = MockLLMAdvisor()

    # Create state with critical violations
    state = RunState(
        run_id="mock-001",
        scenario="baseline",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        max_iterations=200,
        target_score=0.95,
        current_iteration=25,
        best_score=0.45,
        iterations_since_improvement=12,
        current_params=GeneratorParams(algorithm="greedy"),
    )

    evaluation = EvaluationResult(
        score=0.45,
        valid=False,
        critical_violations=3,
        total_violations=8,
        coverage_rate=0.75,
        components=[],
        violations=[],
    )

    # Get suggestion synchronously (mock doesn't need async)
    suggestion = asyncio.run(
        advisor.suggest(state=state, last_evaluation=evaluation, history=[])
    )

    if suggestion:
        logger.info("✓ Mock Suggestion Received:")
        logger.info(f"  Type: {suggestion.type.value}")
        logger.info(f"  Confidence: {suggestion.confidence:.2f}")
        logger.info(f"  Reasoning: {suggestion.reasoning}")

        if suggestion.params:
            logger.info(f"  Suggested Algorithm: {suggestion.params.algorithm}")


async def example_router_health_check() -> None:
    """Example: Check LLM Router health status."""
    logger.info("\n=== Example 3: LLM Router Health Check ===")

    router = LLMRouter(default_provider="ollama", airgap_mode=True)

    try:
        health_status = await router.health_check_all()

        for provider, health in health_status.items():
            status_icon = "✓" if health.is_available else "✗"
            logger.info(f"{status_icon} {provider}:")
            logger.info(f"  Available: {health.is_available}")
            logger.info(f"  Failures: {health.failure_count}")
            if health.avg_latency_ms:
                logger.info(f"  Avg Latency: {health.avg_latency_ms:.2f}ms")
            if health.error_message:
                logger.info(f"  Error: {health.error_message}")

        stats = router.get_stats()
        logger.info("\nRouter Statistics:")
        logger.info(f"  Total Requests: {stats.total_requests}")
        logger.info(f"  Fallback Count: {stats.fallback_count}")
        logger.info(f"  Error Count: {stats.error_count}")

    finally:
        await router.close()


def main() -> None:
    """Run all examples."""
    logger.info("LLM Advisor Examples")
    logger.info("=" * 60)

    # Example 1: Mock advisor (always works)
    example_with_mock_advisor()

    # Example 2: Router health check
    try:
        asyncio.run(example_router_health_check())
    except Exception as e:
        logger.warning(f"Router health check failed: {e}")

        # Example 3: Real LLM advisor (requires Ollama)
    try:
        asyncio.run(example_with_real_llm())
    except Exception as e:
        logger.warning(f"Real LLM example failed (is Ollama running?): {e}")
        logger.info("\nTo run real LLM example, start Ollama:")
        logger.info("  docker-compose up -d ollama")
        logger.info("  # Wait for Ollama to pull llama3.2 model")
        logger.info("  python -m app.autonomous.examples.advisor_example")


if __name__ == "__main__":
    main()
