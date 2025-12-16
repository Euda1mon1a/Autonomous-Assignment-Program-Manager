"""
Centralized logging configuration for the Residency Scheduler API.

Provides:
- Configurable log levels based on DEBUG setting
- Structured JSON logging for production
- Console and file handlers
- Noise reduction for third-party libraries

Usage:
    from logging_config import setup_logging
    setup_logging(debug=True)  # Call once at application startup
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production.

    Outputs logs as single-line JSON for easy parsing by log aggregators
    like ELK stack, Datadog, or CloudWatch.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add file/line info for errors
        if record.levelno >= logging.ERROR:
            log_record["location"] = f"{record.pathname}:{record.lineno}"

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add extra fields if any
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)

        return json.dumps(log_record)


class ConsoleFormatter(logging.Formatter):
    """
    Colored console formatter for development.

    Uses ANSI colors to distinguish log levels.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    debug: bool = False,
    log_file: Optional[str] = None,
    json_format: bool = False,
) -> None:
    """
    Configure application-wide logging.

    Args:
        debug: Enable DEBUG level logging
        log_file: Optional file path for log output
        json_format: Use JSON formatting (recommended for production)
    """
    level = logging.DEBUG if debug else logging.INFO

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on reload
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_format:
        console_handler.setFormatter(JsonFormatter())
    else:
        formatter = ConsoleFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Keep uvicorn error logs visible
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={logging.getLevelName(level)}, "
        f"json={json_format}, file={log_file or 'None'}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Convenience function to ensure consistent logger naming.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
