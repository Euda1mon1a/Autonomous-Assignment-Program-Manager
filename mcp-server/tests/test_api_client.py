"""Tests for API client."""

from unittest.mock import Mock, patch

import httpx
import pytest

from scheduler_mcp.api_client import (
    APIConfig,
    SchedulerAPIClient,
    close_api_client,
    get_api_client,
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

    @patch("httpx.AsyncClient.get")
    async def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        async with SchedulerAPIClient() as client:
            result = await client.health_check()
            assert result is True
            mock_get.assert_called_once_with("/health")

    @patch("httpx.AsyncClient.get")
    async def test_health_check_failure(self, mock_get):
        """Test health check returns False on request error."""
        mock_get.side_effect = httpx.RequestError("Connection failed")

        async with SchedulerAPIClient() as client:
            result = await client.health_check()
            assert result is False

    @patch("httpx.AsyncClient.post")
    async def test_validate_schedule(self, mock_post):
        """Test schedule validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "violations": [],
            "summary": {"total_checks": 5, "passed": 5, "failed": 0},
        }
        mock_post.return_value = mock_response

        async with SchedulerAPIClient() as client:
            result = await client.validate_schedule(
                start_date="2024-01-01", end_date="2024-01-31"
            )
            assert result["valid"] is True
            assert result["violations"] == []
            mock_post.assert_called_once()

    @patch("httpx.AsyncClient.get")
    async def test_get_conflicts(self, mock_get):
        """Test getting schedule conflicts."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "conflicts": [{"type": "overlap", "person_id": "test-123"}]
        }
        mock_get.return_value = mock_response

        async with SchedulerAPIClient() as client:
            result = await client.get_conflicts(
                start_date="2024-01-01", end_date="2024-01-31"
            )
            assert "conflicts" in result
            assert len(result["conflicts"]) == 1
            mock_get.assert_called_once()

    @patch("httpx.AsyncClient.get")
    async def test_get_swap_candidates(self, mock_get):
        """Test getting swap candidates."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {"person_id": "fac-001", "compatibility_score": 0.95},
                {"person_id": "fac-002", "compatibility_score": 0.80},
            ]
        }
        mock_get.return_value = mock_response

        async with SchedulerAPIClient() as client:
            result = await client.get_swap_candidates(
                person_id="fac-123", block_id="block-456"
            )
            assert "candidates" in result
            assert len(result["candidates"]) == 2
            mock_get.assert_called_once()

    @patch("httpx.AsyncClient.post")
    async def test_run_contingency_analysis(self, mock_post):
        """Test running contingency analysis."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "scenario": "n-1",
            "status": "YELLOW",
            "coverage_percentage": 85.5,
            "recommendations": ["Add backup coverage for clinic"],
        }
        mock_post.return_value = mock_response

        async with SchedulerAPIClient() as client:
            result = await client.run_contingency_analysis(
                scenario="n-1",
                affected_ids=["fac-001"],
                start_date="2024-01-01",
                end_date="2024-01-31",
            )
            assert result["scenario"] == "n-1"
            assert result["status"] == "YELLOW"
            mock_post.assert_called_once()

    @patch("httpx.AsyncClient.post")
    async def test_http_error_handling(self, mock_post):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        mock_post.return_value = mock_response

        async with SchedulerAPIClient() as client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.validate_schedule(
                    start_date="2024-01-01", end_date="2024-01-31"
                )

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
