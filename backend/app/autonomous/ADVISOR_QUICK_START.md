***REMOVED*** LLM Advisor Quick Start

**Fast setup guide for using the LLM Advisor with local Ollama.**

---

***REMOVED******REMOVED*** 1. Start Ollama

```bash
docker-compose up -d ollama
```

Wait for model pull (first time only):
```bash
docker-compose logs -f ollama
***REMOVED*** Look for: "pulled llama3.2"
```

---

***REMOVED******REMOVED*** 2. Basic Usage

***REMOVED******REMOVED******REMOVED*** Option A: Automatic (Default)

The advisor is enabled by default when you create an autonomous loop:

```python
from app.autonomous.loop import AutonomousLoop
from datetime import date

loop = AutonomousLoop.from_config(
    db=db,
    scenario="baseline",
    start_date=date(2025, 1, 1),
    end_date=date(2025, 3, 31),
)

***REMOVED*** Advisor is used automatically during iterations
result = loop.run()
```

***REMOVED******REMOVED******REMOVED*** Option B: Manual Control

```python
from app.autonomous.advisor import LLMAdvisor

***REMOVED*** Create advisor
advisor = LLMAdvisor(
    model="llama3.2",
    airgap_mode=True,  ***REMOVED*** Local only
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
        print(f"Applied: {suggestion.reasoning}")
```

---

***REMOVED******REMOVED*** 3. Run Examples

```bash
cd backend
python -m app.autonomous.examples.advisor_example
```

**Output:**
- Mock advisor example (no LLM needed)
- Health check
- Real LLM suggestions (if Ollama running)

---

***REMOVED******REMOVED*** 4. Available Models

Pull additional models:

```bash
***REMOVED*** Faster but less capable
docker-compose exec ollama ollama pull llama3.2       ***REMOVED*** 3B params, 4GB RAM

***REMOVED*** Better reasoning (default)
docker-compose exec ollama ollama pull llama3.2:8b    ***REMOVED*** 8B params, 8GB RAM

***REMOVED*** Tool calling support
docker-compose exec ollama ollama pull mistral        ***REMOVED*** 7B params, 8GB RAM

***REMOVED*** Code generation
docker-compose exec ollama ollama pull qwen2.5        ***REMOVED*** 7B params, 8GB RAM
```

Then use in advisor:
```python
advisor = LLMAdvisor(model="mistral")  ***REMOVED*** Use Mistral instead
```

---

***REMOVED******REMOVED*** 5. Troubleshooting

***REMOVED******REMOVED******REMOVED*** "Connection refused"

```bash
***REMOVED*** Check Ollama is running
docker-compose ps ollama

***REMOVED*** Check logs
docker-compose logs ollama

***REMOVED*** Restart if needed
docker-compose restart ollama
```

***REMOVED******REMOVED******REMOVED*** "Model not found"

```bash
***REMOVED*** List available models
docker-compose exec ollama ollama list

***REMOVED*** Pull missing model
docker-compose exec ollama ollama pull llama3.2
```

***REMOVED******REMOVED******REMOVED*** Slow responses

Enable GPU (if available):
```yaml
***REMOVED*** docker-compose.yml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

---

***REMOVED******REMOVED*** 6. Airgap Mode

For systems without internet:

1. **On connected system:**
   ```bash
   ollama pull llama3.2
   ollama pull mistral
   tar -czf ollama-models.tar.gz ~/.ollama/models
   ```

2. **Transfer `ollama-models.tar.gz` to airgap system**

3. **On airgap system:**
   ```bash
   tar -xzf ollama-models.tar.gz -C ~/.ollama/
   docker-compose up -d ollama
   ```

---

***REMOVED******REMOVED*** 7. Verify Setup

```python
import asyncio
from app.services.llm_router import LLMRouter

async def check():
    router = LLMRouter(airgap_mode=True)
    health = await router.health_check_all()
    print(f"Ollama available: {health['ollama'].is_available}")
    await router.close()

asyncio.run(check())
```

**Expected:** `Ollama available: True`

---

***REMOVED******REMOVED*** 8. Configuration

***REMOVED******REMOVED******REMOVED*** Environment Variables

```bash
***REMOVED*** .env
OLLAMA_URL=http://ollama:11434
LOCAL_LLM_MODEL=llama3.2
AIRGAP_MODE=true
```

***REMOVED******REMOVED******REMOVED*** Custom Settings

```python
advisor = LLMAdvisor(
    model="mistral",           ***REMOVED*** Model name
    temperature=0.1,           ***REMOVED*** 0.0-1.0 (lower = more deterministic)
    max_tokens=1024,           ***REMOVED*** Max response length
    airgap_mode=True,          ***REMOVED*** Local only
)
```

---

***REMOVED******REMOVED*** What the Advisor Does

- ✅ Suggests algorithm switches when stuck
- ✅ Recommends timeout adjustments
- ✅ Identifies critical failure modes
- ✅ Explains schedule violations
- ✅ Validates all suggestions against schema
- ✅ Falls back gracefully if LLM unavailable

---

***REMOVED******REMOVED*** What It Doesn't Do

- ❌ Make decisions without validation
- ❌ Override ACGME compliance rules
- ❌ Require cloud API access
- ❌ Crash the loop on errors

---

***REMOVED******REMOVED*** Performance

| Model | Hardware | Latency |
|-------|----------|---------|
| llama3.2 3B | CPU | 3-8s |
| llama3.2 3B | GPU | 1-2s |
| llama3.2 8B | CPU | 10-20s |
| llama3.2 8B | GPU | 2-5s |

---

***REMOVED******REMOVED*** Next Steps

- 📖 Read full docs: [examples/README.md](examples/README.md)
- 🔬 Run examples: `python -m app.autonomous.examples.advisor_example`
- 📊 Review implementation: [IMPLEMENTATION_SUMMARY.md](/IMPLEMENTATION_SUMMARY.md)
- 📋 See planning doc: [LOCAL_LLM_DOCKER_INTEGRATION_PLAN.md](/docs/planning/LOCAL_LLM_DOCKER_INTEGRATION_PLAN.md)

---

**Ready to use!** The advisor is integrated and works out of the box with Ollama.
