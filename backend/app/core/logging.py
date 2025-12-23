"""
Structured logging configuration using loguru.

This module provides:
1. Loguru configuration with structured JSON output for production
2. Human-readable colored output for development
3. InterceptHandler to bridge standard library logging to loguru
4. Request ID integration for distributed tracing
5. Configurable log levels, formats, and file output

Usage:
    from app.core.logging import setup_logging, get_logger

    # At application startup (in main.py)
    setup_logging()

    # In any module
    logger = get_logger(__name__)
    logger.info("Processing request", user_id=123, action="create")

Environment Variables:
    LOG_LEVEL: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FORMAT: Output format (json, text)
    LOG_FILE: Path to log file (optional, logs to stderr by default)
"""

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

from loguru import logger

# Context variable for request correlation ID (integrates with observability.py)
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Get the current request's correlation ID."""
    return _request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """Set the current request's correlation ID."""
    _request_id_ctx.set(request_id)


class InterceptHandler(logging.Handler):
    """
    Handler to intercept standard library logging and route to loguru.

    This allows all logging (including from third-party libraries) to be
    processed through loguru with consistent formatting.

    Usage:
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by forwarding to loguru."""
        # Get corresponding loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logging call
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _json_serializer(record: dict) -> str:
    """
    Serialize log record to JSON format for structured logging.

    Args:
        record: Loguru record dictionary

    Returns:
        JSON string representation of the log record
    """
    subset = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add request ID if available
    request_id = get_request_id()
    if request_id:
        subset["request_id"] = request_id

    # Add extra fields from the log call
    if record.get("extra"):
        for key, value in record["extra"].items():
            if key not in ("request_id",):  # Avoid duplicates
                subset[key] = value

    # Add exception info if present
    if record["exception"]:
        subset["exception"] = {
            "type": record["exception"].type.__name__
            if record["exception"].type
            else None,
            "value": str(record["exception"].value)
            if record["exception"].value
            else None,
            "traceback": record["exception"].traceback is not None,
        }

    return json.dumps(subset, default=str)


def _json_sink(message: Any) -> None:
    """Sink for JSON-formatted log output."""
    record = message.record
    sys.stderr.write(_json_serializer(record) + "\n")
    sys.stderr.flush()


def _text_format(record: dict) -> str:
    """
    Format log record for human-readable text output.

    Format: timestamp | level | module:function:line | [request_id] | message
    """
    request_id = get_request_id()
    request_id_str = f"[{request_id[:8]}] " if request_id else ""

    # Format extra fields if any
    extra_str = ""
    if record.get("extra"):
        extra_items = [
            f"{k}={v}" for k, v in record["extra"].items() if k not in ("request_id",)
        ]
        if extra_items:
            extra_str = " | " + ", ".join(extra_items)

    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        f"{request_id_str}"
        "<level>{message}</level>"
        f"{extra_str}"
        "\n{exception}"
    )


def setup_logging(
    level: str = "INFO",
    format_type: str = "text",
    log_file: str | None = None,
) -> None:
    """
    Configure loguru logging for the application.

    This function:
    1. Removes default loguru handlers
    2. Adds handlers based on configuration
    3. Intercepts standard library logging
    4. Configures log levels for third-party libraries

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Output format ('json' for structured, 'text' for human-readable)
        log_file: Optional path to log file

    Example:
        # Development mode
        setup_logging(level="DEBUG", format_type="text")

        # Production mode
        setup_logging(level="INFO", format_type="json")
    """
    # Remove default handler
    logger.remove()

    # Add stderr handler based on format type
    if format_type == "json":
        logger.add(
            _json_sink,
            level=level,
            format="{message}",  # Format is handled by _json_sink
            backtrace=True,
            diagnose=False,  # Don't include variable values in production
        )
    else:
        logger.add(
            sys.stderr,
            level=level,
            format=_text_format,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    # Add file handler if configured
    if log_file:
        logger.add(
            log_file,
            level=level,
            format=_text_format if format_type == "text" else "{message}",
            rotation="100 MB",
            retention="7 days",
            compression="gz",
            serialize=format_type == "json",
        )

    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set log levels for noisy third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger.info(
        "Logging configured",
        level=level,
        format=format_type,
        file=log_file or "stderr",
    )


def get_logger(name: str = __name__) -> "logger":
    """
    Get a logger instance bound with the module name.

    This provides a convenient way to get a logger with context.

    Args:
        name: Module name (typically __name__)

    Returns:
        Loguru logger bound with module context

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started", item_id=123)
    """
    return logger.bind(module=name)


# Export the main logger for direct use
__all__ = [
    "logger",
    "get_logger",
    "setup_logging",
    "InterceptHandler",
    "get_request_id",
    "set_request_id",
]
