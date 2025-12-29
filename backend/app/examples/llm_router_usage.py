"""Example usage of LLM Router service.

This file demonstrates how to use the LLM Router for various tasks.
"""

import asyncio
import os
from typing import Any

from app.core.config import get_settings
from app.schemas.llm import LLMRequest
from app.services.llm_router import LLMRouter


async def example_basic_generation():
    """Example: Basic text generation with automatic routing."""
    print("\n=== Example: Basic Generation ===")

    # Initialize router
    settings = get_settings()
    router = LLMRouter(
        default_provider=settings.LLM_DEFAULT_PROVIDER,
        enable_fallback=settings.LLM_ENABLE_FALLBACK,
        airgap_mode=settings.LLM_AIRGAP_MODE,
    )

    # Create request
    request = LLMRequest(
        prompt="Explain the ACGME 80-hour work week rule in simple terms.",
        provider="auto",  # Auto-routing based on task classification
        max_tokens=500,
        temperature=0.7,
    )

    # Generate response
    response = await router.generate(request)

    print(f"Provider: {response.provider}")
    print(f"Model: {response.model}")
    print(f"Content: {response.content}")
    if response.usage:
        print(f"Tokens used: {response.usage.total_tokens}")


async def example_explicit_provider():
    """Example: Use specific provider (Ollama)."""
    print("\n=== Example: Explicit Provider ===")

    router = LLMRouter()

    # Force Ollama for privacy-sensitive data
    request = LLMRequest(
        prompt="Summarize the resident schedule for next week",
        system="You are a medical scheduling assistant. Be concise.",
        provider="ollama",  # Explicitly use local model
        model="llama3.2",
        max_tokens=300,
    )

    response = await router.generate(request)

    print(f"Provider: {response.provider}")
    print(f"Content: {response.content[:100]}...")


async def example_tool_calling():
    """Example: Tool calling with automatic provider selection."""
    print("\n=== Example: Tool Calling ===")

    router = LLMRouter()

    # Define tools
    tools = [
        {
            "name": "validate_schedule",
            "description": "Validate a schedule against ACGME rules",
            "input_schema": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string"},
                },
                "required": ["schedule_id"],
            },
        }
    ]

    request = LLMRequest(
        prompt="Validate schedule ID 12345 for ACGME compliance",
        tools=tools,
        provider="auto",  # Will route to best tool-calling provider
    )

    response = await router.generate(request)

    print(f"Provider: {response.provider}")
    print(f"Model: {response.model}")
    if response.tool_calls:
        print(f"Tool calls: {len(response.tool_calls)}")
        for call in response.tool_calls:
            print(f"  - {call.name}: {call.arguments}")


async def example_task_classification():
    """Example: Task classification without generation."""
    print("\n=== Example: Task Classification ===")

    router = LLMRouter()

    # Classify different types of tasks
    tasks = [
        "Hello, how are you?",
        "Analyze the workload distribution across all residents and identify inequities",
        "Write a Python function to calculate duty hours",
        "What is patient John Doe's schedule?",
    ]

    for task in tasks:
        classification = await router.classify_task(task)
        print(f"\nTask: {task}")
        print(f"  Type: {classification.task_type}")
        print(f"  Complexity: {classification.complexity_score:.2f}")
        print(f"  Recommended: {classification.recommended_provider}/{classification.recommended_model}")
        print(f"  Reasoning: {classification.reasoning}")


async def example_health_monitoring():
    """Example: Health check and statistics."""
    print("\n=== Example: Health Monitoring ===")

    router = LLMRouter()

    # Check provider health
    health_status = await router.health_check_all()

    print("\nProvider Health:")
    for provider, health in health_status.items():
        status = "✓ Available" if health.is_available else "✗ Unavailable"
        print(f"  {provider}: {status}")
        if health.avg_latency_ms:
            print(f"    Avg latency: {health.avg_latency_ms:.2f}ms")
        if health.error_message:
            print(f"    Error: {health.error_message}")

    # Check circuit breaker states
    breaker_states = router.get_circuit_breaker_states()

    print("\nCircuit Breaker States:")
    for provider, state in breaker_states.items():
        print(f"  {provider}: {state.state}")
        if state.failure_count > 0:
            print(f"    Failures: {state.failure_count}")

    # Get usage statistics
    stats = router.get_stats()

    print("\nUsage Statistics:")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Fallback activations: {stats.fallback_count}")
    print(f"  Total tokens: {stats.total_tokens_used}")
    if stats.requests_by_provider:
        print("  Requests by provider:")
        for provider, count in stats.requests_by_provider.items():
            print(f"    {provider}: {count}")


async def example_airgap_mode():
    """Example: Router in airgap mode (local only)."""
    print("\n=== Example: Airgap Mode ===")

    # Initialize in airgap mode
    router = LLMRouter(airgap_mode=True)

    print(f"Airgap mode: {router.airgap_mode}")
    print(f"Available providers: {list(router.providers.keys())}")
    print(f"Fallback chain: {router.fallback_chain}")

    # All requests will use local provider
    request = LLMRequest(
        prompt="Generate a simple schedule template",
        provider="auto",
    )

    response = await router.generate(request)

    print(f"Provider used: {response.provider}")
    assert response.provider == "ollama", "Should only use local provider in airgap mode"


async def example_fallback_behavior():
    """Example: Fallback behavior when primary provider fails."""
    print("\n=== Example: Fallback Behavior ===")

    router = LLMRouter(enable_fallback=True)

    # Simulate provider failure scenario
    # In real usage, this would happen automatically when provider is down

    print("Fallback chain:", router.fallback_chain)
    print("If primary provider fails, router will try:", router.fallback_chain[1:])


async def main():
    """Run all examples."""
    print("=" * 70)
    print("LLM Router Usage Examples")
    print("=" * 70)

    try:
        # Run examples
        await example_basic_generation()
        await example_explicit_provider()
        await example_task_classification()
        await example_health_monitoring()
        await example_airgap_mode()
        await example_fallback_behavior()

        # Note: Tool calling example requires actual LLM connection
        # Uncomment if you have Ollama or Anthropic configured:
        # await example_tool_calling()

    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        print("Make sure Ollama is running: docker-compose up ollama")
        print("Or set ANTHROPIC_API_KEY for cloud provider")

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    # Set environment variables for testing if not set
    if not os.getenv("OLLAMA_URL"):
        os.environ["OLLAMA_URL"] = "http://localhost:11434"

    asyncio.run(main())
