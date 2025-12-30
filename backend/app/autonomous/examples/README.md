***REMOVED*** Autonomous Scheduling Loop Examples

This directory contains example scripts demonstrating how to use the autonomous scheduling loop and its components.

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** For Mock Examples (No LLM Required)

Mock examples work without any external dependencies:
```bash
python -m app.autonomous.examples.advisor_example
```

***REMOVED******REMOVED******REMOVED*** For Real LLM Examples (Ollama Required)

1. Start Ollama via Docker Compose:
```bash
docker-compose up -d ollama
```

2. Wait for Ollama to pull the default models (llama3.2):
```bash
docker-compose logs -f ollama
***REMOVED*** Wait for "pulled llama3.2" message
```

3. Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

4. Run examples:
```bash
python -m app.autonomous.examples.advisor_example
```

***REMOVED******REMOVED*** Available Examples

***REMOVED******REMOVED******REMOVED*** `advisor_example.py`

Demonstrates the LLM Advisor integration:

**Example 1: Mock Advisor**
- Uses heuristic-based suggestions (no LLM)
- Always available, no setup required
- Good for testing without Ollama

**Example 2: LLM Router Health Check**
- Checks availability of LLM providers
- Shows router statistics
- Useful for troubleshooting

**Example 3: Real LLM Advisor**
- Uses local Ollama for suggestions
- Requires Ollama running
- Demonstrates actual LLM advisory loop

***REMOVED******REMOVED*** LLM Advisor Usage

***REMOVED******REMOVED******REMOVED*** Basic Usage

```python
from app.autonomous.advisor import LLMAdvisor
from app.autonomous.state import RunState, GeneratorParams
from app.autonomous.evaluator import EvaluationResult

***REMOVED*** Create advisor (uses local Ollama by default)
advisor = LLMAdvisor(
    model="llama3.2",
    airgap_mode=True,  ***REMOVED*** Local only, no cloud
)

***REMOVED*** Get suggestion
suggestion = await advisor.suggest(
    state=state,
    last_evaluation=evaluation,
    history=history,
)

***REMOVED*** Validate and apply
if suggestion and advisor.validate_suggestion(suggestion):
    if suggestion.params:
        state.current_params = suggestion.params
```

***REMOVED******REMOVED******REMOVED*** Integration with Autonomous Loop

The `AutonomousLoopWithAdvisor` class automatically uses the LLM advisor:

```python
from app.autonomous.loop import AutonomousLoop

***REMOVED*** Create loop (advisor is auto-initialized)
loop = AutonomousLoop.from_config(
    db=db,
    scenario="baseline",
    start_date=date(2025, 1, 1),
    end_date=date(2025, 3, 31),
)

***REMOVED*** Advisor is used automatically during iterations
result = loop.run()
```

***REMOVED******REMOVED*** Configuration

***REMOVED******REMOVED******REMOVED*** Environment Variables

```bash
***REMOVED*** Ollama configuration
OLLAMA_URL=http://ollama:11434  ***REMOVED*** Default in Docker Compose

***REMOVED*** Model selection
LOCAL_LLM_MODEL=llama3.2        ***REMOVED*** Default model
LOCAL_LLM_TEMPERATURE=0.3       ***REMOVED*** Lower = more deterministic

***REMOVED*** Airgap mode (local only)
AIRGAP_MODE=true                ***REMOVED*** Disables cloud providers
```

***REMOVED******REMOVED******REMOVED*** Custom LLM Router

```python
from app.services.llm_router import LLMRouter

***REMOVED*** Create custom router
router = LLMRouter(
    default_provider="ollama",
    enable_fallback=True,
    airgap_mode=True,  ***REMOVED*** Local only
)

***REMOVED*** Pass to advisor
advisor = LLMAdvisor(llm_router=router, model="llama3.2")
```

***REMOVED******REMOVED*** Model Recommendations

| Model | Size | Use Case | Ollama Command |
|-------|------|----------|----------------|
| **llama3.2** | 3B | Fast responses, simple queries | `ollama pull llama3.2` |
| **llama3.2:8b** | 8B | Better reasoning, default | `ollama pull llama3.2:8b` |
| **mistral** | 7B | Tool calling, structured output | `ollama pull mistral` |
| **qwen2.5** | 7B | Code generation, JSON | `ollama pull qwen2.5` |

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** "No LLM router configured"

**Cause:** Ollama is not running or not accessible.

**Fix:**
```bash
docker-compose up -d ollama
docker-compose logs ollama  ***REMOVED*** Check for errors
```

***REMOVED******REMOVED******REMOVED*** "Connection refused" to Ollama

**Cause:** Ollama port not exposed or wrong URL.

**Fix:** Check `docker-compose.yml` has:
```yaml
ollama:
  ports:
    - "11434:11434"
```

***REMOVED******REMOVED******REMOVED*** "Model not found"

**Cause:** Model hasn't been pulled yet.

**Fix:**
```bash
docker-compose exec ollama ollama pull llama3.2
```

***REMOVED******REMOVED******REMOVED*** Slow responses

**Cause:** Running on CPU instead of GPU.

**Fix:** Enable GPU passthrough in `docker-compose.yml`:
```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

***REMOVED******REMOVED*** Airgap Mode

For deployments without internet access:

1. **Pre-pull models on connected system:**
```bash
ollama pull llama3.2
ollama pull mistral
```

2. **Export models:**
```bash
***REMOVED*** Copy Ollama models directory
cp -r ~/.ollama/models ./airgap/ollama-models
```

3. **Load on airgap system:**
```bash
***REMOVED*** Mount pre-pulled models
docker-compose -f docker-compose.airgap.yml up -d
```

4. **Verify:**
```bash
docker-compose exec ollama ollama list
```

***REMOVED******REMOVED*** Performance

Typical latencies (CPU, llama3.2 3B):
- Simple query: 2-5 seconds
- Advisory suggestion: 3-8 seconds
- Complex reasoning: 10-20 seconds

With GPU (RTX 3060):
- Simple query: 0.5-1 second
- Advisory suggestion: 1-2 seconds
- Complex reasoning: 2-5 seconds

***REMOVED******REMOVED*** Next Steps

- Read the [Autonomous Loop Documentation](../README.md)
- See [LLM Router Documentation](/backend/app/services/llm_router.py)
- Review [Local LLM Integration Plan](/docs/planning/LOCAL_LLM_DOCKER_INTEGRATION_PLAN.md)
