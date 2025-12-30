***REMOVED*** Local LLM Docker Integration Plan

> **Date:** 2025-12-29
> **Branch:** claude/local-llm-docker-integration-RtomW
> **Status:** Draft Proposal
> **Priority:** High (Aligns with Airgap Readiness Requirements)

---

***REMOVED******REMOVED*** Executive Summary

This document proposes integrating local LLM capabilities via Docker to enhance the Residency Scheduler. The integration addresses:

- **Airgap Requirements**: Enable AI features without cloud connectivity (military/secure deployments)
- **Cost Optimization**: Reduce Anthropic API costs by routing simple tasks to local models
- **Privacy Compliance**: Keep PHI/HIPAA-sensitive data on-premises
- **Latency Reduction**: Sub-100ms responses for routine queries
- **Resilience**: Fallback when cloud APIs are unavailable

---

***REMOVED******REMOVED*** Table of Contents

1. [Current State Analysis](***REMOVED***current-state-analysis)
2. [Framework Comparison](***REMOVED***framework-comparison)
3. [Recommended Architecture](***REMOVED***recommended-architecture)
4. [Integration Opportunities](***REMOVED***integration-opportunities)
5. [Model Recommendations](***REMOVED***model-recommendations)
6. [Implementation Phases](***REMOVED***implementation-phases)
7. [Docker Configuration](***REMOVED***docker-configuration)
8. [Security Considerations](***REMOVED***security-considerations)
9. [Testing Strategy](***REMOVED***testing-strategy)
10. [Cost-Benefit Analysis](***REMOVED***cost-benefit-analysis)

---

***REMOVED******REMOVED*** Current State Analysis

***REMOVED******REMOVED******REMOVED*** What Exists Today

| Component | Status | Gap |
|-----------|--------|-----|
| **MCP Server** | 81 tools registered | All LLM calls → Anthropic API |
| **Claude Chat Bridge** | WebSocket-based | No local fallback |
| **Vector Embeddings** | pgvector + sentence-transformers | Already local |
| **LLM Advisor** | Defined in `autonomous/advisor.py` | Not wired to any LLM |
| **Model Selection** | `ModelTier` table exists | Not implemented |

***REMOVED******REMOVED******REMOVED*** Key Findings from Codebase Exploration

1. **Single Point of Failure**: All AI features require `ANTHROPIC_API_KEY`
2. **Airgap Blocker**: System loses AI capabilities when air-gapped
3. **Cost Accumulation**: No routing logic to use cheaper models for simple tasks
4. **Infrastructure Ready**: Docker Compose, Redis, PostgreSQL all in place

---

***REMOVED******REMOVED*** Framework Comparison

***REMOVED******REMOVED******REMOVED*** 2025 Local LLM Docker Options

| Framework | Strengths | Weaknesses | Best For |
|-----------|-----------|------------|----------|
| **[Ollama](https://ollama.com/)** | Easy setup, 100+ models, OpenAI-compatible API | Single GPU | Development, small-medium deployments |
| **[vLLM](https://docs.vllm.ai/)** | PagedAttention, high throughput, tensor parallelism | Complex setup, GPU required | Production, high-concurrency |
| **[Docker Model Runner](https://docs.docker.com/ai/model-runner/)** | Native Docker integration, Compose support | New (April 2025), limited models | Docker-native workflows |
| **[LocalAI](https://localai.io/)** | OpenAI-compatible, supports many backends | Complex configuration | Multi-model scenarios |
| **[llama.cpp](https://github.com/ggerganov/llama.cpp)** | CPU inference, minimal deps | Manual compilation | Edge/CPU-only deployments |

***REMOVED******REMOVED******REMOVED*** Recommendation: **Ollama (Primary) + vLLM (Production Option)**

**Rationale:**
- Ollama provides the fastest path to integration with OpenAI-compatible API
- vLLM offers production-grade performance when GPU available
- Both integrate well with existing MCP architecture
- Tool calling supported (Llama 3.1+, Mistral, Qwen)

---

***REMOVED******REMOVED*** Recommended Architecture

***REMOVED******REMOVED******REMOVED*** Multi-Tier LLM Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     LLM Router Service                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Task Classification → Model Selection → Routing        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │   Ollama    │      │  Anthropic  │      │   vLLM      │
   │   (Local)   │      │  (Cloud)    │      │ (Optional)  │
   ├─────────────┤      ├─────────────┤      ├─────────────┤
   │ Llama 3.2   │      │ Claude      │      │ Mistral     │
   │ Mistral 7B  │      │ Sonnet/Opus │      │ Llama 3.1   │
   │ Phi-3       │      │             │      │             │
   └─────────────┘      └─────────────┘      └─────────────┘
        │                    │                    │
        │    Simple/Fast     │   Complex/Tool     │   High-Throughput
        │    Privacy-Req     │   Multi-Step       │   Batch Processing
        └────────────────────┴────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Service Integration Points

```yaml
***REMOVED*** docker-compose.yml additions
services:
  ollama:
    image: ollama/ollama:latest
    container_name: residency-scheduler-ollama
    volumes:
      - ollama_models:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3

  llm-router:
    build:
      context: ./llm-router
      dockerfile: Dockerfile
    container_name: residency-scheduler-llm-router
    environment:
      OLLAMA_URL: http://ollama:11434
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      DEFAULT_PROVIDER: ollama  ***REMOVED*** or anthropic
      FALLBACK_ENABLED: true
    depends_on:
      - ollama
    networks:
      - app-network
```

---

***REMOVED******REMOVED*** Integration Opportunities

***REMOVED******REMOVED******REMOVED*** 1. **LLM Advisor for Autonomous Loop** (High Priority)

**Current Gap:** `backend/app/autonomous/advisor.py` defines `LLMAdvisor` but isn't connected to any LLM.

**Opportunity:** Wire up to local Ollama for:
- Parameter tuning suggestions
- Failure analysis
- Strategy recommendations

**Implementation:**
```python
***REMOVED*** backend/app/autonomous/llm_client.py
class LocalLLMClient:
    """Multi-provider LLM client with local fallback."""

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2",
        provider: str = "auto"
    ) -> str:
        """Route to appropriate provider based on task."""
        if provider == "auto":
            provider = self._select_provider(prompt)

        if provider == "ollama":
            return await self._ollama_generate(prompt, model)
        else:
            return await self._anthropic_generate(prompt)
```

***REMOVED******REMOVED******REMOVED*** 2. **MCP Server Local Fallback** (High Priority)

**Current Gap:** MCP tools can't function without Anthropic API.

**Opportunity:** Add Ollama as MCP client option:
```python
***REMOVED*** mcp-server/src/scheduler_mcp/llm_backend.py
class MCPLLMBackend:
    """Switchable LLM backend for MCP operations."""

    providers = {
        "ollama": OllamaProvider,
        "anthropic": AnthropicProvider,
    }

    def __init__(self, default_provider: str = "ollama"):
        self.default = default_provider
        self.fallback_chain = ["ollama", "anthropic"]
```

***REMOVED******REMOVED******REMOVED*** 3. **Smart Task Routing** (Medium Priority)

**Opportunity:** Route tasks to appropriate model tier:

| Task Type | Local Model | Cloud Model | Routing Logic |
|-----------|-------------|-------------|---------------|
| Documentation generation | Llama 3.2 (3B) | - | Always local |
| Simple Q&A | Mistral 7B | - | Always local |
| Schedule explanation | Llama 3.2 (8B) | - | Always local |
| Complex tool calls | - | Claude Sonnet | Always cloud |
| Multi-step reasoning | - | Claude Opus | Always cloud |
| Privacy-sensitive | Llama 3.2 | - | Always local |

***REMOVED******REMOVED******REMOVED*** 4. **Chat Interface Local Mode** (Medium Priority)

**Current:** `backend/app/api/routes/claude_chat.py` only uses Anthropic.

**Opportunity:** Add "local mode" toggle:
```python
@router.websocket("/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    mode: str = "cloud"  ***REMOVED*** or "local" or "hybrid"
):
    if mode == "local":
        llm = OllamaClient()
    elif mode == "hybrid":
        llm = HybridLLMClient()  ***REMOVED*** Routes based on complexity
    else:
        llm = AnthropicClient()
```

***REMOVED******REMOVED******REMOVED*** 5. **Embedding Generation** (Low Priority - Already Local)

**Current:** Uses `sentence-transformers` (all-MiniLM-L6-v2) locally.

**Opportunity:** Optionally use Ollama embeddings for larger context:
```bash
***REMOVED*** Ollama embedding models
ollama pull nomic-embed-text    ***REMOVED*** 137M params, 768 dims
ollama pull mxbai-embed-large   ***REMOVED*** 334M params, 1024 dims
```

***REMOVED******REMOVED******REMOVED*** 6. **MCP Tool Integration with Ollama** (High Priority)

**Opportunity:** Use existing MCP-Ollama bridges:

- **[ollama-mcp-bridge](https://github.com/patruff/ollama-mcp-bridge)**: Proxy that adds MCP tools to Ollama
- **[mcp-client-for-ollama](https://github.com/jonigl/mcp-client-for-ollama)**: TUI client with tool management

This would allow the 81 existing MCP tools to work with local models.

---

***REMOVED******REMOVED*** Model Recommendations

***REMOVED******REMOVED******REMOVED*** For Medical Scheduling Context

| Model | Size | VRAM | Use Case | Ollama Command |
|-------|------|------|----------|----------------|
| **Llama 3.2** | 3B | 4GB | Fast responses, simple queries | `ollama pull llama3.2` |
| **Llama 3.2** | 8B | 8GB | General purpose, good reasoning | `ollama pull llama3.2:8b` |
| **Mistral 7B** | 7B | 8GB | Tool calling, structured output | `ollama pull mistral` |
| **Qwen 2.5** | 7B | 8GB | Code generation, JSON output | `ollama pull qwen2.5` |
| **Phi-3 Mini** | 3.8B | 4GB | Edge deployment, CPU inference | `ollama pull phi3` |
| **Medical-Llama3** | 8B | 8GB | Medical domain knowledge | `ollama pull lazarevtill/Medical-Llama3-8B` |

***REMOVED******REMOVED******REMOVED*** Recommended Default Configuration

```yaml
***REMOVED*** Environment variables
LOCAL_LLM_MODEL: llama3.2:8b        ***REMOVED*** Primary local model
LOCAL_LLM_FAST_MODEL: llama3.2       ***REMOVED*** Fast model for simple tasks
LOCAL_LLM_TOOL_MODEL: mistral        ***REMOVED*** Model with tool calling
LOCAL_LLM_FALLBACK: qwen2.5          ***REMOVED*** Backup if primary unavailable
```

---

***REMOVED******REMOVED*** Implementation Phases

***REMOVED******REMOVED******REMOVED*** Phase 1: Infrastructure (Week 1)

**Goal:** Add Ollama to Docker Compose, verify connectivity

**Tasks:**
1. [ ] Add Ollama service to `docker-compose.yml`
2. [ ] Add GPU passthrough configuration (optional)
3. [ ] Create `ollama_models` volume for persistence
4. [ ] Add health checks and startup script to pull models
5. [ ] Create `backend/app/core/llm_config.py` for settings
6. [ ] Add environment variables to `.env.example`

**Deliverables:**
- `docker-compose up` includes Ollama
- Models auto-pull on first start
- Health endpoint confirms Ollama availability

***REMOVED******REMOVED******REMOVED*** Phase 2: LLM Router Service (Week 2)

**Goal:** Centralized routing logic for multi-provider LLM calls

**Tasks:**
1. [ ] Create `backend/app/services/llm_router.py`
2. [ ] Implement provider abstraction (Ollama, Anthropic, vLLM)
3. [ ] Add task classification for auto-routing
4. [ ] Implement fallback chain (local → cloud)
5. [ ] Add circuit breaker for provider failures
6. [ ] Create Pydantic schemas for LLM requests/responses

**Deliverables:**
- Unified `LLMRouter.generate()` API
- Automatic fallback on provider failure
- Metrics for provider usage

***REMOVED******REMOVED******REMOVED*** Phase 3: MCP Integration (Week 3)

**Goal:** Connect MCP tools to local LLM

**Tasks:**
1. [ ] Integrate `ollama-mcp-bridge` or build custom adapter
2. [ ] Add local LLM provider to MCP server
3. [ ] Test tool calling with Mistral/Llama 3.1+
4. [ ] Update MCP health checks
5. [ ] Document MCP + Ollama workflow

**Deliverables:**
- MCP tools callable via local LLM
- Tool calling works with Mistral

***REMOVED******REMOVED******REMOVED*** Phase 4: Autonomous Loop Integration (Week 4)

**Goal:** Wire LLMAdvisor to local model

**Tasks:**
1. [ ] Update `autonomous/advisor.py` to use LLMRouter
2. [ ] Add advisory prompt templates
3. [ ] Implement suggestion validation
4. [ ] Test autonomous loop with local LLM
5. [ ] Add logging for advisory decisions

**Deliverables:**
- LLMAdvisor generates suggestions via Ollama
- Autonomous loop can run airgapped

***REMOVED******REMOVED******REMOVED*** Phase 5: Chat Interface & Polish (Week 5)

**Goal:** User-facing local LLM option

**Tasks:**
1. [ ] Add "local mode" toggle to chat WebSocket
2. [ ] Implement hybrid routing for chat
3. [ ] Add model selection UI (if frontend integration desired)
4. [ ] Performance benchmarking
5. [ ] Documentation and admin guide

**Deliverables:**
- Users can choose local vs cloud
- Performance metrics documented

---

***REMOVED******REMOVED*** Docker Configuration

***REMOVED******REMOVED******REMOVED*** Full Docker Compose Addition

```yaml
***REMOVED*** docker-compose.ollama.yml (overlay)
services:
  ollama:
    image: ollama/ollama:latest
    container_name: residency-scheduler-ollama
    restart: unless-stopped
    volumes:
      - ollama_models:/root/.ollama
      ***REMOVED*** Mount custom modelfiles if needed
      - ./ollama/Modelfile.scheduler:/Modelfile.scheduler:ro
    ports:
      - "127.0.0.1:11434:11434"  ***REMOVED*** Localhost only for security
    environment:
      OLLAMA_HOST: "0.0.0.0"
      OLLAMA_ORIGINS: "*"  ***REMOVED*** Allow cross-container requests
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 4G
          ***REMOVED*** GPU optional - uncomment for GPU inference
          ***REMOVED*** devices:
          ***REMOVED***   - driver: nvidia
          ***REMOVED***     count: 1
          ***REMOVED***     capabilities: [gpu]
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s  ***REMOVED*** Allow time for model loading
    ***REMOVED*** Model pre-pull on container start
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        /bin/ollama serve &
        sleep 5
        ollama pull llama3.2
        ollama pull mistral
        wait

  ***REMOVED*** Optional: vLLM for production high-throughput
  ***REMOVED*** vllm:
  ***REMOVED***   image: vllm/vllm-openai:latest
  ***REMOVED***   container_name: residency-scheduler-vllm
  ***REMOVED***   command: --model meta-llama/Llama-3.2-8B-Instruct --gpu-memory-utilization 0.9
  ***REMOVED***   volumes:
  ***REMOVED***     - vllm_cache:/root/.cache/huggingface
  ***REMOVED***   deploy:
  ***REMOVED***     resources:
  ***REMOVED***       reservations:
  ***REMOVED***         devices:
  ***REMOVED***           - driver: nvidia
  ***REMOVED***             count: 1
  ***REMOVED***             capabilities: [gpu]
  ***REMOVED***   networks:
  ***REMOVED***     - app-network

volumes:
  ollama_models:
    driver: local
  ***REMOVED*** vllm_cache:
  ***REMOVED***   driver: local
```

***REMOVED******REMOVED******REMOVED*** Airgap Configuration

```yaml
***REMOVED*** docker-compose.airgap.yml (for offline deployment)
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_models:/root/.ollama
      ***REMOVED*** Pre-loaded models (copy from online system)
      - ./airgap/ollama-models:/root/.ollama/models:ro
    environment:
      OLLAMA_HOST: "0.0.0.0"
      ***REMOVED*** Disable telemetry
      OLLAMA_NOPRUNE: "1"
    networks:
      - app-network
```

---

***REMOVED******REMOVED*** Security Considerations

***REMOVED******REMOVED******REMOVED*** Network Security

| Concern | Mitigation |
|---------|------------|
| Ollama API exposed | Bind to `127.0.0.1:11434` only |
| Cross-container access | Docker network isolation |
| Model tampering | Read-only model mounts in airgap |
| Resource exhaustion | Memory limits in Docker |

***REMOVED******REMOVED******REMOVED*** Data Privacy

| Concern | Mitigation |
|---------|------------|
| PHI in prompts | Local processing, no cloud transmission |
| Model training on data | Ollama doesn't train on inference |
| Logs containing PHI | Structured logging, no prompt logging |

***REMOVED******REMOVED******REMOVED*** HIPAA Compliance

- Local LLM keeps data on-premises
- No data transmitted to third parties
- Audit log integration for LLM calls

---

***REMOVED******REMOVED*** Testing Strategy

***REMOVED******REMOVED******REMOVED*** Unit Tests

```python
***REMOVED*** backend/tests/services/test_llm_router.py
class TestLLMRouter:
    async def test_ollama_generation(self):
        """Test direct Ollama call."""
        router = LLMRouter(default_provider="ollama")
        response = await router.generate("Hello, world!")
        assert response is not None

    async def test_fallback_to_cloud(self):
        """Test fallback when Ollama unavailable."""
        router = LLMRouter(default_provider="ollama")
        ***REMOVED*** Mock Ollama down
        response = await router.generate("Complex task")
        assert response.provider == "anthropic"

    async def test_task_routing(self):
        """Test automatic task classification."""
        router = LLMRouter()
        simple = await router.classify_task("What time is it?")
        complex = await router.classify_task("Analyze the schedule for ACGME violations")
        assert simple.recommended_provider == "ollama"
        assert complex.recommended_provider == "anthropic"
```

***REMOVED******REMOVED******REMOVED*** Integration Tests

```python
***REMOVED*** backend/tests/integration/test_ollama_mcp.py
async def test_mcp_tool_calling_with_ollama():
    """Test MCP tools work with local Ollama."""
    async with MCPClient(provider="ollama") as client:
        result = await client.call_tool("validate_schedule_tool", {"schedule_id": 1})
        assert result.status == "success"
```

***REMOVED******REMOVED******REMOVED*** Load Tests

```javascript
// load-tests/scenarios/local-llm-stress.js
export default function() {
  const responses = http.batch([
    ['POST', 'http://localhost:11434/api/generate', JSON.stringify({
      model: 'llama3.2',
      prompt: 'Explain ACGME 80-hour rule',
      stream: false
    })]
  ]);
  check(responses[0], {
    'status is 200': (r) => r.status === 200,
    'response time < 5s': (r) => r.timings.duration < 5000,
  });
}
```

---

***REMOVED******REMOVED*** Cost-Benefit Analysis

***REMOVED******REMOVED******REMOVED*** Estimated Savings

| Scenario | Cloud Cost/Month | Local Cost/Month | Savings |
|----------|------------------|------------------|---------|
| 10K simple queries | $50 (Haiku) | $0 (Ollama) | $50 |
| 5K complex queries | $150 (Sonnet) | $150 (unchanged) | $0 |
| 1K multi-step | $100 (Opus) | $100 (unchanged) | $0 |
| **Total** | **$300** | **$150** | **50%** |

***REMOVED******REMOVED******REMOVED*** Hardware Requirements

| Configuration | GPU | RAM | Disk | Models |
|---------------|-----|-----|------|--------|
| **Minimal** | None (CPU) | 16GB | 20GB | Phi-3, TinyLlama |
| **Recommended** | RTX 3060 12GB | 32GB | 50GB | Llama 3.2 8B, Mistral 7B |
| **Production** | RTX 4090 24GB | 64GB | 100GB | All models, fast inference |

***REMOVED******REMOVED******REMOVED*** Intangible Benefits

- **Airgap Capability**: Required for military deployments
- **Privacy Compliance**: No PHI leaves the network
- **Latency**: Sub-100ms for simple queries
- **Reliability**: No API outages affect scheduling

---

***REMOVED******REMOVED*** Open Questions

1. **GPU Availability**: Do target deployments have GPU? (Affects model selection)
2. **Model Fine-Tuning**: Should we fine-tune a model on scheduling domain? (Adds complexity)
3. **Frontend Integration**: Do users need to select local vs cloud? (UX decision)
4. **vLLM vs Ollama**: For production, is the complexity of vLLM worth the throughput? (Performance testing needed)

---

***REMOVED******REMOVED*** References

***REMOVED******REMOVED******REMOVED*** Documentation
- [Ollama Docker Guide](https://hub.docker.com/r/ollama/ollama)
- [vLLM Documentation](https://docs.vllm.ai/)
- [Docker Model Runner](https://docs.docker.com/ai/model-runner/)
- [Ollama MCP Bridge](https://github.com/patruff/ollama-mcp-bridge)
- [MCP Client for Ollama](https://github.com/jonigl/mcp-client-for-ollama)
- [Medical-Llama3-8B](https://ollama.com/lazarevtill/Medical-Llama3-8B)

***REMOVED******REMOVED******REMOVED*** Internal Docs
- [Airgap Readiness Audit](./AIRGAP_READINESS_AUDIT.md)
- [MCP Implementation Plan](./MCP_IMPLEMENTATION_PLAN.md)
- [Cross-Disciplinary Resilience](../architecture/cross-disciplinary-resilience.md)

---

***REMOVED******REMOVED*** Next Steps

1. **Review this plan** with stakeholders
2. **Decide on GPU requirements** for target deployments
3. **Begin Phase 1** implementation
4. **Create tracking issue** in GitHub

---

*Document created: 2025-12-29*
*Author: Claude Code Session*
