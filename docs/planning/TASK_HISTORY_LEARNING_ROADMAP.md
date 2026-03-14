# Task History Learning System Roadmap

> **Created:** 2026-03-12 | **Status:** Phases 1-6 Complete (MVP + Skill) | **Author:** Antigravity (Opus 4.6)
>
> **Problem:** The `task_history` table (pgvector-indexed, Dec 2025) is fully functional but completely dormant. No agent writes to it, no agent reads from it. The PAI² design described a feedback loop and episodic memory layer that were never implemented.
>
> **Real-world cost:** On 2026-03-12, an agent wrote `HalfDayAssignment.is_deleted` — a column that doesn't exist. If a prior agent's failure had been logged with "HDA has no is_deleted column", vector similarity search would have surfaced that lesson before the bug shipped.

---

## Current State

### What Exists

| Component | File | Status |
|-----------|------|--------|
| `TaskHistory` model | `backend/app/models/agent_memory.py:65-89` | Schema deployed, 0 rows |
| `AgentEmbedding` model | `backend/app/models/agent_memory.py:36-62` | Schema deployed, 0 rows |
| `ModelTier` model | `backend/app/models/agent_memory.py:13-33` | Schema deployed, 0 rows |
| pgvector extension | Migration `20251227_pgvector` | Enabled, HNSW index created |
| `JobHistoryService` | `backend/app/services/job_monitor/job_history.py` | Celery job monitor — **NOT** agent learning |
| RAG pipeline (reference pattern) | `rag_service.py`, `rag.py` routes, `api_client.py` | Fully operational, 67+ docs |

### What's Missing

1. **No write path** — No MCP tool, API route, or service writes to `task_history`
2. **No read path** — No MCP tool queries `task_history` for lessons learned
3. **No lesson text** — Schema has `success: bool` but no field for *what was learned*
4. **No tags/files** — Can't filter by domain area or files involved
5. **No recall skill** — Agents can't query episodic memory before starting work

---

## Architecture

### Write Path (follows RAG pattern exactly)

```
Agent completes task
    ↓
MCP tool: log_task_tool()
    ↓
API client: api_client.log_task_history()
    ↓  POST /api/v1/task-history/
FastAPI route: create_task_entry()
    ↓
TaskHistoryService.log()
    ↓  embed(task_description) → Vector[384]
PostgreSQL: task_history row + HNSW index
```

### Read Path

```
Agent starts task
    ↓
MCP tool: query_similar_tasks_tool(description)
    ↓
API client: api_client.query_task_history()
    ↓  POST /api/v1/task-history/search
FastAPI route: search_similar_tasks()
    ↓
TaskHistoryService.search_similar()
    ↓  pgvector cosine similarity on embedding
Returns: similar past tasks with notes, success/failure, lessons
```

### Reference Implementation

The RAG pipeline (`rag_service.py` → `rag.py` routes → `api_client.py:913-1038` → `server.py:5138-5300`) is the canonical pattern. Every layer maps 1:1:

| RAG Layer | Task History Equivalent |
|-----------|------------------------|
| `RAGDocument` model | `TaskHistory` model (extended) |
| `rag_service.py` → `RAGService` | `task_history_service.py` → `TaskHistoryService` |
| `schemas/rag.py` | `schemas/task_history.py` |
| `api/routes/rag.py` | `api/routes/task_history.py` |
| `api_client.py` → `rag_retrieve()` | `api_client.py` → `query_task_history()` |
| `server.py` → `rag_search()` | `server.py` → `query_similar_tasks_tool()` |

---

## Phases

### Phase 1: Schema Extension (Migration)

**Goal:** Add lesson-carrying fields to `task_history`.

**New columns:**

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| `notes` | `Text` | Yes | Free-text lesson learned ("HDA has no is_deleted column") |
| `failure_reason` | `Text` | Yes | Structured failure category (schema_error, import_error, constraint_violation) |
| `tags` | `ARRAY(String)` | Yes | Domain tags: `["scheduling", "hda", "constraints"]` |
| `files_touched` | `ARRAY(String)` | Yes | Files involved: `["backend/app/scheduling/engine.py"]` |

**Files:**

| File | Action |
|------|--------|
| `backend/alembic/versions/YYYYMMDD_task_hist_notes.py` | New migration: ADD COLUMN ×4 |
| `backend/app/models/agent_memory.py` | Add 4 fields to `TaskHistory` class |

**Dependencies:** None. Pure additive schema change.

**Migration name:** `20260313_task_hist_notes` (under 64-char limit).

**Notes:**
- All new columns are nullable — no backfill needed, no breaking change
- PG arrays (`ARRAY(String)`) support GIN indexing for tag queries later
- `failure_reason` is intentionally free-text, not an enum — agents discover failure categories organically

---

### Phase 2: Service Layer

**Goal:** `TaskHistoryService` with embed-on-write and similarity search.

**Class:** `TaskHistoryService`

**Methods:**

```python
class TaskHistoryService:
    async def log(
        self,
        task_description: str,
        agent_used: str,
        model_used: str,
        success: bool,
        duration_ms: int | None = None,
        session_id: str | None = None,
        notes: str | None = None,
        failure_reason: str | None = None,
        tags: list[str] | None = None,
        files_touched: list[str] | None = None,
    ) -> TaskHistory:
        """Log a task execution. Embeds task_description via sentence-transformers."""

    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        success_filter: bool | None = None,
        tags_filter: list[str] | None = None,
        min_similarity: float = 0.5,
    ) -> list[dict]:
        """Vector similarity search over past tasks. Returns tasks with similarity scores."""

    async def get_lessons_for_files(
        self,
        file_paths: list[str],
        limit: int = 10,
    ) -> list[dict]:
        """Find past failures involving specific files."""

    async def get_session_history(
        self,
        session_id: str,
    ) -> list[TaskHistory]:
        """Retrieve all tasks from a session (episodic memory)."""
```

**Files:**

| File | Action |
|------|--------|
| `backend/app/services/task_history_service.py` | New file: `TaskHistoryService` class |
| `backend/app/schemas/task_history.py` | New file: request/response Pydantic schemas |

**Dependencies:** Phase 1 (schema must exist).

**Implementation notes:**
- Reuse the same embedding model as RAG (`sentence-transformers/all-MiniLM-L6-v2`, 384 dims)
- Embedding generation should be synchronous on write (tasks are small text, <100ms)
- `search_similar` uses `TaskHistory.embedding <=> query_embedding` (pgvector cosine distance)
- `get_lessons_for_files` uses PG array overlap: `files_touched && ARRAY[...]`

---

### Phase 3: API Endpoints

**Goal:** Two FastAPI routes exposing the service.

**Endpoints:**

| Method | Path | Handler | Purpose |
|--------|------|---------|---------|
| `POST` | `/api/v1/task-history/` | `create_task_entry()` | Log a task execution |
| `POST` | `/api/v1/task-history/search` | `search_similar_tasks()` | Vector similarity search |
| `GET` | `/api/v1/task-history/session/{session_id}` | `get_session_tasks()` | Episodic recall by session |
| `GET` | `/api/v1/task-history/files` | `get_file_lessons()` | Lessons for specific files (query param) |

**Files:**

| File | Action |
|------|--------|
| `backend/app/api/routes/task_history.py` | New file: 4 route handlers |
| `backend/app/api/routes/__init__.py` | Register router |

**Dependencies:** Phase 2 (service must exist).

**Auth:** All endpoints require valid JWT. No special role — any authenticated agent/user can read/write.

---

### Phase 4: API Client Methods

**Goal:** MCP server can call the backend.

**Methods to add to `SchedulerAPIClient`:**

```python
async def log_task_history(self, payload: dict) -> dict:
    """POST /api/v1/task-history/"""

async def query_task_history(self, payload: dict) -> dict:
    """POST /api/v1/task-history/search"""

async def get_session_history(self, session_id: str) -> dict:
    """GET /api/v1/task-history/session/{session_id}"""

async def get_file_lessons(self, file_paths: list[str]) -> dict:
    """GET /api/v1/task-history/files?paths=..."""
```

**Files:**

| File | Action |
|------|--------|
| `mcp-server/src/scheduler_mcp/api_client.py` | Add 4 methods (follow `rag_retrieve` pattern) |

**Dependencies:** Phase 3 (API routes must exist).

---

### Phase 5: MCP Tools (MVP Complete)

**Goal:** Two MCP tools that agents can call directly.

**Tools:**

#### `log_task_tool`

```python
@mcp.tool()
async def log_task_tool(
    task_description: str,
    agent_used: str,
    model_used: str,     # haiku | sonnet | opus
    success: bool,
    duration_ms: int | None = None,
    session_id: str | None = None,
    notes: str | None = None,
    failure_reason: str | None = None,
    tags: list[str] | None = None,
    files_touched: list[str] | None = None,
) -> dict:
    """Log a completed task for the learning system.

    Call this after completing (or failing) any significant task.
    The system embeds the description for future similarity search.

    Example:
        log_task_tool(
            task_description="Add is_deleted filter to HalfDayAssignment query",
            agent_used="scheduling-agent",
            model_used="opus",
            success=False,
            failure_reason="schema_error",
            notes="HalfDayAssignment has no is_deleted column. Only Person and RotationTemplate have soft deletes.",
            tags=["scheduling", "hda", "schema"],
            files_touched=["backend/app/scheduling/engine.py"]
        )
    """
```

#### `query_similar_tasks_tool`

```python
@mcp.tool()
async def query_similar_tasks_tool(
    query: str,
    top_k: int = 5,
    success_filter: bool | None = None,
    tags_filter: list[str] | None = None,
    min_similarity: float = 0.5,
) -> dict:
    """Search past task history for similar work.

    Call this BEFORE starting a task to see if prior agents encountered
    relevant issues. Returns similar tasks with lessons learned.

    Example:
        query_similar_tasks_tool(
            query="modify HalfDayAssignment query with is_deleted filter",
            success_filter=False,  # show me what went wrong
            tags_filter=["hda"]
        )
        # Returns: "HDA has no is_deleted column" lesson from prior failure
    """
```

**Files:**

| File | Action |
|------|--------|
| `mcp-server/src/scheduler_mcp/server.py` | Add 2 tool functions |

**Dependencies:** Phase 4 (API client methods must exist).

**This completes the MVP.** After Phase 5, agents can log tasks and query for similar past work.

---

### Phase 6: `/recall` Skill

**Goal:** Agents can invoke `/recall` before starting work to surface relevant lessons.

**Behavior:**

```
User: /recall "scheduling engine changes"

→ Queries task_history via query_similar_tasks_tool
→ Formats results as actionable warnings:

  ⚠️ 3 relevant lessons from past tasks:

  1. [FAILURE] "Add is_deleted filter to HDA query" (2026-03-12)
     Lesson: HalfDayAssignment has no is_deleted column.
     Files: engine.py

  2. [SUCCESS] "Add block_half filter to HDA query" (2026-03-08)
     Duration: 450ms
     Files: engine.py, sync_preload_service.py

  3. [FAILURE] "Import HalfDayAssignment in engine" (2026-03-10)
     Lesson: HDA import was already present via models/__init__.py
     Files: engine.py
```

**Files:**

| File | Action |
|------|--------|
| `.claude/skills/recall.md` | New skill definition |

**Dependencies:** Phase 5 (MCP tools must exist).

**Design notes:**
- This is NOT a new table. It queries `task_history` grouped by `session_id` for episodic context.
- The skill is a convenience wrapper — agents can also call `query_similar_tasks_tool` directly.
- Skill is local-only (gitignored per existing pattern).

---

### Phase 7: Automatic Logging Hooks (Future)

**Goal:** Remove the manual "call `log_task_tool`" step. Tasks are logged automatically.

**Options (evaluate after 100+ manual entries):**

1. **Claude Code hooks** — `postToolCall` hook triggers `log_task_tool` after significant operations (file edits, test runs)
2. **MCP middleware** — Wrapper around tool dispatch that logs tool call + result
3. **Session-end summary** — At conversation end, summarize all work as a single task_history entry

**Dependencies:** Phase 5 + meaningful data (100+ entries to validate schema design).

**Why deferred:** Automatic logging risks noise. Manual logging for the first 100 entries ensures the schema, tags, and notes fields capture genuinely useful signal before automating.

---

### Phase: Deferred — `agent_embeddings` & `model_tiers`

**Tables exist but are designed for PAI v1 (55 agent specs, identity cards).** With PAI v2 (Opus 4.6 + Agent Teams), the agent landscape has changed.

**Prerequisite:** 100+ `task_history` entries with agent/model data. Then:
- Analyze which model tiers actually perform best per task type
- Populate `model_tiers` based on empirical data, not theoretical assignment
- `agent_embeddings` may be repurposed for skill-based routing if Agent Teams grows

**Do not build until the data justifies it.**

---

## Dependency Graph

```
Phase 1 (Schema)
    ↓
Phase 2 (Service)
    ↓
Phase 3 (API Routes)
    ↓
Phase 4 (API Client)
    ↓
Phase 5 (MCP Tools) ← MVP COMPLETE
    ↓
Phase 6 (/recall Skill)
    ↓
Phase 7 (Auto-logging Hooks) ← requires 100+ entries
```

Phases 1-5 are strictly sequential. Phase 6 is independent once Phase 5 lands. Phase 7 is gated on data volume.

---

## File Manifest

All files created or modified across all phases:

| Phase | File | Action |
|-------|------|--------|
| 1 | `backend/alembic/versions/YYYYMMDD_task_hist_notes.py` | New migration |
| 1 | `backend/app/models/agent_memory.py` | Modify: add 4 columns |
| 2 | `backend/app/services/task_history_service.py` | New: service class |
| 2 | `backend/app/schemas/task_history.py` | New: Pydantic schemas |
| 3 | `backend/app/api/routes/task_history.py` | New: 4 route handlers |
| 3 | `backend/app/api/routes/__init__.py` | Modify: register router |
| 4 | `mcp-server/src/scheduler_mcp/api_client.py` | Modify: add 4 methods |
| 5 | `mcp-server/src/scheduler_mcp/server.py` | Modify: add 2 tools |
| 6 | `.claude/skills/recall.md` | New: skill definition |

**Total:** 5 new files, 4 modified files.

---

## Success Criteria

| Milestone | Metric |
|-----------|--------|
| MVP (Phase 5) | Agent can log a task and query similar tasks via MCP tools |
| First lesson surfaced | `query_similar_tasks_tool` returns a prior failure that prevents a repeat mistake |
| Episodic recall | `/recall "topic"` returns grouped session history with actionable warnings |
| Data threshold | 100+ entries with meaningful notes and tags |
| Auto-logging | Hooks write entries without manual agent invocation |

---

## Anti-Requirements

Things this system is explicitly **NOT**:

1. **Not a job monitor** — `JobHistoryService` tracks Celery task status. This tracks *agent learning*.
2. **Not a new table for episodic memory** — Episodic memory is `task_history` filtered by `session_id`.
3. **Not an agent router** — `model_tiers` / `agent_embeddings` are deferred. This is a learning journal, not a dispatch system.
4. **Not a replacement for RAG** — RAG stores curated documentation. Task history stores empirical outcomes. They complement each other.
5. **Not automated yet** — Manual logging first, automation after data validates the schema.
