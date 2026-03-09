"""
Tests for constraint management tools module.

Tests the structure, models, and tool functions with mocked API client.
"""

from unittest.mock import AsyncMock, patch

import pytest

from scheduler_mcp.constraint_tools import (
    ApplyPresetResult,
    ConstraintInfo,
    ListConstraintsResult,
    ToggleConstraintResult,
    apply_constraint_preset,
    get_constraint,
    list_constraints,
    list_constraints_by_category,
    toggle_constraint,
)

# =============================================================================
# Model Tests
# =============================================================================


class TestModels:
    def test_constraint_info(self):
        c = ConstraintInfo(
            name="TestConstraint",
            enabled=True,
            priority=1,
            weight=1.0,
            category="ACGME",
            description="Test constraint",
        )
        assert c.name == "TestConstraint"
        assert c.enabled

    def test_list_constraints_result(self):
        result = ListConstraintsResult(
            constraints=[],
            total_count=0,
            enabled_count=0,
            disabled_count=0,
        )
        assert result.total_count == 0

    def test_toggle_constraint_result(self):
        result = ToggleConstraintResult(
            success=True,
            message="Enabled",
        )
        assert result.success

    def test_apply_preset_result(self):
        result = ApplyPresetResult(
            success=True,
            message="Applied",
            enabled_constraints=["A", "B"],
            disabled_constraints=["C"],
        )
        assert len(result.enabled_constraints) == 2


# =============================================================================
# Tool Function Tests (mocked API client)
# =============================================================================


MOCK_CONSTRAINT = {
    "name": "OvernightCallGeneration",
    "enabled": True,
    "priority": 1,
    "weight": 100.0,
    "category": "CALL",
    "description": "Generates overnight call assignments",
    "dependencies": [],
    "enable_condition": None,
    "disable_reason": None,
}

MOCK_DISABLED_CONSTRAINT = {
    "name": "ResidentWeeklyClinic",
    "enabled": False,
    "priority": 3,
    "weight": 50.0,
    "category": "SCHEDULING",
    "description": "Weekly clinic scheduling",
    "dependencies": [],
    "enable_condition": None,
    "disable_reason": "Not yet implemented",
}


@pytest.fixture
def mock_api_client():
    client = AsyncMock()
    with patch("scheduler_mcp.constraint_tools.get_api_client", return_value=client):
        yield client


class TestListConstraints:
    @pytest.mark.asyncio
    async def test_list_all(self, mock_api_client):
        mock_api_client.list_constraints.return_value = [
            MOCK_CONSTRAINT,
            MOCK_DISABLED_CONSTRAINT,
        ]

        result = await list_constraints(filter="all")

        assert result.total_count == 2
        assert result.enabled_count == 1
        assert result.disabled_count == 1

    @pytest.mark.asyncio
    async def test_list_enabled(self, mock_api_client):
        mock_api_client.list_constraints.return_value = [MOCK_CONSTRAINT]

        result = await list_constraints(filter="enabled")

        assert result.total_count == 1
        assert result.enabled_count == 1

    @pytest.mark.asyncio
    async def test_invalid_filter(self, mock_api_client):
        result = await list_constraints(filter="bogus")

        assert result.error is not None
        assert "Invalid filter" in result.error
        mock_api_client.list_constraints.assert_not_called()

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.list_constraints.side_effect = Exception("Connection error")

        result = await list_constraints()

        assert result.error is not None
        assert "Connection" in result.error


class TestGetConstraint:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client):
        mock_api_client.get_constraint.return_value = MOCK_CONSTRAINT

        result = await get_constraint("OvernightCallGeneration")

        assert result.success
        assert result.constraint.name == "OvernightCallGeneration"
        assert result.constraint.weight == 100.0

    @pytest.mark.asyncio
    async def test_not_found(self, mock_api_client):
        mock_api_client.get_constraint.side_effect = Exception("404 Not Found")

        result = await get_constraint("NonexistentConstraint")

        assert not result.success
        assert "404" in result.error


class TestListConstraintsByCategory:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client):
        mock_api_client.list_constraints_by_category.return_value = [MOCK_CONSTRAINT]

        result = await list_constraints_by_category("CALL")

        assert result.total_count == 1
        assert result.constraints[0].category == "CALL"

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.list_constraints_by_category.side_effect = Exception(
            "Invalid category"
        )

        result = await list_constraints_by_category("BOGUS")

        assert result.error is not None


class TestToggleConstraint:
    @pytest.mark.asyncio
    async def test_enable(self, mock_api_client):
        mock_api_client.toggle_constraint.return_value = {
            "success": True,
            "message": "Successfully enabled constraint 'Test'",
            "constraint": MOCK_CONSTRAINT,
        }

        result = await toggle_constraint("Test", enabled=True)

        assert result.success
        assert result.constraint is not None
        mock_api_client.toggle_constraint.assert_called_once_with(
            "Test", enabled=True
        )

    @pytest.mark.asyncio
    async def test_disable(self, mock_api_client):
        mock_api_client.toggle_constraint.return_value = {
            "success": True,
            "message": "Successfully disabled",
            "constraint": MOCK_DISABLED_CONSTRAINT,
        }

        result = await toggle_constraint("ResidentWeeklyClinic", enabled=False)

        assert result.success

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.toggle_constraint.side_effect = Exception("Forbidden")

        result = await toggle_constraint("Test", enabled=True)

        assert not result.success
        assert "Forbidden" in result.error


class TestApplyPreset:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client):
        mock_api_client.apply_constraint_preset.return_value = {
            "success": True,
            "message": "Applied preset 'strict'",
            "enabled_constraints": ["A", "B", "C"],
            "disabled_constraints": ["D"],
        }

        result = await apply_constraint_preset("strict")

        assert result.success
        assert len(result.enabled_constraints) == 3

    @pytest.mark.asyncio
    async def test_invalid_preset(self, mock_api_client):
        result = await apply_constraint_preset("nonexistent")

        assert not result.success
        assert "Invalid preset" in result.error
        mock_api_client.apply_constraint_preset.assert_not_called()

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.apply_constraint_preset.side_effect = Exception("Server error")

        result = await apply_constraint_preset("minimal")

        assert not result.success
        assert "Server error" in result.error
