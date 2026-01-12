"""Tests for API client."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

import httpx

from scheduler_mcp.api_client import (
    APIConfig,
    SchedulerAPIClient,
    get_api_client,
    close_api_client,
)


class TestAPIConfig:
    """Test API configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = APIConfig()
        assert config.base_url == "http://localhost:8000"
        assert config.timeout == 30.0
        assert config.api_prefix == "/api/v1"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = APIConfig(
            base_url="http://example.com:9000",
            timeout=60.0,
            api_prefix="/api/v2",
        )
        assert config.base_url == "http://example.com:9000"
        assert config.timeout == 60.0
        assert config.api_prefix == "/api/v2"


class TestSchedulerAPIClient:
    """Test SchedulerAPIClient functionality."""

    async def test_context_manager_initialization(self):
        """Test client initialization via context manager."""
        async with SchedulerAPIClient() as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    async def test_context_manager_cleanup(self):
        """Test client cleanup on context exit."""
        client = SchedulerAPIClient()
        async with client:
            assert client._client is not None
        # Client should be closed after exiting context
        assert client._client is not None  # Still exists but is closed

    async def test_client_property_raises_when_not_initialized(self):
        """Test client property raises when not initialized."""
        client = SchedulerAPIClient()
        with pytest.raises(RuntimeError, match="Client not initialized"):
            _ = client.client

    async def test_health_check_success(self, mock_httpx_client):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        async with SchedulerAPIClient() as client:
            result = await client.health_check()
            assert result is True
            mock_httpx_client.request.assert_awaited_once_with("GET", "/health")

    async def test_health_check_failure(self, mock_httpx_client):
        """Test health check returns False on request error."""
        request = httpx.Request("GET", "http://test/health")
        mock_httpx_client.request = AsyncMock(
            side_effect=httpx.RequestError("Connection failed", request=request)
        )

        async with SchedulerAPIClient() as client:
            with patch("scheduler_mcp.api_client.asyncio.sleep", new=AsyncMock()):
                result = await client.health_check()
                assert result is False

    async def test_validate_schedule(self, mock_httpx_client):
        """Test schedule validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "violations": [],
            "summary": {"total_checks": 5, "passed": 5, "failed": 0},
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        async with SchedulerAPIClient() as client:
            result = await client.validate_schedule(
                start_date="2024-01-01", end_date="2024-01-31"
            )
            assert result["valid"] is True
            assert result["violations"] == []
            mock_httpx_client.request.assert_awaited_once_with(
                "GET",
                f"{client.config.api_prefix}/schedule/validate",
                params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
            )

    async def test_get_conflicts(self, mock_httpx_client):
        """Test getting schedule conflicts."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "conflicts": [{"type": "overlap", "person_id": "test-123"}]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        async with SchedulerAPIClient() as client:
            client._token = "test-token"
            result = await client.get_conflicts(
                start_date="2024-01-01", end_date="2024-01-31"
            )
            assert "conflicts" in result
            assert len(result["conflicts"]) == 1
            mock_httpx_client.request.assert_awaited_once_with(
                "GET",
                f"{client.config.api_prefix}/conflicts/analyze",
                headers={"Authorization": "Bearer test-token"},
                params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
            )

    async def test_get_swap_candidates(self, mock_httpx_client):
        """Test getting swap candidates."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {"person_id": "fac-001", "compatibility_score": 0.95},
                {"person_id": "fac-002", "compatibility_score": 0.80},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        async with SchedulerAPIClient() as client:
            client._token = "test-token"
            result = await client.get_swap_candidates(
                person_id="fac-123", block_id="block-456"
            )
            assert "candidates" in result
            assert len(result["candidates"]) == 2
            mock_httpx_client.request.assert_awaited_once_with(
                "POST",
                f"{client.config.api_prefix}/schedule/swaps/candidates",
                headers={"Authorization": "Bearer test-token"},
                json={
                    "person_id": "fac-123",
                    "assignment_id": None,
                    "block_id": "block-456",
                    "max_candidates": 10,
                },
            )

    async def test_run_contingency_analysis(self, mock_httpx_client):
        """Test running contingency analysis."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "scenario": "n-1",
            "status": "YELLOW",
            "coverage_percentage": 85.5,
            "recommendations": ["Add backup coverage for clinic"],
        }
        mock_response.raise_for_status = Mock()
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        async with SchedulerAPIClient() as client:
            client._token = "test-token"
            result = await client.run_contingency_analysis(
                scenario="n-1",
                affected_ids=["fac-001"],
                start_date="2024-01-01",
                end_date="2024-01-31",
            )
            assert result["scenario"] == "n-1"
            assert result["status"] == "YELLOW"
            mock_httpx_client.request.assert_awaited_once_with(
                "GET",
                f"{client.config.api_prefix}/resilience/vulnerability",
                headers={"Authorization": "Bearer test-token"},
                params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
            )

    async def test_http_error_handling(self, mock_httpx_client):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        mock_httpx_client.request = AsyncMock(return_value=mock_response)

        async with SchedulerAPIClient() as client:
            with patch("scheduler_mcp.api_client.asyncio.sleep", new=AsyncMock()):
                with pytest.raises(httpx.HTTPStatusError):
                    await client.validate_schedule(
                        start_date="2024-01-01", end_date="2024-01-31"
                    )

    async def test_request_with_retry_refreshes_token_on_401(self):
        """Test token refresh when a request returns 401."""
        request = httpx.Request("GET", "http://test/health")
        response_unauthorized = httpx.Response(401, request=request)
        response_ok = httpx.Response(200, request=request)
        login_request = httpx.Request("POST", "http://test/api/v1/auth/login/json")
        login_response = httpx.Response(
            200, request=login_request, json={"access_token": "new-token"}
        )

        client = SchedulerAPIClient()
        client._client = AsyncMock()
        client._client.request = AsyncMock(
            side_effect=[response_unauthorized, response_ok]
        )
        client._client.post = AsyncMock(return_value=login_response)
        client._token = "stale-token"

        result = await client._request_with_retry("GET", "/health", max_retries=0)

        assert result.status_code == 200
        assert client._token == "new-token"
        assert client._client.request.await_count == 2
        client._client.post.assert_awaited_once()

        second_call_headers = client._client.request.await_args_list[1].kwargs["headers"]
        assert second_call_headers["Authorization"] == "Bearer new-token"

    async def test_request_with_retry_raises_after_second_401(self):
        """Test 401 retry stops after a refresh attempt."""
        request = httpx.Request("GET", "http://test/health")
        response_unauthorized = httpx.Response(401, request=request)
        response_unauthorized_second = httpx.Response(401, request=request)
        login_request = httpx.Request("POST", "http://test/api/v1/auth/login/json")
        login_response = httpx.Response(
            200, request=login_request, json={"access_token": "new-token"}
        )

        client = SchedulerAPIClient()
        client._client = AsyncMock()
        client._client.request = AsyncMock(
            side_effect=[response_unauthorized, response_unauthorized_second]
        )
        client._client.post = AsyncMock(return_value=login_response)
        client._token = "stale-token"

        with pytest.raises(httpx.HTTPStatusError):
            await client._request_with_retry("GET", "/health", max_retries=0)

        assert client._client.request.await_count == 2
        client._client.post.assert_awaited_once()

    async def test_request_with_retry_no_refresh_on_non_401(self):
        """Test non-401 errors do not trigger token refresh."""
        request = httpx.Request("GET", "http://test/health")
        response_forbidden = httpx.Response(403, request=request)

        client = SchedulerAPIClient()
        client._client = AsyncMock()
        client._client.request = AsyncMock(return_value=response_forbidden)
        client._client.post = AsyncMock()

        with pytest.raises(httpx.HTTPStatusError):
            await client._request_with_retry("GET", "/health", max_retries=0)

        client._client.post.assert_not_awaited()

    def test_custom_config_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict("os.environ", {"API_BASE_URL": "http://custom:8080"}):
            client = SchedulerAPIClient()
            assert client.config.base_url == "http://custom:8080"


class TestModuleLevelFunctions:
    """Test module-level client management functions."""

    async def test_get_api_client_creates_instance(self):
        """Test get_api_client creates and initializes client."""
        # Clean up any existing client first
        await close_api_client()

        client = await get_api_client()
        assert client is not None
        assert isinstance(client, SchedulerAPIClient)
        assert client._client is not None

        # Cleanup
        await close_api_client()

    async def test_get_api_client_returns_same_instance(self):
        """Test get_api_client returns the same instance."""
        # Clean up any existing client first
        await close_api_client()

        client1 = await get_api_client()
        client2 = await get_api_client()
        assert client1 is client2

        # Cleanup
        await close_api_client()

    async def test_close_api_client_cleans_up(self):
        """Test close_api_client properly cleans up."""
        await get_api_client()
        await close_api_client()

        # After closing, getting client again should create a new instance
        new_client = await get_api_client()
        assert new_client is not None

        # Cleanup
        await close_api_client()

    async def test_close_api_client_handles_none(self):
        """Test close_api_client handles None client gracefully."""
        await close_api_client()  # Should not raise even if no client exists
        await close_api_client()  # Can be called multiple times safely
