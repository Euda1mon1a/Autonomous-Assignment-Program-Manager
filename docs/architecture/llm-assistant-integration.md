# LLM Assistant Integration (Luxury Feature)

> **Status**: Design proposal for consideration  
> **Constraint**: Base scheduler MUST work airgapped. LLM is additive only.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │ Scheduling UI   │  │ Assistant Panel (optional)   │  │
│  │ (always works)  │  │ - Only renders if LLM alive  │  │
│  └─────────────────┘  └──────────────────────────────┘  │
└────────────────┬────────────────────┬───────────────────┘
                 │                    │
                 ▼                    ▼
┌────────────────────────┐  ┌─────────────────────────────┐
│   Backend (FastAPI)    │  │   Ollama Sidecar Container  │
│                        │  │   ┌─────────────────────┐   │
│  /api/scheduling/*     │  │   │ SmolLM2-1.7B-Instruct│   │
│  (deterministic logic) │  │   │ Q4_K_M quantization │   │
│                        │  │   └─────────────────────┘   │
│  /api/assistant/*      │──│──▶ localhost:11434         │
│  (graceful degradation)│  │                             │
└────────────────────────┘  └─────────────────────────────┘
```

## Design Principles

1. **Airgap-first**: All scheduling logic is deterministic. LLM is cosmetic.
2. **Graceful degradation**: If Ollama is unreachable, assistant panel hides silently.
3. **No critical path**: LLM never blocks schedule generation or modification.

## Docker Compose Addition

```yaml
# docker-compose.override.yml (luxury features only)
services:
  ollama:
    image: ollama/ollama:latest
    container_name: scheduler-llm
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_KEEP_ALIVE=-1  # Never unload model
    deploy:
      resources:
        limits:
          memory: 3G  # Leave 1G headroom on 4GB instance
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    profiles:
      - luxury  # Only starts with: docker compose --profile luxury up

volumes:
  ollama_data:
```

## Model Initialization Script

```bash
#!/bin/bash
# scripts/init-llm.sh
# Run once after first deploy to pull the model

docker exec scheduler-llm ollama pull smollm2:1.7b-instruct-q4_K_M
```

## Backend Integration

```python
# backend/app/services/llm_assistant.py (sketch)

import httpx
from typing import Optional

OLLAMA_BASE = "http://ollama:11434"
TIMEOUT = 30.0  # Generous for CPU inference

async def query_assistant(prompt: str) -> Optional[str]:
    """
    Query the LLM assistant. Returns None if unavailable.
    Caller must handle None gracefully.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={
                    "model": "smollm2:1.7b-instruct-q4_K_M",
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json().get("response")
    except Exception:
        return None  # Graceful degradation

async def is_available() -> bool:
    """Health check for frontend to decide whether to show assistant panel."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{OLLAMA_BASE}/api/tags")
            return r.status_code == 200
    except Exception:
        return False
```

## Frontend Integration (Sketch)

```tsx
// features/assistant/AssistantPanel.tsx (concept only)

const AssistantPanel = () => {
  const { data: isAvailable } = useQuery({
    queryKey: ['llm-health'],
    queryFn: () => api.get('/api/assistant/health').then(r => r.data.available),
    refetchInterval: 60_000,
    retry: false,
  });

  if (!isAvailable) return null; // Silent degradation

  return (
    <aside className="assistant-panel">
      {/* Streaming chat UI */}
    </aside>
  );
};
```

## Use Cases (Within SmolLM2 Capability)

| Use Case | Feasibility | Notes |
|:---------|:------------|:------|
| "Summarize this week's schedule" | ✅ Good | Text generation strength |
| "Why is Dr. X assigned here?" | ⚠️ Marginal | Needs context injection |
| "Optimize the schedule" | ❌ No | Use deterministic solver |
| "Find conflicts" | ❌ No | Use existing conflict detection |

## Resource Requirements

| Tier | RAM | Monthly Cost | Recommended |
|:-----|:----|:-------------|:------------|
| Render Standard | 2GB | $25 | ❌ Too tight |
| Render Standard Plus | 4GB | $50 | ✅ Minimum viable |
| Self-hosted (4GB VPS) | 4GB | ~$20 | ✅ Alternative |

## Activation

```bash
# Development
docker compose --profile luxury up

# Production (Render)
# Add ENABLE_LLM_ASSISTANT=true to environment
# Upgrade to 4GB instance
```

---

**Decision**: This document is for consideration only. The base scheduler remains fully functional without any LLM components.
