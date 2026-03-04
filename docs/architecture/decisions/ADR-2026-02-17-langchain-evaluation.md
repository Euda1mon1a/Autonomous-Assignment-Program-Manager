# ADR: LangChain Framework Evaluation

**Date:** 2026-02-17
**Updated:** 2026-02-18
**Status:** ACCEPTED (incremental, AAPM only)
**Context:** Evaluated whether LangChain should be incorporated into the project or personal assistant stack.

---

## Context

LangChain is an open-source LLM orchestration framework (Python/JS) providing chains, agents, memory, RAG, and tool-calling abstractions. Evaluated for two potential use cases:
1. **Personal assistant stack** (OpenClaw/text-router on Mac Mini)
2. **AAPM scheduling agent** (multi-step constraint solving with RAG)

## Decision

**Adopt incrementally for AAPM scheduling agent.** Skip for personal assistant stack.

The existing codebase maps more closely to LangChain/LangGraph patterns than initially assessed. The primary value is moving agent orchestration from non-Python artifacts (YAML skills, markdown system prompts, experimental agent teams) into testable, portable `.py` files.

---

## Charitable Risk/Benefit Analysis

### What Already Maps 1:1

The codebase is structurally closer to LangChain than the original evaluation gave credit for:

| Current Pattern | LangChain Equivalent | Migration Effort |
|----------------|---------------------|-----------------|
| `mcp-server/tools/base.py` BaseTool (name, description, execute) | `langchain_core.tools.BaseTool` | Near-identical. Thin adapter. |
| `SchedulingEngine.generate()` phases 0-7 | LangGraph StateGraph nodes | Each phase becomes a node. State = SchedulingContext. |
| `ConstraintManager` + `ACGMEValidator` | LangGraph conditional edges | Validation failures route back to solver node. |
| MCP tool categories (schedule, compliance, swap, resilience) | LangChain ToolKits | Already organized this way. |
| RAG via MCP (67+ docs) | LangChain retrievers | Could keep MCP RAG or migrate. |
| `.claude/skills/` YAML definitions | LangGraph agent nodes | Python functions instead of YAML. |

### Benefits

| Benefit | Relevance to AAPM | Relevance to PA Stack |
|---------|-------------------|----------------------|
| **Python-native orchestration** — testable, lintable, portable agent logic | **Critical** (current orchestration in YAML/markdown) | N/A |
| **Model-agnostic interfaces** — swap LLM providers with minimal code | **High** (running 5+ model families; Codex-CLAUDE.md incident) | Low |
| **Structured agent loops** — ReAct, plan-and-execute, tool-calling patterns | High (scheduling solver multi-step reasoning) | Low |
| **LangGraph** — state machine orchestration with checkpointing | **High** (solver timeout recovery, phase resumption) | Low |
| **LangSmith/Langfuse** — observability, tracing, evaluation | High (40+ resilience modules need unified tracing) | Low |
| **RAG abstractions** — vector store integrations, retrieval chains | Medium (already have RAG via MCP, 67+ docs) | Low |
| **Community ecosystem** — 700+ integrations, extensive docs | Medium | Low |

### Risks

| Risk | Severity | Why It's Manageable |
|------|----------|-------------------|
| **Latency overhead** — 2-5s per agent step | Low for AAPM | Scheduling is batch work (`timeout_seconds=60`). Irrelevant. |
| **Dependency bloat** — langchain-core, langgraph, etc. | Medium | Use only `langchain-core` + `langgraph`. Skip `langchain-community`. |
| **Abstraction opacity** — logic in chains/callbacks | Medium | LangSmith/Langfuse tracing. Current MCP chains are *already* opaque. |
| **Version churn** — breaking changes v0.1-0.3 | Medium | v0.3 era is stable. LangGraph architecturally separate. Pin versions. |
| **MLX incompatibility** — cloud-optimized tool calling | N/A for AAPM | AAPM uses cloud models. Only affects PA stack (excluded). |
| **Vendor lock-in to LangSmith** | Low | Langfuse (open-source) as alternative. |
| **Refactoring cost** | Medium | 1:1 mappings enable incremental migration. No big-bang. |
| **Over-engineering** | Low | 97+ MCP tools + 40+ resilience modules + 5 model families + 2 autonomous systems already exist. LangGraph *simplifies*. |

### Cost/Benefit Summary

| Use Case | Net Assessment |
|----------|---------------|
| **Personal assistant (OpenClaw/text-router)** | **Skip.** Custom stack is faster, simpler, and purpose-built. |
| **AAPM scheduling agent** | **Adopt incrementally.** Python-native orchestration, state machine scheduling, multi-model portability, and unified observability justify the dependency cost. |

---

## Adoption Path (Incremental)

### Phase 1: LangGraph for Scheduling Pipeline *(Completed — PR #1157, #1181)*
- Convert `SchedulingEngine.generate()` phases into a LangGraph StateGraph
- Keep all existing solver/validator/constraint code unchanged
- Add state checkpointing for solver recovery
- Added `ml_score` node (node 12) for post-validation ML scoring via ScheduleScorer
- **Files:** `backend/app/scheduling/graph.py`, `graph_nodes.py` (13 nodes), `graph_state.py`

### Phase 2: MCP Tool Adapter Layer
- Thin adapter to expose MCP tools as LangChain tools
- Both interfaces coexist — no breaking change to existing MCP consumers
- **Files:** New `mcp-server/src/scheduler_mcp/langchain_adapter.py`

### Phase 3: LangSmith/Langfuse Integration
- Add tracing to scheduling pipeline and resilience checks
- Schedule quality evaluation datasets
- **Files:** Config in `backend/app/core/config.py`, tracing decorator

### Phase 4: Agent Orchestration in Python
- Migrate key `.claude/skills/` patterns to LangGraph agent nodes
- YAML skills continue to work for Claude Code; Python graphs work for everything
- **Files:** New `backend/app/agents/` directory

---

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Raw OpenAI/Anthropic SDKs** | Current approach. Works but doesn't scale to multi-agent or multi-model. |
| **CrewAI** | Simpler multi-agent framework. Less mature than LangGraph. |
| **AutoGen (Microsoft)** | Good for code generation agents. Overkill for scheduling. |
| **Custom (current PA stack)** | Best for personal assistant. Not worth replacing. |
| **Haystack** | RAG-focused. Less agent support than LangChain. |

## References

- LangChain docs: https://python.langchain.com
- LangGraph: https://langchain-ai.github.io/langgraph/
- LangSmith: https://smith.langchain.com
- Terminal Bench Deep Agents (GPT-5.2-Codex + LangChain harness)
- Codex-CLAUDE.md 20-bug incident (Feb 2026) — motivation for model-agnostic orchestration
