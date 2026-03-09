"""
Tests for ARO (Annual Rotation Optimizer) tools module.

Tests the structure, models, and tool functions with mocked API client.
"""

from unittest.mock import AsyncMock, patch

import pytest

from scheduler_mcp.aro_tools import (
    AnnualPlanAssignment,
    AnnualPlanInfo,
    AnnualPlanSummary,
    CreatePlanResult,
    OptimizeResult,
    create_annual_plan,
    get_annual_plan,
    list_annual_plans,
    optimize_annual_plan,
    publish_annual_plan,
)

# =============================================================================
# Model Tests
# =============================================================================


class TestModels:
    """Test Pydantic response models."""

    def test_annual_plan_assignment(self):
        a = AnnualPlanAssignment(
            id="uuid-1",
            person_id="person-uuid-1",
            block_number=3,
            rotation_name="IM",
            is_fixed=False,
        )
        assert a.block_number == 3
        assert a.person_id == "person-uuid-1"

    def test_annual_plan_info(self):
        plan = AnnualPlanInfo(
            id="uuid-plan",
            academic_year=2026,
            name="AY 26-27 Draft",
            status="draft",
        )
        assert plan.academic_year == 2026
        assert plan.assignments == []

    def test_annual_plan_summary(self):
        summary = AnnualPlanSummary(
            id="uuid-plan",
            academic_year=2026,
            name="Test Plan",
            status="optimized",
            solver_status="OPTIMAL",
            objective_value=150,
            solve_duration_ms=2500,
        )
        assert summary.solver_status == "OPTIMAL"
        assert summary.objective_value == 150

    def test_create_plan_result_success(self):
        result = CreatePlanResult(
            success=True,
            plan=AnnualPlanInfo(
                id="uuid-1", academic_year=2026, name="Test", status="draft"
            ),
        )
        assert result.success
        assert result.plan.name == "Test"

    def test_create_plan_result_error(self):
        result = CreatePlanResult(success=False, error="Something went wrong")
        assert not result.success
        assert result.plan is None

    def test_optimize_result(self):
        result = OptimizeResult(
            success=True,
            status="optimized",
            solver_status="OPTIMAL",
            objective_value=150,
            leave_satisfied=12,
            leave_total=15,
            total_assignments=234,
        )
        assert result.solver_status == "OPTIMAL"
        assert result.leave_satisfied == 12


# =============================================================================
# Tool Function Tests (mocked API client)
# =============================================================================


MOCK_PLAN_RESPONSE = {
    "id": "plan-uuid-123",
    "academic_year": 2026,
    "name": "AY 26-27 Draft 1",
    "status": "draft",
    "solver_time_limit": 30.0,
    "solve_duration_ms": None,
    "created_at": "2026-03-09T10:00:00",
    "assignments": [
        {
            "id": "assign-1",
            "person_id": "person-uuid-1",
            "block_number": 1,
            "rotation_name": "IM",
            "is_fixed": False,
        },
    ],
}


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = AsyncMock()
    with patch("scheduler_mcp.aro_tools.get_api_client", return_value=client):
        yield client


class TestCreateAnnualPlan:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client):
        mock_api_client.create_annual_plan.return_value = MOCK_PLAN_RESPONSE

        result = await create_annual_plan(
            academic_year=2026, name="AY 26-27 Draft 1"
        )

        assert result.success
        assert result.plan is not None
        assert result.plan.academic_year == 2026
        assert len(result.plan.assignments) == 1
        mock_api_client.create_annual_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.create_annual_plan.side_effect = Exception("Connection refused")

        result = await create_annual_plan(
            academic_year=2026, name="Test"
        )

        assert not result.success
        assert "Connection refused" in result.error


class TestListAnnualPlans:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client):
        mock_api_client.list_annual_plans.return_value = [
            {
                "id": "plan-1",
                "academic_year": 2026,
                "name": "Draft 1",
                "status": "draft",
                "created_at": "2026-03-09",
                "solver_status": None,
            },
            {
                "id": "plan-2",
                "academic_year": 2026,
                "name": "Final",
                "status": "published",
                "created_at": "2026-03-08",
                "solver_status": "OPTIMAL",
                "objective_value": 150,
                "solve_duration_ms": 2500,
            },
        ]

        result = await list_annual_plans()

        assert result.total_count == 2
        assert result.plans[1].status == "published"

    @pytest.mark.asyncio
    async def test_empty(self, mock_api_client):
        mock_api_client.list_annual_plans.return_value = []

        result = await list_annual_plans()

        assert result.total_count == 0
        assert result.plans == []

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.list_annual_plans.side_effect = Exception("Timeout")

        result = await list_annual_plans()

        assert result.total_count == 0
        assert result.error is not None
        assert "Timeout" in result.error


class TestGetAnnualPlan:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client):
        mock_api_client.get_annual_plan.return_value = MOCK_PLAN_RESPONSE

        result = await get_annual_plan("plan-uuid-123")

        assert result.success
        assert result.plan.id == "plan-uuid-123"
        assert result.plan.assignments[0].rotation_name == "IM"

    @pytest.mark.asyncio
    async def test_not_found(self, mock_api_client):
        mock_api_client.get_annual_plan.side_effect = Exception("404 Not Found")

        result = await get_annual_plan("nonexistent")

        assert not result.success
        assert "404" in result.error


class TestOptimizeAnnualPlan:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client):
        mock_api_client.optimize_annual_plan.return_value = {
            "status": "optimized",
            "solver_status": "OPTIMAL",
            "objective_value": 150,
            "solve_duration_ms": 2500,
            "leave_satisfied": 12,
            "leave_total": 15,
            "total_assignments": 234,
        }

        result = await optimize_annual_plan("plan-uuid-123")

        assert result.success
        assert result.solver_status == "OPTIMAL"
        assert result.total_assignments == 234

    @pytest.mark.asyncio
    async def test_with_time_limit(self, mock_api_client):
        mock_api_client.optimize_annual_plan.return_value = {
            "status": "optimized",
            "solver_status": "FEASIBLE",
            "total_assignments": 200,
        }

        result = await optimize_annual_plan("plan-123", solver_time_limit=60.0)

        mock_api_client.optimize_annual_plan.assert_called_once_with(
            plan_id="plan-123", solver_time_limit=60.0
        )
        assert result.success

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.optimize_annual_plan.side_effect = Exception("Solver timeout")

        result = await optimize_annual_plan("plan-123")

        assert not result.success
        assert "Solver timeout" in result.error


class TestPublishAnnualPlan:
    @pytest.mark.asyncio
    async def test_success(self, mock_api_client):
        published = dict(MOCK_PLAN_RESPONSE)
        published["status"] = "published"
        mock_api_client.publish_annual_plan.return_value = published

        result = await publish_annual_plan("plan-uuid-123")

        assert result.success
        assert result.plan.status == "published"

    @pytest.mark.asyncio
    async def test_error(self, mock_api_client):
        mock_api_client.publish_annual_plan.side_effect = Exception(
            "Plan must be optimized first"
        )

        result = await publish_annual_plan("plan-123")

        assert not result.success
        assert "optimized" in result.error
