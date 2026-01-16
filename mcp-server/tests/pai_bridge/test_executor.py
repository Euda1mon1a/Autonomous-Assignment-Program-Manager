"""
Tests for PAI Agent Executor.

Tests the execution of PAI agents with identity-based access control.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from scheduler_mcp.pai_bridge.executor import PAIAgentExecutor
from scheduler_mcp.pai_bridge.models import AgentIdentity, AgentResult


# Sample identity for testing
SAMPLE_IDENTITY = AgentIdentity(
    name="TEST_SCHEDULER",
    role="Test schedule generator",
    tier="Specialist",
    model="haiku",
    reports_to="COORD_ENGINE",
    can_spawn=[],
    escalate_to="COORD_ENGINE",
    standing_orders=[
        "Generate test schedules",
        "Validate test compliance",
    ],
    escalation_triggers=[
        "Test violation detected",
        "Test timeout occurred",
    ],
    constraints=[
        "Do NOT skip test validation",
    ],
    charter="Test efficiently.",
)


class TestPAIAgentExecutor:
    """Tests for PAIAgentExecutor class."""

    @pytest.fixture
    def executor(self, tmp_path):
        """Create an executor with temp paths."""
        return PAIAgentExecutor(
            identities_path=tmp_path / "identities",
            audit_path=tmp_path / "audit",
        )

    def test_executor_initialization(self, executor):
        """Test executor initializes correctly."""
        assert executor.identity_loader is not None
        assert executor.tool_validator is not None
        assert executor.active_invocations == {}

    def test_build_prompt_structure(self, executor):
        """Test that build_prompt creates valid structure."""
        prompt = executor._build_prompt(
            identity=SAMPLE_IDENTITY,
            mission="Generate a test schedule",
            context={"test_key": "test_value"},
            additional_constraints=["Extra constraint"],
            allowed_tools=["validate_schedule", "generate_schedule"],
        )

        # Check prompt contains key sections
        assert "## BOOT CONTEXT" in prompt
        assert "## MISSION" in prompt
        assert "## CONTEXT" in prompt
        assert "## AVAILABLE MCP TOOLS" in prompt

        # Check identity info included
        assert "TEST_SCHEDULER" in prompt
        assert "Specialist" in prompt
        assert "COORD_ENGINE" in prompt

        # Check mission included
        assert "Generate a test schedule" in prompt

        # Check context included
        assert "test_key" in prompt
        assert "test_value" in prompt

        # Check tools included
        assert "validate_schedule" in prompt
        assert "generate_schedule" in prompt

        # Check constraints included
        assert "Extra constraint" in prompt

    def test_build_prompt_terminal_specialist(self, executor):
        """Test prompt for terminal specialist shows no spawn."""
        prompt = executor._build_prompt(
            identity=SAMPLE_IDENTITY,
            mission="Test",
            context={},
            additional_constraints=[],
            allowed_tools=[],
        )

        assert "None (terminal specialist)" in prompt

    def test_build_prompt_empty_tools(self, executor):
        """Test prompt when no tools available."""
        prompt = executor._build_prompt(
            identity=SAMPLE_IDENTITY,
            mission="Test",
            context={},
            additional_constraints=[],
            allowed_tools=[],
        )

        assert "No MCP tools available" in prompt

    def test_check_escalation_triggers_violation(self, executor):
        """Test escalation trigger detection for violations."""
        identity = AgentIdentity(
            name="TEST",
            role="Test",
            tier="Specialist",
            model="haiku",
            reports_to="COORD",
            escalation_triggers=["violation detected"],
        )

        result = {"status": "error", "message": "ACGME violation found"}
        trigger = executor._check_escalation_triggers(identity, result)

        assert trigger is not None
        assert "violation" in trigger.lower()

    def test_check_escalation_triggers_timeout(self, executor):
        """Test escalation trigger detection for timeouts."""
        identity = AgentIdentity(
            name="TEST",
            role="Test",
            tier="Specialist",
            model="haiku",
            reports_to="COORD",
            escalation_triggers=["timeout exceeded"],
        )

        result = {"status": "error", "message": "Operation timeout"}
        trigger = executor._check_escalation_triggers(identity, result)

        assert trigger is not None
        assert "timeout" in trigger.lower()

    def test_check_escalation_triggers_no_match(self, executor):
        """Test no escalation when no triggers match."""
        identity = AgentIdentity(
            name="TEST",
            role="Test",
            tier="Specialist",
            model="haiku",
            reports_to="COORD",
            escalation_triggers=["violation detected"],
        )

        result = {"status": "success", "message": "All good"}
        trigger = executor._check_escalation_triggers(identity, result)

        assert trigger is None

    def test_find_valid_parent_scheduler(self, executor):
        """Test finding valid parent for SCHEDULER."""
        parent = executor._find_valid_parent("SCHEDULER")
        assert parent == "COORD_ENGINE"

    def test_find_valid_parent_unknown(self, executor):
        """Test finding parent for unknown agent."""
        parent = executor._find_valid_parent("UNKNOWN_AGENT")
        assert parent is None

    def test_simulate_agent_execution_scheduler(self, executor):
        """Test simulated execution for SCHEDULER."""
        identity = AgentIdentity(
            name="SCHEDULER",
            role="Schedule generator",
            tier="Specialist",
            model="haiku",
            reports_to="COORD_ENGINE",
        )

        result = executor._simulate_agent_execution(
            identity=identity,
            allowed_tools=["validate_schedule"],
            context={"schedule_id": "test_123"},
        )

        assert "schedule_id" in result
        assert result["schedule_id"] == "test_123"
        assert result["acgme_compliant"] is True

    def test_simulate_agent_execution_swap_manager(self, executor):
        """Test simulated execution for SWAP_MANAGER."""
        identity = AgentIdentity(
            name="SWAP_MANAGER",
            role="Swap manager",
            tier="Specialist",
            model="haiku",
            reports_to="COORD_ENGINE",
        )

        result = executor._simulate_agent_execution(
            identity=identity,
            allowed_tools=[],
            context={},
        )

        assert "candidates_found" in result

    def test_get_active_invocations_empty(self, executor):
        """Test getting active invocations when empty."""
        active = executor.get_active_invocations()
        assert active == {}


class TestPAIAgentExecutorAsync:
    """Async tests for PAIAgentExecutor."""

    @pytest.fixture
    def executor(self, tmp_path):
        """Create an executor with temp paths."""
        identities_path = tmp_path / "identities"
        identities_path.mkdir(parents=True)

        # Create a test identity file
        identity_content = """# SCHEDULER Identity Card

## Identity
- **Role:** Schedule generation specialist
- **Tier:** Specialist
- **Model:** haiku

## Chain of Command
- **Reports To:** COORD_ENGINE
- **Can Spawn:** None (terminal specialist)
- **Escalate To:** COORD_ENGINE

## Standing Orders (Execute Without Asking)
1. Generate schedules

## Escalation Triggers (MUST Escalate)
- Violation detected

## Key Constraints
- Do NOT skip validation

## One-Line Charter
"Generate compliant schedules."
"""
        (identities_path / "SCHEDULER.identity.md").write_text(identity_content)

        return PAIAgentExecutor(
            identities_path=identities_path,
            audit_path=tmp_path / "audit",
        )

    @pytest.mark.asyncio
    async def test_invoke_agent_success(self, executor):
        """Test successful agent invocation."""
        result = await executor.invoke(
            agent_name="SCHEDULER",
            mission="Generate a test schedule",
            context={"test": True},
        )

        assert isinstance(result, AgentResult)
        assert result.agent_name == "SCHEDULER"
        assert result.status in ["completed", "awaiting_approval"]
        assert result.goal_id != ""

    @pytest.mark.asyncio
    async def test_invoke_agent_not_found(self, executor):
        """Test invocation of non-existent agent."""
        result = await executor.invoke(
            agent_name="NONEXISTENT_AGENT",
            mission="Test",
        )

        assert result.status == "error"
        assert "not found" in result.result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_invoke_with_spawn_chain_violation(self, executor, tmp_path):
        """Test invocation with invalid spawn chain."""
        # Create SWAP_MANAGER identity
        identities_path = tmp_path / "identities"
        swap_identity = """# SWAP_MANAGER Identity Card

## Identity
- **Role:** Swap manager
- **Tier:** Specialist
- **Model:** haiku

## Chain of Command
- **Reports To:** COORD_ENGINE
- **Can Spawn:** None (terminal specialist)
- **Escalate To:** COORD_ENGINE

## Standing Orders (Execute Without Asking)
1. Manage swaps

## Escalation Triggers (MUST Escalate)
- Error detected

## Key Constraints
- Do NOT skip validation

## One-Line Charter
"Manage swaps safely."
"""
        (identities_path / "SWAP_MANAGER.identity.md").write_text(swap_identity)

        # SCHEDULER cannot spawn SWAP_MANAGER
        result = await executor.invoke(
            agent_name="SWAP_MANAGER",
            mission="Test",
            parent_agent="SCHEDULER",  # Invalid: SCHEDULER can't spawn
        )

        assert result.status == "spawn_violation"
        assert len(result.escalations) > 0
        assert result.escalations[0]["type"] == "spawn_violation"

    @pytest.mark.asyncio
    async def test_invoke_writes_audit_trail(self, executor, tmp_path):
        """Test that invocation writes audit trail."""
        result = await executor.invoke(
            agent_name="SCHEDULER",
            mission="Generate audit test schedule",
        )

        assert result.audit_trail_path != ""
        audit_path = Path(result.audit_trail_path)
        assert audit_path.exists()

        # Read and verify audit content
        import json
        audit_content = json.loads(audit_path.read_text())
        assert audit_content["agent_name"] == "SCHEDULER"
        assert audit_content["mission"] == "Generate audit test schedule"

    @pytest.mark.asyncio
    async def test_invoke_with_additional_constraints(self, executor):
        """Test invocation with additional constraints."""
        result = await executor.invoke(
            agent_name="SCHEDULER",
            mission="Generate constrained schedule",
            additional_constraints=[
                "Must prioritize night shifts",
                "Minimize weekend assignments",
            ],
        )

        assert result.status in ["completed", "awaiting_approval"]
        # Constraints would be in the prompt (checked via execution log)

    @pytest.mark.asyncio
    async def test_list_available_agents(self, executor):
        """Test listing available agents."""
        agents = await executor.list_available_agents()

        assert len(agents) >= 1
        scheduler = next((a for a in agents if a["name"] == "SCHEDULER"), None)
        assert scheduler is not None
        assert scheduler["tier"] == "Specialist"
