"""
Redis health check implementation.

Provides comprehensive Redis health monitoring including:
- Connection status
- Ping response time
- Memory usage
- Connected clients
- Key statistics
"""

import asyncio
import logging
import time
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisHealthCheck:
    """
    Redis health check implementation.

    Performs health checks on Redis including:
    - Basic connectivity (PING)
    - Response time measurement
    - Memory usage monitoring
    - Connection count
    - Key space statistics
    """

    def __init__(self, timeout: float = 5.0):
        """
        Initialize Redis health check.

        Args:
            timeout: Maximum time in seconds to wait for health check
        """
        self.timeout = timeout
        self.name = "redis"
        self._redis_client: redis.Redis | None = None

    async def check(self) -> dict[str, Any]:
        """
        Perform Redis health check.

        Returns:
            Dictionary with health status:
            - status: "healthy", "degraded", or "unhealthy"
            - response_time_ms: Ping response time
            - memory_used_mb: Memory usage in MB
            - connected_clients: Number of connected clients
            - keys_total: Total number of keys
            - error: Error message if unhealthy

        Raises:
            TimeoutError: If check exceeds timeout
        """
        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self._perform_check(),
                timeout=self.timeout
            )

            response_time_ms = (time.time() - start_time) * 1000
            result["response_time_ms"] = round(response_time_ms, 2)

            # Determine status based on response time and memory
            if response_time_ms > 500:  # > 500ms is degraded
                result["status"] = "degraded"
                result["warning"] = "Redis response time is slow"
            elif result.get("memory_used_mb", 0) > 1024:  # > 1GB is warning
                if result["status"] == "healthy":
                    result["status"] = "degraded"
                result["warning"] = "Redis memory usage is high"

            return result

        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check timed out after {self.timeout}s")
            return {
                "status": "unhealthy",
                "error": f"Health check timed out after {self.timeout}s",
                "response_time_ms": round(response_time_ms, 2),
            }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": round(response_time_ms, 2),
            }

        finally:
            # Clean up Redis connection
            if self._redis_client:
                await self._redis_client.close()
                self._redis_client = None

    async def _perform_check(self) -> dict[str, Any]:
        """
        Perform the actual Redis health check.

        Returns:
            Dictionary with detailed health information
        """
        try:
            # Create Redis client
            redis_url = settings.redis_url_with_password
            self._redis_client = redis.from_url(redis_url, decode_responses=True)

            # 1. Test basic connectivity with PING
            ping_response = await self._redis_client.ping()
            if not ping_response:
                return {
                    "status": "unhealthy",
                    "error": "Redis PING failed",
                }

            # 2. Get server info
            info = await self._redis_client.info()

            # 3. Get memory statistics
            memory_used_bytes = info.get("used_memory", 0)
            memory_used_mb = memory_used_bytes / (1024 * 1024)

            # 4. Get connection statistics
            connected_clients = info.get("connected_clients", 0)

            # 5. Get key statistics
            keys_total = 0
            try:
                # Get dbsize (total keys across all databases)
                keys_total = await self._redis_client.dbsize()
            except Exception as e:
                logger.warning(f"Could not get key count: {e}")

            # 6. Get Redis version
            redis_version = info.get("redis_version", "unknown")

            # All checks passed
            return {
                "status": "healthy",
                "redis_version": redis_version,
                "memory_used_mb": round(memory_used_mb, 2),
                "connected_clients": connected_clients,
                "keys_total": keys_total,
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return {
                "status": "unhealthy",
                "error": f"Connection error: {str(e)}",
            }

        except redis.RedisError as e:
            logger.error(f"Redis error: {e}")
            return {
                "status": "unhealthy",
                "error": f"Redis error: {str(e)}",
            }

    async def check_read_write(self) -> dict[str, Any]:
        """
        Perform read-write health check (more comprehensive).

        This check writes and reads a test key to verify
        Redis read/write capabilities.

        Returns:
            Dictionary with read-write health status
        """
        try:
            redis_url = settings.redis_url_with_password
            client = redis.from_url(redis_url, decode_responses=True)

            # Write test key
            test_key = "health_check:test"
            test_value = f"test_{int(time.time())}"

            await client.set(test_key, test_value, ex=60)  # Expire in 60 seconds

            # Read back
            read_value = await client.get(test_key)

            # Verify
            if read_value != test_value:
                await client.close()
                return {
                    "status": "degraded",
                    "read_write": "failed",
                    "error": "Value mismatch on read-write test",
                }

            # Delete test key
            await client.delete(test_key)

            await client.close()

            return {
                "status": "healthy",
                "read_write": "functional",
            }

        except redis.RedisError as e:
            logger.error(f"Redis read-write check failed: {e}")
            return {
                "status": "degraded",
                "read_write": "failed",
                "error": str(e),
            }

    async def check_persistence(self) -> dict[str, Any]:
        """
        Check Redis persistence configuration.

        Returns:
            Dictionary with persistence status
        """
        try:
            redis_url = settings.redis_url_with_password
            client = redis.from_url(redis_url, decode_responses=True)

            info = await client.info("persistence")

            await client.close()

            return {
                "status": "healthy",
                "rdb_enabled": info.get("rdb_bgsave_in_progress", 0) == 0,
                "aof_enabled": info.get("aof_enabled", 0) == 1,
                "last_save_time": info.get("rdb_last_save_time", 0),
            }

        except redis.RedisError as e:
            logger.error(f"Redis persistence check failed: {e}")
            return {
                "status": "unknown",
                "error": str(e),
            }
