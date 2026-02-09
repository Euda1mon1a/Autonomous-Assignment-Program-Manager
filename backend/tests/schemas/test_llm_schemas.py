"""Tests for LLM Router schemas (Field bounds, Literals, defaults)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.llm import (
    ToolCall,
    LLMUsage,
    LLMResponse,
    LLMRequest,
    TaskClassification,
    ProviderHealth,
    CircuitBreakerState,
    LLMRouterStats,
    StreamChunk,
)


class TestToolCall:
    def test_valid(self):
        r = ToolCall(id="tc-1", name="get_schedule")
        assert r.arguments == {}

    def test_with_args(self):
        r = ToolCall(id="tc-1", name="validate", arguments={"block": 10})
        assert r.arguments["block"] == 10


class TestLLMUsage:
    def test_defaults(self):
        r = LLMUsage()
        assert r.input_tokens == 0
        assert r.output_tokens == 0
        assert r.total_tokens == 0
        assert r.cost_usd is None

    def test_full(self):
        r = LLMUsage(
            input_tokens=100, output_tokens=200, total_tokens=300, cost_usd=0.05
        )
        assert r.total_tokens == 300


class TestLLMResponse:
    def test_valid_minimal(self):
        r = LLMResponse(content="Hello", provider="anthropic", model="opus")
        assert r.tool_calls is None
        assert r.usage is None
        assert r.finish_reason is None
        assert r.metadata == {}
        assert isinstance(r.timestamp, datetime)

    def test_full(self):
        tc = ToolCall(id="tc-1", name="validate")
        usage = LLMUsage(input_tokens=50, output_tokens=100, total_tokens=150)
        r = LLMResponse(
            content="Result",
            provider="ollama",
            model="llama3",
            tool_calls=[tc],
            usage=usage,
            finish_reason="stop",
        )
        assert len(r.tool_calls) == 1
        assert r.usage.total_tokens == 150


class TestLLMRequest:
    def test_valid_minimal(self):
        r = LLMRequest(prompt="Hello")
        assert r.system is None
        assert r.model is None
        assert r.provider == "auto"
        assert r.max_tokens == 4096
        assert r.temperature == 0.7
        assert r.stream is False
        assert r.tools is None
        assert r.metadata == {}

    # --- max_tokens ge=1, le=100000 ---

    def test_max_tokens_zero(self):
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Hello", max_tokens=0)

    def test_max_tokens_above_max(self):
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Hello", max_tokens=100001)

    def test_max_tokens_boundaries(self):
        r = LLMRequest(prompt="Hello", max_tokens=1)
        assert r.max_tokens == 1
        r = LLMRequest(prompt="Hello", max_tokens=100000)
        assert r.max_tokens == 100000

    # --- temperature ge=0.0, le=2.0 ---

    def test_temperature_negative(self):
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Hello", temperature=-0.1)

    def test_temperature_above_max(self):
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Hello", temperature=2.1)

    def test_temperature_boundaries(self):
        r = LLMRequest(prompt="Hello", temperature=0.0)
        assert r.temperature == 0.0
        r = LLMRequest(prompt="Hello", temperature=2.0)
        assert r.temperature == 2.0

    # --- provider Literal ---

    def test_provider_values(self):
        for p in ("auto", "ollama", "anthropic", "vllm"):
            r = LLMRequest(prompt="Hello", provider=p)
            assert r.provider == p

    def test_provider_invalid(self):
        with pytest.raises(ValidationError):
            LLMRequest(prompt="Hello", provider="openai")


class TestTaskClassification:
    def test_valid(self):
        r = TaskClassification(
            task_type="simple_query",
            complexity_score=0.2,
            recommended_provider="ollama",
            recommended_model="llama3",
            reasoning="Simple question",
        )
        assert r.requires_tools is False
        assert r.is_privacy_sensitive is False

    # --- task_type Literal ---

    def test_task_types(self):
        for tt in (
            "simple_query",
            "explanation",
            "tool_calling",
            "multi_step",
            "code_generation",
            "privacy_sensitive",
        ):
            r = TaskClassification(
                task_type=tt,
                complexity_score=0.5,
                recommended_provider="auto",
                recommended_model="model",
                reasoning="test",
            )
            assert r.task_type == tt

    def test_invalid_task_type(self):
        with pytest.raises(ValidationError):
            TaskClassification(
                task_type="unknown",
                complexity_score=0.5,
                recommended_provider="auto",
                recommended_model="model",
                reasoning="test",
            )

    # --- complexity_score ge=0.0, le=1.0 ---

    def test_complexity_score_negative(self):
        with pytest.raises(ValidationError):
            TaskClassification(
                task_type="simple_query",
                complexity_score=-0.1,
                recommended_provider="auto",
                recommended_model="model",
                reasoning="test",
            )

    def test_complexity_score_above_max(self):
        with pytest.raises(ValidationError):
            TaskClassification(
                task_type="simple_query",
                complexity_score=1.1,
                recommended_provider="auto",
                recommended_model="model",
                reasoning="test",
            )


class TestProviderHealth:
    def test_valid(self):
        r = ProviderHealth(provider="ollama", is_available=True)
        assert r.failure_count == 0
        assert r.avg_latency_ms is None
        assert r.error_message is None
        assert isinstance(r.last_check, datetime)


class TestCircuitBreakerState:
    def test_valid(self):
        r = CircuitBreakerState(provider="anthropic", state="closed")
        assert r.failure_count == 0
        assert r.last_failure is None
        assert r.next_retry is None

    # --- state Literal ---

    def test_state_values(self):
        for s in ("closed", "open", "half_open"):
            r = CircuitBreakerState(provider="p", state=s)
            assert r.state == s

    def test_state_invalid(self):
        with pytest.raises(ValidationError):
            CircuitBreakerState(provider="p", state="broken")


class TestLLMRouterStats:
    def test_defaults(self):
        r = LLMRouterStats()
        assert r.total_requests == 0
        assert r.requests_by_provider == {}
        assert r.requests_by_task_type == {}
        assert r.fallback_count == 0
        assert r.total_tokens_used == 0
        assert r.avg_latency_ms == 0.0
        assert r.error_count == 0
        assert isinstance(r.uptime_start, datetime)


class TestStreamChunk:
    def test_valid(self):
        r = StreamChunk(delta="Hello", provider="anthropic", model="opus")
        assert r.finish_reason is None
        assert r.tool_calls is None

    def test_final_chunk(self):
        r = StreamChunk(
            delta="", provider="anthropic", model="opus", finish_reason="stop"
        )
        assert r.finish_reason == "stop"
