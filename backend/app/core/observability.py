"""
Observability metrics for authentication, idempotency, and scheduling.

Exposes Prometheus metrics for:

Authentication:
- auth_tokens_issued_total: Tokens created (by type)
- auth_tokens_blacklisted_total: Tokens revoked (by reason)
- auth_verification_failures_total: Failed verifications (by reason)

Idempotency:
- idempotency_requests_total: Requests by outcome (hit/miss/conflict/pending)
- idempotency_cache_size: Current number of cached requests
- idempotency_lookup_duration_seconds: Lookup latency histogram

Scheduling:
- schedule_generation_total: Generations by algorithm and outcome
- schedule_generation_duration_seconds: Generation latency by algorithm
- schedule_violations_total: ACGME violations detected
- schedule_assignments_total: Assignments created

Request Correlation:
- Middleware to add X-Request-ID header for distributed tracing
"""

import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger, set_request_id as set_logging_request_id

logger = get_logger(__name__)

# Context variable for request correlation ID
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

try:
    from prometheus_client import REGISTRY, Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available - metrics disabled")


def get_request_id() -> Optional[str]:
    """Get the current request's correlation ID."""
    return request_id_ctx.get()


class ObservabilityMetrics:
    """
    Prometheus metrics for auth, idempotency, and scheduling observability.

    Usage:
        metrics = ObservabilityMetrics()

        # Auth events
        metrics.record_token_issued("access")
        metrics.record_token_blacklisted("logout")
        metrics.record_auth_failure("expired")

        # Idempotency events
        metrics.record_idempotency_hit()
        metrics.record_idempotency_miss()

        # Scheduling events
        with metrics.time_schedule_generation("cp_sat"):
            result = generate()
        metrics.record_schedule_success("cp_sat", assignments=50)
    """

    _instance: Optional["ObservabilityMetrics"] = None

    def __new__(cls):
        """Singleton pattern to ensure metrics are only registered once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize metrics (only once due to singleton)."""
        if self._initialized:
            return

        self._initialized = True

        if not PROMETHEUS_AVAILABLE:
            self._enabled = False
            return

        self._enabled = True

        # === AUTH METRICS ===
        self.tokens_issued = Counter(
            "auth_tokens_issued_total",
            "Total JWT tokens issued",
            ["token_type"],  # access, refresh
            registry=REGISTRY,
        )

        self.tokens_blacklisted = Counter(
            "auth_tokens_blacklisted_total",
            "Total tokens added to blacklist",
            ["reason"],  # logout, revoked, password_change
            registry=REGISTRY,
        )

        self.auth_failures = Counter(
            "auth_verification_failures_total",
            "Total authentication verification failures",
            ["reason"],  # expired, invalid_signature, blacklisted, malformed
            registry=REGISTRY,
        )

        # === IDEMPOTENCY METRICS ===
        self.idempotency_requests = Counter(
            "idempotency_requests_total",
            "Total idempotency requests by outcome",
            ["outcome"],  # cache_hit, cache_miss, conflict, pending
            registry=REGISTRY,
        )

        self.idempotency_cache_size = Gauge(
            "idempotency_cache_size",
            "Current number of non-expired idempotency records",
            registry=REGISTRY,
        )

        self.idempotency_lookup_duration = Histogram(
            "idempotency_lookup_duration_seconds",
            "Time to lookup idempotency key",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=REGISTRY,
        )

        # === SCHEDULING METRICS ===
        self.schedule_generations = Counter(
            "schedule_generation_total",
            "Total schedule generation attempts",
            ["algorithm", "outcome"],  # algorithm: greedy/cp_sat/pulp/hybrid, outcome: success/failure
            registry=REGISTRY,
        )

        self.schedule_duration = Histogram(
            "schedule_generation_duration_seconds",
            "Schedule generation duration by algorithm",
            ["algorithm"],
            buckets=[0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600],
            registry=REGISTRY,
        )

        self.schedule_violations = Counter(
            "schedule_violations_total",
            "Total ACGME violations detected during generation",
            ["violation_type"],  # 80_hour, 1_in_7, supervision_ratio, etc.
            registry=REGISTRY,
        )

        self.schedule_assignments = Counter(
            "schedule_assignments_total",
            "Total assignments created",
            ["algorithm"],
            registry=REGISTRY,
        )

    # === AUTH METHODS ===

    def record_token_issued(self, token_type: str = "access"):
        """Record a token being issued."""
        if self._enabled:
            self.tokens_issued.labels(token_type=token_type).inc()

    def record_token_blacklisted(self, reason: str = "logout"):
        """Record a token being blacklisted."""
        if self._enabled:
            self.tokens_blacklisted.labels(reason=reason).inc()

    def record_auth_failure(self, reason: str):
        """Record an authentication failure."""
        if self._enabled:
            self.auth_failures.labels(reason=reason).inc()

    # === IDEMPOTENCY METHODS ===

    def record_idempotency_hit(self):
        """Record a cache hit (returning cached response)."""
        if self._enabled:
            self.idempotency_requests.labels(outcome="cache_hit").inc()

    def record_idempotency_miss(self):
        """Record a cache miss (processing new request)."""
        if self._enabled:
            self.idempotency_requests.labels(outcome="cache_miss").inc()

    def record_idempotency_conflict(self):
        """Record a key conflict (same key, different body)."""
        if self._enabled:
            self.idempotency_requests.labels(outcome="conflict").inc()

    def record_idempotency_pending(self):
        """Record hitting a pending request."""
        if self._enabled:
            self.idempotency_requests.labels(outcome="pending").inc()

    def set_idempotency_cache_size(self, size: int):
        """Update the current cache size gauge."""
        if self._enabled:
            self.idempotency_cache_size.set(size)

    def time_idempotency_lookup(self) -> "IdempotencyTimer":
        """Context manager to time idempotency lookups."""
        return IdempotencyTimer(self)

    # === SCHEDULING METHODS ===

    def record_schedule_success(self, algorithm: str, assignments: int = 0):
        """Record successful schedule generation."""
        if self._enabled:
            self.schedule_generations.labels(algorithm=algorithm, outcome="success").inc()
            if assignments > 0:
                self.schedule_assignments.labels(algorithm=algorithm).inc(assignments)

    def record_schedule_failure(self, algorithm: str):
        """Record failed schedule generation."""
        if self._enabled:
            self.schedule_generations.labels(algorithm=algorithm, outcome="failure").inc()

    def record_violation(self, violation_type: str):
        """Record an ACGME violation."""
        if self._enabled:
            self.schedule_violations.labels(violation_type=violation_type).inc()

    def time_schedule_generation(self, algorithm: str) -> "ScheduleTimer":
        """Context manager to time schedule generation."""
        return ScheduleTimer(self, algorithm)


class IdempotencyTimer:
    """Context manager for timing idempotency lookups."""

    def __init__(self, metrics: ObservabilityMetrics):
        self.metrics = metrics
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.metrics._enabled and self.start_time:
            duration = time.perf_counter() - self.start_time
            self.metrics.idempotency_lookup_duration.observe(duration)
        return False


class ScheduleTimer:
    """Context manager for timing schedule generation."""

    def __init__(self, metrics: ObservabilityMetrics, algorithm: str):
        self.metrics = metrics
        self.algorithm = algorithm
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.metrics._enabled and self.start_time:
            duration = time.perf_counter() - self.start_time
            self.metrics.schedule_duration.labels(algorithm=self.algorithm).observe(duration)
        return False


# Global metrics instance
metrics = ObservabilityMetrics()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add X-Request-ID header for request correlation.

    If the client provides X-Request-ID, it's used as-is.
    Otherwise, a new UUID is generated.

    The request ID is:
    1. Stored in context variable for logging
    2. Added to response headers
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in context variable for observability metrics
        token = request_id_ctx.set(request_id)

        # Also set in logging context for structured logging
        set_logging_request_id(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)


def with_request_id(func: Callable) -> Callable:
    """
    Decorator to include request ID in log messages.

    With loguru integration, the request ID is automatically included
    in log output when set via the RequestIDMiddleware.

    Usage:
        @with_request_id
        def my_function():
            logger.info("Processing...")  # Will include request ID
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        request_id = get_request_id()
        if request_id:
            # Set request ID in logging context for this call
            set_logging_request_id(request_id)
        return func(*args, **kwargs)

    return wrapper
