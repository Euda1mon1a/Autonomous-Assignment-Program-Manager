"""
Request/Response logging middleware package.

Comprehensive logging solution for FastAPI applications with:
- Request/response body logging (with size limits)
- Sensitive data masking (passwords, tokens, PII)
- Structured JSON logging
- Request ID correlation
- Configurable log levels per endpoint
- Sampling for high-traffic endpoints
- Multiple storage backends (memory, file, database)
- Performance metrics tracking

Usage:
    Basic setup (in app/main.py):
    ```python
    from app.middleware.logging import (
        RequestLoggingMiddleware,
        RequestLoggingConfig,
    )

    # Create configuration
    config = RequestLoggingConfig(
        log_body=True,
        max_body_size=10 * 1024,  # 10 KB
        excluded_paths={"/health", "/metrics"},
        sample_rate=1.0,  # Log all requests
    )

    # Add middleware
    app.add_middleware(RequestLoggingMiddleware, config=config)
    ```

    Advanced setup with custom storage:
    ```python
    from app.middleware.logging import (
        RequestLoggingMiddleware,
        RequestLoggingConfig,
        FileLogStorage,
        MultiLogStorage,
        InMemoryLogStorage,
        SensitiveDataFilter,
    )

    # Create storage backends
    file_storage = FileLogStorage(
        log_dir="logs",
        filename="requests.log",
        rotation_type="size",
        max_bytes=100 * 1024 * 1024,  # 100 MB
    )

    memory_storage = InMemoryLogStorage(max_entries=5000)

    multi_storage = MultiLogStorage([file_storage, memory_storage])

    # Create custom filter
    sensitive_filter = SensitiveDataFilter(
        sensitive_fields={"password", "ssn", "credit_card"},
        show_prefix_chars=3,  # Show first 3 chars
        show_suffix_chars=2,  # Show last 2 chars
    )

    # Create configuration
    config = RequestLoggingConfig(
        log_body=True,
        log_headers=True,
        max_body_size=50 * 1024,
        excluded_paths={"/health", "/metrics", "/docs"},
        sample_rate=0.1,  # Log 10% of requests (for high traffic)
        log_levels={
            "/api/v1/debug": "DEBUG",
            "/api/v1/auth": "WARNING",
        },
        storage_backend=multi_storage,
        sensitive_filter=sensitive_filter,
    )

    app.add_middleware(RequestLoggingMiddleware, config=config)
    ```

    Retrieve logs (e.g., for debugging endpoint):
    ```python
    from app.middleware.logging import get_recent_logs

    @app.get("/admin/logs")
    async def get_logs(limit: int = 100):
        logs = get_recent_logs(limit=limit, filters={"level": "ERROR"})
        return {"logs": logs}
    ```
"""

from app.middleware.logging.filters import (
    SensitiveDataFilter,
    default_filter,
    mask_sensitive_data,
)
from app.middleware.logging.formatters import (
    CompactJSONFormatter,
    JSONFormatter,
    RequestResponseFormatter,
    get_formatter,
)
from app.middleware.logging.request_logger import (
    RequestLoggingConfig,
    RequestLoggingMiddleware,
)
from app.middleware.logging.response_logger import (
    ResponseLogger,
    ResponseMetrics,
    StreamingResponseLogger,
    global_metrics,
)
from app.middleware.logging.storage import (
    DatabaseLogStorage,
    FileLogStorage,
    InMemoryLogStorage,
    LogStorage,
    MultiLogStorage,
    get_storage_backend,
)

__all__ = [
    # Middleware
    "RequestLoggingMiddleware",
    "RequestLoggingConfig",
    # Filters
    "SensitiveDataFilter",
    "default_filter",
    "mask_sensitive_data",
    # Formatters
    "JSONFormatter",
    "RequestResponseFormatter",
    "CompactJSONFormatter",
    "get_formatter",
    # Response logging
    "ResponseLogger",
    "ResponseMetrics",
    "StreamingResponseLogger",
    "global_metrics",
    # Storage
    "LogStorage",
    "InMemoryLogStorage",
    "FileLogStorage",
    "DatabaseLogStorage",
    "MultiLogStorage",
    "get_storage_backend",
]


# Convenience functions for common operations


def get_recent_logs(
    limit: int = 100,
    filters: dict = None,
    storage_backend=None,
):
    """
    Get recent log entries from storage.

    Args:
        limit: Maximum number of log entries to return
        filters: Optional filters (e.g., {"level": "ERROR", "user_id": "123"})
        storage_backend: Storage backend to query (default: global in-memory)

    Returns:
        List of log entries

    Example:
        # Get last 100 error logs
        errors = get_recent_logs(limit=100, filters={"level": "ERROR"})

        # Get logs for specific user
        user_logs = get_recent_logs(filters={"user_id": "user_123"})
    """
    if storage_backend is None:
        # Use global in-memory storage
        storage_backend = get_storage_backend("memory")

    return storage_backend.retrieve(limit=limit, filters=filters)


def get_response_metrics():
    """
    Get current response metrics.

    Returns:
        Dict containing response metrics:
        - total_requests: Total number of requests
        - status_codes: Distribution of status codes
        - response_times: Distribution of response times
        - endpoints: Per-endpoint statistics

    Example:
        metrics = get_response_metrics()
        print(f"Total requests: {metrics['total_requests']}")
        print(f"Error rate: {metrics['status_codes'].get('500', 0)}")
    """
    return global_metrics.get_metrics()


def create_logging_config(
    environment: str = "development",
    **overrides,
) -> RequestLoggingConfig:
    """
    Create logging configuration for different environments.

    Args:
        environment: Environment name ("development", "staging", "production")
        **overrides: Override default settings

    Returns:
        RequestLoggingConfig instance

    Example:
        # Development: log everything
        dev_config = create_logging_config("development")

        # Production: minimal logging with sampling
        prod_config = create_logging_config(
            "production",
            sample_rate=0.01,  # Log 1% of requests
            max_body_size=1024,  # 1 KB max
        )
    """
    # Environment presets
    presets = {
        "development": {
            "enabled": True,
            "log_headers": True,
            "log_body": True,
            "max_body_size": 100 * 1024,  # 100 KB
            "log_response": True,
            "max_response_size": 100 * 1024,
            "sample_rate": 1.0,  # Log all
            "storage_backend": get_storage_backend("memory", max_entries=10000),
        },
        "staging": {
            "enabled": True,
            "log_headers": True,
            "log_body": True,
            "max_body_size": 50 * 1024,  # 50 KB
            "log_response": True,
            "max_response_size": 50 * 1024,
            "sample_rate": 0.5,  # Log 50%
            "storage_backend": FileLogStorage(
                log_dir="logs",
                rotation_type="time",
                when="midnight",
                backup_count=7,
            ),
        },
        "production": {
            "enabled": True,
            "log_headers": False,  # Reduce storage
            "log_body": False,  # Reduce storage and improve performance
            "max_body_size": 10 * 1024,  # 10 KB
            "log_response": True,
            "max_response_size": 10 * 1024,
            "sample_rate": 0.1,  # Log 10%
            "storage_backend": FileLogStorage(
                log_dir="logs",
                rotation_type="time",
                when="midnight",
                backup_count=30,
                use_compact_format=True,
            ),
        },
    }

    # Get preset or use development as default
    config_dict = presets.get(environment, presets["development"]).copy()

    # Apply overrides
    config_dict.update(overrides)

    return RequestLoggingConfig(**config_dict)
