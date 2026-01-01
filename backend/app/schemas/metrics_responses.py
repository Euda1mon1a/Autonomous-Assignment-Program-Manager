"""Metrics API response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class MetricsHealthResponse(BaseModel):
    """Response schema for metrics health check."""

    status: str = Field(..., description="Health status: healthy, degraded")
    metrics_enabled: bool = Field(..., description="Whether metrics are enabled")
    collectors: list[str] = Field(..., description="List of active metric collectors")
    prometheus_available: bool = Field(
        ..., description="Whether Prometheus client is available"
    )
    message: str = Field(..., description="Status message")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "status": "healthy",
                "metrics_enabled": True,
                "collectors": ["http", "database", "cache", "schedule"],
                "prometheus_available": True,
                "message": "Metrics collection operational",
            }
        }


class MetricDocumentation(BaseModel):
    """Documentation for a single metric."""

    type: str = Field(..., description="Metric type: counter, gauge, histogram, summary")
    description: str = Field(..., description="Metric description")
    labels: list[str] = Field(..., description="Metric labels")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "type": "counter",
                "description": "Total HTTP requests",
                "labels": ["method", "endpoint", "status_code"],
            }
        }


class MetricsInfoResponse(BaseModel):
    """Response schema for metrics information."""

    metrics: dict[str, Any] = Field(..., description="Categorized metrics documentation")
    total_metrics: int = Field(..., description="Total number of metrics")
    categories: list[str] = Field(..., description="List of metric categories")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "metrics": {
                    "http": {
                        "http_requests_total": {
                            "type": "counter",
                            "description": "Total HTTP requests",
                        }
                    }
                },
                "total_metrics": 25,
                "categories": ["http", "database", "cache", "schedule"],
            }
        }


class MetricsSummaryResponse(BaseModel):
    """Response schema for metrics summary."""

    status: str = Field(..., description="Metrics status: enabled, disabled")
    timestamp: str | None = Field(None, description="Current timestamp")
    http: dict[str, Any] = Field(
        default_factory=dict, description="HTTP metrics summary"
    )
    database: dict[str, Any] = Field(
        default_factory=dict, description="Database metrics summary"
    )
    cache: dict[str, Any] = Field(
        default_factory=dict, description="Cache metrics summary"
    )
    background_tasks: dict[str, Any] = Field(
        default_factory=dict, description="Background task metrics summary"
    )
    message: str = Field(..., description="Information message")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "status": "enabled",
                "timestamp": None,
                "http": {"active_connections": "See /metrics endpoint"},
                "database": {"active_connections": "See /metrics endpoint"},
                "cache": {"hit_ratio": "See /metrics endpoint"},
                "background_tasks": {"tasks_in_progress": "See /metrics endpoint"},
                "message": "For detailed metrics, query the /metrics endpoint directly",
            }
        }


class MetricsResetResponse(BaseModel):
    """Response schema for metrics reset endpoint."""

    status: str = Field(..., description="Reset status: success, warning, error")
    message: str = Field(..., description="Status message")
    recommendation: str | None = Field(None, description="Recommended action")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "status": "warning",
                "message": "Prometheus metrics cannot be reset without restarting the application",
                "recommendation": "Restart the application to reset metrics",
            }
        }
