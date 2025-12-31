"""
Enhanced logging configuration.

Provides comprehensive logging configuration with:
- Environment-based configuration
- Multiple output formats (JSON, text, GELF)
- Log level configuration per module
- Async logging support
- Integration with observability tools
"""

import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from app.core.config import get_settings

settings = get_settings()


class LogFormat(str, Enum):
    """Supported log output formats."""

    JSON = "json"
    TEXT = "text"
    GELF = "gelf"  # Graylog Extended Log Format
    LOGFMT = "logfmt"  # Key=value format


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LoggingConfig:
    """
    Comprehensive logging configuration.

    Attributes:
        level: Global log level
        format: Output format (json, text, gelf, logfmt)
        log_file: Optional file path for log output
        max_file_size: Maximum log file size before rotation (MB)
        backup_count: Number of rotated log files to keep
        enable_colors: Enable colored output (text format only)
        enable_backtrace: Enable detailed traceback
        enable_diagnose: Enable variable values in errors (disable in prod)
        json_indent: Indent for JSON format (None for compact)
        module_levels: Per-module log level overrides
        correlation_enabled: Enable request correlation IDs
        performance_logging: Enable performance metrics logging
        audit_logging: Enable audit trail logging
        async_logging: Enable asynchronous logging (experimental)
    """

    level: LogLevel = field(default=LogLevel.INFO)
    format: LogFormat = field(default=LogFormat.JSON)
    log_file: str | None = field(default=None)
    max_file_size: int = field(default=100)  # MB
    backup_count: int = field(default=7)
    enable_colors: bool = field(default=True)
    enable_backtrace: bool = field(default=True)
    enable_diagnose: bool = field(default=False)
    json_indent: int | None = field(default=None)
    module_levels: dict[str, LogLevel] = field(default_factory=dict)
    correlation_enabled: bool = field(default=True)
    performance_logging: bool = field(default=True)
    audit_logging: bool = field(default=True)
    async_logging: bool = field(default=False)

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """
        Create logging configuration from environment variables.

        Environment variables:
            LOG_LEVEL: Global log level (default: INFO)
            LOG_FORMAT: Output format (default: json in prod, text in dev)
            LOG_FILE: Path to log file (optional)
            LOG_MAX_FILE_SIZE: Max file size in MB (default: 100)
            LOG_BACKUP_COUNT: Number of backup files (default: 7)
            LOG_ENABLE_COLORS: Enable colored output (default: true)
            LOG_ENABLE_DIAGNOSE: Enable diagnostic info (default: false)
            LOG_CORRELATION: Enable request correlation (default: true)
            LOG_PERFORMANCE: Enable performance logging (default: true)
            LOG_AUDIT: Enable audit logging (default: true)

        Returns:
            LoggingConfig: Configured logging instance
        """
        # Determine format based on environment
        default_format = (
            LogFormat.JSON if settings.ENVIRONMENT == "production" else LogFormat.TEXT
        )

        return cls(
            level=LogLevel(getattr(settings, "LOG_LEVEL", "INFO")),
            format=LogFormat(getattr(settings, "LOG_FORMAT", default_format)),
            log_file=getattr(settings, "LOG_FILE", None),
            max_file_size=int(getattr(settings, "LOG_MAX_FILE_SIZE", 100)),
            backup_count=int(getattr(settings, "LOG_BACKUP_COUNT", 7)),
            enable_colors=getattr(settings, "LOG_ENABLE_COLORS", True),
            enable_diagnose=getattr(settings, "LOG_ENABLE_DIAGNOSE", False),
            correlation_enabled=getattr(settings, "LOG_CORRELATION", True),
            performance_logging=getattr(settings, "LOG_PERFORMANCE", True),
            audit_logging=getattr(settings, "LOG_AUDIT", True),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "level": self.level.value,
            "format": self.format.value,
            "log_file": self.log_file,
            "max_file_size": self.max_file_size,
            "backup_count": self.backup_count,
            "enable_colors": self.enable_colors,
            "enable_backtrace": self.enable_backtrace,
            "enable_diagnose": self.enable_diagnose,
            "correlation_enabled": self.correlation_enabled,
            "performance_logging": self.performance_logging,
            "audit_logging": self.audit_logging,
        }


def configure_module_logging(
    module_name: str, level: LogLevel, config: LoggingConfig | None = None
) -> None:
    """
    Configure logging level for a specific module.

    Args:
        module_name: Module name (e.g., "app.api.routes")
        level: Log level for this module
        config: Optional logging configuration to update

    Example:
        # Quiet down noisy third-party library
        configure_module_logging("sqlalchemy.engine", LogLevel.WARNING)

        # Enable debug logging for specific module
        configure_module_logging("app.scheduling.engine", LogLevel.DEBUG)
    """
    stdlib_logger = logging.getLogger(module_name)
    stdlib_logger.setLevel(level.value)

    if config:
        config.module_levels[module_name] = level

    logger.info(f"Configured logging for {module_name}: {level.value}")


def configure_third_party_logging() -> None:
    """
    Configure logging levels for third-party libraries.

    Reduces noise from verbose third-party packages while maintaining
    visibility for important messages.
    """
    # Quiet down SQLAlchemy
    configure_module_logging("sqlalchemy.engine", LogLevel.WARNING)
    configure_module_logging("sqlalchemy.pool", LogLevel.WARNING)
    configure_module_logging("sqlalchemy.orm", LogLevel.WARNING)

    # Quiet down HTTPX
    configure_module_logging("httpx", LogLevel.WARNING)
    configure_module_logging("httpcore", LogLevel.WARNING)

    # Quiet down Uvicorn access logs (use our middleware instead)
    configure_module_logging("uvicorn.access", LogLevel.WARNING)
    configure_module_logging("uvicorn.error", LogLevel.INFO)

    # Quiet down Celery (unless debugging)
    configure_module_logging("celery", LogLevel.INFO)
    configure_module_logging("celery.worker", LogLevel.INFO)

    # Redis
    configure_module_logging("redis", LogLevel.WARNING)
    configure_module_logging("aioredis", LogLevel.WARNING)

    logger.debug("Configured third-party library logging levels")


def get_logging_config() -> LoggingConfig:
    """
    Get current logging configuration.

    Returns:
        LoggingConfig: Current logging configuration
    """
    return LoggingConfig.from_env()


# Global logging configuration
_logging_config: LoggingConfig | None = None


def set_logging_config(config: LoggingConfig) -> None:
    """Set global logging configuration."""
    global _logging_config
    _logging_config = config
    logger.debug(f"Updated logging configuration: {config.to_dict()}")


def get_current_config() -> LoggingConfig:
    """Get current global logging configuration."""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig.from_env()
    return _logging_config
