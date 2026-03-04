# ADR: LangChain → Pure Python Migration Path

**Date:** 2026-02-18
**Status:** REFERENCE (no action yet)
**Context:** Sketched migration path from LangChain scaffolding to pure Python for AAPM scheduling agent.
**Related:** [ADR-2026-02-17-langchain-evaluation.md](ADR-2026-02-17-langchain-evaluation.md) (DEFERRED)

---

## Context

Following the LangChain evaluation (DEFERRED), this documents the concrete migration path if LangChain is ever adopted as scaffolding for AAPM's scheduling agent. The core insight: use LangChain temporarily to prototype multi-step workflows, then replace LLM nodes with deterministic logic and drop the framework.

## Migration Strategy

### Key Mechanism: `RunnableLambda`

LangChain's `Runnable` interface (`invoke()`, `stream()`, `batch()`) lets any Python function participate in a chain via `RunnableLambda`. This enables incremental replacement:

```python
from langchain_core.runnables import RunnableLambda

def deterministic_scheduler(input_data):
    return solve_schedule(input_data)  # OR-Tools, no LLM

chain = preprocess | RunnableLambda(deterministic_scheduler) | postprocess
```

### Steps

1. **Audit the chain** — which nodes need an LLM (NLU, fuzzy reasoning) vs. deterministic (scheduling, validation, data transforms)?
2. **Replace deterministic nodes with `RunnableLambda`** — OR-Tools solvers, rule engines, validation logic stay composable during transition
3. **Extract graph into LangGraph** — nodes are just Python functions with state; explicit control flow (if/else, loops)
4. **Drop the framework** — once every node is a `RunnableLambda` or pure function, replace pipe syntax with plain function composition

### End-State Architecture (No LLM)

| Layer | Implementation | LLM Required? |
|-------|---------------|---------------|
| Input parsing | Structured forms / API endpoints | No (web UI) |
| Constraint solving | OR-Tools 9.15 | No |
| Validation | Rule-based ACGME checks | No |
| Output | Structured JSON / calendar exports | No |
| Communication | OpenClaw → messaging (templated) | No |

**Only potential LLM use case:** Handling unstructured NL requests from residents (e.g., "swap my Tuesday call"). Even this can be replaced with structured input forms or pattern matching.

## Decision

**No action now.** This is a reference document for when AAPM's scheduling agent moves to production. The current solver architecture (OR-Tools + FastAPI + Celery) works without LangChain. Revisit when building multi-agent workflows that genuinely need LLM reasoning in the loop.

## Sources

- LangChain Expression Language (Pinecone)
- LangChain Runnable Architecture (DZone)
- Why Octomind dropped LangChain (octomind.dev)
