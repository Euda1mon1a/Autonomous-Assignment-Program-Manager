"""Tests for AgentMatcher service.

Tests semantic matching of tasks to agents using embeddings.
"""

import numpy as np
import pytest

from app.services.agent_matcher import (
    AgentMatch,
    AgentMatcher,
    AgentSpec,
    get_agent_matcher,
    match_task_to_agent,
)


class TestAgentSpec:
    """Tests for AgentSpec dataclass."""

    def test_agent_spec_creation(self):
        """Test creating an AgentSpec."""
        embedding = np.zeros(384, dtype=np.float32)
        spec = AgentSpec(
            name="TEST_AGENT",
            archetype="Validator",
            authority_level="Propose-Only",
            capabilities="Test validation and checking",
            embedding=embedding,
        )

        assert spec.name == "TEST_AGENT"
        assert spec.archetype == "Validator"
        assert spec.authority_level == "Propose-Only"
        assert spec.capabilities == "Test validation and checking"
        assert spec.embedding.shape == (384,)


class TestAgentMatch:
    """Tests for AgentMatch dataclass."""

    def test_agent_match_creation(self):
        """Test creating an AgentMatch result."""
        match = AgentMatch(
            agent_name="SCHEDULER",
            similarity_score=0.85,
            archetype="Generator",
            capabilities="Schedule generation and optimization",
            recommended_model="sonnet",
        )

        assert match.agent_name == "SCHEDULER"
        assert match.similarity_score == 0.85
        assert match.archetype == "Generator"
        assert match.recommended_model == "sonnet"


class TestAgentMatcher:
    """Tests for AgentMatcher service."""

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity with identical vectors."""
        matcher = AgentMatcher()
        vec = np.random.randn(384).astype(np.float32)

        similarity = matcher._cosine_similarity(vec, vec)

        assert similarity == pytest.approx(1.0, rel=1e-5)

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity with orthogonal vectors."""
        matcher = AgentMatcher()
        vec1 = np.array([1.0, 0.0, 0.0, 0.0] + [0.0] * 380, dtype=np.float32)
        vec2 = np.array([0.0, 1.0, 0.0, 0.0] + [0.0] * 380, dtype=np.float32)

        similarity = matcher._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(0.0, abs=1e-5)

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity with opposite vectors."""
        matcher = AgentMatcher()
        vec1 = np.array([1.0, 0.0, 0.0, 0.0] + [0.0] * 380, dtype=np.float32)
        vec2 = np.array([-1.0, 0.0, 0.0, 0.0] + [0.0] * 380, dtype=np.float32)

        similarity = matcher._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(-1.0, rel=1e-5)

    def test_cosine_similarity_zero_vector(self):
        """Test cosine similarity with zero vector returns 0."""
        matcher = AgentMatcher()
        vec1 = np.zeros(384, dtype=np.float32)
        vec2 = np.random.randn(384).astype(np.float32)

        similarity = matcher._cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_model_tiers_mapping(self):
        """Test that model tiers are correctly mapped to archetypes."""
        matcher = AgentMatcher()

        assert matcher.MODEL_TIERS["Researcher"] == "sonnet"
        assert matcher.MODEL_TIERS["Validator"] == "haiku"
        assert matcher.MODEL_TIERS["Generator"] == "sonnet"
        assert matcher.MODEL_TIERS["Critic"] == "sonnet"
        assert matcher.MODEL_TIERS["Synthesizer"] == "opus"

    def test_similarity_threshold(self):
        """Test that similarity threshold is respected."""
        matcher = AgentMatcher(similarity_threshold=0.5)

        assert matcher.similarity_threshold == 0.5

    def test_match_task_returns_list(self):
        """Test that match_task returns a list."""
        matcher = AgentMatcher()
        matches = matcher.match_task("Test task description")

        assert isinstance(matches, list)

    def test_match_task_respects_top_k(self):
        """Test that match_task respects top_k parameter."""
        matcher = AgentMatcher()

        matches_1 = matcher.match_task("Generate a schedule", top_k=1)
        matches_3 = matcher.match_task("Generate a schedule", top_k=3)

        assert len(matches_1) <= 1
        assert len(matches_3) <= 3

    def test_match_task_sorted_by_similarity(self):
        """Test that matches are sorted by similarity (descending)."""
        matcher = AgentMatcher()
        matches = matcher.match_task("Validate ACGME compliance", top_k=5)

        if len(matches) > 1:
            for i in range(len(matches) - 1):
                assert matches[i].similarity_score >= matches[i + 1].similarity_score

    def test_get_agent_for_task_returns_tuple(self):
        """Test that get_agent_for_task returns agent and model tuple."""
        matcher = AgentMatcher()
        result = matcher.get_agent_for_task("Test task")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # agent name
        assert isinstance(result[1], str)  # model

    def test_get_agent_for_task_fallback(self):
        """Test fallback agent when no match found."""
        matcher = AgentMatcher(similarity_threshold=1.0)  # Impossible threshold
        agent, model = matcher.get_agent_for_task(
            "xyzzy gibberish",
            fallback_agent="FALLBACK_AGENT",
        )

        assert agent == "FALLBACK_AGENT"
        assert model == "sonnet"

    def test_explain_match_structure(self):
        """Test that explain_match returns expected structure."""
        matcher = AgentMatcher()
        explanation = matcher.explain_match("Create a schedule for residents")

        assert "task" in explanation
        assert "task_embedding_preview" in explanation
        assert "matches" in explanation
        assert "recommendation" in explanation
        assert "confidence" in explanation

        assert isinstance(explanation["matches"], list)
        assert explanation["confidence"] in ("high", "medium", "low")


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_get_agent_matcher_singleton(self):
        """Test that get_agent_matcher returns a singleton."""
        matcher1 = get_agent_matcher()
        matcher2 = get_agent_matcher()

        assert matcher1 is matcher2

    def test_match_task_to_agent_function(self):
        """Test the convenience function."""
        result = match_task_to_agent("Review code for security issues")

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestSemanticMatching:
    """Integration tests for semantic matching quality."""

    @pytest.fixture
    def matcher(self):
        """Create a matcher with some test agents."""
        matcher = AgentMatcher()
        matcher._loaded = True  # Bypass file loading

        # Create test agents with distinctive capabilities
        from app.services.embedding_service import EmbeddingService

        scheduler_embedding = EmbeddingService.embed_text(
            "Generate compliant schedules, optimize assignments, handle rotations"
        )
        validator_embedding = EmbeddingService.embed_text(
            "Validate ACGME compliance, check work hour limits, verify supervision ratios"
        )
        tester_embedding = EmbeddingService.embed_text(
            "Write tests, run pytest, ensure code coverage, test edge cases"
        )

        matcher._agents = [
            AgentSpec(
                name="SCHEDULER",
                archetype="Generator",
                authority_level="Execute with Safeguards",
                capabilities="Generate compliant schedules, optimize assignments, handle rotations",
                embedding=np.array(scheduler_embedding, dtype=np.float32),
            ),
            AgentSpec(
                name="ACGME_VALIDATOR",
                archetype="Validator",
                authority_level="Propose-Only",
                capabilities="Validate ACGME compliance, check work hour limits, verify supervision ratios",
                embedding=np.array(validator_embedding, dtype=np.float32),
            ),
            AgentSpec(
                name="QA_TESTER",
                archetype="Critic",
                authority_level="Execute with Safeguards",
                capabilities="Write tests, run pytest, ensure code coverage, test edge cases",
                embedding=np.array(tester_embedding, dtype=np.float32),
            ),
        ]

        return matcher

    def test_scheduling_task_matches_scheduler(self, matcher):
        """Test that scheduling tasks match the SCHEDULER agent."""
        matches = matcher.match_task("Create a new schedule for the residency program")

        assert len(matches) > 0
        # SCHEDULER should be highly ranked for scheduling tasks
        scheduler_match = next(
            (m for m in matches if m.agent_name == "SCHEDULER"), None
        )
        assert scheduler_match is not None
        assert scheduler_match.similarity_score > 0.3

    def test_compliance_task_matches_validator(self, matcher):
        """Test that compliance tasks match the ACGME_VALIDATOR agent."""
        matches = matcher.match_task(
            "Check if the schedule violates 80-hour work limits"
        )

        assert len(matches) > 0
        # ACGME_VALIDATOR should be highly ranked for compliance tasks
        validator_match = next(
            (m for m in matches if m.agent_name == "ACGME_VALIDATOR"), None
        )
        assert validator_match is not None
        assert validator_match.similarity_score > 0.3

    def test_testing_task_matches_tester(self, matcher):
        """Test that testing tasks match the QA_TESTER agent."""
        matches = matcher.match_task("Write unit tests for the new feature")

        assert len(matches) > 0
        # QA_TESTER should be highly ranked for testing tasks
        tester_match = next((m for m in matches if m.agent_name == "QA_TESTER"), None)
        assert tester_match is not None
        assert tester_match.similarity_score > 0.3

    def test_different_tasks_get_different_agents(self, matcher):
        """Test that semantically different tasks get different top agents."""
        schedule_matches = matcher.match_task("Generate the monthly rotation schedule")
        compliance_matches = matcher.match_task("Validate ACGME compliance rules")
        test_matches = matcher.match_task("Run the pytest test suite")

        # Each task should have a different top recommendation
        assert schedule_matches[0].agent_name != compliance_matches[0].agent_name
        assert compliance_matches[0].agent_name != test_matches[0].agent_name
