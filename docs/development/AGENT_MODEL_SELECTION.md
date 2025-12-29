# Agent Model Selection

> **Status:** Active
> **Version:** 1.0.0
> **Last Updated:** 2025-12-29

This document describes the vector-based agent model selection system that enables ORCHESTRATOR to choose optimal Claude model tiers (haiku/sonnet/opus) when spawning subagents.

---

## Overview

When ORCHESTRATOR spawns agents, it should select the most cost-effective model that can handle the task:

| Model | Cost | Latency | Use Case |
|-------|------|---------|----------|
| **Haiku** | 1x | Fast | Simple tasks, metadata updates, delegation auditing |
| **Sonnet** | 10x | Medium | Code generation, testing, analysis |
| **Opus** | 100x | Slow | Architecture, coordination, multi-agent synthesis |

Without explicit model selection, all agents inherit the parent model (typically Opus), wasting resources on simple tasks.

---

## Architecture

### Database Schema (pgvector)

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                     │
├─────────────────────────────────────────────────────────────┤
│  model_tiers              │  Static lookup table            │
│  ├─ agent_name (PK)       │  Default model per agent        │
│  ├─ default_model         │  haiku | sonnet | opus          │
│  └─ notes                 │  Rationale for assignment       │
├───────────────────────────┼─────────────────────────────────┤
│  agent_embeddings         │  Pre-computed from specs        │
│  ├─ agent_name (PK)       │  Agent identifier               │
│  ├─ embedding (384-dim)   │  sentence-transformers vector   │
│  ├─ spec_hash             │  SHA256 for change detection    │
│  └─ capabilities          │  Extracted capability text      │
├───────────────────────────┼─────────────────────────────────┤
│  task_history             │  Learning dataset               │
│  ├─ id (PK)               │  Auto-increment                 │
│  ├─ task_description      │  Original task text             │
│  ├─ embedding (384-dim)   │  Embedded task for similarity   │
│  ├─ agent_used            │  Which agent handled it         │
│  ├─ model_used            │  Which model tier               │
│  ├─ success               │  Boolean outcome                │
│  └─ duration_ms           │  Execution time                 │
└─────────────────────────────────────────────────────────────┘
```

### Embedding Pipeline

```
Agent Spec (.md file)
       │
       ▼
┌──────────────────────┐
│  EmbeddingService    │
│  (sentence-transformers)
│  all-MiniLM-L6-v2    │
│  384 dimensions      │
│  Local CPU (no API)  │
└──────────────────────┘
       │
       ▼
  agent_embeddings table
```

### Query Flow

```
ORCHESTRATOR receives task
       │
       ▼
┌──────────────────────┐
│ 1. Embed task text   │
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│ 2. Query similar     │
│    historical tasks  │
│    (cosine similarity)
└──────────────────────┘
       │
       ├─── History exists ──▶ Recommend (agent, model) from successes
       │
       └─── No history ──────▶ Fall back to model_tiers lookup
       │
       ▼
┌──────────────────────┐
│ 3. Spawn agent with  │
│    explicit model=   │
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│ 4. Record outcome    │
│    to task_history   │
└──────────────────────┘
```

---

## Model Tier Assignments

### Haiku (4 agents)
Simple tasks requiring minimal reasoning.

| Agent | Rationale |
|-------|-----------|
| DELEGATION_AUDITOR | Read-only metrics collection |
| META_UPDATER | Documentation updates |
| DBA | Migration generation (template-based) |
| SYNTHESIZER | Result aggregation |

### Sonnet (11 agents)
Balanced execution for tests, code, and analysis.

| Agent | Rationale |
|-------|-----------|
| QA_TESTER | Test writing and execution |
| SCHEDULER | Scheduling logic implementation |
| FRONTEND_ENGINEER | React/Next.js development |
| BACKEND_ENGINEER | FastAPI/SQLAlchemy development |
| RELEASE_MANAGER | Git operations, PR creation |
| TOOLSMITH | Tool and skill creation |
| RESILIENCE_ENGINEER | Resilience framework work |
| COMPLIANCE_AUDITOR | ACGME compliance checking |
| BURNOUT_SENTINEL | Burnout detection analysis |
| CAPACITY_OPTIMIZER | Capacity planning |
| EPIDEMIC_ANALYST | SIR model analysis |

### Opus (10 agents)
Complex reasoning, architecture, and coordination.

| Agent | Rationale |
|-------|-----------|
| ORCHESTRATOR | Multi-agent coordination |
| ARCHITECT | System design decisions |
| AGENT_FACTORY | Creating new agents |
| OPTIMIZATION_SPECIALIST | Complex optimization |
| COORD_ENGINE | Scheduling domain coordination |
| COORD_FRONTEND | Frontend domain coordination |
| COORD_OPS | Operations domain coordination |
| COORD_PLATFORM | Platform domain coordination |
| COORD_QUALITY | Quality domain coordination |
| COORD_RESILIENCE | Safety domain coordination |

---

## Files

### Models
- `backend/app/models/agent_memory.py` - SQLAlchemy models

### Services
- `backend/app/services/embedding_service.py` - Embedding generation

### Migration
- `backend/alembic/versions/20251227_add_pgvector_agent_memory.py`

### Agent Specs
All agent specifications in `.claude/Agents/*.md` include:
```markdown
> **Model Tier:** haiku | sonnet | opus
```

---

## Usage

### Spawning with Explicit Model

```python
# In Task tool invocation
{
    "subagent_type": "general-purpose",
    "model": "haiku",  # Explicit model selection
    "prompt": "Update the README file"
}
```

### Querying Similar Tasks

```sql
-- Find 5 most similar successful tasks
SELECT
    task_description,
    agent_used,
    model_used,
    1 - (embedding <=> $query_embedding) as similarity
FROM task_history
WHERE success = true
ORDER BY embedding <=> $query_embedding
LIMIT 5;
```

### Model Recommendation Logic

```python
def recommend_model(similar_tasks: list) -> str:
    """
    Given similar successful tasks, recommend cheapest
    model that reliably handles this type of work.
    """
    MODEL_COST = {"haiku": 1, "sonnet": 10, "opus": 100}

    model_scores = defaultdict(float)
    for task in similar_tasks:
        weight = task.similarity * (1.0 if task.success else 0.3)
        model_scores[task.model_used] += weight

    # Prefer cheaper models when scores are close
    best_model = None
    best_value = 0

    for model, score in model_scores.items():
        value = score / MODEL_COST[model]
        if value > best_value:
            best_value = value
            best_model = model

    return best_model or "sonnet"
```

---

## Dependencies

```
# backend/requirements.txt
pgvector>=0.3.0              # PostgreSQL vector operations
sentence-transformers>=2.2.0  # Local embeddings (all-MiniLM-L6-v2)
```

### Docker Image

```yaml
# docker-compose.yml
db:
  image: pgvector/pgvector:0.8.1-pg15
```

---

## Verification

### Check pgvector Extension

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Test Embedding Service

```python
from app.services.embedding_service import EmbeddingService

embedding = EmbeddingService.embed_text("write pytest tests")
assert len(embedding) == 384
```

### Test Similarity Query

```python
# Insert test embedding
await db.execute("""
    INSERT INTO task_history
    (task_description, embedding, agent_used, model_used, success)
    VALUES ('test task', $1, 'QA_TESTER', 'sonnet', true)
""", [test_embedding])

# Query similar
results = await query_similar_tasks(test_embedding, limit=1)
assert results[0].similarity > 0.99
```

---

## Future Enhancements

1. **Task History Instrumentation** - Automatically record all Task tool invocations
2. **Pre-Plan Hook Integration** - Query recommendations before spawning
3. **Agent Pruning** - Remove agents never matched to any task
4. **Capability Gap Detection** - Find tasks no agent handles well

---

## Related Documentation

- [Agent Skills Reference](AGENT_SKILLS.md)
- [ORCHESTRATOR Agent Spec](../../.claude/Agents/ORCHESTRATOR.md)
- [Parallel Claude Best Practices](PARALLEL_CLAUDE_BEST_PRACTICES.md)
- [Cross-Disciplinary Resilience](../architecture/cross-disciplinary-resilience.md)

---

*Last Updated: 2025-12-29*
*Maintained By: ORCHESTRATOR*
