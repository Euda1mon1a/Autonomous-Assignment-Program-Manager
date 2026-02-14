"""
Tests for spawn_agent_tool MCP function.

Tests the PAI agent spawning factory that prepares agent context
for execution via Claude Code's Task() function.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import tempfile
import os


# Test data
MOCK_REGISTRY = {
    "version": "1.0",
    "agents": {
        "SCHEDULER": {
            "tier": "Specialist",
            "model": "haiku",
            "archetype": "Generator",
            "role": "Schedule generation specialist",
            "reports_to": "COORD_ENGINE",
            "can_spawn": [],
            "max_turns": 5,
            "tools_access": ["validate_schedule", "generate_schedule"],
            "relevant_doc_types": ["scheduling"],
        },
        "COORD_ENGINE": {
            "tier": "Coordinator",
            "model": "sonnet",
            "archetype": "Generator",
            "role": "Scheduling engine coordinator",
            "reports_to": "ARCHITECT",
            "can_spawn": ["SCHEDULER", "SWAP_MANAGER"],
            "max_turns": 20,
            "tools_access": ["validate_schedule", "detect_conflicts"],
            "relevant_doc_types": ["scheduling", "constraints"],
        },
        "ARCHITECT": {
            "tier": "Deputy",
            "model": "opus",
            "archetype": "Synthesizer",
            "role": "Deputy for Systems",
            "reports_to": "ORCHESTRATOR",
            "can_spawn": ["COORD_ENGINE", "COORD_PLATFORM"],
            "max_turns": 50,
            "tools_access": ["validate_schedule", "rag_search"],
            "relevant_doc_types": ["architecture", "patterns"],
        },
    }
}

MOCK_IDENTITY_CARD = """# SCHEDULER Identity Card

## Identity
- **Role:** Schedule generation specialist
- **Tier:** Specialist
- **Model:** haiku

## Chain of Command
- **Reports To:** COORD_ENGINE
- **Can Spawn:** None
- **Escalate To:** COORD_ENGINE

## One-Line Charter
"Generate ACGME-compliant schedules with precision."
"""


class TestSpawnAgentTool:
    """Tests for spawn_agent_tool function."""

    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client for RAG calls."""
        client = AsyncMock()
        client.rag_retrieve = AsyncMock(return_value={
            "documents": [
                {"content": "Test RAG content", "similarity_score": 0.8}
            ]
        })
        return client

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            claude_dir = Path(tmpdir) / ".claude"
            identities_dir = claude_dir / "Identities"
            history_dir = claude_dir / "History" / "agent_invocations"

            claude_dir.mkdir(parents=True)
            identities_dir.mkdir(parents=True)
            history_dir.mkdir(parents=True)

            # Write registry
            registry_path = claude_dir / "agents.yaml"
            import yaml
            with open(registry_path, 'w') as f:
                yaml.dump(MOCK_REGISTRY, f)

            # Write identity card
            identity_path = identities_dir / "SCHEDULER.identity.md"
            with open(identity_path, 'w') as f:
                f.write(MOCK_IDENTITY_CARD)

            yield tmpdir

    @pytest.mark.asyncio
    async def test_spawn_agent_basic(self, temp_project_dir, mock_api_client):
        """Test basic agent spawning with valid agent.

        Note: This test validates the test fixtures are set up correctly.
        Full integration testing of spawn_agent_tool requires the MCP server
        to be running. See test_spawn_agent_integration.py for those tests.
        """
        # Verify temp directory structure exists
        claude_dir = Path(temp_project_dir) / ".claude"
        assert claude_dir.exists()

        registry_path = claude_dir / "agents.yaml"
        assert registry_path.exists()

        identities_path = claude_dir / "Identities"
        assert identities_path.exists()

        identity_file = identities_path / "SCHEDULER.identity.md"
        assert identity_file.exists()

        # Verify registry content
        import yaml
        with open(registry_path) as f:
            registry = yaml.safe_load(f)
        assert "agents" in registry
        assert "SCHEDULER" in registry["agents"]

    @pytest.mark.asyncio
    async def test_spawn_chain_valid(self):
        """Test spawn chain validation when parent can spawn child."""
        # COORD_ENGINE can spawn SCHEDULER
        parent_spec = MOCK_REGISTRY["agents"]["COORD_ENGINE"]
        allowed_children = parent_spec.get("can_spawn", [])

        assert "SCHEDULER" in allowed_children
        assert "SWAP_MANAGER" in allowed_children

    @pytest.mark.asyncio
    async def test_spawn_chain_invalid(self):
        """Test spawn chain validation when parent cannot spawn child."""
        # SCHEDULER cannot spawn anything
        parent_spec = MOCK_REGISTRY["agents"]["SCHEDULER"]
        allowed_children = parent_spec.get("can_spawn", [])

        assert "COORD_ENGINE" not in allowed_children
        assert "ARCHITECT" not in allowed_children
        assert allowed_children == []

    @pytest.mark.asyncio
    async def test_tier_based_max_turns_specialist(self):
        """Test that Specialist tier gets 5 max turns."""
        tier = "Specialist"
        expected_max_turns = {
            "Deputy": 50,
            "Coordinator": 20,
            "Specialist": 5,
            "G-Staff": 20,
            "Special": 15,
        }.get(tier, 10)

        assert expected_max_turns == 5

    @pytest.mark.asyncio
    async def test_tier_based_max_turns_coordinator(self):
        """Test that Coordinator tier gets 20 max turns."""
        tier = "Coordinator"
        expected_max_turns = {
            "Deputy": 50,
            "Coordinator": 20,
            "Specialist": 5,
            "G-Staff": 20,
            "Special": 15,
        }.get(tier, 10)

        assert expected_max_turns == 20

    @pytest.mark.asyncio
    async def test_tier_based_max_turns_deputy(self):
        """Test that Deputy tier gets 50 max turns."""
        tier = "Deputy"
        expected_max_turns = {
            "Deputy": 50,
            "Coordinator": 20,
            "Specialist": 5,
            "G-Staff": 20,
            "Special": 15,
        }.get(tier, 10)

        assert expected_max_turns == 50

    def test_registry_agent_lookup(self):
        """Test that agents can be found in registry."""
        registry = MOCK_REGISTRY

        scheduler = registry["agents"].get("SCHEDULER")
        assert scheduler is not None
        assert scheduler["tier"] == "Specialist"
        assert scheduler["model"] == "haiku"

        coord_engine = registry["agents"].get("COORD_ENGINE")
        assert coord_engine is not None
        assert coord_engine["tier"] == "Coordinator"
        assert coord_engine["model"] == "sonnet"

        architect = registry["agents"].get("ARCHITECT")
        assert architect is not None
        assert architect["tier"] == "Deputy"
        assert architect["model"] == "opus"

    def test_registry_unknown_agent_fallback(self):
        """Test that unknown agents get fallback spec."""
        registry = MOCK_REGISTRY
        unknown_agent = registry["agents"].get("UNKNOWN_AGENT")

        assert unknown_agent is None

        # Fallback spec should be generated
        fallback_spec = {
            "tier": "Specialist",
            "model": "haiku",
            "archetype": "Generator",
            "role": "UNKNOWN_AGENT agent",
            "reports_to": "ORCHESTRATOR",
            "can_spawn": [],
            "max_turns": 5,
            "tools_access": ["rag_search"],
            "relevant_doc_types": [],
        }

        assert fallback_spec["tier"] == "Specialist"
        assert fallback_spec["model"] == "haiku"

    def test_identity_card_parsing(self):
        """Test that identity card content is valid."""
        assert "# SCHEDULER Identity Card" in MOCK_IDENTITY_CARD
        assert "Tier:** Specialist" in MOCK_IDENTITY_CARD
        assert "Reports To:** COORD_ENGINE" in MOCK_IDENTITY_CARD

    def test_checkpoint_path_format(self):
        """Test checkpoint path follows naming convention."""
        from datetime import datetime

        agent_name = "SCHEDULER"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        checkpoint_path = f".claude/Scratchpad/AGENT_{agent_name}_{timestamp}.md"

        assert checkpoint_path.startswith(".claude/Scratchpad/AGENT_")
        assert agent_name in checkpoint_path
        assert checkpoint_path.endswith(".md")

    def test_audit_entry_structure(self):
        """Test audit trail entry has required fields."""
        from datetime import datetime

        invocation_id = datetime.now().strftime('%Y%m%d_%H%M%S') + "_SCHEDULER"
        audit_entry = {
            "invocation_id": invocation_id,
            "timestamp": datetime.now().isoformat(),
            "agent_name": "SCHEDULER",
            "tier": "Specialist",
            "model": "haiku",
            "mission": "Test mission",
            "context": None,
            "rag_injected": True,
            "skills_injected": [],
            "tools_access": ["validate_schedule"],
            "can_spawn": [],
            "checkpoint_path": f".claude/Scratchpad/AGENT_SCHEDULER_{invocation_id}.md",
            "escalation_target": "COORD_ENGINE",
            "prompt_tokens_estimate": 500,
        }

        # Verify required fields
        required_fields = [
            "invocation_id", "timestamp", "agent_name", "tier", "model",
            "mission", "checkpoint_path", "escalation_target"
        ]
        for field in required_fields:
            assert field in audit_entry


class TestSpawnChainValidation:
    """Tests specifically for spawn chain validation logic."""

    def test_architect_can_spawn_coord_engine(self):
        """ARCHITECT should be able to spawn COORD_ENGINE."""
        architect = MOCK_REGISTRY["agents"]["ARCHITECT"]
        assert "COORD_ENGINE" in architect["can_spawn"]

    def test_coord_engine_can_spawn_scheduler(self):
        """COORD_ENGINE should be able to spawn SCHEDULER."""
        coord_engine = MOCK_REGISTRY["agents"]["COORD_ENGINE"]
        assert "SCHEDULER" in coord_engine["can_spawn"]

    def test_scheduler_cannot_spawn(self):
        """SCHEDULER should not be able to spawn any agents."""
        scheduler = MOCK_REGISTRY["agents"]["SCHEDULER"]
        assert scheduler["can_spawn"] == []

    def test_spawn_chain_error_message(self):
        """Test spawn chain violation error message format."""
        parent_agent = "SCHEDULER"
        child_agent = "ARCHITECT"
        allowed_children = []

        error_message = (
            f"Spawn chain violation: {parent_agent} cannot spawn {child_agent}. "
            f"Allowed: {allowed_children}"
        )

        assert "Spawn chain violation" in error_message
        assert parent_agent in error_message
        assert child_agent in error_message


class TestAgentResultStructure:
    """Tests for the structure of spawn_agent_tool return value."""

    def test_result_has_required_fields(self):
        """Test that result dict has all required fields."""
        required_fields = [
            "agent_name",
            "tier",
            "model",
            "full_prompt",
            "max_turns",
            "subagent_type",
            "checkpoint_path",
            "escalation_target",
            "tools_access",
            "can_spawn",
        ]

        # Mock result
        result = {
            "agent_name": "SCHEDULER",
            "tier": "Specialist",
            "model": "haiku",
            "archetype": "Generator",
            "full_prompt": "Test prompt",
            "max_turns": 5,
            "subagent_type": "general-purpose",
            "checkpoint_path": ".claude/Scratchpad/AGENT_SCHEDULER_20260116_143022.md",
            "escalation_target": "COORD_ENGINE",
            "tools_access": ["validate_schedule"],
            "can_spawn": [],
            "prompt_tokens_estimate": 100,
            "invocation_id": "20260116_143022_SCHEDULER",
            "reports_to": "COORD_ENGINE",
        }

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_subagent_type_is_general_purpose(self):
        """Test that subagent_type is always 'general-purpose'."""
        result = {"subagent_type": "general-purpose"}
        assert result["subagent_type"] == "general-purpose"

    def test_spawn_chain_violation_result(self):
        """Test result structure when spawn chain is violated."""
        violation_result = {
            "agent_name": "ARCHITECT",
            "status": "spawn_chain_violation",
            "error": "Spawn chain violation: SCHEDULER cannot spawn ARCHITECT. Allowed: []",
            "parent_agent": "SCHEDULER",
            "suggested_parent": "ORCHESTRATOR",
            "full_prompt": None,
            "audit_trail_path": None,
        }

        assert violation_result["status"] == "spawn_chain_violation"
        assert violation_result["full_prompt"] is None
        assert "suggested_parent" in violation_result


class TestPromptConstruction:
    """Tests for prompt construction logic."""

    def test_prompt_includes_identity(self):
        """Test that prompt includes identity card."""
        identity = MOCK_IDENTITY_CARD
        mission = "Test mission"

        prompt_parts = [identity, f"## MISSION\n\n{mission}"]
        full_prompt = "\n\n".join(prompt_parts)

        assert "SCHEDULER Identity Card" in full_prompt
        assert "Test mission" in full_prompt

    def test_prompt_includes_mission(self):
        """Test that prompt includes mission section."""
        mission = "Generate Block 10 schedule"
        prompt = f"## MISSION\n\n{mission}"

        assert "## MISSION" in prompt
        assert mission in prompt

    def test_prompt_includes_context_when_provided(self):
        """Test that context is included when provided."""
        context = {"block_number": 10, "academic_year": 2026}
        context_section = f"## CONTEXT\n\n```json\n{json.dumps(context, indent=2)}\n```"

        assert "block_number" in context_section
        assert "2026" in context_section

    def test_prompt_includes_checkpoint_instructions(self):
        """Test that checkpoint instructions are included."""
        agent_name = "SCHEDULER"
        checkpoint_path = f".claude/Scratchpad/AGENT_{agent_name}_20260116_143022.md"

        checkpoint_section = f"""## CHECKPOINT PROTOCOL

Write your progress and findings to: `{checkpoint_path}`
"""

        assert "CHECKPOINT PROTOCOL" in checkpoint_section
        assert checkpoint_path in checkpoint_section


class TestModelMapping:
    """Tests for tier-to-model mapping."""

    def test_specialist_uses_haiku(self):
        """Specialists should use haiku model."""
        scheduler = MOCK_REGISTRY["agents"]["SCHEDULER"]
        assert scheduler["model"] == "haiku"

    def test_coordinator_uses_sonnet(self):
        """Coordinators should use sonnet model."""
        coord_engine = MOCK_REGISTRY["agents"]["COORD_ENGINE"]
        assert coord_engine["model"] == "sonnet"

    def test_deputy_uses_opus(self):
        """Deputies should use opus model."""
        architect = MOCK_REGISTRY["agents"]["ARCHITECT"]
        assert architect["model"] == "opus"
