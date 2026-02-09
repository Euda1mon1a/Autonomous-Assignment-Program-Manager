"""Tests for llm_router.py — CircuitBreaker and task classification.

Tests:
- CircuitBreaker state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- LLMRouter.classify_task heuristic routing
- No external HTTP/LLM calls needed
"""

from datetime import datetime, timedelta

import pytest

from app.services.llm_router import CircuitBreaker, LLMRouter


# ============================================================================
# CircuitBreaker
# ============================================================================


class TestCircuitBreakerInit:
    """Test initialization and defaults."""

    def test_default_thresholds(self):
        cb = CircuitBreaker()
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60
        assert cb.half_open_max_calls == 3

    def test_custom_thresholds(self):
        cb = CircuitBreaker(
            failure_threshold=3, recovery_timeout=30, half_open_max_calls=1
        )
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert cb.half_open_max_calls == 1

    def test_no_initial_states(self):
        cb = CircuitBreaker()
        assert len(cb._states) == 0


class TestCircuitBreakerGetState:
    """Test state initialization and retrieval."""

    def test_new_provider_gets_closed_state(self):
        cb = CircuitBreaker()
        state = cb.get_state("test_provider")
        assert state.state == "closed"
        assert state.failure_count == 0
        assert state.provider == "test_provider"

    def test_same_provider_returns_same_state(self):
        cb = CircuitBreaker()
        state1 = cb.get_state("test_provider")
        state2 = cb.get_state("test_provider")
        assert state1 is state2

    def test_different_providers_get_different_states(self):
        cb = CircuitBreaker()
        state_a = cb.get_state("provider_a")
        state_b = cb.get_state("provider_b")
        assert state_a is not state_b


class TestCircuitBreakerCanExecute:
    """Test the can_execute state machine logic."""

    def test_closed_allows_execution(self):
        cb = CircuitBreaker()
        assert cb.can_execute("test") is True

    def test_open_blocks_execution(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure("test")
        cb.record_failure("test")  # Opens circuit
        assert cb.can_execute("test") is False

    def test_open_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
        cb.record_failure("test")  # Opens circuit

        # Simulate time passing beyond recovery timeout
        state = cb.get_state("test")
        state.next_retry = datetime.utcnow() - timedelta(seconds=1)

        assert cb.can_execute("test") is True
        assert state.state == "half_open"

    def test_half_open_allows_execution(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure("test")  # Opens circuit

        # Manually set to half_open
        state = cb.get_state("test")
        state.state = "half_open"

        assert cb.can_execute("test") is True

    def test_open_stays_open_before_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=3600)
        cb.record_failure("test")

        state = cb.get_state("test")
        assert state.state == "open"
        assert cb.can_execute("test") is False


class TestCircuitBreakerRecordSuccess:
    """Test success recording."""

    def test_success_in_half_open_closes_circuit(self):
        cb = CircuitBreaker()
        state = cb.get_state("test")
        state.state = "half_open"
        state.failure_count = 3

        cb.record_success("test")

        assert state.state == "closed"
        assert state.failure_count == 0

    def test_success_in_closed_no_change(self):
        cb = CircuitBreaker()
        state = cb.get_state("test")
        state.state = "closed"
        state.failure_count = 2

        cb.record_success("test")

        # No change for closed state
        assert state.state == "closed"
        assert state.failure_count == 2


class TestCircuitBreakerRecordFailure:
    """Test failure recording and circuit opening."""

    def test_failure_increments_count(self):
        cb = CircuitBreaker()
        cb.record_failure("test")
        state = cb.get_state("test")
        assert state.failure_count == 1

    def test_failure_below_threshold_stays_closed(self):
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            cb.record_failure("test")
        state = cb.get_state("test")
        assert state.state == "closed"

    def test_failure_at_threshold_opens_circuit(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure("test")
        state = cb.get_state("test")
        assert state.state == "open"
        assert state.next_retry is not None

    def test_failure_sets_last_failure(self):
        cb = CircuitBreaker()
        before = datetime.utcnow()
        cb.record_failure("test")
        state = cb.get_state("test")
        assert state.last_failure is not None
        assert state.last_failure >= before

    def test_failure_sets_next_retry(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=120)
        before = datetime.utcnow()
        cb.record_failure("test")
        state = cb.get_state("test")
        assert state.next_retry is not None
        expected_min = before + timedelta(seconds=119)
        assert state.next_retry >= expected_min


class TestCircuitBreakerFullCycle:
    """Test complete state machine cycle."""

    def test_closed_to_open_to_half_open_to_closed(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Start closed
        assert cb.can_execute("test") is True
        state = cb.get_state("test")
        assert state.state == "closed"

        # Fail enough to open
        cb.record_failure("test")
        cb.record_failure("test")
        assert state.state == "open"
        assert cb.can_execute("test") is False

        # Simulate timeout
        state.next_retry = datetime.utcnow() - timedelta(seconds=1)

        # Should transition to half_open
        assert cb.can_execute("test") is True
        assert state.state == "half_open"

        # Success closes circuit
        cb.record_success("test")
        assert state.state == "closed"
        assert state.failure_count == 0

    def test_half_open_failure_reopens(self):
        cb = CircuitBreaker(failure_threshold=1)

        # Open the circuit
        cb.record_failure("test")
        state = cb.get_state("test")
        assert state.state == "open"

        # Transition to half_open
        state.state = "half_open"
        state.failure_count = 0

        # Fail again in half_open reopens
        cb.record_failure("test")
        assert state.state == "open"


class TestCircuitBreakerMultiProvider:
    """Test independent tracking per provider."""

    def test_independent_states(self):
        cb = CircuitBreaker(failure_threshold=2)

        # Fail provider A
        cb.record_failure("a")
        cb.record_failure("a")
        assert cb.get_state("a").state == "open"

        # Provider B unaffected
        assert cb.get_state("b").state == "closed"
        assert cb.can_execute("b") is True


# ============================================================================
# LLMRouter.classify_task
# ============================================================================


class TestClassifyTask:
    """Test heuristic task classification."""

    @pytest.fixture
    def router(self):
        """Create router in airgap mode (no cloud provider init)."""
        return LLMRouter(airgap_mode=True)

    @pytest.mark.asyncio
    async def test_privacy_sensitive(self, router):
        result = await router.classify_task("Show me the patient records")
        assert result.task_type == "privacy_sensitive"
        assert result.is_privacy_sensitive is True

    @pytest.mark.asyncio
    async def test_privacy_phi(self, router):
        result = await router.classify_task("Look up PHI for this visit")
        assert result.is_privacy_sensitive is True

    @pytest.mark.asyncio
    async def test_privacy_hipaa(self, router):
        result = await router.classify_task("Ensure HIPAA compliance for this data")
        assert result.is_privacy_sensitive is True

    @pytest.mark.asyncio
    async def test_tool_calling(self, router):
        result = await router.classify_task(
            "What is the weather?", tools=[{"name": "weather"}]
        )
        assert result.task_type == "tool_calling"
        assert result.requires_tools is True

    @pytest.mark.asyncio
    async def test_multi_step_analyze(self, router):
        result = await router.classify_task(
            "Please analyze the scheduling patterns for the past quarter"
        )
        assert result.task_type == "multi_step"

    @pytest.mark.asyncio
    async def test_multi_step_comprehensive(self, router):
        result = await router.classify_task(
            "Give a comprehensive review of the rotation assignments"
        )
        assert result.task_type == "multi_step"

    @pytest.mark.asyncio
    async def test_code_generation(self, router):
        result = await router.classify_task("Write a function to parse dates")
        assert result.task_type == "code_generation"

    @pytest.mark.asyncio
    async def test_code_implement(self, router):
        result = await router.classify_task("Implement the validation logic")
        assert result.task_type == "code_generation"

    @pytest.mark.asyncio
    async def test_simple_query(self, router):
        result = await router.classify_task("What is Block 7?")
        assert result.task_type == "simple_query"
        assert result.complexity_score < 0.5

    @pytest.mark.asyncio
    async def test_explanation_default(self, router):
        """Longer prompts without specific keywords default to explanation."""
        long_prompt = " ".join(["word"] * 25)
        result = await router.classify_task(long_prompt)
        assert result.task_type == "explanation"

    @pytest.mark.asyncio
    async def test_privacy_takes_priority(self, router):
        """Privacy classification takes priority over other keywords."""
        result = await router.classify_task("Analyze the patient data comprehensively")
        assert result.task_type == "privacy_sensitive"

    @pytest.mark.asyncio
    async def test_airgap_mode_local_provider(self, router):
        """Airgap mode routes tool_calling to local provider."""
        result = await router.classify_task("test", tools=[{"name": "t"}])
        assert result.recommended_provider == "mlx"
