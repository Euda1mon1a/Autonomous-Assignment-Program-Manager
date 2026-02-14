# Agent Model Selection

> **Status:** Active
> **Version:** 2.0.0
> **Last Updated:** 2026-02-05

This document describes the vector-based agent model selection system that enables ORCHESTRATOR to choose optimal Claude model tiers (haiku/sonnet/opus) when spawning subagents.

---

## Model Family: Claude 4.5/4.6 (February 2026)

| Model | Model ID | Cost (per M tokens) | Latency | Use Case |
|-------|----------|---------------------|---------|----------|
| **Haiku 4.5** | `claude-haiku-4-5-20251001` | $0.25 / $1.25 in/out | Fast | Simple tasks, metadata updates, delegation auditing |
| **Sonnet 4.5** | `claude-sonnet-4-5-20250929` | $3 / $15 in/out | Medium | Code generation, testing, analysis |
| **Opus 4.6** | `claude-opus-4-6` | $5 / $25 in/out | Slower | Architecture, coordination, multi-agent synthesis |

### New Opus 4.6 Capabilities

| Capability | Detail |
|------------|--------|
| **Agent Teams** | Native multi-agent coordination (experimental). Enable: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
| **Adaptive Thinking** | Auto-selects reasoning effort (low/medium/high/max) per prompt |
| **1M Token Context** | Beta, API Tier 4+ only. Header: `anthropic-beta: context-1m-2025-08-07` |
| **128K Output Tokens** | Doubled from 64K — longer code generation and analysis |

### Agent Teams vs PAI Hierarchy

Agent Teams are a **complement** to PAI hierarchy, not a replacement:

| Mechanism | Best For | Communication | Token Cost |
|-----------|----------|---------------|------------|
| **Task() subagents** | Focused tasks, results-only | Report back to caller | Lower |
| **Agent Teams** | Complex parallel work needing discussion | Peer-to-peer messaging | Higher |
| **PAI MCP spawn** | Governed agents with identity + audit trail | Chain of command | Medium |

**Guidance:** Use Agent Teams for research, parallel review, and competing-hypotheses debugging. Use PAI hierarchy for governed schedule operations where audit trails and ACGME compliance matter.

Without explicit model selection, all agents inherit the parent model (typically Opus), wasting resources on simple tasks.

---

## Codex Model Tiers (GPT-5.3 Family)

In addition to Claude models, the project uses OpenAI Codex for automated background work and interactive coding.

| Model | Model ID | Speed | Context | Best For |
|-------|----------|-------|---------|----------|
| **5.3-Codex** | `gpt-5.3-codex` | Standard | 192K | Nightly automations, multi-file tasks, deep analysis |
| **5.3-Codex-Spark** | `gpt-5.3-codex-spark` | 1000+ tok/s | 128K | Interactive pairing, quick single-file fixes, real-time iteration |

### Spark vs Regular Codex

**Spark** (released Feb 12, 2026) runs on Cerebras WSE-3 hardware for near-instant response. It trades some capability for speed — more capable than GPT-5.1-Codex-mini but smaller than full 5.3-Codex. Research preview for ChatGPT Pro subscribers.

**When to use Spark:**
- Interactive pairing sessions where sub-second response matters
- Quick single-file fixes (typos, `from e` chaining, import cleanup)
- Guardrail compliance checks on small changesets
- Rapid prototyping and UI iteration

**When to use regular 5.3-Codex:**
- All 15 nightly automations (need full capability, not speed)
- Multi-file refactors (>5 files)
- Tasks touching scheduling, ACGME compliance, or resilience
- PR-level code reviews requiring deep reasoning

**CLI usage:** `codex --model gpt-5.3-codex-spark` or `/model` mid-session. Default remains `gpt-5.3-codex` for automations.

---

## Kimi K2.5 (Moonshot AI)

Open-source MoE model (1T total params, 32B active) with a unique Agent Swarm capability.

| Model | Model ID | Speed | Context | SWE-Bench | Cost (per M tokens) |
|-------|----------|-------|---------|-----------|---------------------|
| **K2.5** | `kimi-k2.5` | Variable | ~128K | 76.8% | $0.60 / $2.50 in/out |

**CLI Tool:** Kimi Code — terminal agent with VSCode/Cursor/Zed integration.

**Four modes:**
- **Instant** — fast responses (3-8s)
- **Thinking** — chain-of-thought reasoning
- **Agent** — 200-300 sequential tool calls without drift
- **Agent Swarm** — up to 100 parallel sub-agents, 1,500 tool calls, 4.5x speedup

**Unique capability:** Vision-grounded coding — generates code from UI mockups and video walkthroughs. Native multimodal (15T visual+text pretraining).

**Best for:** Massive parallelism at low cost (Agent Swarm), vision-to-code from Figma/mockups, budget-friendly exploration tasks.

**Caution:** Chinese company — data sovereignty consideration for military medical data. No established instruction file convention. Not battle-tested in this project's CI/CD workflows.

---

## Gemini CLI (Google)

Google's open-source terminal agent with the largest context window available (1M tokens). MCP-compatible.

| Model | Model ID | Speed | Context | SWE-Bench | Access |
|-------|----------|-------|---------|-----------|--------|
| **Gemini 3 Pro** | `gemini-3-pro` | Medium | **1M** | <78% | AI Ultra subscription |
| **Gemini 3 Flash** | `gemini-3-flash` | Fast (3x Pro) | **1M** | **78%** | Free tier or AI Ultra |

**Install:** `brew install gemini-cli` or `npm install -g @google/gemini-cli`

**Instruction file:** `GEMINI.md` (repo root) — analogous to `CLAUDE.md` and `AGENTS.md`.

**Key features:**
- 1M token context window — largest free context available
- Built-in Google Search grounding for research
- MCP support for custom tools (can connect to residency-scheduler MCP)
- Conversation checkpointing (save/resume sessions)
- Non-interactive mode with JSON output for scripting
- Free tier: 60 req/min, 1,000 req/day with Google login

**Gemini 3 Flash vs Pro:** Flash is 3x faster at 1/4 the cost and scores *higher* on SWE-bench (78% vs Pro). Use Pro for complex reasoning; Flash for everything else.

**Best for:** Whole-codebase analysis (1M context), research with Google Search grounding, high-frequency CLI work (Flash), budget-conscious daily use.

---

## Full Roster — Cross-System Model Comparison

| System | Model | Speed | Context | SWE-Bench | Cost | Best For |
|--------|-------|-------|---------|-----------|------|----------|
| Claude Code | Opus 4.6 | Medium | 200K (1M beta) | — | $$$ | Orchestration, architecture, complex reasoning |
| Claude Code | Sonnet 4.5 | Fast | 200K | — | $$ | Code gen, reviews, tactical work |
| Claude Code | Haiku 4.5 | Fastest | 200K | — | $ | Simple execution, lookups |
| Codex CLI | 5.3-Codex | Standard | 192K | — | Pro sub | Nightly automations, multi-file tasks |
| Codex CLI | 5.3-Spark | 1000+ tok/s | 128K | — | Pro sub | Interactive pairing, quick fixes |
| Kimi Code | K2.5 | Variable | ~128K | 76.8% | $0.60/$2.50 | Agent swarm, vision-to-code |
| Gemini CLI | 3 Pro | Medium | **1M** | <78% | Ultra sub | Whole-codebase analysis, research |
| Gemini CLI | 3 Flash | Fast | **1M** | **78%** | Free/Ultra | High-frequency CLI, rapid iteration |

### Instruction File Discovery

Each CLI reads a different startup file. All must contain project guardrails.

| System | Startup File | Fallback Config |
|--------|-------------|-----------------|
| Claude Code | `CLAUDE.md` | `.claude/` project settings |
| Codex CLI | `AGENTS.md` | `project_doc_fallback_filenames` in `.codex/config.toml` |
| Gemini CLI | `GEMINI.md` | — |
| Kimi Code | TBD (not yet standardized) | — |

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
All agent specifications in `.claude/archive/agents/*.md` *(Archived in PAI v1)* include:
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
- [ORCHESTRATOR Agent Spec](../../.claude/archive/agents/ORCHESTRATOR.md) *(Archived in PAI v1)*
- [Parallel Claude Best Practices](PARALLEL_CLAUDE_BEST_PRACTICES.md)
- [Cross-Disciplinary Resilience](../architecture/cross-disciplinary-resilience.md)

---

*Last Updated: 2026-02-05*
*Maintained By: ORCHESTRATOR*
