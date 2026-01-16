"""
Identity Loader for PAI Agent MCP Bridge.

Loads and parses agent identity cards from .claude/Identities/ directory.
Identity cards define agent capabilities, constraints, and chain of command.
"""

import logging
import re
from pathlib import Path

from .models import AgentIdentity

logger = logging.getLogger(__name__)


class IdentityLoader:
    """
    Loads and parses PAI agent identity cards.

    Identity cards are markdown files in .claude/Identities/ that define:
    - Agent role and tier
    - Chain of command (reports to, can spawn, escalate to)
    - Standing orders (pre-authorized actions)
    - Escalation triggers (when to escalate)
    - Key constraints (what NOT to do)
    - One-line charter (mission philosophy)
    """

    def __init__(self, identities_path: Path | str | None = None):
        """
        Initialize the loader.

        Args:
            identities_path: Path to .claude/Identities/ directory.
                           If None, uses default relative to project root.
        """
        if identities_path is None:
            # Default to project root's .claude/Identities/
            self.identities_path = Path(".claude/Identities")
        else:
            self.identities_path = Path(identities_path)

        self._cache: dict[str, AgentIdentity] = {}
        logger.info(f"IdentityLoader initialized with path: {self.identities_path}")

    async def load(self, agent_name: str) -> AgentIdentity | None:
        """
        Load identity card for an agent.

        Args:
            agent_name: Agent name (e.g., "SCHEDULER", "COORD_ENGINE")

        Returns:
            Parsed AgentIdentity or None if not found
        """
        # Check cache first
        if agent_name in self._cache:
            logger.debug(f"Returning cached identity for {agent_name}")
            return self._cache[agent_name]

        # Find identity file
        identity_file = self.identities_path / f"{agent_name}.identity.md"

        if not identity_file.exists():
            logger.warning(f"Identity file not found: {identity_file}")
            return None

        # Parse identity
        try:
            content = identity_file.read_text(encoding="utf-8")
            identity = self._parse_identity(agent_name, content)
            self._cache[agent_name] = identity
            logger.info(f"Loaded identity for {agent_name}: {identity.role}")
            return identity
        except Exception as e:
            logger.error(f"Error parsing identity for {agent_name}: {e}")
            return None

    def load_sync(self, agent_name: str) -> AgentIdentity | None:
        """
        Synchronous version of load() for non-async contexts.

        Args:
            agent_name: Agent name

        Returns:
            Parsed AgentIdentity or None if not found
        """
        # Check cache first
        if agent_name in self._cache:
            return self._cache[agent_name]

        # Find identity file
        identity_file = self.identities_path / f"{agent_name}.identity.md"

        if not identity_file.exists():
            logger.warning(f"Identity file not found: {identity_file}")
            return None

        try:
            content = identity_file.read_text(encoding="utf-8")
            identity = self._parse_identity(agent_name, content)
            self._cache[agent_name] = identity
            return identity
        except Exception as e:
            logger.error(f"Error parsing identity for {agent_name}: {e}")
            return None

    def _parse_identity(self, name: str, content: str) -> AgentIdentity:
        """
        Parse identity card markdown into AgentIdentity.

        Args:
            name: Agent name
            content: Raw markdown content

        Returns:
            Parsed AgentIdentity
        """
        # Extract single-value fields
        role = self._extract_field(content, r"\*\*Role:\*\*\s*(.+)")
        tier = self._extract_field(content, r"\*\*Tier:\*\*\s*(\w+)")
        model = self._extract_field(content, r"\*\*Model:\*\*\s*(\w+)")
        reports_to = self._extract_field(content, r"\*\*Reports To:\*\*\s*(\w+)")
        escalate_to = self._extract_field(content, r"\*\*Escalate To:\*\*\s*(\w+)")

        # Parse Can Spawn (could be "None (terminal)" or comma-separated list)
        can_spawn_raw = self._extract_field(content, r"\*\*Can Spawn:\*\*\s*(.+)")
        if "None" in can_spawn_raw or "terminal" in can_spawn_raw.lower():
            can_spawn = []
        else:
            can_spawn = [s.strip() for s in can_spawn_raw.split(",") if s.strip()]

        # Extract list sections using section-aware extraction
        standing_orders = self._extract_numbered_list(
            content, r"## Standing Orders.*?\n((?:\d+\..+\n?)+)"
        )
        escalation_triggers = self._extract_section_bullet_list(
            content, "Escalation Triggers"
        )
        constraints = self._extract_section_bullet_list(
            content, "Key Constraints"
        )

        # Extract charter (quoted string)
        charter_match = re.search(r'## One-Line Charter\s*\n"(.+)"', content)
        charter = charter_match.group(1) if charter_match else ""

        return AgentIdentity(
            name=name,
            role=role,
            tier=tier,
            model=model,
            reports_to=reports_to,
            can_spawn=can_spawn,
            escalate_to=escalate_to or reports_to,  # Default to reports_to
            standing_orders=standing_orders,
            escalation_triggers=escalation_triggers,
            constraints=constraints,
            charter=charter,
            raw_content=content,
        )

    def _extract_field(self, content: str, pattern: str) -> str:
        """Extract a single field using regex."""
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""

    def _extract_numbered_list(self, content: str, section_pattern: str) -> list[str]:
        """Extract items from a numbered list section (1. item, 2. item)."""
        match = re.search(section_pattern, content, re.DOTALL)
        if not match:
            return []

        items_text = match.group(1)
        items = re.findall(r"\d+\.\s*(.+)", items_text)
        return [item.strip() for item in items]

    def _extract_bullet_list(self, content: str, section_pattern: str) -> list[str]:
        """Extract items from a bullet list section (- item)."""
        match = re.search(section_pattern, content, re.DOTALL)
        if not match:
            return []

        items_text = match.group(1)
        items = re.findall(r"-\s*(.+)", items_text)
        return [item.strip() for item in items]

    def _extract_section_bullet_list(self, content: str, section_name: str) -> list[str]:
        """
        Extract bullet list items from a named section.

        This method properly handles section boundaries by stopping
        at the next ## header.

        Args:
            content: Full markdown content
            section_name: Name of section (e.g., "Escalation Triggers")

        Returns:
            List of bullet point items
        """
        # Find section header
        header_pattern = rf"## {re.escape(section_name)}.*?\n"
        header_match = re.search(header_pattern, content)
        if not header_match:
            return []

        # Get content from section start to next ## or end
        start_pos = header_match.end()
        remaining = content[start_pos:]

        # Find next section header (## followed by word char)
        next_section = re.search(r"\n##\s+\w", remaining)
        if next_section:
            section_content = remaining[:next_section.start()]
        else:
            section_content = remaining

        # Extract bullet items from this section only
        items = re.findall(r"^-\s*(.+)$", section_content, re.MULTILINE)
        return [item.strip() for item in items]

    def list_available_agents(self) -> list[str]:
        """
        List all available agent identity cards.

        Returns:
            List of agent names with identity cards
        """
        if not self.identities_path.exists():
            return []

        agents = []
        for path in self.identities_path.glob("*.identity.md"):
            agent_name = path.stem.replace(".identity", "")
            agents.append(agent_name)

        return sorted(agents)

    def clear_cache(self) -> None:
        """Clear the identity cache."""
        self._cache.clear()
        logger.info("Identity cache cleared")

    def preload_all(self) -> dict[str, AgentIdentity]:
        """
        Preload all identity cards into cache.

        Returns:
            Dictionary of agent_name -> AgentIdentity
        """
        agents = self.list_available_agents()
        for agent_name in agents:
            self.load_sync(agent_name)

        logger.info(f"Preloaded {len(self._cache)} identity cards")
        return self._cache.copy()
