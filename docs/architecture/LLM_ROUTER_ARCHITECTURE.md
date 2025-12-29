# LLM Router Architecture

> **Created:** 2025-12-29
> **Status:** Implemented
> **Component:** `backend/app/services/llm_router.py`

---

## Overview

The LLM Router provides a unified abstraction layer for multiple LLM providers (local and cloud), with intelligent routing, fallback chains, and circuit breaker patterns. This enables the application to:

- **Operate in airgap mode** (local Ollama only)
- **Reduce costs** by routing simple tasks to local models
- **Ensure availability** with automatic fallback on provider failure
- **Maintain privacy** by routing sensitive data to local models

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Router                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Task Classifier                                  │     │
│  │  - Analyzes prompt complexity                     │     │
│  │  - Detects privacy-sensitive keywords             │     │
│  │  - Recommends provider/model                      │     │
│  └───────────────────────────────────────────────────┘     │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Circuit Breaker                                  │     │
│  │  - Tracks provider failures                       │     │
│  │  - Opens circuit after threshold                  │     │
│  │  - Auto-recovery with half-open state             │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
          │                    │
          ▼                    ▼
   ┌─────────────┐      ┌─────────────┐
   │   Ollama    │      │  Anthropic  │
   │  Provider   │      │   Provider  │
   ├─────────────┤      ├─────────────┤
   │ - HTTP API  │      │ - SDK-based │
   │ - Async     │      │ - Async     │
   │ - Streaming │      │ - Streaming │
   │ - Tools     │      │ - Tools     │
   └─────────────┘      └─────────────┘
```

---

## Provider Abstraction

### Base Provider Interface

All providers implement the `LLMProvider` abstract base class:

```python
class LLMProvider(ABC):
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
        """Generate text from prompt."""
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
        """Generate with tool calling support."""
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream generation results."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
```

---

## Implemented Providers

### 1. Ollama Provider

**Purpose:** Local LLM inference via Docker container

**Features:**
- HTTP API client using `httpx`
- Supports `/api/generate` (completion) and `/api/chat` (tool calling)
- Streaming support
- Automatic token usage tracking
- Configurable timeout and models

**Default Models:**
- `llama3.2` - Fast, lightweight (3B/8B)
- `mistral` - Tool calling support
- `qwen2.5` - Code generation

**Configuration:**
```python
OLLAMA_URL = "http://ollama:11434"
OLLAMA_DEFAULT_MODEL = "llama3.2"
OLLAMA_TIMEOUT = 60.0
```

**Error Handling:**
- HTTP errors (connection refused, timeouts)
- JSON parsing errors
- Circuit breaker integration

---

### 2. Anthropic Provider

**Purpose:** Cloud-based Claude API access

**Features:**
- Async SDK client (`anthropic.AsyncAnthropic`)
- Tool calling with function schemas
- Streaming via async generators
- Token usage and cost tracking
- Graceful degradation when API key missing

**Default Models:**
- `claude-3-5-sonnet-20241022` - Balanced performance

**Configuration:**
```python
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # Optional
ANTHROPIC_DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
```

**Error Handling:**
- API key validation
- Rate limit handling
- Network errors
- Circuit breaker integration

---

## Task Classification

The router automatically classifies tasks to select the optimal provider:

### Classification Logic

| Task Type | Criteria | Recommended Provider | Model |
|-----------|----------|---------------------|-------|
| **simple_query** | < 20 words | Ollama | llama3.2 |
| **explanation** | 20-100 words, general | Ollama | llama3.2 |
| **privacy_sensitive** | Contains PHI keywords | Ollama (always local) | llama3.2 |
| **code_generation** | Code keywords | Ollama | qwen2.5 |
| **tool_calling** | Tools provided | Anthropic (or Ollama in airgap) | Claude/Mistral |
| **multi_step** | Complex analysis keywords | Anthropic (or Ollama 8B in airgap) | Claude |

### Privacy Keywords

Automatically route to local provider if prompt contains:
- `patient`, `phi`, `ssn`, `name`, `medical record`, `hipaa`

### Code Example

```python
classification = await router.classify_task(
    "What is patient John Doe's schedule?"
)

# Result:
# - task_type: "privacy_sensitive"
# - recommended_provider: "ollama"
# - is_privacy_sensitive: True
```

---

## Circuit Breaker Pattern

Prevents cascading failures by tracking provider health:

### States

1. **CLOSED** (Normal operation)
   - All requests pass through
   - Failures increment counter

2. **OPEN** (Provider down)
   - Requests fail immediately
   - No calls to provider
   - After timeout, transition to HALF_OPEN

3. **HALF_OPEN** (Testing recovery)
   - Limited requests allowed
   - Success → CLOSED
   - Failure → OPEN

### Configuration

```python
CircuitBreaker(
    failure_threshold=5,      # Open after 5 consecutive failures
    recovery_timeout=60,      # Wait 60s before HALF_OPEN
    half_open_max_calls=3,    # Test with 3 calls in HALF_OPEN
)
```

### Flow Diagram

```
     ┌──────────┐
     │  CLOSED  │ ◄──── Success in HALF_OPEN
     └─────┬────┘
           │ 5 failures
           ▼
     ┌──────────┐
     │   OPEN   │
     └─────┬────┘
           │ 60s timeout
           ▼
     ┌──────────┐
     │ HALF_OPEN│ ─────► Failure → OPEN
     └──────────┘
```

---

## Fallback Chain

When primary provider fails, router tries alternatives:

### Default Fallback Chain

```python
fallback_chain = ["ollama", "anthropic"]
```

### Fallback Behavior

1. **Primary provider fails** → LLMProviderError raised
2. **If fallback enabled** → Try next in chain
3. **If all fail** → Raise error to caller
4. **Statistics updated** → `fallback_count` incremented

### Example

```python
# Request to Ollama
request = LLMRequest(prompt="Test", provider="ollama")

# Ollama down → Falls back to Anthropic
response = await router.generate(request)

# response.provider == "anthropic"
# router.stats.fallback_count == 1
```

---

## Airgap Mode

For secure/offline deployments without cloud connectivity:

### Configuration

```python
router = LLMRouter(airgap_mode=True)
```

### Behavior

- **Disables Anthropic provider**
- **Fallback chain = ["ollama"]**
- **All requests use local model**
- **Privacy guaranteed** (no data leaves network)

### Use Cases

- Military deployments
- HIPAA-sensitive environments
- Offline/edge deployments
- Development without API keys

---

## Usage Examples

### Basic Generation with Auto-Routing

```python
from app.services.llm_router import LLMRouter
from app.schemas.llm import LLMRequest

router = LLMRouter()

request = LLMRequest(
    prompt="Explain the ACGME 80-hour rule",
    provider="auto",  # Automatic routing
    max_tokens=500,
)

response = await router.generate(request)

print(f"Provider: {response.provider}")
print(f"Content: {response.content}")
```

### Privacy-Sensitive Data (Force Local)

```python
request = LLMRequest(
    prompt="What is patient Jane Doe's schedule?",
    provider="ollama",  # Force local for PHI
    system="You are a medical scheduling assistant.",
)

response = await router.generate(request)

# Guaranteed to use local provider
assert response.provider == "ollama"
```

### Tool Calling

```python
tools = [
    {
        "name": "validate_schedule",
        "description": "Validate schedule against ACGME",
        "input_schema": {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string"}
            }
        }
    }
]

request = LLMRequest(
    prompt="Validate schedule 12345",
    tools=tools,
    provider="auto",  # Routes to best tool-calling provider
)

response = await router.generate(request)

if response.tool_calls:
    for call in response.tool_calls:
        print(f"Tool: {call.name}")
        print(f"Args: {call.arguments}")
```

### Health Monitoring

```python
# Check all providers
health = await router.health_check_all()

for provider, status in health.items():
    if status.is_available:
        print(f"✓ {provider} available")
        print(f"  Latency: {status.avg_latency_ms}ms")
    else:
        print(f"✗ {provider} unavailable")
        print(f"  Error: {status.error_message}")

# Check circuit breakers
states = router.get_circuit_breaker_states()
for provider, state in states.items():
    print(f"{provider}: {state.state}")
```

### Statistics

```python
stats = router.get_stats()

print(f"Total requests: {stats.total_requests}")
print(f"Fallbacks: {stats.fallback_count}")
print(f"Tokens used: {stats.total_tokens_used}")

for provider, count in stats.requests_by_provider.items():
    print(f"  {provider}: {count} requests")
```

---

## Integration Points

### 1. MCP Server

Update MCP server to use LLM Router:

```python
# mcp-server/src/scheduler_mcp/llm_backend.py
from app.services.llm_router import LLMRouter

class MCPLLMBackend:
    def __init__(self):
        self.router = LLMRouter(airgap_mode=True)  # Local only for MCP

    async def generate(self, prompt: str):
        response = await self.router.generate(
            LLMRequest(prompt=prompt, provider="auto")
        )
        return response.content
```

### 2. Autonomous Loop Advisor

Wire LLMAdvisor to router:

```python
# backend/app/autonomous/advisor.py
from app.services.llm_router import LLMRouter

class LLMAdvisor:
    def __init__(self):
        self.router = LLMRouter(default_provider="ollama")

    async def suggest_parameters(self, context: dict) -> dict:
        request = LLMRequest(
            prompt=self._build_prompt(context),
            provider="ollama",  # Fast local suggestions
        )
        response = await self.router.generate(request)
        return self._parse_suggestions(response.content)
```

### 3. Chat Interface

Add local mode toggle:

```python
# backend/app/api/routes/claude_chat.py
@router.websocket("/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    mode: str = "cloud",  # "local", "cloud", "hybrid"
):
    if mode == "local":
        llm_router = LLMRouter(airgap_mode=True)
    elif mode == "hybrid":
        llm_router = LLMRouter(default_provider="ollama")
    else:
        llm_router = LLMRouter(default_provider="anthropic")

    # Use router for chat
    response = await llm_router.generate(request)
```

---

## Error Handling

### Provider-Level Errors

```python
try:
    response = await provider.generate(prompt="Test")
except httpx.RequestError as e:
    # Network error (Ollama unreachable)
    logger.error(f"Connection failed: {e}")
    raise LLMProviderError(f"Provider unreachable: {e}")
except httpx.HTTPStatusError as e:
    # HTTP error (500, 503, etc.)
    logger.error(f"HTTP {e.response.status_code}: {e.response.text}")
    raise LLMProviderError(f"Provider error: {e.response.status_code}")
```

### Router-Level Errors

```python
try:
    response = await router.generate(request)
except ProviderUnavailableError as e:
    # Circuit breaker open or provider unavailable
    logger.warning(f"Provider unavailable: {e}")
    # Try fallback or return error to user
except LLMProviderError as e:
    # All providers failed
    logger.error(f"All providers failed: {e}")
    # Return error response to user
```

---

## Performance Considerations

### Latency Comparison

| Provider | Model | Avg Latency | Use Case |
|----------|-------|-------------|----------|
| Ollama | llama3.2 (3B) | 50-200ms | Simple queries |
| Ollama | llama3.2 (8B) | 200-500ms | Complex queries |
| Ollama | mistral (7B) | 300-600ms | Tool calling |
| Anthropic | Claude Sonnet | 500-2000ms | Multi-step reasoning |

### Optimization Tips

1. **Use smaller models for simple tasks**
   ```python
   OLLAMA_FAST_MODEL = "llama3.2"  # 3B variant
   ```

2. **Enable streaming for long responses**
   ```python
   async for chunk in router.stream_generate(prompt):
       print(chunk.delta, end="")
   ```

3. **Cache responses for repeated queries**
   ```python
   # TODO: Add Redis caching layer
   ```

4. **Monitor circuit breaker states**
   ```python
   # Auto-scaling based on provider health
   if all_providers_degraded():
       scale_up_ollama_replicas()
   ```

---

## Testing

### Unit Tests

See `backend/tests/services/test_llm_router.py`:

```bash
# Run all LLM router tests
pytest backend/tests/services/test_llm_router.py -v

# Test specific functionality
pytest backend/tests/services/test_llm_router.py::TestCircuitBreaker -v
```

### Integration Tests

```bash
# Requires Ollama running
docker-compose up -d ollama

# Run integration tests
pytest backend/tests/integration/test_ollama_integration.py -v
```

### Manual Testing

```bash
# Run example usage
cd backend
python -m app.examples.llm_router_usage
```

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_DEFAULT_PROVIDER` | `ollama` | Default provider (ollama, anthropic) |
| `LLM_ENABLE_FALLBACK` | `true` | Enable fallback chain |
| `LLM_AIRGAP_MODE` | `false` | Disable cloud providers |
| `OLLAMA_URL` | `http://ollama:11434` | Ollama API URL |
| `OLLAMA_DEFAULT_MODEL` | `llama3.2` | Default Ollama model |
| `OLLAMA_FAST_MODEL` | `llama3.2` | Fast model for simple tasks |
| `OLLAMA_TOOL_MODEL` | `mistral` | Model with tool calling |
| `OLLAMA_TIMEOUT` | `60.0` | Request timeout (seconds) |
| `ANTHROPIC_API_KEY` | `` | Anthropic API key (optional) |
| `ANTHROPIC_DEFAULT_MODEL` | `claude-3-5-sonnet-20241022` | Default Claude model |

### Settings Object

```python
from app.core.config import get_settings

settings = get_settings()

router = LLMRouter(
    default_provider=settings.LLM_DEFAULT_PROVIDER,
    enable_fallback=settings.LLM_ENABLE_FALLBACK,
    airgap_mode=settings.LLM_AIRGAP_MODE,
)
```

---

## Future Enhancements

### Phase 1 (Current)
- ✅ Provider abstraction
- ✅ Ollama and Anthropic providers
- ✅ Task classification
- ✅ Circuit breaker pattern
- ✅ Fallback chain

### Phase 2 (Planned)
- [ ] vLLM provider for high-throughput
- [ ] Response caching layer
- [ ] Load balancing across multiple Ollama instances
- [ ] Fine-tuned models for scheduling domain
- [ ] Streaming support in router
- [ ] Tool call result caching

### Phase 3 (Future)
- [ ] Model performance benchmarking
- [ ] Automatic model selection based on benchmarks
- [ ] Cost optimization algorithms
- [ ] A/B testing framework
- [ ] Prompt optimization
- [ ] RAG integration with vector store

---

## Troubleshooting

### Ollama Connection Refused

**Symptom:** `LLMProviderError: Ollama connection failed: Connection refused`

**Solution:**
```bash
# Check if Ollama is running
docker-compose ps ollama

# Start Ollama
docker-compose up -d ollama

# Check logs
docker-compose logs -f ollama

# Verify endpoint
curl http://localhost:11434/api/tags
```

### Anthropic API Key Invalid

**Symptom:** `ProviderUnavailableError: Anthropic API key not configured`

**Solution:**
```bash
# Set API key in .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Or export temporarily
export ANTHROPIC_API_KEY=sk-ant-...

# Verify in settings
python -c "from app.core.config import get_settings; print(get_settings().ANTHROPIC_API_KEY[:10])"
```

### Circuit Breaker Open

**Symptom:** All requests fail with `ProviderUnavailableError`

**Solution:**
```python
# Check circuit breaker states
states = router.get_circuit_breaker_states()
for provider, state in states.items():
    if state.state == "open":
        print(f"{provider} circuit is open")
        print(f"Next retry: {state.next_retry}")

# Wait for auto-recovery or reset manually
router.circuit_breaker._states[provider].state = "closed"
```

---

## References

- [Ollama Docker Documentation](https://hub.docker.com/r/ollama/ollama)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [LLM Router Implementation Plan](../planning/LOCAL_LLM_DOCKER_INTEGRATION_PLAN.md)

---

*Document created: 2025-12-29*
*Last updated: 2025-12-29*
