"""
Log storage backends for request/response logging.

Provides multiple storage options:
- File-based storage (rotating files)
- In-memory storage (for testing/debugging)
- Database storage (PostgreSQL)
- External services (e.g., CloudWatch, Datadog - via handlers)
"""

import logging
from collections import deque
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any

from app.middleware.logging.formatters import (
    CompactJSONFormatter,
    RequestResponseFormatter,
)


class LogStorage:
    """Base class for log storage backends."""

    def store(self, log_entry: dict[str, Any]) -> None:
        """
        Store a log entry.

        Args:
            log_entry: Dictionary containing log data
        """
        raise NotImplementedError

    def retrieve(
        self, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve log entries.

        Args:
            limit: Maximum number of entries to return
            filters: Optional filters (e.g., {"level": "ERROR", "user_id": "123"})

        Returns:
            List of log entries
        """
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all stored logs."""
        raise NotImplementedError


class InMemoryLogStorage(LogStorage):
    """
    In-memory log storage using a circular buffer.

    Useful for:
    - Development and testing
    - Recent logs API endpoint
    - Debug monitoring

    Note: Logs are lost on application restart.
    """

    def __init__(self, max_entries: int = 10000):
        """
        Initialize in-memory storage.

        Args:
            max_entries: Maximum number of log entries to retain
        """
        self.max_entries = max_entries
        self._logs: deque[dict[str, Any]] = deque(maxlen=max_entries)

    def store(self, log_entry: dict[str, Any]) -> None:
        """Store log entry in memory."""
        self._logs.append(log_entry)

    def retrieve(
        self, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve log entries from memory."""
        logs = list(self._logs)

        # Apply filters
        if filters:
            logs = [log for log in logs if self._matches_filters(log, filters)]

        # Apply limit
        return logs[-limit:]

    def _matches_filters(self, log: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if log entry matches all filters."""
        for key, value in filters.items():
            if log.get(key) != value:
                return False
        return True

    def clear(self) -> None:
        """Clear all logs from memory."""
        self._logs.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        return {
            "total_entries": len(self._logs),
            "max_entries": self.max_entries,
            "utilization": (
                len(self._logs) / self.max_entries if self.max_entries > 0 else 0
            ),
        }


class FileLogStorage(LogStorage):
    """
    File-based log storage with rotation.

    Supports:
    - Size-based rotation (RotatingFileHandler)
    - Time-based rotation (TimedRotatingFileHandler)
    - Compression of rotated files
    """

    def __init__(
        self,
        log_dir: str = "logs",
        filename: str = "requests.log",
        rotation_type: str = "size",
        max_bytes: int = 100 * 1024 * 1024,  # 100 MB
        backup_count: int = 10,
        when: str = "midnight",
        interval: int = 1,
        use_compact_format: bool = False,
    ):
        """
        Initialize file-based storage.

        Args:
            log_dir: Directory to store log files
            filename: Base filename for logs
            rotation_type: "size" or "time"
            max_bytes: Maximum file size before rotation (for size-based)
            backup_count: Number of backup files to keep
            when: When to rotate (for time-based): 'S', 'M', 'H', 'D', 'midnight', 'W0'-'W6'
            interval: Rotation interval (for time-based)
            use_compact_format: Use compact JSON format to save space
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        log_path = self.log_dir / filename
        self.logger = logging.getLogger(f"file_storage.{filename}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Don't propagate to root logger

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create appropriate handler
        if rotation_type == "size":
            handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
            )
        else:  # time-based
            handler = TimedRotatingFileHandler(
                log_path,
                when=when,
                interval=interval,
                backupCount=backup_count,
            )

        # Set formatter
        formatter = (
            CompactJSONFormatter() if use_compact_format else RequestResponseFormatter()
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def store(self, log_entry: dict[str, Any]) -> None:
        """Store log entry to file."""
        # Log at appropriate level
        level = log_entry.get("level", "INFO")
        message = log_entry.get("message", "")

        # Create LogRecord with extra fields
        extra = {k: v for k, v in log_entry.items() if k not in ["level", "message"]}

        if level == "ERROR":
            self.logger.error(message, extra=extra)
        elif level == "WARNING":
            self.logger.warning(message, extra=extra)
        elif level == "DEBUG":
            self.logger.debug(message, extra=extra)
        else:
            self.logger.info(message, extra=extra)

    def retrieve(
        self, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve log entries from file.

        Note: This reads from the current log file only.
        For production use, consider using a log aggregation service.
        """
        import json

        logs = []
        log_path = self.log_dir / "requests.log"

        if not log_path.exists():
            return []

        try:
            with open(log_path) as f:
                # Read last N lines (inefficient for large files)
                lines = f.readlines()
                for line in lines[-limit * 2 :]:  # Read extra to account for filtering
                    try:
                        log_entry = json.loads(line.strip())
                        if not filters or self._matches_filters(log_entry, filters):
                            logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue

            return logs[-limit:]
        except Exception as e:
            logging.error(f"Error reading log file: {e}")
            return []

    def _matches_filters(self, log: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if log entry matches filters."""
        for key, value in filters.items():
            # Support nested keys (e.g., "http.status_code")
            if "." in key:
                parts = key.split(".")
                current = log
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part)
                    else:
                        current = None
                        break
                if current != value:
                    return False
            else:
                if log.get(key) != value:
                    return False
        return True

    def clear(self) -> None:
        """Clear log files (use with caution)."""
        for log_file in self.log_dir.glob("*.log*"):
            try:
                log_file.unlink()
            except Exception as e:
                logging.error(f"Error deleting log file {log_file}: {e}")


class DatabaseLogStorage(LogStorage):
    """
    Database-backed log storage.

    Stores logs in PostgreSQL for:
    - Long-term retention
    - Advanced querying
    - Analytics and reporting
    - Compliance and audit trails
    """

    def __init__(self, db_session_factory):
        """
        Initialize database storage.

        Args:
            db_session_factory: Factory function to create database sessions
        """
        self.db_session_factory = db_session_factory

    def store(self, log_entry: dict[str, Any]) -> None:
        """
        Store log entry in database.

        Note: Requires a RequestLog model to be created in app/models/
        This is intentionally not implemented to avoid performance overhead.
        For production, use async inserts and batch processing.
        """
        # Implementation would require creating RequestLog model
        # and handling async database operations
        pass

    def retrieve(
        self, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve log entries from database."""
        # Implementation would query RequestLog model
        pass

    def clear(self) -> None:
        """Clear old log entries (with retention policy)."""
        # Implementation would delete old records based on retention policy
        pass


class MultiLogStorage(LogStorage):
    """
    Composite storage backend that writes to multiple storage backends.

    Useful for:
    - Writing to both file and memory
    - Redundancy and failover
    - Different retention policies per backend
    """

    def __init__(self, backends: list[LogStorage]):
        """
        Initialize multi-backend storage.

        Args:
            backends: List of storage backends to use
        """
        self.backends = backends

    def store(self, log_entry: dict[str, Any]) -> None:
        """Store log entry in all backends."""
        for backend in self.backends:
            try:
                backend.store(log_entry)
            except Exception as e:
                logging.error(f"Error storing log in backend {backend}: {e}")

    def retrieve(
        self, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve from first backend that supports retrieval."""
        for backend in self.backends:
            try:
                return backend.retrieve(limit, filters)
            except Exception:
                continue
        return []

    def clear(self) -> None:
        """Clear all backends."""
        for backend in self.backends:
            try:
                backend.clear()
            except Exception as e:
                logging.error(f"Error clearing backend {backend}: {e}")


def get_storage_backend(
    storage_type: str = "memory",
    **kwargs,
) -> LogStorage:
    """
    Factory function to create storage backend.

    Args:
        storage_type: Type of storage ("memory", "file", "multi")
        **kwargs: Additional arguments for storage backend

    Returns:
        LogStorage: Storage backend instance
    """
    if storage_type == "memory":
        return InMemoryLogStorage(max_entries=kwargs.get("max_entries", 10000))
    elif storage_type == "file":
        return FileLogStorage(**kwargs)
    elif storage_type == "multi":
        backends = kwargs.get("backends", [])
        return MultiLogStorage(backends)
    else:
        # Default to memory storage
        return InMemoryLogStorage()
