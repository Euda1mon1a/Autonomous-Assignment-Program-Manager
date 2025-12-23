"""
API Analytics Service for tracking request/response metrics and usage patterns.

This service provides comprehensive analytics for API usage including:
- Request/response metrics collection
- Endpoint usage statistics
- Error rate tracking by endpoint
- Latency percentile calculations
- User activity analytics
- API versioning analytics
- Geographic distribution tracking
- Custom dimension support

Usage:
    from app.analytics.api import get_api_analytics_service

    analytics = get_api_analytics_service()
    await analytics.record_request(
        endpoint="/api/v1/assignments",
        method="GET",
        status_code=200,
        latency_ms=45.2,
        user_id="user-123",
        ip_address="192.168.1.1"
    )
"""

import logging
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, TypedDict

import redis.asyncio as redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# =============================================================================
# Type Definitions
# =============================================================================


class EndpointStats(TypedDict):
    """Statistics for a single endpoint."""

    endpoint: str
    method: str
    total_requests: int
    success_count: int
    error_count: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    requests_per_minute: float
    last_accessed: str


class UserActivityMetrics(TypedDict):
    """User activity analytics."""

    user_id: str
    total_requests: int
    unique_endpoints: int
    avg_latency_ms: float
    error_rate: float
    most_used_endpoint: str
    last_active: str
    first_seen: str


class GeographicDistribution(TypedDict):
    """Geographic distribution of API requests."""

    country: str
    region: str | None
    request_count: int
    unique_users: int
    avg_latency_ms: float
    error_rate: float


class APIVersionStats(TypedDict):
    """API version usage statistics."""

    version: str
    total_requests: int
    unique_users: int
    endpoints: list[str]
    adoption_rate: float
    deprecated: bool


class CustomDimensionStats(TypedDict):
    """Statistics for custom dimensions."""

    dimension_name: str
    dimension_value: str
    request_count: int
    unique_users: int
    avg_latency_ms: float


class LatencyPercentiles(TypedDict):
    """Latency percentile data."""

    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    max: float
    min: float
    avg: float


class ErrorBreakdown(TypedDict):
    """Error breakdown by status code."""

    status_code: int
    count: int
    percentage: float
    endpoints: list[str]


class APIMetrics(TypedDict):
    """Comprehensive API metrics."""

    period_start: str
    period_end: str
    total_requests: int
    total_errors: int
    error_rate: float
    avg_latency_ms: float
    latency_percentiles: LatencyPercentiles
    top_endpoints: list[EndpointStats]
    error_breakdown: list[ErrorBreakdown]
    unique_users: int
    requests_per_minute: float


class RequestRecord(TypedDict, total=False):
    """Individual request record."""

    timestamp: str
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    user_id: str | None
    ip_address: str | None
    user_agent: str | None
    api_version: str | None
    custom_dimensions: dict[str, str] | None


# =============================================================================
# API Analytics Service
# =============================================================================


class APIAnalyticsService:
    """
    Service for collecting and analyzing API request/response metrics.

    This service uses Redis for high-performance metrics collection with:
    - Time-series data storage with automatic expiration
    - Hash-based aggregations for efficient queries
    - Sorted sets for percentile calculations
    - HyperLogLog for unique user tracking
    """

    def __init__(self, redis_client: redis.Redis | None = None):
        """
        Initialize API analytics service.

        Args:
            redis_client: Optional Redis client (will create new one if not provided)
        """
        self.redis = redis_client
        self._settings = get_settings()
        self._retention_days = 30  # Keep metrics for 30 days

        # Key prefixes for different metric types
        self._prefix_requests = "api:metrics:requests"
        self._prefix_endpoints = "api:metrics:endpoints"
        self._prefix_users = "api:metrics:users"
        self._prefix_errors = "api:metrics:errors"
        self._prefix_latency = "api:metrics:latency"
        self._prefix_versions = "api:metrics:versions"
        self._prefix_geo = "api:metrics:geo"
        self._prefix_custom = "api:metrics:custom"

    async def _get_redis(self) -> redis.Redis:
        """Get Redis client, creating one if needed."""
        if self.redis is None:
            self.redis = await redis.from_url(
                self._settings.redis_url_with_password,
                encoding="utf-8",
                decode_responses=True,
            )
        return self.redis

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    # =========================================================================
    # Request Recording
    # =========================================================================

    async def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        api_version: str | None = None,
        custom_dimensions: dict[str, str] | None = None,
    ) -> None:
        """
        Record an API request with all metrics.

        Args:
            endpoint: API endpoint path (e.g., "/api/v1/assignments")
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP status code
            latency_ms: Request latency in milliseconds
            user_id: Optional user ID who made the request
            ip_address: Optional IP address of the client
            user_agent: Optional user agent string
            api_version: Optional API version (e.g., "v1", "v2")
            custom_dimensions: Optional dict of custom dimension key-value pairs

        Raises:
            Exception: If Redis operations fail (logged but not raised)
        """
        try:
            redis_client = await self._get_redis()
            timestamp = datetime.utcnow()
            timestamp_str = timestamp.isoformat()
            hour_key = timestamp.strftime("%Y-%m-%d-%H")
            day_key = timestamp.strftime("%Y-%m-%d")

            # Build pipeline for atomic operations
            pipe = redis_client.pipeline()

            # 1. Record request count
            pipe.incr(f"{self._prefix_requests}:{day_key}:total")

            # 2. Record endpoint stats
            endpoint_key = f"{self._prefix_endpoints}:{day_key}:{method}:{endpoint}"
            pipe.hincrby(endpoint_key, "count", 1)
            pipe.hincrbyfloat(endpoint_key, "total_latency", latency_ms)
            pipe.zadd(
                f"{endpoint_key}:latencies", {str(latency_ms): timestamp.timestamp()}
            )
            pipe.expire(endpoint_key, self._retention_days * 86400)

            # Track success/error
            if 200 <= status_code < 400:
                pipe.hincrby(endpoint_key, "success", 1)
            else:
                pipe.hincrby(endpoint_key, "errors", 1)
                # Record error details
                error_key = f"{self._prefix_errors}:{day_key}:{status_code}"
                pipe.incr(error_key)
                pipe.sadd(f"{error_key}:endpoints", f"{method}:{endpoint}")
                pipe.expire(error_key, self._retention_days * 86400)

            # 3. Record latency in sorted set for percentile calculations
            latency_key = f"{self._prefix_latency}:{hour_key}"
            pipe.zadd(latency_key, {f"{endpoint}:{timestamp_str}": latency_ms})
            pipe.expire(latency_key, self._retention_days * 86400)

            # 4. Record user activity
            if user_id:
                user_key = f"{self._prefix_users}:{day_key}:{user_id}"
                pipe.hincrby(user_key, "count", 1)
                pipe.hincrbyfloat(user_key, "total_latency", latency_ms)
                pipe.sadd(f"{user_key}:endpoints", endpoint)
                pipe.hset(user_key, "last_active", timestamp_str)
                pipe.expire(user_key, self._retention_days * 86400)

                # Track unique users globally
                pipe.pfadd(f"{self._prefix_requests}:{day_key}:unique_users", user_id)

                # Track endpoint-specific unique users
                pipe.pfadd(f"{endpoint_key}:unique_users", user_id)

            # 5. Record API version usage
            if api_version:
                version_key = f"{self._prefix_versions}:{day_key}:{api_version}"
                pipe.incr(version_key)
                pipe.sadd(f"{version_key}:endpoints", endpoint)
                if user_id:
                    pipe.pfadd(f"{version_key}:unique_users", user_id)
                pipe.expire(version_key, self._retention_days * 86400)

            # 6. Record geographic distribution (from IP address)
            if ip_address:
                # Simple country/region extraction (in production, use GeoIP database)
                country, region = self._extract_geo_info(ip_address)
                geo_key = f"{self._prefix_geo}:{day_key}:{country}"
                pipe.incr(geo_key)
                pipe.hincrbyfloat(f"{geo_key}:latency", "total", latency_ms)
                pipe.hincrby(f"{geo_key}:latency", "count", 1)
                if user_id:
                    pipe.pfadd(f"{geo_key}:unique_users", user_id)
                if 200 <= status_code < 400:
                    pipe.hincrby(geo_key, "success", 1)
                else:
                    pipe.hincrby(geo_key, "errors", 1)
                pipe.expire(geo_key, self._retention_days * 86400)

            # 7. Record custom dimensions
            if custom_dimensions:
                for dim_name, dim_value in custom_dimensions.items():
                    custom_key = (
                        f"{self._prefix_custom}:{day_key}:{dim_name}:{dim_value}"
                    )
                    pipe.incr(custom_key)
                    pipe.hincrbyfloat(f"{custom_key}:latency", "total", latency_ms)
                    pipe.hincrby(f"{custom_key}:latency", "count", 1)
                    if user_id:
                        pipe.pfadd(f"{custom_key}:unique_users", user_id)
                    pipe.expire(custom_key, self._retention_days * 86400)

            # Execute pipeline
            await pipe.execute()

        except Exception as e:
            logger.error(f"Error recording API request metrics: {e}", exc_info=True)
            # Don't raise - metrics collection should not break the API

    # =========================================================================
    # Metrics Retrieval
    # =========================================================================

    async def get_endpoint_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        endpoint: str | None = None,
        method: str | None = None,
        limit: int = 20,
    ) -> list[EndpointStats]:
        """
        Get endpoint usage statistics.

        Args:
            start_date: Start of date range (default: 7 days ago)
            end_date: End of date range (default: now)
            endpoint: Optional filter by specific endpoint
            method: Optional filter by HTTP method
            limit: Maximum number of results to return

        Returns:
            List of endpoint statistics ordered by request count
        """
        try:
            redis_client = await self._get_redis()

            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            # Aggregate stats across date range
            endpoint_data: dict[str, dict[str, Any]] = defaultdict(
                lambda: {
                    "count": 0,
                    "success": 0,
                    "errors": 0,
                    "total_latency": 0.0,
                    "latencies": [],
                    "last_accessed": None,
                }
            )

            current = start_date
            while current <= end_date:
                day_key = current.strftime("%Y-%m-%d")

                # Get all endpoint keys for this day
                pattern = f"{self._prefix_endpoints}:{day_key}:*"
                async for key in redis_client.scan_iter(match=pattern, count=100):
                    # Parse key: api:metrics:endpoints:YYYY-MM-DD:METHOD:ENDPOINT
                    parts = key.split(":", 5)
                    if len(parts) != 6:
                        continue

                    key_method = parts[4]
                    key_endpoint = parts[5]

                    # Apply filters
                    if method and key_method != method:
                        continue
                    if endpoint and key_endpoint != endpoint:
                        continue

                    endpoint_id = f"{key_method}:{key_endpoint}"

                    # Get stats from hash
                    data = await redis_client.hgetall(key)
                    if data:
                        endpoint_data[endpoint_id]["count"] += int(data.get("count", 0))
                        endpoint_data[endpoint_id]["success"] += int(
                            data.get("success", 0)
                        )
                        endpoint_data[endpoint_id]["errors"] += int(
                            data.get("errors", 0)
                        )
                        endpoint_data[endpoint_id]["total_latency"] += float(
                            data.get("total_latency", 0.0)
                        )
                        endpoint_data[endpoint_id]["method"] = key_method
                        endpoint_data[endpoint_id]["endpoint"] = key_endpoint

                    # Get latency data
                    latency_key = f"{key}:latencies"
                    latencies = await redis_client.zrange(latency_key, 0, -1)
                    endpoint_data[endpoint_id]["latencies"].extend(
                        [float(lat) for lat in latencies if lat]
                    )

                current += timedelta(days=1)

            # Build result list
            results: list[EndpointStats] = []
            for endpoint_id, data in endpoint_data.items():
                if data["count"] == 0:
                    continue

                latencies = sorted(data["latencies"])
                count = data["count"]

                # Calculate percentiles
                p50 = self._percentile(latencies, 50) if latencies else 0.0
                p95 = self._percentile(latencies, 95) if latencies else 0.0
                p99 = self._percentile(latencies, 99) if latencies else 0.0

                results.append(
                    EndpointStats(
                        endpoint=data["endpoint"],
                        method=data["method"],
                        total_requests=count,
                        success_count=data["success"],
                        error_count=data["errors"],
                        avg_latency_ms=round(data["total_latency"] / count, 2),
                        p50_latency_ms=round(p50, 2),
                        p95_latency_ms=round(p95, 2),
                        p99_latency_ms=round(p99, 2),
                        error_rate=(
                            round((data["errors"] / count) * 100, 2)
                            if count > 0
                            else 0.0
                        ),
                        requests_per_minute=round(
                            count / ((end_date - start_date).total_seconds() / 60), 2
                        ),
                        last_accessed=data.get(
                            "last_accessed", datetime.utcnow().isoformat()
                        ),
                    )
                )

            # Sort by request count and limit
            results.sort(key=lambda x: x["total_requests"], reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Error getting endpoint stats: {e}", exc_info=True)
            return []

    async def get_user_activity(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_id: str | None = None,
        limit: int = 50,
    ) -> list[UserActivityMetrics]:
        """
        Get user activity metrics.

        Args:
            start_date: Start of date range (default: 7 days ago)
            end_date: End of date range (default: now)
            user_id: Optional filter by specific user
            limit: Maximum number of users to return

        Returns:
            List of user activity metrics ordered by request count
        """
        try:
            redis_client = await self._get_redis()

            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            user_data: dict[str, dict[str, Any]] = defaultdict(
                lambda: {
                    "count": 0,
                    "total_latency": 0.0,
                    "endpoints": set(),
                    "errors": 0,
                    "last_active": None,
                    "first_seen": None,
                }
            )

            current = start_date
            while current <= end_date:
                day_key = current.strftime("%Y-%m-%d")

                # Get all user keys for this day
                pattern = f"{self._prefix_users}:{day_key}:*"
                async for key in redis_client.scan_iter(match=pattern, count=100):
                    # Parse key: api:metrics:users:YYYY-MM-DD:USER_ID
                    parts = key.split(":", 4)
                    if len(parts) != 5:
                        continue

                    key_user_id = parts[4].replace(":endpoints", "")

                    # Apply filter
                    if user_id and key_user_id != user_id:
                        continue

                    # Skip endpoint sets
                    if key.endswith(":endpoints"):
                        continue

                    # Get user stats
                    data = await redis_client.hgetall(key)
                    if data:
                        user_data[key_user_id]["count"] += int(data.get("count", 0))
                        user_data[key_user_id]["total_latency"] += float(
                            data.get("total_latency", 0.0)
                        )
                        last_active = data.get("last_active")
                        if last_active:
                            if (
                                not user_data[key_user_id]["last_active"]
                                or last_active > user_data[key_user_id]["last_active"]
                            ):
                                user_data[key_user_id]["last_active"] = last_active
                            if not user_data[key_user_id]["first_seen"]:
                                user_data[key_user_id]["first_seen"] = last_active

                    # Get unique endpoints
                    endpoint_set = await redis_client.smembers(f"{key}:endpoints")
                    if endpoint_set:
                        user_data[key_user_id]["endpoints"].update(endpoint_set)

                current += timedelta(days=1)

            # Build results
            results: list[UserActivityMetrics] = []
            for uid, data in user_data.items():
                if data["count"] == 0:
                    continue

                endpoints_list = list(data["endpoints"])
                most_used = endpoints_list[0] if endpoints_list else "N/A"

                results.append(
                    UserActivityMetrics(
                        user_id=uid,
                        total_requests=data["count"],
                        unique_endpoints=len(data["endpoints"]),
                        avg_latency_ms=round(data["total_latency"] / data["count"], 2),
                        error_rate=(
                            round((data["errors"] / data["count"]) * 100, 2)
                            if data["count"] > 0
                            else 0.0
                        ),
                        most_used_endpoint=most_used,
                        last_active=data["last_active"]
                        or datetime.utcnow().isoformat(),
                        first_seen=data["first_seen"] or datetime.utcnow().isoformat(),
                    )
                )

            # Sort by request count
            results.sort(key=lambda x: x["total_requests"], reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Error getting user activity: {e}", exc_info=True)
            return []

    async def get_geographic_distribution(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[GeographicDistribution]:
        """
        Get geographic distribution of API requests.

        Args:
            start_date: Start of date range (default: 7 days ago)
            end_date: End of date range (default: now)

        Returns:
            List of geographic distribution stats ordered by request count
        """
        try:
            redis_client = await self._get_redis()

            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            geo_data: dict[str, dict[str, Any]] = defaultdict(
                lambda: {
                    "count": 0,
                    "success": 0,
                    "errors": 0,
                    "total_latency": 0.0,
                    "users": 0,
                }
            )

            current = start_date
            while current <= end_date:
                day_key = current.strftime("%Y-%m-%d")

                pattern = f"{self._prefix_geo}:{day_key}:*"
                async for key in redis_client.scan_iter(match=pattern, count=100):
                    # Skip latency and user keys
                    if ":latency" in key or ":unique_users" in key:
                        continue

                    parts = key.split(":", 4)
                    if len(parts) != 5:
                        continue

                    country = parts[4]

                    # Get counts
                    data = await redis_client.hgetall(key)
                    if data:
                        geo_data[country]["success"] += int(data.get("success", 0))
                        geo_data[country]["errors"] += int(data.get("errors", 0))
                        geo_data[country]["count"] = (
                            geo_data[country]["success"] + geo_data[country]["errors"]
                        )

                    # Get latency
                    latency_data = await redis_client.hgetall(f"{key}:latency")
                    if latency_data:
                        geo_data[country]["total_latency"] += float(
                            latency_data.get("total", 0.0)
                        )

                    # Get unique users
                    user_count = await redis_client.pfcount(f"{key}:unique_users")
                    geo_data[country]["users"] = max(
                        geo_data[country]["users"], user_count
                    )

                current += timedelta(days=1)

            # Build results
            results: list[GeographicDistribution] = []
            for country, data in geo_data.items():
                if data["count"] == 0:
                    continue

                results.append(
                    GeographicDistribution(
                        country=country,
                        region=None,  # Would need GeoIP for region
                        request_count=data["count"],
                        unique_users=data["users"],
                        avg_latency_ms=(
                            round(data["total_latency"] / data["count"], 2)
                            if data["count"] > 0
                            else 0.0
                        ),
                        error_rate=(
                            round((data["errors"] / data["count"]) * 100, 2)
                            if data["count"] > 0
                            else 0.0
                        ),
                    )
                )

            results.sort(key=lambda x: x["request_count"], reverse=True)
            return results

        except Exception as e:
            logger.error(f"Error getting geographic distribution: {e}", exc_info=True)
            return []

    async def get_api_version_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[APIVersionStats]:
        """
        Get API version usage statistics.

        Args:
            start_date: Start of date range (default: 7 days ago)
            end_date: End of date range (default: now)

        Returns:
            List of API version statistics
        """
        try:
            redis_client = await self._get_redis()

            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            version_data: dict[str, dict[str, Any]] = defaultdict(
                lambda: {"count": 0, "endpoints": set(), "users": 0}
            )

            current = start_date
            total_requests = 0

            while current <= end_date:
                day_key = current.strftime("%Y-%m-%d")

                # Get total requests for adoption rate
                total_key = f"{self._prefix_requests}:{day_key}:total"
                day_total = await redis_client.get(total_key)
                if day_total:
                    total_requests += int(day_total)

                pattern = f"{self._prefix_versions}:{day_key}:*"
                async for key in redis_client.scan_iter(match=pattern, count=100):
                    # Skip endpoint and user keys
                    if ":endpoints" in key or ":unique_users" in key:
                        continue

                    parts = key.split(":", 4)
                    if len(parts) != 5:
                        continue

                    version = parts[4]

                    # Get count
                    count = await redis_client.get(key)
                    if count:
                        version_data[version]["count"] += int(count)

                    # Get endpoints
                    endpoints = await redis_client.smembers(f"{key}:endpoints")
                    if endpoints:
                        version_data[version]["endpoints"].update(endpoints)

                    # Get unique users
                    users = await redis_client.pfcount(f"{key}:unique_users")
                    version_data[version]["users"] = max(
                        version_data[version]["users"], users
                    )

                current += timedelta(days=1)

            # Build results
            results: list[APIVersionStats] = []
            for version, data in version_data.items():
                if data["count"] == 0:
                    continue

                adoption_rate = (
                    round((data["count"] / total_requests) * 100, 2)
                    if total_requests > 0
                    else 0.0
                )

                results.append(
                    APIVersionStats(
                        version=version,
                        total_requests=data["count"],
                        unique_users=data["users"],
                        endpoints=list(data["endpoints"]),
                        adoption_rate=adoption_rate,
                        deprecated=False,  # Would need to maintain this separately
                    )
                )

            results.sort(key=lambda x: x["total_requests"], reverse=True)
            return results

        except Exception as e:
            logger.error(f"Error getting API version stats: {e}", exc_info=True)
            return []

    async def get_custom_dimension_stats(
        self,
        dimension_name: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 20,
    ) -> list[CustomDimensionStats]:
        """
        Get statistics for a custom dimension.

        Args:
            dimension_name: Name of the custom dimension
            start_date: Start of date range (default: 7 days ago)
            end_date: End of date range (default: now)
            limit: Maximum number of results

        Returns:
            List of statistics for different values of the dimension
        """
        try:
            redis_client = await self._get_redis()

            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            dimension_data: dict[str, dict[str, Any]] = defaultdict(
                lambda: {"count": 0, "total_latency": 0.0, "users": 0}
            )

            current = start_date
            while current <= end_date:
                day_key = current.strftime("%Y-%m-%d")

                pattern = f"{self._prefix_custom}:{day_key}:{dimension_name}:*"
                async for key in redis_client.scan_iter(match=pattern, count=100):
                    # Skip latency and user keys
                    if ":latency" in key or ":unique_users" in key:
                        continue

                    parts = key.split(":", 5)
                    if len(parts) != 6:
                        continue

                    dim_value = parts[5]

                    # Get count
                    count = await redis_client.get(key)
                    if count:
                        dimension_data[dim_value]["count"] += int(count)

                    # Get latency
                    latency_data = await redis_client.hgetall(f"{key}:latency")
                    if latency_data:
                        dimension_data[dim_value]["total_latency"] += float(
                            latency_data.get("total", 0.0)
                        )

                    # Get unique users
                    users = await redis_client.pfcount(f"{key}:unique_users")
                    dimension_data[dim_value]["users"] = max(
                        dimension_data[dim_value]["users"], users
                    )

                current += timedelta(days=1)

            # Build results
            results: list[CustomDimensionStats] = []
            for dim_value, data in dimension_data.items():
                if data["count"] == 0:
                    continue

                results.append(
                    CustomDimensionStats(
                        dimension_name=dimension_name,
                        dimension_value=dim_value,
                        request_count=data["count"],
                        unique_users=data["users"],
                        avg_latency_ms=(
                            round(data["total_latency"] / data["count"], 2)
                            if data["count"] > 0
                            else 0.0
                        ),
                    )
                )

            results.sort(key=lambda x: x["request_count"], reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Error getting custom dimension stats: {e}", exc_info=True)
            return []

    async def get_comprehensive_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> APIMetrics:
        """
        Get comprehensive API metrics for a date range.

        Args:
            start_date: Start of date range (default: 7 days ago)
            end_date: End of date range (default: now)

        Returns:
            Comprehensive API metrics including all analytics
        """
        try:
            redis_client = await self._get_redis()

            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            total_requests = 0
            total_errors = 0
            all_latencies: list[float] = []
            error_codes: dict[int, dict[str, Any]] = defaultdict(
                lambda: {"count": 0, "endpoints": set()}
            )
            unique_users_sets: list[str] = []

            current = start_date
            while current <= end_date:
                day_key = current.strftime("%Y-%m-%d")

                # Get total requests
                total_key = f"{self._prefix_requests}:{day_key}:total"
                day_total = await redis_client.get(total_key)
                if day_total:
                    total_requests += int(day_total)

                # Collect unique users key for pfcount
                unique_users_sets.append(
                    f"{self._prefix_requests}:{day_key}:unique_users"
                )

                # Get error data
                error_pattern = f"{self._prefix_errors}:{day_key}:*"
                async for key in redis_client.scan_iter(match=error_pattern, count=100):
                    if ":endpoints" in key:
                        continue

                    parts = key.split(":", 4)
                    if len(parts) != 5:
                        continue

                    try:
                        status_code = int(parts[4])
                        count = await redis_client.get(key)
                        if count:
                            error_codes[status_code]["count"] += int(count)
                            total_errors += int(count)

                        # Get endpoints for this error
                        endpoints = await redis_client.smembers(f"{key}:endpoints")
                        if endpoints:
                            error_codes[status_code]["endpoints"].update(endpoints)
                    except (ValueError, IndexError):
                        continue

                # Get latency data
                for hour in range(24):
                    hour_key = current.strftime(f"%Y-%m-%d-{hour:02d}")
                    latency_key = f"{self._prefix_latency}:{hour_key}"
                    latencies = await redis_client.zrange(
                        latency_key, 0, -1, withscores=True
                    )
                    all_latencies.extend([score for _, score in latencies])

                current += timedelta(days=1)

            # Calculate latency percentiles
            sorted_latencies = sorted(all_latencies)
            latency_percentiles = LatencyPercentiles(
                p50=round(self._percentile(sorted_latencies, 50), 2),
                p75=round(self._percentile(sorted_latencies, 75), 2),
                p90=round(self._percentile(sorted_latencies, 90), 2),
                p95=round(self._percentile(sorted_latencies, 95), 2),
                p99=round(self._percentile(sorted_latencies, 99), 2),
                max=round(max(sorted_latencies), 2) if sorted_latencies else 0.0,
                min=round(min(sorted_latencies), 2) if sorted_latencies else 0.0,
                avg=(
                    round(statistics.mean(sorted_latencies), 2)
                    if sorted_latencies
                    else 0.0
                ),
            )

            # Get top endpoints
            top_endpoints = await self.get_endpoint_stats(
                start_date=start_date, end_date=end_date, limit=10
            )

            # Build error breakdown
            error_breakdown: list[ErrorBreakdown] = []
            for status_code, data in error_codes.items():
                error_breakdown.append(
                    ErrorBreakdown(
                        status_code=status_code,
                        count=data["count"],
                        percentage=(
                            round((data["count"] / total_errors) * 100, 2)
                            if total_errors > 0
                            else 0.0
                        ),
                        endpoints=list(data["endpoints"]),
                    )
                )
            error_breakdown.sort(key=lambda x: x["count"], reverse=True)

            # Get unique users count
            unique_users = 0
            if unique_users_sets:
                unique_users = await redis_client.pfcount(*unique_users_sets)

            # Calculate requests per minute
            duration_minutes = (end_date - start_date).total_seconds() / 60
            requests_per_minute = (
                round(total_requests / duration_minutes, 2)
                if duration_minutes > 0
                else 0.0
            )

            return APIMetrics(
                period_start=start_date.isoformat(),
                period_end=end_date.isoformat(),
                total_requests=total_requests,
                total_errors=total_errors,
                error_rate=(
                    round((total_errors / total_requests) * 100, 2)
                    if total_requests > 0
                    else 0.0
                ),
                avg_latency_ms=latency_percentiles["avg"],
                latency_percentiles=latency_percentiles,
                top_endpoints=top_endpoints,
                error_breakdown=error_breakdown,
                unique_users=unique_users,
                requests_per_minute=requests_per_minute,
            )

        except Exception as e:
            logger.error(f"Error getting comprehensive metrics: {e}", exc_info=True)
            return APIMetrics(
                period_start=start_date.isoformat() if start_date else "",
                period_end=end_date.isoformat() if end_date else "",
                total_requests=0,
                total_errors=0,
                error_rate=0.0,
                avg_latency_ms=0.0,
                latency_percentiles=LatencyPercentiles(
                    p50=0.0,
                    p75=0.0,
                    p90=0.0,
                    p95=0.0,
                    p99=0.0,
                    max=0.0,
                    min=0.0,
                    avg=0.0,
                ),
                top_endpoints=[],
                error_breakdown=[],
                unique_users=0,
                requests_per_minute=0.0,
            )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _percentile(data: list[float], percentile: float) -> float:
        """
        Calculate percentile of a sorted list.

        Args:
            data: Sorted list of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Value at the given percentile
        """
        if not data:
            return 0.0

        k = (len(data) - 1) * (percentile / 100)
        f = int(k)
        c = k - f

        if f + 1 < len(data):
            return data[f] + (c * (data[f + 1] - data[f]))
        return data[f]

    @staticmethod
    def _extract_geo_info(ip_address: str) -> tuple[str, str | None]:
        """
        Extract country and region from IP address.

        In production, this would use a GeoIP database like MaxMind.
        For now, returns placeholder data.

        Args:
            ip_address: IP address string

        Returns:
            Tuple of (country, region)
        """
        # Placeholder implementation
        # In production, use: import geoip2.database
        if ip_address.startswith("192.168.") or ip_address.startswith("10."):
            return ("PRIVATE", None)
        elif ip_address.startswith("127."):
            return ("LOCALHOST", None)
        else:
            return ("UNKNOWN", None)


# =============================================================================
# Factory Function
# =============================================================================


_service_instance: APIAnalyticsService | None = None


def get_api_analytics_service() -> APIAnalyticsService:
    """
    Get singleton instance of API analytics service.

    Returns:
        APIAnalyticsService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = APIAnalyticsService()
    return _service_instance
