"""
Metrics API Endpoints.

Provides endpoints for:
- Prometheus metrics export (/metrics)
- Metrics health check
- Custom metrics queries
- Metrics documentation
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse, Response

from app.core.metrics import get_metrics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics"])


@router.get(
    "/metrics/health",
    summary="Metrics Health Check",
    description="Check if metrics collection is enabled and functioning",
)
async def metrics_health() -> dict[str, Any]:
    """
    Check metrics system health.

    Returns:
        Health status of metrics collection system

    Examples:
        >>> GET /api/v1/metrics/health
        {
            "status": "healthy",
            "metrics_enabled": true,
            "collectors": ["http", "database", "cache", "schedule", "system"],
            "prometheus_available": true
        }
    """
    metrics = get_metrics()

    # Check if prometheus is available
    prometheus_available = metrics._enabled

    # List active metric collectors
    collectors = []
    if prometheus_available:
        collectors = [
            "http",
            "database",
            "cache",
            "background_tasks",
            "schedule",
            "acgme_compliance",
            "errors",
            "system_resources",
        ]

    return {
        "status": "healthy" if prometheus_available else "degraded",
        "metrics_enabled": prometheus_available,
        "collectors": collectors,
        "prometheus_available": prometheus_available,
        "message": "Metrics collection operational"
        if prometheus_available
        else "Metrics disabled - prometheus_client not available",
    }


@router.get(
    "/metrics/info",
    summary="Metrics Information",
    description="Get information about available metrics and their descriptions",
)
async def metrics_info() -> dict[str, Any]:
    """
    Get information about available metrics.

    Returns:
        Documentation of all available metrics

    Examples:
        >>> GET /api/v1/metrics/info
        {
            "metrics": {
                "http": [...],
                "database": [...],
                ...
            }
        }
    """
    metrics_documentation = {
        "http": {
            "http_requests_total": {
                "type": "counter",
                "description": "Total HTTP requests by method, endpoint, and status code",
                "labels": ["method", "endpoint", "status_code"],
            },
            "http_request_duration_seconds": {
                "type": "histogram",
                "description": "HTTP request latency by method and endpoint",
                "labels": ["method", "endpoint"],
            },
            "http_requests_in_progress": {
                "type": "gauge",
                "description": "Number of HTTP requests currently being processed",
                "labels": ["method", "endpoint"],
            },
            "http_active_connections": {
                "type": "gauge",
                "description": "Number of active HTTP connections",
                "labels": [],
            },
            "http_request_size_bytes": {
                "type": "summary",
                "description": "HTTP request size in bytes",
                "labels": ["method", "endpoint"],
            },
            "http_response_size_bytes": {
                "type": "summary",
                "description": "HTTP response size in bytes",
                "labels": ["method", "endpoint"],
            },
        },
        "database": {
            "db_queries_total": {
                "type": "counter",
                "description": "Total database queries by operation type",
                "labels": ["operation"],
            },
            "db_query_duration_seconds": {
                "type": "histogram",
                "description": "Database query execution time by operation",
                "labels": ["operation"],
            },
            "db_connections_active": {
                "type": "gauge",
                "description": "Number of active database connections",
                "labels": [],
            },
            "db_connection_pool_size": {
                "type": "gauge",
                "description": "Database connection pool size",
                "labels": [],
            },
        },
        "cache": {
            "cache_operations_total": {
                "type": "counter",
                "description": "Total cache operations by type and result",
                "labels": ["operation", "result"],
            },
            "cache_hit_ratio": {
                "type": "gauge",
                "description": "Cache hit ratio (hits / total_requests)",
                "labels": ["cache_name"],
            },
            "cache_operation_duration_seconds": {
                "type": "histogram",
                "description": "Cache operation duration by operation type",
                "labels": ["operation"],
            },
        },
        "background_tasks": {
            "background_tasks_total": {
                "type": "counter",
                "description": "Total background tasks by name and status",
                "labels": ["task_name", "status"],
            },
            "background_task_duration_seconds": {
                "type": "histogram",
                "description": "Background task execution time by task name",
                "labels": ["task_name"],
            },
            "background_tasks_in_progress": {
                "type": "gauge",
                "description": "Number of background tasks currently executing",
                "labels": ["task_name"],
            },
            "background_task_queue_depth": {
                "type": "gauge",
                "description": "Number of tasks waiting in queue",
                "labels": ["queue_name"],
            },
        },
        "schedule": {
            "schedule_generation_total": {
                "type": "counter",
                "description": "Total schedule generation attempts by algorithm and outcome",
                "labels": ["algorithm", "outcome"],
            },
            "schedule_generation_duration_seconds": {
                "type": "histogram",
                "description": "Schedule generation time by algorithm",
                "labels": ["algorithm"],
            },
            "schedule_optimization_score": {
                "type": "gauge",
                "description": "Current schedule optimization score",
                "labels": ["algorithm"],
            },
        },
        "acgme_compliance": {
            "acgme_violations_total": {
                "type": "counter",
                "description": "Total ACGME violations detected by type",
                "labels": ["violation_type"],
            },
            "acgme_compliance_score": {
                "type": "gauge",
                "description": "ACGME compliance score (0.0-1.0)",
                "labels": ["rule"],
            },
            "acgme_validation_duration_seconds": {
                "type": "histogram",
                "description": "Time to validate ACGME compliance",
                "labels": [],
            },
        },
        "errors": {
            "errors_total": {
                "type": "counter",
                "description": "Total errors by type, severity, and endpoint",
                "labels": ["error_type", "severity", "endpoint"],
            },
            "exceptions_unhandled_total": {
                "type": "counter",
                "description": "Total unhandled exceptions by type",
                "labels": ["exception_type"],
            },
        },
        "system": {
            "system_cpu_usage_percent": {
                "type": "gauge",
                "description": "Current CPU usage percentage",
                "labels": [],
            },
            "system_memory_usage_bytes": {
                "type": "gauge",
                "description": "Current memory usage in bytes",
                "labels": ["type"],
            },
            "system_disk_usage_percent": {
                "type": "gauge",
                "description": "Disk usage percentage",
                "labels": ["mount_point"],
            },
        },
    }

    return {
        "metrics": metrics_documentation,
        "total_metrics": sum(
            len(category) for category in metrics_documentation.values()
        ),
        "categories": list(metrics_documentation.keys()),
    }


@router.get(
    "/metrics/export",
    summary="Export Metrics (Prometheus Format)",
    description="Export all metrics in Prometheus text format",
    response_class=PlainTextResponse,
)
async def export_metrics(request: Request) -> Response:
    """
    Export metrics in Prometheus text format.

    This endpoint provides the same functionality as /metrics but under
    the API router for consistency with other endpoints.

    Returns:
        Prometheus text format metrics

    Note:
        In production, use the /metrics endpoint directly (not under /api/v1)
        as it's optimized for Prometheus scraping.

    Examples:
        >>> GET /api/v1/metrics/export
        # HELP http_requests_total Total HTTP requests
        # TYPE http_requests_total counter
        http_requests_total{method="GET",endpoint="/api/v1/schedule",status_code="200"} 42.0
        ...
    """
    try:
        from prometheus_client import REGISTRY, generate_latest

        # Generate metrics in Prometheus text format
        metrics_output = generate_latest(REGISTRY)

        return Response(
            content=metrics_output,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Metrics export unavailable - prometheus_client not installed",
        )


@router.get(
    "/metrics/summary",
    summary="Metrics Summary",
    description="Get high-level summary of current metrics",
)
async def metrics_summary() -> dict[str, Any]:
    """
    Get a summary of current metrics values.

    Returns:
        Summary of key metrics

    Examples:
        >>> GET /api/v1/metrics/summary
        {
            "http": {
                "total_requests": 1234,
                "active_connections": 5,
                "avg_response_time_ms": 45.2
            },
            "database": {
                "active_connections": 3,
                "pool_size": 10
            },
            ...
        }
    """
    metrics = get_metrics()

    if not metrics._enabled:
        return {
            "status": "disabled",
            "message": "Metrics collection is disabled",
        }

    # Note: Extracting current values from Prometheus metrics is complex
    # This is a simplified version showing structure
    # In production, you might want to use prometheus_client's internal APIs

    summary = {
        "status": "enabled",
        "timestamp": None,  # Would add current timestamp
        "http": {
            "active_connections": "See /metrics endpoint",
            "requests_in_progress": "See /metrics endpoint",
        },
        "database": {
            "active_connections": "See /metrics endpoint",
            "pool_size": "See /metrics endpoint",
        },
        "cache": {
            "hit_ratio": "See /metrics endpoint",
        },
        "background_tasks": {
            "tasks_in_progress": "See /metrics endpoint",
            "queue_depth": "See /metrics endpoint",
        },
        "message": "For detailed metrics, query the /metrics endpoint directly",
    }

    return summary


@router.post(
    "/metrics/reset",
    summary="Reset Metrics (Development Only)",
    description="Reset all metric counters (only available in debug mode)",
)
async def reset_metrics() -> dict[str, Any]:
    """
    Reset all metrics counters.

    WARNING: This endpoint should only be used in development/testing.
    In production, metrics should never be reset.

    Returns:
        Reset confirmation

    Raises:
        HTTPException: If not in debug mode
    """
    from app.core.config import get_settings

    settings = get_settings()

    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Metrics reset is only available in debug mode",
        )

    # Note: Prometheus metrics cannot easily be reset
    # This would require recreating the metrics registry
    # For now, return a warning

    return {
        "status": "warning",
        "message": "Prometheus metrics cannot be reset without restarting the application",
        "recommendation": "Restart the application to reset metrics",
    }
