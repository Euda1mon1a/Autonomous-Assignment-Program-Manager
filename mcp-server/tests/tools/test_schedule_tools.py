"""
Tests for schedule tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from scheduler_mcp.tools.schedule import (
    CreateAssignmentTool,
    DeleteAssignmentTool,
    ExportScheduleTool,
    GenerateScheduleTool,
    GetScheduleTool,
    OptimizeScheduleTool,
    UpdateAssignmentTool,
    ValidateScheduleTool,
)


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = AsyncMock()
    client.config = MagicMock()
    client.config.api_prefix = "/api/v1"
    return client


class TestGetScheduleTool:
    """Tests for GetScheduleTool."""

    @pytest.mark.asyncio
    async def test_get_schedule_success(self, mock_api_client):
        """Test successful schedule retrieval."""
        # Setup mock
        mock_api_client.get_assignments = AsyncMock(
            return_value={
                "assignments": [
                    {
                        "id": "1",
                        "person_id": "p1",
                        "person_name": "John Doe",
                        "block_id": "b1",
                        "block_date": "2025-01-01",
                        "block_session": "AM",
                        "rotation_id": "r1",
                        "rotation_name": "Clinic",
                        "created_at": "2025-01-01T00:00:00",
                    }
                ]
            }
        )

        # Execute
        tool = GetScheduleTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-07",
            limit=100,
        )

        # Assert
        assert result["total_assignments"] == 1
        assert result["date_range_days"] == 7
        assert len(result["assignments"]) == 1

    @pytest.mark.asyncio
    async def test_get_schedule_invalid_dates(self, mock_api_client):
        """Test validation with invalid dates."""
        tool = GetScheduleTool(api_client=mock_api_client)

        with pytest.raises(Exception):
            await tool(
                start_date="2025-01-07",
                end_date="2025-01-01",  # End before start
                limit=100,
            )


class TestCreateAssignmentTool:
    """Tests for CreateAssignmentTool."""

    @pytest.mark.asyncio
    async def test_create_assignment_success(self, mock_api_client):
        """Test successful assignment creation."""
        # Setup mock
        mock_api_client.client.post = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"id": "a1"})
        mock_api_client.client.post.return_value = mock_response
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = CreateAssignmentTool(api_client=mock_api_client)
        result = await tool(
            person_id="p1",
            block_date="2025-01-01",
            block_session="AM",
        )

        # Assert
        assert result["success"] is True
        assert result["assignment_id"] == "a1"

    @pytest.mark.asyncio
    async def test_create_assignment_invalid_session(self, mock_api_client):
        """Test validation with invalid session."""
        tool = CreateAssignmentTool(api_client=mock_api_client)

        with pytest.raises(Exception):
            await tool(
                person_id="p1",
                block_date="2025-01-01",
                block_session="INVALID",
            )


class TestGenerateScheduleTool:
    """Tests for GenerateScheduleTool."""

    @pytest.mark.asyncio
    async def test_generate_schedule_success(self, mock_api_client):
        """Test successful schedule generation."""
        # Setup mock
        mock_api_client.generate_schedule = AsyncMock(
            return_value={
                "assignments_created": 100,
                "validation_passed": True,
                "solver_time_ms": 1500.0,
            }
        )

        # Execute
        tool = GenerateScheduleTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-07",
            algorithm="greedy",
        )

        # Assert
        assert result["success"] is True
        assert result["assignments_created"] == 100
        assert result["validation_passed"] is True

    @pytest.mark.asyncio
    async def test_generate_schedule_invalid_algorithm(self, mock_api_client):
        """Test validation with invalid algorithm."""
        tool = GenerateScheduleTool(api_client=mock_api_client)

        with pytest.raises(Exception):
            await tool(
                start_date="2025-01-01",
                end_date="2025-01-07",
                algorithm="invalid_algo",
            )


class TestValidateScheduleTool:
    """Tests for ValidateScheduleTool."""

    @pytest.mark.asyncio
    async def test_validate_schedule_compliant(self, mock_api_client):
        """Test validation of compliant schedule."""
        # Setup mock
        mock_api_client.validate_schedule = AsyncMock(
            return_value={
                "is_valid": True,
                "compliance_rate": 1.0,
                "issues": [],
            }
        )

        # Execute
        tool = ValidateScheduleTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-07",
        )

        # Assert
        assert result["is_valid"] is True
        assert result["compliance_rate"] == 1.0
        assert result["total_issues"] == 0

    @pytest.mark.asyncio
    async def test_validate_schedule_with_violations(self, mock_api_client):
        """Test validation with violations."""
        # Setup mock
        mock_api_client.validate_schedule = AsyncMock(
            return_value={
                "is_valid": False,
                "compliance_rate": 0.8,
                "issues": [
                    {
                        "severity": "critical",
                        "rule_type": "work_hours",
                        "message": "80-hour violation",
                        "constraint_name": "max_hours_per_week",
                    }
                ],
            }
        )

        # Execute
        tool = ValidateScheduleTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-07",
        )

        # Assert
        assert result["is_valid"] is False
        assert result["total_issues"] == 1
        assert result["critical_count"] == 1
