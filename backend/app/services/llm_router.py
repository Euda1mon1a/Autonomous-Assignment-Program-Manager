"""LLM Router service for multi-provider abstraction.

Provides unified interface for local (Ollama) and cloud (Anthropic) LLM providers
with intelligent routing, fallback chains, and circuit breaker patterns.
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Optional

import httpx
from anthropic import AsyncAnthropic

from app.schemas.llm import (
    CircuitBreakerState,
    LLMRequest,
    LLMResponse,
    LLMRouterStats,
    LLMUsage,
    ProviderHealth,
    StreamChunk,
    TaskClassification,
    ToolCall,
)

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    pass


class ProviderUnavailableError(LLMProviderError):
    """Provider is unavailable or circuit breaker is open."""

    pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, name: str):
        self.name = name
        self._is_available = True
        self._last_check = datetime.utcnow()
        self._failure_count = 0
        self._latencies: list[float] = []

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate text from prompt.

        Args:
            prompt: User prompt
            system: Optional system prompt
            model: Optional specific model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            LLMProviderError: On generation failure
        """
        pass

    @abstractmethod
    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate text with tool calling support.

        Args:
            prompt: User prompt
            tools: List of available tools
            system: Optional system prompt
            model: Optional specific model name
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content and optional tool calls

        Raises:
            LLMProviderError: On generation failure
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream generation results.

        Args:
            prompt: User prompt
            system: Optional system prompt
            model: Optional specific model name
            **kwargs: Additional provider-specific parameters

        Yields:
            StreamChunk objects as they become available

        Raises:
            LLMProviderError: On streaming failure
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available.

        Returns:
            bool: True if provider can accept requests
        """
        pass

    async def health_check(self) -> ProviderHealth:
        """
        Perform health check on provider.

        Returns:
            ProviderHealth with current status
        """
        try:
            # Simple availability check
            available = self.is_available()
            avg_latency = (
                sum(self._latencies[-10:]) / len(self._latencies[-10:])
                if self._latencies
                else None
            )

            return ProviderHealth(
                provider=self.name,
                is_available=available,
                last_check=datetime.utcnow(),
                failure_count=self._failure_count,
                avg_latency_ms=avg_latency,
                error_message=None,
            )
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {str(e)}")
            return ProviderHealth(
                provider=self.name,
                is_available=False,
                last_check=datetime.utcnow(),
                failure_count=self._failure_count,
                error_message=str(e),
            )

    def _record_success(self, latency_ms: float):
        """Record successful request."""
        self._failure_count = 0
        self._is_available = True
        self._latencies.append(latency_ms)
        # Keep only last 100 latencies
        if len(self._latencies) > 100:
            self._latencies = self._latencies[-100:]

    def _record_failure(self):
        """Record failed request."""
        self._failure_count += 1
        if self._failure_count >= 3:
            self._is_available = False
            logger.warning(
                f"Provider {self.name} marked unavailable after {self._failure_count} failures"
            )


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(
        self,
        base_url: str | None = None,
        default_model: str = "llama3.2",
        timeout: float = 60.0,
    ):
        super().__init__(name="ollama")
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.default_model = default_model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        """Generate text using Ollama API."""
        start_time = time.time()
        model = model or self.default_model

        try:
            # Build request payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            if system:
                payload["system"] = system

            # Make request
            response = await self._client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            latency_ms = (time.time() - start_time) * 1000
            self._record_success(latency_ms)

            # Extract usage if available
            usage = None
            if "prompt_eval_count" in data and "eval_count" in data:
                usage = LLMUsage(
                    input_tokens=data.get("prompt_eval_count", 0),
                    output_tokens=data.get("eval_count", 0),
                    total_tokens=data.get("prompt_eval_count", 0)
                    + data.get("eval_count", 0),
                )

            return LLMResponse(
                content=data.get("response", ""),
                provider=self.name,
                model=model,
                usage=usage,
                finish_reason=data.get("done_reason", "stop"),
                metadata={
                    "latency_ms": latency_ms,
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                },
            )

        except httpx.HTTPStatusError as e:
            self._record_failure()
            logger.error(
                f"Ollama HTTP error: {e.response.status_code} - {e.response.text}"
            )
            raise LLMProviderError(
                f"Ollama generation failed: {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            self._record_failure()
            logger.error(f"Ollama request error: {str(e)}")
            raise LLMProviderError(f"Ollama connection failed: {str(e)}") from e
        except Exception as e:
            self._record_failure()
            logger.error(f"Ollama unexpected error: {str(e)}")
            raise LLMProviderError(f"Ollama error: {str(e)}") from e

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate with tool calling (requires Mistral, Llama 3.1+)."""
        start_time = time.time()
        model = model or "mistral"  # Mistral has better tool calling support

        try:
            # Build messages format for chat endpoint
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "tools": tools,
            }

            response = await self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            latency_ms = (time.time() - start_time) * 1000
            self._record_success(latency_ms)

            # Extract message content
            message = data.get("message", {})
            content = message.get("content", "")

            # Extract tool calls if present
            tool_calls = None
            if "tool_calls" in message:
                tool_calls = [
                    ToolCall(
                        id=tc.get("id", f"call_{i}"),
                        name=tc.get("function", {}).get("name", ""),
                        arguments=tc.get("function", {}).get("arguments", {}),
                    )
                    for i, tc in enumerate(message["tool_calls"])
                ]

            return LLMResponse(
                content=content,
                provider=self.name,
                model=model,
                tool_calls=tool_calls,
                finish_reason=data.get("done_reason", "stop"),
                metadata={"latency_ms": latency_ms},
            )

        except Exception as e:
            self._record_failure()
            logger.error(f"Ollama tool calling error: {str(e)}")
            raise LLMProviderError(f"Ollama tool calling failed: {str(e)}") from e

    async def stream_generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream generation from Ollama."""
        model = model or self.default_model

        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": True,
            }

            if system:
                payload["system"] = system

            async with self._client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        import json

                        data = json.loads(line)
                        delta = data.get("response", "")
                        done = data.get("done", False)

                        yield StreamChunk(
                            delta=delta,
                            provider=self.name,
                            model=model,
                            finish_reason="stop" if done else None,
                        )

                        if done:
                            break
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse streaming line: {line}")
                        continue

            self._record_success(0)  # Success but no latency for streaming

        except Exception as e:
            self._record_failure()
            logger.error(f"Ollama streaming error: {str(e)}")
            raise LLMProviderError(f"Ollama streaming failed: {str(e)}") from e

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        if not self._is_available:
            # Try to recover after 60 seconds
            if (datetime.utcnow() - self._last_check).seconds > 60:
                self._is_available = True
                self._failure_count = 0
                logger.info(f"Resetting {self.name} availability after cooldown")

        return self._is_available

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "claude-3-5-sonnet-20241022",
    ):
        super().__init__(name="anthropic")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.default_model = default_model

        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set - Anthropic provider unavailable")
            self._is_available = False
            self._client = None
        else:
            self._client = AsyncAnthropic(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        """Generate text using Anthropic API."""
        if not self._client:
            raise ProviderUnavailableError("Anthropic API key not configured")

        start_time = time.time()
        model = model or self.default_model

        try:
            response = await self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            )

            latency_ms = (time.time() - start_time) * 1000
            self._record_success(latency_ms)

            # Extract text content
            content = ""
            if response.content:
                content = (
                    response.content[0].text
                    if hasattr(response.content[0], "text")
                    else str(response.content[0])
                )

            # Build usage
            usage = LLMUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            return LLMResponse(
                content=content,
                provider=self.name,
                model=model,
                usage=usage,
                finish_reason=response.stop_reason,
                metadata={"latency_ms": latency_ms},
            )

        except Exception as e:
            self._record_failure()
            logger.error(f"Anthropic generation error: {str(e)}")
            raise LLMProviderError(f"Anthropic generation failed: {str(e)}") from e

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate with tool calling using Anthropic."""
        if not self._client:
            raise ProviderUnavailableError("Anthropic API key not configured")

        start_time = time.time()
        model = model or self.default_model

        try:
            response = await self._client.messages.create(
                model=model,
                max_tokens=4096,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
                tools=tools,
            )

            latency_ms = (time.time() - start_time) * 1000
            self._record_success(latency_ms)

            # Extract content and tool calls
            content = ""
            tool_calls = []

            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
                elif hasattr(block, "type") and block.type == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            id=block.id,
                            name=block.name,
                            arguments=block.input,
                        )
                    )

            usage = LLMUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            return LLMResponse(
                content=content,
                provider=self.name,
                model=model,
                tool_calls=tool_calls if tool_calls else None,
                usage=usage,
                finish_reason=response.stop_reason,
                metadata={"latency_ms": latency_ms},
            )

        except Exception as e:
            self._record_failure()
            logger.error(f"Anthropic tool calling error: {str(e)}")
            raise LLMProviderError(f"Anthropic tool calling failed: {str(e)}") from e

    async def stream_generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream generation from Anthropic."""
        if not self._client:
            raise ProviderUnavailableError("Anthropic API key not configured")

        model = model or self.default_model

        try:
            async with self._client.messages.stream(
                model=model,
                max_tokens=4096,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield StreamChunk(
                        delta=text,
                        provider=self.name,
                        model=model,
                    )

                # Final chunk with finish reason
                final_message = await stream.get_final_message()
                yield StreamChunk(
                    delta="",
                    provider=self.name,
                    model=model,
                    finish_reason=final_message.stop_reason,
                )

            self._record_success(0)

        except Exception as e:
            self._record_failure()
            logger.error(f"Anthropic streaming error: {str(e)}")
            raise LLMProviderError(f"Anthropic streaming failed: {str(e)}") from e

    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return self._is_available and self._client is not None


class CircuitBreaker:
    """Circuit breaker for provider fault tolerance."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._states: dict[str, CircuitBreakerState] = {}

    def get_state(self, provider: str) -> CircuitBreakerState:
        """Get circuit breaker state for provider."""
        if provider not in self._states:
            self._states[provider] = CircuitBreakerState(
                provider=provider,
                state="closed",
                failure_count=0,
            )
        return self._states[provider]

    def can_execute(self, provider: str) -> bool:
        """Check if request can be executed."""
        state = self.get_state(provider)

        if state.state == "closed":
            return True
        elif state.state == "open":
            # Check if recovery timeout passed
            if state.next_retry and datetime.utcnow() >= state.next_retry:
                state.state = "half_open"
                logger.info(f"Circuit breaker for {provider} entering half-open state")
                return True
            return False
        else:  # half_open
            return True

    def record_success(self, provider: str):
        """Record successful request."""
        state = self.get_state(provider)
        if state.state == "half_open":
            state.state = "closed"
            state.failure_count = 0
            logger.info(f"Circuit breaker for {provider} closed after recovery")

    def record_failure(self, provider: str):
        """Record failed request."""
        state = self.get_state(provider)
        state.failure_count += 1
        state.last_failure = datetime.utcnow()

        if state.failure_count >= self.failure_threshold:
            state.state = "open"
            state.next_retry = datetime.utcnow() + timedelta(
                seconds=self.recovery_timeout
            )
            logger.warning(
                f"Circuit breaker for {provider} opened after {state.failure_count} failures"
            )


class LLMRouter:
    """
    Multi-provider LLM router with intelligent routing and fallback.

    Features:
    - Provider abstraction (Ollama, Anthropic, vLLM)
    - Intelligent task-based routing
    - Fallback chain on provider failure
    - Circuit breaker pattern
    - Health monitoring
    - Usage statistics
    """

    def __init__(
        self,
        default_provider: str = "ollama",
        enable_fallback: bool = True,
        airgap_mode: bool = False,
    ):
        """
        Initialize LLM Router.

        Args:
            default_provider: Default provider to use ("ollama", "anthropic")
            enable_fallback: Enable fallback to other providers on failure
            airgap_mode: Disable all cloud providers (local only)
        """
        self.default_provider = default_provider
        self.enable_fallback = enable_fallback
        self.airgap_mode = airgap_mode

        # Initialize providers
        self.providers: dict[str, LLMProvider] = {
            "ollama": OllamaProvider(),
        }

        # Only add Anthropic if not in airgap mode
        if not airgap_mode:
            self.providers["anthropic"] = AnthropicProvider()

        # Fallback chain (local first, then cloud)
        self.fallback_chain = ["ollama", "anthropic"]
        if airgap_mode:
            self.fallback_chain = ["ollama"]

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker()

        # Statistics
        self.stats = LLMRouterStats()

        logger.info(
            f"LLM Router initialized (default={default_provider}, airgap={airgap_mode})"
        )

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate text with automatic provider routing.

        Args:
            request: LLM request with prompt and parameters

        Returns:
            LLMResponse from selected provider

        Raises:
            LLMProviderError: If all providers fail
        """
        # Classify task and select provider
        if request.provider == "auto":
            classification = await self.classify_task(request.prompt, request.tools)
            provider_name = classification.recommended_provider
            model = classification.recommended_model
        else:
            provider_name = request.provider
            model = request.model

        # Try primary provider
        try:
            response = await self._generate_with_provider(
                provider_name=provider_name,
                prompt=request.prompt,
                system=request.system,
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                tools=request.tools,
            )

            self.stats.total_requests += 1
            self.stats.requests_by_provider[provider_name] = (
                self.stats.requests_by_provider.get(provider_name, 0) + 1
            )
            if response.usage:
                self.stats.total_tokens_used += response.usage.total_tokens

            return response

        except (LLMProviderError, ProviderUnavailableError) as e:
            logger.warning(
                f"Provider {provider_name} failed: {str(e)}, attempting fallback"
            )
            self.stats.error_count += 1

            # Try fallback chain if enabled
            if self.enable_fallback:
                return await self._fallback_generate(
                    request, failed_provider=provider_name
                )
            else:
                raise

    async def _generate_with_provider(
        self,
        provider_name: str,
        prompt: str,
        system: str | None,
        model: str | None,
        max_tokens: int,
        temperature: float,
        tools: list[dict[str, Any]] | None,
    ) -> LLMResponse:
        """Generate with specific provider."""
        # Check circuit breaker
        if not self.circuit_breaker.can_execute(provider_name):
            raise ProviderUnavailableError(f"Circuit breaker open for {provider_name}")

        provider = self.providers.get(provider_name)
        if not provider:
            raise LLMProviderError(f"Unknown provider: {provider_name}")

        if not provider.is_available():
            raise ProviderUnavailableError(f"Provider {provider_name} unavailable")

        try:
            # Choose method based on tools
            if tools:
                response = await provider.generate_with_tools(
                    prompt=prompt,
                    tools=tools,
                    system=system,
                    model=model,
                )
            else:
                response = await provider.generate(
                    prompt=prompt,
                    system=system,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            self.circuit_breaker.record_success(provider_name)
            return response

        except Exception as e:
            self.circuit_breaker.record_failure(provider_name)
            raise

    async def _fallback_generate(
        self, request: LLMRequest, failed_provider: str
    ) -> LLMResponse:
        """Try fallback providers in chain."""
        for provider_name in self.fallback_chain:
            if provider_name == failed_provider:
                continue  # Skip the failed provider

            if provider_name not in self.providers:
                continue

            try:
                logger.info(f"Attempting fallback to {provider_name}")
                response = await self._generate_with_provider(
                    provider_name=provider_name,
                    prompt=request.prompt,
                    system=request.system,
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    tools=request.tools,
                )

                self.stats.fallback_count += 1
                self.stats.total_requests += 1
                self.stats.requests_by_provider[provider_name] = (
                    self.stats.requests_by_provider.get(provider_name, 0) + 1
                )

                return response

            except Exception as e:
                logger.warning(f"Fallback to {provider_name} failed: {str(e)}")
                continue

        # All providers failed
        raise LLMProviderError("All providers failed")

    async def classify_task(
        self, prompt: str, tools: list[dict[str, Any]] | None = None
    ) -> TaskClassification:
        """
        Classify task to determine appropriate provider and model.

        Args:
            prompt: User prompt
            tools: Optional tools list

        Returns:
            TaskClassification with routing recommendation
        """
        prompt_lower = prompt.lower()

        # Check for privacy-sensitive keywords (always route to local)
        privacy_keywords = ["patient", "phi", "ssn", "name", "medical record", "hipaa"]
        is_privacy_sensitive = any(kw in prompt_lower for kw in privacy_keywords)

        if is_privacy_sensitive:
            return TaskClassification(
                task_type="privacy_sensitive",
                complexity_score=0.3,
                recommended_provider="ollama",
                recommended_model="llama3.2",
                reasoning="Contains privacy-sensitive information, routing to local model",
                requires_tools=False,
                is_privacy_sensitive=True,
            )

        # Check if tools required
        if tools:
            return TaskClassification(
                task_type="tool_calling",
                complexity_score=0.7,
                recommended_provider="anthropic" if not self.airgap_mode else "ollama",
                recommended_model="claude-3-5-sonnet-20241022"
                if not self.airgap_mode
                else "mistral",
                reasoning="Tool calling requested, using provider with best tool support",
                requires_tools=True,
                is_privacy_sensitive=False,
            )

        # Heuristic-based classification
        word_count = len(prompt.split())

        # Simple query (< 20 words)
        if word_count < 20:
            return TaskClassification(
                task_type="simple_query",
                complexity_score=0.2,
                recommended_provider="ollama",
                recommended_model="llama3.2",
                reasoning="Short prompt, using fast local model",
                requires_tools=False,
                is_privacy_sensitive=False,
            )

        # Multi-step reasoning keywords
        multi_step_keywords = [
            "analyze",
            "compare",
            "evaluate",
            "comprehensive",
            "detailed analysis",
        ]
        is_multi_step = any(kw in prompt_lower for kw in multi_step_keywords)

        if is_multi_step:
            return TaskClassification(
                task_type="multi_step",
                complexity_score=0.9,
                recommended_provider="anthropic" if not self.airgap_mode else "ollama",
                recommended_model="claude-3-5-sonnet-20241022"
                if not self.airgap_mode
                else "llama3.2:8b",
                reasoning="Multi-step reasoning detected, using advanced model",
                requires_tools=False,
                is_privacy_sensitive=False,
            )

        # Code generation
        code_keywords = ["code", "function", "script", "implement", "write a"]
        is_code = any(kw in prompt_lower for kw in code_keywords)

        if is_code:
            return TaskClassification(
                task_type="code_generation",
                complexity_score=0.6,
                recommended_provider="ollama",
                recommended_model="qwen2.5",
                reasoning="Code generation task, using code-specialized model",
                requires_tools=False,
                is_privacy_sensitive=False,
            )

        # Default: explanation/medium complexity
        return TaskClassification(
            task_type="explanation",
            complexity_score=0.5,
            recommended_provider="ollama",
            recommended_model="llama3.2",
            reasoning="General explanation task, using local model",
            requires_tools=False,
            is_privacy_sensitive=False,
        )

    async def health_check_all(self) -> dict[str, ProviderHealth]:
        """
        Check health of all providers.

        Returns:
            Dict of provider name to ProviderHealth
        """
        health_status = {}
        for name, provider in self.providers.items():
            health_status[name] = await provider.health_check()
        return health_status

    def get_stats(self) -> LLMRouterStats:
        """Get router statistics."""
        return self.stats

    def get_circuit_breaker_states(self) -> dict[str, CircuitBreakerState]:
        """Get circuit breaker states for all providers."""
        return {
            name: self.circuit_breaker.get_state(name) for name in self.providers.keys()
        }

    async def close(self):
        """Close all provider connections."""
        for provider in self.providers.values():
            if hasattr(provider, "close"):
                await provider.close()
