"""
Circuit Breaker Pattern for Resilience.

Implements the circuit breaker pattern to protect services from cascading failures:

Components:
- State Machine: Manages CLOSED, OPEN, HALF_OPEN states
- Circuit Breaker: Main implementation with fallback support
- Registry: Centralized management of multiple breakers
- Decorators: Easy-to-use decorators for functions
- Monitoring: Prometheus metrics integration

Usage:

    ***REMOVED*** Basic usage with decorator
    from app.resilience.circuit_breaker import async_circuit_breaker

    @async_circuit_breaker(
        name="database",
        failure_threshold=5,
        timeout_seconds=60,
    )
    async def query_database(query: str):
        return await db.execute(query)

    ***REMOVED*** Using registry
    from app.resilience.circuit_breaker import get_registry

    registry = get_registry()
    registry.register("external_api", failure_threshold=3)

    breaker = registry.get("external_api")
    async with breaker.async_call():
        await api_call()

    ***REMOVED*** Manual usage
    from app.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

    config = CircuitBreakerConfig(
        name="service",
        failure_threshold=5,
        timeout_seconds=60,
    )
    breaker = CircuitBreaker(config)

    result = await breaker.call_async(risky_function, arg1, arg2)

Features:
- Automatic failure detection and recovery
- Configurable thresholds and timeouts
- Fallback function support
- Prometheus metrics integration
- Manual override capability
- Per-service configuration
"""

***REMOVED*** States
***REMOVED*** Main breaker
from app.resilience.circuit_breaker.breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerTimeoutError,
    CircuitOpenError,
)

***REMOVED*** Decorators
from app.resilience.circuit_breaker.decorators import (
    async_circuit_breaker,
    circuit_breaker,
    get_breaker_from_function,
    get_breaker_name_from_function,
    with_async_circuit_breaker,
    with_circuit_breaker,
)

***REMOVED*** Monitoring
from app.resilience.circuit_breaker.monitoring import (
    CircuitBreakerMetrics,
    MetricsCollector,
    collect_metrics_for_all_breakers,
    get_metrics,
    setup_metrics,
)

***REMOVED*** Registry
from app.resilience.circuit_breaker.registry import (
    CircuitBreakerRegistry,
    get_registry,
    setup_registry,
)
from app.resilience.circuit_breaker.states import (
    CircuitMetrics,
    CircuitState,
    StateMachine,
    StateTransition,
)

__all__ = [
    ***REMOVED*** States
    "CircuitState",
    "CircuitMetrics",
    "StateTransition",
    "StateMachine",
    ***REMOVED*** Main breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitOpenError",
    "CircuitBreakerTimeoutError",
    ***REMOVED*** Registry
    "CircuitBreakerRegistry",
    "get_registry",
    "setup_registry",
    ***REMOVED*** Decorators
    "circuit_breaker",
    "async_circuit_breaker",
    "with_circuit_breaker",
    "with_async_circuit_breaker",
    "get_breaker_from_function",
    "get_breaker_name_from_function",
    ***REMOVED*** Monitoring
    "CircuitBreakerMetrics",
    "get_metrics",
    "setup_metrics",
    "collect_metrics_for_all_breakers",
    "MetricsCollector",
]
