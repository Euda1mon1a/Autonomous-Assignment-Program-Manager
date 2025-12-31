"""Structured logging configuration with correlation tracking and data redaction."""

import json
import logging
import logging.handlers
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import structlog


# ============================================================================
# CORRELATION ID MANAGEMENT (Task 15)
# ============================================================================


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to all log records."""

    def __init__(self):
        """Initialize filter with context variable."""
        super().__init__()
        self.correlation_id = None

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation ID to log record.

        Args:
            record: Log record to filter

        Returns:
            True to allow logging
        """
        record.correlation_id = self.correlation_id or str(uuid4())
        return True

    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set correlation ID for current context.

        Args:
            correlation_id: Unique correlation ID
        """
        self.correlation_id = correlation_id

    @staticmethod
    def get_correlation_id() -> str:
        """
        Get current correlation ID or generate new one.

        Returns:
            Correlation ID string
        """
        return str(uuid4())


# ============================================================================
# SENSITIVE DATA REDACTION (Task 16)
# ============================================================================


class SensitiveDataRedactor:
    """Redact sensitive data from logs."""

    # Patterns for sensitive data
    PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "api_key": r'(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([^\s"\']+)',
        "token": r'(?:token|authorization)["\']?\s*[:=]\s*["\']?([^\s"\']+)',
        "password": r'(?:password|passwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)',
        "secret": r'(?:secret|secret_key)["\']?\s*[:=]\s*["\']?([^\s"\']+)',
    }

    SENSITIVE_KEYS = {
        "password",
        "passwd",
        "secret",
        "api_key",
        "apikey",
        "token",
        "authorization",
        "auth",
        "access_token",
        "refresh_token",
        "private_key",
        "pem",
        "certificate",
        "ssn",
        "email",
        "phone",
    }

    @classmethod
    def redact(cls, data: str, include_patterns: list | None = None) -> str:
        """
        Redact sensitive data from string.

        Args:
            data: String to redact
            include_patterns: List of pattern names to apply

        Returns:
            Redacted string
        """
        redacted = data
        patterns = include_patterns or list(cls.PATTERNS.keys())

        for pattern_name in patterns:
            if pattern_name in cls.PATTERNS:
                pattern = cls.PATTERNS[pattern_name]
                redacted = re.sub(
                    pattern,
                    f"[REDACTED_{pattern_name.upper()}]",
                    redacted,
                    flags=re.IGNORECASE,
                )

        return redacted

    @classmethod
    def redact_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Redact sensitive data from dictionary.

        Args:
            data: Dictionary to redact

        Returns:
            Dictionary with sensitive data redacted
        """
        redacted = {}

        for key, value in data.items():
            if isinstance(key, str) and any(
                sensitive in key.lower() for sensitive in cls.SENSITIVE_KEYS
            ):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = cls.redact_dict(value)
            elif isinstance(value, str):
                redacted[key] = cls.redact(value)
            elif isinstance(value, list):
                redacted[key] = [
                    cls.redact_dict(item)
                    if isinstance(item, dict)
                    else cls.redact(str(item))
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                redacted[key] = value

        return redacted


# ============================================================================
# STRUCTURED LOGGING CONFIGURATION (Task 14)
# ============================================================================


class JSONFormatter(logging.Formatter):
    """Format log records as JSON with structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "N/A"),
        }

        # Add context fields
        if hasattr(record, "context"):
            context = record.context
            if isinstance(context, dict):
                context = SensitiveDataRedactor.redact_dict(context)
            log_data["context"] = context

        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
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
                "correlation_id",
                "context",
                "getMessage",
            ]:
                if isinstance(value, dict):
                    log_data[key] = SensitiveDataRedactor.redact_dict(value)
                elif isinstance(value, str):
                    log_data[key] = SensitiveDataRedactor.redact(value)
                else:
                    log_data[key] = value

        return json.dumps(log_data)


# ============================================================================
# LOG ROTATION CONFIGURATION (Task 18)
# ============================================================================


def setup_rotating_handler(
    log_path: str,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    formatter: logging.Formatter | None = None,
) -> logging.handlers.RotatingFileHandler:
    """
    Setup rotating file handler.

    Args:
        log_path: Path to log file
        max_bytes: Max file size before rotation
        backup_count: Number of backup files to keep
        formatter: Log formatter

    Returns:
        RotatingFileHandler instance
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count
    )

    if formatter:
        handler.setFormatter(formatter)

    return handler


def setup_timed_rotating_handler(
    log_path: str,
    when: str = "midnight",
    interval: int = 1,
    backup_count: int = 7,
    formatter: logging.Formatter | None = None,
) -> logging.handlers.TimedRotatingFileHandler:
    """
    Setup time-based rotating file handler.

    Args:
        log_path: Path to log file
        when: When to rotate ('midnight', 'hourly', etc)
        interval: Interval for rotation
        backup_count: Number of backup files to keep
        formatter: Log formatter

    Returns:
        TimedRotatingFileHandler instance
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    handler = logging.handlers.TimedRotatingFileHandler(
        log_path, when=when, interval=interval, backupCount=backup_count
    )

    if formatter:
        handler.setFormatter(formatter)

    return handler


# ============================================================================
# LOG LEVEL MANAGEMENT (Task 17)
# ============================================================================


class LogLevelManager:
    """Manage log levels at runtime."""

    _levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    _loggers = {}

    @classmethod
    def register_logger(cls, name: str, logger: logging.Logger) -> None:
        """
        Register logger for management.

        Args:
            name: Logger name
            logger: Logger instance
        """
        cls._loggers[name] = logger

    @classmethod
    def set_level(cls, logger_name: str, level: str) -> None:
        """
        Set log level for logger.

        Args:
            logger_name: Name of logger
            level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if logger_name in cls._loggers:
            level_int = cls._levels.get(level.upper(), logging.INFO)
            cls._loggers[logger_name].setLevel(level_int)

    @classmethod
    def get_level(cls, logger_name: str) -> str:
        """
        Get current log level.

        Args:
            logger_name: Name of logger

        Returns:
            Log level string
        """
        if logger_name in cls._loggers:
            level_int = cls._loggers[logger_name].level
            for name, level in cls._levels.items():
                if level == level_int:
                    return name
        return "INFO"

    @classmethod
    def set_global_level(cls, level: str) -> None:
        """
        Set log level for all registered loggers.

        Args:
            level: Log level string
        """
        for logger_name in cls._loggers:
            cls.set_level(logger_name, level)


# ============================================================================
# COMPREHENSIVE LOGGING SETUP (Task 13)
# ============================================================================


def configure_logging(
    log_dir: str = "/var/log/residency-scheduler",
    level: str = "INFO",
    console: bool = True,
    file: bool = True,
    json_format: bool = True,
) -> None:
    """
    Configure comprehensive logging system.

    Args:
        log_dir: Directory for log files
        level: Log level
        console: Enable console logging
        file: Enable file logging
        json_format: Use JSON formatting
    """
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)

    # Setup formatters
    json_formatter = JSONFormatter()
    text_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s"
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Add console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter if json_format else text_formatter)
        console_handler.addFilter(CorrelationIdFilter())
        root_logger.addHandler(console_handler)

    # Add file handlers
    if file:
        # General application logs
        app_handler = setup_rotating_handler(
            os.path.join(log_dir, "app.log"),
            formatter=json_formatter if json_format else text_formatter,
        )
        app_handler.addFilter(CorrelationIdFilter())
        root_logger.addHandler(app_handler)

        # Error logs
        error_handler = setup_rotating_handler(
            os.path.join(log_dir, "error.log"),
            formatter=json_formatter if json_format else text_formatter,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(CorrelationIdFilter())
        root_logger.addHandler(error_handler)

    # Setup category-specific loggers
    setup_category_loggers(log_dir, json_formatter)

    # Register loggers for management
    LogLevelManager.register_logger("root", root_logger)


def setup_category_loggers(log_dir: str, formatter: logging.Formatter) -> None:
    """
    Setup category-specific loggers.

    Args:
        log_dir: Directory for log files
        formatter: Log formatter
    """
    categories = {
        "audit": ("audit.log", logging.INFO),
        "security": ("security.log", logging.WARNING),
        "performance": ("performance.log", logging.INFO),
        "compliance": ("compliance.log", logging.INFO),
    }

    for category, (log_file, level) in categories.items():
        logger = logging.getLogger(f"app.{category}")
        logger.setLevel(level)

        handler = setup_rotating_handler(
            os.path.join(log_dir, log_file), formatter=formatter
        )
        handler.addFilter(CorrelationIdFilter())
        logger.addHandler(handler)

        LogLevelManager.register_logger(f"app.{category}", logger)


# ============================================================================
# AUDIT TRAIL LOGGING (Task 19)
# ============================================================================


class AuditLogger:
    """Log audit events for compliance."""

    def __init__(self, logger_name: str = "app.audit"):
        """Initialize audit logger."""
        self.logger = logging.getLogger(logger_name)

    def log_user_action(
        self,
        action: str,
        user_id: str,
        resource: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log user action.

        Args:
            action: Action performed
            user_id: ID of user
            resource: Resource affected
            details: Additional details
        """
        log_data = {
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if details:
            log_data["details"] = SensitiveDataRedactor.redact_dict(details)

        self.logger.info(f"AUDIT: {action}", extra={"context": log_data})

    def log_access(
        self,
        user_id: str,
        resource: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log resource access.

        Args:
            user_id: ID of user
            resource: Resource accessed
            status: Access status (allowed/denied)
            details: Additional details
        """
        log_data = {
            "user_id": user_id,
            "resource": resource,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if details:
            log_data["details"] = SensitiveDataRedactor.redact_dict(details)

        level = logging.WARNING if status == "denied" else logging.INFO
        self.logger.log(level, f"ACCESS: {status}", extra={"context": log_data})

    def log_configuration_change(
        self, user_id: str, config_key: str, old_value: Any, new_value: Any
    ) -> None:
        """
        Log configuration change.

        Args:
            user_id: ID of user making change
            config_key: Configuration key
            old_value: Old value
            new_value: New value
        """
        log_data = {
            "user_id": user_id,
            "config_key": config_key,
            "old_value": str(SensitiveDataRedactor.redact(str(old_value))),
            "new_value": str(SensitiveDataRedactor.redact(str(new_value))),
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.logger.info("CONFIG_CHANGE", extra={"context": log_data})


# ============================================================================
# PERFORMANCE LOGGING (Task 20)
# ============================================================================


class PerformanceLogger:
    """Log performance metrics."""

    def __init__(self, logger_name: str = "app.performance"):
        """Initialize performance logger."""
        self.logger = logging.getLogger(logger_name)

    def log_query_performance(
        self,
        query: str,
        duration_ms: float,
        rows_affected: int,
        slow_threshold_ms: float = 100.0,
    ) -> None:
        """
        Log database query performance.

        Args:
            query: Query executed
            duration_ms: Execution time in milliseconds
            rows_affected: Number of rows affected
            slow_threshold_ms: Threshold for slow queries
        """
        level = logging.WARNING if duration_ms > slow_threshold_ms else logging.INFO

        log_data = {
            "query": query,
            "duration_ms": duration_ms,
            "rows_affected": rows_affected,
            "slow": duration_ms > slow_threshold_ms,
        }

        self.logger.log(level, "DB_QUERY", extra={"context": log_data})

    def log_endpoint_performance(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
        slow_threshold_ms: float = 500.0,
    ) -> None:
        """
        Log API endpoint performance.

        Args:
            endpoint: API endpoint
            method: HTTP method
            duration_ms: Response time in milliseconds
            status_code: HTTP status code
            slow_threshold_ms: Threshold for slow requests
        """
        level = logging.WARNING if duration_ms > slow_threshold_ms else logging.INFO

        log_data = {
            "endpoint": endpoint,
            "method": method,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "slow": duration_ms > slow_threshold_ms,
        }

        self.logger.log(level, "ENDPOINT_PERFORMANCE", extra={"context": log_data})


# ============================================================================
# SECURITY EVENT LOGGING (Task 21)
# ============================================================================


class SecurityLogger:
    """Log security events."""

    def __init__(self, logger_name: str = "app.security"):
        """Initialize security logger."""
        self.logger = logging.getLogger(logger_name)

    def log_authentication_attempt(
        self, username: str, success: bool, ip_address: str, reason: str | None = None
    ) -> None:
        """
        Log authentication attempt.

        Args:
            username: Username
            success: Whether authentication succeeded
            ip_address: IP address of request
            reason: Reason for failure
        """
        level = logging.WARNING if not success else logging.INFO

        log_data = {
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.logger.log(level, "AUTH_ATTEMPT", extra={"context": log_data})

    def log_authorization_failure(
        self, user_id: str, action: str, resource: str, reason: str
    ) -> None:
        """
        Log authorization failure.

        Args:
            user_id: ID of user
            action: Action attempted
            resource: Resource accessed
            reason: Reason for failure
        """
        log_data = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.logger.warning("AUTHZ_FAILURE", extra={"context": log_data})

    def log_suspicious_activity(
        self,
        activity_type: str,
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log suspicious activity.

        Args:
            activity_type: Type of suspicious activity
            user_id: ID of user involved
            details: Additional details
        """
        log_data = {
            "activity_type": activity_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if details:
            log_data["details"] = SensitiveDataRedactor.redact_dict(details)

        self.logger.warning("SUSPICIOUS_ACTIVITY", extra={"context": log_data})


# ============================================================================
# LOGGER INSTANCES
# ============================================================================

audit_logger = AuditLogger()
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
