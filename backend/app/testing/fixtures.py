"""
Pytest fixtures for API testing with mock server.

Provides reusable fixtures for:
- Mock server instances
- Request recording
- Response delay simulation
- Error injection
- State management
"""

from collections.abc import Generator

import pytest

from app.testing.mock_server import MockAPIServer, MockRequest


@pytest.fixture
def mock_server() -> Generator[MockAPIServer, None, None]:
    """
    Create a mock API server for testing.

    Automatically resets after each test.

    Example:
        ```python
        def test_api_call(mock_server):
            mock_server.register_endpoint(
                method="GET",
                path="/api/v1/test",
                response={"status": "ok"}
            )

            # Make request
            response = await mock_server.handle_request("GET", "/api/v1/test")
            assert response.status_code == 200
        ```
    """
    server = MockAPIServer()
    yield server
    server.reset()


@pytest.fixture
def recorded_requests(
    mock_server: MockAPIServer,
) -> Generator[list[MockRequest], None, None]:
    """
    Access recorded requests from mock server.

    Example:
        ```python
        def test_request_recording(mock_server, recorded_requests):
            await mock_server.handle_request("GET", "/api/test")

            assert len(recorded_requests) == 1
            assert recorded_requests[0].method == "GET"
        ```
    """
    yield mock_server.recorded_requests
    mock_server.clear_requests()


@pytest.fixture
def reset_mock_state(mock_server: MockAPIServer):
    """
    Reset mock server state before test.

    Use this when you need a completely clean server state.

    Example:
        ```python
        def test_clean_state(reset_mock_state, mock_server):
            # Server is guaranteed to be in clean state
            assert len(mock_server.recorded_requests) == 0
        ```
    """
    mock_server.reset()
    yield
    mock_server.reset()


@pytest.fixture
def with_delay(mock_server: MockAPIServer):
    """
    Configure mock server to simulate response delays.

    Example:
        ```python
        def test_timeout_handling(with_delay, mock_server):
            mock_server.register_endpoint(
                method="GET",
                path="/api/slow",
                response={"data": "value"},
                delay_ms=2000  # 2 second delay
            )

            # Test timeout handling
            start = time.time()
            response = await mock_server.handle_request("GET", "/api/slow")
            duration = time.time() - start
            assert duration >= 2.0
        ```
    """

    def configure_delay(delay_ms: int = 100) -> None:
        """Configure delay for all endpoints."""
        mock_server.simulate_timeout(delay_ms)

    yield configure_delay


@pytest.fixture
def with_errors(mock_server: MockAPIServer):
    """
    Configure mock server to simulate errors.

    Example:
        ```python
        def test_error_handling(with_errors, mock_server):
            mock_server.register_endpoint(
                method="POST",
                path="/api/error",
                error=ValueError("Simulated error")
            )

            with pytest.raises(ValueError):
                await mock_server.handle_request("POST", "/api/error")
        ```
    """

    def configure_errors(
        error: Exception, method: str = None, path_pattern: str = None
    ) -> None:
        """Configure error injection."""
        mock_server.simulate_errors(error, method=method, path_pattern=path_pattern)

    yield configure_errors


@pytest.fixture
def mock_people_endpoint(mock_server: MockAPIServer):
    """
    Pre-configured mock for /api/v1/people endpoint.

    Example:
        ```python
        def test_list_people(mock_people_endpoint, mock_server):
            response = await mock_server.handle_request("GET", "/api/v1/people")
            assert response.status_code == 200
            assert "people" in response.body
        ```
    """
    mock_server.register_endpoint(
        method="GET",
        path="/api/v1/people",
        response={
            "people": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Dr. Test Resident",
                    "type": "resident",
                    "email": "test.resident@hospital.org",
                    "pgy_level": 2,
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "Dr. Test Faculty",
                    "type": "faculty",
                    "email": "test.faculty@hospital.org",
                    "performs_procedures": True,
                },
            ]
        },
    )
    yield


@pytest.fixture
def mock_assignments_endpoint(mock_server: MockAPIServer):
    """
    Pre-configured mock for /api/v1/assignments endpoint.

    Example:
        ```python
        def test_list_assignments(mock_assignments_endpoint, mock_server):
            response = await mock_server.handle_request("GET", "/api/v1/assignments")
            assert response.status_code == 200
        ```
    """
    mock_server.register_endpoint(
        method="GET",
        path="/api/v1/assignments",
        response={
            "assignments": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440010",
                    "block_id": "550e8400-e29b-41d4-a716-446655440020",
                    "person_id": "550e8400-e29b-41d4-a716-446655440000",
                    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440030",
                    "role": "primary",
                }
            ],
            "total": 1,
        },
    )
    yield


@pytest.fixture
def mock_schedule_endpoint(mock_server: MockAPIServer):
    """
    Pre-configured mock for schedule generation endpoint.

    Example:
        ```python
        def test_generate_schedule(mock_schedule_endpoint, mock_server):
            response = await mock_server.handle_request(
                "POST",
                "/api/v1/schedule/generate"
            )
            assert response.status_code == 202
        ```
    """
    mock_server.register_endpoint(
        method="POST",
        path="/api/v1/schedule/generate",
        status_code=202,
        response={
            "job_id": "550e8400-e29b-41d4-a716-446655440100",
            "status": "pending",
            "message": "Schedule generation started",
        },
    )
    yield


@pytest.fixture
def mock_acgme_validation_endpoint(mock_server: MockAPIServer):
    """
    Pre-configured mock for ACGME validation endpoint.

    Example:
        ```python
        def test_acgme_validation(mock_acgme_validation_endpoint, mock_server):
            response = await mock_server.handle_request(
                "POST",
                "/api/v1/schedule/validate-acgme"
            )
            assert response.body["is_compliant"] is True
        ```
    """
    mock_server.register_endpoint(
        method="POST",
        path="/api/v1/schedule/validate-acgme",
        response={
            "is_compliant": True,
            "violations": [],
            "summary": {
                "total_hours_checked": 100,
                "max_hours_per_week": 72,
                "one_in_seven_compliant": True,
            },
        },
    )
    yield


@pytest.fixture
def mock_swap_request_endpoint(mock_server: MockAPIServer):
    """
    Pre-configured mock for swap request endpoints.

    Example:
        ```python
        def test_create_swap(mock_swap_request_endpoint, mock_server):
            response = await mock_server.handle_request(
                "POST",
                "/api/v1/swaps/requests"
            )
            assert response.status_code == 201
        ```
    """
    # List swaps
    mock_server.register_endpoint(
        method="GET",
        path="/api/v1/swaps/requests",
        response={"swap_requests": [], "total": 0},
    )

    # Create swap
    mock_server.register_endpoint(
        method="POST",
        path="/api/v1/swaps/requests",
        status_code=201,
        response={
            "id": "550e8400-e29b-41d4-a716-446655440200",
            "status": "pending",
            "swap_type": "one_to_one",
        },
    )

    # Execute swap
    mock_server.register_endpoint(
        method="POST",
        path_pattern=r"/api/v1/swaps/requests/.*/execute",
        response={
            "id": "550e8400-e29b-41d4-a716-446655440200",
            "status": "completed",
            "executed_at": "2025-12-20T12:00:00Z",
        },
    )
    yield


@pytest.fixture
def mock_resilience_endpoint(mock_server: MockAPIServer):
    """
    Pre-configured mock for resilience health check endpoint.

    Example:
        ```python
        def test_resilience_health(mock_resilience_endpoint, mock_server):
            response = await mock_server.handle_request(
                "GET",
                "/health/resilience"
            )
            assert response.body["status"] == "operational"
        ```
    """
    mock_server.register_endpoint(
        method="GET",
        path="/health/resilience",
        response={
            "status": "operational",
            "metrics_enabled": True,
            "components": [
                "utilization_monitor",
                "defense_in_depth",
                "contingency_analyzer",
                "fallback_scheduler",
                "sacrifice_hierarchy",
            ],
        },
    )
    yield


@pytest.fixture
def mock_auth_endpoint(mock_server: MockAPIServer):
    """
    Pre-configured mock for authentication endpoints.

    Example:
        ```python
        def test_login(mock_auth_endpoint, mock_server):
            response = await mock_server.handle_request(
                "POST",
                "/api/auth/login/json",
                body={"username": "test", "password": "test123"}
            )
            assert "access_token" in response.body
        ```
    """
    mock_server.register_endpoint(
        method="POST",
        path="/api/auth/login/json",
        response={
            "access_token": "mock.jwt.token",
            "token_type": "bearer",
        },
    )

    mock_server.register_endpoint(
        method="GET",
        path="/api/auth/me",
        response={
            "id": "550e8400-e29b-41d4-a716-446655440300",
            "username": "testuser",
            "email": "test@example.com",
            "role": "admin",
            "is_active": True,
        },
    )
    yield
