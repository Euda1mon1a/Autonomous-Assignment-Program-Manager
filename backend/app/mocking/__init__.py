"""
API mocking service for testing in the Residency Scheduler backend.

This package provides a comprehensive mocking infrastructure for testing API
integrations, external services, and complex workflows. It extends beyond basic
HTTP mocking to provide:

- Advanced request matching with custom predicates
- Dynamic response generation with callbacks
- Scenario-based testing with state management
- Response templates and factories
- Error injection and fault simulation
- Performance simulation (delays, rate limits)
- Request verification and assertions

The mocking service is designed to work seamlessly with FastAPI and async
testing patterns used throughout the application.

Example:
    ```python
    from app.mocking import MockServer, MockScenario, ResponseTemplate

    ***REMOVED*** Create mock server
    server = MockServer()

    ***REMOVED*** Register simple endpoint
    server.register(
        method="GET",
        path="/api/external/users/123",
        response={"id": "123", "name": "John Doe"}
    )

    ***REMOVED*** Register dynamic endpoint
    server.register(
        method="POST",
        path="/api/external/events",
        response_fn=lambda req: {"id": generate_id(), "data": req.body}
    )

    ***REMOVED*** Load scenario
    scenario = MockScenario.from_file("scenarios/acgme_compliance.json")
    server.load_scenario(scenario)

    ***REMOVED*** Verify requests
    assert server.verify_called("/api/external/users/123", times=1)
    ```

Key Classes:
    - MockServer: Main mocking server implementation
    - MockScenario: Predefined test scenarios with state
    - ResponseTemplate: Reusable response patterns
    - RequestMatcher: Advanced request matching
    - MockEndpoint: Endpoint configuration
    - MockVerifier: Request verification utilities
"""

from app.mocking.mock_server import (
    DynamicResponseFn,
    ErrorInjector,
    MockEndpoint,
    MockRequest,
    MockResponse,
    MockScenario,
    MockServer,
    MockVerifier,
    RequestMatcher,
    RequestPredicate,
    ResponseDelaySimulator,
    ResponseTemplate,
    ScenarioState,
)

__all__ = [
    ***REMOVED*** Core mocking
    "MockServer",
    "MockEndpoint",
    "MockRequest",
    "MockResponse",
    ***REMOVED*** Request matching
    "RequestMatcher",
    "RequestPredicate",
    ***REMOVED*** Response generation
    "ResponseTemplate",
    "DynamicResponseFn",
    ***REMOVED*** Scenarios
    "MockScenario",
    "ScenarioState",
    ***REMOVED*** Utilities
    "MockVerifier",
    "ErrorInjector",
    "ResponseDelaySimulator",
]
