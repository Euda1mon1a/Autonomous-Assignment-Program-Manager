"""
HTTP caching middleware for FastAPI.

Implements automatic HTTP caching with:
- Cache-Control header generation
- ETag generation and validation
- Last-Modified tracking
- Conditional request handling (304 Not Modified)
- Vary header support
- Automatic cache invalidation on mutations

This middleware intercepts requests and responses to:
1. Check cache for GET/HEAD requests
2. Return 304 Not Modified for conditional requests
3. Store successful GET responses in cache
4. Invalidate cache on POST/PUT/PATCH/DELETE requests
5. Add appropriate Cache-Control headers

Example:
    from fastapi import FastAPI
    from app.caching.middleware import HTTPCacheMiddleware

    app = FastAPI()
    app.add_middleware(HTTPCacheMiddleware)
"""

import logging
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.caching.etag import ETagGenerator
from app.caching.http_cache import (
    CacheDirective,
    CachedResponse,
    HTTPCache,
    HTTPCacheConfig,
)
from app.caching.invalidation import CacheInvalidator, InvalidationReason

logger = logging.getLogger(__name__)


class HTTPCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic HTTP response caching.

    Handles:
    - GET request caching
    - Conditional requests (If-None-Match, If-Modified-Since)
    - Cache-Control header generation
    - ETag generation
    - Automatic cache invalidation

    Example:
        app.add_middleware(
            HTTPCacheMiddleware,
            default_max_age=300,
            enable_etag=True,
            cache_methods=["GET", "HEAD"]
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        config: HTTPCacheConfig | None = None,
        default_max_age: int = 300,
        enable_etag: bool = True,
        enable_last_modified: bool = True,
        cache_methods: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        vary_headers: list[str] | None = None,
    ):
        """
        Initialize HTTP cache middleware.

        Args:
            app: FastAPI application
            config: Cache configuration
            default_max_age: Default cache TTL in seconds
            enable_etag: Generate ETags for responses
            enable_last_modified: Track Last-Modified timestamps
            cache_methods: HTTP methods to cache (default: ["GET", "HEAD"])
            exclude_paths: Paths to exclude from caching
            vary_headers: Headers to include in Vary (e.g., ["Accept", "Accept-Language"])
        """
        super().__init__(app)

        self.config = config or HTTPCacheConfig(default_max_age=default_max_age)
        self.http_cache = HTTPCache(self.config)
        self.invalidator = CacheInvalidator(self.http_cache)
        self.etag_generator = ETagGenerator()

        self.enable_etag = enable_etag
        self.enable_last_modified = enable_last_modified
        self.cache_methods = cache_methods or ["GET", "HEAD"]
        self.exclude_paths = exclude_paths or []
        self.vary_headers = vary_headers or ["Accept-Encoding"]

        # Methods that trigger cache invalidation
        self.mutation_methods = ["POST", "PUT", "PATCH", "DELETE"]

        logger.info(
            f"HTTPCacheMiddleware initialized: "
            f"max_age={default_max_age}s, "
            f"etag={enable_etag}, "
            f"methods={self.cache_methods}"
        )

    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle caching.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response (from cache or upstream)
        """
        # Skip if caching disabled
        if not self.config.enabled:
            return await call_next(request)

        # Skip excluded paths
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Handle cacheable methods (GET, HEAD)
        if request.method in self.cache_methods:
            return await self._handle_cacheable_request(request, call_next)

        # Handle mutation methods (POST, PUT, PATCH, DELETE)
        if request.method in self.mutation_methods:
            return await self._handle_mutation_request(request, call_next)

        # Other methods - pass through
        return await call_next(request)

    async def _handle_cacheable_request(self, request: Request, call_next):
        """
        Handle cacheable request (GET, HEAD).

        Checks cache and handles conditional requests.

        Args:
            request: HTTP request
            call_next: Next middleware

        Returns:
            Cached or fresh response
        """
        cache_key = self._make_cache_key(request)
        vary_values = self._get_vary_values(request)

        # Check for conditional request headers
        if_none_match = request.headers.get("If-None-Match")
        if_modified_since_header = request.headers.get("If-Modified-Since")
        if_modified_since = None

        if if_modified_since_header:
            try:
                if_modified_since = datetime.strptime(
                    if_modified_since_header, "%a, %d %b %Y %H:%M:%S GMT"
                )
            except ValueError:
                logger.debug(
                    f"Invalid If-Modified-Since header: {if_modified_since_header}"
                )

        # Check if resource has been modified
        if if_none_match or if_modified_since:
            is_modified = await self.http_cache.is_modified(
                key=cache_key,
                etag=if_none_match,
                if_modified_since=if_modified_since,
                vary_values=vary_values,
            )

            if not is_modified:
                # Return 304 Not Modified
                logger.debug(f"Returning 304 Not Modified for {cache_key}")
                return Response(status_code=304)

        # Try to get from cache
        cached = await self.http_cache.get(cache_key, vary_values)

        if cached:
            logger.debug(f"Serving from cache: {cache_key}")
            return self._create_response_from_cache(cached)

        # Cache miss - get fresh response
        response = await call_next(request)

        # Cache successful responses
        if response.status_code == 200:
            await self._cache_response(request, response, cache_key, vary_values)

        return response

    async def _handle_mutation_request(self, request: Request, call_next):
        """
        Handle mutation request (POST, PUT, PATCH, DELETE).

        Invalidates related cache entries after successful mutation.

        Args:
            request: HTTP request
            call_next: Next middleware

        Returns:
            Response from upstream
        """
        # Process request
        response = await call_next(request)

        # Invalidate cache on successful mutations
        if 200 <= response.status_code < 300:
            await self._invalidate_for_mutation(request)

        return response

    async def _cache_response(
        self,
        request: Request,
        response: Response,
        cache_key: str,
        vary_values: dict[str, str] | None,
    ) -> None:
        """
        Cache response if cacheable.

        Args:
            request: HTTP request
            response: HTTP response
            cache_key: Cache key
            vary_values: Vary header values
        """
        # Only cache if response has body
        if not hasattr(response, "body") or not response.body:
            return

        # Check if response is cacheable
        cache_control = response.headers.get("Cache-Control")
        if cache_control:
            directive = CacheDirective.from_header(cache_control)
            if not directive.is_cacheable():
                logger.debug(f"Response not cacheable: {cache_control}")
                return

        # Generate ETag if enabled
        etag = None
        if self.enable_etag:
            etag = self.etag_generator.generate(response.body)
            response.headers["ETag"] = etag

        # Add Last-Modified if enabled
        last_modified = None
        if self.enable_last_modified:
            last_modified = datetime.utcnow()
            response.headers["Last-Modified"] = last_modified.strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

        # Add Vary header
        if self.vary_headers:
            existing_vary = response.headers.get("Vary", "")
            vary_set = set(existing_vary.split(", ")) if existing_vary else set()
            vary_set.update(self.vary_headers)
            response.headers["Vary"] = ", ".join(sorted(vary_set))

        # Add Cache-Control if not present
        if not cache_control:
            directive = CacheDirective(
                public=self.config.default_public,
                max_age=self.config.default_max_age,
            )
            response.headers["Cache-Control"] = directive.to_header()

        # Create cached response
        cached_response = CachedResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.body,
            content_type=response.headers.get("Content-Type", "application/json"),
            etag=etag,
            last_modified=last_modified,
            max_age=self.config.default_max_age,
            vary=self.vary_headers,
        )

        # Store in cache
        await self.http_cache.store(
            key=cache_key,
            response=cached_response,
            max_age=self.config.default_max_age,
            vary_values=vary_values,
        )

    def _create_response_from_cache(self, cached: CachedResponse) -> Response:
        """
        Create FastAPI Response from cached response.

        Args:
            cached: Cached response

        Returns:
            Response object
        """
        # Create response with cached data
        response = Response(
            content=cached.body,
            status_code=cached.status_code,
            headers=dict(cached.headers),
        )

        # Add Age header (RFC 7234)
        response.headers["Age"] = str(cached.age)

        # Add X-Cache header for debugging
        response.headers["X-Cache"] = "HIT"

        return response

    async def _invalidate_for_mutation(self, request: Request) -> None:
        """
        Invalidate cache entries after mutation.

        Args:
            request: Mutation request
        """
        # Extract resource from path
        path = request.url.path
        resource = self._extract_resource(path)

        if not resource:
            logger.debug(f"Could not extract resource from path: {path}")
            return

        # Determine invalidation reason
        reason_map = {
            "POST": InvalidationReason.CREATE,
            "PUT": InvalidationReason.UPDATE,
            "PATCH": InvalidationReason.UPDATE,
            "DELETE": InvalidationReason.DELETE,
        }
        reason = reason_map.get(request.method, InvalidationReason.MANUAL)

        # Extract resource ID if present
        resource_id = self._extract_resource_id(path, resource)

        # Invalidate
        await self.invalidator.invalidate_resource(
            resource=resource,
            resource_id=resource_id,
            reason=reason,
            cascade=True,  # Cascade to related resources
        )

        logger.debug(
            f"Invalidated cache for {request.method} {path}: "
            f"resource={resource} id={resource_id}"
        )

    def _make_cache_key(self, request: Request) -> str:
        """
        Generate cache key from request.

        Args:
            request: HTTP request

        Returns:
            Cache key
        """
        # Use path + query string
        key = request.url.path

        if request.url.query:
            key = f"{key}?{request.url.query}"

        return key

    def _get_vary_values(self, request: Request) -> dict[str, str] | None:
        """
        Get values for Vary headers.

        Args:
            request: HTTP request

        Returns:
            Dictionary of vary header values
        """
        if not self.vary_headers:
            return None

        vary_values = {}

        for header in self.vary_headers:
            value = request.headers.get(header)
            if value:
                vary_values[header] = value

        return vary_values if vary_values else None

    def _is_excluded_path(self, path: str) -> bool:
        """
        Check if path should be excluded from caching.

        Args:
            path: Request path

        Returns:
            True if excluded
        """
        for exclude_pattern in self.exclude_paths:
            # Simple prefix matching
            if path.startswith(exclude_pattern):
                return True

        return False

    def _extract_resource(self, path: str) -> str | None:
        """
        Extract resource name from path.

        Args:
            path: Request path (e.g., "/api/users/123")

        Returns:
            Resource name (e.g., "users")
        """
        # Remove leading slash and split
        parts = path.lstrip("/").split("/")

        # Expect format: /api/{resource}/{id}
        if len(parts) >= 2 and parts[0] == "api":
            return parts[1]

        return None

    def _extract_resource_id(self, path: str, resource: str) -> str | None:
        """
        Extract resource ID from path.

        Args:
            path: Request path
            resource: Resource name

        Returns:
            Resource ID if present
        """
        # Remove leading slash and split
        parts = path.lstrip("/").split("/")

        # Find resource index
        try:
            resource_index = parts.index(resource)

            # ID should be next part
            if len(parts) > resource_index + 1:
                return parts[resource_index + 1]

        except ValueError:
            pass

        return None

    def get_stats(self) -> dict:
        """
        Get caching statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "config": {
                "enabled": self.config.enabled,
                "default_max_age": self.config.default_max_age,
                "enable_etag": self.enable_etag,
                "cache_methods": self.cache_methods,
            },
            "invalidation": self.invalidator.get_stats(),
        }
