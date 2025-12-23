"""
Circuit Breaker Monitoring and Metrics.

Integrates circuit breaker metrics with Prometheus:

1. State gauges (CLOSED, OPEN, HALF_OPEN)
2. Request counters (success, failure, rejection)
3. State transition events
4. Per-breaker metrics with labels
"""

import logging
from typing import Optional

from app.resilience.circuit_breaker.registry import get_registry

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        REGISTRY,
        CollectorRegistry,
        Counter,
        Enum,
        Gauge,
        Histogram,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available - circuit breaker metrics disabled")


class CircuitBreakerMetrics:
    """
    Prometheus metrics for circuit breakers.

    Tracks state, requests, and transitions for monitoring.

    Metrics:
    - circuit_breaker_state: Current state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
    - circuit_breaker_requests_total: Total requests by result
    - circuit_breaker_state_transitions_total: State transitions
    - circuit_breaker_failure_rate: Current failure rate
    - circuit_breaker_consecutive_failures: Consecutive failures
    """

    def __init__(self, registry: Optional["CollectorRegistry"] = None):
        """
        Initialize circuit breaker metrics.

        Args:
            registry: Optional custom registry (uses default if not provided)
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available - metrics disabled")
            self._enabled = False
            return

        self._enabled = True
        self._registry = registry or REGISTRY

        # === GAUGES ===

        self.state_gauge = Gauge(
            "circuit_breaker_state",
            "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
            ["breaker"],
            registry=self._registry,
        )

        self.failure_rate = Gauge(
            "circuit_breaker_failure_rate",
            "Current failure rate (0.0-1.0)",
            ["breaker"],
            registry=self._registry,
        )

        self.consecutive_failures = Gauge(
            "circuit_breaker_consecutive_failures",
            "Current consecutive failure count",
            ["breaker"],
            registry=self._registry,
        )

        self.consecutive_successes = Gauge(
            "circuit_breaker_consecutive_successes",
            "Current consecutive success count",
            ["breaker"],
            registry=self._registry,
        )

        self.half_open_calls = Gauge(
            "circuit_breaker_half_open_calls",
            "Current in-flight calls in half-open state",
            ["breaker"],
            registry=self._registry,
        )

        # === COUNTERS ===

        self.requests_total = Counter(
            "circuit_breaker_requests_total",
            "Total requests handled by circuit breaker",
            ["breaker", "result"],  # result: success, failure, rejected
            registry=self._registry,
        )

        self.state_transitions = Counter(
            "circuit_breaker_state_transitions_total",
            "Total state transitions",
            ["breaker", "from_state", "to_state"],
            registry=self._registry,
        )

        self.fallback_executions = Counter(
            "circuit_breaker_fallback_executions_total",
            "Total fallback function executions",
            ["breaker", "result"],  # result: success, failure
            registry=self._registry,
        )

        # === HISTOGRAMS ===

        self.call_duration = Histogram(
            "circuit_breaker_call_duration_seconds",
            "Duration of calls through circuit breaker",
            ["breaker", "result"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self._registry,
        )

        logger.info("Circuit breaker Prometheus metrics initialized")

    def update_breaker_metrics(self, breaker_name: str):
        """
        Update metrics for a specific breaker.

        Args:
            breaker_name: Name of the breaker
        """
        if not self._enabled:
            return

        try:
            registry = get_registry()
            breaker = registry.get(breaker_name)
            status = breaker.get_status()

            # Update state gauge
            state_value = {
                "closed": 0,
                "open": 1,
                "half_open": 2,
            }.get(status["state"], 0)
            self.state_gauge.labels(breaker=breaker_name).set(state_value)

            # Update failure rate
            self.failure_rate.labels(breaker=breaker_name).set(status["failure_rate"])

            # Update consecutive counters
            self.consecutive_failures.labels(breaker=breaker_name).set(
                status["consecutive_failures"]
            )
            self.consecutive_successes.labels(breaker=breaker_name).set(
                status["consecutive_successes"]
            )

            # Update half-open calls
            if hasattr(breaker.state_machine, "half_open_calls_in_flight"):
                self.half_open_calls.labels(breaker=breaker_name).set(
                    breaker.state_machine.half_open_calls_in_flight
                )

        except Exception as e:
            logger.error(f"Error updating metrics for breaker '{breaker_name}': {e}")

    def update_all_breakers(self):
        """Update metrics for all registered breakers."""
        if not self._enabled:
            return

        try:
            registry = get_registry()
            for breaker_name in registry.list_breakers():
                self.update_breaker_metrics(breaker_name)
        except Exception as e:
            logger.error(f"Error updating all breaker metrics: {e}")

    def record_request(
        self,
        breaker_name: str,
        result: str,  # "success", "failure", "rejected"
    ):
        """
        Record a request result.

        Args:
            breaker_name: Name of the breaker
            result: Result of the request
        """
        if not self._enabled:
            return

        self.requests_total.labels(
            breaker=breaker_name,
            result=result,
        ).inc()

    def record_state_transition(
        self,
        breaker_name: str,
        from_state: str,
        to_state: str,
    ):
        """
        Record a state transition.

        Args:
            breaker_name: Name of the breaker
            from_state: Previous state
            to_state: New state
        """
        if not self._enabled:
            return

        self.state_transitions.labels(
            breaker=breaker_name,
            from_state=from_state,
            to_state=to_state,
        ).inc()

        logger.info(
            f"Circuit breaker '{breaker_name}' transitioned: {from_state} -> {to_state}"
        )

    def record_fallback_execution(
        self,
        breaker_name: str,
        success: bool,
    ):
        """
        Record a fallback execution.

        Args:
            breaker_name: Name of the breaker
            success: Whether fallback succeeded
        """
        if not self._enabled:
            return

        result = "success" if success else "failure"
        self.fallback_executions.labels(
            breaker=breaker_name,
            result=result,
        ).inc()

    def get_breaker_summary(self) -> dict:
        """
        Get summary of all circuit breakers.

        Returns:
            Summary statistics
        """
        try:
            registry = get_registry()
            health = registry.health_check()

            return {
                "total_breakers": health["total_breakers"],
                "open_breakers": health["open_breakers"],
                "half_open_breakers": health["half_open_breakers"],
                "closed_breakers": health["closed_breakers"],
                "open_breaker_names": health["open_breaker_names"],
                "half_open_breaker_names": health["half_open_breaker_names"],
                "total_requests": health["total_requests"],
                "total_failures": health["total_failures"],
                "total_rejections": health["total_rejections"],
                "overall_failure_rate": health["overall_failure_rate"],
            }
        except Exception as e:
            logger.error(f"Error getting breaker summary: {e}")
            return {}


# Global metrics instance
_metrics: CircuitBreakerMetrics | None = None


def get_metrics() -> CircuitBreakerMetrics:
    """
    Get or create the global metrics instance.

    Returns:
        The global metrics instance
    """
    global _metrics
    if _metrics is None:
        _metrics = CircuitBreakerMetrics()
    return _metrics


def setup_metrics(
    registry: Optional["CollectorRegistry"] = None,
) -> CircuitBreakerMetrics:
    """
    Set up metrics with optional custom registry.

    Call during app startup to initialize metrics.

    Args:
        registry: Optional custom registry

    Returns:
        The initialized metrics instance
    """
    global _metrics
    _metrics = CircuitBreakerMetrics(registry)
    return _metrics


def collect_metrics_for_all_breakers():
    """
    Collect metrics for all registered circuit breakers.

    Call periodically (e.g., in a background task) to update metrics.
    """
    metrics = get_metrics()
    metrics.update_all_breakers()


# Auto-update integration
class MetricsCollector:
    """
    Background metrics collector for circuit breakers.

    Can be used as a Celery task or standalone background job.
    """

    def __init__(self, interval_seconds: float = 15.0):
        """
        Initialize collector.

        Args:
            interval_seconds: Collection interval
        """
        self.interval = interval_seconds
        self.metrics = get_metrics()

    async def run_async(self):
        """Run async collection loop."""
        import asyncio

        while True:
            try:
                self.metrics.update_all_breakers()
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")

            await asyncio.sleep(self.interval)

    def run_sync(self):
        """Run sync collection loop."""
        import time

        while True:
            try:
                self.metrics.update_all_breakers()
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")

            time.sleep(self.interval)

    def collect_once(self):
        """Collect metrics once (for scheduled tasks)."""
        try:
            self.metrics.update_all_breakers()
        except Exception as e:
            logger.error(f"Error in metrics collection: {e}")
