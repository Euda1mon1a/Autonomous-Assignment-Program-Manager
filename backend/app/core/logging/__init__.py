"""
Enhanced logging package.

Provides comprehensive logging infrastructure with:
- Structured logging (JSON, GELF, Logfmt)
- Context management (request correlation, user tracking)
- Data sanitization (PII redaction)
- Custom formatters and handlers
- Async logging support
"""

import json
import logging
import sys
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

from loguru import logger as _loguru_logger

if TYPE_CHECKING:
    from loguru import Logger


# Context variable for request correlation ID
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id_compat() -> str | None:
    """Get the current request's correlation ID."""
    return _request_id_ctx.get()


def set_request_id_compat(request_id: str) -> None:
    """Set the current request's correlation ID."""
    _request_id_ctx.set(request_id)


class InterceptHandler(logging.Handler):
    """Handler to intercept standard library logging and route to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by forwarding to loguru."""
        try:
            level = _loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        _loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _json_serializer(record: dict) -> str:
    """Serialize log record to JSON format."""
    subset = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    request_id = get_request_id_compat()
    if request_id:
        subset["request_id"] = request_id

    if record.get("extra"):
        for key, value in record["extra"].items():
            if key not in ("request_id",):
                subset[key] = value

    if record["exception"]:
        subset["exception"] = {
            "type": (
                record["exception"].type.__name__ if record["exception"].type else None
            ),
            "value": (
                str(record["exception"].value) if record["exception"].value else None
            ),
            "traceback": record["exception"].traceback is not None,
        }

    return json.dumps(subset, default=str)


def _json_sink(message: Any) -> None:
    """Sink for JSON-formatted log output."""
    record = message.record
    sys.stderr.write(_json_serializer(record) + "\n")
    sys.stderr.flush()


def _text_format(record: dict) -> str:
    """Format log record for human-readable text output."""
    request_id = get_request_id_compat()
    request_id_str = f"[{request_id[:8]}] " if request_id else ""

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
    """Configure loguru logging for the application."""
    _loguru_logger.remove()

    if format_type == "json":
        _loguru_logger.add(
            _json_sink,
            level=level,
            format="{message}",
            backtrace=True,
            diagnose=False,
        )
    else:
        _loguru_logger.add(
            sys.stderr,
            level=level,
            format=_text_format,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

    if log_file:
        _loguru_logger.add(
            log_file,
            level=level,
            format=_text_format if format_type == "text" else "{message}",
            rotation="100 MB",
            retention="7 days",
            compression="gz",
            serialize=format_type == "json",
        )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    _loguru_logger.info(
        "Logging configured",
        level=level,
        format=format_type,
        file=log_file or "stderr",
    )


def get_logger(name: str = __name__) -> "Logger":
    """Get a logger instance bound with the module name."""
    return _loguru_logger.bind(module=name)


# Re-export loguru logger for direct use
logger = _loguru_logger


from app.core.logging.config import (
    LogFormat,
    LogLevel,
    LoggingConfig,
    configure_module_logging,
    configure_third_party_logging,
    get_current_config,
    get_logging_config,
    set_logging_config,
)
from app.core.logging.context import (
    LogContext,
    LogContextManager,
    bind_context_to_logger,
    create_request_context,
    get_all_context,
    get_request_id,
    get_session_id,
    get_trace_id,
    get_user_id,
    set_request_id,
    set_session_id,
    set_trace_id,
    set_user_id,
    with_log_context,
)
from app.core.logging.formatters import (
    CloudWatchFormatter,
    ColoredTextFormatter,
    GELFFormatter,
    JSONFormatter,
    LogfmtFormatter,
    create_cloudwatch_formatter,
    create_colored_text_formatter,
    create_gelf_formatter,
    create_json_formatter,
    create_logfmt_formatter,
)
from app.core.logging.handlers import (
    AsyncLogHandler,
    CompressedRotatingFileHandler,
    DatabaseLogHandler,
    RedisLogHandler,
    WebhookLogHandler,
    create_database_handler,
    create_redis_handler,
    create_webhook_handler,
)
from app.core.logging.sanitizers import (
    DataSanitizer,
    SanitizationRule,
    create_custom_rule,
    get_global_sanitizer,
    sanitize,
    set_global_sanitizer,
)

__all__ = [
    # Core logging functions
    "logger",
    "get_logger",
    "setup_logging",
    "InterceptHandler",
    # Config
    "LogFormat",
    "LogLevel",
    "LoggingConfig",
    "get_logging_config",
    "set_logging_config",
    "get_current_config",
    "configure_module_logging",
    "configure_third_party_logging",
    # Context
    "LogContext",
    "LogContextManager",
    "create_request_context",
    "get_request_id",
    "set_request_id",
    "get_user_id",
    "set_user_id",
    "get_session_id",
    "set_session_id",
    "get_trace_id",
    "set_trace_id",
    "get_all_context",
    "bind_context_to_logger",
    "with_log_context",
    # Formatters
    "JSONFormatter",
    "GELFFormatter",
    "LogfmtFormatter",
    "CloudWatchFormatter",
    "ColoredTextFormatter",
    "create_json_formatter",
    "create_gelf_formatter",
    "create_logfmt_formatter",
    "create_cloudwatch_formatter",
    "create_colored_text_formatter",
    # Handlers
    "AsyncLogHandler",
    "DatabaseLogHandler",
    "RedisLogHandler",
    "WebhookLogHandler",
    "CompressedRotatingFileHandler",
    "create_database_handler",
    "create_redis_handler",
    "create_webhook_handler",
    # Sanitizers
    "DataSanitizer",
    "SanitizationRule",
    "sanitize",
    "get_global_sanitizer",
    "set_global_sanitizer",
    "create_custom_rule",
]
