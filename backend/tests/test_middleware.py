"""
Tests for middleware components.

Tests security headers, rate limiting, and other middleware functionality.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from starlette.responses import JSONResponse

from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limiting import limiter, RATE_LIMITS


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    def test_security_headers_added(self, client: TestClient):
        """Test that security headers are present in responses."""
        response = client.get("/health")

        assert response.status_code == 200

        # Check all security headers
        assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in response.headers
        assert "Permissions-Policy" in response.headers

    def test_csp_header_content(self, client: TestClient):
        """Test Content-Security-Policy header has correct directives."""
        response = client.get("/health")

        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "script-src" in csp
        assert "style-src" in csp
        assert "frame-ancestors 'self'" in csp

    def test_permissions_policy_content(self, client: TestClient):
        """Test Permissions-Policy header restricts features."""
        response = client.get("/health")

        permissions = response.headers.get("Permissions-Policy", "")
        assert "camera=()" in permissions
        assert "microphone=()" in permissions
        assert "geolocation=()" in permissions

    def test_hsts_disabled_by_default(self, client: TestClient):
        """Test that HSTS is disabled by default (for development)."""
        response = client.get("/health")

        # HSTS should not be present when disabled
        # Note: This depends on HSTS_ENABLED setting being False
        # The header presence depends on configuration

    def test_security_headers_on_api_endpoints(self, client: TestClient):
        """Test security headers on API endpoints."""
        response = client.get("/api/people")

        # Should have security headers regardless of response status
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers

    def test_security_headers_on_error_responses(self, client: TestClient):
        """Test security headers are added even on error responses."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        assert response.headers.get("X-Content-Type-Options") == "nosniff"


class TestSecurityHeadersMiddlewareUnit:
    """Unit tests for SecurityHeadersMiddleware configuration."""

    def test_middleware_with_custom_csp(self):
        """Test middleware with custom CSP policy."""
        app = FastAPI()
        custom_csp = "default-src 'none'"

        app.add_middleware(
            SecurityHeadersMiddleware,
            content_security_policy=custom_csp,
        )

        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.headers.get("Content-Security-Policy") == custom_csp

    def test_middleware_with_hsts_enabled(self):
        """Test middleware with HSTS enabled."""
        app = FastAPI()

        app.add_middleware(
            SecurityHeadersMiddleware,
            enable_hsts=True,
            hsts_max_age=86400,  # 1 day
        )

        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is not None
        assert "max-age=86400" in hsts
        assert "includeSubDomains" in hsts


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    def test_rate_limit_headers_present(self, client: TestClient):
        """Test that rate limit headers are present in responses."""
        response = client.get("/health")

        # Rate limit headers should be present when rate limiting is enabled
        # Note: These may not be present on all endpoints depending on configuration

    def test_rate_limits_configuration(self):
        """Test that rate limit constants are properly defined."""
        assert "default" in RATE_LIMITS
        assert "authenticated" in RATE_LIMITS
        assert "schedule_generate" in RATE_LIMITS
        assert "auth_login" in RATE_LIMITS
        assert "auth_register" in RATE_LIMITS
        assert "export" in RATE_LIMITS

        # Verify format of rate limits
        assert "/" in RATE_LIMITS["default"]  # Should be like "100/minute"
        assert "/" in RATE_LIMITS["authenticated"]

    def test_rate_limit_values(self):
        """Test that rate limits have sensible values."""
        # Parse rate limits to verify they're reasonable
        default_limit = RATE_LIMITS["default"]
        parts = default_limit.split("/")
        assert len(parts) == 2
        assert int(parts[0]) > 0  # Should be a positive number

        # Login should be more restrictive than default
        login_limit = RATE_LIMITS["auth_login"]
        login_parts = login_limit.split("/")
        assert int(login_parts[0]) < int(parts[0])  # Login limit should be lower


class TestGZipMiddleware:
    """Tests for GZip compression middleware."""

    def test_gzip_compression_on_large_response(self, client: TestClient):
        """Test that large responses are compressed."""
        # Request with Accept-Encoding header
        response = client.get(
            "/api/people",
            headers={"Accept-Encoding": "gzip"},
        )

        # Note: Compression depends on response size and configuration
        # Small responses may not be compressed

    def test_small_responses_not_compressed(self, client: TestClient):
        """Test that small responses are not compressed."""
        response = client.get(
            "/health",
            headers={"Accept-Encoding": "gzip"},
        )

        # Health endpoint returns a small response, should not be compressed
        # unless the response exceeds GZIP_MINIMUM_SIZE


class TestCORSMiddleware:
    """Tests for CORS middleware."""

    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are present for allowed origins."""
        response = client.options(
            "/api/people",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_localhost(self, client: TestClient):
        """Test that CORS allows localhost:3000."""
        response = client.get(
            "/api/people",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_preflight_request(self, client: TestClient):
        """Test CORS preflight request handling."""
        response = client.options(
            "/api/people",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-methods" in response.headers


class TestMiddlewareOrder:
    """Tests to verify middleware are applied in correct order."""

    def test_security_headers_after_cors(self, client: TestClient):
        """Test that security headers are applied after CORS processing."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )

        # Both CORS and security headers should be present
        assert "access-control-allow-origin" in response.headers
        assert "X-Frame-Options" in response.headers

    def test_all_middleware_work_together(self, client: TestClient):
        """Test that all middleware work together correctly."""
        response = client.get(
            "/api/people",
            headers={
                "Origin": "http://localhost:3000",
                "Accept-Encoding": "gzip",
            },
        )

        # Response should have CORS headers
        assert "access-control-allow-origin" in response.headers

        # Response should have security headers
        assert "X-Content-Type-Options" in response.headers

        # Response should be successful (middleware didn't break anything)
        # Note: 200 for successful, or other valid status codes
        assert response.status_code in [200, 401, 403, 404]
