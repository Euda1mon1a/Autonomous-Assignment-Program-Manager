"""
HTTP cache service with Redis backend.

Implements RFC 7234 HTTP caching with:
- Cache-Control directives
- Conditional requests (ETag, Last-Modified)
- Cache storage and retrieval
- Vary header support
- Cache entry expiration

This service integrates with the existing Redis cache infrastructure
and provides HTTP-specific caching semantics.
"""

import logging
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class CacheDirective:
    """
    Cache-Control directive configuration.

    Represents HTTP Cache-Control header directives as defined in RFC 7234.

    Example:
        # Public cache with 5-minute expiration
        directive = CacheDirective(
            public=True,
            max_age=300,
            must_revalidate=True
        )
    """

    # Response directives
    public: bool = False  # Can be cached by any cache
    private: bool = False  # Can only be cached by client
    no_cache: bool = False  # Must revalidate before use
    no_store: bool = False  # Do not cache at all
    no_transform: bool = False  # Do not transform content
    must_revalidate: bool = False  # Must revalidate when stale
    proxy_revalidate: bool = False  # Proxy must revalidate
    max_age: int | None = None  # Max age in seconds
    s_maxage: int | None = None  # Shared cache max age
    immutable: bool = False  # Never changes (non-standard but widely supported)

    # Custom directives
    stale_while_revalidate: int | None = None  # Serve stale while revalidating
    stale_if_error: int | None = None  # Serve stale if error

    def to_header(self) -> str:
        """
        Convert to Cache-Control header value.

        Returns:
            Cache-Control header string

        Example:
            directive = CacheDirective(public=True, max_age=300)
            header = directive.to_header()
            # Returns: "public, max-age=300"
        """
        directives = []

        if self.public:
            directives.append("public")
        if self.private:
            directives.append("private")
        if self.no_cache:
            directives.append("no-cache")
        if self.no_store:
            directives.append("no-store")
        if self.no_transform:
            directives.append("no-transform")
        if self.must_revalidate:
            directives.append("must-revalidate")
        if self.proxy_revalidate:
            directives.append("proxy-revalidate")
        if self.immutable:
            directives.append("immutable")

        if self.max_age is not None:
            directives.append(f"max-age={self.max_age}")
        if self.s_maxage is not None:
            directives.append(f"s-maxage={self.s_maxage}")
        if self.stale_while_revalidate is not None:
            directives.append(f"stale-while-revalidate={self.stale_while_revalidate}")
        if self.stale_if_error is not None:
            directives.append(f"stale-if-error={self.stale_if_error}")

        return ", ".join(directives)

    @classmethod
    def from_header(cls, header_value: str) -> "CacheDirective":
        """
        Parse Cache-Control header value.

        Args:
            header_value: Cache-Control header string

        Returns:
            CacheDirective instance

        Example:
            directive = CacheDirective.from_header("public, max-age=300")
        """
        directive = cls()

        if not header_value:
            return directive

        # Parse directives
        parts = [part.strip() for part in header_value.split(",")]

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key == "max-age":
                    directive.max_age = int(value)
                elif key == "s-maxage":
                    directive.s_maxage = int(value)
                elif key == "stale-while-revalidate":
                    directive.stale_while_revalidate = int(value)
                elif key == "stale-if-error":
                    directive.stale_if_error = int(value)
            else:
                # Boolean directives
                if part == "public":
                    directive.public = True
                elif part == "private":
                    directive.private = True
                elif part == "no-cache":
                    directive.no_cache = True
                elif part == "no-store":
                    directive.no_store = True
                elif part == "no-transform":
                    directive.no_transform = True
                elif part == "must-revalidate":
                    directive.must_revalidate = True
                elif part == "proxy-revalidate":
                    directive.proxy_revalidate = True
                elif part == "immutable":
                    directive.immutable = True

        return directive

    def is_cacheable(self) -> bool:
        """
        Check if response can be cached.

        Returns:
            True if response is cacheable
        """
        # no-store means never cache
        if self.no_store:
            return False

        # Must have public or max_age to be cacheable
        return self.public or self.max_age is not None


@dataclass
class HTTPCacheConfig:
    """
    Configuration for HTTP cache service.

    Example:
        config = HTTPCacheConfig(
            enabled=True,
            default_max_age=300,
            respect_cache_control=True
        )
    """

    enabled: bool = True
    default_max_age: int = 300  # 5 minutes
    max_cache_size_mb: int = 100  # Maximum cache size
    respect_cache_control: bool = True  # Honor Cache-Control headers
    default_public: bool = False  # Default to public caching
    enable_etag: bool = True  # Generate ETags
    enable_last_modified: bool = True  # Track Last-Modified
    redis_key_prefix: str = "http_cache"
    redis_db: int = 0


@dataclass
class CachedResponse:
    """
    Cached HTTP response with metadata.

    Stores response data along with caching metadata for
    conditional request handling and cache validation.
    """

    # Response data
    status_code: int
    headers: dict[str, str]
    body: bytes
    content_type: str

    # Cache metadata
    cached_at: float = field(default_factory=time.time)
    etag: str | None = None
    last_modified: datetime | None = None
    max_age: int | None = None
    vary: list[str] | None = None

    # Computed properties
    @property
    def age(self) -> int:
        """
        Get age of cached response in seconds.

        Returns:
            Age in seconds
        """
        return int(time.time() - self.cached_at)

    @property
    def is_stale(self) -> bool:
        """
        Check if response is stale.

        Returns:
            True if past max_age
        """
        if self.max_age is None:
            return False
        return self.age > self.max_age

    @property
    def remaining_ttl(self) -> int:
        """
        Get remaining time-to-live.

        Returns:
            Remaining TTL in seconds (0 if stale)
        """
        if self.max_age is None:
            return 0
        remaining = self.max_age - self.age
        return max(0, remaining)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for storage.

        Returns:
            Dictionary representation
        """
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body,
            "content_type": self.content_type,
            "cached_at": self.cached_at,
            "etag": self.etag,
            "last_modified": (
                self.last_modified.isoformat() if self.last_modified else None
            ),
            "max_age": self.max_age,
            "vary": self.vary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CachedResponse":
        """
        Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            CachedResponse instance
        """
        # Parse last_modified
        last_modified = None
        if data.get("last_modified"):
            last_modified = datetime.fromisoformat(data["last_modified"])

        return cls(
            status_code=data["status_code"],
            headers=data["headers"],
            body=data["body"],
            content_type=data["content_type"],
            cached_at=data["cached_at"],
            etag=data.get("etag"),
            last_modified=last_modified,
            max_age=data.get("max_age"),
            vary=data.get("vary"),
        )


class HTTPCache:
    """
    HTTP cache service with Redis backend.

    Provides HTTP-compliant caching with support for:
    - Cache-Control directives
    - ETag validation
    - Last-Modified validation
    - Vary header support
    - Conditional requests

    Example:
        cache = HTTPCache()

        # Store response
        await cache.store(
            key="/api/users",
            response=cached_response,
            max_age=300
        )

        # Retrieve response
        cached = await cache.get("/api/users")

        # Check if modified
        is_modified = await cache.is_modified(
            key="/api/users",
            etag=request_etag,
            if_modified_since=request_date
        )
    """

    def __init__(self, config: HTTPCacheConfig | None = None):
        """
        Initialize HTTP cache service.

        Args:
            config: Cache configuration
        """
        self.config = config or HTTPCacheConfig()
        self._redis: redis.Redis | None = None
        self._settings = get_settings()

    async def _get_redis(self) -> redis.Redis:
        """
        Get or create Redis connection.

        Returns:
            Redis client instance
        """
        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(redis_url, decode_responses=False)

        return self._redis

    def _make_cache_key(
        self, key: str, vary_values: dict[str, str] | None = None
    ) -> str:
        """
        Generate Redis cache key.

        Args:
            key: Base cache key (usually request path)
            vary_values: Values for Vary header fields

        Returns:
            Full Redis cache key

        Example:
            cache_key = self._make_cache_key(
                "/api/users",
                vary_values={"Accept": "application/json"}
            )
        """
        parts = [self.config.redis_key_prefix, key]

        # Add vary values to key if present
        if vary_values:
            vary_str = ":".join(f"{k}={v}" for k, v in sorted(vary_values.items()))
            parts.append(vary_str)

        return ":".join(parts)

    async def get(
        self,
        key: str,
        vary_values: dict[str, str] | None = None,
    ) -> CachedResponse | None:
        """
        Get cached response.

        Args:
            key: Cache key
            vary_values: Vary header values for cache key

        Returns:
            Cached response or None if not found/stale

        Example:
            cached = await cache.get(
                "/api/users",
                vary_values={"Accept": "application/json"}
            )
        """
        if not self.config.enabled:
            return None

        try:
            redis_client = await self._get_redis()
            cache_key = self._make_cache_key(key, vary_values)

            # Get from Redis
            data = await redis_client.get(cache_key)
            if data is None:
                logger.debug(f"Cache miss: {cache_key}")
                return None

            # Deserialize
            cached_dict = pickle.loads(data)
            cached_response = CachedResponse.from_dict(cached_dict)

            # Check if stale
            if cached_response.is_stale:
                logger.debug(f"Cache stale: {cache_key}")
                await self.delete(key, vary_values)
                return None

            logger.debug(f"Cache hit: {cache_key} (age={cached_response.age}s)")
            return cached_response

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def store(
        self,
        key: str,
        response: CachedResponse,
        max_age: int | None = None,
        vary_values: dict[str, str] | None = None,
    ) -> bool:
        """
        Store response in cache.

        Args:
            key: Cache key
            response: Response to cache
            max_age: Cache TTL in seconds
            vary_values: Vary header values

        Returns:
            True if stored successfully

        Example:
            await cache.store(
                "/api/users",
                cached_response,
                max_age=300
            )
        """
        if not self.config.enabled:
            return False

        try:
            # Update max_age
            max_age = max_age or self.config.default_max_age
            response.max_age = max_age

            redis_client = await self._get_redis()
            cache_key = self._make_cache_key(key, vary_values)

            # Serialize
            cached_dict = response.to_dict()
            data = pickle.dumps(cached_dict)

            # Store with TTL
            await redis_client.setex(cache_key, max_age, data)

            logger.debug(f"Cache stored: {cache_key} (ttl={max_age}s)")
            return True

        except Exception as e:
            logger.error(f"Cache store error for key {key}: {e}")
            return False

    async def delete(
        self,
        key: str,
        vary_values: dict[str, str] | None = None,
    ) -> bool:
        """
        Delete cached response.

        Args:
            key: Cache key
            vary_values: Vary header values

        Returns:
            True if deleted

        Example:
            await cache.delete("/api/users")
        """
        try:
            redis_client = await self._get_redis()
            cache_key = self._make_cache_key(key, vary_values)

            deleted = await redis_client.delete(cache_key)
            logger.debug(f"Cache deleted: {cache_key}")
            return deleted > 0

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def is_modified(
        self,
        key: str,
        etag: str | None = None,
        if_modified_since: datetime | None = None,
        vary_values: dict[str, str] | None = None,
    ) -> bool:
        """
        Check if resource has been modified.

        Used for conditional requests (If-None-Match, If-Modified-Since).

        Args:
            key: Cache key
            etag: ETag from If-None-Match header
            if_modified_since: Date from If-Modified-Since header
            vary_values: Vary header values

        Returns:
            True if resource has been modified, False if not modified (304)

        Example:
            is_modified = await cache.is_modified(
                "/api/users",
                etag='"abc123"',
                if_modified_since=datetime(2024, 1, 1)
            )
            if not is_modified:
                # Return 304 Not Modified
                return Response(status_code=304)
        """
        cached = await self.get(key, vary_values)

        if cached is None:
            # No cached version, assume modified
            return True

        # Check ETag (If-None-Match)
        if etag and cached.etag:
            from app.caching.etag import ETagGenerator

            # Parse If-None-Match (can be comma-separated list)
            etag_list = ETagGenerator.parse_if_none_match(etag)

            # If any ETag matches, not modified
            if ETagGenerator.matches_any(cached.etag, etag_list):
                return False

        # Check Last-Modified (If-Modified-Since)
        if if_modified_since and cached.last_modified:
            # Round to seconds (HTTP dates don't include milliseconds)
            cached_timestamp = int(cached.last_modified.timestamp())
            request_timestamp = int(if_modified_since.timestamp())

            if cached_timestamp <= request_timestamp:
                return False

        # If we have either condition but reached here, it's modified
        if etag or if_modified_since:
            return True

        # No conditions provided, assume modified
        return True

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "http_cache:/api/users/*")

        Returns:
            Number of entries invalidated

        Example:
            # Invalidate all user-related caches
            count = await cache.invalidate_pattern("/api/users/*")
        """
        try:
            redis_client = await self._get_redis()

            # Build full pattern
            full_pattern = f"{self.config.redis_key_prefix}:{pattern}"

            # Find matching keys
            keys = []
            async for key in redis_client.scan_iter(match=full_pattern):
                keys.append(key)

            # Delete keys
            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching {pattern}")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0

    async def clear(self) -> int:
        """
        Clear all HTTP cache entries.

        Returns:
            Number of entries cleared

        Example:
            count = await cache.clear()
        """
        return await self.invalidate_pattern("*")
