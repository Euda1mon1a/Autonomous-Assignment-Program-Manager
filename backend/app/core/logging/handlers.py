"""
Custom log handlers for specialized logging destinations.

Provides handlers for:
- Database logging (audit trail)
- Redis logging (real-time monitoring)
- Webhook logging (external systems)
- Rotating file handlers with compression
- Async batch handlers for high-throughput
"""

import asyncio
import gzip
import json
import logging
import shutil
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

settings = get_settings()


class AsyncLogHandler(ABC):
    """
    Abstract base class for asynchronous log handlers.

    Provides buffering and batch processing for high-throughput logging.
    """

    def __init__(
        self,
        buffer_size: int = 100,
        flush_interval: float = 5.0,
        max_retries: int = 3,
    ):
        """
        Initialize async log handler.

        Args:
            buffer_size: Number of log entries to buffer before flush
            flush_interval: Maximum time (seconds) before flush
            max_retries: Maximum number of retry attempts
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self._buffer: Deque[dict[str, Any]] = deque(maxlen=buffer_size)
        self._last_flush = datetime.utcnow()
        self._flush_lock = asyncio.Lock()

    @abstractmethod
    async def _flush_batch(self, entries: list[dict[str, Any]]) -> None:
        """
        Flush a batch of log entries.

        Implemented by subclasses to handle specific destination.

        Args:
            entries: List of log entry dictionaries to flush
        """
        pass

    async def emit(self, entry: dict[str, Any]) -> None:
        """
        Emit a log entry.

        Buffers the entry and flushes when buffer is full or interval exceeded.

        Args:
            entry: Log entry dictionary
        """
        self._buffer.append(entry)

        # Check if we should flush
        should_flush = (
            len(self._buffer) >= self.buffer_size
            or (datetime.utcnow() - self._last_flush).total_seconds()
            >= self.flush_interval
        )

        if should_flush:
            await self.flush()

    async def flush(self) -> None:
        """Flush buffered log entries."""
        async with self._flush_lock:
            if not self._buffer:
                return

            # Get current buffer contents
            entries = list(self._buffer)
            self._buffer.clear()
            self._last_flush = datetime.utcnow()

            # Attempt to flush with retries
            for attempt in range(self.max_retries):
                try:
                    await self._flush_batch(entries)
                    return
                except Exception as e:
                    logger.warning(
                        f"Failed to flush logs (attempt {attempt + 1}/{self.max_retries}): {e}"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2**attempt)  # Exponential backoff
                    else:
                        logger.error(f"Failed to flush {len(entries)} log entries after retries")


class DatabaseLogHandler(AsyncLogHandler):
    """
    Log handler that stores logs in database.

    Useful for audit trails and compliance logging.
    """

    def __init__(
        self,
        db_session_factory,
        table_name: str = "audit_logs",
        **kwargs,
    ):
        """
        Initialize database log handler.

        Args:
            db_session_factory: Factory function that returns AsyncSession
            table_name: Name of database table for logs
            **kwargs: Additional arguments for AsyncLogHandler
        """
        super().__init__(**kwargs)
        self.db_session_factory = db_session_factory
        self.table_name = table_name

    async def _flush_batch(self, entries: list[dict[str, Any]]) -> None:
        """Flush batch to database."""
        async with self.db_session_factory() as session:
            # In production, this would insert into actual table
            # For now, just log the action
            logger.debug(
                f"Flushing {len(entries)} log entries to database table {self.table_name}"
            )

            # Example implementation (would need actual model):
            # from app.models.audit_log import AuditLog
            # logs = [AuditLog(**entry) for entry in entries]
            # session.add_all(logs)
            # await session.commit()


class RedisLogHandler(AsyncLogHandler):
    """
    Log handler that publishes logs to Redis.

    Useful for real-time monitoring and log aggregation.
    """

    def __init__(
        self,
        redis_client,
        channel: str = "app:logs",
        ttl: int = 86400,  # 24 hours
        **kwargs,
    ):
        """
        Initialize Redis log handler.

        Args:
            redis_client: Redis client instance
            channel: Redis channel for pub/sub
            ttl: Time-to-live for log entries (seconds)
            **kwargs: Additional arguments for AsyncLogHandler
        """
        super().__init__(**kwargs)
        self.redis = redis_client
        self.channel = channel
        self.ttl = ttl

    async def _flush_batch(self, entries: list[dict[str, Any]]) -> None:
        """Flush batch to Redis."""
        try:
            # Publish to channel for real-time monitoring
            for entry in entries:
                await self.redis.publish(self.channel, json.dumps(entry))

            # Also store in list with TTL for historical access
            key = f"logs:{datetime.utcnow().strftime('%Y-%m-%d:%H')}"
            await self.redis.rpush(key, *[json.dumps(e) for e in entries])
            await self.redis.expire(key, self.ttl)

            logger.debug(f"Flushed {len(entries)} log entries to Redis channel {self.channel}")
        except Exception as e:
            logger.error(f"Failed to flush logs to Redis: {e}")
            raise


class WebhookLogHandler(AsyncLogHandler):
    """
    Log handler that sends logs to external webhook.

    Useful for integrating with external monitoring systems (Slack, PagerDuty, etc.).
    """

    def __init__(
        self,
        webhook_url: str,
        headers: dict[str, str] | None = None,
        min_level: str = "WARNING",
        **kwargs,
    ):
        """
        Initialize webhook log handler.

        Args:
            webhook_url: URL to send log data
            headers: Optional HTTP headers
            min_level: Minimum log level to send (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            **kwargs: Additional arguments for AsyncLogHandler
        """
        super().__init__(**kwargs)
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.min_level = min_level
        self._client = httpx.AsyncClient(timeout=10.0)

    async def _flush_batch(self, entries: list[dict[str, Any]]) -> None:
        """Flush batch to webhook."""
        # Filter by minimum level
        level_order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        min_level_idx = level_order.index(self.min_level)

        filtered_entries = [
            entry
            for entry in entries
            if level_order.index(entry.get("level", "INFO")) >= min_level_idx
        ]

        if not filtered_entries:
            return

        try:
            response = await self._client.post(
                self.webhook_url,
                json={"logs": filtered_entries},
                headers=self.headers,
            )
            response.raise_for_status()

            logger.debug(
                f"Sent {len(filtered_entries)} log entries to webhook {self.webhook_url}"
            )
        except Exception as e:
            logger.error(f"Failed to send logs to webhook: {e}")
            raise

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()


class CompressedRotatingFileHandler:
    """
    Rotating file handler with automatic compression.

    Features:
    - Size-based rotation
    - Automatic gzip compression of rotated files
    - Configurable retention policy
    """

    def __init__(
        self,
        filepath: str,
        max_bytes: int = 100 * 1024 * 1024,  # 100 MB
        backup_count: int = 7,
        compress: bool = True,
    ):
        """
        Initialize compressed rotating file handler.

        Args:
            filepath: Path to log file
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep
            compress: Whether to compress rotated files
        """
        self.filepath = Path(filepath)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.compress = compress

        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def should_rotate(self) -> bool:
        """Check if file should be rotated."""
        if not self.filepath.exists():
            return False

        return self.filepath.stat().st_size >= self.max_bytes

    def rotate(self) -> None:
        """Rotate log files."""
        if not self.filepath.exists():
            return

        # Close current file handler (would be done by loguru)

        # Rotate existing backups
        for i in range(self.backup_count - 1, 0, -1):
            old_file = self.filepath.with_suffix(f".{i}.gz" if self.compress else f".{i}")
            new_file = self.filepath.with_suffix(
                f".{i + 1}.gz" if self.compress else f".{i + 1}"
            )

            if old_file.exists():
                if i + 1 > self.backup_count:
                    old_file.unlink()  # Delete oldest
                else:
                    shutil.move(str(old_file), str(new_file))

        # Rotate current file
        if self.compress:
            # Compress current file to .1.gz
            with open(self.filepath, "rb") as f_in:
                with gzip.open(self.filepath.with_suffix(".1.gz"), "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove uncompressed file
            self.filepath.unlink()
        else:
            # Just rename to .1
            shutil.move(str(self.filepath), str(self.filepath.with_suffix(".1")))

        logger.info(f"Rotated log file: {self.filepath}")


# Factory functions for handler creation


def create_database_handler(
    db_session_factory,
    buffer_size: int = 100,
) -> DatabaseLogHandler:
    """
    Create database log handler.

    Args:
        db_session_factory: Database session factory
        buffer_size: Buffer size for batching

    Returns:
        DatabaseLogHandler: Configured handler
    """
    return DatabaseLogHandler(
        db_session_factory=db_session_factory,
        buffer_size=buffer_size,
    )


def create_redis_handler(
    redis_client,
    channel: str = "app:logs",
    buffer_size: int = 100,
) -> RedisLogHandler:
    """
    Create Redis log handler.

    Args:
        redis_client: Redis client instance
        channel: Redis pub/sub channel
        buffer_size: Buffer size for batching

    Returns:
        RedisLogHandler: Configured handler
    """
    return RedisLogHandler(
        redis_client=redis_client,
        channel=channel,
        buffer_size=buffer_size,
    )


def create_webhook_handler(
    webhook_url: str,
    min_level: str = "WARNING",
    buffer_size: int = 10,
) -> WebhookLogHandler:
    """
    Create webhook log handler.

    Args:
        webhook_url: Webhook URL
        min_level: Minimum log level to send
        buffer_size: Buffer size for batching

    Returns:
        WebhookLogHandler: Configured handler
    """
    return WebhookLogHandler(
        webhook_url=webhook_url,
        min_level=min_level,
        buffer_size=buffer_size,
    )
