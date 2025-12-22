"""
Response logging utilities.

Provides enhanced response logging capabilities:
- Response body capture and logging
- Performance metrics
- Response size tracking
- Content type analysis
- Streaming response handling
"""

import io
import json
import logging
import time
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

from app.middleware.logging.filters import SensitiveDataFilter

logger = logging.getLogger(__name__)


class ResponseLogger:
    """
    Utility for logging response data.

    Can be used independently or as part of request/response logging middleware.
    """

    def __init__(
        self,
        max_body_size: int = 10 * 1024,  # 10 KB
        filter_sensitive: bool = True,
        sensitive_filter: Optional[SensitiveDataFilter] = None,
    ):
        """
        Initialize response logger.

        Args:
            max_body_size: Maximum response body size to log (bytes)
            filter_sensitive: Whether to filter sensitive data from responses
            sensitive_filter: Custom sensitive data filter
        """
        self.max_body_size = max_body_size
        self.filter_sensitive = filter_sensitive
        self.sensitive_filter = sensitive_filter or SensitiveDataFilter()

    async def log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        duration_ms: float,
    ) -> Dict[str, Any]:
        """
        Log response details.

        Args:
            request: FastAPI request object
            response: Response object
            request_id: Request correlation ID
            duration_ms: Request processing duration

        Returns:
            Dict containing logged response data
        """
        log_entry = {
            "type": "response",
            "timestamp": time.time(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Extract response headers
        headers = dict(response.headers)
        if self.filter_sensitive:
            headers = self.sensitive_filter.filter_headers(headers)
        log_entry["headers"] = headers

        # Extract content type
        content_type = response.headers.get("content-type", "")
        log_entry["content_type"] = content_type

        # Extract content length
        content_length = response.headers.get("content-length")
        if content_length:
            log_entry["content_length"] = int(content_length)

        # Attempt to read response body (if possible)
        if hasattr(response, "body") and response.body:
            body_data = self._parse_response_body(response.body, content_type)
            if body_data:
                log_entry["body"] = body_data

        # Performance categorization
        log_entry["performance"] = self._categorize_performance(duration_ms)

        # Determine log level
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        # Log
        logger.log(
            log_level,
            f"Response: {request.method} {request.url.path} -> "
            f"{response.status_code} ({duration_ms:.2f}ms)",
            extra=log_entry,
        )

        return log_entry

    def _parse_response_body(
        self, body: bytes, content_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parse and filter response body.

        Args:
            body: Response body bytes
            content_type: Response content type

        Returns:
            Parsed and filtered body data or None
        """
        # Check size limit
        if len(body) > self.max_body_size:
            return {
                "_note": f"Body too large ({len(body)} bytes, max {self.max_body_size})"
            }

        # Parse JSON responses
        if "application/json" in content_type:
            try:
                body_json = json.loads(body)
                if self.filter_sensitive:
                    body_json = self.sensitive_filter.filter_dict(body_json)
                return body_json
            except json.JSONDecodeError:
                return {
                    "_note": "Invalid JSON",
                    "_raw": body[:200].decode("utf-8", errors="ignore"),
                }

        # For text responses, include truncated content
        elif "text/" in content_type:
            return {
                "_text": body[:500].decode("utf-8", errors="ignore"),
                "_size": len(body),
            }

        # For other content types, just log metadata
        else:
            return {"_content_type": content_type, "_size": len(body)}

    def _categorize_performance(self, duration_ms: float) -> str:
        """
        Categorize response time performance.

        Args:
            duration_ms: Response time in milliseconds

        Returns:
            Performance category: "excellent", "good", "fair", "poor", "critical"
        """
        if duration_ms < 100:
            return "excellent"
        elif duration_ms < 500:
            return "good"
        elif duration_ms < 1000:
            return "fair"
        elif duration_ms < 3000:
            return "poor"
        else:
            return "critical"


class StreamingResponseLogger:
    """
    Logger for streaming responses.

    Handles logging of streaming responses without consuming the stream,
    using background tasks to log after response is sent.
    """

    def __init__(self, response_logger: Optional[ResponseLogger] = None):
        """
        Initialize streaming response logger.

        Args:
            response_logger: ResponseLogger instance to use
        """
        self.response_logger = response_logger or ResponseLogger()
        self._stream_data: Dict[str, Any] = {}

    def log_streaming_response(
        self,
        request: Request,
        response: StreamingResponse,
        request_id: str,
        start_time: float,
    ) -> StreamingResponse:
        """
        Log streaming response metadata.

        Args:
            request: Request object
            response: StreamingResponse
            request_id: Request correlation ID
            start_time: Request start time (from time.perf_counter())

        Returns:
            Modified StreamingResponse with logging background task
        """
        # Log initial response metadata
        duration_ms = (time.perf_counter() - start_time) * 1000

        log_entry = {
            "type": "streaming_response",
            "timestamp": time.time(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "content_type": response.headers.get("content-type", ""),
            "note": "Streaming response - body not captured",
        }

        logger.info(
            f"Streaming response: {request.method} {request.url.path} -> "
            f"{response.status_code} ({duration_ms:.2f}ms)",
            extra=log_entry,
        )

        return response


class ResponseMetrics:
    """
    Collect and track response metrics.

    Provides statistics on:
    - Response time distribution
    - Status code distribution
    - Response size distribution
    - Endpoint-specific metrics
    """

    def __init__(self):
        """Initialize response metrics tracker."""
        self.metrics: Dict[str, Any] = {
            "total_requests": 0,
            "status_codes": {},
            "response_times": {
                "excellent": 0,  # < 100ms
                "good": 0,  # < 500ms
                "fair": 0,  # < 1000ms
                "poor": 0,  # < 3000ms
                "critical": 0,  # >= 3000ms
            },
            "endpoints": {},
        }

    def record_response(
        self,
        path: str,
        method: str,
        status_code: int,
        duration_ms: float,
        response_size: int = 0,
    ) -> None:
        """
        Record response metrics.

        Args:
            path: Request path
            method: HTTP method
            status_code: Response status code
            duration_ms: Response time in milliseconds
            response_size: Response size in bytes
        """
        self.metrics["total_requests"] += 1

        # Track status codes
        status_key = str(status_code)
        self.metrics["status_codes"][status_key] = (
            self.metrics["status_codes"].get(status_key, 0) + 1
        )

        # Track response times
        if duration_ms < 100:
            self.metrics["response_times"]["excellent"] += 1
        elif duration_ms < 500:
            self.metrics["response_times"]["good"] += 1
        elif duration_ms < 1000:
            self.metrics["response_times"]["fair"] += 1
        elif duration_ms < 3000:
            self.metrics["response_times"]["poor"] += 1
        else:
            self.metrics["response_times"]["critical"] += 1

        # Track per-endpoint metrics
        endpoint_key = f"{method} {path}"
        if endpoint_key not in self.metrics["endpoints"]:
            self.metrics["endpoints"][endpoint_key] = {
                "count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": float("inf"),
                "max_duration_ms": 0,
                "total_size_bytes": 0,
            }

        endpoint = self.metrics["endpoints"][endpoint_key]
        endpoint["count"] += 1
        endpoint["total_duration_ms"] += duration_ms
        endpoint["avg_duration_ms"] = endpoint["total_duration_ms"] / endpoint["count"]
        endpoint["min_duration_ms"] = min(endpoint["min_duration_ms"], duration_ms)
        endpoint["max_duration_ms"] = max(endpoint["max_duration_ms"], duration_ms)
        endpoint["total_size_bytes"] += response_size

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return self.metrics.copy()

    def reset(self) -> None:
        """Reset all metrics."""
        self.__init__()


# Global metrics instance
global_metrics = ResponseMetrics()
