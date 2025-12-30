"""Tests for LLM Router service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.services.llm_router import (
    AnthropicProvider,
    CircuitBreaker,
    LLMProvider,
    LLMProviderError,
    LLMRouter,
    OllamaProvider,
    ProviderUnavailableError,
)
from app.schemas.llm import (
    LLMRequest,
    LLMResponse,
    LLMUsage,
    TaskClassification,
)


class TestOllamaProvider:
    """Test suite for Ollama provider."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation from Ollama."""
        provider = OllamaProvider(base_url="http://test:11434")

        # Mock httpx response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Test response",
            "done_reason": "stop",
            "prompt_eval_count": 10,
            "eval_count": 20,
        }
        mock_response.raise_for_status = Mock()

        with patch.object(provider._client, "post", return_value=mock_response):
            response = await provider.generate(
                prompt="Test prompt", system="Test system"
            )

        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.provider == "ollama"
        assert response.usage is not None
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 20

    @pytest.mark.asyncio
    async def test_generate_failure_records_error(self):
        """Test that failures are recorded."""
        provider = OllamaProvider(base_url="http://test:11434")

        # Mock httpx to raise error
        with patch.object(
            provider._client,
            "post",
            side_effect=Exception("Connection failed"),
        ):
            with pytest.raises(LLMProviderError):
                await provider.generate(prompt="Test")

        # Check failure recorded
        assert provider._failure_count > 0

    @pytest.mark.asyncio
    async def test_is_available_after_failures(self):
        """Test provider becomes unavailable after multiple failures."""
        provider = OllamaProvider()

        # Initially available
        assert provider.is_available() is True

        # Record 3 failures
        provider._record_failure()
        provider._record_failure()
        provider._record_failure()

        # Should be unavailable
        assert provider.is_available() is False


class TestAnthropicProvider:
    """Test suite for Anthropic provider."""

    @pytest.mark.asyncio
    async def test_provider_unavailable_without_api_key(self):
        """Test provider is unavailable without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = AnthropicProvider()
            assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_raises_without_client(self):
        """Test generation raises error without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = AnthropicProvider()

            with pytest.raises(ProviderUnavailableError):
                await provider.generate(prompt="Test")


class TestCircuitBreaker:
    """Test suite for Circuit Breaker."""

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        # Initially can execute
        assert breaker.can_execute("test_provider") is True

        # Record failures
        breaker.record_failure("test_provider")
        assert breaker.can_execute("test_provider") is True

        breaker.record_failure("test_provider")
        assert breaker.can_execute("test_provider") is True

        breaker.record_failure("test_provider")
        # Should be open now
        assert breaker.can_execute("test_provider") is False

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker enters half-open state after timeout."""
        import time
        from datetime import datetime, timedelta

        # Use a 1 second timeout so we can test the transition
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        # Record failures to open circuit
        for _ in range(3):
            breaker.record_failure("test_provider")

        # Circuit should be open
        assert breaker.can_execute("test_provider") is False

        # Manually set next_retry to the past to simulate timeout
        state = breaker.get_state("test_provider")
        state.next_retry = datetime.utcnow() - timedelta(seconds=1)

        # Now it should allow execution and transition to half-open
        assert breaker.can_execute("test_provider") is True

        # State should be half_open
        state = breaker.get_state("test_provider")
        assert state.state == "half_open"

    def test_circuit_breaker_closes_after_success(self):
        """Test circuit breaker closes after successful call in half-open."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0)

        # Open circuit
        for _ in range(3):
            breaker.record_failure("test_provider")

        # Enter half-open
        import time

        time.sleep(0.1)
        breaker.can_execute("test_provider")

        # Record success
        breaker.record_success("test_provider")

        # Should be closed
        state = breaker.get_state("test_provider")
        assert state.state == "closed"


class TestLLMRouter:
    """Test suite for LLM Router."""

    @pytest.mark.asyncio
    async def test_router_initialization(self):
        """Test router initializes with providers."""
        router = LLMRouter(default_provider="ollama")

        assert "ollama" in router.providers
        assert "anthropic" in router.providers
        assert router.default_provider == "ollama"

    @pytest.mark.asyncio
    async def test_router_airgap_mode(self):
        """Test router in airgap mode only has local providers."""
        router = LLMRouter(airgap_mode=True)

        assert "ollama" in router.providers
        assert "anthropic" not in router.providers
        assert router.fallback_chain == ["ollama"]

    @pytest.mark.asyncio
    async def test_classify_simple_task(self):
        """Test task classification for simple queries."""
        router = LLMRouter()

        classification = await router.classify_task("Hello world")

        assert isinstance(classification, TaskClassification)
        assert classification.task_type == "simple_query"
        assert classification.recommended_provider == "ollama"

    @pytest.mark.asyncio
    async def test_classify_privacy_sensitive(self):
        """Test task classification for privacy-sensitive content."""
        router = LLMRouter()

        classification = await router.classify_task(
            "What is the patient's medical record number?"
        )

        assert classification.task_type == "privacy_sensitive"
        assert classification.recommended_provider == "ollama"
        assert classification.is_privacy_sensitive is True

    @pytest.mark.asyncio
    async def test_classify_tool_calling(self):
        """Test task classification with tools."""
        router = LLMRouter()

        tools = [{"name": "test_tool", "description": "Test"}]
        classification = await router.classify_task("Execute task", tools=tools)

        assert classification.task_type == "tool_calling"
        assert classification.requires_tools is True

    @pytest.mark.asyncio
    async def test_classify_multi_step(self):
        """Test task classification for complex queries."""
        router = LLMRouter()

        classification = await router.classify_task(
            "Analyze the schedule and compare utilization rates across all residents"
        )

        assert classification.task_type == "multi_step"
        assert classification.complexity_score > 0.7

    @pytest.mark.asyncio
    async def test_classify_code_generation(self):
        """Test task classification for code tasks."""
        router = LLMRouter()

        classification = await router.classify_task(
            "Write a function to validate dates"
        )

        assert classification.task_type == "code_generation"
        assert classification.recommended_model == "qwen2.5"

    @pytest.mark.asyncio
    async def test_generate_with_explicit_provider(self):
        """Test generation with explicitly specified provider."""
        router = LLMRouter()

        # Mock the provider's generate method
        mock_response = LLMResponse(
            content="Test response",
            provider="ollama",
            model="llama3.2",
            usage=LLMUsage(input_tokens=10, output_tokens=20, total_tokens=30),
        )

        with patch.object(
            router.providers["ollama"],
            "generate",
            return_value=mock_response,
        ):
            request = LLMRequest(
                prompt="Test prompt",
                provider="ollama",
            )
            response = await router.generate(request)

        assert response.content == "Test response"
        assert response.provider == "ollama"
        assert router.stats.total_requests == 1

    @pytest.mark.asyncio
    async def test_fallback_on_provider_failure(self):
        """Test fallback to secondary provider on failure."""
        router = LLMRouter(enable_fallback=True)

        # Mock ollama to fail
        with patch.object(
            router.providers["ollama"],
            "generate",
            side_effect=LLMProviderError("Ollama failed"),
        ):
            # Mock anthropic to be available and succeed
            mock_response = LLMResponse(
                content="Fallback response",
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
            )

            with patch.object(
                router.providers["anthropic"],
                "is_available",
                return_value=True,
            ):
                with patch.object(
                    router.providers["anthropic"],
                    "generate",
                    return_value=mock_response,
                ):
                    request = LLMRequest(
                        prompt="Test prompt",
                        provider="ollama",
                    )
                    response = await router.generate(request)

        assert response.content == "Fallback response"
        assert response.provider == "anthropic"
        assert router.stats.fallback_count == 1

    @pytest.mark.asyncio
    async def test_health_check_all_providers(self):
        """Test health check returns status for all providers."""
        router = LLMRouter()

        health_status = await router.health_check_all()

        assert "ollama" in health_status
        assert "anthropic" in health_status
        assert health_status["ollama"].provider == "ollama"

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test statistics retrieval."""
        router = LLMRouter()

        stats = router.get_stats()

        assert stats.total_requests == 0
        assert isinstance(stats.requests_by_provider, dict)
        assert stats.uptime_start is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_states(self):
        """Test circuit breaker state retrieval."""
        router = LLMRouter()

        states = router.get_circuit_breaker_states()

        assert "ollama" in states
        assert "anthropic" in states
        assert states["ollama"].provider == "ollama"
        assert states["ollama"].state == "closed"
