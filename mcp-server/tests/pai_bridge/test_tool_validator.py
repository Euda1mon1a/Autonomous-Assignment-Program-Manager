"""
Tests for PAI Tool Access Validator.

Tests identity-based tool access control and spawn chain validation.
"""

import pytest
from uuid import uuid4

from scheduler_mcp.pai_bridge.tool_validator import (
    ToolAccessValidator,
    AGENT_TOOL_MATRIX,
    SPAWN_CHAINS,
)


class TestToolAccessValidator:
    """Tests for ToolAccessValidator class."""

    def test_agent_tool_matrix_structure(self):
        """Test that AGENT_TOOL_MATRIX has expected structure."""
        # Key agents should be present
        assert "SCHEDULER" in AGENT_TOOL_MATRIX
        assert "SWAP_MANAGER" in AGENT_TOOL_MATRIX
        assert "COORD_ENGINE" in AGENT_TOOL_MATRIX
        assert "COMPLIANCE_AUDITOR" in AGENT_TOOL_MATRIX

        # SCHEDULER should have scheduling tools
        scheduler_tools = AGENT_TOOL_MATRIX["SCHEDULER"]
        assert "validate_schedule" in scheduler_tools
        assert "generate_schedule" in scheduler_tools

        # Deputies should have minimal/no direct tools
        assert len(AGENT_TOOL_MATRIX.get("ARCHITECT", [])) == 0
        assert len(AGENT_TOOL_MATRIX.get("ORCHESTRATOR", [])) == 0

    def test_spawn_chains_structure(self):
        """Test that SPAWN_CHAINS has expected hierarchy."""
        # ORCHESTRATOR can spawn Deputies
        assert "ARCHITECT" in SPAWN_CHAINS["ORCHESTRATOR"]
        assert "SYNTHESIZER" in SPAWN_CHAINS["ORCHESTRATOR"]

        # Deputies can spawn Coordinators
        assert "COORD_ENGINE" in SPAWN_CHAINS["ARCHITECT"]

        # Coordinators can spawn Specialists
        assert "SCHEDULER" in SPAWN_CHAINS["COORD_ENGINE"]
        assert "SWAP_MANAGER" in SPAWN_CHAINS["COORD_ENGINE"]

        # Terminal specialists cannot spawn
        assert SPAWN_CHAINS.get("SCHEDULER", []) == []
        assert SPAWN_CHAINS.get("SWAP_MANAGER", []) == []


class TestToolAccessValidatorMethods:
    """Tests for ToolAccessValidator methods."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ToolAccessValidator()

    @pytest.mark.asyncio
    async def test_get_allowed_tools_scheduler(self, validator):
        """Test getting allowed tools for SCHEDULER."""
        tools = await validator.get_allowed_tools("SCHEDULER")

        assert "validate_schedule" in tools
        assert "generate_schedule" in tools
        assert "detect_conflicts" in tools
        assert "analyze_swap_candidates" in tools
        assert "execute_swap" in tools

    @pytest.mark.asyncio
    async def test_get_allowed_tools_unknown_agent(self, validator):
        """Test getting allowed tools for unknown agent."""
        tools = await validator.get_allowed_tools("UNKNOWN_AGENT")
        assert tools == []

    @pytest.mark.asyncio
    async def test_can_access_tool_allowed(self, validator):
        """Test that allowed tool access returns True."""
        can_access = await validator.can_access_tool("SCHEDULER", "validate_schedule")
        assert can_access is True

    @pytest.mark.asyncio
    async def test_can_access_tool_denied(self, validator):
        """Test that denied tool access returns False."""
        # SCHEDULER should not have access to resilience tools
        can_access = await validator.can_access_tool("SCHEDULER", "get_defense_level")
        assert can_access is False

    @pytest.mark.asyncio
    async def test_validate_spawn_allowed(self, validator):
        """Test that valid spawn chain returns True."""
        # COORD_ENGINE can spawn SCHEDULER
        valid = await validator.validate_spawn("COORD_ENGINE", "SCHEDULER")
        assert valid is True

    @pytest.mark.asyncio
    async def test_validate_spawn_denied(self, validator):
        """Test that invalid spawn chain returns False."""
        # SCHEDULER cannot spawn anything
        valid = await validator.validate_spawn("SCHEDULER", "SWAP_MANAGER")
        assert valid is False

        # ARCHITECT cannot spawn SCHEDULER directly (must go through COORD_ENGINE)
        valid = await validator.validate_spawn("ARCHITECT", "SCHEDULER")
        assert valid is False

    @pytest.mark.asyncio
    async def test_check_preconditions_no_requirements(self, validator):
        """Test precondition check for tool with no requirements."""
        met, reason = await validator.check_preconditions(
            "SCHEDULER",
            "validate_schedule",
            {},
        )
        assert met is True
        assert reason == "all_preconditions_met"

    @pytest.mark.asyncio
    async def test_check_preconditions_backup_required(self, validator):
        """Test precondition check for tool requiring backup."""
        # execute_swap requires backup verification
        met, reason = await validator.check_preconditions(
            "SCHEDULER",
            "execute_swap",
            {"backup_verified": False},
        )
        assert met is False
        assert "backup" in reason.lower()

    @pytest.mark.asyncio
    async def test_check_preconditions_backup_satisfied(self, validator):
        """Test precondition check when backup is verified."""
        met, reason = await validator.check_preconditions(
            "SCHEDULER",
            "execute_swap",
            {
                "backup_verified": True,
                "tools_called": ["validate_schedule"],
            },
        )
        assert met is True

    def test_log_access_attempt(self, validator):
        """Test that access attempts are logged."""
        initial_log_len = len(validator._access_log)

        validator.log_access_attempt(
            agent_name="SCHEDULER",
            tool_name="validate_schedule",
            allowed=True,
            reason="in_whitelist",
        )

        assert len(validator._access_log) == initial_log_len + 1
        last_record = validator._access_log[-1]
        assert last_record.agent_name == "SCHEDULER"
        assert last_record.tool_name == "validate_schedule"
        assert last_record.allowed is True

    def test_log_spawn_attempt(self, validator):
        """Test that spawn attempts are logged."""
        initial_log_len = len(validator._spawn_log)

        validator.log_spawn_attempt(
            parent="COORD_ENGINE",
            child="SCHEDULER",
            allowed=True,
            reason="in_spawn_chain",
        )

        assert len(validator._spawn_log) == initial_log_len + 1
        last_record = validator._spawn_log[-1]
        assert last_record.parent_agent == "COORD_ENGINE"
        assert last_record.child_agent == "SCHEDULER"
        assert last_record.allowed is True

    def test_get_agent_capabilities(self, validator):
        """Test getting complete capabilities for an agent."""
        caps = validator.get_agent_capabilities("SCHEDULER")

        assert caps["agent_name"] == "SCHEDULER"
        assert "validate_schedule" in caps["allowed_tools"]
        assert caps["can_spawn"] == []
        assert caps["is_terminal"] is True

    def test_get_agent_capabilities_coordinator(self, validator):
        """Test getting capabilities for a coordinator."""
        caps = validator.get_agent_capabilities("COORD_ENGINE")

        assert caps["agent_name"] == "COORD_ENGINE"
        assert "SCHEDULER" in caps["can_spawn"]
        assert caps["is_terminal"] is False

    def test_clear_logs(self, validator):
        """Test clearing audit logs."""
        # Add some logs
        validator.log_access_attempt("TEST", "test_tool", True)
        validator.log_spawn_attempt("PARENT", "CHILD", True)

        assert len(validator._access_log) > 0
        assert len(validator._spawn_log) > 0

        validator.clear_logs()

        assert len(validator._access_log) == 0
        assert len(validator._spawn_log) == 0


class TestToolValidatorEdgeCases:
    """Edge case tests for ToolAccessValidator."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ToolAccessValidator()

    @pytest.mark.asyncio
    async def test_cross_domain_tool_access_denied(self, validator):
        """Test that agents can't access tools outside their domain."""
        # SCHEDULER (scheduling) should not access resilience tools
        assert await validator.can_access_tool("SCHEDULER", "get_defense_level") is False
        assert await validator.can_access_tool("SCHEDULER", "execute_sacrifice_hierarchy") is False

        # RESILIENCE_ENGINEER should not access scheduling generation
        assert await validator.can_access_tool("RESILIENCE_ENGINEER", "generate_schedule") is False

    @pytest.mark.asyncio
    async def test_deputy_has_no_direct_tools(self, validator):
        """Test that deputies have minimal/no direct tool access."""
        architect_tools = await validator.get_allowed_tools("ARCHITECT")
        assert len(architect_tools) == 0

        synthesizer_tools = await validator.get_allowed_tools("SYNTHESIZER")
        assert len(synthesizer_tools) == 0

    @pytest.mark.asyncio
    async def test_spawn_chain_hierarchy(self, validator):
        """Test that spawn chain respects hierarchy."""
        # Valid chain: ORCHESTRATOR -> ARCHITECT
        assert await validator.validate_spawn("ORCHESTRATOR", "ARCHITECT") is True

        # Invalid: ORCHESTRATOR cannot directly spawn COORD_ENGINE
        assert await validator.validate_spawn("ORCHESTRATOR", "COORD_ENGINE") is False

        # Invalid: SCHEDULER cannot spawn anyone
        assert await validator.validate_spawn("SCHEDULER", "ANYTHING") is False

    @pytest.mark.asyncio
    async def test_g_staff_tools(self, validator):
        """Test G-Staff agent tool access."""
        # G5_PLANNING should have planning-related tools
        g5_tools = await validator.get_allowed_tools("G5_PLANNING")
        assert "rag_search" in g5_tools
        assert "validate_schedule" in g5_tools

        # G2_RECON should have recon tools
        g2_tools = await validator.get_allowed_tools("G2_RECON")
        assert "rag_search" in g2_tools
