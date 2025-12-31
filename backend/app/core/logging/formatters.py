"""
Custom log formatters for different output formats.

Provides formatters for:
- JSON (structured logging)
- GELF (Graylog Extended Log Format)
- Logfmt (key=value format)
- Text (human-readable with colors)
- CloudWatch (AWS-specific format)
"""

import json
import socket
from datetime import datetime
from typing import Any

from loguru import logger


class JSONFormatter:
    """
    JSON log formatter for structured logging.

    Produces compact JSON output suitable for log aggregation systems.
    """

    def __init__(
        self,
        indent: int | None = None,
        include_extra: bool = True,
        timestamp_format: str = "iso",
    ):
        """
        Initialize JSON formatter.

        Args:
            indent: JSON indentation (None for compact)
            include_extra: Include extra fields from log context
            timestamp_format: Timestamp format (iso, unix, unix_ms)
        """
        self.indent = indent
        self.include_extra = include_extra
        self.timestamp_format = timestamp_format

    def format(self, record: dict[str, Any]) -> str:
        """
        Format log record as JSON.

        Args:
            record: Loguru record dictionary

        Returns:
            str: JSON-formatted log string
        """
        # Build base log entry
        entry = {
            "timestamp": self._format_timestamp(record["time"]),
            "level": record["level"].name,
            "logger": record["name"],
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
        }

        # Add extra fields if present
        if self.include_extra and record.get("extra"):
            for key, value in record["extra"].items():
                if key not in entry:  # Avoid overwriting core fields
                    entry[key] = value

        # Add exception info if present
        if record["exception"]:
            entry["exception"] = {
                "type": (
                    record["exception"].type.__name__
                    if record["exception"].type
                    else None
                ),
                "value": str(record["exception"].value) if record["exception"].value else None,
                "traceback": record["exception"].traceback is not None,
            }

        # Add process/thread info
        entry["process"] = {
            "id": record["process"].id,
            "name": record["process"].name,
        }
        entry["thread"] = {
            "id": record["thread"].id,
            "name": record["thread"].name,
        }

        return json.dumps(entry, indent=self.indent, default=str)

    def _format_timestamp(self, dt: datetime) -> str | int | float:
        """Format timestamp based on configuration."""
        if self.timestamp_format == "unix":
            return int(dt.timestamp())
        elif self.timestamp_format == "unix_ms":
            return int(dt.timestamp() * 1000)
        else:  # iso
            return dt.isoformat()


class GELFFormatter:
    """
    Graylog Extended Log Format (GELF) formatter.

    GELF is a structured log format designed for Graylog and other log aggregation systems.
    """

    def __init__(
        self,
        facility: str = "app",
        include_extra: bool = True,
    ):
        """
        Initialize GELF formatter.

        Args:
            facility: Facility name (application identifier)
            include_extra: Include extra fields from log context
        """
        self.facility = facility
        self.include_extra = include_extra
        self.hostname = socket.gethostname()

    def format(self, record: dict[str, Any]) -> str:
        """
        Format log record as GELF JSON.

        Args:
            record: Loguru record dictionary

        Returns:
            str: GELF JSON string
        """
        # GELF specification version 1.1
        gelf_entry = {
            "version": "1.1",
            "host": self.hostname,
            "timestamp": record["time"].timestamp(),
            "level": self._map_level(record["level"].no),
            "short_message": record["message"],
            "full_message": record["message"],
            "facility": self.facility,
            "_logger": record["name"],
            "_module": record["module"],
            "_function": record["function"],
            "_line": record["line"],
            "_process_id": record["process"].id,
            "_thread_id": record["thread"].id,
        }

        # Add extra fields (prefixed with _)
        if self.include_extra and record.get("extra"):
            for key, value in record["extra"].items():
                gelf_key = f"_{key}" if not key.startswith("_") else key
                gelf_entry[gelf_key] = value

        # Add exception info
        if record["exception"]:
            gelf_entry["_exception_type"] = (
                record["exception"].type.__name__ if record["exception"].type else None
            )
            gelf_entry["_exception_value"] = (
                str(record["exception"].value) if record["exception"].value else None
            )

        return json.dumps(gelf_entry, default=str)

    def _map_level(self, loguru_level: int) -> int:
        """
        Map Loguru level to Syslog severity level.

        Args:
            loguru_level: Loguru level number

        Returns:
            int: Syslog severity (0-7)
        """
        # Map to syslog levels:
        # 0: Emergency, 1: Alert, 2: Critical, 3: Error
        # 4: Warning, 5: Notice, 6: Informational, 7: Debug
        if loguru_level >= 50:  # CRITICAL
            return 2
        elif loguru_level >= 40:  # ERROR
            return 3
        elif loguru_level >= 30:  # WARNING
            return 4
        elif loguru_level >= 20:  # INFO
            return 6
        else:  # DEBUG
            return 7


class LogfmtFormatter:
    """
    Logfmt formatter (key=value pairs).

    Logfmt is a human-readable and machine-parseable log format.
    """

    def __init__(self, include_extra: bool = True):
        """
        Initialize logfmt formatter.

        Args:
            include_extra: Include extra fields from log context
        """
        self.include_extra = include_extra

    def format(self, record: dict[str, Any]) -> str:
        """
        Format log record as logfmt.

        Args:
            record: Loguru record dictionary

        Returns:
            str: Logfmt string (key=value key=value ...)
        """
        pairs = []

        # Core fields
        pairs.append(f"time={record['time'].isoformat()}")
        pairs.append(f"level={record['level'].name}")
        pairs.append(f"logger={self._quote(record['name'])}")
        pairs.append(f"msg={self._quote(record['message'])}")

        # Location
        pairs.append(f"module={record['module']}")
        pairs.append(f"function={record['function']}")
        pairs.append(f"line={record['line']}")

        # Process/thread
        pairs.append(f"process={record['process'].id}")
        pairs.append(f"thread={record['thread'].id}")

        # Extra fields
        if self.include_extra and record.get("extra"):
            for key, value in record["extra"].items():
                pairs.append(f"{key}={self._quote(str(value))}")

        # Exception
        if record["exception"]:
            exc_type = (
                record["exception"].type.__name__ if record["exception"].type else "Unknown"
            )
            exc_value = str(record["exception"].value) if record["exception"].value else ""
            pairs.append(f"exception_type={exc_type}")
            pairs.append(f"exception_value={self._quote(exc_value)}")

        return " ".join(pairs)

    def _quote(self, value: str) -> str:
        """Quote value if it contains spaces or special characters."""
        if " " in value or "=" in value or '"' in value:
            # Escape quotes and wrap in quotes
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return value


class CloudWatchFormatter:
    """
    AWS CloudWatch Logs formatter.

    Formats logs for optimal CloudWatch Logs Insights queries.
    """

    def __init__(self, include_extra: bool = True):
        """
        Initialize CloudWatch formatter.

        Args:
            include_extra: Include extra fields from log context
        """
        self.include_extra = include_extra

    def format(self, record: dict[str, Any]) -> str:
        """
        Format log record for CloudWatch.

        CloudWatch uses JSON format with specific field naming conventions.

        Args:
            record: Loguru record dictionary

        Returns:
            str: CloudWatch-compatible JSON string
        """
        entry = {
            "@timestamp": record["time"].isoformat(),
            "@level": record["level"].name,
            "@logger": record["name"],
            "@message": record["message"],
            "@module": record["module"],
            "@function": record["function"],
            "@line": record["line"],
            "@process_id": record["process"].id,
            "@thread_id": record["thread"].id,
        }

        # Extra fields (CloudWatch Insights can query these)
        if self.include_extra and record.get("extra"):
            for key, value in record["extra"].items():
                entry[key] = value

        # Exception
        if record["exception"]:
            entry["@exception"] = {
                "type": (
                    record["exception"].type.__name__
                    if record["exception"].type
                    else None
                ),
                "value": (
                    str(record["exception"].value) if record["exception"].value else None
                ),
            }

        return json.dumps(entry, default=str)


class ColoredTextFormatter:
    """
    Colored text formatter for human-readable console output.

    Uses ANSI color codes for different log levels.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "SUCCESS": "\033[92m",  # Bright green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[91m",  # Bright red
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, include_colors: bool = True, include_extra: bool = True):
        """
        Initialize colored text formatter.

        Args:
            include_colors: Enable ANSI color codes
            include_extra: Include extra fields from log context
        """
        self.include_colors = include_colors
        self.include_extra = include_extra

    def format(self, record: dict[str, Any]) -> str:
        """
        Format log record as colored text.

        Args:
            record: Loguru record dictionary

        Returns:
            str: Formatted log string with colors
        """
        level = record["level"].name
        color = self.COLORS.get(level, self.COLORS["RESET"]) if self.include_colors else ""
        reset = self.COLORS["RESET"] if self.include_colors else ""

        # Format timestamp
        timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Format location
        location = f"{record['module']}:{record['function']}:{record['line']}"

        # Build message
        parts = [
            f"{timestamp}",
            f"{color}{level:<8}{reset}",
            f"{location}",
            f"{color}{record['message']}{reset}",
        ]

        # Add extra fields
        if self.include_extra and record.get("extra"):
            extra_parts = [f"{k}={v}" for k, v in record["extra"].items()]
            if extra_parts:
                parts.append(f"| {', '.join(extra_parts)}")

        return " | ".join(parts)


# Factory functions


def create_json_formatter(
    indent: int | None = None,
    timestamp_format: str = "iso",
) -> JSONFormatter:
    """
    Create JSON formatter.

    Args:
        indent: JSON indentation (None for compact)
        timestamp_format: Timestamp format (iso, unix, unix_ms)

    Returns:
        JSONFormatter: Configured formatter
    """
    return JSONFormatter(indent=indent, timestamp_format=timestamp_format)


def create_gelf_formatter(facility: str = "app") -> GELFFormatter:
    """
    Create GELF formatter.

    Args:
        facility: Facility name

    Returns:
        GELFFormatter: Configured formatter
    """
    return GELFFormatter(facility=facility)


def create_logfmt_formatter() -> LogfmtFormatter:
    """
    Create logfmt formatter.

    Returns:
        LogfmtFormatter: Configured formatter
    """
    return LogfmtFormatter()


def create_cloudwatch_formatter() -> CloudWatchFormatter:
    """
    Create CloudWatch formatter.

    Returns:
        CloudWatchFormatter: Configured formatter
    """
    return CloudWatchFormatter()


def create_colored_text_formatter(include_colors: bool = True) -> ColoredTextFormatter:
    """
    Create colored text formatter.

    Args:
        include_colors: Enable ANSI color codes

    Returns:
        ColoredTextFormatter: Configured formatter
    """
    return ColoredTextFormatter(include_colors=include_colors)
