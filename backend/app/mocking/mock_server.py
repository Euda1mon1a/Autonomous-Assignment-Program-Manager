r"""
API mocking server for comprehensive testing support.

This module provides a sophisticated mocking framework for testing API
integrations and external dependencies. It supports:

- Pattern-based request matching (path, method, headers, query params, body)
- Dynamic response generation using callbacks
- Response delay simulation for performance testing
- Error injection for resilience testing
- Request recording and verification
- Scenario-based testing with state management
- Response templates for reusable patterns
- Webhook simulation
- Rate limiting simulation

Architecture:
    The mock server follows a matcher-response pattern where:
    1. Incoming requests are matched against registered endpoints
    2. Matchers use predicates to determine if a request matches
    3. Matched requests generate responses using templates or callbacks
    4. All requests are recorded for verification
    5. Scenarios manage complex multi-step interactions

Example:
    ```python
    server = MockServer()

    # Basic endpoint
    server.register(
        method="GET",
        path="/users/123",
        response={"id": "123", "name": "Test User"}
    )

    # Dynamic response
    server.register(
        method="POST",
        path_pattern=r"/users/\d+/notify",
        response_fn=lambda req: {
            "notification_id": generate_id(),
            "user_id": req.path_params.get("user_id"),
            "sent": True
        },
        delay_ms=100
    )

    # Error injection
    server.inject_error(
        path_pattern=r"/api/.*",
        error=ConnectionError("Network timeout"),
        probability=0.1
    )

    # Verify
    requests = server.get_requests(method="POST")
    assert len(requests) == 1
    ```
"""

import asyncio
import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class HTTPMethod(str, Enum):
    """HTTP methods supported by the mock server."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


# Type alias for dynamic response functions
DynamicResponseFn = Callable[["MockRequest"], dict[str, Any] | Any]


# Type alias for request predicates
RequestPredicate = Callable[["MockRequest"], bool]


@dataclass
class MockRequest:
    """
    Represents a recorded HTTP request.

    Captures all relevant details of a request for matching, verification,
    and debugging purposes.

    Attributes:
        id: Unique request identifier
        method: HTTP method (GET, POST, etc.)
        path: Request path (e.g., "/api/v1/users")
        path_params: Path parameters extracted from pattern matching
        query_params: Query string parameters
        headers: Request headers (case-insensitive)
        body: Request body (parsed JSON or raw)
        timestamp: When the request was received
        metadata: Additional metadata for custom use
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    method: str = ""
    path: str = ""
    path_params: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: Any | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_header(self, name: str, default: str = None) -> str | None:
        """
        Get header value (case-insensitive).

        Args:
            name: Header name
            default: Default value if not found

        Returns:
            Header value or default
        """
        name_lower = name.lower()
        for key, value in self.headers.items():
            if key.lower() == name_lower:
                return value
        return default

    def get_json(self) -> dict[str, Any] | None:
        """
        Get request body as JSON.

        Returns:
            Parsed JSON body or None if body is not JSON
        """
        if isinstance(self.body, dict):
            return self.body
        if isinstance(self.body, str):
            try:
                return json.loads(self.body)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def matches_predicate(self, predicate: RequestPredicate) -> bool:
        """
        Check if request matches a custom predicate.

        Args:
            predicate: Callable that takes MockRequest and returns bool

        Returns:
            True if predicate returns True
        """
        try:
            return predicate(self)
        except Exception as e:
            logger.warning(f"Predicate evaluation failed: {e}")
            return False


@dataclass
class MockResponse:
    """
    Represents a mock HTTP response.

    Defines the response to return for matched requests, including support
    for delays, errors, and dynamic content generation.

    Attributes:
        status_code: HTTP status code
        body: Response body (dict, list, str, or None)
        headers: Response headers
        delay_ms: Simulated delay in milliseconds
        error: Exception to raise instead of returning response
        is_dynamic: Whether this response was generated dynamically
    """

    status_code: int = 200
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    delay_ms: int = 0
    error: Exception | None = None
    is_dynamic: bool = False

    def to_dict(self) -> dict[str, Any]:
        """
        Convert response to dictionary format.

        Returns:
            Dictionary representation of response
        """
        return {
            "status_code": self.status_code,
            "body": self.body,
            "headers": self.headers,
        }

    def add_header(self, name: str, value: str) -> "MockResponse":
        """
        Add a header to the response (fluent interface).

        Args:
            name: Header name
            value: Header value

        Returns:
            Self for chaining
        """
        self.headers[name] = value
        return self

    def with_delay(self, delay_ms: int) -> "MockResponse":
        """
        Set response delay (fluent interface).

        Args:
            delay_ms: Delay in milliseconds

        Returns:
            Self for chaining
        """
        self.delay_ms = delay_ms
        return self


class RequestMatcher:
    r"""
    Flexible request matching with support for patterns and predicates.

    Matches requests based on method, path (exact or pattern), headers,
    query parameters, body content, and custom predicates.

    The matcher uses a combination of exact matching and pattern matching:
    - Method: Exact match (if specified)
    - Path: Exact match OR regex pattern match
    - Headers: All specified headers must match (subset matching)
    - Query params: All specified params must match (subset matching)
    - Body: JSON subset matching or custom predicate
    - Custom predicate: Arbitrary Python function

    Example:
        ```python
        # Match exact path
        matcher = RequestMatcher(method="GET", path="/users/123")

        # Match pattern
        matcher = RequestMatcher(
            method="POST",
            path_pattern=r"/users/\d+/notify"
        )

        # Match with headers
        matcher = RequestMatcher(
            path="/api/data",
            headers={"Authorization": "Bearer token123"}
        )

        # Match with custom predicate
        matcher = RequestMatcher(
            method="POST",
            predicate=lambda req: req.get_json().get("type") == "urgent"
        )
        ```
    """

    def __init__(
        self,
        method: str | None = None,
        path: str | None = None,
        path_pattern: str | None = None,
        headers: dict[str, str] | None = None,
        query_params: dict[str, Any] | None = None,
        body_contains: dict[str, Any] | None = None,
        predicate: RequestPredicate | None = None,
    ):
        """
        Initialize request matcher.

        Args:
            method: HTTP method to match (exact)
            path: Exact path to match
            path_pattern: Regex pattern for path matching
            headers: Headers that must be present (subset match)
            query_params: Query params that must match (subset match)
            body_contains: Key-value pairs that must be in body
            predicate: Custom matching function
        """
        self.method = method.upper() if method else None
        self.path = path
        self.path_pattern = re.compile(path_pattern) if path_pattern else None
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self.query_params = query_params or {}
        self.body_contains = body_contains or {}
        self.predicate = predicate

    def matches(self, request: MockRequest) -> bool:
        """
        Check if request matches this matcher.

        Args:
            request: Request to check

        Returns:
            True if request matches all criteria
        """
        # Check method
        if self.method and request.method.upper() != self.method:
            return False

        # Check exact path
        if self.path and request.path != self.path:
            return False

        # Check path pattern
        if self.path_pattern and not self.path_pattern.match(request.path):
            return False

        # Check headers (subset matching)
        for key, value in self.headers.items():
            request_value = request.get_header(key)
            if request_value != value:
                return False

        # Check query params (subset matching)
        for key, value in self.query_params.items():
            if request.query_params.get(key) != value:
                return False

        # Check body contains (subset matching)
        if self.body_contains and request.body:
            body_json = request.get_json()
            if not body_json:
                return False
            for key, value in self.body_contains.items():
                if body_json.get(key) != value:
                    return False

        # Check custom predicate
        if self.predicate and not request.matches_predicate(self.predicate):
            return False

        return True

    def extract_path_params(self, request: MockRequest) -> dict[str, str]:
        """
        Extract path parameters from pattern match.

        Args:
            request: Request to extract from

        Returns:
            Dictionary of extracted parameters
        """
        if not self.path_pattern:
            return {}

        match = self.path_pattern.match(request.path)
        if not match:
            return {}

        return match.groupdict()


class ResponseTemplate:
    """
    Reusable response template with variable substitution.

    Templates allow defining response patterns that can be customized
    with request-specific data.

    Example:
        ```python
        template = ResponseTemplate(
            status_code=200,
            body_template={
                "user_id": "${path_params.user_id}",
                "action": "created",
                "timestamp": "${now}"
            }
        )

        response = template.generate(request)
        ```
    """

    def __init__(
        self,
        status_code: int = 200,
        body_template: Any = None,
        headers: dict[str, str] = None,
        delay_ms: int = 0,
    ):
        """
        Initialize response template.

        Args:
            status_code: HTTP status code
            body_template: Response body with ${variable} placeholders
            headers: Response headers
            delay_ms: Response delay in milliseconds
        """
        self.status_code = status_code
        self.body_template = body_template
        self.headers = headers or {}
        self.delay_ms = delay_ms

    def generate(
        self,
        request: MockRequest,
        context: dict[str, Any] = None,
    ) -> MockResponse:
        """
        Generate response from template.

        Args:
            request: Request that triggered this response
            context: Additional context for substitution

        Returns:
            Generated MockResponse
        """
        # Build substitution context
        sub_context = {
            "request_id": request.id,
            "method": request.method,
            "path": request.path,
            "path_params": request.path_params,
            "query_params": request.query_params,
            "now": datetime.utcnow().isoformat(),
            "timestamp": int(time.time()),
            "uuid": str(uuid4()),
            **(context or {}),
        }

        # Substitute variables in body
        body = self._substitute(self.body_template, sub_context)

        return MockResponse(
            status_code=self.status_code,
            body=body,
            headers=self.headers.copy(),
            delay_ms=self.delay_ms,
            is_dynamic=True,
        )

    def _substitute(self, obj: Any, context: dict[str, Any]) -> Any:
        """Recursively substitute variables in object."""
        if isinstance(obj, str):
            # Replace ${var} and ${path.to.var}
            import re

            pattern = re.compile(r"\$\{([^}]+)\}")

            def replacer(match):
                path = match.group(1).split(".")
                value = context
                try:
                    for key in path:
                        value = value[key]
                    return str(value)
                except (KeyError, TypeError):
                    return match.group(0)  # Keep original if not found

            return pattern.sub(replacer, obj)

        elif isinstance(obj, dict):
            return {k: self._substitute(v, context) for k, v in obj.items()}

        elif isinstance(obj, list):
            return [self._substitute(item, context) for item in obj]

        else:
            return obj


@dataclass
class MockEndpoint:
    """
    Mock endpoint configuration.

    Represents a registered endpoint with its matcher and response strategy.
    Supports multiple responses for stateful behavior.

    Attributes:
        matcher: Request matcher for this endpoint
        responses: List of responses (for stateful/sequential behavior)
        response_fn: Dynamic response generator function
        template: Response template
        stateful: Whether to cycle through responses
        current_index: Current response index (for stateful)
        call_count: Number of times endpoint was called
        enabled: Whether endpoint is active
    """

    matcher: RequestMatcher
    responses: list[MockResponse] = field(default_factory=list)
    response_fn: DynamicResponseFn | None = None
    template: ResponseTemplate | None = None
    stateful: bool = False
    current_index: int = 0
    call_count: int = 0
    enabled: bool = True

    def get_response(self, request: MockRequest) -> MockResponse | None:
        """
        Get response for this request.

        Args:
            request: Request to respond to

        Returns:
            MockResponse if matcher matches and endpoint is enabled
        """
        if not self.enabled:
            return None

        if not self.matcher.matches(request):
            return None

        # Extract path params
        request.path_params = self.matcher.extract_path_params(request)

        self.call_count += 1

        # Dynamic response function
        if self.response_fn:
            try:
                body = self.response_fn(request)
                return MockResponse(
                    status_code=200,
                    body=body,
                    is_dynamic=True,
                )
            except Exception as e:
                logger.error(f"Dynamic response function failed: {e}")
                return MockResponse(
                    status_code=500,
                    body={"error": "Internal mock server error"},
                )

        # Template-based response
        if self.template:
            return self.template.generate(request)

        # Static responses
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


@dataclass
class ScenarioState:
    """
    State management for mock scenarios.

    Tracks state across multiple requests in a scenario.

    Attributes:
        name: Scenario name
        state: State dictionary
        step: Current step number
        metadata: Additional metadata
    """

    name: str
    state: dict[str, Any] = field(default_factory=dict)
    step: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set state value."""
        self.state[key] = value

    def increment_step(self) -> int:
        """Increment and return step counter."""
        self.step += 1
        return self.step

    def reset(self) -> None:
        """Reset state."""
        self.state = {}
        self.step = 0


class MockScenario:
    """
    Pre-configured test scenario with multiple endpoints and state.

    Scenarios allow loading complex multi-step test setups from
    configuration files or dictionaries.

    Example:
        ```python
        scenario = MockScenario(
            name="user_registration",
            endpoints=[
                {
                    "method": "POST",
                    "path": "/users",
                    "response": {"id": "123", "status": "created"}
                },
                {
                    "method": "GET",
                    "path": "/users/123",
                    "response": {"id": "123", "verified": True}
                }
            ]
        )

        server.load_scenario(scenario)
        ```
    """

    def __init__(
        self,
        name: str,
        endpoints: list[dict[str, Any]] = None,
        initial_state: dict[str, Any] = None,
    ):
        """
        Initialize scenario.

        Args:
            name: Scenario name
            endpoints: List of endpoint configurations
            initial_state: Initial state values
        """
        self.name = name
        self.endpoint_configs = endpoints or []
        self.state = ScenarioState(name=name, state=initial_state or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MockScenario":
        """
        Create scenario from dictionary.

        Args:
            data: Scenario configuration

        Returns:
            MockScenario instance
        """
        return cls(
            name=data.get("name", "unnamed"),
            endpoints=data.get("endpoints", []),
            initial_state=data.get("initial_state", {}),
        )

    @classmethod
    def from_file(cls, filepath: str) -> "MockScenario":
        """
        Load scenario from JSON file.

        Args:
            filepath: Path to scenario file

        Returns:
            MockScenario instance
        """
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)

    def reset(self) -> None:
        """Reset scenario state."""
        self.state.reset()


class ErrorInjector:
    """
    Error injection for resilience testing.

    Allows injecting errors probabilistically or conditionally.

    Example:
        ```python
        injector = ErrorInjector()
        injector.add_error(
            path_pattern=r"/api/.*",
            error=ConnectionError("Simulated network failure"),
            probability=0.1  # 10% of requests
        )
        ```
    """

    def __init__(self):
        """Initialize error injector."""
        self.error_rules: list[dict[str, Any]] = []

    def add_error(
        self,
        error: Exception,
        method: str = None,
        path_pattern: str = None,
        probability: float = 1.0,
        predicate: RequestPredicate = None,
    ) -> None:
        """
        Add error injection rule.

        Args:
            error: Exception to raise
            method: Only apply to this method
            path_pattern: Only apply to matching paths
            probability: Probability of error (0.0 to 1.0)
            predicate: Custom predicate for conditional errors
        """
        self.error_rules.append(
            {
                "error": error,
                "method": method,
                "path_pattern": re.compile(path_pattern) if path_pattern else None,
                "probability": probability,
                "predicate": predicate,
            }
        )

    def should_inject_error(self, request: MockRequest) -> Exception | None:
        """
        Check if error should be injected for request.

        Args:
            request: Request to check

        Returns:
            Exception to raise, or None
        """
        import random

        for rule in self.error_rules:
            # Check method
            if rule["method"] and request.method != rule["method"]:
                continue

            # Check path pattern
            if rule["path_pattern"] and not rule["path_pattern"].match(request.path):
                continue

            # Check predicate
            if rule["predicate"] and not request.matches_predicate(rule["predicate"]):
                continue

            # Check probability
            if random.random() <= rule["probability"]:
                return rule["error"]

        return None

    def clear(self) -> None:
        """Clear all error rules."""
        self.error_rules = []


class ResponseDelaySimulator:
    """
    Response delay simulation for performance testing.

    Simulates network latency and slow responses.

    Example:
        ```python
        simulator = ResponseDelaySimulator()
        simulator.add_delay(
            path_pattern=r"/api/slow/.*",
            delay_ms=2000  # 2 seconds
        )
        ```
    """

    def __init__(self):
        """Initialize delay simulator."""
        self.delay_rules: list[dict[str, Any]] = []

    def add_delay(
        self,
        delay_ms: int,
        method: str = None,
        path_pattern: str = None,
        predicate: RequestPredicate = None,
    ) -> None:
        """
        Add delay rule.

        Args:
            delay_ms: Delay in milliseconds
            method: Only apply to this method
            path_pattern: Only apply to matching paths
            predicate: Custom predicate for conditional delays
        """
        self.delay_rules.append(
            {
                "delay_ms": delay_ms,
                "method": method,
                "path_pattern": re.compile(path_pattern) if path_pattern else None,
                "predicate": predicate,
            }
        )

    def get_delay(self, request: MockRequest) -> int:
        """
        Get delay for request.

        Args:
            request: Request to check

        Returns:
            Delay in milliseconds
        """
        total_delay = 0

        for rule in self.delay_rules:
            # Check method
            if rule["method"] and request.method != rule["method"]:
                continue

            # Check path pattern
            if rule["path_pattern"] and not rule["path_pattern"].match(request.path):
                continue

            # Check predicate
            if rule["predicate"] and not request.matches_predicate(rule["predicate"]):
                continue

            total_delay += rule["delay_ms"]

        return total_delay

    def clear(self) -> None:
        """Clear all delay rules."""
        self.delay_rules = []


class MockVerifier:
    """
    Request verification utilities.

    Provides assertion helpers for verifying mock server interactions.

    Example:
        ```python
        verifier = MockVerifier(server)
        verifier.assert_called("/api/users", times=1)
        verifier.assert_called_with(
            "/api/users/123",
            method="GET",
            headers={"Authorization": "Bearer token"}
        )
        ```
    """

    def __init__(self, server: "MockServer"):
        """
        Initialize verifier.

        Args:
            server: Mock server to verify
        """
        self.server = server

    def assert_called(
        self,
        path: str,
        method: str = None,
        times: int = None,
        at_least: int = None,
        at_most: int = None,
    ) -> None:
        """
        Assert endpoint was called.

        Args:
            path: Path to verify
            method: HTTP method
            times: Exact number of calls
            at_least: Minimum number of calls
            at_most: Maximum number of calls

        Raises:
            AssertionError: If assertion fails
        """
        requests = self.server.get_requests(method=method, path=path)
        actual = len(requests)

        if times is not None:
            assert actual == times, f"Expected {times} calls to {path}, got {actual}"

        if at_least is not None:
            assert (
                actual >= at_least
            ), f"Expected at least {at_least} calls to {path}, got {actual}"

        if at_most is not None:
            assert (
                actual <= at_most
            ), f"Expected at most {at_most} calls to {path}, got {actual}"

    def assert_called_with(
        self,
        path: str,
        method: str = None,
        headers: dict[str, str] = None,
        query_params: dict[str, Any] = None,
        body_contains: dict[str, Any] = None,
    ) -> None:
        """
        Assert endpoint was called with specific parameters.

        Args:
            path: Path to verify
            method: HTTP method
            headers: Headers that must be present
            query_params: Query params that must match
            body_contains: Body fields that must match

        Raises:
            AssertionError: If no matching request found
        """
        requests = self.server.get_requests(method=method, path=path)

        for request in requests:
            # Check headers
            if headers:
                headers_match = all(
                    request.get_header(k) == v for k, v in headers.items()
                )
                if not headers_match:
                    continue

            # Check query params
            if query_params:
                params_match = all(
                    request.query_params.get(k) == v for k, v in query_params.items()
                )
                if not params_match:
                    continue

            # Check body
            if body_contains:
                body_json = request.get_json()
                if not body_json:
                    continue
                body_match = all(
                    body_json.get(k) == v for k, v in body_contains.items()
                )
                if not body_match:
                    continue

            # Found matching request
            return

        # No matching request
        raise AssertionError(f"No matching request found for {method} {path}")

    def assert_not_called(self, path: str, method: str = None) -> None:
        """
        Assert endpoint was not called.

        Args:
            path: Path to verify
            method: HTTP method

        Raises:
            AssertionError: If endpoint was called
        """
        self.assert_called(path, method=method, times=0)


class MockServer:
    r"""
    Comprehensive mock API server for testing.

    The MockServer provides a complete mocking solution for testing API
    integrations and external dependencies. It supports:

    - Flexible request matching (exact, pattern, predicate)
    - Dynamic response generation
    - Response templates
    - Error injection
    - Response delay simulation
    - Request recording and verification
    - Scenario-based testing
    - Stateful behavior

    Example:
        ```python
        # Create server
        server = MockServer()

        # Register endpoints
        server.register(
            method="GET",
            path="/api/users/123",
            response={"id": "123", "name": "Test User"}
        )

        server.register(
            method="POST",
            path_pattern=r"/api/users/\d+/notify",
            response_fn=lambda req: {
                "notification_id": str(uuid4()),
                "sent": True
            }
        )

        # Handle requests
        response = await server.handle_request("GET", "/api/users/123")

        # Verify
        assert server.verify_request_count(1, path="/api/users/123")
        ```
    """

    def __init__(self):
        """Initialize mock server."""
        self.endpoints: list[MockEndpoint] = []
        self.recorded_requests: list[MockRequest] = []
        self.scenarios: dict[str, MockScenario] = {}
        self.error_injector = ErrorInjector()
        self.delay_simulator = ResponseDelaySimulator()
        self.verifier = MockVerifier(self)
        self.enabled = True
        self.default_response = MockResponse(
            status_code=404, body={"detail": "Mock endpoint not configured"}
        )

    def register(
        self,
        method: str,
        path: str = None,
        path_pattern: str = None,
        response: Any = None,
        response_fn: DynamicResponseFn = None,
        template: ResponseTemplate = None,
        status_code: int = 200,
        headers: dict[str, str] = None,
        delay_ms: int = 0,
        error: Exception = None,
        stateful: bool = False,
        responses: list[MockResponse] = None,
        predicate: RequestPredicate = None,
    ) -> MockEndpoint:
        """
        Register a mock endpoint.

        Args:
            method: HTTP method
            path: Exact path to match
            path_pattern: Regex pattern for path
            response: Static response body
            response_fn: Dynamic response generator
            template: Response template
            status_code: HTTP status code
            headers: Response headers
            delay_ms: Response delay in milliseconds
            error: Error to raise
            stateful: Whether to cycle through multiple responses
            responses: List of responses for stateful endpoints
            predicate: Custom request matching predicate

        Returns:
            Created MockEndpoint
        """
        matcher = RequestMatcher(
            method=method,
            path=path,
            path_pattern=path_pattern,
            predicate=predicate,
        )

        # Build responses list
        if responses:
            mock_responses = responses
        elif response is not None or error is not None:
            mock_responses = [
                MockResponse(
                    status_code=status_code,
                    body=response,
                    headers=headers or {},
                    delay_ms=delay_ms,
                    error=error,
                )
            ]
        else:
            mock_responses = []

        endpoint = MockEndpoint(
            matcher=matcher,
            responses=mock_responses,
            response_fn=response_fn,
            template=template,
            stateful=stateful,
        )

        self.endpoints.append(endpoint)
        return endpoint

    async def handle_request(
        self,
        method: str,
        path: str,
        query_params: dict[str, Any] = None,
        headers: dict[str, str] = None,
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

        Raises:
            Exception: If error injection is configured
        """
        # Create request record
        request = MockRequest(
            method=method.upper(),
            path=path,
            query_params=query_params or {},
            headers=headers or {},
            body=body,
        )

        # Record request
        self.recorded_requests.append(request)

        if not self.enabled:
            return self.default_response

        # Check error injection
        error = self.error_injector.should_inject_error(request)
        if error:
            raise error

        # Find matching endpoint
        for endpoint in self.endpoints:
            response = endpoint.get_response(request)
            if response:
                # Apply delay simulation
                base_delay = response.delay_ms
                additional_delay = self.delay_simulator.get_delay(request)
                total_delay = base_delay + additional_delay

                if total_delay > 0:
                    await asyncio.sleep(total_delay / 1000.0)

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
    ) -> list[MockRequest]:
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

        result = []
        for req in self.recorded_requests:
            if method and req.method.upper() != method.upper():
                continue
            if path and req.path != path:
                continue
            if pattern and not pattern.match(req.path):
                continue
            result.append(req)

        return result

    def get_last_request(
        self,
        method: str = None,
        path: str = None,
    ) -> MockRequest | None:
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

    def clear_requests(self) -> None:
        """Clear all recorded requests."""
        self.recorded_requests = []

    def reset(self) -> None:
        """Reset server to initial state."""
        self.endpoints = []
        self.recorded_requests = []
        self.scenarios = {}
        self.error_injector.clear()
        self.delay_simulator.clear()
        self.enabled = True

    def load_scenario(self, scenario: MockScenario) -> None:
        """
        Load a test scenario.

        Args:
            scenario: Scenario to load
        """
        self.scenarios[scenario.name] = scenario

        # Register endpoints from scenario
        for endpoint_config in scenario.endpoint_configs:
            self.register(**endpoint_config)

    def get_scenario(self, name: str) -> MockScenario | None:
        """
        Get loaded scenario by name.

        Args:
            name: Scenario name

        Returns:
            MockScenario or None
        """
        return self.scenarios.get(name)

    def inject_error(
        self,
        error: Exception,
        method: str = None,
        path_pattern: str = None,
        probability: float = 1.0,
    ) -> None:
        """
        Inject error for matching requests.

        Args:
            error: Exception to raise
            method: Only apply to this method
            path_pattern: Only apply to matching paths
            probability: Probability of error (0.0 to 1.0)
        """
        self.error_injector.add_error(
            error=error,
            method=method,
            path_pattern=path_pattern,
            probability=probability,
        )

    def simulate_delay(
        self,
        delay_ms: int,
        method: str = None,
        path_pattern: str = None,
    ) -> None:
        """
        Simulate response delay for matching requests.

        Args:
            delay_ms: Delay in milliseconds
            method: Only apply to this method
            path_pattern: Only apply to matching paths
        """
        self.delay_simulator.add_delay(
            delay_ms=delay_ms,
            method=method,
            path_pattern=path_pattern,
        )

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
            server.register("GET", "/api/test", response={"ok": True})
            response = await server.handle_request("GET", "/api/test")
            assert response.status_code == 200
        # Server automatically reset after context
        ```
    """

    def __init__(self, server: MockServer = None):
        """
        Initialize context.

        Args:
            server: Existing server to use, or creates new one
        """
        self.server = server or MockServer()

    async def __aenter__(self) -> MockServer:
        """Enter context and return server."""
        return self.server

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset server."""
        self.server.reset()
