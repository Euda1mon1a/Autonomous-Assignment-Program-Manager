"""Request replay service for testing and debugging.

This service handles:
- Request capture and storage
- Request replay with timing control
- Request modification before replay
- Response comparison utilities
- Replay filtering by criteria
- Bulk replay operations
- Replay scheduling
- Replay result reporting
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models (Pydantic)
# =============================================================================

from pydantic import BaseModel, Field


class CapturedRequest(BaseModel):
    """Model for a captured HTTP request."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    method: str
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] | None = None
    body_hash: str = ""
    response_status: int = 0
    response_headers: dict[str, str] = Field(default_factory=dict)
    response_body: dict[str, Any] | None = None
    response_time_ms: float = 0.0
    user_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ReplayRequest(BaseModel):
    """Request to replay a captured request."""

    request_id: str
    modifications: dict[str, Any] = Field(default_factory=dict)
    delay_ms: int = 0
    timeout_seconds: int = 30
    follow_redirects: bool = True
    verify_ssl: bool = True


class ReplayResult(BaseModel):
    """Result of a replay operation."""

    request_id: str
    replay_timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = False
    status_code: int = 0
    response_body: dict[str, Any] | None = None
    response_time_ms: float = 0.0
    error_message: str | None = None
    comparison: dict[str, Any] | None = None


class ReplayComparison(BaseModel):
    """Comparison between original and replay responses."""

    status_match: bool = False
    body_match: bool = False
    headers_match: bool = False
    timing_difference_ms: float = 0.0
    differences: list[dict[str, Any]] = Field(default_factory=list)


class ReplayFilter(BaseModel):
    """Filters for querying captured requests."""

    method: str | None = None
    url_pattern: str | None = None
    status_code: int | None = None
    status_code_min: int | None = None
    status_code_max: int | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    user_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    has_error: bool | None = None
    limit: int = 100


class BulkReplayRequest(BaseModel):
    """Request for bulk replay operation."""

    filters: ReplayFilter
    modifications: dict[str, Any] = Field(default_factory=dict)
    delay_between_ms: int = 0
    max_concurrent: int = 5
    timeout_seconds: int = 30
    stop_on_error: bool = False


class ReplaySchedule(BaseModel):
    """Schedule for automated replay."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    filters: ReplayFilter
    cron_expression: str
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None


class ReplayReport(BaseModel):
    """Report summarizing replay results."""

    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)
    avg_response_time_ms: float = 0.0
    status_code_distribution: dict[int, int] = Field(default_factory=dict)
    comparisons: list[ReplayComparison] = Field(default_factory=list)


# =============================================================================
# In-Memory Storage (for MVP - replace with DB models in production)
# =============================================================================


class ReplayStorage:
    """In-memory storage for captured requests and replay results."""

    def __init__(self):
        self.requests: dict[str, CapturedRequest] = {}
        self.results: dict[str, list[ReplayResult]] = {}
        self.schedules: dict[str, ReplaySchedule] = {}

    async def store_request(self, request: CapturedRequest) -> str:
        """Store a captured request."""
        self.requests[request.id] = request
        return request.id

    async def get_request(self, request_id: str) -> CapturedRequest | None:
        """Retrieve a captured request by ID."""
        return self.requests.get(request_id)

    async def search_requests(self, filters: ReplayFilter) -> list[CapturedRequest]:
        """Search for captured requests matching filters."""
        results = list(self.requests.values())

        # Apply filters
        if filters.method:
            results = [r for r in results if r.method == filters.method]

        if filters.url_pattern:
            results = [r for r in results if filters.url_pattern in r.url]

        if filters.status_code:
            results = [r for r in results if r.response_status == filters.status_code]

        if filters.status_code_min:
            results = [
                r for r in results if r.response_status >= filters.status_code_min
            ]

        if filters.status_code_max:
            results = [
                r for r in results if r.response_status <= filters.status_code_max
            ]

        if filters.created_after:
            results = [r for r in results if r.timestamp >= filters.created_after]

        if filters.created_before:
            results = [r for r in results if r.timestamp <= filters.created_before]

        if filters.user_id:
            results = [r for r in results if r.user_id == filters.user_id]

        if filters.tags:
            results = [r for r in results if any(tag in r.tags for tag in filters.tags)]

        if filters.has_error is not None:
            if filters.has_error:
                results = [r for r in results if r.response_status >= 400]
            else:
                results = [r for r in results if r.response_status < 400]

        # Sort by timestamp descending
        results.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        return results[: filters.limit]

    async def store_result(self, request_id: str, result: ReplayResult) -> None:
        """Store a replay result."""
        if request_id not in self.results:
            self.results[request_id] = []
        self.results[request_id].append(result)

    async def get_results(self, request_id: str) -> list[ReplayResult]:
        """Get all replay results for a request."""
        return self.results.get(request_id, [])

    async def store_schedule(self, schedule: ReplaySchedule) -> str:
        """Store a replay schedule."""
        self.schedules[schedule.id] = schedule
        return schedule.id

    async def get_schedule(self, schedule_id: str) -> ReplaySchedule | None:
        """Get a replay schedule by ID."""
        return self.schedules.get(schedule_id)

    async def list_schedules(self, enabled_only: bool = False) -> list[ReplaySchedule]:
        """List all replay schedules."""
        schedules = list(self.schedules.values())
        if enabled_only:
            schedules = [s for s in schedules if s.enabled]
        return schedules


# =============================================================================
# ReplayService Class
# =============================================================================


class ReplayService:
    """
    Service for capturing and replaying HTTP requests.

    This service provides comprehensive request replay functionality including:
    - Request/response capture
    - Single and bulk replay
    - Request modification
    - Response comparison
    - Scheduled replay
    - Detailed reporting
    """

    def __init__(
        self,
        storage: ReplayStorage | None = None,
        base_url: str = "http://localhost:8000",
    ):
        """
        Initialize ReplayService.

        Args:
            storage: Storage backend for requests and results
            base_url: Base URL for replaying requests
        """
        self.storage = storage or ReplayStorage()
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self.client.aclose()

    # =========================================================================
    # Request Capture
    # =========================================================================

    async def capture_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        response_status: int = 0,
        response_headers: dict[str, str] | None = None,
        response_body: dict[str, Any] | None = None,
        response_time_ms: float = 0.0,
        user_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Capture an HTTP request and its response.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            query_params: Query parameters
            body: Request body
            response_status: HTTP response status code
            response_headers: Response headers
            response_body: Response body
            response_time_ms: Response time in milliseconds
            user_id: User who made the request
            tags: Tags for categorization
            metadata: Additional metadata

        Returns:
            Request ID
        """
        # Compute body hash for deduplication
        body_hash = ""
        if body:
            body_str = json.dumps(body, sort_keys=True, default=str)
            body_hash = hashlib.sha256(body_str.encode()).hexdigest()

        request = CapturedRequest(
            method=method.upper(),
            url=url,
            headers=headers or {},
            query_params=query_params or {},
            body=body,
            body_hash=body_hash,
            response_status=response_status,
            response_headers=response_headers or {},
            response_body=response_body,
            response_time_ms=response_time_ms,
            user_id=user_id,
            tags=tags or [],
            metadata=metadata or {},
        )

        request_id = await self.storage.store_request(request)
        logger.info(
            f"Captured request {request_id}: {method} {url} -> {response_status}"
        )

        return request_id

    async def get_captured_request(self, request_id: str) -> CapturedRequest | None:
        """
        Retrieve a captured request by ID.

        Args:
            request_id: Request ID

        Returns:
            CapturedRequest if found, None otherwise
        """
        return await self.storage.get_request(request_id)

    async def search_requests(self, filters: ReplayFilter) -> list[CapturedRequest]:
        """
        Search for captured requests matching filters.

        Args:
            filters: Search filters

        Returns:
            List of matching CapturedRequest objects
        """
        return await self.storage.search_requests(filters)

    # =========================================================================
    # Request Replay
    # =========================================================================

    async def replay_request(
        self,
        request_id: str,
        modifications: dict[str, Any] | None = None,
        delay_ms: int = 0,
        timeout_seconds: int = 30,
        compare: bool = True,
    ) -> ReplayResult:
        """
        Replay a captured request.

        Args:
            request_id: ID of the request to replay
            modifications: Modifications to apply before replay
            delay_ms: Delay before replay in milliseconds
            timeout_seconds: Request timeout
            compare: Whether to compare with original response

        Returns:
            ReplayResult with replay outcome and comparison

        Raises:
            ValueError: If request not found
        """
        # Get original request
        original = await self.storage.get_request(request_id)
        if not original:
            raise ValueError(f"Request {request_id} not found")

        # Apply delay
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000.0)

        # Apply modifications
        modified_request = self._apply_modifications(original, modifications or {})

        # Execute request
        result = ReplayResult(request_id=request_id)

        try:
            start_time = datetime.utcnow()

            # Build full URL
            full_url = modified_request.url
            if not full_url.startswith("http"):
                full_url = f"{self.base_url}{full_url}"

            # Make request
            response = await self.client.request(
                method=modified_request.method,
                url=full_url,
                headers=modified_request.headers,
                params=modified_request.query_params,
                json=modified_request.body,
                timeout=timeout_seconds,
            )

            end_time = datetime.utcnow()
            elapsed_ms = (end_time - start_time).total_seconds() * 1000

            # Store result
            result.success = True
            result.status_code = response.status_code
            result.response_time_ms = elapsed_ms

            try:
                result.response_body = response.json()
            except Exception:
                result.response_body = {"text": response.text}

            # Compare with original if requested
            if compare:
                result.comparison = self._compare_responses(
                    original, result
                ).model_dump()

            logger.info(
                f"Replayed request {request_id}: {response.status_code} "
                f"({elapsed_ms:.2f}ms)"
            )

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            logger.error(f"Failed to replay request {request_id}: {e}")

        # Store result
        await self.storage.store_result(request_id, result)

        return result

    def _apply_modifications(
        self,
        request: CapturedRequest,
        modifications: dict[str, Any],
    ) -> CapturedRequest:
        """
        Apply modifications to a request before replay.

        Modifications can include:
        - headers: dict to merge with existing headers
        - query_params: dict to merge with existing params
        - body: dict to deep merge with existing body
        - url: new URL
        - method: new HTTP method

        Args:
            request: Original request
            modifications: Modifications to apply

        Returns:
            Modified request
        """
        modified = request.model_copy(deep=True)

        # Update headers
        if "headers" in modifications:
            modified.headers.update(modifications["headers"])

        # Update query params
        if "query_params" in modifications:
            modified.query_params.update(modifications["query_params"])

        # Update body (deep merge)
        if "body" in modifications and modified.body:
            modified.body = self._deep_merge(modified.body, modifications["body"])

        # Update URL
        if "url" in modifications:
            modified.url = modifications["url"]

        # Update method
        if "method" in modifications:
            modified.method = modifications["method"].upper()

        return modified

    def _deep_merge(self, base: dict, updates: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in updates.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # =========================================================================
    # Response Comparison
    # =========================================================================

    def _compare_responses(
        self,
        original: CapturedRequest,
        replay: ReplayResult,
    ) -> ReplayComparison:
        """
        Compare original and replay responses.

        Args:
            original: Original captured request
            replay: Replay result

        Returns:
            ReplayComparison with detailed differences
        """
        comparison = ReplayComparison()

        # Status code comparison
        comparison.status_match = original.response_status == replay.status_code

        # Body comparison
        comparison.body_match = self._compare_json(
            original.response_body, replay.response_body
        )

        # Timing comparison
        comparison.timing_difference_ms = (
            replay.response_time_ms - original.response_time_ms
        )

        # Detailed differences
        if not comparison.status_match:
            comparison.differences.append(
                {
                    "field": "status_code",
                    "original": original.response_status,
                    "replay": replay.status_code,
                }
            )

        if not comparison.body_match:
            body_diffs = self._find_json_differences(
                original.response_body or {},
                replay.response_body or {},
            )
            comparison.differences.extend(body_diffs)

        return comparison

    def _compare_json(self, obj1: Any, obj2: Any) -> bool:
        """Compare two JSON objects for equality."""
        try:
            return json.dumps(obj1, sort_keys=True) == json.dumps(obj2, sort_keys=True)
        except Exception:
            return obj1 == obj2

    def _find_json_differences(
        self,
        original: dict,
        replay: dict,
        path: str = "",
    ) -> list[dict[str, Any]]:
        """Find differences between two JSON objects."""
        differences = []

        # Check for missing/extra keys
        original_keys = set(original.keys())
        replay_keys = set(replay.keys())

        for key in original_keys - replay_keys:
            differences.append(
                {
                    "field": f"{path}.{key}" if path else key,
                    "original": original[key],
                    "replay": None,
                    "type": "missing_in_replay",
                }
            )

        for key in replay_keys - original_keys:
            differences.append(
                {
                    "field": f"{path}.{key}" if path else key,
                    "original": None,
                    "replay": replay[key],
                    "type": "extra_in_replay",
                }
            )

        # Check for value differences
        for key in original_keys & replay_keys:
            field_path = f"{path}.{key}" if path else key
            orig_val = original[key]
            replay_val = replay[key]

            if isinstance(orig_val, dict) and isinstance(replay_val, dict):
                # Recurse for nested objects
                differences.extend(
                    self._find_json_differences(orig_val, replay_val, field_path)
                )
            elif orig_val != replay_val:
                differences.append(
                    {
                        "field": field_path,
                        "original": orig_val,
                        "replay": replay_val,
                        "type": "value_mismatch",
                    }
                )

        return differences

    # =========================================================================
    # Bulk Replay
    # =========================================================================

    async def bulk_replay(
        self,
        filters: ReplayFilter,
        modifications: dict[str, Any] | None = None,
        delay_between_ms: int = 0,
        max_concurrent: int = 5,
        timeout_seconds: int = 30,
        stop_on_error: bool = False,
    ) -> ReplayReport:
        """
        Replay multiple requests matching filters.

        Args:
            filters: Filters to select requests
            modifications: Modifications to apply to all requests
            delay_between_ms: Delay between requests
            max_concurrent: Maximum concurrent replays
            timeout_seconds: Timeout for each request
            stop_on_error: Stop on first error

        Returns:
            ReplayReport with summary and results
        """
        # Find matching requests
        requests = await self.storage.search_requests(filters)

        logger.info(f"Bulk replay: found {len(requests)} matching requests")

        report = ReplayReport(total_requests=len(requests))
        semaphore = asyncio.Semaphore(max_concurrent)

        async def replay_with_semaphore(req: CapturedRequest):
            """Replay with concurrency control."""
            async with semaphore:
                if delay_between_ms > 0:
                    await asyncio.sleep(delay_between_ms / 1000.0)

                try:
                    result = await self.replay_request(
                        req.id,
                        modifications=modifications,
                        timeout_seconds=timeout_seconds,
                    )

                    if result.success:
                        report.successful += 1
                        if result.comparison:
                            report.comparisons.append(
                                ReplayComparison(**result.comparison)
                            )
                    else:
                        report.failed += 1
                        if result.error_message:
                            report.errors.append(result.error_message)

                    # Update status distribution
                    if result.status_code > 0:
                        report.status_code_distribution[result.status_code] = (
                            report.status_code_distribution.get(result.status_code, 0)
                            + 1
                        )

                    return result

                except Exception as e:
                    report.failed += 1
                    report.errors.append(str(e))
                    logger.error(f"Error replaying request {req.id}: {e}")
                    if stop_on_error:
                        raise

        # Execute replays
        tasks = [replay_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=not stop_on_error)

        # Calculate average response time
        valid_times = [
            r.response_time_ms
            for r in results
            if isinstance(r, ReplayResult) and r.response_time_ms > 0
        ]
        if valid_times:
            report.avg_response_time_ms = sum(valid_times) / len(valid_times)

        logger.info(
            f"Bulk replay complete: {report.successful} successful, "
            f"{report.failed} failed"
        )

        return report

    # =========================================================================
    # Replay Scheduling
    # =========================================================================

    async def create_schedule(
        self,
        name: str,
        filters: ReplayFilter,
        cron_expression: str,
        enabled: bool = True,
    ) -> str:
        """
        Create a scheduled replay task.

        Args:
            name: Schedule name
            filters: Filters for requests to replay
            cron_expression: Cron expression for scheduling
            enabled: Whether schedule is enabled

        Returns:
            Schedule ID
        """
        schedule = ReplaySchedule(
            name=name,
            filters=filters,
            cron_expression=cron_expression,
            enabled=enabled,
        )

        schedule_id = await self.storage.store_schedule(schedule)
        logger.info(f"Created replay schedule {schedule_id}: {name}")

        return schedule_id

    async def get_schedule(self, schedule_id: str) -> ReplaySchedule | None:
        """
        Get a replay schedule by ID.

        Args:
            schedule_id: Schedule ID

        Returns:
            ReplaySchedule if found, None otherwise
        """
        return await self.storage.get_schedule(schedule_id)

    async def list_schedules(self, enabled_only: bool = False) -> list[ReplaySchedule]:
        """
        List all replay schedules.

        Args:
            enabled_only: Only return enabled schedules

        Returns:
            List of ReplaySchedule objects
        """
        return await self.storage.list_schedules(enabled_only=enabled_only)

    # =========================================================================
    # Reporting
    # =========================================================================

    async def generate_report(
        self,
        request_ids: list[str] | None = None,
        filters: ReplayFilter | None = None,
    ) -> ReplayReport:
        """
        Generate a report for replay results.

        Args:
            request_ids: Specific request IDs to report on
            filters: Filters to select requests

        Returns:
            ReplayReport with aggregated statistics
        """
        report = ReplayReport()

        # Get requests
        if request_ids:
            requests = []
            for req_id in request_ids:
                req = await self.storage.get_request(req_id)
                if req:
                    requests.append(req)
        elif filters:
            requests = await self.storage.search_requests(filters)
        else:
            requests = []

        report.total_requests = len(requests)

        # Aggregate results
        all_results = []
        for req in requests:
            results = await self.storage.get_results(req.id)
            all_results.extend(results)

        # Calculate statistics
        for result in all_results:
            if result.success:
                report.successful += 1
            else:
                report.failed += 1
                if result.error_message:
                    report.errors.append(result.error_message)

            if result.status_code > 0:
                report.status_code_distribution[result.status_code] = (
                    report.status_code_distribution.get(result.status_code, 0) + 1
                )

            if result.comparison:
                report.comparisons.append(ReplayComparison(**result.comparison))

        # Calculate average response time
        valid_times = [
            r.response_time_ms for r in all_results if r.response_time_ms > 0
        ]
        if valid_times:
            report.avg_response_time_ms = sum(valid_times) / len(valid_times)

        return report

    async def get_replay_history(self, request_id: str) -> list[ReplayResult]:
        """
        Get replay history for a specific request.

        Args:
            request_id: Request ID

        Returns:
            List of ReplayResult objects
        """
        return await self.storage.get_results(request_id)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def delete_request(self, request_id: str) -> bool:
        """
        Delete a captured request and its replay results.

        Args:
            request_id: Request ID

        Returns:
            True if deleted, False if not found
        """
        if request_id in self.storage.requests:
            del self.storage.requests[request_id]
            if request_id in self.storage.results:
                del self.storage.results[request_id]
            logger.info(f"Deleted request {request_id}")
            return True
        return False

    async def clear_old_requests(self, days: int = 30) -> int:
        """
        Clear requests older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of requests deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = 0

        for request_id, request in list(self.storage.requests.items()):
            if request.timestamp < cutoff:
                await self.delete_request(request_id)
                count += 1

        logger.info(f"Cleared {count} requests older than {days} days")
        return count
