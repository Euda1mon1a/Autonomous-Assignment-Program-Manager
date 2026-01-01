"""
Tests for swap tools.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from scheduler_mcp.tools.swap import (
    CreateSwapTool,
    ExecuteSwapTool,
    FindSwapMatchesTool,
    GetSwapHistoryTool,
    RollbackSwapTool,
)


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = AsyncMock()
    client.config = MagicMock()
    client.config.api_prefix = "/api/v1"
    client.client = AsyncMock()
    return client


class TestCreateSwapTool:
    """Tests for CreateSwapTool."""

    @pytest.mark.asyncio
    async def test_create_swap_success(self, mock_api_client):
        """Test successful swap creation."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "id": "s1",
                "status": "pending",
            }
        )
        mock_api_client.client.post = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = CreateSwapTool(api_client=mock_api_client)
        result = await tool(
            person_id="p1",
            assignment_id="a1",
            swap_type="one_to_one",
        )

        # Assert
        assert result["success"] is True
        assert result["swap_id"] == "s1"
        assert result["status"] == "pending"


class TestFindSwapMatchesTool:
    """Tests for FindSwapMatchesTool."""

    @pytest.mark.asyncio
    async def test_find_matches_success(self, mock_api_client):
        """Test successful match finding."""
        # Setup mock
        mock_api_client.get_swap_candidates = AsyncMock(
            return_value={
                "candidates": [
                    {
                        "person_id": "p2",
                        "person_name": "Jane Doe",
                        "assignment_id": "a2",
                        "block_date": "2025-01-01",
                        "block_session": "AM",
                        "compatibility_score": 0.9,
                        "reasons": ["Similar preferences"],
                    }
                ]
            }
        )

        # Execute
        tool = FindSwapMatchesTool(api_client=mock_api_client)
        result = await tool(
            person_id="p1",
            max_candidates=10,
        )

        # Assert
        assert result["total_candidates"] == 1
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["compatibility_score"] == 0.9


class TestExecuteSwapTool:
    """Tests for ExecuteSwapTool."""

    @pytest.mark.asyncio
    async def test_execute_swap_success(self, mock_api_client):
        """Test successful swap execution."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "executed_at": "2025-01-01T12:00:00",
                "rollback_deadline": "2025-01-02T12:00:00",
            }
        )
        mock_api_client.client.post = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = ExecuteSwapTool(api_client=mock_api_client)
        result = await tool(swap_id="s1")

        # Assert
        assert result["success"] is True
        assert result["executed_at"] is not None


class TestRollbackSwapTool:
    """Tests for RollbackSwapTool."""

    @pytest.mark.asyncio
    async def test_rollback_swap_success(self, mock_api_client):
        """Test successful swap rollback."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "rolled_back_at": "2025-01-01T14:00:00",
            }
        )
        mock_api_client.client.post = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = RollbackSwapTool(api_client=mock_api_client)
        result = await tool(
            swap_id="s1",
            reason="Changed mind",
        )

        # Assert
        assert result["success"] is True
        assert result["rolled_back_at"] is not None


class TestGetSwapHistoryTool:
    """Tests for GetSwapHistoryTool."""

    @pytest.mark.asyncio
    async def test_get_history_success(self, mock_api_client):
        """Test successful history retrieval."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "swaps": [
                    {
                        "id": "s1",
                        "swap_type": "one_to_one",
                        "status": "executed",
                        "person_id": "p1",
                        "assignment_id": "a1",
                        "created_at": "2025-01-01T00:00:00",
                    }
                ]
            }
        )
        mock_api_client.client.get = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = GetSwapHistoryTool(api_client=mock_api_client)
        result = await tool(limit=50)

        # Assert
        assert result["total_records"] == 1
        assert len(result["records"]) == 1
