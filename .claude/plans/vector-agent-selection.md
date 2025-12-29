# Plan: Vector-Based Agent Model Selection

> **Status:** Draft
> **Created:** 2025-12-29
> **Author:** ORCHESTRATOR
> **Branch:** `claude/parallel-agent-models-c3ZpR`

---

## Problem Statement

When ORCHESTRATOR spawns agents, it currently:
1. **Doesn't specify model** - All agents inherit Opus (parent model), wasting resources on simple tasks
2. **Has no memory** - Same task types get re-analyzed every session
3. **No historical learning** - Can't learn which (task, agent, model) combos work best

**Concrete Example from Previous Session:**

| Agent | Task | Model Used | Should Have Been |
|-------|------|------------|------------------|
| ARCHITECT | Add 2 deps, fix imports | Opus (inherited) | Haiku |
| QA_TESTER | Write game_theory tests | Opus (inherited) | Sonnet |
| QA_TESTER | Write kalman tests | Opus (inherited) | Sonnet |
| QA_TESTER | Write ecological tests | Opus (inherited) | Sonnet |

**Cost/Latency Impact:** Haiku is ~10x cheaper and ~3x faster than Opus for simple tasks.

---

## Proposed Solution: pgvector + Embeddings

### Why pgvector?
- Postgres 15 already running in docker-compose
- Single `CREATE EXTENSION vector;` to enable
- No new infrastructure or dependencies
- Already have DBA agent for migrations

### Architecture Overview

```
                    ┌─────────────────────────────────────────┐
                    │        ORCHESTRATOR                      │
                    │                                          │
                    │  1. Receive task description            │
                    │  2. Embed task → vector                  │
                    │  3. Query similar historical tasks       │
                    │  4. Get recommended (agent, model)       │
                    │  5. Spawn with explicit model param      │
                    └──────────────┬───────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────────┐
                    │      PostgreSQL + pgvector              │
                    │                                          │
                    │  ┌─────────────────────────────────┐    │
                    │  │  agent_embeddings               │    │
                    │  │  - agent_id, spec_embedding     │    │
                    │  └─────────────────────────────────┘    │
                    │                                          │
                    │  ┌─────────────────────────────────┐    │
                    │  │  task_history                   │    │
                    │  │  - task_desc, task_embedding    │    │
                    │  │  - agent_used, model_used       │    │
                    │  │  - success, duration_ms         │    │
                    │  └─────────────────────────────────┘    │
                    │                                          │
                    │  ┌─────────────────────────────────┐    │
                    │  │  model_tiers (lookup table)     │    │
                    │  │  - agent_id, default_model      │    │
                    │  └─────────────────────────────────┘    │
                    └─────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Foundation (This Session)

**Goal:** Get pgvector installed and basic schema created.

#### Step 1.1: Enable pgvector Extension

```sql
-- Run in PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;
```

**Verification:**
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

#### Step 1.2: Create Alembic Migration

Create migration for:
```python
# model_tiers table - Static lookup for default model assignments
class ModelTier(Base):
    __tablename__ = "model_tiers"

    agent_name = Column(String, primary_key=True)  # e.g., "QA_TESTER"
    default_model = Column(String, nullable=False)  # "haiku", "sonnet", "opus"
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    notes = Column(Text, nullable=True)  # Why this model?

# task_history table - Learning from past spawns
class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now())

    # Task info
    task_description = Column(Text, nullable=False)
    task_embedding = Column(Vector(1536), nullable=True)  # OpenAI ada-002 dimension

    # Execution info
    agent_used = Column(String, nullable=False)
    model_used = Column(String, nullable=False)  # "haiku", "sonnet", "opus"

    # Outcome
    success = Column(Boolean, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Context
    session_id = Column(String, nullable=True)
    parent_task_id = Column(UUID, ForeignKey("task_history.id"), nullable=True)

# agent_embeddings table - Pre-computed embeddings of agent specs
class AgentEmbedding(Base):
    __tablename__ = "agent_embeddings"

    agent_name = Column(String, primary_key=True)
    spec_embedding = Column(Vector(1536), nullable=False)
    spec_hash = Column(String, nullable=False)  # SHA256 of spec content
    updated_at = Column(DateTime, server_default=func.now())
```

#### Step 1.3: Seed Model Tiers

Initial tier assignments based on task complexity analysis:

| Tier | Model | Agents | Rationale |
|------|-------|--------|-----------|
| Fast | Haiku | DELEGATION_AUDITOR, META_UPDATER, DBA, SYNTHESIZER | Simple tasks, low reasoning |
| Balanced | Sonnet | QA_TESTER, SCHEDULER, FRONTEND_ENGINEER, BACKEND_ENGINEER, RELEASE_MANAGER, TOOLSMITH, RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, BURNOUT_SENTINEL, CAPACITY_OPTIMIZER, EPIDEMIC_ANALYST | Most work - tests, code, analysis |
| Complex | Opus | ORCHESTRATOR, ARCHITECT, COORD_*, OPTIMIZATION_SPECIALIST | Architecture, coordination, multi-agent synthesis |

### Phase 2: Embedding Infrastructure (Next Session)

**Goal:** Generate and store embeddings.

#### Step 2.1: Embedding Provider Selection

Options:
1. **Anthropic Embeddings API** (if available) - Ideal, same provider
2. **OpenAI ada-002** - Well-tested, 1536 dimensions
3. **Sentence Transformers** (local) - No API calls, but requires model download

**Decision:** Use OpenAI ada-002 initially (widely available, well-documented).
Can swap to Anthropic later if they release embeddings.

#### Step 2.2: Embed All Agent Specs

```python
async def embed_agent_specs():
    """Embed all agent specification files."""
    for agent_file in glob(".claude/Agents/*.md"):
        spec_content = read_file(agent_file)
        agent_name = agent_file.stem  # e.g., "QA_TESTER"

        embedding = await generate_embedding(spec_content)
        spec_hash = hashlib.sha256(spec_content.encode()).hexdigest()

        upsert_agent_embedding(agent_name, embedding, spec_hash)
```

#### Step 2.3: Task Embedding on Spawn

When ORCHESTRATOR spawns an agent:
```python
async def spawn_with_learning(task_description: str) -> Agent:
    # 1. Embed the task
    task_embedding = await generate_embedding(task_description)

    # 2. Find similar historical tasks
    similar_tasks = await query_similar_tasks(task_embedding, limit=5)

    # 3. Determine best model
    if similar_tasks:
        # Use historical success data
        model = recommend_model(similar_tasks)
        agent = recommend_agent(similar_tasks)
    else:
        # Fall back to tier lookup
        model = get_default_model(agent)

    # 4. Spawn with explicit model
    result = spawn_agent(agent, task_description, model=model)

    # 5. Record for future learning
    record_task_history(
        task_description=task_description,
        task_embedding=task_embedding,
        agent_used=agent,
        model_used=model,
        success=result.success,
        duration_ms=result.duration_ms
    )

    return result
```

### Phase 3: Retrieval & Matching (Future Session)

**Goal:** Intelligent model selection based on similarity.

#### Step 3.1: Similarity Query

```sql
-- Find 5 most similar past tasks
SELECT
    task_description,
    agent_used,
    model_used,
    success,
    duration_ms,
    1 - (task_embedding <=> $1) as similarity
FROM task_history
WHERE success = true  -- Only learn from successes
ORDER BY task_embedding <=> $1  -- Cosine distance
LIMIT 5;
```

#### Step 3.2: Model Recommendation Logic

```python
def recommend_model(similar_tasks: list[TaskHistory]) -> str:
    """
    Given similar successful tasks, recommend the cheapest model
    that reliably handles this type of work.
    """
    # Group by model, weighted by similarity
    model_scores = defaultdict(float)
    for task in similar_tasks:
        weight = task.similarity * (1.0 if task.success else 0.3)
        model_scores[task.model_used] += weight

    # Prefer cheaper models when scores are close
    MODEL_COST = {"haiku": 1, "sonnet": 10, "opus": 100}

    best_model = None
    best_value = 0

    for model, score in model_scores.items():
        value = score / MODEL_COST[model]  # Score per dollar
        if value > best_value:
            best_value = value
            best_model = model

    return best_model or "sonnet"  # Default to balanced
```

### Phase 4: Agent Pruning & Evolution (Future)

**Goal:** Remove unused agents, split overloaded ones.

#### Step 4.1: Usage Analytics

```sql
-- Find agents never used in past 30 days
SELECT m.agent_name
FROM model_tiers m
LEFT JOIN task_history t
    ON m.agent_name = t.agent_used
    AND t.created_at > NOW() - INTERVAL '30 days'
WHERE t.id IS NULL;

-- Find overloaded agents (high task volume, mixed success)
SELECT
    agent_used,
    COUNT(*) as task_count,
    AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate,
    AVG(duration_ms) as avg_duration
FROM task_history
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY agent_used
HAVING COUNT(*) > 50 AND AVG(CASE WHEN success THEN 1 ELSE 0 END) < 0.8;
```

#### Step 4.2: Capability Gap Detection

```python
def find_capability_gaps():
    """
    Find task embeddings that are far from all agent embeddings.
    These represent tasks no agent is well-suited for.
    """
    orphan_tasks = query("""
        SELECT t.task_description, MIN(t.task_embedding <=> a.spec_embedding) as min_distance
        FROM task_history t
        CROSS JOIN agent_embeddings a
        WHERE t.success = false
        GROUP BY t.id
        HAVING MIN(t.task_embedding <=> a.spec_embedding) > 0.5  -- Threshold
        ORDER BY min_distance DESC
        LIMIT 10;
    """)

    return orphan_tasks  # Consider creating new agents for these
```

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `backend/app/models/agent_learning.py` | SQLAlchemy models for vector tables |
| `backend/alembic/versions/XXX_add_pgvector_tables.py` | Migration |
| `backend/app/services/embedding_service.py` | Embedding generation |
| `backend/app/services/agent_recommender.py` | Model recommendation logic |
| `.claude/skills/agent-model-selector.md` | Skill for ORCHESTRATOR to invoke |

### Modified Files

| File | Change |
|------|--------|
| `docker-compose.yml` | Ensure postgres has pgvector (use `pgvector/pgvector:pg15` image) |
| `backend/requirements.txt` | Add `pgvector` Python package |
| `.claude/Agents/ORCHESTRATOR.md` | Document model selection capability |

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/unit/test_agent_recommender.py

def test_recommend_model_prefers_cheaper():
    """When success rates equal, prefer cheaper model."""
    similar_tasks = [
        TaskHistory(model_used="opus", success=True, similarity=0.9),
        TaskHistory(model_used="sonnet", success=True, similarity=0.9),
    ]
    assert recommend_model(similar_tasks) == "sonnet"

def test_recommend_model_weights_by_similarity():
    """Higher similarity tasks should have more influence."""
    similar_tasks = [
        TaskHistory(model_used="opus", success=True, similarity=0.95),
        TaskHistory(model_used="haiku", success=True, similarity=0.6),
    ]
    # Opus should win despite cost due to much higher similarity
    assert recommend_model(similar_tasks) == "opus"
```

### Integration Tests

```python
# backend/tests/integration/test_pgvector.py

async def test_pgvector_extension():
    """Verify pgvector is installed."""
    result = await db.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
    assert result.scalar() is not None

async def test_embedding_similarity_query():
    """Verify cosine similarity queries work."""
    # Insert test embedding
    await db.execute("""
        INSERT INTO task_history (task_description, task_embedding, agent_used, model_used, success)
        VALUES ('test task', $1, 'QA_TESTER', 'sonnet', true)
    """, [test_embedding])

    # Query similar
    results = await query_similar_tasks(test_embedding, limit=1)
    assert len(results) == 1
    assert results[0].similarity > 0.99
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| pgvector not in current Postgres image | Medium | High | Use `pgvector/pgvector:pg15` image |
| Embedding API costs add up | Low | Medium | Cache embeddings, use local model for prototype |
| Cold start (no history) | High | Low | Fall back to static tier lookup |
| Model recommendations wrong | Medium | Medium | Log all decisions, easy to audit and retrain |

---

## Success Criteria

1. **pgvector enabled** - Extension installed, tables created
2. **Static tiers working** - Default model lookup functional
3. **First embedding stored** - At least one agent spec embedded
4. **First task recorded** - At least one spawn recorded to task_history
5. **First recommendation made** - Similarity-based model selection working

---

## Immediate Next Steps (This Session)

- [ ] Check if current Postgres image supports pgvector
- [ ] If not, update docker-compose to use `pgvector/pgvector:pg15`
- [ ] Create Alembic migration for `model_tiers` table only (simplest first)
- [ ] Seed initial model tier data
- [ ] Create basic lookup function

---

## Questions for User

1. **Embedding provider:** OpenAI ada-002, or should we explore local options first?
2. **Scope:** Start with just `model_tiers` (no vectors), or go full pgvector immediately?
3. **Agent spec updates:** Should we auto-update embeddings when agent specs change?
