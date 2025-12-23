"""
Service proxy for API gateway.

Provides service proxy functionality with load balancing, circuit breaking,
and service discovery integration.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from fastapi import Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProxyStrategy(str, Enum):
    """Proxy strategy types."""

    FORWARD = "forward"  # Simple forward proxy
    CACHE = "cache"  # Cache responses
    RETRY = "retry"  # Retry on failure
    CIRCUIT_BREAKER = "circuit_breaker"  # Circuit breaker pattern
    RATE_LIMIT = "rate_limit"  # Rate limiting


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class ProxyConfig(BaseModel):
    """Configuration for service proxy."""

    name: str = Field(..., description="Proxy name")
    target_url: str = Field(..., description="Target service URL")
    timeout_seconds: int = Field(
        default=30,
        description="Request timeout in seconds",
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts on failure",
    )
    retry_delay_ms: int = Field(
        default=100,
        description="Delay between retries in milliseconds",
    )
    retry_backoff_multiplier: float = Field(
        default=2.0,
        description="Exponential backoff multiplier",
    )
    circuit_breaker_enabled: bool = Field(
        default=True,
        description="Enable circuit breaker",
    )
    circuit_breaker_threshold: int = Field(
        default=5,
        description="Failures before circuit opens",
    )
    circuit_breaker_timeout_seconds: int = Field(
        default=60,
        description="Seconds to keep circuit open",
    )
    circuit_breaker_half_open_requests: int = Field(
        default=3,
        description="Requests allowed in half-open state",
    )
    cache_enabled: bool = Field(
        default=False,
        description="Enable response caching",
    )
    cache_ttl_seconds: int = Field(
        default=300,
        description="Cache TTL in seconds",
    )
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting",
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Maximum requests per window",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate limit window in seconds",
    )
    preserve_host_header: bool = Field(
        default=False,
        description="Preserve original Host header",
    )
    follow_redirects: bool = Field(
        default=False,
        description="Follow HTTP redirects",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Additional headers to add",
    )

    class Config:
        use_enum_values = True


@dataclass
class CircuitBreaker:
    """Circuit breaker for service proxy."""

    threshold: int
    timeout_seconds: int
    half_open_requests: int
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    half_open_attempts: int = 0

    def record_success(self) -> None:
        """Record successful request."""
        self.success_count += 1

        if self.state == CircuitState.HALF_OPEN:
            # Check if we can close the circuit
            if self.success_count >= self.half_open_requests:
                logger.info("Circuit breaker transitioning to CLOSED state")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.half_open_attempts = 0

    def record_failure(self) -> None:
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self.failure_count >= self.threshold:
                logger.warning(
                    f"Circuit breaker opening after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
                self.success_count = 0

        elif self.state == CircuitState.HALF_OPEN:
            # Failure in half-open, go back to open
            logger.warning("Circuit breaker returning to OPEN state after failure")
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.half_open_attempts = 0

    def can_request(self) -> bool:
        """
        Check if request is allowed.

        Returns:
            bool: True if request is allowed
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time:
                elapsed = datetime.utcnow() - self.last_failure_time
                if elapsed.total_seconds() >= self.timeout_seconds:
                    logger.info("Circuit breaker transitioning to HALF_OPEN state")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_attempts = 0
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited requests
            if self.half_open_attempts < self.half_open_requests:
                self.half_open_attempts += 1
                return True
            return False

        return False


@dataclass
class CacheEntry:
    """Cache entry for proxy responses."""

    data: Any
    timestamp: datetime
    ttl_seconds: int

    def is_expired(self) -> bool:
        """
        Check if cache entry is expired.

        Returns:
            bool: True if expired
        """
        elapsed = datetime.utcnow() - self.timestamp
        return elapsed.total_seconds() >= self.ttl_seconds


@dataclass
class RateLimiter:
    """Rate limiter for service proxy."""

    max_requests: int
    window_seconds: int
    requests: list[datetime] = field(default_factory=list)

    def can_request(self) -> bool:
        """
        Check if request is allowed.

        Returns:
            bool: True if request is allowed
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Remove old requests
        self.requests = [r for r in self.requests if r > cutoff]

        # Check limit
        if len(self.requests) >= self.max_requests:
            return False

        # Record request
        self.requests.append(now)
        return True

    def get_retry_after(self) -> int:
        """
        Get seconds until next request allowed.

        Returns:
            int: Seconds to wait
        """
        if not self.requests:
            return 0

        oldest = min(self.requests)
        elapsed = (datetime.utcnow() - oldest).total_seconds()
        return max(0, int(self.window_seconds - elapsed))


class ServiceProxy:
    """
    Service proxy for API gateway.

    Provides proxy functionality with circuit breaking, retries, caching,
    and rate limiting.
    """

    def __init__(self, config: ProxyConfig):
        """
        Initialize service proxy.

        Args:
            config: Proxy configuration
        """
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            follow_redirects=config.follow_redirects,
            verify=config.verify_ssl,
        )

        # Circuit breaker
        self.circuit_breaker: CircuitBreaker | None = None
        if config.circuit_breaker_enabled:
            self.circuit_breaker = CircuitBreaker(
                threshold=config.circuit_breaker_threshold,
                timeout_seconds=config.circuit_breaker_timeout_seconds,
                half_open_requests=config.circuit_breaker_half_open_requests,
            )

        # Cache
        self.cache: dict[str, CacheEntry] = {}

        # Rate limiter
        self.rate_limiter: RateLimiter | None = None
        if config.rate_limit_enabled:
            self.rate_limiter = RateLimiter(
                max_requests=config.rate_limit_requests,
                window_seconds=config.rate_limit_window_seconds,
            )

        logger.info(
            f"Service proxy '{config.name}' initialized for {config.target_url}"
        )

    async def proxy_request(
        self,
        request: Request,
        path: str,
        body: bytes | None = None,
    ) -> httpx.Response:
        """
        Proxy request to target service.

        Args:
            request: Original request
            path: Path to append to target URL
            body: Request body

        Returns:
            httpx.Response: Response from target service

        Raises:
            httpx.HTTPError: If request fails after retries
            ValueError: If circuit breaker is open or rate limit exceeded
        """
        # Check circuit breaker
        if self.circuit_breaker and not self.circuit_breaker.can_request():
            raise ValueError(
                f"Circuit breaker is {self.circuit_breaker.state.value} "
                f"for proxy '{self.config.name}'"
            )

        # Check rate limiter
        if self.rate_limiter and not self.rate_limiter.can_request():
            retry_after = self.rate_limiter.get_retry_after()
            raise ValueError(
                f"Rate limit exceeded for proxy '{self.config.name}'. "
                f"Retry after {retry_after} seconds"
            )

        # Check cache
        if self.config.cache_enabled:
            cache_key = self._get_cache_key(request.method, path)
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if not entry.is_expired():
                    logger.debug(f"Cache hit for {cache_key}")
                    # Return cached response
                    return self._create_response_from_cache(entry)
                else:
                    # Remove expired entry
                    del self.cache[cache_key]

        # Execute request with retries
        last_error = None
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self._execute_request(request, path, body)

                # Record success
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()

                # Cache response
                if self.config.cache_enabled and request.method == "GET":
                    cache_key = self._get_cache_key(request.method, path)
                    self.cache[cache_key] = CacheEntry(
                        data=response.content,
                        timestamp=datetime.utcnow(),
                        ttl_seconds=self.config.cache_ttl_seconds,
                    )

                return response

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Request attempt {attempt + 1}/{self.config.retry_attempts} "
                    f"failed for proxy '{self.config.name}': {e}"
                )

                # Record failure
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()

                # Don't retry on last attempt
                if attempt < self.config.retry_attempts - 1:
                    # Exponential backoff
                    delay = (
                        self.config.retry_delay_ms
                        * (self.config.retry_backoff_multiplier**attempt)
                    ) / 1000
                    await asyncio.sleep(delay)

        # All retries failed
        raise last_error

    async def _execute_request(
        self,
        request: Request,
        path: str,
        body: bytes | None,
    ) -> httpx.Response:
        """
        Execute single request to target service.

        Args:
            request: Original request
            path: Path to append to target URL
            body: Request body

        Returns:
            httpx.Response: Response from target service
        """
        # Build target URL
        target_url = f"{self.config.target_url.rstrip('/')}/{path.lstrip('/')}"

        # Prepare headers
        headers = dict(request.headers)

        # Add configured headers
        headers.update(self.config.headers)

        # Remove hop-by-hop headers
        hop_by_hop = {
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
        }
        headers = {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}

        # Update Host header if not preserving
        if not self.config.preserve_host_header:
            from urllib.parse import urlparse

            parsed = urlparse(self.config.target_url)
            headers["host"] = parsed.netloc

        # Execute request
        response = await self.client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=dict(request.query_params),
        )

        return response

    def _get_cache_key(self, method: str, path: str) -> str:
        """
        Generate cache key.

        Args:
            method: HTTP method
            path: Request path

        Returns:
            str: Cache key
        """
        return f"{method}:{path}"

    def _create_response_from_cache(self, entry: CacheEntry) -> httpx.Response:
        """
        Create httpx.Response from cache entry.

        Args:
            entry: Cache entry

        Returns:
            httpx.Response: Response object
        """
        return httpx.Response(
            status_code=200,
            content=entry.data,
            headers={"X-Cache": "HIT"},
        )

    async def close(self) -> None:
        """Close proxy client."""
        await self.client.aclose()
        logger.info(f"Service proxy '{self.config.name}' closed")

    def get_stats(self) -> dict[str, Any]:
        """
        Get proxy statistics.

        Returns:
            dict: Statistics including circuit breaker state, cache hits, etc.
        """
        stats = {
            "name": self.config.name,
            "target_url": self.config.target_url,
        }

        if self.circuit_breaker:
            stats["circuit_breaker"] = {
                "state": self.circuit_breaker.state.value,
                "failure_count": self.circuit_breaker.failure_count,
                "success_count": self.circuit_breaker.success_count,
            }

        if self.config.cache_enabled:
            valid_entries = sum(
                1 for entry in self.cache.values() if not entry.is_expired()
            )
            stats["cache"] = {
                "entries": len(self.cache),
                "valid_entries": valid_entries,
            }

        if self.rate_limiter:
            stats["rate_limiter"] = {
                "requests_in_window": len(self.rate_limiter.requests),
                "max_requests": self.rate_limiter.max_requests,
            }

        return stats

    def reset_circuit_breaker(self) -> None:
        """Manually reset circuit breaker to closed state."""
        if self.circuit_breaker:
            self.circuit_breaker.state = CircuitState.CLOSED
            self.circuit_breaker.failure_count = 0
            self.circuit_breaker.success_count = 0
            self.circuit_breaker.half_open_attempts = 0
            logger.info(f"Circuit breaker reset for proxy '{self.config.name}'")

    def clear_cache(self) -> None:
        """Clear response cache."""
        self.cache.clear()
        logger.info(f"Cache cleared for proxy '{self.config.name}'")
