"""
Log formatters for structured logging.

Provides formatters for JSON-structured logs compatible with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog
- Splunk
- CloudWatch
- Standard JSON log aggregators
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Produces JSON-formatted log records with standardized fields:
    - timestamp: ISO 8601 timestamp
    - level: Log level (INFO, ERROR, etc.)
    - logger: Logger name
    - message: Log message
    - request_id: Correlation ID (if available)
    - extra: Additional fields passed via extra={}

    Example output:
    {
        "timestamp": "2024-01-15T10:30:45.123456Z",
        "level": "INFO",
        "logger": "app.api.routes.auth",
        "message": "User logged in",
        "request_id": "abc-123-def-456",
        "user_id": "user_123",
        "ip": "192.168.1.1"
    }
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_exception: bool = True,
        timestamp_format: str = "iso",
        extra_fields: list[str] | None = None,
    ):
        """
        Initialize JSON formatter.

        Args:
            include_timestamp: Include timestamp field
            include_level: Include log level field
            include_logger: Include logger name field
            include_exception: Include exception traceback if present
            timestamp_format: "iso" for ISO 8601, "unix" for Unix timestamp
            extra_fields: List of extra field names to always include
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_exception = include_exception
        self.timestamp_format = timestamp_format
        self.extra_fields = extra_fields or []

        # Reserved field names (don't copy from record.__dict__)
        self.reserved_fields = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
            "asctime",
        }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            str: JSON-formatted log record
        """
        log_data: dict[str, Any] = {}

        # Timestamp
        if self.include_timestamp:
            if self.timestamp_format == "iso":
                log_data["timestamp"] = datetime.fromtimestamp(
                    record.created
                ).isoformat()
            else:  # unix
                log_data["timestamp"] = record.created

        # Level
        if self.include_level:
            log_data["level"] = record.levelname

        # Logger name
        if self.include_logger:
            log_data["logger"] = record.name

        # Message
        log_data["message"] = record.getMessage()

        # Request ID (if available from context)
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Source location (useful for debugging)
        log_data["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Exception information
        if self.include_exception and record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self._format_traceback(record.exc_info),
            }

        # Extra fields (passed via logger.info("msg", extra={...}))
        extra = self._extract_extra_fields(record)
        if extra:
            log_data["extra"] = extra

        return json.dumps(log_data, default=str, ensure_ascii=False)

    def _extract_extra_fields(self, record: logging.LogRecord) -> dict[str, Any]:
        """Extract custom fields from log record."""
        extra = {}

        # Copy all non-reserved fields from record
        for key, value in record.__dict__.items():
            if key not in self.reserved_fields and not key.startswith("_"):
                extra[key] = value

        # Always include specified extra fields (even if None)
        for field in self.extra_fields:
            if field not in extra and hasattr(record, field):
                extra[field] = getattr(record, field)

        return extra

    def _format_traceback(self, exc_info) -> str | None:
        """Format exception traceback."""
        if not exc_info or exc_info == (None, None, None):
            return None

        return "".join(traceback.format_exception(*exc_info))


class RequestResponseFormatter(JSONFormatter):
    """
    Specialized JSON formatter for request/response logging.

    Includes fields specific to HTTP request/response:
    - method: HTTP method (GET, POST, etc.)
    - path: Request path
    - status_code: Response status code
    - duration_ms: Request duration in milliseconds
    - ip: Client IP address
    - user_agent: User agent string
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format with HTTP-specific fields."""
        log_data: dict[str, Any] = {}

        # Timestamp
        if self.include_timestamp:
            if self.timestamp_format == "iso":
                log_data["timestamp"] = datetime.fromtimestamp(
                    record.created
                ).isoformat()
            else:
                log_data["timestamp"] = record.created

        # Level
        log_data["level"] = record.levelname

        # Logger
        log_data["logger"] = record.name

        # Message
        log_data["message"] = record.getMessage()

        # Request ID
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # HTTP-specific fields
        http_data = {}
        if hasattr(record, "method"):
            http_data["method"] = record.method
        if hasattr(record, "path"):
            http_data["path"] = record.path
        if hasattr(record, "status_code"):
            http_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            http_data["duration_ms"] = record.duration_ms
        if hasattr(record, "ip"):
            http_data["ip"] = record.ip
        if hasattr(record, "user_agent"):
            http_data["user_agent"] = record.user_agent

        if http_data:
            log_data["http"] = http_data

        # Request/response data (if present)
        if hasattr(record, "request_headers"):
            log_data["request_headers"] = record.request_headers
        if hasattr(record, "request_body"):
            log_data["request_body"] = record.request_body
        if hasattr(record, "response_headers"):
            log_data["response_headers"] = record.response_headers
        if hasattr(record, "response_body"):
            log_data["response_body"] = record.response_body

        # User info (if available)
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Extra fields
        extra = self._extract_extra_fields(record)
        # Remove fields already included in http_data
        for field in [
            "method",
            "path",
            "status_code",
            "duration_ms",
            "ip",
            "user_agent",
        ]:
            extra.pop(field, None)
        # Remove fields at top level
        for field in [
            "request_headers",
            "request_body",
            "response_headers",
            "response_body",
            "user_id",
        ]:
            extra.pop(field, None)

        if extra:
            log_data["extra"] = extra

        return json.dumps(log_data, default=str, ensure_ascii=False)


class CompactJSONFormatter(JSONFormatter):
    """
    Compact JSON formatter with minimal fields.

    Useful for high-traffic endpoints where full logging would be too verbose.
    Only includes essential fields: timestamp, level, message, request_id.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format with minimal fields."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Always include request_id if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Include only critical HTTP fields
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "status_code"):
            log_data["status"] = record.status_code

        return json.dumps(log_data, default=str, ensure_ascii=False)


def get_formatter(format_type: str = "json") -> logging.Formatter:
    """
    Get a formatter instance by type.

    Args:
        format_type: One of "json", "request_response", "compact"

    Returns:
        logging.Formatter: Formatter instance
    """
    formatters = {
        "json": JSONFormatter(),
        "request_response": RequestResponseFormatter(),
        "compact": CompactJSONFormatter(),
        "text": logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
    }

    return formatters.get(format_type, JSONFormatter())
