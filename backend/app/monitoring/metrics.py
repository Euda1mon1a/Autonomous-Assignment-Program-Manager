"""Prometheus metrics collection for comprehensive system monitoring."""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from prometheus_client import Counter, Gauge, Histogram, Summary


class MetricType(str, Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


# ============================================================================
# REQUEST METRICS (Task 2-3)
# ============================================================================

request_count = Counter(
    'request_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

request_latency = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

request_latency_summary = Summary(
    'request_latency_summary_seconds',
    'Request latency summary in seconds',
    ['method', 'endpoint']
)

request_size = Histogram(
    'request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 1000, 10000, 100000, 1000000)
)

response_size = Histogram(
    'response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint', 'status'],
    buckets=(100, 1000, 10000, 100000, 1000000)
)

concurrent_requests = Gauge(
    'concurrent_requests',
    'Number of concurrent requests',
    ['method', 'endpoint']
)

# ============================================================================
# ERROR RATE METRICS (Task 4)
# ============================================================================

error_count = Counter(
    'error_total',
    'Total number of errors',
    ['error_type', 'endpoint', 'method']
)

error_rate = Gauge(
    'error_rate',
    'Error rate as percentage',
    ['endpoint', 'method']
)

exception_count = Counter(
    'exception_total',
    'Total number of exceptions',
    ['exception_type', 'endpoint']
)

# ============================================================================
# DATABASE QUERY METRICS (Task 5)
# ============================================================================

db_query_count = Counter(
    'db_query_total',
    'Total number of database queries',
    ['operation', 'table', 'status']
)

db_query_latency = Histogram(
    'db_query_latency_seconds',
    'Database query latency in seconds',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

db_query_latency_summary = Summary(
    'db_query_latency_summary_seconds',
    'Database query latency summary',
    ['operation', 'table']
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Size of database connection pool'
)

db_connections_in_use = Gauge(
    'db_connections_in_use',
    'Number of database connections in use'
)

db_connections_available = Gauge(
    'db_connections_available',
    'Number of available database connections'
)

db_transaction_count = Counter(
    'db_transaction_total',
    'Total number of transactions',
    ['status']
)

db_transaction_duration = Histogram(
    'db_transaction_duration_seconds',
    'Database transaction duration in seconds',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0)
)

# ============================================================================
# CACHE METRICS (Task 6)
# ============================================================================

cache_hit = Counter(
    'cache_hit_total',
    'Total number of cache hits',
    ['cache_name']
)

cache_miss = Counter(
    'cache_miss_total',
    'Total number of cache misses',
    ['cache_name']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate as percentage',
    ['cache_name']
)

cache_size = Gauge(
    'cache_size_bytes',
    'Size of cache in bytes',
    ['cache_name']
)

cache_eviction = Counter(
    'cache_eviction_total',
    'Total number of cache evictions',
    ['cache_name']
)

redis_connection_count = Gauge(
    'redis_connection_count',
    'Number of Redis connections',
)

redis_memory_usage = Gauge(
    'redis_memory_usage_bytes',
    'Redis memory usage in bytes'
)

# ============================================================================
# SCHEDULER PERFORMANCE METRICS (Task 7)
# ============================================================================

schedule_generation_time = Histogram(
    'schedule_generation_seconds',
    'Time to generate schedule in seconds',
    ['block_count_range'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)
)

schedule_generation_success = Counter(
    'schedule_generation_success_total',
    'Total successful schedule generations'
)

schedule_generation_failure = Counter(
    'schedule_generation_failure_total',
    'Total failed schedule generations',
    ['failure_reason']
)

schedule_quality_score = Gauge(
    'schedule_quality_score',
    'Quality score of generated schedule (0-100)'
)

solver_iterations = Gauge(
    'solver_iterations',
    'Number of solver iterations for current generation'
)

solver_conflicts = Gauge(
    'solver_conflicts',
    'Number of remaining conflicts in current schedule'
)

schedule_rotation_balance = Gauge(
    'schedule_rotation_balance',
    'Balance score for rotation distribution (0-100)'
)

assignment_latency = Histogram(
    'assignment_latency_seconds',
    'Time to create assignment in seconds',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

# ============================================================================
# ACGME COMPLIANCE METRICS (Task 8)
# ============================================================================

compliance_check_count = Counter(
    'compliance_check_total',
    'Total compliance checks performed',
    ['check_type']
)

compliance_violation_count = Counter(
    'compliance_violation_total',
    'Total compliance violations found',
    ['violation_type']
)

compliance_rate = Gauge(
    'compliance_rate',
    'Overall ACGME compliance rate as percentage'
)

work_hour_violation = Counter(
    'work_hour_violation_total',
    'Total 80-hour rule violations',
    ['person_id', 'week_range']
)

rest_day_violation = Counter(
    'rest_day_violation_total',
    'Total 1-in-7 rule violations',
    ['person_id', 'period']
)

supervision_ratio_violation = Counter(
    'supervision_ratio_violation_total',
    'Total supervision ratio violations',
    ['training_level']
)

average_work_hours = Gauge(
    'average_work_hours',
    'Average work hours per week',
    ['training_level']
)

max_work_hours = Gauge(
    'max_work_hours',
    'Maximum work hours per week',
    ['training_level']
)

# ============================================================================
# RESILIENCE FRAMEWORK METRICS (Task 9)
# ============================================================================

resilience_health_score = Gauge(
    'resilience_health_score',
    'Overall resilience health score (0-100)'
)

resilience_level = Gauge(
    'resilience_level',
    'Current resilience defense level (0-5)',
    ['level_name']
)

utilization_rate = Gauge(
    'utilization_rate',
    'System utilization rate as percentage',
    ['resource']
)

n_minus_one_contingency_count = Gauge(
    'n_minus_one_contingency_count',
    'Number of N-1 contingency plans available'
)

n_minus_two_contingency_count = Gauge(
    'n_minus_two_contingency_count',
    'Number of N-2 contingency plans available'
)

recovery_time_objective = Gauge(
    'recovery_time_objective_seconds',
    'Recovery time objective in seconds'
)

recovery_distance = Gauge(
    'recovery_distance',
    'Minimum edits needed to recover from N-1 shock'
)

cascade_failure_risk = Gauge(
    'cascade_failure_risk',
    'Risk of cascade failure (0-100)'
)

burnout_reproduction_number = Gauge(
    'burnout_reproduction_number',
    'Burnout reproduction number (Rt)',
    ['person_id']
)

defense_layer_status = Gauge(
    'defense_layer_status',
    'Status of defense layer (1=green, 2=yellow, 3=orange, 4=red, 5=black)',
    ['layer']
)

# ============================================================================
# SWAP PROCESSING METRICS (Task 10)
# ============================================================================

swap_request_count = Counter(
    'swap_request_total',
    'Total swap requests received'
)

swap_execution_count = Counter(
    'swap_execution_total',
    'Total swap executions',
    ['swap_type', 'status']
)

swap_execution_time = Histogram(
    'swap_execution_seconds',
    'Time to execute swap in seconds',
    ['swap_type'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0)
)

swap_validation_failure = Counter(
    'swap_validation_failure_total',
    'Total swap validation failures',
    ['reason']
)

swap_queue_depth = Gauge(
    'swap_queue_depth',
    'Number of pending swaps in queue'
)

swap_compatibility_check_time = Histogram(
    'swap_compatibility_check_seconds',
    'Time to check swap compatibility',
    buckets=(0.01, 0.05, 0.1, 0.5)
)

# ============================================================================
# USER ACTIVITY METRICS (Task 11)
# ============================================================================

active_users = Gauge(
    'active_users',
    'Number of active users',
    ['role']
)

user_action_count = Counter(
    'user_action_total',
    'Total user actions',
    ['action_type', 'role']
)

login_count = Counter(
    'login_total',
    'Total login attempts',
    ['status']
)

session_duration = Histogram(
    'session_duration_seconds',
    'User session duration in seconds',
    buckets=(60, 300, 600, 1800, 3600, 7200)
)

api_key_usage = Counter(
    'api_key_usage_total',
    'API key usage count',
    ['api_key_id', 'endpoint']
)

user_role_distribution = Gauge(
    'user_role_distribution',
    'Distribution of users by role',
    ['role']
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_request_metrics(
    method: str,
    endpoint: str,
    status: int,
    latency: float,
    request_size: int,
    response_size: int
) -> None:
    """
    Record HTTP request metrics.

    Args:
        method: HTTP method
        endpoint: API endpoint
        status: HTTP status code
        latency: Request latency in seconds
        request_size: Request size in bytes
        response_size: Response size in bytes
    """
    request_count.labels(method=method, endpoint=endpoint, status=status).inc()
    request_latency.labels(method=method, endpoint=endpoint).observe(latency)
    request_latency_summary.labels(method=method, endpoint=endpoint).observe(latency)
    request_size.labels(method=method, endpoint=endpoint).observe(request_size)
    response_size.labels(method=method, endpoint=endpoint, status=status).observe(response_size)


def record_error(
    error_type: str,
    endpoint: str,
    method: str
) -> None:
    """
    Record error metrics.

    Args:
        error_type: Type of error
        endpoint: API endpoint where error occurred
        method: HTTP method
    """
    error_count.labels(error_type=error_type, endpoint=endpoint, method=method).inc()


def record_database_query(
    operation: str,
    table: str,
    latency: float,
    status: str = 'success'
) -> None:
    """
    Record database query metrics.

    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        latency: Query latency in seconds
        status: Query status (success/failure)
    """
    db_query_count.labels(operation=operation, table=table, status=status).inc()
    db_query_latency.labels(operation=operation, table=table).observe(latency)
    db_query_latency_summary.labels(operation=operation, table=table).observe(latency)


def record_cache_hit(cache_name: str) -> None:
    """
    Record cache hit.

    Args:
        cache_name: Name of cache
    """
    cache_hit.labels(cache_name=cache_name).inc()


def record_cache_miss(cache_name: str) -> None:
    """
    Record cache miss.

    Args:
        cache_name: Name of cache
    """
    cache_miss.labels(cache_name=cache_name).inc()


def update_cache_hit_rate(cache_name: str, hits: int, total: int) -> None:
    """
    Update cache hit rate.

    Args:
        cache_name: Name of cache
        hits: Number of cache hits
        total: Total cache accesses
    """
    rate = (hits / total * 100) if total > 0 else 0
    cache_hit_rate.labels(cache_name=cache_name).set(rate)


def record_schedule_generation(
    generation_time: float,
    success: bool,
    block_count: int,
    quality_score: float = 0.0,
    failure_reason: Optional[str] = None
) -> None:
    """
    Record schedule generation metrics.

    Args:
        generation_time: Time to generate schedule in seconds
        success: Whether generation was successful
        block_count: Number of blocks in schedule
        quality_score: Quality score of generated schedule
        failure_reason: Reason for failure if unsuccessful
    """
    # Determine block count range for histogram bucketing
    if block_count <= 100:
        block_range = "small"
    elif block_count <= 300:
        block_range = "medium"
    else:
        block_range = "large"

    schedule_generation_time.labels(block_count_range=block_range).observe(generation_time)

    if success:
        schedule_generation_success.inc()
        schedule_quality_score.set(quality_score)
    else:
        schedule_generation_failure.labels(failure_reason=failure_reason or "unknown").inc()


def record_compliance_check(
    check_type: str,
    violation_count: int = 0
) -> None:
    """
    Record compliance check metrics.

    Args:
        check_type: Type of compliance check
        violation_count: Number of violations found
    """
    compliance_check_count.labels(check_type=check_type).inc()
    if violation_count > 0:
        compliance_violation_count.labels(violation_type=check_type).inc(violation_count)


def record_swap_execution(
    swap_type: str,
    execution_time: float,
    status: str,
    validation_failures: int = 0
) -> None:
    """
    Record swap execution metrics.

    Args:
        swap_type: Type of swap (one-to-one, absorb)
        execution_time: Time to execute swap in seconds
        status: Execution status (success/failure)
        validation_failures: Number of validation failures
    """
    swap_execution_count.labels(swap_type=swap_type, status=status).inc()
    swap_execution_time.labels(swap_type=swap_type).observe(execution_time)

    if validation_failures > 0:
        swap_validation_failure.labels(reason="validation").inc(validation_failures)


def update_resilience_metrics(
    health_score: float,
    utilization: float,
    cascade_risk: float,
    recovery_distance_val: int
) -> None:
    """
    Update resilience framework metrics.

    Args:
        health_score: Overall health score (0-100)
        utilization: System utilization rate (0-100)
        cascade_risk: Cascade failure risk (0-100)
        recovery_distance_val: Minimum edits to recover from N-1
    """
    resilience_health_score.set(health_score)
    utilization_rate.labels(resource='overall').set(utilization)
    cascade_failure_risk.set(cascade_risk)
    recovery_distance.set(recovery_distance_val)


def record_user_action(action_type: str, role: str) -> None:
    """
    Record user action metrics.

    Args:
        action_type: Type of action performed
        role: User role
    """
    user_action_count.labels(action_type=action_type, role=role).inc()


def update_active_users(role: str, count: int) -> None:
    """
    Update active users count.

    Args:
        role: User role
        count: Number of active users
    """
    active_users.labels(role=role).set(count)


# ============================================================================
# METRIC EXPORT HELPERS
# ============================================================================

def get_all_metrics() -> Dict[str, Any]:
    """
    Get all collected metrics for export.

    Returns:
        Dictionary of all metrics
    """
    return {
        'request_metrics': {
            'total_requests': request_count._metrics,
            'latency': request_latency._metrics,
            'error_rate': error_rate._metrics,
        },
        'database_metrics': {
            'query_count': db_query_count._metrics,
            'query_latency': db_query_latency._metrics,
            'connection_pool_size': db_connection_pool_size._value,
        },
        'cache_metrics': {
            'hit_count': cache_hit._metrics,
            'miss_count': cache_miss._metrics,
            'hit_rate': cache_hit_rate._metrics,
        },
        'scheduler_metrics': {
            'generation_time': schedule_generation_time._metrics,
            'quality_score': schedule_quality_score._value,
            'conflicts': solver_conflicts._value,
        },
        'compliance_metrics': {
            'check_count': compliance_check_count._metrics,
            'violation_count': compliance_violation_count._metrics,
            'compliance_rate': compliance_rate._value,
        },
        'resilience_metrics': {
            'health_score': resilience_health_score._value,
            'utilization_rate': utilization_rate._metrics,
            'cascade_risk': cascade_failure_risk._value,
        },
        'swap_metrics': {
            'request_count': swap_request_count._value,
            'execution_count': swap_execution_count._metrics,
            'queue_depth': swap_queue_depth._value,
        },
        'user_metrics': {
            'active_users': active_users._metrics,
            'login_count': login_count._metrics,
            'action_count': user_action_count._metrics,
        },
    }


def reset_metrics() -> None:
    """Reset all metrics (use with caution)."""
    # Note: Prometheus client doesn't support direct reset
    # This is a placeholder for future implementation
    pass
