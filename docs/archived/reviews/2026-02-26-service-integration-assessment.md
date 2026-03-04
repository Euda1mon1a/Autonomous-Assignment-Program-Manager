# Service Integration Assessment: Pareto Optimization & Agent Matcher

> **Date:** 2026-02-26
> **Scope:** Two backend services with API routes but zero consumers
> **Related:** `docs/reviews/2026-02-26-non-scheduling-assessment.md`, `TODO.md` Batch 4

---

## Summary

Both services were wired to API routes on 2026-02-26 but have no internal consumers. This document assesses where they should integrate and whether that integration is warranted now.

---

## 1. Pareto Optimization Service

**File:** `backend/app/services/pareto_optimization_service.py` (725 LOC)
**Route:** `backend/app/api/routes/pareto.py` — `POST /pareto/optimize`, `POST /pareto/rank`
**Schemas:** `backend/app/schemas/pareto.py` (complete Pydantic)
**Tests:** 3 files (service, integration, schemas)

### What It Does

NSGA-II multi-objective optimizer via pymoo. Takes 2+ objectives (fairness, coverage, preference satisfaction, workload balance, consecutive days, specialty distribution) and constraints, returns a Pareto frontier of non-dominated solutions with hypervolume indicator.

### Integration Points

| # | Integration Point | File | Method | Value | Risk |
|---|---|---|---|---|---|
| 1 | **Scheduling engine** | `backend/app/scheduling/engine.py` | `generate()` | **High** — enables multi-solution comparison for coordinators | **High** — core solver, "Do NOT Auto-Assign" category |
| 2 | Block scheduler | `backend/app/services/block_scheduler_service.py` | `schedule_block()` | Medium — Pareto alternative to greedy assignment | Medium — secondary scheduler |
| 3 | Draft staging | `backend/app/services/schedule_draft_service.py` | `add_solver_assignments_to_draft()` | Medium — stage multiple frontier solutions as competing drafts | Low — additive, doesn't change existing drafts |

### Integration #1 Detail: Scheduling Engine

The highest-value integration is into `SchedulingEngine.generate()`. Currently the engine runs a single solver (CP-SAT, greedy, PuLP, or hybrid) and returns one solution. Pareto integration would:

1. After primary solver completes, optionally invoke `ParetoOptimizationService.optimize_schedule_pareto()` with objectives derived from the generation request
2. Return a Pareto frontier alongside the primary solution
3. Let coordinators compare trade-offs (e.g., "this schedule is fairer but has worse coverage")

**Implementation approach:** Add a `generate_alternatives: bool = False` parameter to `generate()`. When true, run Pareto after the primary solver. Feature-flagged, default off.

**Why defer:** This touches the scheduling engine — the most critical code path in AAPM. Per `TODO.md` "Do NOT Auto-Assign" rules, scheduling engine changes require human review and careful testing with real schedule data.

### Recommendation

**Keep as standalone API for now.** The route endpoint (`POST /pareto/optimize`) is immediately useful for:
- Admin exploratory optimization (run manually, inspect frontier)
- MCP tool integration (expose as a tool for AI-assisted schedule analysis)
- Testing and benchmarking solver quality

**Defer engine integration** to a dedicated sprint with human oversight.

---

## 2. Agent Matcher Service

**File:** `backend/app/services/agent_matcher.py` (346 LOC)
**Route:** `backend/app/api/routes/agent_matcher.py` — `POST /agent-matcher/match`, `POST /agent-matcher/explain`, `GET /agent-matcher/agents`
**Tests:** 1 file
**Dependencies:** `EmbeddingService` (all-MiniLM-L6-v2, 384-dim), no DB

### What It Does

Semantic matching of natural-language task descriptions to AI agent specifications. Uses cosine similarity on sentence-transformer embeddings to find the best-matching agent from `.claude/Agents/` specs. Returns agent name, archetype, similarity score, and recommended model tier.

### Integration Points

| # | Integration Point | File | Method | Value | Risk |
|---|---|---|---|---|---|
| 1 | **Claude chat routing** | `backend/app/api/routes/claude_chat.py` | message handler | **Medium** — auto-select model tier per query | **Low** — routing only, doesn't affect responses |
| 2 | Workflow dispatch | `backend/app/services/workflow_service.py` | `execute_workflow()` | Low — workflow service itself is unwired | N/A |

### Integration #1 Detail: Claude Chat Routing

The chat route currently sends all messages to a fixed Claude model. Agent Matcher could pre-classify the incoming message and select the appropriate model tier:

- "Validate ACGME compliance" → Validator archetype → Haiku (fast, cheap)
- "Design a new scheduling algorithm" → Synthesizer archetype → Opus (deep reasoning)
- "Generate next month's schedule" → Generator archetype → Sonnet (balanced)

**Why low urgency:** The current fixed-model approach works. Model tier optimization saves tokens/cost but doesn't unlock new functionality. Worth doing when multi-agent orchestration becomes a priority.

### Recommendation

**Keep as standalone API.** The route endpoints are useful for:
- Debugging agent selection ("why was this agent chosen?")
- Manual task routing queries
- Future OpenClaw integration (text-router could call this endpoint)

**Integrate into `claude_chat.py`** when multi-agent orchestration is actively being developed — it's a 20-line change but the value is marginal until there are multiple agents actually handling different task types.

---

## Cross-Reference

- **Non-scheduling assessment:** `docs/reviews/2026-02-26-non-scheduling-assessment.md`
- **Master task list:** `TODO.md` — Batch 4 (Service Integration)
- **Roadmap:** `docs/planning/ROADMAP.md`
- **MCP priority list:** `docs/planning/MCP_PRIORITY_LIST.md`
