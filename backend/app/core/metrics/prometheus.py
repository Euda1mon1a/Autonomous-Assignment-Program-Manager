"""
Prometheus Metrics Registry.

Central registry for all Prometheus metrics in the application.
Provides type-safe metric definitions and helper methods.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        REGISTRY,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available - metrics disabled")


class MetricsRegistry:
    """
    Central Prometheus metrics registry for the Residency Scheduler.

    Provides comprehensive metrics for:
    - HTTP requests and responses
    - Database operations
    - Cache performance
    - Background task execution
    - Schedule generation
    - ACGME compliance monitoring
    - System resource usage
    - Error tracking

    Usage:
        metrics = MetricsRegistry()

        # Record HTTP request
        metrics.http_requests_total.labels(
            method="GET",
            endpoint="/api/v1/schedule",
            status_code=200
        ).inc()

        # Time database query
        with metrics.time_database_query("SELECT"):
            result = await db.execute(query)

        # Record cache hit
        metrics.cache_operations_total.labels(
            operation="get",
            result="hit"
        ).inc()
    """

    _instance: Optional["MetricsRegistry"] = None

    def __new__(cls):
        """Singleton pattern to ensure metrics are only registered once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize all Prometheus metrics."""
        if self._initialized:
            return

        self._initialized = True

        if not PROMETHEUS_AVAILABLE:
            self._enabled = False
            logger.warning("Metrics disabled - prometheus_client not available")
            return

        self._enabled = True
        logger.info("Initializing Prometheus metrics registry")

        # =====================================================================
        # HTTP / REQUEST METRICS
        # =====================================================================

        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests by method, endpoint, and status code",
            ["method", "endpoint", "status_code"],
            registry=REGISTRY,
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency by method and endpoint",
            ["method", "endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=REGISTRY,
        )

        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "Number of HTTP requests currently being processed",
            ["method", "endpoint"],
            registry=REGISTRY,
        )

        self.http_active_connections = Gauge(
            "http_active_connections",
            "Number of active HTTP connections",
            registry=REGISTRY,
        )

        self.http_request_size_bytes = Summary(
            "http_request_size_bytes",
            "HTTP request size in bytes",
            ["method", "endpoint"],
            registry=REGISTRY,
        )

        self.http_response_size_bytes = Summary(
            "http_response_size_bytes",
            "HTTP response size in bytes",
            ["method", "endpoint"],
            registry=REGISTRY,
        )

        # =====================================================================
        # DATABASE METRICS
        # =====================================================================

        self.db_queries_total = Counter(
            "db_queries_total",
            "Total database queries by operation type",
            ["operation"],  # SELECT, INSERT, UPDATE, DELETE
            registry=REGISTRY,
        )

        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query execution time by operation",
            ["operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=REGISTRY,
        )

        self.db_connections_active = Gauge(
            "db_connections_active",
            "Number of active database connections",
            registry=REGISTRY,
        )

        self.db_connections_idle = Gauge(
            "db_connections_idle",
            "Number of idle database connections in pool",
            registry=REGISTRY,
        )

        self.db_connection_pool_size = Gauge(
            "db_connection_pool_size",
            "Database connection pool size",
            registry=REGISTRY,
        )

        self.db_connection_wait_time_seconds = Histogram(
            "db_connection_wait_time_seconds",
            "Time spent waiting for database connection",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=REGISTRY,
        )

        self.db_transaction_duration_seconds = Histogram(
            "db_transaction_duration_seconds",
            "Database transaction duration",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=REGISTRY,
        )

        # =====================================================================
        # CACHE METRICS
        # =====================================================================

        self.cache_operations_total = Counter(
            "cache_operations_total",
            "Total cache operations by type and result",
            ["operation", "result"],  # operation: get/set/delete, result: hit/miss/error
            registry=REGISTRY,
        )

        self.cache_hit_ratio = Gauge(
            "cache_hit_ratio",
            "Cache hit ratio (hits / total_requests)",
            ["cache_name"],
            registry=REGISTRY,
        )

        self.cache_size_bytes = Gauge(
            "cache_size_bytes",
            "Current cache size in bytes",
            ["cache_name"],
            registry=REGISTRY,
        )

        self.cache_entries_count = Gauge(
            "cache_entries_count",
            "Number of entries in cache",
            ["cache_name"],
            registry=REGISTRY,
        )

        self.cache_operation_duration_seconds = Histogram(
            "cache_operation_duration_seconds",
            "Cache operation duration by operation type",
            ["operation"],
            buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
            registry=REGISTRY,
        )

        self.cache_evictions_total = Counter(
            "cache_evictions_total",
            "Total cache evictions by reason",
            ["reason"],  # ttl_expired, size_limit, manual
            registry=REGISTRY,
        )

        # =====================================================================
        # BACKGROUND TASK METRICS
        # =====================================================================

        self.background_tasks_total = Counter(
            "background_tasks_total",
            "Total background tasks by name and status",
            ["task_name", "status"],  # status: success, failure, retry
            registry=REGISTRY,
        )

        self.background_task_duration_seconds = Histogram(
            "background_task_duration_seconds",
            "Background task execution time by task name",
            ["task_name"],
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
            registry=REGISTRY,
        )

        self.background_tasks_in_progress = Gauge(
            "background_tasks_in_progress",
            "Number of background tasks currently executing",
            ["task_name"],
            registry=REGISTRY,
        )

        self.background_task_queue_depth = Gauge(
            "background_task_queue_depth",
            "Number of tasks waiting in queue",
            ["queue_name"],
            registry=REGISTRY,
        )

        self.celery_workers_active = Gauge(
            "celery_workers_active",
            "Number of active Celery workers",
            registry=REGISTRY,
        )

        # =====================================================================
        # SCHEDULE GENERATION METRICS
        # =====================================================================

        self.schedule_generation_total = Counter(
            "schedule_generation_total",
            "Total schedule generation attempts by algorithm and outcome",
            ["algorithm", "outcome"],  # algorithm: greedy/cp_sat/pulp, outcome: success/failure
            registry=REGISTRY,
        )

        self.schedule_generation_duration_seconds = Histogram(
            "schedule_generation_duration_seconds",
            "Schedule generation time by algorithm",
            ["algorithm"],
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0],
            registry=REGISTRY,
        )

        self.schedule_assignments_created = Counter(
            "schedule_assignments_created_total",
            "Total schedule assignments created",
            ["algorithm"],
            registry=REGISTRY,
        )

        self.schedule_optimization_score = Gauge(
            "schedule_optimization_score",
            "Current schedule optimization score",
            ["algorithm"],
            registry=REGISTRY,
        )

        # =====================================================================
        # ACGME COMPLIANCE METRICS
        # =====================================================================

        self.acgme_violations_total = Counter(
            "acgme_violations_total",
            "Total ACGME violations detected by type",
            ["violation_type"],  # 80_hour, 1_in_7, supervision_ratio
            registry=REGISTRY,
        )

        self.acgme_compliance_score = Gauge(
            "acgme_compliance_score",
            "ACGME compliance score (0.0-1.0)",
            ["rule"],  # 80_hour, 1_in_7, supervision
            registry=REGISTRY,
        )

        self.acgme_validation_duration_seconds = Histogram(
            "acgme_validation_duration_seconds",
            "Time to validate ACGME compliance",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=REGISTRY,
        )

        self.acgme_hours_worked = Histogram(
            "acgme_hours_worked",
            "Distribution of hours worked per week",
            buckets=[0, 20, 40, 60, 70, 75, 78, 80, 85, 90, 100],
            registry=REGISTRY,
        )

        # =====================================================================
        # ERROR TRACKING
        # =====================================================================

        self.errors_total = Counter(
            "errors_total",
            "Total errors by type, severity, and endpoint",
            ["error_type", "severity", "endpoint"],
            registry=REGISTRY,
        )

        self.exceptions_unhandled_total = Counter(
            "exceptions_unhandled_total",
            "Total unhandled exceptions by type",
            ["exception_type"],
            registry=REGISTRY,
        )

        self.validation_errors_total = Counter(
            "validation_errors_total",
            "Total validation errors by field",
            ["field"],
            registry=REGISTRY,
        )

        # =====================================================================
        # SYSTEM RESOURCE METRICS
        # =====================================================================

        self.system_cpu_usage_percent = Gauge(
            "system_cpu_usage_percent",
            "Current CPU usage percentage",
            registry=REGISTRY,
        )

        self.system_memory_usage_bytes = Gauge(
            "system_memory_usage_bytes",
            "Current memory usage in bytes",
            ["type"],  # rss, vms, shared
            registry=REGISTRY,
        )

        self.system_memory_available_bytes = Gauge(
            "system_memory_available_bytes",
            "Available system memory in bytes",
            registry=REGISTRY,
        )

        self.system_disk_usage_percent = Gauge(
            "system_disk_usage_percent",
            "Disk usage percentage",
            ["mount_point"],
            registry=REGISTRY,
        )

        self.system_open_file_descriptors = Gauge(
            "system_open_file_descriptors",
            "Number of open file descriptors",
            registry=REGISTRY,
        )

        # =====================================================================
        # APPLICATION INFO
        # =====================================================================

        self.app_info = Info(
            "residency_scheduler",
            "Application version and build information",
            registry=REGISTRY,
        )
        self.app_info.info({
            "version": "1.0.0",
            "application": "residency_scheduler",
            "framework": "fastapi",
        })

        logger.info("Prometheus metrics registry initialized successfully")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @contextmanager
    def time_database_query(self, operation: str):
        """
        Context manager to time database queries.

        Args:
            operation: Query operation type (SELECT, INSERT, UPDATE, DELETE)

        Usage:
            with metrics.time_database_query("SELECT"):
                result = await db.execute(query)
        """
        if not self._enabled:
            yield
            return

        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.db_query_duration_seconds.labels(operation=operation).observe(duration)
            self.db_queries_total.labels(operation=operation).inc()

    @contextmanager
    def time_cache_operation(self, operation: str):
        """
        Context manager to time cache operations.

        Args:
            operation: Cache operation (get, set, delete)

        Usage:
            with metrics.time_cache_operation("get"):
                value = await cache.get(key)
        """
        if not self._enabled:
            yield
            return

        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.cache_operation_duration_seconds.labels(operation=operation).observe(duration)

    @contextmanager
    def time_background_task(self, task_name: str):
        """
        Context manager to time background task execution.

        Args:
            task_name: Name of the background task

        Usage:
            with metrics.time_background_task("send_email"):
                await send_email()
        """
        if not self._enabled:
            yield
            return

        self.background_tasks_in_progress.labels(task_name=task_name).inc()
        start_time = time.perf_counter()
        try:
            yield
            self.background_tasks_total.labels(task_name=task_name, status="success").inc()
        except Exception:
            self.background_tasks_total.labels(task_name=task_name, status="failure").inc()
            raise
        finally:
            duration = time.perf_counter() - start_time
            self.background_task_duration_seconds.labels(task_name=task_name).observe(duration)
            self.background_tasks_in_progress.labels(task_name=task_name).dec()

    @contextmanager
    def time_schedule_generation(self, algorithm: str):
        """
        Context manager to time schedule generation.

        Args:
            algorithm: Algorithm used (greedy, cp_sat, pulp, hybrid)

        Usage:
            with metrics.time_schedule_generation("cp_sat"):
                schedule = generate_schedule()
        """
        if not self._enabled:
            yield
            return

        start_time = time.perf_counter()
        try:
            yield
            self.schedule_generation_total.labels(
                algorithm=algorithm,
                outcome="success"
            ).inc()
        except Exception:
            self.schedule_generation_total.labels(
                algorithm=algorithm,
                outcome="failure"
            ).inc()
            raise
        finally:
            duration = time.perf_counter() - start_time
            self.schedule_generation_duration_seconds.labels(algorithm=algorithm).observe(duration)

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
    ):
        """Record HTTP request metrics."""
        if not self._enabled:
            return

        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
        ).observe(duration)

    def record_cache_hit(self, operation: str = "get"):
        """Record cache hit."""
        if self._enabled:
            self.cache_operations_total.labels(operation=operation, result="hit").inc()

    def record_cache_miss(self, operation: str = "get"):
        """Record cache miss."""
        if self._enabled:
            self.cache_operations_total.labels(operation=operation, result="miss").inc()

    def record_error(
        self,
        error_type: str,
        severity: str = "error",
        endpoint: str = "unknown",
    ):
        """Record error occurrence."""
        if self._enabled:
            self.errors_total.labels(
                error_type=error_type,
                severity=severity,
                endpoint=endpoint,
            ).inc()

    def record_acgme_violation(self, violation_type: str):
        """Record ACGME compliance violation."""
        if self._enabled:
            self.acgme_violations_total.labels(violation_type=violation_type).inc()

    def update_acgme_compliance_score(self, rule: str, score: float):
        """Update ACGME compliance score (0.0-1.0)."""
        if self._enabled:
            self.acgme_compliance_score.labels(rule=rule).set(score)


# Global metrics instance
metrics: MetricsRegistry = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """
    Get the global metrics registry instance.

    Returns:
        MetricsRegistry: Global metrics instance
    """
    return metrics
