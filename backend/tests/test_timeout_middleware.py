"""Tests for timeout middleware."""

import asyncio

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.timeout.middleware import TimeoutMiddleware


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()

    @app.get("/quick")
    async def quick_endpoint():
        """Quick endpoint that completes immediately."""
        return {"status": "success"}

    @app.get("/slow")
    async def slow_endpoint():
        """Slow endpoint that takes time."""
        await asyncio.sleep(2.0)
        return {"status": "completed"}

    @app.get("/health")
    async def health_endpoint():
        """Health check endpoint (should be excluded from timeout)."""
        return {"status": "healthy"}

    return app


class TestTimeoutMiddleware:
    """Test suite for timeout middleware."""

    def test_quick_request_succeeds(self, app):
        """Test that quick requests complete successfully."""
        app.add_middleware(TimeoutMiddleware, default_timeout=1.0)
        client = TestClient(app)

        response = client.get("/quick")

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "X-Timeout-Limit" in response.headers
        assert "X-Timeout-Elapsed" in response.headers
        assert "X-Timeout-Remaining" in response.headers

    def test_slow_request_times_out(self, app):
        """Test that slow requests timeout."""
        app.add_middleware(TimeoutMiddleware, default_timeout=0.5)
        client = TestClient(app)

        response = client.get("/slow")

        assert response.status_code == 504
        assert "timeout" in response.json()["detail"].lower()
        assert response.json()["timeout"] == 0.5
        assert "X-Timeout-Limit" in response.headers

    def test_excluded_paths_no_timeout(self, app):
        """Test that excluded paths don't have timeout applied."""
        app.add_middleware(
            TimeoutMiddleware,
            default_timeout=0.1,
            exclude_paths=["/health"]
        )
        client = TestClient(app)

        # Health endpoint should work even with very short timeout
        response = client.get("/health")

        assert response.status_code == 200
        # Excluded paths don't get timeout headers
        assert "X-Timeout-Limit" not in response.headers

    def test_timeout_headers_disabled(self, app):
        """Test disabling timeout headers."""
        app.add_middleware(
            TimeoutMiddleware,
            default_timeout=1.0,
            timeout_header=False
        )
        client = TestClient(app)

        response = client.get("/quick")

        assert response.status_code == 200
        assert "X-Timeout-Limit" not in response.headers
        assert "X-Timeout-Elapsed" not in response.headers

    def test_timeout_headers_values(self, app):
        """Test timeout header values are correct."""
        app.add_middleware(TimeoutMiddleware, default_timeout=5.0)
        client = TestClient(app)

        response = client.get("/quick")

        assert response.status_code == 200
        assert response.headers["X-Timeout-Limit"] == "5.0"
        # Elapsed should be a small positive number
        elapsed = float(response.headers["X-Timeout-Elapsed"])
        assert 0 < elapsed < 1.0
        # Remaining should be close to 5.0
        remaining = float(response.headers["X-Timeout-Remaining"])
        assert 4.0 < remaining <= 5.0

    def test_default_exclude_paths(self, app):
        """Test default excluded paths."""
        app.add_middleware(TimeoutMiddleware, default_timeout=0.1)
        client = TestClient(app)

        # Health endpoint is excluded by default
        response = client.get("/health")
        assert response.status_code == 200

    def test_custom_timeout_value(self, app):
        """Test custom timeout value."""
        app.add_middleware(TimeoutMiddleware, default_timeout=10.0)
        client = TestClient(app)

        response = client.get("/quick")

        assert response.status_code == 200
        assert response.headers["X-Timeout-Limit"] == "10.0"


class TestTimeoutMiddlewareIntegration:
    """Integration tests for timeout middleware."""

    def test_multiple_requests(self, app):
        """Test multiple requests with different durations."""
        app.add_middleware(TimeoutMiddleware, default_timeout=1.0)
        client = TestClient(app)

        # Quick request should succeed
        response1 = client.get("/quick")
        assert response1.status_code == 200

        # Slow request should timeout
        response2 = client.get("/slow")
        assert response2.status_code == 504

        # Another quick request should succeed
        response3 = client.get("/quick")
        assert response3.status_code == 200

    def test_concurrent_requests(self, app):
        """Test concurrent requests don't interfere."""
        app.add_middleware(TimeoutMiddleware, default_timeout=1.0)

        # Note: TestClient is synchronous, so we can't truly test concurrency
        # This is a basic check that multiple requests work
        client = TestClient(app)

        responses = []
        for _ in range(5):
            response = client.get("/quick")
            responses.append(response)

        for response in responses:
            assert response.status_code == 200
            assert "X-Timeout-Limit" in response.headers
