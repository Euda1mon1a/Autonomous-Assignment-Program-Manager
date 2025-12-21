"""
Testing utilities for the Residency Scheduler API.

This package provides comprehensive testing infrastructure including:
- Mock API server with request recording
- Response delay simulation
- Error injection
- Stateful mocking
- OpenAPI-based response generation
- Custom assertions
- Pre-built test scenarios
"""
from app.testing.assertions import (
    assert_api_response,
    assert_compliance_valid,
    assert_json_match,
    assert_no_conflicts,
    assert_schedule_valid,
)
from app.testing.factories import (
    MockResponseFactory,
    create_error_response,
    create_mock_response,
    create_paginated_response,
)
from app.testing.fixtures import (
    mock_server,
    recorded_requests,
    reset_mock_state,
    with_delay,
    with_errors,
)
from app.testing.mock_server import (
    MockAPIServer,
    MockEndpoint,
    MockRequest,
    MockResponse,
    RequestMatcher,
)
from app.testing.scenarios import (
    ACGMEComplianceScenario,
    EmergencyCoverageScenario,
    ScheduleGenerationScenario,
    SwapWorkflowScenario,
    create_scenario,
    load_scenario,
)

__all__ = [
    # Mock server
    "MockAPIServer",
    "MockEndpoint",
    "MockRequest",
    "MockResponse",
    "RequestMatcher",
    # Factories
    "MockResponseFactory",
    "create_mock_response",
    "create_error_response",
    "create_paginated_response",
    # Fixtures
    "mock_server",
    "recorded_requests",
    "reset_mock_state",
    "with_delay",
    "with_errors",
    # Assertions
    "assert_api_response",
    "assert_json_match",
    "assert_schedule_valid",
    "assert_compliance_valid",
    "assert_no_conflicts",
    # Scenarios
    "create_scenario",
    "load_scenario",
    "ScheduleGenerationScenario",
    "SwapWorkflowScenario",
    "ACGMEComplianceScenario",
    "EmergencyCoverageScenario",
]
