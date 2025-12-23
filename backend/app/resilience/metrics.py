"""
Prometheus Metrics for Resilience Monitoring.

Exposes key resilience metrics for monitoring and alerting:

Gauges (current values):
- resilience_utilization_rate: Current system utilization (0.0-1.0)
- resilience_utilization_level: Current level (0=GREEN to 4=BLACK)
- resilience_defense_level: Active defense level (1-5)
- resilience_load_shedding_level: Current load shedding (0-5)
- resilience_n1_compliant: Whether system passes N-1 analysis (0/1)
- resilience_n2_compliant: Whether system passes N-2 analysis (0/1)
- resilience_faculty_available: Number of available faculty
- resilience_coverage_rate: Current coverage rate (0.0-1.0)

Counters (cumulative):
- resilience_crisis_activations_total: Total crisis activations
- resilience_fallback_activations_total: Total fallback activations
- resilience_load_shedding_events_total: Total load shedding events

Histograms:
- resilience_health_check_duration_seconds: Health check duration

Info:
- resilience_info: Build/version info
"""

from typing import Optional

from app.core.logging import get_logger

try:
    from prometheus_client import (
        REGISTRY,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = get_logger(__name__)


class ResilienceMetrics:
    """
    Prometheus metrics collector for resilience monitoring.

    Integrates with prometheus-fastapi-instrumentator for automatic
    exposure via the /metrics endpoint.

    Usage:
        metrics = ResilienceMetrics()

        # Update after health check
        metrics.update_utilization(0.75, "yellow")
        metrics.update_defense_level(2)

        # Record events
        metrics.record_crisis_activation("moderate", "PCS season")
    """

    def __init__(self, registry: Optional["CollectorRegistry"] = None):
        """
        Initialize metrics.

        Args:
            registry: Optional custom registry (uses default if not provided)
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus_client not available - metrics disabled")
            self._enabled = False
            return

        self._enabled = True
        self._registry = registry or REGISTRY

        # === GAUGES (Current State) ===

        self.utilization_rate = Gauge(
            "resilience_utilization_rate",
            "Current system utilization rate (0.0-1.0)",
            ["component"],
            registry=self._registry,
        )

        self.utilization_level = Gauge(
            "resilience_utilization_level",
            "Current utilization level (0=GREEN, 1=YELLOW, 2=ORANGE, 3=RED, 4=BLACK)",
            registry=self._registry,
        )

        self.defense_level = Gauge(
            "resilience_defense_level",
            "Active defense in depth level (1=Prevention to 5=Emergency)",
            registry=self._registry,
        )

        self.load_shedding_level = Gauge(
            "resilience_load_shedding_level",
            "Current load shedding level (0=NORMAL to 5=CRITICAL)",
            registry=self._registry,
        )

        self.n1_compliant = Gauge(
            "resilience_n1_compliant",
            "Whether system passes N-1 contingency analysis (1=pass, 0=fail)",
            registry=self._registry,
        )

        self.n2_compliant = Gauge(
            "resilience_n2_compliant",
            "Whether system passes N-2 contingency analysis (1=pass, 0=fail)",
            registry=self._registry,
        )

        self.faculty_available = Gauge(
            "resilience_faculty_available",
            "Number of available faculty members",
            ["type"],  # "total", "on_duty", "on_leave"
            registry=self._registry,
        )

        self.coverage_rate = Gauge(
            "resilience_coverage_rate",
            "Current schedule coverage rate (0.0-1.0)",
            registry=self._registry,
        )

        self.buffer_remaining = Gauge(
            "resilience_buffer_remaining",
            "Remaining capacity buffer before threshold (0.0-1.0)",
            registry=self._registry,
        )

        self.redundancy_level = Gauge(
            "resilience_redundancy_level",
            "Redundancy level for critical services (0=BELOW, 1=N+0, 2=N+1, 3=N+2)",
            ["service"],
            registry=self._registry,
        )

        self.active_fallbacks = Gauge(
            "resilience_active_fallbacks",
            "Number of currently active fallback schedules",
            registry=self._registry,
        )

        self.suspended_activities = Gauge(
            "resilience_suspended_activities",
            "Number of currently suspended activities",
            registry=self._registry,
        )

        # === COUNTERS (Cumulative Events) ===

        self.crisis_activations = Counter(
            "resilience_crisis_activations_total",
            "Total number of crisis response activations",
            ["severity"],  # "minor", "moderate", "severe", "critical"
            registry=self._registry,
        )

        self.fallback_activations = Counter(
            "resilience_fallback_activations_total",
            "Total number of fallback schedule activations",
            ["scenario"],
            registry=self._registry,
        )

        self.load_shedding_events = Counter(
            "resilience_load_shedding_events_total",
            "Total number of load shedding level changes",
            ["from_level", "to_level"],
            registry=self._registry,
        )

        self.defense_activations = Counter(
            "resilience_defense_activations_total",
            "Total number of defense action activations",
            ["level", "action"],
            registry=self._registry,
        )

        self.health_check_failures = Counter(
            "resilience_health_check_failures_total",
            "Total number of failed health checks",
            ["reason"],
            registry=self._registry,
        )

        # === HISTOGRAMS (Distributions) ===

        self.health_check_duration = Histogram(
            "resilience_health_check_duration_seconds",
            "Duration of health check operations",
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self._registry,
        )

        self.contingency_analysis_duration = Histogram(
            "resilience_contingency_analysis_duration_seconds",
            "Duration of N-1/N-2 contingency analysis",
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
            registry=self._registry,
        )

        # === INFO ===

        self.info = Info(
            "resilience",
            "Resilience framework information",
            registry=self._registry,
        )
        self.info.info(
            {
                "version": "1.0.0",
                "framework": "tier1_critical",
                "components": "utilization,defense,contingency,fallback,sacrifice",
            }
        )

        logger.info("Resilience Prometheus metrics initialized")

    def update_utilization(
        self,
        rate: float,
        level: str,
        buffer: float = 0.0,
        component: str = "overall",
    ):
        """Update utilization metrics."""
        if not self._enabled:
            return

        level_map = {"green": 0, "yellow": 1, "orange": 2, "red": 3, "black": 4}

        self.utilization_rate.labels(component=component).set(rate)
        self.utilization_level.set(level_map.get(level.lower(), 0))
        self.buffer_remaining.set(buffer)

    def update_defense_level(self, level: int):
        """Update defense in depth level (1-5)."""
        if not self._enabled:
            return
        self.defense_level.set(level)

    def update_load_shedding(self, level: int, suspended_count: int = 0):
        """Update load shedding metrics."""
        if not self._enabled:
            return
        self.load_shedding_level.set(level)
        self.suspended_activities.set(suspended_count)

    def update_contingency_status(self, n1_pass: bool, n2_pass: bool):
        """Update contingency analysis status."""
        if not self._enabled:
            return
        self.n1_compliant.set(1 if n1_pass else 0)
        self.n2_compliant.set(1 if n2_pass else 0)

    def update_faculty_counts(
        self,
        total: int,
        on_duty: int = 0,
        on_leave: int = 0,
    ):
        """Update faculty availability metrics."""
        if not self._enabled:
            return
        self.faculty_available.labels(type="total").set(total)
        self.faculty_available.labels(type="on_duty").set(on_duty)
        self.faculty_available.labels(type="on_leave").set(on_leave)

    def update_coverage(self, rate: float):
        """Update coverage rate."""
        if not self._enabled:
            return
        self.coverage_rate.set(rate)

    def update_redundancy(self, service: str, level: int):
        """
        Update redundancy level for a service.

        Level: 0=BELOW, 1=N+0, 2=N+1, 3=N+2
        """
        if not self._enabled:
            return
        self.redundancy_level.labels(service=service).set(level)

    def update_active_fallbacks(self, count: int):
        """Update count of active fallback schedules."""
        if not self._enabled:
            return
        self.active_fallbacks.set(count)

    def record_crisis_activation(self, severity: str, reason: str = ""):
        """Record a crisis activation event."""
        if not self._enabled:
            return
        self.crisis_activations.labels(severity=severity).inc()
        logger.info(f"Metrics: Crisis activation recorded (severity={severity})")

    def record_fallback_activation(self, scenario: str):
        """Record a fallback schedule activation."""
        if not self._enabled:
            return
        self.fallback_activations.labels(scenario=scenario).inc()

    def record_load_shedding_change(self, from_level: int, to_level: int):
        """Record a load shedding level change."""
        if not self._enabled:
            return
        self.load_shedding_events.labels(
            from_level=str(from_level),
            to_level=str(to_level),
        ).inc()

    def record_defense_activation(self, level: int, action: str):
        """Record a defense action activation."""
        if not self._enabled:
            return
        self.defense_activations.labels(
            level=str(level),
            action=action,
        ).inc()

    def record_health_check_failure(self, reason: str):
        """Record a health check failure."""
        if not self._enabled:
            return
        self.health_check_failures.labels(reason=reason).inc()

    def time_health_check(self):
        """
        Context manager to time health check duration.

        Usage:
            with metrics.time_health_check():
                perform_health_check()
        """
        if not self._enabled:
            from contextlib import nullcontext

            return nullcontext()
        return self.health_check_duration.time()

    def time_contingency_analysis(self):
        """Context manager to time contingency analysis."""
        if not self._enabled:
            from contextlib import nullcontext

            return nullcontext()
        return self.contingency_analysis_duration.time()


# Global metrics instance
_metrics: ResilienceMetrics | None = None


def get_metrics() -> ResilienceMetrics:
    """Get or create the global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = ResilienceMetrics()
    return _metrics


def setup_metrics(registry: Optional["CollectorRegistry"] = None) -> ResilienceMetrics:
    """
    Set up metrics with optional custom registry.

    Call this during app startup to initialize metrics.
    """
    global _metrics
    _metrics = ResilienceMetrics(registry)
    return _metrics
