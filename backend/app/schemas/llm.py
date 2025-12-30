"""Schema definitions for LLM Router service."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Tool call from LLM response."""

    id: str = Field(..., description="Unique identifier for the tool call")
    name: str = Field(..., description="Name of the tool to call")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the tool call"
    )


class LLMUsage(BaseModel):
    """Token usage statistics from LLM call."""

    input_tokens: int = Field(0, description="Number of input tokens used")
    output_tokens: int = Field(0, description="Number of output tokens generated")
    total_tokens: int = Field(0, description="Total tokens used")
    cost_usd: float | None = Field(None, description="Estimated cost in USD")


class LLMResponse(BaseModel):
    """Response from LLM generation."""

    content: str = Field(..., description="Generated text content")
    provider: str = Field(..., description="Provider used (ollama, anthropic, vllm)")
    model: str = Field(..., description="Model name used for generation")
    tool_calls: list[ToolCall] | None = Field(
        None, description="Tool calls requested by the LLM"
    )
    usage: LLMUsage | None = Field(None, description="Token usage statistics")
    finish_reason: str | None = Field(
        None, description="Reason generation stopped (stop, length, tool_calls)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional provider-specific metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class LLMRequest(BaseModel):
    """Request for LLM generation."""

    prompt: str = Field(..., description="User prompt for generation")
    system: str | None = Field(None, description="System prompt/instructions")
    model: str | None = Field(None, description="Specific model to use (optional)")
    provider: Literal["auto", "ollama", "anthropic", "vllm"] = Field(
        "auto", description="Provider to use (auto for intelligent routing)"
    )
    max_tokens: int = Field(
        4096, description="Maximum tokens to generate", ge=1, le=100000
    )
    temperature: float = Field(
        0.7, description="Sampling temperature", ge=0.0, le=2.0
    )
    stream: bool = Field(False, description="Enable streaming response")
    tools: list[dict[str, Any]] | None = Field(
        None, description="Available tools for tool calling"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional request metadata"
    )


class TaskClassification(BaseModel):
    """Classification of task for routing decisions."""

    task_type: Literal[
        "simple_query",
        "explanation",
        "tool_calling",
        "multi_step",
        "code_generation",
        "privacy_sensitive",
    ] = Field(..., description="Classified task type")
    complexity_score: float = Field(
        ..., description="Complexity score (0.0-1.0)", ge=0.0, le=1.0
    )
    recommended_provider: str = Field(
        ..., description="Recommended provider for this task"
    )
    recommended_model: str = Field(..., description="Recommended model for this task")
    reasoning: str = Field(..., description="Explanation for the classification")
    requires_tools: bool = Field(
        False, description="Whether task requires tool calling"
    )
    is_privacy_sensitive: bool = Field(
        False, description="Whether task contains sensitive data"
    )


class ProviderHealth(BaseModel):
    """Health status of an LLM provider."""

    provider: str = Field(..., description="Provider name")
    is_available: bool = Field(..., description="Whether provider is available")
    last_check: datetime = Field(
        default_factory=datetime.utcnow, description="Last health check timestamp"
    )
    failure_count: int = Field(0, description="Consecutive failures")
    avg_latency_ms: float | None = Field(
        None, description="Average response latency in milliseconds"
    )
    error_message: str | None = Field(None, description="Last error message if any")


class CircuitBreakerState(BaseModel):
    """Circuit breaker state for provider."""

    provider: str = Field(..., description="Provider name")
    state: Literal["closed", "open", "half_open"] = Field(
        ..., description="Circuit breaker state"
    )
    failure_count: int = Field(0, description="Current failure count")
    last_failure: datetime | None = Field(None, description="Last failure timestamp")
    next_retry: datetime | None = Field(
        None, description="Next retry timestamp (if open)"
    )


class LLMRouterStats(BaseModel):
    """Statistics for LLM Router usage."""

    total_requests: int = Field(0, description="Total requests processed")
    requests_by_provider: dict[str, int] = Field(
        default_factory=dict, description="Requests per provider"
    )
    requests_by_task_type: dict[str, int] = Field(
        default_factory=dict, description="Requests per task type"
    )
    fallback_count: int = Field(0, description="Number of fallback activations")
    total_tokens_used: int = Field(0, description="Total tokens used across providers")
    avg_latency_ms: float = Field(0.0, description="Average latency in milliseconds")
    error_count: int = Field(0, description="Total errors encountered")
    uptime_start: datetime = Field(
        default_factory=datetime.utcnow, description="Statistics collection start time"
    )


class StreamChunk(BaseModel):
    """Chunk from streaming LLM response."""

    delta: str = Field(..., description="Incremental text delta")
    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model name")
    finish_reason: str | None = Field(None, description="Finish reason if final chunk")
    tool_calls: list[ToolCall] | None = Field(
        None, description="Tool calls if present"
    )
