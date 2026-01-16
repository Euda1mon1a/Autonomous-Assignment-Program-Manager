"""
Tests for PAI Identity Loader.

Tests the parsing of agent identity cards from .claude/Identities/ directory.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scheduler_mcp.pai_bridge.identity_loader import IdentityLoader
from scheduler_mcp.pai_bridge.models import AgentIdentity


# Sample identity card content for testing
SAMPLE_IDENTITY_CARD = """# SCHEDULER Identity Card

## Identity
- **Role:** Schedule generation specialist - CP-SAT solver operations and ACGME compliance
- **Tier:** Specialist
- **Model:** haiku
## Boot Instruction (EXECUTE FIRST)
Read `.claude/Governance/CAPABILITIES.md` to discover your available tools and skills.

## Chain of Command
- **Reports To:** COORD_ENGINE
- **Can Spawn:** None (terminal specialist)
- **Escalate To:** COORD_ENGINE

## Standing Orders (Execute Without Asking)
1. Generate schedules using CP-SAT solver with defined constraints
2. Validate all schedules against ACGME compliance rules
3. Create database backups before any schedule write operations
4. Run constraint propagation and optimization loops
5. Log solver metrics and decision variables

## Escalation Triggers (MUST Escalate)
- ACGME violations detected in generated schedule
- Solver timeout exceeding 5 minutes
- Unresolvable constraint conflicts
- Resource exhaustion (memory/CPU)
- Database backup failures before write operations

## Key Constraints
- Do NOT write schedules without backup verification
- Do NOT modify ACGME compliance rules
- Do NOT skip constraint validation steps
- Do NOT proceed if solver is infeasible

## One-Line Charter
"Generate compliant schedules efficiently, validate exhaustively, protect data religiously."
"""

SAMPLE_COORDINATOR_CARD = """# COORD_ENGINE Identity Card

## Identity
- **Role:** Coordinator for Scheduling Engine and Optimization
- **Tier:** Coordinator
- **Model:** sonnet

## Chain of Command
- **Reports To:** ARCHITECT
- **Can Spawn:** SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
- **Escalate To:** ARCHITECT

## Standing Orders (Execute Without Asking)
1. Generate resident schedules using constraint programming
2. Validate ACGME compliance
3. Execute resident swap requests with safety checks

## Escalation Triggers (MUST Escalate)
- ACGME compliance violations in generated schedules
- Solver failures or infinite loops
- Cross-rotation conflicts requiring policy decisions

## Key Constraints
- Do NOT generate schedules without ACGME validation
- Do NOT execute swaps without constraint verification
- Do NOT bypass resilience framework

## One-Line Charter
"Generate compliant, fair, and optimized schedules."
"""


class TestIdentityLoader:
    """Tests for IdentityLoader class."""

    def test_parse_specialist_identity(self):
        """Test parsing a specialist identity card."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        identity = loader._parse_identity("SCHEDULER", SAMPLE_IDENTITY_CARD)

        assert identity.name == "SCHEDULER"
        assert identity.role == "Schedule generation specialist - CP-SAT solver operations and ACGME compliance"
        assert identity.tier == "Specialist"
        assert identity.model == "haiku"
        assert identity.reports_to == "COORD_ENGINE"
        assert identity.can_spawn == []  # Terminal specialist
        assert identity.escalate_to == "COORD_ENGINE"

        # Check standing orders
        assert len(identity.standing_orders) == 5
        assert "Generate schedules using CP-SAT solver" in identity.standing_orders[0]

        # Check escalation triggers
        assert len(identity.escalation_triggers) == 5
        assert "ACGME violations detected" in identity.escalation_triggers[0]

        # Check constraints
        assert len(identity.constraints) == 4
        assert "Do NOT write schedules without backup verification" in identity.constraints[0]

        # Check charter
        assert "Generate compliant schedules" in identity.charter

    def test_parse_coordinator_identity(self):
        """Test parsing a coordinator identity card with spawn authority."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        identity = loader._parse_identity("COORD_ENGINE", SAMPLE_COORDINATOR_CARD)

        assert identity.name == "COORD_ENGINE"
        assert identity.tier == "Coordinator"
        assert identity.model == "sonnet"
        assert identity.reports_to == "ARCHITECT"

        # Coordinator can spawn specialists
        assert len(identity.can_spawn) == 3
        assert "SCHEDULER" in identity.can_spawn
        assert "SWAP_MANAGER" in identity.can_spawn
        assert "OPTIMIZATION_SPECIALIST" in identity.can_spawn

    def test_extract_field(self):
        """Test field extraction with regex."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        content = "- **Role:** Test role description"
        result = loader._extract_field(content, r"\*\*Role:\*\*\s*(.+)")
        assert result == "Test role description"

    def test_extract_field_not_found(self):
        """Test field extraction when field not present."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        content = "Some other content"
        result = loader._extract_field(content, r"\*\*Role:\*\*\s*(.+)")
        assert result == ""

    def test_extract_numbered_list(self):
        """Test extraction of numbered list items."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        content = """## Standing Orders
1. First order
2. Second order
3. Third order
"""
        result = loader._extract_numbered_list(content, r"## Standing Orders\n((?:\d+\..+\n?)+)")
        assert len(result) == 3
        assert result[0] == "First order"
        assert result[1] == "Second order"
        assert result[2] == "Third order"

    def test_extract_bullet_list(self):
        """Test extraction of bullet list items."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        content = """## Key Constraints
- First constraint
- Second constraint
"""
        result = loader._extract_bullet_list(content, r"## Key Constraints\n((?:-.+\n?)+)")
        assert len(result) == 2
        assert result[0] == "First constraint"
        assert result[1] == "Second constraint"

    def test_terminal_specialist_has_no_spawn(self):
        """Test that terminal specialists have empty can_spawn."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        identity = loader._parse_identity("SCHEDULER", SAMPLE_IDENTITY_CARD)
        assert identity.can_spawn == []

    def test_cache_functionality(self):
        """Test that identity cards are cached."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        # Manually add to cache
        mock_identity = AgentIdentity(
            name="TEST_AGENT",
            role="Test role",
            tier="Specialist",
            model="haiku",
            reports_to="COORD_TEST",
        )
        loader._cache["TEST_AGENT"] = mock_identity

        # Should return cached value
        result = loader.load_sync("TEST_AGENT")
        assert result == mock_identity

    def test_clear_cache(self):
        """Test cache clearing."""
        loader = IdentityLoader(Path("/tmp/test_identities"))

        # Add to cache
        loader._cache["TEST_AGENT"] = AgentIdentity(
            name="TEST_AGENT",
            role="Test",
            tier="Specialist",
            model="haiku",
            reports_to="COORD_TEST",
        )

        assert len(loader._cache) == 1

        loader.clear_cache()

        assert len(loader._cache) == 0


class TestIdentityLoaderAsync:
    """Async tests for IdentityLoader."""

    @pytest.mark.asyncio
    async def test_load_identity_not_found(self, tmp_path):
        """Test loading non-existent identity card."""
        loader = IdentityLoader(tmp_path)

        result = await loader.load("NONEXISTENT_AGENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_load_identity_from_file(self, tmp_path):
        """Test loading identity card from file."""
        # Create test identity file
        identity_file = tmp_path / "TEST_AGENT.identity.md"
        identity_file.write_text(SAMPLE_IDENTITY_CARD.replace("SCHEDULER", "TEST_AGENT"))

        loader = IdentityLoader(tmp_path)
        result = await loader.load("TEST_AGENT")

        assert result is not None
        assert result.name == "TEST_AGENT"
        assert result.tier == "Specialist"

    @pytest.mark.asyncio
    async def test_list_available_agents(self, tmp_path):
        """Test listing available agents."""
        # Create test identity files
        (tmp_path / "AGENT_A.identity.md").write_text(SAMPLE_IDENTITY_CARD)
        (tmp_path / "AGENT_B.identity.md").write_text(SAMPLE_COORDINATOR_CARD)
        (tmp_path / "other_file.md").write_text("Not an identity")

        loader = IdentityLoader(tmp_path)
        agents = loader.list_available_agents()

        assert len(agents) == 2
        assert "AGENT_A" in agents
        assert "AGENT_B" in agents
