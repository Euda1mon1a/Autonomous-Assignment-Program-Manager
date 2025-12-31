"""
Enhanced logging package.

Provides comprehensive logging infrastructure with:
- Structured logging (JSON, GELF, Logfmt)
- Context management (request correlation, user tracking)
- Data sanitization (PII redaction)
- Custom formatters and handlers
- Async logging support
"""

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
