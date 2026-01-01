"""
Enhanced health check API endpoints.

Provides comprehensive health monitoring endpoints:
- GET /health/live - Liveness probe (lightweight)
- GET /health/ready - Readiness probe (critical dependencies)
- GET /health/detailed - Detailed health status (all services)
- GET /health/services/{service_name} - Individual service health
- GET /health/history - Health check history
- GET /health/metrics - Health check metrics
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.health.aggregator import AggregatedHealthResult, HealthAggregator

logger = logging.getLogger(__name__)

router = APIRouter()

# Global health aggregator instance
health_aggregator = HealthAggregator(
    enable_history=True, history_size=100, timeout=10.0
)


@router.get(
    "/live",
    response_model=dict[str, Any],
    summary="Liveness Probe",
    description="Lightweight endpoint indicating if the application is running and responsive. Used by orchestrators (Kubernetes, Docker) to determine if the container should be restarted.",
    tags=["Health"],
    responses={
        200: {
            "description": "Application is alive and responding",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:00.000000",
                        "service": "residency-scheduler"
                    }
                }
            }
        }
    }
)
async def liveness_probe() -> dict[str, Any]:
    """
    Liveness probe endpoint.

    This is a lightweight endpoint that indicates if the application
    is running and responsive. Used by orchestrators (Kubernetes, Docker)
    to determine if the container should be restarted.

    Returns:
        Dictionary with liveness status (always healthy if responding)

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00.000000",
            "service": "residency-scheduler"
        }
    """
    return await health_aggregator.check_liveness()


@router.get(
    "/ready",
    response_model=dict[str, Any],
    summary="Readiness Probe",
    description="Checks if the application is ready to serve traffic by verifying critical dependencies (database, Redis). Used by load balancers and orchestrators to determine if traffic should be routed to this instance.",
    tags=["Health"],
    responses={
        200: {
            "description": "Service is ready to serve traffic",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:00.000000",
                        "database": True,
                        "redis": True
                    }
                }
            }
        },
        503: {
            "description": "Service is not ready - dependencies unhealthy"
        }
    }
)
async def readiness_probe() -> dict[str, Any]:
    """
    Readiness probe endpoint.

    Checks if the application is ready to serve traffic by verifying
    critical dependencies (database, Redis). Used by load balancers
    and orchestrators to determine if traffic should be routed to this instance.

    Returns:
        Dictionary with readiness status

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00.000000",
            "database": true,
            "redis": true
        }

    Status Codes:
        - 200: Service is ready
        - 503: Service is not ready (dependencies unhealthy)
    """
    result = await health_aggregator.check_readiness()

    if result["status"] == "unhealthy":
        raise HTTPException(
            status_code=503, detail="Service not ready - dependencies unhealthy"
        )

    return result


@router.get(
    "/detailed",
    response_model=AggregatedHealthResult,
    summary="Detailed Health Check",
    description="Performs comprehensive health checks across all services including database, Redis, Celery, and circuit breakers. Returns detailed status information and performance metrics. More resource-intensive than liveness/readiness probes.",
    tags=["Health"],
    responses={
        200: {
            "description": "Detailed health check completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:00.000000",
                        "services": {
                            "database": {
                                "service": "database",
                                "status": "healthy",
                                "response_time_ms": 12.5
                            }
                        },
                        "summary": {
                            "total_services": 3,
                            "healthy_count": 3,
                            "degraded_count": 0,
                            "unhealthy_count": 0
                        }
                    }
                }
            }
        }
    }
)
async def detailed_health() -> AggregatedHealthResult:
    """
    Detailed health check endpoint.

    Performs comprehensive health checks across all services and returns
    detailed status information. This is more resource-intensive than
    liveness/readiness probes and should not be called frequently.

    Returns:
        AggregatedHealthResult with detailed status for all services

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00.000000",
            "services": {
                "database": {
                    "service": "database",
                    "status": "healthy",
                    "response_time_ms": 12.5,
                    "details": {
                        "database_version": "PostgreSQL 15.3",
                        "connection_pool": {...}
                    }
                },
                "redis": {...},
                "celery": {...}
            },
            "summary": {
                "total_services": 3,
                "healthy_count": 3,
                "degraded_count": 0,
                "unhealthy_count": 0,
                "avg_response_time_ms": 15.2
            }
        }

    Status Codes:
        - 200: Health check completed (status may still indicate issues)
    """
    return await health_aggregator.check_detailed()


@router.get(
    "/services/{service_name}",
    response_model=dict[str, Any],
    summary="Check Specific Service",
    description="Check health status of a specific service (database, redis, celery, or circuit_breakers). Returns detailed status information for the requested service only.",
    tags=["Health"],
    responses={
        200: {
            "description": "Service health check completed",
            "content": {
                "application/json": {
                    "example": {
                        "service": "database",
                        "status": "healthy",
                        "response_time_ms": 12.5,
                        "timestamp": "2024-01-15T10:30:00.000000"
                    }
                }
            }
        },
        404: {
            "description": "Unknown service name"
        }
    }
)
async def check_service(service_name: str) -> dict[str, Any]:
    """
    Check health of a specific service.

    Performs a health check on a single service and returns detailed
    status information for that service only.

    Args:
        service_name: Name of service to check (database, redis, celery, circuit_breakers)

    Returns:
        HealthCheckResult for the requested service

    Example Response:
        {
            "service": "database",
            "status": "healthy",
            "response_time_ms": 12.5,
            "timestamp": "2024-01-15T10:30:00.000000",
            "details": {
                "database_version": "PostgreSQL 15.3",
                "connection_pool": {
                    "size": 10,
                    "checked_in": 8,
                    "checked_out": 2
                }
            }
        }

    Status Codes:
        - 200: Health check completed
        - 404: Unknown service name

    Raises:
        HTTPException: If service name is not recognized
    """
    try:
        result = await health_aggregator.check_service(service_name)
        return result.model_dump()

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service_name}. Valid services: database, redis, celery, circuit_breakers",
        )


@router.get(
    "/history",
    response_model=dict[str, Any],
    summary="Get Health Check History",
    description="Returns historical health check results for trend analysis and debugging purposes. Useful for identifying patterns in service degradation or intermittent failures.",
    tags=["Health"],
    responses={
        200: {
            "description": "Health check history retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "count": 10,
                        "limit": 10,
                        "history": [
                            {
                                "status": "healthy",
                                "timestamp": "2024-01-15T10:30:00.000000",
                                "services": {},
                                "summary": {}
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_health_history(
    limit: int = Query(
        10, ge=1, le=100, description="Number of history entries to return"
    ),
) -> dict[str, Any]:
    """
    Get health check history.

    Returns historical health check results for trend analysis
    and debugging purposes.

    Args:
        limit: Maximum number of history entries to return (1-100)

    Returns:
        Dictionary with health check history

    Example Response:
        {
            "count": 10,
            "limit": 10,
            "history": [
                {
                    "status": "healthy",
                    "timestamp": "2024-01-15T10:30:00.000000",
                    "services": {...},
                    "summary": {...}
                },
                ...
            ]
        }

    Status Codes:
        - 200: History retrieved successfully
    """
    history = health_aggregator.get_history(limit=limit)

    return {
        "count": len(history),
        "limit": limit,
        "history": [h.model_dump() for h in history],
    }


@router.delete(
    "/history",
    response_model=dict[str, Any],
    summary="Clear Health Check History",
    description="Removes all historical health check data. This does not affect current health checks. Useful for resetting monitoring data after system maintenance.",
    tags=["Health"],
    responses={
        200: {
            "description": "Health check history cleared successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Health check history cleared",
                        "timestamp": "2024-01-15T10:30:00.000000"
                    }
                }
            }
        }
    }
)
async def clear_health_history() -> dict[str, Any]:
    """
    Clear health check history.

    Removes all historical health check data. This does not affect
    current health checks.

    Returns:
        Confirmation message

    Example Response:
        {
            "message": "Health check history cleared",
            "timestamp": "2024-01-15T10:30:00.000000"
        }

    Status Codes:
        - 200: History cleared successfully
    """
    from datetime import datetime

    health_aggregator.clear_history()

    return {
        "message": "Health check history cleared",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/metrics",
    response_model=dict[str, Any],
    summary="Get Health Check Metrics",
    description="Returns aggregated metrics about health check performance, uptime, and service availability. Includes average response times and service reliability statistics.",
    tags=["Health"],
    responses={
        200: {
            "description": "Health check metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "history_enabled": True,
                        "history_size": 50,
                        "uptime_percentage": 98.5,
                        "recent_checks": 10,
                        "avg_response_times_ms": {
                            "database": 12.3,
                            "redis": 5.7,
                            "celery": 25.1
                        }
                    }
                }
            }
        }
    }
)
async def get_health_metrics() -> dict[str, Any]:
    """
    Get health check metrics.

    Returns aggregated metrics about health check performance,
    uptime, and service availability.

    Returns:
        Dictionary with health check metrics

    Example Response:
        {
            "history_enabled": true,
            "history_size": 50,
            "uptime_percentage": 98.5,
            "recent_checks": 10,
            "avg_response_times_ms": {
                "database": 12.3,
                "redis": 5.7,
                "celery": 25.1
            }
        }

    Status Codes:
        - 200: Metrics retrieved successfully
    """
    return health_aggregator.get_metrics()


@router.post(
    "/check",
    response_model=AggregatedHealthResult,
    summary="Trigger Immediate Health Check",
    description="Manually triggers a comprehensive health check across all services. Useful for debugging or verifying system status after configuration changes or deployments.",
    tags=["Health"],
    responses={
        200: {
            "description": "Health check triggered and completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:00.000000",
                        "services": {},
                        "summary": {
                            "total_services": 3,
                            "healthy_count": 3,
                            "degraded_count": 0,
                            "unhealthy_count": 0
                        }
                    }
                }
            }
        }
    }
)
async def trigger_health_check() -> AggregatedHealthResult:
    """
    Trigger an immediate health check.

    Manually triggers a comprehensive health check across all services.
    This is useful for debugging or verifying system status after changes.

    Returns:
        AggregatedHealthResult with current health status

    Example Response:
        Same as GET /health/detailed

    Status Codes:
        - 200: Health check completed
    """
    return await health_aggregator.check_detailed()


@router.get(
    "/status",
    response_model=dict[str, Any],
    summary="Get Overall Health Status",
    description="Returns a simplified health status suitable for dashboards and monitoring systems. Provides a quick overview of service health without detailed diagnostics.",
    tags=["Health"],
    responses={
        200: {
            "description": "Overall health status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-15T10:30:00.000000",
                        "services_checked": 3,
                        "all_healthy": True,
                        "healthy_count": 3,
                        "degraded_count": 0,
                        "unhealthy_count": 0
                    }
                }
            }
        }
    }
)
async def get_overall_status() -> dict[str, Any]:
    """
    Get overall health status (simplified).

    Returns a simplified health status suitable for dashboards
    and monitoring systems.

    Returns:
        Dictionary with overall status

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00.000000",
            "services_checked": 3,
            "all_healthy": true
        }

    Status Codes:
        - 200: Status retrieved successfully
    """
    result = await health_aggregator.check_detailed()

    return {
        "status": result.status,
        "timestamp": result.timestamp.isoformat(),
        "services_checked": result.summary["total_services"],
        "all_healthy": result.summary["unhealthy_count"] == 0,
        "healthy_count": result.summary["healthy_count"],
        "degraded_count": result.summary["degraded_count"],
        "unhealthy_count": result.summary["unhealthy_count"],
    }
