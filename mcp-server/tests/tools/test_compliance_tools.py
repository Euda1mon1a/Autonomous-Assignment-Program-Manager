"""
Tests for compliance tools.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from scheduler_mcp.tools.compliance import (
    CheckDayOffTool,
    CheckSupervisionTool,
    CheckWorkHoursTool,
    GetViolationsTool,
)


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = AsyncMock()
    client.config = MagicMock()
    client.config.api_prefix = "/api/v1"
    client.client = AsyncMock()
    return client


class TestCheckWorkHoursTool:
    """Tests for CheckWorkHoursTool."""

    @pytest.mark.asyncio
    async def test_check_work_hours_compliant(self, mock_api_client):
        """Test work hours check with compliant schedule."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "people": [
                    {
                        "person_id": "p1",
                        "person_name": "John Doe",
                        "total_hours": 320.0,
                        "weeks_analyzed": 4,
                        "average_hours_per_week": 80.0,
                        "max_week_hours": 80.0,
                        "violations": 0,
                        "compliant": True,
                    }
                ]
            }
        )
        mock_api_client.client.get = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = CheckWorkHoursTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-28",
        )

        # Assert
        assert result["overall_compliant"] is True
        assert result["violation_count"] == 0
        assert result["total_people_checked"] == 1

    @pytest.mark.asyncio
    async def test_check_work_hours_violation(self, mock_api_client):
        """Test work hours check with violation."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "people": [
                    {
                        "person_id": "p1",
                        "person_name": "John Doe",
                        "total_hours": 360.0,
                        "weeks_analyzed": 4,
                        "average_hours_per_week": 90.0,
                        "max_week_hours": 95.0,
                        "violations": 1,
                        "compliant": False,
                    }
                ]
            }
        )
        mock_api_client.client.get = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = CheckWorkHoursTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-28",
        )

        # Assert
        assert result["overall_compliant"] is False
        assert result["violation_count"] == 1


class TestCheckDayOffTool:
    """Tests for CheckDayOffTool."""

    @pytest.mark.asyncio
    async def test_check_day_off_compliant(self, mock_api_client):
        """Test day-off check with compliant schedule."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "people": [
                    {
                        "person_id": "p1",
                        "person_name": "John Doe",
                        "days_analyzed": 28,
                        "days_off": 4,
                        "longest_stretch_days": 6,
                        "violations": 0,
                        "compliant": True,
                    }
                ]
            }
        )
        mock_api_client.client.get = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = CheckDayOffTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-28",
        )

        # Assert
        assert result["overall_compliant"] is True
        assert result["violation_count"] == 0


class TestCheckSupervisionTool:
    """Tests for CheckSupervisionTool."""

    @pytest.mark.asyncio
    async def test_check_supervision_compliant(self, mock_api_client):
        """Test supervision check with compliant ratios."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "ratios": [
                    {
                        "level": "PGY-1",
                        "residents": 2,
                        "faculty": 1,
                        "required_faculty": 1,
                        "ratio": "1:2",
                        "compliant": True,
                    }
                ],
                "total_residents": 2,
                "total_faculty": 1,
            }
        )
        mock_api_client.client.get = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = CheckSupervisionTool(api_client=mock_api_client)
        result = await tool(
            date="2025-01-01",
            session="AM",
        )

        # Assert
        assert result["overall_compliant"] is True
        assert len(result["ratios"]) == 1


class TestGetViolationsTool:
    """Tests for GetViolationsTool."""

    @pytest.mark.asyncio
    async def test_get_violations_empty(self, mock_api_client):
        """Test getting violations with no violations."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"violations": []})
        mock_api_client.client.get = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = GetViolationsTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-07",
        )

        # Assert
        assert result["total_violations"] == 0
        assert len(result["violations"]) == 0

    @pytest.mark.asyncio
    async def test_get_violations_with_data(self, mock_api_client):
        """Test getting violations with data."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "violations": [
                    {
                        "id": "v1",
                        "rule_type": "work_hours",
                        "severity": "critical",
                        "person_id": "p1",
                        "date": "2025-01-01",
                        "message": "80-hour violation",
                        "details": {},
                    }
                ]
            }
        )
        mock_api_client.client.get = AsyncMock(return_value=mock_response)
        mock_api_client._ensure_authenticated = AsyncMock(
            return_value={"Authorization": "Bearer token"}
        )

        # Execute
        tool = GetViolationsTool(api_client=mock_api_client)
        result = await tool(
            start_date="2025-01-01",
            end_date="2025-01-07",
        )

        # Assert
        assert result["total_violations"] == 1
        assert result["critical_count"] == 1
