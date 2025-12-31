"""
Rate limiting middleware for MCP tools.

This module provides rate limiting to prevent abuse.
"""

import logging
import time
from collections import defaultdict
from typing import Any, Callable

from ..tools.base import ToolError

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.

    Uses token bucket algorithm for smooth rate limiting.
    """

    def __init__(
        self,
        rate: int = 100,  # tokens per minute
        burst: int = 10,  # max burst size
    ):
        """
        Initialize rate limiter.

        Args:
            rate: Tokens per minute
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.time()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on time elapsed
        tokens_to_add = elapsed * (self.rate / 60.0)
        self.tokens = min(self.burst, self.tokens + tokens_to_add)
        self.last_update = now

    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False otherwise
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def get_available_tokens(self) -> float:
        """
        Get available tokens.

        Returns:
            Number of available tokens
        """
        self._refill()
        return self.tokens


class RateLimitMiddleware:
    """
    Rate limiting middleware for MCP tools.

    Prevents excessive tool usage.
    """

    def __init__(
        self,
        enabled: bool = True,
        rate: int = 100,  # requests per minute
        burst: int = 10,  # max burst
    ):
        """
        Initialize rate limit middleware.

        Args:
            enabled: Whether rate limiting is enabled
            rate: Requests per minute
            burst: Maximum burst size
        """
        self.enabled = enabled
        self.rate = rate
        self.burst = burst

        # Per-tool rate limiters
        self._limiters: dict[str, RateLimiter] = defaultdict(
            lambda: RateLimiter(rate=self.rate, burst=self.burst)
        )

        # Global rate limiter
        self._global_limiter = RateLimiter(rate=self.rate * 2, burst=self.burst * 2)

    async def __call__(
        self, tool_name: str, next_handler: Callable[..., Any], **kwargs: Any
    ) -> Any:
        """
        Middleware handler.

        Args:
            tool_name: Name of tool being executed
            next_handler: Next handler in chain
            **kwargs: Tool parameters

        Returns:
            Result from next handler

        Raises:
            ToolError: If rate limit exceeded
        """
        if not self.enabled:
            return await next_handler(**kwargs)

        # Check global rate limit
        if not self._global_limiter.acquire():
            raise ToolError(
                "Global rate limit exceeded",
                details={
                    "tool": tool_name,
                    "rate": self.rate * 2,
                    "retry_after": "60s",
                },
            )

        # Check per-tool rate limit
        limiter = self._limiters[tool_name]
        if not limiter.acquire():
            raise ToolError(
                f"Rate limit exceeded for {tool_name}",
                details={
                    "tool": tool_name,
                    "rate": self.rate,
                    "retry_after": "60s",
                },
            )

        logger.debug(
            f"Rate limit check passed for {tool_name}",
            extra={
                "tool": tool_name,
                "available_tokens": limiter.get_available_tokens(),
            },
        )

        return await next_handler(**kwargs)

    def reset(self, tool_name: str | None = None) -> None:
        """
        Reset rate limiter.

        Args:
            tool_name: Optional tool name. If None, reset all.
        """
        if tool_name is None:
            self._limiters.clear()
            self._global_limiter = RateLimiter(
                rate=self.rate * 2, burst=self.burst * 2
            )
        else:
            if tool_name in self._limiters:
                del self._limiters[tool_name]

    def get_stats(self, tool_name: str) -> dict[str, Any]:
        """
        Get rate limit stats for a tool.

        Args:
            tool_name: Tool name

        Returns:
            Stats dictionary
        """
        limiter = self._limiters.get(tool_name)
        if limiter is None:
            return {
                "tool": tool_name,
                "available_tokens": self.burst,
                "rate": self.rate,
                "burst": self.burst,
            }

        return {
            "tool": tool_name,
            "available_tokens": limiter.get_available_tokens(),
            "rate": self.rate,
            "burst": self.burst,
        }
