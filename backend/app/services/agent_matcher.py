"""Agent Skill Matcher Service - ML-powered agent selection for PAI orchestration.

Uses sentence-transformers embeddings to match incoming tasks with the most
appropriate agent based on semantic similarity of task descriptions to
agent capabilities.

This implements Task 9.4 from ML_RESEARCH_PAI_ADVANCEMENT.md:
"Semantic matching of task descriptions to agent capabilities"
"""

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
from numpy.typing import NDArray

from app.services.embedding_service import EmbeddingService, get_cached_embedding

logger = logging.getLogger(__name__)


@dataclass
class AgentMatch:
    """Result of agent matching."""

    agent_name: str
    similarity_score: float
    archetype: str
    capabilities: str
    recommended_model: str


@dataclass
class AgentSpec:
    """Parsed agent specification."""

    name: str
    archetype: str
    authority_level: str
    capabilities: str
    embedding: NDArray[np.float32]


class AgentMatcher:
    """Matches tasks to agents using semantic similarity.

    Uses cosine similarity between task description embeddings and
    pre-computed agent capability embeddings to find the best match.

    Example:
        matcher = AgentMatcher()
        matches = matcher.match_task(
            "Validate ACGME compliance for the generated schedule"
        )
        best_agent = matches[0]  # Highest similarity match
    """

    # Default model tiers based on archetype complexity
    MODEL_TIERS = {
        "Researcher": "sonnet",
        "Validator": "haiku",
        "Generator": "sonnet",
        "Critic": "sonnet",
        "Synthesizer": "opus",
    }

    def __init__(
        self,
        agents_dir: Path | None = None,
        similarity_threshold: float = 0.3,
    ):
        """Initialize agent matcher.

        Args:
            agents_dir: Path to .claude/Agents/ directory. If None, uses default.
            similarity_threshold: Minimum similarity score to include in results.
        """
        self.agents_dir = agents_dir or self._find_agents_dir()
        self.similarity_threshold = similarity_threshold
        self._agents: list[AgentSpec] = []
        self._loaded = False

    def _find_agents_dir(self) -> Path:
        """Find the .claude/Agents directory."""
        # Try common locations
        candidates = [
            Path("/home/user/Autonomous-Assignment-Program-Manager/.claude/Agents"),
            Path.cwd() / ".claude" / "Agents",
            Path(__file__).parent.parent.parent.parent / ".claude" / "Agents",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]  # Default to first option

    def load_agents(self) -> None:
        """Load and embed all agent specifications."""
        if self._loaded:
            return

        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            self._loaded = True
            return

        agent_files = list(self.agents_dir.glob("*.md"))
        logger.info(
            f"Loading {len(agent_files)} agent specifications from {self.agents_dir}"
        )

        for agent_file in agent_files:
            if agent_file.name in ("AGENT_FACTORY.md", "README.md"):
                continue  # Skip meta-documents

            try:
                spec = self._parse_agent_spec(agent_file)
                if spec:
                    self._agents.append(spec)
                    logger.debug(f"Loaded agent: {spec.name} ({spec.archetype})")
            except Exception as e:
                logger.error(f"Failed to parse agent spec {agent_file}: {e}")

        self._loaded = True
        logger.info(f"Loaded {len(self._agents)} agents for matching")

    def _parse_agent_spec(self, file_path: Path) -> AgentSpec | None:
        """Parse an agent specification markdown file.

        Args:
            file_path: Path to agent .md file

        Returns:
            Parsed AgentSpec or None if parsing fails
        """
        content = file_path.read_text()
        name = file_path.stem  # Filename without extension

        # Extract archetype from header
        archetype = "Generator"  # Default
        for line in content.split("\n"):
            if "Archetype:" in line:
                archetype = line.split(":")[-1].strip().strip("*")
                break

        # Extract authority level
        authority_level = "Propose-Only"  # Default
        for line in content.split("\n"):
            if "Authority Level:" in line:
                authority_level = line.split(":")[-1].strip().strip("*")
                break

        # Extract capabilities from charter and responsibilities sections
        capabilities_parts = []

        # Get role description
        for line in content.split("\n"):
            if "Role:" in line:
                role = line.split(":", 1)[-1].strip().strip("*")
                capabilities_parts.append(role)
                break

        # Get primary responsibilities
        in_responsibilities = False
        for line in content.split("\n"):
            if "Primary Responsibilities:" in line:
                in_responsibilities = True
                continue
            if in_responsibilities:
                if line.startswith("- "):
                    capabilities_parts.append(line[2:].strip())
                elif line.strip() and not line.startswith("-"):
                    in_responsibilities = False

        capabilities = " ".join(capabilities_parts) if capabilities_parts else name

        # Generate embedding for capabilities
        embedding_list = EmbeddingService.embed_text(capabilities)
        embedding = np.array(embedding_list, dtype=np.float32)

        return AgentSpec(
            name=name,
            archetype=archetype,
            authority_level=authority_level,
            capabilities=capabilities,
            embedding=embedding,
        )

    def match_task(
        self,
        task_description: str,
        top_k: int = 3,
    ) -> list[AgentMatch]:
        """Match a task description to the best agents.

        Args:
            task_description: Natural language description of the task
            top_k: Maximum number of matches to return

        Returns:
            List of AgentMatch objects sorted by similarity (highest first)
        """
        self.load_agents()

        if not self._agents:
            logger.warning("No agents loaded, cannot match task")
            return []

        # Get task embedding (cached for repeated queries)
        task_embedding = np.array(
            get_cached_embedding(task_description), dtype=np.float32
        )

        # Calculate cosine similarity with all agents
        matches = []
        for agent in self._agents:
            similarity = self._cosine_similarity(task_embedding, agent.embedding)

            if similarity >= self.similarity_threshold:
                matches.append(
                    AgentMatch(
                        agent_name=agent.name,
                        similarity_score=float(similarity),
                        archetype=agent.archetype,
                        capabilities=agent.capabilities[:200] + "..."
                        if len(agent.capabilities) > 200
                        else agent.capabilities,
                        recommended_model=self.MODEL_TIERS.get(
                            agent.archetype, "sonnet"
                        ),
                    )
                )

        # Sort by similarity (descending)
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        return matches[:top_k]

    def _cosine_similarity(
        self,
        a: NDArray[np.float32],
        b: NDArray[np.float32],
    ) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity score (0 to 1)
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_agent_for_task(
        self,
        task_description: str,
        fallback_agent: str = "SCHEDULER",
    ) -> tuple[str, str]:
        """Get the single best agent for a task.

        Args:
            task_description: Natural language description of the task
            fallback_agent: Agent to use if no match found

        Returns:
            Tuple of (agent_name, recommended_model)
        """
        matches = self.match_task(task_description, top_k=1)

        if matches:
            return matches[0].agent_name, matches[0].recommended_model

        logger.warning(
            f"No agent match found for task, using fallback: {fallback_agent}"
        )
        return fallback_agent, "sonnet"

    def explain_match(
        self,
        task_description: str,
    ) -> dict:
        """Explain why agents were matched to a task.

        Args:
            task_description: Natural language description of the task

        Returns:
            Dictionary with matching explanation
        """
        matches = self.match_task(task_description, top_k=5)

        return {
            "task": task_description,
            "task_embedding_preview": list(get_cached_embedding(task_description)[:5]),
            "matches": [
                {
                    "agent": m.agent_name,
                    "score": round(m.similarity_score, 4),
                    "archetype": m.archetype,
                    "model": m.recommended_model,
                    "capabilities_snippet": m.capabilities,
                }
                for m in matches
            ],
            "recommendation": matches[0].agent_name if matches else None,
            "confidence": "high"
            if matches and matches[0].similarity_score > 0.6
            else "medium"
            if matches and matches[0].similarity_score > 0.4
            else "low",
        }


# Module-level singleton for convenience
_matcher: AgentMatcher | None = None


def get_agent_matcher() -> AgentMatcher:
    """Get or create the global agent matcher instance."""
    global _matcher
    if _matcher is None:
        _matcher = AgentMatcher()
    return _matcher


def match_task_to_agent(task_description: str) -> tuple[str, str]:
    """Convenience function to match a task to the best agent.

    Args:
        task_description: Natural language description of the task

    Returns:
        Tuple of (agent_name, recommended_model)
    """
    return get_agent_matcher().get_agent_for_task(task_description)
