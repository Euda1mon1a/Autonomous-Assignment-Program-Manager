"""
Shadow Traffic Manager for request duplication and comparison.

Provides comprehensive shadow traffic capabilities including:
- Request duplication to shadow services
- Response comparison with diff detection
- Configurable sampling rates
- Shadow service health monitoring
- Performance comparison metrics
- Traffic filtering rules
- Alerting on significant diffs
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)


class DiffSeverity(str, Enum):
    """Severity level for response differences."""

    NONE = "none"  # No differences
    LOW = "low"  # Minor differences (timestamps, IDs, etc.)
    MEDIUM = "medium"  # Moderate differences (data variations)
    HIGH = "high"  # Significant differences (different results)
    CRITICAL = "critical"  # Critical differences (errors, failures)


@dataclass
class ShadowConfig:
    """
    Configuration for shadow traffic management.

    Attributes:
        enabled: Whether shadow traffic is enabled
        shadow_url: Base URL of shadow service
        sampling_rate: Percentage of requests to shadow (0.0 to 1.0)
        timeout: Timeout for shadow requests in seconds
        max_concurrent: Maximum concurrent shadow requests
        verify_ssl: Whether to verify SSL certificates
        alert_on_diff: Whether to alert on response differences
        diff_threshold: Severity threshold for alerting
        retry_on_failure: Whether to retry failed shadow requests
        max_retries: Maximum number of retries
        include_headers: Whether to include original headers
        exclude_headers: List of headers to exclude from duplication
        health_check_interval: Interval for health checks in seconds
        metrics_retention_hours: How long to retain metrics (hours)
    """

    enabled: bool = False
    shadow_url: str = ""
    sampling_rate: float = 0.1  # 10% of requests
    timeout: float = 10.0
    max_concurrent: int = 10
    verify_ssl: bool = True
    alert_on_diff: bool = True
    diff_threshold: DiffSeverity = DiffSeverity.MEDIUM
    retry_on_failure: bool = False
    max_retries: int = 2
    include_headers: bool = True
    exclude_headers: list[str] = field(
        default_factory=lambda: ["authorization", "cookie", "set-cookie"]
    )
    health_check_interval: int = 60  # 1 minute
    metrics_retention_hours: int = 24


@dataclass
class ShadowTrafficFilter:
    """
    Filtering rules for shadow traffic.

    Attributes:
        include_methods: HTTP methods to include (empty = all)
        exclude_methods: HTTP methods to exclude
        include_paths: Path patterns to include (regex)
        exclude_paths: Path patterns to exclude (regex)
        include_users: User IDs to include (empty = all)
        exclude_users: User IDs to exclude
        min_request_size: Minimum request size in bytes
        max_request_size: Maximum request size in bytes
        custom_filter: Custom filter function
    """

    include_methods: list[str] = field(default_factory=list)
    exclude_methods: list[str] = field(default_factory=lambda: ["HEAD", "OPTIONS"])
    include_paths: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)
    include_users: list[str] = field(default_factory=list)
    exclude_users: list[str] = field(default_factory=list)
    min_request_size: int = 0
    max_request_size: int = 10_485_760  # 10 MB
    custom_filter: Callable[[dict[str, Any]], bool] | None = None


@dataclass
class ResponseComparison:
    """
    Comparison result between primary and shadow responses.

    Attributes:
        request_id: Unique request identifier
        timestamp: When comparison was performed
        primary_status: HTTP status from primary service
        shadow_status: HTTP status from shadow service
        primary_response_time: Response time from primary (ms)
        shadow_response_time: Response time from shadow (ms)
        status_match: Whether status codes match
        body_match: Whether response bodies match
        headers_match: Whether headers match (selected)
        diff_severity: Severity of differences found
        diff_details: Detailed diff information
        primary_error: Error from primary service (if any)
        shadow_error: Error from shadow service (if any)
    """

    request_id: str
    timestamp: datetime
    primary_status: int | None = None
    shadow_status: int | None = None
    primary_response_time: float = 0.0
    shadow_response_time: float = 0.0
    status_match: bool = False
    body_match: bool = False
    headers_match: bool = False
    diff_severity: DiffSeverity = DiffSeverity.NONE
    diff_details: dict[str, Any] = field(default_factory=dict)
    primary_error: str | None = None
    shadow_error: str | None = None


@dataclass
class DiffReport:
    """
    Detailed diff report for alerting.

    Attributes:
        comparison: The response comparison
        request_method: HTTP method
        request_path: Request path
        request_body: Request body (truncated)
        diff_summary: Human-readable diff summary
        recommendation: Recommended action
    """

    comparison: ResponseComparison
    request_method: str
    request_path: str
    request_body: str | None = None
    diff_summary: str = ""
    recommendation: str = ""


@dataclass
class ShadowHealthMetrics:
    """
    Health metrics for shadow service.

    Attributes:
        status: Health status (healthy, degraded, unhealthy)
        last_check: Last health check timestamp
        success_rate: Success rate (0.0 to 1.0)
        avg_response_time: Average response time in ms
        error_count: Number of errors in last period
        timeout_count: Number of timeouts in last period
        total_requests: Total shadow requests sent
    """

    status: str = "unknown"
    last_check: datetime | None = None
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    error_count: int = 0
    timeout_count: int = 0
    total_requests: int = 0


@dataclass
class ShadowPerformanceMetrics:
    """
    Performance comparison metrics.

    Attributes:
        primary_avg_response_time: Average primary response time (ms)
        shadow_avg_response_time: Average shadow response time (ms)
        response_time_ratio: Shadow/primary response time ratio
        primary_error_rate: Primary service error rate
        shadow_error_rate: Shadow service error rate
        match_rate: Percentage of matching responses
        total_comparisons: Total comparisons performed
    """

    primary_avg_response_time: float = 0.0
    shadow_avg_response_time: float = 0.0
    response_time_ratio: float = 0.0
    primary_error_rate: float = 0.0
    shadow_error_rate: float = 0.0
    match_rate: float = 0.0
    total_comparisons: int = 0


@dataclass
class ShadowTrafficStats:
    """
    Overall shadow traffic statistics.

    Attributes:
        total_requests: Total requests processed
        sampled_requests: Requests sent to shadow
        sampling_rate_actual: Actual sampling rate achieved
        successful_shadows: Successful shadow requests
        failed_shadows: Failed shadow requests
        skipped_requests: Requests skipped by filters
        diffs_detected: Number of diffs detected
        diffs_by_severity: Diffs grouped by severity
        avg_shadow_overhead: Average overhead of shadow requests (ms)
    """

    total_requests: int = 0
    sampled_requests: int = 0
    sampling_rate_actual: float = 0.0
    successful_shadows: int = 0
    failed_shadows: int = 0
    skipped_requests: int = 0
    diffs_detected: int = 0
    diffs_by_severity: dict[str, int] = field(default_factory=dict)
    avg_shadow_overhead: float = 0.0


class ShadowTrafficManager:
    """
    Manages shadow traffic routing and comparison.

    This manager handles:
    1. Request duplication to shadow service
    2. Response comparison and diff detection
    3. Sampling rate enforcement
    4. Shadow service health monitoring
    5. Performance metrics collection
    6. Traffic filtering
    7. Alerting on significant diffs

    Example:
        ```python
        from app.shadow import ShadowConfig, ShadowTrafficManager

        config = ShadowConfig(
            enabled=True,
            shadow_url="https://shadow.example.com",
            sampling_rate=0.1,  # 10% of traffic
        )

        manager = ShadowTrafficManager(config)

        # Duplicate a request
        await manager.duplicate_request(
            method="GET",
            path="/api/schedules",
            headers={"Authorization": "Bearer token"},
            body=None,
            user_id="user123",
            primary_response={
                "status": 200,
                "body": {"schedules": []},
                "headers": {"content-type": "application/json"},
            },
            primary_response_time=45.2,
        )

        # Get metrics
        metrics = manager.get_performance_metrics()
        health = manager.get_health_metrics()
        ```
    """

    def __init__(
        self,
        config: ShadowConfig,
        traffic_filter: ShadowTrafficFilter | None = None,
        alert_callback: Callable[[DiffReport], None] | None = None,
    ) -> None:
        """
        Initialize shadow traffic manager.

        Args:
            config: Shadow traffic configuration
            traffic_filter: Optional traffic filtering rules
            alert_callback: Optional callback for diff alerts
        """
        self.config = config
        self.filter = traffic_filter or ShadowTrafficFilter()
        self.alert_callback = alert_callback

        # HTTP client for shadow requests
        self._client: httpx.AsyncClient | None = None

        # Metrics storage
        self._comparisons: list[ResponseComparison] = []
        self._stats = ShadowTrafficStats()
        self._health = ShadowHealthMetrics()

        # Response time tracking
        self._shadow_response_times: list[float] = []
        self._primary_response_times: list[float] = []

        # Concurrency control
        self._semaphore = asyncio.Semaphore(config.max_concurrent)

        # Last health check
        self._last_health_check: datetime | None = None

        logger.info(
            f"Shadow traffic manager initialized: "
            f"enabled={config.enabled}, "
            f"shadow_url={config.shadow_url}, "
            f"sampling_rate={config.sampling_rate}"
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client for shadow requests.

        Returns:
            Async HTTP client instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                verify=self.config.verify_ssl,
                timeout=self.config.timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def should_sample(self) -> bool:
        """
        Determine if request should be sampled based on sampling rate.

        Returns:
            True if request should be sent to shadow service
        """
        if not self.config.enabled:
            return False

        return random.random() < self.config.sampling_rate

    def should_filter(
        self,
        method: str,
        path: str,
        body: bytes | None,
        user_id: str | None = None,
    ) -> bool:
        """
        Determine if request should be filtered (excluded).

        Args:
            method: HTTP method
            path: Request path
            body: Request body
            user_id: Optional user ID

        Returns:
            True if request should be filtered (not sent to shadow)
        """
        # Check method filters
        if self.filter.exclude_methods and method in self.filter.exclude_methods:
            return True

        if self.filter.include_methods and method not in self.filter.include_methods:
            return True

            # Check path filters (simple substring matching for now)
        if self.filter.exclude_paths:
            for pattern in self.filter.exclude_paths:
                if pattern in path:
                    return True

        if self.filter.include_paths:
            matched = False
            for pattern in self.filter.include_paths:
                if pattern in path:
                    matched = True
                    break
            if not matched:
                return True

                # Check user filters
        if user_id:
            if self.filter.exclude_users and user_id in self.filter.exclude_users:
                return True

            if self.filter.include_users and user_id not in self.filter.include_users:
                return True

                # Check request size
        if body:
            body_size = len(body)
            if body_size < self.filter.min_request_size:
                return True
            if body_size > self.filter.max_request_size:
                return True

                # Custom filter
        if self.filter.custom_filter:
            filter_data = {
                "method": method,
                "path": path,
                "body_size": len(body) if body else 0,
                "user_id": user_id,
            }
            if not self.filter.custom_filter(filter_data):
                return True

        return False

    def _generate_request_id(
        self,
        method: str,
        path: str,
        body: bytes | None,
    ) -> str:
        """
        Generate unique request ID for tracking.

        Args:
            method: HTTP method
            path: Request path
            body: Request body

        Returns:
            Unique request ID
        """
        timestamp = datetime.utcnow().isoformat()
        data = f"{method}:{path}:{timestamp}"
        if body:
            data += f":{hashlib.md5(body).hexdigest()}"

        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _prepare_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """
        Prepare headers for shadow request.

        Args:
            headers: Original request headers

        Returns:
            Filtered headers for shadow request
        """
        if not self.config.include_headers:
            return {}

            # Filter out excluded headers
        filtered_headers = {
            k: v
            for k, v in headers.items()
            if k.lower() not in [h.lower() for h in self.config.exclude_headers]
        }

        # Add shadow traffic identifier
        filtered_headers["X-Shadow-Traffic"] = "true"

        return filtered_headers

    async def _send_shadow_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: bytes | None,
        request_id: str,
    ) -> tuple[httpx.Response | None, float, str | None]:
        """
        Send request to shadow service.

        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            body: Request body
            request_id: Unique request ID

        Returns:
            Tuple of (response, response_time_ms, error)
        """
        url = urljoin(self.config.shadow_url, path)
        start_time = time.time()
        error: str | None = None

        try:
            client = await self._get_client()

            # Send request
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                timeout=self.config.timeout,
            )

            response_time = (time.time() - start_time) * 1000

            logger.debug(
                f"Shadow request completed: "
                f"request_id={request_id}, "
                f"status={response.status_code}, "
                f"time={response_time:.2f}ms"
            )

            return response, response_time, None

        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            error = f"Timeout after {self.config.timeout}s"
            logger.warning(f"Shadow request timeout: request_id={request_id}")
            self._health.timeout_count += 1
            return None, response_time, error

        except httpx.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            error = f"HTTP error: {str(e)}"
            logger.error(f"Shadow request failed: request_id={request_id}, error={e}")
            self._health.error_count += 1
            return None, response_time, error

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            error = f"Unexpected error: {str(e)}"
            logger.error(
                f"Shadow request unexpected error: request_id={request_id}, error={e}",
                exc_info=True,
            )
            self._health.error_count += 1
            return None, response_time, error

    def _compare_responses(
        self,
        request_id: str,
        primary_status: int,
        primary_body: Any,
        primary_headers: dict[str, str],
        primary_response_time: float,
        shadow_response: httpx.Response | None,
        shadow_response_time: float,
        shadow_error: str | None,
    ) -> ResponseComparison:
        """
        Compare primary and shadow responses.

        Args:
            request_id: Unique request ID
            primary_status: Primary response status code
            primary_body: Primary response body
            primary_headers: Primary response headers
            primary_response_time: Primary response time (ms)
            shadow_response: Shadow response object
            shadow_response_time: Shadow response time (ms)
            shadow_error: Shadow error message (if any)

        Returns:
            ResponseComparison with detailed comparison results
        """
        comparison = ResponseComparison(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            primary_status=primary_status,
            primary_response_time=primary_response_time,
            shadow_response_time=shadow_response_time,
            shadow_error=shadow_error,
        )

        # If shadow request failed, mark as critical
        if shadow_error or shadow_response is None:
            comparison.diff_severity = DiffSeverity.CRITICAL
            comparison.diff_details["shadow_failure"] = shadow_error or "No response"
            return comparison

            # Compare status codes
        comparison.shadow_status = shadow_response.status_code
        comparison.status_match = primary_status == shadow_response.status_code

        # Compare response bodies
        try:
            shadow_body = shadow_response.json()
            comparison.body_match = self._compare_json_bodies(primary_body, shadow_body)

            if not comparison.body_match:
                comparison.diff_details["body_diff"] = {
                    "primary": str(primary_body)[:200],  # Truncate
                    "shadow": str(shadow_body)[:200],
                }
        except Exception as e:
            logger.warning(f"Could not parse shadow response body: {e}")
            comparison.body_match = False
            comparison.diff_details["body_parse_error"] = str(e)

            # Compare selected headers (content-type, etc.)
        important_headers = ["content-type", "content-length"]
        headers_match = True
        for header in important_headers:
            primary_val = primary_headers.get(header)
            shadow_val = shadow_response.headers.get(header)
            if primary_val != shadow_val:
                headers_match = False
                comparison.diff_details[f"header_diff_{header}"] = {
                    "primary": primary_val,
                    "shadow": shadow_val,
                }

        comparison.headers_match = headers_match

        # Determine severity
        comparison.diff_severity = self._calculate_diff_severity(comparison)

        return comparison

    def _compare_json_bodies(self, primary: Any, shadow: Any) -> bool:
        """
        Compare JSON response bodies.

        Ignores certain fields like timestamps, request IDs, etc.

        Args:
            primary: Primary response body
            shadow: Shadow response body

        Returns:
            True if bodies match (ignoring ignorable fields)
        """
        # Simple equality check for now
        # In production, you'd want more sophisticated comparison
        # that ignores timestamps, UUIDs, etc.
        try:
            return json.dumps(primary, sort_keys=True) == json.dumps(
                shadow, sort_keys=True
            )
        except Exception:
            return str(primary) == str(shadow)

    def _calculate_diff_severity(self, comparison: ResponseComparison) -> DiffSeverity:
        """
        Calculate severity of differences between responses.

        Args:
            comparison: Response comparison object

        Returns:
            Severity level of differences
        """
        # No differences
        if (
            comparison.status_match
            and comparison.body_match
            and comparison.headers_match
        ):
            return DiffSeverity.NONE

            # Critical: Status code mismatch or errors
        if not comparison.status_match:
            # Both 2xx or both error is medium
            if (
                200 <= comparison.primary_status < 300
                and 200 <= comparison.shadow_status < 300
            ):
                return DiffSeverity.MEDIUM
            return DiffSeverity.HIGH

            # High: Body content mismatch
        if not comparison.body_match:
            return DiffSeverity.HIGH

            # Low: Only header differences
        if not comparison.headers_match:
            return DiffSeverity.LOW

        return DiffSeverity.MEDIUM

    async def _handle_diff_alert(
        self,
        comparison: ResponseComparison,
        method: str,
        path: str,
        body: bytes | None,
    ) -> None:
        """
        Handle alerting for response differences.

        Args:
            comparison: Response comparison with diffs
            method: Request method
            path: Request path
            body: Request body
        """
        if not self.config.alert_on_diff:
            return

            # Check if severity meets threshold
        severity_order = [
            DiffSeverity.NONE,
            DiffSeverity.LOW,
            DiffSeverity.MEDIUM,
            DiffSeverity.HIGH,
            DiffSeverity.CRITICAL,
        ]

        if severity_order.index(comparison.diff_severity) < severity_order.index(
            self.config.diff_threshold
        ):
            return

            # Create diff report
        report = DiffReport(
            comparison=comparison,
            request_method=method,
            request_path=path,
            request_body=body.decode() if body else None,
            diff_summary=self._generate_diff_summary(comparison),
            recommendation=self._generate_recommendation(comparison),
        )

        # Log alert
        logger.warning(
            f"Shadow traffic diff detected: "
            f"severity={comparison.diff_severity}, "
            f"request_id={comparison.request_id}, "
            f"path={path}"
        )

        # Call alert callback
        if self.alert_callback:
            try:
                # Call callback (could be sync or async)
                if asyncio.iscoroutinefunction(self.alert_callback):
                    await self.alert_callback(report)
                else:
                    self.alert_callback(report)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}", exc_info=True)

    def _generate_diff_summary(self, comparison: ResponseComparison) -> str:
        """
        Generate human-readable diff summary.

        Args:
            comparison: Response comparison

        Returns:
            Summary string
        """
        parts = []

        if not comparison.status_match:
            parts.append(
                f"Status: {comparison.primary_status} vs {comparison.shadow_status}"
            )

        if not comparison.body_match:
            parts.append("Body content differs")

        if not comparison.headers_match:
            parts.append("Headers differ")

        if comparison.shadow_error:
            parts.append(f"Shadow error: {comparison.shadow_error}")

        return "; ".join(parts) if parts else "No differences"

    def _generate_recommendation(self, comparison: ResponseComparison) -> str:
        """
        Generate recommendation based on diff analysis.

        Args:
            comparison: Response comparison

        Returns:
            Recommendation string
        """
        if comparison.diff_severity == DiffSeverity.CRITICAL:
            return "Investigate shadow service failure immediately"

        if not comparison.status_match:
            return "Review status code difference - potential behavior change"

        if not comparison.body_match:
            return "Review response body differences - potential data inconsistency"

        return "Monitor for continued differences"

    async def duplicate_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: bytes | None,
        user_id: str | None,
        primary_response: dict[str, Any],
        primary_response_time: float,
    ) -> ResponseComparison | None:
        """
        Duplicate request to shadow service and compare responses.

        This method:
        1. Checks if request should be sampled
        2. Applies traffic filters
        3. Sends request to shadow service
        4. Compares responses
        5. Updates metrics
        6. Alerts on significant diffs

        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            body: Request body
            user_id: Optional user ID for filtering
            primary_response: Primary service response dict with keys:
                - status: HTTP status code
                - body: Response body (JSON)
                - headers: Response headers dict
            primary_response_time: Primary response time in ms

        Returns:
            ResponseComparison if request was shadowed, None otherwise

        Example:
            ```python
            comparison = await manager.duplicate_request(
                method="POST",
                path="/api/schedules",
                headers={"content-type": "application/json"},
                body=b'{"name": "Test Schedule"}',
                user_id="user123",
                primary_response={
                    "status": 201,
                    "body": {"id": "schedule456", "name": "Test Schedule"},
                    "headers": {"content-type": "application/json"},
                },
                primary_response_time=45.2,
            )
            ```
        """
        self._stats.total_requests += 1

        # Check if enabled
        if not self.config.enabled:
            return None

            # Check sampling
        if not self.should_sample():
            return None

            # Check filters
        if self.should_filter(method, path, body, user_id):
            self._stats.skipped_requests += 1
            return None

            # Generate request ID
        request_id = self._generate_request_id(method, path, body)

        # Track sampling
        self._stats.sampled_requests += 1

        # Prepare headers
        shadow_headers = self._prepare_headers(headers)

        # Send shadow request (with concurrency control)
        async with self._semaphore:
            (
                shadow_response,
                shadow_response_time,
                shadow_error,
            ) = await self._send_shadow_request(
                method, path, shadow_headers, body, request_id
            )

            # Update health metrics
        self._health.total_requests += 1
        if shadow_error:
            self._stats.failed_shadows += 1
        else:
            self._stats.successful_shadows += 1

            # Track response times
        self._primary_response_times.append(primary_response_time)
        self._shadow_response_times.append(shadow_response_time)

        # Compare responses
        comparison = self._compare_responses(
            request_id=request_id,
            primary_status=primary_response["status"],
            primary_body=primary_response["body"],
            primary_headers=primary_response["headers"],
            primary_response_time=primary_response_time,
            shadow_response=shadow_response,
            shadow_response_time=shadow_response_time,
            shadow_error=shadow_error,
        )

        # Store comparison
        self._comparisons.append(comparison)

        # Clean old comparisons (keep last N)
        if len(self._comparisons) > 1000:
            self._comparisons = self._comparisons[-1000:]

            # Update diff stats
        if comparison.diff_severity != DiffSeverity.NONE:
            self._stats.diffs_detected += 1
            severity_key = comparison.diff_severity.value
            self._stats.diffs_by_severity[severity_key] = (
                self._stats.diffs_by_severity.get(severity_key, 0) + 1
            )

            # Alert on significant diffs
            await self._handle_diff_alert(comparison, method, path, body)

        return comparison

    async def check_health(self) -> ShadowHealthMetrics:
        """
        Check shadow service health.

        Returns:
            Health metrics for shadow service
        """
        if not self.config.enabled or not self.config.shadow_url:
            self._health.status = "disabled"
            return self._health

        try:
            client = await self._get_client()
            start_time = time.time()

            # Ping shadow service health endpoint
            health_url = urljoin(self.config.shadow_url, "/health")
            response = await client.get(health_url, timeout=5.0)

            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                self._health.status = "healthy"
            else:
                self._health.status = "degraded"

            self._health.last_check = datetime.utcnow()
            self._health.avg_response_time = response_time

        except Exception as e:
            logger.error(f"Shadow service health check failed: {e}")
            self._health.status = "unhealthy"
            self._health.last_check = datetime.utcnow()

            # Calculate success rate
        if self._health.total_requests > 0:
            success_count = self._stats.successful_shadows
            self._health.success_rate = success_count / self._health.total_requests

        return self._health

    def get_health_metrics(self) -> ShadowHealthMetrics:
        """
        Get current health metrics.

        Returns:
            Shadow service health metrics
        """
        return self._health

    def get_performance_metrics(self) -> ShadowPerformanceMetrics:
        """
        Get performance comparison metrics.

        Returns:
            Performance metrics comparing primary and shadow
        """
        metrics = ShadowPerformanceMetrics()

        # Calculate average response times
        if self._primary_response_times:
            metrics.primary_avg_response_time = sum(self._primary_response_times) / len(
                self._primary_response_times
            )

        if self._shadow_response_times:
            metrics.shadow_avg_response_time = sum(self._shadow_response_times) / len(
                self._shadow_response_times
            )

            # Calculate response time ratio
        if metrics.primary_avg_response_time > 0:
            metrics.response_time_ratio = (
                metrics.shadow_avg_response_time / metrics.primary_avg_response_time
            )

            # Calculate error rates
        total = self._stats.sampled_requests
        if total > 0:
            metrics.shadow_error_rate = self._stats.failed_shadows / total

            # Calculate match rate
        if self._comparisons:
            matches = sum(
                1 for c in self._comparisons if c.diff_severity == DiffSeverity.NONE
            )
            metrics.match_rate = (matches / len(self._comparisons)) * 100

        metrics.total_comparisons = len(self._comparisons)

        return metrics

    def get_traffic_stats(self) -> ShadowTrafficStats:
        """
        Get overall traffic statistics.

        Returns:
            Shadow traffic statistics
        """
        # Calculate actual sampling rate
        if self._stats.total_requests > 0:
            self._stats.sampling_rate_actual = (
                self._stats.sampled_requests / self._stats.total_requests
            )

            # Calculate average shadow overhead
        if self._shadow_response_times and self._primary_response_times:
            avg_shadow = sum(self._shadow_response_times) / len(
                self._shadow_response_times
            )
            avg_primary = sum(self._primary_response_times) / len(
                self._primary_response_times
            )
            self._stats.avg_shadow_overhead = avg_shadow - avg_primary

        return self._stats

    def reset_metrics(self) -> None:
        """Reset all metrics and comparisons."""
        self._comparisons = []
        self._stats = ShadowTrafficStats()
        self._health = ShadowHealthMetrics()
        self._shadow_response_times = []
        self._primary_response_times = []

        logger.info("Shadow traffic metrics reset")
