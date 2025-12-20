"""
Mock API server for testing.

Provides a flexible mock server implementation that can:
- Record and replay API requests
- Simulate response delays
- Inject errors conditionally
- Maintain stateful behavior
- Generate responses from OpenAPI schemas
"""
import asyncio
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Union
from uuid import UUID, uuid4

from fastapi import Request, Response
from pydantic import BaseModel


class HTTPMethod(str, Enum):
    """HTTP methods supported by mock server."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class MockRequest:
    """
    Recorded request information.

    Captures all details of a request for verification in tests.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    method: str = ""
    path: str = ""
    query_params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def matches(self, method: str = None, path: str = None,
                path_pattern: Pattern = None) -> bool:
        """
        Check if this request matches given criteria.

        Args:
            method: HTTP method to match
            path: Exact path to match
            path_pattern: Regex pattern for path matching

        Returns:
            True if request matches all provided criteria
        """
        if method and self.method != method:
            return False
        if path and self.path != path:
            return False
        if path_pattern and not path_pattern.match(self.path):
            return False
        return True


@dataclass
class MockResponse:
    """
    Mock response configuration.

    Defines what response to return for matched requests.
    """
    status_code: int = 200
    body: Any = None
    headers: Dict[str, str] = field(default_factory=dict)
    delay_ms: int = 0
    error: Optional[Exception] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "status_code": self.status_code,
            "body": self.body,
            "headers": self.headers,
        }


class RequestMatcher:
    """
    Flexible request matching with support for patterns.

    Matches requests based on method, path, headers, query params, and body.
    """

    def __init__(
        self,
        method: Optional[str] = None,
        path: Optional[str] = None,
        path_pattern: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        body_contains: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize request matcher.

        Args:
            method: HTTP method to match
            path: Exact path to match
            path_pattern: Regex pattern for path
            headers: Headers that must be present
            query_params: Query parameters that must match
            body_contains: Key-value pairs that must be in request body
        """
        self.method = method
        self.path = path
        self.path_pattern = re.compile(path_pattern) if path_pattern else None
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.body_contains = body_contains or {}

    def matches(self, request: MockRequest) -> bool:
        """
        Check if request matches this matcher.

        Args:
            request: Request to check

        Returns:
            True if request matches all criteria
        """
        # Check method
        if self.method and request.method != self.method:
            return False

        # Check exact path
        if self.path and request.path != self.path:
            return False

        # Check path pattern
        if self.path_pattern and not self.path_pattern.match(request.path):
            return False

        # Check headers
        for key, value in self.headers.items():
            if request.headers.get(key) != value:
                return False

        # Check query params
        for key, value in self.query_params.items():
            if request.query_params.get(key) != value:
                return False

        # Check body contains
        if self.body_contains and request.body:
            if isinstance(request.body, dict):
                for key, value in self.body_contains.items():
                    if request.body.get(key) != value:
                        return False

        return True


@dataclass
class MockEndpoint:
    """
    Mock endpoint configuration.

    Defines behavior for a specific endpoint including multiple responses
    based on conditions or sequence.
    """
    matcher: RequestMatcher
    responses: List[MockResponse] = field(default_factory=list)
    current_index: int = 0
    stateful: bool = False
    call_count: int = 0

    def get_response(self, request: MockRequest) -> Optional[MockResponse]:
        """
        Get response for this request.

        Args:
            request: The request to respond to

        Returns:
            MockResponse if matcher matches, None otherwise
        """
        if not self.matcher.matches(request):
            return None

        self.call_count += 1

        if not self.responses:
            return MockResponse(status_code=200, body={})

        if self.stateful:
            # Cycle through responses
            response = self.responses[self.current_index % len(self.responses)]
            self.current_index += 1
            return response
        else:
            # Always return first response
            return self.responses[0]


class MockAPIServer:
    """
    Comprehensive mock API server for testing.

    Features:
    - Request recording for verification
    - Response delay simulation
    - Error injection
    - Stateful responses
    - OpenAPI-based mock generation
    - Conditional responses

    Example:
        ```python
        server = MockAPIServer()

        # Register endpoint
        server.register_endpoint(
            method="GET",
            path="/api/v1/people",
            response={"people": []},
            delay_ms=100
        )

        # Verify requests
        requests = server.get_requests(method="GET", path="/api/v1/people")
        assert len(requests) == 1
        ```
    """

    def __init__(self):
        """Initialize mock server."""
        self.endpoints: List[MockEndpoint] = []
        self.recorded_requests: List[MockRequest] = []
        self.default_response = MockResponse(
            status_code=404,
            body={"detail": "Mock endpoint not configured"}
        )
        self.state: Dict[str, Any] = {}
        self.enabled = True

    def register_endpoint(
        self,
        method: str,
        path: str = None,
        path_pattern: str = None,
        response: Any = None,
        status_code: int = 200,
        headers: Dict[str, str] = None,
        delay_ms: int = 0,
        error: Exception = None,
        stateful: bool = False,
        responses: List[MockResponse] = None,
    ) -> MockEndpoint:
        """
        Register a mock endpoint.

        Args:
            method: HTTP method
            path: Exact path to match
            path_pattern: Regex pattern for path
            response: Response body
            status_code: HTTP status code
            headers: Response headers
            delay_ms: Response delay in milliseconds
            error: Error to raise
            stateful: Whether to cycle through multiple responses
            responses: List of responses for stateful endpoints

        Returns:
            Created MockEndpoint
        """
        matcher = RequestMatcher(method=method, path=path, path_pattern=path_pattern)

        if responses:
            mock_responses = responses
        else:
            mock_responses = [
                MockResponse(
                    status_code=status_code,
                    body=response,
                    headers=headers or {},
                    delay_ms=delay_ms,
                    error=error,
                )
            ]

        endpoint = MockEndpoint(
            matcher=matcher,
            responses=mock_responses,
            stateful=stateful,
        )

        self.endpoints.append(endpoint)
        return endpoint

    async def handle_request(
        self,
        method: str,
        path: str,
        query_params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        body: Any = None,
    ) -> MockResponse:
        """
        Handle a request and return mock response.

        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters
            headers: Request headers
            body: Request body

        Returns:
            MockResponse for this request
        """
        # Record request
        request = MockRequest(
            method=method,
            path=path,
            query_params=query_params or {},
            headers=headers or {},
            body=body,
        )
        self.recorded_requests.append(request)

        if not self.enabled:
            return self.default_response

        # Find matching endpoint
        for endpoint in self.endpoints:
            response = endpoint.get_response(request)
            if response:
                # Simulate delay
                if response.delay_ms > 0:
                    await asyncio.sleep(response.delay_ms / 1000.0)

                # Raise error if configured
                if response.error:
                    raise response.error

                return response

        # No match found
        return self.default_response

    def get_requests(
        self,
        method: str = None,
        path: str = None,
        path_pattern: str = None,
    ) -> List[MockRequest]:
        """
        Get recorded requests matching criteria.

        Args:
            method: Filter by HTTP method
            path: Filter by exact path
            path_pattern: Filter by path regex pattern

        Returns:
            List of matching requests
        """
        pattern = re.compile(path_pattern) if path_pattern else None

        return [
            req for req in self.recorded_requests
            if req.matches(method=method, path=path, path_pattern=pattern)
        ]

    def get_last_request(
        self,
        method: str = None,
        path: str = None,
    ) -> Optional[MockRequest]:
        """
        Get most recent request matching criteria.

        Args:
            method: Filter by HTTP method
            path: Filter by exact path

        Returns:
            Most recent matching request or None
        """
        requests = self.get_requests(method=method, path=path)
        return requests[-1] if requests else None

    def clear_requests(self) -> None:
        """Clear all recorded requests."""
        self.recorded_requests = []

    def reset(self) -> None:
        """Reset server to initial state."""
        self.endpoints = []
        self.recorded_requests = []
        self.state = {}
        self.enabled = True

    def set_state(self, key: str, value: Any) -> None:
        """
        Set stateful value.

        Args:
            key: State key
            value: State value
        """
        self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get stateful value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self.state.get(key, default)

    def verify_request_count(
        self,
        expected: int,
        method: str = None,
        path: str = None,
    ) -> bool:
        """
        Verify number of requests matching criteria.

        Args:
            expected: Expected number of requests
            method: Filter by HTTP method
            path: Filter by exact path

        Returns:
            True if count matches expected
        """
        actual = len(self.get_requests(method=method, path=path))
        return actual == expected

    def verify_request_order(
        self,
        expected_paths: List[str],
        method: str = None,
    ) -> bool:
        """
        Verify requests were made in expected order.

        Args:
            expected_paths: List of paths in expected order
            method: Filter by HTTP method

        Returns:
            True if order matches
        """
        requests = self.get_requests(method=method)
        actual_paths = [req.path for req in requests]
        return actual_paths == expected_paths

    def register_openapi_endpoint(
        self,
        path: str,
        method: str,
        schema: Dict[str, Any],
    ) -> MockEndpoint:
        """
        Register endpoint with OpenAPI schema-based response.

        Args:
            path: Endpoint path
            method: HTTP method
            schema: OpenAPI response schema

        Returns:
            Created MockEndpoint
        """
        # Generate mock response from schema
        mock_response = self._generate_from_schema(schema)

        return self.register_endpoint(
            method=method,
            path=path,
            response=mock_response,
        )

    def _generate_from_schema(self, schema: Dict[str, Any]) -> Any:
        """
        Generate mock data from OpenAPI schema.

        Args:
            schema: OpenAPI schema definition

        Returns:
            Generated mock data
        """
        schema_type = schema.get("type")

        if schema_type == "object":
            result = {}
            properties = schema.get("properties", {})
            for key, prop_schema in properties.items():
                result[key] = self._generate_from_schema(prop_schema)
            return result

        elif schema_type == "array":
            items_schema = schema.get("items", {})
            # Generate 1-3 items
            return [self._generate_from_schema(items_schema) for _ in range(2)]

        elif schema_type == "string":
            format_type = schema.get("format")
            if format_type == "uuid":
                return str(uuid4())
            elif format_type == "date-time":
                return datetime.utcnow().isoformat()
            elif format_type == "email":
                return "test@example.com"
            return schema.get("example", "string")

        elif schema_type == "integer":
            return schema.get("example", 42)

        elif schema_type == "number":
            return schema.get("example", 3.14)

        elif schema_type == "boolean":
            return schema.get("example", True)

        return None

    def simulate_timeout(self, duration_ms: int = 5000) -> None:
        """
        Configure all endpoints to timeout.

        Args:
            duration_ms: Timeout duration in milliseconds
        """
        for endpoint in self.endpoints:
            for response in endpoint.responses:
                response.delay_ms = duration_ms

    def simulate_errors(
        self,
        error: Exception,
        method: str = None,
        path_pattern: str = None,
    ) -> None:
        """
        Configure endpoints to raise errors.

        Args:
            error: Error to raise
            method: Only apply to this method
            path_pattern: Only apply to matching paths
        """
        pattern = re.compile(path_pattern) if path_pattern else None

        for endpoint in self.endpoints:
            if method and endpoint.matcher.method != method:
                continue
            if pattern and endpoint.matcher.path and not pattern.match(endpoint.matcher.path):
                continue

            for response in endpoint.responses:
                response.error = error

    def enable(self) -> None:
        """Enable mock server."""
        self.enabled = True

    def disable(self) -> None:
        """Disable mock server (returns default response for all requests)."""
        self.enabled = False


class MockServerContext:
    """
    Context manager for mock server lifecycle.

    Automatically sets up and tears down mock server for tests.

    Example:
        ```python
        async with MockServerContext() as server:
            server.register_endpoint("GET", "/api/test", response={"ok": True})
            # ... test code ...
        # Server automatically reset after context
        ```
    """

    def __init__(self, server: MockAPIServer = None):
        """
        Initialize context.

        Args:
            server: Existing server to use, or creates new one
        """
        self.server = server or MockAPIServer()

    async def __aenter__(self) -> MockAPIServer:
        """Enter context and return server."""
        return self.server

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset server."""
        self.server.reset()
